#!/bin/bash

original='G((highwater -> X(pump)))&G((methane -> X(!pump)))'
best=' G((highwater -> X(pump)))& G((methane -> (X(!pump) | X(methane) & X(highwater))))& GF(!methane|!pump)'

output=$(ltlfilt -c -f \
"$best"\
  --imply \
  "$original")

if [ "$output" -eq 1 ]; then
  echo "Best->Original"
else
  echo "NOT Best->Original"
fi

output=$(ltlfilt -c -f \
"$original"\
  --imply \
  "$best")

if [ "$output" -eq 1 ]; then
  echo "Original->Best"
else
  echo "NOT Original->Best"
fi

output=$(ltlfilt -c -f \
"$original"\
  --equivalent-to \
  "$best")

if [ "$output" -eq 1 ]; then
  echo "Equivalent"
  exit 0
else
  echo "Different"
  exit 1
fi
