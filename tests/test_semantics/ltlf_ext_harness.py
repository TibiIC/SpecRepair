#!/usr/bin/env python3
"""
Harness for files/until_semantics/ltl2asp_ext.asp - formulas, traces, and the
reference LTLf evaluator the tests compare clingo against.

Adding a formula is one line in FORMULAS. The kit numbers the AST nodes, emits
the fact block, runs clingo once per semantics, and compares the answer against
a reference LTLf evaluator written here. A mismatch is printed loudly; it means
the ASP rules and the intended semantics have parted company.

Run through pytest (tests/test_semantics/test_ltlf_asp_ext.py), or
interactively for the full table:

    python files/until_semantics/ltlf_testkit.py

STRONG vs WEAK, which is the point of the exercise. On a finite trace the
future operators have two readings, and they differ only at the END:

    strong  "the trace must show it"        X a at the last instant  -> False
                                            F a never seen           -> False
                                            a U b, b never seen      -> False
    weak    "the trace must not refute it"  X a at the last instant  -> True
                                            F a never seen           -> True
                                            a U b, a holds to the end-> True

G needs no variant: one counterexample inside the trace refutes it, and no
extension can repair that, so both readings agree. That is why ltl2asp_ext.asp
has no `semantics(...)` guard on the `always` rule, and it is correct not to.

PREV is the mirror image and is NOT symmetric with next. A finite trace is a
prefix: the future is open, but the past is closed - t=0 really is the
beginning, not a window onto unseen earlier states. So:

    Y a  ("yesterday", strong previous)  at t=0 -> False
    Z a  ("weak yesterday"/"before")     at t=0 -> True

Both are primitive in past-LTL (Lichtenstein/Pnueli/Zuck, "The Glory of the
Past", 1985; Manna & Pnueli 1992) precisely because neither defines the other:
they are duals, !Y(x) === Z(!x). Spectra's PREV is Y - measured, not assumed:
`G(PREV(a))` is unrealizable there while `G(a)` is realizable, which can only
happen if PREV is false at t=0.

The PREV cases below are written and expected-valued already, but skipped until
ltl2asp_ext.asp grows `prev`/`weakprev` facts. The rules it would need are in
prev_rules.asp next to this file.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
from typing import Dict, List, Optional, Sequence, Set, Tuple

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORKSPACE = os.path.join(REPO, "files", "until_semantics")
ENCODER = os.path.join(WORKSPACE, "ltl2asp_ext.asp")
PREV_RULES = os.path.join(WORKSPACE, "prev_rules.asp")

# --------------------------------------------------------------------------
# formulas: a tiny AST as nested tuples
#   ("atom", "a") ("not", f) ("and", f, g, ...) ("or", f, g, ...)
#   ("implies", f, g) ("next", f) ("until", f, g) ("eventually", f)
#   ("always", f) ("prev", f) ("weakprev", f)
# --------------------------------------------------------------------------
A, B, C = ("atom", "a"), ("atom", "b"), ("atom", "c")

FORMULAS: Dict[str, tuple] = {
    # the one already in the file, as a control
    "G(a -> b|c)":        ("always", ("implies", A, ("or", B, C))),
    # every temporal operator in one formula, which the current file lacks
    "G(a -> b U c) & F(X a)": ("and",
                               ("always", ("implies", A, ("until", B, C))),
                               ("eventually", ("next", A))),
    # one operator at a time, so a failure localises
    "X a":                ("next", A),
    "X X a":              ("next", ("next", A)),
    "F a":                ("eventually", A),
    "G a":                ("always", A),
    "a U b":              ("until", A, B),
    "G F a":              ("always", ("eventually", A)),
    "F G a":              ("eventually", ("always", A)),
    "G(a -> X b)":        ("always", ("implies", A, ("next", B))),
    "G(a -> F b)":        ("always", ("implies", A, ("eventually", B))),
    "G(a -> b U c)":      ("always", ("implies", A, ("until", B, C))),
    "!X a":               ("not", ("next", A)),
    "X !a":               ("next", ("not", A)),
    "(a U b) | X c":      ("or", ("until", A, B), ("next", C)),
    "G(a) -> F(b)":       ("implies", ("always", A), ("eventually", B)),
}

# Written now, run once ltl2asp_ext.asp learns `prev`. Y is strong previous,
# Z is weak previous; the pair is the whole point of including both.
PREV_FORMULAS: Dict[str, tuple] = {
    "Y a":                ("prev", A),
    "Z a":                ("weakprev", A),
    "!Y a":               ("not", ("prev", A)),
    "Y !a":               ("prev", ("not", A)),
    "Z !a":               ("weakprev", ("not", A)),
    "G(a -> Y b)":        ("always", ("implies", A, ("prev", B))),
    "G(Y a -> b)":        ("always", ("implies", ("prev", A), B)),
    "G(!Y a & Y b -> c)": ("always", ("implies", ("and", ("not", ("prev", A)),
                                                  ("prev", B)), C)),
    "Y(a & b)":           ("prev", ("and", A, B)),
    "G(Y a | b)":         ("always", ("or", ("prev", A), B)),
}

# --------------------------------------------------------------------------
# traces: name -> list of states, each the set of atoms TRUE at that instant
# --------------------------------------------------------------------------
TRACES: Dict[str, List[Set[str]]] = {
    "t1_empty1":      [set()],                          # one instant, nothing
    "t2_a1":          [set(), {"a"}],                    # the file's g1
    "t3_c1":          [set(), {"c"}],                    # the file's g2
    "t4_a0":          [{"a"}],                           # one instant, a
    "t5_ab0":         [{"a", "b"}],
    "t6_a0_b1":       [{"a"}, {"b"}],
    "t7_b0_c1":       [{"b"}, {"c"}],
    "t8_bb_c":        [{"b"}, {"b"}, {"c"}],             # b until c
    "t9_bbb":         [{"b"}, {"b"}, {"b"}],             # b forever, c never
    "t10_all3":       [{"a", "b", "c"}, {"a", "b", "c"}],
    "t11_a_last":     [set(), set(), {"a"}],
    "t12_a_first":    [{"a"}, set(), set()],
    "t13_alt":        [{"a"}, {"b"}, {"a"}, {"b"}],
    "t14_empty3":     [set(), set(), set()],
}


# --------------------------------------------------------------------------
# reference evaluator
# --------------------------------------------------------------------------

def sat_ref(f: tuple, trace: Sequence[Set[str]], t: int, weak: bool) -> bool:
    """
    LTLf satisfaction of `f` at instant `t`, in the strong or weak reading.

    `weak` flips only the end-of-trace cases. Everything inside the trace is the
    same in both readings, which is why a formula that never reaches the last
    instant gives the same answer either way.
    """
    last = len(trace) - 1
    kind = f[0]
    if kind == "atom":
        return f[1] in trace[t]
    if kind == "not":
        return not sat_ref(f[1], trace, t, weak)
    if kind == "and":
        return all(sat_ref(g, trace, t, weak) for g in f[1:])
    if kind == "or":
        return any(sat_ref(g, trace, t, weak) for g in f[1:])
    if kind == "implies":
        return (not sat_ref(f[1], trace, t, weak)) or sat_ref(f[2], trace, t, weak)
    if kind == "next":
        if t >= last:
            return weak                      # nothing after the end to check
        return sat_ref(f[1], trace, t + 1, weak)
    if kind == "eventually":
        if any(sat_ref(f[1], trace, j, weak) for j in range(t, len(trace))):
            return True
        return weak                          # could still happen later
    if kind == "always":
        # no weak variant: a counterexample inside the trace is final
        return all(sat_ref(f[1], trace, j, weak) for j in range(t, len(trace)))
    if kind == "until":
        for j in range(t, len(trace)):
            if sat_ref(f[2], trace, j, weak):
                return all(sat_ref(f[1], trace, k, weak) for k in range(t, j))
        # right side never seen: weak accepts if the left side held throughout
        return weak and all(sat_ref(f[1], trace, k, weak) for k in range(t, len(trace)))
    if kind == "prev":                       # Y, strong: false at the beginning
        return False if t == 0 else sat_ref(f[1], trace, t - 1, weak)
    if kind == "weakprev":                   # Z, weak: true at the beginning
        return True if t == 0 else sat_ref(f[1], trace, t - 1, weak)
    raise ValueError(f"unknown node {kind}")


# --------------------------------------------------------------------------
# AST -> ASP facts
# --------------------------------------------------------------------------

def emit_formula(f: tuple) -> Tuple[List[str], int]:
    """Fact lines for `f`, and the id of its root node."""
    lines: List[str] = []
    counter = [0]

    def walk(node: tuple) -> int:
        me = counter[0]
        counter[0] += 1
        kind = node[0]
        if kind == "atom":
            lines.append(f"atomic({me},{node[1]}).")
        elif kind in ("not",):
            lines.append(f"negate({me},{walk(node[1])}).")
        elif kind == "and":
            for child in node[1:]:
                lines.append(f"conjunction({me},{walk(child)}).")
        elif kind == "or":
            for child in node[1:]:
                lines.append(f"disjunction({me},{walk(child)}).")
        elif kind == "implies":
            l, r = walk(node[1]), walk(node[2])
            lines.append(f"implies({me},{l},{r}).")
        elif kind == "until":
            l, r = walk(node[1]), walk(node[2])
            lines.append(f"until({me},{l},{r}).")
        elif kind in ("next", "eventually", "always", "prev", "weakprev"):
            lines.append(f"{kind}({me},{walk(node[1])}).")
        else:
            raise ValueError(f"unknown node {kind}")
        return me

    root = walk(f)
    lines.append(f"root({root}).")
    return lines, root


def emit_trace(name: str, trace: Sequence[Set[str]]) -> List[str]:
    lines = [f"trace_name({name}).", f"time(0..{len(trace) - 1},{name})."]
    for i, state in enumerate(trace):
        for atom in sorted(state):
            lines.append(f"trace({i},{atom},{name}).")
    return lines


def encoder_rules(with_prev: bool) -> str:
    """The rule block, with the file's own traces/formula/semantics stripped."""
    with open(ENCODER) as fh:
        body = fh.read()
    keep = []
    for line in body.splitlines():
        s = line.strip()
        if not s or s.startswith("%"):
            continue
        if s.startswith(("semantics(", "trace_name(", "time(", "trace(",
                         "root(", "always(0", "implies(1", "atomic(", "symbol(",
                         "disjunction(", "#show")):
            continue
        keep.append(line)
    rules = "\n".join(keep)
    if with_prev and os.path.exists(PREV_RULES):
        with open(PREV_RULES) as fh:
            rules += "\n" + fh.read()
    return rules


