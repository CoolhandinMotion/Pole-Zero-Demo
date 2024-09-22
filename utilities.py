from dataclasses import dataclass,field
import numpy as np
import matplotlib.pyplot as plt
from typing import Protocol, Callable
from scipy import signal
from enum import Enum,auto
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.lines import Line2D
# TODO: "implement step response as well using  t,y = signal.dstep(sys3,n=30)"
# TODO: "show Fach in int close to x or o pointer on S or Z plane"
side_frame_width = 140
all_fig_size = (5, 5)
theta = np.linspace(0, 2 * np.pi, 150)
radius = 1
grid_division = 11

@dataclass
class Model(Protocol):
    type: Enum = field(init=False)
    filter: Enum = field(init=False)
    poles: dict[complex,int] = field(init=False, default_factory=dict)
    zeros: dict[complex,int] = field(init=False, default_factory=dict)
    freqs: list = field(init=False, repr=False, default_factory=list)
    complex_f_resp: list = field(init=False, repr=False, default_factory=list)
    num: list = field(init=False, repr=False, default_factory=list)
    denom: list = field(init=False, repr=False, default_factory=list)


@dataclass
class PlottingCanvas(Protocol):
    canvas: FigureCanvasTkAgg


def build_repeated_item_list_from_dict(dictionary: dict) -> list:
    repeated_list = [key for key, value in dictionary.items() for i in range(value)]
    return repeated_list


def create_freq_resp_plot(model:Model):
    frequencies, freq_complex_resp = model.freqs, model.complex_f_resp
    fig, ax = plt.subplots(figsize=all_fig_size)
    ax.grid()
    x_values = frequencies
    y_values = np.abs(freq_complex_resp)
    ax.plot(x_values, y_values)
    model_name = f"{model.type.name.lower().capitalize()}"
    ax.set_title(f"frequency response")
    ax.set_xlabel("frequencies")
    ax.set_ylabel("gain")
    # ax.legend()
    return fig, ax


def create_phase_resp_plot(model:Model):
    frequencies, freq_complex_resp = model.freqs, model.complex_f_resp
    fig, ax = plt.subplots(figsize=all_fig_size)
    ax.grid()
    x_values = frequencies
    y_values = np.angle(freq_complex_resp)
    ax.plot(x_values, y_values)
    ax.set_title("phase response")
    ax.set_xlabel("frequencies")
    ax.set_ylabel("phase")
    # ax.legend()
    return fig, ax


def create_unit_circle():
    # plt.grid(color = 'green', linestyle = '--', linewidth = 0.5)
    a = radius * np.cos(theta)
    b = radius * np.sin(theta)
    fig, ax = plt.subplots(figsize=all_fig_size)
    # ax.set_axis_off()

    ax.grid()
    ax.plot(a, b, c="b")
    ax.axhline(y=0, color="k")
    ax.axvline(x=0, color="k")
    return fig, ax


def create_freq_domain_plot(model:Model):
    if model.type.name == "DIGITAL":
        return create_z_plot(model)
    elif model.type.name == "ANALOG":
        return create_s_plot(model)


def create_z_plot(model:Model):
    assert model.type.name == "DIGITAL", "z plot only for descrete case"
    fig, ax = create_unit_circle()
    ax.grid()
    ax.set_title("Pole Zero map")
    for pole in model.poles.keys():
        ax.scatter(np.real(pole), np.imag(pole), marker="X", color="r", s=100)
        ax.text(np.real(pole), np.imag(pole), f'x{model.poles[pole]}', ha='center', size='large')
    for zero in model.zeros.keys():
        ax.scatter(np.real(zero), np.imag(zero), marker="o", color="g", s=100)
        ax.text(np.real(zero), np.imag(zero), f'x{model.zeros[zero]}', ha='center', size='large')

    return fig, ax


def create_s_plot(model:Model):
    assert model.type.name == "ANALOG", "S plot is used only for analog (continuous) case"
    fig, ax = plt.subplots(figsize=all_fig_size)
    ax.grid()
    ax.set_ylim([-4, 4])
    ax.grid()
    ax.axvline(x=0, color="k")
    ax.axhline(y=0, color="k")
    ax.set_title("Pole Zero map")
    for pole in model.poles.keys():
        ax.scatter(np.real(pole), np.imag(pole), marker="X", color="r", s=100)
        ax.text(np.real(pole), np.imag(pole), f'x{model.poles[pole]}', ha='center', size='large')
    for zero in model.zeros.keys():
        ax.scatter(np.real(zero), np.imag(zero), marker="o", color="g", s=100)
        ax.text(np.real(zero), np.imag(zero), f'x{model.zeros[zero]}', ha='center', size='large')

    return fig, ax


def create_time_plot(model:Model):
    if model.type.name == "DIGITAL":
        return create_digital_impulse_time_response(model)
    elif model.type.name == "ANALOG":
        return create_analog_impulse_time_response(model)


def create_digital_impulse_time_response(model:Model):
    DT = .1
    fig, ax = plt.subplots(figsize=all_fig_size)
    sys3 = signal.TransferFunction(model.num, model.denom, dt=DT)
    # t,y = signal.dstep(sys3,n=30)
    t, y = signal.dimpulse(sys3, n=30)
    ax.step(t, np.squeeze(y))
    ax.grid()
    ax.set_xlabel("number of samples")
    ax.set_ylabel("amplitude")
    ax.set_title(f"impulse time response, {DT=} s")
    return fig, ax


def create_analog_impulse_time_response(model:Model):
    fig, ax = plt.subplots(figsize=all_fig_size)
    sys3 = signal.TransferFunction(model.num, model.denom)
    t, y = signal.impulse(sys3)
    ax.plot(t, y)
    ax.grid()
    ax.set_xlabel("time")
    ax.set_ylabel("amplitude")
    ax.set_title("impulse time response")
    return fig, ax


def get_complex_number_from_list(num_list: list[float, float]) -> complex:
    assert len(num_list) == 2, "Complex number not in right format"
    return complex(num_list[0], num_list[1])




def analog_freq_animation(frame: int, plotting_canvas: PlottingCanvas, ax_line_2d_obj:Line2D, max_frame:int, model):
    # ax.set_ylim([-4, 4])
    if frame == max_frame:
        fig, ax = create_s_plot(model)
        plotting_canvas.canvas.figure = fig

    ax_line_2d_obj.set_ydata(np.sin(x + i / 10.0))  # update the data
    return ax_line_2d_obj,

    ...

# def analog_freq_domain_animation(self, animation_func,thumbnail_func) -> None:
#     if self.canvas:
#         self.canvas.get_tk_widget().destroy()
#     fig, ax = thumbnail_func()
#     line_2d = ax._children[0]
#     self.canvas = FigureCanvasTkAgg(fig, self)
#     self.canvas.get_tk_widget().grid(sticky="nsew")
