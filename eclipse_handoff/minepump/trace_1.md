# minepump - trace 1

- target assumption: `?`
- our run recorded these as violated: `?`
- steps: 6 (the last one is where the environment breaks the assumption)

Enter the environment values for each step in order. The system column is
what our run recorded - the one to compare against what the walker does.

| t | environment (enter this) | system (ours) |
| --- | --- | --- |
| 0 | highwater=false  methane=false | pump=false |
| 1 | highwater=true  methane=false | pump=false |
| 2 | highwater=true  methane=false | pump=true |
| 3 | highwater=false  methane=true | pump=true |
| 4 | highwater=false  methane=true | pump=false |
| 5 | highwater=true  methane=true | **? <- the controller's answer goes here** |

Steps 0-4 are genuine controller output: the environment respects
the assumptions and the controller answers normally. Step 5 is the intended violation.

## The violating environment input

```
highwater=true  methane=true
```

## What is missing: the system's response at t=5

That is the whole point of this hand-off. Enter the inputs above step by
step, and at the last one record what the walker does - the system values
it produces, or the crash if it produces none. Send back the log and the
trace can be completed from it.

| variable | walker's value at the violating step |
| --- | --- |
| pump |  |
