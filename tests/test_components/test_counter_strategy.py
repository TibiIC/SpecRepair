import unittest
from unittest import TestCase

from spec_repair.model.counter_strategy import CounterStrategy
from spec_repair.helpers.parsers.spectra_cs_parser import SpectraCSParser


class TestCounterStrategyCycles(TestCase):
    """
    Counter-strategies aren't always DAGs that bottom out at DEAD: the
    environment can also win by forcing the system into an infinite loop.
    These tests make sure CounterStrategy treats such cycles as first-class,
    terminating, winning plays instead of recursing forever or silently
    dropping them.
    """

    def setUp(self):
        self.parser = SpectraCSParser

    def test_self_loop_after_one_hop_from_initial(self):
        # INI branches into S0 (2 ways), and S0 then loops back onto itself (2 ways).
        cs = self.parser.from_lines(
            ['INI -> S0 {car:true, emergency:false, police:false} / {green:false};',
             'INI -> S0 {car:true, emergency:false, police:false} / {green:true};',
             'S0 -> S0 {car:true, emergency:false, police:false} / {green:false};',
             'S0 -> S0 {car:true, emergency:false, police:false} / {green:true};']
        )

        # No state is a dead end: S0 always has somewhere to go (back to itself).
        self.assertEqual({'INI', 'S0'}, cs.all_states())
        self.assertEqual(set(), cs.sink_states())

        paths = cs.all_paths()
        # 2 choices at INI x 2 choices at S0 = 4 distinct winning plays.
        self.assertEqual(4, len(paths))
        for path in paths:
            # Each path stops the instant the cycle is detected: INI -> S0 -> S0.
            self.assertEqual(2, len(path))
            states = [t.source for t in path] + [path[-1].target]
            self.assertEqual(['INI', 'S0', 'S0'], states)

    def test_self_loop_directly_on_initial_state(self):
        # The environment can also force a loop on the very first state.
        cs = self.parser.from_lines(['INI -> INI {a:true} / {b:false};'])

        self.assertEqual({'INI'}, cs.all_states())
        self.assertEqual(set(), cs.sink_states())

        paths = cs.all_paths()
        self.assertEqual(1, len(paths))
        self.assertEqual(1, len(paths[0]))
        self.assertEqual('INI', paths[0][0].source)
        self.assertEqual('INI', paths[0][0].target)

    def test_self_loop_does_not_blow_the_stack(self):
        # Regression guard: a naive unbounded-depth traversal of a self-loop
        # would recurse forever / blow the stack. This should return quickly.
        cs = self.parser.from_lines(['INI -> INI {a:true} / {b:false};'])
        paths = cs.all_paths()
        self.assertEqual(1, len(paths))

    def test_longer_cycle_not_through_initial_state(self):
        # INI -> S0 -> S1 -> S0 : the cycle is detected two hops in, not at INI.
        cs = self.parser.from_lines([
            'INI -> S0 {a:false} / {b:false};',
            'S0 -> S1 {a:true} / {b:false};',
            'S1 -> S0 {a:false} / {b:true};',
        ])
        paths = cs.all_paths()
        self.assertEqual(1, len(paths))
        path = paths[0]
        self.assertEqual(3, len(path))
        states = [t.source for t in path] + [path[-1].target]
        self.assertEqual(['INI', 'S0', 'S1', 'S0'], states)

    def test_mixed_cycle_and_dead_end_branches(self):
        # From S0, one branch loops back to S0 forever, the other reaches DEAD.
        # Both are valid winning plays and should both be reported.
        cs = self.parser.from_lines([
            'INI -> S0 {a:false} / {b:false};',
            'S0 -> S0 {a:true} / {b:false};',
            'S0 -> DEAD {a:true} / {b:true};',
        ])
        paths = cs.all_paths()
        self.assertEqual(2, len(paths))

        path_targets = [[t.target for t in p] for p in paths]
        self.assertIn(['S0', 'S0'], path_targets)
        self.assertIn(['S0', 'DEAD'], path_targets)

    def test_transitions_from_self_loop_state(self):
        cs = self.parser.from_lines([
            'S0 -> S0 {a:true} / {b:false};',
            'S0 -> S0 {a:true} / {b:true};',
        ])
        froms = cs.transitions_from('S0')
        self.assertEqual(2, len(froms))
        for t in froms:
            self.assertEqual('S0', t.source)
            self.assertEqual('S0', t.target)

    def test_round_trip_preserves_self_loop(self):
        original = ['S0 -> S0 {a:true} / {b:false};']
        cs = self.parser.from_lines(original)
        round_tripped = cs.to_spectra_list()
        reparsed = self.parser.from_lines(round_tripped)

        t = reparsed.transitions[0]
        self.assertEqual('S0', t.source)
        self.assertEqual('S0', t.target)
        self.assertEqual({'a': True}, t.inputs)
        self.assertEqual({'b': False}, t.outputs)

    def test_empty_counter_strategy_has_no_paths(self):
        cs = CounterStrategy(transitions=[])
        self.assertEqual([], cs.all_paths())
        self.assertEqual(set(), cs.all_states())
        self.assertEqual(set(), cs.sink_states())

    def test_repr_and_len_and_iteration(self):
        cs = self.parser.from_lines([
            'INI -> S0 {a:false} / {b:false};',
            'S0 -> S0 {a:true} / {b:false};',
        ])
        self.assertEqual(2, len(cs))
        self.assertEqual(2, len(list(iter(cs))))
        r = repr(cs)
        self.assertIn('winning=loop', r)
        self.assertIn('paths=[INI_S0_S0]', r)
        self.assertNotIn('transitions=', r)

    def test_repr_deadlock(self):
        cs = self.parser.from_lines([
            'INI -> S0 {a:false} / {b:false};',
            'S0 -> DEAD {a:true} / {b:true};',
        ])
        r = repr(cs)
        self.assertIn('winning=deadlock', r)
        self.assertIn('INI_S0_DEAD', r)
        self.assertNotIn('transitions=', r)

    def test_repr_mixed(self):
        cs = self.parser.from_lines([
            'INI -> S0 {a:false} / {b:false};',
            'S0 -> S0 {a:true} / {b:false};',
            'S0 -> DEAD {a:true} / {b:true};',
        ])
        self.assertIn('winning=mixed', repr(cs))

    def test_repr_empty(self):
        from spec_repair.model.counter_strategy import CounterStrategy
        cs = CounterStrategy(transitions=[])
        self.assertIn('winning=unknown', repr(cs))

    def test_winning_condition_loop(self):
        cs = self.parser.from_lines([
            'INI -> S0 {car:true, emergency:false, police:false} / {green:false};',
            'INI -> S0 {car:true, emergency:false, police:false} / {green:true};',
            'S0 -> S0 {car:true, emergency:false, police:false} / {green:false};',
            'S0 -> S0 {car:true, emergency:false, police:false} / {green:true};',
        ])
        self.assertEqual('loop', cs.winning_condition())

    def test_winning_condition_deadlock(self):
        cs = self.parser.from_lines([
            'INI -> S0 {highwater:false, methane:false} / {pump:false};',
            'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
            'S0 -> DEAD {highwater:true, methane:true} / {pump:true};',
        ])
        self.assertEqual('deadlock', cs.winning_condition())


