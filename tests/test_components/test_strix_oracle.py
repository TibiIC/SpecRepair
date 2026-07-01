import unittest
from typing import Optional

from spec_repair.components.oracles.strix_gr1_revised_oracle import StrixGR1RevisedOracle
from spec_repair.helpers.counter_strategy import CounterStrategy
from spec_repair.helpers.parsers.spectra_cs_parser import SpectraCSParser
from spec_repair.helpers.spectra_specification import SpectraSpecification
from tests.base_test_case import BaseTestCase


class TestStrixSpecOracle(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Set up the mitigator
        cls.oracle = StrixGR1RevisedOracle()

    def test_is_realisable(self):
        weakened_spec: SpectraSpecification = SpectraSpecification.from_file('./test_files/minepump_aw_methane.spectra')

        self.assertFalse(self.oracle.is_realisable(weakened_spec))

    def test_is_realisable_2(self):
        weakened_spec: SpectraSpecification = SpectraSpecification.from_file('./test_files/minepump_aw_pump.spectra')

        self.assertTrue(self.oracle.is_realisable(weakened_spec))

    def test_is_realisable_asm_eventually(self):
        weakened_spec: SpectraSpecification = SpectraSpecification.from_file('./test_files/minepump_aw_ev.spectra')

        self.assertFalse(self.oracle.is_realisable(weakened_spec))

    def test_is_realisable_arbiter_asm_eventually(self):
        weakened_spec: SpectraSpecification = SpectraSpecification.from_file('./test_files/arbiter_aw_ev.spectra')

        self.assertTrue(self.oracle.is_realisable(weakened_spec))

    def test_synthesise_and_check(self):
        weakened_spec: SpectraSpecification = SpectraSpecification.from_file('./test_files/minepump_aw_methane.spectra')

        cs: CounterStrategy = self.oracle._synthesise_and_check(weakened_spec)

        expected_cs: CounterStrategy = SpectraCSParser.from_lines(
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:true};']
        )
        self.assertEqual(expected_cs, cs)

    def test_synthesise_and_check_2(self):
        weakened_spec: SpectraSpecification = SpectraSpecification.from_file('./test_files/minepump_aw_pump.spectra')

        cs: Optional[CounterStrategy] = self.oracle._synthesise_and_check(weakened_spec)
        self.assertIsNone(cs)

    def test_synthesise_and_check_asm_eventually(self):
        weakened_spec: SpectraSpecification = SpectraSpecification.from_file('./test_files/minepump_aw_ev.spectra')

        cs: CounterStrategy = self.oracle._synthesise_and_check(weakened_spec)

        expected_cs: CounterStrategy = SpectraCSParser.from_lines(
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:true};']
        )
        self.assertEqual(expected_cs, cs)

    def test_synthesise_and_check_arbiter_asm_eventually(self):
        weakened_spec: SpectraSpecification = SpectraSpecification.from_file('./test_files/arbiter_aw_ev.spectra')

        cs: Optional[CounterStrategy] = self.oracle._synthesise_and_check(weakened_spec)
        self.assertIsNone(cs)

    def test_synthesise_and_check_cycle_counter_strategy(self):
        weakened_spec: SpectraSpecification = SpectraSpecification.from_file('./test_files/traffic/traffic_updated_infinite_loop.spectra')

        cs: CounterStrategy = self.oracle._synthesise_and_check(weakened_spec)

        expected_cs: CounterStrategy = SpectraCSParser.from_lines(
            ['INI -> S0 {car:true, emergency:false, police:false} / {green:false};',
             'INI -> S0 {car:true, emergency:false, police:false} / {green:true};',
             'S0 -> S0 {car:true, emergency:false, police:false} / {green:false};',
             'S0 -> S0 {car:true, emergency:false, police:false} / {green:true};']
        )
        self.assertEqual(expected_cs, cs)


if __name__ == "__main__":
    unittest.main()
