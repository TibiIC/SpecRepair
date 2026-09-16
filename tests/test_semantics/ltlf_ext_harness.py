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
    # Lassos: (states, loop_start). These denote INFINITE behaviours, so the
    # strong/weak toggle must not affect them - the last instant has a
    # successor and no weak rule can fire. Any formula whose answer changes
    # between the two readings on one of these is a bug in the guards.
    "l1_a_recurs":    ([set(), {"a"}], 0),          # {} {a} {} {a} ...
    "l2_a_never":     ([set(), set()], 0),          # a never holds
    "l3_a_stuck":     ([{"b"}, {"a"}], 1),          # {b} then {a} forever
    "l4_b_stuck":     ([{"a"}, {"b"}], 1),          # {a} once, then {b} forever
    "l5_self":        ([{"a"}], 0),                 # {a} forever, one instant
    "l6_ab_cycle":    ([{"a"}, {"b"}, {"c"}], 0),   # a,b,c cycling
}


# --------------------------------------------------------------------------
# reference evaluator
# --------------------------------------------------------------------------

def sat_ref(trace, f: tuple, t: int, weak: bool) -> bool:
    """
    LTLf satisfaction of `f` at instant `t` of `trace`.

    `trace` is either a list of states (a finite prefix) or (states, loop_start)
    (a lasso, denoting an infinite behaviour).

    `weak` chooses the end-of-trace reading for the FUTURE operators and is
    ignored on a lasso, which has no end: every instant has a successor, so the
    weak cases are unreachable. Y and Z are not affected by it at all - they are
    different operators, not two readings of one.

    Eventually and Until are least fixpoints over the instants, computed by
    iteration rather than by unrolling, which is both what the ASP rules do and
    the only thing that terminates on a cycle.
    """
    states, loop = states_of(trace), loop_of(trace)
    n = len(states)

    def succ(i):
        if i + 1 < n:
            return i + 1
        return loop                        # None on a finite prefix

    def at_end(i):
        return succ(i) is None

    def ev(node, i):
        kind = node[0]
        if kind == "atom":
            return node[1] in states[i]
        if kind == "not":
            return not ev(node[1], i)
        if kind == "and":
            return all(ev(g, i) for g in node[1:])
        if kind == "or":
            return any(ev(g, i) for g in node[1:])
        if kind == "implies":
            return (not ev(node[1], i)) or ev(node[2], i)
        if kind == "next":
            return weak if at_end(i) else ev(node[1], succ(i))
        if kind == "prev":                 # Y: nothing before the beginning
            return False if i == 0 else ev(node[1], i - 1)
        if kind == "weakprev":             # Z: vacuously true there
            return True if i == 0 else ev(node[1], i - 1)
        if kind == "always":
            # safety: holds iff every REACHABLE instant satisfies it
            return all(ev(node[1], j) for j in reachable(i))
        if kind == "eventually":
            return i in lfp(lambda j: ev(node[1], j), None)
        if kind == "until":
            return i in lfp(lambda j: ev(node[2], j), lambda j: ev(node[1], j))
        raise ValueError(f"unknown node {kind}")

    def reachable(i):
        seen, stack = set(), [i]
        while stack:
            j = stack.pop()
            if j in seen:
                continue
            seen.add(j)
            k = succ(j)
            if k is not None:
                stack.append(k)
        return seen

    def lfp(goal, guard):
        """
        Least fixpoint: instants from which `goal` is eventually reached, moving
        only through instants satisfying `guard` (None = unguarded, i.e. F).

        The weak end-of-trace case is folded in here: on a finite prefix the
        last instant is accepted when the trace merely failed to refute the
        obligation - unguarded for F, and guard-holding for U.
        """
        current = set()
        while True:
            grown = set(current)
            for j in range(n):
                if goal(j):
                    grown.add(j)
                elif guard is None or guard(j):
                    k = succ(j)
                    if k is not None and k in current:
                        grown.add(j)
                    elif k is None and weak and (guard is None or guard(j)):
                        grown.add(j)
            if grown == current:
                return current
            current = grown

    return ev(f, t)


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
        elif kind in ("next", "eventually", "always"):
            lines.append(f"{kind}({me},{walk(node[1])}).")
        elif kind == "prev":            # Y, strong previous
            lines.append(f"previous({me},{walk(node[1])}).")
        elif kind == "weakprev":        # Z, weak previous
            lines.append(f"weakprevious({me},{walk(node[1])}).")
        else:
            raise ValueError(f"unknown node {kind}")
        return me

    root = walk(f)
    lines.append(f"root({root}).")
    return lines, root


def states_of(trace) -> List[Set[str]]:
    """A trace is either a list of states, or (states, loop_start)."""
    return list(trace[0]) if isinstance(trace, tuple) else list(trace)


def loop_of(trace):
    """The loop-back instant, or None when the trace is a finite prefix."""
    return trace[1] if isinstance(trace, tuple) else None


def emit_trace(name: str, trace) -> List[str]:
    states, loop = states_of(trace), loop_of(trace)
    lines = [f"trace_name({name}).", f"time(0..{len(states) - 1},{name})."]
    for i, state in enumerate(states):
        for atom in sorted(state):
            lines.append(f"trace({i},{atom},{name}).")
    if loop is not None:
        lines.append(f"loop({loop},{name}).")
    return lines


def sat_set_from_clingo(formula: tuple, traces: Dict, weak: bool) -> Set[str]:
    """
    Which of `traces` clingo reports as satisfying `formula`.

    Every trace goes into ONE program - the encoding is already parameterised by
    the trace name, so a single solve answers for all of them, and comparing the
    whole `sat` set at once is both faster and a more meaningful assertion than
    a trace at a time.
    """
    facts, _ = emit_formula(formula)
    atoms = sorted({a for tr in traces.values() for st in states_of(tr) for a in st}
                   | {"a", "b", "c"})
    trace_lines: List[str] = []
    for name, trace in traces.items():
        trace_lines += emit_trace(name, trace)
    # The encoder is a real file argument now that it holds nothing but rules,
    # so its #include paths resolve and nothing has to be stripped out of it.
    program = "\n".join([
        f"semantics({'weak' if weak else 'strong'}).",
        *[f"symbol({a})." for a in atoms],
        *trace_lines,
        *facts,
        "#show sat/1.",
    ])
    proc = subprocess.run(["clingo", ENCODER, "-"], input=program,
                          capture_output=True, text=True)
    if "SATISFIABLE" not in proc.stdout:
        raise RuntimeError(
            f"clingo did not solve the program.\nstdout:\n{proc.stdout[-800:]}"
            f"\nstderr:\n{proc.stderr[-400:]}")
    return set(re.findall(r"sat\(([^)]+)\)", proc.stdout))


def sat_set_expected(formula: tuple, traces: Dict, weak: bool) -> Set[str]:
    """The same set, from the reference evaluator."""
    return {name for name, trace in traces.items()
            if sat_ref(trace, formula, 0, weak)}


def pretty(trace) -> str:
    states, loop = states_of(trace), loop_of(trace)
    shape = " . ".join("{" + ",".join(sorted(s)) + "}" for s in states)
    return shape + (f" ->loop@{loop}" if loop is not None else "")
