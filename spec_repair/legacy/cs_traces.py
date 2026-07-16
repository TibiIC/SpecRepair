from typing import Dict, List

from spec_repair.enums import Learning
from spec_repair.helpers.heuristics import choose_one_with_heuristic, manual_choice, HeuristicType
from spec_repair.model.counter_strategy import CounterStrategy
from spec_repair.model.counter_trace import cs_to_named_cs_traces, trace_replace_name
from spec_repair.util.asp_trace_util import create_trace


class CSTraces:
    trace: str
    raw_trace: str
    is_deadlock: bool

    def __init__(self, trace, raw_trace, is_deadlock):
        self.trace = trace
        self.raw_trace = raw_trace
        self.is_deadlock = is_deadlock


def cs_to_cs_trace(cs: CounterStrategy, cs_name: str, heuristic: HeuristicType) -> CSTraces:
    trace_name_dict: dict[str, str] = cs_to_named_cs_traces(cs)
    cs_trace_raw, cs_trace_path = choose_one_with_heuristic(list(trace_name_dict.items()), heuristic)
    cs_trace = trace_replace_name(cs_trace_raw, cs_trace_path, cs_name)
    is_deadlock = "DEAD" in cs_trace_path
    return CSTraces(cs_trace, cs_trace_raw, is_deadlock)


# TODO: generate multiple counter-strategies
def create_cs_traces(ilasp, learning_type: Learning, cs_list: List[CounterStrategy]) \
        -> Dict[str, CSTraces]:
    count = 0
    traces_dict: dict[str, CSTraces] = {}
    for lines in cs_list:
        trace_name_dict = cs_to_named_cs_traces(lines)
        cs_trace, cs_trace_path = choose_one_with_heuristic(list(trace_name_dict.items()), manual_choice)
        cs_trace_list = [cs_trace]
        # TODO: make it clear that a single trace/name pair is created for each element in the list
        trace, trace_names = create_trace(cs_trace_list, ilasp=ilasp, counter_strat=True,
                                          learning_type=learning_type)
        replacement = rf"counter_strat_{count}"
        for name in trace_names:
            trace = trace_replace_name(trace, name, replacement)
        count += 1
        # Add trace to counter-strat collection:
        is_deadlock = "DEAD" in cs_trace_path
        traces_dict[replacement] = CSTraces(trace, cs_trace, is_deadlock)

    return traces_dict
