import argparse
import csv
import os
import sys
from typing import List, Dict


def validate_headers(csv_files: List[str]) -> List[str]:
    headers = None
    for file_path in csv_files:
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            current_headers = next(reader)
            if headers is None:
                headers = current_headers
            elif headers != current_headers:
                raise ValueError(f"Headers mismatch in {file_path}. Expected {headers}, got {current_headers}")
    return headers


def combine_csv_files(csv_files: List[str]) -> List[Dict]:
    combined_data = []
    for file_path in csv_files:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            combined_data.extend(list(reader))
    return combined_data


def to_latex_table(data: List[Dict], headers: List[str]) -> str:
    latex_table = "\\begin{tabular}{" + "c" * len(headers) + "}\n"
    latex_table += " & ".join(headers) + " \\\\\n\\hline\n"
    for row in data:
        latex_table += " & ".join(str(row[h]) for h in headers) + " \\\\\n"
    latex_table += "\\end{tabular}"
    return latex_table


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
    try:
        args = _get_arguments_from_cmd_line()

        try:
            headers = validate_headers(args.csv_files)
            combined_data = combine_csv_files(args.csv_files)

            if args.latex:
                output = to_latex_table(combined_data, headers)
                if args.output:
                    with open(args.output, 'w') as f:
                        f.write(output)
            else:
                writer = csv.DictWriter(sys.stdout, fieldnames=headers)
                writer.writeheader()
                writer.writerows(combined_data)

                if args.output:
                    with open(args.output, 'w') as f:
                        writer = csv.DictWriter(f, fieldnames=headers)
                        writer.writeheader()
                        writer.writerows(combined_data)
        except Exception as e:
            print(f"Error processing CSV files: {str(e)}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error parsing arguments: {str(e)}", file=sys.stderr)
        sys.exit(1)
