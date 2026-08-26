"""
The properties a merge output must have, and what their failures look like.

Driven by real specification objects but a stubbed realisability oracle, so
these run without the JVM.
"""
import unittest
from unittest import TestCase

from spec_repair.diagnosis.merge_invariants import (
    MergeInvariantViolated,
    check_merge_output,
    find_equivalent_pairs,
    response_shaped_guarantees,
)
from spec_repair.ltl_types import GR1FormulaType
from spec_repair.model.spectra_specification import SpectraSpecification

HEADER = """module Minepump

env boolean highwater;
env boolean methane;
sys boolean pump;

assumption -- assumption2_1
\tG((pump=true->(highwater=false|methane=false)));
"""
G1 = "\nguarantee -- guarantee1_1\n\tG((highwater=true->next(pump=true)));\n"
G2 = "\nguarantee -- guarantee2_1\n\tG((methane=true->next(pump=false)));\n"
# Same meaning as G1, written the other way round: a merge that emitted both
# would be emitting one specification twice.
G1_REPHRASED = ("\nguarantee -- guarantee1_1\n"
                "\tG((highwater=false|next(pump=true)));\n")
G_RESPONSE = "\nguarantee -- guarantee2_1\n\tG((methane=true->F(next(pump=false))));\n"


def spec(*parts):
    return SpectraSpecification.from_str(HEADER + "".join(parts))


class TestFindEquivalentPairs(TestCase):
    def test_distinct_specifications_have_no_equivalent_pair(self):
        self.assertEqual([], find_equivalent_pairs([spec(G1), spec(G2)]))

    def test_the_same_property_written_two_ways_is_caught(self):
        pairs = find_equivalent_pairs([spec(G1), spec(G1_REPHRASED)])
        self.assertEqual([(0, 1)], pairs)

    def test_comparison_can_be_restricted_to_guarantees(self):
        pairs = find_equivalent_pairs([spec(G1), spec(G1_REPHRASED)],
                                      GR1FormulaType.GAR)
        self.assertEqual([(0, 1)], pairs)

    def test_empty_and_single_outputs_are_trivially_fine(self):
        self.assertEqual([], find_equivalent_pairs([]))
        self.assertEqual([], find_equivalent_pairs([spec(G1)]))


class TestCheckMergeOutput(TestCase):
    def test_a_sound_output_reports_nothing(self):
        self.assertEqual([], check_merge_output([spec(G1), spec(G2)],
                                                oracle=lambda s: True))

    def test_an_unrealisable_output_is_reported(self):
        problems = check_merge_output([spec(G1)], oracle=lambda s: False)
        self.assertEqual(1, len(problems))
        self.assertIn("not realisable", problems[0])

    def test_a_duplicate_is_reported_with_what_it_implicates(self):
        problems = check_merge_output([spec(G1), spec(G1_REPHRASED)])
        self.assertEqual(1, len(problems))
        self.assertIn("semantically equivalent", problems[0])
        self.assertIn("incomplete core enumeration", problems[0])

    def test_strict_raises_instead_of_returning(self):
        with self.assertRaises(MergeInvariantViolated):
            check_merge_output([spec(G1), spec(G1_REPHRASED)], strict=True)

    def test_the_oracle_is_optional(self):
        self.assertEqual([], check_merge_output([spec(G1), spec(G2)]))

    def test_both_kinds_of_problem_are_reported_together(self):
        problems = check_merge_output([spec(G1), spec(G1_REPHRASED)],
                                      oracle=lambda s: False)
        self.assertEqual(3, len(problems))     # two unrealisable, one duplicate


class TestResponseShaped(TestCase):
    def test_a_response_guarantee_is_named(self):
        self.assertEqual(["guarantee2_1"], response_shaped_guarantees(spec(G_RESPONSE)))

    def test_plain_invariants_are_not(self):
        self.assertEqual([], response_shaped_guarantees(spec(G1, G2)))


if __name__ == "__main__":
    unittest.main()
