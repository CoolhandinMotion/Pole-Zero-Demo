import matplotlib.pyplot as plt
import numpy as np
from model import Model, STRING_2_MODELTYPE, STRING_2_FILTERTYPE
from view import App, get_initial_ui_values


class Presenter:

    def __init__(self, model: Model, app: App) -> None:
        self.model = model
        self.app = app

    def change_default_model(self, variable):

        model_type_str = self.app.side_frame.optionmenu_model.get()
        filter_type_str = self.app.side_frame.optionmenu_filter.get()

        next_model_type = STRING_2_MODELTYPE[model_type_str]
        next_filter_type = STRING_2_FILTERTYPE[filter_type_str]

        self.model = Model()
        self.model.init_default_model(type=next_model_type, filter=next_filter_type)
        plt.close('all')
        try:
            self.app.zero_frame.wipe_zero_display()
            self.app.pole_frame.wipe_pole_display()
        except Exception:
            TODO: "Throw proper Error"
        self.app.response_plot_frame.init_plot_frame()
        self.app.pole_frame.display_poles()
        self.app.zero_frame.display_zeros()
        # print(self.model)

    def handle_manual_coordinates(self):
        for re_zero_entry, im_zero_entry in self.app.zero_frame.zeros_2_display:
            if re_zero_entry.get() and im_zero_entry.get():
                complex_num = np.complex(float(re_zero_entry.get()), float(im_zero_entry.get()))
                conj_num = np.conj(complex_num)
                # If the pole is real there is no need to append conjugate value
                if complex_num == conj_num:
                    self.model.zeros.append(complex_num)
                else:
                    self.model.zeros.append(complex_num)
                    self.model.zeros.append(conj_num)

        for re_pole_entry, im_pole_entry in self.app.pole_frame.poles_2_display:
            if re_pole_entry.get() and im_pole_entry.get():
                complex_num = np.complex(float(re_pole_entry.get()), float(im_pole_entry.get()))
                conj_num = np.conj(complex_num)
                # If the pole is real there is no need to append conjugate value
                if complex_num == conj_num:
                    self.model.poles.append(complex_num)
                else:
                    self.model.poles.append(complex_num)
                    self.model.poles.append(conj_num)



    def change_manual_model(self):
        self.handle_manual_coordinates()
        self.model.update_num_denom()
        self.model.update_freq_resp()
        self.app.zero_frame.wipe_zero_display()
        self.app.pole_frame.wipe_pole_display()
        plt.close('all')
        self.app.response_plot_frame.init_plot_frame()
        self.app.pole_frame.display_poles()
        self.app.zero_frame.display_zeros()

    def run(self):
        initial_model_type, initial_filter_type = get_initial_ui_values()
        type = STRING_2_MODELTYPE[initial_model_type]
        filter = STRING_2_FILTERTYPE[initial_filter_type]

        self.model.init_default_model(type=type, filter=filter)
        self.app.init_ui(self)
        self.app.mainloop()
