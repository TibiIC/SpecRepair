import unittest
import spot

from py_ltl.formula import LTLFormula, Globally, Implies, AtomicProposition, Not, Top, Bottom, Eventually, And, Or, Next

from spec_repair.helpers.spectra_formula_parser import SpectraFormulaParser
from spec_repair.helpers.spot_formula_formatter import SpotFormulaFormatter
from spec_repair.util.ltl_formula_util import normalize_to_pattern


class TestLTLNormalization(unittest.TestCase):
    def setUp(self):
        self.a = AtomicProposition("a", True)
        self.b = AtomicProposition("b", True)
        self.c = AtomicProposition("c", True)
        self._formatter = SpotFormulaFormatter()

    def _equiv(self, formula1: LTLFormula, formula2: LTLFormula):
        f1 = spot.formula(formula1.format(self._formatter))
        f2 = spot.formula(formula2.format(self._formatter))
        return spot.are_equivalent(f1, f2)

    def test_equiv_dnf(self):
        f = Or(And(self.a, self.b), And(self.a, self.b))
        normalized = normalize_to_pattern(f)
        self.assertTrue(self._equiv(f, normalized))

    def test_equiv_dnf_implies_dnf(self):
        f = Implies(And(self.a, self.b), Or(self.b, self.c))
        normalized = normalize_to_pattern(f)
        self.assertTrue(self._equiv(f, normalized))

    def test_equiv_g_dnf_implies_dnf_next(self):
        f = Globally(Implies(self.a, Next(self.b)))
        normalized = normalize_to_pattern(f)
        self.assertTrue(self._equiv(f, normalized))

    def test_equiv_g_dnf_implies_dnf(self):
        f = Globally(Implies(And(self.a, self.b), Or(self.b, self.c)))
        normalized = normalize_to_pattern(f)
        self.assertTrue(self._equiv(f, normalized))

    def test_equiv_g_dnf_implies_fdnf(self):
        f = Globally(Implies(And(self.a, self.b), Eventually(And(self.b, self.c))))
        normalized = normalize_to_pattern(f)
        self.assertTrue(self._equiv(f, normalized))

    def test_equiv_gf_dnf(self):
        f = Globally(Eventually(And(self.a, self.b)))  # Spot: GF(a ∧ b)
        normalized = normalize_to_pattern(f)
        self.assertTrue(self._equiv(f, normalized))

    def test_fails_not_convertible_to_normal_form(self):
        f = Implies(self.a, Eventually(self.b))  # not equivalent to G(F(f)) or G(f→g)
        with self.assertRaises(ValueError):
            normalize_to_pattern(f)

    def test_fails_not_convertible_eventually(self):
        f = Eventually(And(self.a, self.b))
        with self.assertRaises(ValueError):
            normalize_to_pattern(f)

    def test_fails_on_structural_noise(self):
        f = Or(Eventually(self.a), Eventually(self.b))  # could be similar to GF(a∨b) but not equivalent
        with self.assertRaises(ValueError):
            normalize_to_pattern(f)

    def test_equiv_with_constants(self):
        f = Globally(Implies(self.a, Top()))
        normalized = normalize_to_pattern(f)
        self.assertTrue(self._equiv(f, normalized))

    def test_not_equiv_due_to_missing_globally(self):
        f = Implies(And(self.a, self.b), Eventually(self.c))  # Missing outer G
        with self.assertRaises(ValueError):
            normalize_to_pattern(f)

    def test_spec_error(self):
        f_str = "GF((emergency=true->car=false))"
        f = LTLFormula.parse(f_str, SpectraFormulaParser())
        normalized = normalize_to_pattern(f)
        print("Normalized formula:", normalized)
        expected_normalized = Globally(Eventually(Or(Not(AtomicProposition("emergency", True)), AtomicProposition("car", False))))
        print("Expected normalized formula:", expected_normalized)
        self.assertTrue(self._equiv(normalized, expected_normalized))

    def test_spec_error_2(self):
        f_str = "\tG(PREV(pump=true)&pump=true->highwater=false);"
        f = LTLFormula.parse(f_str, SpectraFormulaParser())
        normalized = normalize_to_pattern(f)
        print("Normalized formula:", normalized)
        self.assertTrue(self._equiv(f, normalized))

    def test_ini_error(self):
        f = And(self.a, Or(self.b, Or(self.c, self.a)))
        normalized = normalize_to_pattern(f)
        print("Normalized formula:", normalized)
        expected_normalized = Or(And(self.a, self.b), Or(And(self.a, self.c), And(self.a, self.a)))
        print("Expected normalized formula:", expected_normalized)
        self.assertTrue(self._equiv(normalized, expected_normalized))


    def test_ini_error_2(self):
        f = And(self.a, Implies(self.b, self.c))
        normalized = normalize_to_pattern(f)
        print("Normalized formula:", normalized)
        expected_normalized = Or(And(self.a, Not(self.b)), And(self.a, self.c))
        print("Expected normalized formula:", expected_normalized)
        self.assertTrue(self._equiv(normalized, expected_normalized))


if __name__ == "__main__":
    unittest.main()