# Too quiet, and too loud

Report date: 2026-08-31, covering 29-31 August. Follows
[2026-08-28](2026-08-28-a-repair-that-fails-its-own-trace.md).

Two defects, opposite in temperament, both in how the search classifies
"the learner came back with nothing".

One was **too quiet**: a specification that still violated the trace it was
repaired for was dropped without comment, which is how the disjunction-index bug
survived a full sweep unnoticed. The other was **too loud**: a branch with an
empty hypothesis space - an ordinary limitation - was treated as a broken
invariant and killed the whole run, discarding every other branch's results.

Between them sits the answer to the question 2026-08-28 left open, which is that
the learner was never at fault at all.

## The learning task is correct, and here is the proof

The open question was why the learner accepted a hypothesis that does not cover
its example. It did not. The task was dumped and run, and every optimal solution
carries **one `antecedent_exception` rule per disjunct index**:

    run 0   antecedent_exception(assumption3_1,0,...) :- ..., not_holds_at(pump,V0,V1), ...
            antecedent_exception(assumption3_1,1,...) :- ..., holds_at(flag,V0,V1), ...

    run 1   antecedent_exception(assumption3_1,1,...) :- ..., holds_at(highwater,V0,V1), ...
            antecedent_exception(assumption3_1,0,...) :- ..., not_holds_at(methane,V0,V1), ...

Run 2 is UNSATISFIABLE under the accumulated exclusions, so the space holds
exactly two solutions and both are complete. The mode declarations, the `#bias`
block, and the `#pos({entailed(trace_name_1)},{},{...})` example are all as
intended.

**A correction to how this was first checked.** The 2026-08-28 dump ran *ILASP*,
not FastLAS. `OptimisingSpecLearner.find_adaptations_with_heuristic` calls
`run_ILASP` unconditionally; `FastLASSpecLearner` subclasses it and overrides
exactly that method. Instantiating the base class therefore ran the wrong
solver on a task case study 3 never gives it - and the `%% Solution N (score 6)`
formatting in that output is ILASP's, which should have given it away. The
encoder method being named `encode_ILASP` on both paths does not help: FastLAS
receives that output through `translate_ilasp_task_to_fastlas`, so "ILASP"
names the intermediate dialect as well as the solver. The conclusion was
unaffected - the defect is downstream of either solver - but the evidence was
from the wrong one.

The real FastLAS artifacts are now in the repository, at
`tests/test_files/learning_tasks/minepump_liveness_trace1/`: the task in both
dialects, the raw stdout of each invocation, the parsed adaptations, and a
README deriving why a one-rule hypothesis cannot cover this example.

Note that run 1 returns the two rules **in the opposite order**. FastLAS's rule
ordering varies between runs, and the corruption depended on which index was
applied first, which is why the bug was intermittent rather than a clean
reproducible failure.

## Too quiet: a repair that fails its trace is a contract violation

The 2026-08-28 gate dropped such a candidate with a `REJECT` event and moved on.
That is the wrong temperature for what it is. The learning task *demands*
`entailed(<trace>)`, so no solution to it can leave the trace violating an
assumption; if one does, something in the chain from task to specification is
broken - the modes, the bias, the ASP encoding, the rule parsing, or the
application of the adaptations. Dropping it quietly is what let the
disjunction-index bug ship three bad specifications and a bad merge with nothing
in the run saying so.

`spec_repair/diagnosis/learner_fault.py` now treats it as an assertion about the
pipeline. When it fires the run writes a bundle that reproduces the fault
offline - the exact task the solver was given, its raw answer, the adaptations
parsed from it, the specification before and after, the remaining violations -
logs it at ERROR, counts it, and repeats the count in the final summary.

Both learners retain what they asked and were told. FastLAS needed
`enumerate_solutions` to hand back its per-run text, because the accumulated
exclusions make each run's task different and the initial task alone would not
reproduce the offending run.

The search continues rather than aborting, since one bad branch should not cost
a fifty-run sweep, and the bundle makes the fault actionable either way.
`SPEC_REPAIR_STRICT_LEARNER=1` stops at the first one, after writing the bundle.

**Zero bundles have appeared** across every re-run, with thousands of
specifications recorded. That zero was checked rather than assumed: a positive
control on the lab box produced a bundle in the expected location with all seven
files, and 460+ `SOLVED` events confirm the gate is actually being reached.

## Too loud: an empty hypothesis space is not a broken invariant

`minepump_liveness` trace 2 has died at eight minutes in every sweep on record -
2026-08-07, 08, 09, 10, 13, and both 2026-08-29 batches - with
`MitigationMadeNoProgressException`, after recording 163 solutions on other
branches. It is not caused by anything changed this week; the 2026-08-13 run
fails identically.

The last three nodes tell it:

    n99   LEARN 0 candidate(s) (0.0s)  MITIG 0 tasks  LIMIT - deadlock completion required
    n100  LEARN 0 candidate(s) (0.0s)  MITIG 0 tasks  LIMIT - deadlock completion required
    n101  LEARN 0 candidate(s) (0.8s)  MITIG 0 tasks  -> FATAL

All three reach the same situation. The only difference is whether
`unresolvable_reason` was set. `learn_new` has three ways to come back empty and
they are the same kind of event - a limitation of the methodology, not a broken
invariant - but only two of them said so:

| exception | set a reason? | outcome |
| --- | --- | --- |
| `DeadlockRequiredException` | yes | `LIMIT`, branch ends, run continues |
| `subprocess.TimeoutExpired` | yes | `LIMIT`, branch ends, run continues |
| `NoWeakeningException` | **no** | **whole run aborts** |

