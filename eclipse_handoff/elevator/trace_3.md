# elevator - trace 3 (incomplete)

- target assumption: `stopped_implies_floor_known`
- steps 0-8 are genuine controller output
- step 9 is the intended violation, and its system response is unknown

| t | environment (enter this) | system (ours) |
| --- | --- | --- |
| 0 | floor_lower=true  floor_middle=false  floor_upper=false | elevMot_fwd=false  elevMot_bwd=false |
| 1 | floor_lower=true  floor_middle=false  floor_upper=false | elevMot_fwd=true  elevMot_bwd=false |
| 2 | floor_lower=false  floor_middle=false  floor_upper=true | elevMot_fwd=true  elevMot_bwd=false |
| 3 | floor_lower=false  floor_middle=true  floor_upper=false | elevMot_fwd=false  elevMot_bwd=false |
| 4 | floor_lower=true  floor_middle=false  floor_upper=false | elevMot_fwd=false  elevMot_bwd=true |
| 5 | floor_lower=false  floor_middle=false  floor_upper=false | elevMot_fwd=true  elevMot_bwd=false |
| 6 | floor_lower=false  floor_middle=false  floor_upper=false | elevMot_fwd=true  elevMot_bwd=false |
| 7 | floor_lower=false  floor_middle=false  floor_upper=false | elevMot_fwd=false  elevMot_bwd=true |
| 8 | floor_lower=false  floor_middle=false  floor_upper=false | elevMot_fwd=false  elevMot_bwd=false |
| 9 | floor_lower=true  floor_middle=false  floor_upper=true | **? <- the controller's answer goes here** |

## The violating environment input

```
floor_lower=true  floor_middle=false  floor_upper=true
```

## What is missing: the system's response at t=9

This trace was never completed by us: the controller had no move to make, and nothing was invented to stand in for one. Enter the inputs above step by step and record what the walker does at the last one.

| variable | walker's value at the violating step |
| --- | --- |
| elevMot_fwd |  |
| elevMot_bwd |  |
