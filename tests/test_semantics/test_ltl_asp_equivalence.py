"""
Does the ASP encoding mean the same thing as the LTL formula it came from?

For each case: build a Spectra module, encode it with the real `NewSpecEncoder`,
ask clingo which expressions a trace violates, and compare that against
evaluating the formula directly with `satisfies_ltl_formula`. They should agree
on every trace. Where they do not, the test prints the formula, the trace and
both verdicts, because the divergence is the result worth having.

Scope, matching what the translation currently supports - anything
`normalize_to_pattern` can convert into one of:

    EDNF | EDNF -> EDNF | G(EDNF) | G(EDNF -> EDNF)
         | G(EDNF -> F(EDNF)) | G(F(EDNF))

where EDNF is a disjunction of conjunctions of literals, each conjunct allowed
at most one `next(...)` and one `prev(...)` (each wrapping a conjunction of
literals, not just an atom). Deliberately excluded: `until`, and nested temporal
operators other than the outer `G`.

The interesting region is the trace boundary. `satisfies_ltl_formula` treats
`Next(f)` at the last timepoint and `Prev(f)` at timepoint 0 as False, and the
ASP has `weak_timepoint` guards that are applied to antecedents but not to
consequents. Cases below marked BOUNDARY exist to pin that down.

Run:
    conda activate arm_env
    python -m pytest tests/test_semantics/test_ltl_asp_equivalence.py -q
    python -m pytest tests/test_semantics/test_ltl_asp_equivalence.py -q -k simple
"""
from __future__ import annotations

import itertools
from typing import Dict, List, Sequence, Set

import pytest

from spec_repair.model.spectra_specification import SpectraSpecification
from tests.test_semantics.ltl_asp_harness import (
    asp_violated_names, describe, ltl_violated_names, spec_text,
)

# --------------------------------------------------------------------------
# trace construction
# --------------------------------------------------------------------------

def all_traces(atoms: Sequence[str], length: int) -> List[List[Set[str]]]:
    """
    Every trace of `length` over `atoms`. 2^len(atoms) states per timepoint.

    Exhaustive beats hand-picked here: the cases that break a temporal encoding
    are usually the ones nobody thinks to write down, and the spaces are small.
    """
    states = [set(c) for r in range(len(atoms) + 1)
              for c in itertools.combinations(atoms, r)]
    return [list(t) for t in itertools.product(states, repeat=length)]


def t(*rows: str) -> List[Set[str]]:
    """A trace from shorthand: t("a b", "", "a") -> [{a,b}, {}, {a}]."""
    return [set(r.split()) for r in rows]


# --------------------------------------------------------------------------
# cases
#
# (case_id, {name: spectra_formula}, env, sys, traces)
# A name starting "asm" becomes an assumption, otherwise a guarantee.
# --------------------------------------------------------------------------

AB = ["a", "b"]
ABC = ["a", "b", "c"]

