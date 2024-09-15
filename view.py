from dataclasses import dataclass

import customtkinter
import tkinter as tk
from typing import Protocol

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import utilities
from functools import partial

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
    return model_menu_values[0], filter_menu_values[0]


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


class App(customtkinter.CTk):
    def __init__(self) -> None:
        super().__init__()
        # configure window
        self.response_plot_frame = None
        self.side_frame = None
        self.pole_frame = None
        self.zero_frame = None
        self.title("Digital Signal Processing Demo")
        self.geometry(f"{app_geometry[0]}x{app_geometry[0]}")
        self.minsize(*app_geometry)

    def init_ui(self, presenter: Presenter) -> None:
        self.grid_columnconfigure(tuple(range(11)), weight=1)
        self.grid_rowconfigure(tuple(range(11)), weight=1)
        'side_frame hosts different settings that user can choose'
        self.side_frame = SideFrame(self, presenter)
        # self.plot_frame = PlotFrame(self, presenter)
        'The ResponsePlotFrame itself consists of 4 different canvas that host different plots'
        self.response_plot_frame = ResponsePlotFrame(self, presenter, 1)
        'pole_frame is a place where user can add manual poles to the filter'
        self.pole_frame = ManualPoleFrame(self, presenter)
        'zero_frame is a place where user can add manual zeros to the filter'
        self.zero_frame = ManualZeroFrame(self, presenter)

        'Below we define buttons that do not belong to any frame but necessary for functionality of the whole program'
        'button below is the confirmation button that users clicks on to confirm addition of new poles or zeros'
        self.manual_pole_zero_button = customtkinter.CTkButton(
            master=self, text="Eingeben", command=presenter.change_manual_model
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

        value_inside = tk.StringVar()
        value_inside.set(model_menu_values[0])

        self.optionmenu_model = customtkinter.CTkOptionMenu(
            self,
            dynamic_resizing=False,
            variable=value_inside,
            values=model_menu_values,
            command=self.presenter.change_default_model,
        )
        self.optionmenu_model.grid(row=1, column=0, padx=10, pady=20, sticky="n")

        value_inside = tk.StringVar()
        value_inside.set(filter_menu_values[0])
        self.optionmenu_filter = customtkinter.CTkOptionMenu(
            self,
            dynamic_resizing=False,
            variable=value_inside,
            values=filter_menu_values,
            command=self.presenter.change_default_model,
        )

        self.optionmenu_filter.grid(row=2, column=0, padx=10, pady=10, sticky="n")


class ResponsePlotFrame:
    plots_2_display = []

    def __init__(self, master, presenter: Presenter, span) -> None:
        self.master = master
        self.presenter = presenter
        self.span = span
        self.refresh_plot_frame()

    def refresh_plot_frame(self) -> None:
        self.__wipe_plot_frame()

        # generates pole zero map on top left corner of response frame
        self.canvas1 = EmptyCanvas(
            self.master, self.presenter, grid_row=0, grid_column=1, span=self.span
        )
        self.plots_2_display.append(self.canvas1)

        # generates time response on bottom left corner of response frame
        self.canvas2 = EmptyCanvas(
            self.master, self.presenter, grid_row=2, grid_column=1, span=self.span
        )
        self.plots_2_display.append(self.canvas2)

        # generates frequency on top right corner of response frame
        self.canvas3 = EmptyCanvas(
            self.master, self.presenter, grid_row=0, grid_column=3, span=self.span
        )
        self.plots_2_display.append(self.canvas3)

        # generates phase response on bottom right corner of response frame
        self.canvas4 = EmptyCanvas(
            self.master, self.presenter, grid_row=2, grid_column=3, span=self.span
        )
        self.plots_2_display.append(self.canvas4)

        self.update_plot()

    def update_plot(self) -> None:
        # temporary partial function that when executes, generates proper pole zero map
        my_func = partial(utilities.create_freq_domain_plot, self.presenter.model)
        self.canvas1.canvas_shw_func(my_func)

        # temporary partial function that when executes, generates proper time response
        my_func = partial(utilities.create_time_plot, self.presenter.model)
        self.canvas2.canvas_shw_func(my_func)

        # temporary partial function that when executes, generates proper frequency response plot
        my_func = partial(utilities.create_freq_resp_plot, self.presenter.model)
        self.canvas3.canvas_shw_func(my_func)

        # temporary partial function that when executes, generates proper phase response
        my_func = partial(utilities.create_phase_resp_plot, self.presenter.model)
        self.canvas4.canvas_shw_func(my_func)

    def __wipe_plot_frame(self) -> None:
        plots_list = self.plots_2_display.copy()
        for plot in plots_list:
            plot.destroy()
        self.plots_2_display.clear()
        del plots_list


class EmptyCanvas(customtkinter.CTkCanvas):
    canvases_2_display = []

    def __init__(self, master, presenter, grid_row, grid_column, span) -> None:
        super().__init__(master)
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

    def canvas_shw_func(self, func) -> None:
        fig, ax = func()
        self.canvas = FigureCanvasTkAgg(fig, self)
        self.canvas.get_tk_widget().grid(sticky="nsew")


class ManualPoleFrame(customtkinter.CTkScrollableFrame):
    # list below stores ctkentry objects which are containers for numbers (real and imaginary part separately).
    # when we need to clear screen, all members of this list will be destroyed (destroy is how tkinter objects are deleted)
    poles_2_display = []

    def __init__(self, master, presenter: Presenter) -> None:
        super().__init__(master, label_text="Poles [Real, Imaginary]")
        # self.place(x=0, y=0, relwidth=0.15, relheight=1)
        self.presenter = presenter
        # self.pole_frame_values =
        self.__init_pole_frame()

    def __init_pole_frame(self) -> None:
        self.grid(row=0, column=5, sticky="nsew")
        self.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.display_poles()

    def display_poles(self) -> None:
        for i,pole in enumerate(self.presenter.model.poles.keys()):
            entry_re = customtkinter.CTkEntry(self, placeholder_text=f"{np.real(pole)}")
            entry_re.grid(row=i, column=1, padx=10, pady=(0, 20))
            entry_im = customtkinter.CTkEntry(self, placeholder_text=f"{np.imag(pole)}")
            entry_im.grid(row=i, column=3, padx=10, pady=(0, 20))
            self.poles_2_display.append([entry_re, entry_im])# members are tkinter objects not numbers

        # for i in range(len(self.presenter.model.poles)):
        #     entry_re = customtkinter.CTkEntry(
        #         self, placeholder_text=f"{np.real(self.presenter.model.poles[i])}"
        #     )
        #     entry_re.grid(row=i, column=1, padx=10, pady=(0, 20))
        #     entry_im = customtkinter.CTkEntry(
        #         self, placeholder_text=f"{np.imag(self.presenter.model.poles[i])}"
        #     )
        #     entry_im.grid(row=i, column=3, padx=10, pady=(0, 20))
        #     self.poles_2_display.append([entry_re, entry_im])# members are tkinter objects not numbers

        'below leaving 3 empty place holders for user to enter poles manually'
        for i in range(
            len(self.presenter.model.poles.keys()), len(self.presenter.model.poles.keys()) + 3
        ):
            entry_re = customtkinter.CTkEntry(self, placeholder_text="leer")
            entry_re.grid(row=i, column=1, padx=10, pady=(0, 20))
            entry_im = customtkinter.CTkEntry(self, placeholder_text="leer")
            entry_im.grid(row=i, column=3, padx=10, pady=(0, 20))
            self.poles_2_display.append([entry_re, entry_im])# empty placeholders are also objects that are saved for reference

    def wipe_pole_display(self) -> None:
        copy_list = self.poles_2_display.copy()
        for re_disp, im_disp in copy_list:
            re_disp.destroy()
            im_disp.destroy()

        self.poles_2_display.clear()


class ManualZeroFrame(customtkinter.CTkScrollableFrame):
    # list below stores ctkentry objects which are containers for numbers (real and imaginary part separately).
    # when we need to clear screen, all members of this list will be destroyed (destroy is how tkinter objects are deleted)
    zeros_2_display = []
    def __init__(self, master, presenter: Presenter) -> None:
        super().__init__(master, label_text="Zeros [Real, Imaginary]")
        self.presenter = presenter
        self.__init_zero_frame()

    def __init_zero_frame(self) -> None:
        self.grid(row=2, column=5, sticky="nsew")
        self.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.display_zeros()

    def display_zeros(self) -> None:
        for i,zero in enumerate(self.presenter.model.zeros.keys()):
            entry_re = customtkinter.CTkEntry(self, placeholder_text=f"{np.real(zero)}")
            entry_re.grid(row=i, column=1, padx=10, pady=(0, 20))
            entry_im = customtkinter.CTkEntry(self, placeholder_text=f"{np.imag(zero)}")
            entry_im.grid(row=i, column=3, padx=10, pady=(0, 20))
            self.zeros_2_display.append([entry_re, entry_im]) # members are tkinter objects not numbers
        #
        # for i in range(len(self.presenter.model.zeros)):
        #     entry_re = customtkinter.CTkEntry(
        #         self, placeholder_text=f"{np.real(self.presenter.model.zeros[i])}"
        #     )
        #     entry_re.grid(row=i, column=1, padx=10, pady=(0, 20))
        #     entry_im = customtkinter.CTkEntry(
        #         self, placeholder_text=f"{np.imag(self.presenter.model.zeros[i])}"
        #     )
        #     entry_im.grid(row=i, column=3, padx=10, pady=(0, 20))
        #     self.zeros_2_display.append([entry_re, entry_im]) # members are tkinter objects not numbers
        'below leaving 3 empty place holders for user to enter zeros manually'
        for i in range(
            len(self.presenter.model.zeros.keys()), len(self.presenter.model.zeros.keys()) + 3
        ):
            entry_re = customtkinter.CTkEntry(self, placeholder_text="leer")
            entry_re.grid(row=i, column=1, padx=10, pady=(0, 20))
            entry_im = customtkinter.CTkEntry(self, placeholder_text="leer")
            entry_im.grid(row=i, column=3, padx=10, pady=(0, 20))
            self.zeros_2_display.append([entry_re, entry_im]) # empty placeholders are also objects that are saved here for reference

    def wipe_zero_display(self) -> None:
        copy_list = self.zeros_2_display.copy()
        for re_disp, im_disp in copy_list:
            re_disp.destroy()
            im_disp.destroy()

        self.zeros_2_display.clear()
