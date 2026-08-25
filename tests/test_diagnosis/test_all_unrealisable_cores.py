"""
MARCO core enumeration, tested against oracles rather than against Spectra.

The component takes its realisability oracle as a parameter, so these run
without the JVM, without clingo doing any real work on a specification, and in
well under a second - which is the point of keeping it independent of Spectra.
"""
import unittest
from unittest import TestCase

from spec_repair.diagnosis.all_unrealisable_cores import AllUnrealisableCores


def oracle_from_cores(cores):
    """
    A monotone oracle whose minimal unrealisable cores are exactly `cores`.

    A subset is unrealisable exactly when it contains one of them, which is the
    monotonicity the enumeration relies on.
    """
    cores = [set(c) for c in cores]

    def check(subset):
        return not any(core <= set(subset) for core in cores)

    return check


def as_sorted(cores):
    return sorted(tuple(sorted(c)) for c in cores)


class TestAllUnrealisableCores(TestCase):
    def test_no_cores_when_everything_is_realisable(self):
        finder = AllUnrealisableCores(["g1", "g2", "g3"], lambda s: True)
        self.assertEqual([], finder.enumerate())

    def test_single_core(self):
        finder = AllUnrealisableCores(["g1", "g2", "g3"],
                                      oracle_from_cores([{"g1", "g2"}]))
        self.assertEqual([("g1", "g2")], as_sorted(finder.enumerate()))

    def test_two_disjoint_cores(self):
        """The shape of the specification Spectra itself returns two cores for."""
        finder = AllUnrealisableCores(["g1", "g2", "g3", "g4"],
                                      oracle_from_cores([{"g1", "g2"}, {"g3", "g4"}]))
        self.assertEqual([("g1", "g2"), ("g3", "g4")], as_sorted(finder.enumerate()))

    def test_overlapping_cores(self):
        finder = AllUnrealisableCores(["a", "b", "c"],
                                      oracle_from_cores([{"a", "b"}, {"b", "c"}]))
        self.assertEqual([("a", "b"), ("b", "c")], as_sorted(finder.enumerate()))

    def test_nested_candidates_return_only_the_minimal_one(self):
        """{a} unrealisable makes {a,b} unrealisable too - only {a} is a core."""
        finder = AllUnrealisableCores(["a", "b"], oracle_from_cores([{"a"}]))
        self.assertEqual([("a",)], as_sorted(finder.enumerate()))

    def test_every_singleton_can_be_a_core(self):
        finder = AllUnrealisableCores(["a", "b", "c"],
                                      oracle_from_cores([{"a"}, {"b"}, {"c"}]))
        self.assertEqual([("a",), ("b",), ("c",)], as_sorted(finder.enumerate()))

    def test_cores_are_unique(self):
        finder = AllUnrealisableCores(["a", "b", "c", "d"],
                                      oracle_from_cores([{"a", "b"}, {"c", "d"}]))
        cores = finder.enumerate()
        self.assertEqual(len(cores), len({tuple(sorted(c)) for c in cores}))

    def test_empty_specification_has_no_cores(self):
        self.assertEqual([], AllUnrealisableCores([], lambda s: True).enumerate())

    def test_result_is_deterministic(self):
        """Same input, same cores in the same order - no seeds, no randomness."""
        cores = [{"g1", "g2"}, {"g3", "g4"}, {"g2", "g4"}]
        first = AllUnrealisableCores(["g1", "g2", "g3", "g4"],
                                     oracle_from_cores(cores)).enumerate()
        second = AllUnrealisableCores(["g1", "g2", "g3", "g4"],
                                      oracle_from_cores(cores)).enumerate()
        self.assertEqual(first, second)

    def test_stats_are_reported(self):
        finder = AllUnrealisableCores(["a", "b", "c"],
                                      oracle_from_cores([{"a", "b"}]))
        finder.enumerate()
        self.assertEqual(1, finder.stats.cores)
        self.assertGreater(finder.stats.oracle_calls, 0)
        self.assertIn("core(s)", str(finder.stats))

    def test_names_with_awkward_characters(self):
        """Real guarantee names are not ASP constants - they are quoted."""
        names = ["unnamed_guarantee_1", "if_we_pause_this_means_no_motors_move",
                 "botMot_mutual_exclusion_1"]
        finder = AllUnrealisableCores(names, oracle_from_cores([{names[0], names[2]}]))
        self.assertEqual([tuple(sorted([names[0], names[2]]))],
                         as_sorted(finder.enumerate()))


if __name__ == "__main__":
    unittest.main()


class TestShrinkIsCheaperButEqual(TestCase):
    """
    Block deletion must find the same minimal cores as the old linear scan,
    for many fewer questions - that saving is the whole reason it exists.
    """

    def _run(self, names, cores):
        calls = []
        base = oracle_from_cores(cores)

        def counting(subset):
            calls.append(len(subset))
            return base(subset)

        finder = AllUnrealisableCores(names, counting)
        return as_sorted(finder.enumerate()), len(calls)

    def test_small_core_in_a_large_set_costs_far_less_than_one_call_each(self):
        names = [f"g{i}" for i in range(200)]
        got, calls = self._run(names, [{"g7", "g150"}])
        self.assertEqual([("g150", "g7")], got)
        self.assertLess(calls, 60,
                        f"block deletion should beat a 200-call linear scan, took {calls}")

    def test_several_cores_are_all_found(self):
        names = [f"g{i}" for i in range(60)]
        cores = [{"g1", "g2"}, {"g5"}, {"g10", "g11", "g12"}]
        got, _ = self._run(names, cores)
        self.assertEqual(as_sorted(cores), got)

    def test_single_element_core(self):
        got, _ = self._run([f"g{i}" for i in range(40)], [{"g13"}])
        self.assertEqual([("g13",)], got)

    def test_core_spanning_the_whole_set_is_still_minimal(self):
        names = ["g0", "g1", "g2"]
        got, _ = self._run(names, [set(names)])
        self.assertEqual([("g0", "g1", "g2")], got)
