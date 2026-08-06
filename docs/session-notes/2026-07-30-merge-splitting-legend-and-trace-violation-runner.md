# Splitting the merge, shrinking the legend, running the new case studies, and two crashes — session notes

Session date: 2026-07-30. Started with the five items from the PERSONAL NOTES
appended to the [2026-07-28](2026-07-28-experiment-pivot-to-trace-violation-and-pipeline-fixes.md)
notes (Parts 0-5), then went on to make the runners solver-configurable and to
fix the two crashes that surfaced once the new case studies were actually run
under both learners (Parts 6-8).

The learner comparison itself — what FastLAS and ILASP each produce, and what
that means for the methodology — is written up separately in
[2026-07-30-fastlas-vs-ilasp-results](2026-07-30-fastlas-vs-ilasp-results.md),
since those are results rather than engineering.

## Part 0: which open item the note meant

The note read:

> number 3 above is important to fix. a max limit of merges is not the right way to do it.

Open item **3** is "arbiter is unusable — its only assumption is `GF(a)`". The
max-merge limit is open item **5**. The second sentence names its subject
directly, so item 5 was the one meant; confirmed before starting. arbiter remains
open and untouched.

## Part 1: the merge splits instead of capping

`--max-merge-formulas` was the wrong shape of fix, and the note is right about
why. The problem was never the size of the merge — it was what happened next.
An unrealisable merge was broken back down with
`get_all_trivial_solutions_guarantee_only`, which starts from Spectra's
exhaustive all-unrealisable-cores search: the same cost centre that makes
ColorSort intractable, a blocking JVM call that cannot be interrupted from
Python, and on elevator_updated's 134-formula merge it did not return at all.
Capping the formula count only converted a hang into a refusal. Neither produces
a result, which is the thing the experiment actually needs.

**Divide and conquer.** Merge everything; if the result is realisable, that is
the answer. If it is not, the set over-constrains the system, so split it in
half and merge each half independently, recursively. A single specification that
is still unrealisable is torn down with the core search — safe there, because it
is one repair-sized spec, which that search handles in well under a second.
Termination is structural: each recursion halves the set, and a singleton cannot
be split further.

The expensive search is therefore never reached on a large merge. Cost is
proportional to how fragmented the answer actually is rather than to the number
of inputs: the recursion does one check per node and bottoms out at `k` leaves,
so `k` pieces cost `2k-1` checks.

Measured on real pulled data:

| Case study | Inputs | Merged | Checks | Splits | Time |
|---|---|---|---|---|---|
| pcar | 19 | 1 | 1 | 0 | <1s |
| lift | 21 | 1 | 1 | 0 | 1s |
| elevator_updated | 966 | 373 | 745 | 372 | **173s** |

elevator_updated is the run that previously never returned. `745 = 2×373 - 1`
exactly, which is the arithmetic above and a useful check that no teardown was
reached — none was.

The 373 is itself a finding worth keeping: those 966 repairs genuinely conflict.
They do not merge into one solution, or a handful, and no amount of algorithm
choice changes that. It is evidence for open item 5's other half — that merging
*all* repairs may not be the right operation at scale — rather than against it.

`--max-merge-formulas` is gone from the pipeline. `MergeTooLargeError` and
`max_formulas_for_trivial_fallback` survive as accepted-and-ignored, so older
callers still import and run; the parameter logs a deprecation warning.

## Part 2: the legend was competing with the graph

The legend was a Graphviz cluster, so `dot` laid it out *as part of the graph* —
18-24pt boxes plus a whole nested table demonstrating the equivalence bubble.
On a small graph it came out wider than everything it was explaining.

It is now the **graph's own label**, with `labelloc=b` / `labeljust=r`, so it is
placed after layout, in the bottom-right corner, taking only the strip of canvas
it occupies. 8pt text, 6px swatches, and one line of text for the bubble rather
than a reproduction of one.

Measured on a three-group graph: the cluster added 234,000 px² around a
45,900 px² graph; the compact legend adds 22,700 px². About a tenth, as asked.

`--legend {compact,full,none}` on `visualise_resulting_specs.py`, threaded
through `run_experiment_pipeline.py`. `full` is the old cluster, kept because it
is more legible when a graph is large enough not to care.

`original` was added to `GROUP_COLOURS` sharing `strong`'s colour, since it plays
the same role in the new setup — otherwise it cycled through `EXTRA_COLOURS` and
changed colour between runs.

## Part 3: minepump's second assumption, double-checked

The supervisor's edit strengthened `trace_violation/minepump/original.spectra`
in two places, making it byte-identical to `strengthened/minepump/strong.spectra`
(the old file was missing a trailing newline; that is the only difference). This
is deliberate — minepump is studied that way — so the edit was kept, not treated
as the drift it would be elsewhere.

