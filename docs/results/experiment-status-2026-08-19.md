# Case study 3: every run, every pipeline stage

Snapshot taken 2026-08-19 15:00. Experiment date `2026-08-13`, learner `fastlas`,
55 runs (11 case studies x 5 traces). **47 have results**; colorsort 0-4 and
genbuf 1/3/4 have none.

## The pipeline this table reports

Post-processing is a main chain with two side-branches off the same pool, not one
line:

    final_specs --+--> strongest_gar --> unique --> merged      (main chain)
                  |
                  +--> asm_merge                (assumptions of every repair, conjoined)
                  |
                  +--> unique_from_final        (the paper's "unique", measured on the raw pool)

`asm_merge` reads `final_specs` and produces a single specification, so it is an
artifact of its own rather than a stage the chain flows through - conjoining the
assumptions of *every* repair the search found, including the guarantee-weakening
ones that `strongest_gar` drops before they can reach a merge.

`unique_from_final` exists because the `unique` count inside the chain is **not**
the number the paper reports. There, `strongest_gar` has already removed dominated
specifications, so an entire equivalence class that happened to be dominated never
reaches the equivalence check at all. The paper's figure is the equivalence filter
applied to the raw pool, which is what this branch measures. Where a run was
post-processed in the old order (unique first, then strongest), that stage-1 number
*is* this measurement and is reported as such.

## Legend

| symbol | meaning |
| --- | --- |
| ✅ n | stage passed, produced n specifications |
| ✅ *nr* | stage passed, but the count was never written to a log that survived |
| ⏳ | in progress, or queued behind work in progress |
| ❌ | crashed, was killed, or produced nothing |
| — | not applicable (nothing upstream to work on) |
| asm/gar/gr1 | graphs drawn; `·` marks one that is missing |
| ‡ | this run's filters ran in the opposite order (final → unique → strongest_gar); each column still reports its own filter's output, so the later column may hold the larger number |

`intermediate` counts `intermediate_specs/`, which most runs never write - a `—`
there is an absent directory, not a failure.

## Status

| Run | Violated assumptions | Search | intermediate | final | asm_merge | strongest_gar | unique (chain) | merged | unique-from-final | trivial | graphs | n |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `amba_trace0` | **2** · `a30`, `hburst_mutual_exclusion` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ *nr* | ✅ *nr* | ✅ 1 | ⏳ queued | ✅ 1 | asm/gar/· | [n](#amba-trace0) |
| `amba_trace1` | **2** · `a30`, `hburst_mutual_exclusion` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ *nr* | ✅ *nr* | ✅ 1 | ⏳ queued | ✅ 1 | asm/gar/· | [n](#amba-trace1) |
| `amba_trace2` | **2** · `a30`, `hburst_mutual_exclusion` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ *nr* | ✅ *nr* | ✅ 1 | ⏳ queued | ✅ 1 | asm/gar/· | [n](#amba-trace2) |
| `amba_trace3` | **2** · `a30`, `hburst_mutual_exclusion` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ *nr* | ✅ *nr* | ✅ 1 | ⏳ queued | ✅ 1 | — | [n](#amba-trace3) |
| `amba_trace4` | **1** · `a30` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ *nr* | ✅ *nr* | ✅ 1 | ⏳ queued | ✅ 1 | asm/gar/· | [n](#amba-trace4) |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
| `colorsort_trace0` | **20** · `color_mutual_exclusion_1`, `color_mutual_exclusion_10` +18 | ❌ stopped | — | ❌ 0 | ⏳ queued | — | — | — | — | ✅ 16 | — | [n](#colorsort-trace0) |
| `colorsort_trace1` | **20** · `color_mutual_exclusion_1`, `color_mutual_exclusion_10` +18 | ❌ stopped | — | ❌ 0 | ⏳ queued | — | — | — | — | ✅ 16 | — | [n](#colorsort-trace1) |
| `colorsort_trace2` | **20** · `color_mutual_exclusion_1`, `color_mutual_exclusion_10` +18 | ✅ done | — | ❌ 0 | ⏳ queued | — | — | — | — | ✅ 16 | — |  |
| `colorsort_trace3` | **20** · `color_mutual_exclusion_1`, `color_mutual_exclusion_10` +18 | ✅ done | — | ❌ 0 | ⏳ queued | — | — | — | — | ✅ 16 | — |  |
| `colorsort_trace4` | **20** · `color_mutual_exclusion_1`, `color_mutual_exclusion_10` +18 | ❌ stopped | — | ❌ 0 | ⏳ queued | — | — | — | — | ✅ 16 | — | [n](#colorsort-trace4) |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
| `elevator_trace0` | **1** · `floor_mutual_exclusion` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ 21 | ✅ 16 | ✅ 1 | ⏳ queued | ✅ 1 | — |  |
| `elevator_trace1` | **1** · `stopped_implies_floor_known` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ 7 ‡ | ✅ 7 ‡ | ✅ 1 | ✅ 7 | ✅ 1 | asm/gar/gr1 | [n](#elevator-trace1) |
| `elevator_trace2` | **1** · `floor_mutual_exclusion` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ 21 | ✅ 15 | ✅ 1 | ⏳ queued | ✅ 1 | — |  |
| `elevator_trace3` | **1** · `stopped_implies_floor_known` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ 7 ‡ | ✅ 7 ‡ | ✅ 1 | ✅ 7 | ✅ 1 | asm/gar/gr1 | [n](#elevator-trace3) |
| `elevator_trace4` | **1** · `floor_mutual_exclusion` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ 21 | ✅ 16 | ✅ 1 | ⏳ queued | ✅ 1 | — |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
| `genbuf_trace0` | **3** · `unnamed_assumption_10`, `unnamed_assumption_20` +1 | ❌ stopped | 1 | ✅ 2 | ⏳ queued | ✅ 2 | ⏳ on gpu08 | ⏳ on gpu08 | ⏳ queued | ⏳ running | — | [n](#genbuf-trace0) |
| `genbuf_trace1` | **2** · `unnamed_assumption_12`, `unnamed_assumption_20` | ❌ stopped | — | ❌ 0 | ⏳ queued | — | — | — | — | ⏳ running | — | [n](#genbuf-trace1) |
| `genbuf_trace2` | **5** · `unnamed_assumption_10`, `unnamed_assumption_12` +3 | ✅ done | — | ✅ 21 | ⏳ queued | ✅ 21 | ⏳ on gpu07 | ⏳ on gpu07 | ⏳ queued | ✅ 1 | — |  |
| `genbuf_trace3` | **7** · `unnamed_assumption_10`, `unnamed_assumption_13` +5 | ⏳ verifying d1 candidate | — | ❌ 0 | ⏳ queued | — | — | — | — | ⏳ running | — | [n](#genbuf-trace3) |
| `genbuf_trace4` | **5** · `unnamed_assumption_10`, `unnamed_assumption_13` +3 | ❌ stopped | — | ❌ 0 | ⏳ queued | — | — | — | — | ⏳ running | — | [n](#genbuf-trace4) |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
| `gyro_trace0` | **1** · `ready_stays_ready` | ❌ stopped | 9 | ✅ 100 | ⏳ queued | ✅ 24 ‡ | ✅ 35 ‡ | ✅ 1 | ✅ 35 | ✅ 3 | asm/gar/gr1 | [n](#gyro-trace0) |
| `gyro_trace1` | **1** · `ready_stays_ready` | ❌ stopped | 9 | ✅ 120 | ⏳ queued | ✅ 35 ‡ | ✅ 50 ‡ | ✅ 1 | ✅ 50 | ✅ 3 | asm/gar/gr1 | [n](#gyro-trace1) |
| `gyro_trace2` | **1** · `ready_stays_ready` | ⏳ verifying d3 candidate | 9 | ✅ 111 | ⏳ queued | ✅ 28 ‡ | ✅ 36 ‡ | ✅ 1 | ✅ 36 | ✅ 3 | asm/gar/gr1 | [n](#gyro-trace2) |
| `gyro_trace3` | **1** · `ready_stays_ready` | ⏳ verifying d3 candidate | 12 | ✅ 98 | ⏳ queued | ✅ 28 ‡ | ✅ 39 ‡ | ✅ 1 | ✅ 39 | ✅ 3 | asm/gar/gr1 | [n](#gyro-trace3) |
| `gyro_trace4` | **1** · `ready_stays_ready` | ❌ stopped | 16 | ✅ 143 | ⏳ queued | ✅ 32 ‡ | ✅ 42 ‡ | ✅ 1 | ✅ 42 | ✅ 3 | asm/gar/gr1 | [n](#gyro-trace4) |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
| `lift_trace0` | **1** · `button1_off_at_floor1` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ *nr* | ✅ *nr* | ✅ 1 | ⏳ queued | ✅ 1 | asm/gar/gr1 |  |
| `lift_trace1` | **1** · `button2_stays_on` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ *nr* | ✅ *nr* | ✅ 1 | ⏳ queued | ✅ 1 | asm/gar/gr1 |  |
| `lift_trace2` | **2** · `button1_stays_on`, `button3_stays_on` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ *nr* | ✅ *nr* | ✅ 1 | ⏳ queued | ✅ 1 | asm/gar/gr1 |  |
| `lift_trace3` | **2** · `button2_stays_on`, `button3_stays_on` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ *nr* | ✅ *nr* | ✅ 1 | ⏳ queued | ✅ 1 | asm/gar/gr1 |  |
| `lift_trace4` | **1** · `button1_stays_on` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ *nr* | ✅ *nr* | ✅ 1 | ⏳ queued | ✅ 1 | asm/gar/gr1 |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
| `minepump_trace0` | **1** · `assumption1_1` | ✅ done | — | ✅ 17 | ⏳ queued | ✅ 11 ‡ | ✅ 11 ‡ | ✅ 1 | ✅ 11 | ✅ 1 | asm/gar/gr1 | [n](#minepump-trace0) |
| `minepump_trace1` | **1** · `assumption2_1` | ⏳ verifying d5 candidate | 12247 | ✅ 26877 | ⏳ queued | ⏳ on gpu17 | ⏳ on gpu17 | ⏳ on gpu17 | ⏳ queued | ✅ 2 | — | [n](#minepump-trace1) |
| `minepump_trace2` | **2** · `assumption1_1`, `assumption2_1` | ❌ stopped | 11608 | ✅ 23598 | ⏳ queued | ⏳ on gpu18 | ⏳ on gpu18 | ⏳ on gpu18 | ⏳ queued | ✅ 2 | — | [n](#minepump-trace2) |
| `minepump_trace3` | **1** · `assumption2_1` | ⏳ learning d4 (guarantee_weakening) | 9864 | ✅ 23201 | ⏳ queued | ⏳ on gpu14 | ⏳ on gpu14 | ⏳ on gpu14 | ⏳ queued | ✅ 2 | — | [n](#minepump-trace3) |
| `minepump_trace4` | **2** · `assumption1_1`, `assumption2_1` | ❌ stopped | 11136 | ✅ 27589 | ⏳ queued | ⏳ on gpu15 | ⏳ on gpu15 | ⏳ on gpu15 | ⏳ queued | ✅ 2 | — | [n](#minepump-trace4) |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
| `minepump_liveness_trace0` | **1** · `assumption1_1` | ⏳ learning d4 (guarantee_weakening) | 737 | ✅ 18542 | ⏳ queued | ⏳ on gpu20 | ⏳ on gpu20 | ⏳ on gpu20 | ⏳ queued | ✅ 2 | — | [n](#minepump-liveness-trace0) |
| `minepump_liveness_trace1` | **1** · `assumption3_1` | ✅ done | — | ✅ 17 | ⏳ queued | ✅ 17 | ✅ 13 | ✅ 1 | ⏳ queued | ✅ 1 | asm/gar/gr1 |  |
| `minepump_liveness_trace2` | **1** · `assumption1_1` | ❌ stopped | 31 | ✅ 151 | ⏳ queued | ✅ *nr* | ✅ *nr* | ✅ 1 | ⏳ queued | ✅ 2 | asm/gar/gr1 | [n](#minepump-liveness-trace2) |
| `minepump_liveness_trace3` | **1** · `assumption3_1` | ✅ done | — | ✅ 19 | ⏳ queued | ✅ 19 | ✅ 12 | ✅ 1 | ⏳ queued | ✅ 1 | asm/gar/gr1 |  |
| `minepump_liveness_trace4` | **1** · `assumption1_1` | ❌ stopped | 983 | ✅ 21135 | ⏳ queued | ✅ 19 | ✅ 7 | ✅ 1 | ⏳ queued | ✅ 2 | — | [n](#minepump-liveness-trace4) |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
| `pcar_trace0` | **1** · `obstacle_mutual_exclusion` | ❌ stopped | 73 | ✅ 764 | ⏳ queued | ✅ *nr* | ✅ *nr* | ✅ 1 | ⏳ queued | ✅ 2 | asm/gar/gr1 | [n](#pcar-trace0) |
| `pcar_trace1` | **1** · `sideSense_mutual_exclusion` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ 17 ‡ | ✅ 17 ‡ | ✅ 1 | ✅ 17 | ✅ 1 | asm/gar/gr1 | [n](#pcar-trace1) |
| `pcar_trace2` | **1** · `unnamed_assumption_1` | ⏳ verifying d3 candidate | 78 | ✅ 568 | ⏳ queued | ✅ 75 ‡ | ✅ 86 ‡ | ✅ 1 | ✅ 86 | ✅ 2 | asm/gar/gr1 | [n](#pcar-trace2) |
| `pcar_trace3` | **1** · `unnamed_assumption_1` | ⏳ verifying d3 candidate | 569 | ✅ 1315 | ⏳ queued | ✅ 71 ‡ | ✅ 152 ‡ | ✅ 1 | ✅ 152 | ✅ 2 | asm/gar/gr1 | [n](#pcar-trace3) |
| `pcar_trace4` | **1** · `obstacle_mutual_exclusion` | ⏳ learning d2 (assumption_weakening) | 92 | ✅ 940 | ⏳ queued | ✅ *nr* | ✅ *nr* | ✅ 1 | ⏳ queued | ✅ 2 | asm/gar/gr1 | [n](#pcar-trace4) |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
| `traffic_single_trace0` | **1** · `car_idle_when_red` | ✅ done | — | ✅ 19 | ⏳ queued | ✅ 7 ‡ | ✅ 7 ‡ | ✅ 1 | ✅ 7 | ✅ 1 | asm/gar/gr1 | [n](#traffic-single-trace0) |
| `traffic_single_trace1` | **1** · `car_moves_when_green` | ⏳ verifying d6 candidate | 5003 | ✅ 35640 | ⏳ queued | ✅ 2 | ✅ 2 | ✅ 1 | ⏳ queued | ✅ 1 | — | [n](#traffic-single-trace1) |
| `traffic_single_trace2` | **1** · `car_idle_when_red` | ✅ done | — | ✅ 19 | ⏳ queued | ✅ 7 ‡ | ✅ 7 ‡ | ✅ 1 | ✅ 7 | ✅ 1 | asm/gar/gr1 | [n](#traffic-single-trace2) |
| `traffic_single_trace3` | **1** · `car_moves_when_green` | ⏳ verifying d5 candidate | 839 | ✅ 3395 | ⏳ queued | ✅ 3 | ✅ 3 | ✅ 1 | ⏳ queued | ✅ 1 | asm/gar/gr1 | [n](#traffic-single-trace3) |
| `traffic_single_trace4` | **1** · `car_idle_when_red` | ✅ done | — | ✅ 19 | ⏳ queued | ✅ 7 ‡ | ✅ 7 ‡ | ✅ 1 | ✅ 7 | ✅ 1 | asm/gar/gr1 | [n](#traffic-single-trace4) |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
| `traffic_updated_trace0` | **1** · `carA_idle_when_red` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ 10 ‡ | ✅ 10 ‡ | ✅ 1 | ✅ 10 | ✅ 1 | asm/gar/gr1 | [n](#traffic-updated-trace0) |
| `traffic_updated_trace1` | **1** · `carA_moves_when_green` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ 12 ‡ | ✅ 12 ‡ | ✅ 1 | ✅ 12 | ✅ 1 | asm/gar/gr1 | [n](#traffic-updated-trace1) |
| `traffic_updated_trace2` | **1** · `carB_idle_when_red` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ 10 ‡ | ✅ 10 ‡ | ✅ 1 | ✅ 10 | ✅ 1 | asm/gar/gr1 | [n](#traffic-updated-trace2) |
| `traffic_updated_trace3` | **1** · `carB_moves_when_green` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ 11 ‡ | ✅ 11 ‡ | ✅ 1 | ✅ 11 | ✅ 1 | asm/gar/gr1 | [n](#traffic-updated-trace3) |
| `traffic_updated_trace4` | **1** · `carA_idle_when_red` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ 10 ‡ | ✅ 10 ‡ | ✅ 1 | ✅ 10 | ✅ 1 | asm/gar/gr1 | [n](#traffic-updated-trace4) |

## Where the 55 stand, stage by stage

| stage | passed | in progress | crashed / none | n/a |
| --- | --- | --- | --- | --- |
| search | 30 | 11 | 14 | — |
| final specs | 47 | — | 8 | — |
| asm_merge | 0 | 55 queued | — | — |
| strongest_gar | 42 | 5 | — | 8 |
| unique (chain) | 40 | 7 | — | 8 |
| merged | 40 | 7 | — | 8 |
| unique-from-final | 19 | 28 | — | 8 |
| trivial solutions | 51 | 4 | — | — |

The seven merges still running are genbuf 0 and 2, minepump 1-4 and
minepump_liveness 0. The 28 outstanding unique-from-final measurements are queued
six-deep across gpu01/02/06/09/16/19; the 19 already reported come from runs that
were post-processed in the old order, where that number was measured directly.

## Bugs

**No lock on a run directory.** Nothing stops two processes working the same run.
It has happened twice and both are live findings, not history:
`traffic_single_trace3` currently has **two search processes** (gpu12 and gpu20)
writing one `final_specs/`, and `genbuf_trace0` had two `filter_then_merge`
processes until one was killed today. Every count drawn from a directory in that
state is the sum of two writers.

**`ftm_big.sh` truncates the log it shares.** The script opens its log with `>`,
keyed only on the run name. A second process on the same run therefore erases the
first's output and later appends its own `rc=`, which then reads as the surviving
job's exit status. `genbuf_trace0_fastlas.big.log` carries exactly this: an
`rc=143` from the process killed today, above a job that is still running.

**Post-processing read pools that were still being written.** Eleven searches have
never stopped, so `filter_then_merge` sampled a moving target. `pcar_trace3` was
filtered at 382 final specs and now holds 1315; `pcar_trace2` at 490, now 568;
`gyro_trace0` at 97, now 100. Their merged output is correct for the pool as it was
read, and is not a result over the pool as it now stands.

**A dead search is indistinguishable from a live one on disk.** `status.txt` is
only ever advanced by the process itself, so a killed run keeps its last phase
forever. Fourteen runs read `verifying dN candidate` with no process behind them;
telling those apart from the eleven genuinely running needed a `ps` sweep across
twenty machines, not anything in the run directory.

**Fixed today, listed because the table still carries their marks.**
`exploreAllCores`'s quadratic memoisation, which is why genbuf had no trivial
solutions for five days (now MARCO); the `PREV` shift doubling at every conjunction,
which turned one `PREV` into 59,010 `X` operators and killed ten merges on memory
(`362547c`); and `SpecificationNotVerifiableException` reporting neither of the two
conditions it covers (`6e4df2a`), which is why colorsort's failures are still
uncharacterised.

## Details

Numbered by run. Everything here is specific to one run and does not generalise.

<a id="amba-trace0"></a>**`amba_trace0`**
- an earlier post-processing attempt hit the 6h `timeout` (rc=124)

<a id="amba-trace1"></a>**`amba_trace1`**
- an earlier post-processing attempt hit the 6h `timeout` (rc=124)

<a id="amba-trace2"></a>**`amba_trace2`**
- an earlier post-processing attempt hit the 6h `timeout` (rc=124)

<a id="amba-trace3"></a>**`amba_trace3`**
- an earlier post-processing attempt hit the 6h `timeout` (rc=124)

<a id="amba-trace4"></a>**`amba_trace4`**
- an earlier attempt died rc=2 (`ltl2tgba` out of memory, pre-PREV-fix)

<a id="colorsort-trace0"></a>**`colorsort_trace0`**
- search process gone while status.txt still reads `verifying d1 candidate` at 3h25m36s — died rather than finished

<a id="colorsort-trace1"></a>**`colorsort_trace1`**
- search process gone while status.txt still reads `verifying d1 candidate` at 6h12m04s — died rather than finished

<a id="colorsort-trace4"></a>**`colorsort_trace4`**
- search process gone while status.txt still reads `verifying d1 candidate` at 5h11m00s — died rather than finished

<a id="elevator-trace1"></a>**`elevator_trace1`**
- stage counts come from the old order (unique → strongest); same final set

<a id="elevator-trace3"></a>**`elevator_trace3`**
- stage counts come from the old order (unique → strongest); same final set

<a id="genbuf-trace0"></a>**`genbuf_trace0`**
- search process gone while status.txt still reads `verifying d1 candidate` at 122h26m20s — died rather than finished
- rc=143 in the shared log is the duplicate process killed on 2026-08-19, not this run

<a id="genbuf-trace1"></a>**`genbuf_trace1`**
- search process gone while status.txt still reads `verifying d1 candidate` at 142h25m45s — died rather than finished

<a id="genbuf-trace3"></a>**`genbuf_trace3`**
- search still running on gpu20 after 136h24m07s

<a id="genbuf-trace4"></a>**`genbuf_trace4`**
- search process gone while status.txt still reads `verifying d1 candidate` at 122h26m40s — died rather than finished

<a id="gyro-trace0"></a>**`gyro_trace0`**
- search process gone while status.txt still reads `verifying d3 candidate` at 103h00m41s — died rather than finished
- unique-from-final measured on a pool of 97, not today's 100 — the search kept writing after post-processing read it
- stage counts come from the old order (unique → strongest); same final set

<a id="gyro-trace1"></a>**`gyro_trace1`**
- search process gone while status.txt still reads `verifying d3 candidate` at 103h11m19s — died rather than finished
- unique-from-final measured on a pool of 109, not today's 120 — the search kept writing after post-processing read it
- stage counts come from the old order (unique → strongest); same final set

<a id="gyro-trace2"></a>**`gyro_trace2`**
- search still running on gpu12 after 103h00m31s
- unique-from-final measured on a pool of 101, not today's 111 — the search kept writing after post-processing read it
- stage counts come from the old order (unique → strongest); same final set

<a id="gyro-trace3"></a>**`gyro_trace3`**
- search still running on gpu16 after 103h17m34s
- unique-from-final measured on a pool of 93, not today's 98 — the search kept writing after post-processing read it
- stage counts come from the old order (unique → strongest); same final set

<a id="gyro-trace4"></a>**`gyro_trace4`**
- search process gone while status.txt still reads `verifying d3 candidate` at 98h26m53s — died rather than finished
- unique-from-final measured on a pool of 138, not today's 143 — the search kept writing after post-processing read it
- stage counts come from the old order (unique → strongest); same final set

<a id="minepump-trace0"></a>**`minepump_trace0`**
- stage counts come from the old order (unique → strongest); same final set

<a id="minepump-trace1"></a>**`minepump_trace1`**
- search still running on gpu19 after 99h47m25s

<a id="minepump-trace2"></a>**`minepump_trace2`**
- search process gone while status.txt still reads `learning d4 (guarantee_weakening)` at 99h47m23s — died rather than finished
- an earlier attempt died rc=2 (`ltl2tgba` out of memory, pre-PREV-fix)

<a id="minepump-trace3"></a>**`minepump_trace3`**
- search still running on gpu19 after 99h47m13s
- an earlier attempt died rc=2 (`ltl2tgba` out of memory, pre-PREV-fix)

<a id="minepump-trace4"></a>**`minepump_trace4`**
- search process gone while status.txt still reads `verifying d5 candidate` at 99h47m25s — died rather than finished

<a id="minepump-liveness-trace0"></a>**`minepump_liveness_trace0`**
- search still running on gpu20 after 136h26m32s

<a id="minepump-liveness-trace2"></a>**`minepump_liveness_trace2`**
- search process gone while status.txt still reads `learning d1 (guarantee_weakening)` at 9m19s — died rather than finished

<a id="minepump-liveness-trace4"></a>**`minepump_liveness_trace4`**
- search process gone while status.txt still reads `verifying d4 candidate` at 122h26m55s — died rather than finished

<a id="pcar-trace0"></a>**`pcar_trace0`**
- search process gone while status.txt still reads `verifying d3 candidate` at 73h01m35s — died rather than finished
- an earlier attempt died rc=2 (`ltl2tgba` out of memory, pre-PREV-fix)

<a id="pcar-trace1"></a>**`pcar_trace1`**
- stage counts come from the old order (unique → strongest); same final set

<a id="pcar-trace2"></a>**`pcar_trace2`**
- search still running on gpu08 after 122h26m59s
- unique-from-final measured on a pool of 490, not today's 568 — the search kept writing after post-processing read it
- stage counts come from the old order (unique → strongest); same final set

<a id="pcar-trace3"></a>**`pcar_trace3`**
- search still running on gpu08 after 122h26m49s
- unique-from-final measured on a pool of 382, not today's 1315 — the search kept writing after post-processing read it
- stage counts come from the old order (unique → strongest); same final set

<a id="pcar-trace4"></a>**`pcar_trace4`**
- search still running on gpu20 after 133h11m25s
- an earlier attempt died rc=2 (`ltl2tgba` out of memory, pre-PREV-fix)

<a id="traffic-single-trace0"></a>**`traffic_single_trace0`**
- stage counts come from the old order (unique → strongest); same final set

<a id="traffic-single-trace1"></a>**`traffic_single_trace1`**
- search still running on gpu02 after 122h26m54s

<a id="traffic-single-trace2"></a>**`traffic_single_trace2`**
- stage counts come from the old order (unique → strongest); same final set

<a id="traffic-single-trace3"></a>**`traffic_single_trace3`**
- search still running on gpu12+gpu20 after 136h12m11s — **two processes on the same run dir**

<a id="traffic-single-trace4"></a>**`traffic_single_trace4`**
- stage counts come from the old order (unique → strongest); same final set

<a id="traffic-updated-trace0"></a>**`traffic_updated_trace0`**
- stage counts come from the old order (unique → strongest); same final set

<a id="traffic-updated-trace1"></a>**`traffic_updated_trace1`**
- stage counts come from the old order (unique → strongest); same final set

<a id="traffic-updated-trace2"></a>**`traffic_updated_trace2`**
- stage counts come from the old order (unique → strongest); same final set

<a id="traffic-updated-trace3"></a>**`traffic_updated_trace3`**
- stage counts come from the old order (unique → strongest); same final set

<a id="traffic-updated-trace4"></a>**`traffic_updated_trace4`**
- stage counts come from the old order (unique → strongest); same final set

## What is in flight at the time of the snapshot

| work | runs | where |
| --- | --- | --- |
| search (never stopped) | traffic_single 1/3, pcar 2/3/4, gyro 2/3, minepump 1/3, minepump_liveness 0, genbuf 3 | gpu02, gpu08, gpu12, gpu16, gpu19, gpu20 |
| main chain, merge outstanding | genbuf 0/2, minepump 1-4, minepump_liveness 0 | gpu07, gpu08, gpu14, gpu15, gpu17, gpu18, gpu20 |
| unique-from-final | 28 runs, six queues, largest pool first | gpu01, gpu02, gpu06, gpu09, gpu16, gpu19 |
| trivial solutions (MARCO) | genbuf 0/1/3/4 | gpu13, gpu04, gpu10, gpu05 |
| asm_merge | all 47 with results | not started - queued behind unique-from-final |

## Reproducing the two side-branches

    # the paper's unique count, off the raw pool
    python scripts/filter_then_merge.py <run_dir> --unique-only --workers 3
    #   -> <run_dir>/unique_from_final_specs/

    # every repair's assumptions, conjoined
    python scripts/merge_assumptions.py <run_dir>

    # trivial solutions where exploreAllCores does not finish
    python scripts/generate_trivial_solutions.py 2026-08-13 --setup case_study_3 \
        --case-study genbuf --trace 0 --marco
