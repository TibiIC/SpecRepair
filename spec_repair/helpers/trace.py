from __future__ import annotations

from collections import defaultdict
from typing import Set, List, Any, TypeVar, Generic, Optional, Tuple, Iterator

from py_ltl.formula import AtomicProposition

from spec_repair.helpers.asp_mini_parser import ASPMiniParser

T = TypeVar("T")


class Trace:
    def __init__(self, values: List[Tuple[AtomicProposition, ...]], name: Optional[str] = None,
                 loop_index: Optional[int] = None) -> None:
        self.values: List[Tuple[AtomicProposition, ...]] = values
        self.name: Optional[str] = name
        self.loop_index: Optional[int] = loop_index
        if loop_index is not None and not (0 <= loop_index < len(values)):
            raise ValueError("loop_index must be a valid index in values")

    def __len__(self) -> int:
        if self.loop_index is None:
            return len(self.values)
        else:
            return -1

    def __getitem__(self, index: int) -> Tuple[AtomicProposition, ...]:
        if index < len(self.values):
            return self.values[index]
        if self.loop_index is None:
            raise IndexError("Trace index out of range (finite trace).")
        # wrap into loop
        loop_length = len(self.values) - self.loop_index
        offset = (index - self.loop_index) % loop_length
        return self.values[self.loop_index + offset]

    def __iter__(self) -> Iterator[Tuple[AtomicProposition, ...]]:
        # careful: may be infinite
        for i, v in enumerate(self.values):
            yield v
        if self.loop_index is not None:
            while True:
                for v in self.values[self.loop_index:]:
                    yield v

    @staticmethod
    def from_str(trace_str: str) -> Trace:
        lines = trace_str.strip().splitlines()
        values_dict: dict[int, Tuple[AtomicProposition, ...]] = defaultdict()
        trace_names: Set[str] = set()
        for line in lines:
            atomic_prop_timepoint_name = ASPMiniParser.parse_ap_adv(line)
            if atomic_prop_timepoint_name is None:
                continue
            ap, timepoint, trace_name = atomic_prop_timepoint_name
            trace_names.add(trace_name)
            values_dict[timepoint] = values_dict.get(timepoint, tuple()) + (ap,)
        values = [values_dict[i] for i in sorted(values_dict.keys())]
        trace_name = trace_names.pop() if len(trace_names) == 1 else None
        return Trace(values=values, name=trace_name, loop_index=None)
