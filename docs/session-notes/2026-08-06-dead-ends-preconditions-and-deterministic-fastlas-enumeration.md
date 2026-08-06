# Every node must lead to a leaf: dead ends, case-study preconditions, and making FastLAS deterministic

Report date: 2026-08-06 (early report, written mid-afternoon; the four sweeps
relaunched at 16:30 are still running).

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
counts as an *admissible repair*. A configurable, per-learner version belongs
with the deferred heuristic-manager refactor.

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

## 14. Open

* **Third experiment type** - supervisors want one. `unrealisable.spectra`
  exists for minepump and minepump_liveness (strengthened guarantees plus a
  removed assumption), a natural seed exercising guarantee weakening as the
  primary path rather than as a fallback.
* **Heuristic-manager refactor** on a branch - deferred deliberately (§4).
* **submarine** - realisability check throws; deliberately excluded from the
  precondition audit.
* **`test_trivial_solution.py` JVM hang** (§10).
