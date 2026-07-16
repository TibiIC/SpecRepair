import re
from collections import OrderedDict
from typing import Dict, List

import pandas as pd

from spec_repair.enums import When, ExpType
from spec_repair.util.file_util import read_file_lines
from spec_repair.util.formula_string_util import format_spec, parse_formula_str
from spec_repair.util.patterns import PRS_REG


# TODO: toggle "sorted" off when performance optimised
def create_signature(spec_df: pd.DataFrame):
    variables = extract_variables(spec_df)
    output = "%---*** Signature  ***---\n\n"
    for var in sorted(variables):
        output += f"atom({var}).\n"
    output += "\n\n"
    return output


def extract_variables(spec_df: pd.DataFrame) -> List[str]:
    variables = set()
    for _, row in spec_df.iterrows():
        antecedents: List[Dict[str, List[str]]] = parse_formula_str(row['antecedent'])
        consequents: List[Dict[str, List[str]]] = parse_formula_str(row['consequent'])

        for conjunction in antecedents + consequents:
            for assignments in conjunction.values():
                for assignment in assignments:
                    variables.add(assignment.split("=")[0].strip())

    return list(variables)


def get_assumptions_and_guarantees_from(start_file) -> pd.DataFrame:
    spec: List[str] = format_spec(read_file_lines(start_file))
    spec_df: pd.DataFrame = spectra_to_df(spec)
    return spec_df


def illegal_assignments(spec_df: pd.DataFrame, violations, trace):
    illegals = dict()
    # Violations needs to contain some values
    if trace == "" or not violations:
        return illegals
    expression_names: List[str] = re.findall(r"[assumption|guarantee]\(([^\)^,]*)\)", violations[0])
    for exp_name in expression_names:
        when = extract_df_content(spec_df, exp_name, "when")
        violated_timepoints = re.findall(r"violation_holds\(" + exp_name + r",(\d*),([^\)]*)\)", violations[0])
        preds: List[str] = []
        for vt in violated_timepoints:
            preds += extract_predicates(vt, trace)
        if when == when.EVENTUALLY:
            preds: List[str] = [re.sub(r"at_next\(|at_prev\(|at\(", "at_eventually(", x) for x in preds]
        preds = list(dict.fromkeys(preds))
        preds = [re.sub(r"\.", "", x) for x in preds]
        negs = [x[4:] if re.search(r"^not_", x) else "not_" + x for x in preds]
        illegals[exp_name] = negs
        # illegals[exp_name] = [x for x in negs if x not in preds]
    return illegals


def extract_df_content(formula_df: pd.DataFrame, name: str, extract_col: str):
    try:
        extracted_item = formula_df.loc[formula_df["name"] == name, extract_col].iloc[0]
        return extracted_item
    except IndexError:
        print(f"Cannot find name:\t'{name}'\n\nIn specification expression names:\n")
        print(formula_df["name"])
        exit(1)


def extract_predicates(vt, trace):
    trace_list = trace.split("\n")
    unprimed_preds = extract_preds_at(trace_list, vt, 0)
    prev_preds = extract_preds_at(trace_list, vt, -1)
    next_preds = extract_preds_at(trace_list, vt, 1)
    return unprimed_preds + prev_preds + next_preds


def extract_preds_at(trace_list, vt, offset):
    timepoint_string = "," + str(int(vt[0]) + offset) + "," + vt[1]
    swap = ""
    if offset == -1:
        swap = "_prev"
    if offset == 1:
        swap = "_next"
    preds = [re.sub(r"at\(", "at" + swap + "(", x) for x in trace_list if re.search(r"_.*" + timepoint_string, x)]
    return [re.sub(timepoint_string, ",V1,V2", x) for x in preds]


def spectra_to_df(spec: List[str]) -> pd.DataFrame:
    """
    Converts formatted Spectra file into Pandas DataFrame for manipulation into ASP.

    :param spec: Spectra specification as List of Strings.
    :return: Pandas DataFrame containing GR(1) expressions converted into antecedent/consequent.
    """
    formula_list = []
    for i, line in enumerate(spec):
        words = line.split(" ")
        if line.find('--') >= 0:
            name = re.sub(r":|\s", "", words[2])
            formula = re.sub('\s*', '', spec[i + 1])

            pRespondsToS, when = gr1_type_of(formula)

            formula_parts = formula.replace(");", "").split("->")
            if len(formula_parts) == 1:
                antecedent = ""
                consequent = re.sub(r"[^\(]*\(", "", formula_parts[0], 1)
            else:
                antecedent = re.sub(r"[^\(]*\(", "", formula_parts[0], 1)
                consequent = formula_parts[1]
            if pRespondsToS:
                consequent = re.sub(r"^F\(", "", consequent)

            formula_list.append(
                [words[0], name, formula,
                 antecedent,
                 consequent, when]
            )
    columns_and_types = OrderedDict([
        ('type', str),
        ('name', str),
        ('formula', str),
        ('antecedent', object),  # list[str]
        ('consequent', object),  # list[str]
        ('when', object)  # When
    ])
    spec_df = pd.DataFrame(formula_list, columns=list(columns_and_types.keys()))
    # Set the data types for each column
    for col, dtype in columns_and_types.items():
        spec_df[col] = spec_df[col].astype(dtype)

    return spec_df


def gr1_type_of(formula):
    '''
    :param formula:
    :return: pRespondsToS, when
    '''
    formula = re.sub('\s*', '', formula)
    eventually = re.search(r"^GF", formula)
    pRespondsToS = PRS_REG.search(formula)
    initially = not re.search(r"^G", formula)
    if eventually:
        when = When.EVENTUALLY
    elif initially:
        when = When.INITIALLY
    elif pRespondsToS:
        when = When.EVENTUALLY
    else:
        when = When.ALWAYS
    return pRespondsToS, when


def filter_formulas_of_type(formula_df: pd.DataFrame, expression: ExpType) -> pd.DataFrame:
    return formula_df.loc[formula_df['type'] == str(expression)]
