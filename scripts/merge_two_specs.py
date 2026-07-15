import argparse
import os
from typing import List, Optional

from spec_repair.interfaces.ispecification import ISpecification
from spec_repair.components.oracles.spectra_gr1_oracle import SpectraGR1Oracle
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.ltl_types import GR1FormulaType
from spec_repair.new_research import get_all_trivial_solutions_guarantee_only
from spec_repair.util.file_util import write_to_file

def merge_two_solutions(spec1: ISpecification, spec2: ISpecification, og_spec:Optional[ISpecification]=None) -> List[ISpecification]:
    oracle = SpectraGR1Oracle()
    if not oracle.is_realisable(spec1) or not oracle.is_realisable(spec2):
        print("WARNING: At least one of the two solutions is unrealizable.")
        assert oracle.is_realisable(spec1) and oracle.is_realisable(spec2)
    if og_spec:
        assert og_spec.implies(spec1, GR1FormulaType.ASM) and og_spec.implies(spec2,
                                                                                                      GR1FormulaType.ASM)
        assert og_spec.implies(spec1, GR1FormulaType.GAR) and og_spec.implies(spec2,
                                                                                                      GR1FormulaType.GAR)

    merged_spec = spec1.merge(spec2)
    if oracle.is_realisable(merged_spec):
        return [merged_spec]
    else:
        new_merged_specs = get_all_trivial_solutions_guarantee_only(merged_spec)
        for new_merged_spec in new_merged_specs:
            if not oracle.is_realisable(new_merged_spec):
                print("WARNING: Merged solution is unrealizable.")
                print(merged_spec)
        return new_merged_specs


def main():
    parser = argparse.ArgumentParser(description='Merge two specification files')
    parser.add_argument('og_spec_path', type=str, nargs='?', default=None,
                        help='Path to original specification file (optional)')
    parser.add_argument('spec1_path', type=str, help='Path to first specification file')
    parser.add_argument('spec2_path', type=str, help='Path to second specification file')
    parser.add_argument('output_folder', type=str, help='Path to output folder')

    args = parser.parse_args()

    og_spec_path = args.og_spec_path
    spec1_path = args.spec1_path
    spec2_path = args.spec2_path
    output_folder = args.output_folder

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    og_spec = SpectraSpecification.from_file(og_spec_path) if og_spec_path else None
    spec1 = SpectraSpecification.from_file(spec1_path)
    spec2 = SpectraSpecification.from_file(spec2_path)

    merged_specs = merge_two_solutions(spec1, spec2, og_spec)

    for i, merged_spec in enumerate(merged_specs):
        output_filename = f"{output_folder}/merged_{i}.spectra"
        write_to_file(output_filename, merged_spec.to_str())
        print(f"Written merged specification to: {output_filename}")

    print(f"Total merged specifications generated: {len(merged_specs)}")


if __name__ == "__main__":
    main()
