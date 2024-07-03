import re
from unittest import TestCase

import pandas as pd

from spec_repair.enums import Learning
from spec_repair.util.spec_util import create_signature, extract_variables, create_trace, \
    get_assumptions_and_guarantees_from, trace_list_to_asp_form, trace_list_to_ilasp_form


def is_ascending(timepoint_poss: list[int]) -> bool:
    return all([(timepoint_poss[k + 1] - timepoint_poss[k]) > 0 for k in range(len(timepoint_poss) - 1)])


class TestSpec(TestCase):
    minepump_spec_file = '../../input-files/examples/Minepump/minepump_strong.spectra'
    traffic_spec_file = '../test_files/traffic/traffic_single_strong.spectra'
    traffic_updated_spec_file = '../test_files/traffic/traffic_updated_strong.spectra'

    def test_extract_variables(self):
        spec_df: pd.DataFrame = get_assumptions_and_guarantees_from(self.minepump_spec_file)
        variables = extract_variables(spec_df)
        self.assertListEqual(["highwater", "methane", "pump"], variables)

    def test_create_signature_methane(self):
        spec_df: pd.DataFrame = get_assumptions_and_guarantees_from(self.minepump_spec_file)
        signature: str = create_signature(spec_df)
        header_pattern: re.Pattern = re.compile(r"^%-{3}\*{3}\s*Signature\s*\*{3}-{3}$", flags=re.MULTILINE)
        self.assertRegex(signature, header_pattern)
        header_pos = header_pattern.search(signature).end()
        for var in ["highwater", "methane", "pump"]:
            atom_pattern = re.compile(rf"^atom\({var}\).$", flags=re.MULTILINE)
            self.assertRegex(signature, atom_pattern)
            atom_pos = atom_pattern.search(signature).start()
            self.assertLess(header_pos, atom_pos)

    def test_create_signature_traffic_single(self):
        spec_df: pd.DataFrame = get_assumptions_and_guarantees_from(self.traffic_spec_file)
        signature: str = create_signature(spec_df)
        header_pattern: re.Pattern = re.compile(r"^%-{3}\*{3}\s*Signature\s*\*{3}-{3}$", flags=re.MULTILINE)
        self.assertRegex(signature, header_pattern)
        header_pos = header_pattern.search(signature).end()
        for var in ["car", "emergency", "green", "police"]:
            atom_pattern = re.compile(rf"^atom\({var}\).$", flags=re.MULTILINE)
            self.assertRegex(signature, atom_pattern)
            atom_pos = atom_pattern.search(signature).start()
            self.assertLess(header_pos, atom_pos)

    def test_create_signature_traffic_updated(self):
        spec_df: pd.DataFrame = get_assumptions_and_guarantees_from(self.traffic_updated_spec_file)
        signature: str = create_signature(spec_df)
        header_pattern: re.Pattern = re.compile(r"^%-{3}\*{3}\s*Signature\s*\*{3}-{3}$", flags=re.MULTILINE)
        self.assertRegex(signature, header_pattern)
        header_pos = header_pattern.search(signature).end()
        for var in ["carA", "emergency", "greenA", "greenB", "carB"]:
            atom_pattern = re.compile(rf"^atom\({var}\).$", flags=re.MULTILINE)
            self.assertRegex(signature, atom_pattern)
            atom_pos = atom_pattern.search(signature).start()
            self.assertLess(header_pos, atom_pos)

    def test_create_trace_empty(self):
        for is_ilasp in [True, False]:
            for is_counter_strat in [True, False]:
                for learning_type in Learning:
                    trace = create_trace("", is_ilasp, is_counter_strat, learning_type)
                    self.assertEqual("", trace)

    def test_create_trace(self):
        trace_name = "trace_name_0"
        trace = [
            f'not_holds_at(highwater,0,{trace_name}).\n',
            f'not_holds_at(methane,0,{trace_name}).\n',
            f'not_holds_at(pump,0,{trace_name}).\n',
            '\n',
            f'holds_at(highwater,1,{trace_name}).\n',
            f'holds_at(methane,1,{trace_name}).\n',
            f'not_holds_at(pump,1,{trace_name}).\n',
            '\n'
        ]

        is_ilasp = False
        is_counter_strat = False
        for learning_type in Learning:
            trace_in_file: str = create_trace(trace, is_ilasp, is_counter_strat, learning_type)
            header_pattern: re.Pattern = re.compile(r"^%-{3}\*{3}\s*Violation Trace\s*\*{3}-{3}$", flags=re.MULTILINE)
            self.assertRegex(trace_in_file, header_pattern)
            header_pos = header_pattern.search(trace_in_file).end()
            timepoint_poss: list[int] = []
            for timepoint in [0, 1]:
                timepoint_pattern = re.compile(rf"^timepoint\({timepoint},{trace_name}\).$", flags=re.MULTILINE)
                self.assertRegex(trace_in_file, timepoint_pattern)
                timepoint_pos: int = timepoint_pattern.search(trace_in_file).start()
                timepoint_poss.append(timepoint_pos)
                self.assertLess(header_pos, timepoint_pos)
                if timepoint > 0:
                    next_pattern = re.compile(rf"^next\({timepoint},{timepoint - 1},{trace_name}\).$",
                                              flags=re.MULTILINE)
                    self.assertRegex(trace_in_file, next_pattern)
                    next_pos: int = next_pattern.search(trace_in_file).start()
                    self.assertLess(timepoint_pos, next_pos)

            self.assertTrue(is_ascending(timepoint_poss))
            for line in trace:
                line = line.replace("\n", '')
                pattern = re.compile(rf"^{re.escape(line)}$", flags=re.MULTILINE)
                self.assertRegex(trace_in_file, pattern)

    def test_trace_list_to_asp_form(self):
        trace_name = "trace_name_0"
        trace = [
            f'not_holds_at(highwater,0,{trace_name}).\n',
            f'not_holds_at(methane,0,{trace_name}).\n',
            f'not_holds_at(pump,0,{trace_name}).\n',
            '\n',
            f'holds_at(highwater,1,{trace_name}).\n',
            f'holds_at(methane,1,{trace_name}).\n',
            f'not_holds_at(pump,1,{trace_name}).\n',
            '\n'
        ]

        trace_in_file: str = trace_list_to_asp_form(trace)
        header_pattern: re.Pattern = re.compile(r"^%-{3}\*{3}\s*Violation Trace\s*\*{3}-{3}$", flags=re.MULTILINE)
        self.assertRegex(trace_in_file, header_pattern)
        header_pos = header_pattern.search(trace_in_file).end()
        timepoint_poss: list[int] = []
        for timepoint in [0, 1]:
            timepoint_pattern = re.compile(rf"^timepoint\({timepoint},{trace_name}\).$", flags=re.MULTILINE)
            self.assertRegex(trace_in_file, timepoint_pattern)
            timepoint_pos: int = timepoint_pattern.search(trace_in_file).start()
            timepoint_poss.append(timepoint_pos)
            self.assertLess(header_pos, timepoint_pos)
            if timepoint > 0:
                next_pattern = re.compile(rf"^next\({timepoint},{timepoint - 1},{trace_name}\).$", flags=re.MULTILINE)
                self.assertRegex(trace_in_file, next_pattern)
                next_pos: int = next_pattern.search(trace_in_file).start()
                self.assertLess(timepoint_pos, next_pos)

        self.assertTrue(is_ascending(timepoint_poss))
        for line in trace:
            line = line.replace("\n", '')
            pattern = re.compile(rf"^{re.escape(line)}$", flags=re.MULTILINE)
            self.assertRegex(trace_in_file, pattern)

    def test_trace_list_to_ilasp_form(self):
        trace_name = "trace_name_0"
        learning: Learning = Learning.ASSUMPTION_WEAKENING
        trace = [
            f'not_holds_at(highwater,0,{trace_name}).\n',
            f'not_holds_at(methane,0,{trace_name}).\n',
            f'not_holds_at(pump,0,{trace_name}).\n',
            '\n',
            f'holds_at(highwater,1,{trace_name}).\n',
            f'holds_at(methane,1,{trace_name}).\n',
            f'not_holds_at(pump,1,{trace_name}).\n',
            '\n'
        ]

        trace_as_asp: str = trace_list_to_asp_form(trace)
        trace_as_ilasp: str = trace_list_to_ilasp_form(trace_as_asp, learning=learning)
        self.assert_ILASP_equivalent(trace_as_ilasp, trace, trace_name, is_positive=True, timepoints=[0, 1])

    def test_trace_list_to_ilasp_form_cs_dead(self):
        trace_name = "ini_S0_S1_DEAD"
        learning: Learning = Learning.GUARANTEE_WEAKENING
        trace = [
            f"not_holds_at(highwater,0,{trace_name}).\n",
            f"not_holds_at(methane,0,{trace_name}).\n",
            f"not_holds_at(pump,0,{trace_name}).\n",
            '\n',
            f"not_holds_at(highwater,1,{trace_name}).\n",
            f"holds_at(methane,1,{trace_name}).\n",
            f"holds_at(pump,1,{trace_name}).\n",
            '\n',
            f"holds_at(highwater,2,{trace_name}).\n",
            f"holds_at(methane,2,{trace_name}).\n",
            f"not_holds_at(pump,2,{trace_name}).\n"
        ]

        trace_as_asp: str = trace_list_to_asp_form(trace)
        trace_as_ilasp: str = trace_list_to_ilasp_form(trace_as_asp, learning=learning)
        self.assert_ILASP_equivalent(trace_as_ilasp, trace, trace_name, is_positive=True, timepoints=[0, 1, 2])

    def test_trace_list_to_ilasp_form_cs_loop(self):
        trace_name = "ini_S0_S1_S2_S2"
        learning: Learning = Learning.GUARANTEE_WEAKENING
        trace = [
            "not_holds_at(highwater,0,ini_S0_S1_S2_S2).",
            "not_holds_at(methane,0,ini_S0_S1_S2_S2).",
            "not_holds_at(pump,0,ini_S0_S1_S2_S2).",
            '\n',
            "not_holds_at(highwater,1,ini_S0_S1_S2_S2).",
            "holds_at(methane,1,ini_S0_S1_S2_S2).",
            "holds_at(pump,1,ini_S0_S1_S2_S2).",
            '\n',
            "holds_at(highwater,2,ini_S0_S1_S2_S2).",
            "holds_at(methane,2,ini_S0_S1_S2_S2).",
            "not_holds_at(pump,2,ini_S0_S1_S2_S2).",
        ]

        trace_as_asp: str = trace_list_to_asp_form(trace)
        trace_as_ilasp: str = trace_list_to_ilasp_form(trace_as_asp, learning=learning)
        self.assert_ILASP_equivalent(trace_as_ilasp, trace, trace_name, is_positive=True, timepoints=[0, 1, 2], is_loop=True)

    def assert_ILASP_equivalent(self, trace_as_ilasp: str, trace: list[str], trace_name: str,
                                is_positive: bool, timepoints: list[int], is_loop: bool = False) -> None:
        assert len(timepoints) >= 1 and timepoints == list(range(len(timepoints)))
        header_pattern: re.Pattern = re.compile(r"^%-{3}\*{3}\s*Violation Trace\s*\*{3}-{3}$", flags=re.MULTILINE)
        self.assertRegex(trace_as_ilasp, header_pattern)
        header_pos = header_pattern.search(trace_as_ilasp).end()
        if is_positive:
            encapsulation_header_pattern = re.compile(
                rf"^{re.escape('#pos({entailed(')}{trace_name}{re.escape(')},{},{')}$", flags=re.MULTILINE)
        else:
            encapsulation_header_pattern = re.compile(
                rf"^{re.escape('#pos({},{entailed(')}{trace_name}{re.escape(')},{')}$", flags=re.MULTILINE)
        self.assertRegex(trace_as_ilasp, encapsulation_header_pattern)
        encapsulation_header_pos = encapsulation_header_pattern.search(trace_as_ilasp).end()
        self.assertLess(header_pos, encapsulation_header_pos)
        timepoint_poss: list[int] = []
        for timepoint in timepoints:
            timepoint_pattern = re.compile(rf"^timepoint\({timepoint},{trace_name}\).$", flags=re.MULTILINE)
            self.assertRegex(trace_as_ilasp, timepoint_pattern)
            timepoint_pos: int = timepoint_pattern.search(trace_as_ilasp).start()
            timepoint_poss.append(timepoint_pos)
            self.assertLess(encapsulation_header_pos, timepoint_pos)
            if timepoint > 0:
                next_pattern = re.compile(rf"^next\({timepoint},{timepoint - 1},{trace_name}\).$", flags=re.MULTILINE)
                self.assertRegex(trace_as_ilasp, next_pattern)
                next_pos: int = next_pattern.search(trace_as_ilasp).start()
                self.assertLess(timepoint_pos, next_pos)
        if is_loop:
            next_loop_pattern = re.compile(rf"^next\({timepoint},{timepoint},{trace_name}\).$", flags=re.MULTILINE)
            self.assertRegex(trace_as_ilasp, next_loop_pattern)
            loop_pos: int = next_loop_pattern.search(trace_as_ilasp).start()
            self.assertLess(next_pos, loop_pos)
        max_line_pos = 0
        self.assertTrue(is_ascending(timepoint_poss))
        for line in trace:
            line = line.replace("\n", '')
            pattern = re.compile(rf"^{re.escape(line)}$", flags=re.MULTILINE)
            self.assertRegex(trace_as_ilasp, pattern)
            line_end_pos = pattern.search(line).end()
            max_line_pos = max(max_line_pos, line_end_pos)
        encapsulation_footer_pattern = re.compile(rf"^{re.escape('}).')}$", flags=re.MULTILINE)
        self.assertRegex(trace_as_ilasp, encapsulation_footer_pattern)
        encapsulation_footer_pos = encapsulation_footer_pattern.search(trace_as_ilasp).end()
        self.assertLess(line_end_pos, encapsulation_footer_pos)