def sat_set_from_clingo(formula: tuple, traces: Dict[str, List[Set[str]]],
                        weak: bool, with_prev: bool) -> Set[str]:
    """
    Which of `traces` clingo reports as satisfying `formula`.

    Every trace goes into ONE program - the encoding is already parameterised by
    the trace name, so a single solve answers for all of them, and comparing the
    whole `sat` set at once is both faster and a more meaningful assertion than
    a trace at a time.
    """
    facts, _ = emit_formula(formula)
    atoms = sorted({a for st in traces.values() for s in st for a in s} | {"a", "b", "c"})
    trace_lines: List[str] = []
    for name, trace in traces.items():
        trace_lines += emit_trace(name, trace)
    program = "\n".join([
        encoder_rules(with_prev),
        f"semantics({'weak' if weak else 'strong'}).",
        *[f"symbol({a})." for a in atoms],
        *trace_lines,
        *facts,
        "#show sat/1.",
    ])
    proc = subprocess.run(["clingo", "-"], input=program,
                          capture_output=True, text=True)
    if "SATISFIABLE" not in proc.stdout:
        raise RuntimeError(
            f"clingo did not solve the program.\nstdout:\n{proc.stdout[-800:]}"
            f"\nstderr:\n{proc.stderr[-400:]}")
    return set(re.findall(r"sat\(([^)]+)\)", proc.stdout))


def sat_set_expected(formula: tuple, traces: Dict[str, List[Set[str]]],
                     weak: bool) -> Set[str]:
    """The same set, from the reference evaluator."""
    return {name for name, trace in traces.items()
            if sat_ref(formula, trace, 0, weak)}


def pretty(trace: Sequence[Set[str]]) -> str:
    return " . ".join("{" + ",".join(sorted(s)) + "}" for s in trace)
