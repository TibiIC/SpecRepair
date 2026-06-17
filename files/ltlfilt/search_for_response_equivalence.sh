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
  echo "Spectra's Dwyer pattern implies the normal response pattern."
else
  echo "Verification failed: output is $output, expected 1"
fi

output=$(ltlfilt -c -f \
'G(s -> F(p))' \
  --imply \
  '!state & G((!state & ((!s) | (s & p)) & X(!state)) | (!state & (s & !p) & X(state)) | (state & (p) & X(!state)) |(state & (!p) & X(state))) & GF(!state)')

if [ "$output" -eq 0 ]; then
  echo "Normal response pattern implies Spectra's Dwyer pattern."
else
  echo "Verification failed: output is $output, expected 0"
fi

output=$(ltlfilt -c -f \
'G(s -> F(p))' \
  --equivalent-to \
  '!state & G((!state & ((!s) | (s & p)) & X(!state)) | (!state & (s & !p) & X(state)) | (state & (p) & X(!state)) |(state & (!p) & X(state))) & GF(!state)')

if [ "$output" -eq 0 ]; then
  echo "Normal response pattern is not equivalent to Spectra's Dwyer pattern."
else
  echo "Verification failed: output is $output, expected 0"
fi