#!/bin/bash

strong='!pump&G((highwater -> X(pump)))&G((methane -> X(!pump)))'
best='!pump& G((highwater -> X(pump)))& G((methane -> (X(!pump) | X(methane) & X(highwater))))& G((methane -> F(X(!pump))))'

output=$(ltlfilt -c -f \
"$best"\
  --imply \
  "$strong")

if [ "$output" -eq 1 ]; then
  echo "Best->Strong"
else
  echo "NOT Best->Strong"
fi

output=$(ltlfilt -c -f \
"$strong"\
  --imply \
  "$best")

if [ "$output" -eq 1 ]; then
  echo "Strong->Best"
else
  echo "NOT Strong->Best"
fi

output=$(ltlfilt -c -f \
"$strong"\
  --equivalent-to \
  "$best")

if [ "$output" -eq 1 ]; then
  echo "Equivalent"
  exit 0
else
  echo "Different"
  exit 1
fi
