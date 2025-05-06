import re
from collections import defaultdict
from typing import List, Optional, Set

from spec_repair import config
from spec_repair.helpers.adaptation_learned import Adaptation
from spec_repair.helpers.counter_trace import CounterTrace
from spec_repair.enums import Learning, When
from spec_repair.exceptions import LearningException
from spec_repair.helpers.heuristic_managers.iheuristic_manager import IHeuristicManager
from spec_repair.helpers.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.helpers.gr1_formula import GR1Formula
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.ltl_types import GR1FormulaType
from spec_repair.old.patterns import FIRST_PRED, ALL_PREDS
from spec_repair.special_types import EventuallyConsequentRule
from spec_repair.util.spec_util import trace_list_to_asp_form, \
    trace_list_to_ilasp_form, format_spec, parse_formula_str, \
    eventualise_consequent, re_line_spec, create_atom_signature_asp
from spec_repair.components.spec_generator import SpecGenerator


class NewSpecEncoder:
    def __init__(self, heuristic_manager: Optional[IHeuristicManager]):
        if heuristic_manager is None:
            self._hm = NoFilterHeuristicManager()
        self._hm = heuristic_manager

    def encode_ASP(self, spec: SpectraSpecification, trace: list[str], ct_list: List[CounterTrace]) -> str:
        """
        ASSUMES LEARNING ASSUMPTION WEAKENING ONLY
        """
        # Generate first Clingo file to find violating assumptions/guarantees
        formulas_string = spec.to_asp(for_clingo=True)
        signature_string = create_atom_signature_asp(spec.get_atoms())
        violation_trace = trace_list_to_asp_form(trace)
        cs_trace_string: str = ''.join([cs_trace.get_asp_form() for cs_trace in ct_list])
        return SpecGenerator.generate_clingo(formulas_string, "", signature_string, violation_trace,
                                             cs_trace_string)

    def encode_ILASP(self, spec: SpectraSpecification, trace: List[str], ct_list: List[CounterTrace],
                     violations: list[str],
                     learning_type: Learning):
        mode_declaration = self._create_mode_bias(spec, violations, learning_type)
        trace_asp = trace_list_to_asp_form(trace)
        trace_ilasp = trace_list_to_ilasp_form(trace_asp, learning=Learning.ASSUMPTION_WEAKENING)
        # TODO: see how to deal with generation/renaming of counter-strategy traces (based on Learning type too)
        ct_list_ilasp: str = ''.join([cs_trace.get_ilasp_form(learning=learning_type) for cs_trace in ct_list])
        sub_spec = spec.extract_sub_specification(
            lambda x: x['type'] == learning_type.formula_type()
        )
        if learning_type == Learning.ASSUMPTION_WEAKENING:
            exp_names_to_learn = get_violated_expression_names_of_type(violations, learning_type.exp_type_str())
        else:
            exp_names_to_learn = get_expression_names_of_type(violations, learning_type.exp_type_str())
        expressions_to_weaken = sub_spec.to_asp(learning_names=exp_names_to_learn, for_clingo=False,
                                                is_ev_temp_op=self._hm.is_enabled("INVARIANT_TO_RESPONSE_WEAKENING"))
        signature_string = create_atom_signature_asp(spec.get_atoms())
        las = SpecGenerator.generate_ilasp(mode_declaration, expressions_to_weaken, signature_string, trace_ilasp,
                                           ct_list_ilasp)
        return las

    def _create_mode_bias(self, spec: SpectraSpecification, violations: list[str], learning_type) -> str:
        head = "antecedent"
        extra_args = "_,_"

        if learning_type == Learning.GUARANTEE_WEAKENING:
            head = "consequent"
            extra_args = "_"

        output = "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n" \
                 "%% Mode Declaration\n" \
                 "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\n"

        if learning_type == Learning.ASSUMPTION_WEAKENING:
            output += f"#modeh({head}_exception(const(expression_v), const(index), var(time), var(trace))).\n"
        else:
            output += f"#modeh({head}_exception(const(expression_v), var(time), var(trace))).\n"

        restriction = ", (positive)"
        output += f"#modeb(2,timepoint_of_op(const(temp_op_v), var(time), var(time), var(trace)){restriction}).\n"
        output += f"#modeb(2,holds_at(const(usable_atom), var(time), var(trace)){restriction}).\n"
        output += f"#modeb(2,not_holds_at(const(usable_atom), var(time), var(trace)){restriction}).\n"
        if self._hm.is_enabled("INVARIANT_TO_RESPONSE_WEAKENING"):
            output += f"#modeh(ev_temp_op(const(expression_v))).\n"

        for atom in sorted(spec.get_atoms()):
            output += f"#constant(usable_atom,{atom.name}).\n"
        # TODO: find a way to provide the correct end index value
        output += f"#constant(index,0..1).\n"
        for temp_op in ["current", "next", "prev", "eventually"]:
            output += f"#constant(temp_op_v,{temp_op}).\n"

        # This determines which rules can be weakened.
        if learning_type == Learning.GUARANTEE_WEAKENING:
            formula_names = spec.filter(lambda x: x['type'] == GR1FormulaType.GAR)["name"]
        elif not violations:
            formula_names = spec.filter(lambda x: x['type'] == GR1FormulaType.ASM)["name"]
        else:
            formula_names = get_violated_expression_names_of_type(violations, learning_type.exp_type_str())

        for name in formula_names:
            output += f"#constant(expression_v, {name}).\n"

        output += f"#bias(\"\n"
        output += f":- constraint.\n"
        output += f":- head({head}_exception({extra_args},V1,V2)), body(timepoint_of_op(_,V3,_,V4)), (V1, V2) != (V3, V4).\n"
        output += f":- head({head}_exception({extra_args},_,V1)), body(holds_at(_,_,V2)), V1 != V2.\n"
        output += f":- head({head}_exception({extra_args},_,V1)), body(not_holds_at(_,_,V2)), V1 != V2.\n"
        output += f":- body(timepoint_of_op(_,_,V1,_)), body(holds_at(_,V2,_)), V1 != V2.\n"
        output += f":- body(timepoint_of_op(_,_,V1,_)), body(not_holds_at(_,V2,_)), V1 != V2.\n"
        output += f":- body(timepoint_of_op(_,_,_,_)), not body(not_holds_at(_,_,_)), not body(holds_at(_,_,_)).\n"
        output += f":- body(timepoint_of_op(current,V1,V2,_)), V1 != V2.\n"
        output += f":- body(timepoint_of_op(next,V1,V2,_)), V1 == V2.\n"
        output += f":- body(timepoint_of_op(prev,V1,V2,_)), V1 == V2.\n"
        output += f":- body(timepoint_of_op(eventually,V1,V2,_)), V1 == V2.\n"
        output += f":- body(holds_at(_,V1,V2)), not body(timepoint_of_op(_,_,V1,V2)).\n"
        output += f":- body(not_holds_at(_,V1,V2)), not body(timepoint_of_op(_,_,V1,V2)).\n"

        if not self._hm.is_enabled("INCLUDE_NEXT"):
            output += f":- head({head}_exception({extra_args},_,_)), body(timepoint_of_op(next,_,_,_)).\n"
        if not self._hm.is_enabled("INCLUDE_PREV"):
            output += f":- head({head}_exception({extra_args},_,_)), body(timepoint_of_op(prev,_,_,_)).\n"
        if learning_type == Learning.ASSUMPTION_WEAKENING or not config.WEAKENING_TO_JUSTICE:
            # Learning eventually expressions doesn't make sense within the antecedent of a formula
            output += f":- head({head}_exception({extra_args},_,_)), body(timepoint_of_op(eventually,_,_,_)).\n"
        if self._hm.is_enabled("INVARIANT_TO_RESPONSE_WEAKENING"):
            output += f":- head(ev_temp_op(_)), body(timepoint_of_op(_,_,_,_)).\n"
            output += f":- head(ev_temp_op(_)), body(holds_at(_,_,_)).\n"
            output += f":- head(ev_temp_op(_)), body(not_holds_at(_,_,_)).\n"
        output += "\").\n\n"
        return output

    def integrate_learned_hypothesis(self, spec: list[str], learning_hypothesis, learning_type) -> list[str]:
        adaptations_strings: list[str] = list(
            filter(re.compile("_exception|ev_temp_op").search, learning_hypothesis))
        if len(adaptations_strings) == 0:
            raise LearningException("Nothing learned")
        else:
            print("Rule:")
        formatted_spec = format_spec(spec)
        line_list = []
        rule_list = []
        output_list = []
        for adaptation_str in adaptations_strings:
            if EventuallyConsequentRule.pattern.match(adaptation_str):
                self.process_new_eventually_exception(learning_type, line_list, output_list, adaptation_str, rule_list,
                                                      formatted_spec)
            else:  # either antecedent or consequent exception
                self.process_new_rule_exception(learning_type, line_list, output_list, adaptation_str, rule_list,
                                                formatted_spec)

        formatted_spec = [re.sub(r"\bI\b\s*\(", "(", line) for line in formatted_spec]
        formatted_spec = re_line_spec(formatted_spec)
        return formatted_spec

    def process_new_rule_exception(self, learning_type, line_list, output_list, adaptation_str: str, adaptation_list,
                                   spec):
        name = FIRST_PRED.search(adaptation_str).group(1)
        for i, line in enumerate(spec):
            if re.search(name + r"\b", line):
                j = i + 1
        line = spec[j].strip("\n")
        print(line)
        line_list.append(line)
        print("Hypothesis:")
        print(f'\t{adaptation_str}')
        adaptation_list.append(adaptation_str)

        # Generate data structures from line strings
        spectra_rule: GR1Formula = GR1Formula.from_str(line)
        adaptation_learned = Adaptation.from_str(adaptation_str)

        # Integrate the learned adaptation into the spectra rule
        spectra_rule.integrate(adaptation_learned)

        # Replace the old rule with the new one
        new_spectra_rule_str = f"\t{spectra_rule.to_str()}\n"
        spec[j] = new_spectra_rule_str
        # TODO: deal with generation of multiple lines of assumptions/guarantees from current

        print("New Rule:")
        print(new_spectra_rule_str)
        output_list.append(new_spectra_rule_str)

    def process_new_eventually_exception(self, learning_type, line_list, output_list, rule, rule_list, spec):
        name = ALL_PREDS.search(rule).group(1).split(',')[1].strip()
        for i, line in enumerate(spec):
            if re.search(name + r"\b", line):
                j = i + 1
        line = spec[j].strip("\n")
        print(line)
        line_list.append(line)
        print("Hypothesis:")
        print(f'\t{rule}')
        rule_list.append(rule)
        output = eventualise_consequent(line, learning_type)
        spec[j] = output
        print("New Rule:")
        print(output.strip("\n"))
        output_list.append(output.strip("\n"))

    def set_heuristic_manager(self, heuristic_manager):
        self._hm = heuristic_manager


