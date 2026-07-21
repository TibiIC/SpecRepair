import re
from abc import ABC


PRS_REG = re.compile(r"^\s*G[^-]*->\s*F")


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

class GR1InlineEnumAtom:
    ATOM_TYPE = 1
    VALUES = 2
    NAME = 3
    pattern = re.compile(r'^\s*(env|sys)\s*\{([^}]*)\}\s*([a-zA-Z0-9_-]+);?\s*$')

class GR1TypeAlias:
    NAME = 1
    VALUES = 2
    pattern = re.compile(r'^\s*type\s+([a-zA-Z0-9_-]+)\s*=\s*\{([^}]*)\}\s*;?\s*$')

class DeadlockAtomSet:
    ATOM_NAME = 1
    ATOM_VALUE = 2
    pattern = re.compile(r"^atom_set_to\(([^,]+),([^,]+)\).?$")

class DeadlockViolations:
    VIOLATED_EXP_NAME = 1
    VIOLATED_TIMEPOINT = 2
    VIOLATING_TRACE_NAME = 3
    pattern = re.compile(r"^violation_holds\(([^,]+),([^,]+),([^,]+)\).?$")
