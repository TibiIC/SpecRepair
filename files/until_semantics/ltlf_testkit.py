#!/usr/bin/env python3
"""
Interactive table over ltl2asp_ext.asp: every formula, every trace, both sides.

Formulas, traces and the reference evaluator live in
`tests/test_semantics/ltlf_weak_ops.py`, so this script and the pytest suite
cannot drift apart. Add a formula there and it appears in both.

    conda activate arm_env
    python files/until_semantics/ltlf_testkit.py              # the table
    python files/until_semantics/ltlf_testkit.py --disagree   # only mismatches
    python files/until_semantics/ltlf_testkit.py --example    # check ltl/example.asp

For the same checks as assertions:

    python -m pytest tests/test_semantics/test_ltlf_weak_operators.py -q
"""
from __future__ import annotations

import argparse
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from tests.test_semantics.ltlf_weak_ops import (  # noqa: E402
    EXAMPLE_FORMULA, EXAMPLE_TRACES, TRACES, expected_names, holds,
    sat_names, sat_names_of_files, supported,
)
from tests.test_semantics.test_ltlf_weak_operators import CASES  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLE = os.path.join(HERE, "ltl", "example.asp")


def check_example() -> int:
    """Does the hand-written example file encode the formula it claims to?"""
    stated = sat_names(EXAMPLE_FORMULA, EXAMPLE_TRACES)
    actual = sat_names_of_files([EXAMPLE])
    print(f"  {EXAMPLE}")
    print(f"    the file satisfies        : {sorted(actual) or '{}'}")
    print(f"    its stated formula would  : {sorted(stated) or '{}'}")
    if stated == actual:
        print("    -> the file encodes what its comment says")
        return 0
    print("    -> MISMATCH: the facts and the comment describe different formulas")
    return 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--disagree", action="store_true",
                    help="only rows where clingo and the reference differ")
    ap.add_argument("--example", action="store_true",
                    help="check ltl/example.asp against its stated formula")
    args = ap.parse_args(argv)

    if args.example:
        return check_example()

    print(f"{'formula':22} {'trace':10} {'trace shape':28} {'clingo':>8} {'ref':>6}")
    rows = bad = 0
    for label, formula, kinds in CASES:
        missing = [k for k in kinds if not supported(k)]
        if missing:
            print(f"{label:22} {'-':10} not defined: {', '.join(missing)}")
            continue
        got = sat_names(formula, TRACES)
        for name, trace in TRACES.items():
            g, e = name in got, holds(trace, formula, 0)
            if args.disagree and g == e:
                continue
            rows += 1
            bad += g != e
            shape = " . ".join("{" + ",".join(sorted(s)) + "}" for s in trace)
            print(f"{label:22} {name:10} {shape:28} "
                  f"{('sat' if g else '-'):>8} {('sat' if e else '-'):>6}"
                  f"{'' if g == e else '   <-- differ'}")
        if not args.disagree:
            print()

    print(f"\n{rows} rows, {bad} disagreements with the reference evaluator")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
