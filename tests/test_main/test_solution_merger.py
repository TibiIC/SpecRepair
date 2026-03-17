import os

import spot

from main.solution_merger import RepairBro
from spec_repair.components.interfaces.ispecification import ISpecification
from spec_repair.components.oracles.spectra_gr1_oracle import SpectraGR1Oracle
from spec_repair.helpers.formatters.spectra_formula_formatter import SpectraFormulaFormatter
from spec_repair.helpers.formatters.spot_specification_formatter import SpotSpecificationFormatter
from spec_repair.helpers.parsers.spectra_formula_parser import SpectraFormulaParser
from spec_repair.helpers.spectra_specification import SpectraSpecification, Self
from spec_repair.ltl_types import GR1FormulaType
from tests.base_test_case import BaseTestCase
from datetime import datetime


def _create_minepump_test(i, j):
    def test_method(self):
        case_study_name = f'minepump_{i}_{j}'
        input_specs_path = 'test_files/maximal_solutions_from_ssh'
        spec_1 = SpectraSpecification.from_file(f"{input_specs_path}/minepump_{i}.spectra")
        spec_2 = SpectraSpecification.from_file(f"{input_specs_path}/minepump_{j}.spectra")
        case_study_path = '../input-files/case-studies/spectra/minepump'
        new_specs = self.run_merge_two(
            case_study_name,
            case_study_path,
            spec_1,
            spec_2,
            is_debug=True
        )
        expected_dir = f"test_files/expected/merge_two/minepump/{i}+{j}/"
        expected_specs = [SpectraSpecification.from_file(os.path.join(expected_dir, file_name))
                          for file_name in os.listdir(expected_dir) if file_name.endswith('.spectra')]
        self.are_specification_sets_equivalent(expected_specs, new_specs)

    return test_method