def get_violated_expression_names_of_type(violations: list[str], exp_type: str) -> list[str]:
    assert exp_type in ["assumption", "guarantee"]
    vs: list[str] = get_violated_expression_names(violations)
    es: list[str] = get_expression_names_of_type(violations, exp_type)
    return list(dict.fromkeys([v for v in vs if v in es]))


def get_expression_names_of_type(asp_text: list[str], exp_type: str):
    assert exp_type in ["assumption", "guarantee"]
    return re.findall(rf"{exp_type}\(\b([^,^)]*)", ''.join(asp_text))


def get_violated_expression_names(violations: list[str]) -> list[str]:
    return re.findall(r"violation_holds\(\b([^,^)]*)", ''.join(violations))


all_temp_ops = ["prev", "current", "next", "eventually"]
temp_ops_order_map = {string: index for index, string in enumerate(all_temp_ops)}


def get_temp_ops(rule: str) -> List[str]:
    """
    Extracts the first argument of the "holds_at" expression.
    On error (generally means string is empty), returns the
    "current" temporal operator.
    @param rule:
    @return:
    """
    try:
        ops = list(set(re.findall(r"holds_at\((\w+)(?:,\w+)*\)", rule)))
        return sorted(ops, key=lambda x: temp_ops_order_map[x])
    except AttributeError:
        return ["current"]


