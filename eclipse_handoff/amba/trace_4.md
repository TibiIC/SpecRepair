# amba - trace 4 (incomplete)

- target assumption: `hburst_mutual_exclusion`
- steps 0-4 are genuine controller output
- step 5 is the intended violation, and its system response is unknown

| t | environment (enter this) | system (ours) |
| --- | --- | --- |
| 0 | hburst_burst4=false  hburst_single=false  hbusreq_0=false  hbusreq_1=false  hbusreq_2=false  hlock_0=false  hlock_1=false  hlock_2=false  hready=false | btq_state_1_s0=true  btq_state_1_s1=false  btq_state_2_s0=true  btq_state_2_s1=false  btq_state_3_s0=true  btq_state_3_s1=false  btq_state_4_s0=true  btq_state_4_s1=false  btq_state_5_s0=true  btq_state_5_s1=false  btq_state_6_s0=true  btq_state_6_s1=false  decide=true  hgrant_0=true  hgrant_1=false  hgrant_2=false  hmaster_val0=true  hmaster_val1=false  hmastlock=false  hready_counter_val0=true  hready_counter_val1=false  hready_counter_val2=false  hready_counter_val3=false  locked=false  start=true |
| 1 | hburst_burst4=false  hburst_single=true  hbusreq_0=true  hbusreq_1=true  hbusreq_2=true  hlock_0=false  hlock_1=true  hlock_2=true  hready=true | btq_state_1_s0=true  btq_state_1_s1=false  btq_state_2_s0=true  btq_state_2_s1=false  btq_state_3_s0=true  btq_state_3_s1=false  btq_state_4_s0=true  btq_state_4_s1=false  btq_state_5_s0=false  btq_state_5_s1=true  btq_state_6_s0=false  btq_state_6_s1=true  decide=false  hgrant_0=true  hgrant_1=false  hgrant_2=false  hmaster_val0=true  hmaster_val1=false  hmastlock=false  hready_counter_val0=true  hready_counter_val1=false  hready_counter_val2=false  hready_counter_val3=false  locked=false  start=false |
| 2 | hburst_burst4=false  hburst_single=true  hbusreq_0=true  hbusreq_1=true  hbusreq_2=true  hlock_0=true  hlock_1=false  hlock_2=true  hready=true | btq_state_1_s0=true  btq_state_1_s1=false  btq_state_2_s0=true  btq_state_2_s1=false  btq_state_3_s0=true  btq_state_3_s1=false  btq_state_4_s0=true  btq_state_4_s1=false  btq_state_5_s0=true  btq_state_5_s1=false  btq_state_6_s0=true  btq_state_6_s1=false  decide=true  hgrant_0=true  hgrant_1=false  hgrant_2=false  hmaster_val0=true  hmaster_val1=false  hmastlock=false  hready_counter_val0=false  hready_counter_val1=true  hready_counter_val2=false  hready_counter_val3=false  locked=false  start=false |
| 3 | hburst_burst4=false  hburst_single=true  hbusreq_0=true  hbusreq_1=true  hbusreq_2=true  hlock_0=false  hlock_1=true  hlock_2=true  hready=true | btq_state_1_s0=true  btq_state_1_s1=false  btq_state_2_s0=true  btq_state_2_s1=false  btq_state_3_s0=true  btq_state_3_s1=false  btq_state_4_s0=true  btq_state_4_s1=false  btq_state_5_s0=true  btq_state_5_s1=false  btq_state_6_s0=true  btq_state_6_s1=false  decide=false  hgrant_0=true  hgrant_1=false  hgrant_2=false  hmaster_val0=true  hmaster_val1=false  hmastlock=false  hready_counter_val0=false  hready_counter_val1=false  hready_counter_val2=true  hready_counter_val3=false  locked=true  start=false |
| 4 | hburst_burst4=false  hburst_single=true  hbusreq_0=true  hbusreq_1=true  hbusreq_2=true  hlock_0=true  hlock_1=false  hlock_2=true  hready=true | btq_state_1_s0=true  btq_state_1_s1=false  btq_state_2_s0=true  btq_state_2_s1=false  btq_state_3_s0=true  btq_state_3_s1=false  btq_state_4_s0=true  btq_state_4_s1=false  btq_state_5_s0=true  btq_state_5_s1=false  btq_state_6_s0=true  btq_state_6_s1=false  decide=true  hgrant_0=true  hgrant_1=false  hgrant_2=false  hmaster_val0=true  hmaster_val1=false  hmastlock=true  hready_counter_val0=false  hready_counter_val1=false  hready_counter_val2=false  hready_counter_val3=true  locked=true  start=true |
| 5 | hburst_burst4=true  hburst_single=true  hbusreq_0=true  hbusreq_1=true  hbusreq_2=true  hlock_0=true  hlock_1=false  hlock_2=true  hready=true | **? <- the controller's answer goes here** |

## The violating environment input

```
hburst_burst4=true  hburst_single=true  hbusreq_0=true  hbusreq_1=true  hbusreq_2=true  hlock_0=true  hlock_1=false  hlock_2=true  hready=true
```

## What is missing: the system's response at t=5

This trace was never completed by us: the controller had no move to make, and nothing was invented to stand in for one. Enter the inputs above step by step and record what the walker does at the last one.

| variable | walker's value at the violating step |
| --- | --- |
| btq_state_1_s0 |  |
| btq_state_1_s1 |  |
| btq_state_2_s0 |  |
| btq_state_2_s1 |  |
| btq_state_3_s0 |  |
| btq_state_3_s1 |  |
| btq_state_4_s0 |  |
| btq_state_4_s1 |  |
| btq_state_5_s0 |  |
| btq_state_5_s1 |  |
| btq_state_6_s0 |  |
| btq_state_6_s1 |  |
| decide |  |
| hgrant_0 |  |
| hgrant_1 |  |
| hgrant_2 |  |
| hmaster_val0 |  |
| hmaster_val1 |  |
| hmastlock |  |
| hready_counter_val0 |  |
| hready_counter_val1 |  |
| hready_counter_val2 |  |
| hready_counter_val3 |  |
| locked |  |
| start |  |
