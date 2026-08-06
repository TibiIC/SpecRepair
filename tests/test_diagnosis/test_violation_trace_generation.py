"""
Tests for generating traces that deliberately violate a specification's
assumptions - the trace-violation experimental setup.

The property that matters is not "a trace was produced" but "the trace violates
exactly the assumptions it claims and nothing else", so most of these verify the
generated trace independently, by feeding it back through the repair pipeline's
own ASP violation check rather than trusting the generator's own constraints.
"""
import random
import re

from spec_repair.components.new_spec_encoder import NewSpecEncoder
from spec_repair.diagnosis.violation_trace_generation import (
    GeneratedTrace,
    INVARIANT_WHEN,
    build_violation_asp,
    find_violable_assumptions,
    generate_assumption_violating_traces,
    get_formula_names,
)
from spec_repair.ltl_types import GR1FormulaType
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.wrappers.asp_wrappers import get_violations
from tests.base_test_case import BaseTestCase

CASE_STUDIES = '../input-files/case-studies/spectra/trace_violation'

# `G(!a -> (!a | !b))` is `true`: whenever the antecedent holds, `!a` makes the
# consequent hold too. `real_assumption` is the control - an ordinary violable
# invariant in the same specification.
TAUTOLOGICAL_ASSUMPTION_SPEC = '''module Tautology

env boolean a;
env boolean b;
sys boolean c;

assumption -- initial_assumption
\t!a & !b;

guarantee -- initial_guarantee
\t!c;

assumption -- tautological_assumption
\tG(!a->!a|!b);

assumption -- real_assumption
\tG(!a|!b);
'''


def violations_of(spec: SpectraSpecification, trace: GeneratedTrace):
    """What the repair pipeline itself says this trace violates."""
    lines = [line + "\n" for line in trace.lines if line.strip()]
    output = get_violations(NewSpecEncoder.encode_ASP(spec, lines, []))
    return sorted(set(re.findall(r"violation_holds\(([^,]+),", "".join(output))))


