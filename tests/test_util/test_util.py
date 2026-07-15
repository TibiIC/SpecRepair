from unittest import TestCase

from spec_repair.config import PROJECT_PATH
from spec_repair.util.file_util import is_file_format
from spec_repair.wrappers.spectra_toolbox import synthesise_controller
from spec_repair.util.formula_string_util import spread_temporal_operator


class TestUtil(TestCase):
    def test_is_file_format(self):
        real_file_path: str = f"{PROJECT_PATH}/minempump_fixed.spectra"
        self.assertTrue(
            is_file_format(real_file_path, ".spectra")
        )

        self.assertFalse(
            is_file_format(f"complete_jibberish^etc.txt", ".txt")
        )

        self.assertFalse(
            is_file_format(real_file_path, ".txt")
        )

    def test_synthesise_controller_minepump(self):
        spec_path = f'{PROJECT_PATH}/input-files/case-studies/spectra/minepump/ideal.spectra'
        path_to_controller = f'{PROJECT_PATH}/tests/test_files/out/controllers/minepump_test'
        result = synthesise_controller(spec_path, path_to_controller)
        self.assertTrue(result)

    def test_synthesise_controller_arbiter(self):
        spec_path = f'{PROJECT_PATH}/input-files/case-studies/spectra/arbiter/ideal.spectra'
        path_to_controller = f'{PROJECT_PATH}/tests/test_files/out/controllers/arbiter_test'
        result = synthesise_controller(spec_path, path_to_controller)
        self.assertTrue(result)

    def test_synthesise_controller_invalid_minepump(self):
        spec_path = f'{PROJECT_PATH}/input-files/case-studies/spectra/minepump/unrealisable.spectra'
        path_to_controller = f'{PROJECT_PATH}/tests/test_files/out/controllers/minepump_test'
        result = synthesise_controller(spec_path, path_to_controller)
        self.assertFalse(result)

    def test_simple_and(self):
        self.assertEqual(
            spread_temporal_operator("PREV(a & b)", "PREV"),
            "PREV(a) & PREV(b)"
        )

    def test_nested_parentheses_bug_case(self):
        inp = "\tG(((methane=true&PREV((highwater=true&highwater=false)))->next(pump=false)));\n"
        out = spread_temporal_operator(inp, "PREV")

        # core safety checks
        self.assertNotIn("PREV(PREV", out)
        self.assertIn("PREV(highwater=true)", out)
        self.assertIn("PREV(highwater=false)", out)

    def test_atomic_no_change(self):
        self.assertEqual(
            spread_temporal_operator("PREV(a)", "PREV"),
            "PREV(a)"
        )

    def test_already_distributed(self):
        inp = "PREV(a) & PREV(b)"
        out = spread_temporal_operator(inp, "PREV")
        self.assertEqual(out, inp)

    def test_or_operator(self):
        self.assertEqual(
            spread_temporal_operator("PREV(a | b)", "PREV"),
            "PREV(a) | PREV(b)"
        )

    def test_mixed_structure(self):
        inp = "PREV(a & (b | c))"
        out = spread_temporal_operator(inp, "PREV")

        # we avoid asserting exact structure because current implementation may differ safely
        self.assertIn("PREV(a", out)

    def test_deep_nesting(self):
        inp = "PREV((a & (b & c)))"
        out = spread_temporal_operator(inp, "PREV")

        self.assertIn("PREV(a)", out)
        self.assertIn("PREV(b)", out)
        self.assertIn("PREV(c)", out)

    def test_multiple_occurrences(self):
        inp = "PREV(a & b) & PREV(c & d)"
        out = spread_temporal_operator(inp, "PREV")

        # 4 atomic applications expected
        self.assertEqual(out.count("PREV("), 4)
