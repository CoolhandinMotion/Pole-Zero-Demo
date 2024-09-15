from enum import Enum, auto
from dataclasses import dataclass, field
import json
import numpy as np
from scipy.signal import freqz, freqs, zpk2tf
from collections import defaultdict
from utilities import build_repeated_item_list_from_dict



class FilterType(Enum):
    MANUAL = auto()
    TP = auto()
    HP = auto()
    BP = auto()
    BS = auto()
    AP = auto()


class ModelType(Enum):
    DIGITAL = auto()
    ANALOG = auto()


@dataclass
class Model:
    type: ModelType = field(init=False)
    filter: FilterType = field(init=False)
    poles: dict = field(init=False, default_factory=dict)
    zeros: dict = field(init=False, default_factory=dict)
    freqs: list = field(init=False, repr=False, default_factory=list)
    complex_f_resp: list = field(init=False, repr=False, default_factory=list)
    num: list = field(init=False, repr=False, default_factory=list)
    denom: list = field(init=False, repr=False, default_factory=list)

    def init_default_model(self, type: ModelType, filter: FilterType) -> None:
        self.type = type
        self.filter = filter
        self.poles, self.zeros = get_default_poles_zeros(
            type_str=self.type.name, filter_str=self.filter.name
        )
        self.update_num_denom()
        self.update_freq_resp()

    def update_num_denom(self) -> None:
        repeated_zeros_list = build_repeated_item_list_from_dict(self.zeros)
        repeated_poles_list = build_repeated_item_list_from_dict(self.poles)
        self.num, self.denom = zpk2tf(repeated_zeros_list, repeated_poles_list, 1)

    def update_freq_resp(self) -> None:
        if self.type == ModelType.DIGITAL:
            self.freqs, self.complex_f_resp = freqz(self.num, self.denom, worN=10000)
        elif self.type == ModelType.ANALOG:
            self.freqs, self.complex_f_resp = freqs(self.num, self.denom, worN=1000)


# the reason for ModelType.name and FilterType.name is that only string is json serializable so convertion is necessary
# to load the setting from config.json file


def get_default_poles_zeros(type_str: str, filter_str: str):
    complex_poles_dict = defaultdict(int)
    complex_zeros_dict = defaultdict(int)
    with open("config.json", "r") as file:
        cfg = json.load(file)
        model_cfg = cfg[type_str]
        filter_cfg = model_cfg[filter_str]
        # we know beforehand that json file contains at most one complex number for each filter for pole or zero
        # for loading default settings, each pole or zero is constructed by calling the complex_number_from_list()
        # exactly once
        if filter_cfg["poles"]:
            for pole in filter_cfg["poles"]:
                complex_num = complex_number_from_list(pole)
                conj_num = np.conj(complex_num)
                # If the pole is real there is no need to append conjugate value
                if complex_num == conj_num:
                    # complex_poles_list.append(complex_num)
                    complex_poles_dict[complex_num] +=1
                else:
                    # complex_poles_list.append(complex_num)
                    complex_poles_dict[complex_num] += 1
                    # complex_poles_list.append(conj_num)
                    complex_poles_dict[conj_num] += 1

        # The reason for this if statement is that some default filters do not have any poles or zeros
        # therefore in json file there is actually None value corresponding to some poles or zeros
        if filter_cfg["zeros"]:
            for zero in filter_cfg["zeros"]:
                complex_num = complex_number_from_list(zero)
                conj_num = np.conj(complex_num)
                if complex_num == conj_num:
                    # complex_zeros_list.append(complex_num)
                    complex_zeros_dict[complex_num] +=1
                else:
                    # complex_zeros_list.append(complex_num)
                    complex_zeros_dict[complex_num] += 1
                    # complex_zeros_list.append(conj_num)
                    complex_zeros_dict[conj_num] += 1
    return complex_poles_dict, complex_zeros_dict


# Here I assume 2 poles or zeros would be a 2*2 list
# conjugates are not accounted for in the list, they will be generated automatically
# so a real system with 4 conjugate poles would be saved in config file as a  2*2 list of float
def complex_number_from_list(num_list):
    assert len(num_list) == 2, "Complex number not in right format"
    return complex(num_list[0], num_list[1])


STRING_2_MODELTYPE = {"Analog": ModelType.ANALOG, "Digital": ModelType.DIGITAL}

STRING_2_FILTERTYPE = {
    "Tief pass": FilterType.TP,
    "Hoch pass": FilterType.HP,
    "Band pass": FilterType.BP,
    "Band stop": FilterType.BS,
    "All pass": FilterType.AP,
    "Manual": FilterType.MANUAL,
}
