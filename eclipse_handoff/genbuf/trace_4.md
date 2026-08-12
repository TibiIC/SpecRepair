# genbuf - trace 4

- target assumption: `unnamed_assumption_14`
- our run recorded these as violated: `unnamed_assumption_10, unnamed_assumption_13, unnamed_assumption_14, unnamed_assumption_20, unnamed_assumption_22`
- steps: 6 (the last one is where the environment breaks the assumption)

Enter the environment values for each step in order. The system column is
what our run recorded - the one to compare against what the walker does.

| t | environment (enter this) | system (ours) |
| --- | --- | --- |
| 0 | eMPTY=true  fULL=false  rtoB_ACK0=false  rtoB_ACK1=false  stoB_REQ0=false  stoB_REQ1=false  stoB_REQ2=false  stoB_REQ3=false  stoB_REQ4=false | btoR_REQ0=false  btoR_REQ1=false  btoS_ACK0=false  btoS_ACK1=false  btoS_ACK2=false  btoS_ACK3=false  btoS_ACK4=false  dEQ=false  eNQ=false  sLC0=false  sLC1=false  sLC2=false  stateG12=false  stateG7_0=false  stateG7_1=true |
| 1 | eMPTY=true  fULL=false  rtoB_ACK0=false  rtoB_ACK1=false  stoB_REQ0=false  stoB_REQ1=true  stoB_REQ2=true  stoB_REQ3=true  stoB_REQ4=true | btoR_REQ0=true  btoR_REQ1=false  btoS_ACK0=false  btoS_ACK1=false  btoS_ACK2=false  btoS_ACK3=false  btoS_ACK4=false  dEQ=false  eNQ=false  sLC0=true  sLC1=false  sLC2=true  stateG12=false  stateG7_0=true  stateG7_1=true |
| 2 | eMPTY=true  fULL=false  rtoB_ACK0=false  rtoB_ACK1=false  stoB_REQ0=true  stoB_REQ1=true  stoB_REQ2=true  stoB_REQ3=true  stoB_REQ4=true | btoR_REQ0=true  btoR_REQ1=false  btoS_ACK0=false  btoS_ACK1=false  btoS_ACK2=false  btoS_ACK3=false  btoS_ACK4=false  dEQ=false  eNQ=false  sLC0=false  sLC1=false  sLC2=false  stateG12=false  stateG7_0=false  stateG7_1=false |
| 3 | eMPTY=true  fULL=false  rtoB_ACK0=true  rtoB_ACK1=false  stoB_REQ0=true  stoB_REQ1=true  stoB_REQ2=true  stoB_REQ3=true  stoB_REQ4=true | btoR_REQ0=true  btoR_REQ1=false  btoS_ACK0=false  btoS_ACK1=true  btoS_ACK2=false  btoS_ACK3=false  btoS_ACK4=false  dEQ=false  eNQ=true  sLC0=true  sLC1=false  sLC2=false  stateG12=false  stateG7_0=false  stateG7_1=false |
| 4 | eMPTY=false  fULL=false  rtoB_ACK0=true  rtoB_ACK1=false  stoB_REQ0=true  stoB_REQ1=false  stoB_REQ2=true  stoB_REQ3=true  stoB_REQ4=true | btoR_REQ0=false  btoR_REQ1=false  btoS_ACK0=false  btoS_ACK1=true  btoS_ACK2=false  btoS_ACK3=false  btoS_ACK4=false  dEQ=false  eNQ=false  sLC0=true  sLC1=false  sLC2=true  stateG12=false  stateG7_0=false  stateG7_1=false |
| 5 | eMPTY=false  fULL=false  rtoB_ACK0=true  rtoB_ACK1=true  stoB_REQ0=false  stoB_REQ1=true  stoB_REQ2=false  stoB_REQ3=true  stoB_REQ4=true | **? <- the controller's answer goes here** |

Steps 0-4 are genuine controller output: the environment respects
the assumptions and the controller answers normally. Step 5 is the intended violation.

## The violating environment input

```
eMPTY=false  fULL=false  rtoB_ACK0=true  rtoB_ACK1=true  stoB_REQ0=false  stoB_REQ1=true  stoB_REQ2=false  stoB_REQ3=true  stoB_REQ4=true
```

## What is missing: the system's response at t=5

That is the whole point of this hand-off. Enter the inputs above step by
step, and at the last one record what the walker does - the system values
it produces, or the crash if it produces none. Send back the log and the
trace can be completed from it.

| variable | walker's value at the violating step |
| --- | --- |
| btoR_REQ0 |  |
| btoR_REQ1 |  |
| btoS_ACK0 |  |
| btoS_ACK1 |  |
| btoS_ACK2 |  |
| btoS_ACK3 |  |
| btoS_ACK4 |  |
| dEQ |  |
| eNQ |  |
| sLC0 |  |
| sLC1 |  |
| sLC2 |  |
| stateG12 |  |
| stateG7_0 |  |
| stateG7_1 |  |
