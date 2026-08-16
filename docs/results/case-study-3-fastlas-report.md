# case_study_3 - FastLAS results

Run **2026-08-13**, FastLAS arm only, under CUDD with the counter-strategy
expansion capped. Nothing here is comparable with anything measured before
2026-08-13: the BDD package changed, and a different package can return a
different counter-strategy among the many valid ones.

Regenerate the derived tables with `scripts/report_trace_violations.py` and
`scripts/report_repair_modifications.py`.

## 1. What each trace violates

Full table: [case-study-3-trace-violations.md](case-study-3-trace-violations.md).
Summary, assumptions broken per trace:

| case study | per trace | isolates one assumption |
| --- | --- | --- |
| elevator, gyro, traffic_single, traffic_updated, pcar | 1 each | 5 of 5 |
| minepump | 1, 1, 2, 1, 1 | 4 of 5 |
| lift | 1, 1, 2, 2, 1 | 3 of 5 |
| amba | 2, 2, 2, 2, 1 | 1 of 5 |
| genbuf | 3, 2, 5, 7, 5 | 0 of 5 |
| colorsort | **20 each** | 0 of 5 |

37 of 55 traces isolate a single assumption; 34 also violate a guarantee, which
is permitted - once the environment breaks an assumption the system is released.

colorsort's twenty are the pairwise mutual-exclusion constraints that encode two
5-valued enums as booleans, so its five traces are one case repeated five times.

## 2. What the repairs changed

Weakened means the formula text changed; dropped means it is absent from the
repaired specification. `from` is `merged` where the run has been merged, and a
5-solution sample where it has not, so sampled sets may still grow.

| case study | trace | asm weakened | gar weakened | dropped | changes | from |
| --- | --- | --- | --- | --- | --- | --- |
| amba | 0 | - | - | `a30`, `hburst_mutual_exclusion` | 2 | merged |
| amba | 1 | `a30`, `hburst_mutual_exclusion` | - | - | 2 | merged |
| amba | 2 | `a30`, `hburst_mutual_exclusion` | - | - | 2 | merged |
| amba | 3 | `a30`, `hburst_mutual_exclusion` | - | - | 2 | final (sample) |
| amba | 4 | - | - | `a30` | 1 | merged |
| elevator | 0 | `floor_mutual_exclusion` | - | - | 1 | final (sample) |
| elevator | 1 | `stopped_implies_floor_known` | - | - | 1 | merged |
| elevator | 2 | `floor_mutual_exclusion` | - | - | 1 | final (sample) |
| elevator | 3 | `stopped_implies_floor_known` | - | - | 1 | merged |
| elevator | 4 | `floor_mutual_exclusion` | - | - | 1 | final (sample) |
| genbuf | 0 | `unnamed_assumption_10`, `unnamed_assumption_20`, `unnamed_assumption_26` | - | - | 3 | final (sample) |
| genbuf | 2 | `unnamed_assumption_12`, `unnamed_assumption_18` | - | `unnamed_assumption_10`, `unnamed_assumption_14`, `unnamed_assumption_16` | 5 | merged |
| gyro | 0 | `ready_stays_ready` | - | - | 1 | final (sample) |
| gyro | 1 | `ready_stays_ready` | - | - | 1 | final (sample) |
| gyro | 2 | `ready_stays_ready` | - | - | 1 | final (sample) |
| gyro | 3 | `ready_stays_ready` | - | - | 1 | final (sample) |
| gyro | 4 | `ready_stays_ready` | `not_ready_implies_stopped`, `safety_requirement` | - | 1-3 | final (sample) |
| lift | 0 | - | - | `button1_off_at_floor1` | 1 | merged |
| lift | 1 | - | - | `button2_stays_on` | 1 | merged |
| lift | 2 | - | - | `button1_stays_on`, `button3_stays_on` | 2 | merged |
| lift | 3 | - | - | `button2_stays_on`, `button3_stays_on` | 2 | merged |
| lift | 4 | `button1_stays_on` | - | - | 1 | merged |
| minepump | 0 | `assumption1_1` | - | - | 1 | final (sample) |
| minepump | 1 | `assumption2_1` | `guarantee1_1` | - | 2 | final (sample) |
| minepump | 2 | `assumption1_1`, `assumption2_1` | `guarantee1_1`, `guarantee2_1` | - | 3-4 | final (sample) |
| minepump | 3 | `assumption2_1` | `guarantee1_1`, `guarantee2_1` | - | 2-3 | final (sample) |
| minepump | 4 | `assumption1_1`, `assumption2_1` | `guarantee2_1` | - | 3 | final (sample) |
| minepump_liveness | 0 | `assumption1_1` | `guarantee3_1`, `guarantee4_1` | - | 1-3 | final (sample) |
| minepump_liveness | 1 | `assumption3_1` | - | - | 1 | final (sample) |
| minepump_liveness | 2 | `assumption1_1` | `guarantee2_1`, `guarantee4_1` | - | 1-3 | final (sample) |
| minepump_liveness | 3 | `assumption3_1` | - | - | 1 | final (sample) |
| minepump_liveness | 4 | `assumption1_1` | `guarantee3_1`, `guarantee4_1` | - | 1-3 | final (sample) |
| pcar | 0 | `obstacle_mutual_exclusion` | - | - | 1 | final (sample) |
| pcar | 1 | `sideSense_mutual_exclusion` | - | - | 1 | merged |
| pcar | 2 | `unnamed_assumption_1` | - | - | 1 | final (sample) |
| pcar | 3 | `unnamed_assumption_1` | `unnamed_guarantee_1` | - | 1-2 | final (sample) |
| pcar | 4 | `obstacle_mutual_exclusion` | - | - | 1 | final (sample) |
| traffic_single | 0 | `car_idle_when_red` | - | - | 1 | merged |
| traffic_single | 1 | `car_moves_when_green` | `green_often`, `no_car_often` | - | 1-3 | final (sample) |
| traffic_single | 2 | `car_idle_when_red` | - | - | 1 | merged |
| traffic_single | 3 | `car_moves_when_green` | `no_car_often` | - | 1-2 | final (sample) |
| traffic_single | 4 | `car_idle_when_red` | - | - | 1 | merged |
| traffic_updated | 0 | - | - | `carA_idle_when_red` | 1 | merged |
| traffic_updated | 1 | - | - | `carA_moves_when_green` | 1 | merged |
| traffic_updated | 2 | - | - | `carB_idle_when_red` | 1 | merged |
| traffic_updated | 3 | `carB_moves_when_green` | - | - | 1 | merged |
| traffic_updated | 4 | - | - | `carA_idle_when_red` | 1 | merged |

