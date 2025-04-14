import unittest

from spec_repair.helpers.asp_formula_formatter import ASPFormulaFormatter

from py_ltl.formula import AtomicProposition, Not, And, Or, Until, Next, Globally, Eventually, Implies, Prev, Top, \
    Bottom

class TestASPFormatter(unittest.TestCase):
    def setUp(self):
        self.formatter = ASPFormulaFormatter()

    def test_atomic_proposition_true(self):
        f = AtomicProposition("x", True)
        self.assertEqual(f.format(self.formatter),
        """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(T,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(x,T2,S).\
""")

    def test_atomic_proposition_false(self):
        f = AtomicProposition("y", False)
        self.assertEqual(f.format(self.formatter),
"""\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(T,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tnot_holds_at(y,T2,S).\
""")

    def test_atomic_proposition_with_value(self):
        f = AtomicProposition("z", 5)
        with self.assertRaises(ValueError):
            self.formatter.format(f)

    def test_true_false_constants(self):
        with self.assertRaises(ValueError):
            self.formatter.format(Top())
        with self.assertRaises(ValueError):
            self.formatter.format(Bottom())

    def test_not(self):
        f = Not(AtomicProposition("x", True))
        self.assertEqual(self.formatter.format(f),
"""\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(T,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tnot_holds_at(x,T2,S).\
""")

        g = Not(AtomicProposition("x", False))
        self.assertEqual(self.formatter.format(g),
    """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(T,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(x,T2,S).\
""")

    def test_not_op(self):
        f = Not(Prev(AtomicProposition("x", True)))
        with self.assertRaises(ValueError):
            self.formatter.format(f)

    def test_and(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        self.assertEqual(self.formatter.format(And(a, b)), """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(T,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,T2,S),
\tholds_at(b,T2,S).\
""")

    def test_and_ops(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        self.assertEqual(self.formatter.format(And(Prev(a), Next(b))),
                         """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(T,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(prev,{name},0,0,S),
\troot_consequent_holds(next,{name},1,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,T2,S).

root_consequent_holds(OP,{name},1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,T2,S).\
""")

    def test_nested_and(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        c = AtomicProposition("c", True)
        self.assertEqual(self.formatter.format(And(And(a, b), c)),
                         """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(T,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,T2,S),
\tholds_at(b,T2,S),
\tholds_at(c,T2,S).\
""")


    def test_or(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        self.assertEqual(self.formatter.format(Or(a, b)),
                         """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(T,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,T2,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,{name},1,0,S).

root_consequent_holds(OP,{name},1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,T2,S).\
""")

    def test_implies(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)

        self.assertEqual(self.formatter.format(Implies(a, b)),
                         """\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(current,{name},0,T,S).

root_antecedent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,T2,S).

consequent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,{name},0,T,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,T2,S).\
""")

    def test_eventually(self):
        a = AtomicProposition("a", True)

        self.assertEqual(self.formatter.format(Eventually(a)),
                         """\
consequent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(eventually,{name},0,T,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,T2,S).\
""")

    def test_response(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)

        self.assertEqual(self.formatter.format(Implies(a,Eventually(b))),
                         """\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(current,{name},0,T,S).

root_antecedent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,T2,S).

consequent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(eventually,{name},0,T,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,T2,S).\
""")


if __name__ == '__main__':
    unittest.main()