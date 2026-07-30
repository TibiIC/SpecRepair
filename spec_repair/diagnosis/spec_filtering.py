"""
Filtering sets of specifications by semantic uniqueness and maximality.

Moved out of `scripts/util.py` because setup.cfg packages only `spec_repair`:
anything living under `scripts/` is not installed, so it cannot be imported by
an installed package or exercised from a wheel. `scripts/util.py` re-exports
these names, so existing script imports keep working.

"Maximal" here means maximal under implication: a specification is maximal when
no other specification in the set is strictly stronger than it. Passing a
`comparison_type` restricts the comparison to assumptions or guarantees only;
passing None requires maximality on both.
"""
import os
from typing import List, Optional, Tuple

from spec_repair.ltl_types import GR1FormulaType
from spec_repair.model.spectra_specification import SpectraSpecification

FileWithSpec = Tuple[str, SpectraSpecification]


def get_files_with_specs_from_directory(spec_directory_path: str) -> List[FileWithSpec]:
    """
    Load every .spectra file in a directory as (file_name, spec).

    Sorted by name so downstream numbering is reproducible - os.listdir order is
    arbitrary, which previously made "spec_0" mean a different specification
    from run to run.
    """
    return [
        (spec_file_path, SpectraSpecification.from_file(os.path.join(spec_directory_path, spec_file_path)))
        for spec_file_path in sorted(os.listdir(spec_directory_path))
        if spec_file_path.endswith('.spectra')
    ]


def filter_semantically_unique_specifications(
        files_with_specs: List[FileWithSpec],
        comparison_type: Optional[GR1FormulaType] = None,
) -> List[FileWithSpec]:
    files_with_specs = sorted(files_with_specs, key=lambda x: x[0])
    unique_specs: List[FileWithSpec] = []
    for file_path, spec in files_with_specs:
        if comparison_type:
            if not any(spec.equivalent_to(other_spec, comparison_type) for _, other_spec in unique_specs):
                unique_specs.append((file_path, spec))
        else:
            if not any(spec == other_spec for _, other_spec in unique_specs):
                unique_specs.append((file_path, spec))
    return unique_specs


def find_semantically_unique_specifications_from_directory(
        spec_directory_path: str,
        comparison_type: Optional[GR1FormulaType] = None,
) -> List[FileWithSpec]:
    files_with_specs = get_files_with_specs_from_directory(spec_directory_path)
    return filter_semantically_unique_specifications(files_with_specs, comparison_type)


def filter_maximal_specifications(
        files_with_specs: List[FileWithSpec],
        semantically_unique_files_with_specs: Optional[List[FileWithSpec]] = None,
        comparison_type: Optional[GR1FormulaType] = None,
) -> List[FileWithSpec]:
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


def find_maximal_specifications_from_folder(
        spec_directory_path: str,
        comparison_type: Optional[GR1FormulaType] = None,
) -> List[FileWithSpec]:
    files_with_specs = get_files_with_specs_from_directory(spec_directory_path)
    semantically_unique_specs = filter_semantically_unique_specifications(files_with_specs)
    return filter_maximal_specifications(files_with_specs, semantically_unique_specs, comparison_type)


def make_plural(item_list) -> str:
    return 's' if len(item_list) != 1 else ''
