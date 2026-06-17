import unittest

from spec_repair.helpers.formatters.spot_formula_formatter import SpotFormulaFormatter

from py_ltl.formula import AtomicProposition, Not, And, Or, Next, Globally, Eventually, Implies, Prev, Top, \
    Bottom

class TestSpotFormatter(unittest.TestCase):
    def setUp(self):
        self.formatter = SpotFormulaFormatter()

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
        self.assertEqual(self.formatter.format(And(a, b)), "(a & b)")
        self.assertEqual(self.formatter.format(Or(a, b)), "(a | b)")
        self.assertEqual(self.formatter.format(Implies(a, b)), "(a -> b)")

    def test_temporal_ops(self):
        a = AtomicProposition("a", True)
        self.assertEqual(self.formatter.format(Next(a)), "X(a)")
        self.assertEqual(self.formatter.format(Prev(a)), "a")
        self.assertEqual(self.formatter.format(Eventually(a)), "F(a)")
        self.assertEqual(self.formatter.format(Globally(a)), "G(a)")

    def test_nested(self):
        f = And(Next(AtomicProposition("x", True)), Not(Top()))
        self.assertEqual(self.formatter.format(f), "(X(x) & !(true))")

    def test_implies_chain(self):
        f = Implies(Globally(AtomicProposition("r", True)),
                    Eventually(AtomicProposition("s", True)))
        self.assertEqual(self.formatter.format(f), "(G(r) -> F(s))")

    def test_prev_formula(self):
        f = Globally(Implies(And(Prev(AtomicProposition("pump", True)), AtomicProposition("pump", True)),
                             Next(AtomicProposition("highwater", False))))
        self.assertEqual(self.formatter.format(f), "G(((pump & X(pump)) -> X(X(!highwater))))")

    def test_complex_prev_formula(self):
        f = Globally(Implies(And(And(AtomicProposition("pump", True), Prev(AtomicProposition("pump", True))), Prev(Prev(AtomicProposition("pump", True)))),
                             Next(AtomicProposition("highwater", False))))
        self.assertEqual("G(((X((X(pump) & pump)) & pump) -> X(X(X(!highwater)))))", self.formatter.format(f))

    def test_response_pattern_as_dwyer_pattern(self):
        f = Globally(Implies(AtomicProposition("s", True),
                    Eventually(AtomicProposition("p", True))))
        self.assertEqual(self.formatter.format(f), "G((s -> F(p)))")
        f_string, d_index = self.formatter.format_dwyer_response_aware(f)
        self.assertEqual(f_string, "!dwyer_state_0 & G((!dwyer_state_0 & (!(s) | ((s) & (p))) & X(!dwyer_state_0)) | (!dwyer_state_0 & ((s) & !(p)) & X(dwyer_state_0)) | (dwyer_state_0 & (p) & X(!dwyer_state_0)) | (dwyer_state_0 & !(p) & X(dwyer_state_0))) & GF(!dwyer_state_0)")
        self.assertEqual(d_index, 1)

    def test_response_pattern_as_dwyer_pattern_against_false_equivalents(self):
        f = Implies(Globally(AtomicProposition("r", True)),
                    Eventually(AtomicProposition("s", True)))
        self.assertEqual(self.formatter.format(f), "(G(r) -> F(s))")
        f_string, d_index = self.formatter.format_dwyer_response_aware(f)
        self.assertEqual(f_string, "(G(r) -> F(s))")
        self.assertEqual(d_index, 0)

    def test_response_pattern_as_dwyer_pattern_complex(self):
        # G((methane -> F(X(!pump))))
        f = Globally(Implies(AtomicProposition("methane", True),
                             Eventually(Next(AtomicProposition("pump", False)))))
        self.assertEqual(self.formatter.format(f), "G((methane -> F(X(!pump))))")
        f_string, d_index = self.formatter.format_dwyer_response_aware(f)
        self.assertEqual(f_string, "!dwyer_state_0 & G((!dwyer_state_0 & (!(methane) | ((methane) & (X(!pump)))) & X(!dwyer_state_0)) | (!dwyer_state_0 & ((methane) & !(X(!pump))) & X(dwyer_state_0)) | (dwyer_state_0 & (X(!pump)) & X(!dwyer_state_0)) | (dwyer_state_0 & !(X(!pump)) & X(dwyer_state_0))) & GF(!dwyer_state_0)")
        self.assertEqual(d_index, 1)

    def test_response_pattern_as_dwyer_pattern_complex_2(self):
        # G((highwater -> F((X(pump) | X(methane)))))
        f = Globally(Implies(AtomicProposition("highwater", True),
                             Eventually(
                                 Or(Next(AtomicProposition("pump", True)), Next(AtomicProposition("methane", True))))))
        self.assertEqual(self.formatter.format(f), "G((highwater -> F((X(pump) | X(methane)))))")
        f_string, d_index = self.formatter.format_dwyer_response_aware(f, 2)
        self.assertEqual(f_string,
                         "!dwyer_state_2 & G((!dwyer_state_2 & (!(highwater) | ((highwater) & ((X(pump) | X(methane))))) & X(!dwyer_state_2)) | (!dwyer_state_2 & ((highwater) & !((X(pump) | X(methane)))) & X(dwyer_state_2)) | (dwyer_state_2 & ((X(pump) | X(methane))) & X(!dwyer_state_2)) | (dwyer_state_2 & !((X(pump) | X(methane))) & X(dwyer_state_2))) & GF(!dwyer_state_2)")
        self.assertEqual(d_index, 3)


if __name__ == "__main__":
    unittest.main()
