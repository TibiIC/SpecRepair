# Every node must lead to a leaf: dead ends, case-study preconditions, and making FastLAS deterministic

Report date: 2026-08-06 (written through the day; the four sweeps relaunched at
17:15 are still running).

**Short version.** The day started from a catalogue of overnight failures and
ended with the search invariant restored and FastLAS made deterministic.

Four crash classes were ending whole runs from inside a single branch. Two
error classes - `IndexError` and `TypeError` - turned out not to be code bugs
at all but **invalid case studies**: 8 of 81 configurations broke preconditions
the repair cannot establish for itself. Those preconditions are now asserted up
front, and two further ways a branch could silently vanish were closed. A
separate root cause was found for the remaining dead ends, worth 34 events and
four failed case studies under ILASP.

Finally, FastLAS's multi-solution search no longer relies on randomness. It
enumerates: each solution found is forbidden in the `#bias` and the solver is
asked again. On minepump it now recovers **exactly** ILASP's 6 solutions,
identically on every run.

## 1. Four crashes that ended the run instead of the branch

Each of these was raised inside one branch of the BFS and propagated out,
killing a sweep that had done hours of useful work on other branches.

| Commit | Cause |
| --- | --- |
| `db6f1fe` | A debug-graph *label* threw, ending the repair run |
| `4327443` | *Drawing* the debug graph threw, ending the repair run |
| `28abfc2` | A candidate Spectra could not check ⇒ ended the run |
| `6e0c1bf` | Spectra BDD heap exhaustion ⇒ ended the run |

The debug graph is write-only diagnostic output. It must never be able to
affect the result of the run it is describing. The two Spectra cases are
genuine per-candidate outcomes - an unparseable candidate or a spec too big for
the BDD engine is a fact about *that branch*, not about the run.

## 2. The failures were invalid case studies, not code bugs

The overnight `IndexError` and `TypeError` failures resisted a code fix because
there was nothing wrong with the code. A repair run assumes two things it
cannot establish for itself:

1. the input specification is realisable, and
2. the violation trace violates at least one **non-initial** assumption.

Both are properties of the *case study*. An audit found **8 of 81**
configurations breaking them, in two shapes:

* **The trace violated nothing at all** - `humanoid_updated`,
  `traffic_updated_updated`. An already-realisable specification was pushed
  into guarantee weakening, where the unrealisable core is empty, so nothing is
  marked learnable and the task returns UNSAT. This was reported as *"No
  guarantee weakening produces realizable spec"* - which reads as though the
  specification were unrealisable when it is exactly the opposite. Source of
  the `IndexError`.

* **The trace violated only an initial assumption** - `gyro/0`, `gyro/3`,
  `lift/0`, `minepump_liveness/1`, `minepump_liveness/4`. Weakening an initial
  assumption drags system variables into it, which Spectra's CLI rejects
  outright. Source of the 15 `TypeError` failures.

Both are now asserted before the BFS starts (`f4106ef`), raising
`InvalidCaseStudyException` rather than failing later as something unrecognisable.

The traces were regenerated (`9a4bb0d`), all five per affected case study
together so each set stays internally consistent. **Final audit: 80 OK, 0 BAD,
1 error** - submarine, whose realisability check throws, deliberately left.

## 3. Two more ways a branch could vanish

> "Repeat after me: every node must lead to a leaf."

`44f4b09` closes both:

* **A mitigation returning its input unchanged** is neither progress nor a
  decision to stop. The orchestration manager sees an already-visited task,
  returns its id without pushing it, and the branch disappears - the run still
  reports a result, just a quietly smaller one. `complete_counter_traces` did
  exactly this, which the mitigator's own TODO already recorded as *"it loops
  infinitely on the same task"*. Now raises `MitigationMadeNoProgressException`.

* **A branch ending with nothing** may be standing on a perfectly good repair:
  the learner has nothing left to weaken precisely because there is nothing
  left to fix. `_record_if_solution` now checks before letting a branch end,
  recording it as a leaf if it is realisable and its assumptions are no longer
  violated by the trace. The third property of a solution - assumptions weaker,
  guarantees weaker or equivalent - is a side effect of only ever weakening, so
  it is not re-checked.

### 3.1 The root cause behind the remaining dead ends

