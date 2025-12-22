import os
from functools import partial

from spec_repair.helpers.counter_trace import CounterTrace, ct_from_cs, complete_cts_from_ct
from spec_repair.enums import Learning
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.heuristics import first_choice, last_choice, nth_choice
from spec_repair.ltl_types import CounterStrategy
from tests.base_test_case import BaseTestCase

cs1: CounterStrategy = \
    ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
     'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
     'S0 -> DEAD {highwater:true, methane:true} / {pump:true};']

cs1_1_raw_trace = """\
not_holds_at(highwater,0,ini_S0_DEAD).
not_holds_at(methane,0,ini_S0_DEAD).
not_holds_at(pump,0,ini_S0_DEAD).
holds_at(highwater,1,ini_S0_DEAD).
holds_at(methane,1,ini_S0_DEAD).
holds_at(pump,1,ini_S0_DEAD).
"""

cs1_2_raw_trace = """\
not_holds_at(highwater,0,ini_S0_DEAD).
not_holds_at(methane,0,ini_S0_DEAD).
not_holds_at(pump,0,ini_S0_DEAD).
holds_at(highwater,1,ini_S0_DEAD).
holds_at(methane,1,ini_S0_DEAD).
not_holds_at(pump,1,ini_S0_DEAD).
"""

cs2: CounterStrategy = \
    ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
     'S0 -> S1 {highwater:false, methane:true} / {pump:false};',
     'S0 -> S1 {highwater:false, methane:true} / {pump:true};',
     'S1 -> DEAD {highwater:true, methane:true} / {pump:false};']

cs2_1_raw_trace = """\
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

cs3: CounterStrategy = \
    ['INI -> S0 {car:true, emergency:false, police:false} / {green:false};',
     'INI -> S0 {car:true, emergency:false, police:false} / {green:true};',
     'S0 -> S0 {car:true, emergency:false, police:false} / {green:false};',
     'S0 -> S0 {car:true, emergency:false, police:false} / {green:true};']

cs3_1_raw_trace = """\
holds_at(car,0,ini_S0_S0).
not_holds_at(emergency,0,ini_S0_S0).
not_holds_at(police,0,ini_S0_S0).
not_holds_at(green,0,ini_S0_S0).
holds_at(car,1,ini_S0_S0).
not_holds_at(emergency,1,ini_S0_S0).
not_holds_at(police,1,ini_S0_S0).
not_holds_at(green,1,ini_S0_S0).
"""

cs3_2_raw_trace = """\
holds_at(car,0,ini_S0_S0).
not_holds_at(emergency,0,ini_S0_S0).
not_holds_at(police,0,ini_S0_S0).
holds_at(green,0,ini_S0_S0).
holds_at(car,1,ini_S0_S0).
not_holds_at(emergency,1,ini_S0_S0).
not_holds_at(police,1,ini_S0_S0).
holds_at(green,1,ini_S0_S0).
"""

cs3_3_raw_trace = """\
holds_at(car,0,ini_S0_S0_S0).
not_holds_at(emergency,0,ini_S0_S0_S0).
not_holds_at(police,0,ini_S0_S0_S0).
holds_at(green,0,ini_S0_S0_S0).
holds_at(car,1,ini_S0_S0_S0).
not_holds_at(emergency,1,ini_S0_S0_S0).
not_holds_at(police,1,ini_S0_S0_S0).
holds_at(green,1,ini_S0_S0_S0).
holds_at(car,2,ini_S0_S0_S0).
not_holds_at(emergency,2,ini_S0_S0_S0).
not_holds_at(police,2,ini_S0_S0_S0).
not_holds_at(green,2,ini_S0_S0_S0).
"""


class TestCounterTrace(BaseTestCase):
    maxDiff = None

    def test_get_raw_form_1(self):
        ct = ct_from_cs(cs1, heuristic=first_choice)
        self.assertEqual(cs1_1_raw_trace, ct.get_raw_trace())
        self.assertEqual("ini_S0_DEAD", ct._path)

    def test_get_raw_form_2(self):
        ct = ct_from_cs(cs1, heuristic=last_choice)
        self.assertEqual(cs1_2_raw_trace, ct.get_raw_trace())
        self.assertEqual("ini_S0_DEAD", ct._path)

    def test_get_raw_form_3(self):
        ct = ct_from_cs(cs2, heuristic=first_choice)
        self.assertEqual(cs2_1_raw_trace, ct.get_raw_trace())
        self.assertEqual("ini_S0_S1_DEAD", ct._path)

    def test_get_raw_form_cycle(self):
        ct = ct_from_cs(cs3, heuristic=first_choice)
        self.assertEqual(cs3_1_raw_trace, ct.get_raw_trace())
        self.assertEqual("ini_S0_S0", ct._path)

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
        self.assertEqual(expected_ct_raw, ct.get_raw_trace())
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
        self.assertEqual(expected_ct_raw, ct.get_raw_trace())
        self.assertEqual("ini_S0_S1_DEAD", ct._path)
        self.assertEqual("counter_strat_1_1", ct._name)

    def test_get_asp_form_1(self):
        ct = ct_from_cs(cs1, heuristic=first_choice, cs_id=0)
        expected_ct_asp = """\
