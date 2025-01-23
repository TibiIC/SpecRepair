import os
from unittest import TestCase

from spec_repair.helpers.spectra_formula import SpectraFormula
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import read_file_lines
from spec_repair.util.spec_util import format_spec


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
        spec_txt: str = "".join(format_spec(read_file_lines(spec_file)))
        # spec = SpectraSpecification.from_file(spec_file)
        spec = SpectraSpecification(spec_txt)
        # get all entries at column "formula" in the DataFrame
        formulas = spec.formulas_df["formula"]
        expected_formulas: set[str] = {
            SpectraFormula.from_str("\thighwater=false&methane=false;").to_str(),
            SpectraFormula.from_str("\tpump=false;").to_str(),
            SpectraFormula.from_str("G(highwater=true->next(pump=true));").to_str(),
            SpectraFormula.from_str("G(methane=true->next(pump=false));").to_str(),
            SpectraFormula.from_str("G(PREV(pump=true)&pump=true->next(highwater=false));").to_str(),
            SpectraFormula.from_str("G(highwater=false|methane=false)").to_str(),
        }
        for formula in formulas:
            self.assertIn(formula.to_str(), expected_formulas)
