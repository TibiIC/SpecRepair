import os
from unittest import TestCase

from spec_repair.helpers.adaptation_learned import Adaptation
from spec_repair.helpers.gr1_formula import GR1Formula
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.helpers.spectra_atom import SpectraAtom


class TestSpectraSpecification(TestCase):
    @classmethod
    def setUpClass(cls):
        # Change the working directory to the script's directory
        cls.original_working_directory = os.getcwd()
        test_components_dir = os.path.dirname(os.path.abspath(__file__))
        tests_dir = os.path.dirname(test_components_dir)
        os.chdir(tests_dir)

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
            GR1Formula.from_str("\thighwater=false&methane=false;").to_str(),
            GR1Formula.from_str("\tpump=false;").to_str(),
            GR1Formula.from_str("G(highwater=true->next(pump=true));").to_str(),
            GR1Formula.from_str("G(methane=true->next(pump=false));").to_str(),
            GR1Formula.from_str("G(PREV(pump=true)&pump=true->next(highwater=false));").to_str(),
            GR1Formula.from_str("G(highwater=false|methane=false)").to_str(),
        }
        for formula in formulas:
            self.assertIn(formula.to_str(), expected_formulas)

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
            GR1Formula.from_str("\thighwater=false&methane=false;").to_str(),
            GR1Formula.from_str("\tpump=false;").to_str(),
            GR1Formula.from_str("G(highwater=true->next(pump=true));").to_str(),
            GR1Formula.from_str("G(methane=true->next(pump=false));").to_str(),
            GR1Formula.from_str("G(PREV(pump=true)&pump=true->next(highwater=false));").to_str(),
            GR1Formula.from_str("G(methane=false->highwater=false|methane=false)").to_str(),
        }
        for formula in formulas:
            self.assertIn(formula.to_str(), expected_formulas)


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
            GR1Formula.from_str("\thighwater=false&methane=false;").to_str(),
            GR1Formula.from_str("\tpump=false;").to_str(),
            GR1Formula.from_str("G(highwater=true->pump=true|next(pump=true));").to_str(),
            GR1Formula.from_str("G(methane=true->pump=false|next(pump=false));").to_str(),
            GR1Formula.from_str("G(PREV(pump=true)&pump=true->next(highwater=false));").to_str(),
            GR1Formula.from_str("G(methane=false->highwater=false|methane=false)").to_str(),
        }
        for formula in formulas:
            self.assertIn(formula.to_str(), expected_formulas)

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
