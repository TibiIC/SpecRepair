import unittest
from typing import Optional

from spec_repair.components.oracles.spectra_gr1_oracle import SpectraGR1Oracle
from spec_repair.exceptions import SpecificationNotVerifiableException
from spec_repair.model.counter_strategy import CounterStrategy
from spec_repair.helpers.parsers.spectra_cs_parser import SpectraCSParser
from spec_repair.model.spectra_specification import SpectraSpecification
from tests.base_test_case import BaseTestCase


class TestSpectraSpecOracle(BaseTestCase):
    def test_synthesise_and_check(self):
        spec_oracle = SpectraGR1Oracle()
        weakened_spec: SpectraSpecification = SpectraSpecification.from_file('./test_files/minepump_aw_methane.spectra')

        cs: CounterStrategy = spec_oracle._synthesise_and_check(weakened_spec)

        expected_cs: CounterStrategy = SpectraCSParser.from_lines(
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:true};']
        )
        self.assertEqual(expected_cs, cs)

    def test_synthesise_and_check_2(self):
        spec_oracle = SpectraGR1Oracle()
        weakened_spec: SpectraSpecification = SpectraSpecification.from_file('./test_files/minepump_aw_pump.spectra')

        cs: CounterStrategy = spec_oracle._synthesise_and_check(weakened_spec)

        expected_cs: CounterStrategy = SpectraCSParser.from_lines(
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> S1 {highwater:false, methane:true} / {pump:false};',
             'S0 -> S1 {highwater:false, methane:true} / {pump:true};',
             'S1 -> DEAD {highwater:true, methane:true} / {pump:false};']
        )
        self.assertEqual(expected_cs, cs)

    def test_synthesise_and_check_asm_eventually(self):
        spec_oracle = SpectraGR1Oracle()
        weakened_spec: SpectraSpecification = SpectraSpecification.from_file('./test_files/minepump_aw_ev.spectra')

        cs: CounterStrategy = spec_oracle._synthesise_and_check(weakened_spec)

        expected_cs: CounterStrategy = SpectraCSParser.from_lines(
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:true};']
        )
        self.assertEqual(expected_cs, cs)

    def test_synthesise_and_check_cycle_counter_strategy(self):
        spec_oracle = SpectraGR1Oracle()
        weakened_spec: SpectraSpecification = SpectraSpecification.from_file('./test_files/traffic/traffic_updated_infinite_loop.spectra')

        cs: CounterStrategy = spec_oracle._synthesise_and_check(weakened_spec)

        expected_cs: CounterStrategy = SpectraCSParser.from_lines(
            ['INI -> S0 {car:true, emergency:false, police:false} / {green:false};',
             'INI -> S0 {car:true, emergency:false, police:false} / {green:true};',
             'S0 -> S0 {car:true, emergency:false, police:false} / {green:false};',
             'S0 -> S0 {car:true, emergency:false, police:false} / {green:true};']
        )
        self.assertEqual(expected_cs, cs)

    def test_synthesise_and_check_arbiter_asm_eventually(self):
        spec_oracle = SpectraGR1Oracle()
        weakened_spec: SpectraSpecification = SpectraSpecification.from_file('./test_files/arbiter_aw_ev.spectra')

        cs: Optional[CounterStrategy] = spec_oracle._synthesise_and_check(weakened_spec)
        self.assertIsNone(cs)

class TestUnverifiableSpecifications(BaseTestCase):
    """
    A specification Spectra's CLI refuses to check at all.

    `violations_in_initial_conditions` screens those out before invoking the
    CLI - because the CLI reports them inconsistently - and the synthesis
    wrappers return None instead of output. Both oracle entry points used to run
    `re.search` straight over that None and die with `TypeError: expected string
    or bytes-like object`, which named neither the specification nor the reason.
    Worse, it happened several frames below the repair search, which had no
    handler, so one malformed candidate ended the whole run.
    """

    # An initial assumption referring to a system variable: legal to write,
    # rejected by Spectra. This is exactly what the repair search produced for
    # lift and gyro on the trace-violation case studies.
    INITIAL_ASSUMPTION_ON_SYS_VAR = """module Broken

env boolean a;
sys boolean b;

assumption -- initial_assumption
\t!b;

guarantee -- initial_guarantee
\t!b;
"""

    def setUp(self):
        self.spec = SpectraSpecification.from_str(self.INITIAL_ASSUMPTION_ON_SYS_VAR)

    def test_synthesise_and_check_raises_a_named_exception(self):
        with self.assertRaises(SpecificationNotVerifiableException) as ctx:
            SpectraGR1Oracle()._synthesise_and_check(self.spec)
        # The message has to identify the cause and the specification, since the
        # point of the change is that the old TypeError identified neither.
        self.assertIn("initial assumption", str(ctx.exception).lower())
        self.assertIn("module Broken", str(ctx.exception))

    def test_is_realisable_raises_rather_than_guessing_a_verdict(self):
        """
        `is_realisable` must not answer. Returning True would record a
        specification Spectra never checked as a repair; returning False would
        claim a verdict it never reached.
        """
        with self.assertRaises(SpecificationNotVerifiableException):
            SpectraGR1Oracle.is_realisable(self.spec)

    def test_a_checkable_specification_is_unaffected(self):
        """The guard must only fire when Spectra actually declined."""
        ok = SpectraSpecification.from_file('./test_files/minepump_aw_methane.spectra')
        self.assertIsNotNone(SpectraGR1Oracle()._synthesise_and_check(ok))
    def test_heap_exhaustion_is_reported_as_unverifiable(self):
        """
        Spectra's BDD engine can exhaust the JVM heap on a large state space -
        colorsort does it even with the default 15.7 GB max heap on a 62 GB
        machine, so it is not a -Xmx misconfiguration. The OutOfMemoryError used
        to propagate out of jpype and kill the whole case study; it is now the
        same "could not check this" the orchestrator already skips.
        """
        import jpype
        from spec_repair.components.oracles.spectra_gr1_oracle import _synthesise_or_reject
        oom = jpype.JClass("java.lang.OutOfMemoryError")

        def raises_oom():
            raise oom("Java heap space")

        with self.assertRaises(SpecificationNotVerifiableException) as ctx:
            _synthesise_or_reject(raises_oom, self.spec)
        self.assertIn("ran out of heap", str(ctx.exception))

    def test_an_unrelated_java_error_is_not_swallowed(self):
        """Only heap exhaustion maps to unverifiable; anything else must surface."""
        import jpype
        from spec_repair.components.oracles.spectra_gr1_oracle import _synthesise_or_reject
        iae = jpype.JClass("java.lang.IllegalArgumentException")

        def raises_other():
            raise iae("something else")

        with self.assertRaises(jpype.JException):
            _synthesise_or_reject(raises_other, self.spec)


if __name__ == "__main__":
    unittest.main()
