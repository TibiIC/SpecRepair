import os
import re
import subprocess
from typing import Optional
import pickle
import unittest
from datetime import datetime

import networkx as nx
from pyvis.network import Network

from main.bfs_repair_orchestrator import BFSRepairOrchestrator
from main.bfs_repair_orchestrator_builder import (
    BFSRepairOrchestratorBuilder,
    DEFAULT_LEARNER,
    learner_from_env,
)
from spec_repair.components.repair_data import RepairData
from spec_repair.enums import Learning
from spec_repair.components.heuristic_managers.choose_first_heuristic_manager import ChooseFirstHeuristicManager
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import read_file_lines, write_to_file
from spec_repair.wrappers.spectra_toolbox import synthesise_controller
from tests.base_test_case import BaseTestCase


# Rendering the debug graph is optional work on a growing artefact, and it runs
# on every record. Both limits below exist because of measured stalls, not
# caution: on the 2026-08-07 sweep six of gpu11's eight jobs sat at 0% CPU for
# over twelve hours, each blocked in `futex_do_wait` on a child `dot -Tpng` that
# never returned. The runs were not verifying or learning - `status.txt` said
# "verifying d1 candidate" and the logs had stopped after two minutes - they were
# inside Graphviz.
GRAPH_RENDER_TIMEOUT = int(os.environ.get("SPEC_REPAIR_GRAPH_TIMEOUT", "30"))
GRAPH_RENDER_MAX_NODES = int(os.environ.get("SPEC_REPAIR_GRAPH_MAX_NODES", "400"))

# The deepest search depth each output directory has had a picture drawn for.
# The callback fires on every record - a run reaching 255 leaves redrew a
# growing graph 255 times - but the graph only changes shape meaningfully as the
# search descends, so one picture per depth captures the same story for a
# fraction of the work.
_rendered_depth: dict = {}


def _render_png(A, path: str) -> None:
    """
    Draw with `dot`, but never wait on it indefinitely.

    `pygraphviz`'s `A.draw(prog="dot")` spawns a subprocess with no timeout, so
    a graph `dot` cannot lay out quickly hangs the run that produced it - the
    Python process blocks on the child and neither ever finishes. Driving the
    subprocess directly is the only way to bound it.
    """
    dot_source = A.to_string()
    proc = subprocess.run(["dot", "-Tpng", "-o", path],
                          input=dot_source, text=True,
                          capture_output=True, timeout=GRAPH_RENDER_TIMEOUT)
    if proc.returncode != 0:
        raise RuntimeError(f"dot exited {proc.returncode}: {proc.stderr.strip()[:200]}")


def save_layered_graph(G: nx.DiGraph, filepath: str, depth: Optional[int] = None):
    """
    Write the debug graph: a pickle of the data, a PNG, and an interactive HTML.

    Everything here is a *debug artefact*, and this runs on every record via
    `with_on_record`, so nothing in it may end - or stall - the repair run.

    The pickle is written first and deliberately not guarded: it is a local
    `pickle.dump` with no subprocess behind it, and it is the artefact worth
    keeping, since both pictures can be regenerated from it afterwards.

    The pictures are skipped entirely once the graph passes
    GRAPH_RENDER_MAX_NODES. A layout of a few thousand nodes is unreadable as a
    picture regardless, so the choice is between an image nobody can use and a
    run that finishes.

    They are also drawn at most once per search depth. `depth` is the caller's
    `data.learning_steps`; passing None keeps the old draw-every-time behaviour
    for anything that has no depth to give.
    """
    with open(f"{filepath}/graph.pkl", "wb") as f:
        pickle.dump(G, f)

    if G.number_of_nodes() > GRAPH_RENDER_MAX_NODES:
        return

    if depth is not None:
        if _rendered_depth.get(filepath) == depth:
            return
        _rendered_depth[filepath] = depth

    try:
        A = nx.nx_agraph.to_agraph(G)
        A.node_attr.update(fontsize=24)

        # Find the node with '0' in its label
        target_node_name = None
        for node_name in G.nodes():
            if node_name == 0:
                target_node_name = node_name
            if '#' in str(node_name):
                leaf_node = A.get_node(node_name)
                leaf_node.attr['color'] = 'blue'
        if target_node_name is not None:
            A.get_node(target_node_name).attr['penwidth'] = '5'

        _render_png(A, f"{filepath}/graph.png")
    except subprocess.TimeoutExpired:
        print(f"Graph render exceeded {GRAPH_RENDER_TIMEOUT}s and was abandoned; "
              f"graph.pkl is still written.")
    except Exception as e:
        print(f"Could not render {filepath}/graph.png ({type(e).__name__}: {e}); "
              f"graph.pkl is still written.")

    try:
        # Create the interactive visualization
        net = Network(height="800px", width="100%")
        net.from_nx(G)
        # Write the HTML file
        net.write_html(f"{filepath}/graph.html")
    except Exception as e:
        print(f"Could not write {filepath}/graph.html ({type(e).__name__}: {e}); "
              f"graph.pkl is still written.")


