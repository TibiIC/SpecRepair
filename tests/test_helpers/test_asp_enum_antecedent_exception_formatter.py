import unittest

from spec_repair.helpers.asp_enum_exception_formatter import ASPEnumExceptionFormatter

from py_ltl.formula import AtomicProposition, Not, And, Or, Until, Next, Globally, Eventually, Implies, Prev, Top, \
    Bottom

class TestASPAntecedentExceptionFormatter(unittest.TestCase):
    def setUp(self):
        self.formatter = ASPEnumExceptionFormatter(is_antecedent_exception=True)

    def test_atomic_proposition_true(self):
        f = AtomicProposition("x", True)
        self.assertEqual(f.format(self.formatter),
 """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\tnot antecedent_exception({name},0,0,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(x,true,T2,S).\
""")

    def test_atomic_proposition_false(self):
        f = AtomicProposition("y", False)
        self.assertEqual(f.format(self.formatter),
 """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\tnot antecedent_exception({name},0,0,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(y,false,T2,S).\
""")

    def test_atomic_proposition_enum(self):
        f = AtomicProposition("y", "HIGH")
        self.assertEqual(f.format(self.formatter),
"""\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\tnot antecedent_exception({name},0,0,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(y,high,T2,S).\
""")

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
\ttimepoint(0,S),
\tnot antecedent_exception({name},0,0,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(x,false,T2,S).\
""")

        g = Not(AtomicProposition("x", False))
        self.assertEqual(self.formatter.format(g),
"""\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\tnot antecedent_exception({name},0,0,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(x,true,T2,S).\
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
\ttimepoint(0,S),
\tnot antecedent_exception({name},0,0,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S),
\tholds_at(b,true,T2,S).\
""")

    def test_and_ops(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        self.assertEqual(self.formatter.format(And(Prev(a), Next(b))),
                     """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\tnot antecedent_exception({name},0,0,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(prev,{name},0,0,S),
\troot_consequent_holds(next,{name},1,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S).

root_consequent_holds(OP,{name},1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,true,T2,S).\
""")

    def test_nested_and(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        c = AtomicProposition("c", True)
        self.assertEqual(self.formatter.format(And(And(a, b), c)),
                     """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\tnot antecedent_exception({name},0,0,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S),
\tholds_at(b,true,T2,S),
\tholds_at(c,true,T2,S).\
""")

    def test_or(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        self.assertEqual(self.formatter.format(Or(a, b)),
                     """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\tnot antecedent_exception({name},0,0,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},1,0,S).

root_consequent_holds(OP,{name},1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,true,T2,S).\
""")

    def test_or_3(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        c = AtomicProposition("c", True)
        self.assertEqual(self.formatter.format(Or(Or(a, b), c)),
                     """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\tnot antecedent_exception({name},0,0,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},1,0,S).

root_consequent_holds(OP,{name},1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,true,T2,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},2,0,S).

root_consequent_holds(OP,{name},2,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(c,true,T2,S).\
""")

    def test_dnf(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        c = AtomicProposition("c", True)
        d = AtomicProposition("d", True)
        e = AtomicProposition("e", True)
        f = AtomicProposition("f", True)
        g = AtomicProposition("g", True)
        h = AtomicProposition("h", True)
        i = AtomicProposition("i", True)
        self.assertEqual(self.formatter.format(Or(Or(And(And(a, b), c), And(And(d, e), f)), And(And(g, h), i))),
                     """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\tnot antecedent_exception({name},0,0,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S),
\tholds_at(b,true,T2,S),
\tholds_at(c,true,T2,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},1,0,S).

root_consequent_holds(OP,{name},1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(d,true,T2,S),
\tholds_at(e,true,T2,S),
\tholds_at(f,true,T2,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},2,0,S).

