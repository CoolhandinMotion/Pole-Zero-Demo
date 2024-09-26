import warnings
warnings.filterwarnings("ignore")
from dataclasses import dataclass,field
import numpy as np
from numpy.typing import NDArray
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
    normalized_abs_f_resp:NDArray = field(init=False,repr=False)
    max_abs_resp: float = field(init=False,repr=False)
    num: list = field(init=False, repr=False, default_factory=list)
    denom: list = field(init=False, repr=False, default_factory=list)

    @property
    def sampling_frequency(self):
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
    frequencies, freq_abs_resp = model.freqs, model.normalized_abs_f_resp
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
    ax.set_title(f"Pole Zero map fs = {model.sampling_frequency} Hz")

    y_labels = ["","","","","",r"$\frac{fs}{2}$","","","",""]

    ax.set_yticklabels(y_labels,rotation='horizontal', fontsize=16)
    ax.set_xticklabels(y_labels, rotation='horizontal', fontsize=0)
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

    ax.step(t, np.squeeze(y),label=f"sampling time {np.around(model.sampling_time,decimals=3)} s")
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
    return fig, ax


def get_complex_number_from_list(num_list: list[float, float]) -> complex:
    assert len(num_list) == 2, "Complex number not in right format"
    return complex(num_list[0], num_list[1])


def get_analog_pole_zero_line_objects(model: Model):
    pole_line_2d_objects = []
    zero_line_2d_objects = []
    pointer_line_objects = []
    pointer_x, pointer_y = 0, 0
    fig, ax = create_s_plot(model)
    for pole in model.poles.keys():
        line, = ax.plot([pointer_x, np.real(pole)], [pointer_y, np.imag(pole)], color="r")
        pole_line_2d_objects.append(line)
    for zero in model.zeros.keys():
        line, = ax.plot([pointer_x, np.real(zero)], [pointer_y, np.imag(zero)], color="g")
        zero_line_2d_objects.append(line)

    line = ax.scatter(pointer_x,pointer_y, marker="o", color="b", s=50)
    pointer_line_objects.append(line)

    pole_zero_line_obj_dict = {"pole_line_objects": pole_line_2d_objects,
                   "zero_line_objects": zero_line_2d_objects,
                   "pointer_line_objects": pointer_line_objects,
                   "fig":fig,
                   "ax":ax}

    return pole_zero_line_obj_dict

def analog_pole_zero_animation_func(frame:int,line_obj_dict:dict,canvas,model):
    frequencies, freq_abs_resp = model.freqs, model.normalized_abs_f_resp
    max_frame = len(frequencies)-1
    if frame >= max_frame:
        fig,ax = create_s_plot(model)
        canvas.figure = fig

    ax = line_obj_dict["ax"]
    children = ax._children
    pole_dist = 1
    zero_dist = 1

    num_pole_line_objs = len(line_obj_dict["pole_line_objects"])
    num_zero_line_objs = len(line_obj_dict["zero_line_objects"])
    poles_animated = 0
    zeros_animated = 0
    for line_obj in children:
        if line_obj in line_obj_dict["pole_line_objects"]:
            line_ydata = line_obj.get_ydata()
            line_xdata = line_obj.get_xdata()

            line_ydata[0] =  frequencies[frame] # object in question is a line, we only increase the y for one end of the line (corresponding to Pointer)
            line_obj.set_ydata(line_ydata) # set new y in animation for ascending point on s plane imaginary axis
            line_corr = np.array([line_xdata, line_ydata]) # put together line coordinates to calculate its length (distance from pole/zero)
            pole_dist = pole_dist *  np.linalg.norm(line_corr[:, 0] - line_corr[:, 1])
            poles_animated +=1
            if poles_animated == num_pole_line_objs:
                line_obj.set_label(f"pole distance {pole_dist:.3f}")

        elif line_obj in line_obj_dict["zero_line_objects"]:
            line_ydata = line_obj.get_ydata()
            line_xdata = line_obj.get_xdata()

            line_ydata[0] =  frequencies[frame] # object in question is a line, we only increase the y for one end of the line (corresponding to Pointer)
            line_obj.set_ydata(line_ydata) # set new y in animation for ascending point on s plane imaginary axis
            line_corr = np.asarray([line_xdata, line_ydata]) # put together line coordinates to calculate its length (distance from pole/zero)
            zero_dist = zero_dist * np.linalg.norm(line_corr[:, 0] - line_corr[:, 1])
            zeros_animated +=1

            if zeros_animated == num_zero_line_objs:
                line_obj.set_label(f"zero distance {zero_dist:.3f}")

        elif line_obj in line_obj_dict["pointer_line_objects"]:
            new_location = [0,frequencies[frame]]
            line_obj.set_offsets(new_location)
            line_obj.set_label(f"z/p {zero_dist/pole_dist:.3f}")

    ax.legend()
    return ax,

def get_response_line_objects(model:Model):
    line_2d_objects = []
    frequencies, freq_abs_resp = model.freqs, model.normalized_abs_f_resp
    pointer_x = frequencies[0]
    pointer_y = freq_abs_resp[0]
    fig, ax = create_freq_resp_plot(model)
    line = ax.scatter(pointer_x,pointer_y, marker="o", color="b", s=100)
    line_2d_objects.append(line)
    return fig, ax, line_2d_objects

