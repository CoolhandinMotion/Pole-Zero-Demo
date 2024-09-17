import matplotlib.pyplot as plt
import numpy as np
from model import Model, STRING_2_MODELTYPE, STRING_2_FILTERTYPE
from view import App, get_initial_ui_values
from customtkinter import CTkEntry
from enum import Enum,auto
# print(pole_zero_entry._placeholder_text)

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

def handle_manual_entry(entry: list[CTkEntry,CTkEntry,CTkEntry]):
    field_re_new = entry[0].get()
    field_img_new = entry[1].get()
    field_fach_new = entry[2].get()

    field_re_old = entry[0]._placeholder_text
    field_img_old = entry[1]._placeholder_text
    field_fach_old = entry[2]._placeholder_text

    if not any([field_re_new,field_img_new,field_fach_new]):
        #means the entry field was left unfilled, no info was typed in, so we move on
        return EntryOperation.IGNORE
    #below are conditions were at least one entry was provided by the user

    real = read_proper_number(field_re_new)
    imaginary = read_proper_number(field_img_new)
    fach = read_proper_number(field_fach_new)
    #TODO: throw erros if ubstable poles are given
    'addition of new pole/zero'
    if all([field_re_old.isalpha(),field_img_old.isalpha(),field_fach_old.isalpha()]):
        #a new entry that needs to be recorded.it means that there was only plain text placeholder before
        #we can only record new pole/zero if real and imaginary parts are given, no default value for real and imaginary provided by software
        if real and imaginary: #user gave proper inputs, if fach was not provided, default to one
            if isinstance(fach,int):
                if fach > 0:
                    return EntryOperation.ADDITION
            elif field_fach_new == "":
                return EntryOperation.ADDITION
    else:
        #there were numbers written as placeholder, it is either modification or deletion
        if fach ==0:
            return EntryOperation.DELETION
        elif any([real,imaginary]):
            return EntryOperation.MODIFICATION #if user wants to change the coordinate, we modify. if wrong fach is also given, we ignore that part later
        elif fach: # if user explicitly changes fach only, it needs to be strictly checked
            if isinstance(fach,int):
                if fach>0:
                    return EntryOperation.MODIFICATION

    return EntryOperation.IGNORE


class Presenter:
    def __init__(self, model: Model, app: App) -> None:
        self.model = model
        self.app = app

    def change_default_model(self, variable):
        model_type_str = self.app.side_frame.optionmenu_model.get()
        filter_type_str = self.app.side_frame.optionmenu_filter.get()

        next_model_type = STRING_2_MODELTYPE[model_type_str]
        next_filter_type = STRING_2_FILTERTYPE[filter_type_str]
        "Nader thinks code below is redundant. Except maybe for resetting default factory values "
        self.model = Model()
        self.model.init_default_model(type=next_model_type, filter=next_filter_type)
        plt.close("all")
        try:
            self.app.zero_frame.wipe_zero_display()
            self.app.pole_frame.wipe_pole_display()
        except Exception:
            TODO: "Throw proper Error"
        self.app.response_plot_frame.refresh_plot_frame()
        self.app.pole_frame.display_poles()
        self.app.zero_frame.display_zeros()

    def handle_manual_coordinates(self):
        for re_zero_entry, im_zero_entry,fach_zero_entry in self.app.zero_frame.zeros_2_display:
            if re_zero_entry.get() and im_zero_entry.get():
                complex_num = complex(
                    float(re_zero_entry.get()), float(im_zero_entry.get())
                )
                conj_num = np.conj(complex_num)
                fach = fach_zero_entry.get()
                try: #default fach value is 1 if user makes a mistake
                    fach = float(fach)
                    fach = 1 if fach < 0 else int(fach)
                except ValueError:
                    fach = 1

                if fach == 0:
                    "delete the zero altogether, use continue keyword"
                    "the zeros_2_display is not updated"
                    self.model.zeros.pop(complex_num,None)
                    self.model.zeros.pop(conj_num,None)
                # If the zero is real there is no need to append conjugate value
                if complex_num == conj_num:
                    self.model.zeros[complex_num] +=fach
                else:
                    self.model.zeros[complex_num] +=fach
                    self.model.zeros[conj_num] += fach

        for re_pole_entry, im_pole_entry,fach_pole_entry in self.app.pole_frame.poles_2_display:
            if re_pole_entry.get() and im_pole_entry.get():

                complex_num = complex(
                    float(re_pole_entry.get()), float(im_pole_entry.get())
                )
                conj_num = np.conj(complex_num)
                fach = fach_pole_entry.get()
                try:#default fach value is 1 if user makes a mistake
                    fach = float(fach)
                    fach = 1 if fach < 0 else int(fach)
                except ValueError:
                    fach = 1
                if fach == 0:
                    "delete the zero altogether, use continue keyword"
                    "the poles_2_display is not updated"
                    self.model.poles.pop(complex_num,None)
                    self.model.poles.pop(conj_num,None)
                # If the pole is real there is no need to append conjugate value
                if complex_num == conj_num:
                    self.model.poles[complex_num] +=fach
                else:
                    self.model.poles[complex_num] += fach
                    self.model.poles[conj_num] += fach

    def change_manual_model(self):
        self.handle_manual_coordinates()
        self.model.update_num_denom()
        self.model.update_freq_resp()
        self.app.zero_frame.wipe_zero_display()
        self.app.pole_frame.wipe_pole_display()
        plt.close("all")
        self.app.response_plot_frame.refresh_plot_frame()
        self.app.pole_frame.display_poles()
        self.app.zero_frame.display_zeros()

    def run(self):
        initial_model_type, initial_filter_type = get_initial_ui_values()
        type = STRING_2_MODELTYPE[initial_model_type]
        filter = STRING_2_FILTERTYPE[initial_filter_type]

        self.model.init_default_model(type=type, filter=filter)
        self.app.init_ui(self)
        self.app.mainloop()
