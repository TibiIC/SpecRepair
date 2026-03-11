import unittest
import spot

from spec_repair.util.spot_ltl_conjoining_util import (
    conjoin_and_simplify,
    rewrite_as_G_ant_to_dnf,
    encode_prev,
    decode_prev,
    classify_formula,
    FormulaType,
)


class TestSpotLtlConjoiningUtil(unittest.TestCase):

    # ---------------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------------

    def _check_rewrite(self, formula_str, expected_str=None):
        """Run rewrite_as_G_ant_to_dnf, assert equivalence, optionally assert exact output."""
        result_str = rewrite_as_G_ant_to_dnf(formula_str)
        self.assertIsInstance(result_str, str)
        self.assertTrue(result_str.startswith("G("),
            f"Expected result to start with 'G(' but got: {result_str}")
        original_encoded = spot.formula(encode_prev(formula_str))
        result_encoded = spot.formula(encode_prev(result_str))
        self.assertTrue(
            spot.are_equivalent(original_encoded, result_encoded),
            f"Result '{result_str}' is not equivalent to input '{formula_str}'"
        )
        if expected_str is not None:
            self.assertEqual(result_str, expected_str,
                f"Result '{result_str}' differs from expected '{expected_str}'"
            )
        return result_str

    def _check_equivalent(self, formula_a, formula_b, result_str):
        """Assert result is equivalent to the conjunction of the two inputs."""
        combined = spot.formula(encode_prev(f"({formula_a}) && ({formula_b})"))
        result = spot.formula(encode_prev(result_str))
        self.assertTrue(spot.are_equivalent(combined, result),
            f"Result '{result_str}' not equivalent to '{formula_a}' && '{formula_b}'"
        )

    # ---------------------------------------------------------------------------
    # encode_prev / decode_prev
    # ---------------------------------------------------------------------------

    def test_prev_encode_decode_roundtrip(self):
        cases = [
            "G(PREV(p) -> Xq)",
            "G(PREV(!p) -> Xq)",
            "G(!PREV(p) -> Xq)",
            "G((PREV(p) & h) -> (Xq | PREV(!r)))",
        ]
        for s in cases:
            self.assertEqual(decode_prev(encode_prev(s)), s,
                f"Round-trip failed for: {s}")

    # ---------------------------------------------------------------------------
    # classify_formula
    # ---------------------------------------------------------------------------

    def test_classify_invariant(self):
        self.assertEqual(classify_formula("G(h -> Xp)"), FormulaType.INVARIANT)

    def test_classify_invariant_with_prev(self):
        self.assertEqual(classify_formula("G(PREV(p) -> Xq)"), FormulaType.INVARIANT)

    def test_classify_justice(self):
        self.assertEqual(classify_formula("GF(p)"), FormulaType.JUSTICE)

    def test_classify_response(self):
        self.assertEqual(classify_formula("G(p -> F(q))"), FormulaType.RESPONSE)

    def test_classify_other(self):
        self.assertEqual(classify_formula("F(p)"), FormulaType.OTHER)

    def test_classify_invalid_x_in_antecedent(self):
        with self.assertRaises(ValueError) as ctx:
            classify_formula("G(X(p) -> Xq)")
        self.assertIn("antecedent contains X(...)", str(ctx.exception))

    def test_classify_invalid_prev_in_consequent(self):
        with self.assertRaises(ValueError) as ctx:
            classify_formula("G(h -> PREV(p))")
        self.assertIn("consequent contains PREV(...)", str(ctx.exception))

    # ---------------------------------------------------------------------------
    # rewrite_as_G_ant_to_dnf
    # ---------------------------------------------------------------------------

    def test_rewrite_original_case(self):
        self._check_rewrite(
            "(G(h -> (Xp | m))) && (G((h & p) -> Xp))",
            expected_str="G(h -> ((m & !p) | Xp))"
        )

    def test_rewrite_same_antecedent_two_constraints(self):
        result = self._check_rewrite("(G(h -> (Xp | a))) && (G(h -> (Xq | b)))")
        self.assertIn("h -> ", result)

    def test_rewrite_antecedent_refinement_three_choices(self):
        self._check_rewrite("(G(h -> (a | b | c))) && (G((h & p) -> a))")

    def test_rewrite_three_rules_same_antecedent(self):
        self._check_rewrite(
            "(G(h -> (Xp | a))) && (G(h -> (Xq | b))) && (G(h -> (Xr | c)))"
        )

    def test_rewrite_disjunctive_antecedent(self):
        self._check_rewrite(
            "(G((h | k) -> (Xp | m))) && (G(((h | k) & p) -> Xp))"
        )

    def test_rewrite_two_refinements_under_h(self):
        self._check_rewrite(
            "(G(h -> (Xp | Xq | m))) && (G((h & p) -> Xp)) && (G((h & q) -> Xq))"
        )

    def test_rewrite_redundant_rule_subsumed(self):
        self._check_rewrite(
            "(G(h -> Xp)) && (G(h -> (Xp | m)))",
            expected_str="G(h -> Xp)"
        )

    def test_rewrite_purely_propositional(self):
        self._check_rewrite(
            "(G(h -> (a | b))) && (G((h & b) -> a))",
            expected_str="G(h -> a)"
        )

    def test_rewrite_compound_antecedent_refined(self):
        self._check_rewrite("(G((h & p) -> (a | b))) && (G((h & p & q) -> a))")

    def test_rewrite_forced_consequent(self):
        self._check_rewrite(
            "(G(h -> Xp)) && (G((h & p) -> Xp))",
            expected_str="G(h -> Xp)"
        )

    def test_rewrite_prev_positive_atom(self):
        self._check_rewrite(
            "(G((PREV(p) & h) -> (Xq | m))) && (G((PREV(p) & h & q) -> Xq))"
        )

    def test_rewrite_prev_negated_inside(self):
        self._check_rewrite(
            "(G((PREV(!p) & h) -> (Xq | m))) && (G((PREV(!p) & h & q) -> Xq))"
        )

    def test_rewrite_prev_negated_outside(self):
        self._check_rewrite(
            "(G((!PREV(p) & h) -> (Xq | m))) && (G((!PREV(p) & h & q) -> Xq))"
        )

    # ---------------------------------------------------------------------------
    # conjoin_and_simplify
    # ---------------------------------------------------------------------------

    def test_conjoin_invariant_invariant_merges(self):
        result = conjoin_and_simplify("G(h -> (Xp | m))", "G((h & p) -> Xp)")
        self.assertEqual(result, "G(h -> ((m & !p) | Xp))")

    def test_conjoin_invariant_invariant_equivalent(self):
        a = "G(h -> (Xp | m))"
        b = "G((h & p) -> Xp)"
        self._check_equivalent(a, b, conjoin_and_simplify(a, b))

    def test_conjoin_invariant_justice_unchanged(self):
        a, b = "G(h -> Xp)", "GF(q)"
        self.assertEqual(conjoin_and_simplify(a, b), f"{a} & {b}")

    def test_conjoin_justice_invariant_unchanged(self):
        a, b = "GF(q)", "G(h -> Xp)"
        self.assertEqual(conjoin_and_simplify(a, b), f"{a} & {b}")

    def test_conjoin_invariant_response_unchanged(self):
        a, b = "G(h -> Xp)", "G(p -> F(q))"
        self.assertEqual(conjoin_and_simplify(a, b), f"{a} & {b}")

    def test_conjoin_response_invariant_unchanged(self):
        a, b = "G(p -> F(q))", "G(h -> Xp)"
        self.assertEqual(conjoin_and_simplify(a, b), f"{a} & {b}")

    def test_conjoin_justice_justice_unchanged(self):
        a, b = "GF(p)", "GF(q)"
        self.assertEqual(conjoin_and_simplify(a, b), f"{a} & {b}")

    def test_conjoin_justice_response_unchanged(self):
        a, b = "GF(p)", "G(p -> F(q))"
        self.assertEqual(conjoin_and_simplify(a, b), f"{a} & {b}")

    def test_conjoin_response_justice_unchanged(self):
        a, b = "G(p -> F(q))", "GF(p)"
        self.assertEqual(conjoin_and_simplify(a, b), f"{a} & {b}")

    def test_conjoin_response_response_unchanged(self):
        a, b = "G(p -> F(q))", "G(r -> F(s))"
        self.assertEqual(conjoin_and_simplify(a, b), f"{a} & {b}")

    def test_conjoin_other_raises(self):
        with self.assertRaises(ValueError):
            conjoin_and_simplify("F(p)", "G(h -> Xp)")

    def test_conjoin_other_b_raises(self):
        with self.assertRaises(ValueError):
            conjoin_and_simplify("G(h -> Xp)", "F(p)")

    def test_conjoin_invariant_invariant_with_prev(self):
        a = "G((PREV(p) & h) -> (Xq | m))"
        b = "G((PREV(p) & h & q) -> Xq)"
        result = conjoin_and_simplify(a, b)
        self.assertTrue(result.startswith("G("),
            f"Expected G(...) but got: {result}")
        self._check_equivalent(a, b, result)


if __name__ == "__main__":
    unittest.main(verbosity=2)