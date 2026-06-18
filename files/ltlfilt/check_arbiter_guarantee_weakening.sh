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

# G((a=false->F((g1=false&g2=false))));
original='G(!a -> (!g1 & !g2))'
response='G(!a -> F(!g1 & !g2))'
pattern='!state & G((!state & ((!!a) | (!a & (!g1 & !g2))) & X(!state)) | (!state & (!a & !(!g1 & !g2)) & X(state)) | (state & ((!g1 & !g2)) & X(!state)) |(state & (!(!g1 & !g2)) & X(state))) & GF(!state)'

output=$(ltlfilt -c -f \
"$pattern" \
  --imply \
  "$original")

if [ "$output" -eq 1 ]; then
  echo "Pattern->Original"
else
  echo "NOT Pattern->Original"
fi

output=$(ltlfilt -c -f \
"$original" \
  --imply \
  "$pattern")

if [ "$output" -eq 1 ]; then
  echo "Original->Pattern"
else
  echo "NOT Original->Pattern"
fi

output=$(ltlfilt -c -f \
"$original" \
  --equivalent-to \
  "$pattern")

if [ "$output" -eq 1 ]; then
  echo "Original and Pattern Equivalent"
else
  echo "Original and Pattern Different"
fi

output=$(ltlfilt -c -f \
"$original" \
  --imply \
  "$response")

if [ "$output" -eq 1 ]; then
  echo "Original->Response"
else
  echo "NOT Original->Response"
fi

output=$(ltlfilt -c -f \
"$response" \
  --imply \
  "$original")

if [ "$output" -eq 1 ]; then
  echo "Response->Original"
else
  echo "NOT Response->Original"
fi

output=$(ltlfilt -c -f \
"$response" \
  --equivalent-to \
  "$original")

if [ "$output" -eq 1 ]; then
  echo "Original and Response Equivalent"
else
  echo "Original and Response Different"
fi

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
  echo "Pattern and Response Equivalent"
else
  echo "Pattern and Response Different"
fi
