# Making FastLAS learn the same rules as ILASP, and deploying the four-way comparison

Report date: 2026-08-05 (evening; experiments launched 22:52, running overnight).

**Short version.** FastLAS was never solving the same problem as ILASP. Three
independent translation defects, each **silent** - no error, no warning - meant
it returned `UNSATISFIABLE` for every antecedent- and consequent-weakening task,
and an unconstrained rule for the rest. All three are fixed and verified. A
fourth bug, found while deploying, was worse: the strengthened case-study tests
read `SPEC_REPAIR_LEARNER` but never used it, so a FastLAS sweep would have
produced **ILASP results labelled FastLAS**.

The 2026-07-30 comparison was therefore measuring a crippled FastLAS. Any
conclusion drawn from it about FastLAS's solution quality should be discarded.

## 1. The three translation defects

### 1.1 `var(T)` had no backing predicate

FastLAS grounds a `var(T)` placeholder from a `T/1` predicate in the background
knowledge, and emits it into the learned rule as a type guard:

    antecedent_exception(e,0,V0,V1) :- holds_at(highwater,V0,V1), time(V0), trace(V1).

ILASP types variables from the mode declarations alone and needs no such
predicate, so the encoder never emitted one. `trace/1` existed **by accident** -
each example's context asserts `trace(name).` - but `time/1` never did: the
encoding uses `timepoint/2` throughout.

Without it FastLAS cannot build a single candidate rule. `SPACE SIZE: 0`,
`UNSATISFIABLE`, and **no error message** - indistinguishable from "this branch
found no repair", so the search silently explored nothing.

This is the whole ev-works/ae-ce-fails asymmetry that had been puzzling us:
`#modeh(ev_temp_op(const(expression_v)))` carries no `var()` at all, so
INVARIANT_TO_RESPONSE_WEAKENING was the one direction unaffected.

### 1.2 The `#bias` block was in ILASP's dialect

    ILASP     head(X)      body(X)
    FastLAS   in_head(X)   in_body(X)

In FastLAS `body/1` is simply an **undefined predicate**. So an untranslated
block is not rejected, it is inert:

* `:- body(X), ...`     -> can never fire -> constraint silently ignored
* `:- not body(X), ...` -> always fires   -> instant UNSATISFIABLE

Every constraint on rule shape was dead text. That is why FastLAS returned
`antecedent_exception(...) :- holds_at(highwater,...)` with no
`timepoint_of_op` - the four constraints at the end of the block exist
specifically to forbid that.

Measured: `:- body(holds_at(highwater,_,_)).` does **not** exclude highwater;
`:- in_body(holds_at(highwater,V0,V1)).` does.

Two smaller fixes in the same block: `:- constraint.` is dropped (ILASP's flag
for "the learned rule has an empty head"; FastLAS only learns `#modeh`-headed
rules, so the atom is undefined), and `==` becomes `=`, which FastLAS's parser
requires.

### 1.3 The recall bound was being stripped

`translate_ilasp_task_to_fastlas` removed the recall along with the `(positive)`
annotation. FastLAS accepts the recall; only the annotation is rejected.

### Ground truth for the dialect

The published docs (spike-imperial.github.io/FastLAS) contain **no syntax
reference at all**. The authoritative source is the repo, which ships the same
tasks in both dialects:

    FastLAS2/data/agent/ilasp_tasks/X.las
    FastLAS2/data/agent/fastnonopl_tasks/X.las

`diff` an identical pair. For `non_opl_agent_iteration7_extra_predicates1.las`,
across 2331 lines the only difference is:

    #modeb(p(...), (positive)).  ->  #modeb(p(...)).
    #modeb(p(...), (negative)).  ->  #modeb(not p(...)).

with the recall untouched. `FastLAS2/testing/non_opl.las` is the reference NOPL
task.

### Result

Every FastLAS answer measured is now a member of ILASP's solution set, with
`timepoint_of_op` present. On minepump:

| variant | FastLAS | in ILASP's set? |
|---|---|---|
| antecedent | `... :- timepoint_of_op(prev,V0,V2,V1), not_holds_at(highwater,V2,V1), ...` | yes (sol. 4 of 6) |
| consequent | `... :- timepoint_of_op(current,V0,V0,V1), holds_at(highwater,V0,V1), ...` | yes (sol. 1 of 10) |
| eventualisation | `ev_temp_op(assumption2_1).` | exact match |

`Adaptation.from_str` maps a guarded FastLAS rule and the equivalent ILASP rule
to **equal** Adaptations - the type guards fall outside its regexes - so nothing
downstream needed changing.

