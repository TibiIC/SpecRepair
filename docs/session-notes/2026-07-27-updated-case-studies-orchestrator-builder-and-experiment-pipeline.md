# `*_updated` case studies, ColorSort's real bottleneck, an orchestrator builder, and the experiment pipeline — session notes

Session date: 2026-07-27. Started by resuming an investigation that a
`~/Documents` access outage had interrupted mid-flight, and ended up
touching most of the experiment toolchain: seven new case studies, the
long-standing "why does ColorSort produce nothing" question, a builder to
kill orchestrator boilerplate, three duplicated merge implementations
collapsed into one, and a six-step experiment pipeline wired end to end.

Work landed across three branches — see [Final state](#final-state).

## Part 1: finishing the interrupted mutation investigation

Three questions were outstanding from the interrupted session: which case
studies currently work, how the five newer case studies' `strong.spectra`
were chosen, and whether the mutation code can strengthen assumptions
*and* guarantees together.

**How `strong.spectra` was chosen.** A raw `diff` against `ideal.spectra`
is useless here: `strong.spectra` is a fully normalised re-serialisation
of the whole file, with atoms reordered, so nearly every line differs
cosmetically. Parsing both with the same parser and re-serialising with
the same formatter isolates the real change. Result: **every existing
case study's `strong.spectra` is assumption-only**. Two earlier
hypotheses were wrong and are corrected here: formula counts and atom
sets are *identical* between ideal and strong (the "+2 lines" is
serialisation whitespace, not an added formula), and `replace_formula`
edits in place by name rather than appending a label+formula pair.

**Can the mutation code strengthen both sides?** Yes, and it does so
routinely. Assumption-only in 5/5 fixtures looked suspicious — with
`n_guarantee_steps = rng.randint(0, 2)` that is only a ⅓ chance each — so
both downstream filters were measured rather than reasoned about:

- Realizability is a mild skew, not a block. Over 30 seeded attempts per
  case study: elevator accepted 8 with `n_gar=0` vs 4 with `n_gar>0`;
  pcar 9 vs 7; gyro 0 vs 5.
- The violating-trace search shows *no* anti-guarantee bias at all —
  every mutation dropped for "no trace" was assumption-only.
- End-to-end, mutations touching both sides survive easily: elevator 3/6,
  pcar 2/4, humanoid 2/5, gyro 6/6.

So the assumption-only fixtures are a sampling artifact of taking
`mutation_0` from a single unseeded draw, not a limitation of the
generator.

## Part 2: seven `*_updated` case studies

Added `<name>_updated` for every case study whose `strong.spectra` was
assumption-only: elevator, gyro, humanoid, pcar, lift, traffic_updated,
colorsort. Each reuses its original's `ideal.spectra` and pairs it with a
`strong.spectra` strengthening **at least one assumption and at least one
guarantee**, plus a matching `violation_trace.txt`. Selection from seeded
`generate_realizable_mutations` output prefers the most balanced mutation
(max `min(#asm, #gar)`), then breadth, then temporal-shape changes
(`GF -> G`), then how much text was dropped.

**arbiter and traffic_single deliberately have no `_updated` variant** —
for both, guarantee strengthening is provably impossible, not merely
unlucky:

- arbiter's only eligible guarantee `G(!g1|!g2)` reduces to `G(!g1)` or
  `G(!g2)`, each contradicting its `F(g1)`/`F(g2)` promises.
- traffic_single's sole possible guarantee strengthening is
  `GF(!car) -> G(!car)`, and `car` is an *environment* variable, so it is
  unrealizable as a guarantee. Confirmed by exhaustive enumeration over
  40 seeds.

Seventeen `_syn` tests now exist. `run_parallel_bfs_repair_syn.sh` takes
an optional group argument (`all` | `original` | `updated`) with a
group-scoped tmux session name and log directory, so two groups can run
side by side.

## Part 3: ColorSort's real bottleneck — and the one behind it

[Last session's](2026-07-24-colorsort-zero-specs-orphaned-processes-and-test-cleanup.md)
working theory was that BFS was burning through branches that each wait
out the full 60s ILASP timeout. **That was only about 25% right.**

Profiling (sampling profiler on the main thread, plus timing every
subprocess and every oracle call) put **74–90% of wall time inside a
single `SpectraToolbox.exploreAllCores` call**. After 16 minutes the run
was still inside the *first* one — measured directly as `1 distinct
input, 0 repeats`, which also killed the memoisation hypothesis I started
with.

Timing one `run_all_unrealisable_cores` per case study's
`strong.spectra`: arbiter 0.69s, everything else ≤0.06s, **colorsort
>180s and never returning**. All of them return **zero cores**, because
every `strong.spectra` is realizable by construction.

**Fix:** `run_all_unrealisable_cores` now checks realizability first and
returns `[]` when realizable — which is provably the answer, since a
realizable specification has no unrealisable core. ColorSort: **1.43s
instead of >16 min**. Verified non-regressive: elevator/pcar/traffic_single
produce identical final-spec counts with and without it (16/19/3), and
traffic_single still runs 9 full core searches on its genuinely
unrealizable specs, so the short-circuit only fires where it is a no-op.

**ColorSort still produces zero repairs.** Past the cores blocker it
stalls in BDD counter-strategy synthesis instead — a 60-minute unattended
run reached ~32 min CPU and 2.4GB RSS with no specs and **no error
raised**. That is the same cost centre `synthesise_check_realisability_only`'s
docstring already warns about. With 39 boolean atoms this is a genuine
state-space ceiling, separate from the cores problem. Item 1 from last
session is therefore *diagnosed but not solved*.

Operational note: long JVM/JNI calls hold the GIL, so an in-process
Python watchdog thread is starved and its wall-clock cap never fires. Use
an external `( sleep N; pkill -f ... ) &`. `py-spy` needs root on macOS,
so it cannot dump these stacks.

## Part 4: a builder for BFSRepairOrchestrator

Every construction site repeated ~13 lines of identical wiring. What
actually varied was a small discrete set of choices that always travel
together, so those became four presets — `semantic`, `syntactic`,
`assumption_only`, `guarantee_only` — with fluent overrides on top.

The builder also removes a real wart rather than just boilerplate.
Callers wanting to snapshot the search graph on each recorded spec had to
build the logger with a closure over a mutable `repairer_ref = []` and
append the orchestrator afterwards, because the orchestrator takes the
logger as a constructor argument. The builder owns both, so
`with_on_record` hands the finished orchestrator to the callback
directly; `SpecLogger` gained `set_on_record` to make that explicit.

Net **−236 / +76** lines across five call sites. Two latent bugs
surfaced, both from positional arguments into a keyword-heavy
constructor: the tests' `run_single_repair` passed `hm/recorder/logger`
into the `om/hm/recorder` slots (silently installing a heuristic manager
as the orchestration manager), and `scripts/repair_specification.py` did
the same *and* referenced an undefined `NewSpecOracle()`, so it could
never have run.

## Part 5: `UniqueSpecRecorder` was silently discarding results

Chasing a documented quirk — the syntactic preset's non-debug path used
semantically-deduping recorders — turned up something worse.

Both modes bottom out in `SpectraSpecification`'s dunders, which disagree
by design: `__eq__` is spot-backed logical equivalence, `__hash__` is
purely syntactic. So `sem_equivalence=True` scans a list with `__eq__`
(true semantic dedup) while `sem_equivalence=False` goes through the
set/dict, where `__hash__` picks the bucket and `__eq__` only runs inside
it (syntactic dedup). Measured: two equivalent specs give 1 entry
semantic, 2 syntactic. **The dedup is on whole specifications.**

The real bug: in semantic mode `add()` appended to its own `_specs` list
and **never called `super().add()`**, so `UniqueRecorder`'s
`_set`/`_value_to_id` stayed empty forever. Every inherited read method
reported on that empty store — `get_all_values() -> []`, `__len__ -> 0`,
`__contains__ -> False`, `get_id() -> None`. Only `get_specs()` worked,
because it alone branched on the mode.

That silently discarded results for the two callers reading back via
`get_all_values()`: the degradation runner (which then wrote zero
`*_fix_*.spectra` and returned `[]` without failing, since it asserts
nothing) and `scripts/repair_specification.py` (whose `assert len(...) == 1`
could never hold). Leftover run directories corroborate the timeline: the
one labelled `pre_semantinc_equiv` holds 1788 fix files, while every
dated run after semantic equivalence became the default (2026-03-10,
2026-05-26, 2026-07-27) holds none.

Fixed by overriding the inherited read methods to consult `_specs` in
semantic mode, and defining `get_specs()` in terms of `get_all_values()`
so they cannot diverge again. Syntactic mode now returns
`_value_to_id.keys()` rather than `list(self._set)`, so results keep
insertion order instead of varying with set iteration order.

## Part 6: three merge implementations collapsed into one

`scripts/merge_two_specs.py`, `scripts/merge_all_specs.py` and
`RepairBro.merge_two_solutions` were the same procedure, and had drifted:
both two-spec versions *asserted* that the original implies each repair,
while the all-specs version had that check **commented out** — identical
inputs, different verdict depending on which you ran.

The binary case is just the n-ary case with two elements, so there is now
one `merge_solutions` in `spec_repair/diagnosis/solution_merging.py`.
That location matters beyond tidiness: `setup.cfg` packages only
`spec_repair`, so logic parked in `scripts/` or `main/` is not installed
and cannot be imported or tested from a wheel — which is precisely how
one procedure became three copies.

The drifted check is reconciled explicitly rather than by picking a side:
a warning by default, fatal under `strict=True`. `RepairBro` passes
`strict=True` to keep its old behaviour; the CLI defaults to warning.
`og_spec` is optional throughout and is now a named `--og-spec` flag —
previously it was a leading positional with `nargs="?"` ahead of required
positionals, so what a bare path meant depended on how many arguments
followed.

Fifteen new tests cover merging semantically distinct specifications. Two
caught wrong assumptions while being written: **merge conjoins, so
`merged => input`**, not the reverse, and every fixture in `specs.py` is
already a weakening of `spec_strong`, so the non-weakening case had to be
built the other way round.

## Part 7: the experiment pipeline

Wired the six methodology steps together; full detail in
[docs/experiment-pipeline.md](../experiment-pipeline.md).

| Step | Command | Output |
|---|---|---|
| 1 | `scripts/pull_experiment_from_ssh.sh <date> [host]` | `tests/test_files/out_ssh/<date>/<cs>_<date>/` |
| 2–4, 6 | `scripts/run_experiment_pipeline.py <date>` | `merged_specs/`, `max_merged_specs/`, `unique_max_merged_specs/`, `implication_graph.png` |
| 5 | `pytest tests/test_diagnosis/test_trivial_solution.py -k get_all_trivial_solution_<cs>` | `out/trivial_solutions/<date>/all/<cs>/` |

Step 3 filters on guarantees alone because every merged specification
shares the same assumptions, so an assumption comparison cannot eliminate
anything. Trivial-solution tests are generated from a list covering all
18 case studies and are date-stamped; "all" solutions get a folder per
case study so they feed the graph directly. The graph takes repeatable
`--group LABEL=PATH` arguments — cataloguing by folder works because each
stage already writes to its own directory, so the directory *is* the
type. Specs that turn out equivalent merge into one grey, heavy-bordered
node listing every group it came from.

Bugs fixed en route: `remove_transitive_relations` hardcoded
`root_node='0'` (so any named node set crashed, and the single-root walk
silently skipped disconnected components); both filter scripts only ever
*printed* their results and now take `-o/--output-dir`; and
`get_files_with_specs_from_directory` did not sort, so `spec_0` meant a
different specification between runs.

**Two traps worth remembering.** A whole GR(1) spec is formatted as
`(assumptions) -> (guarantees)`, so strengthening assumptions *weakens*
the formula and `strong.spectra` sits at the **bottom** of a default
`--graph-type gr1` graph. And merging conjoins assumptions, so merging
several assumption-weakenings re-strengthens the assumption set toward
the original — on pcar the merged result came out assumption-equivalent
to `strong.spectra`.

## Part 8: correcting a documented "pre-existing failure"

Last session's notes recorded 3 pre-existing failures in
`test_util/test_spec.py::test_all_unrealisable_cores_raw_*`. The cause is
now known: those tests pass a **relative** path straight to the JVM,
whose working directory is fixed when it starts. `BaseTestCase.setUpClass`
calls `os.chdir` into `tests/`, but that moves Python's cwd, not the
JVM's. They pass when pytest is launched from `tests/` and fail from the
project root. Not a code bug — an invocation constraint.

Related: `test_bfs_repair_orchestrator.py` must be *collected* from the
project root (`main/bfs_repair_orchestrator.py` opens
`./main/spec_repair.log` in a class body) and `BaseTestCase` then chdirs
into `tests/` itself. `run_parallel_bfs_repair_syn.sh` already does this
correctly. An earlier claim in this session that this was a repo bug was
wrong.

## Final state

Three branches, none pushed — no SSH key in the assistant's environment,
so `git push` fails with `Permission denied (publickey)`.

**`main`** (`a4a3172`):
- `80f3640` — `*_updated` case studies + exploreAllCores short-circuit
- `0a2c942` — merge of `prev-consequent-support`
- `a970ce9` — single `merge_specs` CLI over one shared implementation
- `6912fc8` — experiment pipeline
- `a4a3172` — merge of `merge-specs`

**`fast`** (2 commits ahead of `main`, unmerged):
- `f3b296c` — `BFSRepairOrchestratorBuilder`
- `fe5f3f3` — semantic-mode `UniqueSpecRecorder` fix

**`merge-specs`** — merged into `main`, safe to delete.

Verification: 54 diagnosis tests pass on `main`; 38 pass under
`tests/test_builders/` on `fast`; the pipeline runs end to end on
replayed local BFS output for elevator (16 final specs), pcar (19) and
traffic_single (3).

## Open items for next session

1. **`git push`** — `main` and `fast` are local only.
2. **`fast` is unmerged.** The `UniqueSpecRecorder` fix in particular
   affects degradation results, which have been silently empty for
   months.
3. **ColorSort's BDD counter-strategy ceiling** — the cores blocker is
   fixed, but ColorSort still produces no repairs and its
   `get_all_trivial_solution` runs past 8 minutes. Every other case study
   completes. Carried forward from item 1 of 2026-07-24, now diagnosed.
4. **arbiter/minepump/gyro true runtime is still unknown** — unchanged
   from 2026-07-24 item 2. Still needs one isolated, freshly-cleared,
   single-invocation run each; `out_test_dir_name` is still scoped only
   by case-study name + date, so same-day reruns silently collide.
5. **`pull_experiment_from_ssh.sh` — partially confirmed against the real
   remote.** A first real run reached `pulling arbiter_2026-07-27`, so
   the SSH connection, the `*_<date>` glob and the assumed remote layout
   are all correct. It then died on `rsync --info=stats1`: macOS ships
   openrsync, which reports itself as "rsync version 2.6.9 compatible"
   and rejects rsync 3.x's `--info=`. Fixed by probing for a supported
   summary flag (`--info=stats1`, else `--stats`, else neither) instead
   of assuming one, and a failed case study is now warned about and
   skipped rather than aborting the whole pull. Still unconfirmed: that a
   full multi-case-study transfer completes.
6. **Degradation tests are slow (>10 min) and unconfirmed end to end** —
   verified pre-existing by timing them on unrefactored code. Worth one
   run on the GPU box to confirm they now emit fix files.
7. **`tests/test_main/test_solution_merger.py` is broken independently**
   — it reads `maximal_solutions_from_ssh/arbiter_0.spectra`, but those
   fixtures were moved into that directory's `old/` subfolder. Left alone
   rather than guessed at, since `old/` and `2026-06-12/` hold different
   specs.
8. **`scripts/` organisation** — 33 Python files, only 12 with
   `argparse`. Proposed but not done: move the non-CLI ones to
   `scripts/exploratory/` and add `console_scripts` entry points now that
   library logic lives in `spec_repair`.