root_consequent_holds(OP,{name},2,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(g,true,T2,S),
\tholds_at(h,true,T2,S),
\tholds_at(i,true,T2,S).\
""")

    def test_dnf_ops(self):
        a = Prev(AtomicProposition("a", True))
        b = AtomicProposition("b", True)
        c = Next(AtomicProposition("c", True))
        d = Prev(AtomicProposition("d", True))
        e = AtomicProposition("e", True)
        f = Next(AtomicProposition("f", True))
        g = Prev(AtomicProposition("g", True))
        h = AtomicProposition("h", True)
        i = Next(AtomicProposition("i", True))
        self.assertEqual(self.formatter.format(Or(Or(And(And(a, b), c), And(And(d, e), f)), And(And(g, h), i))),
                     """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\tnot antecedent_exception({name},0,0,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(prev,{name},0,0,S),
\troot_consequent_holds(current,{name},1,0,S),
\troot_consequent_holds(next,{name},2,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S).

root_consequent_holds(OP,{name},1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,true,T2,S).

root_consequent_holds(OP,{name},2,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(c,true,T2,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(prev,{name},3,0,S),
\troot_consequent_holds(current,{name},4,0,S),
\troot_consequent_holds(next,{name},5,0,S).

root_consequent_holds(OP,{name},3,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(d,true,T2,S).

root_consequent_holds(OP,{name},4,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(e,true,T2,S).

root_consequent_holds(OP,{name},5,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(f,true,T2,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(prev,{name},6,0,S),
\troot_consequent_holds(current,{name},7,0,S),
\troot_consequent_holds(next,{name},8,0,S).

root_consequent_holds(OP,{name},6,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(g,true,T2,S).

root_consequent_holds(OP,{name},7,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(h,true,T2,S).

root_consequent_holds(OP,{name},8,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(i,true,T2,S).\
""")

    def test_atomic_proposition_true_antecedent(self):
        a = AtomicProposition("a", True)
        x = AtomicProposition("x", True)
        self.assertEqual(Implies(a, x).format(self.formatter),
 """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_antecedent_holds(current,{name},0,0,S),
\tnot antecedent_exception({name},0,0,S).

root_antecedent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(x,true,T2,S).\
""")

    def test_atomic_proposition_false_antecedent(self):
        a = AtomicProposition("a", False)
        x = AtomicProposition("x", True)
        self.assertEqual(Implies(a, x).format(self.formatter),
 """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_antecedent_holds(current,{name},0,0,S),
\tnot antecedent_exception({name},0,0,S).

root_antecedent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,false,T2,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(x,true,T2,S).\
""")

    def test_not_antecedent(self):
        a = Not(AtomicProposition("a", True))
        x = AtomicProposition("x", True)
        self.assertEqual(self.formatter.format(Implies(a, x)),
 """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_antecedent_holds(current,{name},0,0,S),
\tnot antecedent_exception({name},0,0,S).

root_antecedent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,false,T2,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(x,true,T2,S).\
""")

        b = Not(AtomicProposition("b", False))
        self.assertEqual(self.formatter.format(Implies(b, x)),
 """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_antecedent_holds(current,{name},0,0,S),
\tnot antecedent_exception({name},0,0,S).

root_antecedent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,true,T2,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(x,true,T2,S).\
""")

    def test_and_antecedent(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        x = AtomicProposition("x", True)
        self.assertEqual(self.formatter.format(Implies(And(a, b),x)), """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_antecedent_holds(current,{name},0,0,S),
\tnot antecedent_exception({name},0,0,S).

root_antecedent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S),
\tholds_at(b,true,T2,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(x,true,T2,S).\
""")

    def test_and_ops_antecedent(self):
        a = Prev(AtomicProposition("a", True))
        b = Next(AtomicProposition("b", True))
        x = AtomicProposition("x", True)
        self.assertEqual(self.formatter.format(Implies(And(a, b),x)),
                         """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_antecedent_holds(prev,{name},0,0,S),
\troot_antecedent_holds(next,{name},1,0,S),
\tnot antecedent_exception({name},0,0,S).

root_antecedent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S).

root_antecedent_holds(OP,{name},1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,true,T2,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(x,true,T2,S).\
""")

    def test_nested_and_antecedent(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        c = AtomicProposition("c", True)
        x = AtomicProposition("x", True)
        self.assertEqual(self.formatter.format(Implies(And(And(a, b), c), x)),
                         """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_antecedent_holds(current,{name},0,0,S),
\tnot antecedent_exception({name},0,0,S).

root_antecedent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S),
\tholds_at(b,true,T2,S),
\tholds_at(c,true,T2,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(x,true,T2,S).\
""")

    def test_or_antecedent(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        x = AtomicProposition("x", True)
        self.assertEqual(self.formatter.format(Implies(Or(a, b), x)),
                         """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_antecedent_holds(current,{name},0,0,S),
\tnot antecedent_exception({name},0,0,S).

root_antecedent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S).

antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_antecedent_holds(current,{name},1,0,S),
\tnot antecedent_exception({name},1,0,S).

root_antecedent_holds(OP,{name},1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,true,T2,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(x,true,T2,S).\
""")

    def test_or_3_antecedent(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        c = AtomicProposition("c", True)
        x = AtomicProposition("x", True)
        self.assertEqual(self.formatter.format(Implies(Or(Or(a, b), c), x)),
                         """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_antecedent_holds(current,{name},0,0,S),
\tnot antecedent_exception({name},0,0,S).

root_antecedent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S).

antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_antecedent_holds(current,{name},1,0,S),
\tnot antecedent_exception({name},1,0,S).

root_antecedent_holds(OP,{name},1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,true,T2,S).

antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_antecedent_holds(current,{name},2,0,S),
\tnot antecedent_exception({name},2,0,S).

root_antecedent_holds(OP,{name},2,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(c,true,T2,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(x,true,T2,S).\
""")

    def test_dnf_antecedent(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        c = AtomicProposition("c", True)
        d = AtomicProposition("d", True)
        e = AtomicProposition("e", True)
        f = AtomicProposition("f", True)
        g = AtomicProposition("g", True)
        h = AtomicProposition("h", True)
        i = AtomicProposition("i", True)
        x = AtomicProposition("x", True)
        self.assertEqual(self.formatter.format(Implies(Or(Or(And(And(a, b), c), And(And(d, e), f)), And(And(g, h), i)),x)),
                         """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_antecedent_holds(current,{name},0,0,S),
\tnot antecedent_exception({name},0,0,S).

root_antecedent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S),
\tholds_at(b,true,T2,S),
\tholds_at(c,true,T2,S).

antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_antecedent_holds(current,{name},1,0,S),
\tnot antecedent_exception({name},1,0,S).

root_antecedent_holds(OP,{name},1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(d,true,T2,S),
\tholds_at(e,true,T2,S),
\tholds_at(f,true,T2,S).

antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_antecedent_holds(current,{name},2,0,S),
\tnot antecedent_exception({name},2,0,S).

root_antecedent_holds(OP,{name},2,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(g,true,T2,S),
\tholds_at(h,true,T2,S),
\tholds_at(i,true,T2,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(x,true,T2,S).\
""")

    def test_dnf_ops_antecedent(self):
        a = Prev(AtomicProposition("a", True))
        b = AtomicProposition("b", True)
        c = Next(AtomicProposition("c", True))
        d = Prev(AtomicProposition("d", True))
        e = AtomicProposition("e", True)
        f = Next(AtomicProposition("f", True))
        g = Prev(AtomicProposition("g", True))
        h = AtomicProposition("h", True)
        i = Next(AtomicProposition("i", True))
        x = AtomicProposition("x", True)
        self.assertEqual(self.formatter.format(Implies(Or(Or(And(And(a, b), c), And(And(d, e), f)), And(And(g, h), i)),x)),
                         """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_antecedent_holds(prev,{name},0,0,S),
\troot_antecedent_holds(current,{name},1,0,S),
\troot_antecedent_holds(next,{name},2,0,S),
\tnot antecedent_exception({name},0,0,S).

root_antecedent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S).

root_antecedent_holds(OP,{name},1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,true,T2,S).

root_antecedent_holds(OP,{name},2,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(c,true,T2,S).

antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_antecedent_holds(prev,{name},3,0,S),
\troot_antecedent_holds(current,{name},4,0,S),
\troot_antecedent_holds(next,{name},5,0,S),
\tnot antecedent_exception({name},1,0,S).

root_antecedent_holds(OP,{name},3,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(d,true,T2,S).

root_antecedent_holds(OP,{name},4,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(e,true,T2,S).

root_antecedent_holds(OP,{name},5,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(f,true,T2,S).

antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_antecedent_holds(prev,{name},6,0,S),
\troot_antecedent_holds(current,{name},7,0,S),
\troot_antecedent_holds(next,{name},8,0,S),
\tnot antecedent_exception({name},2,0,S).

root_antecedent_holds(OP,{name},6,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(g,true,T2,S).

root_antecedent_holds(OP,{name},7,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(h,true,T2,S).

root_antecedent_holds(OP,{name},8,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(i,true,T2,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(x,true,T2,S).\
""")

    def test_always_atomic_proposition_true(self):
        f = AtomicProposition("x", True)
        self.assertEqual(Globally(f).format(self.formatter),
        """\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tnot antecedent_exception({name},0,T,S).

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
\tholds_at(x,true,T2,S).\
""")

    def test_always_atomic_proposition_false(self):
        f = AtomicProposition("y", False)
        self.assertEqual(Globally(f).format(self.formatter),
"""\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tnot antecedent_exception({name},0,T,S).

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
\tholds_at(y,false,T2,S).\
""")

    def test_always_not(self):
        f = Not(AtomicProposition("x", True))
        self.assertEqual(self.formatter.format(Globally(f)),
"""\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tnot antecedent_exception({name},0,T,S).

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
\tholds_at(x,false,T2,S).\
""")

        g = Not(AtomicProposition("x", False))
        self.assertEqual(self.formatter.format(Globally(g)),
    """\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tnot antecedent_exception({name},0,T,S).

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
\tholds_at(x,true,T2,S).\
""")

    def test_always_and(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        self.assertEqual(self.formatter.format(Globally(And(a, b))), """\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tnot antecedent_exception({name},0,T,S).

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
\tholds_at(a,true,T2,S),
\tholds_at(b,true,T2,S).\
""")

    def test_always_and_ops(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        self.assertEqual(self.formatter.format(Globally(And(Prev(a), Next(b)))),
                         """\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tnot antecedent_exception({name},0,T,S).

consequent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(prev,{name},0,T,S),
\troot_consequent_holds(next,{name},1,T,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S).

root_consequent_holds(OP,{name},1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,true,T2,S).\
""")

    def test_always_nested_and(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        c = AtomicProposition("c", True)
        self.assertEqual(self.formatter.format(Globally(And(And(a, b), c))),
                         """\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tnot antecedent_exception({name},0,T,S).

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
\tholds_at(a,true,T2,S),
\tholds_at(b,true,T2,S),
\tholds_at(c,true,T2,S).\
""")


    def test_always_or(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        self.assertEqual(self.formatter.format(Globally(Or(a, b))),
                         """\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tnot antecedent_exception({name},0,T,S).

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
\tholds_at(a,true,T2,S).

consequent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,{name},1,T,S).

root_consequent_holds(OP,{name},1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,true,T2,S).\
""")

    def test_always_or_3(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        c = AtomicProposition("c", True)
        self.assertEqual(self.formatter.format(Globally(Or(Or(a, b), c))),
                         """\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tnot antecedent_exception({name},0,T,S).

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
\tholds_at(a,true,T2,S).

consequent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,{name},1,T,S).

root_consequent_holds(OP,{name},1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,true,T2,S).

consequent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,{name},2,T,S).

root_consequent_holds(OP,{name},2,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(c,true,T2,S).\
""")

    def test_always_dnf(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        c = AtomicProposition("c", True)
        d = AtomicProposition("d", True)
        e = AtomicProposition("e", True)
        f = AtomicProposition("f", True)
        g = AtomicProposition("g", True)
        h = AtomicProposition("h", True)
        i = AtomicProposition("i", True)
        self.assertEqual(self.formatter.format(Globally(Or(Or(And(And(a, b), c), And(And(d, e), f)), And(And(g, h), i)))),
                         """\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tnot antecedent_exception({name},0,T,S).

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
\tholds_at(a,true,T2,S),
\tholds_at(b,true,T2,S),
\tholds_at(c,true,T2,S).

consequent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,{name},1,T,S).

root_consequent_holds(OP,{name},1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(d,true,T2,S),
\tholds_at(e,true,T2,S),
\tholds_at(f,true,T2,S).

consequent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,{name},2,T,S).

root_consequent_holds(OP,{name},2,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(g,true,T2,S),
\tholds_at(h,true,T2,S),
\tholds_at(i,true,T2,S).\
""")

    def test_always_dnf_ops(self):
        a = Prev(AtomicProposition("a", True))
        b = AtomicProposition("b", True)
        c = Next(AtomicProposition("c", True))
        d = Prev(AtomicProposition("d", True))
        e = AtomicProposition("e", True)
        f = Next(AtomicProposition("f", True))
        g = Prev(AtomicProposition("g", True))
        h = AtomicProposition("h", True)
        i = Next(AtomicProposition("i", True))
        self.assertEqual(self.formatter.format(Globally(Or(Or(And(And(a, b), c), And(And(d, e), f)), And(And(g, h), i)))),
                         """\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tnot antecedent_exception({name},0,T,S).

consequent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(prev,{name},0,T,S),
\troot_consequent_holds(current,{name},1,T,S),
\troot_consequent_holds(next,{name},2,T,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S).

root_consequent_holds(OP,{name},1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,true,T2,S).

root_consequent_holds(OP,{name},2,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(c,true,T2,S).

consequent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(prev,{name},3,T,S),
\troot_consequent_holds(current,{name},4,T,S),
\troot_consequent_holds(next,{name},5,T,S).

root_consequent_holds(OP,{name},3,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(d,true,T2,S).

root_consequent_holds(OP,{name},4,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(e,true,T2,S).

root_consequent_holds(OP,{name},5,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(f,true,T2,S).

consequent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(prev,{name},6,T,S),
\troot_consequent_holds(current,{name},7,T,S),
\troot_consequent_holds(next,{name},8,T,S).

root_consequent_holds(OP,{name},6,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(g,true,T2,S).

root_consequent_holds(OP,{name},7,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(h,true,T2,S).

root_consequent_holds(OP,{name},8,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(i,true,T2,S).\
""")

    def test_always_eventually_dnf(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        c = AtomicProposition("c", True)
        d = AtomicProposition("d", True)
        e = AtomicProposition("e", True)
        f = AtomicProposition("f", True)
        g = AtomicProposition("g", True)
        h = AtomicProposition("h", True)
        i = AtomicProposition("i", True)
        self.assertEqual(
            self.formatter.format(Globally(Eventually(Or(Or(And(And(a, b), c), And(And(d, e), f)), And(And(g, h), i))))),
            """\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tnot antecedent_exception({name},0,T,S).

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
\tholds_at(a,true,T2,S),
\tholds_at(b,true,T2,S),
\tholds_at(c,true,T2,S).

consequent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(eventually,{name},1,T,S).

root_consequent_holds(OP,{name},1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(d,true,T2,S),
\tholds_at(e,true,T2,S),
\tholds_at(f,true,T2,S).

consequent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(eventually,{name},2,T,S).

root_consequent_holds(OP,{name},2,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(g,true,T2,S),
\tholds_at(h,true,T2,S),
\tholds_at(i,true,T2,S).\
""")

    def test_always_atomic_proposition_true_antecedent(self):
        a = AtomicProposition("a", True)
        x = AtomicProposition("x", True)
        self.assertEqual(Globally(Implies(a, x)).format(self.formatter),
"""\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(current,{name},0,T,S),
\tnot antecedent_exception({name},0,T,S).

root_antecedent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S).

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
\tholds_at(x,true,T2,S).\
""")

    def test_always_atomic_proposition_false_antecedent(self):
        a = AtomicProposition("a", False)
        x = AtomicProposition("x", True)
        self.assertEqual(Globally(Implies(a, x)).format(self.formatter),
"""\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(current,{name},0,T,S),
\tnot antecedent_exception({name},0,T,S).

root_antecedent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,false,T2,S).

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
\tholds_at(x,true,T2,S).\
""")

    def test_always_not_antecedent(self):
        a = Not(AtomicProposition("a", True))
        x = AtomicProposition("x", True)
        self.assertEqual(self.formatter.format(Globally(Implies(a, x))),
"""\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(current,{name},0,T,S),
\tnot antecedent_exception({name},0,T,S).

root_antecedent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,false,T2,S).

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
\tholds_at(x,true,T2,S).\
""")

        b = Not(AtomicProposition("b", False))
        self.assertEqual(self.formatter.format(Globally(Implies(b, x))),
"""\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(current,{name},0,T,S),
\tnot antecedent_exception({name},0,T,S).

root_antecedent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,true,T2,S).

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
\tholds_at(x,true,T2,S).\
""")

    def test_always_and_antecedent(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        x = AtomicProposition("x", True)
        self.assertEqual(self.formatter.format(Globally(Implies(And(a, b), x))), """\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(current,{name},0,T,S),
\tnot antecedent_exception({name},0,T,S).

root_antecedent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S),
\tholds_at(b,true,T2,S).

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
\tholds_at(x,true,T2,S).\
""")

    def test_always_and_ops_antecedent(self):
        a = Prev(AtomicProposition("a", True))
        b = Next(AtomicProposition("b", True))
        x = AtomicProposition("x", True)
        self.assertEqual(self.formatter.format(Globally(Implies(And(a, b), x))),
                         """\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(prev,{name},0,T,S),
\troot_antecedent_holds(next,{name},1,T,S),
\tnot antecedent_exception({name},0,T,S).

root_antecedent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S).

root_antecedent_holds(OP,{name},1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,true,T2,S).

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
\tholds_at(x,true,T2,S).\
""")

    def test_always_nested_and_antecedent(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        c = AtomicProposition("c", True)
        x = AtomicProposition("x", True)
        self.assertEqual(self.formatter.format(Globally(Implies(And(And(a, b), c), x))),
                         """\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(current,{name},0,T,S),
\tnot antecedent_exception({name},0,T,S).

root_antecedent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S),
\tholds_at(b,true,T2,S),
\tholds_at(c,true,T2,S).

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
\tholds_at(x,true,T2,S).\
""")

    def test_always_or_antecedent(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        x = AtomicProposition("x", True)
        self.assertEqual(self.formatter.format(Globally(Implies(Or(a, b), x))),
                         """\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(current,{name},0,T,S),
\tnot antecedent_exception({name},0,T,S).

root_antecedent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S).

antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(current,{name},1,T,S),
\tnot antecedent_exception({name},1,T,S).

root_antecedent_holds(OP,{name},1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,true,T2,S).

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
\tholds_at(x,true,T2,S).\
""")

    def test_always_or_3_antecedent(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        c = AtomicProposition("c", True)
        x = AtomicProposition("x", True)
        self.assertEqual(self.formatter.format(Globally(Implies(Or(Or(a, b), c), x))),
                         """\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(current,{name},0,T,S),
\tnot antecedent_exception({name},0,T,S).

root_antecedent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S).

antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(current,{name},1,T,S),
\tnot antecedent_exception({name},1,T,S).

root_antecedent_holds(OP,{name},1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,true,T2,S).

antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(current,{name},2,T,S),
\tnot antecedent_exception({name},2,T,S).

root_antecedent_holds(OP,{name},2,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(c,true,T2,S).

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
\tholds_at(x,true,T2,S).\
""")

    def test_always_dnf_antecedent(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        c = AtomicProposition("c", True)
        d = AtomicProposition("d", True)
        e = AtomicProposition("e", True)
        f = AtomicProposition("f", True)
        g = AtomicProposition("g", True)
        h = AtomicProposition("h", True)
        i = AtomicProposition("i", True)
        x = AtomicProposition("x", True)
        self.assertEqual(
            self.formatter.format(Globally(Implies(Or(Or(And(And(a, b), c), And(And(d, e), f)), And(And(g, h), i)), x))),
            """\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(current,{name},0,T,S),
\tnot antecedent_exception({name},0,T,S).

root_antecedent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S),
\tholds_at(b,true,T2,S),
\tholds_at(c,true,T2,S).

antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(current,{name},1,T,S),
\tnot antecedent_exception({name},1,T,S).

root_antecedent_holds(OP,{name},1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(d,true,T2,S),
\tholds_at(e,true,T2,S),
\tholds_at(f,true,T2,S).

antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(current,{name},2,T,S),
\tnot antecedent_exception({name},2,T,S).

root_antecedent_holds(OP,{name},2,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(g,true,T2,S),
\tholds_at(h,true,T2,S),
\tholds_at(i,true,T2,S).

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
\tholds_at(x,true,T2,S).\
""")

    def test_always_dnf_ops_antecedent(self):
        a = Prev(AtomicProposition("a", True))
        b = AtomicProposition("b", True)
        c = Next(AtomicProposition("c", True))
        d = Prev(AtomicProposition("d", True))
        e = AtomicProposition("e", True)
        f = Next(AtomicProposition("f", True))
        g = Prev(AtomicProposition("g", True))
        h = AtomicProposition("h", True)
        i = Next(AtomicProposition("i", True))
        x = AtomicProposition("x", True)
        self.assertEqual(
            self.formatter.format(Globally(Implies(Or(Or(And(And(a, b), c), And(And(d, e), f)), And(And(g, h), i)), x))),
            """\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(prev,{name},0,T,S),
\troot_antecedent_holds(current,{name},1,T,S),
\troot_antecedent_holds(next,{name},2,T,S),
\tnot antecedent_exception({name},0,T,S).

root_antecedent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,true,T2,S).

root_antecedent_holds(OP,{name},1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,true,T2,S).

root_antecedent_holds(OP,{name},2,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(c,true,T2,S).

antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(prev,{name},3,T,S),
\troot_antecedent_holds(current,{name},4,T,S),
\troot_antecedent_holds(next,{name},5,T,S),
\tnot antecedent_exception({name},1,T,S).

root_antecedent_holds(OP,{name},3,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(d,true,T2,S).

root_antecedent_holds(OP,{name},4,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(e,true,T2,S).

root_antecedent_holds(OP,{name},5,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(f,true,T2,S).

antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(prev,{name},6,T,S),
\troot_antecedent_holds(current,{name},7,T,S),
\troot_antecedent_holds(next,{name},8,T,S),
\tnot antecedent_exception({name},2,T,S).

root_antecedent_holds(OP,{name},6,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(g,true,T2,S).

root_antecedent_holds(OP,{name},7,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(h,true,T2,S).

root_antecedent_holds(OP,{name},8,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(i,true,T2,S).

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
\tholds_at(x,true,T2,S).\
""")

    def test_eventually(self):
        a = AtomicProposition("a", True)

        self.assertEqual(self.formatter.format(Globally(Eventually(a))),
                         """\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tnot antecedent_exception({name},0,T,S).

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
\tholds_at(a,true,T2,S).\
""")

    def test_response_edge_case(self):
        x = AtomicProposition("x", True)

        self.assertEqual(self.formatter.format(Globally(Implies(Top(),Eventually(x)))),
                         """\
antecedent_holds({name},T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tnot antecedent_exception({name},0,T,S).

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
\tholds_at(x,true,T2,S).\
""")

    def test_not_conjunction(self):
        h = AtomicProposition("highwater", True)
        m = AtomicProposition("methane", True)

        self.assertEqual(self.formatter.format(And(Not(h), Not(m))),
                         """\
antecedent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\tnot antecedent_exception({name},0,0,S).

consequent_holds({name},0,S):-
\ttrace(S),
\ttimepoint(0,S),
\troot_consequent_holds(current,{name},0,0,S).

root_consequent_holds(OP,{name},0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(highwater,false,T2,S),
\tholds_at(methane,false,T2,S).\
""")

    def test_always_eventually_implies(self):
        a = AtomicProposition("a", True)
        b = AtomicProposition("b", True)
        with self.assertRaises(ValueError):
            self.formatter.format(Globally(Eventually(Implies(a, b))))

if __name__ == '__main__':
    unittest.main()