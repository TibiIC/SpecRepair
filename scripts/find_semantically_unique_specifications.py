import argparse
import os
from typing import Optional

from util import find_semantically_unique_specifications_from_directory, make_plural
from spec_repair.ltl_types import GR1FormulaType

_description = """
This script finds all semantically unique specifications in a given directory.
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
    parser.add_argument(
        '-o', '--output-dir',
        required=False,
        default=None,
        help='Optional directory to write the selected specifications into, as spec_<i>.spectra'
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
    return spec_directory_path, comparison_type, args.output_dir



def save_specs_to_directory(files_with_specs, output_dir: str, prefix: str = "spec") -> None:
    """
    Write the selected specifications out as <prefix>_<i>.spectra.

    Renumbered from 0 rather than keeping the original file names: these
    directories feed the next pipeline stage, which expects a contiguous set,
    and the original names carry indices from a different (larger) population.
    The source file name is recorded as a comment so provenance is not lost.
    """
    os.makedirs(output_dir, exist_ok=True)
    for i, (source_name, spec) in enumerate(files_with_specs):
        out_path = os.path.join(output_dir, f"{prefix}_{i}.spectra")
        with open(out_path, "w") as f:
            f.write(f"// selected from: {source_name}\n")
            f.write(spec.to_str())
    print(f"Saved {len(files_with_specs)} specification(s) to {output_dir}")


if __name__ == '__main__':
    spec_directory_path, comparison_type, output_dir = _get_arguments_from_cmd_line()
    print("Finding unique specs in directory: ", spec_directory_path)
    unique_specs = find_semantically_unique_specifications_from_directory(spec_directory_path, comparison_type)
    print(f"Found {len(unique_specs)} semantically unique specification{make_plural(unique_specs)} in the directory: {spec_directory_path}")
    print(f"Unique specification{make_plural(unique_specs)} found in file{make_plural(unique_specs)}:")
    for file_path, spec in unique_specs:
        print(f"{file_path}")
        # print(spec.to_str())
        # print("-" * 40)
    if output_dir:
        save_specs_to_directory(unique_specs, output_dir)