With `MitigationMadeNoProgressException` making dead ends *visible*, the real
culprit surfaced (`abff783`). The `NoViolationException` escape for guarantee
weakening also required `not data.trace` - which excludes the entire
trace-violation setup, where a trace is always present. The branch fell through
to `return []`, the mitigator returned its input unchanged, and the node was
dropped.

Whether a violation trace exists says nothing about whether counter-strategies
are needed. **Measured: 34 such events under ILASP, failing `amba`,
`colorsort`, `genbuf` and `gyro` outright.** `gyro_0` under ILASP now produces
6 final specs where it previously failed.

## 4. Initial formulas excluded from learning

Weakening an initial assumption pulls system variables into it, which Spectra
rejects. Rather than repair that downstream, the learning task no longer offers
it: `encode_ILASP` excludes INITIAL formulas from `expressions_to_weaken`,
while `encode_ASP` keeps them for violation and realisability checking.

This landed twice. `074fef3` added six `LEARN_<type>_<when>` heuristic toggles;
`bf3d34b` replaced them with a single `NON_LEARNABLE_WHEN` constant, because
**the toggles could not do what they were for**: `IHeuristicManager` is one
object shared by every learner, so a flag set for the assumption learner cannot
mean something different for the guarantee learner. They read as per-learner
configuration while being global - worse than not offering the knob at all.

Which formulas a methodology may weaken is also not a heuristic. Heuristics
narrow a search that would still be correct without them; this decides what
counts as an *admissible repair*. A configurable, per-learner version now
exists - see §15.2.

## 5. AMBA and genbuf, and three silent corruptions they surfaced

Both case studies were desugared to boolean form (`e81366a`) and set up in both
experimental setups. `pRespondsToS` was left to the existing translation;
`pBecomesTrue_betweenQandR` - which uses the release operator `V` - was expanded
to a GR(1)-compliant three-state monitor.

Desugaring them surfaced three bugs (`81da75c`), **all of which produced wrong
output rather than an error**:

1. **`PRS_REG` matched `-> FALSE` as a response pattern.** `^\s*G[^-]*->\s*F`
   looks for `G(a -> F(b))`, but a bare `F` also matches the constant `FALSE`,
   so an ordinary safety constraint `G(a -> FALSE)` was taken for a response
   pattern. Three genbuf guarantees are that shape. Now requires `F\s*\(`.
2. **`pRespondsToS_substitution` called `exit(1)`** on a malformed pattern -
   inside a repair run that kills the interpreter outright, with no traceback
   and no chance for the caller to treat it as a failed branch. Raises now.
3. **`assign_equalities` substituted inside longer variable names.** Its guards
   stopped a match running into a following lowercase letter but not into an
   underscore or digit, so any variable whose name prefixes another corrupted
   it. Now uses `\b`.

## 6. FastLAS: enumeration instead of sampling

**The change.** FastLAS returns one solution per invocation where ILASP returns
all optimal ones. The search used to run it `n_runs` times and keep whatever
distinct answers turned up - relying on it breaking ties differently between
runs. The branching factor was non-deterministic, repeated runs duplicated
work, and solutions could simply be missed.

Now each solution found is appended to the `#bias` as a constraint forbidding
it, and FastLAS is asked again. When the constrained task goes `UNSATISFIABLE`
the space is exhausted and the loop stops early.

**The subtlety: supersets.** A constraint listing only body literals reads
*"never this head with **at least** these literals"*. Excluding

    antecedent_exception(...) :- not_holds_at(methane,...)

would then also lose the genuinely different, more specific

    antecedent_exception(...) :- not_holds_at(methane,...), holds_at(highwater,...)

which the search still needs to see. Pinning the body size fixes it:

    :- in_head(antecedent_exception(_,_,_,_)),
       in_body(timepoint_of_op(prev,V0,V2,V1)),
       in_body(not_holds_at(highwater,V2,V1)),
       #count{X : in_body(X)} = 2.

This is the same device pylasp uses for ILASP, where the alternative is spelled
out as *"if you want to allow non-subset-minimal solutions"*. Verified against
the real binary: `#count` aggregates work in FastLAS's bias, and the `time`/
`trace` type guards FastLAS injects are **not** counted, so the arithmetic is
over real body literals only.

**Measured on minepump (antecedent weakening):**