def store_placeholder_OP_rules_by_replaced_rule(input_string):
    # Define a default dictionary to store the functions by their first variable
    rule_by_temp_op = defaultdict(list)

    # Regular expression to capture holds_at or not_holds_at functions and their first variable
    pattern = r"(holds_at|not_holds_at)\((\w+),(.*?)\)"

    # Find all functions and group them by their first variable
    matches = re.findall(pattern, input_string)
    for func_type, first_var, rest in matches:
        # Replace the first variable with "OP"
        new_rule = f"{func_type}(OP,{rest.strip()})"
        rule_by_temp_op[first_var].append(new_rule)

    # Prepare the output dictionary
    result = {}
    for var, functions in rule_by_temp_op.items():
        # Join the functions by ",\n" and add them to the dictionary
        result[var] = ",\n\t".join(functions)

    return result


def propositionalise_antecedent(line, exception=False):
    output = ""
    disjunction_of_conjunctions = parse_formula_str(line["antecedent"])
    n_root_antecedents = 0
    timepoint = "T" if line['when'] != When.INITIALLY else "0"
    if len(disjunction_of_conjunctions) == 0 and exception:
        disjunction_of_conjunctions = [defaultdict(list)]
    component_body = f"antecedent_holds({line['name']},{timepoint},S):-\n" + \
                     f"\ttrace(S),\n" + \
                     f"\ttimepoint({timepoint},S)"
    for asm_id, disjunct in enumerate(disjunction_of_conjunctions):
        output += component_body
        for i, (temp_op, conjuncts) in enumerate(disjunct.items()):
            output += f",\n{component_end_antecedent(line['name'], temp_op, timepoint, n_root_antecedents + i)}"
        if exception:
            output += f",\n\tnot antecedent_exception({line['name']},{asm_id},{timepoint},S)"
        output += ".\n\n"
        for temp_op, conjuncts in disjunct.items():
            output += root_antecedent_body(line['name'], n_root_antecedents)
            for conjunct in conjuncts:
                conjunct_and_value = conjunct.split("=")
                c = conjunct_and_value[0]
                v = conjunct_and_value[1] == "true"
                output += f",\n\t{'' if v else 'not_'}holds_at({c},T2,S)"
            output += ".\n\n"
            n_root_antecedents += 1

    return output


