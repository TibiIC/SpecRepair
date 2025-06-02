import argparse
import os
from typing import Optional

from scripts.util import print_spec_names
from util import make_plural, find_maximal_specifications_from_folder
from spec_repair.ltl_types import GR1FormulaType

_description = """
This script finds all maximal specifications in a given directory.
"""


def _get_arguments_from_cmd_line():
    parser = argparse.ArgumentParser(description=_description)
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


if __name__ == '__main__':
    spec_directory_path, comparison_type = _get_arguments_from_cmd_line()
    print("Finding maximal specs in directory: ", spec_directory_path)
    maximal_specs = find_maximal_specifications_from_folder(spec_directory_path, comparison_type)
    print(
        f"Found {len(maximal_specs)} maximal specification{make_plural(maximal_specs)} in the directory: {spec_directory_path}")
    print(f"Maximal specification{make_plural(maximal_specs)} found in file{make_plural(maximal_specs)}:")
    print_spec_names(maximal_specs)
