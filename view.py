import gc
from dataclasses import dataclass
import customtkinter
import tkinter as tk
from typing import Protocol, Callable
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import utilities
from functools import partial

# TODO check this link for clearing canvas instead of reconstructing an instance: https://stackoverflow.com/questions/64273113/how-to-refresh-figurecanvastkagg-continuously-in-tkinter
# TODO: "a button for save as PDF in the Side Frame"
# TODO: "Animation mode as requested by professor"


customtkinter.set_appearance_mode(
    "System"
)  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme(
    "blue"
)  # Themes: "blue" (standard), "green", "dark-blue"

model_menu_values = ["Digital", "Analog"]
filter_menu_values = ["Tief pass", "Hoch pass", "Band pass", "Band stop"]

app_geometry = (750, 750)


def get_initial_ui_values():
    # return model_menu_values[0], filter_menu_values[0]
    return model_menu_values[1], filter_menu_values[-1]

@dataclass
class Model(Protocol):
    poles: dict
    zeros: dict


@dataclass
class Presenter(Protocol):
    model: Model

    def change_default_model(self, variable):
        ...

    def change_manual_model(self):
        ...

    def run_analog_animation(self):
        ...


class App(customtkinter.CTk):
    def __init__(self) -> None:
        super().__init__()
        # configure window
        self.manual_pole_zero_button = None
        self.visual_filter_frame = None
        self.side_frame = None
        self.pole_number_frame = None
        self.zero_number_frame = None
        self.title("Digital Signal Processing Demo")
        self.geometry(f"{app_geometry[0]}x{app_geometry[0]}")
        self.minsize(*app_geometry)

    def init_ui(self, presenter: Presenter) -> None:
        self.grid_columnconfigure(tuple(range(11)), weight=1)
        self.grid_rowconfigure(tuple(range(11)), weight=1)
        'side_frame hosts different settings that user can choose'
        self.side_frame = SideFrame(self, presenter)
        'The FilterVisualFrame itself consists of 4 different canvas that host different plots'
        self.visual_filter_frame = FilterVisualFrame(self, presenter, 1)
        'pole_number_frame is a place where user can add manual poles to the filter'
        self.pole_number_frame = ManualPoleNumberFrame(self, presenter)
        'zero_number_frame is a place where user can add manual zeros to the filter'
        self.zero_number_frame = ManualZeroNumberFrame(self, presenter)

        'Below we define buttons that do not belong to any frame but necessary for functionality of the whole program'
        'button below is the confirmation button that users clicks on to confirm addition of new poles or zeros'
        self.manual_pole_zero_button = customtkinter.CTkButton(
            master=self, text="Confirm", command=presenter.change_manual_model
        )
        self.manual_pole_zero_button.grid(row=3, column=5, sticky="n")


class SideFrame(customtkinter.CTkFrame):
    def __init__(self, master, presenter: Presenter) -> None:
        super().__init__(
            master,
            corner_radius=0,
        )
        # self.place(x=0, y=0, relwidth=0.15, relheight=1)
        self.presenter = presenter
        self.__init_side_frame()

    def __init_side_frame(self) -> None:
        self.grid_rowconfigure(tuple(range(3)), weight=1)
        self.grid_rowconfigure(4, weight=50)
        self.grid_columnconfigure(0, weight=50)
        self.grid_columnconfigure(1, weight=1)
        self.grid(row=0, column=0, rowspan=11, sticky="nsew")

        self.logo_label = customtkinter.CTkLabel(
            self,
            text="Zero Pole Demo",
            font=customtkinter.CTkFont(size=12, weight="bold"),
        )
        self.logo_label.grid(
            row=0, column=0, columnspan=2, padx=20, pady=20, sticky="n"
        )
        initial_model_name_for_display_button = get_initial_ui_values()[0]
        value_inside = tk.StringVar()
        value_inside.set(initial_model_name_for_display_button)

        self.optionmenu_model = customtkinter.CTkOptionMenu(
            self,
            dynamic_resizing=False,
            variable=value_inside,
            values=model_menu_values,
            command=self.presenter.change_default_model,
        )
        self.optionmenu_model.grid(row=1, column=0, padx=10, pady=20, sticky="n")
        initial_filter_name_for_display_button = get_initial_ui_values()[1]
        value_inside = tk.StringVar()
        value_inside.set(initial_filter_name_for_display_button)
        self.optionmenu_filter = customtkinter.CTkOptionMenu(
            self,
            dynamic_resizing=False,
            variable=value_inside,
            values=filter_menu_values,
            command=self.presenter.change_default_model,
        )

        self.optionmenu_filter.grid(row=2, column=0, padx=10, pady=10, sticky="n")

        self.animation_button = customtkinter.CTkButton(
            master=self, text="Animation", command=self.presenter.run_analog_animation)

        self.animation_button.grid(row=3, column=0, sticky="s")

