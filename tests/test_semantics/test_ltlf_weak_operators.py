"""
Specification for the separate strong/weak operators. The ASP is not written yet.

Every test here needs an operator the encoder may not define. Rather than fail,
each is SKIPPED with the operator named, so the suite reads as a to-do list that
turns green one operator at a time and never shows red for something that simply
does not exist yet:

    python -m pytest tests/test_semantics/test_ltlf_weak_operators.py -q -rs

The `-rs` prints the skip reasons, which is the list of what is left to build.

What the tests demand, in order of how much they will tell you:

  1. each operator matches its reference semantics on 14 traces
  2. the duality identities hold - these catch a boundary that is off by one
     instant, which the per-operator tests can miss
  3. strong implies weak, for every pair
  4. once every operator names its own reading, `semantics(strong|weak)` is
     inert: the same formula gives the same answer under both
"""
from __future__ import annotations

import shutil
from typing import Dict, Set

import pytest

from tests.test_semantics.ltlf_weak_ops import (
    A, B, C, TRACES, expected_names, holds, sat_names, supported,
)

pytestmark = pytest.mark.skipif(shutil.which("clingo") is None,
                                reason="clingo is not on PATH")


def needs(*kinds: str):
    """Skip unless the encoder defines every operator the case uses."""
    missing = [k for k in kinds if not supported(k)]
    return pytest.mark.skipif(
        bool(missing),
        reason=f"encoder does not define: {', '.join(missing)}")


def _report(label: str, got: Set[str], want: Set[str]) -> str:
    return (f"\n{label}"
            f"\n  clingo   : {sorted(got) or '{}'}"
            f"\n  expected : {sorted(want) or '{}'}"
            f"\n  wrongly satisfied   : {sorted(got - want) or '{}'}"
            f"\n  wrongly unsatisfied : {sorted(want - got) or '{}'}")


# --------------------------------------------------------------------------
# 1. each operator against its reference semantics
# --------------------------------------------------------------------------

CASES = [
    ("next a",          ("next", A),                        ("next",)),
    ("w_next a",        ("w_next", A),                      ("w_next",)),
    ("prev a",          ("prev", A),                        ("prev",)),
    ("w_prev a",        ("w_prev", A),                      ("w_prev",)),
    ("a U b",           ("until", A, B),                    ("until",)),
    ("a W b",           ("w_until", A, B),                  ("w_until",)),
    ("F a",             ("eventually", A),                  ("eventually",)),
    ("G a",             ("always", A),                      ("always",)),
    ("a R b",           ("release", A, B),                   ("release",)),
    ("a M b",           ("s_release", A, B),                 ("s_release",)),
    ("G(a -> b R c)",   ("always", ("implies", A, ("release", B, C))), ("always", "release")),
    ("G(a -> b M c)",   ("always", ("implies", A, ("s_release", B, C))), ("always", "s_release")),
    ("G(a -> b S c)",   ("always", ("implies", A, ("since", B, C))), ("always", "since")),
    ("G(O a -> b)",     ("always", ("implies", ("once", A), B)), ("always", "once")),
    ("G(H a -> b)",     ("always", ("implies", ("historically", A), B)), ("always", "historically")),
    ("F(a S b)",        ("eventually", ("since", A, B)),     ("eventually", "since")),
    ("O(a U b)",        ("once", ("until", A, B)),           ("once", "until")),
    ("w_next w_next a", ("w_next", ("w_next", A)),           ("w_next",)),
    ("w_prev w_prev a", ("w_prev", ("w_prev", A)),           ("w_prev",)),
    ("a U (b U c)",     ("until", A, ("until", B, C)),       ("until",)),
    ("(a W b) & (b R a)", ("and", ("w_until", A, B), ("release", B, A)),
                          ("w_until", "release")),
    ("a S b",           ("since", A, B),                    ("since",)),
    ("a B b",           ("w_since", A, B),                  ("w_since",)),
    ("O a",             ("once", A),                        ("once",)),
    ("H a",             ("historically", A),                ("historically",)),
    ("G(a -> w_next b)", ("always", ("implies", A, ("w_next", B))), ("always", "w_next")),
    ("G(a -> b W c)",   ("always", ("implies", A, ("w_until", B, C))), ("always", "w_until")),
    ("G(w_prev a -> b)", ("always", ("implies", ("w_prev", A), B)), ("always", "w_prev")),
    ("!w_prev a & prev b",
     ("and", ("not", ("w_prev", A)), ("prev", B)),          ("w_prev", "prev")),
]


