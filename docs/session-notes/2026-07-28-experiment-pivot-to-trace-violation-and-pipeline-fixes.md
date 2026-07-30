# Pivoting the experiments to trace violation, and unblocking the pipeline — session notes

Session date: 2026-07-28. Started by fixing the experiment pipeline against real
pulled data, and ended up rebuilding what a case study *is*: a supervisor's
pivot replaced the artificial-strengthening setup with one where the original
specification is the thing to be repaired and traces are generated to violate
it.

Continues [2026-07-27](2026-07-27-updated-case-studies-orchestrator-builder-and-experiment-pipeline.md).

## Part 1: the pull script assumed rsync 3.x

The first real run against `gpu11` reached `pulling arbiter_2026-07-27` — which
confirmed the SSH connection, the `*_<date>` glob and the assumed remote layout
were all correct — then died on `rsync: unrecognized option --info=stats1`.
macOS ships **openrsync**, which reports itself as "rsync version 2.6.9
compatible" and only has the older `--stats`. My mistake: I used a flag without
checking what the local rsync accepts.

Fixed by probing for a supported summary flag rather than picking one, so the
same script works on the Mac and on the Linux GPU box. Only `-a` and `-z` are
assumed. Also stopped one failed transfer from aborting the whole pull under
`set -e`, which would discard every case study still queued behind it.

## Part 2: three graphs, not one

The `gr1` implication graph put the trivial solutions at the top and
`strong.spectra` at the bottom — the opposite of intuition. A whole GR(1)
specification is formatted as `(assumptions) -> (guarantees)`, so *strengthening
the assumptions weakens that implication*. With guarantees untouched, `gr1`
orders specifications purely by the assumption side, inverted.

`run_experiment_pipeline.py` now draws all three every run —
`implication_graph_{asm,gar,gr1}.png` — because no single comparison tells the
whole story and reading the wrong one is actively misleading. traffic_single
shows both halves: in `asm`, `strong` is at the top with `ideal`/`trivial`
below; in `gar`, `ideal`, `strong` and the merged result collapse into a single
equivalent node with only `trivial` beneath, i.e. no guarantee degradation
occurred at all, which is exactly why `gr1` had nothing but assumptions to
order by.

## Part 3: bubbles instead of a grey node

Equivalent specifications were merged into one grey box listing its groups in
text, which threw away the information the colour coding exists to convey. Such
a node is now a rounded **bubble** holding one coloured box per specification,
each keeping its group's colour — built with a Graphviz HTML-like table label.
An orange `strong` beside a blue `unique_max_merged_0` in one bubble says at a
glance that the merged repair is equivalent to the original.

The key's bubble example is only added when the graph actually contains one, and
group labels are HTML-escaped since they come from user-supplied `--group`
arguments and now land inside markup.

## Part 4: the experiment pivot

The old setup manufactured what it repaired: strengthen a known-good
`ideal.spectra` into a `strong.spectra`, find a trace satisfying ideal but
violating strong, repair back down. The new one takes the specification as it is
and finds short environment behaviours it does not admit, so repair has to weaken
a real specification to accommodate a real trace.

`input-files/case-studies/spectra` is now split by approach:

| Folder | Files | Repair target |
|---|---|---|
| `strengthened/` | `ideal.spectra`, `strong.spectra`, `violation_trace.txt` | `strong.spectra` |
| `trace_violation/` | `original.spectra`, `violation_trace_<ID>.txt` | `original.spectra` |

`original.spectra` is content-identical to the former `ideal.spectra`. The
`*_updated` case studies get no counterpart: they existed only to make the
mutation step strengthen guarantees as well as assumptions, and there is no
mutation step any more. They stay in `strengthened/` rather than being deleted,
since they remain valid case studies for that approach.

All 115 references to the old path were rewritten. One escaped the sweep and is
worth remembering: `run_experiment_pipeline.py`'s `CASE_STUDIES_DIR` is built
with `os.path.join`, not a slash-joined string, so a `sed` on
`case-studies/spectra/` did not match it. Step 6 would have silently drawn
graphs with no `strong`/`ideal` group.

## Part 5: generating violating traces

**SYNTECH's Rich Controller Walker is not usable here.** None of the three
Spectra jars in `~/Tools` contain any walker classes — they ship the CLI and
`games/controller` sources only; the walker is Eclipse-plugin-only. So ASP, as
expected.

`spec_repair/diagnosis/violation_trace_generation.py` reuses the encoding the
repair pipeline already has: `spec.to_asp(for_clingo=True)` derives
`violation_holds`, `background_knowledge.txt` supplies GR(1) semantics, a choice
rule *guesses* the trace instead of reading it from a file, and two integrity
constraints force exactly the chosen assumptions to fail while every other
assumption and every guarantee holds.

Traces cover **distinct groups** of assumptions, smallest first and shuffled
within each size, so five traces witness five different violations rather than
one violation five ways. A group can be unsatisfiable as a whole even when each
of its assumptions is violable alone.

### Why some assumptions cannot be violated

