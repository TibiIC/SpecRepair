#!/bin/bash


response='G((methane -> F(X(!pump))))& G((highwater -> F((X(pump) | X(methane)))))'
pattern='!dwyer_state_0 & G((!dwyer_state_0 & (!(methane) | ((methane) & (X(!pump)))) & X(!dwyer_state_0)) | (!dwyer_state_0 & ((methane) & !(X(!pump))) & X(dwyer_state_0)) | (dwyer_state_0 & (X(!pump)) & X(!dwyer_state_0)) | (dwyer_state_0 & !(X(!pump)) & X(dwyer_state_0))) & GF(!dwyer_state_0)&!dwyer_state_1 & G((!dwyer_state_1 & (!(highwater) | ((highwater) & ((X(pump) | X(methane))))) & X(!dwyer_state_1)) | (!dwyer_state_1 & ((highwater) & !((X(pump) | X(methane)))) & X(dwyer_state_1)) | (dwyer_state_1 & ((X(pump) | X(methane))) & X(!dwyer_state_1)) | (dwyer_state_1 & !((X(pump) | X(methane))) & X(dwyer_state_1))) & GF(!dwyer_state_1)'

common='!pump&G((highwater -> X(pump)))&G((highwater -> (X(pump) | X(methane))))&G((methane -> (X(!pump) | X(methane))))&G(((X(highwater) & (!pump & !highwater)) -> X(X(pump))))&G((highwater -> (X(pump) | X(highwater))))&G(((X(highwater) & highwater) -> X(X(pump))))&G((methane -> (X(!pump) | X(highwater))))&G(((X(highwater) & !methane) -> X(X(pump))))&G(((highwater & !methane) -> X(pump)))'

output=$(ltlfilt -c -f \
"$common & $pattern" --imply "$common & $response")

if [ "$output" -eq 1 ]; then
  echo "Common&Pattern->Common&Response"
else
  echo "NOT Pattern->Response"
fi

output=$(ltlfilt -c -f \
"$common & $response" --imply "$common & $pattern")

if [ "$output" -eq 1 ]; then
  echo "Common&Response->Common&Pattern"
else
  echo "NOT Common&Response->Common&Pattern"
fi

output=$(ltlfilt -c -f \
"$common & $pattern" --equivalent-to "$common & $response")

if [ "$output" -eq 1 ]; then
  echo "Equivalent"
  exit 0
else
  echo "Different"
  exit 1
fi
