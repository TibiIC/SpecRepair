# pcar - trace 4

- target assumption: `obstacle_mutual_exclusion`
- our run recorded these as violated: `obstacle_mutual_exclusion`
- steps: 6 (the last one is where the environment breaks the assumption)

Enter the environment values for each step in order. The system column is
what our run recorded - the one to compare against what the walker does.

| t | environment (enter this) | system (ours) |
| --- | --- | --- |
| 0 | obstacle_clear=true  obstacle_blocked=false  sideSense_clear=true  sideSense_p_o=false | throttle_fwd=true  throttle_bwd=false  steer_right=false  steer_left=false |
| 1 | obstacle_clear=false  obstacle_blocked=true  sideSense_clear=false  sideSense_p_o=false | throttle_fwd=false  throttle_bwd=false  steer_right=false  steer_left=false |
| 2 | obstacle_clear=true  obstacle_blocked=false  sideSense_clear=false  sideSense_p_o=false | throttle_fwd=false  throttle_bwd=true  steer_right=false  steer_left=false |
| 3 | obstacle_clear=true  obstacle_blocked=false  sideSense_clear=false  sideSense_p_o=true | throttle_fwd=true  throttle_bwd=false  steer_right=false  steer_left=false |
| 4 | obstacle_clear=true  obstacle_blocked=false  sideSense_clear=false  sideSense_p_o=false | throttle_fwd=false  throttle_bwd=true  steer_right=true  steer_left=false |
| 5 | obstacle_clear=true  obstacle_blocked=true  sideSense_clear=false  sideSense_p_o=true | **? <- the controller's answer goes here** |

Steps 0-4 are genuine controller output: the environment respects
the assumptions and the controller answers normally. Step 5 is the intended violation.

## The violating environment input

```
obstacle_clear=true  obstacle_blocked=true  sideSense_clear=false  sideSense_p_o=true
```

## What is missing: the system's response at t=5

That is the whole point of this hand-off. Enter the inputs above step by
step, and at the last one record what the walker does - the system values
it produces, or the crash if it produces none. Send back the log and the
trace can be completed from it.

| variable | walker's value at the violating step |
| --- | --- |
| throttle_fwd |  |
| throttle_bwd |  |
| steer_right |  |
| steer_left |  |