@pytest.mark.parametrize("label,formula,kinds", CASES, ids=[c[0] for c in CASES])
def test_operator_matches_reference(label, formula, kinds) -> None:
    for k in kinds:
        if not supported(k):
            pytest.skip(f"encoder does not define: {k}")
    got = sat_names(formula, TRACES)
    want = expected_names(formula, TRACES)
    assert got == want, _report(label, got, want)


# --------------------------------------------------------------------------
# 2. dualities
#
# These are the tests worth having. A per-operator test can pass with a boundary
# that is off by one instant, because the reference and the encoder can be wrong
# in the same direction. A duality cannot: it relates two operators whose
# boundaries must disagree in exactly one place, so it fails loudly if either is
# shifted.
# --------------------------------------------------------------------------

DUALITIES = [
    ("!X a  ===  w_X !a",
     ("not", ("next", A)), ("w_next", ("not", A)), ("next", "w_next")),
    ("!Y a  ===  w_Y !a",
     ("not", ("prev", A)), ("w_prev", ("not", A)), ("prev", "w_prev")),
    ("!F a  ===  G !a",
     ("not", ("eventually", A)), ("always", ("not", A)), ("eventually", "always")),
    ("!G a  ===  F !a",
     ("not", ("always", A)), ("eventually", ("not", A)), ("always", "eventually")),
    ("!(a U b)  ===  (!a) R (!b)",
     ("not", ("until", A, B)),
     ("release", ("not", A), ("not", B)),
     ("until", "release")),
    ("!O a  ===  H !a",
     ("not", ("once", A)), ("historically", ("not", A)), ("once", "historically")),
    ("!H a  ===  O !a",
     ("not", ("historically", A)), ("once", ("not", A)), ("historically", "once")),
    ("!(a W b)  ===  (!a) M (!b)",
     ("not", ("w_until", A, B)),
     ("s_release", ("not", A), ("not", B)), ("w_until", "s_release")),
    ("!(a R b)  ===  (!a) U (!b)",
     ("not", ("release", A, B)),
     ("until", ("not", A), ("not", B)), ("release", "until")),
    ("!(a M b)  ===  (!a) W (!b)",
     ("not", ("s_release", A, B)),
     ("w_until", ("not", A), ("not", B)), ("s_release", "w_until")),
    ("G a  ===  !F !a",
     ("always", A), ("not", ("eventually", ("not", A))), ("always", "eventually")),
    ("H a  ===  !O !a",
     ("historically", A), ("not", ("once", ("not", A))), ("historically", "once")),
]


# Derived-operator identities: each says one operator is expressible with
# others. If an encoder implements them as independent rule sets rather than
# deriving them, these are what catch the two definitions drifting apart.
IDENTITIES = [
    ("a M b  ===  b U (a & b)",
     ("s_release", A, B), ("until", B, ("and", A, B)), ("s_release", "until")),
    ("a R b  ===  b W (a & b)",
     ("release", A, B), ("w_until", B, ("and", A, B)), ("release", "w_until")),
    ("a W b  ===  (a U b) | G a",
     ("w_until", A, B), ("or", ("until", A, B), ("always", A)),
     ("w_until", "until", "always")),
    ("F F a  ===  F a",
     ("eventually", ("eventually", A)), ("eventually", A), ("eventually",)),
    ("G G a  ===  G a",
     ("always", ("always", A)), ("always", A), ("always",)),
    ("O O a  ===  O a",
     ("once", ("once", A)), ("once", A), ("once",)),
    ("H H a  ===  H a",
     ("historically", ("historically", A)), ("historically", A), ("historically",)),
]


