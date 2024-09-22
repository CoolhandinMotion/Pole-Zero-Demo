from dataclasses import dataclass,field
import numpy as np
import matplotlib.pyplot as plt
from typing import Protocol, Callable
from scipy import signal
from enum import Enum,auto
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.lines import Line2D
from matplotlib import animation
from functools import partial

# TODO: "implement step response as well using  t,y = signal.dstep(sys3,n=30)"
# TODO: "show Fach in int close to x or o pointer on S or Z plane"
side_frame_width = 140
all_fig_size = (5, 5)
theta = np.linspace(0, 2 * np.pi, 150)
radius = 1
grid_division = 11

class ModelType(Enum):
    DIGITAL = auto()
    ANALOG = auto()

@dataclass
class Model(Protocol):
    type: Enum = field(init=False)
    filter: Enum = field(init=False)
    sampling_time: float = field(init=False, default=.01)
    poles: dict[complex,int] = field(init=False, default_factory=dict)
    zeros: dict[complex,int] = field(init=False, default_factory=dict)
    freqs: list = field(init=False, repr=False, default_factory=list)
    complex_f_resp: list = field(init=False, repr=False, default_factory=list)
    num: list = field(init=False, repr=False, default_factory=list)
    denom: list = field(init=False, repr=False, default_factory=list)

    @property
    def sampling_frequency(self):
        ...


@dataclass
class PlottingCanvas(Protocol):
    canvas: FigureCanvasTkAgg


def build_repeated_item_list_from_dict(dictionary: dict) -> list:
    repeated_list = [key for key, value in dictionary.items() for i in range(value)]
    return repeated_list


def create_freq_resp_plot(model:Model) -> tuple[plt.Figure,plt.axes]:
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


def create_phase_resp_plot(model:Model) -> tuple[plt.Figure,plt.axes]:
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


def create_unit_circle() -> tuple[plt.Figure,plt.axes]:
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


def create_freq_domain_plot(model:Model)->Callable[[Model],tuple[plt.Figure,plt.axes]]:
    if model.type.name == "DIGITAL":
        return create_z_plot(model)
    elif model.type.name == "ANALOG":
        return create_s_plot(model)


def create_z_plot(model:Model) ->tuple[plt.Figure,plt.axes] :
    assert model.type.name == "DIGITAL", "z plot only for Digital (discrete) case"
    fig, ax = create_unit_circle()
    ax.grid()
    ax.set_title(f"Pole Zero map fs {model.sampling_frequency} Hz")
    for pole in model.poles.keys():
        ax.scatter(np.real(pole), np.imag(pole), marker="X", color="r", s=100)
        ax.text(np.real(pole), np.imag(pole), f'x{model.poles[pole]}', ha='center', size='large')
    for zero in model.zeros.keys():
        ax.scatter(np.real(zero), np.imag(zero), marker="o", color="g", s=100)
        ax.text(np.real(zero), np.imag(zero), f'x{model.zeros[zero]}', ha='center', size='large')

    return fig, ax


def create_s_plot(model:Model) -> tuple[plt.Figure,plt.axes]:
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


def create_time_plot(model:Model)->Callable[[Model],tuple[plt.Figure,plt.axes]]:
    if model.type.name == "DIGITAL":
        return create_digital_impulse_time_response(model)
    elif model.type.name == "ANALOG":
        return create_analog_impulse_time_response(model)


def create_digital_impulse_time_response(model:Model) -> tuple[plt.Figure,plt.axes]:
    fig, ax = plt.subplots(figsize=all_fig_size)
    sys3 = signal.TransferFunction(model.num, model.denom, dt=model.sampling_time)
    # t,y = signal.dstep(sys3,n=30)
    t, y = signal.dimpulse(sys3, n=30)
    ax.step(t, np.squeeze(y),label=f"sampling time {model.sampling_time} s")
    ax.grid()
    ax.set_xlabel("number of samples")
    ax.set_ylabel("amplitude")
    ax.set_title(f"impulse time response")
    ax.legend()
    return fig, ax


def create_analog_impulse_time_response(model:Model) -> tuple[plt.Figure,plt.axes]:
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


def get_analog_pole_zero_line_objects(model: Model):
    pole_line_2d_objects = []
    zero_line_2d_objects = []
    pointer_x, pointer_y = 0, 0
    fig, ax = create_s_plot(model)
    # fig, ax = plt.subplots(figsize=all_fig_size)
    for pole in model.poles.keys():
        line, = ax.plot([pointer_x, np.real(pole)], [pointer_y, np.imag(pole)], color="r")
        pole_line_2d_objects.append(line)
    for zero in model.zeros.keys():
        line, = ax.plot([pointer_x, np.real(zero)], [pointer_y, np.imag(zero)], color="g")
        zero_line_2d_objects.append(line)

    line_2d_objects = pole_line_2d_objects + zero_line_2d_objects
    return fig, ax, line_2d_objects

def analog_pole_zero_animation_func(frame:int,line_2d_objects:list[Line2D],ax,canvas,model):
    max_frame = 30
    if frame == max_frame:
        fig,ax = create_s_plot(model)
        canvas.figure = fig

    children = ax._children
    for line_obj in children:
        if line_obj in line_2d_objects:
            next_ydata = line_obj.get_ydata()
            next_ydata[0] = frame/10
            line_obj.set_ydata(next_ydata)
    return ax,

def run_analog_pole_zero_animation(model:Model,pole_zero_canvas):
    fig, ax, line_2d_objects = get_analog_pole_zero_line_objects(model)
    partial_anim_func = partial(analog_pole_zero_animation_func,
                                line_2d_objects=line_2d_objects,
                                ax=ax,
                                canvas=pole_zero_canvas,
                                model=model)
    animation_result = animation.FuncAnimation(fig=fig,
                                                func=partial_anim_func,
                                                frames=50,
                                                interval=1000,
                                                blit=False,
                                                repeat=False,)
    return animation_result

