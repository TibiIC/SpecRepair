import os
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
    files_with_specs = [(spec_file_path, SpectraSpecification.from_file(spec_file_path)) for spec_file_path in
                        os.listdir(spec_directory_path) if
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
