"""
`integrate_multiple` applies a *whole learned solution*, and that is the unit
under test here - not one adaptation at a time, which is what
`test_gr1_formula.py` covers.

The distinction is the entire point. A solution's `antecedent_exception` rules
all carry a `disjunction_index` numbering the disjuncts of the **same**
antecedent, as the ASP encoder saw it. Applying them one at a time used to
rewrite the antecedent underneath the indices not yet used: narrowing disjunct 0
removed it from the list and appended the narrowed version at the end, so the
rule for index 1 landed on what index 0 had just produced, and the real disjunct
1 was left unguarded. On minepump_liveness trace 1 that unguarded disjunct was
exactly the one the violation fires through, so the search recorded a repair
that still failed its own trace.

The real FastLAS solutions that exposed this are kept verbatim under
`tests/test_files/learning_tasks/minepump_liveness_trace1/` and replayed below,
including their original rule ordering - FastLAS returns the two rules in a
different order on different runs, which is why the defect was intermittent.

Every test here fails on the pre-`integrate_all` implementation.
"""
import copy
import os
import re
from unittest import TestCase

from spec_repair.helpers.formatters.spectra_formula_formatter import SpectraFormulaFormatter
from spec_repair.model.adaptation_learned import Adaptation
from spec_repair.model.gr1_formula import GR1Formula
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.ltl_types import GR1TemporalType
from spec_repair.util.ltl_formula_util import get_disjuncts_from_disjunction

from py_ltl.formula import AtomicProposition, And, Or, Prev

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
TASK_DIR = os.path.join(REPO, "tests", "test_files", "learning_tasks",
                        "minepump_liveness_trace1")
MINEPUMP_LIVENESS = os.path.join(
    REPO, "input-files", "case-studies", "spectra", "case_study_3",
    "minepump_liveness", "original.spectra")

# The two solutions FastLAS returned, verbatim from fastlas_run_0.out and
# fastlas_run_1.out. Note run 1's ordering: index 1 first.
FASTLAS_RUN_0 = [
    "antecedent_exception(assumption3_1,0,V0,V1) :- timepoint_of_op(current,V0,V0,V1), "
    "not_holds_at(pump,V0,V1), time(V0), trace(V1).",
    "antecedent_exception(assumption3_1,1,V0,V1) :- timepoint_of_op(current,V0,V0,V1), "
    "holds_at(flag,V0,V1), time(V0), trace(V1).",
]
FASTLAS_RUN_1 = [
    "antecedent_exception(assumption3_1,1,V0,V1) :- timepoint_of_op(current,V0,V0,V1), "
    "holds_at(highwater,V0,V1), time(V0), trace(V1).",
    "antecedent_exception(assumption3_1,0,V0,V1) :- timepoint_of_op(current,V0,V0,V1), "
    "not_holds_at(methane,V0,V1), time(V0), trace(V1).",
]


def antecedent_disjuncts(formula, formatter):
    """
    The antecedent's disjuncts, in the order `disjunction_index` numbers them.

    Uses the library's own splitter rather than parsing the serialised string.
    `disjunction_index` indexes exactly this list - it is what
    `_integrate_antecedent_exceptions` indexes into - so asserting against it
    tests the thing that matters, and sidesteps the fact that `Or` is
    left-nested and the serialiser wraps bodies in a variable number of parens.
    """
    return [d.format(formatter)
            for d in get_disjuncts_from_disjunction(formula.antecedent)]


