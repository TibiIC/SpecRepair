"""
The unrealisable-core cache.

The search it avoids is the most expensive call in the system - exponential in
the number of expressions, and measured on genbuf at over thirteen hours without
returning - so what matters is that a repeat costs nothing, that it cannot serve
a wrong answer, and that a caller can reset or disable it.

The component knows nothing about Spectra or the JVM: `compute` is passed in, so
these tests need neither.
"""
import unittest
from unittest import TestCase

from spec_repair.components.unrealisable_core_cache import UnrealisableCoreCache


class Counter:
    """A stand-in for the core search, counting how often it actually ran."""

    def __init__(self, result):
        self.result = result
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return [set(core) for core in self.result]


class TestUnrealisableCoreCache(TestCase):
    def setUp(self):
        self.cache = UnrealisableCoreCache()

    def test_second_lookup_does_not_recompute(self):
        search = Counter([{"g1", "g2"}])
        first = self.cache.lookup_or_compute("module A\n", "cudd", search)
        second = self.cache.lookup_or_compute("module A\n", "cudd", search)

        self.assertEqual([{"g1", "g2"}], first)
        self.assertEqual(first, second)
        self.assertEqual(1, search.calls)
        self.assertEqual(1, self.cache.stats.hits)
        self.assertEqual(1, self.cache.stats.misses)
        self.assertEqual(0.5, self.cache.stats.hit_rate)

    def test_different_text_is_a_different_entry(self):
        search = Counter([{"g1"}])
        self.cache.lookup_or_compute("module A\n", "cudd", search)
        self.cache.lookup_or_compute("module B\n", "cudd", search)

        self.assertEqual(2, search.calls)
        self.assertEqual(0, self.cache.stats.hits)
        self.assertEqual(2, len(self.cache))

    def test_bdd_package_is_part_of_the_key(self):
        """CUDD and JTLV can report different cores, so one must not answer for the other."""
        search = Counter([{"g1"}])
        self.cache.lookup_or_compute("module A\n", "cudd", search)
        self.cache.lookup_or_compute("module A\n", "jtlv", search)

        self.assertEqual(2, search.calls)
        self.assertEqual(0, self.cache.stats.hits)

    def test_a_caller_mutating_the_result_cannot_poison_the_entry(self):
        search = Counter([{"g1"}])
        first = self.cache.lookup_or_compute("module A\n", "cudd", search)
        first[0].add("not_really_a_core")
        second = self.cache.lookup_or_compute("module A\n", "cudd", search)

        self.assertEqual([{"g1"}], second)

    def test_empty_cores_are_cached_too(self):
        """A realizable specification has no cores, and that answer is worth keeping."""
        search = Counter([])
        self.cache.lookup_or_compute("module Realizable\n", "cudd", search)
        self.assertEqual([], self.cache.lookup_or_compute("module Realizable\n", "cudd", search))
        self.assertEqual(1, search.calls)

    def test_reset_forgets_entries_and_statistics(self):
        search = Counter([{"g1"}])
        self.cache.lookup_or_compute("module A\n", "cudd", search)
        self.cache.lookup_or_compute("module A\n", "cudd", search)

        self.cache.reset()

        self.assertEqual(0, len(self.cache))
        self.assertEqual(0, self.cache.stats.calls)
        self.assertEqual(0, self.cache.stats.hits)
        self.cache.lookup_or_compute("module A\n", "cudd", search)
        self.assertEqual(2, search.calls, "after a reset the search runs again")

    def test_disabled_cache_always_computes(self):
        cache = UnrealisableCoreCache(enabled=False)
        search = Counter([{"g1"}])
        cache.lookup_or_compute("module A\n", "cudd", search)
        cache.lookup_or_compute("module A\n", "cudd", search)

        self.assertEqual(2, search.calls)
        self.assertEqual(0, len(cache))

    def test_stats_render_readably(self):
        search = Counter([{"g1"}])
        self.cache.lookup_or_compute("module A\n", "cudd", search)
        self.cache.lookup_or_compute("module A\n", "cudd", search)
        self.assertEqual("2 call(s), 1 hit(s), 1 miss(es), 50% hit rate",
                         str(self.cache.stats))


if __name__ == "__main__":
    unittest.main()