# ---- Tier 1: one formula, one idea -------------------------------------- 32
SIMPLE = [
    # initial conditions (no temporal operator at all)
    ("ini-atom",            {"g": "a"},                 ["a"], ["b"]),
    ("ini-neg",             {"g": "!a"},                ["a"], ["b"]),
    ("ini-and",             {"g": "a&b"},               ["a"], ["b"]),
    ("ini-or",              {"g": "a|b"},               ["a"], ["b"]),
    ("ini-implies",         {"g": "a->b"},              ["a"], ["b"]),
    ("ini-neg-and",         {"g": "!a&!b"},             ["a"], ["b"]),
    # G over a plain formula
    ("g-atom",              {"g": "G(a)"},              ["a"], ["b"]),
    ("g-neg",               {"g": "G(!a)"},             ["a"], ["b"]),
    ("g-and",               {"g": "G(a&b)"},            ["a"], ["b"]),
    ("g-or",                {"g": "G(a|b)"},            ["a"], ["b"]),
    # G(implication), the bread and butter
    ("g-imp",               {"g": "G(a->b)"},           ["a"], ["b"]),
    ("g-imp-neg-ante",      {"g": "G(!a->b)"},          ["a"], ["b"]),
    ("g-imp-neg-cons",      {"g": "G(a->!b)"},          ["a"], ["b"]),
    ("g-imp-and-ante",      {"g": "G(a&b->c)"},         ABC[:2], ["c"]),
    ("g-imp-or-cons",       {"g": "G(a->b|c)"},         ["a"], ["b", "c"]),
    ("g-imp-or-ante",       {"g": "G(a|b->c)"},         AB, ["c"]),
    ("g-imp-and-cons",      {"g": "G(a->b&c)"},         ["a"], ["b", "c"]),
    # next  (BOUNDARY: behaviour at the last timepoint)
    ("g-next-cons",         {"g": "G(a->next(b))"},     ["a"], ["b"]),
    ("g-next-ante",         {"g": "G(next(a)->b)"},     ["a"], ["b"]),
    ("g-next-bare",         {"g": "G(next(a))"},        ["a"], ["b"]),
    ("g-next-neg-inner",    {"g": "G(a->next(!b))"},    ["a"], ["b"]),
    ("g-next-conj-inner",   {"g": "G(a->next(b&c))"},   ["a"], ["b", "c"]),
    ("g-next-disj",         {"g": "G(next(a)|b)"},      ["a"], ["b"]),
    # prev  (BOUNDARY: behaviour at timepoint 0)
    ("g-prev-cons",         {"g": "G(a->PREV(b))"},     ["a"], ["b"]),
    ("g-prev-ante",         {"g": "G(PREV(a)->b)"},     ["a"], ["b"]),
    ("g-prev-bare",         {"g": "G(PREV(a))"},        ["a"], ["b"]),
    ("g-prev-neg-inner",    {"g": "G(a->PREV(!b))"},    ["a"], ["b"]),
    ("g-prev-disj",         {"g": "G(PREV(a)|b)"},      ["a"], ["b"]),
    # justice / response
    ("gf-atom",             {"g": "G(F(a))"},           ["a"], ["b"]),
    ("gf-or",               {"g": "G(F(a|b))"},         AB, ["c"]),
    ("g-imp-f",             {"g": "G(a->F(b))"},        ["a"], ["b"]),
    ("g-imp-f-and-ante",    {"g": "G(a&b->F(c))"},      AB, ["c"]),
]

# ---- Tier 2: not canonical on the way in, must convert ------------------ 22
# to_ednf has to apply De Morgan, distribute, or group temporals. The point of
# each case is that the converted form must mean the same as what was written.
CONVERSION = [
    ("conv-demorgan-and",   {"g": "G(!(a&b)->c)"},          AB, ["c"]),
    ("conv-demorgan-or",    {"g": "G(!(a|b)->c)"},          AB, ["c"]),
    ("conv-double-neg",     {"g": "G(!(!a)->b)"},           ["a"], ["b"]),
    ("conv-distribute",     {"g": "G((a|b)&c->d)"},         ABC, ["d"]),
    ("conv-distribute-cons",{"g": "G(a->(b|c)&d)"},         ["a"], ["b", "c", "d"]),
    ("conv-nested-parens",  {"g": "G(((a)&(b))->(c))"},     AB, ["c"]),
    ("conv-group-next",     {"g": "G(next(a)&next(b)->c)"}, AB, ["c"]),
    ("conv-group-prev",     {"g": "G(PREV(a)&PREV(b)->c)"}, AB, ["c"]),
    ("conv-group-next-cons",{"g": "G(a->next(b)&next(c))"}, ["a"], ["b", "c"]),
    ("conv-neg-next",       {"g": "G(!next(a)->b)"},        ["a"], ["b"]),
    ("conv-neg-next-cons",  {"g": "G(a->!next(b))"},        ["a"], ["b"]),
    ("conv-neg-prev",       {"g": "G(!PREV(a)->b)"},        ["a"], ["b"]),
    ("conv-neg-prev-cons",  {"g": "G(a->!PREV(b))"},        ["a"], ["b"]),
    ("conv-next-and-prev",  {"g": "G(next(a)&PREV(b)->c)"}, AB, ["c"]),
    ("conv-mixed-lit-temp", {"g": "G(a&next(b)->c)"},       AB, ["c"]),
    ("conv-mixed-prev-lit", {"g": "G(PREV(a)&b->c)"},       AB, ["c"]),
    ("conv-or-of-temps",    {"g": "G(next(a)|PREV(b)->c)"}, AB, ["c"]),
    ("conv-imp-in-ante",    {"g": "G((a->b)->c)"},          AB, ["c"]),
    ("conv-neg-implies",    {"g": "G(!(a->b)->c)"},         AB, ["c"]),
    ("conv-neg-implies-cons", {"g": "G(a->!(b->c))"},       ["a"], ["b", "c"]),
    ("conv-neg-implies-nested", {"g": "G(!(a->b)|c->d)"},   ABC, ["d"]),
    ("conv-f-disj",         {"g": "G(a->F(b|c))"},          ["a"], ["b", "c"]),
    ("conv-f-conj",         {"g": "G(a->F(b&c))"},          ["a"], ["b", "c"]),
    ("conv-gf-conj",        {"g": "G(F(a&b))"},             AB, ["c"]),
]

