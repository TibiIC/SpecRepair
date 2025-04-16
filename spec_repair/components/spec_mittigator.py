import re
from copy import deepcopy
from typing import List, Tuple, Any, Set

from spec_repair.components.interfaces.imittigator import IMittigator
from spec_repair.components.interfaces.ispecification import ISpecification
from spec_repair.enums import Learning
from spec_repair.exceptions import NoViolationException
from spec_repair.helpers.counter_trace import CounterTrace
from spec_repair.wrappers.asp_wrappers import get_violations


class SpecMittigator(IMittigator):
    def __init__(self):
        pass

    def prepare_alternative_learning_tasks(self, spec, data) -> List[Tuple[ISpecification, Any]]:
        trace, cts, learning_type = data
        assert learning_type == Learning.ASSUMPTION_WEAKENING

        ctss: Set[Tuple[CounterTrace]] = {tuple(cts)}
        unchanged = False
        while not unchanged:
            unchanged = True
            for cts in deepcopy(ctss):
                asp: str = self.spec_encoder.encode_ASP(spec_df, trace, list(cts))
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
                                         complete_cts_from_ct(ct, spec, deadlock_required)])
                            unchanged = False
                    if not unchanged:
                        ctss.remove(cts)
        return [list(cts) for cts in ctss]

    def add_counter_example_to_data(self, data, counter_argument) -> List[Tuple[ISpecification, Any]]:
        pass
