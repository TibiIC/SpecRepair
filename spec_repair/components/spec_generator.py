import pandas as pd

from spec_repair.config import PROJECT_PATH
from spec_repair.util.file_util import read_file_lines
from spec_repair.util.spec_util import create_signature


class SpecGenerator:
    background_file_path = f"{PROJECT_PATH}/files/background_knowledge.txt"
    background_with_enum_file_path = f"{PROJECT_PATH}/files/enum/background_knowledge.txt"
    background_knowledge = ''.join(read_file_lines(background_file_path))
    background_enum_knowledge = ''.join(read_file_lines(background_with_enum_file_path))

    @staticmethod
    def generate_clingo(assumptions: str, guarantees: str, signature: str, violation_trace: str,
                        cs_trace: str, does_encode_enum: bool = False) -> str:
        """
        Generate the contents of the .lp file to be run in Clingo.
        Running this file will generate the violations that hold, given the problem statement
        :param assumptions: GR(1) assumptions, provided as a string in the form of Clingo-compatible statements
        :param guarantees: GR(1) guarantees, provided as a string in the form of Clingo-compatible statements
        :param signature: LTL atoms used in expressions (e.g. methane, highwater, pump, etc.)
        :param violation_trace: Trace which violated the original GR(1) specification
        :param cs_trace: Traces from counter-strategies, which are supposed to violate current specification
        :return:
        """
        background_knowledge = SpecGenerator.background_enum_knowledge if does_encode_enum else SpecGenerator.background_knowledge
        lp = background_knowledge + \
             assumptions + \
             guarantees + \
             signature + \
             violation_trace + \
             cs_trace
        for element_to_show in ["violation_holds/3", "assumption/1", "guarantee/1", "entailed/1"]:
            lp += f"\n#show {element_to_show}.\n"
        return lp

    @staticmethod
    def generate_ilasp(mode_declaration: str, expressions: str, signature: str, violation_trace: str,
                       cs_trace: str, does_encode_enum: bool = False) -> str:
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
        background_knowledge = SpecGenerator.background_enum_knowledge if does_encode_enum else SpecGenerator.background_knowledge
        las = mode_declaration + \
              background_knowledge + \
              expressions + \
              signature + \
              violation_trace + \
              cs_trace
        return las
