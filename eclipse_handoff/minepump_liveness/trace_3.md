# minepump_liveness - trace 3

- target assumption: `assumption3_1`
- our run recorded these as violated: `assumption3_1`
- steps: 7 (the last one is where the environment breaks the assumption)

Enter the environment values for each step in order. The system column is
what our run recorded - the one to compare against what the walker does.

| t | environment (enter this) | system (ours) |
| --- | --- | --- |
| 0 | highwater=false  methane=false | pump=false  flag=true |
| 1 | highwater=false  methane=false | pump=true  flag=true |
| 2 | highwater=false  methane=true | pump=true  flag=false |
| 3 | highwater=false  methane=true | pump=false  flag=false |
| 4 | highwater=false  methane=false | pump=false  flag=true |
| 5 | highwater=true  methane=true | pump=true  flag=true |
| 6 | highwater=false  methane=true | **? <- the controller's answer goes here** |

Steps 0-5 are genuine controller output: the environment respects
the assumptions and the controller answers normally. Step 6 is the intended violation.

## The violating environment input

```
highwater=false  methane=true
```

## What is missing: the system's response at t=6

That is the whole point of this hand-off. Enter the inputs above step by
step, and at the last one record what the walker does - the system values
it produces, or the crash if it produces none. Send back the log and the
trace can be completed from it.

| variable | walker's value at the violating step |
| --- | --- |
| pump |  |
| flag |  |
