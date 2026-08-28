#!/usr/bin/env python3
"""
Filter first, merge second - the methodology, in the order it was specified.

    1. semantically unique   drop any specification that another in the pool is
                             semantically equivalent to
    2. strongest guarantees  of those, keep the ones no other specification's
                             guarantees are strictly stronger than (incomparable
                             ones all survive)

Stage 1 comes first and there is no input cap. The order is not interchangeable:
equivalent specifications imply each other in both directions, so neither is
"strictly stronger" and stage 2 keeps them both. Stage 2 therefore cannot remove
a single duplicate, and running it first would pay a full O(n^2) of guarantee
implications while leaving stage 1 exactly as much work as before. Measured, the
filters bear that out - stage 1 removes 50-65% of a pool, stage 2 removed
nothing at all on every 21-specification run.
    3. merge                 only that pool is merged

`scripts/run_experiment_pipeline.py` has had this backwards since it was written
on 2026-07-27: it merges the whole pool and then filters the *merged* output.
That inflates the merge from a handful of specifications to the entire result
set - 24,619 for traffic_single trace 1 - and conjoins fifteen variants of the
same assumption, five of them carrying `PREV`, whose rewrite expands a
563-character formula into 177,492 characters of nested `X`.

Reports the count at each stage, because that is the number the methodology is
described by.

    python scripts/filter_then_merge.py <run_dir> [--out <dir>] [--workers N]
"""
import argparse
import glob
from concurrent.futures import ThreadPoolExecutor
import itertools
import os
import time
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from spec_repair.exceptions import EquivalenceUndecided
from spec_repair.ltl_types import GR1FormulaType
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.diagnosis.guarantee_filters import strongest_guarantees
from spec_repair.util.file_util import write_to_file


UNDECIDED = []


def _equivalent_or_undecided(spec, other):
    """
    Whether `spec` is equivalent to `other`, counting the checks that time out.

    An undecided check is reported as *not* equivalent, which keeps both
    specifications. That is the conservative direction for a filter - it can
    only leave the pool larger than the exact answer would, never smaller, so no
    repair is ever discarded on the strength of a question that was not
    answered. It does mean the unique count is an upper bound whenever anything
    lands in `UNDECIDED`, and the run says so at the end rather than reporting a
    number that looks exact.
    """
    try:
        return spec.equivalent_to(other)
    except EquivalenceUndecided as e:
        UNDECIDED.append(str(e))
        return False


def _equivalent_to_any(spec, kept, workers):
    """
    True if `spec` is equivalent to anything in `kept`.

    Every check is an `ltlfilt`/`ltl2tgba` subprocess that this thread only
    waits on, so threads - not processes - are the right pool: the GIL is
    released for the whole call and nothing has to be pickled. Submitted in
    order and consumed in order, cancelling the rest at the first hit, so the
    common case (an early duplicate) still costs about what the serial loop
    cost, while a genuinely new specification gets its whole scan in parallel.
    """
    if not kept:
        return False
    if workers <= 1:
        return any(_equivalent_or_undecided(spec, other) for other in kept)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_equivalent_or_undecided, spec, other)
                   for other in kept]
        try:
            for f in futures:
                if f.result():
                    return True
        finally:
            for f in futures:
                f.cancel()
    return False


def semantically_unique(specs, workers=1):
    """
    One representative per equivalence class, keeping first-seen order.

    Two tiers, both exact - this never merges specifications that differ:

    1. identical serialisations collapse with no Spot call at all. A BFS search
       reaches the same specification by many paths, and those cost nothing to
       recognise.
    2. what survives is compared semantically against the representatives kept
       so far, `workers` checks at a time.

    There is deliberately no bucketing by automaton size or any other cheap
    "semantic fingerprint". Spot's minimisation is heuristic, not canonical, so
    two equivalent specifications can minimise to different-sized automata;
    bucketing on that would put them in different buckets, keep both, and
    silently report more unique specifications than there are. An
    over-reported uniqueness count is exactly the kind of wrong number that
    reads as a result.
    """
    by_text = {}
    for spec in specs:
        by_text.setdefault(spec.to_str(), spec)
    candidates = list(by_text.values())
    if len(candidates) < len(specs):
        print(f"stage 1a identical serialisations     {len(specs)} -> {len(candidates)}",
              flush=True)

    kept = []
    started = last_report = time.time()
    for n, spec in enumerate(candidates, 1):
        if not _equivalent_to_any(spec, kept, workers):
            kept.append(spec)
        # This loop had no output at all, so a stage that runs for a day looked
        # identical to one that had hung. The work per candidate grows with
        # `kept`, so elapsed time alone does not say how far along it is.
        if time.time() - last_report >= 60:
            last_report = time.time()
            print(f"         ...{n}/{len(candidates)} compared, {len(kept)} kept"
                  f"{_undecided_note()} ({last_report - started:.0f}s)", flush=True)
    return kept