**The repair targets what the trace broke.** `floor_mutual_exclusion` for
elevator 0/2/4 and `stopped_implies_floor_known` for 1/3; `assumption1_1` and
`assumption2_1` tracking minepump's targets; `ready_stays_ready` for every gyro
trace; `car_idle_when_red` / `car_moves_when_green` for traffic_single. That
correspondence is the soundness check, and it holds on every finished run.

Repairs are **small**: 1 to 5 expressions. lift and traffic_updated mostly
*drop* an assumption where the others weaken one.

## 3. Post-processing

Steps 2-4 of the pipeline, then the three implication graphs.

| run | final | merged | maximal | unique | graphs |
| --- | --- | --- | --- | --- | --- |
| amba_trace0 | 21 | 1 | 1 | 1 | 2 |
| amba_trace1 | 21 | 1 | 1 | 1 | pending |
| amba_trace2 | 21 | 1 | 1 | 1 | pending |
| amba_trace4 | 21 | 1 | 1 | 1 | pending |
| elevator_trace1 | 21 | 1 | 1 | 1 | 3 |
| elevator_trace3 | 21 | 1 | 1 | 1 | 3 |
| genbuf_trace2 | 21 | 1 | 1 | 1 | pending |
| lift_trace0 | 21 | 1 | 1 | 1 | 3 |
| lift_trace1 | 21 | 1 | 1 | 1 | 3 |
| lift_trace2 | 21 | 1 | 1 | 1 | 3 |
| lift_trace3 | 21 | 1 | 1 | 1 | 3 |
| lift_trace4 | 21 | 1 | 1 | 1 | 3 |
| pcar_trace1 | 21 | 1 | 1 | 1 | 3 |
| traffic_single_trace0 | 19 | 1 | 1 | 1 | 3 |
| traffic_single_trace2 | 19 | 1 | 1 | 1 | 3 |
| traffic_single_trace4 | 19 | 1 | 1 | 1 | 3 |
| traffic_updated_trace0 | 21 | 1 | 1 | 1 | 3 |
| traffic_updated_trace1 | 21 | 1 | 1 | 1 | 3 |
| traffic_updated_trace2 | 21 | 1 | 1 | 1 | 3 |
| traffic_updated_trace3 | 21 | 1 | 1 | 1 | 3 |
| traffic_updated_trace4 | 21 | 1 | 1 | 1 | 3 |

