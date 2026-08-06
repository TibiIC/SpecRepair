# Experiment pipeline

End-to-end methodology for one experiment date: pull a parallel BFS repair run
off the remote, merge and filter its solutions, and draw the resulting
implication graph.

Everything derived from a remote run stays inside that run's folder under
`tests/test_files/out_ssh/<date>/`; everything generated locally (trivial
solutions) stays under `tests/test_files/out/trivial_solutions/<date>/`. Both
are gitignored.

## Step 0 — produce the run on the remote

```bash
./scripts/run_parallel_bfs_repair_syn.sh            # all 17 syn tests
./scripts/run_parallel_bfs_repair_syn.sh updated    # only the *_updated ones
```

Writes `tests/test_files/out/repair_syn/<case_study>_<date>/` per case study.

## Step 1 — pull a date's run

```bash
./scripts/pull_experiment_from_ssh.sh 2026-07-27 [remote_host]
```

Pulls every `*_<date>` run directory into
`tests/test_files/out_ssh/<date>/<case_study>_<date>/`, mirroring the remote
folder names so provenance stays obvious. `REMOTE_BASE`, `REMOTE_SUBDIR`,
`REMOTE_HOST` and `LOCAL_DEST` are environment-overridable.

## Step 5 — trivial solutions (local, no remote needed)

Independent of the remote, so it can run at any point before the graph:

```bash
python -m pytest tests/test_diagnosis/test_trivial_solution.py -k get_all_trivial_solution_pcar
```

Writes `tests/test_files/out/trivial_solutions/<date>/all/<case_study>/spec_<i>.spectra`
(and `.../single/<case_study>.spectra` for the single-solution variant). One
folder per case study specifically so it can be handed to the graph as a group.

Tests are generated from `TRIVIAL_SOLUTION_CASE_STUDIES` in that file — adding a
case study is a one-line change, and each still runs individually by name.

## Steps 2, 3, 4, 6 — merge, filter, draw

```bash
python scripts/run_experiment_pipeline.py 2026-07-27
python scripts/run_experiment_pipeline.py 2026-07-27 --case-study pcar
python scripts/run_experiment_pipeline.py 2026-07-27 --graph-type gar

# the trace-violation case studies
python scripts/run_experiment_pipeline.py 2026-07-30 --setup trace_violation
./scripts/run_trace_experiment_pipeline.sh 2026-07-30   # same thing, batch driver
```

Per case study, inside `out_ssh/<date>/<case_study>_<date>/`:

| Step | Output | What it does |
|---|---|---|
| 2 | `merged_specs/` | merges every spec in `final_specs/` (`spec_repair.diagnosis.solution_merging`) |
| 3 | `max_merged_specs/` | keeps only those maximal by **guarantee** (GAR) |
| 4 | `unique_max_merged_specs/` | keeps only the semantically unique ones |
| 6 | `implication_graph_{asm,gar,gr1}.png` | colour-coded graphs of the reference specs / trivial / unique max merged |

`--setup` selects which reference specifications step 6 draws: `strong` and
`ideal` for the strengthened case studies, `original` for the trace-violation
ones, which have no manufactured spec and no known-good answer. Steps 2-4 are
identical either way. Trace-violation runs are named
`<case_study>_trace<ID>_<date>`, since each case study is repaired once per
violating trace; the `_trace<ID>` is stripped when looking up the case study.

### Merging: divide and conquer

Step 2 merges everything and checks the result is realisable. If it is not, the
set over-constrains the system, so it is **split in half and each half merged
separately**, recursively. Every returned specification is realisable.

This replaced a "merge everything, then break the wreckage back down with
Spectra's exhaustive unrealisable-core search" approach, which on a large run
did not return at all — and being a blocking JVM call, could not be interrupted
from Python. A `--max-merge-formulas` cap used to guard it, but capping only
converted a hang into a refusal; neither produces a result. The flag is gone and
`max_formulas_for_trivial_fallback` is accepted-and-ignored.

Cost is proportional to how fragmented the answer actually is, not to the number
of inputs:

| Case study | Inputs | Merged | Realisability checks | Time |
|---|---|---|---|---|
| pcar | 19 | 1 | 1 | <1s |
| lift | 21 | 1 | 1 | 1s |
| elevator_updated | 966 | 373 | 745 | 173s |

The core search is only ever reached for a *single* specification that is
unrealisable on its own — a repair-sized spec, which it handles in well under a
second — never for a large merge.

Step 3 filters on GAR alone because every merged specification shares the same
assumptions — they all derive from one original and merging conjoins — so an
assumption comparison cannot eliminate anything and only costs spot equivalence
checks.

