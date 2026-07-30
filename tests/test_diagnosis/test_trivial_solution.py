import os
import unittest
from datetime import datetime

from spec_repair.components.oracles.spectra_gr1_oracle import SpectraGR1Oracle
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.ltl_types import GR1FormulaType
from spec_repair.diagnosis.trivial_solution import get_trivial_solution, get_all_trivial_solution, \
    get_all_trivial_solutions_guarantee_only
from spec_repair.util.file_util import read_file_lines, write_to_file
from tests.base_test_case import BaseTestCase

CASE_STUDIES_DIR = '../input-files/case-studies/spectra/strengthened'

# Output roots. Runs are stamped with the date they were generated, so a rerun
# never silently overwrites an earlier day's solutions and a graph can be built
# against the exact set that a given experiment used:
#   test_files/out/trivial_solutions/<date>/all/<case_study>/spec_<i>.spectra
#   test_files/out/trivial_solutions/<date>/single/<case_study>.spectra
# "all" gets a folder per case study specifically so it can be handed straight
# to visualise_resulting_specs.py as `--group trivial=<that folder>`.
TRIVIAL_SOLUTIONS_ROOT = 'test_files/out/trivial_solutions'

# Every case study with both a strong.spectra and a violation_trace.txt. The
# *_updated variants strengthen at least one assumption AND one guarantee,
# unlike the originals which are all assumption-only.
TRIVIAL_SOLUTION_CASE_STUDIES = [
    'arbiter',
    'colorsort',
    'colorsort_updated',
    'elevator',
    'elevator_updated',
    'gyro',
    'gyro_updated',
    'humanoid',
    'humanoid_updated',
    'lift',
    'lift_updated',
    'minepump',
    'minepump_liveness',
    'pcar',
    'pcar_updated',
    'traffic_single',
    'traffic_updated',
    'traffic_updated_updated',
]


