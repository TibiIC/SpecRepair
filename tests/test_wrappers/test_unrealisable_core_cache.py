"""
The unrealisable-core cache: same text in, same cores out, one search.

The search it avoids is the most expensive call in the system - exponential in
the number of expressions, and measured on genbuf at over thirteen hours without
returning - so what matters is that a repeat costs nothing and that it cannot
serve a wrong answer.
"""
import unittest
from unittest import TestCase, mock

from spec_repair.wrappers import spectra_toolbox


class TestUnrealisableCoreCache(TestCase):
    def setUp(self):
        spectra_toolbox._uc_cache.clear()
        for k in spectra_toolbox._uc_stats:
            spectra_toolbox._uc_stats[k] = 0

    def test_second_call_is_served_from_the_cache(self):
        spec = "module Test\nenv boolean a;\nsys boolean b;\n"
        with mock.patch.object(spectra_toolbox, "is_realizable", return_value=False), \
             mock.patch.object(spectra_toolbox, "run_all_unrealisable_cores_raw") as raw, \
             mock.patch.object(spectra_toolbox, "_extract_cores", return_value=[{4}]), \
             mock.patch.object(spectra_toolbox, "get_line_from_file",
                               return_value="guarantee -- g1"), \
             mock.patch.object(spectra_toolbox, "pRespondsToS_substitution"), \
             mock.patch.object(spectra_toolbox, "write_to_file"):
            first = spectra_toolbox.run_all_unrealisable_cores(spec)
            second = spectra_toolbox.run_all_unrealisable_cores(spec)

        self.assertEqual([{"g1"}], first)
        self.assertEqual(first, second)
        self.assertEqual(1, raw.call_count, "the search should run once, not twice")
        stats = spectra_toolbox.unrealisable_core_cache_stats()
        self.assertEqual(2, stats["calls"])
        self.assertEqual(1, stats["hits"])
        self.assertEqual(1, stats["searches"])

    def test_different_text_is_not_shared(self):
        with mock.patch.object(spectra_toolbox, "is_realizable", return_value=False), \
             mock.patch.object(spectra_toolbox, "run_all_unrealisable_cores_raw") as raw, \
             mock.patch.object(spectra_toolbox, "_extract_cores", return_value=[{4}]), \
             mock.patch.object(spectra_toolbox, "get_line_from_file",
                               return_value="guarantee -- g1"), \
             mock.patch.object(spectra_toolbox, "pRespondsToS_substitution"), \
             mock.patch.object(spectra_toolbox, "write_to_file"):
            spectra_toolbox.run_all_unrealisable_cores("module A\n")
            spectra_toolbox.run_all_unrealisable_cores("module B\n")

        self.assertEqual(2, raw.call_count)
        self.assertEqual(0, spectra_toolbox.unrealisable_core_cache_stats()["hits"])

    def test_a_caller_mutating_the_result_cannot_poison_the_cache(self):
        spec = "module Test\n"
        with mock.patch.object(spectra_toolbox, "is_realizable", return_value=False), \
             mock.patch.object(spectra_toolbox, "run_all_unrealisable_cores_raw"), \
             mock.patch.object(spectra_toolbox, "_extract_cores", return_value=[{4}]), \
             mock.patch.object(spectra_toolbox, "get_line_from_file",
                               return_value="guarantee -- g1"), \
             mock.patch.object(spectra_toolbox, "pRespondsToS_substitution"), \
             mock.patch.object(spectra_toolbox, "write_to_file"):
            first = spectra_toolbox.run_all_unrealisable_cores(spec)
            first[0].add("not_really_a_core")
            second = spectra_toolbox.run_all_unrealisable_cores(spec)

        self.assertEqual([{"g1"}], second)

    def test_realizable_result_is_cached_too(self):
        spec = "module Realizable\n"
        with mock.patch.object(spectra_toolbox, "is_realizable", return_value=True) as chk, \
             mock.patch.object(spectra_toolbox, "pRespondsToS_substitution"), \
             mock.patch.object(spectra_toolbox, "write_to_file"):
            self.assertEqual([], spectra_toolbox.run_all_unrealisable_cores(spec))
            self.assertEqual([], spectra_toolbox.run_all_unrealisable_cores(spec))

        self.assertEqual(1, chk.call_count,
                         "the realizability check is itself worth not repeating")

    def test_cache_can_be_switched_off(self):
        spec = "module Test\n"
        with mock.patch.dict("os.environ", {"SPEC_REPAIR_UC_CACHE": "0"}), \
             mock.patch.object(spectra_toolbox, "is_realizable", return_value=False), \
             mock.patch.object(spectra_toolbox, "run_all_unrealisable_cores_raw") as raw, \
             mock.patch.object(spectra_toolbox, "_extract_cores", return_value=[{4}]), \
             mock.patch.object(spectra_toolbox, "get_line_from_file",
                               return_value="guarantee -- g1"), \
             mock.patch.object(spectra_toolbox, "pRespondsToS_substitution"), \
             mock.patch.object(spectra_toolbox, "write_to_file"):
            spectra_toolbox.run_all_unrealisable_cores(spec)
            spectra_toolbox.run_all_unrealisable_cores(spec)

        self.assertEqual(2, raw.call_count)


if __name__ == "__main__":
    unittest.main()
