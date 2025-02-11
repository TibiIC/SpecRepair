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


def print_trivial_results(spec_directory_path: str):
    spec_abs_paths = glob.glob(os.path.join(spec_directory_path, '*.spectra'))
    spec_abs_paths = [os.path.abspath(file_path) for file_path in spec_abs_paths]

    specs: Dict[str, Spec] = {}
    for spec_abs_path in spec_abs_paths:
        spec_name: str = os.path.splitext(os.path.basename(spec_abs_path))[0]
        spec_txt: str = read_file(spec_abs_path)
        spec: Spec = Spec(spec_txt)
        specs[spec_name] = spec

    trivial_true_asms = set()
    trivial_false_asms = set()
    trivial_true_gars = set()
    trivial_false_gars = set()

    trivial_true_asms_no_initial = set()
    trivial_false_asms_no_initial = set()
    trivial_true_gars_no_initial = set()
    trivial_false_gars_no_initial = set()

    for spec_name, spec in specs.items():
        if spec.is_trivial_true(GR1FormulaType.ASM):
            trivial_true_asms.add(spec_name)
        if spec.is_trivial_false(GR1FormulaType.ASM):
            trivial_false_asms.add(spec_name)
        if spec.is_trivial_true(GR1FormulaType.GAR):
            trivial_true_gars.add(spec_name)
        if spec.is_trivial_false(GR1FormulaType.GAR):
            trivial_false_gars.add(spec_name)

        if spec.is_trivial_true(GR1FormulaType.ASM, ignore_initial=True):
            trivial_true_asms_no_initial.add(spec_name)
        if spec.is_trivial_false(GR1FormulaType.ASM, ignore_initial=True):
            trivial_false_asms_no_initial.add(spec_name)
        if spec.is_trivial_true(GR1FormulaType.GAR, ignore_initial=True):
            trivial_true_gars_no_initial.add(spec_name)
        if spec.is_trivial_false(GR1FormulaType.GAR, ignore_initial=True):
            trivial_false_gars_no_initial.add(spec_name)

    print(f"TOTAL SPECS: {len(specs)}")
    print(f"==============================================")
    print(f"Trivial False Assumptions False Guarantees: {len(trivial_false_asms & trivial_false_gars)}")
    print(f"Trivial False Assumptions True Guarantees: {len(trivial_false_asms & trivial_true_gars)}")
    print(f"Trivial True Assumptions False Guarantees: {len(trivial_true_asms & trivial_false_gars)}")
    print(f"Trivial True Assumptions True Guarantees: {len(trivial_true_asms & trivial_true_gars)}")
    print(f"Trivial False Assumptions Only: {len(trivial_false_asms)}")
    print(f"Trivial True Assumptions Only: {len(trivial_true_asms)}")
    print(f"Trivial False Guarantees Only: {len(trivial_false_gars)}")
    print(f"Trivial True Guarantees Only: {len(trivial_true_gars)}")
    print(f"Neither Trivial Assumptions nor Guarantees: {len(specs) - len(trivial_false_asms | trivial_true_asms | trivial_false_gars | trivial_true_gars)}")
    print(f"==============================================")
    print(f"Trivial False Assumptions False Guarantees: {len(trivial_false_asms_no_initial & trivial_false_gars_no_initial)}")
    print(f"Trivial False Assumptions True Guarantees: {len(trivial_false_asms_no_initial & trivial_true_gars_no_initial)}")
    print(f"Trivial True Assumptions False Guarantees: {len(trivial_true_asms_no_initial & trivial_false_gars_no_initial)}")
    print(f"Trivial True Assumptions True Guarantees: {len(trivial_true_asms_no_initial & trivial_true_gars_no_initial)}")
    print(f"Trivial False Assumptions Only: {len(trivial_false_asms_no_initial)}")
    print(f"Trivial True Assumptions Only: {len(trivial_true_asms_no_initial)}")
    print(f"Trivial False Guarantees Only: {len(trivial_false_gars_no_initial)}")
    print(f"Trivial True Guarantees Only: {len(trivial_true_gars_no_initial)}")
    print(f"Neither Trivial Assumptions nor Guarantees: {len(specs) - len(trivial_false_asms_no_initial | trivial_true_asms_no_initial | trivial_false_gars_no_initial | trivial_true_gars_no_initial)}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-s', '--spec_dir', type=str,
                        required=True,
                        help='Path to the directory with specifications to be compared. All files should be named [a-zA-Z0-9_.-]+\.spectra')
    args = parser.parse_args()

    current_directory = os.getcwd()
    spec_directory_path = os.path.join(current_directory, args.spec_dir)

    print_trivial_results(spec_directory_path)
