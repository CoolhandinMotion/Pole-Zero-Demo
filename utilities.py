from dataclasses import dataclass
import numpy as np
import matplotlib.pyplot as plt
from typing import Protocol, Callable
from scipy import signal
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from customtkinter import CTkCanvas
# TODO: "implement step response as well using  t,y = signal.dstep(sys3,n=30)"
# TODO: "show Fach in int close to x or o pointer on S or Z plane"
side_frame_width = 140
all_fig_size = (5, 5)
theta = np.linspace(0, 2 * np.pi, 150)
radius = 1
grid_division = 11


@dataclass
class PlottingCanvas(Protocol):
    canvas: FigureCanvasTkAgg


def build_repeated_item_list_from_dict(dictionary:dict) -> list:
    repeated_list = [key for key, value in dictionary.items() for i in range(value)]
    return  repeated_list

def create_freq_resp_plot(model):
    frequencies, freq_complex_resp = model.freqs, model.complex_f_resp
    fig, ax = plt.subplots(figsize=all_fig_size)
    ax.grid()
    x_values = frequencies
    y_values = np.abs(freq_complex_resp)
    ax.plot(x_values, y_values, label="Frequency response")
    ax.set_title("Frequency response")
    ax.set_xlabel("Frequencies")
    ax.set_ylabel("Gain")
    # ax.legend()
    return fig, ax


def create_phase_resp_plot(model):
    frequencies, freq_complex_resp = model.freqs, model.complex_f_resp
    fig, ax = plt.subplots(figsize=all_fig_size)
    ax.grid()
    x_values = frequencies
    y_values = np.angle(freq_complex_resp)
    ax.plot(x_values, y_values, label="Phase response")
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


def create_freq_domain_plot(model):
    if model.type.name == "DIGITAL":
        return create_z_plot(model)
    elif model.type.name == "ANALOG":
        return create_s_plot(model)


def create_z_plot(model):
    assert model.type.name == "DIGITAL", "z plot only for descrete case"
    fig, ax = create_unit_circle()
    ax.grid()
    ax.set_title("Pole Zero map")
    for pole in model.poles.keys():
        ax.scatter(np.real(pole), np.imag(pole), marker="X", color="r", s=100)
        ax.text(np.real(pole),np.imag(pole),f'x{model.poles[pole]}',ha='center',size='large')
    for zero in model.zeros.keys():
        ax.scatter(np.real(zero), np.imag(zero), marker="o", color="g", s=100)
        ax.text(np.real(zero), np.imag(zero),f'x{model.zeros[zero]}',ha='center',size='large')

    # children = ax._children
    # print(children)
    return fig, ax


def create_s_plot(model):
    assert model.type.name == "ANALOG", "S plot is only for continuous case"
    fig, ax = plt.subplots(figsize=all_fig_size)
    ax.grid()
    ax.set_ylim([-4, 4])
    ax.grid()
    ax.axvline(x=0, color="k")
    ax.axhline(y=0, color="k")
    ax.set_title("Pole Zero map")
    for pole in model.poles.keys():
        ax.scatter(np.real(pole), np.imag(pole), marker="X", color="r", s=100)
        ax.text(np.real(pole), np.imag(pole), f'x{model.poles[pole]}', ha='center',size='large')
    for zero in model.zeros.keys():
        ax.scatter(np.real(zero), np.imag(zero), marker="o", color="g", s=100)
        ax.text(np.real(zero), np.imag(zero), f'x{model.zeros[zero]}', ha='center',size='large')


    children = ax._children
    print(children)
    return fig, ax


def create_time_plot(model):
    if model.type.name == "DIGITAL":
        return create_digital_impulse_time_response(model)
    elif model.type.name == "ANALOG":
        return create_analog_impulse_time_response(model)


def create_digital_impulse_time_response(model):
    fig, ax = plt.subplots(figsize=all_fig_size)
    sys3 = signal.TransferFunction(model.num, model.denom, dt=0.1)
    # t,y = signal.dstep(sys3,n=30)
    t, y = signal.dimpulse(sys3, n=30)
    ax.step(t, np.squeeze(y))
    ax.grid()
    ax.set_xlabel("Number of samples")
    ax.set_ylabel("Amplitude")
    ax.set_title("Impulse time response")
    return fig, ax


def create_analog_impulse_time_response(model):
    fig, ax = plt.subplots(figsize=all_fig_size)
    sys3 = signal.TransferFunction(model.num, model.denom)
    t, y = signal.impulse(sys3)
    ax.plot(t, y)
    ax.grid()
    ax.set_xlabel("time")
    ax.set_ylabel("Amplitude")
    ax.set_title("Impulse time response")
    return fig, ax

def get_complex_number_from_list(num_list:list[float,float]) -> complex:
    assert len(num_list) == 2, "Complex number not in right format"
    return complex(num_list[0], num_list[1])



def display_canvas_plot(plotting_canvas: PlottingCanvas,plotting_func:Callable):
    if plotting_canvas.canvas:
        plotting_canvas.canvas.get_tk_widget().destroy()
    fig, ax = plotting_func()
    plotting_canvas.canvas = FigureCanvasTkAgg(fig, plotting_canvas)
    plotting_canvas.canvas.get_tk_widget().grid(sticky="nsew")

# def s_plot_animation(i,ax_line_2d_obj,canvas, max_frame,model):
#
#     if i == max_frame:
#         # fig,ax = thumbnail_func()
#         canvas.figure = fig
#
#     ax_line_2d_obj.set_ydata(np.sin(x + i / 10.0))  # update the data
#     return ax_line_2d_obj,
#     # ax.set_ylim([-4, 4])
#     ...

# def analog_freq_domain_animation(self, animation_func,thumbnail_func) -> None:
#     if self.canvas:
#         self.canvas.get_tk_widget().destroy()
#     fig, ax = thumbnail_func()
#     line_2d = ax._children[0]
#     self.canvas = FigureCanvasTkAgg(fig, self)
#     self.canvas.get_tk_widget().grid(sticky="nsew")
