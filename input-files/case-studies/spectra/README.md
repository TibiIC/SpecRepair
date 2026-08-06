# Case studies

Two experimental setups, kept in separate folders because they construct the
repair scenario in fundamentally different ways.

## `strengthened/` — the original setup

Each case study holds:

| File | Role |
|---|---|
| `original.spectra` | a correct specification |
| `strong.spectra` | that specification, **artificially strengthened** |
| `violation_trace.txt` | a trace satisfying `ideal` but violating `strong` |

Repair starts from `strong.spectra` and weakens it back down. The scenario is
synthetic: the thing being repaired was manufactured by
`spec_repair.diagnosis.spec_mutation` strengthening a known-good specification,
so the "correct" answer is known in advance.

The `*_updated` variants are the same setup with a `strong.spectra` that
strengthens at least one assumption **and** at least one guarantee, since every
other `strong.spectra` happens to be assumption-only.

## `trace_violation/` — the current setup

Each case study holds:

| File | Role |
|---|---|
| `original.spectra` | the specification under test — content-identical to the old `original.spectra` |
| `violation_trace_<ID>.txt` | a short execution violating one or more of its **assumptions** |

There is no `original.spectra` and no artificial strengthening step. `original.spectra`
now plays the role `strong.spectra` used to: it is the thing to be repaired.
Repair has to weaken a real specification to accommodate a real trace, which
removes the synthetic strengthening the previous setup depended on.

`*_updated` case studies have no counterpart here — they existed only to add
guarantee strengthening to the mutation step, which no longer happens.

### Running and post-processing

```bash
# repair every case study against every one of its traces, on the GPU box
./scripts/run_parallel_bfs_repair_trace.sh

# pull the results back
REMOTE_SUBDIR=repair_trace_syn ./scripts/pull_experiment_from_ssh.sh 2026-07-30

# steps 2-6: merge, maximal, semantically unique, graphs
./scripts/run_trace_experiment_pipeline.sh 2026-07-30
```

Each case study is repaired once per trace, so a run directory is named
`<case_study>_trace<ID>_<date>`. The pipeline strips the `_trace<ID>` when
looking up `original.spectra` for the graph.

### Generating traces

```bash
# report which assumptions can be violated, and at what trace lengths
python scripts/generate_violation_traces.py \
    input-files/case-studies/spectra/trace_violation --all --report-only

# generate two traces per case study, reproducibly
python scripts/generate_violation_traces.py \
    input-files/case-studies/spectra/trace_violation --all -n 2 --seed 0 --clean

# only target invariant (G) assumptions, skipping `ini` and `GF` ones
python scripts/generate_violation_traces.py \
    input-files/case-studies/spectra/trace_violation/minepump \
    --invariant-only -n 5 --max-timepoints 5 --seed 0 --clean
```

`--invariant-only` restricts which assumptions a trace may violate to the `G`
ones. An `ini` violation only says the run started in a state the specification
excludes, which exercises no temporal behaviour and is rarely the scenario
wanted; `GF` cannot be violated on a finite prefix at all. Use
`--only-assumptions NAME ...` to pick specific ones. Neither relaxes anything:
every formula outside the targeted set must still hold.

Traces are found with ASP (`spec_repair.diagnosis.violation_trace_generation`),
reusing the same encoding the repair pipeline uses: the specification's formulas
become rules deriving `violation_holds`, a choice rule guesses the trace, and
two constraints force exactly the chosen assumptions to fail while every other
assumption and every guarantee still holds.

### Why some assumptions cannot be violated

`--report-only` will show assumptions as *not violable in range*. Three distinct
causes, all real rather than tool limitations:

1. **Tautologies.** minepump's `assumption2_1` *was*
   `G(!highwater -> (!highwater | !methane))`, equivalent to `true`, so no trace
   of any length violated it. It has since been strengthened to
   `G(!highwater | !methane)` — making `original.spectra` identical to the old
   `strengthened/minepump/strong.spectra`, which is how this case study is
   studied — and is now violable from 2 timepoints. The pattern is still worth
   watching for elsewhere.
2. **Not enough timepoints.** A trace is a finite prefix ending in a *weak
   timepoint*, where every atom both holds and does not, so a `next` evaluated
   at the last real timepoint is satisfied vacuously. A violation involving
   `next` must therefore happen at least one timepoint before the end —
   minepump's `G((PREV(pump) & pump) -> next(!highwater))` needs 4 timepoints.
   Raise `--max-timepoints`.
3. **Liveness.** `GF(...)` is always satisfiable on a finite prefix for the same
   reason. **arbiter** has exactly one assumption, `GF(a)`, so it has no
   generatable trace at any length and is currently unusable in this setup.
