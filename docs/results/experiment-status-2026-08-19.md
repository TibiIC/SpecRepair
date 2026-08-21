# Case study 3: every run, every pipeline stage

Snapshot taken 2026-08-19 15:00; **table re-verified against the machines
2026-08-21 09:00** and the changed cells rewritten. Experiment date `2026-08-13`,
learner `fastlas`, 55 runs (11 case studies x 5 traces). **48 have results** -
genbuf_trace1's re-run wrote its first specifications overnight, leaving
colorsort 0-4 and genbuf 3/4 with none.

The freshest reading is [Update 2026-08-21](#update-2026-08-21-morning), below
the genbuf section. In short: every main-chain merge is now finished, eight more
unique-from-final counts have landed, the pools they were measured on are still
growing - and the machine sweep this file was built from only covered gpu01-gpu20,
while **six live searches were sitting on gpu26, gpu27 and gpu29** the whole time.
Read that section before trusting any ❌ in the Search column.

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
| ★ | measured directly by the `unique_from_final` branch, exactly (no equivalence timeout). The pool it read is given in Details; for a run whose search never stopped that pool is smaller than the one on disk now |
| ↑ | the count is an upper bound: some equivalence checks timed out and were counted as *not* equivalent |

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
| `genbuf_trace0` | **3** · `unnamed_assumption_10`, `unnamed_assumption_20` +1 | ⏳ running on gpu26 | 1 | ✅ 2 | ⏳ queued | ✅ 2 | ✅ 2 ↑ | ✅ 1 | ⏳ queued | ⏳ running | — | [n](#genbuf-trace0) |
| `genbuf_trace1` | **2** · `unnamed_assumption_12`, `unnamed_assumption_20` | ⏳ re-run, verifying d0 n1 spec #2 | 3 | ✅ 2 | ⏳ queued | ⏳ queued | ⏳ queued | ⏳ queued | ⏳ queued | ⏳ running | — | [n](#genbuf-trace1) |
| `genbuf_trace2` | **5** · `unnamed_assumption_10`, `unnamed_assumption_12` +3 | ✅ done | — | ✅ 21 | ⏳ queued | ✅ 21 | ✅ 21 ↑ | ✅ 1 | ⏳ queued | ✅ 1 | — |  |
| `genbuf_trace3` | **7** · `unnamed_assumption_10`, `unnamed_assumption_13` +5 | ⏳ re-run, first verify 37h+ | — | ❌ 0 | ⏳ queued | — | — | — | — | ⏳ running | — | [n](#genbuf-trace3) |
| `genbuf_trace4` | **5** · `unnamed_assumption_10`, `unnamed_assumption_13` +3 | ⏳ re-run, second verify 32h+ | 1 | ❌ 0 | ⏳ queued | — | — | — | — | ⏳ running | — | [n](#genbuf-trace4) |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
| `gyro_trace0` | **1** · `ready_stays_ready` | ❌ stopped | 9 | ✅ 100 | ⏳ queued | ✅ 24 ‡ | ✅ 35 ‡ | ✅ 1 | ★ 36 | ✅ 3 | asm/gar/gr1 | [n](#gyro-trace0) |
| `gyro_trace1` | **1** · `ready_stays_ready` | ❌ stopped | 9 | ✅ 120 | ⏳ queued | ✅ 35 ‡ | ✅ 50 ‡ | ✅ 1 | ★ 53 | ✅ 3 | asm/gar/gr1 | [n](#gyro-trace1) |
| `gyro_trace2` | **1** · `ready_stays_ready` | ⏳ verifying d3 candidate | 9 | ✅ 111 | ⏳ queued | ✅ 28 ‡ | ✅ 36 ‡ | ✅ 1 | ★ 40 | ✅ 3 | asm/gar/gr1 | [n](#gyro-trace2) |
| `gyro_trace3` | **1** · `ready_stays_ready` | ⏳ verifying d3 candidate | 12 | ✅ 98 | ⏳ queued | ✅ 28 ‡ | ✅ 39 ‡ | ✅ 1 | ✅ 39 | ✅ 3 | asm/gar/gr1 | [n](#gyro-trace3) |
| `gyro_trace4` | **1** · `ready_stays_ready` | ❌ stopped | 16 | ✅ 143 | ⏳ queued | ✅ 32 ‡ | ✅ 42 ‡ | ✅ 1 | ★ 42 | ✅ 3 | asm/gar/gr1 | [n](#gyro-trace4) |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
| `lift_trace0` | **1** · `button1_off_at_floor1` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ *nr* | ✅ *nr* | ✅ 1 | ⏳ queued | ✅ 1 | asm/gar/gr1 |  |
| `lift_trace1` | **1** · `button2_stays_on` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ *nr* | ✅ *nr* | ✅ 1 | ⏳ queued | ✅ 1 | asm/gar/gr1 |  |
| `lift_trace2` | **2** · `button1_stays_on`, `button3_stays_on` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ *nr* | ✅ *nr* | ✅ 1 | ⏳ queued | ✅ 1 | asm/gar/gr1 |  |
| `lift_trace3` | **2** · `button2_stays_on`, `button3_stays_on` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ *nr* | ✅ *nr* | ✅ 1 | ⏳ queued | ✅ 1 | asm/gar/gr1 |  |
| `lift_trace4` | **1** · `button1_stays_on` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ *nr* | ✅ *nr* | ✅ 1 | ⏳ queued | ✅ 1 | asm/gar/gr1 |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
| `minepump_trace0` | **1** · `assumption1_1` | ✅ done | — | ✅ 17 | ⏳ queued | ✅ 11 ‡ | ✅ 11 ‡ | ✅ 1 | ✅ 11 | ✅ 1 | asm/gar/gr1 | [n](#minepump-trace0) |
| `minepump_trace1` | **1** · `assumption2_1` | ⏳ verifying d5 candidate | 12247 | ✅ 26877 | ⏳ queued | ✅ 296 | ✅ 54 | ✅ 50 | ⏳ queued | ✅ 2 | — | [n](#minepump-trace1) |
| `minepump_trace2` | **2** · `assumption1_1`, `assumption2_1` | ❌ stopped | 11608 | ✅ 23598 | ⏳ queued | ✅ 94 | ✅ 36 | ✅ 35 | ⏳ queued | ✅ 2 | — | [n](#minepump-trace2) |
| `minepump_trace3` | **1** · `assumption2_1` | ⏳ learning d4 (guarantee_weakening) | 9864 | ✅ 23201 | ⏳ queued | ✅ 120 | ✅ 45 | ✅ 40 | ⏳ queued | ✅ 2 | — | [n](#minepump-trace3) |
| `minepump_trace4` | **2** · `assumption1_1`, `assumption2_1` | ❌ stopped | 11136 | ✅ 27589 | ⏳ queued | ✅ 178 | ✅ 50 | ✅ 48 | ⏳ queued | ✅ 2 | — | [n](#minepump-trace4) |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
| `minepump_liveness_trace0` | **1** · `assumption1_1` | ⏳ learning d4 (guarantee_weakening) | 737 | ✅ 18542 | ⏳ queued | ✅ 21 | ✅ 9 | ✅ 1 | ⏳ queued | ✅ 2 | — | [n](#minepump-liveness-trace0) |
| `minepump_liveness_trace1` | **1** · `assumption3_1` | ✅ done | — | ✅ 17 | ⏳ queued | ✅ 17 | ✅ 13 | ✅ 1 | ⏳ queued | ✅ 1 | asm/gar/gr1 |  |
| `minepump_liveness_trace2` | **1** · `assumption1_1` | ❌ stopped | 31 | ✅ 151 | ⏳ queued | ✅ *nr* | ✅ *nr* | ✅ 1 | ⏳ queued | ✅ 2 | asm/gar/gr1 | [n](#minepump-liveness-trace2) |
| `minepump_liveness_trace3` | **1** · `assumption3_1` | ✅ done | — | ✅ 19 | ⏳ queued | ✅ 19 | ✅ 12 | ✅ 1 | ⏳ queued | ✅ 1 | asm/gar/gr1 |  |
| `minepump_liveness_trace4` | **1** · `assumption1_1` | ⏳ running on gpu27, d5 | 983 | ✅ 21135 | ⏳ queued | ✅ 19 | ✅ 7 | ✅ 1 | ⏳ queued | ✅ 2 | — | [n](#minepump-liveness-trace4) |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
| `pcar_trace0` | **1** · `obstacle_mutual_exclusion` | ❌ stopped | 73 | ✅ 764 | ⏳ queued | ✅ *nr* | ✅ *nr* | ✅ 1 | ★ 161 | ✅ 2 | asm/gar/gr1 | [n](#pcar-trace0) |
| `pcar_trace1` | **1** · `sideSense_mutual_exclusion` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ 17 ‡ | ✅ 17 ‡ | ✅ 1 | ✅ 17 | ✅ 1 | asm/gar/gr1 | [n](#pcar-trace1) |
| `pcar_trace2` | **1** · `unnamed_assumption_1` | ⏳ verifying d3 candidate | 78 | ✅ 568 | ⏳ queued | ✅ 75 ‡ | ✅ 86 ‡ | ✅ 1 | ✅ 86 | ✅ 2 | asm/gar/gr1 | [n](#pcar-trace2) |
| `pcar_trace3` | **1** · `unnamed_assumption_1` | ⏳ verifying d3 candidate | 569 | ✅ 1315 | ⏳ queued | ✅ 71 ‡ | ✅ 152 ‡ | ✅ 1 | ★ 609 | ✅ 2 | asm/gar/gr1 | [n](#pcar-trace3) |
| `pcar_trace4` | **1** · `obstacle_mutual_exclusion` | ⏳ learning d2 (assumption_weakening) | 92 | ✅ 940 | ⏳ queued | ✅ *nr* | ✅ *nr* | ✅ 1 | ★ 98 | ✅ 2 | asm/gar/gr1 | [n](#pcar-trace4) |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
| `traffic_single_trace0` | **1** · `car_idle_when_red` | ✅ done | — | ✅ 19 | ⏳ queued | ✅ 7 ‡ | ✅ 7 ‡ | ✅ 1 | ✅ 7 | ✅ 1 | asm/gar/gr1 | [n](#traffic-single-trace0) |
| `traffic_single_trace1` | **1** · `car_moves_when_green` | ⏳ verifying d6 candidate | 5003 | ✅ 35640 | ⏳ queued | ✅ 2 | ✅ 2 | ✅ 1 | ⏳ queued | ✅ 1 | — | [n](#traffic-single-trace1) |
| `traffic_single_trace2` | **1** · `car_idle_when_red` | ✅ done | — | ✅ 19 | ⏳ queued | ✅ 7 ‡ | ✅ 7 ‡ | ✅ 1 | ✅ 7 | ✅ 1 | asm/gar/gr1 | [n](#traffic-single-trace2) |
| `traffic_single_trace3` | **1** · `car_moves_when_green` | ⏳ verifying d5 candidate | 839 | ✅ 3395 | ⏳ queued | ✅ 3 | ✅ 3 | ✅ 1 | ★ 802 | ✅ 1 | asm/gar/gr1 | [n](#traffic-single-trace3) |
| `traffic_single_trace4` | **1** · `car_idle_when_red` | ✅ done | — | ✅ 19 | ⏳ queued | ✅ 7 ‡ | ✅ 7 ‡ | ✅ 1 | ✅ 7 | ✅ 1 | asm/gar/gr1 | [n](#traffic-single-trace4) |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
| `traffic_updated_trace0` | **1** · `carA_idle_when_red` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ 10 ‡ | ✅ 10 ‡ | ✅ 1 | ✅ 10 | ✅ 1 | asm/gar/gr1 | [n](#traffic-updated-trace0) |
| `traffic_updated_trace1` | **1** · `carA_moves_when_green` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ 12 ‡ | ✅ 12 ‡ | ✅ 1 | ✅ 12 | ✅ 1 | asm/gar/gr1 | [n](#traffic-updated-trace1) |
| `traffic_updated_trace2` | **1** · `carB_idle_when_red` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ 10 ‡ | ✅ 10 ‡ | ✅ 1 | ✅ 10 | ✅ 1 | asm/gar/gr1 | [n](#traffic-updated-trace2) |
| `traffic_updated_trace3` | **1** · `carB_moves_when_green` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ 11 ‡ | ✅ 11 ‡ | ✅ 1 | ✅ 11 | ✅ 1 | asm/gar/gr1 | [n](#traffic-updated-trace3) |
| `traffic_updated_trace4` | **1** · `carA_idle_when_red` | ✅ done | — | ✅ 21 | ⏳ queued | ✅ 10 ‡ | ✅ 10 ‡ | ✅ 1 | ✅ 10 | ✅ 1 | asm/gar/gr1 | [n](#traffic-updated-trace4) |

## Where the 55 stand, stage by stage

Counted from the table above as it stands on 2026-08-21 09:00.

| stage | passed | in progress | crashed / none | n/a |
| --- | --- | --- | --- | --- |
| search | 30 | 15 | 10 | — |
| final specs | 48 | — | 7 | — |
| asm_merge | 0 | 55 queued | — | — |
| strongest_gar | 47 | 1 | — | 7 |
| unique (chain) | 47 | 1 | — | 7 |
| merged | 47 | 1 | — | 7 |
| unique-from-final | 22 | 26 | — | 7 |
| trivial solutions | 51 | 4 | — | — |

**No main-chain merge is outstanding any more.** The seven that were running on
2026-08-19 - genbuf 0 and 2, minepump 1-4, minepump_liveness 0 - all finished
between 08-20 05:23 and 08-20 17:32. The single remaining ⏳ in those three
columns is genbuf_trace1, whose re-run produced its first final specifications
overnight and has not been post-processed yet.

Fifteen searches are running rather than eleven: the genbuf 1 and 4 MARCO re-runs
join the eleven that never stopped, plus genbuf_trace0 and
minepump_liveness_trace4, both found alive on gpu26/gpu27 by the wider sweep and
both previously marked ❌. The ten still marked ❌ are dead processes whose
`status.txt` reads mid-verification - and given that the gpu01-gpu20 sweep missed
six live jobs, treat that ten as an upper bound until gpu22 and gpu28 answer.

Of the 26 outstanding unique-from-final measurements, six are on a machine now
(gpu01/02/06/09/16/19) and the rest are queued behind them; four more (minepump
1-4) run separately on eight workers each. Of the 22 reported, 8 were measured
exactly by the dedicated branch (marked ★) and 14 are old-order numbers that the
branch has not reached yet.

<a id="bugs"></a>

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

**Post-processing read pools that were still being written.** Eleven searches had
never stopped when this was written (thirteen now, with the genbuf re-runs), so
`filter_then_merge` sampled a moving target. `pcar_trace3` was filtered at 382
final specs, held 1,315 on 08-19 and holds **2,104** on 08-21; `pcar_trace2` at
490, now 599; `gyro_trace0` at 97, now 100. Their merged output is correct for the
pool as it was read, and is not a result over the pool as it now stands. The
2026-08-21 update below tabulates how far each of these has drifted.

**A dead search is indistinguishable from a live one on disk.** `status.txt` is
only ever advanced by the process itself, so a killed run keeps its last phase
forever. Fourteen runs read `verifying dN candidate` with no process behind them (twelve
as of 08-21, since genbuf 1 and 4 are genuinely running again); telling those
apart from the ones genuinely running needed a `ps` sweep across twenty machines,
not anything in the run directory. `genbuf_trace1` shows the converse failure:
its `status.txt` says `0 final, 0 intermediate` while it has written 2 and 3.

**Fixed today, listed because the table still carries their marks.**
`exploreAllCores`'s quadratic memoisation, which is why genbuf had no trivial
solutions for five days (now MARCO); the `PREV` shift doubling at every conjunction,
which turned one `PREV` into 59,010 `X` operators and killed ten merges on memory
(`362547c`); and `SpecificationNotVerifiableException` reporting neither of the two
conditions it covers (`6e4df2a`), which is why colorsort's failures are still
uncharacterised.

## Why genbuf 1, 3 and 4 produced nothing

All three stop in the same place - `verifying d1 candidate`, depth 0, node 1,
the *first* candidate - after 122h, 142h and 122h. Each learns its 21 candidates
in about a minute and then never returns from the first verification.

A stack dump of the one still alive on 2026-08-19 (trace 3, gpu20) names the
cause outright:

    "main" ... cpu=489246243.18ms      <- 136 hours of CPU
      at tau.smlab.syntech.cores.util.Checker$Memoize.isSubset(Checker.java:142)
      at tau.smlab.syntech.cores.util.Checker$Memoize.lookupPos(Checker.java:88)
      ... AllCoresPunchAlgorithm.computeCoresWithBase x24
      at cores.SpectraToolbox.exploreAllCores(SpectraToolbox.java:53)

Verification reaches `exploreAllCores` through `filter_counter_traces` ->
`get_unrealisable_core_expression_names`, and on genbuf's 81 guarantees its
quadratic memoisation never finishes. This is the same failure that kept genbuf
from having trivial solutions, in a different call site.

The cost is not the realisability oracle. Measured on genbuf: the full guarantee
set answers in 2.8s, a subset of 80 in 0.2s, a subset of 40 in 0.1s. The
algorithm is rescanning its own cache, not computing.

`SPEC_REPAIR_MARCO_CORES=1` switches that call to our MARCO enumeration. It is
opt-in: MARCO returns every core and each one minimal, which is a *larger* union
than Syntech's incomplete answer, so more counter-traces survive the filter and
the results are not identical to the 47 runs already finished. Where Syntech's
does terminate the two agree - checked on gyro, same three names.

Re-run with the flag on 2026-08-19, into the original directories
(`SPEC_REPAIR_RUN_DATE=2026-08-13`, `n_runs=10`):

| | before | after |
| --- | --- | --- |
| learn 21 candidates | 31.8s | 31.8s |
| verify candidate #1 | never returned in 122h | ~14s |
| first solution | none in five days | `SOLVED leaf #0` at 45.7s |

Traces 1 and 4 are re-running. Trace 3 cannot be, until its 142-hour process is
killed - starting a second run against a live directory is the collision
recorded under Bugs, not a fix for it.

### What the re-runs found next

The wall is gone and a second one is behind it. Five hours in:

| run | elapsed | final specs | where the JVM is |
| --- | --- | --- | --- |
| genbuf_trace1 | 5h11m | 1 | `CUDDFactory.gr1Game0` |
| genbuf_trace3 | 53m | 0 | `CUDDFactory.initialize0` |
| genbuf_trace4 | 5h11m | 0 | `CUDDFactory.gr1Game0` |

Trace 1 cleared the verification that had blocked it for 122 hours and wrote a
specification, so the diagnosis holds. But traces 1 and 4 have each since spent
over four hours inside a *single* BDD realisability game. The cost did not
disappear; it moved out of Syntech's memoisation and into genuinely hard
`gr1Game` calls on the guarantee subsets the enumeration probes.

This also corrects a measurement recorded above. The 2.8s / 0.2s / 0.1s figures
were taken on guarantee subsets of the *original* specification, and were read at
the time as showing that per-call cost was not a factor. They do not generalise:
the subsets reached while verifying a weakened candidate are far more expensive,
and some of them do not finish in hours. The claim held for what was sampled,
not for what the enumeration actually asks.

The runs are being left to run untouched rather than bounded. Note for anyone
reaching for a cap: the standing rule against truncating a core set was proven
for the trivial-solution path, where a hitting set of the cores must realise the
specification. It does not transfer to this call site, where the only use is
testing whether the violated guarantees lie in the union - and an incomplete
union is exactly what `exploreAllCores` gave all 47 finished runs.

Count with results, colorsort excluded: **48 of 50**.

**Update 2026-08-20.** genbuf traces 0 and 2 are now merged - trace 0 in 21
minutes once the equivalence check was bounded, trace 2 at 17:32 with all 210 of
its equivalence checks timing out, so its unique count of 21 is an upper bound
that establishes nothing while its merge of 1 is real. All five minepump traces
are merged. 47 of 55 runs now have a corrected merge; the 8 without are
colorsort 0-4 and genbuf 1/3/4, and the genbuf three are re-running. See
[the 2026-08-20 session notes](../session-notes/2026-08-20-the-walls-behind-the-wall.md)
and [what is still running](running-state-2026-08-20.md).

Worth recording, because it is not obvious: MARCO is fast *here* and slow in the
trivial-solution path, which was still enumerating after 2.5 hours on the same
case study. Per-call cost is identical; what differs is the number of cores. The
oracle asks about a specification that is barely unrealisable, so there are few
cores; the trivial-solution path asks after stripping the violated assumptions,
which leaves many.

<a id="update-2026-08-21-morning"></a>

## Update 2026-08-21, 09:00

Read off the machines this morning, not carried forward from yesterday.

### The sweep was looking at the wrong twenty machines

Everything in this file, and in `running-state-2026-08-20.md`, was built from a
`ps` sweep of gpu01-gpu20. **There are jobs on gpu26, gpu27 and gpu29**, launched
2026-08-14 12:08 by a `dist_fastlas_gpu<NN>_2026-08-14_120842` launcher, that no
sweep has ever seen. Six searches, all alive for 6d21h:

| box | searches |
| --- | --- |
| gpu26 | `genbuf_0`, `genbuf_1` |
| gpu27 | `genbuf_4`, `traffic_single_1`, `minepump_liveness_4` |
| gpu29 | `pcar_3` |

gpu22 and gpu28 refuse ssh (`connection reset`) and remain unchecked, so this
list is a lower bound.

Two consequences, both of which change entries in the table above.

**`minepump_liveness_trace4`'s search never stopped.** It is marked ❌ throughout
this file. It is on gpu27, 165h08m in, at depth 4, node 7,524 of a 30,423-node
queue, and it wrote 195 specifications in the hour before this snapshot. Its
`final_specs/` has gone 21,135 → 24,774 and is still climbing. The merge recorded
for it on 08-19 read a pool that no longer exists.

**Five runs have two search processes writing one directory, not one.** The
no-lock bug under [Bugs](#bugs) is five times worse than recorded:

| run | process A | process B |
| --- | --- | --- |
| `traffic_single_trace3` | gpu12 | gpu20 |
| `traffic_single_trace1` | gpu02 | gpu27 |
| `pcar_trace3` | gpu08 | gpu29 |
| `genbuf_trace1` | gpu03 (MARCO re-run) | gpu26 (original) |
| `genbuf_trace4` | gpu13 (MARCO re-run) | gpu27 (original) |

The last two are the ones to worry about, because the MARCO re-runs were started
*into the original directories* on the understanding that the original processes
were dead. They are not. `genbuf_trace3` is clean - its original was killed before
its re-run started, which is exactly the precaution the other two skipped.

For `genbuf_trace1` the attribution still holds: the gpu26 process's log is 190
bytes and has not been written since 2026-08-14 12:10, so it is wedged in
`exploreAllCores` producing nothing, and the 2 final specifications are the MARCO
re-run's. That is an argument from the log, not from the filesystem, and it is the
best available - nothing in the run directory records which process wrote a file.
It also explains the `status.txt` inconsistency noted below: two processes share
one status file.

`genbuf_trace0` is likewise still searching on gpu26, so its merge of 1 - reported
below as finished - was taken over a pool of 2 that may yet grow.

**Every main-chain merge has finished.** The seven outstanding on 2026-08-19 all
completed, the last at 17:32 on 08-20:

| run | final pool read | strongest_gar | unique | merged |
| --- | --- | --- | --- | --- |
| `minepump_trace1` | 26,877 | 296 | 54 | **50** |
| `minepump_trace2` | 23,598 | 94 | 36 | **35** |
| `minepump_trace3` | 23,201 | 120 | 45 | **40** |
| `minepump_trace4` | 27,589 | 178 | 50 | **48** |
| `minepump_liveness_trace0` | 18,134 | 21 | 9 | **1** |
| `genbuf_trace0` | 2 | 2 | 2 ↑ | **1** |
| `genbuf_trace2` | 21 | 21 | 21 ↑ | **1** |

The two genbuf uniques carry the equivalence timeout: trace 0 had 1 check time
out, trace 2 had **all 210**, so its "21 unique" is the input count restated and
establishes nothing. Both merges of 1 are real. The minepump merged counts are
upper bounds for the usual reason - `merge_solutions` does not test all pairs.

**Eight unique-from-final measurements landed overnight**, all exact (no
equivalence timeout), marked ★ in the table:

| run | pool it read | unique | previously reported |
| --- | --- | --- | --- |
| `gyro_trace0` | 100 | 36 | 35 |
| `gyro_trace1` | 120 | 53 | 50 |
| `gyro_trace2` | 111 | 40 | 36 |
| `gyro_trace4` | 143 | 42 | 42 |
| `pcar_trace0` | 764 | 161 | not measured |
| `pcar_trace3` | 1,865 | **609** | 152 |
| `pcar_trace4` | 1,008 | 98 | not measured |
| `traffic_single_trace3` | 3,502 | **802** | not measured |

`pcar_trace3` is the one to look at. The 152 in the table came from the old-order
post-processing, which read the pool at 1,315 specifications; the exact
measurement read 1,865 and found 609. That is not a correction to an equivalence
check - it is a different pool. The gyro deltas (35→36, 50→53, 36→40) are on
pools of the same size and are genuine measurement differences.

**The pools are still moving, and faster than when this was first written.**
Compared against the 2026-08-19 15:00 snapshot at the top of this file:

| run | final specs on 08-19 | on 08-21 09:00 |
| --- | --- | --- |
| `traffic_single_trace1` | 35,640 | 43,796 |
| `traffic_single_trace3` | 3,395 | 3,569 |
| `minepump_liveness_trace0` | 18,542 | 24,475 |
| `minepump_liveness_trace4` | 21,135 | 24,689 |
| `pcar_trace3` | 1,315 | 2,104 |
| `pcar_trace4` | 940 | 1,049 |
| `pcar_trace2` | 568 | 599 |

Measured directly, the drift is fast. Files written into `final_specs/` in the
hour and the day before this snapshot:

| run | last 60 min | last 24 h |
| --- | --- | --- |
| `minepump_liveness_trace0` | 221 | 3,106 |
| `minepump_liveness_trace4` | 195 | 3,336 |
| `pcar_trace2` | 0 | 147 |

Read those as *files touched*, not specifications added - the searches rewrite
existing files as well as appending new ones, so the two differ. `pcar_trace2` is
the clearest case: 147 files touched in 24h, but its pool moved only 568 → 599,
and its most recent write is `spec_12.spectra`, a re-write of an early file rather
than a new one.

Net growth over the 42h since the 08-19 snapshot is the number to use:
`minepump_liveness_trace0` +5,933 (~3,400/day) and `minepump_liveness_trace4`
+3,554 (~2,000/day). Their merges - taken on 08-19 over 18,134 and ~21,000 - are
already six thousand and three-and-a-half thousand specifications behind
respectively, and fall further each day.

Every count in this file for those runs is a reading of a pool that has since
grown, `traffic_single_trace3`'s from two search processes at once. The minepump
1-4 pools have not moved since 08-19 - their searches are alive but stuck in
verification - so their merges above are over the complete pool.

**The four minepump unique-from-final jobs will not finish this week.** Restarted
on eight workers at 18:05 on 08-20, after 14h45m:

| run | compared | kept | pool |
| --- | --- | --- | --- |
| `minepump_trace1` | 3,954 | 716 | 26,877 |
| `minepump_trace2` | 4,532 | 600 | 23,598 |
| `minepump_trace3` | 2,565 | 629 | 23,201 |
| `minepump_trace4` | 3,656 | 658 | 27,589 |

That is roughly 15% of the pool in 15 hours, and the per-item cost rises as the
kept set grows, so the linear projection of four more days is the optimistic one.
These are deliberately run without an equivalence timeout, so they are exact or
they are nothing - there is no partial answer to report from them.

**The genbuf re-runs have hit a third wall.** All three are alive; none has the
14-second verification the first measurement promised:

| run | box | elapsed | final | where it is |
| --- | --- | --- | --- | --- |
| `genbuf_trace1` | gpu03 | 42h | **2** | d0 n1, verifying candidate #2 of 21 |
| `genbuf_trace3` | gpu11 | 37h42m | 0 | d0 n1, still inside its *first* verification |
| `genbuf_trace4` | gpu13 | 42h | 0 | d0 n1, second verification, 32h36m so far |

Trace 1 is the one that works, and it shows the shape of the cost: its two
completed verifications took 2h51m and 3h01m, each returning ~980
counter-examples, and it has written 2 final specifications and 3 intermediates.
At three hours a candidate, its 21 candidates at this one node are alone a
sixty-hour job. Trace 4 got one verification back in 9h22m and its second has now
been running three and a half times that. Trace 3 has never had one back at all.

The 14s figure recorded above was therefore a single fast candidate, not the
per-verify cost. The honest statement is that the MARCO flag turned a search that
never produced anything into one that produces something slowly: **genbuf_trace1
now has results where it had none**, which takes the count with results to 48 of
55 (49 of 50 excluding colorsort), and traces 3 and 4 remain at zero.

One inconsistency worth flagging rather than papering over: `genbuf_trace1`'s
`status.txt` reports `0 final, 0 intermediate` while its directory holds 2 and 3.
That counter is not tracking what the run writes - trust the directory.

**gpu07 is now free** - the genbuf_trace2 merge that held it has finished. It is
the only idle box of the twenty.

**`asm_merge` has still not been run on anything.**

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

Re-swept 2026-08-21 09:00, across gpu01-gpu30 rather than gpu01-gpu20. gpu07 is
idle; gpu21/23/24/25/30 are idle; gpu22 and gpu28 could not be reached.

| work | runs | where |
| --- | --- | --- |
| search (never stopped) | traffic_single 1/3, pcar 2/3/4, gyro 2/3, minepump 1/3, minepump_liveness 0/4 | gpu02, gpu08, gpu12, gpu16, gpu19, gpu20 |
| search (genbuf MARCO re-runs) | genbuf 1/3/4 | gpu03, gpu11, gpu13 |
| search (never swept until 08-21) | genbuf 0/1/4, traffic_single 1, pcar 3, minepump_liveness 4 | gpu26, gpu27, gpu29 |
| unknown | gpu22 and gpu28 refuse ssh | — |
| main chain, merge outstanding | none - all seven finished by 08-20 17:32 | — |
| unique-from-final, minepump | minepump 1-4, 8 workers each, exact | gpu15, gpu17, gpu18, gpu14 |
| unique-from-final, six queues | amba 1/2/3/4 now; minepump_liveness 4 and traffic_single 1 still on their first job since 08-19 | gpu06, gpu16, gpu02, gpu19, gpu01, gpu09 |
| trivial solutions (MARCO) | genbuf 0/1/3/4, silent since 08-19 12:20 | gpu13, gpu04, gpu10, gpu05 |
| asm_merge | all 48 with results | not started - queued behind unique-from-final |
| orphans to kill deliberately | `generate_trivial_solutions` 2026-08-12 and 2026-08-13, the pre-MARCO `exploreAllCores` runs, 7 days each | gpu03, gpu06 |

The four amba unique-from-final jobs are worth watching: each has only 21 final
specifications and they have been running 7-15 hours without printing a single
comparison line. On this case study one equivalence check can hold a machine for
a day, which is the failure `0e5b2c1` bounded elsewhere; these queues run
unbounded on purpose.

## Reproducing the two side-branches

    # the paper's unique count, off the raw pool
    python scripts/filter_then_merge.py <run_dir> --unique-only --workers 3
    #   -> <run_dir>/unique_from_final_specs/

    # every repair's assumptions, conjoined
    python scripts/merge_assumptions.py <run_dir>

    # trivial solutions where exploreAllCores does not finish
    python scripts/generate_trivial_solutions.py 2026-08-13 --setup case_study_3 \
        --case-study genbuf --trace 0 --marco
