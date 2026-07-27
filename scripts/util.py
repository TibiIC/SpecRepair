import os
from enum import Enum
from typing import Optional, Tuple, List
import pandas as pd

from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.ltl_types import GR1FormulaType


# These filtering helpers now live in the installed package, since only
# `spec_repair` is packaged by setup.cfg. Re-exported here so the existing
# `from util import ...` imports across scripts/ keep working.
from spec_repair.diagnosis.spec_filtering import (  # noqa: F401
    FileWithSpec,
    filter_maximal_specifications,
    filter_semantically_unique_specifications,
    find_maximal_specifications_from_folder,
    find_semantically_unique_specifications_from_directory,
    get_files_with_specs_from_directory,
    make_plural,
)


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