def response_animation_func(frame:int, line_2d_objects:list[Line2D], ax, canvas, model):
    frequencies, freq_abs_resp = model.freqs, model.normalized_abs_f_resp
    max_frame = len(frequencies)-1
    if frame >= max_frame:
        fig, ax = create_freq_resp_plot(model)
        canvas.figure = fig
    children = ax._children
    for line_obj in children:
        if line_obj in line_2d_objects:
            new_location = [frequencies[frame],freq_abs_resp[frame]]
            line_obj.set_offsets(new_location)
            line_obj.set_label(f"gain {freq_abs_resp[frame]:.3f}")
    ax.legend()
    return ax,


def get_digital_pole_zero_line_objects(model: Model):
    pole_line_2d_objects = []
    zero_line_2d_objects = []
    pointer_line_objects = []
    pointer_x, pointer_y = 1, 0
    fig, ax = create_z_plot(model)
    for pole in model.poles.keys():
        line, = ax.plot([pointer_x, np.real(pole)], [pointer_y, np.imag(pole)], color="r")
        pole_line_2d_objects.append(line)
    for zero in model.zeros.keys():
        line, = ax.plot([pointer_x, np.real(zero)], [pointer_y, np.imag(zero)], color="g")
        zero_line_2d_objects.append(line)

    line = ax.scatter(pointer_x,pointer_y, marker="o", color="b", s=50)
    pointer_line_objects.append(line)

    pole_zero_line_obj_dict = {"pole_line_objects": pole_line_2d_objects,
                   "zero_line_objects": zero_line_2d_objects,
                   "pointer_line_objects": pointer_line_objects,
                   "fig":fig,
                   "ax":ax}
    return pole_zero_line_obj_dict

def digital_pole_zero_animation_func(frame:int,line_obj_dict:dict,canvas,model):
    frequencies, freq_abs_resp = model.freqs, model.normalized_abs_f_resp
    fs = model.sampling_frequency
    max_frame = len(frequencies)-1
    if frame >= max_frame:
        fig,ax = create_z_plot(model)
        canvas.figure = fig

    ax = line_obj_dict["ax"]
    children = ax._children
    pole_dist = 1
    zero_dist = 1

    num_pole_line_objs = len(line_obj_dict["pole_line_objects"])
    num_zero_line_objs = len(line_obj_dict["zero_line_objects"])
    poles_animated = 0
    zeros_animated = 0
    for line_obj in children:
        if line_obj in line_obj_dict["pole_line_objects"]:
            line_ydata = line_obj.get_ydata() # object in question is a line, we only increase the y for one end of the line (corresponding to Pointer)
            line_xdata = line_obj.get_xdata()

            line_corr = np.array([line_xdata, line_ydata]) # put together line coordinates to calculate its length (distance from pole/zero)
            pole_dist = pole_dist * np.linalg.norm(line_corr[:, 0] - line_corr[:, 1])

            new_x , new_y = get_carthasian_coordinates(frequencies[frame]/fs)
            line_ydata[0] = new_y
            line_xdata[0] = new_x
            line_obj.set_ydata(line_ydata)
            line_obj.set_xdata(line_xdata)

            poles_animated+=1

            if poles_animated == num_pole_line_objs:
                line_obj.set_label(f"pole distance {pole_dist:.3f}")

        elif line_obj in line_obj_dict["zero_line_objects"]:
            line_ydata = line_obj.get_ydata() # object in question is a line, we only increase the y for one end of the line (corresponding to Pointer)
            line_xdata = line_obj.get_xdata()

            line_corr = np.asarray([line_xdata, line_ydata]) # put together line coordinates to calculate its length (distance from pole/zero)
            zero_dist = zero_dist * np.linalg.norm(line_corr[:, 0] - line_corr[:, 1])

            new_x , new_y = get_carthasian_coordinates(frequencies[frame]/fs)
            line_ydata[0] = new_y
            line_xdata[0] = new_x
            line_obj.set_ydata(line_ydata)
            line_obj.set_xdata(line_xdata)
            zeros_animated+=1

            if zeros_animated == num_zero_line_objs:
                line_obj.set_label(f"zero distance {zero_dist:.3f}")

        elif line_obj in line_obj_dict["pointer_line_objects"]:

            new_x , new_y = get_carthasian_coordinates(frequencies[frame]/fs)
            new_location = [new_x,new_y]
            line_obj.set_offsets(new_location)
            degree = get_degree_on_unit_circle(new_x, new_y)
            pole_over_zero = (zero_dist / pole_dist) / model.max_abs_resp
            line_obj.set_label(f"z/p {pole_over_zero:.3f} degree {degree:.2f}°")
            # we can either show the gain for pointer in z plane
            # line_obj.set_label(f"z/p {(zero_dist/pole_dist)/model.max_abs_resp:.3f} degree")
            # alternatively we can either show the angle for pointer in z plane
            # line_obj.set_label(f"degree {get_degree_on_unit_circle(new_x, new_y):.2f}°")

    ax.legend()
    return ax,


def get_degree_on_unit_circle(x,y):
    degree = (np.arctan(y/x)/np.pi)*180
    if x>0 and y>0:
        return degree
    elif x>0 and y<0:
        return 360 + degree
    elif x<0 and y>0:
        return 180 + degree
    elif x<0 and y<0:
        return 180 + degree
    else:
        return degree
