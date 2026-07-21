import unittest
import spot

from py_ltl.formula import LTLFormula, Globally, Implies, AtomicProposition, Not, Top, Bottom, Eventually, And, Or, \
    Next, Prev

from spec_repair.helpers.parsers.spectra_formula_parser import SpectraFormulaParser
from spec_repair.helpers.formatters.spot_formula_formatter import SpotFormulaFormatter
from spec_repair.util.ltl_formula_util import normalize_to_pattern, satisfies_ltl_formula, to_dnf


class TestLTLNormalization(unittest.TestCase):
    def setUp(self):
        self.a = AtomicProposition("a", True)
        self.b = AtomicProposition("b", True)
        self.c = AtomicProposition("c", True)
        self._formatter = SpotFormulaFormatter()
        self._parser = SpectraFormulaParser()

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
        f = LTLFormula.parse(f_str, self._parser)
        normalized = normalize_to_pattern(f)
        print("Normalized formula:", normalized)
        expected_normalized = Globally(Eventually(Or(Not(AtomicProposition("emergency", True)), AtomicProposition("car", False))))
        print("Expected normalized formula:", expected_normalized)
        self.assertTrue(self._equiv(normalized, expected_normalized))

    def test_spec_error_2(self):
        f_str = "\tG(PREV(pump=true)&pump=true->highwater=false);"
        f = LTLFormula.parse(f_str, self._parser)
        normalized = normalize_to_pattern(f)
        print("Normalized formula:", normalized)
        self.assertTrue(self._equiv(f, normalized))

    def test_spec_error_3(self):
        f_str = "G(((methane=true&PREV((highwater=true&highwater=false)))->next(pump=false)));"
        print(f_str)
        f = LTLFormula.parse(f_str, self._parser)
        print(f)
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

    def test_atom_true(self):
        f = self._parser.parse("p")
        trace = [{"p"}]
        self.assertTrue(satisfies_ltl_formula(f, trace))

    def test_atom_false(self):
        f = self._parser.parse("p")
        trace = [{"q"}]
        self.assertFalse(satisfies_ltl_formula(f, trace))

    def test_negation_true(self):
        f = self._parser.parse("!p")
        trace = [{"q"}]
        self.assertTrue(satisfies_ltl_formula(f, trace))

    def test_negation_false(self):
        f = self._parser.parse("!p")
        trace = [{"p"}]
        self.assertFalse(satisfies_ltl_formula(f, trace))

    def test_or_true(self):
        f = self._parser.parse("p | q")
        trace = [{"q"}]
        self.assertTrue(satisfies_ltl_formula(f, trace))

    def test_and_false(self):
        f = self._parser.parse("p & q")
        trace = [{"p"}]
        self.assertFalse(satisfies_ltl_formula(f, trace))

    def test_next_true(self):
        f = self._parser.parse("next(p)")
        trace = [{"q"}, {"p"}]
        self.assertTrue(satisfies_ltl_formula(f, trace))

    def test_next_false_end_of_trace(self):
        f = self._parser.parse("X p")
        trace = [{"q"}]  # no next state
        self.assertFalse(satisfies_ltl_formula(f, trace))

    def test_eventually_true(self):
        f = self._parser.parse("F(p)")
        trace = [{"q"}, {"q"}, {"p"}]
        self.assertTrue(satisfies_ltl_formula(f, trace))

    def test_globally_false(self):
        f = self._parser.parse("G(p)")
        trace = [{"p"}, {"q"}, {"p"}]
        self.assertFalse(satisfies_ltl_formula(f, trace))

    def test_prev_true(self):
        f = self._parser.parse("prev(p)")
        trace = [{"p"}, {"q"}]
        self.assertTrue(satisfies_ltl_formula(f, trace, t=1))

    def test_prev_false_wrong_value_at_previous_state(self):
        f = self._parser.parse("prev(p)")
        trace = [{"q"}, {"p"}]
        self.assertFalse(satisfies_ltl_formula(f, trace, t=1))

    def test_prev_false_no_previous_state(self):
        f = self._parser.parse("prev(p)")
        trace = [{"p"}]  # t=0, nothing before it
        self.assertFalse(satisfies_ltl_formula(f, trace, t=0))


