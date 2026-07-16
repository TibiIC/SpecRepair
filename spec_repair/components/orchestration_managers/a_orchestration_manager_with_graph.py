from abc import ABC
from collections import deque
from typing import Deque, Tuple, Any, Optional
from collections import Counter

import networkx as nx

from spec_repair.interfaces.iorchestration_manager import IOrchestrationManager
from spec_repair.interfaces.ispecification import ISpecification
from spec_repair.components.repair_data import RepairData
from spec_repair.enums import Learning
from spec_repair.interfaces.irecorder import IRecorder
from spec_repair.components.recorders.unique_recorder import UniqueRecorder

RED = "#ff4444"
GREEN = "#44ff44"
BLUE = "#4444ff"
YELLOW = "#ffff44"


def parse_ct(text):
    # Remove CT( and )
    inner = text.strip()[3:-1]
    # Split on semicolons to get each state
    states = inner.split(';')
    # Convert each state into a tuple of values
    return Counter([tuple(state.split(',')) for state in states])


class AOrchestrationManagerWithStackAndGraph(IOrchestrationManager, ABC):
    def __init__(self):
        self._stack: Deque[Tuple[ISpecification, Any]] = deque()
        self._graph = nx.MultiDiGraph()

    def _reset(self):
        self._stack.clear()

    def initialise_learning_tasks(
            self,
            spec: ISpecification,
            data: Any
    ):
        self._reset()
        self.enqueue_new_tasks(spec, data, prev=None)

    def _add_edge_data_to_graph(
            self,
            data: RepairData,
            prev: Optional[tuple[ISpecification, RepairData]],
            failed_spec: Optional[ISpecification],
            task_id: int
    ):
        if prev is not None:
            _, prev_data = prev
            prev_task_id = self._get_task_id(*prev)
            if failed_spec is not None:
                if prev_data.adaptation_history:
                    self._graph.add_edge(
                        prev_task_id,
                        task_id,
                        failed_spec=failed_spec.to_str(),
                        last_adaptation=[str(adaptation) for adaptation in prev_data.adaptation_history[-1]]
                    )
                else:  # happens at the start of guarantee weakening from unrealisable spec, after counter example generation
                    self._graph.add_edge(
                        prev_task_id,
                        task_id,
                        failed_spec=failed_spec.to_str(),
                        details="Generating first counter-example"
                    )
            elif prev_data.learning_type == Learning.ASSUMPTION_WEAKENING and data.learning_type == Learning.GUARANTEE_WEAKENING:
                self._graph.add_edge(
                    prev_task_id,
                    task_id,
                    last_adaptation=["Switch to Guarantee Weakening"]
                )
            else:
                ct1 = prev_data.counter_traces[-1].print_one_line()
                ct2 = data.counter_traces[-1].print_one_line()
                if len(prev_data.counter_traces) == len(data.counter_traces) and ct1 != ct2:
                    difference = parse_ct(ct2) - parse_ct(ct1)
                    self._graph.add_edge(
                        prev_task_id,
                        task_id,
                        before_deadlock_completion=prev_data.counter_traces[-1].print_multi_line(),
                        after_deadlock_completion=data.counter_traces[-1].print_multi_line(),
                        deadlock_completion=list(difference)
                    )
                else:
                    self._graph.add_edge(
                        prev_task_id,
                        task_id,
                        last_adaptation=[str(adaptation) for adaptation in prev_data.adaptation_history[-1]]
                    )

    def connect_leaf_node(
            self,
            spec: ISpecification,
            unique_id: int,
            prev: Tuple[ISpecification, Any]
    ):
        prev_id = self._get_task_id(*prev)
        prev_spec, prev_data = prev
        self._graph.add_node(f"#{unique_id}", spec=spec.to_str(), color=BLUE)
        self._graph.add_edge(
            prev_id,
            f"#{unique_id}",
            last_adaptation=[str(adaptation) for adaptation in prev_data.adaptation_history[-1]]
        )

    def has_next(self) -> bool:
        return bool(self._stack)

    def get_next(self) -> Tuple[ISpecification, Any]:
        return self._stack.popleft()