class TestCounterStrategyEquality(TestCase):
    """
    Structural equality: state names are abstracted away, AP names are exact.
    """

    def setUp(self):
        self.parser = SpectraCSParser

    # --- equal cases ---

    def test_equal_to_itself(self):
        cs = self.parser.from_lines([
            'INI -> S0 {highwater:false, methane:false} / {pump:false};',
            'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
            'S0 -> DEAD {highwater:true, methane:true} / {pump:true};',
        ])
        self.assertEqual(cs, cs)

    def test_equal_same_lines_different_objects(self):
        lines = [
            'INI -> S0 {highwater:false, methane:false} / {pump:false};',
            'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
            'S0 -> DEAD {highwater:true, methane:true} / {pump:true};',
        ]
        self.assertEqual(self.parser.from_lines(lines), self.parser.from_lines(lines))

    def test_equal_renamed_states_deadlock(self):
        """INI/S0/DEAD and A/B/C with the same transitions must be equal."""
        cs_original = self.parser.from_lines([
            'INI -> S0 {highwater:false, methane:false} / {pump:false};',
            'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
            'S0 -> DEAD {highwater:true, methane:true} / {pump:true};',
        ])
        from spec_repair.model.counter_strategy import CounterStrategy, CSTransition
        cs_renamed = CounterStrategy([
            CSTransition('A', 'B', {'highwater': False, 'methane': False}, {'pump': False}),
            CSTransition('B', 'C', {'highwater': True, 'methane': True}, {'pump': False}),
            CSTransition('B', 'C', {'highwater': True, 'methane': True}, {'pump': True}),
        ], initial_state='A', dead_state='C')
        self.assertEqual(cs_original, cs_renamed)

    def test_equal_renamed_states_loop(self):
        """Same loop structure under different state names must be equal."""
        cs1 = self.parser.from_lines([
            'INI -> S0 {car:true, emergency:false, police:false} / {green:false};',
            'INI -> S0 {car:true, emergency:false, police:false} / {green:true};',
            'S0 -> S0 {car:true, emergency:false, police:false} / {green:false};',
            'S0 -> S0 {car:true, emergency:false, police:false} / {green:true};',
        ])
        from spec_repair.model.counter_strategy import CounterStrategy, CSTransition
        cs2 = CounterStrategy([
            CSTransition('A', 'B', {'car': True, 'emergency': False, 'police': False}, {'green': False}),
            CSTransition('A', 'B', {'car': True, 'emergency': False, 'police': False}, {'green': True}),
            CSTransition('B', 'B', {'car': True, 'emergency': False, 'police': False}, {'green': False}),
            CSTransition('B', 'B', {'car': True, 'emergency': False, 'police': False}, {'green': True}),
        ], initial_state='A', dead_state='DEAD')
        self.assertEqual(cs1, cs2)

    # --- not-equal cases ---

    def test_not_equal_different_ap_names(self):
        """Abbreviated AP names must not match full names."""
        cs_full = self.parser.from_lines([
            'INI -> S0 {highwater:false, methane:false} / {pump:false};',
            'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
            'S0 -> DEAD {highwater:true, methane:true} / {pump:true};',
        ])
        cs_abbrev = self.parser.from_lines([
            'INI -> S0 {h:false, m:false} / {p:false};',
            'S0 -> DEAD {h:true, m:true} / {p:false};',
            'S0 -> DEAD {h:true, m:true} / {p:true};',
        ])
        self.assertNotEqual(cs_full, cs_abbrev)

    def test_not_equal_different_ap_values(self):
        cs1 = self.parser.from_lines([
            'INI -> S0 {a:false} / {b:false};',
            'S0 -> DEAD {a:true} / {b:false};',
        ])
        cs2 = self.parser.from_lines([
            'INI -> S0 {a:false} / {b:false};',
            'S0 -> DEAD {a:false} / {b:false};',  # a:false instead of true
        ])
        self.assertNotEqual(cs1, cs2)

    def test_not_equal_different_structure(self):
        """One extra intermediate state makes them non-equal."""
        cs_short = self.parser.from_lines([
            'INI -> S0 {highwater:false, methane:false} / {pump:false};',
            'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
            'S0 -> DEAD {highwater:true, methane:true} / {pump:true};',
        ])
        cs_long = self.parser.from_lines([
            'INI -> S0 {highwater:false, methane:false} / {pump:false};',
            'S0 -> S1 {highwater:false, methane:true} / {pump:false};',
            'S0 -> S1 {highwater:false, methane:true} / {pump:true};',
            'S1 -> DEAD {highwater:true, methane:true} / {pump:false};',
        ])
        self.assertNotEqual(cs_short, cs_long)

    def test_not_equal_deadlock_vs_loop(self):
        cs_dead = self.parser.from_lines([
            'INI -> S0 {a:false} / {b:false};',
            'S0 -> DEAD {a:true} / {b:false};',
        ])
        cs_loop = self.parser.from_lines([
            'INI -> S0 {a:false} / {b:false};',
            'S0 -> S0 {a:true} / {b:false};',
        ])
        self.assertNotEqual(cs_dead, cs_loop)

    def test_hashable_and_usable_in_set(self):
        lines = [
            'INI -> S0 {highwater:false, methane:false} / {pump:false};',
            'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
            'S0 -> DEAD {highwater:true, methane:true} / {pump:true};',
        ]
        cs1 = self.parser.from_lines(lines)
        cs2 = self.parser.from_lines(lines)
        # Two equal objects should collapse to one entry in a set.
        self.assertEqual(1, len({cs1, cs2}))


if __name__ == "__main__":
    unittest.main()