class FilterVisualFrame:
    plots_2_display = []

    def __init__(self, master, presenter: Presenter, span) -> None:
        self.canvas_2_partial_func_plotter_map = None
        self.master = master
        self.presenter = presenter
        self.span = span
        self.__populate_filter_visual_frame()


    def __populate_filter_visual_frame(self) -> None:
        # generates pole zero map on top left corner of response frame
        self.canvas_freq_domain = PlottingCanvas(
            self.master, self.presenter, grid_row=0, grid_column=1, span=self.span
        )
        self.plots_2_display.append(self.canvas_freq_domain)

        # generates time response on bottom left corner of response frame
        self.canvas_time_domain = PlottingCanvas(
            self.master, self.presenter, grid_row=2, grid_column=1, span=self.span
        )
        self.plots_2_display.append(self.canvas_time_domain)

        # generates frequency on top right corner of response frame
        self.canvas_freq_resp = PlottingCanvas(
            self.master, self.presenter, grid_row=0, grid_column=3, span=self.span
        )
        self.plots_2_display.append(self.canvas_freq_resp)

        # generates phase response on bottom right corner of response frame
        self.canvas_phase_resp = PlottingCanvas(
            self.master, self.presenter, grid_row=2, grid_column=3, span=self.span
        )

        self.plots_2_display.append(self.canvas_phase_resp)

        refresh_visual_filter_frame(filter_frame=self)


    def __wipe_plot_frame(self) -> None:
        #not currently used, it destroys all the frames containing matplotlib objects in ResponseFrame
        plots_list = self.plots_2_display.copy()
        for plot in plots_list:
            plot.destroy()
        self.plots_2_display.clear()
        del plots_list


class PlottingCanvas(customtkinter.CTkCanvas):
    """used to create space for matplotlib plots to latch on to, 4 of these will be used throughout code"""
    def __init__(self, master, presenter, grid_row, grid_column, span) -> None:
        super().__init__(master)
        self.canvas = None
        self.presenter = presenter
        self.grid_row = grid_row
        self.grid_column = grid_column
        self.span = span
        self.__init_canvas()

    def __init_canvas(self) -> None:
        self.grid(
            row=self.grid_row,
            column=self.grid_column,
            rowspan=self.span,
            columnspan=self.span,
            sticky="nsew",
        )




class ManualPoleNumberFrame(customtkinter.CTkScrollableFrame):
    # list below stores ctkentry objects which are containers for numbers (real and imaginary part separately).
    # when we need to clear screen, all members of this list will be destroyed (destroy is how tkinter objects are deleted)
    poles_2_display = []

    def __init__(self, master, presenter: Presenter) -> None:
        super().__init__(master, label_text="Poles [Real, Imaginary, Fach]")
        # self.place(x=0, y=0, relwidth=0.15, relheight=1)
        self.presenter = presenter
        self.__init_pole_frame()

    def __init_pole_frame(self) -> None:
        self.grid(row=0, column=5, sticky="nsew")
        self.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.grid_manual_pole_entries()

    def grid_manual_pole_entries(self) -> None:
        for i,pole in enumerate(self.presenter.model.poles.keys()):
            entry_re = customtkinter.CTkEntry(self, placeholder_text=f"{np.real(pole)}",placeholder_text_color='white')
            entry_re.grid(row=i, column=0, padx=10, pady=(0, 20))
            entry_im = customtkinter.CTkEntry(self, placeholder_text=f"{np.imag(pole)}",placeholder_text_color='white')
            entry_im.grid(row=i, column=2, padx=10, pady=(0, 20))
            entry_fach = customtkinter.CTkEntry(self, placeholder_text=f"{self.presenter.model.poles[pole]}",placeholder_text_color='white')
            entry_fach.grid(row=i, column=4, padx=10, pady=(0, 20))
            self.poles_2_display.append([entry_re, entry_im,entry_fach])# members are tkinter objects not numbers

        'below leaving 3 empty place holders for user to enter poles manually'
        for i in range(
            len(self.presenter.model.poles.keys()), len(self.presenter.model.poles.keys()) + 3
        ):
            entry_re = customtkinter.CTkEntry(self, placeholder_text="real")
            entry_re.grid(row=i, column=0, padx=10, pady=(0, 20))
            entry_im = customtkinter.CTkEntry(self, placeholder_text="imaginary")
            entry_im.grid(row=i, column=2, padx=10, pady=(0, 20))
            entry_fach = customtkinter.CTkEntry(self, placeholder_text="fach")
            entry_fach.grid(row=i, column=4, padx=10, pady=(0, 20))
            self.poles_2_display.append([entry_re, entry_im,entry_fach])# empty placeholders are also objects that are saved for reference

    def wipe_manual_pole_entries(self) -> None:
        copy_list = self.poles_2_display.copy()
        for pole_display_entry in copy_list:
            for pole_section in pole_display_entry:
                pole_section.destroy()
        self.poles_2_display.clear()


