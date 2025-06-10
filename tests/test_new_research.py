from unittest import TestCase

from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.new_research import get_trivial_solution
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

    def get_trivial_spec(self, dir):
        spec = SpectraSpecification.from_file(
            f'{dir}/strong.spectra'
        )
        trace: list[str] = read_file_lines(
            f'{dir}/violation_trace.txt'
        )
        trivial_spec = get_trivial_solution(spec, trace)
        return trivial_spec
