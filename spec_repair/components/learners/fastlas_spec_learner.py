"""
A learner that uses FastLAS instead of ILASP.

Everything outside this file is untouched: FastLASSpecLearner subclasses
OptimisingSpecLearner and overrides exactly one method,
`find_adaptations_with_heuristic`, which is the seam where the learning task is
handed to the solver and the answer parsed back. The orchestrator, oracle,
mitigator, discriminator and encoder are all unaware which solver is in use.

Two things have to be bridged.

**The task syntax.** FastLAS 2.1.0 does not accept the ILASP dialect the encoder
emits, so `translate_ilasp_task_to_fastlas` rewrites it - see that function for
the specifics and for what FastLAS silently ignores.

**Multiple solutions.** FastLAS returns a single solution per run, where ILASP
returns every optimal one, and the BFS search needs a set of candidate
adaptations to branch on. `n_runs` therefore invokes FastLAS repeatedly and
collects the distinct solutions.

    Measured caveat: FastLAS 2.1.0 is deterministic. On this repo's tasks,
    repeated invocations return byte-identical output - verified across six
    consecutive runs, with `--threads 4`, and with the mode declarations and
    constant facts shuffled under five different seeds. So `n_runs > 1`
    currently yields one distinct solution, at a cost of n_runs FastLAS
    invocations. The collection and deduplication are here so that a build
    which does randomise (or a future `--seed`) needs no further change, but
    with 2.1.0 the honest default is 1. Raising it is only worthwhile if you
    have reason to believe your FastLAS varies.
"""
import re
import subprocess
from typing import List, Optional, Tuple

from spec_repair.components.learners.optimising_final_spec_learner import OptimisingSpecLearner
from spec_repair.config import SETUP_DICT
from spec_repair.helpers.parsers.fastlas_interpreter import FastLASInterpreter
from spec_repair.interfaces.iheuristic_manager import IHeuristicManager
from spec_repair.components.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.model.adaptation_learned import Adaptation
from spec_repair.util.file_util import generate_temp_filename, write_to_file
from spec_repair.util.subprocess_util import create_cmd

# ILASP allows a recall bound and a (positive) annotation; FastLAS takes a bare
# schema and rejects the rest with "syntax error, unexpected T_COMMA".
_MODEB = re.compile(r"#modeb\(\s*\d+\s*,\s*(.+?)\s*,\s*\(\s*positive\s*\)\s*\)\.")
# FastLAS has no #constant directive - it errors with "Unknown token: '#'" - and
# instead draws const(t) values from a t/1 predicate in the background knowledge.
# Note the trailing `[ \t]*$` rather than `\s*$`: under re.MULTILINE a greedy
# `\s*` happily consumes the newline and matches `$` on a later line, which
# silently joined consecutive #constant lines together.
_CONSTANT = re.compile(r"^#constant\(\s*([^,]+?)\s*,\s*(.+?)\s*\)\.[ \t]*$", re.M)
# FastLAS requires an identifier as the first argument of an example.
_POS_NO_ID = re.compile(r"#pos\(\s*\{")

DEFAULT_FASTLAS_ARGS = ("--nopl", "--force-safety")


