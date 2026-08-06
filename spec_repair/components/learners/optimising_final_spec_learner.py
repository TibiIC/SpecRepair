import re
import subprocess
from copy import copy, deepcopy
from typing import Set, List, Tuple, Optional

from spec_repair.interfaces.ilearner import ILearner
from spec_repair.components.new_spec_encoder import NewSpecEncoder
from spec_repair.components.repair_data import RepairData
from spec_repair.model.adaptation_learned import Adaptation
from spec_repair.model.counter_trace import CounterTrace, complete_cts_from_ct
from spec_repair.enums import Learning
from spec_repair.exceptions import NoViolationException, NoWeakeningException, DeadlockRequiredException, \
    NoAssumptionWeakeningException
from spec_repair.interfaces.iheuristic_manager import IHeuristicManager
from spec_repair.components.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.helpers.parsers.ilasp_interpreter import ILASPInterpreter
from spec_repair.model.spectra_specification import SpectraSpecification

from spec_repair.wrappers.asp_wrappers import get_violations, run_ILASP


class OptimisingSpecLearner(ILearner):
    def __init__(
            self,
            heuristic_manager: IHeuristicManager = NoFilterHeuristicManager(),
    ):
        self._hm = heuristic_manager
        self.spec_encoder = NewSpecEncoder(heuristic_manager)

    # TODO: consider returning "data" instead of empty list when no learning is possible
    def learn_new(
            self,
            spec: SpectraSpecification,
            data: RepairData
    ) -> List[Tuple[SpectraSpecification, RepairData]]:
        try:
            possible_adaptations: List[List[Adaptation]] = self.find_possible_adaptations(spec, data.trace, data.counter_traces, data.learning_type)
            if self._hm:
                possible_adaptations = self._hm.select_possible_learning_adaptations(possible_adaptations)
            new_specs = []
            new_repair_datas = []
            for adaptations in possible_adaptations:
                new_spec = deepcopy(spec).integrate_multiple(adaptations)
                new_specs.append(new_spec)
                new_repair_data = deepcopy(data)
                new_repair_data.learning_steps += 1
                new_repair_data.adaptation_history.append(adaptations)
                new_repair_datas.append(new_repair_data)
            new_tasks = [(new_spec, new_repair_data) for new_spec, new_repair_data in zip(new_specs, new_repair_datas)]
            return new_tasks
        except NoWeakeningException as e:
            print(f"Weakening failed: NoWeakeningException thrown and {e}")
            return []
        except NoViolationException as e:
            if not data.counter_traces and data.learning_type == Learning.GUARANTEE_WEAKENING:
                # Guarantee weakening learns from counter-strategies, and there
                # are none yet - so hand the specification back for the oracle
                # to extract them from, rather than giving up.
                #
                # This used to also require `not data.trace`, which excluded the
                # whole trace-violation setup: there a trace is always present,
                # so the branch fell through to returning [], the mitigator's
                # complete_counter_traces had nothing to complete and returned
                # its input unchanged, and the orchestration manager dropped the
                # already-visited task without ever reaching a leaf. Measured on
                # the 2026-08-06 sweep: 34 such events under ILASP, failing
                # amba, colorsort, genbuf and gyro outright once
                # MitigationMadeNoProgressException made them visible.
                #
                # Whether a violation trace exists says nothing about whether
                # counter-strategies are needed. Both outcomes now reach a leaf:
                # an unrealisable specification yields counter-strategies and
                # the search continues, a realisable one yields none and is
                # recorded as a solution - which it is, having nothing left to
                # repair.
                print("No counter-traces for guarantee weakening, so moving "
                      "straight to extracting counter strategies.")
                return [(spec, data)]
            else:
                print(f"Weakening failed: NoViolationException thrown and {e}")
                return []
        except DeadlockRequiredException as e:
            print(f"Weakening failed: DeadlockRequiredException thrown and {e}")
            return []
        except subprocess.TimeoutExpired as e:
            # run_ILASP's hypothesis search can time out on a large enough
            # spec (e.g. ColorSort) without being genuinely stuck - treat it
            # like the other "this branch didn't pan out" cases above rather
            # than crashing the whole BFS run.
            print(f"Weakening failed: ILASP timed out and {e}")
            return []

    def find_possible_adaptations(self, spec: SpectraSpecification, trace, cts, learning_type) -> List[
        List[Adaptation]]:
        violations = self.get_spec_violations(spec, trace, cts, learning_type)
        con_adaptations = self.find_consequent_exception_adaptations(spec, trace, cts, learning_type, violations)
        ant_adaptations = self.find_antecedent_exception_adaptations(spec, trace, cts, learning_type, violations)
        ev_adaptations = self.find_eventualisation_adaptations(spec, trace, cts, learning_type, violations)
        adaptations = ant_adaptations + con_adaptations + ev_adaptations
        # adaptations = self.find_all_exception_adaptations(spec, trace, cts, learning_type, violations)
        if not adaptations:
            if learning_type == Learning.ASSUMPTION_WEAKENING:
                raise NoAssumptionWeakeningException(
                    f"No {learning_type.exp_type_str()} weakening produces realizable spec (las file UNSAT)"
                )
            else:
                raise NoWeakeningException(
                    f"No {learning_type.exp_type_str()} weakening produces realizable spec (las file UNSAT)")

        useful_adaptations: List[List[Adaptation]] = filter_useful_adaptations(adaptations)
        return useful_adaptations

    def find_all_exception_adaptations(self, spec, trace, cts, learning_type, violations) -> List[Tuple[int, List[Adaptation]]]:
        hm = deepcopy(self._hm)
        hm.set_enabled("ANTECEDENT_WEAKENING")
        hm.set_enabled("CONSEQUENT_WEAKENING")
        hm.set_enabled("INVARIANT_TO_RESPONSE_WEAKENING")
        return self.find_adaptations_with_heuristic(spec, trace, cts, learning_type, violations, hm)

    def find_antecedent_exception_adaptations(self, spec, trace, cts, learning_type, violations) -> List[Tuple[int, List[Adaptation]]]:
        hm = deepcopy(self._hm)
        hm.set_enabled("ANTECEDENT_WEAKENING")
        hm.set_disabled("CONSEQUENT_WEAKENING")
        hm.set_disabled("INVARIANT_TO_RESPONSE_WEAKENING")
        return self.find_adaptations_with_heuristic(spec, trace, cts, learning_type, violations, hm)

    def find_consequent_exception_adaptations(self, spec, trace, cts, learning_type, violations) -> List[Tuple[int, List[Adaptation]]]:
        hm = deepcopy(self._hm)
        hm.set_disabled("ANTECEDENT_WEAKENING")
        hm.set_enabled("CONSEQUENT_WEAKENING")
        hm.set_disabled("INVARIANT_TO_RESPONSE_WEAKENING")
        return self.find_adaptations_with_heuristic(spec, trace, cts, learning_type, violations, hm)

    def find_eventualisation_adaptations(self, spec, trace, cts, learning_type, violations) -> List[Tuple[int, List[Adaptation]]]:
        hm = deepcopy(self._hm)
        hm.set_disabled("ANTECEDENT_WEAKENING")
        hm.set_disabled("CONSEQUENT_WEAKENING")
        hm.set_enabled("INVARIANT_TO_RESPONSE_WEAKENING")
        return self.find_adaptations_with_heuristic(spec, trace, cts, learning_type, violations, hm)

    def find_adaptations_with_heuristic(self, spec, trace, cts, learning_type, violations, hm):
        self.spec_encoder.set_heuristic_manager(hm)
        ilasp: str = self.spec_encoder.encode_ILASP(spec, trace, cts, violations, learning_type)
        output: str = run_ILASP(ilasp)
        adaptations: Optional[
            List[Tuple[int, List[Adaptation]]]] = ILASPInterpreter.extract_learned_possible_adaptations(output)
        if not adaptations:
            return []
        return adaptations

    def get_spec_violations(self, spec: SpectraSpecification, trace, cts, learning_type) -> List[str]:
        asp: str = self.spec_encoder.encode_ASP(spec, trace, cts)
        violations = get_violations(asp, exp_type=learning_type.exp_type())
        if not violations:
            raise NoViolationException("Violation trace is not violating!")
        if learning_type == Learning.GUARANTEE_WEAKENING:
            deadlock_required = re.findall(r"entailed\((counter_strat_\d*_\d*)\)", ''.join(violations))
            violation_ct = re.findall(r"violation_holds\([^,]*,[^,]*,\s*(counter_strat_\d+_\d+)", ''.join(violations))
            if deadlock_required and not violation_ct:
                raise DeadlockRequiredException("Violation trace is not violating! Deadlock completion is required.")
        return violations


def filter_useful_adaptations(potential_adaptations: List[Tuple[int, List[Adaptation]]]) -> List[List[Adaptation]]:
    ev_adaptations = [(score, adaptations) for score, adaptations in potential_adaptations if
                      all(adaptation.type == "ev_temp_op" for adaptation in adaptations)]
    other_adaptations = [(score, adaptations) for score, adaptations in potential_adaptations if
                         (score, adaptations) not in ev_adaptations]
    top_adaptations = ([adaptations for score, adaptations in other_adaptations if
                        score == min(other_adaptations, key=lambda x: x[0])[0]] +
                       [adaptations for score, adaptations in ev_adaptations if
                        score == min(ev_adaptations, key=lambda x: x[0])[0]])
    return top_adaptations