class TestToDnf(unittest.TestCase):
    """
    Exhaustive coverage for to_dnf specifically (previously untested directly -
    only exercised indirectly through normalize_to_pattern). Semantic
    equivalence is checked via spot rather than structural equality, since
    to_dnf's exact And/Or associativity/ordering isn't part of its contract.
    """

    def setUp(self):
        self.a = AtomicProposition("a", True)
        self.b = AtomicProposition("b", True)
        self.c = AtomicProposition("c", True)
        self._formatter = SpotFormulaFormatter()

    def _equiv(self, formula1: LTLFormula, formula2: LTLFormula):
        f1 = spot.formula(formula1.format(self._formatter))
        f2 = spot.formula(formula2.format(self._formatter))
        return spot.are_equivalent(f1, f2)

    def _assert_trace_equiv(self, original: LTLFormula, dnf: LTLFormula):
        """
        Independent verification via satisfies_ltl_formula (a separately
        implemented interpreter) rather than spot-equivalence-to-a-hand-derived
        shape: to_dnf(original) must agree with original on every *interior*
        state of every trace below (1 <= t <= len-2, so both a Next and a
        Prev anywhere in the formula are guaranteed non-vacuous).

        Deliberately excludes t=0 and t=len-1: satisfies_ltl_formula treats
        Next at the last state and Prev at the first state as vacuously
        False *regardless of what they wrap* (already true before to_dnf
        existed - see test_next_false_end_of_trace). That convention makes
        !Next(x) and Next(!x) (equally !Prev(x) and Prev(!x)) disagree
        exactly at that boundary even though they're genuinely equivalent
        everywhere else and under spot's proper (boundary-free) semantics -
        see test_next_prev_negation_disagrees_at_trace_boundary below for
        that documented as its own thing, not silently swept under the rug.
        """
        traces = [
            [{"a"}, {"b"}, {"a", "b"}, {"a"}, {"b"}],
            [{"a", "b"}, set(), {"a"}, {"b"}, {"a", "b"}],
            [set(), {"a"}, {"b"}, set(), {"a", "b"}],
        ]
        for trace in traces:
            for t in range(1, len(trace) - 1):
                self.assertEqual(
                    satisfies_ltl_formula(original, trace, t),
                    satisfies_ltl_formula(dnf, trace, t),
                    f"mismatch on trace={trace} t={t}: "
                    f"original={original.format(self._formatter)} dnf={dnf.format(self._formatter)}"
                )

    # --- base cases: literals pass through unchanged ---

    def test_literal_atom(self):
        self.assertTrue(self._equiv(to_dnf(self.a), self.a))

    def test_literal_negated_atom(self):
        f = Not(self.a)
        self.assertTrue(self._equiv(to_dnf(f), f))

    def test_literal_top(self):
        self.assertTrue(self._equiv(to_dnf(Top()), Top()))

    def test_literal_bottom(self):
        self.assertTrue(self._equiv(to_dnf(Bottom()), Bottom()))

    def test_negated_top_passes_through(self):
        f = Not(Top())
        self.assertTrue(self._equiv(to_dnf(f), f))

    # --- De Morgan / double negation ---

    def test_double_negation(self):
        f = Not(Not(self.a))
        self.assertTrue(self._equiv(to_dnf(f), self.a))

    def test_negated_and(self):
        f = Not(And(self.a, self.b))
        self.assertTrue(self._equiv(to_dnf(f), Or(Not(self.a), Not(self.b))))

    def test_negated_or(self):
        f = Not(Or(self.a, self.b))
        self.assertTrue(self._equiv(to_dnf(f), And(Not(self.a), Not(self.b))))

    def test_negated_nested_and_or(self):
        # !((a&b)|c) === (!a|!b)&!c
        f = Not(Or(And(self.a, self.b), self.c))
        expected = And(Or(Not(self.a), Not(self.b)), Not(self.c))
        self.assertTrue(self._equiv(to_dnf(f), expected))

    # --- distribution: OR over AND ---

    def test_and_distributes_over_or_on_left(self):
        f = And(Or(self.a, self.b), self.c)
        expected = Or(And(self.a, self.c), And(self.b, self.c))
        self.assertTrue(self._equiv(to_dnf(f), expected))

    def test_and_distributes_over_or_on_right(self):
        f = And(self.a, Or(self.b, self.c))
        expected = Or(And(self.a, self.b), And(self.a, self.c))
        self.assertTrue(self._equiv(to_dnf(f), expected))

    def test_or_passthrough(self):
        f = Or(self.a, self.b)
        self.assertTrue(self._equiv(to_dnf(f), f))

    # --- implies ---

    def test_implies_rewritten_to_or(self):
        f = Implies(self.a, self.b)
        self.assertTrue(self._equiv(to_dnf(f), Or(Not(self.a), self.b)))

    # --- Next/Prev: no negation involved, should pass through untouched ---

    def test_next_of_literal_passthrough(self):
        f = Next(self.a)
        self.assertTrue(self._equiv(to_dnf(f), f))

    def test_prev_of_literal_passthrough(self):
        f = Prev(self.a)
        self.assertTrue(self._equiv(to_dnf(f), f))

    def test_next_of_conjunction_passthrough(self):
        f = Next(And(self.a, self.b))
        self.assertTrue(self._equiv(to_dnf(f), f))

    # --- Next/Prev negation-pushdown: the actual ColorSort bug ---

    def test_negated_next_of_atom(self):
        # !X(a) === X(!a)
        f = Not(Next(self.a))
        result = to_dnf(f)
        self.assertTrue(self._equiv(result, Next(Not(self.a))))
        self._assert_trace_equiv(f, result)

    def test_negated_prev_of_atom_not_implemented(self):
        """
        !P(a) is deliberately NOT rewritten to P(!a). This looked like a
        safe textbook identity (single-step temporal operators are
        bijective, so negation "should" commute through them same as
        Next), spot agreed both forms were equivalent, and 25 tests here
        confirmed no regressions - but it's actually FALSE under real
        Spectra semantics specifically because Prev has a genuine boundary
        at t=0 that Next never hits in a forward-infinite realizability
        game. Confirmed directly against the real Spectra CLI: built a
        minimal <->-shaped spec using !(a&PREV(!a)) as one guarantee and
        the "equivalent" Prev-pushed form as another - the CLI called the
        first realizable and the second unrealizable, on the exact same
        variables. SpotFormulaFormatter's shift-based rendering of Prev
        doesn't model the t=0 boundary at all, which is why spot didn't
        catch this. Whatever the fix eventually is, it isn't "just push
        the negation through" - stays NotImplementedError until there is one.
        """
        f = Not(Prev(self.a))
        with self.assertRaises(NotImplementedError):
            to_dnf(f)

    def test_negated_next_of_conjunction(self):
        # !X(a&b) === X(!a)|X(!b) - De Morgan has to reach *through* the Next
        f = Not(Next(And(self.a, self.b)))
        expected = Or(Next(Not(self.a)), Next(Not(self.b)))
        result = to_dnf(f)
        self.assertTrue(self._equiv(result, expected))
        self._assert_trace_equiv(f, result)

    def test_negated_prev_of_conjunction_not_implemented(self):
        f = Not(Prev(And(self.a, self.b)))
        with self.assertRaises(NotImplementedError):
            to_dnf(f)

    def test_negated_next_of_disjunction(self):
        # !X(a|b) === X(!a)&X(!b)
        f = Not(Next(Or(self.a, self.b)))
        expected = And(Next(Not(self.a)), Next(Not(self.b)))
        result = to_dnf(f)
        self.assertTrue(self._equiv(result, expected))
        self._assert_trace_equiv(f, result)

    def test_negated_prev_of_negation_not_implemented(self):
        # !P(!a) - same as test_negated_prev_of_atom_not_implemented, just
        # with the operand itself already negated.
        f = Not(Prev(Not(self.a)))
        with self.assertRaises(NotImplementedError):
            to_dnf(f)

    # --- Next/Prev distribution (no negation crossing the Prev boundary,
    # so this stays safe even at t=0 - see the module-level comment in
    # to_dnf): a disjunction produced *inside* the wrapper (e.g. by De
    # Morgan on a Next) must escape it, since nothing downstream expects
    # Next/Prev to ever wrap an Or ---

    def test_next_of_or_distributes_out(self):
        f = Next(Or(self.a, self.b))
        expected = Or(Next(self.a), Next(self.b))
        result = to_dnf(f)
        self.assertTrue(self._equiv(result, expected))
        self._assert_trace_equiv(f, result)

    def test_prev_of_or_distributes_out(self):
        f = Prev(Or(self.a, self.b))
        expected = Or(Prev(self.a), Prev(self.b))
        result = to_dnf(f)
        self.assertTrue(self._equiv(result, expected))
        self._assert_trace_equiv(f, result)

    def test_negated_and_containing_prev_not_implemented(self):
        # This is the literal ColorSort shape that started this
        # investigation: !(a & PREV(!b)). Confirmed via the real Spectra
        # CLI (see test_negated_prev_of_atom_not_implemented) that treating
        # this as !a | PREV(b) is actually wrong, so it correctly raises
        # instead of silently producing an incorrect DNF.
        f = Not(And(self.a, Prev(Not(self.b))))
        with self.assertRaises(NotImplementedError):
            to_dnf(f)

    def test_full_colorsort_iff_expansion_not_implemented(self):
        # (a & PREV(!b) & c) | (!(a & PREV(!b)) & !c) - the exact shape
        # produced by desugaring `a & PREV(b=false) <-> c` via A<->B ===
        # (A&B)|(!A&!B), taken directly from ColorSortLTL2_621's
        # `haltButton=PRESS & PREV(haltButton=RELEASE) <-> ...` formula.
        # Correctly refuses rather than silently computing a wrong DNF.
        conj = And(self.a, Prev(Not(self.b)))
        f = Or(And(conj, self.c), And(Not(conj), Not(self.c)))
        with self.assertRaises(NotImplementedError):
            to_dnf(f)

    def test_double_nested_next_prev_negation_not_implemented(self):
        # !X(P(a)): to_dnf correctly pushes the negation through the Next
        # (safe), but what's left, !P(a), still isn't implemented - the
        # unsafety of negating Prev doesn't go away just because it's
        # nested one level deeper.
        f = Not(Next(Prev(self.a)))
        with self.assertRaises(NotImplementedError):
            to_dnf(f)


if __name__ == "__main__":
    unittest.main()