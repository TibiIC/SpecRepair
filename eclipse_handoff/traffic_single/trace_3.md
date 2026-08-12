# traffic_single - trace 3

- target assumption: `car_moves_when_green`
- our run recorded these as violated: `car_moves_when_green`
- steps: 35 (the last one is where the environment breaks the assumption)

Enter the environment values for each step in order. The system column is
what our run recorded - the one to compare against what the walker does.

| t | environment (enter this) | system (ours) |
| --- | --- | --- |
| 0 | car=false  emergency=false  police=false | green=false |
| 1 | car=true  emergency=true  police=true | green=false |
| 2 | car=false  emergency=false  police=true | green=false |
| 3 | car=false  emergency=false  police=true | green=true |
| 4 | car=true  emergency=false  police=true | green=true |
| 5 | car=false  emergency=true  police=false | green=false |
| 6 | car=false  emergency=false  police=false | green=true |
| 7 | car=false  emergency=false  police=true | green=true |
| 8 | car=true  emergency=true  police=true | green=false |
| 9 | car=false  emergency=false  police=true | green=true |
| 10 | car=false  emergency=false  police=true | green=false |
| 11 | car=false  emergency=false  police=true | green=true |
| 12 | car=true  emergency=true  police=true | green=false |
| 13 | car=false  emergency=true  police=false | green=true |
| 14 | car=true  emergency=true  police=true | green=false |
| 15 | car=false  emergency=false  police=true | green=true |
| 16 | car=false  emergency=false  police=false | green=true |
| 17 | car=true  emergency=true  police=true | green=false |
| 18 | car=true  emergency=true  police=true | green=true |
| 19 | car=false  emergency=true  police=true | green=true |
| 20 | car=true  emergency=false  police=true | green=true |
| 21 | car=false  emergency=true  police=true | green=false |
| 22 | car=false  emergency=true  police=true | green=true |
| 23 | car=false  emergency=true  police=true | green=false |
| 24 | car=true  emergency=false  police=true | green=true |
| 25 | car=false  emergency=true  police=false | green=false |
| 26 | car=false  emergency=false  police=true | green=true |
| 27 | car=false  emergency=false  police=false | green=false |
| 28 | car=false  emergency=false  police=true | green=false |
| 29 | car=false  emergency=false  police=true | green=false |
| 30 | car=false  emergency=false  police=false | green=true |
| 31 | car=true  emergency=true  police=true | green=false |
| 32 | car=false  emergency=true  police=false | green=false |
| 33 | car=true  emergency=true  police=false | green=true |
| 34 | car=true  emergency=true  police=false | **? <- the controller's answer goes here** |

Steps 0-33 are genuine controller output: the environment respects
the assumptions and the controller answers normally. Step 34 is the intended violation.

## The violating environment input

```
car=true  emergency=true  police=false
```

## What is missing: the system's response at t=34

That is the whole point of this hand-off. Enter the inputs above step by
step, and at the last one record what the walker does - the system values
it produces, or the crash if it produces none. Send back the log and the
trace can be completed from it.

| variable | walker's value at the violating step |
| --- | --- |
| green |  |
