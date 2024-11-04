import re
from collections import defaultdict
from typing import List, Optional, Dict

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
from spec_repair.util.spec_util import illegal_assignments, \
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


def expressions_df_to_str(expressions: pd.DataFrame, learning_names: Optional[List[str]] = None,
                          for_clingo=False) -> str:
    if learning_names is None:
        learning_names = []
    expression_string = ""
    for _, line in expressions.iterrows():
        # This removes alwEv's unless they are being learned:
        expression_string += expression_to_str(line, learning_names, for_clingo)
    return expression_string


def expression_to_str(line: pd.Series, learning_names: list[str], for_clingo: bool) -> str:
    if line.when == When.EVENTUALLY and line['name'] not in learning_names and not for_clingo:
        return ""
    expression_string = f"%{line['type']} -- {line['name']}\n"
    expression_string += f"%\t{line['formula']}\n\n"
    expression_string += f"{line['type']}({line['name']}).\n\n"
    is_exception = (line['name'] in learning_names) and not for_clingo
    ant_exception = is_exception and line['type'] == str(ExpType.ASSUMPTION)
    gar_exception = is_exception and line['type'] == str(ExpType.GUARANTEE)
    expression_string += propositionalise_antecedent(line, ant_exception)
    expression_string += propositionalise_consequent(line, gar_exception)
    return expression_string


def get_temp_op(rule: str) -> str:
    """
    Extracts the first argument of the "holds_at" expression.
    On error (generally means string is empty), returns the
    "current" temporal operator.
    @param rule:
    @return:
    """
    try:
        return re.search(r"holds_at\((\w+)(?:,\w+)*\)", rule).group(1)
    except AttributeError:
        return "current"


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


def propositionalise_consequent(line, exception=False):
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
            output += f",\n{component_end_consequent(line['name'], temp_op, timepoint, n_root_consequents + i)}"
        if "eventually" not in disjunct.keys():
            output += f",\n\tnot ev_temp_op({line['name']})"
        output += ".\n\n"
        for temp_op, conjuncts in disjunct.items():
            output += root_consequent_body(line['name'], n_root_consequents)
            for conjunct in conjuncts:
                conjunct_and_value = conjunct.split("=")
                c = conjunct_and_value[0]
                v = conjunct_and_value[1] == "true"
                output += f",\n\t{'' if v else 'not_'}holds_at({c},T2,S)"
            output += ".\n\n"
            n_root_consequents += 1

    if exception:
        output += component_body
        output += f",\n\tconsequent_exception({line['name']},{timepoint},S).\n\n"

    return output


def parse_formula_str(formula: str) -> List[Dict[str, List[str]]]:
    """
    Parse a formula consisting of disjunctions and conjunctions of temporal operators.

    Args:
        formula (str): The input formula to parse.

    Returns:
        List[Dict[str, List[str]]]: A list of dictionaries containing operators and their associated literals.
    """
    # Remove any whitespace for easier processing
    formula = formula.replace(" ", "")

    # Split the formula by disjunction (e.g., '|' or '∨')
    disjunctions = formula.split('|')
    parsed_conjunctions = []

    for conjunct in disjunctions:
        conjunct = remove_outer_parentheses(conjunct)
        conjunct_dict = defaultdict(list)

        # Split each conjunct by conjunctions (e.g., '&')
        parts = split_with_outer_parentheses(conjunct)

        for part in parts:
            # Regex to capture "operator(content)"
            match = re.match(r'^(next|prev|G|F)\((.+)\)', part)

            if match:
                operator = match.group(1)
                operator = "eventually" if operator == "F" else operator
                content = match.group(2)
                # Split content by '&' and add to corresponding operator
                literals = re.split(r'\s*&\s*', content)
                conjunct_dict[operator].extend(literals)
            else:
                # No temporal operator, assume 'current' (no operation)
                literals = re.split(r'\s*&\s*', part.strip("()"))
                conjunct_dict["current"].extend(literals)

        parsed_conjunctions.append(dict(conjunct_dict))

    return parsed_conjunctions


def split_with_outer_parentheses(input_str: str) -> List[str]:
    """
    Split the input string based on operators while considering outer parentheses.

    Args:
        input_str (str): The input string to split.

    Returns:
        List[str]: A list of segments split based on the defined logic.
    """
    # This regex captures '&' not enclosed within parentheses
    pattern = r'\b(next|prev|F|G)\(([^()]*|[^&]*)*\)|[^()&\s]+'
    segments = [match.group(0) for match in re.finditer(pattern, input_str)]

    # Clean up the segments and filter out empty strings
    return [segment.strip() for segment in segments if segment.strip()]


def remove_outer_parentheses(s):
    s = s.strip()
    # Check if the string starts and ends with parentheses
    if s.startswith('(') and s.endswith(')'):
        return s[1:-1]  # Remove the first and last character
    return s  # Return the original string if conditions are not met


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
