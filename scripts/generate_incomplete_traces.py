#!/usr/bin/env python3
"""
Traces that stop where the generator gives up: prefix, then the violating input.

The full generator only writes a trace when the whole episode succeeds - a
compliant prefix, a violating step, *and* a final state. amba, colorsort,
elevator, humanoid and lift never get past the violating step, so they produce
nothing at all, even though the two parts we can produce are exactly the two
parts that are wanted:

1. a compliant prefix, walked against the real controller, so the system half
   is genuine output;
2. an environment input that the solver says breaks a chosen assumption.

What is missing is the controller's answer to (2) - which is the question the
Rich Controller Walker is being driven by hand to answer. So this stops there
deliberately: the violating input is *not* executed, nothing is fabricated to
stand in for the response, and the trace is written incomplete on purpose.

    python scripts/generate_incomplete_traces.py amba --traces 5
    python scripts/generate_incomplete_traces.py            # every case study

Writes eclipse_handoff/<case_study>/trace_<n>.md in the same format as the
complete ones, with the system's value at the violating step left blank.
"""
import argparse
import glob
import os
import random
import shutil
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from spec_repair.diagnosis import controller_trace_generation as ctg
from spec_repair.model.spectra_specification import SpectraSpecification

SOURCE = os.path.join(REPO_ROOT, "input-files", "case-studies", "spectra", "case_study_2")
OUT_ROOT = os.path.join(REPO_ROOT, "eclipse_handoff")


def incomplete_trace(spec_path, target, seed, compliant_steps, walk_limit):
    """
    (states, violating_input) - or None if the prefix or the input cannot be had.

    `states` are real controller states. `violating_input` is the environment's
    next move, unexecuted: the controller's response to it is the unknown.
    """
    spec = SpectraSpecification.from_file(spec_path)
    variables = ctg._spec_variable_names(spec)
    repairable = ctg._non_initial_assumption_names(spec)
    rng = random.Random(seed)
    work_dir = tempfile.mkdtemp(prefix="incomplete_trace_")
    try:
        executor = ctg._executor_for(spec_path, work_dir)
        env_domains = {str(k): [str(v) for v in vals]
                       for k, vals in executor.getEnvVars().items()}
        states, started = [], False

        def step(inputs):
            nonlocal started
            java_inputs = ctg.jpype.JClass("java.util.HashMap")()
            for k, v in inputs.items():
                java_inputs.put(k, v)
            try:
                if not started:
                    executor.initState(java_inputs)
                    started = True
                else:
                    executor.updateState(java_inputs)
                ctg._settle(executor, rng)
            except ctg.jpype.JException:
                return False
            states.append(ctg._state_from(executor, variables))
            return True

        # Phase 1, unchanged: a compliant prefix of genuine controller output.
        for _ in range(compliant_steps):
            compliant = ctg._targeted_inputs(spec, states, env_domains, variables,
                                             repairable, set(), rng, "trace_name_0")
            if not any(step(c) for c in compliant):
                return None

        # Phase 2, stopped early: walk until the solver can name a violating
        # input, then hand that input back rather than executing it.
        for _ in range(walk_limit):
            candidates = ctg._targeted_inputs(spec, states, env_domains, variables,
                                              repairable, {target}, rng, "trace_name_0")
            if not candidates:
                return None
            proposed = candidates[0]
            breaks = ctg._hypothetical_violations(spec, states, proposed, variables,
                                                  repairable, "trace_name_0")
            if target in breaks:
                return states, proposed
            # Not yet the violating step - a move towards it. Execute and go on.
            if not step(proposed):
                # The controller refused a step that was not meant to violate:
                # this walk is spent.
                return None
        return None
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def write(out_dir, index, states, violating, env, sysv, target):
    os.makedirs(out_dir, exist_ok=True)
    # The "no traces yet" placeholder is a statement about the folder, and it
    # stops being true the moment one is written. Left behind, it contradicts
    # the files next to it.
    placeholder = os.path.join(out_dir, "NO_TRACES_YET.md")
    if os.path.exists(placeholder):
        os.remove(placeholder)

    def row(state, names):
        return "  ".join(f"{n}={str(state.get(n, False)).lower()}" for n in names)

    last = len(states)
    lines = [f"# {os.path.basename(out_dir)} - trace {index} (incomplete)", "",
             f"- target assumption: `{target}`",
             f"- steps 0-{last - 1} are genuine controller output",
             f"- step {last} is the intended violation, and its system response is unknown",
             "",
             "| t | environment (enter this) | system (ours) |",
             "| --- | --- | --- |"]
    lines += [f"| {t} | {row(s, env)} | {row(s, sysv)} |" for t, s in enumerate(states)]
    lines.append(f"| {last} | {row(violating, env)} | **? <- the controller's answer "
                 f"goes here** |")
    lines += ["", "## The violating environment input", "", "```",
              row(violating, env), "```", "",
              f"## What is missing: the system's response at t={last}", "",
              "This trace was never completed by us: the controller had no move to "
              "make, and nothing was invented to stand in for one. Enter the inputs "
              "above step by step and record what the walker does at the last one.",
              "", "| variable | walker's value at the violating step |", "| --- | --- |"]
    lines += [f"| {n} |  |" for n in sysv]
    with open(os.path.join(out_dir, f"trace_{index}.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(out_dir, f"trace_{index}_inputs.txt"), "w") as f:
        for s in states:
            f.write(row(s, env) + "\n")
        f.write(row(violating, env) + "   # violating step\n")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("case_studies", nargs="*")
    p.add_argument("--traces", type=int, default=5)
    p.add_argument("--compliant-steps", type=int, default=5)
    p.add_argument("--walk-limit", type=int, default=20)
    args = p.parse_args(argv)

    names = args.case_studies or sorted(
        d for d in os.listdir(SOURCE)
        if os.path.isfile(os.path.join(SOURCE, d, "original.spectra")))

    for cs in names:
        spec_path = os.path.join(SOURCE, cs, "original.spectra")
        targets = ctg.violatable_assumptions(spec_path)
        if not targets:
            print(f"{cs}: no invariant assumption to target - skipped")
            continue
        env, sysv = [], []
        for line in open(spec_path):
            line = line.strip()
            if line.startswith("env "):
                env.append(line.split()[-1].rstrip(";"))
            elif line.startswith("sys "):
                sysv.append(line.split()[-1].rstrip(";"))

        written = 0
        for seed in range(args.traces):
            target = targets[seed % len(targets)]
            print(f"{cs}: trace {seed} aiming at {target}", flush=True)
            try:
                result = incomplete_trace(spec_path, target, seed,
                                          args.compliant_steps, args.walk_limit)
            except Exception as e:  # noqa: BLE001 - one target must not stop the rest
                print(f"  failed: {type(e).__name__}: {str(e)[:80]}")
                continue
            if result is None:
                print(f"  no violating input reachable for {target}")
                continue
            states, violating = result
            write(os.path.join(OUT_ROOT, cs), seed, states, violating, env, sysv, target)
            print(f"  wrote {len(states)} genuine step(s) + the violating input")
            written += 1
        print(f"{cs}: {written}/{args.traces} incomplete trace(s)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
