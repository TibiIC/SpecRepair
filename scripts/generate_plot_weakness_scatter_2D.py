import argparse
from collections import Counter
import os
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from matplotlib.legend_handler import HandlerPatch
from matplotlib.patches import Patch

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
    parser.add_argument('--trivial-specs', type=str, nargs='+',
                        help='Paths to trivial specification files for comparison')

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
    trivial_spec_paths = [os.path.abspath(path) for path in args.trivial_specs] if args.trivial_specs else None
    compare_type = None if args.compare_type == 'NONE' else getattr(GR1FormulaType, args.compare_type)

    return spec_directory_path, args.verbose, compare_type, args.output, args.latex, ideal_spec_path, original_spec_path, trivial_spec_paths


if __name__ == '__main__':
    spec_directory_path, is_verbose, compare_type, output_path, use_latex, ideal_spec_path, original_spec_path, trivial_spec_paths = _get_arguments_from_cmd_line()

    if is_verbose:
        print(f"Specification directory: {spec_directory_path}")
        print(f"Ideal spec: {ideal_spec_path}")
        print(f"Original spec: {original_spec_path}")
        print(f"Output file: {output_path}")

    # -----------------------------
    # Parameters for plotting
    # -----------------------------
    circle_size = 600  # Bigger circles
    star_size = 2000  # Bigger stars
    count_fontsize = 14  # Larger count labels
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

    # Include trivial specifications as reference
    if trivial_spec_paths:
        for path in trivial_spec_paths:
            trivial_spec = SpectraSpecification.from_file(path)
            trivial_key = (round(trivial_spec.get_weakness(GR1FormulaType.ASM).d2, precision),
                           round(trivial_spec.get_weakness(GR1FormulaType.GAR).d2, precision))
            points_counter[trivial_key] += 0

    # -----------------------------
    # Plotting
    # -----------------------------
    plt.figure(figsize=(12, 9))

    # Extract ideal/original actual d2 values again (rounded for plotting comparisons)
    ideal_point = None
    if ideal_spec_path:
        ideal_asm = ideal_spec.get_weakness(GR1FormulaType.ASM)
        ideal_gar = ideal_spec.get_weakness(GR1FormulaType.GAR)
        ideal_point = (round(ideal_asm.d2, precision), round(ideal_gar.d2, precision))

    original_point = None
    if original_spec_path:
        original_asm = original_spec.get_weakness(GR1FormulaType.ASM)
        original_gar = original_spec.get_weakness(GR1FormulaType.GAR)
        original_point = (round(original_asm.d2, precision), round(original_gar.d2, precision))

    trivial_points = []
    if trivial_spec_paths:
        for path in trivial_spec_paths:
            trivial_spec = SpectraSpecification.from_file(path)
            trivial_asm = trivial_spec.get_weakness(GR1FormulaType.ASM)
            trivial_gar = trivial_spec.get_weakness(GR1FormulaType.GAR)
            trivial_points.append((round(trivial_asm.d2, precision), round(trivial_gar.d2, precision)))

    # Flags so legend entries appear only once
    drew_ideal_legend = False
    drew_original_legend = False
    drew_trivial_legend = False

    for (x, y), count in points_counter.items():
        # CASE 1: Ideal specification
        if ideal_point is not None and (x, y) == ideal_point:
            plt.scatter(
                x, y, s=star_size, color='green', marker='*', edgecolor='black',
                zorder=4,
                label='Ideal Specification' if not drew_ideal_legend else None
            )
            drew_ideal_legend = True

            if count > 1:
                txt = plt.text(x, y, str(count),
                               color='white', fontsize=count_fontsize, ha='center', va='center',
                               fontweight='bold', zorder=5)
                txt.set_path_effects([
                    path_effects.Stroke(linewidth=2, foreground='black'),
                    path_effects.Normal()
                ])
            continue

        # CASE 2: Original specification
        if original_point is not None and (x, y) == original_point:
            plt.scatter(
                x, y, s=star_size, color='red', marker='*', edgecolor='black',
                zorder=4,
                label='Original Specification' if not drew_original_legend else None
            )
            drew_original_legend = True

            if count > 1:
                txt = plt.text(x, y, str(count),
                               color='white', fontsize=count_fontsize, ha='center', va='center',
                               fontweight='bold', zorder=5)
                txt.set_path_effects([
                    path_effects.Stroke(linewidth=2, foreground='black'),
                    path_effects.Normal()
                ])
            continue

        # CASE 3: Trivial specifications
        if trivial_points and (x, y) in trivial_points:
            plt.scatter(
                x, y, s=star_size, color='darkblue', marker='*', edgecolor='black',
                zorder=4,
                label='Trivial Specification' if not drew_trivial_legend else None
            )
            drew_trivial_legend = True

            if count > 1:
                txt = plt.text(x, y, str(count),
                               color='white', fontsize=count_fontsize, ha='center', va='center',
                               fontweight='bold', zorder=5)
                txt.set_path_effects([
                    path_effects.Stroke(linewidth=2, foreground='black'),
                    path_effects.Normal()
                ])
            continue

        # CASE 4: Standard point
        plt.scatter(x, y, s=circle_size, color='skyblue', edgecolor='black', zorder=2)

        if count > 1:
            txt = plt.text(x, y, str(count),
                           color='white', fontsize=count_fontsize, ha='center', va='center',
                           fontweight='bold', zorder=3)
            txt.set_path_effects([
                path_effects.Stroke(linewidth=2, foreground='black'),
                path_effects.Normal()
            ])

    # Axis labels and decoration
    plt.xlabel("Assumption-based Weakness (ASM)", fontsize=14)
    plt.ylabel("Guarantee-based Weakness (GAR)", fontsize=14)
    plt.title("Specification Weakness: ASM vs GAR", fontsize=16)
    plt.grid(True, linestyle='--', alpha=0.6)
    # --- Legend: use smaller stars ---
    legend_elements = []

    if ideal_spec_path:
        legend_elements.append(
            Patch(facecolor='green', edgecolor='black', label='Ideal Specification')
        )

    if original_spec_path:
        legend_elements.append(
            Patch(facecolor='red', edgecolor='black', label='Original Specification')
        )

    if trivial_spec_paths:
        legend_elements.append(
            Patch(facecolor='darkblue', edgecolor='black', label='Trivial Specification')
        )

    plt.legend(
        handles=legend_elements,
        loc='upper left',
        markerscale=0.4,  # << smaller markers
        fontsize=12,
        frameon=True
    )
    plt.tight_layout()

    # Save or show plot
    if output_path:
        plt.savefig(output_path, bbox_inches='tight', dpi=300)
        plt.close()
    else:
        plt.show()
