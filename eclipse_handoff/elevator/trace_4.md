# elevator - trace 4 (incomplete)

- target assumption: `floor_mutual_exclusion`
- steps 0-4 are genuine controller output
- step 5 is the intended violation, and its system response is unknown

| t | environment (enter this) | system (ours) |
| --- | --- | --- |
| 0 | floor_lower=false  floor_middle=false  floor_upper=true | elevMot_fwd=false  elevMot_bwd=false |
| 1 | floor_lower=false  floor_middle=true  floor_upper=false | elevMot_fwd=true  elevMot_bwd=false |
| 2 | floor_lower=false  floor_middle=false  floor_upper=true | elevMot_fwd=false  elevMot_bwd=false |
| 3 | floor_lower=false  floor_middle=true  floor_upper=false | elevMot_fwd=false  elevMot_bwd=true |
| 4 | floor_lower=false  floor_middle=true  floor_upper=false | elevMot_fwd=false  elevMot_bwd=false |
| 5 | floor_lower=true  floor_middle=true  floor_upper=true | **? <- the controller's answer goes here** |

## The violating environment input

```
floor_lower=true  floor_middle=true  floor_upper=true
```

## What is missing: the system's response at t=5

This trace was never completed by us: the controller had no move to make, and nothing was invented to stand in for one. Enter the inputs above step by step and record what the walker does at the last one.

| variable | walker's value at the violating step |
| --- | --- |
| elevMot_fwd |  |
| elevMot_bwd |  |
