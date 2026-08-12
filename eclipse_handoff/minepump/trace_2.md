# minepump - trace 2

- target assumption: `?`
- our run recorded these as violated: `?`
- steps: 20 (the last one is where the environment breaks the assumption)

Enter the environment values for each step in order. The system column is
what our run recorded - the one to compare against what the walker does.

| t | environment (enter this) | system (ours) |
| --- | --- | --- |
| 0 | highwater=false  methane=false | pump=false |
| 1 | highwater=false  methane=false | pump=true |
| 2 | highwater=false  methane=false | pump=true |
| 3 | highwater=false  methane=true | pump=true |
| 4 | highwater=false  methane=false | pump=false |
| 5 | highwater=false  methane=false | pump=true |
| 6 | highwater=false  methane=false | pump=false |
| 7 | highwater=false  methane=true | pump=false |
| 8 | highwater=false  methane=true | pump=false |
| 9 | highwater=false  methane=false | pump=false |
| 10 | highwater=false  methane=true | pump=false |
| 11 | highwater=false  methane=true | pump=false |
| 12 | highwater=false  methane=false | pump=false |
| 13 | highwater=false  methane=true | pump=false |
| 14 | highwater=false  methane=true | pump=false |
| 15 | highwater=false  methane=true | pump=false |
| 16 | highwater=true  methane=false | pump=false |
| 17 | highwater=true  methane=false | pump=true |
| 18 | highwater=true  methane=false | pump=true |
| 19 | highwater=true  methane=false | **? <- the controller's answer goes here** |

Steps 0-18 are genuine controller output: the environment respects
the assumptions and the controller answers normally. Step 19 is the intended violation.

## The violating environment input

```
highwater=true  methane=false
```

## What is missing: the system's response at t=19

That is the whole point of this hand-off. Enter the inputs above step by
step, and at the last one record what the walker does - the system values
it produces, or the crash if it produces none. Send back the log and the
trace can be completed from it.

| variable | walker's value at the violating step |
| --- | --- |
| pump |  |