| Seeded constraint | Rules reachable | 2-literal superset survives |
| --- | --- | --- |
| none | 6 | — |
| block 1-literal `not_holds_at(highwater)`, no pin | 5 | ✗ collateral damage |
| same, with `#count = 1` | 6 | ✓ |

FastLAS now recovers **exactly** ILASP's 6 solutions, identical across repeated
runs. That is stronger than the old containment property, which was all the
2026-08-05 tests could assert.

**`n_runs` 5 → 10**, mirroring ILASP's `MAX_ASP_HYPOTHESES`. Nearly free under
enumeration: it is a *ceiling*, not a cost - a step with three solutions costs
four invocations whatever the ceiling says. It only costs more where 6-10
solutions genuinely exist, which is precisely the breadth being lost at 5.

## 7. `write_trace` and the retirement of `test_debug`

`test_debug/test_asp.py::test_hongbo` had been on the skip-list since
2026-07-20 with a known diagnosis and a decision to skip rather than fix. It
was a **real bug in live code**: `write_trace` handled a *missing* trace file -
start at `trace_name_0` - but not an existing file naming no traces, which took
the success branch and hit `max()` over an empty sequence. Both mean "nothing
written yet". `generate_trace_asp`, which the mutation generator uses, is
routinely handed exactly such a file. Fixed; the test then passed.

`test_debug` was removed anyway (`c32902e`). Neither test was worth keeping:
`test_asp` duplicated coverage in `test_helpers/test_spectra_specification.py`
and read an **untracked** `tests/debug_logs/specification.spectra`, so it could
only ever have passed on one machine; `test_hongbo` appended to a checked-in
fixture on every run. The numbering rule is now asserted directly against a
temporary file in `tests/test_util/test_file_util.py::TestWriteTrace`.

## 8. Commits

| Commit | Summary |
| --- | --- |
| `5eb76de` | DOCS: outstanding session notes from 2026-07-28 to 07-31 |
| `db6f1fe` | FIX: a debug-graph label must never end the repair run |
| `28abfc2` | FIX: a candidate Spectra cannot check must end its branch |
| `4327443` | FIX: drawing the debug graph must not end the repair run |
| `6e0c1bf` | FIX: heap exhaustion in Spectra must end its branch |
| `f4106ef` | FEAT: assert the repair's preconditions on its case study |
| `44f4b09` | FEAT: a branch may not vanish |
| `074fef3` | FEAT: six toggles for which formulas the learner may weaken |
| `bf3d34b` | SIMPLIFY: exclude initial formulas outright, not via toggles |
| `81da75c` | FIX: three silent corruptions surfaced by AMBA and genbuf |
| `e81366a` | FEAT: AMBA and genbuf case studies, in both setups |
| `9a4bb0d` | FIX: regenerate traces of every case study failing preconditions |
| `56f51ac` | FEAT: enumerate FastLAS solutions systematically |
| `abff783` | FIX: let guarantee weakening reach counter-strategies |
| `8b461f6` | CHORE: experiment pipeline, merge splitting, trace generation |
| `c32902e` | FIX: trace numbering from 0 on empty file; retire test_debug |

## 9. Experiments relaunched (16:30)

All four sweeps were restarted on `c32902e`. The previous sweeps - started
13:13 - were running **without** the dead-end root-cause fix, which had not yet
been committed, so their results were not usable. Old tmux sessions were killed
first so nothing kept writing into the same NFS output directories, a
contamination mode that has bitten before.

| Machine | Learner | Setup | Runs | Command |
| --- | --- | --- | --- | --- |
| gpu11 | FastLAS `n_runs=10` | trace-violation | 60 | `LEARNER=fastlas FASTLAS_RUNS=10 MAX_WINDOWS=8 ./scripts/run_parallel_bfs_repair_trace.sh` |
| gpu13 | ILASP | trace-violation | 60 | `LEARNER=ilasp MAX_WINDOWS=8 ./scripts/run_parallel_bfs_repair_trace.sh` |
| gpu14 | FastLAS `n_runs=10` | strengthened | 19 | `LEARNER=fastlas FASTLAS_RUNS=10 ./scripts/run_parallel_bfs_repair_syn.sh all` |
| gpu15 | ILASP | strengthened | 19 | `LEARNER=ilasp ./scripts/run_parallel_bfs_repair_syn.sh all` |

