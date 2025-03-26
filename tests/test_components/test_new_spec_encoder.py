from unittest import TestCase

from spec_repair.components.new_spec_encoder import NewSpecEncoder
from spec_repair.enums import Learning
from spec_repair.helpers.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import read_file


class TestSpecEncoder(TestCase):
    minepump_spec_file = '../../input-files/examples/Minepump/minepump_strong.spectra'
    minepump_spec_1_aw_step = '../test_files/minepump_aw_methane.spectra'
    minepump_clingo_file = '../test_files/test_components/minepump_strong_WA_no_cs.lp'
    minepump_mode_bias_aw_file = '../test_files/mode_bias/minepump_1_aw_step.txt'
    minepump_mode_bias_gw_file = '../test_files/mode_bias/minepump_1_gw_step.txt'
    traffic_updated_spec_file = '../../input-files/case-studies/spectra/traffic-updated/strong.spectra'
    traffic_updated_mode_bias_aw_file = '../test_files/mode_bias/traffic_updated_aw.txt'
    traffic_updated_mode_bias_aw_file_no_ev = '../test_files/mode_bias/traffic_updated_aw_no_ev.txt'
    maxDiff = None

    def __init__(self, methodName: str = "runTest"):
        super().__init__(methodName)

    def test_encode_asp(self):
        spec: SpectraSpecification = SpectraSpecification.from_file(self.minepump_spec_file)
        trace_name = "trace_name_0"
        trace = [
            f'not_holds_at(highwater,0,{trace_name}).\n',
            f'not_holds_at(methane,0,{trace_name}).\n',
            f'not_holds_at(pump,0,{trace_name}).\n',
            '\n',
            f'holds_at(highwater,1,{trace_name}).\n',
            f'holds_at(methane,1,{trace_name}).\n',
            f'not_holds_at(pump,1,{trace_name}).\n',
            '\n'
        ]
        encoder: NewSpecEncoder = NewSpecEncoder(NoFilterHeuristicManager())
        clingo_str: str = encoder.encode_ASP(spec, trace, set())

        expected_clingo_str: str = read_file(self.minepump_clingo_file)
        self.assertEqual(expected_clingo_str, clingo_str)

    def test_create_mode_bias_aw(self):
        spec: SpectraSpecification = SpectraSpecification.from_file(self.minepump_spec_file)
        violations: list[str] = [
            """\
    assumption(initial_assumption)
    assumption(assumption1_1)
    assumption(assumption2_1)
    guarantee(initial_guarantee)
    guarantee(guarantee1_1)
    guarantee(guarantee2_1)
    violation_holds(assumption2_1,1,trace_name_0)
    violation_holds(guarantee1_1,1,trace_name_0)\
    """
        ]
        encoder: NewSpecEncoder = NewSpecEncoder(NoFilterHeuristicManager())
        mode_bias: str = encoder._create_mode_bias(spec, violations, Learning.ASSUMPTION_WEAKENING)

        expected_mode_bias: str = read_file(self.minepump_mode_bias_aw_file)
        self.assertEqual(expected_mode_bias, mode_bias)

