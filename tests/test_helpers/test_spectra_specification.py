import os
from unittest import TestCase

import pandas as pd

from spec_repair.helpers.adaptation_learned import Adaptation
from spec_repair.helpers.gr1_formula import GR1Formula
from spec_repair.helpers.spectra_formula_formatter import SpectraFormulaFormatter
from spec_repair.helpers.spectra_formula_parser import SpectraFormulaParser
from spec_repair.helpers.spectra_specification import SpectraSpecification, propositionalise_antecedent, \
    propositionalise_consequent
from spec_repair.helpers.spectra_atom import SpectraAtom
from spec_repair.ltl_types import GR1FormulaType, GR1TemporalType


class TestSpectraSpecification(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.parser = SpectraFormulaParser()
        cls.formatter = SpectraFormulaFormatter()
        # Change the working directory to the script's directory
        cls.original_working_directory = os.getcwd()
        test_components_dir = os.path.dirname(os.path.abspath(__file__))
        tests_dir = os.path.dirname(test_components_dir)
        os.chdir(tests_dir)
        # Some template spec for method testing
        cls.spec = SpectraSpecification.from_file("./test_files/minepump_strong.spectra")

    @classmethod
    def tearDownClass(cls):
        # Restore the original working directory
        os.chdir(cls.original_working_directory)

    def test_file_to_specification_records_all_formulas(self):
        spec_file = "./test_files/minepump_strong.spectra"
        spec = SpectraSpecification.from_file(spec_file)
        # get all entries at column "formula" in the DataFrame
        print(spec._formulas_df.columns)
        formulas = spec._formulas_df["formula"]
        expected_formulas: set[str] = {
            GR1Formula.from_str("\thighwater=false&methane=false;", self.parser).to_str(self.formatter),
            GR1Formula.from_str("\tpump=false;", self.parser).to_str(self.formatter),
            GR1Formula.from_str("G(highwater=true->next(pump=true));", self.parser).to_str(self.formatter),
            GR1Formula.from_str("G(methane=true->next(pump=false));", self.parser).to_str(self.formatter),
            GR1Formula.from_str("G(PREV(pump=true)&pump=true->next(highwater=false));", self.parser).to_str(self.formatter),
            GR1Formula.from_str("G(highwater=false|methane=false)", self.parser).to_str(self.formatter),
        }
        for formula in formulas:
            self.assertIn(formula.to_str(self.formatter), expected_formulas)

    def test_file_to_specification_records_all_atoms(self):
        spec_file = "./test_files/minepump_strong.spectra"
        spec = SpectraSpecification.from_file(spec_file)

        print(spec._atoms)
        expected_atoms_str: set[str] = {
            str(SpectraAtom.from_str("env boolean highwater;")),
            str(SpectraAtom.from_str("env boolean methane;")),
            str(SpectraAtom.from_str("sys boolean pump;")),
        }
        for atom in spec._atoms:
            self.assertIn(str(atom), expected_atoms_str)

    def test_integrate_learning_rule(self):
        spec_file = "./test_files/minepump_strong.spectra"
        spec = SpectraSpecification.from_file(spec_file)
        adaptation = Adaptation(
            type='antecedent_exception',
            formula_name='assumption2_1',
            disjunction_index=0,
            atom_temporal_operators=[('current', 'methane=true')]
        )
        spec.integrate(adaptation)

        formulas = spec._formulas_df["formula"]
        expected_formulas: set[str] = {
            GR1Formula.from_str("\thighwater=false&methane=false;", self.parser).to_str(self.formatter),
            GR1Formula.from_str("\tpump=false;", self.parser).to_str(self.formatter),
            GR1Formula.from_str("G(highwater=true->next(pump=true));", self.parser).to_str(self.formatter),
            GR1Formula.from_str("G(methane=true->next(pump=false));", self.parser).to_str(self.formatter),
            GR1Formula.from_str("G(PREV(pump=true)&pump=true->next(highwater=false));", self.parser).to_str(self.formatter),
            GR1Formula.from_str("G(methane=false->highwater=false|methane=false)", self.parser).to_str(self.formatter),
        }
        for formula in formulas:
            self.assertIn(formula.to_str(self.formatter), expected_formulas)


    def test_integrate_learning_rule_multiple(self):
        spec_file = "./test_files/minepump_strong.spectra"
        spec = SpectraSpecification.from_file(spec_file)
        adaptation = Adaptation(
            type='antecedent_exception',
            formula_name='assumption2_1',
            disjunction_index=0,
            atom_temporal_operators=[('current', 'methane=true')]
        )
        adaptation_2 = Adaptation(
            type="consequent_exception",
            formula_name="guarantee1_1",
            disjunction_index=None,
            atom_temporal_operators=[("current", "pump=true")]
        )
        adaptation_3 = Adaptation(
            type="consequent_exception",
            formula_name="guarantee2_1",
            disjunction_index=None,
            atom_temporal_operators=[("current", "pump=false")]
        )
        spec.integrate(adaptation)
        spec.integrate(adaptation_2)
        spec.integrate(adaptation_3)

        formulas = spec._formulas_df["formula"]
        expected_formulas: set[str] = {
            GR1Formula.from_str("\thighwater=false&methane=false;", self.parser).to_str(self.formatter),
            GR1Formula.from_str("\tpump=false;", self.parser).to_str(self.formatter),
            GR1Formula.from_str("G(highwater=true->pump=true|next(pump=true));", self.parser).to_str(self.formatter),
            GR1Formula.from_str("G(methane=true->pump=false|next(pump=false));", self.parser).to_str(self.formatter),
            GR1Formula.from_str("G(PREV(pump=true)&pump=true->next(highwater=false));", self.parser).to_str(self.formatter),
            GR1Formula.from_str("G(methane=false->highwater=false|methane=false)", self.parser).to_str(self.formatter),
        }
        for formula in formulas:
            self.assertIn(formula.to_str(self.formatter), expected_formulas)

    def test_to_str(self):
        spec_file = "./test_files/minepump_strong.spectra"
        spec = SpectraSpecification.from_file(spec_file)
        expected_str = (
            "env boolean highwater;\n"
            "env boolean methane;\n"
            "sys boolean pump;\n"
            "assumption -- initial_assumption\n"
            "ini(highwater=false&methane=false);\n"
            "guarantee -- initial_guarantee\n"
            "ini(pump=false);\n"
            "guarantee -- guarantee1_1\n"
            "G(highwater=true->next(pump=true));\n"
            "guarantee -- guarantee2_1\n"
            "G(methane=true->next(pump=false));\n"
            "assumption -- assumption1_1\n"
            "G(PREV(pump=true)&pump=true->next(highwater=false));\n"
            "assumption -- assumption2_1\n"
            "G(highwater=false|methane=false);"
        )
        spec_str = spec.to_str()
        # remove all new lines more than one from spec string
        spec_str = "\n".join(line for line in spec_str.split("\n") if line.strip())

        self.assertEqual(spec_str, expected_str)

    def test_propositionalise_assumption_exception_no_eventually(self):
        line_data = {
            'name': 'a_always',
            'type': GR1FormulaType.ASM,
            'when': GR1TemporalType.INVARIANT,
            'formula': GR1Formula.from_str("G(a=true);", parser=self.parser)
        }

        line = pd.Series(line_data)
        out = self.spec._formula_to_asp_str(line, ['a_always'], for_clingo=False, is_ev_temp_op=False)
        expected = """
%assumption -- a_always
%\tG(a=true)

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
            'name': 'a_always',
            'type': GR1FormulaType.ASM,
            'when': GR1TemporalType.INVARIANT,
            'formula': GR1Formula.from_str("G(a=true);", parser=self.parser)
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
            'name': 'a_arrow_b',
            'type': GR1FormulaType.ASM,
            'when': GR1TemporalType.INVARIANT,
            'formula': GR1Formula.from_str("G(a=true->b=true);", parser=self.parser)
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
            'name': 'a_always',
            'type': GR1FormulaType.ASM,
            'when': GR1TemporalType.INVARIANT,
            'formula': GR1Formula.from_str("G(a=true);", parser=self.parser)
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
            'name': 'a_arrow_b',
            'type': GR1FormulaType.ASM,
            'when': GR1TemporalType.INVARIANT,
            'formula': GR1Formula.from_str("G(a=false->b=false);", parser=self.parser)
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
            'name': 'a_always',
            'type': GR1FormulaType.ASM,
            'when': GR1TemporalType.INVARIANT,
            'formula': GR1Formula.from_str("G(a=true);", parser=self.parser)
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
            'name': 'a_always',
            'type': GR1FormulaType.ASM,
            'when': GR1TemporalType.INVARIANT,
            'formula': GR1Formula.from_str("G(a=true);", parser=self.parser)
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
            'name': 'guarantee1_1',
            'type': GR1FormulaType.GAR,
            'when': GR1TemporalType.INVARIANT,
            'formula': GR1Formula.from_str("G(r1=true->F(g1=true));", parser=self.parser)
        }

        line = pd.Series(line_data)
        out = self.spec._formula_to_asp_str(line, ['guarantee1_1'], for_clingo=True, is_ev_temp_op=True)
        expected = """
%guarantee -- guarantee1_1
%\tG((r1=true->F(g1=true)))

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
            'name': 'guarantee3_1',
            'type': GR1FormulaType.GAR,
            'when': GR1TemporalType.INVARIANT,
            'formula': GR1Formula.from_str("G(a=false->g1=false&g2=false);", parser=self.parser)
        }

        line = pd.Series(line_data)
        out = self.spec._formula_to_asp_str(line, ['guarantee3_1'], for_clingo=True, is_ev_temp_op=True)
        expected = """
%guarantee -- guarantee3_1
%	G((a=false->(g1=false&g2=false)))

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
            'name': 'guarantee4',
            'type': GR1FormulaType.GAR,
            'when': GR1TemporalType.INVARIANT,
            'formula': GR1Formula.from_str("G(g1=false|g2=false);", parser=self.parser)
        }

        line = pd.Series(line_data)
        out = self.spec._formula_to_asp_str(line, ['guarantee4'], for_clingo=True, is_ev_temp_op=True)
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
            'name': 'a_b_c',
            'type': GR1FormulaType.ASM,
            'when': GR1TemporalType.INVARIANT,
            'formula': GR1Formula.from_str("G(a=true|b=true->next(c=true));", parser=self.parser)
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
            'name': 'a_b_c',
            'type': GR1FormulaType.ASM,
            'when': GR1TemporalType.INVARIANT,
            'formula': GR1Formula.from_str("G(a=true&b=true|c=true&d=true->next(e=true));", parser=self.parser)
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
            'name': 'a_b_c',
            'type': GR1FormulaType.ASM,
            'when': GR1TemporalType.INVARIANT,
            'formula': GR1Formula.from_str("G(PREV(a=true)&b=true|PREV(c=true)&d=true->next(e=true));", parser=self.parser)
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
            'name': 'a_b_c',
            'type': GR1FormulaType.ASM,
            'when': GR1TemporalType.INVARIANT,
            'formula': GR1Formula.from_str("G(PREV(a=true)&b=true|PREV(c=true)&d=true->next(e=true));", parser=self.parser)
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
            'name': 'a_b_c',
            'type': GR1FormulaType.ASM,
            'when': GR1TemporalType.INVARIANT,
            'formula': GR1Formula.from_str("G(PREV(a=true)->b=true|c=true);", parser=self.parser)
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
            'name': 'a_b_c',
            'type': GR1FormulaType.ASM,
            'when': GR1TemporalType.INVARIANT,
            'formula': GR1Formula.from_str("G(PREV(a=true)->b=true&c=true|d=true&e=true);", parser=self.parser)
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
            'name': 'a_b_c',
            'type': GR1FormulaType.ASM,
            'when': GR1TemporalType.INVARIANT,
            'formula': GR1Formula.from_str("G(PREV(a=true)->b=true&next(c=true)|d=true&next(e=true));", parser=self.parser)
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
            'name': 'a_b_c',
            'type': GR1FormulaType.ASM,
            'when': GR1TemporalType.INVARIANT,
            'formula': GR1Formula.from_str("G(PREV(a=true)->b=true&next(c=true)|d=true&next(e=true));", parser=self.parser)
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
            'name': 'a_b_c',
            'type': GR1FormulaType.GAR,
            'when': GR1TemporalType.INVARIANT,
            'formula': GR1Formula.from_str("G(PREV(a=true)->b=true&next(c=true)|d=true&next(e=true));", parser=self.parser)
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
            'name': 'a_b_c',
            'type': GR1FormulaType.ASM,
            'when': GR1TemporalType.JUSTICE,
            'formula': GR1Formula.from_str("GF(b=true&c=true|d=true&e=true));", parser=self.parser)
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
            'name': 'a_b_c',
            'type': GR1FormulaType.ASM,
            'when': GR1TemporalType.INVARIANT,
            'formula': GR1Formula.from_str("G(a=true->F(b=true&c=true)|F(d=true&e=true));", parser=self.parser)
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
            'name': 'a_b_c',
            'type': GR1FormulaType.ASM,
            'when': GR1TemporalType.INVARIANT,
            'formula': GR1Formula.from_str("G(a=true->F(b=true&c=true|d=true&e=true)));", parser=self.parser)
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