%---*** Violation Trace ***---

% CS_Path: ini_S0_DEAD

trace(counter_strat_0_0).

timepoint(0,counter_strat_0_0).
timepoint(1,counter_strat_0_0).
weak_timepoint(weak_t,counter_strat_0_0).
next(1,0,counter_strat_0_0).
next(weak_t,1,counter_strat_0_0).

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

% CS_Path: ini_S0_S1_DEAD

trace(counter_strat_1_0).

timepoint(0,counter_strat_1_0).
timepoint(1,counter_strat_1_0).
timepoint(2,counter_strat_1_0).
weak_timepoint(weak_t,counter_strat_1_0).
next(1,0,counter_strat_1_0).
next(2,1,counter_strat_1_0).
next(weak_t,2,counter_strat_1_0).

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
weak_timepoint(weak_t,counter_strat_0_0).
next(1,0,counter_strat_0_0).
next(weak_t,1,counter_strat_0_0).
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
weak_timepoint(weak_t,counter_strat_1_0).
next(1,0,counter_strat_1_0).
next(2,1,counter_strat_1_0).
next(weak_t,2,counter_strat_1_0).
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

    def test_ct_deadlock_completion(self):
        print(os.getcwd())
        ct = ct_from_cs(cs1, heuristic=first_choice, cs_id=0)
        spec: SpectraSpecification = SpectraSpecification.from_file(
            './test_files/minepump_aw_methane.spectra')
        ct = complete_cts_from_ct(ct, spec, ["counter_strat_0_0"])[0]
        expected_ct_raw = """\
not_holds_at(highwater,0,counter_strat_0_0).
not_holds_at(methane,0,counter_strat_0_0).
not_holds_at(pump,0,counter_strat_0_0).
holds_at(highwater,1,counter_strat_0_0).
holds_at(methane,1,counter_strat_0_0).
holds_at(pump,1,counter_strat_0_0).
not_holds_at(pump,2,counter_strat_0_0).
holds_at(highwater,2,counter_strat_0_0).
holds_at(methane,2,counter_strat_0_0).\
"""
        self.assertEqual(expected_ct_raw, ct.get_raw_trace())

    def test_ct_deadlock_completion_2(self):
        ct = ct_from_cs(cs2, heuristic=partial(nth_choice, 1), cs_id=1)
        spec: SpectraSpecification = SpectraSpecification.from_file(
            './test_files/minepump_aw_pump.spectra')
        ct = complete_cts_from_ct(ct, spec, ["counter_strat_1_1"])[0]
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
not_holds_at(pump,3,counter_strat_1_1).
holds_at(highwater,3,counter_strat_1_1).
holds_at(methane,3,counter_strat_1_1).\
"""
        self.assertEqual(expected_ct_raw, ct.get_raw_trace())

    def test_ct_deadlock_completion_asp(self):
        ct = ct_from_cs(cs1, heuristic=first_choice, cs_id=0)
        spec: SpectraSpecification = SpectraSpecification.from_file(
            './test_files/minepump_aw_methane.spectra')
        ct = complete_cts_from_ct(ct, spec, ["counter_strat_0_0"])[0]
        expected_ct_asp = """\