class TestRepairBro(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.date_str = datetime.now().strftime("%Y-%m-%d")
        cls.maxDiff = None
        cls.parser = SpectraFormulaParser()
        cls.formatter = SpectraFormulaFormatter()
        cls.spot_formatter_asm = SpotSpecificationFormatter(GR1FormulaType.ASM)
        cls.spot_formatter_gar = SpotSpecificationFormatter(GR1FormulaType.GAR)
        # Some template spec for method testing
        cls.spec = SpectraSpecification.from_file("./test_files/minepump_strong.spectra")

    def test_merge_two_solutions_arbiter_0_1(self):
        case_study_name = 'arbiter_0_1'
        input_specs_path = 'test_files/maximal_solutions_from_ssh'
        spec_1 = SpectraSpecification.from_file(f"{input_specs_path}/arbiter_0.spectra")
        spec_2 = SpectraSpecification.from_file(f"{input_specs_path}/arbiter_1.spectra")
        case_study_path = '../input-files/case-studies/spectra/arbiter'
        new_specs = self.run_merge_two(
            case_study_name,
            case_study_path,
            spec_1,
            spec_2,
            is_debug=True
        )
        expected_dir = "test_files/expected/merge_two/arbiter/0+1/"
        expected_specs = [SpectraSpecification.from_file(os.path.join(expected_dir, file_name))
                          for file_name in os.listdir(expected_dir) if file_name.endswith('.spectra')]
        self.are_specification_sets_equivalent(expected_specs, new_specs)

    def test_merge_two_solutions_arbiter_1_2(self):
        case_study_name = 'arbiter_1_2'
        input_specs_path = 'test_files/maximal_solutions_from_ssh'
        spec_1 = SpectraSpecification.from_file(f"{input_specs_path}/arbiter_1.spectra")
        spec_2 = SpectraSpecification.from_file(f"{input_specs_path}/arbiter_2.spectra")
        case_study_path = '../input-files/case-studies/spectra/arbiter'

        new_specs = self.run_merge_two(
            case_study_name,
            case_study_path,
            spec_1,
            spec_2,
            is_debug=True
        )
        expected_dir = "test_files/expected/merge_two/arbiter/1+2/"
        expected_specs = [SpectraSpecification.from_file(os.path.join(expected_dir, file_name))
                          for file_name in os.listdir(expected_dir) if file_name.endswith('.spectra')]
        self.are_specification_sets_equivalent(expected_specs, new_specs)

    def test_merge_two_solutions_arbiter_1_3(self):
        case_study_name = 'arbiter_1_3'
        input_specs_path = 'test_files/maximal_solutions_from_ssh'
        spec_1 = SpectraSpecification.from_file(f"{input_specs_path}/arbiter_1.spectra")
        spec_2 = SpectraSpecification.from_file(f"{input_specs_path}/arbiter_3.spectra")
        case_study_path = '../input-files/case-studies/spectra/arbiter'
        new_specs = self.run_merge_two(
            case_study_name,
            case_study_path,
            spec_1,
            spec_2,
            is_debug=True
        )
        expected_dir = "test_files/expected/merge_two/arbiter/1+3/"
        expected_specs = [SpectraSpecification.from_file(os.path.join(expected_dir, file_name))
                          for file_name in os.listdir(expected_dir) if file_name.endswith('.spectra')]
        self.are_specification_sets_equivalent(expected_specs, new_specs)

    def test_merge_two_solutions_lift_0_1(self):
        case_study_name = 'lift_0_1'
        input_specs_path = 'test_files/maximal_solutions_from_ssh'
        spec_1 = SpectraSpecification.from_file(f"{input_specs_path}/lift_0.spectra")
        spec_2 = SpectraSpecification.from_file(f"{input_specs_path}/lift_1.spectra")
        case_study_path = '../input-files/case-studies/spectra/lift'
        new_specs = self.run_merge_two(
            case_study_name,
            case_study_path,
            spec_1,
            spec_2,
            is_debug=True
        )
        expected_dir = "test_files/expected/merge_two/lift/0+1/"
        expected_specs = [SpectraSpecification.from_file(os.path.join(expected_dir, file_name))
                          for file_name in os.listdir(expected_dir) if file_name.endswith('.spectra')]
        self.are_specification_sets_equivalent(expected_specs, new_specs)

    def run_merge_two(self, case_study_name, case_study_path, spec1, spec2, out_test_dir_name=None, is_debug=False):
        if not out_test_dir_name:
            out_test_dir_name = f"./test_files/out/merge_two/{case_study_name}_{self.date_str}"
        log_file = f"{out_test_dir_name}/log.txt"
        if not os.path.exists(out_test_dir_name):
            os.mkdir(out_test_dir_name)
        original_spec = SpectraSpecification.from_file(f"{case_study_path}/strong.spectra")
        repair_bro = RepairBro(original_spec=original_spec, oracle=SpectraGR1Oracle())
        new_specs = repair_bro.merge_two_solutions(spec1, spec2)
        return new_specs

    def are_specification_sets_equivalent(self, expected_specs: list[SpectraSpecification], new_specs: list[ISpecification]):
        self.assertEqual(len(expected_specs), len(new_specs))
        for new_spec in new_specs:
            self.assertTrue(self._has_equivalent_in_list(new_spec, expected_specs),
                            f"New spec not found in expected_specs")

    def _has_equivalent_in_list(self, spec: SpectraSpecification, spec_list: list[SpectraSpecification]) -> bool:
        for spec_candidate in spec_list:
            if (spec.equivalent_to(spec_candidate, GR1FormulaType.ASM) and
                    spec.equivalent_to(spec_candidate, GR1FormulaType.GAR)):
                return True
        return False


# Generate individual test methods for all minepump combinations
for i in range(0, 6):
    for j in range(i+1, 7):
        test_name = f'test_merge_two_solutions_minepump_{i}_{j}'
        test_method = _create_minepump_test(i, j)
        setattr(TestRepairBro, test_name, test_method)