`--report-only` shows assumptions as *not violable in range*, for three genuinely
different reasons — none of them tool limitations:

1. **Tautologies.** minepump's `assumption2_1` is
   `G(!highwater -> (!highwater | !methane))`, which spot confirms is equivalent
   to `true`. Unviolable at any length. Presumably trivialised by an earlier
   repair.
2. **Trace too short.** A trace is a finite prefix ending in a *weak timepoint*
   where every atom both holds and does not, so a `next` evaluated at the last
   real timepoint is satisfied vacuously. A violation involving `next` must occur
   at least one timepoint before the end — minepump's
   `G((PREV(pump) & pump) -> next(!highwater))` needs 4 timepoints, so the 1-3
   default silently excluded it until this was surfaced.
3. **Liveness.** `GF(...)` is always vacuously satisfiable on a finite prefix.
   **arbiter has exactly one assumption, `GF(a)`**, so it produces no trace at
   any length and is currently unusable in this setup.

Generated 5 traces for each of the 10 usable case studies. All 50 were verified
independently — fed back through the pipeline's own `get_violations` rather than
trusting the generator's constraints — and each violates exactly the assumptions
it claims, with no guarantee violated. Distinct groups achieved: colorsort, lift,
pcar, traffic_updated 5 each; gyro, minepump_liveness, traffic_single 3 each;
elevator, humanoid, minepump 1 each, having only one violable assumption.

## Part 6: the pipeline was not hung, it was intractable

`elevator_updated` appeared to halt after a couple of Spectra
garbage-collection blocks. The GC output was a red herring — stdout buffering
meant it was simply the last thing flushed. Measured:

| Phase | Time |
|---|---|
| load 966 final specs | 4s |
| verify each input is realisable | **648s** (966 Spectra synthesis calls) |
| merge pairwise | 34s → 134 formulas |
| check merge is realisable | 1s → **False** |
| break it back down | **>10 min, no return** |

Two problems. The verification loop re-established something already known —
these specs come from the BFS repair search, which only records a spec once its
oracle has accepted it — so `merge_solutions` gained `verify_inputs` (default
`True`; the pipeline passes `False`). Turning it off degrades gracefully:
merging is monotone, so an unrealisable input still makes the merge
unrealisable, which the post-merge check catches.

The real wall is the fallback. Breaking down an over-constrained merge starts
from Spectra's exhaustive all-unrealisable-cores search — the same cost centre
that makes ColorSort intractable. Fine on the 10-25 formula merges the small
case studies produce; on 134 formulas it does not return, and being a blocking
JVM call it cannot be interrupted from Python. `merge_solutions` now raises
`MergeTooLargeError` with the real numbers instead of hanging;
`--max-merge-formulas` (default 50, 0 disables) overrides. elevator_updated now
fails in **42 seconds** with an explanation.

Deduplicating inputs before merging was tried and rejected on measurement:
semantic dedup of 966 specs is itself an O(n²) spot comparison that also exceeds
10 minutes.

## Part 7: a FastLAS learner (branch `fastlas-learner`)

Groundwork for tackling the case studies ILASP cannot: a learner backed by
FastLAS instead. Confined to one component, as intended — `FastLASSpecLearner`
subclasses `OptimisingSpecLearner` and overrides exactly one method,
`find_adaptations_with_heuristic`, the seam where the task goes to the solver
and the answer comes back. Orchestrator, oracle, mitigator, discriminator and
encoder are untouched and unaware which solver is in use. Selected with
`BFSRepairOrchestratorBuilder.<preset>().using_fastlas(n_runs=N)`, which
composes with every preset; the builder gained a learner factory so swapping
solver is one override rather than a preset per (strategy × solver) pair.

### Translating the task

FastLAS 2.1.0 rejects the ILASP dialect the encoder emits. Three rewrites, each
for something it refuses outright:

| ILASP | FastLAS | Why |
|---|---|---|
| `#modeb(2, p(...), (positive)).` | `#modeb(p(...)).` | `syntax error, unexpected T_COMMA` |
| `#constant(t, v).` | `t(v).` | no `#constant` directive — `Unknown token: '#'`; it reads `const(t)` values from a `t/1` predicate |
| `#pos({...},{...},{...}).` | `#pos(eg1,{...},{...},{...}).` | examples need an identifier |

Output parsing differs too — ILASP prints `%% Solution N (score M)` blocks,
FastLAS prints bare rules — but individual rules share a syntax, so
`Adaptation.from_str` is reused unchanged.

### Two findings, both measured rather than assumed

**FastLAS 2.1.0 is deterministic.** The premise for this work was that FastLAS
returns *one solution, randomly*, so running it repeatedly would sample
different ones. It does not: identical output across six consecutive runs, with
`--threads 4`, and with the mode declarations and constant facts shuffled under
five different seeds. Excluding a found solution via `#bias` and enumerating via
`--output-solve-program` were both tried; the former has no effect (see below)
and the latter only exposes `in_h(N)` indices with no mapping back to rule text.

