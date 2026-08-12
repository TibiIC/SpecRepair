# traffic_single - trace 1

- target assumption: `car_moves_when_green`
- our run recorded these as violated: `car_moves_when_green`
- steps: 7 (the last one is where the environment breaks the assumption)

Enter the environment values for each step in order. The system column is
what our run recorded - the one to compare against what the walker does.

| t | environment (enter this) | system (ours) |
| --- | --- | --- |
| 0 | car=false  emergency=true  police=true | green=true |
| 1 | car=false  emergency=true  police=false | green=true |
| 2 | car=false  emergency=false  police=true | green=false |
| 3 | car=false  emergency=true  police=false | green=true |
| 4 | car=true  emergency=false  police=true | green=true |
| 5 | car=true  emergency=false  police=false | green=true |
| 6 | car=true  emergency=false  police=false | **? <- the controller's answer goes here** |

Steps 0-5 are genuine controller output: the environment respects
the assumptions and the controller answers normally. Step 6 is the intended violation.

## The violating environment input

```
car=true  emergency=false  police=false
```

## What is missing: the system's response at t=6

That is the whole point of this hand-off. Enter the inputs above step by
step, and at the last one record what the walker does - the system values
it produces, or the crash if it produces none. Send back the log and the
trace can be completed from it.

| variable | walker's value at the violating step |
| --- | --- |
| green |  |
