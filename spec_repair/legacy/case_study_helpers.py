import os
import re


def print_dict(dict):
    for key in dict.keys():
        print(key + "\t:\t" + dict.get(key))


def dict_to_text(dict):
    output = ""
    for key in dict.keys():
        output += key + "\t:\t" + dict.get(key) + "\n"
    return output


def get_folders(folder, exclusions=[]):
    files = [os.path.join(folder, x) for x in os.listdir(folder) if x not in exclusions]
    folders = [x for x in files if os.path.isdir(x)]
    return folders


def get_name(filename):
    path = filename.split("/")
    name = path[len(path) - 2]
    name = re.sub(r"\s", r"_", name)
    return name.title()


CASE_STUDY_EXCLUSION_LIST = ['acheivepattern',
                             'atm',
                             'detector',
                             'lily01',
                             'lily02',
                             'lily11',
                             'lily15',
                             'lily16',
                             'ltl2dba_R_2',
                             'ltl2dba_theta_2',
                             'ltl2dba27',
                             'prioritizedArbiter',
                             'retractionPattern2',
                             'tcp',
                             'telephone']

CASE_STUDY_FINALS = {  # "../Translators/input-files/examples/Arbiter/Arbiter_FINAL.spectra",
        "Lift": "../Translators/input-files/examples/lift_FINAL.spectra",
        "Lift New": "../Translators/input-files/examples/lift_FINAL_NEW.spectra",
        "Minepump": "../Translators/input-files/case-studies/modified-specs/minepump/genuine/minepump_FINAL.spectra",
        "Traffic Single": "../Translators/input-files/examples/Traffic/traffic_single_FINAL.spectra",
        "Traffic": "../Translators/input-files/examples/Traffic/traffic_updated_FINAL.spectra"}