def propositionalise_consequent(line, exception=False, is_ev_temp_op=True):
    output = ""
    disjunction_of_conjunctions = parse_formula_str(line["consequent"])
    n_root_consequents = 0
    timepoint = "T" if line['when'] != When.INITIALLY else "0"
    if len(disjunction_of_conjunctions) == 0 and exception:
        disjunction_of_conjunctions = [defaultdict(list)]
    component_body = f"consequent_holds({line['name']},{timepoint},S):-\n" + \
                     f"\ttrace(S),\n" + \
                     f"\ttimepoint({timepoint},S)"
    for disjunct in disjunction_of_conjunctions:
        output += component_body
        for i, (temp_op, conjuncts) in enumerate(disjunct.items()):
            if line['when'] == When.EVENTUALLY:
                temp_op = "eventually"
            output += f",\n{component_end_consequent(line['name'], temp_op, timepoint, n_root_consequents + i)}"
        if "eventually" not in disjunct.keys() and exception and is_ev_temp_op and timepoint == "T":
            output += f",\n\tnot ev_temp_op({line['name']})"
        output += ".\n\n"
        if exception and is_ev_temp_op:
            output += component_body
            for i in range(len(disjunct)):
                output += f",\n{component_end_consequent(line['name'], 'eventually', timepoint, n_root_consequents + i)}"
            output += f",\n\tev_temp_op({line['name']}).\n\n"
        for temp_op, conjuncts in disjunct.items():
            output += root_consequent_body(line['name'], n_root_consequents)
            for conjunct in conjuncts:
                conjunct_and_value = conjunct.split("=")
                c = conjunct_and_value[0]
                v = conjunct_and_value[1] == "true"
                output += f",\n\t{'' if v else 'not_'}holds_at({c},T2,S)"
            output += ".\n\n"
            n_root_consequents += 1

    if exception and line['type'] == "guarantee":
        output += component_body
        output += f",\n\tconsequent_exception({line['name']},{timepoint},S)"
        if is_ev_temp_op:
            output += f",\n\tnot ev_temp_op({line['name']})"
        output += f".\n\n"

    return output


def root_antecedent_body(name, id: int):
    out = f"root_antecedent_holds(OP,{name},{id},T1,S):-\n" + \
          f"\ttrace(S),\n" + \
          f"\ttimepoint(T1,S),\n" + \
          f"\tnot weak_timepoint(T1,S),\n" + \
          f"\ttimepoint(T2,S),\n" + \
          f"\ttemporal_operator(OP),\n" + \
          f"\ttimepoint_of_op(OP,T1,T2,S)"
    return out


def component_end_antecedent(name, temp_op, timepoint, id: int):
    assert temp_op in ["current", "next", "prev"]
    out = f"\troot_antecedent_holds({temp_op},{name},{id},{timepoint},S)"
    return out


def root_consequent_body(name, id: int):
    out = f"root_consequent_holds(OP,{name},{id},T1,S):-\n" + \
          f"\ttrace(S),\n" + \
          f"\ttimepoint(T1,S),\n" + \
          f"\tnot weak_timepoint(T1,S),\n" + \
          f"\ttimepoint(T2,S),\n" + \
          f"\ttemporal_operator(OP),\n" + \
          f"\ttimepoint_of_op(OP,T1,T2,S)"
    return out


def component_end_consequent(name, temp_op, timepoint, id: int):
    assert temp_op in ["current", "next", "prev", "eventually"]
    out = f"\troot_consequent_holds({temp_op},{name},{id},{timepoint},S)"
    return out
