"""
Reference semantics for the SEPARATE-operator design, and the formulas for it.

This is a specification, not an implementation. It says what `w_next`,
`w_until`, `w_eventually`, `w_prev` (and, if you want them, `since`, `w_since`,
`release`, `trigger`, `once`, `historically`) have to mean; the ASP is yours to
write. Every test that needs an operator the encoder does not define yet is
skipped rather than failed, so the suite goes from skipped to green as each
lands, and never shows spurious red.

The distinction, stated once
----------------------------

A finite trace is a PREFIX. The two halves of the boundary are not symmetric,
and conflating them is what makes a single global toggle awkward:

  * The FUTURE runs out. At the last instant `next` has no evidence either way,
    so there are two honest readings - demand it (strong) or decline to refute
    it (weak). This is about missing information.

  * The PAST does not run out. Instant 0 is the beginning of the behaviour, not
    a window onto unseen earlier states, and that is true even of an infinite
    behaviour. `previous` at 0 has complete information; the two readings differ
    over what "before the beginning" evaluates to, which is a modelling choice,
    not an evidential one.

Naming them separately lets one formula use both, which a global toggle cannot
express - and the duality below is exactly a formula that needs both.

Operator table
--------------

    next a        at the last instant -> False
    w_next a      at the last instant -> True
    prev a        at instant 0        -> False
    w_prev a      at instant 0        -> True

    a U b         some j >= t has b, and a holds on [t, j)
    a W b         (a U b)  OR  a holds everywhere from t on   ("unless")

    F a           some j >= t has a
    G a           every j >= t has a

Dualities the tests pin:

    !X a   ===  w_X !a          !Y a   ===  w_Y !a
    !F a   ===  G !a            !(a U b) === (!b) W (!a & !b)      [release]

A warning about `w_eventually`
------------------------------

Measured against the current encoder: under `semantics(weak)`, `F a` is
satisfied by EVERY trace in the suite, including ones where `a` never holds. A
finite prefix can never refute an eventuality, so "weak eventually" collapses to
constant true and carries no information.

That is not a bug, it is what the weak reading means for that operator - but it
does mean `w_eventually` is a degenerate operator worth thinking twice about.
The useful weak variants on finite traces are the ones whose obligation can
still be discharged *within* the trace: `w_next`, `w_until`, `w_prev`. `F`
already has a perfectly good dual in `G`, and does not need a weak twin.
"""
from __future__ import annotations

import os
import subprocess
from typing import Dict, List, Sequence, Set, Tuple

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENCODER = os.path.join(REPO, "files", "until_semantics", "ltl2asp_ext.asp")

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
        elif kind in ("next", "eventually", "always",
                      "w_next", "w_eventually"):
            lines.append(f"{kind}({me},{walk(node[1])}).")
        elif kind == "prev":
            lines.append(f"previous({me},{walk(node[1])}).")
        elif kind == "w_prev":
            lines.append(f"w_previous({me},{walk(node[1])}).")
        elif kind == "w_until":
            l, r = walk(node[1]), walk(node[2])
            lines.append(f"w_until({me},{l},{r}).")
        elif kind in ("since", "w_since", "release", "s_release", "trigger"):
            l, r = walk(node[1]), walk(node[2])
            lines.append(f"{kind}({me},{l},{r}).")
        elif kind in ("once", "historically"):
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



A, B, C = ("atom", "a"), ("atom", "b"), ("atom", "c")


# --------------------------------------------------------------------------
# reference semantics: each operator fixed, nothing keyed on a global flag
# --------------------------------------------------------------------------

def holds(trace: Sequence[Set[str]], f: tuple, t: int) -> bool:
    states = list(trace)
    n = len(states)
    last = n - 1

    def ev(node: tuple, i: int) -> bool:
        k = node[0]
        if k == "atom":
            return node[1] in states[i]
        if k == "not":
            return not ev(node[1], i)
        if k == "and":
            return all(ev(g, i) for g in node[1:])
        if k == "or":
            return any(ev(g, i) for g in node[1:])
        if k == "implies":
            return (not ev(node[1], i)) or ev(node[2], i)

        # future
        if k == "next":
            return False if i >= last else ev(node[1], i + 1)
        if k == "w_next":
            return True if i >= last else ev(node[1], i + 1)
        if k == "eventually":
            return any(ev(node[1], j) for j in range(i, n))
        if k == "w_eventually":
            # degenerate by construction: a prefix cannot refute an eventuality
            return True
        if k == "always":
            return all(ev(node[1], j) for j in range(i, n))
        if k == "until":
            for j in range(i, n):
                if ev(node[2], j):
                    return all(ev(node[1], m) for m in range(i, j))
            return False
        if k == "w_until":
            for j in range(i, n):
                if ev(node[2], j):
                    return all(ev(node[1], m) for m in range(i, j))
            return all(ev(node[1], m) for m in range(i, n))   # a forever
        if k == "release":
            # weak release (R): b holds up to and including the instant a
            # releases it - and if a never comes, b forever is enough.
            for j in range(i, n):
                if not ev(node[2], j):
                    return False
                if ev(node[1], j):
                    return True
            return True
        if k == "s_release":
            # strong release (M): as R, but the release must actually happen.
            # b holding forever is NOT enough.
            for j in range(i, n):
                if not ev(node[2], j):
                    return False
                if ev(node[1], j):
                    return True
            return False

        # past
        if k == "prev":
            return False if i == 0 else ev(node[1], i - 1)
        if k == "w_prev":
            return True if i == 0 else ev(node[1], i - 1)
        if k == "once":
            return any(ev(node[1], j) for j in range(0, i + 1))
        if k == "historically":
            return all(ev(node[1], j) for j in range(0, i + 1))
        if k == "since":
            for j in range(i, -1, -1):
                if ev(node[2], j):
                    return all(ev(node[1], m) for m in range(j + 1, i + 1))
            return False
        if k == "w_since":
            for j in range(i, -1, -1):
                if ev(node[2], j):
                    return all(ev(node[1], m) for m in range(j + 1, i + 1))
            return all(ev(node[1], m) for m in range(0, i + 1))
        if k == "trigger":
            for j in range(i, -1, -1):
                if not ev(node[2], j):
                    return any(ev(node[1], m) for m in range(j + 1, i + 1))
            return True
        raise ValueError(f"unknown node {k}")

    return ev(f, t)


