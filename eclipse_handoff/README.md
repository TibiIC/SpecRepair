# Eclipse hand-off

One folder per case study. In each: `original.spectra` to synthesise,
and per trace a step table plus the bare environment inputs.

| case study | traces | env vars | sys vars |
| --- | --- | --- | --- |
| amba | 0 | hburst_burst4, hburst_single, hbusreq_0, hbusreq_1, hbusreq_2, hlock_0, hlock_1, hlock_2, hready | btq_state_1_s0, btq_state_1_s1, btq_state_2_s0, btq_state_2_s1, btq_state_3_s0, btq_state_3_s1, btq_state_4_s0, btq_state_4_s1, btq_state_5_s0, btq_state_5_s1, btq_state_6_s0, btq_state_6_s1, decide, hgrant_0, hgrant_1, hgrant_2, hmaster_val0, hmaster_val1, hmastlock, hready_counter_val0, hready_counter_val1, hready_counter_val2, hready_counter_val3, locked, start |
| arbiter | 0 | a, r1, r2 | g1, g2 |
| colorsort | 0 | color_red, color_green, color_blue, color_black, color_yellow, detect_red, detect_green, detect_blue, detect_black, detect_yellow, ack_ver_hor_move, ack_bot_move, atEdge_noedge, num_of_cubes_zero, haltButton_press, speedButton_press | spec_allsleep, spec_finished_cycle, spec_speedButtonValidPressed, spec_haltButtonValidPressed, verMot_move, horMot_move, botMot_right, botMot_left, botMot_stop, motSpeed_level1, motSpeed_level2, reduce_num_of_cubes_reduce, spec_currentColor_red, spec_currentColor_green, spec_currentColor_blue, spec_currentColor_black, spec_currentColor_yellow, spec_stage_wait, spec_stage_kick, spec_stage_toangleright, spec_stage_toangleleft, spec_stage_drop, spec_pausing_pause |
| elevator | 0 | floor_lower, floor_middle, floor_upper | elevMot_fwd, elevMot_bwd |
| genbuf | 5 | eMPTY, fULL, rtoB_ACK0, rtoB_ACK1, stoB_REQ0, stoB_REQ1, stoB_REQ2, stoB_REQ3, stoB_REQ4 | btoR_REQ0, btoR_REQ1, btoS_ACK0, btoS_ACK1, btoS_ACK2, btoS_ACK3, btoS_ACK4, dEQ, eNQ, sLC0, sLC1, sLC2, stateG12, stateG7_0, stateG7_1 |
| gyro | 5 | distSense_blocked, isReady | balancer_fwd, balancer_bwd, balancer_turn_left, balancer_turn_right |
| humanoid | 0 | Obstacle_clear, InputMoveMode_fwd, InputMoveMode_turn | LeftMotor_fwd, LeftMotor_bwd, RightMotor_fwd, RightMotor_bwd, HeadMotor_fwd, HeadMotor_bwd, OutputMoveMode_fwd, OutputMoveMode_turn |
| lift | 0 | b1, b2, b3, c | f1, f2, f3 |
| minepump | 5 | highwater, methane | pump |
| minepump_liveness | 5 | highwater, methane | pump, flag |
| pcar | 2 | obstacle_clear, obstacle_blocked, sideSense_clear, sideSense_p_o | throttle_fwd, throttle_bwd, steer_right, steer_left |
| traffic_single | 5 | car, emergency, police | green |
| traffic_updated | 5 | carA, carB, emergency | greenA, greenB |

## The question

At the last step of each trace the environment breaks an assumption.
Our run could not get a system move there and reused the previous system
values. Whether the walker produces a genuine move at that step, and what
it is, is what these are for.

Send back the walker's log up to and including the crash.
