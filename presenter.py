import matplotlib.pyplot as plt
import numpy as np
import utilities
import view
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import animation
from functools import partial
from model import Model, STRING_2_MODELTYPE, STRING_2_FILTERTYPE,STRING_2_TIMERESPONSE
from view import App, get_initial_ui_values
from customtkinter import CTkEntry
from enum import Enum,auto
import gc


class EntryOperation(Enum):
    ADDITION = auto()
    MODIFICATION = auto()
    DELETION = auto()
    IGNORE = auto()

def read_proper_number(number_string:str) -> float | None:
    try:
        num = float(number_string)
        return num
    except ValueError:
        return None

def get_proper_fach(fach:str) -> int|None:
    if fach == "":
        return 1
    fach = read_proper_number(fach)
    if not fach is None and fach >= 0:
            return int(fach)
    return None




def complex_and_conj_fach_dict(real:float,imaginary:float,fach:int | None) -> dict[complex,int]:
    """this function receives a real and imaginary part of a complex number, checks whether it is located on the real axis
    and returns a dictionary containing fach for complex and complex conjugate (if conjugate is different from number itself)"""

    complex_num = complex(real,imaginary)
    conj_num = np.conj(complex_num)
    if conj_num == complex_num:
        decision_dict = {complex_num: fach}
    else:
        decision_dict = {complex_num: fach, conj_num: fach}
    return decision_dict

def handle_manual_entry(entry: list[CTkEntry,CTkEntry,CTkEntry])-> tuple[EntryOperation,dict]:
    field_re_new = entry[0].get()
    field_img_new = entry[1].get()
    field_fach_new = entry[2].get()
    field_re_old = entry[0]._placeholder_text
    field_img_old = entry[1]._placeholder_text
    field_fach_old = entry[2]._placeholder_text

    if not any([field_re_new,field_img_new,field_fach_new]):
        #means the entry field was left unfilled, no info was typed in, so we move on
        return EntryOperation.IGNORE, {}
    #below are conditions were at least one entry was provided by the user

    new_real = read_proper_number(field_re_new)
    new_img = read_proper_number(field_img_new)
    fach = get_proper_fach(field_fach_new)
    #TODO: throw erros if ubstable poles are given
    'addition of new pole/zero'
    if all([field_re_old.isalpha(),field_img_old.isalpha(),field_fach_old.isalpha()]):
        #a new entry that needs to be recorded.it means that there was only plain text placeholder before
        #we can only record new pole/zero if real and imaginary parts are given, no default value for real and imaginary provided by software
        if not new_real is None  and  not new_img is None: #user gave proper inputs, if fach was not provided, default to one
            if fach and fach >0:
                addition_dict = complex_and_conj_fach_dict(real=new_real,imaginary=new_img,fach=fach)
                return EntryOperation.ADDITION,{"addition":addition_dict}

    else:
        'modification/deletion'
        #there were numbers written as placeholder, it is either modification or deletion
        if fach ==0:
            #deleting an already existing pole/zero becasue fach was set to zero
            deletion_dict = complex_and_conj_fach_dict(real=float(field_re_old),imaginary=float(field_img_old),fach=None)
            return EntryOperation.DELETION, {"deletion":deletion_dict}

        #modification means having previous values as default, if not provided by user, use default values
        new_real = new_real if not new_real is None else float(field_re_old)
        new_img = new_img if not new_img is None else float(field_img_old)
        fach = fach if fach not in [None,1] else int(field_fach_old)
        addition_dict = complex_and_conj_fach_dict(real=new_real, imaginary=new_img, fach=fach)
        deletion_dict = complex_and_conj_fach_dict(real=float(field_re_old), imaginary=float(field_img_old), fach=None)
        return EntryOperation.MODIFICATION, {"addition": addition_dict, "deletion": deletion_dict}

    return EntryOperation.IGNORE, {}


