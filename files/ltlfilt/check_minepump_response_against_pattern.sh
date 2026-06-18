#!/bin/bash


# ┌───────────────────────────────────────────────┬──────────────────────────────────────────────────────────────────────────────┐
# │ LTL Formula Pattern                           │ G((methane -> F(X(!pump)))) Equivalent                                       │
# ├───────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
# │                                               │  // S0=false, S1=true                                                        │
# │                                               │                                                                              │
# │ // initial assignments: initial state         │ // initial assignments: initial state                                        │
# │ !state                                        │ !state                                                                       │
# │  &                                            │  &                                                                           │
# │ // safety this and next state                 │ // safety this and next state                                                │
# │ G((!state & ((!s) | (s & p)) & X(!state)) |   │ !state & G((!state & (!(methane) | ((methane) & (X(!pump)))) & X(!state)) |  │
# │   (!state & (s & !p) & X(state)) |            │   (!state & ((methane) & !(X(!pump))) & X(state)) |                          │
# │   (state & (p) & X(!state)) |                 │   (state & (X(!pump)) & X(!state)) |                                         │
# │   (state & (!p) & X(state)))                  │   (state & !(X(!pump)) & X(state)))                                          │
# │  &                                            │  &                                                                           │
# │ // equivalence of satisfaction                │ // equivalence of satisfaction                                               │
# │ GF(!state)                                    │ GF(!state)                                                                   │
# └───────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────────────────┘

# ┌───────────────────────────────────────────────┬───────────────────────────────────────────────────────────────────────────────────────┐
# │ LTL Formula Pattern                           │ G((highwater -> F((X(pump) | X(methane))))) Equivalent                                │
# ├───────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤
# │                                               │  // S0=false, S1=true                                                                 │
# │                                               │                                                                                       │
# │ // initial assignments: initial state         │ // initial assignments: initial state                                                 │
# │ !state                                        │ !state                                                                                │
# │  &                                            │  &                                                                                    │
# │ // safety this and next state                 │ // safety this and next state                                                         │
# │ G((!state & ((!s) | (s & p)) & X(!state)) |   │ G((!state & (!(highwater) | ((highwater) & ((X(pump) | X(methane))))) & X(!state)) |  │
# │   (!state & (s & !p) & X(state)) |            │   (!state & ((highwater) & !((X(pump) | X(methane)))) & X(state)) |                   │
# │   (state & (p) & X(!state)) |                 │   (state & ((X(pump) | X(methane))) & X(!state)) |                                    │
# │   (state & (!p) & X(state)))                  │   (state & !((X(pump) | X(methane))) & X(state)))                                     │
# │  &                                            │  &                                                                                    │
# │ // equivalence of satisfaction                │ // equivalence of satisfaction                                                        │
# │ GF(!state)                                    │ GF(!state)                                                                            │
# └───────────────────────────────────────────────┴───────────────────────────────────────────────────────────────────────────────────────┘

response='G((methane -> F(X(!pump))))& G((highwater -> F((X(pump) | X(methane)))))'
pattern='!dwyer_state_0 & G((!dwyer_state_0 & (!(methane) | ((methane) & (X(!pump)))) & X(!dwyer_state_0)) | (!dwyer_state_0 & ((methane) & !(X(!pump))) & X(dwyer_state_0)) | (dwyer_state_0 & (X(!pump)) & X(!dwyer_state_0)) | (dwyer_state_0 & !(X(!pump)) & X(dwyer_state_0))) & GF(!dwyer_state_0) &!dwyer_state_1 & G((!dwyer_state_1 & (!(highwater) | ((highwater) & ((X(pump) | X(methane))))) & X(!dwyer_state_1)) | (!dwyer_state_1 & ((highwater) & !((X(pump) | X(methane)))) & X(dwyer_state_1)) | (dwyer_state_1 & ((X(pump) | X(methane))) & X(!dwyer_state_1)) | (dwyer_state_1 & !((X(pump) | X(methane))) & X(dwyer_state_1))) & GF(!dwyer_state_1)'

output=$(ltlfilt -c -f \
"$pattern" --imply "$response")

if [ "$output" -eq 1 ]; then
  echo "Pattern->Response"
else
  echo "NOT Pattern->Response"
fi

output=$(ltlfilt -c -f \
"$response" --imply "$pattern")

if [ "$output" -eq 1 ]; then
  echo "Response->Pattern"
else
  echo "NOT Response->Pattern"
fi

output=$(ltlfilt -c -f \
"$response" --equivalent-to "$pattern")

if [ "$output" -eq 1 ]; then
  echo "Equivalent"
  exit 0
else
  echo "Different"
  exit 1
fi
