import unittest
import spot

from spec_repair.util.spot_ltl_conjoining_util import rewrite_as_G_ant_to_dnf


class TestRewriteAsGAntToDNF(unittest.TestCase):
    """
    Unit tests for rewrite_as_G_ant_to_dnf().
    Each test conjoins two or more G(DNF->DNF) invariant formulas and checks:
      1. The rewriter does not raise an exception
      2. The result is equivalent to the original conjunction
      3. The result has the form G(... -> ...)
    Specific expected outputs are noted in comments where known.
    """

    def _check(self, formula_str, expected_str=None):
        """
        Helper: run the rewriter, assert equivalence, optionally assert exact output.
        Returns the result formula for further assertions.
        """
        original = spot.formula(formula_str)
        result = rewrite_as_G_ant_to_dnf(formula_str)

        # Must always be equivalent to original
        self.assertTrue(
            spot.are_equivalent(original, result),
            f"Result '{result}' is not equivalent to input '{formula_str}'"
        )

        # Must always be of the form G(...)
        self.assertEqual(result.kindstr(), "G",
            f"Expected G(...) but got kind '{result.kindstr()}': {result}")

        # Optionally check exact output
        if expected_str is not None:
            expected = spot.formula(expected_str)
            self.assertTrue(
                spot.are_equivalent(result, expected),
                f"Result '{result}' not equivalent to expected '{expected_str}'"
            )
            # Also check structural form matches
            self.assertEqual(str(result), str(expected),
                f"Result '{result}' differs structurally from expected '{expected_str}'"
            )

        return result

    # ------------------------------------------------------------------
    # 1. Baseline: your original motivating case
    # ------------------------------------------------------------------
    def test_original_case(self):
        """Single antecedent h, consequent narrows when p is also true."""
        self._check(
            "(G(h -> (Xp | m))) && (G((h & p) -> Xp))",
            expected_str="G(h -> ((m & !p) | Xp))"
        )

    # ------------------------------------------------------------------
    # 2. Same antecedent, two independent consequent constraints
    # ------------------------------------------------------------------
    def test_same_antecedent_two_constraints(self):
        """Both rules share antecedent h; consequents should be conjoined."""
        result = self._check(
            "(G(h -> (Xp | a))) && (G(h -> (Xq | b)))"
        )
        # Result should still be G(h -> ...)
        body = result[0]
        self.assertEqual(body.kindstr(), "Implies",
            f"Expected G(h -> ...) but body kind is '{body.kindstr()}'")

    # ------------------------------------------------------------------
    # 3. Antecedent refinement: broad then narrowed by extra condition
    # ------------------------------------------------------------------
    def test_antecedent_refinement_three_choices(self):
        """h -> a|b|c, but h&p -> must pick a."""
        self._check(
            "(G(h -> (a | b | c))) && (G((h & p) -> a))"
        )

    # ------------------------------------------------------------------
    # 4. Three conjoined rules with same antecedent h
    # ------------------------------------------------------------------
    def test_three_rules_same_antecedent(self):
        """Three G(h -> ...) rules; consequents should all be merged."""
        self._check(
            "(G(h -> (Xp | a))) && (G(h -> (Xq | b))) && (G(h -> (Xr | c)))"
        )

    # ------------------------------------------------------------------
    # 5. Disjunctive antecedent (h | k)
    # ------------------------------------------------------------------
    def test_disjunctive_antecedent(self):
        """Antecedent is h|k; refinement adds p constraint."""
        self._check(
            "(G((h | k) -> (Xp | m))) && (G(((h | k) & p) -> Xp))"
        )

    # ------------------------------------------------------------------
    # 6. Two separate refinements under h (on p and q independently)
    # ------------------------------------------------------------------
    def test_two_refinements_under_h(self):
        """h -> Xp|Xq|m, refined separately for p and for q."""
        self._check(
            "(G(h -> (Xp | Xq | m))) && (G((h & p) -> Xp)) && (G((h & q) -> Xq))"
        )

    # ------------------------------------------------------------------
    # 7. Redundant rule: stricter subsumes looser
    # ------------------------------------------------------------------
    def test_redundant_rule_subsumed(self):
        """G(h->Xp) is strictly stronger than G(h->(Xp|m)); result should be G(h->Xp)."""
        self._check(
            "(G(h -> Xp)) && (G(h -> (Xp | m)))",
            expected_str="G(h -> Xp)"
        )

    # ------------------------------------------------------------------
    # 8. Purely propositional invariants (no temporal operators)
    # ------------------------------------------------------------------
    def test_purely_propositional(self):
        """No X/G/F operators; h -> a|b, refined by h&b -> a."""
        self._check(
            "(G(h -> (a | b))) && (G((h & b) -> a))",
            expected_str="G(h -> a)"  # (a&!b)|(a&b) simplifies to just a
        )

    # ------------------------------------------------------------------
    # 9. Multiple antecedent literals refined further
    # ------------------------------------------------------------------
    def test_compound_antecedent_refined(self):
        """h&p -> a|b, then h&p&q -> a."""
        self._check(
            "(G((h & p) -> (a | b))) && (G((h & p & q) -> a))"
        )

    # ------------------------------------------------------------------
    # 10. Consequent is already a single literal (no real choice)
    # ------------------------------------------------------------------
    def test_forced_consequent(self):
        """Both rules force Xp; second rule is redundant."""
        self._check(
            "(G(h -> Xp)) && (G((h & p) -> Xp))",
            expected_str="G(h -> Xp)"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)