class Presenter:
    def __init__(self, model: Model, app: App) -> None:
        self.model = model
        self.app = app
        self.anime = None
    def change_time_response(self,variable):
        time_resp_str = self.app.side_frame.optionmenu_response.get()
        next_time_resp = STRING_2_TIMERESPONSE[time_resp_str]
        self.model.time_resp = next_time_resp
        view.refresh_visual_filter_frame(filter_frame=self.app.visual_filter_frame)

    def change_digital_sampling_freq(self):
        if not self.model.type.name == "DIGITAL":
            return
        sampling_freq = self.app.side_frame.open_fs_input_dialog_event()
        if sampling_freq:
            self.model.sampling_time = 1/sampling_freq
            self.change_manual_model()


    def run_animation(self):
        if self.model.type.name == "ANALOG":
            self.run_analog_animation()
        elif self.model.type.name == "DIGITAL":
            self.run_digital_animation()

    def run_analog_animation(self):
        assert self.model.type.name == "ANALOG"
        self.run_analog_pole_zero_animation()
        self.run_analog_response_animation()

    def run_digital_animation(self):
        assert self.model.type.name == "DIGITAL"
        self.run_digital_pole_zero_animation()
        self.run_digital_response_animation()

    def run_analog_response_animation(self):

        anim_canvas = self.app.visual_filter_frame.canvas_freq_resp
        if anim_canvas.canvas:
            anim_canvas.canvas.get_tk_widget().destroy()

        fig, ax, line_2d_objects = utilities.get_response_line_objects(self.model)
        anim_canvas.canvas = FigureCanvasTkAgg(fig, anim_canvas)
        anim_canvas.canvas.get_tk_widget().grid(sticky="nsew")

        partial_anim_func = partial(utilities.response_animation_func,
                                    line_2d_objects=line_2d_objects,
                                    ax=ax,
                                    canvas=anim_canvas.canvas,
                                    model=self.model)

        self.response_anime = animation.FuncAnimation(fig=fig,
                                                   func=partial_anim_func,
                                                   frames=len(self.model.freqs),
                                                   interval=10,
                                                   blit=False,
                                                   repeat=False, )

    def run_digital_response_animation(self):
        anim_canvas = self.app.visual_filter_frame.canvas_freq_resp
        if anim_canvas.canvas:
            anim_canvas.canvas.get_tk_widget().destroy()

        fig, ax, line_2d_objects = utilities.get_response_line_objects(self.model)
        anim_canvas.canvas = FigureCanvasTkAgg(fig, anim_canvas)
        anim_canvas.canvas.get_tk_widget().grid(sticky="nsew")

        partial_anim_func = partial(utilities.response_animation_func,
                                    line_2d_objects=line_2d_objects,
                                    ax=ax,
                                    canvas=anim_canvas.canvas,
                                    model=self.model)

        self.response_anime = animation.FuncAnimation(fig=fig,
                                                   func=partial_anim_func,
                                                   frames=len(self.model.freqs),
                                                   interval=10,
                                                   blit=False,
                                                   repeat=False, )


    def run_analog_pole_zero_animation(self):
        anim_canvas = self.app.visual_filter_frame.canvas_freq_domain
        if anim_canvas.canvas:
            anim_canvas.canvas.get_tk_widget().destroy()

        line_obj_dict = utilities.get_analog_pole_zero_line_objects(self.model)

        anim_canvas.canvas = FigureCanvasTkAgg(line_obj_dict["fig"], anim_canvas)
        anim_canvas.canvas.get_tk_widget().grid(sticky="nsew")


        partial_anim_func = partial(utilities.analog_pole_zero_animation_func,
                                    line_obj_dict = line_obj_dict,
                                    canvas=anim_canvas.canvas,
                                    model=self.model)
        self.anime = animation.FuncAnimation(fig=line_obj_dict["fig"],
                                                   func=partial_anim_func,
                                                   frames=len(self.model.freqs),
                                                   interval=10,
                                                   blit=False,
                                                   repeat=False, )
    def run_digital_pole_zero_animation(self):
        anim_canvas = self.app.visual_filter_frame.canvas_freq_domain
        if anim_canvas.canvas:
            anim_canvas.canvas.get_tk_widget().destroy()

        line_obj_dict = utilities.get_digital_pole_zero_line_objects(self.model)

        anim_canvas.canvas = FigureCanvasTkAgg(line_obj_dict["fig"], anim_canvas)
        anim_canvas.canvas.get_tk_widget().grid(sticky="nsew")


        partial_anim_func = partial(utilities.digital_pole_zero_animation_func,
                                    line_obj_dict = line_obj_dict,
                                    canvas=anim_canvas.canvas,
                                    model=self.model)
        self.anime = animation.FuncAnimation(fig=line_obj_dict['fig'],
                                                   func=partial_anim_func,
                                                   frames=len(self.model.freqs),
                                                   interval=10,
                                                   blit=False,
                                                   repeat=False, )


    def change_default_model(self, variable):
        model_type_str = self.app.side_frame.optionmenu_model.get()
        filter_type_str = self.app.side_frame.optionmenu_filter.get()
        time_resp_str = self.app.side_frame.optionmenu_response.get()
        next_model_type = STRING_2_MODELTYPE[model_type_str]
        next_filter_type = STRING_2_FILTERTYPE[filter_type_str]
        next_time_resp = STRING_2_TIMERESPONSE[time_resp_str]
        "Nader thinks code below is redundant. Except maybe for resetting default factory values "
        # self.model = Model()
        self.model.init_default_model(type=next_model_type, filter=next_filter_type,time_resp=next_time_resp)
        plt.close("all")
        try:
            self.app.zero_number_frame.wipe_manual_zero_entries()
            self.app.pole_number_frame.wipe_manual_pole_entries()
        except Exception:
            ...
            # "Throw proper Error"
        # self.app.visual_filter_frame.refresh_plot_frame()
        view.refresh_visual_filter_frame(filter_frame=self.app.visual_filter_frame)
        self.app.pole_number_frame.grid_manual_pole_entries()
        self.app.zero_number_frame.grid_manual_zero_entries()
        self.app.side_frame.disable_fs_button() if self.model.type.name == "ANALOG" else self.app.side_frame.enable_fs_button()

    def handle_manual_coordinates(self):
        all_zero_entries = self.app.zero_number_frame.zeros_2_display.copy()
        for i,zero_entry in enumerate(all_zero_entries):
            decision, decision_dict = handle_manual_entry(zero_entry)
            if decision == EntryOperation.DELETION:
                self.model.remove_zeros(decision_dict["deletion"].keys())
                self.app.zero_number_frame.zeros_2_display.pop(i)
            elif decision == EntryOperation.ADDITION:
                self.model.add_zeros(decision_dict["addition"])
            elif decision == EntryOperation.MODIFICATION:
                self.model.remove_zeros(decision_dict["deletion"].keys())
                self.app.zero_number_frame.zeros_2_display.pop(i)
                self.model.add_zeros(decision_dict["addition"])

        all_pole_entries = self.app.pole_number_frame.poles_2_display.copy()
        for i, pole_entry in enumerate(all_pole_entries):
            decision, decision_dict = handle_manual_entry(pole_entry)
            if decision == EntryOperation.DELETION:
                self.model.remove_poles(decision_dict["deletion"].keys())
                self.app.pole_number_frame.poles_2_display.pop(i)
            elif decision == EntryOperation.ADDITION:
                self.model.add_poles(decision_dict["addition"])
            elif decision == EntryOperation.MODIFICATION:
                self.model.remove_poles(decision_dict["deletion"].keys())
                self.app.pole_number_frame.poles_2_display.pop(i)
                self.model.add_poles(decision_dict["addition"])

        gc.collect()

    def change_manual_model(self):
        self.handle_manual_coordinates()
        self.model.update_num_denom()
        self.model.update_freq_resp()
        self.app.zero_number_frame.wipe_manual_zero_entries()
        self.app.pole_number_frame.wipe_manual_pole_entries()
        plt.close("all")
        view.refresh_visual_filter_frame(filter_frame=self.app.visual_filter_frame)
        self.app.pole_number_frame.grid_manual_pole_entries()
        self.app.zero_number_frame.grid_manual_zero_entries()

    def run(self):
        initial_model_type, initial_filter_type,initial_time_resp = get_initial_ui_values()
        type = STRING_2_MODELTYPE[initial_model_type]
        filter = STRING_2_FILTERTYPE[initial_filter_type]
        time_resp = STRING_2_TIMERESPONSE[initial_time_resp]
        self.model.init_default_model(type=type, filter=filter,time_resp=time_resp)
        self.app.init_ui(self)
        self.app.mainloop()