The relevant change is `assumption2_1`:

| | |
|---|---|
| was | `G(!highwater -> (!highwater \| !methane))` — a tautology, unviolable at any length |
| now | `G(!highwater \| !methane)` — violable from **2** timepoints |

So "3 steps should be enough" is confirmed, with one to spare. It is 2 rather
than 1 because `initial_assumption` forces `!highwater & !methane` at t0, so the
conflict cannot appear until t1.

The 2026-07-28 notes and the case-study README both cite this assumption as the
worked example of a tautology. Both now say it *was* one and has since been
strengthened — the pattern is still worth watching for, but the example is no
longer live.

`test_tautological_assumption_is_reported_unviolable` cited it too, and failed
for exactly the right reason. The *property* is still worth pinning, so the test
now uses a two-assumption specification written into the test file — one
tautological, one violable as a control so it cannot pass by everything being
unviolable — rather than a case study that is free to move underneath it.

### Targeting invariant assumptions

Regenerating minepump's five traces meant being able to say *which* assumptions
may be violated: the ask was violations of either **invariant** assumption, and
`initial_assumption` is neither interesting nor what was wanted. An `ini`
violation only says the run started in a state the specification excludes; no
temporal behaviour is exercised.

`find_violable_assumptions` and `generate_assumption_violating_traces` gained
`only_assumptions`; the CLI gained `--invariant-only` (selects `when == G` off
the formula table, so it generalises to every case study) and
`--only-assumptions NAME ...`. Neither relaxes anything — every formula outside
the targeted set must still hold, so this narrows the *choice* of violation, not
the constraints on it.

One bug caught while writing it: the `when` column holds `GR1TemporalType` enum
members, not strings, so an initial `when == "G"` comparison silently matched
nothing and reported "no invariant assumptions" rather than failing.

Five traces regenerated, `--seed 0`, 1-5 timepoints: three violating
`assumption1_1` (which needs 4, being under a `next`), two violating
`assumption2_1`. All five verified independently — fed back through
`get_violations` rather than trusting the generator — each violating exactly one
invariant assumption, no guarantee, and never `initial_assumption`.

## Part 4: running the trace-violation case studies

`tests/test_main/test_bfs_repair_trace_violation.py` is the counterpart to
`test_bfs_repair_orchestrator.py`'s `*_syn` tests. Two differences follow from
the pivot:

* the spec repaired is `original.spectra`, and nothing manufactured it, so there
  is no known-good answer to compare against — the tests assert that repair runs
  and returns at least one weakening, nothing more;
* five traces per case study means five independent runs, so one test per
  (case study, trace).

50 tests, generated at import from what is on disk — following the existing
`test_solution_merger.py` idiom — so each has its own selectable name:
`test_bfs_repair_trace_violation_minepump_3_syn`. arbiter contributes none,
having no traces, and that falls out of the discovery rather than needing a
skip.

`scripts/run_parallel_bfs_repair_trace.sh` drives them in tmux, mirroring
`run_parallel_bfs_repair_syn.sh`. One addition: 50 windows means 50 simultaneous
JVMs, which is enough to exhaust the box, so `MAX_WINDOWS` (default 10) gates
them behind a file-based semaphore — all windows are created up front, each
claims a slot by `mv` (atomic within a filesystem) before starting and releases
it after.

Output lands in `test_files/out/repair_trace_syn/<case_study>_trace<ID>_<date>/`,
which `pull_experiment_from_ssh.sh` handles unchanged via
`REMOTE_SUBDIR=repair_trace_syn`.

**These runs are much heavier than the strengthened ones.** One test —
`minepump_1`, a 4-timepoint trace violating `assumption2_1` — was started
locally to verify the plumbing and was still going after ~50 minutes, past 200
recorded specifications. The plumbing is confirmed working (spec and trace load,
orchestrator builds, output lands in the right layout), but the run itself did
not finish. The cause is not mysterious: these traces are 4-5 timepoints where
the strengthened setup's were shorter, and the BFS search branches per timepoint.
It matters for planning the sweep — 50 of these is not 50 of the old ones, and
`MAX_WINDOWS` should be tuned with that in mind.

## Part 5: post-processing the new case studies

Steps 2-4 are identical for both setups — merging, maximal-by-GAR and semantic
uniqueness do not care where the specs came from. Only step 6 differs, in which
reference specifications it draws: `strong` + `ideal` for the strengthened
setup, `original` for the trace-violation one, which has neither.

So it is a `--setup {strengthened,trace_violation}` flag on
`run_experiment_pipeline.py` rather than a second copy of the pipeline that
would drift. `scripts/run_trace_experiment_pipeline.sh` is the thin batch driver
over it, the analogue of `find_maximal_all_case_studies.sh`.

