from unittest import TestCase

from spec_repair.ltl_types import CounterStrategy
from spec_repair.util.spec_util import cs_to_named_cs_traces


class Test(TestCase):
    def test_cs_to_named_cs_traces_1(self):
        cs: CounterStrategy = \
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:true};']
        ct_list: dict[str, str] = cs_to_named_cs_traces(cs)
        ct_list_expected = {
            'not_holds_at(highwater,0,ini_S0_DEAD).\nnot_holds_at(methane,0,ini_S0_DEAD).\nnot_holds_at(pump,0,ini_S0_DEAD).\nholds_at(highwater,1,ini_S0_DEAD).\nholds_at(methane,1,ini_S0_DEAD).\nholds_at(pump,1,ini_S0_DEAD).\n': 'ini_S0_DEAD',
            'not_holds_at(highwater,0,ini_S0_DEAD).\nnot_holds_at(methane,0,ini_S0_DEAD).\nnot_holds_at(pump,0,ini_S0_DEAD).\nholds_at(highwater,1,ini_S0_DEAD).\nholds_at(methane,1,ini_S0_DEAD).\nnot_holds_at(pump,1,ini_S0_DEAD).\n': 'ini_S0_DEAD'
        }
        self.assertEqual(ct_list_expected, ct_list)

    def test_cs_to_named_cs_traces_2(self):
        cs: CounterStrategy = \
            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> S1 {highwater:false, methane:true} / {pump:false};',
             'S0 -> S1 {highwater:false, methane:true} / {pump:true};',
             'S1 -> DEAD {highwater:true, methane:true} / {pump:false};']
        ct_dict: dict[str, str] = cs_to_named_cs_traces(cs)
        ct_dict_expected = {
            'not_holds_at(highwater,0,ini_S0_S1_DEAD).\nnot_holds_at(methane,0,ini_S0_S1_DEAD).\nnot_holds_at(pump,0,ini_S0_S1_DEAD).\nnot_holds_at(highwater,1,ini_S0_S1_DEAD).\nholds_at(methane,1,ini_S0_S1_DEAD).\nholds_at(pump,1,ini_S0_S1_DEAD).\nholds_at(highwater,2,ini_S0_S1_DEAD).\nholds_at(methane,2,ini_S0_S1_DEAD).\nnot_holds_at(pump,2,ini_S0_S1_DEAD).\n': 'ini_S0_S1_DEAD',
            'not_holds_at(highwater,0,ini_S0_S1_DEAD).\nnot_holds_at(methane,0,ini_S0_S1_DEAD).\nnot_holds_at(pump,0,ini_S0_S1_DEAD).\nnot_holds_at(highwater,1,ini_S0_S1_DEAD).\nholds_at(methane,1,ini_S0_S1_DEAD).\nnot_holds_at(pump,1,ini_S0_S1_DEAD).\nholds_at(highwater,2,ini_S0_S1_DEAD).\nholds_at(methane,2,ini_S0_S1_DEAD).\nnot_holds_at(pump,2,ini_S0_S1_DEAD).\n': 'ini_S0_S1_DEAD'
        }

        self.assertEqual(ct_dict_expected, ct_dict)
