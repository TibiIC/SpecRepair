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

## Final state

`main` is pushed (`404e88b`), and now includes the previously-unmerged `fast`
branch — the `BFSRepairOrchestratorBuilder` and the semantic-mode
`UniqueSpecRecorder` fix that had been silently discarding degradation results.

Cleanup worth recording: three `out_ssh` case studies carried stale
`merged_specs`/`max_merged_specs`/`unique_max_merged_specs` from my own
end-to-end verification the previous day, which I had run in the *real* output
location rather than a scratch directory. The real pull then landed on top —
rsync without `--delete` merges — leaving derived output computed from different
inputs than the `final_specs` beside it. Removed.

## Open items for next session

1. **arbiter is unusable in the new setup** — its only assumption is `GF(a)`.
   Needs either a non-liveness assumption or a bounded-liveness semantics
   ("no witness within N steps"), which is a different encoding.
2. **ColorSort remains intractable everywhere** — no BFS repair specs,
   `get_all_trivial_solution` past 8 minutes, and now the merge fallback too.
   All the same all-unrealisable-cores cost centre.
3. **Merging all repairs may not be the right operation at scale.** 966
   elevator_updated repairs merge into a 134-formula unrealisable spec that then
   has to be torn back down. Reducing to maximal/unique *before* merging would
   avoid that, but reorders the methodology, so it is the supervisor's call.
4. **`tests/test_main/test_solution_merger.py` is still broken** — it reads
   `maximal_solutions_from_ssh/arbiter_0.spectra`, but those fixtures moved into
   that directory's `old/` subfolder. Left alone since `old/` and `2026-06-12/`
   hold different specs.
5. **`scripts/` organisation** — 33 Python files, only 12 with `argparse`.
   Proposed but not done: move the rest to `scripts/exploratory/` and add
   `console_scripts` entry points.
