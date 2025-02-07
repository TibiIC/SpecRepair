import argparse
import glob
import os
from typing import Dict, Optional

from spot import formula, formulaiterator

from spec_repair.ltl_types import GR1FormulaType
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
    formula_type: Optional[GR1FormulaType] = GR1FormulaType.GAR
    for spec_name, spec in specs.items():
        weaker = ideal_spec.implies(spec, formula_type)
        stronger = spec.implies(ideal_spec, formula_type)
        if weaker and stronger:
            identical_specs.append(spec_name)
        elif weaker:
            weaker_specs.append(spec_name)
        elif stronger:
            stronger_specs.append(spec_name)
        else:
            logically_unrelated_specs.append(spec_name)

    print(f"Identical specifications: {len(identical_specs)}")
    for identical_spec in sorted(identical_specs):
        print(f"\t* {identical_spec}")
    print(f"Specifications weaker than the ideal specification: {len(weaker_specs)}")
    for weaker_spec in sorted(weaker_specs):
        print(f"\t* {weaker_spec}")
    print(f"Specifications stronger than the ideal specification: {len(stronger_specs)}")
    for stronger_spec in sorted(stronger_specs):
        print(f"\t* {stronger_spec}")
    print(f"Specifications logically unrelated to the ideal specification: {len(logically_unrelated_specs)}")
    for unrelated_spec in sorted(logically_unrelated_specs):
        print(f"\t* {unrelated_spec}")


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
