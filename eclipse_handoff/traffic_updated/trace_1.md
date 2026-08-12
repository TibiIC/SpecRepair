# traffic_updated - trace 1

- target assumption: `carA_moves_when_green`
- our run recorded these as violated: `carA_moves_when_green`
- steps: 8 (the last one is where the environment breaks the assumption)

Enter the environment values for each step in order. The system column is
what our run recorded - the one to compare against what the walker does.

| t | environment (enter this) | system (ours) |
| --- | --- | --- |
| 0 | carA=false  carB=true  emergency=true | greenA=false  greenB=false |
| 1 | carA=false  carB=true  emergency=false | greenA=false  greenB=false |
| 2 | carA=true  carB=true  emergency=true | greenA=false  greenB=false |
| 3 | carA=false  carB=true  emergency=false | greenA=false  greenB=true |
| 4 | carA=true  carB=false  emergency=true | greenA=false  greenB=false |
| 5 | carA=true  carB=false  emergency=false | greenA=false  greenB=true |
| 6 | carA=true  carB=true  emergency=false | greenA=true  greenB=false |
| 7 | carA=true  carB=true  emergency=true | **? <- the controller's answer goes here** |

Steps 0-6 are genuine controller output: the environment respects
the assumptions and the controller answers normally. Step 7 is the intended violation.

## The violating environment input

```
carA=true  carB=true  emergency=true
```

## What is missing: the system's response at t=7

That is the whole point of this hand-off. Enter the inputs above step by
step, and at the last one record what the walker does - the system values
it produces, or the crash if it produces none. Send back the log and the
trace can be completed from it.

| variable | walker's value at the violating step |
| --- | --- |
| greenA |  |
| greenB |  |