`n_runs` is implemented as specified — repeated invocation, distinct solutions
collected and deduplicated — so a build that *does* randomise needs no further
change. But with 2.1.0 it returns one solution and extra runs only cost time, so
the default is 1. A test pins the determinism, so if FastLAS ever gains
randomisation that test fails and says so.

**FastLAS ignores the `#bias` block.** Its `#bias` is a scoring hook, not a
constraint: adding `:- body(k(_)).` to a task that had chosen `k` left the
answer unchanged. ILASP uses that block for *hard* constraints on rule shape —
matching the head's time/trace variables to the body's `timepoint_of_op`,
forbidding contradictory `holds_at`/`not_holds_at` pairs, and so on. **FastLAS
is therefore solving a less constrained problem on the same task** and can in
principle return a rule ILASP's bias would have excluded. Its preference for the
shortest hypothesis makes that unlikely in practice — the shortest candidates
are body-free facts that satisfy those constraints vacuously — but it is a real
difference, not an equivalence, and matters before trusting FastLAS results.

### Other notes

`run_fastlas` captures stderr rather than discarding it. FastLAS reports a
malformed task on stderr and writes *nothing* to stdout, so ignoring it would
make a translation bug indistinguishable from "this branch found no
adaptations" — the search would quietly explore nothing and report no repair.

29 tests: 21 unit in `tests/test_components/test_fastlas_spec_learner.py` with
the binary mocked, 8 integration in `tests/test_main/test_fastlas_integration.py`
that invoke it for real against minepump, traffic_single and lift, skipped when
FastLAS is not installed. Writing them caught three of my own bugs: a greedy
`\s*$` under `re.MULTILINE` that silently joined consecutive `#constant` lines,
an inconsistent None-vs-empty contract in the interpreter, and the discarded
stderr above.

## Final state

`main` is pushed (`02e65e5`), and now includes the previously-unmerged `fast`
branch — the `BFSRepairOrchestratorBuilder` and the semantic-mode
`UniqueSpecRecorder` fix that had been silently discarding degradation results.
Parts 1-6 are all on `main`:

| Commit | |
|---|---|
| `4356374` | pull script: probe for a supported rsync flag, survive one bad transfer |
| `2abcf2e` | draw all three implication graphs |
| `f4d5c1a` | coloured bubbles replace the grey equivalence node |
| `df58ddb` | trace-violation case studies and the ASP generator |
| `e4761f2` | merge guard, so a large merge reports instead of hanging |
| `b23c8bb` | five traces per case study, covering distinct assumption groups |
| `404e88b` | merge of `fast` |
| `02e65e5` | these notes |

Part 7 is on **`fastlas-learner`** (`bd73a4f`), pushed but not merged — the
FastLAS learner is groundwork rather than something the current experiments
depend on, and its two caveats above are worth reviewing before it lands.

Cleanup worth recording: three `out_ssh` case studies carried stale
`merged_specs`/`max_merged_specs`/`unique_max_merged_specs` from my own
end-to-end verification the previous day, which I had run in the *real* output
location rather than a scratch directory. The real pull then landed on top —
rsync without `--delete` merges — leaving derived output computed from different
inputs than the `final_specs` beside it. Removed.

## Open items for next session

1. **FastLAS gives one solution, not many** — the `n_runs` mechanism is built
   and tested, but 2.1.0 is deterministic so it currently yields one branch per
   learning step where ILASP yields several. A narrower repair search is the
   trade for FastLAS's speed; whether that is acceptable is a research call.
   Getting genuine alternatives would need either a FastLAS build with a seed,
   or reconstructing the rule-index mapping behind `--output-solve-program`.
2. **FastLAS ignores ILASP's `#bias` constraints**, so it solves a less
   constrained problem on the same task. Worth confirming on a complex case
   study that the rules it returns are ones ILASP would also have allowed,
   before trusting the results.
3. **arbiter is unusable in the new setup** — its only assumption is `GF(a)`.
   Needs either a non-liveness assumption or a bounded-liveness semantics
   ("no witness within N steps"), which is a different encoding.
4. **ColorSort remains intractable everywhere** — no BFS repair specs,
   `get_all_trivial_solution` past 8 minutes, and now the merge fallback too.
   All the same all-unrealisable-cores cost centre.
5. **Merging all repairs may not be the right operation at scale.** 966
   elevator_updated repairs merge into a 134-formula unrealisable spec that then
   has to be torn back down. Reducing to maximal/unique *before* merging would
   avoid that, but reorders the methodology, so it is the supervisor's call.
6. **`tests/test_main/test_solution_merger.py` is still broken** — it reads
   `maximal_solutions_from_ssh/arbiter_0.spectra`, but those fixtures moved into
   that directory's `old/` subfolder. Left alone since `old/` and `2026-06-12/`
   hold different specs.
7. **`scripts/` organisation** — 33 Python files, only 12 with `argparse`.
   Proposed but not done: move the rest to `scripts/exploratory/` and add
   `console_scripts` entry points.

## PERSONAL NOTES
* number 3 above is important to fix. a max limit of merges is not the right way to do it.
* 3 steps should be enough to violate minepump's second assumption. double-check!
