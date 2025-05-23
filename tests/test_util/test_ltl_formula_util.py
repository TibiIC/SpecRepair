import unittest

from py_ltl.formula import LTLFormula, Globally, Implies, AtomicProposition, Not, Top, Bottom, Eventually, And, Or

from spec_repair.util.ltl_formula_util import normalize_to_pattern, is_dnf


class TestLTLNormalization(unittest.TestCase):
    def setUp(self):
        self.a = AtomicProposition("a", True)
        self.b = AtomicProposition("b", True)
        self.c = AtomicProposition("c", True)
        self.t = Top()
        self.f = Bottom()

    def test_g_dnf_implies_dnf(self):
        formula = Globally(Implies(And(self.a, self.b), Or(self.b, self.c)))
        normalized = normalize_to_pattern(formula)
        self.assertIsInstance(normalized, Globally)
        self.assertIsInstance(normalized.formula, Implies)
        self.assertTrue(is_dnf(normalized.formula.left))
        self.assertTrue(is_dnf(normalized.formula.right))

    def test_g_dnf_implies_fdnf(self):
        formula = Globally(Implies(And(self.a, self.b), Eventually(And(self.b, self.c))))
        normalized = normalize_to_pattern(formula)
        self.assertIsInstance(normalized, Globally)
        self.assertIsInstance(normalized.formula, Implies)
        self.assertTrue(is_dnf(normalized.formula.left))
        self.assertIsInstance(normalized.formula.right, Eventually)
        self.assertTrue(is_dnf(normalized.formula.right.formula))

    def test_gf_dnf(self):
        formula = Eventually(And(self.a, self.b))
        normalized = normalize_to_pattern(formula)
        self.assertIsInstance(normalized, Globally)
        self.assertIsInstance(normalized.formula, Eventually)
        self.assertTrue(is_dnf(normalized.formula.formula))

    def test_non_conforming_formula_to_gf_dnf(self):
        formula = Implies(self.a, Eventually(self.b))  # not wrapped in G or GF
        normalized = normalize_to_pattern(formula)
        self.assertIsInstance(normalized, Globally)
        self.assertIsInstance(normalized.formula, Eventually)
        self.assertTrue(is_dnf(normalized.formula.formula))

    def test_deeply_nested(self):
        formula = Not(Or(self.a, Not(self.b)))  # not in DNF
        normalized = normalize_to_pattern(formula)
        self.assertIsInstance(normalized, Globally)
        self.assertIsInstance(normalized.formula, Eventually)
        self.assertTrue(is_dnf(normalized.formula.formula))

    def test_true_and_false_constants(self):
        formula = And(self.t, Not(self.f))  # should simplify to 'true'
        normalized = normalize_to_pattern(formula)
        self.assertIsInstance(normalized, Globally)
        self.assertIsInstance(normalized.formula, Eventually)
        self.assertTrue(is_dnf(normalized.formula.formula))

if __name__ == "__main__":
    unittest.main()