# ---- Tier 3: one formula, genuinely complex ---------------------------- 22
COMPLEX = [
    ("cx-2disj-ante",       {"g": "G(a&b|c->d)"},                   ABC, ["d"]),
    ("cx-3disj-ante",       {"g": "G(a|b|c->d)"},                   ABC, ["d"]),
    ("cx-2disj-cons",       {"g": "G(a->b&c|d)"},                   ["a"], ["b", "c", "d"]),
    ("cx-next-in-disj",     {"g": "G(a&next(b)|c->d)"},             ABC, ["d"]),
    ("cx-prev-in-disj",     {"g": "G(PREV(a)&b|c->d)"},             ABC, ["d"]),
    ("cx-next-prev-disj",   {"g": "G(next(a)&PREV(b)|c->d)"},       ABC, ["d"]),
    ("cx-temporal-both-sides", {"g": "G(next(a)->PREV(b))"},        ["a"], ["b"]),
    ("cx-prev-ante-next-cons", {"g": "G(PREV(a)->next(b))"},        ["a"], ["b"]),
    ("cx-neg-conj-ante",    {"g": "G(!a&!b->c)"},                   AB, ["c"]),
    ("cx-neg-disj-cons",    {"g": "G(a->!b|!c)"},                   ["a"], ["b", "c"]),
    ("cx-f-with-temporal",  {"g": "G(next(a)->F(b))"},              ["a"], ["b"]),
    ("cx-f-prev-ante",      {"g": "G(PREV(a)->F(b))"},              ["a"], ["b"]),
    ("cx-f-disj-cons",      {"g": "G(a&b->F(c|d))"},                AB, ["c", "d"]),
    ("cx-gf-disj",          {"g": "G(F(a|b|c))"},                   ABC, ["d"]),
    ("cx-wide-ante",        {"g": "G(a&b&c->d)"},                   ABC, ["d"]),
    ("cx-wide-cons",        {"g": "G(a->b&c&d)"},                   ["a"], ["b", "c", "d"]),
    ("cx-next-conj2",       {"g": "G(a->next(b&c))"},               ["a"], ["b", "c"]),
    ("cx-prev-conj2",       {"g": "G(a->PREV(b&c))"},               ["a"], ["b", "c"]),
    ("cx-distribute-both",  {"g": "G((a|b)->(c|d))"},               AB, ["c", "d"]),
    ("cx-neg-next-disj",    {"g": "G(!next(a)|b->c)"},              AB, ["c"]),
    ("cx-ini-complex",      {"g": "a&!b|c"},                        ABC, ["d"]),
    ("cx-ini-implies",      {"g": "a|b->c&d"},                      AB, ["c", "d"]),
]

# ---- Tier 4: several formulas at once ---------------------------------- 12
INTEGRATION = [
    ("int-two-guarantees",  {"g1": "G(a->b)", "g2": "G(b->a)"},                       ["a"], ["b"]),
    ("int-asm-and-gar",     {"asm1": "G(a->b)", "g1": "G(b->a)"},                     ["a"], ["b"]),
    ("int-ini-plus-g",      {"g1": "!a&!b", "g2": "G(a->b)"},                         ["a"], ["b"]),
    ("int-next-pair",       {"g1": "G(a->next(b))", "g2": "G(next(a)->b)"},           ["a"], ["b"]),
    ("int-prev-pair",       {"g1": "G(a->PREV(b))", "g2": "G(PREV(a)->b)"},           ["a"], ["b"]),
    ("int-next-and-prev",   {"g1": "G(a->next(b))", "g2": "G(b->PREV(a))"},           ["a"], ["b"]),
    ("int-with-justice",    {"g1": "G(a->b)", "g2": "G(F(a))"},                       ["a"], ["b"]),
    ("int-response-pair",   {"g1": "G(a->F(b))", "g2": "G(b->F(a))"},                 ["a"], ["b"]),
    ("int-minepump-shape",  {"asm1": "!a&!b", "g1": "!c",
                             "g2": "G(a&!b->next(c))", "g3": "G(b->next(!c))"},       AB, ["c"]),
    ("int-three-guarantees",{"g1": "G(a->b)", "g2": "G(b->c)", "g3": "G(c->a)"},      ["a"], ["b", "c"]),
    ("int-conversion-mix",  {"g1": "G(!(a&b)->c)", "g2": "G(next(a)&next(b)->c)"},    AB, ["c"]),
    ("int-all-shapes",      {"g1": "a|b", "g2": "G(a->b)", "g3": "G(a->F(b))",
                             "g4": "G(F(b))"},                                        ["a"], ["b"]),
]

