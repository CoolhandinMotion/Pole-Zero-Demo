from dataclasses import dataclass,field
import numpy as np
import matplotlib.pyplot as plt
from typing import Protocol, Callable
from scipy import signal
from enum import Enum,auto
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.lines import Line2D


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
    @property
    def normalized_absolute_f_response(self):
        ...

@dataclass
class PlottingCanvas(Protocol):
    canvas: FigureCanvasTkAgg

def read_proper_number(number_string:str) -> float | None:
    try:
        num = float(number_string)
        return num
    except ValueError:
        return None


def build_repeated_item_list_from_dict(dictionary: dict) -> list:
    repeated_list = [key for key, value in dictionary.items() for i in range(value)]
    return repeated_list

def get_carthasian_coordinates(fraction_of_circle):
    rad = 2*np.pi*fraction_of_circle
    x = np.cos(rad)
    y = np.sin(rad)
    return x,y

def create_freq_resp_plot(model:Model) -> tuple[plt.Figure,plt.axes]:
    frequencies, freq_abs_resp = model.freqs, model.normalized_absolute_f_response
    fig, ax = plt.subplots(figsize=all_fig_size)
    ax.grid()
    x_values = frequencies
    y_values = freq_abs_resp

    ax.plot(x_values, y_values)
    ax.set_title(f"frequency response")
    ax.set_xlabel("frequencies")
    ax.set_ylabel("gain")
    return fig, ax


def create_phase_resp_plot(model:Model) -> tuple[plt.Figure,plt.axes]:
    frequencies, freq_complex_resp = model.freqs, model.complex_f_resp
    fig, ax = plt.subplots(figsize=all_fig_size)
    ax.grid()
    x_values = frequencies
    y_values = np.angle(freq_complex_resp)
    y_values = y_values/np.max(y_values) #normalize phase gain
    ax.plot(x_values, y_values)
    ax.set_title("phase response")
    ax.set_xlabel("frequencies")
    ax.set_ylabel("phase")
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
        return create_digital_time_response(model)
    elif model.type.name == "ANALOG":
        return create_analog_time_response(model)


def create_digital_time_response(model:Model) -> tuple[plt.Figure,plt.axes]:
    fig, ax = plt.subplots(figsize=all_fig_size)
    sys3 = signal.TransferFunction(model.num, model.denom, dt=model.sampling_time)
    if model.time_resp.name == "IMPULSE":
        t, y = signal.dimpulse(sys3, n=30)
        ax.set_title(f"impulse time response")
    elif model.time_resp.name == "STEP":
        t, y = signal.dstep(sys3, n=30)
        ax.set_title(f"step time response")
    else:
        raise ValueError("Either Impulse or Step time response")


    ax.step(t, np.squeeze(y),label=f"sampling time {model.sampling_time} s")
    ax.grid()
    ax.set_xlabel("number of samples")
    ax.set_ylabel("amplitude")

    ax.legend()
    return fig, ax


def create_analog_time_response(model:Model) -> tuple[plt.Figure,plt.axes]:
    fig, ax = plt.subplots(figsize=all_fig_size)
    sys3 = signal.TransferFunction(model.num, model.denom)
    if model.time_resp.name == "IMPULSE":
        t, y = signal.impulse(sys3)
        ax.set_title("impulse time response")
    elif model.time_resp.name == "STEP":
        t, y = signal.step(sys3)
        ax.set_title("step time response")
    else:
        raise ValueError("Either Impulse or Step time response")
    ax.plot(t, y)
    ax.grid()
    ax.set_xlabel("time")
    ax.set_ylabel("amplitude")
    # ax.set_title("impulse time response")
    return fig, ax


def get_complex_number_from_list(num_list: list[float, float]) -> complex:
    assert len(num_list) == 2, "Complex number not in right format"
    return complex(num_list[0], num_list[1])


