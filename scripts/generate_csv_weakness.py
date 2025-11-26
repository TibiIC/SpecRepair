import argparse
import csv
import os

from spec_repair.helpers.spectra_specification import SpectraSpecification
from util import get_files_with_specs_from_directory
from spec_repair.ltl_types import GR1FormulaType

_description = """
Extracts full 4-dimensional weakness measures (ASM + GAR) for all specifications
and writes them to a CSV file instead of plotting.
Each row represents one specification and includes:
filename, asm_d0..asm_d3, gar_d0..gar_d3, type
"""


def _get_arguments_from_cmd_line():
    parser = argparse.ArgumentParser(description=_description)
    parser.add_argument(
        "spec_dir",
        type=str,
        nargs="?",
        default=os.getcwd(),
        help="Directory containing Spectra specifications (*.spectra)."
    )
    parser.add_argument("--ideal-spec", type=str, help="Path to ideal specification")
    parser.add_argument("--original-spec", type=str, help="Path to original specification")
    parser.add_argument("--trivial-specs", type=str, nargs="+",
                        help="Paths to trivial specification files")
    parser.add_argument("-o", "--output", type=str, required=True,
                        help="Output CSV file path")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    spec_directory_path = os.path.abspath(args.spec_dir)
    if not os.path.isdir(spec_directory_path):
        raise ValueError(f"Invalid specification directory: {spec_directory_path}")

    ideal_spec_path = os.path.abspath(args.ideal_spec) if args.ideal_spec else None
    original_spec_path = os.path.abspath(args.original_spec) if args.original_spec else None
    trivial_spec_paths = [os.path.abspath(p) for p in args.trivial_specs] if args.trivial_specs else []

    return spec_directory_path, ideal_spec_path, original_spec_path, trivial_spec_paths, args.output, args.verbose


def extract_weakness_tuple(spec):
    """Return full 4-dimensional ASM + GAR weakness tuple."""
    asm = spec.get_weakness(GR1FormulaType.ASM)
    gar = spec.get_weakness(GR1FormulaType.GAR)
    return [asm.d1, asm.d2, asm.nummaxentropysccs , asm.d3,
            gar.d1, gar.d2, gar.nummaxentropysccs , gar.d3]


if __name__ == "__main__":
    (spec_directory_path,
     ideal_spec_path,
     original_spec_path,
     trivial_spec_paths,
     output_path,
     verbose) = _get_arguments_from_cmd_line()

    rows = []

    # ------------------------------------------------------
    # 1. Process main spec directory
    # ------------------------------------------------------
    for file_path, spec in get_files_with_specs_from_directory(spec_directory_path):
        if verbose:
            print(f"Processing {file_path}")

        row = {
            "filename": os.path.basename(file_path),
            "type": "normal"
        }

        row_values = extract_weakness_tuple(spec)
        (row["asm_d0"], row["asm_d1"], row["asm_d2"], row["asm_d3"],
         row["gar_d0"], row["gar_d1"], row["gar_d2"], row["gar_d3"]) = row_values

        rows.append(row)

    # ------------------------------------------------------
    # 2. Process ideal spec
    # ------------------------------------------------------
    if ideal_spec_path:
        ideal_spec = SpectraSpecification.from_file(ideal_spec_path)
        vals = extract_weakness_tuple(ideal_spec)

        row = {
            "filename": os.path.basename(ideal_spec_path),
            "type": "ideal"
        }
        (row["asm_d0"], row["asm_d1"], row["asm_d2"], row["asm_d3"],
         row["gar_d0"], row["gar_d1"], row["gar_d2"], row["gar_d3"]) = vals
        rows.append(row)

    # ------------------------------------------------------
    # 3. Process original spec
    # ------------------------------------------------------
    if original_spec_path:
        original_spec = SpectraSpecification.from_file(original_spec_path)
        vals = extract_weakness_tuple(original_spec)

        row = {
            "filename": os.path.basename(original_spec_path),
            "type": "original"
        }
        (row["asm_d0"], row["asm_d1"], row["asm_d2"], row["asm_d3"],
         row["gar_d0"], row["gar_d1"], row["gar_d2"], row["gar_d3"]) = vals
        rows.append(row)

    # ------------------------------------------------------
    # 4. Process trivial specs
    # ------------------------------------------------------
    for tpath in trivial_spec_paths:
        trivial_spec = SpectraSpecification.from_file(tpath)
        vals = extract_weakness_tuple(trivial_spec)

        row = {
            "filename": os.path.basename(tpath),
            "type": "trivial"
        }
        (row["asm_d0"], row["asm_d1"], row["asm_d2"], row["asm_d3"],
         row["gar_d0"], row["gar_d1"], row["gar_d2"], row["gar_d3"]) = vals
        rows.append(row)

    # ------------------------------------------------------
    # Write CSV
    # ------------------------------------------------------
    fieldnames = [
        "filename", "type",
        "asm_d0", "asm_d1", "asm_d2", "asm_d3",
        "gar_d0", "gar_d1", "gar_d2", "gar_d3"
    ]

    dir_path = os.path.dirname(output_path)
    if dir_path:  # only create directory if it exists
        os.makedirs(dir_path, exist_ok=True)

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    if verbose:
        print(f"\nWrote CSV to: {output_path}")