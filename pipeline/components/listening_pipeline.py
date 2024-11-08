"""
Run this to open up a listener on a folder where logs of traces will appear.
The logs of traces will be extracted as traces of a specification, then the
violation fixer will run to repair the specification, afterwards providing it
as a file.
"""

from spec_repair.util.spec_util import log_to_asp_trace
from spec_repair.util.file_util import write_to_file
from pipeline.components.violation_listener import start_listening_for_violations

log_folder = '/Users/tg4018/eclipse-workspace/PhD/Lift'
main_spec = f"{log_folder}/lift_well_sep_strong.spectra"
cnt: int = 0


def weaken_spec(log_contents):
    global main_spec, cnt
    # Process the log contents and return the result
    # Replace with your actual function implementation
    print("Started Fixing")
    tmp_trace_file = "/tmp/log_trace.txt"
    violation_trace = log_to_asp_trace(log_contents)
    write_to_file(tmp_trace_file, violation_trace)
    fixed_spec = f"{log_folder}/lift_well_sep_{cnt}.spectra"
    self = Specification(main_spec, tmp_trace_file, fixed_spec=fixed_spec, include_prev=False, random_hypothesis=True)
    self.run_pipeline()
    main_spec = fixed_spec
    cnt += 1
    print("Fixed Spec Done")
    return violation_trace


if __name__ == '__main__':
    cnt = 0
    print("Started Listening for Violations")
    start_listening_for_violations(weaken_spec)