def _undecided_note() -> str:
    """A suffix naming how many equivalence checks were never decided."""
    if not UNDECIDED:
        return ""
    return (f"   [upper bound: {len(UNDECIDED)} equivalence check(s) hit "
            f"SPEC_REPAIR_EQUIV_TIMEOUT and were counted as not equivalent]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--out", default=None, help="where to write the merged result")
    ap.add_argument("--workers", type=int, default=8,
                    help="concurrent ltlfilt/ltl2tgba subprocesses (default 8)")
    ap.add_argument("--unique-only", action="store_true",
                    help="stop after the equivalence filter, applied to the raw "
                         "pool, and write the representatives to unique_specs/. "
                         "This is the count the paper reports as 'unique', which "
                         "is not the same number the full pipeline reaches: there "
                         "the guarantee filter has already removed dominated "
                         "specifications, so classes that were entirely dominated "
                         "never reach the equivalence check at all.")
    ap.add_argument("--maximal", action="store_true",
                    help="merge FIRST, by enumerating maximal realisable subsets "
                         "of the pooled guarantees, then report the unique and "
                         "strongest counts over the result. The default order "
                         "filters before merging, which can delete the only "
                         "carrier of a formula the merge needed: on minepump "
                         "trace 1 all 15 specs holding one such guarantee were "
                         "dominated and dropped, and the merge could not conjoin "
                         "what it never received. Writes maximal_merged_specs/.")
    ap.add_argument("--five-step", action="store_true",
                    help="the five-step pipeline: merge the assumptions of every "
                         "solution, filter to the soft semantically unique "
                         "specifications by guarantees, broadcast the merged "
                         "assumptions, filter to the strongest by guarantees, "
                         "then merge losslessly by unrealisable cores and their "
                         "minimal hitting sets. Same unique -> strongest -> merge "
                         "order as the default; what differs is the uniqueness "
                         "test, the assumption coalescing, and the merge. Writes "
                         "five_step_specs/.")
    ap.add_argument("--directed", action="store_true",
                    help="merge by descending from the ORIGINAL specification: "
                         "check its guarantees against the pooled assumptions, "
                         "take the minimal unrealisable cores of that, and weaken "
                         "only the guarantees a core implicates. The same cores "
                         "-> minimal-hitting-sets skeleton the trivial solutions "
                         "use, with weakening in place of deletion. Writes "
                         "directed_merged_specs/.")
    ap.add_argument("--strongest-first", action="store_true",
                    help="run the guarantee filter before the equivalence filter. "
                         "Same final set, far cheaper on a large pool")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.run_dir, "final_specs", "*.spectra")))
    print(f"stage 0  final specs on disk          {len(files)}", flush=True)
    if not files:
        return 1

    specs = [SpectraSpecification.from_file(f) for f in files]
    by_text = {}
    for spec in specs:
        by_text.setdefault(spec.to_str(), spec)
    if len(by_text) < len(specs):
        print(f"stage 0a identical serialisations     {len(specs)} -> {len(by_text)}",
              flush=True)
        specs = list(by_text.values())

    if args.unique_only:
        unique = semantically_unique(specs, workers=args.workers)
        print(f"stage 1  semantically unique          {len(unique)}"
              f"{_undecided_note()}", flush=True)
        # A name of its own: `unique_specs/` is what run_experiment_pipeline
        # writes for its own stage 2, and these two are not the same set.
        out = args.out or os.path.join(args.run_dir, "unique_from_final_specs")
        os.makedirs(out, exist_ok=True)
        for i, spec in enumerate(unique):
            write_to_file(os.path.join(out, f"spec_{i}.spectra"), spec.to_str())
        print(f"         written to {out}", flush=True)
        return 0

    if args.five_step:
        import logging
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        import re as _re5
        from spec_repair.diagnosis.five_step import run_five_step, TraceNotAdmitted
        from spec_repair.components.learners.optimising_final_spec_learner import (
            OptimisingSpecLearner)
        from spec_repair.components.new_spec_encoder import (
            get_violated_expression_names_of_type)
        from spec_repair.enums import Learning
        from spec_repair.util.file_util import read_file_lines
        from spec_repair.diagnosis.merge_invariants import (
            check_merge_output, response_shaped_guarantees)
        # The violating trace this run was repaired for. Without it the merge
        # can pool a violated assumption back in and undo the repair silently,
        # which is what happened to minepump_liveness trace 1.
        run5 = os.path.basename(os.path.normpath(args.run_dir))
        case5 = _re5.sub(r"_trace\d+_.*$", "", run5)
        trace_no = _re5.search(r"_trace(\d+)_", run5)
        trace_path = os.path.join(
            REPO_ROOT, "input-files", "case-studies", "spectra", "case_study_3",
            case5, f"violation_trace_{trace_no.group(1)}.txt") if trace_no else None
        admits = None
        if trace_path and os.path.exists(trace_path):
            trace_lines = read_file_lines(trace_path)
            _learner = OptimisingSpecLearner()

            def admits(spec, _t=trace_lines, _l=_learner):
                violated = get_violated_expression_names_of_type(
                    _l.get_spec_violations(spec, _t, [], Learning.ASSUMPTION_WEAKENING),
                    "assumption")
                return not violated

            print(f"         trace gate: {trace_path}", flush=True)
        else:
            print("         WARNING no violation trace found; the merge is not "
                  "checked against it", flush=True)
        try:
            report = run_five_step(specs, workers=args.workers, admits=admits)
        except TraceNotAdmitted as exc:
            print(f"stage !   TRACE NOT ADMITTED: {exc}", flush=True)
            return 2
        print(f"stage 0  admitting the trace           {report.admitting}"
              f" of {report.inputs}", flush=True)
        print(f"stage 1  merged assumptions            {report.pooled_assumptions}",
              flush=True)
        print(f"stage 2  soft semantically unique      {report.soft_unique}", flush=True)
        print(f"stage 2b semantically unique           {report.semantic_unique}", flush=True)
        print(f"stage 3  rebased                       {report.rebased}", flush=True)
        print(f"stage 4  strongest by guarantees       {report.strongest}", flush=True)
        print(f"stage 5  merged                        {report.merged}"
              f"   (pool {report.pooled_guarantees}, {report.cores} core(s))", flush=True)
        # Distinct maximal realisable subsets cannot be semantically equivalent,
        # so a duplicate here means the cores were incomplete or realisability is
        # not behaving semantically.
        for problem in check_merge_output(report.specs):
            print(f"         WARNING {problem}", flush=True)
            named = sorted({n for m in report.specs
                            for n in response_shaped_guarantees(m)})
            if named:
                print(f"         response-shaped guarantees: {named}", flush=True)
        # Every stage is written, not just the last. These take hours to
        # produce and are inputs to analysis nobody has thought of yet; a
        # pipeline that keeps only its final answer forces a full re-run to ask
        # any question about the middle of it. The guarantee graph wanting
        # step 4 is the first such question and will not be the last.
        for sub, specs in (("merged_assumptions", report.assumption_specs),
                           ("soft_unique_specs", report.unique_specs),
                           ("semantic_unique_specs", report.semantic_unique_specs),
                           ("strongest_specs", report.strongest_specs)):
            stage_out = os.path.join(args.run_dir, sub)
            os.makedirs(stage_out, exist_ok=True)
            for i, spec in enumerate(specs):
                write_to_file(os.path.join(stage_out, f"spec_{i}.spectra"),
                              spec.to_str())
            print(f"         {sub}: {len(specs)} written", flush=True)
        out = args.out or os.path.join(args.run_dir, "five_step_specs")
        os.makedirs(out, exist_ok=True)
        for i, spec in enumerate(report.specs):
            write_to_file(os.path.join(out, f"spec_{i}.spectra"), spec.to_str())
        print(f"         written to {out}   ({report.seconds:.0f}s)", flush=True)
        return 0

    if args.directed:
        import logging
        import re as _re
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        from spec_repair.diagnosis.directed_merging import directed_merges
        run = os.path.basename(os.path.normpath(args.run_dir))
        case = _re.sub(r"_trace\d+_.*$", "", run)
        original_path = os.path.join(
            REPO_ROOT, "input-files", "case-studies", "spectra", "case_study_3",
            case, "original.spectra")
        if not os.path.exists(original_path):
            print(f"no original specification at {original_path}", flush=True)
            return 1
        print(f"         original: {original_path}", flush=True)
        original = SpectraSpecification.from_file(original_path)
        merged = directed_merges(specs, original)
        print(f"stage 1  directed merges              {len(merged)}", flush=True)
        # What the construction promises, checked rather than assumed. Distinct
        # maximal realisable subsets cannot be semantically equivalent, so a
        # duplicate here means the cores were incomplete or realisability is not
        # behaving semantically - see spec_repair/diagnosis/merge_invariants.py.
        from spec_repair.diagnosis.merge_invariants import (
            check_merge_output, response_shaped_guarantees)
        problems = check_merge_output(merged)
        for problem in problems:
            print(f"         WARNING {problem}", flush=True)
        if problems:
            named = sorted({n for m in merged for n in response_shaped_guarantees(m)})
            if named:
                print(f"         response-shaped guarantees present: {named}", flush=True)
        unique = semantically_unique(merged, workers=args.workers)
        print(f"stage 2  semantically unique          {len(unique)}"
              f"{_undecided_note()}", flush=True)
        strongest = strongest_guarantees(unique, workers=args.workers)
        print(f"stage 3  strongest guarantees         {len(strongest)}", flush=True)
        out = args.out or os.path.join(args.run_dir, "directed_merged_specs")
        os.makedirs(out, exist_ok=True)
        for i, spec in enumerate(strongest):
            write_to_file(os.path.join(out, f"spec_{i}.spectra"), spec.to_str())
        print(f"         written to {out}", flush=True)
        return 0

    if args.maximal:
        from spec_repair.diagnosis.maximal_merging import maximal_merges
        merged = maximal_merges(specs)
        print(f"stage 1  maximal realisable merges    {len(merged)}", flush=True)
        # Both filters are reporting steps here, not gatekeepers: the merge has
        # already happened, so nothing they drop can cost a later stage a
        # formula. Inclusion-maximal subsets can still be semantically
        # equivalent to one another, or one can dominate another outright.
        unique = semantically_unique(merged, workers=args.workers)
        print(f"stage 2  semantically unique          {len(unique)}"
              f"{_undecided_note()}", flush=True)
        strongest = strongest_guarantees(unique, workers=args.workers)
        print(f"stage 3  strongest guarantees         {len(strongest)}", flush=True)
        out = args.out or os.path.join(args.run_dir, "maximal_merged_specs")
        os.makedirs(out, exist_ok=True)
        for i, spec in enumerate(strongest):
            write_to_file(os.path.join(out, f"spec_{i}.spectra"), spec.to_str())
        print(f"         written to {out}", flush=True)
        return 0

    if args.strongest_first:
        # Same final set, reached more cheaply. Dropping a dominated
        # specification needs GAR-only implications and stops at the first
        # dominator; proving two specifications equivalent needs the whole
        # specification and cannot stop early. On a pool where most entries are
        # dominated it is much cheaper to throw them out before paying for any
        # equivalence check. The composition is unchanged either way: equivalent
        # specifications imply each other in both directions, so the guarantee
        # filter never separates an equivalence class - it keeps all of a class
        # or, if something dominates it, none of it.
        strongest = strongest_guarantees(specs, workers=args.workers)
        print(f"stage 1  strongest guarantees         {len(strongest)}", flush=True)
        unique = semantically_unique(strongest, workers=args.workers)
        print(f"stage 2  semantically unique          {len(unique)}"
              f"{_undecided_note()}", flush=True)
        strongest = unique
    else:
        unique = semantically_unique(specs, workers=args.workers)
        print(f"stage 1  semantically unique          {len(unique)}"
              f"{_undecided_note()}", flush=True)

        strongest = strongest_guarantees(unique, workers=args.workers)
        print(f"stage 2  strongest guarantees         {len(strongest)}", flush=True)

    from spec_repair.diagnosis.solution_merging import merge_solutions
    merged = (list(strongest) if len(strongest) < 2
              else merge_solutions(strongest, verify_inputs=False))
    print(f"stage 3  merged                       {len(merged)}", flush=True)

    out = args.out or os.path.join(args.run_dir, "filtered_merged_specs")
    os.makedirs(out, exist_ok=True)
    for i, spec in enumerate(merged):
        write_to_file(os.path.join(out, f"spec_{i}.spectra"), spec.to_str())
    print(f"         written to {out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
