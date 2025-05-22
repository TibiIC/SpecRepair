import os
from typing import Tuple
from unittest import TestCase

from spec_repair.components.spec_mitigator import SpecMitigator
from spec_repair.enums import Learning
from spec_repair.helpers.counter_trace import cts_from_cs, CounterTrace
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.ltl_types import CounterStrategy


class TestSpecMittigator(TestCase):
    @classmethod
    def setUpClass(cls):
        # Change the working directory to the script's directory
        cls.original_working_directory = os.getcwd()
        test_components_dir = os.path.dirname(os.path.abspath(__file__))
        tests_dir = os.path.dirname(test_components_dir)
        os.chdir(tests_dir)
        # Set up the mittigator
        cls.mittigator = SpecMitigator()

    @classmethod
    def tearDownClass(cls):
        # Restore the original working directory
        os.chdir(cls.original_working_directory)

    def test_expand_deadlocks(self):
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
        cs: CounterStrategy = \
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> S1 {highwater:false, methane:true} / {pump:false};',
             'S0 -> S1 {highwater:false, methane:true} / {pump:true};',
             'S1 -> DEAD {highwater:true, methane:true} / {pump:false};']
        cts = [cts_from_cs(cs, 0)[0]]
        learning_type = Learning.ASSUMPTION_WEAKENING
        data = (trace, cts, learning_type)
        new_learning_tasks = self.mittigator.prepare_alternative_learning_tasks(spec, data)
        new_ctss = set()
        for new_learning_task in new_learning_tasks:
            new_spec, new_data = new_learning_task
            self.assertIsInstance(new_spec, SpectraSpecification)
            self.assertEqual(new_spec.to_str(), spec.to_str())
            self.assertIsInstance(new_data, Tuple)
            self.assertEqual(len(new_data), 3)
            new_trace, new_cts, new_learning_type = new_data
            self.assertEqual(new_trace, trace)
            self.assertEqual(new_learning_type, Learning.GUARANTEE_WEAKENING)
            self.assertEqual(len(new_cts), 1)
            self.assertIsInstance(new_cts[0], CounterTrace)
            new_ctss.add(new_cts[0])
        expected_ctss = {
           'CT(!highwater,!methane,!pump;!highwater,methane,pump;highwater,methane,!pump;!highwater,methane,pump)',
           'CT(!highwater,!methane,!pump;!highwater,methane,pump;highwater,methane,!pump;!highwater,methane,!pump)',
           'CT(!highwater,!methane,!pump;!highwater,methane,pump;highwater,methane,!pump;!highwater,!methane,!pump)',
           'CT(!highwater,!methane,!pump;!highwater,methane,pump;highwater,methane,!pump;!highwater,!methane,pump)'
        }
        for new_cts in new_ctss:
            self.assertIn(new_cts.print_one_line(), expected_ctss)
            expected_ctss.remove(new_cts.print_one_line())
            self.assertEqual(new_cts.get_name(), "counter_strat_0_0")
            self.assertEqual(new_cts.is_deadlock(), False)
        self.assertEqual(len(expected_ctss), 0)