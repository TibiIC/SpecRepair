import unittest
from copy import deepcopy
from typing import Tuple

from spec_repair.components.repair_data import RepairData
from spec_repair.helpers.counter_strategy import CounterStrategy
from spec_repair.helpers.parsers.spectra_cs_parser import SpectraCSParser
from tests.base_test_case import BaseTestCase
from spec_repair.components.mitigators.learning_type_spec_mitigator import LearningTypeSpecMitigator
from spec_repair.enums import Learning
from spec_repair.helpers.counter_trace import cts_from_cs, CounterTrace
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.strategies.mitigation_strategies import move_one_to_guarantee_weakening, complete_counter_traces


class TestSpecMittigator(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Set up the mitigator
        cls.mitigator = LearningTypeSpecMitigator({
            Learning.ASSUMPTION_WEAKENING: move_one_to_guarantee_weakening,
            Learning.GUARANTEE_WEAKENING: complete_counter_traces
        })

    def test_mitigate_assumption_learning(self):
        spec = SpectraSpecification.from_file("./test_files/minepump_aw_pump.spectra")
        trace = [
            'not_holds_at(highwater,0,trace_name_0).\n',
            'not_holds_at(methane,0,trace_name_0).\n',
            'not_holds_at(pump,0,trace_name_0).\n',
            '\n',
            'holds_at(highwater,1,trace_name_0).\n',
            'holds_at(methane,1,trace_name_0).\n',
            'not_holds_at(pump,1,trace_name_0).\n',
            '\n'
        ]
        cs: CounterStrategy = SpectraCSParser.from_lines(
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> S1 {highwater:false, methane:true} / {pump:false};',
             'S0 -> S1 {highwater:false, methane:true} / {pump:true};',
             'S1 -> DEAD {highwater:true, methane:true} / {pump:false};']
        )
        cts = [cts_from_cs(cs, 0)[0]]
        learning_type = Learning.ASSUMPTION_WEAKENING
        data = RepairData(trace, counter_traces=cts, learning_type=learning_type, spec_history=[deepcopy(spec)])
        new_learning_tasks = self.mitigator.prepare_alternative_learning_tasks(spec, data)
        new_ctss = set()
        for new_learning_task in new_learning_tasks:
            new_spec, new_data = new_learning_task
            self.assertIsInstance(new_spec, SpectraSpecification)
            self.assertEqual(new_spec.to_str(), spec.to_str())
            self.assertIsInstance(new_data, RepairData)
            self.assertEqual(new_data.trace, trace)
            self.assertEqual(new_data.learning_type, Learning.GUARANTEE_WEAKENING)
            self.assertEqual(len(new_data.counter_traces), 1)
            self.assertIsInstance(new_data.counter_traces[0], CounterTrace)
            new_ctss.add(new_data.counter_traces[0])
        expected_ctss = {
            'CT(!highwater,!methane,!pump;!highwater,methane,pump;highwater,methane,!pump)',
        }
        for new_cts in new_ctss:
            self.assertIn(new_cts.print_one_line(), expected_ctss)
            expected_ctss.remove(new_cts.print_one_line())
            self.assertEqual(new_cts.get_name(), "counter_strat_0_0")
            self.assertEqual(new_cts.is_deadlock(), True)
        self.assertEqual(len(expected_ctss), 0)

    def test_mitigate_guarantee_learning_complete_deadlocks(self):
        spec = SpectraSpecification.from_file("./test_files/minepump_aw_pump.spectra")
        trace = [
            'not_holds_at(highwater,0,trace_name_0).\n',
            'not_holds_at(methane,0,trace_name_0).\n',
            'not_holds_at(pump,0,trace_name_0).\n',
            '\n',
            'holds_at(highwater,1,trace_name_0).\n',
            'holds_at(methane,1,trace_name_0).\n',
            'not_holds_at(pump,1,trace_name_0).\n',
            '\n'
        ]
        cs: CounterStrategy = SpectraCSParser.from_lines(
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> S1 {highwater:false, methane:true} / {pump:false};',
             'S0 -> S1 {highwater:false, methane:true} / {pump:true};',
             'S1 -> DEAD {highwater:true, methane:true} / {pump:false};']
        )
        cts = [cts_from_cs(cs, 0)[0]]
        learning_type = Learning.GUARANTEE_WEAKENING
        data = RepairData(trace, counter_traces=cts, learning_type=learning_type)
        new_learning_tasks = self.mitigator.prepare_alternative_learning_tasks(spec, data)
        new_ctss = set()
        for new_learning_task in new_learning_tasks:
            new_spec, new_data = new_learning_task
            self.assertIsInstance(new_spec, SpectraSpecification)
            self.assertEqual(new_spec.to_str(), spec.to_str())
            self.assertIsInstance(new_data, RepairData)
            self.assertEqual(new_data.trace, trace)
            self.assertEqual(new_data.learning_type, Learning.GUARANTEE_WEAKENING)
            self.assertEqual(len(new_data.counter_traces), 1)
            self.assertIsInstance(new_data.counter_traces[0], CounterTrace)
            new_ctss.add(new_data.counter_traces[0])
        expected_ctss = {
            'CT(!highwater,!methane,!pump;!highwater,methane,pump;highwater,methane,!pump;highwater,methane,pump)',
            'CT(!highwater,!methane,!pump;!highwater,methane,pump;highwater,methane,!pump;highwater,methane,!pump)',
            'CT(!highwater,!methane,!pump;!highwater,methane,pump;highwater,methane,!pump;highwater,!methane,!pump)',
            'CT(!highwater,!methane,!pump;!highwater,methane,pump;highwater,methane,!pump;highwater,!methane,pump)',
            'CT(!highwater,!methane,!pump;!highwater,methane,pump;highwater,methane,!pump;!highwater,methane,pump)',
            'CT(!highwater,!methane,!pump;!highwater,methane,pump;highwater,methane,!pump;!highwater,methane,!pump)',
            'CT(!highwater,!methane,!pump;!highwater,methane,pump;highwater,methane,!pump;!highwater,!methane,!pump)',
            'CT(!highwater,!methane,!pump;!highwater,methane,pump;highwater,methane,!pump;!highwater,!methane,pump)'
        }
        self.assertEqual(len(new_ctss), 8)
        for new_cts in new_ctss:
            self.assertIn(new_cts.print_one_line(), expected_ctss)
            expected_ctss.remove(new_cts.print_one_line())
            self.assertEqual(new_cts.get_name(), "counter_strat_0_0")
            self.assertEqual(new_cts.is_deadlock(), False)
        self.assertEqual(len(expected_ctss), 0)


if __name__ == "__main__":
    unittest.main()
