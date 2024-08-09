import re
from typing import List

import pandas as pd

from spec_repair import config
from spec_repair.helpers.counter_trace import CounterTrace
from spec_repair.enums import Learning, ExpType, When
from spec_repair.exceptions import LearningException
from spec_repair.ltl import filter_expressions_of_type, Spec
from spec_repair.old.patterns import FIRST_PRED, ALL_PREDS
from spec_repair.special_types import EventuallyConsequentRule
from spec_repair.util.exp_util import eventualise_consequent
from spec_repair.util.list_util import re_line_spec
from spec_repair.util.spec_util import expressions_df_to_str, illegal_assignments, \
    extract_variables, extract_df_content, trace_list_to_asp_form, \
    trace_list_to_ilasp_form, format_spec, integrate_rule
from spec_repair.components.spec_generator import SpecGenerator


class SpecEncoder:
    def __init__(self, spec_generator: SpecGenerator):
        self.include_prev = False
        self.include_next = False
        self.spec_generator = spec_generator

    def encode_ASP(self, spec_df: Spec, trace: list[str], ct_list: List[CounterTrace]) -> str:
        """
        ASSUMES LEARNING ASSUMPTION WEAKENING ONLY
        """
        # Generate first Clingo file to find violating assumptions/guarantees
        assumptions = filter_expressions_of_type(spec_df, ExpType.ASSUMPTION)
        guarantees = filter_expressions_of_type(spec_df, ExpType.GUARANTEE)
        assumption_string = expressions_df_to_str(assumptions, for_clingo=True)
        guarantee_string = expressions_df_to_str(guarantees, for_clingo=True)
        violation_trace = trace_list_to_asp_form(trace)
        cs_trace_string: str = ''.join([cs_trace.get_asp_form() for cs_trace in ct_list])
        return self.spec_generator.generate_clingo(spec_df, assumption_string, guarantee_string, violation_trace,
                                                   cs_trace_string)

        # TODO: consider, instead of spec_df, to offer only assumptions/guarantees as df, based on learning type
        #       won't need to carry flag type anymore

    def encode_ILASP(self, spec_df: pd.DataFrame, trace: List[str], ct_list: List[CounterTrace], violations: list[str],
                     learning_type: Learning):
        mode_declaration = self._create_mode_bias(spec_df, violations, learning_type)
        trace_asp = trace_list_to_asp_form(trace)
        trace_ilasp = trace_list_to_ilasp_form(trace_asp, learning=Learning.ASSUMPTION_WEAKENING)
        # TODO: see how to deal with generation/renaming of counter-strategy traces (based on Learning type too)
        ct_list_ilasp: str = ''.join([cs_trace.get_ilasp_form(learning=learning_type) for cs_trace in ct_list])
        expressions = filter_expressions_of_type(spec_df, learning_type.exp_type())
        if learning_type == Learning.ASSUMPTION_WEAKENING:
            exp_names_to_learn = get_violated_expression_names_of_type(violations, learning_type.exp_type_str())
        else:
            exp_names_to_learn = get_expression_names_of_type(violations, learning_type.exp_type_str())
        expressions_to_weaken = expressions_df_to_str(expressions, exp_names_to_learn)
        las = self.spec_generator.generate_ilasp(spec_df, mode_declaration, expressions_to_weaken, trace_ilasp,
                                                 ct_list_ilasp)
        return las

    def _create_mode_bias(self, spec_df: Spec, violations: list[str], learning_type):
        head = "antecedent_exception"
        next_type = ""
        in_bias = ""

        if learning_type == Learning.GUARANTEE_WEAKENING:
            head = "consequent_exception"
            next_type = "_weak"

        output = "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n" \
                 "%% Mode Declaration\n" \
                 "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\n" \
                 f"#modeh({head}(const(expression_v), var(time), var(trace))).\n"

        # Learning rule for weakening to justice rule
        if config.WEAKENING_TO_JUSTICE:
            output += f"#modeh(consequent_holds(eventually,const(expression_v), var(time), var(trace))).\n"

        restriction = ", (positive)"
        if config.WEAKENING_TO_JUSTICE:
            output += f"#modeb(1,root_consequent_holds(eventually, const(expression_v), var(time), var(trace)){restriction}).\n"
        output += f"#modeb(2,holds_at(const(temp_op_v), const(usable_atom), var(time), var(trace)){restriction}).\n"
        output += f"#modeb(2,not_holds_at(const(temp_op_v), const(usable_atom), var(time), var(trace)){restriction}).\n"

        for variable in extract_variables(spec_df):
            output += "#constant(usable_atom," + variable + ").\n"

        for temp_op in ["current", "next", "prev", "eventually"]:
            output += "#constant(temp_op_v," + temp_op + ").\n"

        # This determines which rules can be weakened.
        if not violations:
            expression_names = spec_df.loc[spec_df["type"] == "assumption"]["name"]
        else:
            expression_names = get_violated_expression_names_of_type(violations, learning_type.exp_type_str())

        if learning_type == Learning.GUARANTEE_WEAKENING:
            expression_names = spec_df.loc[spec_df["type"] == "guarantee"]["name"]

        for name in expression_names:
            output += f"#constant(expression_v, {name}).\n"

        output += f"#bias(\"\n"
        output += f":- constraint.\n"
        output += f":- {in_bias}head({head}(_,V1,V2)), {in_bias}body(holds_at(_,_,V3,V4)), (V3, V4) != (V1, V2).\n"
        output += f":- {in_bias}head({head}(_,V1,V2)), {in_bias}body(not_holds_at(_,_,V3,V4)), (V3, V4) != (V1, V2).\n"

        # The below would be true when learning a rule like A :- B,C. , but not A :- B;C. Not sure how to
        # distinguish, but the rules we learn seem to be disjunct bodies mostly.
        # Added back in because the ';' actually means and, it turns out
        output += f":- {in_bias}body(holds_at(eventually,_,V1,_)), {in_bias}body(holds_at(eventually,_,V2,_)), V1 != V2.\n"

        if not self.include_next:
            output += f":- {in_bias}head({head}(_,V1,V2)), {in_bias}body(holds_at(next,_,_,_)).\n"
            output += f":- {in_bias}head({head}(_,V1,V2)), {in_bias}body(not_holds_at(next,_,_,_)).\n"
        if not self.include_prev:
            output += f":- {in_bias}head({head}(_,V1,V2)), {in_bias}body(holds_at(prev,_,_,_)).\n"
            output += f":- {in_bias}head({head}(_,V1,V2)), {in_bias}body(not_holds_at(prev,_,_,_)).\n"

        ill_assign: dict = illegal_assignments(spec_df, violations, "")
        for name in expression_names:
            when = extract_df_content(spec_df, name, extract_col="when")
            if name in ill_assign.keys():
                restricted_assignments = ill_assign[name]
                restricted_assignments = [re.sub("_next", next_type + "_next", x) for x in restricted_assignments]
            else:
                restricted_assignments = []

            if when != When.EVENTUALLY:
                output += f":- {in_bias}head({head}({name},V1,V2)), {in_bias}body(holds_at(eventually,_,_,_)).\n"
                output += f":- {in_bias}head({head}({name},V1,V2)), {in_bias}body(not_holds_at(eventually,_,_,_)).\n"
                for assignment in restricted_assignments:
                    output += f":- {in_bias}head({head}({name},V1,V2)), {in_bias}body({assignment}).\n"

            if when == When.EVENTUALLY:
                output += f":- {in_bias}head({head}({name},V1,V2)), {in_bias}body(holds_at(current,_,_,_)).\n"
                output += f":- {in_bias}head({head}({name},V1,V2)), {in_bias}body(not_holds_at(current_,_,_,_)).\n"
                restricted_assignments = [re.sub("V1,V2", "_,_,_", x) for x in restricted_assignments]
                for assignment in restricted_assignments:
                    output += f":- {in_bias}head({head}({name},V1,V2)), {in_bias}body({assignment}).\n"
                if self.include_prev:
                    output += f":- {in_bias}head({head}({name},V1,V2)), {in_bias}body(holds_at(prev,_,_,_)).\n"
                    output += f":- {in_bias}head({head}({name},V1,V2)), {in_bias}body(not_holds_at(prev,_,_,_)).\n"
                if self.include_next:
                    output += f":- {in_bias}head({head}({name},V1,V2)), {in_bias}body(holds_at(next,_,_,_)).\n"
                    output += f":- {in_bias}head({head}({name},V1,V2)), {in_bias}body(not_holds_at(next,_,_,_)).\n"

        # This is making sure we don't learn a body that is already in our rule.
        for name in expression_names:
            antecedent_list = extract_df_content(spec_df, name, extract_col=re.sub(r"_exception", "", head))
            for antecedents in antecedent_list:
                if antecedents != "":
                    antecedents = antecedents.split(",\n\t")
                    for fact in antecedents:
                        fact = fact.replace("T,S)", "V1,V2)")
                        output += f":- {in_bias}head({head}({name},V1,V2)), {in_bias}body({fact}).\n"

        if config.WEAKENING_TO_JUSTICE:
            output += f":- {in_bias}head({head}(_,_,_)), {in_bias}body(root_consequent_holds(_,_,_,_)).\n"
            output += f":- {in_bias}head(consequent_holds(_,_,_,_)), {in_bias}body(holds_at(_,_,_,_)).\n"
            output += f":- {in_bias}head(consequent_holds(_,_,_,_)), {in_bias}body(not_holds_at(_,_,_,_)).\n"
            output += f":- {in_bias}head(consequent_holds(eventually,E1,V1,V2)), {in_bias}body(root_consequent_holds(eventually,E2,V3,V4)), (E1,V1,V2) != (E2,V3,V4).\n"

        output += "\").\n\n"
        return output

    def integrate_learned_hypothesis(self, spec: list[str], learning_hypothesis, learning_type) -> list[str]:
        rules: list[str] = list(filter(re.compile("_exception|root_consequent_").search, learning_hypothesis))
        if len(rules) == 0:
            raise LearningException("Nothing learned")
        else:
            print("Rule:")
        formatted_spec = format_spec(spec)
        line_list = []
        rule_list = []
        output_list = []
        for rule in rules:
            if EventuallyConsequentRule.pattern.match(rule):
                self.process_new_eventually_exception(learning_type, line_list, output_list, rule, rule_list,
                                                      formatted_spec)
            else:  # either antecedent or consequent exception
                self.process_new_rule_exception(learning_type, line_list, output_list, rule, rule_list, formatted_spec)

        formatted_spec = [re.sub(r"\bI\b\s*\(", "(", line) for line in formatted_spec]
        formatted_spec = re_line_spec(formatted_spec)
        return formatted_spec

    def process_new_rule_exception(self, learning_type, line_list, output_list, rule, rule_list, spec):
        name = FIRST_PRED.search(rule).group(1)
        rule_split = rule.replace("\n", "").split(":-")
        if learning_type == Learning.ASSUMPTION_WEAKENING:
            body = rule_split[1].split("; ")
        else:
            body = [rule_split[1]]
        # body = rule_split[1].split("; ")
        for i, line in enumerate(spec):
            if re.search(name + r"\b", line):
                j = i + 1
        line = spec[j].strip("\n")
        print(line)
        line_list.append(line)
        print("Hypothesis:")
        print(f'\t{rule}')
        rule_list.append(rule)
        line = spec[j].split("->")
        if len(line) == 1:
            arrow = ""
            line = re.sub(r"(G|GF)\(\s*", r"\1( -> ", line[0])
            line = line.split("->")
            if len(line) == 1:
                line = re.sub(r"\(", r"( ->", line[0])
                line = line.split("->")
        else:
            arrow = "->"
        for i, conjunct in enumerate(body):
            output = integrate_rule(arrow, conjunct, learning_type, line)
            if i == 0:
                spec[j] = output
                if output == "\n":
                    spec[j - 1] = ""
            else:
                string_out = spec[j - 1].replace(name, name + str(i)) + output
                spec.append(string_out)
            print("New Rule:")
            print(output.strip("\n"))
            output_list.append(output.strip("\n"))

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