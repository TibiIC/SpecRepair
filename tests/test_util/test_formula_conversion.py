import unittest
from unittest import TestCase

import pandas as pd

from spec_repair.util.spec_util import expression_to_str, propositionalise_formula


class Test(TestCase):
    maxDiff = None
    expected = """
%assumption -- a_always
%\tG(a=true);

assumption(a_always).

antecedent_holds(a_always,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tnot antecedent_exception(a_always,T,S).

consequent_holds(current,a_always,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,a_always,T,S),
\tnot ev_temp_op(a_always).

root_consequent_holds(OP,a_always,T,S):-
\ttemporal_operator(OP),
\ttrace(S),
\ttimepoint(T,S),
\tholds_at(OP,a,T,S).
"""

    @unittest.expectedFailure
    def test_propositionalise_expression_old(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_always',
            'formula': 'G(a=true);',
            'antecedent': [],
            'consequent': ['holds_at(a,T,S)'],
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = expression_to_str(line, [], for_clingo=True)
        expected = """
%assumption -- a_always
%\tG(a=true);

assumption(a_always).

antecedent_holds(a_always,T,S):-
\ttrace(S),
\ttimepoint(T,S).

consequent_holds(a_always,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tholds_at(a,T,S).
    """
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_assumption_exception(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_always',
            'formula': 'G(a=true);',
            'antecedent': [],
            'consequent': ['holds_at(current,a,T,S)'],
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = expression_to_str(line, ['a_always'], for_clingo=False)
        expected = """
%assumption -- a_always
%\tG(a=true);

assumption(a_always).

antecedent_holds(a_always,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tnot antecedent_exception(a_always,T,S).

consequent_holds(current,a_always,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,a_always,T,S),
\tnot ev_temp_op(a_always).

root_consequent_holds(OP,a_always,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\ttemporal_operator(OP),
\tholds_at(OP,a,T,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_antecedent(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_always',
            'formula': 'G(a=true);',
            'antecedent': [],
            'consequent': ['holds_at(current,a,T,S)'],
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = propositionalise_formula(line, 'antecedent', exception=False)
        expected = """
antecedent_holds(a_always,T,S):-
\ttrace(S),
\ttimepoint(T,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_antecedent_exception(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_always',
            'formula': 'G(a=true);',
            'antecedent': [],
            'consequent': ['holds_at(current,a,T,S)'],
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = propositionalise_formula(line, 'antecedent', exception=True)
        expected = """
antecedent_holds(a_always,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tnot antecedent_exception(a_always,T,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    @unittest.expectedFailure
    def test_propositionalise_formula_consequent_old(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_always',
            'formula': 'G(a=true);',
            'antecedent': [],
            'consequent': ['holds_at(a,T,S)'],
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = propositionalise_formula(line, 'consequent', exception=False)
        expected = """
consequent_holds(a_always,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tholds_at(a,T,S).
"""
        self.assertMultiLineEqual(out.strip(), expected.strip())

    @unittest.expectedFailure
    def test_propositionalise_formula_consequent_exception_old(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_always',
            'formula': 'G(a=true);',
            'antecedent': [],
            'consequent': ['holds_at(a,T,S)'],
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = propositionalise_formula(line, 'consequent', exception=True)
        expected = """
consequent_holds(a_always,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tholds_at(a,T,S).

consequent_holds(a_always,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tconsequent_exception(a_always,T,S).
"""
        self.assertMultiLineEqual(out.strip(), expected.strip())

    def test_propositionalise_formula_consequent(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_always',
            'formula': 'G(a=true);',
            'antecedent': [],
            'consequent': ['holds_at(current,a,T,S)'],
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = propositionalise_formula(line, 'consequent', exception=False)
        expected = """
consequent_holds(current,a_always,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,a_always,T,S),
\tnot ev_temp_op(a_always).

root_consequent_holds(OP,a_always,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\ttemporal_operator(OP),
\tholds_at(OP,a,T,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_consequent_exception(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_always',
            'formula': 'G(a=true);',
            'antecedent': [],
            'consequent': ['holds_at(current,a,T,S)'],
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = propositionalise_formula(line, 'consequent', exception=True)
        expected = """
consequent_holds(current,a_always,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(current,a_always,T,S),
\tnot ev_temp_op(a_always).

root_consequent_holds(OP,a_always,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\ttemporal_operator(OP),
\tholds_at(OP,a,T,S).

root_consequent_holds(OP,a_always,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\ttemporal_operator(OP),
\tconsequent_exception(a_always,T,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_edge_case_1(self):
        line_data = {
            'type': 'guarantee',
            'name': 'guarantee1_1',
            'formula': 'G(r1=true->F(g1=true));',
            'antecedent': ['holds_at(current,r1,T,S)'],
            'consequent': ['holds_at(eventually,g1,T,S)'],
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = expression_to_str(line, ['guarantee1_1'], for_clingo=True)
        expected = """
%guarantee -- guarantee1_1
%\tG(r1=true->F(g1=true));

guarantee(guarantee1_1).

antecedent_holds(guarantee1_1,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tholds_at(current,r1,T,S).

consequent_holds(eventually,guarantee1_1,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\troot_consequent_holds(eventually,guarantee1_1,T,S).

root_consequent_holds(OP,guarantee1_1,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\ttemporal_operator(OP),
\tholds_at(OP,g1,T,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())


    def test_propositionalise_formula_edge_case_2(self):
        line_data = {
            'type': 'guarantee',
            'name': 'guarantee3_1',
            'formula': 'G(a=false->g1=false&g2=false);',
            'antecedent': ['not_holds_at(current,a,T,S)'],
            'consequent': ['not_holds_at(current,g1,T,S),\n\tnot_holds_at(current,g2,T,S)'],
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = expression_to_str(line, ['guarantee3_1'], for_clingo=True)
        expected = """
%guarantee -- guarantee3_1
%	G(a=false->g1=false&g2=false);

guarantee(guarantee3_1).

antecedent_holds(guarantee3_1,T,S):-
	trace(S),
	timepoint(T,S),
	not_holds_at(current,a,T,S).

consequent_holds(current,guarantee3_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(current,guarantee3_1,T,S),
	not ev_temp_op(guarantee3_1).

root_consequent_holds(OP,guarantee3_1,T,S):-
	trace(S),
	timepoint(T,S),
	temporal_operator(OP),
	not_holds_at(OP,g1,T,S),
	not_holds_at(OP,g2,T,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())


    def test_propositionalise_formula_edge_case_3(self):
        line_data = {
            'type': 'guarantee',
            'name': 'guarantee4',
            'formula': 'G(g1=false|g2=false);',
            'antecedent': [],
            'consequent': ['not_holds_at(current,g1,T,S)', 'not_holds_at(current,g2,T,S)'],
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = expression_to_str(line, ['guarantee4'], for_clingo=True)
        expected = """
%guarantee -- guarantee4
%	G(g1=false|g2=false);

guarantee(guarantee4).

antecedent_holds(guarantee4,T,S):-
	trace(S),
	timepoint(T,S).

consequent_holds(current,guarantee4,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(current,guarantee4,T,S),
	not ev_temp_op(guarantee4).

root_consequent_holds(OP,guarantee4,T,S):-
	trace(S),
	timepoint(T,S),
	temporal_operator(OP),
	not_holds_at(OP,g1,T,S).

root_consequent_holds(OP,guarantee4,T,S):-
	trace(S),
	timepoint(T,S),
	temporal_operator(OP),
	not_holds_at(OP,g2,T,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())

    def test_propositionalise_formula_antecedent_disjunction(self):
        line_data = {
            'type': 'assumption',
            'name': 'a_b_c',
            'formula': 'G(a=true|b=true->next(c=true));',
            'antecedent': ['holds_at(current,a,T,S)', 'holds_at(current,b,T,S)'],
            'consequent': ['holds_at(next,c,T,S)'],
            'when': 'When.ALWAYS'
        }

        line = pd.Series(line_data)
        out = propositionalise_formula(line, 'antecedent', exception=False)
        expected = """
antecedent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tholds_at(current,a,T,S).

antecedent_holds(a_b_c,T,S):-
\ttrace(S),
\ttimepoint(T,S),
\tholds_at(current,b,T,S).
"""
        self.assertMultiLineEqual(expected.strip(), out.strip())
