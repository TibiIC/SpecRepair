# traffic_single - trace 4

- target assumption: `car_idle_when_red`
- our run recorded these as violated: `car_idle_when_red`
- steps: 8 (the last one is where the environment breaks the assumption)

Enter the environment values for each step in order. The system column is
what our run recorded - the one to compare against what the walker does.

| t | environment (enter this) | system (ours) |
| --- | --- | --- |
| 0 | car=false  emergency=false  police=true | green=true |
| 1 | car=true  emergency=true  police=true | green=true |
| 2 | car=true  emergency=false  police=true | green=false |
| 3 | car=true  emergency=false  police=true | green=false |
| 4 | car=true  emergency=true  police=false | green=true |
| 5 | car=false  emergency=true  police=true | green=false |
| 6 | car=true  emergency=false  police=true | green=false |
| 7 | car=false  emergency=true  police=true | **? <- the controller's answer goes here** |

Steps 0-6 are genuine controller output: the environment respects
the assumptions and the controller answers normally. Step 7 is the intended violation.

## The violating environment input

```
car=false  emergency=true  police=true
```

## What is missing: the system's response at t=7

That is the whole point of this hand-off. Enter the inputs above step by
step, and at the last one record what the walker does - the system values
it produces, or the crash if it produces none. Send back the log and the
trace can be completed from it.

| variable | walker's value at the violating step |
| --- | --- |
| green |  |
