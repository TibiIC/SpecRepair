from functools import partial
from unittest import TestCase

from spec_repair.components.counter_trace import CounterTrace, ct_from_cs
from spec_repair.enums import Learning
from spec_repair.heuristics import first_choice, last_choice, nth_choice
from spec_repair.ltl import CounterStrategy

cs1: CounterStrategy = \
    ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
     'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
     'S0 -> DEAD {highwater:true, methane:true} / {pump:true};']

cs2: CounterStrategy = \
    ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
     'S0 -> S1 {highwater:false, methane:true} / {pump:false};',
     'S0 -> S1 {highwater:false, methane:true} / {pump:true};',
     'S1 -> DEAD {highwater:true, methane:true} / {pump:false};']


class TestCounterTrace(TestCase):
    def test_get_raw_form_1(self):
        ct = ct_from_cs(cs1, heuristic=first_choice)
        expected_ct_raw = """\
not_holds_at(highwater,0,ini_S0_DEAD).
not_holds_at(methane,0,ini_S0_DEAD).
not_holds_at(pump,0,ini_S0_DEAD).
holds_at(highwater,1,ini_S0_DEAD).
holds_at(methane,1,ini_S0_DEAD).
holds_at(pump,1,ini_S0_DEAD).
"""
        self.assertEqual(expected_ct_raw, ct._raw_trace)
        self.assertEqual("ini_S0_DEAD", ct._path)

    def test_get_raw_form_2(self):
        ct = ct_from_cs(cs1, heuristic=last_choice)
        expected_ct_raw = """\
not_holds_at(highwater,0,ini_S0_DEAD).
not_holds_at(methane,0,ini_S0_DEAD).
not_holds_at(pump,0,ini_S0_DEAD).
holds_at(highwater,1,ini_S0_DEAD).
holds_at(methane,1,ini_S0_DEAD).
not_holds_at(pump,1,ini_S0_DEAD).
"""
        self.assertEqual(expected_ct_raw, ct._raw_trace)
        self.assertEqual("ini_S0_DEAD", ct._path)

    def test_get_raw_form_3(self):
        ct = ct_from_cs(cs2, heuristic=first_choice)
        expected_ct_raw = """\
not_holds_at(highwater,0,ini_S0_S1_DEAD).
not_holds_at(methane,0,ini_S0_S1_DEAD).
not_holds_at(pump,0,ini_S0_S1_DEAD).
not_holds_at(highwater,1,ini_S0_S1_DEAD).
holds_at(methane,1,ini_S0_S1_DEAD).
holds_at(pump,1,ini_S0_S1_DEAD).
holds_at(highwater,2,ini_S0_S1_DEAD).
holds_at(methane,2,ini_S0_S1_DEAD).
not_holds_at(pump,2,ini_S0_S1_DEAD).
"""
        self.assertEqual(expected_ct_raw, ct._raw_trace)
        self.assertEqual("ini_S0_S1_DEAD", ct._path)

    def test_get_named_form_1(self):
        ct = ct_from_cs(cs1, heuristic=first_choice, cs_id=0)
        expected_ct_raw = """\
not_holds_at(highwater,0,counter_strat_0_0).
not_holds_at(methane,0,counter_strat_0_0).
not_holds_at(pump,0,counter_strat_0_0).
holds_at(highwater,1,counter_strat_0_0).
holds_at(methane,1,counter_strat_0_0).
holds_at(pump,1,counter_strat_0_0).
"""
        self.assertEqual(expected_ct_raw, ct._raw_trace)
        self.assertEqual("ini_S0_DEAD", ct._path)
        self.assertEqual("counter_strat_0_0", ct._name)

    def test_get_named_form_2(self):
        ct = ct_from_cs(cs2, heuristic=partial(nth_choice, 1), cs_id=1)
        expected_ct_raw = """\
not_holds_at(highwater,0,counter_strat_1_1).
not_holds_at(methane,0,counter_strat_1_1).
not_holds_at(pump,0,counter_strat_1_1).
not_holds_at(highwater,1,counter_strat_1_1).
holds_at(methane,1,counter_strat_1_1).
not_holds_at(pump,1,counter_strat_1_1).
holds_at(highwater,2,counter_strat_1_1).
holds_at(methane,2,counter_strat_1_1).
not_holds_at(pump,2,counter_strat_1_1).
"""
        self.assertEqual(expected_ct_raw, ct._raw_trace)
        self.assertEqual("ini_S0_S1_DEAD", ct._path)
        self.assertEqual("counter_strat_1_1", ct._name)

    def test_get_asp_form_1(self):
        ct = ct_from_cs(cs1, heuristic=first_choice, cs_id=0)
        expected_ct_asp = """\
%---*** Violation Trace ***---

trace(counter_strat_0_0).

timepoint(0,counter_strat_0_0).
timepoint(1,counter_strat_0_0).
next(1,0,counter_strat_0_0).

not_holds_at(highwater,0,counter_strat_0_0).
not_holds_at(methane,0,counter_strat_0_0).
not_holds_at(pump,0,counter_strat_0_0).
holds_at(highwater,1,counter_strat_0_0).
holds_at(methane,1,counter_strat_0_0).
holds_at(pump,1,counter_strat_0_0).
"""
        self.assertEqual(expected_ct_asp, ct.get_asp_form())

    def test_get_asp_form_2(self):
        ct = ct_from_cs(cs2, heuristic=first_choice, cs_id=1)
        expected_ct_asp = """\
%---*** Violation Trace ***---

trace(counter_strat_1_0).

timepoint(0,counter_strat_1_0).
timepoint(1,counter_strat_1_0).
timepoint(2,counter_strat_1_0).
next(1,0,counter_strat_1_0).
next(2,1,counter_strat_1_0).

not_holds_at(highwater,0,counter_strat_1_0).
not_holds_at(methane,0,counter_strat_1_0).
not_holds_at(pump,0,counter_strat_1_0).
not_holds_at(highwater,1,counter_strat_1_0).
holds_at(methane,1,counter_strat_1_0).
holds_at(pump,1,counter_strat_1_0).
holds_at(highwater,2,counter_strat_1_0).
holds_at(methane,2,counter_strat_1_0).
not_holds_at(pump,2,counter_strat_1_0).
"""
        self.assertEqual(expected_ct_asp, ct.get_asp_form())

    def test_get_ilasp_form_1(self):
        ct = ct_from_cs(cs1, heuristic=first_choice, cs_id=0)
        expected_ct_ilasp = """\
%---*** Violation Trace ***---

#pos({},{entailed(counter_strat_0_0)},{

% CS_Path: ini_S0_DEAD

trace(counter_strat_0_0).
timepoint(0,counter_strat_0_0).
timepoint(1,counter_strat_0_0).
next(1,0,counter_strat_0_0).
not_holds_at(highwater,0,counter_strat_0_0).
not_holds_at(methane,0,counter_strat_0_0).
not_holds_at(pump,0,counter_strat_0_0).
holds_at(highwater,1,counter_strat_0_0).
holds_at(methane,1,counter_strat_0_0).
holds_at(pump,1,counter_strat_0_0).
}).
"""
        self.assertEqual(expected_ct_ilasp, ct.get_ilasp_form(learning=Learning.ASSUMPTION_WEAKENING))

    def test_get_ilasp_form_2(self):
        ct = ct_from_cs(cs2, heuristic=first_choice, cs_id=1)
        expected_ct_ilasp = """\
%---*** Violation Trace ***---

#pos({},{entailed(counter_strat_1_0)},{

% CS_Path: ini_S0_S1_DEAD

trace(counter_strat_1_0).
timepoint(0,counter_strat_1_0).
timepoint(1,counter_strat_1_0).
timepoint(2,counter_strat_1_0).
next(1,0,counter_strat_1_0).
next(2,1,counter_strat_1_0).
not_holds_at(highwater,0,counter_strat_1_0).
not_holds_at(methane,0,counter_strat_1_0).
not_holds_at(pump,0,counter_strat_1_0).
not_holds_at(highwater,1,counter_strat_1_0).
holds_at(methane,1,counter_strat_1_0).
holds_at(pump,1,counter_strat_1_0).
holds_at(highwater,2,counter_strat_1_0).
holds_at(methane,2,counter_strat_1_0).
not_holds_at(pump,2,counter_strat_1_0).
}).
"""
        self.assertEqual(expected_ct_ilasp, ct.get_ilasp_form(learning=Learning.ASSUMPTION_WEAKENING))
