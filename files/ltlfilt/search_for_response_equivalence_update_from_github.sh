#!/bin/bash

# ┌────────────────────────────────────────────────────────┬───────────────────────────────────────────────┐
# │ Spectra Pattern: pRespondsToS(p, s)                    │ LTL Formula Equivalent  G (p -> F s)          │
# ├────────────────────────────────────────────────────────┼───────────────────────────────────────────────┤
# │ var { S0, S1} state;                                   │  // S0=false, S1=true                         │
# │                                                        │                                               │
# │   -- initial assignments: initial state                │ // initial assignments: initial state         │
# │   state=S0;                                            │ !state                                        │
# │                                                        │  &                                            │
# │   -- safety this and next state                        │ // safety this and next state                 │
# │   G ((state=S0 & ((!p) | (p & s)) & next(state=S0)) |  │ G((!state & ((!p) | (p & s)) & X(!state)) |   │
# │   (state=S0 & (p & !s) & next(state=S1)) |             │   (!state & (p & !s) & X(state)) |            │
# │   (state=S1 & (s) & next(state=S0)) |                  │   (state & (s) & X(!state)) |                 │
# │   (state=S1 & (!s) & next(state=S1)));                 │   (state & (!s) & X(state)))                  │
# │                                                        │  &                                            │
# │   -- equivalence of satisfaction                       │ // equivalence of satisfaction                │
# │   GF (state=S0);                                       │ GF(!state)                                    │
# └────────────────────────────────────────────────────────┴───────────────────────────────────────────────┘

response='G(p -> F(s))'
pattern='!state & G((!state & ((!p) | (p & s)) & X(!state)) | (!state & (p & !s) & X(state)) | (state & (s) & X(!state)) | (state & (!s) & X(state))) & GF(!state)'



output=$(ltlfilt -c -f \
"$pattern" \
  --imply \
  "$response")

if [ "$output" -eq 1 ]; then
  echo "Pattern->Response"
else
  echo "NOT Pattern->Response"
fi

output=$(ltlfilt -c -f \
"$response" \
  --imply \
  "$pattern")

if [ "$output" -eq 1 ]; then
  echo "Response->Pattern"
else
  echo "NOT Response->Pattern"
fi

output=$(ltlfilt -c -f \
"$response" \
  --equivalent-to \
  "$pattern")

if [ "$output" -eq 1 ]; then
  echo "Equivalent"
else
  echo "Different"
fi