%---*** Violation Trace ***---

% CS_Path: ini_S0_DEAD

trace(counter_strat_0_0).

timepoint(0,counter_strat_0_0).
timepoint(1,counter_strat_0_0).
timepoint(2,counter_strat_0_0).
weak_timepoint(weak_t,counter_strat_0_0).
next(1,0,counter_strat_0_0).
next(2,1,counter_strat_0_0).
next(weak_t,2,counter_strat_0_0).

not_holds_at(highwater,0,counter_strat_0_0).
not_holds_at(methane,0,counter_strat_0_0).
not_holds_at(pump,0,counter_strat_0_0).
holds_at(highwater,1,counter_strat_0_0).
holds_at(methane,1,counter_strat_0_0).
holds_at(pump,1,counter_strat_0_0).
not_holds_at(pump,2,counter_strat_0_0).
holds_at(highwater,2,counter_strat_0_0).
holds_at(methane,2,counter_strat_0_0).
"""
        self.assertEqual(expected_ct_asp, ct.get_asp_form())

    def test_ct_deadlock_completion_asp_2(self):
        ct = ct_from_cs(cs2, heuristic=partial(nth_choice, 1), cs_id=1)
        spec: SpectraSpecification = SpectraSpecification.from_file(
            './test_files/minepump_aw_pump.spectra')
        ct = complete_cts_from_ct(ct, spec, ["counter_strat_1_1"])[0]
        expected_ct_asp = """\
%---*** Violation Trace ***---

% CS_Path: ini_S0_S1_DEAD

trace(counter_strat_1_1).

timepoint(0,counter_strat_1_1).
timepoint(1,counter_strat_1_1).
timepoint(2,counter_strat_1_1).
timepoint(3,counter_strat_1_1).
weak_timepoint(weak_t,counter_strat_1_1).
next(1,0,counter_strat_1_1).
next(2,1,counter_strat_1_1).
next(3,2,counter_strat_1_1).
next(weak_t,3,counter_strat_1_1).

not_holds_at(highwater,0,counter_strat_1_1).
not_holds_at(methane,0,counter_strat_1_1).
not_holds_at(pump,0,counter_strat_1_1).
not_holds_at(highwater,1,counter_strat_1_1).
holds_at(methane,1,counter_strat_1_1).
not_holds_at(pump,1,counter_strat_1_1).
holds_at(highwater,2,counter_strat_1_1).
holds_at(methane,2,counter_strat_1_1).
not_holds_at(pump,2,counter_strat_1_1).
not_holds_at(pump,3,counter_strat_1_1).
holds_at(highwater,3,counter_strat_1_1).
holds_at(methane,3,counter_strat_1_1).
"""
        self.assertEqual(expected_ct_asp, ct.get_asp_form())

    def test_ct_equality(self):
        ct1 = CounterTrace(cs1_1_raw_trace, "ini_S0_DEAD", "counter_strat_0_0")
        ct2 = CounterTrace(cs1_1_raw_trace, "ini_S0_DEAD", "counter_strat_1_2")
        self.assertEqual(ct1, ct2)

    def test_ct_equality_2(self):
        ct1 = CounterTrace(cs2_1_raw_trace, "ini_S0_S1_DEAD", "counter_strat_0_1")
        ct2 = CounterTrace(cs2_1_raw_trace, "ini_S0_S1_DEAD", "counter_strat_1_1")
        self.assertEqual(ct1, ct2)

    def test_ct_inequality(self):
        """
        CounterTraces are not equal if and only if their raw traces are different
        """
        ct1 = CounterTrace(cs1_1_raw_trace, "ini_S0_DEAD", "counter_strat_0_0")
        ct2 = CounterTrace(cs1_2_raw_trace, "ini_S0_DEAD", "counter_strat_0_0")
        self.assertNotEqual(ct1, ct2)