def translate_ilasp_task_to_fastlas(las: str) -> str:
    """
    Rewrite an ILASP learning task into the dialect FastLAS 2.1.0 accepts.

    Three rewrites, each for a construct FastLAS rejects outright:

    1. `#modeb(2, p(...), (positive)).` -> `#modeb(p(...)).`
    2. `#constant(type, value).` -> `type(value).` as a background fact, which
       is where FastLAS looks for the values of a `const(type)` placeholder.
       Ranges survive this unchanged: `#constant(index,0..0).` becomes
       `index(0..0).`, still a valid clingo fact.
    3. `#pos({...},{...},{...}).` -> `#pos(eg1,{...},{...},{...}).`

    **What FastLAS ignores:** the `#bias("...")` block. ILASP uses it for hard
    constraints on rule shape - matching the head's time/trace variables to the
    body's `timepoint_of_op`, forbidding contradictory `holds_at`/`not_holds_at`
    pairs, and so on. FastLAS's `#bias` is a scoring hook, not a constraint, and
    the block is accepted without effect: adding `:- body(k(_)).` to a task that
    had chosen `k` left the answer unchanged. FastLAS is therefore solving a
    *less constrained* problem than ILASP on the same task, and can in principle
    return a rule ILASP's bias would have excluded. In practice its preference
    for the shortest hypothesis makes that unlikely, since the shortest
    candidates are body-free facts that satisfy those constraints vacuously -
    but it is a real difference, not an equivalence.
    """
    las = _MODEB.sub(r"#modeb(\1).", las)
    las = _CONSTANT.sub(r"\1(\2).", las)

    counter = [0]

    def _add_example_id(_match) -> str:
        counter[0] += 1
        return f"#pos(eg{counter[0]},{{"

    return _POS_NO_ID.sub(_add_example_id, las)


class FastLASTaskError(RuntimeError):
    """Raised when FastLAS rejects the learning task itself."""


def run_fastlas(las: str, extra_args: Tuple[str, ...] = DEFAULT_FASTLAS_ARGS) -> str:
    """
    Run FastLAS over an already-translated task and return its stdout.

    stderr is captured separately and turned into an exception rather than
    discarded. FastLAS reports a malformed task ("syntax error, unexpected
    T_COMMA", "Unknown token: '#'") on stderr and writes *nothing* to stdout, so
    ignoring it would make a translation bug indistinguishable from "this branch
    found no adaptations" - the search would quietly explore nothing and report
    no repair.
    """
    las_file = generate_temp_filename(ext=".las")
    write_to_file(las_file, las)
    cmd = create_cmd(["FastLAS", *extra_args, las_file])
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    stdout, stderr = stdout.decode("utf-8"), stderr.decode("utf-8")
    if stderr.strip() and not stdout.strip():
        raise FastLASTaskError(
            f"FastLAS rejected the learning task: {stderr.strip()}\nTask written to {las_file}")
    return stdout


class FastLASSpecLearner(OptimisingSpecLearner):
    """
    OptimisingSpecLearner with FastLAS as the solver.

    :param n_runs: how many times to invoke FastLAS per learning step, keeping
        the distinct solutions. See the module docstring: FastLAS 2.1.0 is
        deterministic, so values above 1 currently cost extra invocations
        without yielding extra solutions.
    """

    def __init__(
            self,
            heuristic_manager: IHeuristicManager = NoFilterHeuristicManager(),
            n_runs: int = 1,
            fastlas_args: Tuple[str, ...] = DEFAULT_FASTLAS_ARGS,
    ):
        super().__init__(heuristic_manager=heuristic_manager)
        if n_runs < 1:
            raise ValueError(f"n_runs must be at least 1, got {n_runs}")
        self.n_runs = n_runs
        self.fastlas_args = tuple(fastlas_args)

    def find_adaptations_with_heuristic(self, spec, trace, cts, learning_type, violations, hm):
        self.spec_encoder.set_heuristic_manager(hm)
        las: str = self.spec_encoder.encode_ILASP(spec, trace, cts, violations, learning_type)
        fastlas_task: str = translate_ilasp_task_to_fastlas(las)

        adaptations: List[Tuple[int, List[Adaptation]]] = []
        seen = set()
        for _ in range(self.n_runs):
            output = run_fastlas(fastlas_task, self.fastlas_args)
            solutions: Optional[List[Tuple[int, List[Adaptation]]]] = \
                FastLASInterpreter.extract_learned_possible_adaptations(output)
            if not solutions:
                continue
            for score, solution in solutions:
                # Deduplicate on the rendered adaptations: an identical solution
                # from a second run is not a second branch for the search.
                fingerprint = tuple(sorted(str(a) for a in solution))
                if fingerprint in seen:
                    continue
                seen.add(fingerprint)
                adaptations.append((score, solution))
        return adaptations