The individual filters are also usable standalone, and now save as well as
print:

```bash
cd scripts
python find_maximal_specifications.py <dir> -t gar -o <out_dir>
python find_semantically_unique_specifications.py <dir> -o <out_dir>
```

## Choosing the learner

Both tmux runners take `LEARNER` (default `ilasp`):

```bash
LEARNER=fastlas ./scripts/run_parallel_bfs_repair_syn.sh
LEARNER=fastlas ./scripts/run_parallel_bfs_repair_trace.sh
```

The runner exports `SPEC_REPAIR_LEARNER`, which the test classes read once in
`setUpClass` and pass to `BFSRepairOrchestratorBuilder.using_learner()`. Nothing
else in the search changes — that is the point of the component.

A non-default learner adds a suffix to the run directory
(`minepump_fastlas_<date>`, `minepump_trace0_fastlas_<date>`), so a FastLAS run
lands *beside* an ILASP run of the same date rather than overwriting it, and the
two are directly comparable. ILASP keeps the unsuffixed name every existing
path was written against. `case_study_dir_name` strips both the `_trace<ID>` and
the `_<learner>` suffix when looking up the case study's own files.

An unknown name fails immediately with the valid ones, rather than silently
running the default solver and labelling the results as the other one.

To run the case studies locally instead of on the box, and record timings:

```bash
python scripts/run_learner_comparison.py --learner fastlas ilasp \
    --setup strengthened trace_violation --timeout 300 -o results.json
```

One subprocess per case study, so a run that does not terminate is killed
without taking the sweep with it — which is necessary, because some (learner,
case study) pairs do not finish. Post-process those local runs with
`--runs-root`:

```bash
python scripts/run_experiment_pipeline.py <date> --setup trace_violation \
    --runs-root tests/test_files/out/repair_trace_syn
```

## Reading the graph

`--group LABEL=PATH` gives each specification type its own colour; PATH is a
file or a directory, so each pipeline stage's folder *is* its type. Nodes are
named `LABEL` (single file) or `LABEL_<i>` (directory).

Specifications that turn out equivalent are merged into one node, drawn as a
rounded **bubble** holding one coloured box per specification inside it, each
keeping its own group's colour. So a bubble containing an orange `strong` next
to a blue `unique_max_merged_0` says at a glance that the merged repair is
equivalent to the original — usually the interesting finding — without
flattening either into a colour that belongs to neither.

**Edge direction:** `A -> B` means A implies B, i.e. A is the stronger
specification.

**The legend** is a small swatch table pinned to the bottom-right corner.
`--legend full` restores the older legend cluster, which `dot` lays out
alongside the graph and which competed with the real nodes for space;
`--legend none` omits it.

### Three graphs, and which to read

All three are drawn every run, because no single one tells the whole story:

| File | Compares | Read it for |
|---|---|---|
| `implication_graph_asm.png` | assumptions only | how far each repair weakened the assumptions |
| `implication_graph_gar.png` | guarantees only | whether any guarantee degradation happened at all |
| `implication_graph_gr1.png` | whole spec, as `(asm) -> (gar)` | the combined picture — **easy to misread, see below** |

Restrict with e.g. `--graph-type gar`, or `--graph-type asm gar`.

**The gr1 graph inverts when guarantees are untouched.** A whole GR(1)
specification is formatted as `(assumptions) -> (guarantees)`, so *strengthening
the assumptions weakens that implication*. When a repair run weakens assumptions
and leaves guarantees alone — the common case — gr1 orders the specifications
purely by the assumption side, and in the opposite direction to intuition:
`strong.spectra` sinks to the **bottom** and the trivial solutions rise to the
**top**.

traffic_single on 2026-07-27 shows this clearly. In `asm`, `strong` is at the
top and `ideal`/`trivial` at the bottom, as expected. In `gar`, `ideal`, `strong`
and the merged result collapse into a single equivalent node with only `trivial`
below them — i.e. no guarantee degradation occurred, which is exactly why the
`gr1` view had nothing but assumptions to order by.

Rule of thumb: **read `asm` and `gar` first**, and treat `gr1` as a summary that
only means what you expect when both sides actually moved.

## Known limitations

- **colorsort** is impractical throughout: its BFS repair produces no specs
  (blocked in BDD counter-strategy synthesis), and
  `get_all_trivial_solution` runs past 8 minutes. Every other case study
  completes.
- Merging conjoins assumptions, so merging several assumption-weakenings can
  re-strengthen the assumption set back toward the original. On pcar the merged
  result came out assumption-equivalent to `strong.spectra`. Expected from the
  operation, but worth keeping in mind when interpreting results.
