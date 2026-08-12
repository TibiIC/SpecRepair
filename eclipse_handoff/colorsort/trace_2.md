# colorsort - trace 2 (incomplete)

- target assumption: `color_mutual_exclusion_10`
- steps 0-4 are genuine controller output
- step 5 is the intended violation, and its system response is unknown

| t | environment (enter this) | system (ours) |
| --- | --- | --- |
| 0 | color_red=false  color_green=false  color_blue=false  color_black=true  color_yellow=false  detect_red=false  detect_green=true  detect_blue=false  detect_black=false  detect_yellow=false  ack_ver_hor_move=false  ack_bot_move=true  atEdge_noedge=true  num_of_cubes_zero=false  haltButton_press=true  speedButton_press=true | spec_allsleep=true  spec_finished_cycle=false  spec_speedButtonValidPressed=false  spec_haltButtonValidPressed=false  verMot_move=false  horMot_move=false  botMot_right=false  botMot_left=false  botMot_stop=true  motSpeed_level1=true  motSpeed_level2=false  reduce_num_of_cubes_reduce=false  spec_currentColor_red=false  spec_currentColor_green=true  spec_currentColor_blue=false  spec_currentColor_black=false  spec_currentColor_yellow=false  spec_stage_wait=true  spec_stage_kick=false  spec_stage_toangleright=false  spec_stage_toangleleft=false  spec_stage_drop=false  spec_pausing_pause=false |
| 1 | color_red=false  color_green=false  color_blue=false  color_black=true  color_yellow=false  detect_red=true  detect_green=false  detect_blue=false  detect_black=false  detect_yellow=false  ack_ver_hor_move=false  ack_bot_move=false  atEdge_noedge=true  num_of_cubes_zero=false  haltButton_press=false  speedButton_press=false | spec_allsleep=true  spec_finished_cycle=false  spec_speedButtonValidPressed=false  spec_haltButtonValidPressed=false  verMot_move=false  horMot_move=false  botMot_right=false  botMot_left=false  botMot_stop=true  motSpeed_level1=true  motSpeed_level2=false  reduce_num_of_cubes_reduce=false  spec_currentColor_red=false  spec_currentColor_green=true  spec_currentColor_blue=false  spec_currentColor_black=false  spec_currentColor_yellow=false  spec_stage_wait=true  spec_stage_kick=false  spec_stage_toangleright=false  spec_stage_toangleleft=false  spec_stage_drop=false  spec_pausing_pause=false |
| 2 | color_red=false  color_green=false  color_blue=false  color_black=true  color_yellow=false  detect_red=true  detect_green=false  detect_blue=false  detect_black=false  detect_yellow=false  ack_ver_hor_move=false  ack_bot_move=true  atEdge_noedge=true  num_of_cubes_zero=false  haltButton_press=false  speedButton_press=false | spec_allsleep=true  spec_finished_cycle=false  spec_speedButtonValidPressed=false  spec_haltButtonValidPressed=false  verMot_move=false  horMot_move=false  botMot_right=false  botMot_left=false  botMot_stop=true  motSpeed_level1=true  motSpeed_level2=false  reduce_num_of_cubes_reduce=false  spec_currentColor_red=false  spec_currentColor_green=false  spec_currentColor_blue=true  spec_currentColor_black=false  spec_currentColor_yellow=false  spec_stage_wait=true  spec_stage_kick=false  spec_stage_toangleright=false  spec_stage_toangleleft=false  spec_stage_drop=false  spec_pausing_pause=false |
| 3 | color_red=false  color_green=false  color_blue=false  color_black=true  color_yellow=false  detect_red=false  detect_green=false  detect_blue=false  detect_black=false  detect_yellow=true  ack_ver_hor_move=false  ack_bot_move=true  atEdge_noedge=true  num_of_cubes_zero=false  haltButton_press=false  speedButton_press=false | spec_allsleep=true  spec_finished_cycle=false  spec_speedButtonValidPressed=false  spec_haltButtonValidPressed=false  verMot_move=false  horMot_move=false  botMot_right=false  botMot_left=false  botMot_stop=true  motSpeed_level1=true  motSpeed_level2=false  reduce_num_of_cubes_reduce=false  spec_currentColor_red=false  spec_currentColor_green=true  spec_currentColor_blue=false  spec_currentColor_black=false  spec_currentColor_yellow=false  spec_stage_wait=true  spec_stage_kick=false  spec_stage_toangleright=false  spec_stage_toangleleft=false  spec_stage_drop=false  spec_pausing_pause=false |
| 4 | color_red=false  color_green=false  color_blue=false  color_black=true  color_yellow=false  detect_red=true  detect_green=false  detect_blue=false  detect_black=false  detect_yellow=false  ack_ver_hor_move=false  ack_bot_move=false  atEdge_noedge=true  num_of_cubes_zero=false  haltButton_press=false  speedButton_press=false | spec_allsleep=true  spec_finished_cycle=false  spec_speedButtonValidPressed=false  spec_haltButtonValidPressed=false  verMot_move=false  horMot_move=false  botMot_right=false  botMot_left=false  botMot_stop=true  motSpeed_level1=true  motSpeed_level2=false  reduce_num_of_cubes_reduce=false  spec_currentColor_red=true  spec_currentColor_green=false  spec_currentColor_blue=false  spec_currentColor_black=false  spec_currentColor_yellow=false  spec_stage_wait=true  spec_stage_kick=false  spec_stage_toangleright=false  spec_stage_toangleleft=false  spec_stage_drop=false  spec_pausing_pause=false |
| 5 | color_red=false  color_green=false  color_blue=true  color_black=true  color_yellow=true  detect_red=true  detect_green=true  detect_blue=true  detect_black=true  detect_yellow=true  ack_ver_hor_move=false  ack_bot_move=false  atEdge_noedge=false  num_of_cubes_zero=true  haltButton_press=false  speedButton_press=false | **? <- the controller's answer goes here** |

## The violating environment input

```
color_red=false  color_green=false  color_blue=true  color_black=true  color_yellow=true  detect_red=true  detect_green=true  detect_blue=true  detect_black=true  detect_yellow=true  ack_ver_hor_move=false  ack_bot_move=false  atEdge_noedge=false  num_of_cubes_zero=true  haltButton_press=false  speedButton_press=false
```

## What is missing: the system's response at t=5

This trace was never completed by us: the controller had no move to make, and nothing was invented to stand in for one. Enter the inputs above step by step and record what the walker does at the last one.

| variable | walker's value at the violating step |
| --- | --- |
| spec_allsleep |  |
| spec_finished_cycle |  |
| spec_speedButtonValidPressed |  |
| spec_haltButtonValidPressed |  |
| verMot_move |  |
| horMot_move |  |
| botMot_right |  |
| botMot_left |  |
| botMot_stop |  |
| motSpeed_level1 |  |
| motSpeed_level2 |  |
| reduce_num_of_cubes_reduce |  |
| spec_currentColor_red |  |
| spec_currentColor_green |  |
| spec_currentColor_blue |  |
| spec_currentColor_black |  |
| spec_currentColor_yellow |  |
| spec_stage_wait |  |
| spec_stage_kick |  |
| spec_stage_toangleright |  |
| spec_stage_toangleleft |  |
| spec_stage_drop |  |
| spec_pausing_pause |  |
