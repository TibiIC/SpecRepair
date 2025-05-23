import unittest

from spec_repair.helpers.spot_formatter import SpotFormatter

from py_ltl.formula import AtomicProposition, Not, And, Or, Until, Next, Globally, Eventually, Implies, Prev, Top, \
    Bottom

class TestSpotFormatter(unittest.TestCase):
    def setUp(self):
        self.formatter = SpotFormatter()

    def test_atomic(self):
        f = AtomicProposition("a", True)
        self.assertEqual(self.formatter.format(f), "a")

        f = AtomicProposition("x", False)
        self.assertEqual(self.formatter.format(f), "!x")

    def test_constants(self):
        self.assertEqual(self.formatter.format(Top()), "true")
        self.assertEqual(self.formatter.format(Bottom()), "false")

    def test_logical_ops(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)

        self.assertEqual(self.formatter.format(Not(a)), "!(a)")
        self.assertEqual(self.formatter.format(And(a, b)), "(a && b)")
        self.assertEqual(self.formatter.format(Or(a, b)), "(a || b)")
        self.assertEqual(self.formatter.format(Implies(a, b)), "(a -> b)")

    def test_temporal_ops(self):
        a = AtomicProposition("a", True)
        self.assertEqual(self.formatter.format(Next(a)), "X(a)")
        self.assertEqual(self.formatter.format(Prev(a)), "Y(a)")
        self.assertEqual(self.formatter.format(Eventually(a)), "F(a)")
        self.assertEqual(self.formatter.format(Globally(a)), "G(a)")

    def test_nested(self):
        f = And(Next(AtomicProposition("x", True)), Not(Top()))
        self.assertEqual(self.formatter.format(f), "(X(x) && !(true))")

    def test_implies_chain(self):
        f = Implies(Globally(AtomicProposition("r", True)),
                    Eventually(AtomicProposition("s", True)))
        self.assertEqual(self.formatter.format(f), "(G(r) -> F(s))")

if __name__ == "__main__":
    unittest.main()