# Expansion laws: the fixpoint characterisation of each recursive operator.
# These are the sharpest structural tests in the suite - they pin the recursive
# rule AND its interaction with the boundary operator it unrolls through, so a
# base case at the wrong end (the `w_since`/`has_succ` mistake) fails here even
# when the operator's own test passes.
EXPANSIONS = [
    ("a U b  ===  b | (a & X(a U b))",
     ("until", A, B),
     ("or", B, ("and", A, ("next", ("until", A, B)))), ("until", "next")),
    ("a W b  ===  b | (a & wX(a W b))",
     ("w_until", A, B),
     ("or", B, ("and", A, ("w_next", ("w_until", A, B)))), ("w_until", "w_next")),
    ("a S b  ===  b | (a & Y(a S b))",
     ("since", A, B),
     ("or", B, ("and", A, ("prev", ("since", A, B)))), ("since", "prev")),
    ("a B b  ===  b | (a & wY(a B b))",
     ("w_since", A, B),
     ("or", B, ("and", A, ("w_prev", ("w_since", A, B)))), ("w_since", "w_prev")),
    ("a R b  ===  b & (a | wX(a R b))",
     ("release", A, B),
     ("and", B, ("or", A, ("w_next", ("release", A, B)))), ("release", "w_next")),
    ("a M b  ===  b & (a | X(a M b))",
     ("s_release", A, B),
     ("and", B, ("or", A, ("next", ("s_release", A, B)))), ("s_release", "next")),
]


@pytest.mark.parametrize("label,lhs,rhs,kinds", DUALITIES,
                         ids=[d[0] for d in DUALITIES])
def test_duality(label, lhs, rhs, kinds) -> None:
    for k in kinds:
        if not supported(k):
            pytest.skip(f"encoder does not define: {k}")
    left, right = sat_names(lhs, TRACES), sat_names(rhs, TRACES)
    assert left == right, _report(f"duality {label}", left, right)


@pytest.mark.parametrize("label,lhs,rhs,kinds", DUALITIES,
                         ids=[f"ref:{d[0]}" for d in DUALITIES])
def test_duality_holds_in_the_reference_too(label, lhs, rhs, kinds) -> None:
    """
    The reference satisfies the same identities.

    Without this, a duality test passing would only say the encoder is
    self-consistent with a reference that might itself be wrong on both sides.
    This needs no encoder support, so it runs immediately and is the first thing
    to trust.
    """
    for name, trace in TRACES.items():
        assert holds(trace, lhs, 0) == holds(trace, rhs, 0), (
            f"the REFERENCE breaks {label} on {name}: "
            f"{[sorted(s) for s in trace]}")


# --------------------------------------------------------------------------
# 3. strong implies weak
# --------------------------------------------------------------------------

PAIRS = [
    ("next -> w_next", ("next", A), ("w_next", A), ("next", "w_next")),
    ("prev -> w_prev", ("prev", A), ("w_prev", A), ("prev", "w_prev")),
    ("U -> W", ("until", A, B), ("w_until", A, B), ("until", "w_until")),
    ("S -> B", ("since", A, B), ("w_since", A, B), ("since", "w_since")),
]


@pytest.mark.parametrize("label,strong,weak,kinds", PAIRS,
                         ids=[p[0] for p in PAIRS])
def test_strong_implies_weak(label, strong, weak, kinds) -> None:
    """
    The weak variant accepts everything the strong one does, and then some.

    It only ever adds the vacuous case at the boundary, so anything else is a
    sign the two are not variants of the same operator at all.
    """
    for k in kinds:
        if not supported(k):
            pytest.skip(f"encoder does not define: {k}")
    s, w = sat_names(strong, TRACES), sat_names(weak, TRACES)
    assert s <= w, (
        f"{label}: strong accepted traces the weak variant rejects: "
        f"{sorted(s - w)}")
    assert s != w, (
        f"{label}: the two readings agreed on every trace, so the boundary "
        f"instant is not being distinguished")