Log directories:

    gpu11  logs/trace_tests/all_fastlas_2026-08-06_163019/
    gpu13  logs/trace_tests/all_ilasp_2026-08-06_163028/
    gpu14  logs/parallel_tests/all_fastlas_2026-08-06_163038/
    gpu15  logs/parallel_tests/all_ilasp_2026-08-06_163047/

`SPEC_REPAIR_FASTLAS_RUNS=10` was verified in the live process environment, not
just in the launch command.

**Note on deployment:** the four machines share **one** NFS checkout at
`/vol/bitbucket/tg4018/PhD/SpecRepair`, so the update only had to be applied
once. `git pull` from the boxes fails - no SSH agent forwarding to GitHub - so
the transfer went by `git bundle` over `scp`.

## 10. Test-suite state

**812 passed, 6 failed.** All six failures are **pre-existing**, confirmed by
re-running them against a stashed clean tree:

* `test_perf/test_cs_to_trace_performance` (×2)
* `test_util/test_spec.py::test_all_unrealisable_cores_raw_*` (×3)
* `test_debug/test_asp.py::test_hongbo` - now fixed and the file deleted

Two things worth carrying forward:

* **`tests/test_diagnosis/test_trivial_solution.py` hangs the whole suite.**
  Measured at 87 minutes with no child process, blocking inside a JVM call that
  `--timeout=300 --timeout-method=thread` **cannot interrupt**. It is
  pre-existing - untouched since `df58ddb`, and its case list includes
  `colorsort` with the known BDD ceiling - but it is *not* on the skip-list, so
  a full run currently needs `--ignore` on it. Unresolved.
* `--deselect tests/test_asp.py::test_hongbo` was a **wrong path** and silently
  deselected nothing; the file was `tests/test_debug/test_asp.py`. A deselect
  that does not resolve is a no-op, not an error.

## 11. One naming convention: `case_study_1` and `case_study_2`

The same setup had **three different names depending on the layer** - the
original setup was `strengthened` in the input tree, `parallel_tests` in the
tmux session and log directory, and `repair_syn` in the output directory. The
new setup was `trace_violation`, `trace_tests` and `repair_trace_syn`. Nothing
connected them, so reading a log path told you nothing about which experiment
produced it.

Settled on **`case_study_1`** (was strengthened / parallel_tests / repair_syn)
and **`case_study_2`** (was trace_violation / trace_tests / repair_trace_syn),
applied at every layer:

| Layer | `case_study_1` (was) | `case_study_2` (was) |
| --- | --- | --- |
| Input tree | `spectra/strengthened/` | `spectra/trace_violation/` |
| Output dir | `out/repair_syn/` | `out/repair_trace_syn/` |
| Log dir | `logs/parallel_tests/` | `logs/trace_tests/` |
| tmux session | `parallel_tests_*` | `trace_tests_*` |
| Runner script | `run_parallel_bfs_repair_syn.sh` | `run_parallel_bfs_repair_trace.sh` |
| Test module | `test_bfs_repair_orchestrator.py` | `test_bfs_repair_trace_violation.py` |
| Test class | `TestBFSRepairOrchestrator` | `TestBFSRepairTraceViolation` |
| Test methods | `test_bfs_repair_spec_<cs>_syn` | `test_bfs_repair_trace_violation_<cs>_<n>_syn` |
| `--setup` value | `strengthened` | `trace_violation` |

All now `case_study_1` / `case_study_2` — including
`scripts/run_case_study_1.sh`, `tests/test_main/test_case_study_1.py`,
`TestCaseStudy1`, and `test_case_study_1_<cs>_syn`.

The English word "strengthened" is **kept where it is a description rather than
a name** - a guarantee genuinely is strengthened, and `strong.spectra` is still
the artificially strengthened specification inside `case_study_1`.

## 12. The concurrency semaphore never worked

Found while watching the 16:30 sweep on gpu11: windows showing
`mv: cannot stat '.../slot_0.taken.3502253.taken.3502856.taken.3502799...'`,
case studies that never started, and `amba` sitting in endless BDD garbage
collection.

