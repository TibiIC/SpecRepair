# Where the rerun stands

Report date: 2026-08-14. Follows
[2026-08-13](2026-08-13-what-is-actually-broken.md).

This is the starting point for today: every case_study_3 (specification, trace)
pair and what has happened to it. The sweeps launched at 21:57 and 21:58 last
night and are still running, so most of the table is still `queued` - that is
the point of writing it down now rather than at the end.

Both arms run **under CUDD**, with the counter-strategy expansion capped. Nothing
here is comparable with anything measured before 2026-08-13.

## Status of all 55 pairs, both learners

Read the codes as: **repaired** is exit 0, a run that finished and produced at
least one repaired specification; **no repair** is exit 1, a run that finished
and produced none, which is a result rather than a failure; **SIGTERM** is exit
143, the run being stopped by something outside itself.

| case study | trace | FastLAS (gpu20) | ILASP (gpu12) |
| --- | --- | --- | --- |
| **amba** | 0 | repaired, 12m40s | no repair, 14m17s |
| **amba** | 1 | repaired, 13m53s | no repair, 13m56s |
| **amba** | 2 | repaired, 12m53s | no repair, 13m55s |
| **amba** | 3 | repaired, 13m47s | no repair, 14m03s |
| **amba** | 4 | repaired, 11m22s | **repaired, 13m08s** |
| **genbuf** | 0 | queued | no repair, 10m27s |
| **genbuf** | 1 | queued | no repair, 10m44s |
| **genbuf** | 2 | repaired, 1m21s | **repaired, 10m08s** |
| **genbuf** | 3 | running, 13h30m | queued |
| **genbuf** | 4 | queued | no repair, 10m22s |
| **minepump** | 0 | queued | queued |
| **minepump** | 1 | queued | queued |
| **minepump** | 2 | queued | queued |
| **minepump** | 3 | queued | queued |
| **minepump** | 4 | queued | queued |
| colorsort | 0 | **SIGTERM**, at 28.5GB | queued |
| colorsort | 1 | queued | queued |
| colorsort | 2 | queued | no repair, 10m57s |
| colorsort | 3 | queued | queued |
| colorsort | 4 | queued | queued |
| elevator | 0 | queued | queued |
| elevator | 1 | repaired, 21.7s | queued |
| elevator | 2 | repaired, 15.8s | queued |
| elevator | 3 | queued | queued |
| elevator | 4 | queued | queued |
| gyro | 0 | queued | running, 13h09m |
| gyro | 1 | queued | queued |
| gyro | 2 | queued | running, 2h23m |
| gyro | 3 | queued | queued |
| gyro | 4 | queued | queued |
| lift | 0 | queued | repaired, 25.6s |
| lift | 1-4 | queued | queued |
| minepump_liveness | 0 | running, 13h32m | repaired, 5h01m |
| minepump_liveness | 1 | queued | queued |
| minepump_liveness | 2 | no repair, 9m21s | no repair, 6m00s |
| minepump_liveness | 3 | queued | queued |
| minepump_liveness | 4 | queued | repaired, 5h32m |
| pcar | 0 | queued | running, 13h17m |
| pcar | 1 | queued | repaired, 16.8s |
| pcar | 2 | queued | queued |
| pcar | 3 | queued | queued |
| pcar | 4 | running, 10h17m | queued |
| traffic_single | 0 | repaired, 17.1s | queued |
| traffic_single | 1 | queued | queued |
| traffic_single | 2 | queued | queued |
| traffic_single | 3 | running, 13h18m | running, 13h17m |
| traffic_single | 4 | queued | queued |
| traffic_updated | 0 | queued | queued |
| traffic_updated | 1 | queued | queued |
| traffic_updated | 2 | queued | repaired, 7.8s |
| traffic_updated | 3 | queued | repaired, 13.6s |
| traffic_updated | 4 | queued | queued |

Totals: **FastLAS 11 of 55 finished**, 4 running. **ILASP 17 of 55 finished**,
4 running. Four concurrent per box, so the rest are waiting on a slot rather
than on anything being wrong.

## What the finished rows already say

**genbuf completes.** It had never finished once, on any machine, under either
learner - it was OOM-killed every time. Five of its ten runs are in, at around
ten minutes each. Both fixes were needed: the counter-trace cap for the 53GB,
CUDD for the JTLV thrash.

**ILASP repairs amba.** [results/case-study-3-amba.md](../results/case-study-3-amba.md)
records ILASP at 0/5 for amba at both 600s and 3600s. Under CUDD `amba_4` comes
back exit 0. Those earlier runs were dying rather than failing to learn, so that
finding does not survive and the file needs rewriting from this data.