# --------------------------------------------------------------------------
# 4. the toggle should become inert
# --------------------------------------------------------------------------

@pytest.mark.parametrize("label,formula,kinds", CASES, ids=[c[0] for c in CASES])
def test_semantics_toggle_is_inert(label, formula, kinds) -> None:
    """
    Once every operator names its own reading, the global flag means nothing.

    This is the test that says the migration is finished. While `next` and
    `previous` are still keyed on `semantics(...)` it will fail for them, which
    is the point: it names exactly which operators have not moved across yet.
    """
    for k in kinds:
        if not supported(k):
            pytest.skip(f"encoder does not define: {k}")
    strong = sat_names(formula, TRACES, "strong")
    weak = sat_names(formula, TRACES, "weak")
    assert strong == weak, (
        f"{label} still depends on semantics(strong|weak)\n"
        f"  under strong: {sorted(strong)}\n"
        f"  under weak  : {sorted(weak)}")


@pytest.mark.parametrize("label,lhs,rhs,kinds", IDENTITIES,
                         ids=[i[0] for i in IDENTITIES])
def test_identity(label, lhs, rhs, kinds) -> None:
    """One operator expressed with others, checked through clingo."""
    for k in kinds:
        if not supported(k):
            pytest.skip(f"encoder does not define: {k}")
    left, right = sat_names(lhs, TRACES), sat_names(rhs, TRACES)
    assert left == right, _report(f"identity {label}", left, right)


@pytest.mark.parametrize("label,lhs,rhs,kinds", IDENTITIES,
                         ids=[f"ref:{i[0]}" for i in IDENTITIES])
def test_identity_holds_in_the_reference_too(label, lhs, rhs, kinds) -> None:
    for name, trace in TRACES.items():
        assert holds(trace, lhs, 0) == holds(trace, rhs, 0), (
            f"the REFERENCE breaks {label} on {name}: "
            f"{[sorted(s) for s in trace]}")


@pytest.mark.parametrize("label,lhs,rhs,kinds", EXPANSIONS,
                         ids=[e[0] for e in EXPANSIONS])
def test_expansion_law(label, lhs, rhs, kinds) -> None:
    """
    The fixpoint characterisation of a recursive operator.

    Sharper than the operator's own test: it pins the recursive rule together
    with the boundary operator it unrolls through. A base case attached at the
    wrong end still satisfies the operator test on traces that never reach that
    end, but cannot satisfy the expansion law.
    """
    for k in kinds:
        if not supported(k):
            pytest.skip(f"encoder does not define: {k}")
    left, right = sat_names(lhs, TRACES), sat_names(rhs, TRACES)
    assert left == right, _report(f"expansion {label}", left, right)


@pytest.mark.parametrize("label,lhs,rhs,kinds", EXPANSIONS,
                         ids=[f"ref:{e[0]}" for e in EXPANSIONS])
def test_expansion_law_holds_in_the_reference_too(label, lhs, rhs, kinds) -> None:
    for name, trace in TRACES.items():
        assert holds(trace, lhs, 0) == holds(trace, rhs, 0), (
            f"the REFERENCE breaks {label} on {name}: "
            f"{[sorted(s) for s in trace]}")


@pytest.mark.parametrize("label,strong,weak,kinds", [
    ("M -> R", ("s_release", A, B), ("release", A, B), ("s_release", "release")),
], ids=["M -> R"])
def test_strong_release_implies_weak_release(label, strong, weak, kinds) -> None:
    """Strong release is the demanding one: M implies R, never the reverse."""
    for k in kinds:
        if not supported(k):
            pytest.skip(f"encoder does not define: {k}")
    s, w = sat_names(strong, TRACES), sat_names(weak, TRACES)
    assert s <= w, f"{label}: M accepted traces R rejects: {sorted(s - w)}"
    assert s != w, f"{label}: M and R agreed everywhere, so 'b forever' is not distinguished"
