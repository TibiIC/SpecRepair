"""
Merging by maximal-realisable-subset enumeration.

Like the core enumeration tests, these drive the component with a hand-written
realisability oracle rather than Spectra, so they run without the JVM and in
under a second. The one thing they cannot check that way is whether Spectra
agrees about any particular specification - that is what the case study runs are
for.
"""
import unittest
from unittest import TestCase

from spec_repair.diagnosis.maximal_merging import (
    group_by_assumptions,
    maximal_merges,
)
from spec_repair.ltl_types import GR1FormulaType
from spec_repair.model.spectra_specification import SpectraSpecification

HEADER = """module Minepump

env boolean highwater;
env boolean methane;
sys boolean pump;
"""

ASM_WEAK = """
assumption -- assumption2_1
\tG((pump=true->(highwater=false|methane=false)));
"""

ASM_OTHER = """
assumption -- assumption2_1
\tG((methane=false->(highwater=false|methane=false)));
"""

G1_INTACT = """
guarantee -- guarantee1_1
\tG((highwater=true->next(pump=true)));
"""

G1_WEAK = """
guarantee -- guarantee1_1
\tG((highwater=true->(next(pump=true)|next(highwater=true))));
"""

G2_A = """
guarantee -- guarantee2_1
\tG((methane=true->(next(pump=false)|next(methane=true))));
"""

G2_B = """
guarantee -- guarantee2_1
\tG((methane=true->(next(pump=false)|next(highwater=true))));
"""


def spec(*parts) -> SpectraSpecification:
    return SpectraSpecification.from_str(HEADER + "".join(parts))


def formulas_of(s, kind=GR1FormulaType.GAR):
    rows = s._formulas_df
    return sorted(str(r["formula"]) for _, r in rows[rows["type"] == kind].iterrows())


def names_of(s, kind=GR1FormulaType.GAR):
    rows = s._formulas_df
    return sorted(str(r["name"]) for _, r in rows[rows["type"] == kind].iterrows())


class TestGrouping(TestCase):
    def test_specs_sharing_assumptions_pool_their_guarantees(self):
        pool = [spec(ASM_WEAK, G1_INTACT), spec(ASM_WEAK, G2_A)]
        groups = group_by_assumptions(pool)
        self.assertEqual(1, len(groups))
        self.assertEqual(2, len(groups[0]))
        self.assertEqual(2, groups[0].source_count)

    def test_differing_assumptions_are_kept_apart(self):
        pool = [spec(ASM_WEAK, G1_INTACT), spec(ASM_OTHER, G2_A)]
        groups = group_by_assumptions(pool)
        self.assertEqual(2, len(groups))

    def test_identical_formulas_pool_once(self):
        pool = [spec(ASM_WEAK, G1_INTACT), spec(ASM_WEAK, G1_INTACT)]
        self.assertEqual(1, len(group_by_assumptions(pool)[0]))


