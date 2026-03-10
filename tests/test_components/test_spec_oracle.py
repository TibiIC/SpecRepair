from typing import Optional

from spec_repair.components.oracles.spectra_gr1_oracle import SpectraGR1Oracle
from spec_repair.helpers.spectra_specification import SpectraSpecification
from tests.base_test_case import BaseTestCase
from spec_repair.ltl_types import CounterStrategy


class TestSpectraSpecOracle(BaseTestCase):
    def test_synthesise_and_check(self):
        spec_oracle = SpectraGR1Oracle()
        weakened_spec: SpectraSpecification = SpectraSpecification.from_file('./test_files/minepump_aw_methane.spectra')

        cs: CounterStrategy = spec_oracle._synthesise_and_check(weakened_spec)

        expected_cs: CounterStrategy = \
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:true};']
        self.assertEqual(expected_cs, cs)

    def test_synthesise_and_check_2(self):
        spec_oracle = SpectraGR1Oracle()
        weakened_spec: SpectraSpecification = SpectraSpecification.from_file('./test_files/minepump_aw_pump.spectra')

        cs: CounterStrategy = spec_oracle._synthesise_and_check(weakened_spec)

        expected_cs: CounterStrategy = \
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> S1 {highwater:false, methane:true} / {pump:false};',
             'S0 -> S1 {highwater:false, methane:true} / {pump:true};',
             'S1 -> DEAD {highwater:true, methane:true} / {pump:false};']
        self.assertEqual(expected_cs, cs)

    def test_synthesise_and_check_asm_eventually(self):
        spec_oracle = SpectraGR1Oracle()
        weakened_spec: SpectraSpecification = SpectraSpecification.from_file('./test_files/minepump_aw_ev.spectra')

        cs: CounterStrategy = spec_oracle._synthesise_and_check(weakened_spec)

        expected_cs: CounterStrategy = \
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:true};']
        self.assertEqual(expected_cs, cs)

    def test_synthesise_and_check_arbiter_asm_eventually(self):
        spec_oracle = SpectraGR1Oracle()
        weakened_spec: SpectraSpecification = SpectraSpecification.from_file('./test_files/arbiter_aw_ev.spectra')

        cs: Optional[CounterStrategy] = spec_oracle._synthesise_and_check(weakened_spec)
        self.assertIsNone(cs)
