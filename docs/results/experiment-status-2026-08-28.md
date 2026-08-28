# Case study 3: the five-step pipeline, stage by stage

Snapshot 2026-08-28. Experiment date `2026-08-13`, learner `fastlas`, 55 runs
(11 case studies x 5 traces). Companion to the
[merge atlas](merge-atlas.html); this is the table, that is the pictures.

**44 of 55 runs have been through all five steps.** minepump traces 1, 2 and 4
are still in the pipeline, and colorsort 0-4 plus genbuf 3-4 have no repairs to
post-process.

## The pipeline these columns report

    1. merge the assumptions of every solution into one set     -> asm
    2. filter to the soft semantically unique, by guarantees    -> unique
    3. broadcast the step-1 assumptions                            (count unchanged)
    4. filter to the strongest, by guarantees                    -> strongest
    5. merge losslessly, by cores and minimal hitting sets       -> merged

Step 3 never changes the count, so it has no column of its own. `strongest` is
deduplicated by guarantee equivalence: step 4 leaves an antichain under
*strict* domination, which still admits two specifications that imply each
other, and those are one answer written twice.

`merged` is complete rather than an upper bound. The outputs are maximal
realisable subsets, read off as the complements of the minimal hitting sets of
the unrealisable cores, and distinct maximal subsets cannot be semantically
equivalent - so no two of them are the same specification.

## Where the violated assumptions come from

`traces.json` records the target and violated assumptions for 45 of the 55
runs. pcar traces 0, 1 and 2 are absent from its manifest although their trace
files exist and were used, so for every run with repairs the set is instead
**derived from the data**: an assumption is violated exactly when the repairs
weakened it, which is visible by comparing each run's assumptions against
`original.spectra`.

The two agree on **all 45 runs where both exist**, no disagreements, which is
what makes the derived values usable for the three the manifest omits. Entries
marked `†` are derived; the rest come from the manifest, which is the only
source for colorsort and genbuf 3-4 since those produced no repairs.

## Status