The one real wrinkle: run directories are named `<case_study>_trace<ID>_<date>`,
so the case study is `minepump`, not `minepump_trace3`. `case_study_dir_name`
strips the suffix before looking up `original.spectra` and the trivial
solutions.

Verified end to end on a synthetic `2026-07-30` run directory built from real
minepump final specs: 5 specs merged to 2, both maximal, both semantically
unique, all three graphs drawn with `original` as the reference group and the
trivial group correctly reported missing.

## Part 6: choosing the learner from the runner

Both tmux runners now take `LEARNER` (default `ilasp`):

```bash
LEARNER=fastlas ./scripts/run_parallel_bfs_repair_syn.sh
LEARNER=fastlas ./scripts/run_parallel_bfs_repair_trace.sh
```

The runner exports `SPEC_REPAIR_LEARNER`; the test classes read it once in
`setUpClass` and hand it to a new `BFSRepairOrchestratorBuilder.using_learner()`,
the name-keyed form of `using_fastlas`. Reading it once per class rather than per
test is deliberate — a mid-run change would put half ILASP's results and half
FastLAS's under one directory name.

An unknown name raises immediately, listing the valid ones. Silently falling back
to the default would produce a directory of ILASP results labelled as FastLAS,
which is worse than a crash: it is wrong data that looks right.

**Only a non-default learner gets a directory suffix.** ILASP keeps
`minepump_<date>`; FastLAS writes `minepump_fastlas_<date>`. Every existing
pulled directory and downstream path was written against the unsuffixed name and
keeps working unchanged, and a FastLAS run lands *beside* an ILASP run of the
same date rather than overwriting it — which is what makes them comparable at
all. tmux sessions and log directories are learner-scoped too, so both sweeps can
run at once. `case_study_dir_name` strips `_trace<ID>` and `_fastlas`, verified
across all seven naming permutations including
`minepump_liveness_trace0_fastlas` → `minepump_liveness`.

`scripts/run_learner_comparison.py` runs the same unittest methods locally, one
subprocess per case study so a non-terminating run is killed without taking the
sweep with it, appending to a JSON summary as it goes. Necessary rather than
tidy: several (learner, case study) pairs do not finish, and the useful result is
*which*, measured. `run_experiment_pipeline.py` gained `--runs-root` so those
locally produced runs — which land in `out/repair_syn/`, not `out_ssh/<date>/` —
can be post-processed.

## Part 7: two crashes, one per learner

Running the new case studies under both solvers surfaced two pre-existing bugs.
gyro and lift failed on every attempt, and **which** crash you got depended on
the learner, because the learner determines how far the search gets before
dead-ending. Neither is FastLAS-specific in origin.

### `TypeError: expected string or bytes-like object` (hit by ILASP)

`synthesise_extract_counter_strategies` and `synthesise_check_realisability_only`
return `None`, not output, when `violations_in_initial_conditions` screens a file
out up front — a check that exists because Spectra's CLI reports these
inconsistently. Both oracle entry points then ran `re.search(pattern, None)`,
several frames below the repair search, naming neither the specification nor the
reason. For gyro and lift the trigger was *"Initial assumption refers to system
variables"*: the search had produced a candidate that is malformed by Spectra's
own rules.

The tempting fix — guard the `None` and return a boolean — is wrong. `None`
means Spectra **declined to check the specification at all**, so there is no
honest verdict: `True` records a specification Spectra never checked as a repair,
`False` claims an unrealisability result it never reached. `_reject_unverifiable`
raises `SpecificationNotVerifiableException` instead, naming both cause and spec,
and `repair_bfs` catches it, logs the candidate as `Unverifiable`, and continues
with the other branches.

That distinction is the whole win. **ILASP now finds 2 repairs for gyro and 7 for
lift, where the run previously died.** The malformed candidate was never the only
one — it just took the run down with it, and a silent boolean would have hidden
that rather than fixed it.

`is_realisable` carried the identical latent bug and is fixed too, though nothing
had reached it yet.

### `IndexError: list index out of range` (hit by FastLAS)

`_add_edge_data_to_graph` labels each edge with whatever record of the transition
exists — a deadlock completion, or the last adaptation — and indexed
`counter_traces[-1]` and `adaptation_history[-1]` unconditionally. A transition
carrying neither ended the entire repair run from inside **debug-graph
bookkeeping**. That is reachable whenever a learner dead-ends before producing
any counter-trace, which FastLAS does far more often precisely because it returns
a single solution per step.

