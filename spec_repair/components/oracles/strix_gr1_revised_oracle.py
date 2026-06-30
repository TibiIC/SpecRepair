import re
from copy import deepcopy
from typing import Optional, List, Tuple

from spec_repair.components.interfaces.ioracle import IOracle
from spec_repair.components.new_spec_encoder import NewSpecEncoder
from spec_repair.components.repair_data import RepairData
from spec_repair.helpers.counter_trace import cts_from_cs, CounterTrace
from spec_repair.helpers.formatters.spot_specification_formatter import SpotSpecificationFormatter
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.ltl_types import CounterStrategy
from spec_repair.util.file_util import generate_temp_filename, write_to_file
from spec_repair.util.spec_util import synthesise_extract_counter_strategies, run_all_unrealisable_cores
from spec_repair.wrappers.asp_wrappers import get_violations
from spec_repair.wrappers.strix import Strix

from spec_repair.ltl_types import GR1AtomType


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

def get_unrealisable_core_expression_names(spec: SpectraSpecification) -> List[str]:
    unrealisable_cores = run_all_unrealisable_cores(spec.to_str(is_to_compile=True))
    return list(set().union(*unrealisable_cores))

class StrixGR1RevisedOracle(IOracle):
    def __init__(self, strix_path: Optional[str] = None):
        self._ct_cnt = 0
        self._hm = None
        if strix_path:
            self._strix: Strix = Strix(binary=strix_path)
        else:
            self._strix: Strix = Strix()

    def is_valid_or_counter_arguments(
            self,
            new_spec: SpectraSpecification,
            data: RepairData
    ) -> Optional[List[Tuple[CounterTrace, RepairData]]]:
        raise NotImplementedError("This oracle does not support counter arguments")
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

    def is_realisable(
            self,
            spec: SpectraSpecification
    ) -> bool:
        """
        Uses Spectra under the hood to check whether specifcation is realisable.
        If it is, nothing is returned. Otherwise, it returns a CounterStrategy.
        """
        return self._call_realisability_check_strix(spec)

    def _synthesise_and_check(self, spec: SpectraSpecification) -> Optional[CounterStrategy]:
        """
        Uses Spectra under the hood to check whether specifcation is realisable.
        If it is, nothing is returned. Otherwise, it returns a CounterStrategy.
        """
        raise NotImplementedError("This oracle does not support counter arguments")
        output = self._synthesise(spec)
        if re.search("Result: Specification is unrealizable", output):
            output = str(output).split("\n")
            counter_strategy = list(filter(re.compile(r"\s*->\s*[^{]*{[^}]*").search, output))
            return counter_strategy
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

    def _call_realisability_check_strix(self, spec: SpectraSpecification) -> bool:
        # TODO: make formula use the revised realisability formula from
        #  "Revisiting Synthesis of GR(1) Specifications" by Uri Klein & Amir Pnueli
        formula = spec.to_formatted_string(SpotSpecificationFormatter())
        atoms = spec.get_atoms()
        env_atom_names = [atom.name for atom in atoms if atom.atom_type == GR1AtomType.ENV]
        sys_atom_names = [atom.name for atom in atoms if atom.atom_type == GR1AtomType.SYS]

        return self._strix.check_realizability(
            formula,
            env_atom_names,
            sys_atom_names
        ).realizable
