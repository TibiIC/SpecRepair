import argparse
import os
from collections import defaultdict
from typing import Optional

import matplotlib.pyplot as plt

from spec_repair.helpers.spectra_specification import SpectraSpecification
from util import get_files_with_specs_from_directory
from spec_repair.ltl_types import GR1FormulaType

_description= """
Generates a beautiful distribution of all specifications' weaknesses across a graph, encoding:
x axis: weakness measure
y axis: number of specifications with that weakness measure
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
    parser.add_argument(
        '--ideal-spec',
        type=str,
        help='Path to an ideal specification file for comparison'
    )
    parser.add_argument(
        '--compare-type',
        type=str,
        choices=['ASM', 'GAR', 'NONE'],
        default='GAR',
        help='Type of formulas to compare: ASM (assumptions), GAR (guarantees), or NONE'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Path to output file for the generated plot'
    )
    parser.add_argument(
        '--latex',
        action='store_true',
        help='Output the table in LaTeX format'
    )

    args = parser.parse_args()
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
    # Validate the ideal specification file path
    if args.ideal_spec is not None:
        ideal_spec_path = os.path.abspath(args.ideal_spec)
        if not os.path.exists(ideal_spec_path):
            raise FileNotFoundError(f"The specified ideal specification file does not exist: {ideal_spec_path}")
        if not os.path.isfile(ideal_spec_path):
            raise NotADirectoryError(f"The specified path is not a file: {ideal_spec_path}")
    else:
        ideal_spec_path = None
    compare_type = None if args.compare_type == 'NONE' else getattr(GR1FormulaType, args.compare_type)
    return spec_directory_path, args.verbose, compare_type, args.output, args.latex, ideal_spec_path

if __name__ == '__main__':
    spec_directory_path, is_verbose, compare_type, output_path, use_latex, ideal_spec_path = _get_arguments_from_cmd_line()
    if is_verbose:
        print(f"Specification directory: {spec_directory_path}")
        if ideal_spec_path:
            print(f"Ideal specification file: {ideal_spec_path}")
        else:
            print("No ideal specification file provided.")
        if output_path:
            print(f"Output file: {output_path}")
        else:
            print("No output file provided; will print to console.")
        print(f"LaTeX output: {'enabled' if use_latex else 'disabled'}")
    if is_verbose:
        print("Starting weakness statistics generation...")
        
    # Initialise statistics data structures
    weakness_statistics = defaultdict(int)
    weakness_values = []
    # Get all specifications from the directory
    all_files_with_specs = get_files_with_specs_from_directory(spec_directory_path)
    for file_path, spec in all_files_with_specs:
        if is_verbose:
            print(f"Processing specification file: {file_path}")
        weakness = spec.get_weakness(compare_type)
        weakness_statistics[weakness] += 1
        weakness_values.append(weakness)

    # Add ideal specification weakness if provided
    if ideal_spec_path:
        ideal_spec = SpectraSpecification.from_file(ideal_spec_path)
        ideal_weakness = ideal_spec.get_weakness(compare_type)
        weakness_values.append(ideal_weakness)
        if is_verbose:
            print(f"Added ideal specification weakness: {ideal_weakness}")

    # Create mapping of weakness to rank (1=weakest, max=strongest)
    sorted_weakness = sorted(set(weakness_values))
    weakness_to_rank = {w: i + 1 for i, w in enumerate(sorted_weakness)}

    if is_verbose:
        print("\nWeakness rankings:")
        for file_path, spec in all_files_with_specs:
            weakness = spec.get_weakness(compare_type)
            rank = weakness_to_rank[weakness]
            print(f"{file_path}: weakness {weakness} (rank {rank} of {len(sorted_weakness)})")

    # Plot distribution
    plt.figure(figsize=(10, 6))
    x_values = list(weakness_statistics.keys())
    y_values = list(weakness_statistics.values())

    # Sort based on x values
    sorted_pairs = sorted(zip(x_values, y_values))
    x_values, y_values = zip(*sorted_pairs)

    # Create regular specification bars
    bars = plt.bar(range(len(x_values)), y_values, label='Regular Specifications', color='skyblue')

    # Add ideal specification if provided
    if ideal_spec_path:
        ideal_weakness = ideal_spec.get_weakness(compare_type)
        ideal_x = list(x_values).index(ideal_weakness) if ideal_weakness in x_values else len(x_values)
        plt.bar(ideal_x, weakness_statistics[ideal_weakness], color='red', label='Ideal Specification')

    plt.xticks(range(len(x_values)), [f"{x.d1:.3f}" for x in x_values], rotation=45)
    plt.xlabel("Weakness (d1 component)")
    plt.ylabel('Number of Specifications')
    plt.title('Distribution of Specification Weaknesses')
    plt.legend()

    # plt.tight_layout()
    if output_path:
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
    else:
        plt.show()
