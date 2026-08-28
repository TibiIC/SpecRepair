"""
The five-step pipeline, step by step, against stubbed realisability.

Each test names the step it pins down, because the counts these steps report are
what the methodology is described by - if one of them shifts, the paper's
numbers shift with it.
"""
import unittest
from unittest import TestCase

from spec_repair.diagnosis.five_step import (
    merge_assumptions,
    merge_losslessly,
    rebase,
    run_five_step,
    soft_semantically_unique,
    strongest_by_guarantees,
)
from spec_repair.ltl_types import GR1FormulaType
from spec_repair.model.spectra_specification import SpectraSpecification

HEADER = """module Minepump

env boolean highwater;
env boolean methane;
sys boolean pump;
"""
A_STRONG = "\nassumption -- assumption2_1\n\tG((highwater=false|methane=false));\n"
A_WEAK = "\nassumption -- assumption2_1\n\tG((pump=true->(highwater=false|methane=false)));\n"
G1 = "\nguarantee -- guarantee1_1\n\tG((highwater=true->next(pump=true)));\n"
G1_AGAIN = "\nguarantee -- guarantee1_1_b\n\tG((highwater=false|next(pump=true)));\n"
G2 = "\nguarantee -- guarantee2_1\n\tG((methane=true->next(pump=false)));\n"
G1_WEAK = ("\nguarantee -- guarantee1_1\n"
           "\tG((highwater=true->(next(pump=true)|next(highwater=true))));\n")


def spec(*parts):
    return SpectraSpecification.from_str(HEADER + "".join(parts))


def gars(s):
    rows = s._formulas_df
    return sorted(str(r["formula"])
                  for _, r in rows[rows["type"] == GR1FormulaType.GAR].iterrows())


def asms(s):
    rows = s._formulas_df
    return sorted(str(r["formula"])
                  for _, r in rows[rows["type"] == GR1FormulaType.ASM].iterrows())


class TestStep1MergeAssumptions(TestCase):
    def test_distinct_assumptions_are_all_kept(self):
        frame, n = merge_assumptions([spec(A_STRONG, G1), spec(A_WEAK, G1)])
        self.assertEqual(2, n)

    def test_identical_assumptions_pool_once(self):
        frame, n = merge_assumptions([spec(A_WEAK, G1), spec(A_WEAK, G2)])
        self.assertEqual(1, n)

    def test_names_are_disambiguated_so_spectra_will_take_it(self):
        frame, _ = merge_assumptions([spec(A_STRONG, G1), spec(A_WEAK, G1)])
        self.assertEqual(len(set(frame["name"])), len(frame))


class TestStep2SoftSemanticUniqueness(TestCase):
    def test_the_same_guarantee_written_twice_ways_collapses(self):
        """One spec says it once, the other says it twice - keep the smaller."""
        small, large = spec(A_WEAK, G1), spec(A_WEAK, G1, G1_AGAIN)
        kept = soft_semantically_unique([large, small])
        self.assertEqual(1, len(kept))
        self.assertEqual(1, len(gars(kept[0])), "kept the one with more formulas")

    def test_genuinely_different_guarantees_are_both_kept(self):
        kept = soft_semantically_unique([spec(A_WEAK, G1), spec(A_WEAK, G2)])
        self.assertEqual(2, len(kept))

    def test_only_guarantees_are_compared(self):
        """Assumptions are settled by step 1, so they must not split a class."""
        kept = soft_semantically_unique([spec(A_STRONG, G1), spec(A_WEAK, G1)])
        self.assertEqual(1, len(kept))


class TestStep3Rebase(TestCase):
    def test_every_spec_gets_the_pooled_assumptions_and_keeps_its_guarantees(self):
        pool = [spec(A_STRONG, G1), spec(A_WEAK, G2)]
        frame, _ = merge_assumptions(pool)
        out = rebase(pool, frame)
        self.assertEqual(2, len(out))
        self.assertEqual(asms(out[0]), asms(out[1]), "assumptions must be identical")
        self.assertNotEqual(gars(out[0]), gars(out[1]), "guarantees must be untouched")

    def test_the_count_is_unchanged(self):
        pool = [spec(A_WEAK, G1), spec(A_WEAK, G2), spec(A_WEAK, G1_WEAK)]
        frame, _ = merge_assumptions(pool)
        self.assertEqual(len(pool), len(rebase(pool, frame)))


class TestStep4Strongest(TestCase):
    def test_a_strictly_weaker_specification_is_dropped(self):
        kept = strongest_by_guarantees([spec(A_WEAK, G1), spec(A_WEAK, G1_WEAK)])
        self.assertEqual(1, len(kept))
        self.assertEqual(gars(spec(A_WEAK, G1)), gars(kept[0]))

    def test_incomparable_specifications_both_survive(self):
        kept = strongest_by_guarantees([spec(A_WEAK, G1), spec(A_WEAK, G2)])
        self.assertEqual(2, len(kept))