`run_case_study_2.sh` capped concurrency with one semaphore file per slot,
claimed by renaming `slot_<n>` to `slot_<n>.taken.<pid>` **in place**. The
waiting loop globs `slot_*` - which matches `slot_0.taken.123` exactly as
happily as `slot_0`. So a *waiting* window would claim an *already-claimed*
slot, chaining the name further, and the true `slot_0` ceased to exist. The
release `mv "$MY_SLOT.taken.$$" "$MY_SLOT"` then failed, because some other
window had renamed the file again - hence the `cannot stat`, and hence slots
that were never returned.

**Measured on gpu11 before the fix: 0 free slots and 39 concurrent runs against
a cap of 8.** That is the whole explanation for `amba` thrashing in garbage
collection and for almost nothing finishing - the box was running five times
its intended load.

Free and taken slots now live in **separate directories**, so a claimed slot is
invisible to the waiting glob, and the release is wrapped in a `trap ... EXIT
INT TERM` so a killed run cannot leak its slot. Verified under simulated
contention (12 workers, 3 slots): never exceeded 3 concurrent, every slot
returned, none leaked, no chained names. Verified again live after relaunch:
8 busy, 0 free, 0 chained, exactly 8 `python -m unittest` processes.

`run_case_study_1.sh` has no semaphore and was unaffected.

## 13. Sweeps relaunched again (17:15) on the new naming

All four were killed and restarted on `af90b23`, so every result uses the new
directory layout and the working semaphore.

| Machine | Session | Log directory |
| --- | --- | --- |
| gpu11 | `case_study_2_all_fastlas` | `logs/case_study_2/all_fastlas_2026-08-06_171549/` |
| gpu13 | `case_study_2_all_ilasp` | `logs/case_study_2/all_ilasp_2026-08-06_171552/` |
| gpu14 | `case_study_1_all_fastlas` | `logs/case_study_1/all_fastlas_2026-08-06_171602/` |
| gpu15 | `case_study_1_all_ilasp` | `logs/case_study_1/all_ilasp_2026-08-06_171603/` |

The 16:30 runs are discarded: gpu11/gpu13 were crippled by the semaphore bug,
and gpu14/gpu15 had only 4 results each, not worth keeping on the old naming.

**Beware the shared NFS when checking progress.** `ls -dt logs/...` on gpu14
returned *gpu15's* log directory, because all four machines share one
filesystem. Always name the exact per-session log directory.

## 14. Why `amba` sits in garbage collection forever

Diagnosed from a log of `Garbage collection #3233 ... 200033 nodes`. The number
that matters is the one that never changes: **200033 nodes on every line.** The
table is not growing.

We run Spectra with `--jtlv`, which selects the pure-Java BDD package instead of
the default CUDD. That is not arbitrary - CUDD failed to load, verified on macOS *and* on gpu13,
both failing identically (**superseded by §16**: on Linux this was only a
missing library path):

    java.lang.NullPointerException: Cannot load from int array because "attrSizes" is null

The JTLV factory runs a fixed node table of 200033. Each collection frees
78k-130k nodes, so **40-65% of the table is free afterwards**. JavaBDD only
resizes when free-after-GC falls *below* `minFreeNodes` (default 20%), so the
engine concludes it need not grow - but the reclaimed space refills within
milliseconds and it collects again. 3252 collections against 17.5s of cumulative
GC is **~186 collections per second**, indefinitely.

It is a stable equilibrium: never resizes, never runs out of memory, never
finishes. Which makes it worse than a crash - there is nothing to catch. It is a
different failure from the heap exhaustion already handled in
`_synthesise_or_reject`, where `--counter-strategy` materialises a strategy past
12.8M nodes and throws.

Only the large case studies reach it: BDD size scales with the boolean state
space, so `amba`, `genbuf` and `colorsort` qualify and `minepump` and `lift`
never approach the table size.

**What was done.** `Env` exposes `enableReorder` but *no* accessor for the node
table, so of the two levers only variable reordering is reachable - sifting is
what actually moves BDD size. It is wired in behind `SPEC_REPAIR_BDD_REORDER=1`
and is **off by default, deliberately**. Reordering is semantics-preserving, and
realisability verdicts were confirmed identical with it on and off. But it can
change *which* counter-strategy Spectra returns among the many valid ones, and
the search branches on the counter-strategy it is given - so runs either side of
the flag are not result-comparable, and it must not switch itself on underneath
a sweep in progress.

