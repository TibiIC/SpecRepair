#!/bin/bash

# ┌────────────────────────────────────────────────────────┬───────────────────────────────────────────────┐
# │ Spectra Pattern: pRespondsToS(s, p)                    │ LTL Formula Equivalent                        │
# ├────────────────────────────────────────────────────────┼───────────────────────────────────────────────┤
# │ var { S0, S1} state;                                   │  // S0=false, S1=true                         │
# │                                                        │                                               │
# │ // initial assignments: initial state                  │ // initial assignments: initial state         │
# │ ini state=S0;                                          │ !state                                        │
# │                                                        │  &                                            │
# │ // safety this and next state                          │ // safety this and next state                 │
# │ alw ((state=S0 & ((!s) | (s & p)) & next(state=S0)) |  │ G((!state & ((!s) | (s & p)) & X(!state)) |   │
# │      (state=S0 & (s & !p) & next(state=S1)) |          │   (!state & (s & !p) & X(state)) |            │
# │      (state=S1 & (p) & next(state=S0)) |               │   (state & (p) & X(!state)) |                 │
# │      (state=S1 & (!p) & next(state=S1)));              │   (state & (!p) & X(state)))                  │
# │                                                        │  &                                            │
# │ // equivalence of satisfaction                         │ // equivalence of satisfaction                │
# │ alwEv (state=S0);                                      │ GF(!state)                                    │
# └────────────────────────────────────────────────────────┴───────────────────────────────────────────────┘

response='G(s -> F(X(!p)))'
pattern='!state & G((!state & ((!s) | (s & X(!p))) & X(!state)) | (!state & (s & !X(!p)) & X(state)) | (state & (X(!p)) & X(!state)) |(state & (!X(!p)) & X(state))) & GF(!state)'

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