### Correction: FastLAS is NOT deterministic

Earlier notes recorded FastLAS 2.1.0 as deterministic. That was an artefact of
the broken translation: the hypothesis space was empty or held a single forced
candidate, so every run trivially agreed. With the fixes it returns **up to 4
distinct answers in 6 runs**, and the clingo tie count confirms it (15, 31, 127,
511, 2047 optimal models where it used to be 1).

`n_runs` is therefore how a run samples the ties, and is now settable from the
environment via `SPEC_REPAIR_FASTLAS_RUNS`. The variance is stochastic - a batch
can still collapse to one answer - so **do not assert variance in a test**; it
is flaky. Assert the space size instead.

## 2. The deployment bug: results labelled with the wrong solver

`tests/test_main/test_bfs_repair_orchestrator.py` read the learner name into
`self.learner` and **never passed it to the builder**. The committed file had
zero `using_learner` calls; the wiring existed only in an uncommitted working
copy. So on the GPU box:

* `SPEC_REPAIR_LEARNER=fastlas` was read, then ignored
* the builder fell back to the default `OptimisingSpecLearner`
* the run used ILASP, while writing to a `_fastlas`-suffixed directory

Exactly the failure `learner_from_env`'s own docstring warns about, one layer
up. The trace-violation tests were already wired correctly; only the
strengthened ones were affected.

Found by instrumenting `run_ILASP` inside the pytest process and printing the
stack, after the `.las` file it was solving turned out to be untranslated ILASP
dialect. Guessing had failed for several rounds before that.

## 3. Config: the GPU box can now commit and pull

`spec_repair/config.py` no longer needs per-machine editing, which is what
forced the `git stash` / `git stash pop` cycle on every branch switch:

* `PROJECT_PATH` is **derived** from the file's own location, never configured
* the jars and solver binaries all come from `$SPEC_REPAIR_TOOLS` (default `~/Tools`)
* `PATH_TO_SHIELD` hangs off `PROJECT_PATH`; `LOG_FOLDER` takes `$SPEC_REPAIR_LOGS`
* `PATH_TO_JVM` is resolved by search

**`$JAVA_HOME` is deliberately the last resort.** It reflects shell state, not
what the jars need, and it broke on both platforms during development: under
conda on macOS it points at the environment's Java, and on Linux without sdkman
sourced it gives Java 21 against jars needing 23+
(`UnsupportedClassVersionError: class file version 67.0 ... up to 65.0`).
Homebrew's newest openjdk is preferred on macOS, sdkman's `current` on Linux.

The GPU box needs one variable, set in **`~/phd_work.sh`**:

    export SPEC_REPAIR_TOOLS=/vol/bitbucket/tg4018/Tools

Not `~/.bashrc` - that early-returns for non-interactive shells (line 8,
`*) return;;`), so SSH and batch runs silently fall back to `~/Tools`. This is
also why `which FastLAS` reports MISSING over SSH while the binary is installed.

gpu11 now has zero local modifications and made commit `f88a475` itself.

## 4. Commits

    f88a475  FIX: Unbuffer the plot scripts and stop them clobbering their own logs
    6772edc  FIX: Prefer sdkman's JDK over $JAVA_HOME on Linux
    f33110a  FIX: Honour SPEC_REPAIR_LEARNER in the strengthened case-study tests
    f5efa68  FIX: Make config.py machine-independent
    2979606  DOCS: Reference ILASP/FastLAS task pairs for the minepump case study
    76b70f5  FIX: Make FastLAS learn the same rules as ILASP

Reference tasks for hand-inspection are in `files/fastlas/` - the same minepump
learning step emitted for each solver and each of the three `#modeh`
directions. Run the `.ilasp.las` files with plain `ILASP <file>`, **without**
`--version=4`: they carry the pylasp multi-solution driver, and the flag makes
ILASP run the search twice and print a spurious trailing `UNSATISFIABLE`.

## 5. Experiment deployment

Four sweeps, one per machine, all from `/vol/bitbucket/tg4018/PhD/SpecRepair`
at `f88a475`. Launched 2026-08-05 22:52.

