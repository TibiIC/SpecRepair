import os
from enum import Enum
from typing import Optional, Tuple, List
import pandas as pd

from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.ltl_types import GR1FormulaType


def find_semantically_unique_specifications_from_directory(
        spec_directory_path: str,
        comparison_type: Optional[GR1FormulaType] = None
) -> List[Tuple[str, SpectraSpecification]]:
    files_with_specs = get_files_with_specs_from_directory(spec_directory_path)
    return filter_semantically_unique_specifications(files_with_specs, comparison_type)


def get_files_with_specs_from_directory(
        spec_directory_path: str
) -> List[Tuple[str, SpectraSpecification]]:
    files_with_specs = [
        (spec_file_path, SpectraSpecification.from_file(os.path.join(spec_directory_path, spec_file_path)))
        for spec_file_path in os.listdir(spec_directory_path) if
        spec_file_path.endswith('.spectra')]
    return files_with_specs


def filter_semantically_unique_specifications(
        files_with_specs: List[Tuple[str, SpectraSpecification]],
        comparison_type: Optional[GR1FormulaType] = None
) -> List[Tuple[str, SpectraSpecification]]:
    files_with_specs = sorted(files_with_specs, key=lambda x: x[0])
    unique_specs = []
    for file_path, spec in files_with_specs:
        if not any(spec.equivalent_to(other_spec, comparison_type) for other_path, other_spec in unique_specs):
            unique_specs.append((file_path, spec))
    return unique_specs


def make_plural(item_list):
    return 's' if len(item_list) != 1 else ''


def find_maximal_specifications_from_folder(spec_directory_path, comparison_type):
    files_with_specs = get_files_with_specs_from_directory(spec_directory_path)
    semantically_unique_specs = filter_semantically_unique_specifications(files_with_specs)
    return filter_maximal_specifications(files_with_specs, semantically_unique_specs, comparison_type)


def filter_maximal_specifications(
        files_with_specs: List[Tuple[str, SpectraSpecification]],
        semantically_unique_files_with_specs: Optional[List[Tuple[str, SpectraSpecification]]] = None,
        comparison_type: Optional[GR1FormulaType] = None
) -> List[Tuple[str, SpectraSpecification]]:
    """
    precondition: semantically_unique_files_with_specs is the subset of unique specifications from files_with_specs
    precondition: if no semantically_unique_files_with_specs is produced, files_with_specs is assumed to be semantically unique
    """
    if semantically_unique_files_with_specs is None:
        semantically_unique_files_with_specs = files_with_specs
    if comparison_type is None:
        maximal_asm_specs = filter_maximal_specifications(files_with_specs, semantically_unique_files_with_specs,
                                                          GR1FormulaType.ASM)
        maximal_gar_specs = filter_maximal_specifications(files_with_specs, semantically_unique_files_with_specs,
                                                          GR1FormulaType.GAR)
        # Get intersection based on file names
        gar_files = {spec[0] for spec in maximal_gar_specs}
        return [(name, spec) for name, spec in maximal_asm_specs if name in gar_files]

    maximal_specs_of_comparison_type = []
    for spec_name, spec in files_with_specs:
        is_maximal = True
        for other_spec_name, other_spec in semantically_unique_files_with_specs:
            if (spec_name != other_spec_name and (
                    (other_spec.implies(spec, comparison_type) and not spec.implies(other_spec, comparison_type))
            )):
                is_maximal = False
                break
        if is_maximal:
            maximal_specs_of_comparison_type.append((spec_name, spec))
    return maximal_specs_of_comparison_type


def get_table_from_csv(file_path: str):
    try:
        table = pd.read_csv(file_path)
        return table
    except Exception as e:
        print(f"Error reading CSV file {file_path}: {e}")
        return None


def print_spec_names(maximal_specs):
    for file_path, spec in maximal_specs:
        print(f"{file_path}")
        # print(spec.to_str())
        # print("-" * 40)


class ComparisonType(Enum):
    UNRELATED = 'u'
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
        return self.value

    def to_txt(self):
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
            case ComparisonType.UNRELATED:
                return 'unrelated to'


def is_compared_specifications(spec, ideal_spec, cmp_type, formula_type):
    if not cmp_type:
        return True
    match cmp_type:
        case ComparisonType.WEAKER:
            return spec.implied_by(ideal_spec, formula_type) and not ideal_spec.implied_by(spec, formula_type)
        case ComparisonType.WEAKER_OR_EQUIVALENT:
            return spec.implied_by(ideal_spec, formula_type)
        case ComparisonType.EQUIVALENT:
            return spec.implies(ideal_spec, formula_type) and ideal_spec.implies(spec, formula_type)
        case ComparisonType.STRONGER_OR_EQUIVALENT:
            return spec.implies(ideal_spec, formula_type)
        case ComparisonType.STRONGER:
            return spec.implies(ideal_spec, formula_type) and not ideal_spec.implies(spec, formula_type)
        case ComparisonType.UNRELATED:
            return not spec.implies(ideal_spec, formula_type) and not ideal_spec.implies(spec, formula_type)

def compare_specifications(spec, ideal_spec, formula_type) -> ComparisonType:
    is_spec_weaker_than_ideal = spec.implied_by(ideal_spec, formula_type)
    is_spec_stronger_than_ideal = spec.implies(ideal_spec, formula_type)
    match is_spec_weaker_than_ideal, is_spec_stronger_than_ideal:
        case True, True:
            return ComparisonType.EQUIVALENT
        case True, False:
            return ComparisonType.WEAKER
        case False, True:
            return ComparisonType.STRONGER
        case False, False:
            return ComparisonType.UNRELATED
    return ComparisonType.UNRELATED


def is_compared_specification(spec, ideal_spec, asm_cmp_type, gar_cmp_type):
    is_cmp_asm = not asm_cmp_type or is_compared_specifications(spec, ideal_spec, asm_cmp_type, GR1FormulaType.ASM)
    is_cmp_gar = not gar_cmp_type or is_compared_specifications(spec, ideal_spec, gar_cmp_type, GR1FormulaType.GAR)
    return is_cmp_asm and is_cmp_gar


def filter_compared_specifications(files_with_specs, ideal_spec, asm_cmp_type, gar_cmp_type):
    compared_specs = []
    for file_path, spec in files_with_specs:
        if is_compared_specification(spec, ideal_spec, asm_cmp_type, gar_cmp_type):
            compared_specs.append((file_path, spec))
    return compared_specs