class TestTrivialSolution(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.date_str = datetime.now().strftime("%Y-%m-%d")
        cls.merged_spec_file = 'test_files/edge_cases/unrealisable_merged_spec.spectra'
        cls.sanity_merged_minepump = 'test_files/edge_cases/sanity_merged_minepump.spectra'
        cls.sanity_merged_minepump_2 = 'test_files/edge_cases/sanity_merged_minepump_2.spectra'

    def all_trivial_solutions_dir(self, case_study_name: str) -> str:
        return f'{TRIVIAL_SOLUTIONS_ROOT}/{self.date_str}/all/{case_study_name}'

    def single_trivial_solution_path(self, case_study_name: str) -> str:
        return f'{TRIVIAL_SOLUTIONS_ROOT}/{self.date_str}/single/{case_study_name}.spectra'

    # Per-case-study tests are generated at the bottom of this file rather than
    # hand-written, so adding a case study is a one-line change to
    # TRIVIAL_SOLUTION_CASE_STUDIES instead of two more copy-pasted methods.

    @unittest.skip("Cannot find violation trace file anymore, spec may be unrealisable anyway.")
    def test_weird_case_study(self):
        dir = '../input-files/case-studies/spectra/strengthened/weird_uc'
        trivial_specs = self.get_all_trivial_specs(dir)
        for i, trivial_spec in enumerate(trivial_specs):
            write_to_file(f'test_files/out/trivial_solutions/weird_uc_{i}.spectra', trivial_spec.to_str())

    def test_edge_case_get_all_trivial_solutions_guarantee_only(self):
        merged_spec = SpectraSpecification.from_file(self.merged_spec_file)
        new_merged_specs = get_all_trivial_solutions_guarantee_only(merged_spec)
        oracle = SpectraGR1Oracle()
        for new_merged_spec in new_merged_specs:
            self.assertTrue(oracle.is_realisable(new_merged_spec))

    @unittest.skip("Takes too long")
    def test_edge_case_get_all_trivial_solutions_guarantee_only_2(self):
        merged_spec = SpectraSpecification.from_file(self.sanity_merged_minepump)
        new_merged_specs = get_all_trivial_solutions_guarantee_only(merged_spec)
        oracle = SpectraGR1Oracle()
        for new_merged_spec in new_merged_specs:
            self.assertTrue(oracle.is_realisable(new_merged_spec))

    @unittest.skip("Takes too long")
    def test_edge_case_get_all_trivial_solutions_guarantee_only_3(self):
        merged_spec = SpectraSpecification.from_file(self.sanity_merged_minepump_2)
        new_merged_specs = get_all_trivial_solutions_guarantee_only(merged_spec)
        oracle = SpectraGR1Oracle()
        for new_merged_spec in new_merged_specs:
            self.assertTrue(oracle.is_realisable(new_merged_spec))

    @unittest.skip("Takes too long")
    def test_edge_case_get_all_trivial_solutions_guarantee_only_bad_split(self):
        merged_spec = SpectraSpecification.from_file(self.sanity_merged_minepump_2)
        new_merged_specs = get_all_trivial_solutions_guarantee_only(merged_spec)
        oracle = SpectraGR1Oracle()
        pre_merge_spec_1 = SpectraSpecification.from_file(self.spec_1)
        pre_merge_spec_2 = SpectraSpecification.from_file(self.spec_2)
        for new_merged_spec in new_merged_specs:
            self.assertTrue(oracle.is_realisable(new_merged_spec))
            self.assertTrue(pre_merge_spec_1.implies(new_merged_spec, GR1FormulaType.ASM) or pre_merge_spec_2.implies(new_merged_spec, GR1FormulaType.ASM))

    def get_trivial_spec(self, dir):
        spec = SpectraSpecification.from_file(
            f'{dir}/strong.spectra'
        )
        trace: list[str] = read_file_lines(
            f'{dir}/violation_trace.txt'
        )
        trivial_spec = get_trivial_solution(spec, trace)
        return trivial_spec

    def get_all_trivial_specs(self, dir):
        print(f"Current working directory: {os.getcwd()}")

        spec = SpectraSpecification.from_file(
            f'{dir}/strong.spectra'
        )
        trace: list[str] = read_file_lines(
            f'{dir}/violation_trace.txt'
        )
        trivial_specs = get_all_trivial_solution(spec, trace)
        return trivial_specs


def _make_single_trivial_solution_test(case_study_name: str):
    def test_method(self):
        case_study_dir = f'{CASE_STUDIES_DIR}/{case_study_name}'
        trivial_spec = self.get_trivial_spec(case_study_dir)
        write_to_file(self.single_trivial_solution_path(case_study_name), trivial_spec.to_str())

    test_method.__name__ = f'test_get_trivial_solution_{case_study_name}'
    return test_method


def _make_all_trivial_solutions_test(case_study_name: str):
    def test_method(self):
        case_study_dir = f'{CASE_STUDIES_DIR}/{case_study_name}'
        trivial_specs = self.get_all_trivial_specs(case_study_dir)
        self.assertGreater(len(trivial_specs), 0,
                           f"expected at least one trivial solution for {case_study_name}")
        out_dir = self.all_trivial_solutions_dir(case_study_name)
        os.makedirs(out_dir, exist_ok=True)
        for i, trivial_spec in enumerate(trivial_specs):
            write_to_file(f'{out_dir}/spec_{i}.spectra', trivial_spec.to_str())
        print(f"Wrote {len(trivial_specs)} trivial solution(s) for {case_study_name} to {out_dir}")

    test_method.__name__ = f'test_get_all_trivial_solution_{case_study_name}'
    return test_method


# Attach one pair of tests per case study, so each can still be run on its own
# by name (e.g. -k test_get_all_trivial_solution_pcar_updated) exactly as the
# hand-written ones could.
for _case_study in TRIVIAL_SOLUTION_CASE_STUDIES:
    for _factory in (_make_single_trivial_solution_test, _make_all_trivial_solutions_test):
        _test = _factory(_case_study)
        setattr(TestTrivialSolution, _test.__name__, _test)
del _case_study, _factory, _test
