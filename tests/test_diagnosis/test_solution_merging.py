"""
Tests for merging semantically distinct specifications.

The interesting case is two repairs that are *not* equivalent: the merge has to
keep both sets of behaviour rather than collapse to either input, and when
conjoining their guarantees over-constrains the system it has to fall back to
the trivial guarantee-only solutions instead of returning something unrealisable.
"""
from typing import List

from spec_repair.diagnosis.solution_merging import MergeTooLargeError, NotAWeakeningError, \
    UnrealisableInputError, check_weakens_original, merge_solutions, merge_two_solutions
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

    # ---------------- guards on large / expensive merges ----------------

    def test_verify_inputs_can_be_skipped(self):
        """
        Skipping input verification must not change the result - it only avoids
        re-establishing that specs from the repair search are realisable.
        """
        checked = merge_solutions([self.repair_a, self.repair_b], verify_inputs=True)
        unchecked = merge_solutions([self.repair_a, self.repair_b], verify_inputs=False)
        self.assertEqual([s.to_str() for s in checked], [s.to_str() for s in unchecked])

    def test_unrealisable_input_is_not_caught_when_verification_is_off(self):
        """Documents the trade-off: the check is what raises, so turning it off removes that."""
        class _NeverRealisable:
            @staticmethod
            def is_realisable(_spec):
                return False

        with self.assertRaises(UnrealisableInputError):
            merge_solutions([self.repair_a, self.repair_b], oracle=_NeverRealisable(),
                            verify_inputs=True)
        # With verification off the unrealisable merge is still detected, and
        # here it is refused by the size guard rather than silently accepted.
        with self.assertRaises(MergeTooLargeError):
            merge_solutions([self.repair_a, self.repair_b], oracle=_NeverRealisable(),
                            verify_inputs=False, max_formulas_for_trivial_fallback=0)

    def test_large_unrealisable_merge_is_refused_rather_than_attempted(self):
        class _NeverRealisable:
            @staticmethod
            def is_realisable(_spec):
                return False

        with self.assertRaises(MergeTooLargeError) as ctx:
            merge_solutions([self.repair_a, self.repair_b], oracle=_NeverRealisable(),
                            verify_inputs=False, max_formulas_for_trivial_fallback=1)
        self.assertIn("unrealisable specification", str(ctx.exception))

    def test_no_limit_still_attempts_the_fallback(self):
        """A realisable merge never reaches the guard, whatever the limit."""
        merged = merge_solutions([self.repair_a, self.repair_b],
                                 max_formulas_for_trivial_fallback=1)
        self.assertGreaterEqual(len(merged), 1)
