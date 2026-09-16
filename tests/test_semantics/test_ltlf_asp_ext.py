"""
Does `files/until_semantics/ltl2asp_ext.asp` compute the LTLf semantics it means to?

One clingo solve per (formula, semantics), with every trace in the same program,
and the whole set of satisfied traces compared against a reference evaluator.
Comparing sets rather than one trace at a time makes the failure message say
which traces the encoding got wrong in both directions - traces it wrongly
accepts and traces it wrongly rejects - instead of stopping at the first.

    conda activate arm_env
    python -m pytest tests/test_semantics/test_ltlf_asp_ext.py -q
    python -m pytest tests/test_semantics/test_ltlf_asp_ext.py -q -k weak
    python -m pytest tests/test_semantics/test_ltlf_asp_ext.py -q -k prev

Three groups:

  * strong / weak    every formula under both readings. On a finite trace the
                     future operators have two: strong wants the trace to show
                     it, weak only wants the trace not to refute it. They differ
                     only at the last instant.
  * discriminating   the (formula, trace) pairs where strong and weak actually
                     disagree, asserted individually. These are the cases that
                     would still pass if the semantics toggle were ignored
                     entirely, so they are worth naming.
  * prev             Y (strong previous, false at t=0) and Z (weak previous,
                     true at t=0). Needs `prev_rules.asp`, which supplies rules
                     ltl2asp_ext.asp does not have yet; when it grows them, drop
                     the extra file from `with_prev`.
"""
from __future__ import annotations

import shutil
from typing import Dict, List, Set

import pytest

from tests.test_semantics.ltlf_ext_harness import (
    FORMULAS, PREV_FORMULAS, TRACES, pretty, sat_ref, sat_set_expected,
    sat_set_from_clingo,
)

pytestmark = pytest.mark.skipif(shutil.which("clingo") is None,
                                reason="clingo is not on PATH")

SEMANTICS = [pytest.param(False, id="strong"), pytest.param(True, id="weak")]


def _report(label: str, weak: bool, got: Set[str], want: Set[str]) -> str:
    wrongly_sat = sorted(got - want)
    wrongly_unsat = sorted(want - got)
    lines = [f"\n{label}  [{'weak' if weak else 'strong'}]",
             f"  clingo   : {sorted(got) or '{}'}",
             f"  expected : {sorted(want) or '{}'}"]
    if wrongly_sat:
        lines.append("  satisfied but should NOT be:")
        lines += [f"    {n:14} {pretty(TRACES[n])}" for n in wrongly_sat]
    if wrongly_unsat:
        lines.append("  should be satisfied but is NOT:")
        lines += [f"    {n:14} {pretty(TRACES[n])}" for n in wrongly_unsat]
    return "\n".join(lines)


@pytest.mark.parametrize("weak", SEMANTICS)
@pytest.mark.parametrize("label", list(FORMULAS), ids=lambda s: s)
def test_sat_set_matches_reference(label: str, weak: bool) -> None:
    """The set of traces clingo satisfies is the set the semantics require."""
    formula = FORMULAS[label]
    got = sat_set_from_clingo(formula, TRACES, weak)
    want = sat_set_expected(formula, TRACES, weak)
    assert got == want, _report(label, weak, got, want)


# The pairs where the two readings genuinely disagree. Asserted separately
# because a toggle that was silently ignored would still pass every test above
# under one of the two semantics.
DISCRIMINATING = [
    (label, name)
    for label, f in FORMULAS.items()
    for name, tr in TRACES.items()
    if sat_ref(tr, f, 0, False) != sat_ref(tr, f, 0, True)
]


@pytest.mark.parametrize("label,trace_name", DISCRIMINATING,
                         ids=[f"{l}|{t}" for l, t in DISCRIMINATING])
def test_strong_and_weak_actually_differ(label: str, trace_name: str) -> None:
    """
    A case where strong and weak give opposite answers, and clingo agrees.

    Most of these are weak-accepts / strong-rejects, because weak means "not
    refuted". `!X a` is the one that goes the other way: under weak, `X a` is
    vacuously true at the end so its negation is false. If weak-next were ever
    made unconditional, every other case here would still look right and only
    the negated ones would break.
    """
    formula = FORMULAS[label]
    trace = TRACES[trace_name]
    strong = trace_name in sat_set_from_clingo(formula, {trace_name: trace},
                                               False)
    weak = trace_name in sat_set_from_clingo(formula, {trace_name: trace},
                                             True)
    assert strong == sat_ref(trace, formula, 0, False), \
        f"{label} on {pretty(trace)}: strong reading disagrees with clingo"
    assert weak == sat_ref(trace, formula, 0, True), \
        f"{label} on {pretty(trace)}: weak reading disagrees with clingo"
    assert strong != weak, \
        (f"{label} on {pretty(trace)} was supposed to tell the two readings "
         f"apart, but clingo gave {strong} for both")


