import argparse
import os
import glob

from typing import Dict, Optional, Set, Tuple

from compare_specialised import print_comparison_results_one_to_many
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import read_file
from spec_repair.ltl_types import GR1FormulaType


def filter_duplicates(specs: Set[SpectraSpecification]) -> Set[SpectraSpecification]:
    unique_specs = set()
    for spec in specs:
        is_unique = True
        for other_spec in specs:
            if other_spec in unique_specs and spec == other_spec:
                is_unique = False
                break
        if is_unique:
            unique_specs.add(spec)
    return unique_specs

# filter_duplicates but for the values of a dictionary
def filter_duplicate_values(specs: Dict[str, SpectraSpecification]) -> Dict[str, SpectraSpecification]:
    unique_specs = {}
    for spec_name, spec in specs.items():
        is_unique = True
        for other_spec_name, other_spec in specs.items():
            if other_spec_name in unique_specs and spec == other_spec:
                is_unique = False
                break
        if is_unique:
            unique_specs[spec_name] = spec
    return unique_specs

def find_maximal_specs(spec_directory_path: str) -> Tuple[Dict[str, SpectraSpecification], Dict[str, SpectraSpecification], Dict[str, SpectraSpecification]]:
    # Use the glob module to find all .spectra files in the specified directory
    spec_abs_paths = glob.glob(os.path.join(spec_directory_path, '*.spectra'))
    spec_abs_paths = [os.path.abspath(file_path) for file_path in spec_abs_paths]

    specs: Dict[str, SpectraSpecification] = {}
    for spec_abs_path in spec_abs_paths:
        spec_name: str = os.path.splitext(os.path.basename(spec_abs_path))[0]
        spec: SpectraSpecification = SpectraSpecification.from_file(spec_abs_path)
        specs[spec_name] = spec

    semantically_unique_specs: Dict[str, SpectraSpecification] = filter_duplicate_values(specs)

    maximal_asm_specs: Dict[str, SpectraSpecification] = {}
    for spec_name, spec in semantically_unique_specs.items():
        is_maximal = True
        for other_spec_name, other_spec in semantically_unique_specs.items():
            if (spec_name != other_spec_name and (
                    (other_spec.implies(spec, GR1FormulaType.ASM) and not spec.implies(other_spec, GR1FormulaType.ASM))
            )):
                is_maximal = False
                break
        if is_maximal:
            maximal_asm_specs[spec_name] = spec

    maximal_gar_specs: Dict[str, Spec] = {}
    for spec_name, spec in semantically_unique_specs.items():
        is_maximal = True
        for other_spec_name, other_spec in semantically_unique_specs.items():
            if (spec_name != other_spec_name and (
                    (other_spec.implies(spec, GR1FormulaType.GAR) and not spec.implies(other_spec, GR1FormulaType.GAR))
            )):
                is_maximal = False
                break
        if is_maximal:
            maximal_gar_specs[spec_name] = spec

    # Printing all maximal spec names
    unique_max_asm_not_max_gar = maximal_asm_specs.keys() - maximal_gar_specs.keys()
    unique_max_gar_not_max_asm = maximal_gar_specs.keys() - maximal_asm_specs.keys()
    unique_max_asm_max_gar = maximal_asm_specs.keys() & maximal_gar_specs.keys()
    print(f"Unique ID Maximal Assumption Specs: {unique_max_asm_not_max_gar}")
    print(f"Unique ID Maximal Guarantee Specs: {unique_max_gar_not_max_asm}")
    print(f"Unique ID Maximal Both Specs: {unique_max_asm_max_gar}")

    # Comparing maximal assumption specs
    formula_type: Optional[GR1FormulaType] = GR1FormulaType.ASM
    max_spec_names_asm = set()
    not_max_spec_names_asm = set()
    impossible_spec_names_asm = set() # Debug set to check if any specs are stronger than the maximal spec
    for max_spec_name, max_spec in maximal_asm_specs.items() - maximal_gar_specs.items():
        weaker_asms = set()
        stronger_asms = set()
        for spec_name, spec in specs.items():
            weaker = max_spec.implies(spec, formula_type)
            stronger = spec.implies(max_spec, formula_type)
            if weaker:
                weaker_asms.add(spec_name)
            if stronger:
                stronger_asms.add(spec_name)
        max_spec_names_asm |= weaker_asms & stronger_asms
        not_max_spec_names_asm |= weaker_asms - stronger_asms
        impossible_spec_names_asm |= stronger_asms - weaker_asms
    unrelated_spec_names_asm = specs.keys() - max_spec_names_asm - not_max_spec_names_asm - impossible_spec_names_asm


    # Comparing maximal guarantee specs
    formula_type: Optional[GR1FormulaType] = GR1FormulaType.GAR
    max_spec_names_gar = set()
    not_max_gar_specs = set()
    impossible_specs_gar = set() # Debug set to check if any specs are stronger than the maximal spec
    for max_spec_name, max_spec in maximal_gar_specs.items() - maximal_asm_specs.items():
        weaker_gars = set()
        stronger_gars = set()
        for spec_name, spec in specs.items():
            weaker = max_spec.implies(spec, formula_type)
            stronger = spec.implies(max_spec, formula_type)
            if weaker:
                weaker_gars.add(spec_name)
            if stronger:
                stronger_gars.add(spec_name)
        max_spec_names_gar |= weaker_gars & stronger_gars
        not_max_gar_specs |= weaker_gars - stronger_gars
        impossible_specs_gar |= stronger_gars - weaker_gars
    unrelated_specs_gar = specs.keys() - max_spec_names_gar - not_max_gar_specs - impossible_specs_gar


    # Comparing maximal both specs
    max_spec_names_both = set()
    not_max_spec_names_both = set()
    impossible_spec_names_both = set() # Debug set to check if any specs are stronger than the maximal spec
    for max_spec_name, max_spec in maximal_gar_specs.items() & maximal_asm_specs.items():
        weaker_both_spec_names = set()
        stronger_both_spec_names = set()
        for spec_name, spec in specs.items():
            weaker = max_spec.implies(spec, GR1FormulaType.ASM) and max_spec.implies(spec, GR1FormulaType.GAR)
            stronger = spec.implies(max_spec, GR1FormulaType.ASM) and spec.implies(max_spec, GR1FormulaType.GAR)
            if weaker:
                weaker_both_spec_names.add(spec_name)
            if stronger:
                stronger_both_spec_names.add(spec_name)
        max_spec_names_both |= weaker_both_spec_names & stronger_both_spec_names
        not_max_spec_names_both |= weaker_both_spec_names - stronger_both_spec_names
        impossible_spec_names_both |= stronger_both_spec_names - weaker_both_spec_names
    unrelated_specs_both = specs.keys() - max_spec_names_both - not_max_spec_names_both - impossible_spec_names_both

    print(f"Max Asm SPECS: {len(max_spec_names_asm)}")
    print(f"Not Max Asm SPECS: {len(not_max_spec_names_asm)}")
    print(f"Impossible Asm SPECS: {len(impossible_spec_names_asm)}")
    print(f"Unrelated Asm SPECS: {len(unrelated_spec_names_asm)}")
    print(unrelated_spec_names_asm)

    print(f"Max Gar SPECS: {len(max_spec_names_gar)}")
    print(f"Not Max Gar SPECS: {len(not_max_gar_specs)}")
    print(f"Impossible Gar SPECS: {len(impossible_specs_gar)}")
    print(f"Unrelated Gar SPECS: {len(unrelated_specs_gar)}")
    print(unrelated_specs_gar)

    print(f"Max Both SPECS: {len(max_spec_names_both)}")
    print(f"Not Max Both SPECS: {len(not_max_spec_names_both)}")
    print(f"Impossible Both SPECS: {len(impossible_spec_names_both)}")
    print(f"Unrelated Both SPECS: {len(unrelated_specs_both)}")
    print(unrelated_specs_both)

    return ({spec_name: specs[spec_name] for spec_name in max_spec_names_asm},
            {spec_name: specs[spec_name] for spec_name in max_spec_names_gar},
            {spec_name: specs[spec_name] for spec_name in max_spec_names_both})



description = """
TODO: fill up a description for this specification visualiser
"""

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-s', '--spec_dir', type=str,
                        required=True,
                        help='Path to the directory with specifications to be compared. All files should be named [0-9]+.spectra')
    parser.add_argument("-i", "--ideal_spec", type=str,
                        required=True,
                        help="Path to the ideal specification file")
    args = parser.parse_args()

    current_directory = os.getcwd()
    spec_directory_path = os.path.join(current_directory, args.spec_dir)
    ideal_spec_file_path = os.path.join(current_directory, args.ideal_spec)
    print("Comparing specs in directory: ", spec_directory_path)
    print("with ideal spec: ", ideal_spec_file_path)
    max_asm_specs, max_gar_specs, max_both_specs = find_maximal_specs(spec_directory_path)
    ideal_spec = SpectraSpecification.from_file(ideal_spec_file_path)
    print("Comparing ideal spec with maximal assumption specs")
    print_comparison_results_one_to_many(ideal_spec, max_asm_specs)
    print("Comparing ideal spec with maximal guarantee specs")
    print_comparison_results_one_to_many(ideal_spec, max_gar_specs)
    print("Comparing ideal spec with maximal both specs")
    print_comparison_results_one_to_many(ideal_spec, max_both_specs)



