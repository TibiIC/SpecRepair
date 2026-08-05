"""
BFS repair over the trace-violation case studies.

The counterpart to `test_bfs_repair_orchestrator.py`'s `*_syn` tests, for the
setup in `input-files/case-studies/spectra/trace_violation/`. Two differences,
both from the pivot away from artificial strengthening:

* the specification to repair is `original.spectra`, not `strong.spectra` - it
  is a real specification rather than one manufactured by mutating a known-good
  one, so there is no "correct answer" to compare against and these tests assert
  only that repair runs and produces something;
* each case study has **five** traces rather than one, each violating a
  different group of assumptions, so there are five independent runs per case
  study rather than one.

One test method per (case study, trace), generated at import so each gets its
own name and can be selected individually - which is what
`run_parallel_bfs_repair_trace.sh` needs to give each its own tmux window:

    test_bfs_repair_trace_violation_minepump_0_syn
    test_bfs_repair_trace_violation_minepump_1_syn
    ...

Output goes to `test_files/out/repair_trace_syn/<case_study>_trace<ID>_<date>/`,
which is the layout `pull_experiment_from_ssh.sh` expects under a different
REMOTE_SUBDIR.
"""
import os
import re
from datetime import datetime
from typing import List

from main.bfs_repair_orchestrator import BFSRepairOrchestrator
from main.bfs_repair_orchestrator_builder import BFSRepairOrchestratorBuilder, learner_from_env
from spec_repair.components.repair_data import RepairData
from spec_repair.enums import Learning
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import read_file_lines
from tests.base_test_case import BaseTestCase
from tests.test_main.test_bfs_repair_orchestrator import learner_suffix, save_layered_graph

CASE_STUDIES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "input-files", "case-studies", "spectra", "trace_violation")

ORIGINAL_SPEC = "original.spectra"
TRACE_RE = re.compile(r"^violation_trace_(\d+)\.txt$")

# arbiter has no traces: its only assumption is `GF(a)`, and a liveness formula
# is vacuously satisfied on a finite prefix, so no violating trace exists at any
# length. Discovering that from a missing-file error at run time would be
# confusing, so case studies are enumerated by what they actually have.


def discover_case_studies() -> List[tuple]:
    """[(case_study, trace_id), ...] for every trace that exists on disk."""
    found = []
    if not os.path.isdir(CASE_STUDIES_DIR):
        return found
    for name in sorted(os.listdir(CASE_STUDIES_DIR)):
        case_study_dir = os.path.join(CASE_STUDIES_DIR, name)
        if not os.path.isfile(os.path.join(case_study_dir, ORIGINAL_SPEC)):
            continue
        trace_ids = sorted(
            int(m.group(1)) for m in
            (TRACE_RE.match(f) for f in os.listdir(case_study_dir)) if m
        )
        found.extend((name, trace_id) for trace_id in trace_ids)
    return found


class TestBFSRepairTraceViolation(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.date_str = datetime.now().strftime("%Y-%m-%d")
        cls.learner = learner_from_env()
        cls.learner_suffix = learner_suffix(cls.learner)

    def run_bfs_repair_trace_syn(self, case_study_name: str, trace_id: int,
                                 out_test_dir_name: str = None, is_debug: bool = True) -> List[str]:
        """
        Repair `original.spectra` against one of its violating traces.

        Mirrors `run_bfs_repair_syn_unique`, with `original.spectra` in the role
        `strong.spectra` used to play and a numbered trace instead of the single
        `violation_trace.txt`.
        """
        case_study_path = os.path.join(CASE_STUDIES_DIR, case_study_name)
        if not out_test_dir_name:
            out_test_dir_name = (f"./test_files/out/repair_trace_syn/"
                                 f"{case_study_name}_trace{trace_id}"
                                 f"{self.learner_suffix}_{self.date_str}")
        log_file = f"{out_test_dir_name}/log.txt"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        os.makedirs(out_test_dir_name, exist_ok=True)
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)

        spec = SpectraSpecification.from_file(os.path.join(case_study_path, ORIGINAL_SPEC))
        trace = read_file_lines(os.path.join(case_study_path, f"violation_trace_{trace_id}.txt"))

        builder = (BFSRepairOrchestratorBuilder.syntactic()
                   .enabling("INCLUDE_NEXT", "INCLUDE_PREV")
                   .using_learner(self.learner)
                   .with_log_file(log_file)
                   .with_on_record(lambda r, idx, s, d: save_layered_graph(r._om._graph, out_test_dir_name)))
        if is_debug:
            builder.with_debug_dir(out_test_dir_name)
        repairer: BFSRepairOrchestrator = builder.build()

        repairer.repair_bfs(spec, RepairData(trace, counter_traces=[],
                                             learning_type=Learning.ASSUMPTION_WEAKENING))
        new_spec_strings: List[str] = repairer.recorder.get_specs()
        save_layered_graph(repairer._om._graph, out_test_dir_name)
        return new_spec_strings


def _make_test(case_study_name: str, trace_id: int):
    def test(self):
        new_spec_strings = self.run_bfs_repair_trace_syn(case_study_name, trace_id, is_debug=True)
        print(f"{case_study_name} trace {trace_id}: {len(new_spec_strings)} repaired spec(s)")
        # No expected-output comparison: unlike the strengthened setup, nothing
        # here manufactured the specification, so there is no known answer to
        # check against. Repair producing at least one weakening is the claim.
        self.assertGreater(len(new_spec_strings), 0,
                           f"{case_study_name} trace {trace_id} produced no repaired specification")
    test.__name__ = f"test_bfs_repair_trace_violation_{case_study_name}_{trace_id}_syn"
    return test


for _case_study, _trace_id in discover_case_studies():
    _method = _make_test(_case_study, _trace_id)
    setattr(TestBFSRepairTraceViolation, _method.__name__, _method)
