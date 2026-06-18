#!/bin/bash


strong='!pump&G((highwater -> X(pump)))&G((methane -> X(!pump)))'
best='!pump&G((highwater -> X(pump)))&G((highwater -> (X(pump) | X(methane))))&G((methane -> (X(!pump) | X(methane))))&G(((X(highwater) & (!pump & !highwater)) -> X(X(pump))))&G((highwater -> (X(pump) | X(highwater))))&!dwyer_state_0 & G((!dwyer_state_0 & (!(methane) | ((methane) & (X(!pump)))) & X(!dwyer_state_0)) | (!dwyer_state_0 & ((methane) & !(X(!pump))) & X(dwyer_state_0)) | (dwyer_state_0 & (X(!pump)) & X(!dwyer_state_0)) | (dwyer_state_0 & !(X(!pump)) & X(dwyer_state_0))) & GF(!dwyer_state_0)&!dwyer_state_1 & G((!dwyer_state_1 & (!(highwater) | ((highwater) & ((X(pump) | X(methane))))) & X(!dwyer_state_1)) | (!dwyer_state_1 & ((highwater) & !((X(pump) | X(methane)))) & X(dwyer_state_1)) | (dwyer_state_1 & ((X(pump) | X(methane))) & X(!dwyer_state_1)) | (dwyer_state_1 & !((X(pump) | X(methane))) & X(dwyer_state_1))) & GF(!dwyer_state_1)&G(((X(highwater) & highwater) -> X(X(pump))))&G((methane -> (X(!pump) | X(highwater))))&G(((X(highwater) & !methane) -> X(X(pump))))&G(((highwater & !methane) -> X(pump)))'

output=$(ltlfilt -c -f \
"$best" --imply "$strong")

if [ "$output" -eq 1 ]; then
  echo "Best->Strong"
else
  echo "NOT Best->Strong"
fi

output=$(ltlfilt -c -f \
"$strong" --imply "$best")

if [ "$output" -eq 1 ]; then
  echo "Strong->Best"
else
  echo "NOT Strong->Best"
fi

output=$(ltlfilt -c -f \
"$strong" --equivalent-to "$best")

if [ "$output" -eq 1 ]; then
  echo "Equivalent"
  exit 0
else
  echo "Different"
  exit 1
fi
