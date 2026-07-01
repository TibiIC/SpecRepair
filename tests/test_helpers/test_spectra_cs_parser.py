import unittest
from unittest import TestCase

from spec_repair.helpers.parsers.spectra_cs_parser import SpectraCSParser


class TestSpectraCSParser(TestCase):
    """Tests that validate the parsing of the Spectra CLI counter-strategy format is sound."""

    def setUp(self):
        self.parser = SpectraCSParser

    def test_parses_single_transition(self):
        cs = self.parser.from_lines(
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};']
        )
        self.assertEqual(1, len(cs))
        t = cs.transitions[0]
        self.assertEqual('INI', t.source)
        self.assertEqual('S0', t.target)
        self.assertEqual({'highwater': False, 'methane': False}, t.inputs)
        self.assertEqual({'pump': False}, t.outputs)

    def test_parses_true_and_false_values(self):
        cs = self.parser.from_lines(
            ['S0 -> DEAD {highwater:true, methane:false} / {pump:true};']
        )
        t = cs.transitions[0]
        self.assertEqual({'highwater': True, 'methane': False}, t.inputs)
        self.assertEqual({'pump': True}, t.outputs)

    def test_multiple_transitions_from_same_source_share_inputs(self):
        cs = self.parser.from_lines([
            'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
            'S0 -> DEAD {highwater:true, methane:true} / {pump:true};',
        ])
        froms = cs.transitions_from('S0')
        self.assertEqual(2, len(froms))
        self.assertEqual(froms[0].inputs, froms[1].inputs)
        self.assertNotEqual(froms[0].outputs, froms[1].outputs)

    def test_from_str_splits_on_lines(self):
        text = (
            "Some banner text from spectra-cli\n"
            "INI -> S0 {a:false} / {b:false};\n"
            "S0 -> DEAD {a:true} / {b:true};\n"
            "Footer text\n"
        )
        cs = self.parser.from_str(text)
        self.assertEqual(2, len(cs))
        self.assertEqual({'INI', 'S0', 'DEAD'}, cs.all_states())

    def test_ignores_non_matching_lines(self):
        cs = self.parser.from_lines([
            'This is not a transition',
            '',
            'INI -> S0 {a:false} / {b:false};',
            '# a comment',
        ])
        self.assertEqual(1, len(cs))

    def test_round_trip_to_spectra_list(self):
        original = ['INI -> S0 {a:false, b:true} / {c:false};']
        cs = self.parser.from_lines(original)
        round_tripped = cs.to_spectra_list()
        self.assertEqual(1, len(round_tripped))
        # Re-parsing the round-tripped string should yield the same transition data.
        reparsed = self.parser.from_lines(round_tripped)
        self.assertEqual(cs.transitions[0].inputs, reparsed.transitions[0].inputs)
        self.assertEqual(cs.transitions[0].outputs, reparsed.transitions[0].outputs)

    def test_all_states_and_sink_states(self):
        cs = self.parser.from_lines([
            'INI -> S0 {a:false} / {b:false};',
            'S0 -> DEAD {a:true} / {b:true};',
        ])
        self.assertEqual({'INI', 'S0', 'DEAD'}, cs.all_states())
        self.assertEqual({'DEAD'}, cs.sink_states())

    def test_parses_self_loop_transition(self):
        """A transition whose source and target are the same state (an
        infinite-loop counter-strategy) must parse just like any other edge."""
        cs = self.parser.from_lines(
            ['S0 -> S0 {car:true, emergency:false, police:false} / {green:false};']
        )
        self.assertEqual(1, len(cs))
        t = cs.transitions[0]
        self.assertEqual('S0', t.source)
        self.assertEqual('S0', t.target)
        self.assertEqual({'car': True, 'emergency': False, 'police': False}, t.inputs)
        self.assertEqual({'green': False}, t.outputs)

    def test_self_loop_state_is_not_a_sink(self):
        """A state that only loops back to itself still has an outgoing
        transition, so it must not be reported as a sink state."""
        cs = self.parser.from_lines([
            'INI -> S0 {a:true} / {b:false};',
            'S0 -> S0 {a:true} / {b:false};',
        ])
        self.assertEqual({'INI', 'S0'}, cs.all_states())
        self.assertEqual(set(), cs.sink_states())

    def test_multiple_self_loop_transitions_share_inputs(self):
        """Same shared-inputs invariant should hold even when the transitions
        in question are self-loops."""
        cs = self.parser.from_lines([
            'S0 -> S0 {a:true, b:false} / {c:false};',
            'S0 -> S0 {a:true, b:false} / {c:true};',
        ])
        froms = cs.transitions_from('S0')
        self.assertEqual(2, len(froms))
        self.assertTrue(all(t.source == 'S0' and t.target == 'S0' for t in froms))
        self.assertEqual(froms[0].inputs, froms[1].inputs)
        self.assertNotEqual(froms[0].outputs, froms[1].outputs)


if __name__ == "__main__":
    unittest.main()