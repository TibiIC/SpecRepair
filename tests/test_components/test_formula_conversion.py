import unittest
from unittest import TestCase

import pandas as pd

from spec_repair.components.spec_encoder import expression_to_str, \
    propositionalise_antecedent, propositionalise_consequent
from spec_repair.enums import When
from spec_repair.util.spec_util import parse_formula_str


class Test(TestCase):
    maxDiff = None


    def test_parse_formula(self):
        formula = "(next(a&b&c)&d&prev(e))|(next(f)&g&F(h&i))"
        output = parse_formula_str(formula)
        expected_output = [
            {'next': ['a', 'b', 'c'], 'current': ['d'], 'prev': ['e']},  # First conjunct
            {'next': ['f'], 'current': ['g'], 'eventually': ['h', 'i']}  # Second conjunct
        ]
        self.assertEqual(output, expected_output)

    def test_parse_formula_2(self):
        formula = "(next(a=true&b=true&c=false)&d=false&prev(e=true))|(next(f=false)&g=true&F(h=true&i=false))"
        output = parse_formula_str(formula)
        expected_output = [
            {'next': ['a=true', 'b=true', 'c=false'], 'current': ['d=false'], 'prev': ['e=true']},  # First conjunct
            {'next': ['f=false'], 'current': ['g=true'], 'eventually': ['h=true', 'i=false']}  # Second conjunct
        ]
        self.assertEqual(output, expected_output)

    def test_parse_formula_3(self):
        formula = "F(a=true&b=true)"
        output = parse_formula_str(formula)
        expected_output = [
            {'eventually': ['a=true', 'b=true']}
        ]
        self.assertEqual(output, expected_output)

    @unittest.skip("This test is not working")
    def test_parse_formula_4(self):
        formula = "F(a=true&b=true|c=true&d=false)"
        output = parse_formula_str(formula)
        expected_output = [
            {'eventually': ['a=true', 'b=true']},
            {'eventually': ['c=true', 'd=true']}
        ]
        self.assertEqual(output, expected_output)

    def test_parse_formula_4_edge_case(self):
        # NOTE: this means we need to handle the case when a justice rule has a disjunction inside it
        formula = "F(a=true&b=true)|F(c=true&d=false)"
        output = parse_formula_str(formula)
        expected_output = [
            {'eventually': ['a=true', 'b=true']},
            {'eventually': ['c=true', 'd=false']}
        ]
        self.assertEqual(output, expected_output)

    def test_propositionalise_assumption_exception_no_eventually(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_always',
            'formula': 'G(a=true);',
            'antecedent': "",
            'consequent': 'a=true',
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = expression_to_str(line, ['a_always'], for_clingo=False, is_ev_temp_op=False)
        expected = """
%assumption -- a_always
%\tG(a=true);

assumption(a_always).

antecedent_holds(a_always,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tnot antecedent_exception(a_always,0,T,S).

consequent_holds(a_always,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,a_always,0,T,S).

root_consequent_holds(OP,a_always,0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,T2,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_antecedent(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_always',
            'formula': 'G(a=true);',
            'antecedent': "",
            'consequent': "a=true",
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = propositionalise_antecedent(line, exception=False)
        expected = """
antecedent_holds(a_always,T,S):-
\ttrace(S),
\ttimepoint(T,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_antecedent_2(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_arrow_b',
            'formula': 'G(a=true->b=true);',
            'antecedent': "a=true",
            'consequent': "b=true",
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = propositionalise_antecedent(line, exception=False)
        expected = """
antecedent_holds(a_arrow_b,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(current,a_arrow_b,0,T,S).

root_antecedent_holds(OP,a_arrow_b,0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,T2,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_antecedent_exception(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_always',
            'formula': 'G(a=true);',
            'antecedent': "",
            'consequent': "a=false",
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = propositionalise_antecedent(line, exception=True)
        expected = """
antecedent_holds(a_always,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tnot antecedent_exception(a_always,0,T,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_antecedent_exception_2(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_arrow_b',
            'formula': 'G(a=true->b=true);',
            'antecedent': "a=false",
            'consequent': "b=false",
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = propositionalise_antecedent(line, exception=True)
        expected = """
antecedent_holds(a_arrow_b,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(current,a_arrow_b,0,T,S),
\tnot antecedent_exception(a_arrow_b,0,T,S).

root_antecedent_holds(OP,a_arrow_b,0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tnot_holds_at(a,T2,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_consequent(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_always',
            'formula': 'G(a=true);',
            'antecedent': "",
            'consequent': "a=true",
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = propositionalise_consequent(line, exception=False)
        expected = """
consequent_holds(a_always,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,a_always,0,T,S).

root_consequent_holds(OP,a_always,0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,T2,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_assumption_consequent_exception(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_always',
            'formula': 'G(a=true);',
            'antecedent': "",
            'consequent': "a=true",
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = propositionalise_consequent(line, exception=True)
        expected = """
consequent_holds(a_always,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,a_always,0,T,S),
\tnot ev_temp_op(a_always).

consequent_holds(a_always,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(eventually,a_always,0,T,S),
\tev_temp_op(a_always).

root_consequent_holds(OP,a_always,0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,T2,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_edge_case_1(self):
        line_data = {
            'type': 'guarantee',
            'name': 'guarantee1_1',
            'formula': 'G(r1=true->F(g1=true));',
            'antecedent': "r1=true",
            'consequent': "F(g1=true)",
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = expression_to_str(line, ['guarantee1_1'], for_clingo=True, is_ev_temp_op=True)
        expected = """
%guarantee -- guarantee1_1
%\tG(r1=true->F(g1=true));

guarantee(guarantee1_1).

antecedent_holds(guarantee1_1,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(current,guarantee1_1,0,T,S).

root_antecedent_holds(OP,guarantee1_1,0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(r1,T2,S).

consequent_holds(guarantee1_1,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(eventually,guarantee1_1,0,T,S).

root_consequent_holds(OP,guarantee1_1,0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(g1,T2,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_edge_case_2(self):
        line_data = {
            'type': 'guarantee',
            'name': 'guarantee3_1',
            'formula': 'G(a=false->g1=false&g2=false);',
            'antecedent': 'a=false',
            'consequent': 'g1=false&g2=false',
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = expression_to_str(line, ['guarantee3_1'], for_clingo=True, is_ev_temp_op=True)
        expected = """
%guarantee -- guarantee3_1
%	G(a=false->g1=false&g2=false);

guarantee(guarantee3_1).

antecedent_holds(guarantee3_1,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(current,guarantee3_1,0,T,S).

root_antecedent_holds(OP,guarantee3_1,0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tnot_holds_at(a,T2,S).

consequent_holds(guarantee3_1,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,guarantee3_1,0,T,S).

root_consequent_holds(OP,guarantee3_1,0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tnot_holds_at(g1,T2,S),
\tnot_holds_at(g2,T2,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_edge_case_3(self):
        line_data = {
            'type': 'guarantee',
            'name': 'guarantee4',
            'formula': 'G(g1=false|g2=false);',
            'antecedent': "",
            'consequent': 'g1=false|g2=false',
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = expression_to_str(line, ['guarantee4'], for_clingo=True, is_ev_temp_op=True)
        expected = """
%guarantee -- guarantee4
%	G(g1=false|g2=false);

guarantee(guarantee4).

antecedent_holds(guarantee4,T,S):-
\ttrace(S),
\ttimepoint(T,S).

consequent_holds(guarantee4,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,guarantee4,0,T,S).

root_consequent_holds(OP,guarantee4,0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tnot_holds_at(g1,T2,S).

consequent_holds(guarantee4,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,guarantee4,1,T,S).

root_consequent_holds(OP,guarantee4,1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tnot_holds_at(g2,T2,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_antecedent_disjunction(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_b_c',
            'formula': 'G(a=true|b=true->next(c=true));',
            'antecedent': "a=true|b=true",
            'consequent': "c=true",
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = propositionalise_antecedent(line, exception=False)
        expected = """
antecedent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(current,a_b_c,0,T,S).

root_antecedent_holds(OP,a_b_c,0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,T2,S).

antecedent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(current,a_b_c,1,T,S).

root_antecedent_holds(OP,a_b_c,1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,T2,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_antecedent_disjunction_of_conjunctions(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_b_c',
            'formula': 'G(a=true&b=true|c=true&d=true->next(e=true));',
            'antecedent': "(a=true&b=true)|(c=true&d=true)",
            'consequent': "e=true",
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = propositionalise_antecedent(line, exception=False)
        expected = """
antecedent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(current,a_b_c,0,T,S).

root_antecedent_holds(OP,a_b_c,0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,T2,S),
\tholds_at(b,T2,S).

antecedent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(current,a_b_c,1,T,S).

root_antecedent_holds(OP,a_b_c,1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(c,T2,S),
\tholds_at(d,T2,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_antecedent_disjunction_of_conjunctions_multi_op(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_b_c',
            'formula': 'G(PREV(a=true)&b=true|PREV(c=true)&d=true->next(e=true));',
            'antecedent': "(prev(a=true)&b=true)|(prev(c=true)&d=true)",
            'consequent': "e=true",
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = propositionalise_antecedent(line, exception=False)
        expected = """
antecedent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(prev,a_b_c,0,T,S),
\troot_antecedent_holds(current,a_b_c,1,T,S).

root_antecedent_holds(OP,a_b_c,0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,T2,S).

root_antecedent_holds(OP,a_b_c,1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,T2,S).

antecedent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(prev,a_b_c,2,T,S),
\troot_antecedent_holds(current,a_b_c,3,T,S).

root_antecedent_holds(OP,a_b_c,2,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(c,T2,S).

root_antecedent_holds(OP,a_b_c,3,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(d,T2,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_antecedent_disjunction_of_conjunctions_multi_op_exception(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_b_c',
            'formula': 'G(PREV(a=true)&b=true|PREV(c=true)&d=true->next(e=true));',
            'antecedent': "(prev(a=true)&b=true)|(prev(c=true)&d=true)",
            'consequent': "e=true",
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = propositionalise_antecedent(line, exception=True)
        expected = """
antecedent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(prev,a_b_c,0,T,S),
\troot_antecedent_holds(current,a_b_c,1,T,S),
\tnot antecedent_exception(a_b_c,0,T,S).

root_antecedent_holds(OP,a_b_c,0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(a,T2,S).

root_antecedent_holds(OP,a_b_c,1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,T2,S).

antecedent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_antecedent_holds(prev,a_b_c,2,T,S),
\troot_antecedent_holds(current,a_b_c,3,T,S),
\tnot antecedent_exception(a_b_c,1,T,S).

root_antecedent_holds(OP,a_b_c,2,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(c,T2,S).

root_antecedent_holds(OP,a_b_c,3,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(d,T2,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_consequent_disjunction(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_b_c',
            'formula': 'G(PREV(a=true)->b=true|c=true);',
            'antecedent': "prev(a=true)",
            'consequent': "b=true|c=true",
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = propositionalise_consequent(line, exception=False)
        expected = """
consequent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,a_b_c,0,T,S).

root_consequent_holds(OP,a_b_c,0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,T2,S).

consequent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,a_b_c,1,T,S).

root_consequent_holds(OP,a_b_c,1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(c,T2,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_consequent_disjunction_of_conjunctions(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_b_c',
            'formula': 'G(PREV(a=true)->b=true&c=true|d=true&e=true);',
            'antecedent': "prev(a=true)",
            'consequent': "b=true&c=true|d=true&e=true",
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = propositionalise_consequent(line, exception=False)
        expected = """
consequent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,a_b_c,0,T,S).

root_consequent_holds(OP,a_b_c,0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,T2,S),
\tholds_at(c,T2,S).

consequent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,a_b_c,1,T,S).

root_consequent_holds(OP,a_b_c,1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(d,T2,S),
\tholds_at(e,T2,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_consequent_disjunction_of_conjunctions_multi_op(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_b_c',
            'formula': 'G(PREV(a=true)->b=true&c=true|next(d=true)&next(e=true));',
            'antecedent': "prev(a=true)",
            'consequent': "(b=true&next(c=true))|(d=true&next(e=true))",
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = propositionalise_consequent(line, exception=False)
        expected = """
consequent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,a_b_c,0,T,S),
\troot_consequent_holds(next,a_b_c,1,T,S).

root_consequent_holds(OP,a_b_c,0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,T2,S).

root_consequent_holds(OP,a_b_c,1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(c,T2,S).

consequent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,a_b_c,2,T,S),
\troot_consequent_holds(next,a_b_c,3,T,S).

root_consequent_holds(OP,a_b_c,2,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(d,T2,S).

root_consequent_holds(OP,a_b_c,3,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(e,T2,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_assumption_disjunction_of_conjunctions_multi_op_exception(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_b_c',
            'formula': 'G(PREV(a=true)->b=true&next(c=true)|d=true&next(e=true));',
            'antecedent': "prev(a=true)",
            'consequent': "(b=true&next(c=true))|(d=true&next(e=true))",
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = propositionalise_consequent(line, exception=True)
        expected = """
consequent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,a_b_c,0,T,S),
\troot_consequent_holds(next,a_b_c,1,T,S),
\tnot ev_temp_op(a_b_c).

consequent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(eventually,a_b_c,0,T,S),
\troot_consequent_holds(eventually,a_b_c,1,T,S),
\tev_temp_op(a_b_c).

root_consequent_holds(OP,a_b_c,0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,T2,S).

root_consequent_holds(OP,a_b_c,1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(c,T2,S).

consequent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,a_b_c,2,T,S),
\troot_consequent_holds(next,a_b_c,3,T,S),
\tnot ev_temp_op(a_b_c).

consequent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(eventually,a_b_c,2,T,S),
\troot_consequent_holds(eventually,a_b_c,3,T,S),
\tev_temp_op(a_b_c).

root_consequent_holds(OP,a_b_c,2,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(d,T2,S).

root_consequent_holds(OP,a_b_c,3,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(e,T2,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_guarantee_disjunction_of_conjunctions_multi_op_exception(self):
        line_data = {
            'type': 'guarantee',
            'name': 'a_b_c',
            'formula': 'G(PREV(a=true)->b=true&next(c=true)|d=true&next(e=true));',
            'antecedent': "prev(a=true)",
            'consequent': "(b=true&next(c=true))|(d=true&next(e=true))",
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = propositionalise_consequent(line, exception=True)
        expected = """
consequent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,a_b_c,0,T,S),
\troot_consequent_holds(next,a_b_c,1,T,S),
\tnot ev_temp_op(a_b_c).

consequent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(eventually,a_b_c,0,T,S),
\troot_consequent_holds(eventually,a_b_c,1,T,S),
\tev_temp_op(a_b_c).

root_consequent_holds(OP,a_b_c,0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,T2,S).

root_consequent_holds(OP,a_b_c,1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(c,T2,S).

consequent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,a_b_c,2,T,S),
\troot_consequent_holds(next,a_b_c,3,T,S),
\tnot ev_temp_op(a_b_c).

consequent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(eventually,a_b_c,2,T,S),
\troot_consequent_holds(eventually,a_b_c,3,T,S),
\tev_temp_op(a_b_c).

root_consequent_holds(OP,a_b_c,2,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(d,T2,S).

root_consequent_holds(OP,a_b_c,3,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(e,T2,S).

consequent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tconsequent_exception(a_b_c,T,S),
\tnot ev_temp_op(a_b_c).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_justice_assumption(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_b_c',
            'formula': 'GF(b=true&c=true|d=true&e=true));',
            'antecedent': "",
            'consequent': "(b=true&c=true)|(d=true&e=true)",
            'when': When.EVENTUALLY
        }

        line = pd.Series(line_data)
        out = propositionalise_consequent(line, exception=False)
        expected = """
consequent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(eventually,a_b_c,0,T,S).

root_consequent_holds(OP,a_b_c,0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,T2,S),
\tholds_at(c,T2,S).

consequent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(eventually,a_b_c,1,T,S).

root_consequent_holds(OP,a_b_c,1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(d,T2,S),
\tholds_at(e,T2,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_implies_eventually(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_b_c',
            'formula': 'G(a=true->F(b=true&c=true)|F(d=true&e=true));',
            'antecedent': "a=true",
            'consequent': "F(b=true&c=true)|F(d=true&e=true)",
            'when': When.ALWAYS
        }

        line = pd.Series(line_data)
        out = propositionalise_consequent(line, exception=False)
        expected = """
consequent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(eventually,a_b_c,0,T,S).

root_consequent_holds(OP,a_b_c,0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,T2,S),
\tholds_at(c,T2,S).

consequent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(eventually,a_b_c,1,T,S).

root_consequent_holds(OP,a_b_c,1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(d,T2,S),
\tholds_at(e,T2,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_implies_eventually_exception(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_b_c',
            'formula': 'G(a=true->F(b=true&c=true|d=true&e=true)));',
            'antecedent': "",
            'consequent': "(b=true&c=true)|(d=true&e=true)",
            'when': When.EVENTUALLY
        }

        line = pd.Series(line_data)
        out = propositionalise_consequent(line, exception=False)
        expected = """
consequent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(eventually,a_b_c,0,T,S).

root_consequent_holds(OP,a_b_c,0,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(b,T2,S),
\tholds_at(c,T2,S).

consequent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(eventually,a_b_c,1,T,S).

root_consequent_holds(OP,a_b_c,1,T1,S):-
\ttrace(S),
\ttimepoint(T1,S),
\tnot weak_timepoint(T1,S),
\ttimepoint(T2,S),
\ttemporal_operator(OP),
\ttimepoint_of_op(OP,T1,T2,S),
\tholds_at(d,T2,S),
\tholds_at(e,T2,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

