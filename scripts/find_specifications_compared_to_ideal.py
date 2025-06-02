import argparse
import os

from spec_repair.helpers.spectra_specification import SpectraSpecification
from util import make_plural, print_spec_names, get_files_with_specs_from_directory
from spec_repair.ltl_types import GR1FormulaType

_description = """
This script finds all weaker specifications in a given directory than an ideal specification.
"""

from enum import Enum


class ComparisonType(Enum):
    WEAKER = 'w'
    WEAKER_OR_EQUIVALENT = 'we'
    EQUIVALENT = 'e'
    STRONGER_OR_EQUIVALENT = 'se'
    STRONGER = 's'

    @classmethod
    def from_str(cls, value: str):
        if not value:
            return None
        value = value.lower()
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"Invalid comparison type: {value}")

    def to_str(self):
        # Convert the enum value to a string representation
        match self:
            case ComparisonType.WEAKER:
                return 'weaker than'
            case ComparisonType.WEAKER_OR_EQUIVALENT:
                return 'weaker or equivalent to'
            case ComparisonType.EQUIVALENT:
                return 'equivalent to'
            case ComparisonType.STRONGER_OR_EQUIVALENT:
                return 'stronger or equivalent to'
            case ComparisonType.STRONGER:
                return 'stronger than'


def _get_arguments_from_cmd_line():
    parser = argparse.ArgumentParser(description=_description)
    parser.add_argument(
        "spec_dir",
        type=str,
        nargs="?",
        default=os.getcwd(),
        help='Path to the directory with Spectra specifications. If no argument is given, it will attempt to perform its task inside the directory in which the script is run. All files should be named [0-9]+.spectra'
    )
    parser.add_argument(
        '--ideal-spec',
        type=str,
        help='Path to an ideal specification file for comparison'
    )
    parser.add_argument(
        '-a',
        type=str,
        choices=['w', 'we', 'e', 'se', 's', 'W', 'WE', 'E', 'SE', 'S'],
        help='Assumption comparison type (w=weaker, we=weaker_or_equivalent, e=equivalent, se=stronger_or_equivalent, s=stronger)'
    )
    parser.add_argument(
        '-g',
        type=str,
        choices=['w', 'we', 'e', 'se', 's', 'W', 'WE', 'E', 'SE', 'S'],
        help='Guarantee comparison type (w=weaker, we=weaker_or_equivalent, e=equivalent, se=stronger_or_equivalent, s=stronger)'
    )

    args = parser.parse_args()
    assumption_type = ComparisonType.from_str(args.a) if args.a else None
    guarantee_type = ComparisonType.from_str(args.g) if args.g else None
    print("Assumption comparison type: {}".format(assumption_type))
    print("Guarantee comparison type: {}".format(guarantee_type))
    spec_directory_path = os.path.abspath(args.spec_dir)
    # Validate the directory path
    if not os.path.exists(spec_directory_path):
        raise FileNotFoundError(f"The specified directory does not exist: {spec_directory_path}")
    if not os.path.isdir(spec_directory_path):
        raise NotADirectoryError(f"The specified path is not a directory: {spec_directory_path}")
    # Validate that the directory contains Spectra files
    spectra_files = [f for f in os.listdir(spec_directory_path) if f.endswith('.spectra')]
    if not spectra_files:
        raise ValueError(
            f"No Spectra files found in the directory: {spec_directory_path}. Please ensure the directory contains files with the '.spectra' extension.")
    # Validate the ideal specification file path
    if args.ideal_spec is None:
        raise ValueError("An ideal specification file must be provided with the --ideal-spec argument.")
    ideal_spec_path = os.path.abspath(args.ideal_spec)
    if not os.path.exists(ideal_spec_path):
        raise FileNotFoundError(f"The specified ideal specification file does not exist: {ideal_spec_path}")
    if not os.path.isfile(ideal_spec_path):
        raise NotADirectoryError(f"The specified path is not a file: {ideal_spec_path}")
    return spec_directory_path, ideal_spec_path, assumption_type, guarantee_type


def is_compared_specifications(spec, ideal_spec, cmp_type, formula_type):
    if not cmp_type:
        return True
    match cmp_type:
        case ComparisonType.WEAKER:
            return spec.implies(ideal_spec, formula_type) and not ideal_spec.implies(spec, formula_type)
        case ComparisonType.WEAKER_OR_EQUIVALENT:
            return spec.implies(ideal_spec, formula_type)
        case ComparisonType.EQUIVALENT:
            return spec.implies(ideal_spec, formula_type) and ideal_spec.implies(spec, formula_type)
        case ComparisonType.STRONGER_OR_EQUIVALENT:
            return spec.implied_by(ideal_spec, formula_type)
        case ComparisonType.STRONGER:
            return spec.implied_by(ideal_spec, formula_type) and not ideal_spec.implied_by(spec, formula_type)


def is_compared_specification(spec, ideal_spec, asm_cmp_type, gar_cmp_type):
    is_cmp_asm = not asm_cmp_type or is_compared_specifications(spec, ideal_spec, asm_cmp_type, GR1FormulaType.ASM)
    is_cmp_gar = not gar_cmp_type or is_compared_specifications(spec, ideal_spec, gar_cmp_type, GR1FormulaType.GAR)
    return is_cmp_asm and is_cmp_gar


def find_compared_specifications_from_folder(spec_directory_path, ideal_spec_path, asm_cmp_type, gar_cmp_type):
    files_with_specs = get_files_with_specs_from_directory(spec_directory_path)
    ideal_spec = SpectraSpecification.from_file(ideal_spec_path)
    compared_specs = []
    for file_path, spec in files_with_specs:
        if is_compared_specification(spec, ideal_spec, asm_cmp_type, gar_cmp_type):
            compared_specs.append((file_path, spec))
    return compared_specs


if __name__ == '__main__':
    spec_directory_path, ideal_spec_path, asm_cmp_type, gar_cmp_type = _get_arguments_from_cmd_line()
    print("Comparing specs in directory: ", spec_directory_path)
    print("With the ideal specification at path: ", ideal_spec_path)
    compared_specs = find_compared_specifications_from_folder(spec_directory_path, ideal_spec_path, asm_cmp_type, gar_cmp_type)
    print(
        f"Found {len(compared_specs)} {f'{asm_cmp_type.to_str()} assumptions ' if asm_cmp_type else ''}{'and ' if asm_cmp_type and gar_cmp_type else ''}{f'{gar_cmp_type.to_str()} guarantees ' if gar_cmp_type else ''}specification{make_plural(compared_specs)} in the directory: {spec_directory_path}")
    print(f"{f'{asm_cmp_type.to_str()} assumptions ' if asm_cmp_type else ''}{'and ' if asm_cmp_type and gar_cmp_type else ''}{f'{gar_cmp_type.to_str()} guarantees ' if gar_cmp_type else ''} specification{make_plural(compared_specs)} found in file{make_plural(compared_specs)}:")
    print_spec_names(compared_specs)