class TestViolationTraceGeneration(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.minepump = SpectraSpecification.from_file(f'{CASE_STUDIES}/minepump/original.spectra')
        cls.traffic = SpectraSpecification.from_file(f'{CASE_STUDIES}/traffic_single/original.spectra')

    def test_generated_trace_violates_exactly_what_it_claims(self):
        for spec in (self.minepump, self.traffic):
            with self.subTest(module=spec._module_name):
                traces = generate_assumption_violating_traces(spec, n_traces=1, rng=random.Random(0))
                self.assertEqual(1, len(traces))
                self.assertEqual(traces[0].violated_assumptions, violations_of(spec, traces[0]))

    def test_no_guarantee_is_ever_violated(self):
        """
        The environment misbehaves; the system must not. A trace that also
        breaks a guarantee would not isolate an assumption failure.
        """
        guarantees = set(get_formula_names(self.traffic, GR1FormulaType.GAR))
        traces = generate_assumption_violating_traces(self.traffic, n_traces=3, rng=random.Random(1))
        self.assertGreater(len(traces), 0)
        for trace in traces:
            self.assertFalse(set(violations_of(self.traffic, trace)) & guarantees)

    def test_only_assumptions_are_violated(self):
        assumptions = set(get_formula_names(self.traffic, GR1FormulaType.ASM))
        traces = generate_assumption_violating_traces(self.traffic, n_traces=2, rng=random.Random(2))
        for trace in traces:
            self.assertTrue(set(violations_of(self.traffic, trace)) <= assumptions)

    def test_trace_length_is_respected(self):
        traces = generate_assumption_violating_traces(
            self.traffic, n_traces=3, min_timepoints=2, max_timepoints=3, rng=random.Random(3))
        self.assertGreater(len(traces), 0)
        for trace in traces:
            self.assertIn(trace.n_timepoints, (2, 3))
            timepoints = {int(m) for m in re.findall(r"holds_at\([^,]+,(\d+),", "\n".join(trace.lines))}
            self.assertEqual(set(range(trace.n_timepoints)), timepoints)

    def test_traces_are_distinct(self):
        traces = generate_assumption_violating_traces(self.traffic, n_traces=4, rng=random.Random(4))
        rendered = ["\n".join(t.lines) for t in traces]
        self.assertEqual(len(rendered), len(set(rendered)))

    def test_trace_has_no_weak_timepoint_facts(self):
        """
        Background knowledge derives holds_at *and* not_holds_at at the weak
        timepoint for every atom, by design. Those are the open end of a finite
        prefix, not observed state, and must not reach the trace file - they
        would read as a contradiction.
        """
        traces = generate_assumption_violating_traces(self.minepump, n_traces=2, rng=random.Random(5))
        for trace in traces:
            self.assertNotIn("weak_t", "\n".join(trace.lines))

    def test_trace_lines_reparse_as_asp_facts(self):
        traces = generate_assumption_violating_traces(self.minepump, n_traces=1, rng=random.Random(6))
        for line in traces[0].lines:
            if line.strip():
                self.assertRegex(line, r"^(not_)?holds_at\(\w+,\d+,\w+\)\.$")

    # ---------------- violability reporting ----------------

    def test_tautological_assumption_is_reported_unviolable(self):
        """
        A tautological assumption cannot be violated at any length.

        This used to use minepump's assumption2_1, which was
        `G(!highwater -> (!highwater | !methane))` - equivalent to `true`. It was
        strengthened to `G(!highwater | !methane)` on 2026-07-30 to make
        original.spectra match the old strong.spectra, so it is violable now and
        no longer demonstrates this. The tautology is written out here instead,
        where nothing else can move it.
        """
        spec = SpectraSpecification.from_str(TAUTOLOGICAL_ASSUMPTION_SPEC)
        violable = find_violable_assumptions(spec, 1, 3)
        self.assertEqual([], violable["tautological_assumption"],
                         "an assumption equivalent to `true` must be unviolable")
        # The non-tautological one in the same spec is the control: if it were
        # also empty, the test would pass for the wrong reason.
        self.assertNotEqual([], violable["real_assumption"])

    # ---------------- restricting which assumptions are targeted ----------------

    def test_only_assumptions_restricts_what_is_reported(self):
        violable = find_violable_assumptions(self.minepump, 1, 5,
                                             only_assumptions=["assumption2_1"])
        self.assertEqual(["assumption2_1"], list(violable))

    def test_only_assumptions_rejects_an_unknown_name(self):
        with self.assertRaises(ValueError):
            find_violable_assumptions(self.minepump, 1, 3, only_assumptions=["no_such_assumption"])

    def test_invariant_filter_excludes_the_initial_assumption(self):
        """
        `--invariant-only` is this filter. minepump's initial_assumption is
        `ini`; both numbered ones are `G`.
        """
        invariant = get_formula_names(self.minepump, GR1FormulaType.ASM, when=INVARIANT_WHEN)
        self.assertEqual(["assumption1_1", "assumption2_1"], invariant)
        self.assertIn("initial_assumption",
                      get_formula_names(self.minepump, GR1FormulaType.ASM))

    def test_generated_traces_respect_only_assumptions(self):
        """Restricting the targets narrows the violation, not the constraints."""
        traces = generate_assumption_violating_traces(
            self.minepump, n_traces=3, min_timepoints=1, max_timepoints=5,
            rng=random.Random(0), only_assumptions=["assumption2_1"])
        self.assertGreater(len(traces), 0)
        for trace in traces:
            self.assertEqual(["assumption2_1"], trace.violated_assumptions)
            # Everything outside the targeted set must still hold - checked
            # against the pipeline's own violation detection, not the generator.
            self.assertEqual(["assumption2_1"], violations_of(self.minepump, trace))

    def test_minepump_second_assumption_is_violable_within_three_timepoints(self):
        """
        Pins the 2026-07-30 strengthening. `G(!highwater | !methane)` needs 2
        timepoints, not 1, because initial_assumption forces `!highwater &
        !methane` at t0 - so the conflict cannot appear until t1.
        """
        violable = find_violable_assumptions(self.minepump, 1, 3)
        self.assertEqual([2, 3], violable["assumption2_1"])

    def test_next_violation_needs_room_before_the_end(self):
        """
        A violation involving `next` cannot occur at the last real timepoint,
        because `next` there lands on the weak timepoint and is satisfied
        vacuously. minepump's assumption1_1 needs 4 timepoints for that reason.
        """
        self.assertEqual([], find_violable_assumptions(self.minepump, 1, 3)["assumption1_1"])
        self.assertIn(4, find_violable_assumptions(self.minepump, 4, 4)["assumption1_1"])

    def test_generation_fails_loudly_when_nothing_is_violable(self):
        """
        arbiter's only assumption is the liveness property GF(a), which a finite
        prefix can always satisfy vacuously at the weak timepoint - so there is
        nothing to generate, and that should be an error rather than silence.
        """
        arbiter = SpectraSpecification.from_file(f'{CASE_STUDIES}/arbiter/original.spectra')
        with self.assertRaises(ValueError):
            generate_assumption_violating_traces(arbiter, n_traces=1, rng=random.Random(0))

    def test_invalid_timepoint_range_is_rejected(self):
        for lo, hi in ((0, 3), (3, 2)):
            with self.subTest(range=(lo, hi)):
                with self.assertRaises(ValueError):
                    generate_assumption_violating_traces(
                        self.minepump, min_timepoints=lo, max_timepoints=hi)

    def test_asp_program_pins_the_chosen_assumptions(self):
        asp = build_violation_asp(self.minepump, ["initial_assumption"], 2)
        self.assertIn("to_violate(initial_assumption).", asp)
        self.assertIn(":- violation_holds(E,T,S), not to_violate(E).", asp)
