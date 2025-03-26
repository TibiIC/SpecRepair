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

    print_comparison_results_one_to_many(ideal_spec, specs)


def print_comparison_results_one_to_many(ideal_spec: Spec, specs: Dict[str, Spec]):
    weaker_asms = set()
    stronger_asms = set()
    formula_type: Optional[GR1FormulaType] = GR1FormulaType.ASM
    for spec_name, spec in specs.items():
        weaker = ideal_spec.implies(spec, formula_type)
        stronger = spec.implies(ideal_spec, formula_type)
        if weaker:
            weaker_asms.add(spec_name)
        if stronger:
            stronger_asms.add(spec_name)
    weaker_gars = set()
    stronger_gars = set()
    formula_type: Optional[GR1FormulaType] = GR1FormulaType.GAR
    for spec_name, spec in specs.items():
        weaker = ideal_spec.implies(spec, formula_type)
        stronger = spec.implies(ideal_spec, formula_type)
        if weaker:
            weaker_gars.add(spec_name)
        if stronger:
            stronger_gars.add(spec_name)
    weaker_specs = set()
    stronger_specs = set()
    formula_type: Optional[GR1FormulaType] = None
    for spec_name, spec in specs.items():
        weaker = ideal_spec.implies(spec, formula_type)
        stronger = spec.implies(ideal_spec, formula_type)
        if weaker:
            weaker_specs.add(spec_name)
        if stronger:
            stronger_specs.add(spec_name)
    identical_asms = weaker_asms & stronger_asms
    identical_gars = weaker_gars & stronger_gars
    identical_specs = weaker_specs & stronger_specs
    print(f"TOTAL SPECS: {len(specs)}")
    print(f"AwGw SPECS: {len((weaker_asms - identical_asms) & (weaker_gars - identical_gars))}")
    print(f"AwGi SPECS: {len((weaker_asms - identical_asms) & identical_gars)}")
    print(f"AwGs SPECS: {len((weaker_asms - identical_asms) & (stronger_gars - identical_gars))}")
    print(f"AwGu SPECS: {len((weaker_asms - identical_asms) - (weaker_gars | stronger_gars))}")
    print(f"AiGw SPECS: {len(identical_asms & (weaker_gars - identical_gars))}")
    print(f"AiGi SPECS: {len(identical_asms & identical_gars)}")
    print(f"AiGs SPECS: {len(identical_asms & (stronger_gars - identical_gars))}")
    print(f"AiGu SPECS: {len(identical_asms - (weaker_gars | stronger_gars))}")
    print(f"AsGw SPECS: {len((stronger_asms - identical_asms) & (weaker_gars - identical_gars))}")
    print(f"AsGi SPECS: {len((stronger_asms - identical_asms) & identical_gars)}")
    print(f"AsGs SPECS: {len((stronger_asms - identical_asms) & (stronger_gars - identical_gars))}")
    print(f"AsGu SPECS: {len((stronger_asms - identical_asms) - (weaker_gars | stronger_gars))}")
    print(f"AuGw SPECS: {len((specs.keys() - weaker_asms - stronger_asms) & (weaker_gars - identical_gars))}")
    print(f"AuGi SPECS: {len((specs.keys() - weaker_asms - stronger_asms) & identical_gars)}")
    print(f"AuGs SPECS: {len((specs.keys() - weaker_asms - stronger_asms) & (stronger_gars - identical_gars))}")
    print(f"AuGu SPECS: {len(specs) - len(weaker_asms | stronger_asms | weaker_gars | stronger_gars)}")
    print(f"A->G WEAKER SPECS: {len(weaker_specs - identical_specs)}")
    print(f"A->G STRONGER SPECS: {len(stronger_specs - identical_specs)}")
    print(f"A->G IDENTICAL SPECS: {len(identical_specs)}")
    print(f"A->G UNRELATED SPECS: {len(specs.keys() - (weaker_specs | stronger_specs))}")


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