class TestMaximalMerges(TestCase):
    def test_whole_pool_realisable_gives_one_merge(self):
        pool = [spec(ASM_WEAK, G1_INTACT), spec(ASM_WEAK, G2_A)]
        merged = maximal_merges(pool, oracle=lambda s: True, progress_every=0)
        self.assertEqual(1, len(merged))
        self.assertEqual(2, len(formulas_of(merged[0])))

    def test_the_pairing_a_greedy_merge_loses_is_recovered(self):
        """
        The minepump case, in miniature.

        `G2_A` only ever arrives alongside a weakened `guarantee1_1`, so a
        filter that drops dominated specifications drops the only carrier and
        the merge never sees it. Pooling formulas rather than specifications
        puts `G2_A` next to the intact guarantee it never shared a file with.
        """
        pool = [spec(ASM_WEAK, G1_INTACT, G2_B),   # intact, but not G2_A
                spec(ASM_WEAK, G1_WEAK, G2_A)]     # carries G2_A, dominated
        merged = maximal_merges(pool, oracle=lambda s: True, progress_every=0)
        self.assertEqual(1, len(merged))
        got = formulas_of(merged[0])
        self.assertEqual(4, len(got))
        # Compare against the model's own rendering rather than the source text.
        for wanted in (G1_INTACT, G2_A):
            self.assertIn(formulas_of(spec(ASM_WEAK, wanted))[0], got)

    def test_conflicting_guarantees_split_into_maximal_subsets(self):
        """Two guarantees that cannot hold together give two merges, not one."""
        pool = [spec(ASM_WEAK, G1_INTACT), spec(ASM_WEAK, G2_A)]

        def oracle(s):
            got = formulas_of(s)
            return not (len(got) > 1)

        merged = maximal_merges(pool, oracle=oracle, progress_every=0)
        self.assertEqual(2, len(merged))
        self.assertEqual([1, 1], sorted(len(formulas_of(m)) for m in merged))

    def test_group_policy_result_is_independent_of_input_order(self):
        parts = [spec(ASM_WEAK, G1_INTACT), spec(ASM_WEAK, G2_A), spec(ASM_WEAK, G2_B)]

        def oracle(s):
            got = formulas_of(s)
            g2s = [g for g in got if "methane=true->" in g]
            return len(g2s) < 2          # the two guarantee2_1 variants conflict

        forwards = maximal_merges(parts, oracle=oracle, progress_every=0,
                                  assumptions="group")
        backwards = maximal_merges(list(reversed(parts)), oracle=oracle,
                                   progress_every=0, assumptions="group")
        self.assertEqual(sorted(formulas_of(m) for m in forwards),
                         sorted(formulas_of(m) for m in backwards))

    def test_group_policy_keeps_each_assumption_set_apart(self):
        pool = [spec(ASM_WEAK, G1_INTACT), spec(ASM_OTHER, G2_A)]
        merged = maximal_merges(pool, oracle=lambda s: True, progress_every=0,
                                assumptions="group")
        self.assertEqual(2, len(merged))
        for m in merged:
            self.assertEqual(1, len(formulas_of(m, GR1FormulaType.ASM)))

    def test_conjoin_policy_pools_differing_assumptions(self):
        """
        The default. minepump trace 0 varies only in `assumption1_1`, so under
        the `group` policy every spec is its own group and nothing merges; the
        conjoined pool is what lets those repairs combine at all.
        """
        pool = [spec(ASM_WEAK, G1_INTACT), spec(ASM_OTHER, G2_A)]
        merged = maximal_merges(pool, oracle=lambda s: True, progress_every=0)
        self.assertEqual(1, len(merged))
        self.assertEqual(2, len(formulas_of(merged[0], GR1FormulaType.ASM)))
        self.assertEqual(2, len(formulas_of(merged[0], GR1FormulaType.GAR)))

    def test_conjoined_assumption_variants_get_distinct_names(self):
        pool = [spec(ASM_WEAK, G1_INTACT), spec(ASM_OTHER, G1_INTACT)]
        merged = maximal_merges(pool, oracle=lambda s: True, progress_every=0)
        self.assertEqual(["assumption2_1_0", "assumption2_1_1"],
                         names_of(merged[0], GR1FormulaType.ASM))

    def test_unknown_assumption_policy_is_rejected(self):
        with self.assertRaises(ValueError):
            maximal_merges([spec(ASM_WEAK, G1_INTACT)], oracle=lambda s: True,
                           progress_every=0, assumptions="whatever")

    def test_variants_of_one_formula_get_distinct_names(self):
        pool = [spec(ASM_WEAK, G2_A), spec(ASM_WEAK, G2_B)]
        merged = maximal_merges(pool, oracle=lambda s: True, progress_every=0)
        self.assertEqual(["guarantee2_1_0", "guarantee2_1_1"], names_of(merged[0]))

    def test_a_lone_variant_keeps_its_original_name(self):
        pool = [spec(ASM_WEAK, G1_INTACT), spec(ASM_WEAK, G2_A)]
        merged = maximal_merges(pool, oracle=lambda s: True, progress_every=0)
        self.assertEqual(["guarantee1_1", "guarantee2_1"], names_of(merged[0]))

    def test_empty_pool(self):
        self.assertEqual([], maximal_merges([], oracle=lambda s: True, progress_every=0))

    def test_nothing_realisable_gives_the_assumptions_alone(self):
        pool = [spec(ASM_WEAK, G1_INTACT)]
        merged = maximal_merges(pool, oracle=lambda s: not formulas_of(s),
                                progress_every=0)
        self.assertEqual(1, len(merged))
        self.assertEqual([], formulas_of(merged[0]))


if __name__ == "__main__":
    unittest.main()
