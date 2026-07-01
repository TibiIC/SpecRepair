"""
Tests for StrixHOAParser.

The HOA example used throughout is the mine-pump counter-strategy from Strix:

    AP: 3 "methane" "highwater" "pump"
    controllable-AP: 0 1          ← env controls methane/highwater (inputs)
                                    system controls pump (output)

AP/controllable mapping convention
-----------------------------------
controllable-AP indices → inputs  (environment's choices in the counter-strategy)
non-controllable indices → outputs (system's choices, shown as nondeterminism)

This is the *opposite* of standard HOA controllable-AP semantics but is
consistent with the Spectra counter-strategy invariant: transitions from the
same source state always share inputs and may differ only in outputs.
"""

import unittest
from unittest import TestCase

from spec_repair.helpers.parsers.strix_cs_parser import _parse_guard, _enumerate_satisfying, StrixCSParser

# ── Shared fixture ─────────────────────────────────────────────────────────────

MINE_PUMP_HOA = """\
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

# A minimal two-state counter-strategy: INI self-loops under all inputs when
# the only output (b) is false; reaching a trap otherwise.
SIMPLE_LOOP_HOA = """\
HOA: v1
States: 2
Start: 0
AP: 2 "a" "b"
controllable-AP: 0
--BODY--
State: 0 "[0]"
[(0) & (!1)] 0
[(0) & (1)] 1
State: 1 "[1]"
[(t) & (t)] 1
--END--
"""

# Deadlock example: INI → S0 → DEAD, with only one AP each way.
SIMPLE_DEAD_HOA = """\
HOA: v1
States: 3
Start: 0
AP: 2 "x" "y"
controllable-AP: 0
--BODY--
State: 0 "[0]"
[(!0) & (!1)] 1
State: 1 "[1]"
[(0) & (!1)] 2
State: 2 "[2]"
[(t) & (t)] 2
--END--
"""


# ── Formula internals ──────────────────────────────────────────────────────────

class TestGuardParsing(TestCase):
    """Low-level tests for the guard formula parser and enumerator."""

    def test_tautology_satisfies_all(self):
        guard = _parse_guard("t")
        results = _enumerate_satisfying(guard, 2)
        self.assertEqual(4, len(results))

    def test_single_positive_literal(self):
        guard = _parse_guard("0")
        results = _enumerate_satisfying(guard, 2)
        self.assertTrue(all(r[0] is True for r in results))
        self.assertEqual(2, len(results))

    def test_single_negative_literal(self):
        guard = _parse_guard("!0")
        results = _enumerate_satisfying(guard, 2)
        self.assertTrue(all(r[0] is False for r in results))

    def test_conjunction_both_true(self):
        guard = _parse_guard("0 & 1")
        results = _enumerate_satisfying(guard, 2)
        self.assertEqual(1, len(results))
        self.assertEqual({0: True, 1: True}, results[0])

    def test_disjunction(self):
        guard = _parse_guard("0 | 1")
        results = _enumerate_satisfying(guard, 2)
        self.assertEqual(3, len(results))

    def test_negated_disjunction(self):
        # !(0 | 1) = !0 & !1
        guard = _parse_guard("!(0 | 1)")
        results = _enumerate_satisfying(guard, 2)
        self.assertEqual(1, len(results))
        self.assertEqual({0: False, 1: False}, results[0])

    def test_complex_guard_from_example(self):
        # !(1 | !0) = !1 & 0  (methane=T, highwater=F)
        guard = _parse_guard("!(1 | !0)")
        results = _enumerate_satisfying(guard, 2)
        self.assertEqual(1, len(results))
        self.assertEqual({0: True, 1: False}, results[0])

    def test_tautology_and_negative_literal(self):
        # (!(0 | 1)) & (!2) with 3 APs → one assignment
        guard = _parse_guard("(!(0 | 1)) & (!2)")
        results = _enumerate_satisfying(guard, 3)
        self.assertEqual(1, len(results))
        self.assertEqual({0: False, 1: False, 2: False}, results[0])

    def test_double_negation(self):
        guard = _parse_guard("!!0")
        results = _enumerate_satisfying(guard, 1)
        self.assertEqual(1, len(results))
        self.assertEqual({0: True}, results[0])

    def test_false_literal_unsatisfiable(self):
        guard = _parse_guard("f")
        results = _enumerate_satisfying(guard, 2)
        self.assertEqual([], results)


# ── Header parsing ─────────────────────────────────────────────────────────────

class TestHeaderParsing(TestCase):

    def setUp(self):
        self.parser = StrixCSParser

    def test_ap_names_extracted(self):
        cs = self.parser.from_str(MINE_PUMP_HOA)
        all_names = {name for t in cs.transitions for name in list(t.inputs) + list(t.outputs)}
        self.assertIn("methane", all_names)
        self.assertIn("highwater", all_names)
        self.assertIn("pump", all_names)

    def test_controllable_aps_become_inputs(self):
        """controllable-AP: 0 1 → methane and highwater should be inputs."""
        cs = self.parser.from_str(MINE_PUMP_HOA)
        for t in cs.transitions:
            self.assertIn("methane", t.inputs)
            self.assertIn("highwater", t.inputs)
            self.assertNotIn("pump", t.inputs)

    def test_non_controllable_aps_become_outputs(self):
        """pump is non-controllable → it should be an output."""
        cs = self.parser.from_str(MINE_PUMP_HOA)
        for t in cs.transitions:
            self.assertIn("pump", t.outputs)
            self.assertNotIn("methane", t.outputs)
            self.assertNotIn("highwater", t.outputs)

    def test_start_state_becomes_ini(self):
        cs = self.parser.from_str(MINE_PUMP_HOA)
        self.assertEqual("INI", cs.initial_state)
        sources = {t.source for t in cs.transitions}
        self.assertIn("INI", sources)


# ── Trap / DEAD state detection ────────────────────────────────────────────────

class TestTrapStateDetection(TestCase):

    def setUp(self):
        self.parser = StrixCSParser

    def test_trap_state_named_dead(self):
        cs = self.parser.from_str(MINE_PUMP_HOA)
        self.assertIn("DEAD", cs.all_states())

    def test_dead_state_has_no_outgoing_transitions_in_cs(self):
        """DEAD is a sentinel: the CS object should not expose its self-loops."""
        cs = self.parser.from_str(MINE_PUMP_HOA)
        self.assertEqual([], cs.transitions_from("DEAD"))

    def test_dead_is_a_sink(self):
        cs = self.parser.from_str(MINE_PUMP_HOA)
        self.assertIn("DEAD", cs.sink_states())

    def test_simple_loop_trap_is_dead(self):
        cs = self.parser.from_str(SIMPLE_LOOP_HOA)
        self.assertIn("DEAD", cs.all_states())
        self.assertIn("DEAD", cs.sink_states())


# ── Concrete transition content ────────────────────────────────────────────────

class TestMinePumpTransitions(TestCase):
    """
    Mine-pump counter-strategy:

    State 0 (INI): guard !(0|1) & !2 → state1  /  !(0|1) & 2 → state2(DEAD)
    State 1 (S0):  guard !(1|!0) & t  → state3(S1)   [2 transitions, pump varies]
    State 3 (S1):  guard (0&1) & t    → state2(DEAD) [2 transitions, pump varies]
    State 2 (DEAD): trap, not expanded

    Expected Spectra-equivalent transitions (inputs shared, outputs vary):
        INI → S0  {methane:F, highwater:F} / {pump:F}
        INI → DEAD {methane:F, highwater:F} / {pump:T}
        S0  → S1  {methane:T, highwater:F} / {pump:F}
        S0  → S1  {methane:T, highwater:F} / {pump:T}
        S1  → DEAD {methane:T, highwater:T} / {pump:F}
        S1  → DEAD {methane:T, highwater:T} / {pump:T}
    """

    def setUp(self):
        self.cs = StrixCSParser.from_str(MINE_PUMP_HOA)

    def test_total_transition_count(self):
        self.assertEqual(6, len(self.cs))

    def test_ini_has_two_transitions(self):
        self.assertEqual(2, len(self.cs.transitions_from("INI")))

    def test_ini_transitions_share_inputs(self):
        ts = self.cs.transitions_from("INI")
        self.assertEqual(ts[0].inputs, ts[1].inputs)
        self.assertEqual({'methane': False, 'highwater': False}, ts[0].inputs)

    def test_ini_transitions_differ_in_outputs(self):
        ts = self.cs.transitions_from("INI")
        outputs = {frozenset(t.outputs.items()) for t in ts}
        self.assertEqual(2, len(outputs))
        self.assertIn(frozenset({'pump': False}.items()), outputs)
        self.assertIn(frozenset({'pump': True}.items()), outputs)

    def test_ini_targets(self):
        ts = self.cs.transitions_from("INI")
        targets = {t.target for t in ts}
        self.assertEqual({'S0', 'DEAD'}, targets)

    def test_s0_has_two_transitions_to_s1(self):
        ts = self.cs.transitions_from("S0")
        self.assertEqual(2, len(ts))
        self.assertTrue(all(t.target == "S1" for t in ts))

    def test_s0_inputs_are_methane_true_highwater_false(self):
        ts = self.cs.transitions_from("S0")
        for t in ts:
            self.assertEqual({'methane': True, 'highwater': False}, t.inputs)

    def test_s0_outputs_differ(self):
        ts = self.cs.transitions_from("S0")
        self.assertNotEqual(ts[0].outputs, ts[1].outputs)

    def test_s1_leads_to_dead(self):
        ts = self.cs.transitions_from("S1")
        self.assertEqual(2, len(ts))
        self.assertTrue(all(t.target == "DEAD" for t in ts))

    def test_s1_inputs_are_methane_true_highwater_true(self):
        ts = self.cs.transitions_from("S1")
        for t in ts:
            self.assertEqual({'methane': True, 'highwater': True}, t.inputs)

    def test_all_states_present(self):
        self.assertEqual({'INI', 'S0', 'S1', 'DEAD'}, self.cs.all_states())

    def test_winning_condition_is_deadlock(self):
        self.assertEqual('deadlock', self.cs.winning_condition())

    def test_path_count(self):
        # The DFS fans out across every transition, not every state sequence.
        # S0 has 2 outgoing transitions (pump:F, pump:T), S1 has 2 (pump:F, pump:T),
        # giving 2x2 = 4 paths through INI->S0->S1->DEAD, plus 1 direct INI->DEAD = 5.
        paths = self.cs.all_paths()
        self.assertEqual(5, len(paths))


# ── Loop counter-strategy ─────────────────────────────────────────────────────

class TestLoopCounterStrategy(TestCase):
    """
    SIMPLE_LOOP_HOA: env controls 'a' (controllable-AP: 0), system controls 'b'.
    State 0: [(0) & (!1)] → 0 (self-loop, a=T b=F)
             [(0) & (1)]  → 1 (trap,     a=T b=T)
    State 1: trap → DEAD
    """

    def setUp(self):
        self.cs = StrixCSParser.from_str(SIMPLE_LOOP_HOA)

    def test_states_present(self):
        self.assertIn('INI', self.cs.all_states())
        self.assertIn('DEAD', self.cs.all_states())

    def test_ini_self_loop_transition(self):
        self_loops = [t for t in self.cs.transitions_from('INI') if t.target == 'INI']
        self.assertEqual(1, len(self_loops))
        self.assertEqual({'a': True}, self_loops[0].inputs)
        self.assertEqual({'b': False}, self_loops[0].outputs)

    def test_ini_to_dead_transition(self):
        to_dead = [t for t in self.cs.transitions_from('INI') if t.target == 'DEAD']
        self.assertEqual(1, len(to_dead))
        self.assertEqual({'a': True}, to_dead[0].inputs)
        self.assertEqual({'b': True}, to_dead[0].outputs)

    def test_paths_include_loop(self):
        paths = self.cs.all_paths()
        targets_per_path = [[t.target for t in p] for p in paths]
        self.assertIn(['INI'], targets_per_path)    # self-loop detected immediately

    def test_winning_condition_is_mixed(self):
        # One path loops (INI→INI), one deadlocks (INI→DEAD).
        self.assertEqual('mixed', self.cs.winning_condition())


# ── Simple deadlock counter-strategy ─────────────────────────────────────────

class TestSimpleDeadCounterStrategy(TestCase):
    """
    SIMPLE_DEAD_HOA: INI → S0 → DEAD, one transition each, no branching.
    """

    def setUp(self):
        self.cs = StrixCSParser.from_str(SIMPLE_DEAD_HOA)

    def test_three_states(self):
        self.assertEqual({'INI', 'S0', 'DEAD'}, self.cs.all_states())

    def test_single_path(self):
        paths = self.cs.all_paths()
        self.assertEqual(1, len(paths))
        states = [paths[0][0].source, paths[0][0].target, paths[0][1].target]
        self.assertEqual(['INI', 'S0', 'DEAD'], states)

    def test_ini_transition_inputs(self):
        t = self.cs.transitions_from('INI')[0]
        self.assertEqual({'x': False}, t.inputs)
        self.assertEqual({'y': False}, t.outputs)

    def test_winning_condition_deadlock(self):
        self.assertEqual('deadlock', self.cs.winning_condition())


# ── Structural equality with Spectra parser ───────────────────────────────────

class TestCrossParserEquality(TestCase):
    """
    A counter-strategy parsed from HOA and the equivalent one parsed from the
    Spectra list format must be structurally equal (state names abstracted away).
    """

    def test_mine_pump_equal_to_spectra_equivalent(self):
        from spec_repair.helpers.parsers.spectra_cs_parser import SpectraCSParser

        hoa_cs = StrixCSParser.from_str(MINE_PUMP_HOA)

        # Manually constructed Spectra-equivalent (matches the 6 transitions above)
        spectra_cs = SpectraCSParser.from_lines([
            'INI -> S0 {methane:false, highwater:false} / {pump:false};',
            'INI -> DEAD {methane:false, highwater:false} / {pump:true};',
            'S0 -> S1 {methane:true, highwater:false} / {pump:false};',
            'S0 -> S1 {methane:true, highwater:false} / {pump:true};',
            'S1 -> DEAD {methane:true, highwater:true} / {pump:false};',
            'S1 -> DEAD {methane:true, highwater:true} / {pump:true};',
        ])

        self.assertEqual(hoa_cs, spectra_cs)


if __name__ == '__main__':
    unittest.main()