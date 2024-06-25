import os
from unittest import TestCase

from spec_repair.components.spec_oracle import SpecOracle
from spec_repair.ltl import CounterStrategy
from spec_repair.old.specification_helper import read_file
from spec_repair.util.spec_util import format_spec


class TestSpecLearner(TestCase):
    @classmethod
    def setUpClass(cls):
        # Change the working directory to the script's directory
        cls.original_working_directory = os.getcwd()
        test_components_dir = os.path.dirname(os.path.abspath(__file__))
        tests_dir = os.path.dirname(test_components_dir)
        print(tests_dir)
        os.chdir(tests_dir)

    @classmethod
    def tearDownClass(cls):
        # Restore the original working directory
        os.chdir(cls.original_working_directory)

    def test_synthesise_and_check(self):
        spec_oracle = SpecOracle()
        weakened_spec: list[str] = format_spec(read_file(
            './test_files/minepump_aw_methane.spectra'))

        cs: CounterStrategy = spec_oracle.synthesise_and_check(weakened_spec)

        expected_cs: CounterStrategy = \
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:true};']
        self.assertEqual(expected_cs, cs)

    def test_synthesise_and_check_2(self):
        spec_oracle = SpecOracle()
        weakened_spec: list[str] = format_spec(read_file(
            './test_files/minepump_aw_pump.spectra'))

        cs: CounterStrategy = spec_oracle.synthesise_and_check(weakened_spec)

        expected_cs: CounterStrategy = \
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> S1 {highwater:false, methane:true} / {pump:false};',
             'S0 -> S1 {highwater:false, methane:true} / {pump:true};',
             'S1 -> DEAD {highwater:true, methane:true} / {pump:false};']
        self.assertEqual(expected_cs, cs)

    def test_synthesise_and_check_asm_eventually(self):
        spec_oracle = SpecOracle()
        weakened_spec: list[str] = format_spec(read_file(
            './test_files/minepump_aw_ev.spectra'))

        cs: CounterStrategy = spec_oracle.synthesise_and_check(weakened_spec)

        expected_cs: CounterStrategy = \
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:true};']
        self.assertEqual(expected_cs, cs)
