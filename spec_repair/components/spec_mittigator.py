import re
from copy import deepcopy, copy
from typing import List, Tuple, Any, Set

from spec_repair.components.interfaces.imittigator import IMittigator
from spec_repair.components.interfaces.ispecification import ISpecification
from spec_repair.components.new_spec_encoder import NewSpecEncoder
from spec_repair.enums import Learning
from spec_repair.exceptions import NoViolationException
from spec_repair.helpers.counter_trace import CounterTrace, complete_cts_from_ct
from spec_repair.helpers.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.wrappers.asp_wrappers import get_violations


class SpecMittigator(IMittigator):
    def __init__(self):
        self.spec_encoder = NewSpecEncoder(NoFilterHeuristicManager())

    # TODO: generate test for this method, from
    #  both assumption and guarantee weakening perspectives
    def prepare_alternative_learning_tasks(self, spec, data) -> List[Tuple[ISpecification, Any]]:
        trace, cts, learning_type = data
        assert learning_type == Learning.ASSUMPTION_WEAKENING

        ctss: Set[Tuple[CounterTrace]] = {tuple(cts)}
        unchanged = False
        while not unchanged:
            unchanged = True
            for cts in deepcopy(ctss):
                asp: str = self.spec_encoder.encode_ASP(spec, trace, list(cts))
                violations = get_violations(asp, exp_type=learning_type.exp_type())
                if not violations:
                    raise NoViolationException("Violation trace is not violating!")
                deadlock_required = re.findall(r"entailed\((counter_strat_\d*_\d*)\)", ''.join(violations))
                if deadlock_required:
                    set_cts = set(cts)
                    for i, ct in enumerate(copy(cts)):
                        if ct.is_deadlock() and ct.get_name() in deadlock_required:
                            new_set_cts = copy(set_cts)
                            new_set_cts.remove(ct)
                            ctss |= set([tuple(new_set_cts | {complete_ct}) for complete_ct in
                                         complete_cts_from_ct(ct, spec.to_str().split('\n'), deadlock_required)])
                            unchanged = False
                    if not unchanged:
                        ctss.remove(cts)
        possible_cts_list = [list(cts) for cts in ctss]
        alternative_learning_tasks: List[Tuple[ISpecification, Any]] = []
        for possible_cts in possible_cts_list:
            new_spec = deepcopy(spec)
            new_learning_type = Learning.GUARANTEE_WEAKENING
            new_data = (trace, possible_cts, new_learning_type)
            alternative_learning_tasks.append((new_spec, new_data))
        return alternative_learning_tasks


    def add_counter_example_to_data(self, data, counter_argument) -> Any:
        trace, cts, learning_type = data
        return trace, cts + [counter_argument], learning_type