| Run | Violated assumptions | final | interm | asm | **unique** | **strongest** | **merged** | graph |
|---|---|---:|---:|---:|---:|---:|---:|:-:|
| `amba_trace0` | **2**† · `a30`, `hburst_mutual_exclusion` | 21 | — | 43 | 1 | 1 | 1 | ✅ |
| `amba_trace1` | **2**† · `a30`, `hburst_mutual_exclusion` | 21 | — | 44 | 1 | 1 | 1 | ✅ |
| `amba_trace2` | **2**† · `a30`, `hburst_mutual_exclusion` | 21 | — | 44 | 1 | 1 | 1 | ✅ |
| `amba_trace3` | **2**† · `a30`, `hburst_mutual_exclusion` | 21 | — | 43 | 1 | 1 | 1 | ✅ |
| `amba_trace4` | **1**† · `a30` | 21 | — | 23 | 1 | 1 | 1 | ✅ |
|  |  |  |  |  |  |  |  |  |
| `colorsort_trace0` | **20** · `color_mutual_exclusion_1`, `color_mutual_exclusion_10` +18 | 0 | — | — | — | — | — | — |
| `colorsort_trace1` | **20** · `color_mutual_exclusion_1`, `color_mutual_exclusion_10` +18 | 0 | — | — | — | — | — | — |
| `colorsort_trace2` | **20** · `color_mutual_exclusion_1`, `color_mutual_exclusion_10` +18 | 0 | — | — | — | — | — | — |
| `colorsort_trace3` | **20** · `color_mutual_exclusion_1`, `color_mutual_exclusion_10` +18 | 0 | — | — | — | — | — | — |
| `colorsort_trace4` | **20** · `color_mutual_exclusion_1`, `color_mutual_exclusion_10` +18 | 0 | — | — | — | — | — | — |
|  |  |  |  |  |  |  |  |  |
| `elevator_trace0` | **1**† · `floor_mutual_exclusion` | 21 | — | 17 | 1 | 1 | 1 | ✅ |
| `elevator_trace1` | **1**† · `stopped_implies_floor_known` | 21 | — | 8 | 1 | 1 | 1 | ✅ |
| `elevator_trace2` | **1**† · `floor_mutual_exclusion` | 21 | — | 18 | 1 | 1 | 1 | ✅ |
| `elevator_trace3` | **1**† · `stopped_implies_floor_known` | 21 | — | 8 | 1 | 1 | 1 | ✅ |
| `elevator_trace4` | **1**† · `floor_mutual_exclusion` | 21 | — | 17 | 1 | 1 | 1 | ✅ |
|  |  |  |  |  |  |  |  |  |
| `genbuf_trace0` | **3**† · `unnamed_assumption_10`, `unnamed_assumption_20` +1 | 2 | 1 | 31 | 1 | 1 | 1 | — |
| `genbuf_trace1` | **2**† · `unnamed_assumption_12`, `unnamed_assumption_20` | 2 | 4 | 30 | 1 | 1 | 1 | — |
| `genbuf_trace2` | **5**† · `unnamed_assumption_10`, `unnamed_assumption_12` +3 | 21 | — | 117 | 1 | 1 | 1 | — |
| `genbuf_trace3` | **7** · `unnamed_assumption_10`, `unnamed_assumption_13` +5 | 0 | — | — | — | — | — | — |
| `genbuf_trace4` | **5** · `unnamed_assumption_10`, `unnamed_assumption_13` +3 | 0 | 1 | — | — | — | — | — |
|  |  |  |  |  |  |  |  |  |
| `gyro_trace0` | **1**† · `ready_stays_ready` | 100 | 9 | 48 | 18 | 1 | 1 | ✅ |
| `gyro_trace1` | **1**† · `ready_stays_ready` | 120 | 9 | 58 | 20 | 1 | 1 | ✅ |
| `gyro_trace2` | **1**† · `ready_stays_ready` | 111 | 9 | 53 | 17 | 1 | 1 | ✅ |
| `gyro_trace3` | **1**† · `ready_stays_ready` | 98 | 12 | 51 | 18 | 1 | 1 | ✅ |
| `gyro_trace4` | **1**† · `ready_stays_ready` | 143 | 16 | 56 | 18 | 1 | 1 | ✅ |
|  |  |  |  |  |  |  |  |  |
| `lift_trace0` | **1**† · `button1_off_at_floor1` | 21 | — | 28 | 1 | 1 | 1 | ✅ |
| `lift_trace1` | **1**† · `button2_stays_on` | 21 | — | 27 | 1 | 1 | 1 | ✅ |
| `lift_trace2` | **2**† · `button1_stays_on`, `button3_stays_on` | 21 | — | 44 | 1 | 1 | 1 | ✅ |
| `lift_trace3` | **2**† · `button2_stays_on`, `button3_stays_on` | 21 | — | 42 | 1 | 1 | 1 | ✅ |
| `lift_trace4` | **1**† · `button1_stays_on` | 21 | — | 25 | 1 | 1 | 1 | ✅ |
|  |  |  |  |  |  |  |  |  |
| `minepump_trace0` | **1**† · `assumption1_1` | 17 | — | 14 | 1 | 1 | 1 | ✅ |
| `minepump_trace1` | **1**† · `assumption2_1` | 26877 | 12247 | — | — | — | — | ✅ |
| `minepump_trace2` | **2**† · `assumption1_1`, `assumption2_1` | 23598 | 11608 | — | — | — | — | ✅ |
| `minepump_trace3` | **1**† · `assumption2_1` | 23201 | 9864 | 5 | 10944 | 77 | 12 | ✅ |
| `minepump_trace4` | **2**† · `assumption1_1`, `assumption2_1` | 27589 | 11136 | — | — | — | — | ✅ |
|  |  |  |  |  |  |  |  |  |
| `minepump_liveness_trace0` | **1**† · `assumption1_1` | 37737 | 1130 | 19 | 10704 | 1 | 1 | ✅ |
| `minepump_liveness_trace1` | **1**† · `assumption3_1` | 17 | — | 20 | 1 | 1 | 1 | ✅ |
| `minepump_liveness_trace2` | **1**† · `assumption1_1` | 151 | 31 | 5 | 132 | 1 | 1 | ✅ |
| `minepump_liveness_trace3` | **1**† · `assumption3_1` | 19 | — | 20 | 1 | 1 | 1 | ✅ |
| `minepump_liveness_trace4` | **1**† · `assumption1_1` | 33493 | 1193 | 17 | 12080 | 1 | 1 | ✅ |
|  |  |  |  |  |  |  |  |  |
| `pcar_trace0` | **1**† · `obstacle_mutual_exclusion` | 764 | 73 | 185 | 116 | 1 | 1 | ✅ |
| `pcar_trace1` | **1**† · `sideSense_mutual_exclusion` | 21 | — | 20 | 1 | 1 | 1 | ✅ |
| `pcar_trace2` | **1**† · `unnamed_assumption_1` | 599 | 84 | 128 | 42 | 1 | 1 | ✅ |
| `pcar_trace3` | **1**† · `unnamed_assumption_1` | 2555 | 1266 | 109 | 1484 | 1 | 1 | ✅ |
| `pcar_trace4` | **1**† · `obstacle_mutual_exclusion` | 1140 | 104 | 260 | 35 | 1 | 1 | ✅ |
|  |  |  |  |  |  |  |  |  |
| `traffic_single_trace0` | **1**† · `car_idle_when_red` | 19 | — | 13 | 1 | 1 | 1 | ✅ |
| `traffic_single_trace1` | **1**† · `car_moves_when_green` | 55145 | 7311 | 6 | 26572 | 1 | 1 | ✅ |
| `traffic_single_trace2` | **1**† · `car_idle_when_red` | 19 | — | 12 | 1 | 1 | 1 | ✅ |
| `traffic_single_trace3` | **1**† · `car_moves_when_green` | 15504 | 3632 | 8 | 7873 | 1 | 1 | ✅ |
| `traffic_single_trace4` | **1**† · `car_idle_when_red` | 19 | — | 14 | 1 | 1 | 1 | ✅ |
|  |  |  |  |  |  |  |  |  |
| `traffic_updated_trace0` | **1**† · `carA_idle_when_red` | 21 | — | 18 | 1 | 1 | 1 | ✅ |
| `traffic_updated_trace1` | **1**† · `carA_moves_when_green` | 21 | — | 22 | 1 | 1 | 1 | ✅ |
| `traffic_updated_trace2` | **1**† · `carB_idle_when_red` | 21 | — | 17 | 1 | 1 | 1 | ✅ |
| `traffic_updated_trace3` | **1**† · `carB_moves_when_green` | 21 | — | 22 | 1 | 1 | 1 | ✅ |
| `traffic_updated_trace4` | **1**† · `carA_idle_when_red` | 21 | — | 21 | 1 | 1 | 1 | ✅ |


