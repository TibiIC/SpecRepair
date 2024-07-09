from __future__ import annotations

from copy import copy
from typing import Optional

from spec_repair.enums import Learning
from spec_repair.heuristics import choose_one_with_heuristic, HeuristicType
from spec_repair.ltl import CounterStrategy
from spec_repair.util.spec_util import cs_to_named_cs_traces, trace_replace_name, trace_list_to_asp_form, \
    trace_list_to_ilasp_form


class CounterTrace:
    def __init__(self, raw_trace: str, raw_path: str, name: Optional[str] = None):
        self._raw_trace, self._path = raw_trace, raw_path
        self._init_trace = copy(self._raw_trace)
        if name is not None:
            self._name = name
            self._raw_trace = trace_replace_name(self._raw_trace, self._path, name)
        else:
            self._name = self._path
        self._is_deadlock = "DEAD" in self._path

    def get_asp_form(self):
        return trace_list_to_asp_form([self._raw_trace])

    def get_ilasp_form(self, learning: Learning, complete_deadlock: bool = False):
        return trace_replace_name(trace_list_to_ilasp_form(self.get_asp_form(), learning), self._path, self._name)

    def __eq__(self, other: CounterTrace) -> bool:
        return self._init_trace == other._init_trace

    def __le__(self, other: CounterTrace) -> bool:
        return self._init_trace <= other._init_trace

    def __lt__(self, other: CounterTrace) -> bool:
        return self._init_trace < other._init_trace

    def __ge__(self, other: CounterTrace) -> bool:
        return self._init_trace >= other._init_trace

    def __gt__(self, other: CounterTrace) -> bool:
        return self._init_trace > other._init_trace

    def __hash__(self):
        return hash(self._init_trace)

    # TODO: Streamline this to be one-two lines maximum
    def __str__(self):
        return f"CounterTrace({self._name}):\nPATH: '{self._path}'\nTrace:\n{self._raw_trace}"


def cts_from_cs(cs: CounterStrategy, cs_id: Optional[int] = None) -> list[CounterTrace]:
    trace_name_dict: dict[str, str] = dict(sorted(cs_to_named_cs_traces(cs).items()))

    return [CounterTrace(raw_trace, raw_path, f"counter_strat_{cs_id}_{ct_id}" if cs_id is not None else None)
            for ct_id, (raw_trace, raw_path) in enumerate(trace_name_dict.items())]


def ct_from_cs(cs: CounterStrategy, heuristic: HeuristicType, cs_id: Optional[int] = None) -> CounterTrace:
    return choose_one_with_heuristic(cts_from_cs(cs, cs_id), heuristic)
