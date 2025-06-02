import argparse
import os
import sys
import pandas as pd
from typing import List, Dict


def validate_headers(csv_files: List[str]) -> List[str]:
    first_df = pd.read_csv(csv_files[0])
    headers = list(first_df.columns)

    for file_path in csv_files[1:]:
        current_df = pd.read_csv(file_path)
        current_headers = list(current_df.columns)
        if headers != current_headers:
            raise ValueError(f"Headers mismatch in {file_path}. Expected {headers}, got {current_headers}")
    return headers


def combine_csv_files(csv_files: List[str]) -> pd.DataFrame:
    dfs = [pd.read_csv(file) for file in csv_files]
    return pd.concat(dfs, ignore_index=True)


def to_latex_table(data: pd.DataFrame) -> str:
    return data.to_latex(index=False)


def _get_arguments_from_cmd_line():
    parser = argparse.ArgumentParser(description="Combine CSV files with identical headers into a single table")
    parser.add_argument(
        "csv_files",
        type=str,
        nargs="+",
        help="List of CSV files to combine"
    )
    parser.add_argument(
        "-l", "--latex",
        action="store_true",
        help="Output as LaTeX table instead of CSV"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output file path (defaults to stdout)"
    )
    args = parser.parse_args()

    # Validate CSV files existence
    for csv_file in args.csv_files:
        if not os.path.exists(csv_file):
            raise FileNotFoundError(f"CSV file not found: {csv_file}")
        if not os.path.isfile(csv_file):
            raise ValueError(f"Path is not a file: {csv_file}")

    return args


if __name__ == '__main__':
    args = _get_arguments_from_cmd_line()
    headers = validate_headers(args.csv_files)
    combined_data = combine_csv_files(args.csv_files)

    if args.latex:
        output = to_latex_table(combined_data)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
    else:
        if args.output:
            combined_data.to_csv(args.output, index=False)
        else:
            combined_data.to_csv(sys.stdout, index=False)