@pytest.mark.parametrize("weak", SEMANTICS)
@pytest.mark.parametrize("label", list(PREV_FORMULAS), ids=lambda s: s)
def test_prev_sat_set_matches_reference(label: str, weak: bool) -> None:
    """
    Y and Z, the two past operators.

    The strong/weak toggle is passed through but must not affect these: Y and Z
    are different operators, not two readings of one, so a formula naming Y
    should mean Y whichever future semantics is selected. A failure here where
    strong and weak disagree means the prev rules got wired to the toggle.
    """
    formula = PREV_FORMULAS[label]
    got = sat_set_from_clingo(formula, TRACES, weak)
    want = sat_set_expected(formula, TRACES, weak)
    assert got == want, _report(label, weak, got, want)


def test_prev_is_insensitive_to_the_future_toggle() -> None:
    """Y stays Y under both future semantics; same for Z."""
    for label, formula in PREV_FORMULAS.items():
        strong = sat_set_from_clingo(formula, TRACES, False)
        weak = sat_set_from_clingo(formula, TRACES, True)
        assert strong == weak, (
            f"{label}: the prev rules are sensitive to semantics(strong|weak), "
            f"which would make Y silently become Z.\n"
            f"  strong: {sorted(strong)}\n  weak  : {sorted(weak)}")


def test_negated_strong_prev_equals_weak_prev_of_negation() -> None:
    """
    !Y(a) === Z(!a), the duality that makes !PREV(x) != PREV(!x).

    This is the identity the GR(1) translation cannot express, because it has
    only one PREV. Pinning it here means that if `prev_rules.asp` is ever
    "simplified" into a single operator, the reason it cannot be will be stated
    by a failing test rather than rediscovered.
    """
    neg_strong = sat_set_from_clingo(PREV_FORMULAS["!Y a"], TRACES, False)
    weak_of_neg = sat_set_from_clingo(PREV_FORMULAS["Z !a"], TRACES, False)
    strong_of_neg = sat_set_from_clingo(PREV_FORMULAS["Y !a"], TRACES, False)
    assert neg_strong == weak_of_neg, "!Y(a) should equal Z(!a)"
    assert neg_strong != strong_of_neg, (
        "!Y(a) should NOT equal Y(!a) - if these agree, the t=0 boundary is "
        "not being modelled and the whole !PREV story collapses")


LASSOS = [n for n, tr in TRACES.items() if isinstance(tr, tuple)]


@pytest.mark.parametrize("label", list(FORMULAS), ids=lambda s: s)
def test_lassos_ignore_the_future_toggle(label: str) -> None:
    """
    An infinite behaviour has one reading, not two.

    On a lasso the last instant has a successor through the back edge, so every
    `not has_succ` guard in ltl/future.asp fails and no weak rule can fire. If a
    lasso's answer changes with the toggle, a weak rule is reachable when it
    should not be - which would quietly make liveness unfalsifiable on exactly
    the traces where it is decidable.
    """
    formula = FORMULAS[label]
    lassos = {n: TRACES[n] for n in LASSOS}
    strong = sat_set_from_clingo(formula, lassos, False)
    weak = sat_set_from_clingo(formula, lassos, True)
    assert strong == weak, (
        f"{label}: lasso answers changed with the semantics toggle\n"
        f"  strong: {sorted(strong)}\n  weak  : {sorted(weak)}")


def test_past_on_a_lasso_is_flagged() -> None:
    """
    Mixing a past operator with a looping trace is marked, not silently wrong.

    A lasso folds the start of the behaviour and a point inside the cycle onto
    the same instant. Future operators cannot distinguish them; Y and Z can.
    `pred` therefore never traverses the back edge, which makes the reading at
    t=0 correct - and t=0 is where sat/1 asks. Under `always`, though, a past
    operator on a lasso describes the first pass only.

    `past_on_lasso/1` exists so that a specification hitting that caveat can be
    detected rather than quietly believed.
    """
    import subprocess
    from tests.test_semantics.ltlf_ext_harness import ENCODER, emit_formula, emit_trace

    facts, _ = emit_formula(PREV_FORMULAS["Y a"])
    program = "\n".join([
        "semantics(strong).", "symbol(a).",
        *emit_trace("finite", [set(), {"a"}]),
        *emit_trace("looping", ([set(), {"a"}], 0)),
        *facts,
        "#show past_on_lasso/1.",
    ])
    out = subprocess.run(["clingo", ENCODER, "-"], input=program,
                         capture_output=True, text=True).stdout
    assert "past_on_lasso(looping)" in out, \
        f"a past operator on a looping trace should be flagged:\n{out}"
    assert "past_on_lasso(finite)" not in out, \
        f"a finite trace carries no such caveat:\n{out}"