class TestStep5Merge(TestCase):
    def test_a_jointly_realisable_pool_gives_one_merge(self):
        pool = [spec(A_WEAK, G1), spec(A_WEAK, G2)]
        frame, _ = merge_assumptions(pool)
        out, size, cores = merge_losslessly(pool, frame, lambda s: True,
                                            progress_every=0)
        self.assertEqual(1, len(out))
        self.assertEqual(2, size)
        self.assertEqual(0, cores)
        self.assertEqual(2, len(gars(out[0])))

    def test_a_conflict_splits_into_maximal_subsets(self):
        pool = [spec(A_WEAK, G1), spec(A_WEAK, G2)]
        frame, _ = merge_assumptions(pool)
        out, _, cores = merge_losslessly(pool, frame,
                                         lambda s: len(gars(s)) < 2,
                                         progress_every=0)
        self.assertEqual(2, len(out))
        self.assertEqual(1, cores)
        self.assertEqual([1, 1], sorted(len(gars(s)) for s in out))

    def test_a_weaker_formula_is_not_discarded_for_being_weaker(self):
        """
        The whole point of the lossless merge: `G1_WEAK` is implied by `G1`, and
        must still be available when `G1` cannot be used.
        """
        pool = [spec(A_WEAK, G1), spec(A_WEAK, G1_WEAK), spec(A_WEAK, G2)]
        frame, _ = merge_assumptions(pool)
        strong = gars(spec(A_WEAK, G1))[0]

        def oracle(s):                      # G1 and G2 cannot hold together
            got = gars(s)
            return not (strong in got and gars(spec(A_WEAK, G2))[0] in got)

        out, _, _ = merge_losslessly(pool, frame, oracle, progress_every=0)
        weak = gars(spec(A_WEAK, G1_WEAK))[0]
        self.assertTrue(any(weak in gars(s) and strong not in gars(s) for s in out),
                        "the weaker formula was dropped and its combination lost")


class TestEndToEnd(TestCase):
    def test_counts_are_reported_for_every_step(self):
        pool = [spec(A_STRONG, G1), spec(A_WEAK, G1, G1_AGAIN), spec(A_WEAK, G2)]
        r = run_five_step(pool, oracle=lambda s: True, progress_every=0)
        self.assertEqual(3, r.inputs)
        self.assertEqual(2, r.pooled_assumptions)
        self.assertEqual(r.soft_unique, r.rebased, "step 3 must not change the count")
        self.assertGreaterEqual(r.soft_unique, r.strongest)
        self.assertEqual(len(r.specs), r.merged)

    def test_every_output_carries_the_pooled_assumptions(self):
        pool = [spec(A_STRONG, G1), spec(A_WEAK, G2)]
        r = run_five_step(pool, oracle=lambda s: True, progress_every=0)
        for s in r.specs:
            self.assertEqual(2, len(asms(s)))

    def test_empty_input(self):
        r = run_five_step([], oracle=lambda s: True, progress_every=0)
        self.assertEqual(0, r.inputs)
        self.assertEqual([], r.specs)


class TestContainmentPreFilter(TestCase):
    """
    Step 4's cheap pass: a specification whose guarantees are a proper subset of
    another's is dominated, and set comparison establishes that without an
    oracle call.
    """

    def test_a_proper_subset_is_dropped(self):
        from spec_repair.diagnosis.five_step import _drop_contained
        small, large = spec(A_WEAK, G1), spec(A_WEAK, G1, G2)
        kept = _drop_contained([small, large])
        self.assertEqual(1, len(kept))
        self.assertEqual(2, len(gars(kept[0])))

    def test_incomparable_sets_are_both_kept(self):
        from spec_repair.diagnosis.five_step import _drop_contained
        self.assertEqual(2, len(_drop_contained([spec(A_WEAK, G1), spec(A_WEAK, G2)])))

    def test_equal_sets_are_both_kept_for_the_semantic_pass(self):
        from spec_repair.diagnosis.five_step import _drop_contained
        self.assertEqual(2, len(_drop_contained([spec(A_WEAK, G1), spec(A_WEAK, G1)])))

    def test_it_never_removes_a_maximal_specification(self):
        from spec_repair.diagnosis.five_step import _drop_contained
        pool = [spec(A_WEAK, G1), spec(A_WEAK, G2), spec(A_WEAK, G1, G2)]
        kept = _drop_contained(pool)
        self.assertEqual(1, len(kept))
        self.assertEqual(2, len(gars(kept[0])))


class TestEveryStageIsKept(TestCase):
    """
    The report must carry each stage's specifications, not only the last.

    These take hours to produce on a large run. A pipeline that returns only its
    final answer makes any later question about the middle of it a full re-run,
    which is how minepump trace 3's step-4 output came to need regenerating.
    """

    def test_all_stages_are_populated(self):
        pool = [spec(A_STRONG, G1), spec(A_WEAK, G1, G1_AGAIN), spec(A_WEAK, G2)]
        r = run_five_step(pool, oracle=lambda s: True, progress_every=0)
        self.assertTrue(r.assumption_specs, "step 1 output missing")
        self.assertTrue(r.unique_specs, "step 2 output missing")
        self.assertTrue(r.strongest_specs, "step 4 output missing")
        self.assertTrue(r.specs, "step 5 output missing")

    def test_the_kept_lists_match_the_reported_counts(self):
        pool = [spec(A_STRONG, G1), spec(A_WEAK, G2), spec(A_WEAK, G1, G1_AGAIN)]
        r = run_five_step(pool, oracle=lambda s: True, progress_every=0)
        self.assertEqual(r.soft_unique, len(r.unique_specs))
        self.assertEqual(r.strongest, len(r.strongest_specs))
        self.assertEqual(r.merged, len(r.specs))

    def test_the_step_one_artefact_carries_the_merged_assumptions(self):
        pool = [spec(A_STRONG, G1), spec(A_WEAK, G2)]
        r = run_five_step(pool, oracle=lambda s: True, progress_every=0)
        self.assertEqual(r.pooled_assumptions, len(asms(r.assumption_specs[0])))


if __name__ == "__main__":
    unittest.main()
