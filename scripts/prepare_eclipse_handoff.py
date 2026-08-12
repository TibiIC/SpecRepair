#!/usr/bin/env python3
"""
Lay out everything needed to replay a generated trace by hand in Eclipse.

We cannot tell whether a controller's final move is a legal transition or
something the Rich Controller Walker constructed for display, so the walker has
to be driven by hand and the crash log read back. This writes one folder per
case study containing the specification to synthesise, and for each trace the
environment inputs to enter step by step, the system outputs our run recorded,
and the violating input at the end.

    python scripts/prepare_eclipse_handoff.py            # every case study with traces
    python scripts/prepare_eclipse_handoff.py genbuf minepump

Output under eclipse_handoff/<case_study>/:

    original.spectra          the specification to synthesise
    trace_<n>.md              a step table: environment in, system out, per timepoint
    trace_<n>_inputs.txt      just the environment inputs, one step per line
    README.md                 what to do with them
"""
import argparse
import glob
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPECTRA = os.path.join(REPO_ROOT, "input-files", "case-studies", "spectra", "case_study_3")
# Every case study planned for case_study_3, which is all of case_study_2 -
# including the ones with no trace yet, whose specifications still have to be
# synthesised by hand to find out what the walker does with them.
PLANNED = os.path.join(REPO_ROOT, "input-files", "case-studies", "spectra", "case_study_2")
OUT_ROOT = os.path.join(REPO_ROOT, "eclipse_handoff")

_ATOM = re.compile(r"(not_)?holds_at\((\w+),(\w+),")


def read_states(path):
    """The trace file as a list of {var: bool} in timepoint order."""
    states = {}
    for negated, var, t in _ATOM.findall(open(path).read()):
        if not t.isdigit():
            continue
        states.setdefault(int(t), {})[var] = (negated == "")
    return [states[t] for t in sorted(states)]


def env_sys_names(spec_path):
    env, sysv = [], []
    for line in open(spec_path):
        line = line.strip()
        if line.startswith("env "):
            env.append(line.split()[-1].rstrip(";"))
        elif line.startswith("sys "):
            sysv.append(line.split()[-1].rstrip(";"))
    return env, sysv


def manifest_for(directory, index):
    path = os.path.join(directory, "traces.json")
    if not os.path.isfile(path):
        return {}
    data = json.load(open(path))
    entries = data if isinstance(data, list) else data.get("traces", [])
    for e in entries:
        if e.get("trace") == index:
            return e
    return {}


def write_trace(out_dir, index, states, env, sysv, meta):
    def row(state, names):
        return "  ".join(f"{n}={str(state.get(n, False)).lower()}" for n in names)

    last = len(states) - 1
    lines = [
        f"# {os.path.basename(out_dir)} - trace {index}",
        "",
        f"- target assumption: `{meta.get('target', '?')}`",
        f"- our run recorded these as violated: `{', '.join(meta.get('violated', [])) or '?'}`",
        f"- steps: {len(states)} (the last one is where the environment breaks the assumption)",
        "",
        "Enter the environment values for each step in order. The system column is",
        "what our run recorded - the one to compare against what the walker does.",
        "",
        "| t | environment (enter this) | system (ours) |",
        "| --- | --- | --- |",
    ]
    for t, state in enumerate(states):
        if t == last:
            # The system half of the violating step is deliberately absent. Ours
            # is not a controller response - the controller refused the move and
            # the previous outputs were carried over - so printing it here would
            # be handing back the very fabrication this is meant to replace.
            lines.append(f"| {t} | {row(state, env)} | **? <- the controller's "
                         f"answer goes here** |")
        else:
            lines.append(f"| {t} | {row(state, env)} | {row(state, sysv)} |")
    lines += [
        "",
        f"Steps 0-{last - 1} are genuine controller output: the environment respects",
        "the assumptions and the controller answers normally. Step "
        f"{last} is the intended violation.",
        "",
        "## The violating environment input",
        "",
        "```",
        row(states[last], env) if states else "",
        "```",
        "",
        f"## What is missing: the system's response at t={last}",
        "",
        "That is the whole point of this hand-off. Enter the inputs above step by",
        "step, and at the last one record what the walker does - the system values",
        "it produces, or the crash if it produces none. Send back the log and the",
        "trace can be completed from it.",
        "",
        "| variable | walker's value at the violating step |",
        "| --- | --- |",
    ] + [f"| {n} |  |" for n in sysv]
    with open(os.path.join(out_dir, f"trace_{index}.md"), "w") as f:
        f.write("\n".join(lines) + "\n")

    with open(os.path.join(out_dir, f"trace_{index}_inputs.txt"), "w") as f:
        for t, state in enumerate(states):
            tag = "   # violating step" if t == last else ""
            f.write(row(state, env) + tag + "\n")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("case_studies", nargs="*")
    args = p.parse_args(argv)

    names = args.case_studies or sorted(
        d for d in os.listdir(PLANNED)
        if os.path.isfile(os.path.join(PLANNED, d, "original.spectra")))

    os.makedirs(OUT_ROOT, exist_ok=True)
    summary = ["# Eclipse hand-off", "",
               "One folder per case study. In each: `original.spectra` to synthesise,",
               "and per trace a step table plus the bare environment inputs.", "",
               "| case study | traces | env vars | sys vars |",
               "| --- | --- | --- | --- |"]
    for cs in names:
        directory = os.path.join(SPECTRA, cs)
        spec_path = os.path.join(directory, "original.spectra")
        if not os.path.isfile(spec_path):
            # No case_study_3 folder yet: the specification is the case_study_2
            # one it would be copied from, and is still worth synthesising.
            spec_path = os.path.join(PLANNED, cs, "original.spectra")
        if not os.path.isfile(spec_path):
            continue
        traces = sorted(glob.glob(os.path.join(directory, "violation_trace_*.txt")))
        out_dir = os.path.join(OUT_ROOT, cs)
        os.makedirs(out_dir, exist_ok=True)
        with open(spec_path) as src, open(os.path.join(out_dir, "original.spectra"), "w") as dst:
            dst.write(src.read())
        env, sysv = env_sys_names(spec_path)
        for path in traces:
            index = int(re.search(r"violation_trace_(\d+)", path).group(1))
            write_trace(out_dir, index, read_states(path), env, sysv,
                        manifest_for(directory, index))
        note = "" if traces else "  (no trace generated yet - spec only)"
        summary.append(f"| {cs} | {len(traces)} | {', '.join(env)} | {', '.join(sysv)} |")
        print(f"{cs}: {len(traces)} trace(s) -> {out_dir}{note}")
        if not traces:
            with open(os.path.join(out_dir, "NO_TRACES_YET.md"), "w") as f:
                f.write(f"# {cs}\n\nNo violating trace has been generated for this case "
                        f"study yet, so there are no steps to replay. The specification is "
                        f"here to be synthesised: what the walker does when the environment "
                        f"breaks an assumption is the question, and it can be explored by "
                        f"hand without a trace from us.\n")

    summary += ["", "## The question",
                "", "At the last step of each trace the environment breaks an assumption.",
                "Our run could not get a system move there and reused the previous system",
                "values. Whether the walker produces a genuine move at that step, and what",
                "it is, is what these are for.", "",
                "Send back the walker's log up to and including the crash."]
    with open(os.path.join(OUT_ROOT, "README.md"), "w") as f:
        f.write("\n".join(summary) + "\n")
    print(f"\nWrote {OUT_ROOT}/README.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
