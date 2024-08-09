import re
from abc import ABC
from typing import Callable, List

from spec_repair.helpers.counter_trace import CounterTrace


class ExceptionRule(ABC):
    pass


class AntecedentExceptionRule(ExceptionRule):
    pattern = re.compile(r"^antecedent_exception\(([^,]+,){2}[^,]+\)\s*:-\s*(not_)?holds_at\(([^,]+,){3}[^,]+\).$")


class ConsequentExceptionRule(ExceptionRule):
    pattern = re.compile(r"^consequent_exception\(([^,]+,){2}[^,]+\)\s*:-\s*(not_)?holds_at\(([^,]+,){3}[^,]+\).$")


class EventuallyConsequentRule(ExceptionRule):
    pattern = re.compile(r"^consequent_holds\(([^,]+,){3}[^,]+\)\s*:-\s*root_consequent_holds\(([^,]+,){3}[^,]+\).$")


StopHeuristicType = Callable[[List[str], List[CounterTrace]], bool]