def get_analog_pole_zero_line_objects(model: Model):
    pole_line_2d_objects = []
    zero_line_2d_objects = []
    pointer_x, pointer_y = 0, 0
    fig, ax = create_s_plot(model)
    for pole in model.poles.keys():
        line, = ax.plot([pointer_x, np.real(pole)], [pointer_y, np.imag(pole)], color="r")
        pole_line_2d_objects.append(line)
    for zero in model.zeros.keys():
        line, = ax.plot([pointer_x, np.real(zero)], [pointer_y, np.imag(zero)], color="g")
        zero_line_2d_objects.append(line)

    line_2d_objects = pole_line_2d_objects + zero_line_2d_objects
    return fig, ax, line_2d_objects

def analog_pole_zero_animation_func(frame:int,line_2d_objects:list[Line2D],ax,canvas,model):
    frequencies = model.freqs

    max_frame = len(frequencies)-1
    if frame >= max_frame:
        fig,ax = create_s_plot(model)
        canvas.figure = fig

    children = ax._children
    for line_obj in children:
        if line_obj in line_2d_objects:
            line_ydata = line_obj.get_ydata() # object in question is a line, we only increase the y for one end of the line (corresponding to Pointer)
            line_ydata[0] =  frequencies[frame]
            line_obj.set_ydata(line_ydata)
    return ax,

def get_response_line_objects(model:Model):
    line_2d_objects = []
    frequencies, freq_abs_resp = model.freqs, model.normalized_absolute_f_response
    pointer_x = frequencies[0]
    pointer_y = freq_abs_resp[0]
    fig, ax = create_freq_resp_plot(model)
    line = ax.scatter(pointer_x,pointer_y, marker="o", color="b", s=100)
    line_2d_objects.append(line)
    return fig, ax, line_2d_objects

def response_animation_func(frame:int, line_2d_objects:list[Line2D], ax, canvas, model):
    frequencies, freq_abs_resp = model.freqs, model.normalized_absolute_f_response
    max_frame = len(frequencies)-1
    if frame >= max_frame:
        fig, ax = create_freq_resp_plot(model)
        canvas.figure = fig

    children = ax._children
    for line_obj in children:
        if line_obj in line_2d_objects:
            new_location = [frequencies[frame],freq_abs_resp[frame]]
            line_obj.set_offsets(new_location)
    return ax,


def get_digital_pole_zero_line_objects(model: Model):
    pole_line_2d_objects = []
    zero_line_2d_objects = []
    pointer_x, pointer_y = 1, 0
    fig, ax = create_z_plot(model)
    for pole in model.poles.keys():
        line, = ax.plot([pointer_x, np.real(pole)], [pointer_y, np.imag(pole)], color="r")
        pole_line_2d_objects.append(line)
    for zero in model.zeros.keys():
        line, = ax.plot([pointer_x, np.real(zero)], [pointer_y, np.imag(zero)], color="g")
        zero_line_2d_objects.append(line)

    line_2d_objects = pole_line_2d_objects + zero_line_2d_objects
    return fig, ax, line_2d_objects

def digital_pole_zero_animation_func(frame:int,line_2d_objects:list[Line2D],ax,canvas,model):
    frequencies = model.freqs
    fs = model.sampling_frequency
    max_frame = len(frequencies)-1
    if frame >= max_frame:
        fig,ax = create_z_plot(model)
        canvas.figure = fig

    children = ax._children
    for line_obj in children:
        if line_obj in line_2d_objects:
            line_ydata = line_obj.get_ydata() # object in question is a line, we only increase the y for one end of the line (corresponding to Pointer)
            line_xdata = line_obj.get_xdata()
            new_x , new_y = get_carthasian_coordinates(frequencies[frame]/fs)
            line_ydata[0] = new_y
            line_xdata[0] = new_x
            line_obj.set_ydata(line_ydata)
            line_obj.set_xdata(line_xdata)
    return ax,
