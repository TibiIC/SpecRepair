import pandas as pd

from spec_repair.config import PROJECT_PATH
from spec_repair.util.file_util import read_file_lines
from spec_repair.util.spec_util import create_signature


class SpecGenerator:
    def __init__(self, background_file_path=f"{PROJECT_PATH}/files/background_knowledge.txt"):
        self.background_knowledge = ''.join(read_file_lines(background_file_path))

    def generate_clingo(self, spec_df: pd.DataFrame, assumptions: str, guarantees: str, violation_trace: str,
                        cs_trace: str) -> str:
        '''
        Generate the contents of the .lp file to be run in Clingo.
        Running this file will generate the violations that hold, given the problem statement
        :param assumptions: GR(1) assumptions, provided as a string in the form of Clingo-compatible statements
        :param guarantees: GR(1) guarantees, provided as a string in the form of Clingo-compatible statements
        :param signature: LTL atoms used in expressions (e.g. methane, highwater, pump, etc.)
        :param violation_trace: Trace which violated the original GR(1) specification
        :param cs_trace: Traces from counter-strategies, which are supposed to violate current specification
        :return:
        '''
        lp = self.background_knowledge + \
             assumptions + \
             guarantees + \
             create_signature(spec_df) + \
             violation_trace + \
             cs_trace
        for element_to_show in ["violation_holds/3", "assumption/1", "guarantee/1", "entailed/1"]:
            lp += f"\n#show {element_to_show}.\n"
        return lp

    def generate_ilasp(self, spec_df: pd.DataFrame, mode_declaration: str, expressions: str, violation_trace: str,
                       cs_trace: str) -> str:
        '''
        Generate the contents of the .las file to be run in Clingo.
        Running this file will generate the violations that hold, given the problem statement
        :param assumptions: GR(1) assumptions, provided as a string in the form of Clingo-compatible statements
        :param guarantees: GR(1) guarantees, provided as a string in the form of Clingo-compatible statements
        :param signature: LTL atoms used in expressions (e.g. methane, highwater, pump, etc.)
        :param violation_trace: Trace which violated the original GR(1) specification
        :param cs_trace: Traces from counter-strategies, which are supposed to violate current specification
        :return:
        '''
        las = mode_declaration + \
              self.background_knowledge + \
              expressions + \
              create_signature(spec_df) + \
              violation_trace + \
              cs_trace
        return las
