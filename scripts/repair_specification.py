import argparse
from typing import Optional

from main.bfs_repair_orchestrator import BFSRepairOrchestrator
from main.bfs_repair_orchestrator_builder import BFSRepairOrchestratorBuilder
from spec_repair.components.repair_data import RepairData
from spec_repair.enums import Learning
from spec_repair.components.heuristic_managers.choose_first_heuristic_manager import ChooseFirstHeuristicManager
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import write_to_file, read_file_lines


def run_single_repair(spec_path: str, trace_path: str, out_spec_path, out_test_dir_name: Optional[str] = None):
    spec: SpectraSpecification = SpectraSpecification.from_file(spec_path)
    trace: list[str] = read_file_lines(trace_path)
    # Previously constructed an undefined `NewSpecOracle()` and passed
    # hm/recorder/logger positionally into the om/hm/recorder slots; the builder
    # supplies the Spectra oracle by default and names every slot.
    builder = (BFSRepairOrchestratorBuilder.semantic()
               .with_heuristic_manager(ChooseFirstHeuristicManager()))
    if out_test_dir_name:
        builder.with_flat_debug_dir(out_test_dir_name)
    repairer: BFSRepairOrchestrator = builder.build()
    # Getting all possible repairs
    repairer.repair_bfs(spec, RepairData(trace, counter_traces=[],
                                         learning_type=Learning.ASSUMPTION_WEAKENING))
    new_spec_strings: list[str] = [spec.to_str() for spec in repairer.recorder.get_all_values()]
    assert len(new_spec_strings) == 1, "Expected exactly one new specification after single repair."
    write_to_file(out_spec_path, new_spec_strings[0])
    return new_spec_strings


def main():
    parser = argparse.ArgumentParser(description='Run single repair on specification')
    parser.add_argument('spec_path', help='Path to the specification file')
    parser.add_argument('trace', help='Path to the trace file')
    parser.add_argument('out_spec_path', help='Path where to save the repaired specification')
    args = parser.parse_args()

    run_single_repair(args.spec_path, args.trace, args.out_spec_path)


if __name__ == "__main__":
    run_single_repair(
        "/Users/tg4018/Documents/PhD/SpecRepair/tests/test_files/shield_test/specs/spec_0.spectra",
        "/Users/tg4018/Documents/PhD/SpecRepair/tests/test_files/shield_test/specs/violation_trace_0.txt",
        "/Users/tg4018/Documents/PhD/SpecRepair/tests/test_files/shield_test/specs/spec_1.spectra"
    )
    # main()