Not time-boxed, by request. The run reports how long it has been where it is
instead - see below.

## 15. Run output, and per-learner configuration

### 15.1 What a run says about itself

Runs printed very little of use and a lot of noise. The three-stanza
`Rule:`/`Hypothesis:`/`New Rule:` block fired once per adaptation per candidate -
thousands of times on a branching search - and never said which node or depth it
belonged to. It is now one debug-level line.

`ProgressReporter` gives one compact line per event, carrying depth, node, queue
and duration:

    [    0.0s] START  lift trace 1  [ilasp]
    [    0.8s] NODE   d0 n1  ASM   queue 0
    [    3.0s] LEARN  d0 n1  21 candidate(s)  (2.2s)
    [    3.1s] SOLVED d0 n1  leaf #0
    [    4.0s] DONE   lift trace 1  21 final, 0 intermediate, 1 nodes explored, 4.0s

The **learning step** is timed specifically - it is where ILASP/FastLAS and
Spectra run, and where a run that looks stuck nearly always is. Verification is
timed too but stays silent under 5s: it happens once per candidate and is
normally instant, so printing every one buries the lines that say where the run
is.

Three outputs, deliberately separate: **stdout** for watching, **`progress.log`**
for reconstructing a finished run after the pane is gone, and **`status.txt`**,
rewritten in place, for coming back the next morning:

    case study : lift trace 1
    learner    : fastlas (n_runs=10)
    started    : 2026-08-06 17:15:49
    elapsed    : 4.0s
    depth      : 0
    node       : 1 (queue 0, 1 explored)
    phase      : learning d0 (assumption_weakening)
    in phase   : 2.2s
    solutions  : 21 final, 0 intermediate

`in phase` is the line that answers the `amba` question above. The heartbeat
keeping it fresh sleeps between updates and writes a few hundred bytes, so it
costs nothing against a run saturating a core in the JVM.

### 15.2 `LearningConfig`: configuration that holds still

The half of `IHeuristicManager` that was never a heuristic is now its own frozen
object, owned per learner. A heuristic narrows a search that would still be
correct without it; these flags decide what counts as an admissible repair.

Three problems went with the old arrangement:

* **One object, every learner.** `_initialise_repair` assigned the
  orchestrator's manager to every learner at the start of each run, so a flag
  set for the assumption learner could not mean anything different for the
  guarantee learner. The knobs read as per-learner configuration while being
  global - this is exactly why the six toggles of §4 were withdrawn.
* **Mutated mid-run, then reset.** Running one weakening operator at a time
  meant deep-copying the manager and flipping flags on the copy, three times per
  learning step. "What is this learner configured to do" had a time-dependent
  answer.
* **Fixed at two learners.** Nothing was wrong with two; nothing supported a
  third either.

`LearningConfig` is frozen, and narrowing returns a new one:

```python
repairer = (BFSRepairOrchestratorBuilder.syntactic()
            .with_learner_config(ASSUMPTION_WEAKENING,
                                 LearningConfig().with_only(ANTECEDENT_WEAKENING))
            .with_learner_config(GUARANTEE_WEAKENING,
                                 LearningConfig().with_only(INVARIANT_TO_RESPONSE_WEAKENING))
            .build())
```

Learners left unconfigured keep the shared default, so configuring one does not
silently change the others, and a third learner can be added with a policy of
its own. `with_only` intersects rather than replaces, so a learner cannot gain
an operator it was denied. INITIAL stays out of `learnable_when` by default, for
the reasons in §4.

**Behaviour is unchanged**, which was the constraint. Verified end to end either
side of the refactor: `lift` trace 1 gives 21 final specs, `minepump` trace 0
gives 12, `traffic_single` trace 0 gives 1 final and 11 intermediate - identical
before and after. 814 passed with only the five pre-existing failures, plus 12
new tests covering the config itself.

The deferred heuristic-manager refactor of §4 is therefore **done** for the
configuration half. What remains in `IHeuristicManager` is now only genuine
selection: which counter-traces, which alternative tasks, which adaptations.

## 16. CUDD works on Linux after all - it just needed unpacking

§14 concluded CUDD "cannot load in this deployment", verified by the same
`NullPointerException: Cannot load from int array because "attrSizes" is null`
on macOS and on gpu13. That was two different causes wearing one error message.

