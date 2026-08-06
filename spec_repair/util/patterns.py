import re
from abc import ABC


# `F\s*\(` rather than a bare `F`: the response pattern is G(a -> F(b)), and a
# bare F also matches the literal constant FALSE, so an ordinary safety
# constraint written `G(a -> FALSE)` was treated as a response pattern.
# pRespondsToS_substitution then searched it for "F(" and died with
# AttributeError on the None match. Three genbuf guarantees are of that form.
PRS_REG = re.compile(r"^\s*G[^-]*->\s*F\s*\(")


class ExceptionRule(ABC):
    pass


class AntecedentExceptionRule(ExceptionRule):
    pattern = re.compile(r"^antecedent_exception\(([^,]+,){3}[^,]+\)\s*:-\s*(not_)?holds_at\(([^,]+,){2}[^,]+\).$")


class ConsequentExceptionRule(ExceptionRule):
    pattern = re.compile(r"^consequent_exception\(([^,]+,){2}[^,]+\)\s*:-\s*(not_)?holds_at\(([^,]+,){2}[^,]+\).$")


class EventuallyConsequentRule(ExceptionRule):
    pattern = re.compile(
        r"^consequent_exception\(([^,]+,){2}[^,]+\)\s*:-\s*root_consequent_holds\(([^,]+,){4}[^,]+\).$")


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
