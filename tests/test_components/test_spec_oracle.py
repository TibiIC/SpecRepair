from typing import Optional

from tests.base_test_case import BaseTestCase
from spec_repair.components.spec_oracle import SpecOracle
from spec_repair.ltl_types import CounterStrategy
from spec_repair.util.file_util import read_file_lines
from spec_repair.util.spec_util import format_spec


class TestSpecLearner(BaseTestCase):
    def test_synthesise_and_check(self):
        spec_oracle = SpecOracle()
        weakened_spec: list[str] = format_spec(read_file_lines(
            './test_files/minepump_aw_methane.spectra'))

        cs: CounterStrategy = spec_oracle.synthesise_and_check(weakened_spec)

        expected_cs: CounterStrategy = \
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:true};']
        self.assertEqual(expected_cs, cs)

    def test_synthesise_and_check_2(self):
        spec_oracle = SpecOracle()
        weakened_spec: list[str] = format_spec(read_file_lines(
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
        weakened_spec: list[str] = format_spec(read_file_lines(
            './test_files/minepump_aw_ev.spectra'))

        cs: CounterStrategy = spec_oracle.synthesise_and_check(weakened_spec)

        expected_cs: CounterStrategy = \
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:true};']
        self.assertEqual(expected_cs, cs)

    def test_synthesise_and_check_arbiter_asm_eventually(self):
        spec_oracle = SpecOracle()
        weakened_spec: list[str] = format_spec(read_file_lines(
            './test_files/arbiter_aw_ev.spectra'))

        cs: Optional[CounterStrategy] = spec_oracle.synthesise_and_check(weakened_spec)
        self.assertIsNone(cs)
