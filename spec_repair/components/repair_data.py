from typing import Any, Optional, List

from spec_repair.enums import Learning
from spec_repair.model.adaptation_learned import Adaptation
from spec_repair.model.counter_trace import CounterTrace


class RepairData:
    def __init__(self, trace: Any = None, counter_traces: List[CounterTrace] = None, learning_type: Optional[Learning] = None,
                 spec_history: Optional[list] = None, adaptation_history: Optional[list[Adaptation]] = None, learning_steps: int = 0, learning_time: float = 0.0):
        self.trace = trace
        self.counter_traces = counter_traces
        self.learning_type = learning_type
        self.spec_history = spec_history if spec_history is not None else []
        self.adaptation_history = adaptation_history if adaptation_history is not None else []
        self.learning_steps = learning_steps
        self.learning_time = learning_time
        # Why this branch cannot continue, when that is known and expected.
        #
        # The distinction matters at the point a branch dies. "The search is
        # exhausted" is a fact about the specification and, if no leaf was
        # reached, a broken invariant worth shouting about. "The learner ran out
        # of time" or "this needs deadlock completion, which is not available"
        # are facts about the budget and the methodology's coverage - real
        # limitations, but not reasons to discard every other branch's work.
        # minepump's controller-generated trace reaches 168 leaves before one
        # branch needs deadlock completion; killing the run there loses all 168.
        self.unresolvable_reason = None

    def __repr__(self):
        return f"RepairData(trace={self.trace}, counter_traces={self.counter_traces}, learning_type={self.learning_type}, spec_history={self.spec_history}, learning_steps={self.learning_steps}, learning_time={self.learning_time})"