def learner_suffix(learner: str) -> str:
    """
    `_<learner>` always - `_ilasp` as much as `_fastlas`.

    It used to be empty for the default learner, so that ILASP kept producing
    the unsuffixed paths everything downstream had been written against. That
    convenience cost more than it saved:

    * the two arms of a sweep were shaped differently, so anything iterating
      over runs needed to know which learner produced which name;
    * an unsuffixed directory is indistinguishable from *any* older ILASP run at
      the same date, which is the trap `running-on-ssh.md` already warns about
      under "run directories are not cleared between sweeps";
    * a query for the ILASP results of a live sweep reported `NO_DIR` for all
      thirteen running jobs, which read exactly like "produced nothing" -
      measured on 2026-08-14.

    Old unsuffixed directories are unaffected: this changes where *new* runs
    write, not how existing results are read.
    """
    return f"_{learner}"


def run_date_str() -> str:
    """
    The date stamped into every output directory name for this sweep.

    `datetime.now()` is evaluated when the *job* starts, not when the sweep
    does, and a sweep runs its jobs through a concurrency semaphore over many
    hours. A sweep launched at 20:11 therefore stamps the jobs that start
    before midnight `_2026-08-08` and the ones that start after `_2026-08-09`,
    splitting one experiment across two directory names. That is not cosmetic:
    `pull_experiment_from_ssh.sh` and every pipeline step after it select a run
    by globbing `*_<date>`, so half the results are silently left on the
    remote - and a two-day sweep scatters across three.

    `SPEC_REPAIR_RUN_DATE` lets the runner resolve the date once at launch and
    hand the same value to every job. Unset, the old behaviour stands, so a
    developer running a single test still gets today's date.
    """
    stamped = os.environ.get("SPEC_REPAIR_RUN_DATE", "").strip()
    if not stamped:
        return datetime.now().strftime("%Y-%m-%d")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", stamped):
        raise ValueError(
            f"SPEC_REPAIR_RUN_DATE='{stamped}' must look like YYYY-MM-DD. It "
            f"becomes part of an output directory name that the experiment "
            f"pipeline selects on.")
    return stamped


