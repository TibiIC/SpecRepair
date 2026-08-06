"""
Tests for merging semantically distinct specifications.

The interesting case is two repairs that are *not* equivalent: the merge has to
keep both sets of behaviour rather than collapse to either input, and when
conjoining their guarantees over-constrains the system it has to split the set
and merge each half separately, instead of returning something unrealisable.
"""
from typing import List
from unittest import mock

from spec_repair.diagnosis.solution_merging import NotAWeakeningError, \
    UnrealisableInputError, check_weakens_original, merge_solutions, merge_two_solutions, \
    warn_if_merge_undid_the_weakening
from spec_repair.components.oracles.spectra_gr1_oracle import SpectraGR1Oracle
from spec_repair.interfaces.ispecification import ISpecification
from spec_repair.ltl_types import GR1FormulaType
from spec_repair.model.spectra_specification import SpectraSpecification
from tests.base_test_case import BaseTestCase
from tests.test_common_utility_strings.specs import spec_asm_eq_gar_weaker, spec_fixed_imperf, \
    spec_fixed_perf, spec_strong


class TestSolutionMerging(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.oracle = SpectraGR1Oracle()
        cls.strong = SpectraSpecification.from_str(spec_strong)
        # Two repairs of the same original that are NOT equivalent to each other.
        cls.repair_a = SpectraSpecification.from_str(spec_fixed_perf)
        cls.repair_b = SpectraSpecification.from_str(spec_fixed_imperf)

    def test_the_two_repairs_really_are_semantically_distinct(self):
        """Guards the premise of every other test in this file."""
        self.assertNotEqual(self.repair_a, self.repair_b)
        self.assertFalse(self.repair_a.equivalent_to(self.repair_b, GR1FormulaType.GAR))

    def test_merging_distinct_specs_returns_realisable_solutions(self):
        merged: List[ISpecification] = merge_solutions([self.repair_a, self.repair_b])
        self.assertGreaterEqual(len(merged), 1)
        for spec in merged:
            self.assertTrue(self.oracle.is_realisable(spec),
                            "every merged solution must be realisable")

    def test_merged_result_implies_each_distinct_input(self):
        """
        Merging conjoins guarantees, so the merge is at least as strong as every
        input: merged => input, not the other way round. That is what makes the
        result a common solution rather than a pick of one side.
        """
        merged = merge_solutions([self.repair_a, self.repair_b])
        for spec in merged:
            self.assertTrue(spec.implies(self.repair_a, GR1FormulaType.GAR))
            self.assertTrue(spec.implies(self.repair_b, GR1FormulaType.GAR))

    def test_merging_distinct_specs_is_strictly_stronger_than_one_of_them(self):
        """
        The inputs are distinct, so the conjunction cannot be equivalent to both.
        Here repair_a's guarantee is the stronger one, so the merge lands on
        repair_a and is strictly stronger than repair_b.
        """
        merged = merge_solutions([self.repair_a, self.repair_b])
        for spec in merged:
            strictly_stronger_than_some_input = any(
                spec.implies(other, GR1FormulaType.GAR)
                and not other.implies(spec, GR1FormulaType.GAR)
                for other in (self.repair_a, self.repair_b)
            )
            self.assertTrue(strictly_stronger_than_some_input,
                            "merging distinct specs must strengthen at least one of them")

    def test_merging_equivalent_specs_is_idempotent(self):
        """A spec merged with itself must not gain or lose behaviour."""
        merged = merge_solutions([self.repair_a, self.repair_a])
        self.assertEqual(1, len(merged))
        self.assertTrue(merged[0].equivalent_to(self.repair_a, GR1FormulaType.GAR))
        self.assertTrue(merged[0].equivalent_to(self.repair_a, GR1FormulaType.ASM))

    def test_merge_is_order_insensitive_up_to_equivalence(self):
        forward = merge_solutions([self.repair_a, self.repair_b])
        backward = merge_solutions([self.repair_b, self.repair_a])
        self.assertEqual(len(forward), len(backward))
        for spec in forward:
            self.assertTrue(
                any(spec.equivalent_to(other, GR1FormulaType.GAR) for other in backward),
                "merging in the opposite order should give equivalent solutions",
            )

    def test_three_distinct_specs_merge(self):
        third = SpectraSpecification.from_str(spec_asm_eq_gar_weaker)
        merged = merge_solutions([self.repair_a, self.repair_b, third])
        self.assertGreaterEqual(len(merged), 1)
        for spec in merged:
            self.assertTrue(self.oracle.is_realisable(spec))

    def test_merge_two_solutions_alias_matches_n_ary_call(self):
        via_alias = merge_two_solutions(self.repair_a, self.repair_b)
        via_n_ary = merge_solutions([self.repair_a, self.repair_b])
        self.assertEqual([s.to_str() for s in via_n_ary], [s.to_str() for s in via_alias])

    # ---------------- og_spec is optional ----------------

    def test_og_spec_is_optional(self):
        """The whole point of the parameter being Optional: omitting it works."""
        without = merge_solutions([self.repair_a, self.repair_b])
        with_og = merge_solutions([self.repair_a, self.repair_b], og_spec=self.strong)
        self.assertEqual([s.to_str() for s in without], [s.to_str() for s in with_og])

    def test_og_spec_none_explicitly_is_accepted(self):
        merged = merge_solutions([self.repair_a, self.repair_b], og_spec=None)
        self.assertGreaterEqual(len(merged), 1)

    def test_non_weakening_warns_by_default_but_still_merges(self):
        """
        Uses repair_b as the "original": spec_strong is strictly stronger than
        it, so repair_b does not imply spec_strong and spec_strong is therefore
        not a weakening of it. Default behaviour is to warn and carry on,
        matching what the directory-merging path has always done.
        """
        self.assertFalse(check_weakens_original(self.strong, self.repair_b))
        with self.assertLogs("spec_repair.diagnosis.solution_merging", level="WARNING"):
            merged = merge_solutions([self.strong, self.repair_a], og_spec=self.repair_b)
        self.assertGreaterEqual(len(merged), 1)

    def test_non_weakening_raises_in_strict_mode(self):
        with self.assertRaises(NotAWeakeningError):
            merge_solutions([self.strong, self.repair_a], og_spec=self.repair_b, strict=True)

    def test_check_weakens_original_passes_for_a_genuine_weakening(self):
        self.assertTrue(check_weakens_original(self.repair_a, self.strong))
        self.assertTrue(check_weakens_original(self.repair_b, self.strong))

    # ---------------- input validation ----------------

    def test_fewer_than_two_specs_is_rejected(self):
        for specs in ([], [self.repair_a]):
            with self.subTest(n=len(specs)):
                with self.assertRaises(ValueError):
                    merge_solutions(specs)

    def test_unrealisable_input_is_rejected(self):
        class _NeverRealisable:
            @staticmethod
            def is_realisable(_spec):
                return False

        with self.assertRaises(UnrealisableInputError):
            merge_solutions([self.repair_a, self.repair_b], oracle=_NeverRealisable())

    # ---------------- large / expensive merges ----------------

    def test_verify_inputs_can_be_skipped(self):
        """
        Skipping input verification must not change the result - it only avoids
        re-establishing that specs from the repair search are realisable.
        """
        checked = merge_solutions([self.repair_a, self.repair_b], verify_inputs=True)
        unchecked = merge_solutions([self.repair_a, self.repair_b], verify_inputs=False)
        self.assertEqual([s.to_str() for s in checked], [s.to_str() for s in unchecked])

    def test_unrealisable_merge_splits_instead_of_tearing_down(self):
        """
        The whole point of divide and conquer: an unrealisable merge is split,
        and the expensive unrealisable-core teardown is only ever reached for a
        single specification - never for the large merge.
        """
        torn_down = []

        class _NeverRealisable:
            @staticmethod
            def is_realisable(_spec):
                return False

        def _record_teardown(spec):
            torn_down.append(spec)
            return [spec]

        with mock.patch("spec_repair.diagnosis.solution_merging."
                        "get_all_trivial_solutions_guarantee_only", _record_teardown):
            merged = merge_solutions([self.repair_a, self.repair_b],
                                     oracle=_NeverRealisable(), verify_inputs=False)

        # Split all the way down to singletons, so every teardown is of one spec.
        self.assertEqual(2, len(torn_down))
        for spec in torn_down:
            self.assertIn(spec.to_str(), (self.repair_a.to_str(), self.repair_b.to_str()))
        self.assertEqual(2, len(merged))

    def test_realisable_merge_costs_a_single_check_and_never_tears_down(self):
        """The common case: one realisability check, no split, no core search."""
        checks = []

        class _CountingOracle:
            @staticmethod
            def is_realisable(_spec):
                checks.append(_spec)
                return True

        def _fail(_spec):
            raise AssertionError("teardown must not be reached for a realisable merge")

        with mock.patch("spec_repair.diagnosis.solution_merging."
                        "get_all_trivial_solutions_guarantee_only", _fail):
            merged = merge_solutions([self.repair_a, self.repair_b],
                                     oracle=_CountingOracle(), verify_inputs=False)
        self.assertEqual(1, len(merged))
        self.assertEqual(1, len(checks))

    def test_deprecated_size_limit_is_accepted_and_ignored(self):
        """
        The old formula cap refused to answer above a size. It is now a no-op:
        callers passing it still get a result rather than MergeTooLargeError.
        """
        merged = merge_solutions([self.repair_a, self.repair_b],
                                 max_formulas_for_trivial_fallback=1)
        self.assertGreaterEqual(len(merged), 1)


class TestMergeUndoingTheWeakening(BaseTestCase):
    """
    Merging conjoins, and the repair search routinely produces several
    weakenings of one formula by adding alternative disjuncts. When two such
    disjuncts cannot both hold, conjoining them cancels the addition and
    restores the formula that was weakened - so the merge of a set of genuine
    repairs can be semantically equivalent to the thing they repaired.

    Nothing else catches it: the merged spec stays realisable, and the ASP
    violation check still reports the trace as admitted, because on a finite
    prefix each disjunct is individually satisfiable. See
    docs/session-notes/2026-07-31-merge-collapse-investigation.md.
    """

    ORIGINAL = "G(!highwater|!methane);"

    def _weakened_with(self, disjunct: str) -> SpectraSpecification:
        """spec_strong with `assumption2_1` weakened by an extra disjunct."""
        text = spec_strong.replace(self.ORIGINAL, f"G(!highwater|!methane|{disjunct});")
        assert text != spec_strong, "fixture no longer contains the expected formula"
        return SpectraSpecification.from_str(text)

    def test_complementary_weakenings_are_detected(self):
        """`p | X(q)` and `p | X(!q)` conjoin back to `p`, undoing both repairs."""
        og = SpectraSpecification.from_str(spec_strong)
        a, b = self._weakened_with("next(pump)"), self._weakened_with("next(!pump)")
        # Each is genuinely a strict weakening on its own - that is the point.
        for one in (a, b):
            self.assertTrue(og.implies(one, GR1FormulaType.ASM))
            self.assertFalse(one.implies(og, GR1FormulaType.ASM))

        merged = a.merge(b)
        self.assertTrue(merged.implies(og, GR1FormulaType.ASM),
                        "conjoining complementary disjuncts should restore the original")
        self.assertFalse(
            warn_if_merge_undid_the_weakening(merged, og),
            "a merge equivalent to the original on assumptions must be reported")

    def test_a_genuine_weakening_is_not_flagged(self):
        """The guard must stay silent when the merge really is weaker."""
        og = SpectraSpecification.from_str(spec_strong)
        merged = self._weakened_with("next(pump)")
        self.assertTrue(warn_if_merge_undid_the_weakening(merged, og))

    def test_guard_is_silent_without_an_original_to_compare_against(self):
        """No og_spec means no claim about weakening, so nothing to check."""
        merged = merge_solutions(
            [SpectraSpecification.from_str(spec_fixed_perf),
             SpectraSpecification.from_str(spec_fixed_imperf)], og_spec=None)
        self.assertGreaterEqual(len(merged), 1)
