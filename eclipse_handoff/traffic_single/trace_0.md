# traffic_single - trace 0

- target assumption: `car_idle_when_red`
- our run recorded these as violated: `car_idle_when_red`
- steps: 13 (the last one is where the environment breaks the assumption)

Enter the environment values for each step in order. The system column is
what our run recorded - the one to compare against what the walker does.

| t | environment (enter this) | system (ours) |
| --- | --- | --- |
| 0 | car=true  emergency=false  police=false | green=false |
| 1 | car=true  emergency=false  police=false | green=true |
| 2 | car=false  emergency=true  police=true | green=true |
| 3 | car=true  emergency=true  police=true | green=true |
| 4 | car=false  emergency=false  police=false | green=false |
| 5 | car=true  emergency=false  police=false | green=true |
| 6 | car=false  emergency=false  police=true | green=false |
| 7 | car=true  emergency=true  police=true | green=true |
| 8 | car=false  emergency=true  police=true | green=true |
| 9 | car=false  emergency=true  police=false | green=false |
| 10 | car=false  emergency=true  police=true | green=false |
| 11 | car=true  emergency=false  police=false | green=false |
| 12 | car=false  emergency=false  police=false | **? <- the controller's answer goes here** |

Steps 0-11 are genuine controller output: the environment respects
the assumptions and the controller answers normally. Step 12 is the intended violation.

## The violating environment input

```
car=false  emergency=false  police=false
```

## What is missing: the system's response at t=12

That is the whole point of this hand-off. Enter the inputs above step by
step, and at the last one record what the walker does - the system values
it produces, or the crash if it produces none. Send back the log and the
trace can be completed from it.

| variable | walker's value at the violating step |
| --- | --- |
| green |  |
