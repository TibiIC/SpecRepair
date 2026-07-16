import os
import unittest

from spec_repair.components.oracles.spectra_gr1_oracle import SpectraGR1Oracle
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.ltl_types import GR1FormulaType
from spec_repair.diagnosis.trivial_solution import get_trivial_solution, get_all_trivial_solution, \
    get_all_trivial_solutions_guarantee_only
from spec_repair.util.file_util import read_file_lines, write_to_file
from tests.base_test_case import BaseTestCase


class TestTrivialSolution(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.merged_spec_file = 'test_files/edge_cases/unrealisable_merged_spec.spectra'
        cls.sanity_merged_minepump = 'test_files/edge_cases/sanity_merged_minepump.spectra'
        cls.sanity_merged_minepump_2 = 'test_files/edge_cases/sanity_merged_minepump_2.spectra'

    def test_get_trivial_solution_minepump(self):
        dir = '../input-files/case-studies/spectra/minepump'
        trivial_spec = self.get_trivial_spec(dir)
        write_to_file('test_files/out/trivial_solutions/minepump.spectra', trivial_spec.to_str())

    def test_get_trivial_solution_arbiter(self):
        dir = '../input-files/case-studies/spectra/arbiter'
        trivial_spec = self.get_trivial_spec(dir)
        write_to_file('test_files/out/trivial_solutions/arbiter.spectra', trivial_spec.to_str())

    def test_get_trivial_solution_lift(self):
        dir = '../input-files/case-studies/spectra/lift'
        trivial_spec = self.get_trivial_spec(dir)
        write_to_file('test_files/out/trivial_solutions/lift.spectra', trivial_spec.to_str())

    def test_get_trivial_solution_traffic_single(self):
        dir = '../input-files/case-studies/spectra/traffic_single'
        trivial_spec = self.get_trivial_spec(dir)
        write_to_file('test_files/out/trivial_solutions/traffic_single.spectra', trivial_spec.to_str())

    def test_get_trivial_solution_traffic_updated(self):
        dir = '../input-files/case-studies/spectra/traffic_updated'
        trivial_spec = self.get_trivial_spec(dir)
        write_to_file('test_files/out/trivial_solutions/traffic_updated.spectra', trivial_spec.to_str())

    def test_get_all_trivial_solution_minepump(self):
        dir = '../input-files/case-studies/spectra/minepump'
        trivial_specs = self.get_all_trivial_specs(dir)
        for i, trivial_spec in enumerate(trivial_specs):
            write_to_file(f'test_files/out/trivial_solutions/minepump_{i}.spectra', trivial_spec.to_str())

    def test_get_all_trivial_solution_arbiter(self):
        dir = '../input-files/case-studies/spectra/arbiter'
        trivial_specs = self.get_all_trivial_specs(dir)
        for i, trivial_spec in enumerate(trivial_specs):
            write_to_file(f'test_files/out/trivial_solutions/arbiter_{i}.spectra', trivial_spec.to_str())

    def test_get_all_trivial_solution_lift(self):
        dir = '../input-files/case-studies/spectra/lift'
        trivial_specs = self.get_all_trivial_specs(dir)
        for i, trivial_spec in enumerate(trivial_specs):
            write_to_file(f'test_files/out/trivial_solutions/lift_{i}.spectra', trivial_spec.to_str())

    def test_get_all_trivial_solution_traffic_single(self):
        dir = '../input-files/case-studies/spectra/traffic_single'
        trivial_specs = self.get_all_trivial_specs(dir)
        for i, trivial_spec in enumerate(trivial_specs):
            write_to_file(f'test_files/out/trivial_solutions/traffic_single_{i}.spectra', trivial_spec.to_str())

    def test_get_all_trivial_solution_traffic_updated(self):
        dir = '../input-files/case-studies/spectra/traffic_updated'
        trivial_specs = self.get_all_trivial_specs(dir)
        for i, trivial_spec in enumerate(trivial_specs):
            write_to_file(f'test_files/out/trivial_solutions/traffic_updated_{i}.spectra', trivial_spec.to_str())

    @unittest.skip("Cannot find violation trace file anymore, spec may be unrealisable anyway.")
    def test_weird_case_study(self):
        dir = '../input-files/case-studies/spectra/weird_uc'
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
