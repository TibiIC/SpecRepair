from unittest import TestCase

import pandas as pd
from pandas.util.testing import assert_frame_equal

from spec_repair.enums import When
from spec_repair.util.spec_util import log_line_to_asp_trace, spectra_to_df


class TestLTL(TestCase):
    spec = ['module Minepump\n',
            '\n',
            'env boolean highwater;\n',
            'env boolean methane;\n',
            'sys boolean pump;\n',
            '\n',
            'assumption -- initial_assumption\n',
            '    highwater=false & methane=false;\n',
            '\n',
            'guarantee -- initial_guarantee\n',
            '    pump=false;\n',
            '\n',
            'guarantee -- guarantee1_1\n',
            '\tG(highwater=true->next(pump=true));\n',
            '\n',
            'guarantee -- guarantee2_1\n',
            '\tG(methane=true->next(pump=false));\n',
            '\n',
            'assumption -- assumption1_1\n',
            '\tG(PREV(pump=true)&pump=true->next(highwater=false));\n',
            '\n',
            'assumption -- assumption2_1\n',
            '\tG(highwater=false|methane=false);\n',
            '\n']
    columns = ['type', 'name', 'formula', 'antecedent', 'consequent', 'when']
    formula_list = [['assumption', 'initial_assumption', 'highwater=false&methane=false;', [],
                     ['not_holds_at(current,highwater,0,S),\n\tnot_holds_at(current,methane,0,S)'], When.INITIALLY],
                    ['guarantee', 'initial_guarantee', 'pump=false;', [], ['not_holds_at(current,pump,0,S)'], When.INITIALLY],
                    ['guarantee', 'guarantee1_1', 'G(highwater=true->next(pump=true));', ['holds_at(current,highwater,T,S)'],
                     ['holds_at(next,pump,T,S)'], When.ALWAYS],
                    ['guarantee', 'guarantee2_1', 'G(methane=true->next(pump=false));', ['holds_at(current,methane,T,S)'],
                     ['not_holds_at(next,pump,T,S)'], When.ALWAYS],
                    ['assumption', 'assumption1_1', 'G(PREV(pump=true)&pump=true->next(highwater=false));',
                     ['holds_at(prev,pump,T,S),\n\tholds_at(current,pump,T,S)'], ['not_holds_at(next,highwater,T,S)'],
                     When.ALWAYS],
                    ['assumption', 'assumption2_1', 'G(highwater=false|methane=false);', [],
                     ['not_holds_at(current,highwater,T,S)', 'not_holds_at(current,methane,T,S)'], When.ALWAYS]]

    def test_env_sys_vars_get_ignored(self):
        spec = ['module Minepump\n',
                '\n',
                'env boolean highwater;\n',
                'env boolean methane;\n',
                'sys boolean pump;\n']

        spec_df: pd.DataFrame = spectra_to_df(spec)
        empty_df: pd.DataFrame = pd.DataFrame(columns=self.columns)
        assert_frame_equal(spec_df, empty_df)

    def test_assumptions(self):
        spec = ['assumption -- initial_assumption\n',
                '    highwater=false & methane=false;\n',
                '\n',
                'assumption -- assumption1_1\n',
                '\tG(PREV(pump=true)&pump=true->next(highwater=false));\n',
                '\n',
                'assumption -- assumption2_1\n',
                '\tG(highwater=false|methane=false);\n',
                '\n']

        spec_df: pd.DataFrame = spectra_to_df(spec)
        formula_list: list = [formula for formula in self.formula_list if formula[0] == "assumption"]
        empty_df: pd.DataFrame = pd.DataFrame(formula_list, columns=self.columns)
        assert_frame_equal(spec_df, empty_df)

    def test_guarantees(self):
        spec = ['guarantee -- initial_guarantee\n',
                '    pump=false;\n',
                '\n',
                'guarantee -- guarantee1_1\n',
                '\tG(highwater=true->next(pump=true));\n',
                '\n',
                'guarantee -- guarantee2_1\n',
                '\tG(methane=true->next(pump=false));\n',
                '\n']

        spec_df: pd.DataFrame = spectra_to_df(spec)
        formula_list: list = [formula for formula in self.formula_list if formula[0] == "guarantee"]
        empty_df: pd.DataFrame = pd.DataFrame(formula_list, columns=self.columns)
        assert_frame_equal(spec_df, empty_df)

    def test_pRespondsToS(self):
        # TODO: ask Titus to give you an example for this
        self.fail()


class TestTrace(TestCase):
    def test_log_line_to_asp_trace_baseline(self):
        log_line = "<highwater:false, methane:false, pump:false, PREV_aux_0:false, Zn:0>"
        asp_trace = log_line_to_asp_trace(log_line)
        expected_asp_trace = "not_holds_at(current,highwater,0,trace_name_0).\n" \
                             "not_holds_at(current,methane,0,trace_name_0).\n" \
                             "not_holds_at(current,pump,0,trace_name_0).\n"
        self.assertEqual(asp_trace, expected_asp_trace)

    def test_log_line_to_asp_trace_varying(self):
        log_line = "<highwater:false, methane:true, pump:false, Zn:0>"
        asp_trace = log_line_to_asp_trace(log_line)
        expected_asp_trace = "not_holds_at(current,highwater,0,trace_name_0).\n" \
                             "holds_at(current,methane,0,trace_name_0).\n" \
                             "not_holds_at(current,pump,0,trace_name_0).\n"
        self.assertEqual(asp_trace, expected_asp_trace)

        log_line = "<highwater:true, methane:false, pump:true, Zn:0>"
        asp_trace = log_line_to_asp_trace(log_line, 1)
        expected_asp_trace = "holds_at(current,highwater,1,trace_name_0).\n" \
                             "not_holds_at(current,methane,1,trace_name_0).\n" \
                             "holds_at(current,pump,1,trace_name_0).\n"
        self.assertEqual(asp_trace, expected_asp_trace)

    def test_log_line_to_asp_trace_name_change(self):
        log_line = "<highwater:false, methane:true, pump:false, Zn:0>"
        asp_trace = log_line_to_asp_trace(log_line, trace_name="other_name_42")
        expected_asp_trace = "not_holds_at(current,highwater,0,other_name_42).\n" \
                             "holds_at(current,methane,0,other_name_42).\n" \
                             "not_holds_at(current,pump,0,other_name_42).\n"
        self.assertEqual(asp_trace, expected_asp_trace)
