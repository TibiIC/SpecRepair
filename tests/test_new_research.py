from unittest import TestCase

from spec_repair.helpers.spectra_boolean_specification import SpectraBooleanSpecification
from spec_repair.new_research import get_trivial_solution, get_all_trivial_solution
from spec_repair.util.file_util import read_file_lines, write_to_file


class TestNewResearch(TestCase):
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
        dir = '../input-files/case-studies/spectra/traffic-single'
        trivial_spec = self.get_trivial_spec(dir)
        write_to_file('test_files/out/trivial_solutions/traffic-single.spectra', trivial_spec.to_str())

    def test_get_trivial_solution_traffic_updated(self):
        dir = '../input-files/case-studies/spectra/traffic-updated'
        trivial_spec = self.get_trivial_spec(dir)
        write_to_file('test_files/out/trivial_solutions/traffic-updated.spectra', trivial_spec.to_str())

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
        dir = '../input-files/case-studies/spectra/traffic-single'
        trivial_specs = self.get_all_trivial_specs(dir)
        for i, trivial_spec in enumerate(trivial_specs):
            write_to_file(f'test_files/out/trivial_solutions/traffic-single_{i}.spectra', trivial_spec.to_str())

    def test_get_all_trivial_solution_traffic_updated(self):
        dir = '../input-files/case-studies/spectra/traffic-updated'
        trivial_specs = self.get_all_trivial_specs(dir)
        for i, trivial_spec in enumerate(trivial_specs):
            write_to_file(f'test_files/out/trivial_solutions/traffic-updated_{i}.spectra', trivial_spec.to_str())

    def get_trivial_spec(self, dir):
        spec = SpectraBooleanSpecification.from_file(
            f'{dir}/strong.spectra'
        )
        trace: list[str] = read_file_lines(
            f'{dir}/violation_trace.txt'
        )
        trivial_spec = get_trivial_solution(spec, trace)
        return trivial_spec

    def get_all_trivial_specs(self, dir):
        spec = SpectraBooleanSpecification.from_file(
            f'{dir}/strong.spectra'
        )
        trace: list[str] = read_file_lines(
            f'{dir}/violation_trace.txt'
        )
        trivial_specs = get_all_trivial_solution(spec, trace)
        return trivial_specs