| Machine | Learner | Setup | Runs | Command |
|---|---|---|---|---|
| gpu11 | FastLAS `n_runs=3` -> **5**, see §8 | trace-violation (new) | 50 | `LEARNER=fastlas FASTLAS_RUNS=3 MAX_WINDOWS=8 ./scripts/run_parallel_bfs_repair_trace.sh` |
| gpu13 | ILASP | trace-violation (new) | 50 | `LEARNER=ilasp MAX_WINDOWS=8 ./scripts/run_parallel_bfs_repair_trace.sh` |
| gpu14 | FastLAS `n_runs=3` -> **5**, see §8 | strengthened (old) | 17 | `LEARNER=fastlas FASTLAS_RUNS=3 ./scripts/run_parallel_bfs_repair_syn.sh all` |
| gpu15 | ILASP | strengthened (old) | 17 | `LEARNER=ilasp ./scripts/run_parallel_bfs_repair_syn.sh all` |

| Machine | tmux session | Logs | Output |
|---|---|---|---|
| gpu11 | `trace_tests_all_fastlas` | `logs/trace_tests/all_fastlas_2026-08-05_225217/` | `out/repair_trace_syn/<case>_trace<N>_fastlas_2026-08-05/` |
| gpu13 | `trace_tests_all_ilasp` | `logs/trace_tests/all_ilasp_2026-08-05_225231/` | `out/repair_trace_syn/<case>_trace<N>_2026-08-05/` |
| gpu14 | `parallel_tests_all_fastlas` | `logs/parallel_tests/all_fastlas_2026-08-05_225245/` | `out/repair_syn/<case>_fastlas_2026-08-05/` |
| gpu15 | `parallel_tests_all_ilasp` | `logs/parallel_tests/all_ilasp_2026-08-05_225247/` | `out/repair_syn/<case>_2026-08-05/` |

Trace setup: **10 case studies x 5 traces**. `arbiter` is absent by design - its
only assumption is `GF(a)`, satisfied by any finite prefix, so it has no
violating trace. Strengthened setup: 10 original + 7 `_updated` = 17.

`/vol/bitbucket` and `/homes` are shared NFS, so all four machines see the same
checkout. Output paths do not collide: the `_fastlas` suffix separates the
learners, and `repair_syn` vs `repair_trace_syn` separates the setups.

    tmux attach -t <session>        # watch
    tmux kill-session -t <session>  # stop

## 6. Caveats

1. **gpu11 was restarted from `n_runs=1` to `n_runs=3`**, discarding about an
   hour. Mismatched `n_runs` between the two FastLAS sweeps would have made them
   incomparable.
2. **One result was contaminated and repaired.** A leftover timing loop on gpu11
   wrote 241 `final_specs` into `repair_syn/minepump_fastlas_2026-08-05` - the
   same NFS path gpu14 writes to. It was killed, the directory cleared, and that
   single test restarted. Worth spot-checking.
3. **`MAX_WINDOWS=8` may not be capping.** 41 python processes were observed on
   gpu11 with zero free slots. The slot mechanism uses `mv` on NFS, whose
   atomicity across clients is not guaranteed. Not fatal - memory is ample and
   only 3-6 processes are CPU-runnable, the rest being in I/O wait - but it
   makes any wall-clock timing from these runs unreliable.
4. **No clean per-case-study timing exists.** Every attempt was contaminated by
   a competing job. `n_runs=5` did not finish minepump in 37 minutes; `n_runs=1`
   never completed cleanly either.
5. **`n_runs=3` is a guess, not a measurement.** The cost curve across `n_runs`
   was never obtained.
6. **Cost is branching, not the solver.** FastLAS itself is fast, and faster on
   the GPU box than locally (0.63s vs 1.23s for 5 invocations of the same task);
   2.2.0 and 2.1.0 behave identically on these tasks. The expense is that
   FastLAS now returns *varied* rules, so each sampled run can open a distinct
   BFS branch, and every new node pays for a Spectra/JVM realisability check.

## 7. Postscript: FastLAS is not slow - measured

Added ~01:00 after the sweeps had been running about an hour. The premise that
"FastLAS learning is not as fast as we want" **does not hold**. The four sweeps
are a natural A/B - same workload, same concurrency cap, started within 30
seconds of each other - and FastLAS is ahead in both setups:

| Setup | FastLAS `n_runs=3` | ILASP | Total runs |
| --- | --- | --- | --- |
| trace-violation | **29 finished** (19 OK, 10 failed) | 20 finished (9 OK, 11 failed) | 50 |
| strengthened | **7 finished** (4 OK, 3 failed) | 5 finished (3 OK, 2 failed) | 17 |

Roughly 1.4x more runs completed. Failure counts are comparable between the two
learners, and the dominant reason (`Error: expected ...`) appears on both sides,
so it is pre-existing test-assertion behaviour rather than anything FastLAS
introduced.

