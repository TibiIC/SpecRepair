import argparse
import os
from typing import Optional

from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.ltl_types import GR1FormulaType

description = """
This script finds all semantically unique specifications in a given directory.
"""


def get_arguments_from_cmd_line():
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "spec_dir",
        type=str,
        nargs="?",
        default=os.getcwd(),
        help='Path to the directory with Spectra specifications. If no argument is given, it will attempt to perform its task inside the directory in which the script is run. All files should be named [0-9]+.spectra'
    )
    # Optional argument with a flag
    parser.add_argument(
        '-t', '--type',
        required=False,
        default=None,
        help='Type of comparison to be provided [asm/gar/assumption/guarantee]. Leave empty for GR(1)'
    )
    args = parser.parse_args()
    comparison_type: Optional[GR1FormulaType] = GR1FormulaType.from_str(args.type) if args.type else None
    print("Comparison type: {}".format(comparison_type))
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
    return spec_directory_path, comparison_type


def find_semantically_unique_specifications(spec_directory_path: str, comparison_type: Optional[GR1FormulaType] = None):
    files_with_specs = [(spec_file_path, SpectraSpecification.from_file(spec_file_path)) for spec_file_path in
                        os.listdir(spec_directory_path) if
                        spec_file_path.endswith('.spectra')]
    files_with_specs = sorted(files_with_specs, key=lambda x: x[0])
    unique_specs = []
    for file_path, spec in files_with_specs:
        if not any(spec.equivalent_to(other_spec, comparison_type) for other_path, other_spec in unique_specs):
            unique_specs.append((file_path, spec))
    return unique_specs


def make_plural(item_list):
    return 's' if len(item_list) != 1 else ''


if __name__ == '__main__':
    spec_directory_path, comparison_type = get_arguments_from_cmd_line()
    print("Finding unique specs in directory: ", spec_directory_path)
    unique_specs = find_semantically_unique_specifications(spec_directory_path, comparison_type)
    print(f"Found {len(unique_specs)} semantically unique specification{make_plural(unique_specs)} in the directory: {spec_directory_path}")
    print(f"Unique specification{make_plural(unique_specs)} found in file{make_plural(unique_specs)}:")
    for file_path, spec in unique_specs:
        print(f"{file_path}")
        # print(spec.to_str())
        # print("-" * 40)

