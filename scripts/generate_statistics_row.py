import argparse
import os
import pandas as pd

from spec_repair.helpers.spectra_specification import SpectraSpecification
from util import filter_maximal_specifications, get_files_with_specs_from_directory, \
    filter_semantically_unique_specifications, print_spec_names, ComparisonType, filter_compared_specifications

_description = """
This script generates a row composed of all statistics relevant for the journal paper.
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
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Path to output file for the statistics table'
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
    return spec_directory_path, args.verbose, args.output, args.latex, ideal_spec_path


if __name__ == '__main__':
    spec_directory_path, is_verbose, output_path, use_latex, ideal_spec_path = _get_arguments_from_cmd_line()
    if is_verbose:
        print("Generating statistics from specs in directory: ", spec_directory_path)
    all_specs = get_files_with_specs_from_directory(spec_directory_path)
    if is_verbose:
        print(f"Found {len(all_specs)} specification files in the directory: {spec_directory_path}")
        print_spec_names(all_specs)
    unique_specs = filter_semantically_unique_specifications(all_specs)
    if is_verbose:
        print(f"Found {len(unique_specs)} unique specification:")
        print_spec_names(unique_specs)
    maximal_specs = filter_maximal_specifications(unique_specs)
    if is_verbose:
        print(f"Found {len(maximal_specs)} maximal unique specification:")
        print_spec_names(maximal_specs)

    experiment_name = os.path.basename(spec_directory_path)
    if not ideal_spec_path:
        df = pd.DataFrame(columns=['name_experiment', 'num_specs', 'num_unique_specs', 'num_unique_maximal_specs'])
        df.loc[0] = [experiment_name, len(all_specs), len(unique_specs), len(maximal_specs)]
    else:
        if is_verbose:
            print(f"Comparing with ideal specification at: {ideal_spec_path}")
        ideal_spec = SpectraSpecification.from_file(ideal_spec_path)
        compared_specs = {}
        comparisons = [ComparisonType.WEAKER, ComparisonType.EQUIVALENT, ComparisonType.STRONGER, ComparisonType.UNRELATED]
        for asm_cmp in comparisons:
            for gar_cmp in comparisons:
                if is_verbose:
                    print(f"Finding {asm_cmp.to_txt()} assumptions and {gar_cmp.to_txt()} guarantees compared to the ideal specification.")
                compared_specs[f"A{asm_cmp.to_str()}G{gar_cmp.to_str()}"] = filter_compared_specifications(unique_specs, ideal_spec, asm_cmp, gar_cmp)
                if is_verbose:
                    print(f"Found {len(compared_specs[f'A{asm_cmp.to_str()}G{gar_cmp.to_str()}'])} {asm_cmp.to_txt()} assumptions and {gar_cmp.to_txt()} guarantees:")
                    print_spec_names(compared_specs[f"A{asm_cmp.to_str()}G{gar_cmp.to_str()}"])

        df = pd.DataFrame(columns=['name_experiment', 'num_specs', 'num_unique_specs', 'num_unique_maximal_specs', 'num_awgw', 'num_awge', 'num_awgs', 'num_awgu', 'num_aegw', 'num_aege', 'num_aegs', 'num_aegu', 'num_asgw', 'num_asge', 'num_asgs', 'num_asgu', 'num_augw', 'num_auge', 'num_augs', 'num_augu'])
        df.loc[0] = [experiment_name, len(all_specs), len(unique_specs), len(maximal_specs), len(compared_specs["AwGw"]), len(compared_specs["AwGe"]), len(compared_specs["AwGs"]), len(compared_specs["AwGu"]), len(compared_specs["AeGw"]), len(compared_specs["AeGe"]), len(compared_specs["AeGs"]), len(compared_specs["AeGu"]), len(compared_specs["AsGw"]), len(compared_specs["AsGe"]), len(compared_specs["AsGs"]), len(compared_specs["AsGu"]), len(compared_specs["AuGw"]), len(compared_specs["AuGe"]), len(compared_specs["AuGs"]), len(compared_specs["AuGu"])]

    print("\nStatistics Table:")
    if use_latex:
        print(df.to_latex(index=False))
    else:
        print(df.to_string(index=False))

    if output_path:
        if use_latex:
            df.to_latex(output_path, index=False)
        else:
            df.to_csv(output_path, index=False)
        if is_verbose:
            print(f"\nTable saved to: {output_path}")