class ManualZeroNumberFrame(customtkinter.CTkScrollableFrame):
    # list below stores ctkentry objects which are containers for numbers (real and imaginary part separately).
    # when we need to clear screen, all members of this list will be destroyed (destroy is how tkinter objects are deleted)
    zeros_2_display = []
    def __init__(self, master, presenter: Presenter) -> None:
        super().__init__(master, label_text="Zeros [Real, Imaginary, Fach]")
        self.presenter = presenter
        self.__init_zero_frame()

    def __init_zero_frame(self) -> None:
        self.grid(row=2, column=5, sticky="nsew")
        self.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.grid_manual_zero_entries()

    def grid_manual_zero_entries(self) -> None:
        for i,zero in enumerate(self.presenter.model.zeros.keys()):
            entry_re = customtkinter.CTkEntry(self, placeholder_text=f"{np.real(zero)}",placeholder_text_color='white')
            entry_re.grid(row=i, column=0, padx=10, pady=(0, 20))
            entry_im = customtkinter.CTkEntry(self, placeholder_text=f"{np.imag(zero)}",placeholder_text_color='white')
            entry_im.grid(row=i, column=2, padx=10, pady=(0, 20))
            entry_fach = customtkinter.CTkEntry(self, placeholder_text=f"{self.presenter.model.zeros[zero]}",placeholder_text_color='white')
            entry_fach.grid(row=i, column=4, padx=10, pady=(0, 20))
            self.zeros_2_display.append([entry_re, entry_im,entry_fach]) # members are tkinter objects not numbers
        'below leaving 3 empty place holders for user to enter zeros manually'
        for i in range(
            len(self.presenter.model.zeros.keys()), len(self.presenter.model.zeros.keys()) + 3
        ):
            entry_re = customtkinter.CTkEntry(self, placeholder_text="real")
            entry_re.grid(row=i, column=0, padx=10, pady=(0, 20))
            entry_im = customtkinter.CTkEntry(self, placeholder_text="imaginary")
            entry_im.grid(row=i, column=2, padx=10, pady=(0, 20))
            entry_fach = customtkinter.CTkEntry(self, placeholder_text="fach")
            entry_fach.grid(row=i, column=4, padx=10, pady=(0, 20))
            self.zeros_2_display.append([entry_re, entry_im,entry_fach]) # empty placeholders are also objects that are saved here for reference

    def wipe_manual_zero_entries(self) -> None:
        copy_list = self.zeros_2_display.copy()
        for zero_display_entry in copy_list:
            for zero_section in zero_display_entry:
                zero_section.destroy()

        self.zeros_2_display.clear()


def display_canvas_plot(plotting_canvas: PlottingCanvas, plotting_func: Callable) -> None:
    if plotting_canvas.canvas:
        plotting_canvas.canvas.get_tk_widget().destroy()
    fig, ax = plotting_func()
    plotting_canvas.canvas = FigureCanvasTkAgg(fig, plotting_canvas)
    plotting_canvas.canvas.get_tk_widget().grid(sticky="nsew")


def update_canvas_partial_function_plotters(filter_frame: FilterVisualFrame) -> dict[PlottingCanvas,Callable]:
    frame = filter_frame
    canvas_2_partial_func_plotter_map = {
        frame.canvas_freq_domain: partial(utilities.create_freq_domain_plot, frame.presenter.model),
        frame.canvas_time_domain: partial(utilities.create_time_plot, frame.presenter.model),
        frame.canvas_freq_resp: partial(utilities.create_freq_resp_plot, frame.presenter.model),
        frame.canvas_phase_resp: partial(utilities.create_phase_resp_plot, frame.presenter.model)
        }

    return canvas_2_partial_func_plotter_map


def refresh_visual_filter_frame(filter_frame: FilterVisualFrame) -> None:
    # first refresh the partial functions for each canvas, then plot
    canvas_2_partial_func_plotter_map = update_canvas_partial_function_plotters(filter_frame=filter_frame)
    plt.close("all")
    for canvas,partial_func in canvas_2_partial_func_plotter_map.items():
        display_canvas_plot(plotting_canvas=canvas,plotting_func=partial_func)
    gc.collect()