**The native library ships inside the Spectra jars.** `spectra-cli.jar`
contains `libcudd.so` and `cudd.dll` - and no `.dylib`. So:

* **macOS genuinely cannot run CUDD.** There is nothing to load. JTLV is the
  only option, permanently.
* **Linux only needed the `.so` on `java.library.path`.** Extracting it needs
  no root, so it works on a shared box.

Measured on gpu13 with the extracted library:

| Case study | JTLV | CUDD | Verdict |
| --- | --- | --- | --- |
| minepump | 1.17s | **0.19s** | identical |
| genbuf | 0.4s | **0.2s** | identical |

`ensure_cudd_native()` unpacks the library at JVM startup and adds
`-Djava.library.path`; `SPEC_REPAIR_BDD=cudd` then selects it.

**macOS is untouched on every path**: the extractor returns early without
writing anything or adding a JVM argument, and an explicit
`SPEC_REPAIR_BDD=cudd` there is refused with a one-line notice rather than
swapping a working run for the NPE. Verified on the Mac - 828 passed, only the
five pre-existing failures.

Opt-in, for the same reason as reordering (§14): a different BDD package can
return a different counter-strategy among the many valid ones, and the search
branches on the one it is given.

**Not yet measured: whether CUDD fixes amba and colorsort.** The benchmark used
the raw CLI, which rejects those two before synthesising because it skips the
`pRespondsToS` substitution the real path performs, so both reported "(no
verdict)" in 0.3s rather than a real timing. That measurement is the one worth
taking next, since it is the whole reason for wanting CUDD.

## 17. Trivial-solution generation

Syntech's `exploreAllCores` does not return every unrealisable core, and the
ones it returns are not necessarily minimal, so a hitting set of them does not
reliably give a realisable specification. The recheck that compensates for that
is inherent and stays. What it did *twice* does not:

* **The recursion recomputed the cores it was just given.** The recheck computed
  a candidate's cores, then called back in, which recomputed exactly those cores
  as its first act. Every unrealisable intermediate cost two full core searches.
* **Candidates were dropped with `list.remove`**, and
  `SpectraSpecification.__eq__` is *semantic* equivalence via spot - so removing
  one ran an LTL equivalence check against every other candidate in the list.
* **No memoisation**, though sibling branches routinely reach the same
  trivialisation by removing the same guarantees in a different order.

Same solutions, fewer searches - identical counts on minepump, gyro, lift,
arbiter and elevator, and the existing tests pass.

**Where the time actually goes.** Measured per case study: every one finishes in
under a second except **colorsort, which exceeds 150s**. So the file that hung
the whole test suite (§10) hangs on `exploreAllCores` on one specification.
Halving the searches helps proportionally but does not make it fast. The
remaining levers are asking for *one* core rather than all where the caller only
needs a hitting set, and CUDD (§16).

## 18. The third experiment type - built, and running

`case_study_3`. The first two setups manufacture their traces symbolically:
ASP is asked for a trace violating some assumption and obliges, but it
constrains the system's moves only by the specification, so a trace can contain
system behaviour no synthesised controller would ever produce. A repair learned
against such a trace is a repair against a fiction.

Here a controller is synthesised and **run**. The environment respects the
assumptions for N steps, then acts at random until it breaks one. Every system
value in the trace is genuine controller output.

### 18.1 What syntech provides, and what it does not

Controller execution is theirs: `ControllerExecutor` in **spectra-executor**,
loaded here against a `StaticController` over the files
`synthesise_controller` writes (`controller.init.bdd`, `controller.trans.bdd`,
`vars.doms`).

**The environment side does not exist anywhere in the SpectraSynthesizer
org.** Checked: `ControllerExecutor` offers `getAllLegalSystemOutputs` with no
counterpart for inputs; **spectra-ext** has only `CTDExecutor`; and
**spectra-sim** turns out to be a set of worked examples - CinderellaStepmother,
TowersOfHanoi, MonkeyRunner - each hand-rolling its own environment in a
per-example `Board.java`, with nothing shared to reuse.

So "does this input respect the assumptions" is answered with **this project's
own ASP violation check** - the same one the repair, the preconditions and the
oracle use. That keeps one definition of "violates an assumption" across the
whole pipeline instead of introducing a second.

