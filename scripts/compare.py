import argparse
import glob
import os
from typing import Dict

from spec_repair.util.file_util import read_file

from spec_repair.wrappers.spec import Spec

description = """
Compares one specification to a set of specifications from a given directory.
"""


def print_comparison_results(ideal_spec_path: str, spec_directory_path: str):
    ideal_spec_txt: str = read_file(ideal_spec_path)
    ideal_spec: Spec = Spec(ideal_spec_txt)

    spec_abs_paths = glob.glob(os.path.join(spec_directory_path, '*.spectra'))
    spec_abs_paths = [os.path.abspath(file_path) for file_path in spec_abs_paths]

    specs: Dict[str, Spec] = {}
    for spec_abs_path in spec_abs_paths:
        spec_name: str = os.path.splitext(os.path.basename(spec_abs_path))[0]
        spec_txt: str = read_file(spec_abs_path)
        spec: Spec = Spec(spec_txt)
        specs[spec_name] = spec

    weaker_specs = []
    identical_specs = []
    stronger_specs = []
    logically_unrelated_specs = []
    for spec_name, spec in specs.items():
        weaker = ideal_spec.implies(spec, None)
        stronger = spec.implies(ideal_spec, None)
        if weaker and stronger:
            identical_specs.append(spec_name)
        elif weaker:
            weaker_specs.append(spec_name)
        elif stronger:
            stronger_specs.append(spec_name)
        else:
            logically_unrelated_specs.append(spec_name)

    print(f"Identical specifications: {sorted(identical_specs)}")
    print(f"Specifications weaker than the ideal specification: {sorted(weaker_specs)}")
    print(f"Specifications stronger than the ideal specification: {sorted(stronger_specs)}")
    print(f"Specifications logically unrelated to the ideal specification: {sorted(logically_unrelated_specs)}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-i', '--ideal_spec', type=str,
                        required=True,
                        help='Path to the initial/ideal specification to compare the rest of the specifications. The file should be named [a-zA-Z0-9_.-]+\.spectra')
    parser.add_argument('-s', '--spec_dir', type=str,
                        required=True,
                        help='Path to the directory with specifications to be compared. All files should be named [a-zA-Z0-9_.-]+\.spectra')
    args = parser.parse_args()

    current_directory = os.getcwd()
    ideal_spec_path = os.path.join(current_directory, args.ideal_spec)
    spec_directory_path = os.path.join(current_directory, args.spec_dir)

    print_comparison_results(ideal_spec_path, spec_directory_path)
