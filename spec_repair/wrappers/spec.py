import re
import subprocess
from typing import Optional

from spec_repair.ltl_types import GR1ExpType, LTLFiltOperation
from spec_repair.old.specification_helper import strip_vars
from spec_repair.util.spec_util import simplify_assignments, shift_prev_to_next


class Spec:
    def __init__(self, spec: str):
        self.text: str = spec

    def swap_rule(self, name: str, new_rule: str):
        # Use re.sub with a callback function to replace the next line after the pattern
        def replace_line(match):
            name_line = match.group(0)
            rule_line = match.group(2)
            indentation = re.search(r'^\s*', rule_line).group(0)  # Capture the indentation
            new_rule_line = f"{indentation}{new_rule}\n"
            return name_line.replace(rule_line, new_rule_line, 1)

        # Find the pattern and replace the next line following it
        regex_pattern = re.compile(rf'({re.escape(name)}.*?\n)((.*?)\n)', re.DOTALL)
        self.text = re.sub(regex_pattern, replace_line, self.text)

    def __eq__(self, other):
        asm_eq = self.equivalent_to(other, GR1ExpType.ASM)
        if not asm_eq:
            return False
        gar_eq = self.equivalent_to(other, GR1ExpType.GAR)
        return asm_eq and gar_eq

    def __ne__(self, other):
        # Define the not equal comparison
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return self.text.__hash__()

    def to_spot(self, exp_type: Optional[GR1ExpType] = None) -> str:
        """
        Returns spec as string that can be operated on by SPOT
        """
        exps_asm = extract_GR1_expressions_of_type_spot(str(GR1ExpType.ASM), self.text.split("\n"))
        exps_gar = extract_GR1_expressions_of_type_spot(str(GR1ExpType.GAR), self.text.split("\n"))
        match exp_type:
            case GR1ExpType.ASM:
                return exps_asm
            case GR1ExpType.GAR:
                return exps_gar
            case _:
                exps = f"({exps_asm})->({exps_gar})"
                return exps

    def implied_by(self, other, exp_type: Optional[GR1ExpType] = None):
        return other.implies(self, exp_type)

    def implies(self, other, exp_type: Optional[GR1ExpType] = None):
        ltl_op = LTLFiltOperation.IMPLIES
        return self.compare_to(other, exp_type, ltl_op)

    def equivalent_to(self, other, exp_type: GR1ExpType):
        ltl_op = LTLFiltOperation.EQUIVALENT
        return self.compare_to(other, exp_type, ltl_op)

    def compare_to(self, other, exp_type: GR1ExpType, ltl_op: LTLFiltOperation):
        this_exps = self.to_spot(exp_type)
        other_exps = other.to_spot(exp_type)
        return is_left_cmp_right(this_exps, ltl_op, other_exps)

    def get_spec(self):
        return self.text


def is_left_cmp_right(this_exps: str, ltl_op: LTLFiltOperation, other_exps: str) -> bool:
    # TODO: introduce an assertion against ltl_ops which do not exist yet
    linux_cmd = ["ltlfilt", "-c", "-f", f"{this_exps}", f"{ltl_op.flag()}", f"{other_exps}"]
    p = subprocess.Popen(linux_cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    output: str = p.communicate()[0].decode('utf-8')
    reg = re.search(r"([01])\n", output)
    if not reg:
        raise Exception(
            f"The output of ltlfilt is unexpected, ergo error occurred during the comparison of:\n{this_exps}\nand\n{other_exps}",
        )
    result = reg.group(1)
    return result == "1"


def extract_GR1_expressions_of_type_spot(exp_type: str, spec: list[str]) -> str:
    variables = strip_vars(spec)
    spec = simplify_assignments(spec, variables)
    expressions = [re.sub(r"\s", "", spec[i + 1]) for i, line in enumerate(spec) if re.search(f"^{exp_type}", line)]
    expressions = [shift_prev_to_next(formula, variables) for formula in expressions]
    if any([re.search("PREV", x) for x in expressions]):
        raise Exception("There are still PREVs in the expressions!")
    exp_conj = re.sub(";", "", '&'.join(expressions))
    return exp_conj