**Every run collapses to exactly one specification.** 19-21 solutions merge to a
single realisable specification, which is then trivially maximal and
semantically unique. That has held for every case study measured, so the search
produces one coherent answer per trace rather than a spread.

## 4. Graphs

Three per run, in each run directory:

* `implication_graph_asm.png` - assumptions only
* `implication_graph_gar.png` - guarantees only
* `implication_graph_gr1.png` - whole specification, assumptions -> guarantees

Each draws `original`, `trivial` (the floor) and `unique_max_merged` as groups,
with edges for implication, so a sound repair sits strictly between the trivial
solution and the original.

**genbuf has no graphs, and cannot have them by this method.** Two reasons, both
measured. Its trivial solutions were never generated - the `exploreAllCores`
stall - so there is no floor to draw against. And the comparison itself does not
complete: `ltlfilt` dies with `std::bad_alloc` translating genbuf's
28-assumption conjunction into an automaton, having consumed ~59GB on a box with
no `ulimit`. That is a scaling wall in the automata construction, distinct from
the acceptance-set ceiling below, and raising the limit does not touch it.

Three bugs had to be fixed before any of these existed, all on 2026-08-16:

* **All graphs failed.** `PATH` put `Tools/bin/ltlfilt` (Spot 2.11.6) ahead of
  conda's while `LD_LIBRARY_PATH` supplied conda's `libspot.so.0` (2.14.3):
  mismatched ABI, exit 127. `does_left_imply_right` discards stderr and reports
  only "the output of ltlfilt is unexpected".
* **`gr1` failed on liveness-heavy specifications.** Spot's compile-time ceiling
  of 32 acceptance sets, which a whole-GR1 comparison passes. Rebuilt as 2.14.5
  with `--enable-max-accsets=128` in `/vol/bitbucket/tg4018/spot-maxacc`,
  selected by `SPEC_REPAIR_LTLFILT`.
* **Every failure looked identical.** `does_left_imply_right` discarded
  `ltlfilt`'s stderr and raised "the output of ltlfilt is unexpected" for all of
  them, so an ABI mismatch (exit 127), an acceptance-set overflow (exit 2) and
  an out-of-memory (also exit 2) were indistinguishable and each cost a separate
  investigation. It now reports the exit code and what ltlfilt actually said -
  which is how the `std::bad_alloc` above was found in one run rather than
  three.

## 5. What did not finish, and why

Diagnostic, not results.

| case study | traces | state | cause |
| --- | --- | --- | --- |
| colorsort | 0, 1, 4 | rerunning on Slurm | **earlyoom** SIGTERMed them at 4-7h. Every lab box runs `earlyoom -r 60 -m 25 -s 25`: SIGTERM to the largest process whenever *available* memory drops under 25%, so a run dies for somebody else's memory. The compute nodes do not run it. |
| colorsort | 2, 3 | finished, 0 repairs | FastLAS learned 3 candidates in 17s; all three were discarded as `SpecificationNotVerifiableException` after 46m, 1h59m and 30m. Synthesis exhausts the JVM heap, which defaults to a quarter of RAM. `SPEC_REPAIR_JVM_HEAP` now raises it; trace 2 is rerunning at 40g. |
| genbuf | 0, 1, 3, 4 | running, 0-2 specs | `exploreAllCores` does not return. Measured directly: genbuf is realizable with one violated assumption removed and unrealisable with two, and the core search on that point has not returned in hours. Nothing is wrong with the file - Spectra decides realizability in 1.6s. Not to be bounded: a truncated core set breaks the hitting-set argument the trivial solutions are proven on. |
| minepump, gyro, pcar, traffic_single, minepump_liveness | various | still running | Deep searches, 35-49h, producing thousands of solutions. First repair arrived in seconds to 22 minutes; the remaining time finds more. |

## 6. Timing

First repair arrives quickly wherever it arrives at all.

| case study | first repair | run length |
| --- | --- | --- |
| elevator, lift, traffic_updated | 8-22s | 15-54s, done |
| traffic_single (0, 2, 4) | 12-27s | 17-59s, done |
| minepump_liveness (1, 3), pcar_1, minepump_0 | 9-18s | 40-50s, done |
| genbuf_2 | 1m02s | 1m15s, done |
| amba | 1m22s-1m53s | 11-13m, done |
| minepump 1-4, traffic_single 1 | 1m18s-4m34s | 35h+, running |
| pcar 0-4, gyro 0-4 | 1m-1h | 35-46h, running |
