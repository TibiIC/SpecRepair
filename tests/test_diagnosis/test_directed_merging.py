"""
Core-directed merging, driven by hand-written oracles rather than Spectra.

The minepump shape is the one that matters and is reproduced here in miniature:
two original guarantees that cannot hold together once the assumption is
weakened, so the single core is both of them, its two minimal hitting sets give
two branches, and each branch weakens exactly one of the pair.
"""
import unittest
from unittest import TestCase

from spec_repair.diagnosis.directed_merging import (
    build_pool,
    directed_merges,
)
from spec_repair.ltl_types import GR1FormulaType
from spec_repair.model.spectra_specification import SpectraSpecification

HEADER = """module Minepump

env boolean highwater;
env boolean methane;
sys boolean pump;
"""

ASM_ORIG = """
assumption -- assumption2_1
\tG((highwater=false|methane=false));
"""
ASM_WEAK = """
assumption -- assumption2_1
\tG((pump=true->(highwater=false|methane=false)));
"""
G1 = """
guarantee -- guarantee1_1
\tG((highwater=true->next(pump=true)));
"""
G2 = """
guarantee -- guarantee2_1
\tG((methane=true->next(pump=false)));
"""
G1_WEAK = """
guarantee -- guarantee1_1
\tG((highwater=true->(next(pump=true)|next(highwater=true))));
"""
G2_WEAK = """
guarantee -- guarantee2_1
\tG((methane=true->(next(pump=false)|next(methane=true))));
"""


def spec(*parts):
    return SpectraSpecification.from_str(HEADER + "".join(parts))


def gars(s):
    rows = s._formulas_df
    return sorted(str(r["formula"])
                  for _, r in rows[rows["type"] == GR1FormulaType.GAR].iterrows())


ORIGINAL = spec(ASM_ORIG, G1, G2)
STRONG_G1 = gars(spec(ASM_ORIG, G1))[0]
STRONG_G2 = gars(spec(ASM_ORIG, G2))[0]


def conflict_oracle(s):
    """
    The minepump conflict: the two untouched guarantees cannot hold together.

    Anything else is realisable, so weakening either one is enough.
    """
    got = gars(s)
    return not (STRONG_G1 in got and STRONG_G2 in got)


class TestBuildPool(TestCase):
    def test_variants_group_by_root_name(self):
        names = {"guarantee1_1", "guarantee2_1"}
        pool = build_pool([spec(ASM_WEAK, G1, G2), spec(ASM_WEAK, G1_WEAK, G2_WEAK)],
                          original_names=names)
        self.assertEqual({"guarantee1_1", "guarantee2_1"}, set(pool.variants))
        self.assertEqual(2, len(pool.variants["guarantee1_1"]))
        self.assertEqual(4, pool.variant_count())

    def test_identical_variants_pool_once(self):
        pool = build_pool([spec(ASM_WEAK, G1), spec(ASM_WEAK, G1)],
                          original_names={"guarantee1_1"})
        self.assertEqual(1, pool.variant_count())

    def test_a_suffixed_variant_maps_back_to_its_original(self):
        from spec_repair.diagnosis.directed_merging import _root_name
        names = {"guarantee1_1", "guarantee2_1"}
        self.assertEqual("guarantee1_1", _root_name("guarantee1_1", names))
        self.assertEqual("guarantee1_1", _root_name("guarantee1_1_0", names))
        self.assertEqual("guarantee1_1", _root_name("guarantee1_1_12", names))
        self.assertEqual("unknown", _root_name("unknown", names))

    def test_assumption_sample_limits_only_assumptions(self):
        pool = build_pool([spec(ASM_WEAK, G1), spec(ASM_ORIG, G2)], sample=1)
        self.assertEqual(1, len(pool.assumptions))     # only the first spec read
        self.assertEqual(2, pool.variant_count())      # but both guarantees kept


class TestDirectedMerges(TestCase):
    def test_realisable_base_is_the_unique_maximum_in_one_call(self):
        calls = []

        def oracle(s):
            calls.append(s)
            return True

        out = directed_merges([spec(ASM_WEAK, G1_WEAK)], ORIGINAL,
                              oracle=oracle, progress_every=0)
        self.assertEqual(1, len(out))
        self.assertEqual(1, len(calls), "a realisable base should cost one check")
        self.assertEqual(sorted([STRONG_G1, STRONG_G2]), gars(out[0]))

    def test_one_core_gives_two_branches_each_weakening_one_guarantee(self):
        pool = [spec(ASM_WEAK, G1_WEAK, G2), spec(ASM_WEAK, G1, G2_WEAK)]
        out = directed_merges(pool, ORIGINAL, oracle=conflict_oracle,
                              progress_every=0)
        self.assertEqual(2, len(out))
        kept_strong = sorted(
            (STRONG_G1 in gars(s), STRONG_G2 in gars(s)) for s in out)
        # exactly one branch keeps each of the two untouched guarantees
        self.assertEqual([(False, True), (True, False)], kept_strong)

    def test_each_branch_keeps_the_guarantee_no_core_implicated(self):
        pool = [spec(ASM_WEAK, G1_WEAK, G2_WEAK)]
        out = directed_merges(pool, ORIGINAL, oracle=conflict_oracle,
                              progress_every=0)
        for s in out:
            self.assertTrue(STRONG_G1 in gars(s) or STRONG_G2 in gars(s),
                            "a branch weakened a guarantee no core implicated")

    def test_branch_with_no_usable_variant_degenerates_to_deletion(self):
        """Deletion is weakening's limiting case - the trivial solution."""
        pool = [spec(ASM_WEAK, G1), spec(ASM_WEAK, G2)]

        def oracle(s):
            got = gars(s)
            if STRONG_G1 in got and STRONG_G2 in got:
                return False
            return True

        out = directed_merges(pool, ORIGINAL, oracle=oracle, progress_every=0)
        self.assertEqual(2, len(out))
        for s in out:
            self.assertEqual(1, len(gars(s)))

    def test_result_is_independent_of_pool_order(self):
        pool = [spec(ASM_WEAK, G1_WEAK, G2), spec(ASM_WEAK, G1, G2_WEAK)]
        forwards = directed_merges(pool, ORIGINAL, oracle=conflict_oracle,
                                   progress_every=0)
        backwards = directed_merges(list(reversed(pool)), ORIGINAL,
                                    oracle=conflict_oracle, progress_every=0)
        self.assertEqual(sorted(gars(s) for s in forwards),
                         sorted(gars(s) for s in backwards))

    def test_empty_pool(self):
        self.assertEqual([], directed_merges([], ORIGINAL, oracle=lambda s: True,
                                             progress_every=0))

    def test_nothing_realisable_at_all_falls_back_to_the_assumptions(self):
        """
        Every branch runs out of usable variants, so each degenerates to the
        guarantees no core implicated - here, none of them.
        """
        out = directed_merges([spec(ASM_WEAK, G1)], ORIGINAL,
                              oracle=lambda s: not gars(s), progress_every=0)
        self.assertTrue(out)
        for s in out:
            self.assertEqual([], gars(s))


if __name__ == "__main__":
    unittest.main()