**The learners differ, but not the way it was written up.** On amba FastLAS
repairs all five and ILASP one of five; on genbuf both repair trace 2 and
neither repairs the others so far. "ILASP cannot repair these two at a practical
budget" was measuring the crash, not the learner.

**Run times are bimodal.** Most finish in seconds or ten-ish minutes;
`minepump_liveness` takes five hours on ILASP and four runs have passed thirteen
on FastLAS. Long is expected here and is not itself evidence of a fault.

## Open, and unchanged from last night

* **`exploreAllCores` does not return on genbuf.** `genbuf_3` on FastLAS is
  13h30m inside `Checker$Memoize.seek`; genbuf's trivial solutions are 13h13m
  into the same call. Sibling genbuf traces cleared it in minutes. This is what
  blocks genbuf's graphs, since it is the trivial solutions that are stuck.

  **It must not be bounded.** A time budget returns a silently smaller core set,
  which is indistinguishable from a complete one and breaks the hitting-set
  argument the trivial solution algorithm is proven on - a wrong trivial
  solution is a wrong floor under every graph drawn against it. The tool's known
  defect (it returns neither all cores nor only minimal ones) is already
  accounted for by the recheck loop in
  `get_all_trivial_solutions_guarantee_only`; truncation is a different and
  unrecoverable failure. The options are to wait, to run it elsewhere, or to
  report genbuf without graphs. Reducing the *number* of calls is fair game -
  that is what the core cache does - since it changes no answer.
* **colorsort died on SIGTERM at 28.5GB.** Exit 143, not the kernel's 137, so
  the unexplained SIGTERM is still unexplained. The growth itself is steady with
  elapsed time, which is what CUDD's native uncapped BDD tables do - not the
  expansion bug, which is capped.
* **Trivial solutions: 50 of 55.** 146 specification files, no empty
  directories. genbuf is the missing five.

## What each trace violates, as first generated

Recorded here as the first generation of this table, on 2026-08-14. The living
copy is [results/case-study-3-trace-violations.md](../results/case-study-3-trace-violations.md),
regenerated by `scripts/report_trace_violations.py` whenever the traces change;
this copy is a log of what it said today and is deliberately not updated.

Derived from the repair machinery's own `get_spec_violations` rather than from
the `traces.json` manifest, so it reports what the search actually sees - and
guarantee violations along with the assumption ones.

