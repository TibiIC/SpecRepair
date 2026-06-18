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

response_1='G((methane -> F(X(!pump))))'
response_2='G((highwater -> F((X(pump) | X(methane)))))'
pattern_1='!dwyer_state_0 & G((!dwyer_state_0 & (!(methane) | ((methane) & (X(!pump)))) & X(!dwyer_state_0)) | (!dwyer_state_0 & ((methane) & !(X(!pump))) & X(dwyer_state_0)) | (dwyer_state_0 & (X(!pump)) & X(!dwyer_state_0)) | (dwyer_state_0 & !(X(!pump)) & X(dwyer_state_0))) & GF(!dwyer_state_0)'
pattern_2='!dwyer_state_1 & G((!dwyer_state_1 & (!(highwater) | ((highwater) & ((X(pump) | X(methane))))) & X(!dwyer_state_1)) | (!dwyer_state_1 & ((highwater) & !((X(pump) | X(methane)))) & X(dwyer_state_1)) | (dwyer_state_1 & ((X(pump) | X(methane))) & X(!dwyer_state_1)) | (dwyer_state_1 & !((X(pump) | X(methane))) & X(dwyer_state_1))) & GF(!dwyer_state_1)'

echo "Checking Response 1 against Pattern 1"
output=$(ltlfilt -c -f \
"$pattern_1" --imply "$response_1")

if [ "$output" -eq 1 ]; then
  echo "Pattern->Response"
else
  echo "NOT Pattern->Response"
fi

output=$(ltlfilt -c -f \
"$response_1" --imply "$pattern_1")

if [ "$output" -eq 1 ]; then
  echo "Response->Pattern"
else
  echo "NOT Response->Pattern"
fi

output=$(ltlfilt -c -f \
"$response_1" --equivalent-to "$pattern_1")

if [ "$output" -eq 1 ]; then
  echo "Equivalent"
else
  echo "Different"
fi

echo "Checking Response 2 against Pattern 2"
output=$(ltlfilt -c -f \
"$pattern_2" --imply "$response_2")

if [ "$output" -eq 1 ]; then
  echo "Pattern->Response"
else
  echo "NOT Pattern->Response"
fi

output=$(ltlfilt -c -f \
"$response_2" --imply "$pattern_2")

if [ "$output" -eq 1 ]; then
  echo "Response->Pattern"
else
  echo "NOT Response->Pattern"
fi

output=$(ltlfilt -c -f \
"$response_2" --equivalent-to "$pattern_2")

if [ "$output" -eq 1 ]; then
  echo "Equivalent"
  exit 0
else
  echo "Different"
  exit 1
fi
