import os
from typing import List, Set
from unittest import TestCase

from spec_repair.components.counter_trace import CounterTrace
from spec_repair.components.spec_learner import SpecLearner
from spec_repair.enums import Learning
from spec_repair.exceptions import NoWeakeningException
from spec_repair.heuristics import T, random_choice, first_choice, manual_choice, last_choice
from spec_repair.ltl import CounterStrategy
from spec_repair.util.file_util import read_file_lines
from spec_repair.util.spec_util import format_spec, create_cs_traces


def methane_choice_asm(options_list: List[T]) -> T:
    options_list.sort()
    assert len(options_list) == 4
    return options_list[1]


def methane_choice_gar(options_list: List[T]) -> T:
    options_list.sort()
    assert len(options_list) == 6
    return options_list[1]


class TestSpecLearner(TestCase):
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

    def test_learn_spec_asm_1(self):
        spec_learner = SpecLearner()

        spec: list[str] = format_spec(read_file_lines(
            '../input-files/examples/Minepump/minepump_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/minepump_strong_auto_violation.txt")

        expected_spec: list[str] = format_spec(read_file_lines(
            './test_files/minepump_aw_methane.spectra'))

        new_spec: list[str]
        new_spec = spec_learner.learn_weaker_spec(spec, trace, cs_traces=[],
                                                  learning_type=Learning.ASSUMPTION_WEAKENING,
                                                  heuristic=methane_choice_asm)

        print(expected_spec)
        print(new_spec)
        self.assertEqual(expected_spec, new_spec)

    def test_learn_spec_asm_2(self):
        spec_learner = SpecLearner()

        spec: list[str] = format_spec(read_file_lines(
            '../input-files/examples/Minepump/minepump_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/minepump_strong_auto_violation.txt")
        cs: CounterStrategy = \
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:true};']
        cs_trace: CounterTrace = CounterTrace(cs, name="counter_strat_0", heuristic=first_choice)
        cs_traces: List[CounterTrace] = [cs_trace]

        expected_spec: list[str] = format_spec(read_file_lines(
            './test_files/minepump_aw_pump.spectra'))

        new_spec: list[str]
        new_spec = spec_learner.learn_weaker_spec(spec, trace, cs_traces=cs_traces,
                                                  learning_type=Learning.ASSUMPTION_WEAKENING,
                                                  heuristic=random_choice)

        print(expected_spec)
        print(new_spec)
        self.assertEqual(expected_spec, new_spec)

    def test_learn_spec_asm_3(self):
        spec_learner = SpecLearner()

        spec: list[str] = format_spec(read_file_lines(
            '../input-files/examples/Minepump/minepump_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/minepump_strong_auto_violation.txt")
        cs1: CounterStrategy = \
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:true};']
        cs2: CounterStrategy = \
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> S1 {highwater:false, methane:true} / {pump:false};',
             'S0 -> S1 {highwater:false, methane:true} / {pump:true};',
             'S1 -> DEAD {highwater:true, methane:true} / {pump:false};']
        ct0: CounterTrace = CounterTrace(cs1, name="counter_strat_0", heuristic=first_choice)
        ct1: CounterTrace = CounterTrace(cs2, name="counter_strat_1", heuristic=first_choice)
        cs_traces: List[CounterTrace] = [ct0, ct1]

        with self.assertRaises(NoWeakeningException):
            spec_learner.learn_weaker_spec(spec, trace, cs_traces=cs_traces,
                                           learning_type=Learning.ASSUMPTION_WEAKENING,
                                           heuristic=random_choice)

    def test_learn_spec_gar_1(self):
        spec_learner = SpecLearner()

        spec: list[str] = format_spec(read_file_lines(
            './test_files/minepump_aw_methane.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/minepump_strong_auto_violation.txt")
        cs: CounterStrategy = \
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:true};']
        cs_trace: CounterTrace = CounterTrace(cs, name="counter_strat_0", heuristic=first_choice)
        cs_traces: List[CounterTrace] = [cs_trace]

        expected_spec: list[str] = format_spec(read_file_lines(
            './test_files/minepump_aw_methane_gw_methane_fix.spectra'))

        new_spec: list[str]
        new_spec = spec_learner.learn_weaker_spec(spec, trace, cs_traces=cs_traces,
                                                  learning_type=Learning.GUARANTEE_WEAKENING,
                                                  heuristic=methane_choice_gar)

        self.assertEqual(expected_spec, new_spec)

    def test_learn_spec_arbiter_asm_1(self):
        spec_learner = SpecLearner()

        spec: list[str] = format_spec(read_file_lines(
            '../input-files/examples/Arbiter/Arbiter_FINAL_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/arbiter_strong_auto_violation.txt")

        expected_spec: list[str] = format_spec(read_file_lines(
            './test_files/arbiter_aw_ev.spectra'))

        new_spec: list[str]
        new_spec = spec_learner.learn_weaker_spec(spec, trace, cs_traces=[],
                                                  learning_type=Learning.ASSUMPTION_WEAKENING,
                                                  heuristic=last_choice)

        self.assertEqual(expected_spec, new_spec)
