import os
import unittest
from typing import Tuple
from unittest import TestCase
# import warnings
# warnings.simplefilter('always', DeprecationWarning)

import numpy as np
import pandas as pd
import spot

from spec_repair.helpers.adaptation_learned import Adaptation
from spec_repair.helpers.gr1_formula import GR1Formula
from spec_repair.helpers.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.helpers.spectra_formula_formatter import SpectraFormulaFormatter
from spec_repair.helpers.spectra_formula_parser import SpectraFormulaParser
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.helpers.spectra_atom import SpectraAtom
from spec_repair.helpers.spot_specification_formatter import SpotSpecificationFormatter
from spec_repair.ltl_types import GR1FormulaType, GR1TemporalType
from tests.test_common_utility_strings.specs import spec_perf, spec_fixed_perf, spec_fixed_imperf, \
    spec_asm_eq_gar_weaker, spec_asm_stronger_gar_eq


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
            GR1Formula.from_str("G(PREV(pump=true)&pump=true->next(highwater=false));", self.parser).to_str(
                self.formatter),
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
            GR1Formula.from_str("G(PREV(pump=true)&pump=true->next(highwater=false));", self.parser).to_str(
                self.formatter),
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
            GR1Formula.from_str("G(highwater=true->next(pump=true)|pump=true);", self.parser).to_str(self.formatter),
            GR1Formula.from_str("G(methane=true->next(pump=false)|pump=false);", self.parser).to_str(self.formatter),
            GR1Formula.from_str("G(PREV(pump=true)&pump=true->next(highwater=false));", self.parser).to_str(
                self.formatter),
            GR1Formula.from_str("G(methane=false->highwater=false|methane=false)", self.parser).to_str(self.formatter),
        }
        for formula in formulas:
            self.assertIn(formula.to_str(self.formatter), expected_formulas)

    def test_to_str(self):
        spec_file = "./test_files/minepump_strong.spectra"
        spec = SpectraSpecification.from_file(spec_file)
        expected_str = (
            "module Minepump\n"
            "env boolean highwater;\n"
            "env boolean methane;\n"
            "sys boolean pump;\n"
            "assumption -- initial_assumption\n"
            "\t(highwater=false&methane=false);\n"
            "guarantee -- initial_guarantee\n"
            "\tpump=false;\n"
            "guarantee -- guarantee1_1\n"
            "\tG((highwater=true->next(pump=true)));\n"
            "guarantee -- guarantee2_1\n"
            "\tG((methane=true->next(pump=false)));\n"
            "assumption -- assumption1_1\n"
            "\tG(((PREV(pump=true)&pump=true)->next(highwater=false)));\n"
            "assumption -- assumption2_1\n"
            "\tG((highwater=false|methane=false));"
        )
        spec_str = spec.to_str()
        # remove all new lines more than one from spec string
        spec_str = "\n".join(line for line in spec_str.split("\n") if line.strip())

        self.assertEqual(expected_str, spec_str)

    def test_propositionalise_assumption_exception_no_eventually(self):
        line_data = {
            'name': 'a_always',
            'type': GR1FormulaType.ASM,
            'when': GR1TemporalType.INVARIANT,
            'formula': GR1Formula.from_str("G(a=true);", parser=self.parser)
        }

        line = pd.Series(line_data)
        hm = NoFilterHeuristicManager()
        hm.set_disabled("CONSEQUENT_WEAKENING")
        hm.set_disabled("INVARIANT_TO_RESPONSE_WEAKENING")
        out = self.spec._formula_to_asp_str(line, ['a_always'], for_clingo=False, hm=hm)
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

    def test_propositionalise_formula_edge_case_1(self):
        line_data = {
            'name': 'guarantee1_1',
            'type': GR1FormulaType.GAR,
            'when': GR1TemporalType.INVARIANT,
            'formula': GR1Formula.from_str("G(r1=true->F(g1=true));", parser=self.parser)
        }

        line = pd.Series(line_data)
        hm = NoFilterHeuristicManager()
        hm.set_enabled("INVARIANT_TO_RESPONSE_WEAKENING")
        out = self.spec._formula_to_asp_str(line, ['guarantee1_1'], for_clingo=True, hm=hm)
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
        hm = NoFilterHeuristicManager()
        hm.set_disabled("CONSEQUENT_WEAKENING")
        hm.set_enabled("INVARIANT_TO_RESPONSE_WEAKENING")
        out = self.spec._formula_to_asp_str(line, ['guarantee3_1'], for_clingo=True, hm=hm)
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
        hm = NoFilterHeuristicManager()
        hm.set_disabled("ANTECEDENT_WEAKENING")
        hm.set_enabled("INVARIANT_TO_RESPONSE_WEAKENING")
        out = self.spec._formula_to_asp_str(line, ['guarantee4'], for_clingo=True, hm=hm)
        expected = """
%guarantee -- guarantee4
%	G((g1=false|g2=false))

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

    def _equiv(self, formula1: str, formula2: str):
        """
        precondition: formula1 and formula2 are spot formulas
        """
        f1 = spot.formula(formula1)
        f2 = spot.formula(formula2)
        return spot.are_equivalent(f1, f2)

    def test_arbiter_compare(self):
        spec_ideal: SpectraSpecification = SpectraSpecification.from_file(
            "../input-files/case-studies/spectra/arbiter/ideal.spectra")
        spec_trivial: SpectraSpecification = SpectraSpecification.from_file(
            "./test_files/out/trivial_solutions/arbiter.spectra")
        self.assertTrue(spec_ideal.implies(spec_trivial, GR1FormulaType.GAR))
        self.assertTrue(spec_ideal.implies(spec_trivial, GR1FormulaType.ASM))

    def test_minepump_compare(self):
        spec_ideal: SpectraSpecification = SpectraSpecification.from_file(
            "../input-files/case-studies/spectra/minepump/ideal.spectra")
        spec_strong: SpectraSpecification = SpectraSpecification.from_file(
            "../input-files/case-studies/spectra/minepump/strong.spectra")
        self.assertTrue(spec_ideal.implied_by(spec_strong, GR1FormulaType.GAR))
        self.assertTrue(spec_ideal.implied_by(spec_strong, GR1FormulaType.ASM))

    def test_minepump_is_trivial(self):
        spec_ideal: SpectraSpecification = SpectraSpecification.from_file(
            "../input-files/case-studies/spectra/minepump/ideal.spectra")
        self.assertFalse(spec_ideal.is_trivial_true(GR1FormulaType.ASM))
        self.assertFalse(spec_ideal.is_trivial_false(GR1FormulaType.ASM))

        spec_strong: SpectraSpecification = SpectraSpecification.from_file(
            "../input-files/case-studies/spectra/minepump/strong.spectra")
        self.assertFalse(spec_strong.is_trivial_true(GR1FormulaType.ASM))
        self.assertFalse(spec_strong.is_trivial_false(GR1FormulaType.ASM))

    def test_minepump_is_trivial_no_initial(self):
        spec_ideal: SpectraSpecification = SpectraSpecification.from_file(
            "../input-files/case-studies/spectra/minepump/ideal.spectra")
        self.assertFalse(spec_ideal.is_trivial_true(GR1FormulaType.ASM, ignore_initial=True))
        self.assertFalse(spec_ideal.is_trivial_false(GR1FormulaType.ASM, ignore_initial=True))

        spec_strong: SpectraSpecification = SpectraSpecification.from_file(
            "../input-files/case-studies/spectra/minepump/strong.spectra")
        self.assertFalse(spec_strong.is_trivial_true(GR1FormulaType.ASM, ignore_initial=True))
        self.assertFalse(spec_strong.is_trivial_false(GR1FormulaType.ASM, ignore_initial=True))

    def test_extract_gr1_expressions_of_type_spot(self):
        spec_ideal: SpectraSpecification = SpectraSpecification.from_file(
            "../input-files/case-studies/spectra/minepump/ideal.spectra")
        spec_strong: SpectraSpecification = SpectraSpecification.from_file(
            "../input-files/case-studies/spectra/minepump/strong.spectra")

        formatter = SpotSpecificationFormatter(GR1FormulaType.ASM)
        spec_ideal_spot: str = spec_ideal.to_formatted_string(formatter)
        self._equiv("!highwater&!methane&G(pump&X(pump)->XX(!highwater))", spec_ideal_spot)
        spec_strong_spot: str = spec_strong.to_formatted_string(formatter)
        self._equiv("!highwater&!methane&G(pump&X(pump)->XX(!highwater))&G(!highwater|!methane)", spec_strong_spot)

        formatter = SpotSpecificationFormatter(GR1FormulaType.GAR)
        spec_ideal_spot: str = spec_ideal.to_formatted_string(formatter)
        self._equiv("!pump&G(highwater&!methane->X(pump))&G(methane->X(!pump))", spec_ideal_spot)
        spec_strong_spot: str = spec_strong.to_formatted_string(formatter)
        self._equiv("!pump&G(highwater->X(pump))&G(methane->X(!pump))", spec_strong_spot)

    def test_extract_gr1_expressions_of_type_spot_no_initial(self):
        spec_ideal: SpectraSpecification = SpectraSpecification.from_file(
            "../input-files/case-studies/spectra/minepump/ideal.spectra")
        spec_strong: SpectraSpecification = SpectraSpecification.from_file(
            "../input-files/case-studies/spectra/minepump/strong.spectra")

        formatter = SpotSpecificationFormatter(GR1FormulaType.ASM, not_initial=True)
        spec_ideal_spot: str = spec_ideal.to_formatted_string(formatter)
        self._equiv("G(pump&X(pump)->XX(!highwater))", spec_ideal_spot)
        spec_strong_spot: str = spec_strong.to_formatted_string(formatter)
        self._equiv("G(pump&X(pump)->XX(!highwater))&G(!highwater|!methane)", spec_strong_spot)

        formatter = SpotSpecificationFormatter(GR1FormulaType.GAR, not_initial=True)
        spec_ideal_spot: str = spec_ideal.to_formatted_string(formatter)
        self._equiv("G(highwater&!methane->X(pump))&G(methane->X(!pump))", spec_ideal_spot)
        spec_strong_spot: str = spec_strong.to_formatted_string(formatter)
        self._equiv("G(highwater->X(pump))&G(methane->X(!pump))", spec_strong_spot)

    def test_weakness_measurement(self):
        spec_ideal: SpectraSpecification = SpectraSpecification.from_file(
            "../input-files/case-studies/spectra/minepump/ideal.spectra")
        spec_strong: SpectraSpecification = SpectraSpecification.from_file(
            "../input-files/case-studies/spectra/minepump/strong.spectra")
        spec_ideal_weakness_asm: Tuple[np.float64, np.float64, int, np.float64] = spec_ideal.get_weakness(GR1FormulaType.ASM)
        print(spec_ideal_weakness_asm)
        spec_strong_weakness_asm: Tuple[np.float64, np.float64, int, np.float64] = spec_strong.get_weakness(GR1FormulaType.ASM)
        print(spec_strong_weakness_asm)
        self.assertLessEqual(spec_strong_weakness_asm, spec_ideal_weakness_asm)

        spec_ideal_weakness_gar: Tuple[np.float64, np.float64, int, np.float64] = spec_ideal.get_weakness(GR1FormulaType.GAR)
        print(spec_ideal_weakness_gar)
        spec_strong_weakness_gar: Tuple[np.float64, np.float64, int, np.float64] = spec_strong.get_weakness(GR1FormulaType.GAR)
        print(spec_strong_weakness_gar)
        self.assertLessEqual(spec_strong_weakness_gar, spec_ideal_weakness_gar)

    def test_eq_identical_strings(self):
        spec_1 = SpectraSpecification.from_str(spec_perf)
        spec_2 = SpectraSpecification.from_str(spec_perf)
        self.assertEqual(spec_1, spec_2)

    def test_eq_1(self):
        spec_1 = SpectraSpecification.from_str(spec_perf)
        spec_2 = SpectraSpecification.from_str(spec_fixed_perf)
        self.assertEqual(spec_1, spec_2)

    def test_neq_1(self):
        spec_1 = SpectraSpecification.from_str(spec_perf)
        spec_2 = SpectraSpecification.from_str(spec_fixed_imperf)
        self.assertNotEquals(spec_1, spec_2)

    def test_neq_2(self):
        spec_1 = SpectraSpecification.from_str(spec_fixed_imperf)
        spec_2 = SpectraSpecification.from_str(spec_fixed_perf)
        self.assertNotEquals(spec_1, spec_2)

    @unittest.skip("To be considered at a later date")
    def test_swap_rule_1(self):
        spec = Spec(copy.deepcopy(spec_strong))
        new_spec = Spec(copy.deepcopy(spec_strong_asm_w))
        spec.swap_rule(
            name="assumption2_1",
            new_rule="G(highwater=false-> highwater=false|methane=false);",
        )
        self.assertEqual(spec, new_spec)

    def test_asm_eq_gar_weaker(self):
        spec_1: SpectraSpecification = SpectraSpecification.from_str(spec_perf)
        spec_2: SpectraSpecification = SpectraSpecification.from_str(spec_asm_eq_gar_weaker)
        self.assertTrue(spec_1.equivalent_to(spec_2, GR1FormulaType.ASM))
        self.assertTrue(spec_1.implies(spec_2, GR1FormulaType.GAR))

    def test_asm_stronger_gar_same(self):
        spec_1 = SpectraSpecification.from_str(spec_perf)
        spec_2 = SpectraSpecification.from_str(spec_asm_stronger_gar_eq)
        self.assertTrue(spec_1.implied_by(spec_2, GR1FormulaType.ASM))
        self.assertTrue(spec_1.equivalent_to(spec_2, GR1FormulaType.GAR))