**Where the 37-minute observation came from.** It was
`test_bfs_repair_spec_minepump_syn`, which is a massive outlier in the suite:

    minepump   243 final specs
    humanoid    20
    pcar        16
    lift_upd    12
    elevator     9
    ...everything else 1-9

minepump produces **12-40x more final specifications than any other case
study**, under *either* learner - the 243 above is ILASP's. So the smoke test
picked the single widest search in the suite and ran it at `n_runs=5`, the
maximum branching setting. That is the worst case at the worst setting, not a
FastLAS problem.

Supporting evidence that the solver is not the bottleneck: FastLAS runs faster
on the GPU box than locally (0.63s vs 1.23s for five invocations of the same
task), and the machines show only 3-6 CPU-runnable processes against load
averages near 40 - the rest are in NFS I/O wait, since all four machines share
`/vol/bitbucket`.

One scoring asymmetry is worth knowing, though it did not cause the slowdown:
`FastLASInterpreter` reports every solution at `FASTLAS_SCORE = 0`, so
`filter_useful_adaptations` - which keeps the minimum-scoring adaptations -
retains **all** of them. ILASP's differing scores let it discard non-minimal
ones. With `n_runs=3` that is at most 3 per direction against ILASP's up to 10,
so FastLAS still branches less, but the two are not filtering on the same basis.

### A run that was silently doing nothing

While measuring, gpu14's `minepump` was found **not running at all** - 0 specs,
0 workers. My earlier restart of that one window (after the contamination in
caveat 2) had left the pane with `CONDA_PREFIX=logic` but base anaconda's `bin`
first on `PATH`, so it ran python 3.11 without `pyvis` and died instantly on
import.

Two traps behind it, both worth remembering:

* `~/phd_work.sh` sources `~/.bashrc`, which re-runs conda's init and resets to
  base. `conda activate` must come **after** it, which is what the runner does.
* Re-running `conda activate logic` in a pane that already has it "active" is a
  no-op for `PATH`, so a half-activated pane cannot be repaired by activating
  again. The fix is a fresh window.

Resolved by killing the window and recreating it with the runner's own setup
line; verified `which python` now gives `envs/logic/bin/python` and the worker
is running.

## 8. Restarted at `n_runs=5` (00:00, 2026-08-06)

Once FastLAS was shown to be the faster learner, both FastLAS sweeps were
restarted at `FASTLAS_RUNS=5`. The ILASP sweeps on gpu13/gpu15 were left
running untouched.

    gpu11   LEARNER=fastlas FASTLAS_RUNS=5 MAX_WINDOWS=8 ./scripts/run_parallel_bfs_repair_trace.sh
    gpu14   LEARNER=fastlas FASTLAS_RUNS=5 ./scripts/run_parallel_bfs_repair_syn.sh all

**Deliberately delayed until just after midnight.** `date_str` is
`datetime.now()` in `setUpClass`, computed once per *test process*, and each
window is its own process. Launching at 23:52 would have put the first ~8
windows in `2026-08-05` and everything queued behind them in `2026-08-06` -
one sweep split across two directories. Waiting eight minutes gives a clean
single date, and means nothing had to be deleted:

    *_fastlas_2026-08-05   n_runs=3   (19 OK / 10 failed trace, 4 OK / 3 failed syn)
    *_fastlas_2026-08-06   n_runs=5   (this run)

Both are kept, so the two settings can be compared directly.

Verified after relaunch: sessions created 00:00:06 and 00:00:08, workers
carrying `SPEC_REPAIR_LEARNER=fastlas` and `SPEC_REPAIR_FASTLAS_RUNS=5`.

**Caveat - the ILASP sweeps do span midnight.** They were not restarted, since
that would have discarded real progress for a cosmetic gain. Their runs that
started before 00:00 are under `*_2026-08-05` and the rest under
`*_2026-08-06`; collecting ILASP results needs **both** date directories.

## 9. What to check next

* Whether the `MAX_WINDOWS` slot cap actually works on NFS - if not, add a
  cap that does, and note that the syn runner has no cap at all (17 at once).
* A clean `n_runs` cost curve on an idle machine, to choose the value on
  evidence.
* Whether FastLAS can reach the `prev`/`next` rules at all. For `current` the
  `timepoint_of_op` binding is tautological; for `prev`/`next` it is not, and
  ILASP finds three `prev` variants on minepump AE.
* Re-run the 2026-07-30 comparison. Its FastLAS numbers were produced by the
  crippled translation and are not meaningful.