| case study | trace | assumptions violated | guarantees violated |
| --- | --- | --- | --- |
| amba | 0 | `a30`, `hburst_mutual_exclusion` | `btq_state_4_mutual_exclusion` |
| amba | 1 | `a30`, `hburst_mutual_exclusion` | `btq_state_1_mutual_exclusion`, `btq_state_2_mutual_exclusion`, `btq_state_6_mutual_exclusion` |
| amba | 2 | `a30`, `hburst_mutual_exclusion` | `btq_state_4_mutual_exclusion` |
| amba | 3 | `a30`, `hburst_mutual_exclusion` | `btq_state_2_mutual_exclusion`, `btq_state_3_mutual_exclusion`, `btq_state_4_mutual_exclusion`, `btq_state_5_mutual_exclusion` |
| amba | 4 | `a30` | `btq_state_3_mutual_exclusion`, `btq_state_5_mutual_exclusion`, `btq_state_6_mutual_exclusion` |
| colorsort | 0 | `color_mutual_exclusion_1`, `color_mutual_exclusion_10`, `color_mutual_exclusion_2`, `color_mutual_exclusion_3`, `color_mutual_exclusion_4`, `color_mutual_exclusion_5`, `color_mutual_exclusion_6`, `color_mutual_exclusion_7`, `color_mutual_exclusion_8`, `color_mutual_exclusion_9`, `detect_mutual_exclusion_1`, `detect_mutual_exclusion_10`, `detect_mutual_exclusion_2`, `detect_mutual_exclusion_3`, `detect_mutual_exclusion_4`, `detect_mutual_exclusion_5`, `detect_mutual_exclusion_6`, `detect_mutual_exclusion_7`, `detect_mutual_exclusion_8`, `detect_mutual_exclusion_9` | `after_the_bottom_motor_finished_moving_return_to_starting_stage`, `botMot_mutual_exclusion_1`, `if_the_speed_button_is_released_the_speed_remains_the_same`, `if_we_pause_this_means_no_motors_move_and_all_the_rest_of_the_stats_remain_the_same`, `unnamed_guarantee_6` |
| colorsort | 1 | `color_mutual_exclusion_1`, `color_mutual_exclusion_10`, `color_mutual_exclusion_2`, `color_mutual_exclusion_3`, `color_mutual_exclusion_4`, `color_mutual_exclusion_5`, `color_mutual_exclusion_6`, `color_mutual_exclusion_7`, `color_mutual_exclusion_8`, `color_mutual_exclusion_9`, `detect_mutual_exclusion_1`, `detect_mutual_exclusion_10`, `detect_mutual_exclusion_2`, `detect_mutual_exclusion_3`, `detect_mutual_exclusion_4`, `detect_mutual_exclusion_5`, `detect_mutual_exclusion_6`, `detect_mutual_exclusion_7`, `detect_mutual_exclusion_8`, `detect_mutual_exclusion_9` | `botMot_mutual_exclusion_1`, `if_the_speed_button_is_released_the_speed_remains_the_same`, `if_we_pause_this_means_no_motors_move_and_all_the_rest_of_the_stats_remain_the_same`, `reduce_the_number_of_cubes_left_to_soft_iff_a_cycle_has_been_finished`, `unnamed_guarantee_1`, `unnamed_guarantee_4`, `unnamed_guarantee_5` |
| colorsort | 2 | `color_mutual_exclusion_1`, `color_mutual_exclusion_10`, `color_mutual_exclusion_2`, `color_mutual_exclusion_3`, `color_mutual_exclusion_4`, `color_mutual_exclusion_5`, `color_mutual_exclusion_6`, `color_mutual_exclusion_7`, `color_mutual_exclusion_8`, `color_mutual_exclusion_9`, `detect_mutual_exclusion_1`, `detect_mutual_exclusion_10`, `detect_mutual_exclusion_2`, `detect_mutual_exclusion_3`, `detect_mutual_exclusion_4`, `detect_mutual_exclusion_5`, `detect_mutual_exclusion_6`, `detect_mutual_exclusion_7`, `detect_mutual_exclusion_8`, `detect_mutual_exclusion_9` | `if_the_speed_button_is_released_the_speed_remains_the_same`, `if_we_pause_this_means_no_motors_move_and_all_the_rest_of_the_stats_remain_the_same`, `unnamed_guarantee_1` |
| colorsort | 3 | `color_mutual_exclusion_1`, `color_mutual_exclusion_10`, `color_mutual_exclusion_2`, `color_mutual_exclusion_3`, `color_mutual_exclusion_4`, `color_mutual_exclusion_5`, `color_mutual_exclusion_6`, `color_mutual_exclusion_7`, `color_mutual_exclusion_8`, `color_mutual_exclusion_9`, `detect_mutual_exclusion_1`, `detect_mutual_exclusion_10`, `detect_mutual_exclusion_2`, `detect_mutual_exclusion_3`, `detect_mutual_exclusion_4`, `detect_mutual_exclusion_5`, `detect_mutual_exclusion_6`, `detect_mutual_exclusion_7`, `detect_mutual_exclusion_8`, `detect_mutual_exclusion_9` | `if_the_speed_button_is_released_the_speed_remains_the_same`, `if_we_pause_this_means_no_motors_move_and_all_the_rest_of_the_stats_remain_the_same`, `spec_allsleep_is_true_iff_all_motors_sleep`, `unnamed_guarantee_1` |
| colorsort | 4 | `color_mutual_exclusion_1`, `color_mutual_exclusion_10`, `color_mutual_exclusion_2`, `color_mutual_exclusion_3`, `color_mutual_exclusion_4`, `color_mutual_exclusion_5`, `color_mutual_exclusion_6`, `color_mutual_exclusion_7`, `color_mutual_exclusion_8`, `color_mutual_exclusion_9`, `detect_mutual_exclusion_1`, `detect_mutual_exclusion_10`, `detect_mutual_exclusion_2`, `detect_mutual_exclusion_3`, `detect_mutual_exclusion_4`, `detect_mutual_exclusion_5`, `detect_mutual_exclusion_6`, `detect_mutual_exclusion_7`, `detect_mutual_exclusion_8`, `detect_mutual_exclusion_9` | `if_the_speed_button_is_released_the_speed_remains_the_same`, `if_we_pause_this_means_no_motors_move_and_all_the_rest_of_the_stats_remain_the_same` |
| elevator | 0 | `floor_mutual_exclusion` | - |
| elevator | 1 | `stopped_implies_floor_known` | - |
| elevator | 2 | `floor_mutual_exclusion` | - |
| elevator | 3 | `stopped_implies_floor_known` | - |
| elevator | 4 | `floor_mutual_exclusion` | - |
| genbuf | 0 | `unnamed_assumption_10`, `unnamed_assumption_20`, `unnamed_assumption_26` | `unnamed_guarantee_60`, `unnamed_guarantee_65`, `unnamed_guarantee_68`, `unnamed_guarantee_70`, `unnamed_guarantee_75` |
| genbuf | 1 | `unnamed_assumption_12`, `unnamed_assumption_20` | `unnamed_guarantee_73` |
| genbuf | 2 | `unnamed_assumption_10`, `unnamed_assumption_12`, `unnamed_assumption_14`, `unnamed_assumption_16`, `unnamed_assumption_18` | - |
| genbuf | 3 | `unnamed_assumption_10`, `unnamed_assumption_13`, `unnamed_assumption_14`, `unnamed_assumption_16`, `unnamed_assumption_18`, `unnamed_assumption_22`, `unnamed_assumption_26` | `unnamed_guarantee_23`, `unnamed_guarantee_73` |
| genbuf | 4 | `unnamed_assumption_10`, `unnamed_assumption_13`, `unnamed_assumption_14`, `unnamed_assumption_20`, `unnamed_assumption_22` | `unnamed_guarantee_23`, `unnamed_guarantee_49`, `unnamed_guarantee_73` |
| gyro | 0 | `ready_stays_ready` | `not_ready_implies_stopped` |
| gyro | 1 | `ready_stays_ready` | `not_ready_implies_stopped` |
| gyro | 2 | `ready_stays_ready` | `not_ready_implies_stopped` |
| gyro | 3 | `ready_stays_ready` | `not_ready_implies_stopped` |
| gyro | 4 | `ready_stays_ready` | `not_ready_implies_stopped` |
| lift | 0 | `button1_off_at_floor1` | - |
| lift | 1 | `button2_stays_on` | `move_one_max1` |
| lift | 2 | `button1_stays_on`, `button3_stays_on` | `move_one_max2` |
| lift | 3 | `button2_stays_on`, `button3_stays_on` | `move_one_max1` |
| lift | 4 | `button1_stays_on` | `move_one_max2` |
| minepump | 0 | `assumption1_1` | - |
| minepump | 1 | `assumption2_1` | - |
| minepump | 2 | `assumption1_1`, `assumption2_1` | - |
| minepump | 3 | `assumption2_1` | - |
| minepump | 4 | `assumption1_1`, `assumption2_1` | - |
| minepump_liveness | 0 | `assumption1_1` | `guarantee4_1` |
| minepump_liveness | 1 | `assumption3_1` | `guarantee1_1` |
| minepump_liveness | 2 | `assumption1_1` | `guarantee2_1` |
| minepump_liveness | 3 | `assumption3_1` | `guarantee2_1` |
| minepump_liveness | 4 | `assumption1_1` | `guarantee4_1` |
| pcar | 0 | `obstacle_mutual_exclusion` | `unnamed_guarantee_1` |
| pcar | 1 | `sideSense_mutual_exclusion` | `throttle_mutual_exclusion` |
| pcar | 2 | `unnamed_assumption_1` | - |
| pcar | 3 | `unnamed_assumption_1` | - |
| pcar | 4 | `obstacle_mutual_exclusion` | - |
| traffic_single | 0 | `car_idle_when_red` | - |
| traffic_single | 1 | `car_moves_when_green` | - |
| traffic_single | 2 | `car_idle_when_red` | - |
| traffic_single | 3 | `car_moves_when_green` | - |
| traffic_single | 4 | `car_idle_when_red` | - |
| traffic_updated | 0 | `carA_idle_when_red` | `red_when_emergency` |
| traffic_updated | 1 | `carA_moves_when_green` | `red_when_emergency` |
| traffic_updated | 2 | `carB_idle_when_red` | - |
| traffic_updated | 3 | `carB_moves_when_green` | `red_when_emergency` |
| traffic_updated | 4 | `carA_idle_when_red` | `red_when_emergency` |

55 trace(s). **37** violate exactly one assumption, which are the ones that isolate a single weakening; the rest break several at once and so cover fewer distinct cases than their count suggests. **34** violate a guarantee as well.

Two things worth reading off it. **37 of 55 traces isolate a single assumption**,
and those are the ones that give a clean weakening; the rest break several at
once, so the corpus covers fewer distinct cases than 55 suggests - colorsort
breaks twenty assumptions in every trace, which is one case repeated five times.
And **34 traces violate a guarantee as well**, which is allowed - once the
environment breaks an assumption the system is released - but it means the
guarantee side is rarely clean either.