`†` derived from the repairs rather than read from `traces.json`.

## What the stages do

**Step 1 is where the biggest reduction happens on the assumption side**, and it
is exact: discarding an assumption implied by another kept assumption is
lossless for the conjunction. It also cannot exclude the violating trace - every
input assumption admits it, so their conjunction does. Every specification a run
produces ends up with the same assumption set, so any variation there would be
an artifact of the merge rather than a property of the repairs.

**Step 2 does less than its name suggests.** It buckets on `spot.simplify`
canonical forms, which is conservative: formulas that are equivalent but
simplify differently stay in separate classes. It never over-merges, so the
result is sound, but it keeps more than a fully semantic test would. On minepump
trace 1 that is 26,877 down to 12,881 - a halving, not a collapse - and those
extras are what step 4 then has to grind through.

**Step 4 is the expensive one.** It costs O(n x |maxima|) implication checks and
|maxima| grows into the hundreds. A containment pre-pass removes specifications
whose guarantees are a proper subset of another's, which is sound and free,
before the semantic pass runs.

**Step 5 is cheap where the cores are few and not otherwise.** minepump trace 3
needed 7,056 cores over a 79-formula pool and 236,943 realisability checks,
which is four hours, and is the only run so far that does not merge to 1.

## What is missing, and why

**colorsort, 0 of 5.** Candidates are learned in seconds and lost during
synthesis: the JVM exhausts its heap, `_synthesise_or_reject` turns the
`OutOfMemoryError` into `SpecificationNotVerifiableException`, and the search
records "cannot verify" and moves on - so a run finishes reporting no repair and
looks like a search that found nothing. Unset, the JVM takes a quarter of RAM,
about 15.5GB of a 62GB box, and `run_case_study_3.sh` does not set it. Raising
it to 48g made things worse rather than better: all five runs came back rc=143,
SIGTERM from earlyoom, because `-Xmx` bounds the Java heap while CUDD's BDD
tables are native and uncapped. Re-running at 24g.

**genbuf, 3 of 5.** Traces 0, 1 and 2 have repairs and a merge; 3 and 4 have
none after a week. Three separate walls, each real: `exploreAllCores`'
quadratic memoisation, replaced by MARCO; then genuinely hard `gr1Game` calls;
then a per-verification cost of hours - trace 1's completed verifications took
2h51m and 3h01m, trace 4 got one back in 9h22m and its next ran 32h without
returning. genbuf has no graphs either: `asm` and `gar` both hit the one-hour
cap, since 81 guarantees make every implication check expensive even though the
merged set is a single specification.

**minepump 1, 2 and 4** are still running.
