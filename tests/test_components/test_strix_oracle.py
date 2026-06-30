from typing import Optional

from spec_repair.components.oracles.strix_gr1_revised_oracle import StrixGR1RevisedOracle
from spec_repair.helpers.spectra_specification import SpectraSpecification
from tests.base_test_case import BaseTestCase
from spec_repair.ltl_types import CounterStrategy


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

        expected_cs: CounterStrategy = \
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:true};']
        self.assertEqual(expected_cs, cs)

    def test_synthesise_and_check_2(self):
        weakened_spec: SpectraSpecification = SpectraSpecification.from_file('./test_files/minepump_aw_pump.spectra')

        cs: CounterStrategy = self.oracle._synthesise_and_check(weakened_spec)

        expected_cs: CounterStrategy = \
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> S1 {highwater:false, methane:true} / {pump:false};',
             'S0 -> S1 {highwater:false, methane:true} / {pump:true};',
             'S1 -> DEAD {highwater:true, methane:true} / {pump:false};']
        self.assertEqual(expected_cs, cs)

    def test_synthesise_and_check_asm_eventually(self):
        weakened_spec: SpectraSpecification = SpectraSpecification.from_file('./test_files/minepump_aw_ev.spectra')

        cs: CounterStrategy = self.oracle._synthesise_and_check(weakened_spec)

        expected_cs: CounterStrategy = \
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:true};']
        self.assertEqual(expected_cs, cs)

    def test_synthesise_and_check_arbiter_asm_eventually(self):
        weakened_spec: SpectraSpecification = SpectraSpecification.from_file('./test_files/arbiter_aw_ev.spectra')

        cs: Optional[CounterStrategy] = self.oracle._synthesise_and_check(weakened_spec)
        self.assertIsNone(cs)
