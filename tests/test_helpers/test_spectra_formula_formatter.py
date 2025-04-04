import unittest

from spec_repair.helpers.spectra_formula_formatter import SpectraFormulaFormatter

from py_ltl.formula import AtomicProposition, Not, And, Or, Until, Next, Globally, Eventually, Implies, Prev, Top, \
    Bottom

class TestSpectraFormatter(unittest.TestCase):
    def setUp(self):
        self.formatter = SpectraFormulaFormatter()

    def test_atomic_proposition_plain(self):
        f = AtomicProposition("x", True)
        self.assertEqual(self.formatter.format(f), "x=true")

    def test_atomic_proposition_with_value(self):
        f = AtomicProposition("y", False)
        self.assertEqual(self.formatter.format(f), "y=false")

        f = AtomicProposition("z", 5)
        self.assertEqual(self.formatter.format(f), "z=5")

    def test_true_false_constants(self):
        self.assertEqual(self.formatter.format(Top()), "true")
        self.assertEqual(self.formatter.format(Bottom()), "false")

    def test_not(self):
        f = Not(Top())
        self.assertEqual(self.formatter.format(f), "!(true)")

    def test_and_or_implies(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        self.assertEqual(self.formatter.format(And(a, b)), "(a=true&b=true)")
        self.assertEqual(self.formatter.format(Or(a, b)), "(a=true|b=true)")
        self.assertEqual(self.formatter.format(Implies(a, b)), "(a=true->b=true)")

    def test_temporal_operators(self):
        x = AtomicProposition("x", True)
        self.assertEqual(self.formatter.format(Next(x)), "next(x=true)")
        self.assertEqual(self.formatter.format(Prev(x)), "prev(x=true)")
        self.assertEqual(self.formatter.format(Eventually(x)), "F(x=true)")
        self.assertEqual(self.formatter.format(Globally(x)), "G(x=true)")

    def test_nested_formula(self):
        f = And(Next(AtomicProposition("a", True)), Not(Bottom()))
        self.assertEqual(self.formatter.format(f), "(next(a=true)&!(false))")

    def test_complex_formula(self):
        f = Implies(
            Globally(AtomicProposition("ready", True)),
            Eventually(AtomicProposition("done", True))
        )
        self.assertEqual(self.formatter.format(f), "(G(ready=true)->F(done=true))")

if __name__ == '__main__':
    unittest.main()