n101 took 0.8s rather than 0.0s because it did real work: violations *were*
found, and then all three learning tasks - antecedent exception, consequent
exception, invariant-to-response - came back UNSAT.

**The space really is empty.** Reproduced on the specification the run printed:
it is unrealisable, yields 12 counter-traces, and all 12 give "No guarantee
weakening produces realizable spec (las file UNSAT)". The reason is visible in
the specification - the surviving counter-strategies violate `guarantee3_1`,
which is `GF(flag=false)`. None of the three weakening shapes applies to a
justice goal: there is no antecedent to except, no consequent to widen, and it
is already a response. The learner correctly has nothing to offer.

Worth noting from the same branch's history: `assumption1_1` had been weakened
to `G(((PREV(pump) & pump) & !pump) -> next(!highwater))`, whose antecedent is
unsatisfiable. A weakening narrowed to a contradiction is legitimate - it is the
weakest the formula can get - but it means the branch had already given away
everything that assumption constrained before reaching the dead end.

`NoWeakeningException` now sets its reason like its siblings. The effect was
larger than the single node suggested:

    [ 9m22s] LIMIT  d1 n101  branch abandoned - no guarantee weakening available
    [ 9m23s] LIMIT  d1 n102  branch abandoned - no guarantee weakening available
    [ 9m23s] LIMIT  d1 n103  branch abandoned - no guarantee weakening available
    [ 9m24s] LIMIT  d1 n104  branch abandoned - no guarantee weakening available

Four consecutive dead branches sat at depth 1, and the old code could never get
past the first. The trace now runs past 13 hours at depth 3 with 406
specifications against the 163 it managed before.

## What the tables say now

Two genuinely new results: **Minepump 2 merges to 58** specifications from 73
preferred, and **Minepump 3 to 12** from 36. Both were previously reported as
not computed.

Everything else in the table update is a retraction. Eighteen runs - AMBA, Gyro
and Minepump Liveness across all five traces, GenBuf traces 0-2 - came from a
search whose antecedent exceptions could leave a disjunct unguarded, so their
stage counts are now `n/a` with a footnote rather than sitting there as results.

Which eighteen was determined by scanning `final_specs` for a formula whose
top-level implication has a disjunction in its antecedent - the precondition for
the bug, since only then can one solution carry two exception rules for the same
formula. The first scan returned all zeros and was **wrong**: it identified the
top-level `->` by a fixed paren depth, and the serialiser wraps bodies in a
variable number of parens. The top-level arrow is the one at *minimum* depth.
The corrected scan, unit-checked against six hand-written formulas, is
unambiguous - the affected runs hit 100% of what was sampled, the unaffected
ones 0%.

AMBA has since finished re-running and its counts are unchanged: 21 realisable
explored, 1 unique, 1 preferred, 1 merged, per trace. Its ordering was
re-derived from the corrected merges - assumptions strictly stronger in the
original, guarantees equivalent - and holds. Its *merged specification* differs
from the old sweep's, but FastLAS returns different equally-optimal solutions
between runs, so that difference **cannot be attributed to the fix**.

`tab:ordering`'s caption glossed `\prec` as "is strictly weaker than" while its
rows are ordered by increasing weakness, so `a \prec b` means a is stronger.
Every relation in the table read backwards for anyone using the legend. Caption
corrected; the 61 rows were right.

## Provenance

Everything is now on `e8d619d`, except eight runs that completed on `178c29f`:
AMBA 0-4, GenBuf 2, Minepump Liveness 1 and 3. The difference between those
commits only bites when a branch hits `NoWeakeningException`, and all eight
exited 0, so their results are already what `e8d619d` would produce. Restarting
them would change correct results, because FastLAS is non-deterministic. The
argument for doing it anyway is provenance - one commit behind every number -
and that call is open.

The lab checkout at `/vol/bitbucket/tg4018/PhD/SpecRepair` is a **single shared
filesystem** visible from every gpu host. It sits on an old commit with a large
pile of working-tree edits and is updated by file copy, not by `git pull`: a
checkout there would swap code under every running job. Each deployment this
week copied the specific files and verified md5s against local before anything
was launched.

Both runners now take `RUN_DATE`. `five_step_runner.sh` hardcoded 2026-08-13,
which silently pointed every re-merge at the old sweep's output;
`run_case_study_3.sh` stamped `date +%F`, so relaunching one trace of yesterday's
sweep would have made it invisible to the merge that collects its siblings.

## Still open

* The eight runs on `178c29f`, above.
* Gyro remains the wall it has always been: four traces reached depth 1 in six
  hours and the runner's own notes record none finishing in 44h. Results within
  a usable timeframe need a decision about a bound, which is a methodology
  question rather than a scheduling one.
* ColorSort still produces nothing; both 48g and 24g of heap came back
  SIGTERM from earlyoom, and `-Xmx` does not bound CUDD's native tables.
* `minepump_liveness` trace 2's count will need re-reading into `tab:total` once
  it finishes. The 163 currently archived is not what it will report.
* A subtlety introduced by the `unresolvable_reason` fix: the reason is carried
  in `RepairData`, so a reason set at one node is inherited by tasks derived
  from it. A stale reason could in principle suppress a genuinely fatal stall
  further down the branch. Not observed, and the fatal path is arguably too
  aggressive anyway, but it is a real change in what the invariant check can
  still catch.