Now the edge takes whichever record exists, most informative first, falling back
to a plain `details` label. Losing an annotation is the right cost; losing the
run is not. The deadlock-completion path is untouched and still tested.

Six tests pin both fixes. Writing them caught a real trap: `RepairData`'s fourth
positional parameter is `spec_history`, not `adaptation_history`, so passing the
latter positionally silently populates the wrong field — the tests use keyword
arguments and say why. An existing test in that file passes
`RepairData(trace, [], learning_type, [], 0, 0)`, landing `0` in
`adaptation_history`; harmless today because it is falsy, but worth knowing.

## Part 8: what the fixes revealed

| | before | after |
|---|---|---|
| ILASP gyro | `TypeError` crash | **ok — 2 repairs, 17s** |
| ILASP lift | `TypeError` crash | **ok — 7 repairs, 9s** |
| FastLAS gyro | `IndexError` crash | completes, **0 repairs**, 8s |
| FastLAS lift | `IndexError` crash | completes, **0 repairs**, 5s |

FastLAS genuinely finds no repair for gyro and lift on trace 0. That is now a
measurable finding reported as a clean assertion failure, rather than a crash
that said nothing.

The full learner comparison and its research findings are written up separately —
they are results rather than engineering, and belong with the experiment record
rather than in session notes.

## Final state

| File | |
|---|---|
| `spec_repair/diagnosis/solution_merging.py` | divide-and-conquer merge; cap deprecated |
| `spec_repair/diagnosis/violation_trace_generation.py` | `only_assumptions`, `when` filter |
| `scripts/visualise_resulting_specs.py` | compact bottom-right legend, `--legend` |
| `scripts/run_experiment_pipeline.py` | `--setup`, `--legend`; `--max-merge-formulas` removed |
| `scripts/generate_violation_traces.py` | `--invariant-only`, `--only-assumptions` |
| `scripts/run_parallel_bfs_repair_trace.sh` | new — tmux runner, concurrency-capped |
| `scripts/run_trace_experiment_pipeline.sh` | new — post-processing batch driver |
| `tests/test_main/test_bfs_repair_trace_violation.py` | new — 50 generated tests |
| `input-files/.../trace_violation/minepump/` | strengthened `original.spectra`, 5 new traces |
| `main/bfs_repair_orchestrator_builder.py` | `using_learner`, `learner_from_env`, learner names |
| `main/bfs_repair_orchestrator.py` | skip unverifiable candidates instead of dying |
| `spec_repair/components/oracles/spectra_gr1_oracle.py` | `_reject_unverifiable` guard |
| `spec_repair/components/orchestration_managers/a_orchestration_manager_with_graph.py` | edge labels degrade instead of crashing |
| `spec_repair/exceptions.py` | `SpecificationNotVerifiableException` |
| `scripts/run_parallel_bfs_repair_syn.sh` | `LEARNER` selection |
| `scripts/run_learner_comparison.py` | new — local sweep with per-run timeouts |
| `tests/test_components/test_spectra_oracle.py` | 3 tests for the oracle fix |
| `tests/test_components/test_orchestration_manager_syntactic_equivalence.py` | 3 tests for the graph fix |

## Open items for next session

1. **373 merged solutions from 966 elevator_updated repairs.** The merge now
   terminates, but the result is heavily fragmented. Whether merging all repairs
   is the right operation at that scale is still the methodology question from
   the previous session's open item 5 — this just makes it answerable with a
   number instead of a hang.
2. **arbiter is still unusable** — original open item 3, deliberately not
   touched. Needs a non-liveness assumption or a bounded-liveness encoding.
3. **The trace-violation runs have not been executed at scale on the box.**
   Twenty of them ran locally under each learner (trace 0 only) and the
   post-processing pipeline was exercised on those real runs, so the plumbing is
   no longer only synthetically verified. What remains is the full sweep — all
   five traces per case study, on the GPU box. Note the earlier "~50 minutes and
   still going" observation was a *pre-fix* ILASP run on minepump trace 1; post
   fix, every ILASP trace-violation run that completes does so in 6-17s, so that
   figure should not be used for planning.
4. **FastLAS finds no repair at all for gyro and lift** on trace 0, where ILASP
   finds 2 and 7. Now a clean result rather than a crash, and the sharpest
   available case for asking whether one-solution-per-step is an acceptable
   trade — see the research report.
5. **minepump's traces now need 1-5 timepoints**, where the other nine case
   studies were generated with the 1-3 default. Regenerating them all
   `--invariant-only` would make the set consistent, and would drop the `ini`
   violations the earlier run was free to pick.
6. Still open from before: FastLAS `#bias` (determinism is now measured rather
   than open — see the research report), ColorSort, the broken
   `test_solution_merger.py` fixtures, and `scripts/` organisation.
