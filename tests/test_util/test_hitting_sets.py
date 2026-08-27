"""
Minimal hitting sets by clingo, checked against the brute-force implementation.

The brute force in `set_util` is correct and unusably slow past a few dozen
elements; these pin the clingo version to it on families small enough for both.
"""
import unittest
from unittest import TestCase

from spec_repair.util.hitting_sets import minimal_hitting_sets
from spec_repair.util.set_util import all_minimal_hitting_sets


def norm(hitting):
    return sorted(tuple(sorted(h)) for h in hitting)


class TestAgainstBruteForce(TestCase):
    def _both(self, sets):
        return norm(minimal_hitting_sets(sets)), norm(all_minimal_hitting_sets(sets))

    def test_single_set(self):
        fast, slow = self._both([{"a", "b"}])
        self.assertEqual(slow, fast)

    def test_disjoint_sets_need_one_from_each(self):
        fast, slow = self._both([{"a", "b"}, {"c", "d"}])
        self.assertEqual(slow, fast)
        self.assertTrue(all(len(h) == 2 for h in fast))

    def test_overlapping_sets_share_a_hitter(self):
        fast, slow = self._both([{"a", "b"}, {"b", "c"}, {"c", "d"}])
        self.assertEqual(slow, fast)

    def test_a_singleton_forces_its_element(self):
        fast, slow = self._both([{"a"}, {"a", "b"}, {"b", "c"}])
        self.assertEqual(slow, fast)

    def test_nested_sets(self):
        fast, slow = self._both([{"a", "b", "c"}, {"a", "b"}, {"a"}])
        self.assertEqual(slow, fast)

    def test_several_incomparable_solutions(self):
        fast, slow = self._both([{"a", "b"}, {"a", "c"}, {"b", "c"}])
        self.assertEqual(slow, fast)


class TestEdges(TestCase):
    def test_no_sets_are_hit_by_nothing(self):
        self.assertEqual([set()], minimal_hitting_sets([]))

    def test_an_empty_set_cannot_be_hit(self):
        self.assertEqual([], minimal_hitting_sets([{"a"}, set()]))

    def test_elements_need_not_be_valid_asp_constants(self):
        sets = [{"G((a -> X(b)))", "guarantee1_1"}, {"guarantee1_1"}]
        got = minimal_hitting_sets(sets)
        self.assertEqual([{"guarantee1_1"}], got)


class TestScale(TestCase):
    def test_many_sets_over_a_small_universe(self):
        """The shape that defeats the brute force: many sets, few elements."""
        universe = [f"g{i}" for i in range(40)]
        sets = [{universe[i], universe[(i + 1) % 40]} for i in range(40)]
        got = minimal_hitting_sets(sets)
        self.assertTrue(got)
        for h in got:
            for s in sets:
                self.assertTrue(h & s, "not a hitting set")


if __name__ == "__main__":
    unittest.main()
