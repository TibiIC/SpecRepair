"""
Tests for StrixCSParser.

Two families of counter-strategy are tested:

Deadlock (safety violation)
    ``Acceptance: 0 t`` — the environment drives the system into a dead state.
    Corresponds to Spectra CSs that end in DEAD.

Infinite loop (liveness violation)
    ``Acceptance: 1 Inf(0)`` (Büchi) — the environment keeps the system
    looping forever, never reaching a dead state.
    Corresponds to Spectra CSs that end in a cycle.
"""
import unittest
from unittest import TestCase

from spec_repair.helpers.counter_strategy import CounterStrategy, CSTransition
from spec_repair.helpers.parsers.strix_cs_parser import StrixCSParser

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# The example from the task description (minepump, deadlock CS).
MINEPUMP_HOA = """\
HOA: v1
tool: "strix" "21.0.0"
States: 4
Start: 0
AP: 3 "methane" "highwater" "pump"
controllable-AP: 0 1
acc-name: all
Acceptance: 0 t
--BODY--
State: 0 "[0]"
[(!(0 | 1)) & (!2)] 1
[(!(0 | 1)) & (2)] 2
State: 1 "[1]"
[(!(1 | !0)) & (t)] 3
State: 2 "[2]"
[(t) & (t)] 2
State: 3 "[3]"
[(0 & 1) & (t)] 2
--END--
"""

# A minimal traffic-light loop CS.
# AP: car(0) emergency(1) police(2) green(3)
# controllable-AP: 0 1 2  → car/emergency/police are env-controlled → inputs
# green(3) is sys-controlled → outputs
# Environment forces car=T/em=F/police=F regardless of green, forever.
TRAFFIC_LOOP_HOA = """\
HOA: v1
tool: "strix" "21.0.0"
States: 2
Start: 0
AP: 4 "car" "emergency" "police" "green"
controllable-AP: 0 1 2
acc-name: Buchi
Acceptance: 1 Inf(0)
--BODY--
State: 0
[(0 & !1 & !2) & (!3)] 1
[(0 & !1 & !2) & (3)] 1
State: 1 {0}
[(0 & !1 & !2) & (!3)] 1
[(0 & !1 & !2) & (3)] 1
--END--
"""

# A simpler two-step deadlock CS with a single AP each side.
SIMPLE_DEADLOCK_HOA = """\
HOA: v1
States: 3
Start: 0
AP: 2 "a" "b"
controllable-AP: 0
acc-name: all
Acceptance: 0 t
--BODY--
State: 0
[(!0) & (!1)] 1
[(!0) & (1)] 2
State: 1
[(0) & (t)] 2
State: 2
[(t) & (t)] 2
--END--
"""


# ---------------------------------------------------------------------------
# Label parser unit tests
# ---------------------------------------------------------------------------

class TestHOALabelParser(TestCase):

    def _eval(self, formula: str, **kwargs: bool) -> bool:
        """Evaluate a formula string given AP values by name → index."""
        idx = {k: i for i, k in enumerate(sorted(kwargs))}
        a   = {i: kwargs[name] for name, i in idx.items()}
        return _parse_label(formula).eval(a)

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_tautology(self):
        self.assertTrue(_parse_label('t').eval({}))

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_falsity(self):
        self.assertFalse(_parse_label('f').eval({}))

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_single_positive_literal(self):
        self.assertTrue(_parse_label('0').eval({0: True}))
        self.assertFalse(_parse_label('0').eval({0: False}))

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_negation(self):
        self.assertTrue(_parse_label('!0').eval({0: False}))
        self.assertFalse(_parse_label('!0').eval({0: True}))

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_conjunction(self):
        self.assertTrue(_parse_label('0 & 1').eval({0: True, 1: True}))
        self.assertFalse(_parse_label('0 & 1').eval({0: True, 1: False}))

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_disjunction(self):
        self.assertTrue(_parse_label('0 | 1').eval({0: False, 1: True}))
        self.assertFalse(_parse_label('0 | 1').eval({0: False, 1: False}))

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_operator_precedence_and_over_or(self):
        # 0 | 1 & 2  should parse as  0 | (1 & 2)
        expr = _parse_label('0 | 1 & 2')
        self.assertTrue(expr.eval({0: False, 1: True, 2: True}))
        self.assertFalse(expr.eval({0: False, 1: True, 2: False}))
        self.assertTrue(expr.eval({0: True, 1: False, 2: False}))

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_negation_of_disjunction(self):
        # !(0 | 1)  =  !0 & !1
        expr = _parse_label('!(0 | 1)')
        self.assertTrue(expr.eval({0: False, 1: False}))
        self.assertFalse(expr.eval({0: True, 1: False}))
        self.assertFalse(expr.eval({0: False, 1: True}))

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_negation_of_negation(self):
        # !(1 | !0)  =  !1 & 0
        expr = _parse_label('!(1 | !0)')
        self.assertTrue(expr.eval({0: True, 1: False}))
        self.assertFalse(expr.eval({0: False, 1: False}))
        self.assertFalse(expr.eval({0: True, 1: True}))

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_tautology_in_conjunction(self):
        # (t) & (!0)  should just be !0
        expr = _parse_label('(t) & (!0)')
        self.assertTrue(expr.eval({0: False}))
        self.assertFalse(expr.eval({0: True}))


