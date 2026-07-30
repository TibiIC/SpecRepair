"""
Merge repaired Spectra specifications into as few solutions as possible.

Replaces the former merge_two_specs.py and merge_all_specs.py, which did the
same thing with different argument shapes. Inputs are any mix of .spectra files
and directories of them, so both old use cases are one command now:

    # what merge_two_specs.py did
    python scripts/merge_specs.py -o out/ a.spectra b.spectra

    # what merge_all_specs.py did
    python scripts/merge_specs.py -o out/ specs_dir/

    # original specification is optional, and now a named flag
    python scripts/merge_specs.py -o out/ --og-spec strong.spectra specs_dir/

The merge procedure itself lives in spec_repair.diagnosis.solution_merging so it
can be imported and tested; this file is only argument handling and file I/O.
"""
import argparse
import logging
import os
import sys
from typing import List

from spec_repair.diagnosis.solution_merging import merge_solutions
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import write_to_file

SPECTRA_EXT = ".spectra"


def collect_spec_paths(inputs: List[str]) -> List[str]:
    """
    Expand each input into specification file paths. A directory contributes its
    .spectra files, sorted by name so runs are reproducible (os.listdir order is
    not guaranteed); a file is taken as-is.
    """
    paths: List[str] = []
    for entry in inputs:
        if os.path.isdir(entry):
            found = sorted(f for f in os.listdir(entry) if f.endswith(SPECTRA_EXT))
            if not found:
                raise ValueError(f"No {SPECTRA_EXT} files found in directory: {entry}")
            paths.extend(os.path.join(entry, f) for f in found)
        elif os.path.isfile(entry):
            paths.append(entry)
        else:
            raise ValueError(f"No such file or directory: {entry}")
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Merge two or more Spectra specifications into as few solutions as possible.",
    )
    parser.add_argument("inputs", nargs="+", metavar="INPUT",
                        help=f"specification files and/or directories containing {SPECTRA_EXT} files")
    parser.add_argument("-o", "--output-folder", required=True,
                        help="folder to write merged_N.spectra into")
    # A named flag rather than a leading optional positional: the old scripts
    # declared `og_spec_path` with nargs="?" ahead of required positionals,
    # which makes what a bare path means depend on how many arguments follow.
    parser.add_argument("--og-spec", default=None, metavar="PATH",
                        help="optional original specification; each input is checked to be a weakening of it")
    parser.add_argument("--strict", action="store_true",
                        help="fail instead of warning when an input is not a weakening of --og-spec")
    return parser


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = build_parser().parse_args(argv)

    try:
        spec_paths = collect_spec_paths(args.inputs)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if len(spec_paths) < 2:
        print(f"ERROR: found {len(spec_paths)} specification file(s); need at least 2 to merge.",
              file=sys.stderr)
        return 2

    os.makedirs(args.output_folder, exist_ok=True)

    og_spec = SpectraSpecification.from_file(args.og_spec) if args.og_spec else None
    specs = [SpectraSpecification.from_file(p) for p in spec_paths]
    print(f"Merging {len(specs)} specifications:")
    for path in spec_paths:
        print(f"  {path}")

    try:
        merged_specs = merge_solutions(specs, og_spec=og_spec, strict=args.strict)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    for i, merged_spec in enumerate(merged_specs):
        output_filename = os.path.join(args.output_folder, f"merged_{i}{SPECTRA_EXT}")
        write_to_file(output_filename, merged_spec.to_str())
        print(f"Written merged specification to: {output_filename}")

    print(f"Total merged specifications generated: {len(merged_specs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
