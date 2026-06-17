import argparse
import os
from typing import List, Optional

from spec_repair.components.interfaces.ispecification import ISpecification
from spec_repair.components.oracles.spectra_gr1_oracle import SpectraGR1Oracle
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.ltl_types import GR1FormulaType
from spec_repair.new_research import get_all_trivial_solutions_guarantee_only
from spec_repair.util.file_util import write_to_file

def merge_all_solutions(specs: List[ISpecification], og_spec:Optional[ISpecification]=None) -> List[ISpecification]:
    assert len(specs) >= 2
    oracle = SpectraGR1Oracle()
    for spec in specs:
        assert oracle.is_realisable(spec)
        if og_spec:
            assert og_spec.implies(spec, GR1FormulaType.ASM) and og_spec.implies(spec, GR1FormulaType.GAR)

    merged_spec = specs[0].merge(specs[1])
    for i in range(2, len(specs)):
        merged_spec = merged_spec.merge(specs[i])

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
    parser = argparse.ArgumentParser(description='Merge all specification files in a directory')
    parser.add_argument('og_spec_path', type=str, nargs='?', default=None,
                        help='Path to original specification file (optional)')
    parser.add_argument('specs_dir', type=str, help='Path to directory containing specification files')
    parser.add_argument('output_folder', type=str, help='Path to output folder')

    args = parser.parse_args()

    og_spec_path = args.og_spec_path
    specs_dir = args.specs_dir
    output_folder = args.output_folder

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    og_spec = SpectraSpecification.from_file(og_spec_path) if og_spec_path else None

    spec_files = [f for f in os.listdir(specs_dir) if f.endswith('.spectra')]
    if len(spec_files) < 2:
        print(f"ERROR: Found {len(spec_files)} specification file(s). Need at least 2 files to merge.")
        return

    specs = [SpectraSpecification.from_file(os.path.join(specs_dir, f)) for f in spec_files]
    print(f"Found {len(specs)} specification files to merge")

    merged_specs = merge_all_solutions(specs, og_spec)
    for i, merged_spec in enumerate(merged_specs):
        output_filename = f"{output_folder}/merged_{i}.spectra"
        write_to_file(output_filename, merged_spec.to_str())
        print(f"Written merged specification to: {output_filename}")

    print(f"Total merged specifications generated: {len(merged_specs)}")


if __name__ == "__main__":
    main()