# ---- Known gap: confirmed by the author, not a test expectation ----------
# `!PREV(a) & PREV(b)` cannot be grouped, because !Prev(x) is not Prev(!x) under
# Spectra's real semantics, so to_ednf leaves two independent prev-references in
# one conjunct and the result is not EDNF. Intended to be supported; is not.
GAP = [
    # Confirmed by the author as a gap, not intended behaviour. !Prev(x) is not
    # Prev(!x) under Spectra's real semantics, so to_ednf cannot group two
    # independent prev-references into one conjunct and the result is not EDNF.
    ("gap-neg-prev-and-prev", {"g": "G(!PREV(a)&PREV(b)->c)"}, AB, ["c"]),
    ("gap-neg-prev-and-prev-cons", {"g": "G(a->!PREV(b)&PREV(c))"}, ["a"], ["b", "c"]),
]

ALL = (
    [("simple", *c) for c in SIMPLE]
    + [("conversion", *c) for c in CONVERSION]
    + [("complex", *c) for c in COMPLEX]
    + [("integration", *c) for c in INTEGRATION]
)


def _traces_for(atoms: Sequence[str]) -> List[List[Set[str]]]:
    """
    Exhaustive where the space is small, curated where it is not.

    Two atoms over three timepoints is 64 traces and catches every boundary
    interaction. Beyond that the product explodes, so the curated set keeps the
    cases that matter: all-false, all-true, a single true instant at each end,
    and alternation.
    """
    if len(atoms) <= 2:
        return all_traces(atoms, 3)
    first, second = atoms[0], atoms[1]
    return (
        all_traces(atoms[:2], 3)[:32]
        + [t("", "", ""), t(" ".join(atoms), " ".join(atoms), " ".join(atoms)),
           t(first, "", ""), t("", "", first), t(first, second, ""),
           t("", first, second), t(" ".join(atoms), "", " ".join(atoms))]
    )


@pytest.mark.parametrize("tier,case_id,formulas,env,sys_", [
    pytest.param(tier, cid, f, e, s, id=f"{tier}-{cid}") for tier, cid, f, e, s in ALL
])
def test_asp_matches_ltl(tier: str, case_id: str, formulas: Dict[str, str],
                         env: Sequence[str], sys_: Sequence[str]) -> None:
    atoms = list(env) + list(sys_)
    spec = SpectraSpecification.from_str(spec_text(formulas, env, sys_))
    divergences = []
    for trace in _traces_for(atoms):
        asp = asp_violated_names(spec, trace, atoms)
        ltl = ltl_violated_names(spec, trace)
        if asp != ltl:
            divergences.append((trace, asp, ltl))
    if divergences:
        trace, asp, ltl = divergences[0]
        pytest.fail(
            f"\n{case_id}: ASP and LTL disagree on {len(divergences)} of "
            f"{len(_traces_for(atoms))} traces.\n"
            f"  formulas: {formulas}\n"
            f"  first disagreement:\n{describe(trace, atoms)}\n"
            f"    ASP says violated: {asp or '{}'}\n"
            f"    LTL says violated: {ltl or '{}'}\n"
        )


@pytest.mark.xfail(reason="known gap, confirmed by the author: !PREV(x) & PREV(y) "
                          "cannot be grouped into one conjunct. Sound but too "
                          "strong - the rewrite PREV(!x & y) is in fact valid "
                          "whenever a positive PREV is present, because that "
                          "term is false at t=0 on both sides and masks the one "
                          "cell where !Prev(x) and Prev(!x) differ.",
                   strict=False)
@pytest.mark.parametrize("case_id,formulas,env,sys_", [
    pytest.param(cid, f, e, s, id=cid) for cid, f, e, s in GAP
])
def test_known_grammar_gaps(case_id: str, formulas: Dict[str, str],
                                env: Sequence[str], sys_: Sequence[str]) -> None:
    atoms = list(env) + list(sys_)
    spec = SpectraSpecification.from_str(spec_text(formulas, env, sys_))
    for trace in _traces_for(atoms):
        assert asp_violated_names(spec, trace, atoms) == ltl_violated_names(spec, trace)
