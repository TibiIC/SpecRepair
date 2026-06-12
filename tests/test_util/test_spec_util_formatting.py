import unittest
import random
import re

from spec_repair.util.spec_util import spread_temporal_operator


class TestSpreadTemporalOperatorInvariants(unittest.TestCase):

    # -----------------------------
    # 1. Structural invariants
    # -----------------------------

    def test_no_nested_temporal_explosion(self):
        cases = [
            "PREV(a & b)",
            "PREV(a | b)",
            "PREV(a & (b | c))",
            "PREV((a & b) & c)",
        ]

        for x in cases:
            out = spread_temporal_operator(x, "PREV")
            self.assertNotIn("PREV(PREV", out)

    def test_operator_preservation(self):
        cases = [
            "PREV(a & b)",
            "PREV(a | b)",
            "PREV((a & b) | c)",
            "PREV(a & (b | c))",
        ]

        for x in cases:
            print(x)
            out = spread_temporal_operator(x, "PREV")
            print(out)

            self.assertEqual(x.count("&"), out.count("&"))
            self.assertEqual(x.count("|"), out.count("|"))

    def test_idempotence(self):
        cases = [
            "PREV(a & b)",
            "PREV(a | b)",
            "PREV((a & b) & c)",
            "PREV(a)",
        ]

        for x in cases:
            once = spread_temporal_operator(x, "PREV")
            twice = spread_temporal_operator(once, "PREV")

            self.assertEqual(once, twice)

    # -----------------------------
    # 2. Structural sanity checks
    # -----------------------------

    def test_parentheses_balance(self):
        cases = [
            "PREV(a & b)",
            "PREV((a & b) | (c & d))",
            "PREV(a | (b & (c | d)))",
        ]

        for x in cases:
            out = spread_temporal_operator(x, "PREV")

            self.assertEqual(out.count("("), out.count(")"))

    def test_no_loss_of_content(self):
        cases = [
            "PREV(a & b)",
            "PREV(a | b)",
            "PREV((x1 & x2) | x3)",
        ]

        for x in cases:
            out = spread_temporal_operator(x, "PREV")

            # all atomic symbols should still appear
            atoms_in = set(re.findall(r"[a-zA-Z_]\w*", x))
            atoms_out = set(re.findall(r"[a-zA-Z_]\w*", out))

            self.assertTrue(atoms_in.issubset(atoms_out))

    # -----------------------------
    # 3. Randomized fuzz tests
    # -----------------------------

    def generate_expr(self, depth=3):
        """Generate random boolean expressions."""
        vars = ["a", "b", "c", "d", "e"]
        ops = ["&", "|"]

        if depth == 0 or random.random() < 0.3:
            return random.choice(vars)

        left = self.generate_expr(depth - 1)
        right = self.generate_expr(depth - 1)
        op = random.choice(ops)

        return f"({left} {op} {right})"

    def test_random_fuzz_no_crash(self):
        for _ in range(50):
            expr = f"PREV({self.generate_expr(3)})"
            out = spread_temporal_operator(expr, "PREV")

            self.assertIsInstance(out, str)
            self.assertTrue(len(out) > 0)

    def test_random_fuzz_no_temporal_duplication(self):
        for _ in range(50):
            expr = f"PREV({self.generate_expr(3)})"
            out = spread_temporal_operator(expr, "PREV")

            self.assertNotIn("PREV(PREV", out)

    # -----------------------------
    # 4. Edge stability tests
    # -----------------------------

    def test_whitespace_resilience(self):
        cases = [
            "PREV( a & b )",
            "PREV(  a|b  )",
            "PREV( (a & b) | (c & d) )",
        ]

        for x in cases:
            out = spread_temporal_operator(x, "PREV")
            self.assertIsInstance(out, str)

    def test_repeated_applications_stability(self):
        x = "PREV(a & (b | c))"

        out = x
        for _ in range(5):
            out = spread_temporal_operator(out, "PREV")

        # should stabilize quickly
        self.assertEqual(
            spread_temporal_operator(out, "PREV"),
            out
        )


if __name__ == "__main__":
    unittest.main()