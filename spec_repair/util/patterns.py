import re
from abc import ABC


PRS_REG = re.compile(r"^\s*G[^-]*->\s*F")
FIRST_PRED = re.compile(r"\(([^,)]*)")
ALL_PREDS = re.compile(r"\(([^)]*)\)")
aImplies_bUntil_c = re.compile(r"G\s*\(([^-]*)->\(*([^U]*)U\(*(.*)\)")
aImpliesNext_bUntil_c = re.compile(r"G\s*\(([^-]*)->next\(([^U]*)U(.*)\)")

# These are all old

temporal_operators = ['X', 'G', 'F']
symbols = ['G', 'F', 'X', '->', '|', '&', ')', '(']
bool_op = '!&'

# for declare and xml
achieve_pattern = re.compile(r"\s*G\s*\(\s*(.*)\s*->\s*(\w)\s*(.*)\s*\)")
achieve_pattern_next = re.compile(r"\s*G\s*\(\s*(.*)\s*->\s*X\s*(.*)\s*\)")
achieve_pattern_next_iff = re.compile(r"\s*G\s*\(\s*(.*)\s*<->\s*X\s*(.*)\s*\)")
achieve_pattern_eventually = re.compile(r"\s*G\s*\(\s*(.*)\s*->\s*<>\s*(.*)\s*\)")
achieve_pattern_eventually_beq = re.compile(r"\s*G\s*\(\s*(.*)\s*->\s*<>_{\s*<=\s*(.*)\s*}\s*(.*)\s*\)")
achieve_pattern_eventually_b = re.compile(r"\s*G\s*\(\s*(.*)\s*->\s*<>_{\s*<\s*(.*)\s*}\s*(.*)\s*\)")
maintain_pattern = re.compile(r"\s*G\s*\(\s*(.*)\s*->\s*(.*)\s*\)")
maintain_pattern2 = re.compile(r"\s*G\s*\(\s*(.*)\s*<->\s*(.*)\s*\)")
# maintain_pattern3 = re.compile(r"G\s*\(\s*(.*)\s*\)")
# Fairness example:
# G (F (pattern_to_keep))
fairness_pattern = re.compile(r"\s*G\s*\(F\s*\(\s*(.*)\s*\)\)")
temp_op_pattern = re.compile(r"\s*X\s*}")
# temp_op_pattern2 = re.compile(r"\s*<>_{\s*<=\s*(.*)\s*}")
# temp_op_pattern3 = re.compile(r"\s*<>_{\s*<\s*(.*)\s*}")
# initial_pattern = re.compile(r"\s*\(\s*(.*)\s*\)")
# initial_pattern2 = re.compile(r"\s*(.*)\s*")

# for spectra
rho_pattern = re.compile(r"G\s*\(\s*(.*)\s*\)")
# fairness2 example
# GF (pattern_to_keep)
fairness_pattern2 = re.compile(r"\s*G\s*F\s*\(\s*(.*)\s*\)")
theta_pattern = re.compile(r"\s*\(\s*(.*)\s*\)")
theta_pattern2 = re.compile(r"\s*(.*)\s*")
achieve_pattern_next_spectra = re.compile(r"\s*G\s*\(\s*(.*)\s*->\s*next\(\s*(.*)\s*\)\s*\)")
ass_pattern_rho = re.compile(r"\s*asm\s*G\s*\((.*)\s*\)\s*;\s*")
gar_pattern_rho = re.compile(r"\s*gar\s*G\s*\((.*)\s*\)\s*;\s*")
ass_pattern_fairness = re.compile(r"\s*asm\s*GF\s*\((.*)\s*\)\s*;\s*")
gar_pattern_fairness = re.compile(r"\s*gar\s*GF\s*\((.*)\s*\)\s*;\s*")
external_brackets = re.compile(r"\s*\(\s*(.*)\s*\)\s*")
monitor_pattern = re.compile(r"monitor\s*(.*)\s*(.*)\s*{\s*")
define_pattern = re.compile(r"define\s*(.*)\s*:=\s*(.*)\s*;\s*")

goal_conditions_pa = [['gname', 'gc_pa', 'pos']]
goal_targets_pa = [['gname', 'gc_pa', 'pos']]

assumption_conditions_pa = [['gname', 'ac_pa', 'pos']]
assumption_targets_pa = [['gname', 'ac_pa', 'pos']]


class ExceptionRule(ABC):
    pass


class AntecedentExceptionRule(ExceptionRule):
    pattern = re.compile(r"^antecedent_exception\(([^,]+,){3}[^,]+\)\s*:-\s*(not_)?holds_at\(([^,]+,){2}[^,]+\).$")


class ConsequentExceptionRule(ExceptionRule):
    pattern = re.compile(r"^consequent_exception\(([^,]+,){2}[^,]+\)\s*:-\s*(not_)?holds_at\(([^,]+,){2}[^,]+\).$")


class EventuallyConsequentRule(ExceptionRule):
    pattern = re.compile(
        r"^consequent_exception\(([^,]+,){2}[^,]+\)\s*:-\s*root_consequent_holds\(([^,]+,){4}[^,]+\).$")


class HoldsAtAtom:
    NEG_PREFIX = 1
    ATOM = 2
    pattern = re.compile(r"^(not_)?holds_at\(([^,]+),([^,]+),[^,]+\).?$")


class GR1FormulaPattern:
    TEMP_OP = 1
    FORMULA = 2
    pattern = re.compile(r"\s*(inv|alw|alwEv|G|GF)?\((.*)\);?$")

class GR1Atom:
    ATOM_TYPE = 1
    VALUE_TYPE = 2
    NAME = 3
    pattern = re.compile(r'^\s*(env|sys)\s+([a-zA-Z0-9_-]+)\s+([a-zA-Z0-9_-]+);?\s*$')

class DeadlockAtomSet:
    ATOM_NAME = 1
    ATOM_VALUE = 2
    pattern = re.compile(r"^atom_set_to\(([^,]+),([^,]+)\).?$")

class DeadlockViolations:
    VIOLATED_EXP_NAME = 1
    VIOLATED_TIMEPOINT = 2
    VIOLATING_TRACE_NAME = 3
    pattern = re.compile(r"^violation_holds\(([^,]+),([^,]+),([^,]+)\).?$")