import re
from copy import deepcopy, copy
from typing import List, Tuple, Set, Any, cast

from spec_repair.components.interfaces.ispecification import ISpecification
from spec_repair.components.new_spec_encoder import NewSpecEncoder
from spec_repair.components.repair_data import RepairData
from spec_repair.enums import Learning
from spec_repair.exceptions import NoViolationException
from spec_repair.helpers.counter_trace import CounterTrace, complete_cts_from_ct
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.wrappers.asp_wrappers import get_violations


def move_one_to_guarantee_weakening(
        spec: ISpecification,  # ignored
        data: RepairData,
) -> List[Tuple[
    ISpecification, RepairData]]:
    new_spec = data.spec_history[0]
    new_data = deepcopy(data)
    new_data.counter_traces = data.counter_traces[0:1]  # Only keep the first counter-trace
    new_data.learning_type = Learning.GUARANTEE_WEAKENING
    new_data.spec_history  = []
    return [(new_spec, new_data)]

def move_all_to_guarantee_weakening(
        spec: ISpecification,  # ignored
        data: RepairData,
) -> List[Tuple[
    ISpecification, RepairData]]:
    assert len(data.spec_history) == len(data.spec_history) == len(data.counter_traces)
    new_spec_cts_pairs = zip(data.spec_history, data.counter_traces, data.adaptation_history)
    new_data_template = deepcopy(data)
    new_data_template.learning_type = Learning.GUARANTEE_WEAKENING
    new_data_template.spec_history = []
    new_data_template.adaptation_history = []
    new_tasks = []
    for new_spec, new_cts, new_adaptation_history in new_spec_cts_pairs:
        new_data = deepcopy(new_data_template)
        new_data.counter_traces = [new_cts]
        new_data.adaptation_history = [new_adaptation_history]
        new_tasks.append((new_spec, new_data))
    return new_tasks


def complete_counter_traces(
        spec: ISpecification,
        data: RepairData,
) -> List[Tuple[
    ISpecification, RepairData]]:
    ctss: Set[Tuple[CounterTrace, ...]] = {tuple(data.counter_traces)}
    unchanged = False
    while not unchanged:
        unchanged = True
        for cts in deepcopy(ctss):
            asp: str = NewSpecEncoder.encode_ASP(cast(SpectraSpecification, spec), data.trace, list(cts))
            violations = get_violations(asp, exp_type=Learning.GUARANTEE_WEAKENING.exp_type())
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
    possible_cts_list = [list(cts) for cts in ctss]
    alternative_learning_tasks: List[Tuple[ISpecification, Any]] = []
    for possible_cts in possible_cts_list:
        new_spec = deepcopy(spec)
        new_data = deepcopy(data)
        new_data.counter_traces = possible_cts
        new_data.learning_type = Learning.GUARANTEE_WEAKENING
        alternative_learning_tasks.append((new_spec, new_data))
    return alternative_learning_tasks
