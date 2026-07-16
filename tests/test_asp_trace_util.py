import unittest
from unittest import TestCase

from spec_repair.model.counter_trace import cs_to_named_cs_traces
from spec_repair.helpers.parsers.spectra_cs_parser import SpectraCSParser


class Test(TestCase):
    def setUp(self):
        self.parser = SpectraCSParser

    def test_cs_to_named_cs_traces_1(self):
        self.cs_lines: list[str] = \
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:true};']
        cs = self.parser.from_lines(self.cs_lines)
        ct_list: dict[str, str] = cs_to_named_cs_traces(cs)
        ct_list_expected = {
            'not_holds_at(highwater,0,ini_S0_DEAD).\nnot_holds_at(methane,0,ini_S0_DEAD).\nnot_holds_at(pump,0,ini_S0_DEAD).\nholds_at(highwater,1,ini_S0_DEAD).\nholds_at(methane,1,ini_S0_DEAD).\nholds_at(pump,1,ini_S0_DEAD).\n': 'ini_S0_DEAD',
            'not_holds_at(highwater,0,ini_S0_DEAD).\nnot_holds_at(methane,0,ini_S0_DEAD).\nnot_holds_at(pump,0,ini_S0_DEAD).\nholds_at(highwater,1,ini_S0_DEAD).\nholds_at(methane,1,ini_S0_DEAD).\nnot_holds_at(pump,1,ini_S0_DEAD).\n': 'ini_S0_DEAD'
        }
        self.assertEqual(ct_list_expected, ct_list)

    def test_cs_to_named_cs_traces_2(self):
        cs_lines: list[str] = \
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> S1 {highwater:false, methane:true} / {pump:false};',
             'S0 -> S1 {highwater:false, methane:true} / {pump:true};',
             'S1 -> DEAD {highwater:true, methane:true} / {pump:false};']
        cs = self.parser.from_lines(cs_lines)
        ct_dict: dict[str, str] = cs_to_named_cs_traces(cs)
        ct_dict_expected = {
            'not_holds_at(highwater,0,ini_S0_S1_DEAD).\nnot_holds_at(methane,0,ini_S0_S1_DEAD).\nnot_holds_at(pump,0,ini_S0_S1_DEAD).\nnot_holds_at(highwater,1,ini_S0_S1_DEAD).\nholds_at(methane,1,ini_S0_S1_DEAD).\nholds_at(pump,1,ini_S0_S1_DEAD).\nholds_at(highwater,2,ini_S0_S1_DEAD).\nholds_at(methane,2,ini_S0_S1_DEAD).\nnot_holds_at(pump,2,ini_S0_S1_DEAD).\n': 'ini_S0_S1_DEAD',
            'not_holds_at(highwater,0,ini_S0_S1_DEAD).\nnot_holds_at(methane,0,ini_S0_S1_DEAD).\nnot_holds_at(pump,0,ini_S0_S1_DEAD).\nnot_holds_at(highwater,1,ini_S0_S1_DEAD).\nholds_at(methane,1,ini_S0_S1_DEAD).\nnot_holds_at(pump,1,ini_S0_S1_DEAD).\nholds_at(highwater,2,ini_S0_S1_DEAD).\nholds_at(methane,2,ini_S0_S1_DEAD).\nnot_holds_at(pump,2,ini_S0_S1_DEAD).\n': 'ini_S0_S1_DEAD'
        }

        self.assertEqual(ct_dict_expected, ct_dict)

    def test_cs_to_named_cs_traces_branching_at_root(self):
        """Two distinct branches straight off INI should produce two distinct named traces."""
        cs_lines = [
            'INI -> S0 {a:false} / {b:false};',
            'INI -> S1 {a:true} / {b:true};',
            'S0 -> DEAD {a:true} / {b:false};',
            'S1 -> DEAD {a:false} / {b:true};',
        ]
        cs = self.parser.from_lines(cs_lines)
        ct_dict = cs_to_named_cs_traces(cs)
        names = set(ct_dict.values())
        self.assertEqual({'ini_S0_DEAD', 'ini_S1_DEAD'}, names)
        self.assertEqual(2, len(ct_dict))

    def test_cs_to_named_cs_traces_cycle_terminates(self):
        """A self-looping (non-DEAD) cycle should still terminate trace extraction instead of recursing forever."""
        cs_lines = [
            'INI -> S0 {a:false} / {b:false};',
            'S0 -> S1 {a:true} / {b:false};',
            'S1 -> S0 {a:false} / {b:true};',
        ]
        cs = self.parser.from_lines(cs_lines)
        ct_dict = cs_to_named_cs_traces(cs)
        # Path INI -> S0 -> S1 -> S0 detects the repeated S0 and stops.
        self.assertEqual(['ini_S0_S1_S0'], list(ct_dict.values()))
        trace = list(ct_dict.keys())[0]
        # Three timepoints (0, 1, 2) should appear before the cycle is cut off.
        self.assertIn(',0,', trace)
        self.assertIn(',1,', trace)
        self.assertIn(',2,', trace)
        self.assertNotIn(',3,', trace)


if __name__ == "__main__":
    unittest.main()