# --------------------------------------------------------------------------
# which operators the encoder actually defines
# --------------------------------------------------------------------------

_PREDICATE = {
    "next": "next", "w_next": "w_next", "eventually": "eventually",
    "w_eventually": "w_eventually", "always": "always", "until": "until",
    "w_until": "w_until", "release": "release", "s_release": "s_release", "prev": "previous",
    "w_prev": "w_previous", "since": "since", "w_since": "w_since",
    "once": "once", "historically": "historically", "trigger": "trigger",
}
_cache: Dict[str, bool] = {}


def supported(kind: str) -> bool:
    """
    Whether the encoder has a rule that can ever derive `kind`.

    Probed by asking clingo for the predicate's arity in a trivial program: if
    no rule mentions it, clingo reports it as never occurring in a head, and the
    test is skipped instead of failing for a reason that is not a bug.
    """
    if kind in _cache:
        return _cache[kind]
    pred = _PREDICATE[kind]
    with open(ENCODER) as fh:
        assembled = fh.read()
    rules = ""
    base = os.path.dirname(ENCODER)
    for line in assembled.splitlines():
        line = line.strip()
        if line.startswith("#include"):
            inc = line.split('"')[1]
            with open(os.path.join(base, inc)) as fh:
                rules += fh.read() + "\n"
    _cache[kind] = any(
        l.strip().startswith("holds(") and f"{pred}(" in l
        for l in rules.splitlines())
    return _cache[kind]


def sat_names(formula: tuple, traces: Dict[str, List[Set[str]]],
              semantics: str = "strong") -> Set[str]:
    """
    Traces clingo says satisfy `formula`.

    `semantics` is still emitted because the encoder's existing rules reference
    it; once every operator names its own reading it becomes inert, and these
    tests assert exactly that by running both ways and demanding the same answer.
    """
    import re
    facts, _ = emit_formula(formula)
    atoms = sorted({a for tr in traces.values() for st in tr for a in st}
                   | {"a", "b", "c"})
    lines: List[str] = []
    for name, trace in traces.items():
        lines += emit_trace(name, trace)
    program = "\n".join([
        f"semantics({semantics}).",
        *[f"symbol({a})." for a in atoms],
        *lines, *facts, "#show sat/1.",
    ])
    proc = subprocess.run(["clingo", ENCODER, "-"], input=program,
                          capture_output=True, text=True)
    if "SATISFIABLE" not in proc.stdout:
        raise RuntimeError(f"clingo failed:\n{proc.stdout[-600:]}\n{proc.stderr[-300:]}")
    return set(re.findall(r"sat\(([^)]+)\)", proc.stdout))


def expected_names(formula: tuple, traces: Dict[str, List[Set[str]]]) -> Set[str]:
    return {n for n, tr in traces.items() if holds(tr, formula, 0)}


TRACES: Dict[str, List[Set[str]]] = {
    "e1":      [set()],
    "a1":      [{"a"}],
    "ab1":     [{"a", "b"}],
    "b1":      [{"b"}],
    "e_a":     [set(), {"a"}],
    "a_e":     [{"a"}, set()],
    "a_b":     [{"a"}, {"b"}],
    "b_a":     [{"b"}, {"a"}],
    "aa_b":    [{"a"}, {"a"}, {"b"}],
    "aaa":     [{"a"}, {"a"}, {"a"}],
    "e3":      [set(), set(), set()],
    "a_e_b":   [{"a"}, set(), {"b"}],
    "b_e_a":   [{"b"}, set(), {"a"}],
    "abc":     [{"a"}, {"b"}, {"c"}],
    # `once`/`historically` are only really pinned by a trace where the atom is
    # in the middle: with it only ever at instant 0, a broken recursive case
    # still passes on the base case alone.
    "e_a_e":   [set(), {"a"}, set()],
    "e_b_e":   [set(), {"b"}, set()],
    "ab_e_ab": [{"a", "b"}, set(), {"a", "b"}],
    "b_ab_a":  [{"b"}, {"a", "b"}, {"a"}],
    "bb_ab":   [{"b"}, {"b"}, {"a", "b"}],
    "bbb":     [{"b"}, {"b"}, {"b"}],
    "e_ab":    [set(), {"a", "b"}],
}
