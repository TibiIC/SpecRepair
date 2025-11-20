import argparse
import numpy as np
from collections import Counter
import os
import matplotlib.pyplot as plt

from spec_repair.helpers.spectra_specification import SpectraSpecification
from util import get_files_with_specs_from_directory
from spec_repair.ltl_types import GR1FormulaType

_description = """
Generates a beautiful scatter plot of specifications' weaknesses:
x axis: assumption-based weakness (ASM)
y axis: guarantee-based weakness (GAR)
Dots show the number of specifications with that weakness pair.
"""


def _get_arguments_from_cmd_line():
    parser = argparse.ArgumentParser(description=_description)
    parser.add_argument(
        "spec_dir",
        type=str,
        nargs="?",
        default=os.getcwd(),
        help='Directory containing Spectra specifications.'
    )
    parser.add_argument('--ideal-spec', type=str, help='Path to an ideal specification file for comparison')
    parser.add_argument('--original-spec', type=str, help='Path to the initial specification file for comparison')
    parser.add_argument(
        '--compare-type',
        type=str,
        choices=['ASM', 'GAR', 'NONE'],
        default='GAR',
        help='Formula type to compare: ASM, GAR, or NONE'
    )
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('-o', '--output', type=str, help='Output file path for the plot')
    parser.add_argument('--latex', action='store_true', help='Output table in LaTeX format')

    args = parser.parse_args()

    spec_directory_path = os.path.abspath(args.spec_dir)
    if not os.path.exists(spec_directory_path) or not os.path.isdir(spec_directory_path):
        raise ValueError(f"Invalid specification directory: {spec_directory_path}")

    ideal_spec_path = os.path.abspath(args.ideal_spec) if args.ideal_spec else None
    original_spec_path = os.path.abspath(args.original_spec) if args.original_spec else None
    compare_type = None if args.compare_type == 'NONE' else getattr(GR1FormulaType, args.compare_type)

    return spec_directory_path, args.verbose, compare_type, args.output, args.latex, ideal_spec_path, original_spec_path


if __name__ == '__main__':
    spec_directory_path, is_verbose, compare_type, output_path, use_latex, ideal_spec_path, original_spec_path = _get_arguments_from_cmd_line()

    if is_verbose:
        print(f"Specification directory: {spec_directory_path}")
        print(f"Ideal spec: {ideal_spec_path}")
        print(f"Original spec: {original_spec_path}")
        print(f"Output file: {output_path}")

    # -----------------------------
    # Parameters for plotting
    # -----------------------------
    circle_size = 200  # Dot size
    count_fontsize = 12  # Font size for count
    jitter_amount = 0.005  # Small jitter for overlapping special points
    precision = 6  # Number of decimals to round for counter keys

    # -----------------------------
    # Gather weaknesses for all specifications
    # -----------------------------
    points_counter = Counter()  # keys=(ASM_weakness.d2, GAR_weakness.d2), values=count

    all_files_with_specs = get_files_with_specs_from_directory(spec_directory_path)
    for file_path, spec in all_files_with_specs:
        asm_weakness = spec.get_weakness(GR1FormulaType.ASM)
        gar_weakness = spec.get_weakness(GR1FormulaType.GAR)

        # Round to avoid float precision duplicates
        key = (round(asm_weakness.d2, precision), round(gar_weakness.d2, precision))
        points_counter[key] += 1

    # Include ideal specification as reference
    if ideal_spec_path:
        ideal_spec = SpectraSpecification.from_file(ideal_spec_path)
        ideal_key = (round(ideal_spec.get_weakness(GR1FormulaType.ASM).d2, precision),
                     round(ideal_spec.get_weakness(GR1FormulaType.GAR).d2, precision))
        points_counter[ideal_key] += 0  # Don't increment count, just ensure it exists

    # Include original specification as reference
    if original_spec_path:
        original_spec = SpectraSpecification.from_file(original_spec_path)
        original_key = (round(original_spec.get_weakness(GR1FormulaType.ASM).d2, precision),
                        round(original_spec.get_weakness(GR1FormulaType.GAR).d2, precision))
        points_counter[original_key] += 0

    # -----------------------------
    # Plotting
    # -----------------------------
    plt.figure(figsize=(12, 9))

    for (x, y), count in points_counter.items():
        plt.scatter(x, y, s=circle_size, color='skyblue', edgecolor='black', zorder=2)
        if count >= 1:
            plt.text(x, y, str(count), color='red', fontsize=count_fontsize,
                     ha='center', va='center', fontweight='bold', zorder=3)

    # Highlight ideal specification
    if ideal_spec_path:
        plt.scatter(ideal_key[0] + np.random.uniform(-jitter_amount, jitter_amount),
                    ideal_key[1] + np.random.uniform(-jitter_amount, jitter_amount),
                    s=250, color='green', marker='*', label='Ideal Specification', zorder=4)

    # Highlight original specification
    if original_spec_path:
        plt.scatter(original_key[0] + np.random.uniform(-jitter_amount, jitter_amount),
                    original_key[1] + np.random.uniform(-jitter_amount, jitter_amount),
                    s=250, color='red', marker='*', label='Original Specification', zorder=4)

    plt.xlabel("Assumption-based Weakness (ASM)", fontsize=14)
    plt.ylabel("Guarantee-based Weakness (GAR)", fontsize=14)
    plt.title("Specification Weakness: ASM vs GAR", fontsize=16)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(fontsize=12)
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, bbox_inches='tight', dpi=300)
        plt.close()
    else:
        plt.show()