class TestCaseStudy1(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.date_str = run_date_str()
        # Read once per class: a mid-run change would make half the results
        # ILASP's and half FastLAS's under one directory name.
        cls.learner = learner_from_env()
        cls.learner_suffix = learner_suffix(cls.learner)

    def test_case_study_1_arbiter(self):
        case_study_name = 'arbiter'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/arbiter'
        new_spec_strings = self.run_bfs_repair_sem_unique(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_case_study_1_traffic_single(self):
        case_study_name = 'traffic_single'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/traffic_single'
        new_spec_strings = self.run_bfs_repair_sem_unique(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_case_study_1_traffic_updated(self):
        case_study_name = 'traffic_updated'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/traffic_updated'
        new_spec_strings = self.run_bfs_repair_sem_unique(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_case_study_1_lift(self):
        case_study_name = 'lift'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/lift'
        new_spec_strings = self.run_bfs_repair_sem_unique(
            case_study_name,
            case_study_path,
            is_debug=True
        )

        expected_specs_files: list[str] = os.listdir('./test_files/lift_weakenings/2026_06_03')
        expected_specs: list[SpectraSpecification] = [
            SpectraSpecification.from_file(f"./test_files/lift_weakenings/2026_06_03/{spec_file}")
            for spec_file in expected_specs_files
        ]

        actual_specs: list[SpectraSpecification] = [
            SpectraSpecification.from_str(new_spec_string)
            for new_spec_string in new_spec_strings
        ]

        self.assertEqual(len(expected_specs), len(new_spec_strings))

        for i, expected_specs in enumerate(expected_specs):
            print(i)
            self.assertIn(expected_specs.to_str(), new_spec_strings)

    def test_case_study_1_minepump(self):
        case_study_name = 'minepump'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/minepump'
        new_spec_strings = self.run_bfs_repair_sem_unique(case_study_name, case_study_path, is_debug=True)

        expected_specs_files: list[str] = os.listdir('./test_files/minepump_weakenings')
        expected_spec_strings: list[SpectraSpecification] = [
            SpectraSpecification.from_file(f"./test_files/minepump_weakenings/{spec_file}")
            for spec_file in expected_specs_files
        ]

        self.assertEqual(len(expected_spec_strings), len(new_spec_strings))
        for i, expected_spec in enumerate(expected_spec_strings):
            print(i)
            self.assertIn(expected_spec.to_str(), new_spec_strings)

    def test_case_study_1_submarine(self):
        case_study_name = 'submarine'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/submarine'
        new_spec_strings = self.run_bfs_repair_sem_unique(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_case_study_1_arbiter_syn(self):
        case_study_name = 'arbiter'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/arbiter'
        new_spec_strings = self.run_case_study_1_repair(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_case_study_1_traffic_single_syn(self):
        case_study_name = 'traffic_single'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/traffic_single'
        new_spec_strings = self.run_case_study_1_repair(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_case_study_1_traffic_updated_syn(self):
        case_study_name = 'traffic_updated'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/traffic_updated'
        new_spec_strings = self.run_case_study_1_repair(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_case_study_1_lift_syn(self):
        case_study_name = 'lift'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/lift'
        new_spec_strings = self.run_case_study_1_repair(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_case_study_1_minepump_syn(self):
        case_study_name = 'minepump'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/minepump'
        new_spec_strings = self.run_case_study_1_repair(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_case_study_1_amba_syn(self):
        """
        AMBA AHB. Its source uses arrays, Int ranges, predicates, forall,
        quantified templates and Dwyer patterns; amba_desugar lowers those into
        the boolean+enum subset enum_desugar takes. 63 formulas, 34 atoms.
        """
        case_study_name = 'amba'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/amba'
        new_spec_strings = self.run_case_study_1_repair(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_case_study_1_genbuf_syn(self):
        """
        Generalised buffer. Its formulas are unnamed in the source, which the
        parser silently ignored - the previous strong.spectra here loaded as an
        empty specification. Regenerated through enum_desugar: 109 formulas.
        """
        case_study_name = 'genbuf'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/genbuf'
        new_spec_strings = self.run_case_study_1_repair(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_case_study_1_colorsort_syn(self):
        case_study_name = 'colorsort'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/colorsort'
        new_spec_strings = self.run_case_study_1_repair(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_case_study_1_gyro_syn(self):
        case_study_name = 'gyro'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/gyro'
        new_spec_strings = self.run_case_study_1_repair(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_case_study_1_elevator_syn(self):
        case_study_name = 'elevator'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/elevator'
        new_spec_strings = self.run_case_study_1_repair(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_case_study_1_humanoid_syn(self):
        case_study_name = 'humanoid'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/humanoid'
        new_spec_strings = self.run_case_study_1_repair(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_case_study_1_pcar_syn(self):
        case_study_name = 'pcar'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/pcar'
        new_spec_strings = self.run_case_study_1_repair(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    # The *_updated case studies below share each original's ideal.spectra but
    # pair it with a strong.spectra that strengthens at least one assumption
    # AND at least one guarantee. The original fixtures all happen to be
    # assumption-only, so these exercise the guarantee-weakening half of the
    # repair search against a violation that genuinely requires it.
    def test_case_study_1_elevator_updated_syn(self):
        case_study_name = 'elevator_updated'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/elevator_updated'
        new_spec_strings = self.run_case_study_1_repair(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_case_study_1_gyro_updated_syn(self):
        case_study_name = 'gyro_updated'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/gyro_updated'
        new_spec_strings = self.run_case_study_1_repair(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_case_study_1_humanoid_updated_syn(self):
        case_study_name = 'humanoid_updated'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/humanoid_updated'
        new_spec_strings = self.run_case_study_1_repair(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_case_study_1_pcar_updated_syn(self):
        case_study_name = 'pcar_updated'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/pcar_updated'
        new_spec_strings = self.run_case_study_1_repair(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_case_study_1_lift_updated_syn(self):
        case_study_name = 'lift_updated'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/lift_updated'
        new_spec_strings = self.run_case_study_1_repair(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_case_study_1_traffic_updated_updated_syn(self):
        case_study_name = 'traffic_updated_updated'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/traffic_updated_updated'
        new_spec_strings = self.run_case_study_1_repair(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_case_study_1_colorsort_updated_syn(self):
        case_study_name = 'colorsort_updated'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/colorsort_updated'
        new_spec_strings = self.run_case_study_1_repair(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_case_study_1_arbiter_asm_only(self):
        case_study_name = 'arbiter'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/arbiter'
        intermediate_spec_strings, new_spec_strings = self.run_bfs_asm_only_repair_sem_unique(
            case_study_name,
            case_study_path,
            is_debug=True
        )
        print(len(intermediate_spec_strings))
        print(len(new_spec_strings))

    def test_case_study_1_traffic_single_asm_only(self):
        case_study_name = 'traffic_single'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/traffic_single'
        intermediate_spec_strings, new_spec_strings = self.run_bfs_asm_only_repair_sem_unique(
            case_study_name,
            case_study_path,
            is_debug=True
        )
        print(len(intermediate_spec_strings))
        print(len(new_spec_strings))

    def test_case_study_1_traffic_updated_asm_only(self):
        case_study_name = 'traffic_updated'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/traffic_updated'
        intermediate_spec_strings, new_spec_strings = self.run_bfs_asm_only_repair_sem_unique(
            case_study_name,
            case_study_path,
            is_debug=True
        )
        print(len(intermediate_spec_strings))
        print(len(new_spec_strings))

    def test_case_study_1_lift_asm_only(self):
        case_study_name = 'lift'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/lift'
        intermediate_spec_strings, new_spec_strings = self.run_bfs_asm_only_repair_sem_unique(
            case_study_name,
            case_study_path,
            is_debug=True
        )
        print(len(intermediate_spec_strings))
        print(len(new_spec_strings))

    def test_case_study_1_minepump_asm_only(self):
        case_study_name = 'minepump'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/minepump'
        intermediate_spec_strings, new_spec_strings = self.run_bfs_asm_only_repair_sem_unique(
            case_study_name,
            case_study_path,
            is_debug=True
        )
        print(len(intermediate_spec_strings))
        print(len(new_spec_strings))

    @unittest.skip("skip test")
    def test_single_repair_spec_minepump(self):
        case_study_name = 'minepump'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/minepump'
        out_test_dir_name = "./test_files/out/minepump_single"
        new_spec_strings = self.run_single_repair(case_study_name, case_study_path, out_test_dir_name)
        print(new_spec_strings)

    @unittest.skip("skip test")
    def test_single_repair_spec_minepump_liveness(self):
        case_study_name = 'minepump_liveness'
        case_study_path = '../input-files/case-studies/spectra/case_study_1/minepump_liveness'
        out_test_dir_name = "./test_files/out/minepump_liveness_single"
        new_spec_strings = self.run_single_repair(case_study_name, case_study_path, out_test_dir_name)
        print(new_spec_strings)

    def run_bfs_asm_only_repair_sem_unique(self, case_study_name, case_study_path, out_test_dir_name=None,
                                           is_debug=False):
        if not out_test_dir_name:
            out_test_dir_name = f"./test_files/out/repair_asm_only/{case_study_name}{self.learner_suffix}_{self.date_str}"
        log_file = f"{out_test_dir_name}/log.txt"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if not os.path.exists(out_test_dir_name):
            os.makedirs(out_test_dir_name, exist_ok=True)
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        spec: SpectraSpecification = SpectraSpecification.from_file(f"{case_study_path}/strong.spectra")
        trace: list[str] = read_file_lines(f"{case_study_path}/violation_trace.txt")
        builder = (BFSRepairOrchestratorBuilder.assumption_only()
                   .enabling("INCLUDE_NEXT", "INCLUDE_PREV")
                   .using_learner(self.learner)
                   .with_run_label(f"case_study_1 / {case_study_name}")
                   .with_log_file(log_file)
                   .with_on_record(lambda r, idx, s, d: save_layered_graph(r._om._graph, out_test_dir_name, d.learning_steps)))
        if is_debug:
            builder.with_debug_dir(out_test_dir_name)
        repairer: BFSRepairOrchestrator = builder.build()

        repairer.repair_bfs(spec, RepairData(trace, counter_traces=[], learning_type=Learning.ASSUMPTION_WEAKENING))
        intermediate_spec_strings: list[str] = repairer.intermediate_recorder.get_specs()
        new_spec_strings: list[str] = repairer.recorder.get_specs()
        save_layered_graph(repairer._om._graph, out_test_dir_name)
        return intermediate_spec_strings, new_spec_strings

    def run_bfs_repair_sem_unique(self, case_study_name, case_study_path, out_test_dir_name=None, is_debug=False):
        if not out_test_dir_name:
            out_test_dir_name = f"./test_files/out/repair/{case_study_name}{self.learner_suffix}_{self.date_str}"
        log_file = f"{out_test_dir_name}/log.txt"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if not os.path.exists(out_test_dir_name):
            os.makedirs(out_test_dir_name, exist_ok=True)
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        spec: SpectraSpecification = SpectraSpecification.from_file(f"{case_study_path}/strong.spectra")
        trace: list[str] = read_file_lines(f"{case_study_path}/violation_trace.txt")
        builder = (BFSRepairOrchestratorBuilder.semantic()
                   .enabling("INCLUDE_NEXT", "INCLUDE_PREV")
                   .using_learner(self.learner)
                   .with_run_label(f"case_study_1 / {case_study_name}")
                   .with_log_file(log_file)
                   .with_on_record(lambda r, idx, s, d: save_layered_graph(r._om._graph, out_test_dir_name, d.learning_steps)))
        if is_debug:
            builder.with_debug_dir(out_test_dir_name)
        repairer: BFSRepairOrchestrator = builder.build()

        repairer.repair_bfs(spec, RepairData(trace, counter_traces=[], learning_type=Learning.ASSUMPTION_WEAKENING))
        new_spec_strings: list[str] = repairer.recorder.get_specs()
        save_layered_graph(repairer._om._graph, out_test_dir_name)
        return new_spec_strings

    def run_single_repair(self, case_study_name, case_study_path, out_test_dir_name, is_debug=False):
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        log_file = f"{out_test_dir_name}/log.txt"
        if not os.path.exists(out_test_dir_name):
            os.makedirs(out_test_dir_name, exist_ok=True)
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        spec: SpectraSpecification = SpectraSpecification.from_file(f"{case_study_path}/strong.spectra")
        trace: list[str] = read_file_lines(f"{case_study_path}/violation_trace.txt")
        # Note: this previously passed hm/recorder/logger positionally into the
        # om/hm/recorder slots, so the heuristic manager was silently installed
        # as the orchestration manager. The builder makes those slots explicit.
        builder = (BFSRepairOrchestratorBuilder.semantic()
                   .with_heuristic_manager(ChooseFirstHeuristicManager())
                   .using_learner(self.learner)
                   .with_run_label(f"case_study_1 / {case_study_name}")
                   .with_log_file(log_file))
        if is_debug:
            builder.with_flat_debug_dir(out_test_dir_name)
        repairer: BFSRepairOrchestrator = builder.build()
        # Getting all possible repairs
        repairer.repair_bfs(spec, RepairData(trace, counter_traces=[],
                                             learning_type=Learning.ASSUMPTION_WEAKENING))
        new_spec_strings: list[str] = repairer.recorder.get_specs()
        for i, new_spec in enumerate(new_spec_strings):
            write_to_file(f"{out_test_dir_name}/{case_study_name}_fix_{i}.spectra", new_spec)
        assert len(new_spec_strings) == 1, "Expected exactly one new specification after single repair."
        synthesise_controller(
            f"{os.getcwd()}/{out_test_dir_name}/{case_study_name}_fix_0.spectra",
            f"{os.getcwd()}/{out_test_dir_name}/{case_study_name}_controller",
        )
        return new_spec_strings

    def run_case_study_1_repair(self, case_study_name, case_study_path, out_test_dir_name=None, is_debug=False):
        if not out_test_dir_name:
            out_test_dir_name = f"./test_files/out/case_study_1/{case_study_name}{self.learner_suffix}_{self.date_str}"
        log_file = f"{out_test_dir_name}/log.txt"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if not os.path.exists(out_test_dir_name):
            os.makedirs(out_test_dir_name, exist_ok=True)
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        spec: SpectraSpecification = SpectraSpecification.from_file(f"{case_study_path}/strong.spectra")
        trace: list[str] = read_file_lines(f"{case_study_path}/violation_trace.txt")
        builder = (BFSRepairOrchestratorBuilder.syntactic()
                   .enabling("INCLUDE_NEXT", "INCLUDE_PREV")
                   .using_learner(self.learner)
                   .with_run_label(f"case_study_1 / {case_study_name}")
                   .with_log_file(log_file)
                   .with_on_record(lambda r, idx, s, d: save_layered_graph(r._om._graph, out_test_dir_name, d.learning_steps)))
        if is_debug:
            builder.with_debug_dir(out_test_dir_name)
        repairer: BFSRepairOrchestrator = builder.build()

        repairer.repair_bfs(spec, RepairData(trace, counter_traces=[], learning_type=Learning.ASSUMPTION_WEAKENING))
        new_spec_strings: list[str] = repairer.recorder.get_specs()
        save_layered_graph(repairer._om._graph, out_test_dir_name)
        return new_spec_strings
