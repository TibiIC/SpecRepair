# traffic_single - trace 2

- target assumption: `car_idle_when_red`
- our run recorded these as violated: `car_idle_when_red`
- steps: 37 (the last one is where the environment breaks the assumption)

Enter the environment values for each step in order. The system column is
what our run recorded - the one to compare against what the walker does.

| t | environment (enter this) | system (ours) |
| --- | --- | --- |
| 0 | car=true  emergency=false  police=true | green=false |
| 1 | car=true  emergency=false  police=true | green=true |
| 2 | car=false  emergency=false  police=false | green=true |
| 3 | car=true  emergency=false  police=true | green=true |
| 4 | car=false  emergency=true  police=true | green=false |
| 5 | car=true  emergency=true  police=false | green=true |
| 6 | car=false  emergency=false  police=false | green=false |
| 7 | car=false  emergency=false  police=false | green=true |
| 8 | car=false  emergency=false  police=false | green=true |
| 9 | car=false  emergency=false  police=false | green=true |
| 10 | car=false  emergency=false  police=false | green=false |
| 11 | car=true  emergency=false  police=false | green=true |
| 12 | car=false  emergency=true  police=false | green=false |
| 13 | car=true  emergency=true  police=false | green=false |
| 14 | car=false  emergency=false  police=true | green=false |
| 15 | car=false  emergency=true  police=true | green=false |
| 16 | car=false  emergency=true  police=true | green=false |
| 17 | car=true  emergency=false  police=false | green=true |
| 18 | car=false  emergency=true  police=false | green=false |
| 19 | car=false  emergency=true  police=false | green=true |
| 20 | car=false  emergency=false  police=false | green=false |
| 21 | car=false  emergency=false  police=true | green=false |
| 22 | car=true  emergency=false  police=false | green=true |
| 23 | car=false  emergency=true  police=true | green=true |
| 24 | car=true  emergency=true  police=true | green=true |
| 25 | car=false  emergency=true  police=true | green=false |
| 26 | car=true  emergency=true  police=true | green=true |
| 27 | car=true  emergency=true  police=false | green=true |
| 28 | car=false  emergency=true  police=false | green=false |
| 29 | car=false  emergency=true  police=true | green=true |
| 30 | car=true  emergency=true  police=false | green=true |
| 31 | car=false  emergency=false  police=true | green=true |
| 32 | car=false  emergency=true  police=false | green=false |
| 33 | car=true  emergency=true  police=true | green=true |
| 34 | car=true  emergency=true  police=true | green=true |
| 35 | car=true  emergency=false  police=true | green=false |
| 36 | car=false  emergency=true  police=false | **? <- the controller's answer goes here** |

Steps 0-35 are genuine controller output: the environment respects
the assumptions and the controller answers normally. Step 36 is the intended violation.

## The violating environment input

```
car=false  emergency=true  police=false
```

## What is missing: the system's response at t=36

That is the whole point of this hand-off. Enter the inputs above step by
step, and at the last one record what the walker does - the system values
it produces, or the crash if it produces none. Send back the log and the
trace can be completed from it.

| variable | walker's value at the violating step |
| --- | --- |
| green |  |
