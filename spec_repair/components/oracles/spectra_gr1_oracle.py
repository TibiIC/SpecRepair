import re
from copy import deepcopy
from typing import Optional, List, Tuple

import jpype

from spec_repair.exceptions import SpecificationNotVerifiableException
from spec_repair.interfaces.ioracle import IOracle
from spec_repair.components.new_spec_encoder import NewSpecEncoder
from spec_repair.components.repair_data import RepairData
from spec_repair.model.counter_strategy import CounterStrategy
from spec_repair.model.counter_trace import cts_from_cs, CounterTrace
from spec_repair.helpers.parsers.spectra_cs_parser import SpectraCSParser
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import generate_temp_filename, write_to_file
from spec_repair.wrappers.spectra_toolbox import synthesise_extract_counter_strategies, \
    synthesise_check_realisability_only, run_all_unrealisable_cores
from spec_repair.wrappers.asp_wrappers import get_violations


def filter_counter_traces(cts: List[CounterTrace], spec: SpectraSpecification) -> List[CounterTrace]:
    unrealisable_cores = set(get_unrealisable_core_expression_names(spec))
    filtered_cts = []
    for ct in cts:
        asp: str = NewSpecEncoder.encode_ASP(spec, [""], [ct])
        violations = get_violations(asp)
        if not violations:
            filtered_cts.append(ct)
        else:
            pattern = r'violation_holds\(\s*([^,]+),'
            violated_expressions = set(re.findall(pattern, violations[0]))
            guarantees = set(re.findall(r'guarantee\(\s*([^)]+)\s*\)', violations[0]))
            violated_guarantees = violated_expressions.intersection(guarantees)
            if not violated_guarantees - unrealisable_cores:
                filtered_cts.append(ct)
    return filtered_cts

def _synthesise_or_reject(synthesise, spec: SpectraSpecification) -> Optional[str]:
    """
    Run a synthesis call, turning a JVM heap exhaustion into the same named
    exception `_reject_unverifiable` raises.

    Spectra's BDD engine can exhaust the heap on a large enough state space -
    measured on colorsort, which does it even with the JVM's default 15.7 GB
    max heap on a 62 GB machine, so this is not a `-Xmx` misconfiguration. The
    error surfaced as `java.lang.OutOfMemoryError` propagating out of jpype and
    killing the entire case study.

    Treating it as "not verifiable" is the honest reading: Spectra never
    reached a verdict, exactly as when `violations_in_initial_conditions`
    rejects a file up front, and the caller already knows to end that branch
    and continue. It is emphatically *not* "unrealisable" - that would record a
    verdict the tool never gave.
    """
    try:
        return synthesise()
    except jpype.JException as e:
        if "OutOfMemoryError" not in str(type(e).__name__) and "OutOfMemoryError" not in str(e):
            raise
        raise SpecificationNotVerifiableException(
            "Spectra ran out of heap checking this specification: its BDD engine "
            "exhausted the JVM heap before reaching a verdict.\n"
            f"{spec.to_str()}") from e


def _reject_unverifiable(output: Optional[str], spec: SpectraSpecification) -> None:
    """
    Turn "Spectra could not check this" into a named exception.

    The synthesis wrappers return None - not output - when
    `violations_in_initial_conditions` rejects the file up front: an initial
    condition referring to a primed variable, or an initial assumption referring
    to a system variable. Every caller here then ran `re.search` over that None
    and died with `TypeError: expected string or bytes-like object`, several
    frames from the cause and saying nothing about it.

    Raising instead of returning a verdict is deliberate. There is no honest
    answer to give: "realisable" would record a malformed specification as a
    repair, and "unrealisable" would claim a verdict Spectra never reached. The
    caller decides what to do with a candidate it cannot check.
    """
    if output is None:
        raise SpecificationNotVerifiableException(
            "Spectra could not check this specification: it breaks a structural rule of the "
            "CLI (an initial condition referring to a primed variable, or an initial "
            "assumption referring to a system variable).\n"
            f"{spec.to_str()}")


def get_unrealisable_core_expression_names(spec: SpectraSpecification) -> List[str]:
    unrealisable_cores = run_all_unrealisable_cores(spec.to_str(is_to_compile=True))
    return list(set().union(*unrealisable_cores))

class SpectraGR1Oracle(IOracle):
    def __init__(self):
        self._ct_cnt = 0
        self._hm = None

    def is_valid_or_counter_arguments(
            self,
            new_spec: SpectraSpecification,
            data: RepairData
    ) -> Optional[List[Tuple[CounterTrace, RepairData]]]:
        counter_strategy = self._synthesise_and_check(new_spec)
        if counter_strategy:
            all_counter_traces = cts_from_cs(counter_strategy, cs_id=self._ct_cnt)
            possible_counter_traces = filter_counter_traces(all_counter_traces, new_spec)
            if self._hm:
                possible_counter_traces = self._hm.select_counter_traces(possible_counter_traces)
            self._ct_cnt += 1
            possible_counter_traces_with_data = [(possible_counter_trace, deepcopy(data)) for possible_counter_trace in possible_counter_traces]
            return possible_counter_traces_with_data
        else:
            return None

    @staticmethod
    def is_realisable(
            spec: SpectraSpecification
    ) -> bool:
        """
        Uses Spectra under the hood to check whether specifcation is realisable.
        If it is, nothing is returned. Otherwise, it returns a CounterStrategy.

        Deliberately uses the lightweight synthesis path (no
        --counter-strategy) rather than _synthesise/_synthesise_and_check's
        one: this method only ever reads the realizable/unrealizable verdict
        out of the CLI output, never the counter-strategy itself, and
        --counter-strategy extraction can be dramatically more expensive for
        large state spaces (confirmed: ran the JVM's BDD engine out of heap
        memory on a spec where the lightweight check completes in seconds).
        _synthesise_and_check (used by is_valid_or_counter_arguments, which
        genuinely needs a CounterStrategy object) is untouched.
        """
        output = _synthesise_or_reject(
            lambda: SpectraGR1Oracle._synthesise_realisability_only(spec), spec)
        _reject_unverifiable(output, spec)
        if re.search("Result: Specification is unrealizable", output):
            return False
        elif re.search("Result: Specification is realizable", output):
            return True
        else:
            raise Exception(output)

    def _synthesise_and_check(self, spec: SpectraSpecification) -> Optional[CounterStrategy]:
        """
        Uses Spectra under the hood to check whether specifcation is realisable.
        If it is, nothing is returned. Otherwise, it returns a CounterStrategy.
        """
        output = _synthesise_or_reject(lambda: self._synthesise(spec), spec)
        _reject_unverifiable(output, spec)
        if re.search("Result: Specification is unrealizable", output):
            return SpectraCSParser.from_str(output)
        elif re.search("Result: Specification is realizable", output):
            return None
        else:
            raise Exception(output)

    @staticmethod
    def _synthesise(spec: SpectraSpecification):
        spec_str = spec.to_str(is_to_compile=True)
        spectra_file: str = generate_temp_filename(ext=".spectra")
        write_to_file(spectra_file, spec_str)
        return synthesise_extract_counter_strategies(spectra_file)

    @staticmethod
    def _synthesise_realisability_only(spec: SpectraSpecification):
        spec_str = spec.to_str(is_to_compile=True)
        spectra_file: str = generate_temp_filename(ext=".spectra")
        write_to_file(spectra_file, spec_str)
        return synthesise_check_realisability_only(spectra_file)
