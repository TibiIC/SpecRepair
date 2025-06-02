import os
from typing import Optional, Tuple

from spec_repair import config
import argparse
from spec_repair.util.spec_util import log_to_asp_trace
from spec_repair.util.file_util import write_to_file, Log, ASPTrace, FilePath, read_file

description = """
Given an LTL specification written in Spectra and the logs of its latest trace, assuming there was a violation detected,
the program generates a repaired version of the specification, which does not allow the observed violation.
Optionally, the path to the newly repaired specification can be specified (defaults to <name>_fixed.spectra).
"""


def parse_args() -> Tuple[str, list[str], Optional[str]]:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-s', '--spec', type=str, help='Path to the spec argument.')
    parser.add_argument('-t', '--trace_logs', nargs='+', type=str, help='Path to the trace_logs argument.')
    parser.add_argument('-o', '--out_spec', type=str, help='Path to the new fixed spec.', default=None)
    parser.add_argument('--manual', type=bool, help='Whether the choices will be made manually or not', default=False)
    args = parser.parse_args()

    # Check if any of the non-default arguments are missing
    if args.spec is None or args.trace_logs is None:
        parser.print_help()
        exit(1)

    # Convert relative paths to full paths
    args.spec = os.path.abspath(args.spec)
    args.trace_logs = [os.path.abspath(arg_trace_log) for arg_trace_log in args.trace_logs]
    if args.out_spec:
        args.out_spec = os.path.abspath(args.out_spec)
    config.MANUAL = args.manual

    return args.spec, args.trace_logs, args.out_spec


if __name__ == '__main__':
    spec_path, trace_log_paths, fixed_spec_path = parse_args()
    # Use the arguments in your program
    print(f'Spec path: {spec_path}')
    print(f'Trace log path: {trace_log_paths}')
    if fixed_spec_path:
        print(f'Fixed spec at path: {fixed_spec_path}')

    print("Creating Temporary Trace File...")
    tmp_trace_file: FilePath = "/tmp/log_trace.txt"
    violation_trace: ASPTrace = ""

    for i, trace_log_path in enumerate(trace_log_paths):
        trace_log: Log = read_file(trace_log_path)
        violation_trace += log_to_asp_trace(trace_log, trace_name=f"trace_name_{i}")

    write_to_file(filename=tmp_trace_file, content=violation_trace)

    print("Started Fixing...")
    self = Specification(spec_path, tmp_trace_file, fixed_spec=fixed_spec_path, include_prev=False,
                         random_hypothesis=True)
    self.run_pipeline()
    print("Fixed Spec Done")
