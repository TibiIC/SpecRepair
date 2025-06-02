import argparse
import os

from spec_repair.helpers.spectra_specification import SpectraSpecification
from util import ComparisonType, filter_compared_specifications, make_plural, print_spec_names, \
    get_files_with_specs_from_directory

_description = """
This script compares all specifications in a given directory to an ideal specification.
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
        '-a',
        type=str,
        choices=['w', 'we', 'e', 'se', 's', 'W', 'WE', 'E', 'SE', 'S'],
        help='Assumption comparison type (w=weaker, we=weaker_or_equivalent, e=equivalent, se=stronger_or_equivalent, s=stronger)'
    )
    parser.add_argument(
        '-g',
        type=str,
        choices=['w', 'we', 'e', 'se', 's', 'W', 'WE', 'E', 'SE', 'S'],
        help='Guarantee comparison type (w=weaker, we=weaker_or_equivalent, e=equivalent, se=stronger_or_equivalent, s=stronger)'
    )

    args = parser.parse_args()
    assumption_type = ComparisonType.from_str(args.a) if args.a else None
    guarantee_type = ComparisonType.from_str(args.g) if args.g else None
    print("Assumption comparison type: {}".format(assumption_type))
    print("Guarantee comparison type: {}".format(guarantee_type))
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
    if args.ideal_spec is None:
        raise ValueError("An ideal specification file must be provided with the --ideal-spec argument.")
    ideal_spec_path = os.path.abspath(args.ideal_spec)
    if not os.path.exists(ideal_spec_path):
        raise FileNotFoundError(f"The specified ideal specification file does not exist: {ideal_spec_path}")
    if not os.path.isfile(ideal_spec_path):
        raise NotADirectoryError(f"The specified path is not a file: {ideal_spec_path}")
    return spec_directory_path, ideal_spec_path, assumption_type, guarantee_type


def find_compared_specifications_from_folder(spec_directory_path, ideal_spec_path, asm_cmp_type, gar_cmp_type):
    files_with_specs = get_files_with_specs_from_directory(spec_directory_path)
    ideal_spec = SpectraSpecification.from_file(ideal_spec_path)
    return filter_compared_specifications(files_with_specs, ideal_spec, asm_cmp_type, gar_cmp_type)


if __name__ == '__main__':
    spec_directory_path, ideal_spec_path, asm_cmp_type, gar_cmp_type = _get_arguments_from_cmd_line()
    print("Comparing specs in directory: ", spec_directory_path)
    print("With the ideal specification at path: ", ideal_spec_path)
    compared_specs = find_compared_specifications_from_folder(spec_directory_path, ideal_spec_path, asm_cmp_type,
                                                              gar_cmp_type)
    print(
        f"Found {len(compared_specs)} {f'{asm_cmp_type.to_txt()} assumptions ' if asm_cmp_type else ''}{'and ' if asm_cmp_type and gar_cmp_type else ''}{f'{gar_cmp_type.to_txt()} guarantees ' if gar_cmp_type else ''}specification{make_plural(compared_specs)} in the directory: {spec_directory_path}")
    print(
        f"{f'{asm_cmp_type.to_txt()} assumptions ' if asm_cmp_type else ''}{'and ' if asm_cmp_type and gar_cmp_type else ''}{f'{gar_cmp_type.to_txt()} guarantees ' if gar_cmp_type else ''} specification{make_plural(compared_specs)} found in file{make_plural(compared_specs)}:")
    print_spec_names(compared_specs)
