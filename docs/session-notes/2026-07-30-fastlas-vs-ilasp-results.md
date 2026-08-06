# FastLAS vs ILASP on both case-study setups — experimental results

Date: 2026-07-30. A **results** record rather than a session log: what the two
learners actually produce on the case studies, and what follows for the
methodology. The engineering that made these runs possible — solver selection,
and the two crashes fixed along the way — is in
[2026-07-30-merge-splitting-legend-and-trace-violation-runner](2026-07-30-merge-splitting-legend-and-trace-violation-runner.md).

## Method

40 runs: 2 learners × 2 setups × 10 case studies, driven by
`scripts/run_learner_comparison.py`, which invokes the same unittest methods the
tmux runners drive with `SPEC_REPAIR_LEARNER` set.

| | |
|---|---|
| Machine | local (macOS), **not** the GPU box — timings are not comparable to pulled runs |
| Per-run limit | 300s wall clock, one subprocess per case study |
| Setups | `strengthened` (repair `strong.spectra` against `violation_trace.txt`), `trace_violation` (repair `original.spectra` against `violation_trace_0.txt`) |
| Preset | `BFSRepairOrchestratorBuilder.syntactic()`, `INCLUDE_NEXT`, `INCLUDE_PREV` |
| Code state | **after** both crash fixes; every number here comes from one consistent state |

arbiter has no trace-violation counterpart (its only assumption is `GF(a)`), and
`trace_violation` adds minepump_liveness, so each setup has ten case studies but
not the same ten.

Three caveats that bound every claim below:

1. **300s is a short budget.** A "timeout" here means "did not finish in 300s on
   a laptop", not "intractable". The pulled 2026-07-27 GPU runs found 1052 final
   specs for minepump where this budget reaches 59.
2. **Timeout rows carry partial counts.** The process is killed mid-search, so
   `final_specs` is whatever had been written by then, not a total.
3. **One trace only** (`violation_trace_0`) for the trace-violation setup. Each
   case study has five, each violating a different group of assumptions.

## Result 1: FastLAS returns exactly one repair, always

Across all 17 runs that produced anything, FastLAS's `final_specs` was **1**,
without exception — the only other value it ever took was 0. ILASP's ranged from
0 to 59.

This is the 2026-07-28 determinism finding showing up end to end. FastLAS 2.1.0
returns one solution per learning step, so each step has one successor, so the
BFS search is a single path rather than a tree. `n_runs > 1` does not help — the
solver is deterministic, so repeated invocation returns the same solution.

| Setup | ILASP final specs | FastLAS |
|---|---|---|
| strengthened | 0-59 (median 17.5) | 1 |
| trace_violation | 0-21 (median 8.5) | 1 |

## Result 2: the one repair is usually one of ILASP's

The obvious worry is that a single-solution learner finds a *different, worse*
repair. Measured by semantic equivalence against ILASP's set, on the same case
study and setup:

Of the **16** pairs where both learners produced at least one repair, FastLAS's
single solution was semantically equivalent to one of ILASP's in **15**. The sole
exception is a case where ILASP's set is incomplete:

| Exception | What actually happened |
|---|---|
| minepump, strengthened | ILASP timed out with 59 *partial* specs; FastLAS's is not among *those*. Inconclusive rather than a counter-example — the complete set is 1052 on the GPU box. |

**In every case where ILASP produced a complete solution set, FastLAS's single
solution was one of them.** Separately, colorsort under `trace_violation` is not
in the 16: ILASP produced nothing there at all, while FastLAS solved it in 6s.

So the narrower search is not, on this evidence, finding worse repairs. It is
finding *one of the right ones* and stopping.

## Result 3: against the known-good specification

The `strengthened` setup is the one with an answer key — `ideal.spectra` is the
specification `strong.spectra` was manufactured from. Comparing FastLAS's single
repair to it:

| Case study | Assumptions | Guarantees |
|---|---|---|
| arbiter, gyro, lift | **equivalent to ideal** | **equivalent to ideal** |
| elevator, humanoid, pcar, traffic_single, traffic_updated | incomparable | **equivalent to ideal** |
| minepump | stronger than ideal | incomparable |

All nine are genuine weakenings of `strong.spectra` on both sides — verified, not
assumed.

Three recover the ideal specification exactly. Five more recover the ideal
*guarantees* exactly and differ only in which assumption weakening they chose —
a different point on the assumption lattice, not a worse one. minepump is the
only case where FastLAS weakened a guarantee as well
(`G(methane -> next(!pump))` → `G(methane -> F(next(!pump)))`), landing somewhere
incomparable to ideal.

## Result 4: completion rate, not speed, is the difference

An earlier claim of mine that FastLAS is "dramatically faster" does not survive a
like-for-like comparison and is withdrawn. On the case studies both learners
complete, the times overlap:

| | completed | time range (completed runs) |
|---|---|---|
| FastLAS, strengthened | **9/10** | 4-31s |
| ILASP, strengthened | 6/10 | 9-14s |
| FastLAS, trace_violation | 8/10 | 4-6s |
| ILASP, trace_violation | 8/10 | 6-19s |

FastLAS is modestly faster per run and completes more often — 17/20 against
14/20 overall. But ILASP is doing strictly more work in that time: it returns
every optimal solution where FastLAS returns one. The right reading is not
"FastLAS is faster" but **"FastLAS answers a smaller question"**.

Two results cut against a simple ordering:

* **colorsort is tractable under `trace_violation` and not under
  `strengthened`.** FastLAS solves it in 6s in the new setup and times out in the
  old one; ILASP times out in both. The setup matters more than the solver here.
* **ILASP handles `trace_violation` better than `strengthened`** (8/10 vs 6/10),
  despite the traces being longer. arbiter, gyro and minepump all time out in the
  old setup and gyro and minepump complete in the new one.

## Result 5: FastLAS finds no repair at all for gyro and lift

On `trace_violation` trace 0, FastLAS returns **zero** repairs where ILASP
returns 2 (gyro) and 7 (lift). Both learners run to completion in under 20s;
this is not a timeout.

This is the sharpest available case against one-solution-per-step. The 2026-07-28
notes flagged that FastLAS ignores ILASP's `#bias` block, so it solves a *less
constrained* problem on the same task — the concern there was that it might
return a rule ILASP would have excluded. What these two show is the other
failure mode: committing to a single hypothesis early and finding no way forward,
where ILASP's branching finds several.

Until this session both cases crashed rather than reporting anything, one crash
per learner, so the result was invisible.

## Result 6: after post-processing, ILASP also yields one specification

I expected the merge step to be the place the two learners became incomparable —
many repairs against one. The measurement says otherwise. Running steps 2-4 over
every run:

| | ILASP final specs | after unique_max_merged | FastLAS |
|---|---|---|---|
| arbiter | 11 | **1** | 1 |
| elevator | 16 | **1** | 1 |
| gyro | 10 | **1** | 1 |
| humanoid, lift, traffic_updated | 21 | **1** | 1 |
| pcar | 19 | **1** | 1 |
| traffic_single | 3 | **1** | 1 |
| minepump | 59 | **10** | 1 |

**ILASP's solution space collapses to a single specification in 17 of 18 runs.**
minepump is the sole exception. So the pipeline's output cardinality is not what
distinguishes the learners — both nearly always end at one specification.

### But it is not the same specification

Comparing those outputs directly, they differ in 14 of 15 comparable cases. The
reason is mechanical, and worth stating precisely because it is easy to misread
as the learners disagreeing:

* FastLAS's single repair **is** one of ILASP's individual repairs (Result 2). It
  passes through the merge unchanged, because merging one thing is the identity.
* ILASP's output is the **merge** of all its repairs. Merging conjoins, so the
  result is not equal to any of its own inputs — verified: in every case above,
  ILASP's merged output is equivalent to none of the final specs it came from.

The relationship is consistent and one-directional:

> ILASP's merged output **implies** FastLAS's repair on assumptions in 14/16
> cases, and is **equivalent** on guarantees.

That is, ILASP's answer has the *stronger* assumption set — it is the less
weakened, less degraded repair. FastLAS's single repair is a strictly more
permissive weakening of the environment, with the same guarantees.

The one case where the two outputs agree exactly, traffic_single on
`trace_violation`, is the case that proves the mechanism: ILASP found only **one**
final spec there, so its merge was also the identity, and both learners land on
the same specification.

minepump is again the outlier — incomparable on both sides, and the only run
where ILASP's output does not reduce to one.

So the two are comparable at the pipeline's output, but the comparison is
**merged-many against unmerged-one**, and reporting them side by side without
saying so would suggest a disagreement between solvers that is really an artefact
of the merge.

## What this means for the methodology

1. **FastLAS is a viable solver for the cases ILASP cannot reach**, which was the
   premise for building it. colorsort under `trace_violation` is the concrete
   win: 6s against a timeout.
2. **The cost is not where I expected it.** The obvious worry — FastLAS returns
   one repair where ILASP returns twenty, so it must be losing information — is
   not what the measurement shows. ILASP's twenty collapse to *one* under the
   pipeline's own post-processing in 17 of 18 runs. What is lost is not the
   cardinality of the answer but its **position on the lattice**: ILASP's merged
   answer is the stronger, less-degraded weakening, and FastLAS's is a more
   permissive one with identical guarantees.
3. **This makes the merge step, not the learner, the thing to scrutinise.** If
   merging many repairs into one is what produces the less-degraded answer, then
   the value ILASP adds over FastLAS is concentrated entirely in that step — and
   the previous session's open question about whether merging all repairs is the
   right operation at scale becomes the more important one, not less.
4. **A hybrid remains the obvious shape**: FastLAS to establish cheaply that a
   repair exists and what one looks like, ILASP where the merged solution space
   is the object of study. Nothing prevents it — the learner is one component,
   selected per run.
5. **gyro and lift need explaining before FastLAS is trusted**, since "no repair
   found" is indistinguishable from "no repair exists" to a caller. The `#bias`
   gap is the first thing to check.

## Reproducing

```bash
python scripts/run_learner_comparison.py --learner fastlas ilasp \
    --setup strengthened trace_violation --timeout 300 -o results.json

python scripts/run_experiment_pipeline.py 2026-07-30 --setup strengthened \
    --runs-root tests/test_files/out/repair_syn
```

On the GPU box, with a real budget and all five traces:

```bash
LEARNER=fastlas ./scripts/run_parallel_bfs_repair_trace.sh
LEARNER=ilasp   ./scripts/run_parallel_bfs_repair_trace.sh
```

Both write to distinct directories (`_fastlas` suffix), so the two sweeps can run
concurrently and be compared afterwards.

## Open questions

1. **Why do gyro and lift yield nothing under FastLAS?** Result 5. Check whether
   the missing `#bias` constraints let it commit to a hypothesis ILASP would have
   excluded.
2. **Does the "one of ILASP's" property hold at a real budget?** Result 2 rests
   on 300s locally. minepump is the one case study where ILASP's complete set is
   known (1052 specs, GPU box) and it was not checked against that.
3. **Only trace 0 was run.** Whether FastLAS's single solution tracks ILASP's set
   across all five traces is unmeasured.
4. **Is one repair enough for the research question?** Not a technical question.
   Sharper now than when this was drafted: since ILASP's space collapses to one
   specification anyway (Result 6), the question is not "one answer or many" but
   "whose one answer" — the merged, less-degraded one, or a single sampled point
   from the same set.
5. **Why does minepump behave unlike everything else?** It is the only run whose
   solution space does not collapse to one (59 -> 10), the only one where
   FastLAS's repair is not among ILASP's, and the only one where FastLAS weakened
   a guarantee. Three outliers in the same case study is unlikely to be
   coincidence.