### 18.2 Two things the controller itself teaches

Both found by getting them wrong first, and both are properties of GR(1) rather
than of this code:

* **A refused step is free to retry.** Spectra's controller will not accept an
  input its assumptions forbid, and the executor does not advance when it
  refuses - so the next candidate starts from the same state. That does most of
  the compliance filtering for free. A step that succeeds and only *then* turns
  out to violate is the unrecoverable one: there is no rewind, so the episode is
  abandoned and retried.
* **A refusal during the random phase is not a dead end - it is the
  violation.** The controller is only obliged to respond while the environment
  keeps its assumptions, so a refusal means one has just been broken. Treating
  it as failure produced traces for **minepump alone**, whose controller happens
  to tolerate the violating input and carry on; every other case study silently
  produced nothing. The difference was whether the controller tolerated the
  violation, not whether one occurred.

### 18.3 What was generated

**29 traces, precondition audit 29 OK / 0 BAD.**

| Case study | Traces | Example violation |
| --- | --- | --- |
| minepump | 5 | `assumption2_1`, `assumption1_1` |
| minepump_liveness | 5 | `assumption3_1`, `assumption1_1` |
| gyro | 5 | `ready_stays_ready` |
| traffic_single | 5 | `car_moves_when_green`, `car_idle_when_red` |
| traffic_updated | 5 | `carA_moves_when_green`, `carB_idle_when_red` |
| pcar | 4 | `sideSense_mutual_exclusion` |

Not generated, and why:

* **amba** - the CLI rejects its initial conditions before synthesis, so no
  controller can be built (the same check that made §16's benchmark report "(no
  verdict)").
* **arbiter** - only a liveness assumption, which no finite prefix can violate.
  It is excluded from case_study_2 for exactly this reason.
* **lift, elevator, humanoid, colorsort, genbuf** - a uniformly random
  environment did not break their assumptions within the step budget. These want
  a *targeted* environment - one that aims at a chosen assumption rather than
  sampling blindly - which is the obvious next iteration.

The layout matches case_study_2 exactly (`original.spectra` +
`violation_trace_<n>.txt`), so the runner, the pipeline and the precondition
assertions all apply unchanged.

### 18.4 Running now

| Machine | Learner | Session | Log directory |
| --- | --- | --- | --- |
| gpu12 | FastLAS `n_runs=10` | `case_study_3_all_fastlas` | `logs/case_study_3/all_fastlas_2026-08-07_000503/` |
| gpu20 | ILASP | `case_study_3_all_ilasp` | `logs/case_study_3/all_ilasp_2026-08-07_000514/` |

30 runs each, capped at 8 concurrent, alongside the four case_study_1 and
case_study_2 sweeps on gpu11/13/14/15.

## 19. Housekeeping

* **`run_case_study_1.sh` had no concurrency cap at all** - 19 tests, 19
  simultaneous JVMs, which is the condition behind its OutOfMemoryError
  failures. Now `MAX_WINDOWS=8` by default, 0 for the old behaviour.
* **The semaphore is now shared** (`scripts/lib/slots.sh`) by both runners, so
  they cannot drift apart - the §12 bug existed in one runner only because the
  other had no cap to get wrong.
* **Run labels** now read `case_study_2 / pcar / trace 2` rather than
  `pcar_trace2_fastlas_2026-08-06`, which said neither which setup it came from
  nor, legibly, which trace.
* **`NewSpecEncoder._hm` renamed to `_config`**, and `builder.enabling(...)`
  folded into the same `LearningConfig` that `with_learner_config` sets, so
  learning policy has one entry point rather than two.

## 20. Open

* **Third experiment type** - built and running (§18). The random environment
  was replaced by a targeted one on 2026-08-07; see that day's notes, §4.
* ~~Heuristic-manager refactor~~ - done, see §15.2.
* **submarine** - realisability check throws; deliberately excluded from the
  precondition audit.
* **`test_trivial_solution.py`** - no longer hangs the suite for the other case
  studies (33 pass in 10s), but colorsort alone still exceeds 150s in
  `exploreAllCores` (§17).
* ~~Does CUDD fix amba and colorsort?~~ **Measured on 2026-08-07: yes.** A full
  amba repair completed in 577s with **zero** garbage-collection lines. See the
  2026-08-07 notes, §3.
