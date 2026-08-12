# minepump - trace 0

- target assumption: `assumption1_1`
- our run recorded these as violated: `assumption1_1, assumption2_1`
- steps: 11 (the last one is where the environment breaks the assumption)

Enter the environment values for each step in order. The system column is
what our run recorded - the one to compare against what the walker does.

| t | environment (enter this) | system (ours) |
| --- | --- | --- |
| 0 | highwater=false  methane=false | pump=false |
| 1 | highwater=false  methane=true | pump=false |
| 2 | highwater=false  methane=true | pump=false |
| 3 | highwater=false  methane=true | pump=false |
| 4 | highwater=true  methane=false | pump=false |
| 5 | highwater=false  methane=false | pump=true |
| 6 | highwater=false  methane=true | pump=false |
| 7 | highwater=false  methane=false | pump=false |
| 8 | highwater=true  methane=false | pump=true |
| 9 | highwater=false  methane=true | pump=true |
| 10 | highwater=true  methane=true | **? <- the controller's answer goes here** |

Steps 0-9 are genuine controller output: the environment respects
the assumptions and the controller answers normally. Step 10 is the intended violation.

## The violating environment input

```
highwater=true  methane=true
```

## What is missing: the system's response at t=10

That is the whole point of this hand-off. Enter the inputs above step by
step, and at the last one record what the walker does - the system values
it produces, or the crash if it produces none. Send back the log and the
trace can be completed from it.

| variable | walker's value at the violating step |
| --- | --- |
| pump |  |
