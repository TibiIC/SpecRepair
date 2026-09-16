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
  * prev             `previous`, read as Y under strong (false before the
                     beginning) and Z under weak (vacuously true there).
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




def test_previous_reads_as_y_under_strong_and_z_under_weak() -> None:
    """
    There is one past operator, and the semantics toggle chooses its reading.

    Under `semantics(strong)` `previous` is Y - false before the beginning, so
    `PREV a` never holds at instant 0. Under `semantics(weak)` it is Z, and it
    holds there vacuously. The two readings must therefore differ on exactly the
    traces where instant 0 is the only place the operator could fire.

    This is the boundary that makes !PREV(x) different from PREV(!x), which is
    why the GR(1) translation in spec_repair leaves !PREV opaque rather than
    pushing the negation through. If these two ever agree, t=0 has stopped being
    special and that argument is gone.
    """
    strong = sat_set_from_clingo(PREV_FORMULAS["PREV a"], TRACES, False)
    weak = sat_set_from_clingo(PREV_FORMULAS["PREV a"], TRACES, True)
    assert strong != weak, (
        "PREV read the same under both semantics, so t=0 is not being treated "
        "as the beginning of the trace")
    assert strong <= weak, (
        "the weak reading should accept everything the strong one does, and "
        "then some - it only adds the vacuous case at instant 0")


def test_negated_prev_differs_from_prev_of_negation() -> None:
    """
    !PREV(a) is not PREV(!a), under either reading.

    At instant 0 one of them is vacuous and the other is not, whichever way the
    toggle is set, so the two can never coincide. This is the identity the GR(1)
    normaliser must refuse, pinned here so that a future "simplification" that
    pushes negation through PREV fails a test instead of passing review.
    """
    for weak in (False, True):
        neg_prev = sat_set_from_clingo(PREV_FORMULAS["!PREV a"], TRACES, weak)
        prev_neg = sat_set_from_clingo(PREV_FORMULAS["PREV !a"], TRACES, weak)
        assert neg_prev != prev_neg, (
            f"[{'weak' if weak else 'strong'}] !PREV(a) and PREV(!a) agreed on "
            f"every trace, so the instant-0 boundary is not being modelled")

