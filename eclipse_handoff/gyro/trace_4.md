# gyro - trace 4

- target assumption: `ready_stays_ready`
- our run recorded these as violated: `ready_stays_ready`
- steps: 7 (the last one is where the environment breaks the assumption)

Enter the environment values for each step in order. The system column is
what our run recorded - the one to compare against what the walker does.

| t | environment (enter this) | system (ours) |
| --- | --- | --- |
| 0 | distSense_blocked=true  isReady=false | balancer_fwd=false  balancer_bwd=false  balancer_turn_left=false  balancer_turn_right=false |
| 1 | distSense_blocked=true  isReady=false | balancer_fwd=false  balancer_bwd=false  balancer_turn_left=false  balancer_turn_right=false |
| 2 | distSense_blocked=true  isReady=false | balancer_fwd=false  balancer_bwd=false  balancer_turn_left=false  balancer_turn_right=false |
| 3 | distSense_blocked=true  isReady=false | balancer_fwd=false  balancer_bwd=false  balancer_turn_left=false  balancer_turn_right=false |
| 4 | distSense_blocked=true  isReady=false | balancer_fwd=false  balancer_bwd=false  balancer_turn_left=false  balancer_turn_right=false |
| 5 | distSense_blocked=true  isReady=true | balancer_fwd=false  balancer_bwd=false  balancer_turn_left=true  balancer_turn_right=false |
| 6 | distSense_blocked=true  isReady=false | **? <- the controller's answer goes here** |

Steps 0-5 are genuine controller output: the environment respects
the assumptions and the controller answers normally. Step 6 is the intended violation.

## The violating environment input

```
distSense_blocked=true  isReady=false
```

## What is missing: the system's response at t=6

That is the whole point of this hand-off. Enter the inputs above step by
step, and at the last one record what the walker does - the system values
it produces, or the crash if it produces none. Send back the log and the
trace can be completed from it.

| variable | walker's value at the violating step |
| --- | --- |
| balancer_fwd |  |
| balancer_bwd |  |
| balancer_turn_left |  |
| balancer_turn_right |  |
