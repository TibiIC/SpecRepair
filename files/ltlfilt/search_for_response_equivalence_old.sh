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

output=$(ltlfilt -c -f \
'!state & G((!state & ((!s) | (s & p)) & X(!state)) | (!state & (s & !p) & X(state)) | (state & (p) & X(!state)) |(state & (!p) & X(state))) & GF(!state)' \
  --imply \
  'G(s -> F(p))')

if [ "$output" -eq 1 ]; then
  echo "Pattern->Response"
else
  echo "NOT Pattern->Response"
fi

output=$(ltlfilt -c -f \
'G(s -> F(p))' \
  --imply \
  '!state & G((!state & ((!s) | (s & p)) & X(!state)) | (!state & (s & !p) & X(state)) | (state & (p) & X(!state)) |(state & (!p) & X(state))) & GF(!state)')

if [ "$output" -eq 1 ]; then
  echo "Response->Pattern"
else
  echo "NOT Response->Pattern"
fi

output=$(ltlfilt -c -f \
'G(s -> F(p))' \
  --equivalent-to \
  '!state & G((!state & ((!s) | (s & p)) & X(!state)) | (!state & (s & !p) & X(state)) | (state & (p) & X(!state)) |(state & (!p) & X(state))) & GF(!state)')

if [ "$output" -eq 1 ]; then
  echo "Equivalent"
else
  echo "Different"
fi
