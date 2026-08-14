# What each case_study_3 trace violates

Generated 2026-08-14 by `scripts/report_trace_violations.py`. Regenerate it whenever the traces change - it is derived, not written by hand.

Taken from the repair machinery's own `get_spec_violations`, not from the `traces.json` manifest, so it reports what the search actually sees. A trace is built to break at least one assumption at its last step; guarantee violations are listed where they occur, since the system is released from its guarantees once the environment breaks its side.

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