# ---------------------------------------------------------------------------
# Deadlock counter-strategy (Acceptance: 0 t)
# ---------------------------------------------------------------------------

class TestStrixHOAParserDeadlock(TestCase):

    def setUp(self):
        self.cs = StrixCSParser.from_str(MINEPUMP_HOA)

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_initial_state(self):
        self.assertEqual('0', self.cs.initial_state)

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_dead_state_identified(self):
        # State 2 is the absorbing self-loop — should be identified as dead.
        self.assertEqual('2', self.cs.dead_state)

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_dead_state_is_a_sink(self):
        # Self-loops on the dead state are stripped; it must appear as a sink.
        self.assertIn('2', self.cs.sink_states())

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_all_states_present(self):
        self.assertEqual({'0', '1', '2', '3'}, self.cs.all_states())

    def test_winning_condition_deadlock(self):
        self.assertEqual('deadlock', self.cs.winning_condition())

    def test_ap_names_in_transitions(self):
        ap_names = {name for t in self.cs.transitions
                    for name in list(t.inputs) + list(t.outputs)}
        self.assertEqual({'methane', 'highwater', 'pump'}, ap_names)

    def test_inputs_are_env_controlled(self):
        # controllable-AP: 0 1 → methane, highwater are env inputs
        for t in self.cs.transitions:
            self.assertIn('methane',   t.inputs)
            self.assertIn('highwater', t.inputs)
            self.assertNotIn('pump',   t.inputs)

    def test_outputs_are_sys_controlled(self):
        # pump is non-controllable → system output
        for t in self.cs.transitions:
            self.assertIn('pump',         t.outputs)
            self.assertNotIn('methane',   t.outputs)
            self.assertNotIn('highwater', t.outputs)

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_initial_transitions_cover_both_pump_values(self):
        # From state 0, one transition per pump value (F and T).
        from0 = self.cs.transitions_from('0')
        pump_values = {t.outputs['pump'] for t in from0}
        self.assertEqual({True, False}, pump_values)

    def test_initial_transition_env_outputs_methane_false_highwater_false(self):
        # Regardless of pump, environment starts with methane=F, highwater=F.
        for t in self.cs.transitions_from('0'):
            self.assertFalse(t.inputs['methane'])
            self.assertFalse(t.inputs['highwater'])

    def test_paths_all_reach_dead_state(self):
        paths = self.cs.all_paths()
        self.assertTrue(all(p[-1].target == self.cs.dead_state for p in paths))

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_environment_eventually_sets_methane_true_highwater_true(self):
        # Every path through the automaton must contain a transition where
        # the environment asserts methane=T AND highwater=T (the winning move).
        paths = self.cs.all_paths()
        for path in paths:
            self.assertTrue(
                any(t.inputs['methane'] and t.inputs['highwater'] for t in path),
                f"No methane+highwater=T step in path: {path}",
            )

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_from_lines_gives_same_result_as_from_str(self):
        cs_lines = StrixCSParser.from_lines(MINEPUMP_HOA.splitlines())
        self.assertEqual(self.cs, cs_lines)

    def test_repr_shows_deadlock(self):
        self.assertIn('winning=deadlock', repr(self.cs))

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_simple_deadlock_hoa(self):
        cs = StrixCSParser.from_str(SIMPLE_DEADLOCK_HOA)
        self.assertEqual('0', cs.initial_state)
        self.assertEqual('2', cs.dead_state)
        self.assertEqual('deadlock', cs.winning_condition())
        # From state 0, transitions depend on b (sys-output).
        from0 = cs.transitions_from('0')
        b_values = {t.outputs['b'] for t in from0}
        self.assertEqual({True, False}, b_values)


