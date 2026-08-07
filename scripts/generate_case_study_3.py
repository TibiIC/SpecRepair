"""
Build case_study_3: violation traces produced by running a real controller.

The first two setups manufacture traces symbolically with ASP, which constrains
the system only by the specification - so a trace can contain system behaviour
no synthesised controller would ever produce. Here the system half of every
trace is genuine controller output, and only the environment is adversarial.

    python scripts/generate_case_study_3.py                  # every case study
    python scripts/generate_case_study_3.py minepump lift    # just these
    python scripts/generate_case_study_3.py --traces 5 --compliant-steps 5

Each case study gets `original.spectra` copied from case_study_2 and
`violation_trace_<n>.txt` per seed, so the layout matches case_study_2 exactly
and the existing runner, pipeline and precondition assertions apply unchanged.

Traces that do not satisfy the repair's preconditions are not written: a case
study is only useful if its trace violates at least one non-initial assumption,
and shipping one that does not is what cost a day of unrecognisable failures on
2026-08-06.
"""
import argparse
import json
import os
import shutil
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from spec_repair.diagnosis.controller_trace_generation import (  # noqa: E402
    ControllerTraceError, generate_controller_violation_trace,
    violatable_assumptions)

SPECTRA = os.path.join(REPO_ROOT, "input-files", "case-studies", "spectra")
SOURCE = os.path.join(SPECTRA, "case_study_2")
TARGET = os.path.join(SPECTRA, "case_study_3")


def case_studies_available():
    return sorted(d for d in os.listdir(SOURCE)
                  if os.path.isfile(os.path.join(SOURCE, d, "original.spectra")))


def generate_for(case_study: str, traces: int, compliant_steps: int,
                 max_random_steps: int, attempts: int, max_targets: int = 1) -> int:
    src_spec = os.path.join(SOURCE, case_study, "original.spectra")
    out_dir = os.path.join(TARGET, case_study)
    os.makedirs(out_dir, exist_ok=True)
    shutil.copyfile(src_spec, os.path.join(out_dir, "original.spectra"))

    # Each trace gets its own assumption to aim at, cycling through them, and
    # assumptions already covered are tried last on the fallbacks. Coverage of
    # the assumptions is what makes five traces worth more than one.
    available = violatable_assumptions(src_spec)
    covered: list = []
    manifest: list = []

    written = 0
    for seed in range(traces):
        preferred = available[seed % len(available)] if available else None
        order = ([preferred] if preferred else []) + \
                [a for a in available if a != preferred and a not in covered] + \
                [a for a in available if a != preferred and a in covered]

        lines = violated = None
        for target in order:
            try:
                lines, violated = generate_controller_violation_trace(
                    src_spec, compliant_steps=compliant_steps,
                    max_random_steps=max_random_steps, seed=seed, attempts=attempts,
                    trace_name=f"trace_name_{seed}", max_targets=max_targets,
                    target_assumptions=[target])
                break
            except ControllerTraceError:
                continue
            except Exception as e:  # noqa: BLE001 - one bad target must not stop the rest
                print(f"  trace {seed}: FAILED on {target} "
                      f"({type(e).__name__}: {str(e)[:70]})")
                continue
        if lines is None:
            print(f"  trace {seed}: none (no assumption of {available} was reachable)")
            continue
        covered.extend(violated)
        with open(os.path.join(out_dir, f"violation_trace_{seed}.txt"), "w") as f:
            f.writelines(lines)
        steps = sum(1 for ln in lines if ln.strip() == "") or 1
        print(f"  trace {seed}: {steps} steps, violates {', '.join(violated)}")
        manifest.append({
            "trace": seed,
            "seed": seed,
            "target": target,
            "violated": violated,
            "steps": steps,
            "compliant_steps": compliant_steps,
            "max_random_steps": max_random_steps,
            "attempts": attempts,
            "max_targets": max_targets,
        })
        written += 1

    if written == 0:
        # An empty case study directory is worse than none: the runner would
        # generate tests for traces that do not exist.
        shutil.rmtree(out_dir, ignore_errors=True)
        return 0

    # Record how each trace was made. Generation is reproducible from the seed,
    # but only if you know which assumption it aimed at: a trace whose preferred
    # target proved unreachable fell back to another, and nothing in the trace
    # file says which. Without this, a specific trace cannot be regenerated -
    # verified the hard way, when two of three spot-checks failed to reproduce
    # for exactly this reason.
    #
    # One caveat this does not remove. Replaying a single trace from its
    # manifest reproduces it exactly for the smaller case studies (gyro checks
    # out) but not always for the larger ones (pcar does not). Spectra's Env is
    # global to the JVM, so state accumulates across the generator's calls, and
    # a trace generated after four earlier seeds in one process is not
    # guaranteed to match one generated first in a fresh one. Regenerating the
    # whole case study in order is the reliable replay.
    with open(os.path.join(out_dir, "traces.json"), "w") as f:
        json.dump({"case_study": case_study, "traces": manifest}, f, indent=2)
        f.write("\n")
    return written


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("case_studies", nargs="*", help="default: all of case_study_2")
    parser.add_argument("--traces", type=int, default=5)
    parser.add_argument("--compliant-steps", type=int, default=5,
                        help="N: steps the environment respects the assumptions")
    parser.add_argument("--max-random-steps", type=int, default=40)
    parser.add_argument("--attempts", type=int, default=25)
    parser.add_argument("--max-targets", type=int, default=1,
                        help="how many assumptions one trace may violate at once. "
                             "One by default: an environment that breaks every "
                             "assumption simultaneously is not a deployment anyone "
                             "would recognise, and the repair cannot tell which "
                             "weakening such a trace is asking for. Two is the "
                             "sensible ceiling.")
    args = parser.parse_args(argv)

    selected = args.case_studies or case_studies_available()
    unknown = set(selected) - set(case_studies_available())
    if unknown:
        parser.error(f"unknown case study/studies: {', '.join(sorted(unknown))}")

    os.makedirs(TARGET, exist_ok=True)
    total = 0
    for case_study in selected:
        print(f"{case_study}:")
        total += generate_for(case_study, args.traces, args.compliant_steps,
                              args.max_random_steps, args.attempts, args.max_targets)
    print(f"\n{total} trace(s) written under {os.path.relpath(TARGET, REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