class TestIntegrateMultipleOnRealSolutions(TestCase):
    """The minepump_liveness case, replayed from the captured FastLAS output."""

    def setUp(self):
        self.spec = SpectraSpecification.from_file(MINEPUMP_LIVENESS)
        self.formatter = SpectraFormulaFormatter()

    def original_antecedent_disjuncts(self):
        return antecedent_disjuncts(
            self.spec.get_formula("assumption3_1"), self.formatter)

    def test_the_fixture_files_are_present(self):
        """The captured task and solver output are part of the repo, not a memory."""
        for name in ("task.las", "task.fastlas.las", "solutions.txt",
                     "fastlas_run_0.out", "fastlas_run_1.out", "README.md"):
            self.assertTrue(os.path.exists(os.path.join(TASK_DIR, name)),
                            f"missing fixture {name}")

    def test_captured_solutions_have_one_rule_per_disjunct_index(self):
        """
        The precondition for the whole bug: FastLAS returns *two* rules, one per
        index. If this ever returns one, the learner - not the integration - is
        wrong, because a single exception cannot cover the example.
        """
        for label, rules in (("run_0", FASTLAS_RUN_0), ("run_1", FASTLAS_RUN_1)):
            indices = sorted(int(re.search(r"assumption3_1,(\d+)", r).group(1))
                             for r in rules)
            self.assertEqual([0, 1], indices, f"{label} does not cover both disjuncts")

    def test_assumption3_1_antecedent_really_is_a_disjunction(self):
        """Without two disjuncts there is no index to get wrong."""
        self.assertEqual(2, len(self.original_antecedent_disjuncts()))

    def test_every_indexed_disjunct_is_narrowed(self):
        """
        The defect, stated directly: after applying a whole solution, no disjunct
        may survive untouched. Under the old sequential application, disjunct 1
        came through verbatim.
        """
        for label, rules in (("run_0", FASTLAS_RUN_0), ("run_1", FASTLAS_RUN_1)):
            spec = copy.deepcopy(self.spec)
            spec.integrate_multiple([Adaptation.from_str(r) for r in rules])
            after = antecedent_disjuncts(
                spec.get_formula("assumption3_1"), self.formatter)
            for original in self.original_antecedent_disjuncts():
                self.assertNotIn(
                    original, after,
                    f"{label}: disjunct {original!r} survived unnarrowed - the "
                    f"violation would still pass through it")

    def test_result_is_independent_of_rule_order(self):
        """
        FastLAS lists the two rules in either order between runs. The repaired
        specification must not depend on which arrives first.
        """
        rules = [Adaptation.from_str(r) for r in FASTLAS_RUN_0]
        forwards = copy.deepcopy(self.spec)
        forwards.integrate_multiple(rules)
        backwards = copy.deepcopy(self.spec)
        backwards.integrate_multiple(list(reversed(rules)))
        self.assertEqual(
            forwards.get_formula("assumption3_1").to_str(self.formatter),
            backwards.get_formula("assumption3_1").to_str(self.formatter))

    def test_disjunct_count_is_preserved_for_single_atom_rules(self):
        """
        One atom per rule narrows each disjunct in place, so the antecedent keeps
        its arity. The old code also kept it at two, but with the *wrong* two -
        which is why arity alone was never enough to notice.
        """
        spec = copy.deepcopy(self.spec)
        spec.integrate_multiple([Adaptation.from_str(r) for r in FASTLAS_RUN_0])
        after = antecedent_disjuncts(
            spec.get_formula("assumption3_1"), self.formatter)
        self.assertEqual(2, len(after))

    def test_narrowings_land_on_the_disjunct_the_learner_named(self):
        """
        The sharp version: index 0 is `highwater & PREV(!pump)` and index 1 is
        `highwater & !pump`, so run 0's `pump=false` exception must attach to the
        PREV disjunct and its `flag=true` exception to the other. The old code
        attached both to the PREV disjunct.

        Atoms are inverted on the way in (`replace_false_true`) - an exception
        fires when the learned condition holds, so the disjunct is narrowed by
        its negation.
        """
        spec = copy.deepcopy(self.spec)
        spec.integrate_multiple([Adaptation.from_str(r) for r in FASTLAS_RUN_0])
        after = antecedent_disjuncts(
            spec.get_formula("assumption3_1"), self.formatter)
        prev_disjunct = [d for d in after if "PREV" in d]
        plain_disjunct = [d for d in after if "PREV" not in d]
        self.assertEqual(1, len(prev_disjunct), after)
        self.assertEqual(1, len(plain_disjunct), after)
        self.assertIn("pump=true", prev_disjunct[0])
        self.assertIn("flag=false", plain_disjunct[0])


class TestIntegrateMultipleSemantics(TestCase):
    """Order-independence and grouping, on formulas small enough to read."""

    def setUp(self):
        self.formatter = SpectraFormulaFormatter()

    @staticmethod
    def two_disjunct_formula():
        return GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=Or(AtomicProposition("a", True), AtomicProposition("b", True)),
            consequent=AtomicProposition("c", True),
        )  # G((a|b) -> c)

    @staticmethod
    def exception(index, atom):
        return Adaptation(type='antecedent_exception', formula_name='a_always',
                          disjunction_index=index,
                          atom_temporal_operators=[('current', atom)])

    def test_both_orders_agree(self):
        expected = "G((((a=true&d=true)|(b=true&e=true))->c=true))"
        for order in ([0, 1], [1, 0]):
            formula = self.two_disjunct_formula()
            adaptations = {0: self.exception(0, 'd=false'),
                           1: self.exception(1, 'e=false')}
            formula.integrate_all([adaptations[i] for i in order])
            self.assertEqual(expected, formula.to_str(self.formatter),
                             f"order {order}")

    def test_an_unnamed_disjunct_is_carried_over_untouched(self):
        """A solution that excepts only index 0 must leave index 1 exactly as it was."""
        formula = self.two_disjunct_formula()
        formula.integrate_all([self.exception(0, 'd=false')])
        self.assertEqual("G((((a=true&d=true)|b=true)->c=true))",
                         formula.to_str(self.formatter))

    def test_three_disjuncts_keep_their_positions(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=Or(Or(AtomicProposition("a", True), AtomicProposition("b", True)),
                          AtomicProposition("c", True)),
            consequent=AtomicProposition("z", True),
        )
        formula.integrate_all([self.exception(2, 'd=false'), self.exception(0, 'e=false')])
        result = formula.to_str(self.formatter)
        parts = antecedent_disjuncts(formula, self.formatter)
        self.assertEqual(3, len(parts), result)
        self.assertIn("e=true", parts[0])      # index 0 narrowed
        self.assertEqual("b=true", parts[1])   # index 1 untouched, still in place
        self.assertIn("d=true", parts[2])      # index 2 narrowed

    def test_temporal_operators_are_preserved_per_disjunct(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=Or(Prev(AtomicProposition("a", True)), AtomicProposition("b", True)),
            consequent=AtomicProposition("c", True),
        )
        formula.integrate_all([self.exception(0, 'd=false'), self.exception(1, 'e=false')])
        parts = antecedent_disjuncts(formula, self.formatter)
        self.assertIn("PREV", parts[0])
        self.assertNotIn("PREV", parts[1])

    def test_adaptations_are_grouped_by_formula_name(self):
        """
        `integrate_multiple` dispatches per formula: two formulas in one solution
        must each receive only their own adaptations.
        """
        spec = SpectraSpecification.from_file(MINEPUMP_LIVENESS)
        before_a1 = spec.get_formula("assumption1_1").to_str(spec._formater)
        spec.integrate_multiple([Adaptation.from_str(r) for r in FASTLAS_RUN_0])
        self.assertEqual(before_a1,
                         spec.get_formula("assumption1_1").to_str(spec._formater),
                         "a solution for assumption3_1 modified assumption1_1")