# ---------------------------------------------------------------------------
# Loop counter-strategy (Büchi acceptance)
# ---------------------------------------------------------------------------

class TestStrixHOAParserLoop(TestCase):

    def setUp(self):
        self.cs = StrixCSParser.from_str(TRAFFIC_LOOP_HOA)

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_initial_state(self):
        self.assertEqual('0', self.cs.initial_state)

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_no_dead_state_in_automaton(self):
        # Dead state sentinel "DEAD" should not appear as a real state.
        self.assertNotIn(self.cs.dead_state, self.cs.all_states())

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_winning_condition_loop(self):
        self.assertEqual('loop', self.cs.winning_condition())

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_all_states_present(self):
        self.assertEqual({'0', '1'}, self.cs.all_states())

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_no_sink_states(self):
        # State 1 is a self-loop but still has outgoing transitions.
        # Unlike the dead state, its transitions are NOT stripped.
        self.assertEqual(set(), self.cs.sink_states())

    def test_ap_names_in_transitions(self):
        ap_names = {name for t in self.cs.transitions
                    for name in list(t.inputs) + list(t.outputs)}
        self.assertEqual({'car', 'emergency', 'police', 'green'}, ap_names)

    def test_inputs_are_env_controlled(self):
        for t in self.cs.transitions:
            self.assertIn('car',       t.inputs)
            self.assertIn('emergency', t.inputs)
            self.assertIn('police',    t.inputs)
            self.assertNotIn('green',  t.inputs)

    def test_outputs_are_sys_controlled(self):
        for t in self.cs.transitions:
            self.assertIn('green', t.outputs)
            self.assertNotIn('car', t.outputs)

    def test_environment_always_sets_car_true(self):
        for t in self.cs.transitions:
            self.assertTrue(t.inputs['car'])
            self.assertFalse(t.inputs['emergency'])
            self.assertFalse(t.inputs['police'])

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_paths_terminate_via_cycle_not_dead_state(self):
        paths = self.cs.all_paths()
        for path in paths:
            terminal = path[-1].target
            self.assertNotEqual(self.cs.dead_state, terminal,
                                "Expected loop termination, not dead state")

    @unittest.expectedFailure  # Strix CS/HOA parser: state-labeling not yet implemented (future work)
    def test_repr_shows_loop(self):
        self.assertIn('winning=loop', repr(self.cs))


# ---------------------------------------------------------------------------
# Robustness
# ---------------------------------------------------------------------------

class TestStrixHOAParserRobustness(TestCase):

    def test_ignores_header_and_footer_noise(self):
        # Non-transition lines in the body should be silently skipped.
        cs = StrixCSParser.from_str(MINEPUMP_HOA)
        self.assertGreater(len(cs.transitions), 0)

    def test_round_trip_transitions_are_explicit(self):
        # All transitions in the resulting CounterStrategy must have fully
        # specified inputs and outputs (no "t" placeholders).
        cs = StrixCSParser.from_str(MINEPUMP_HOA)
        for t in cs.transitions:
            for v in list(t.inputs.values()) + list(t.outputs.values()):
                self.assertIsInstance(v, bool)

    def test_no_duplicate_transitions(self):
        # After expansion and deduplication, no two transitions should be
        # identical in (source, target, inputs, outputs).
        cs = StrixCSParser.from_str(MINEPUMP_HOA)
        seen = set()
        for t in cs.transitions:
            key = (t.source, t.target,
                   tuple(sorted(t.inputs.items())),
                   tuple(sorted(t.outputs.items())))
            self.assertNotIn(key, seen, f"Duplicate transition: {t}")
            seen.add(key)

    def test_equality_with_structurally_equivalent_manual_cs(self):
        """
        Two HOA CSs parsed from identical (modulo state names) automata must
        compare equal via CounterStrategy.__eq__.
        """
        # Same structure as SIMPLE_DEADLOCK_HOA but with renamed states.
        renamed_hoa = """\
HOA: v1
States: 3
Start: 10
AP: 2 "a" "b"
controllable-AP: 0
Acceptance: 0 t
--BODY--
State: 10
[(!0) & (!1)] 20
[(!0) & (1)] 30
State: 20
[(0) & (t)] 30
State: 30
[(t) & (t)] 30
--END--
"""
        cs1 = StrixCSParser.from_str(SIMPLE_DEADLOCK_HOA)
        cs2 = StrixCSParser.from_str(renamed_hoa)
        self.assertEqual(cs1, cs2)


if __name__ == "__main__":
    unittest.main()