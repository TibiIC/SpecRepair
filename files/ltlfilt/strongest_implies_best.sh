#!/bin/bash

output=$(ltlfilt -c -f \
'!pump& G((highwater -> X(pump)))& G((highwater -> (X(pump) | X(methane))))& G((methane -> (X(!pump) | X(methane))))& G(((X(highwater) & (!pump & !highwater)) -> X(X(pump))))& G((highwater -> (X(pump) | X(highwater))))& G((methane -> F(X(!pump))))& G((highwater -> F((X(pump) | X(methane)))))& G(((X(highwater) & highwater) -> X(X(pump))))& G((methane -> (X(!pump) | X(highwater))))& G(((X(highwater) & !methane) -> X(X(pump))))& G(((highwater & !methane) -> X(pump)))'\
  --imply \
  '!pump&G((highwater -> X(pump)))&G((methane -> X(!pump)))')

if [ "$output" -eq 1 ]; then
  echo "Best specification's guarantees implies strong specification's guarantees."
else
  echo "Verification failed: output is $output, expected 1"
fi

output=$(ltlfilt -c -f \
'!pump&G((highwater -> X(pump)))&G((methane -> X(!pump)))'\
  --imply \
  '!pump& G((highwater -> X(pump)))& G((highwater -> (X(pump) | X(methane))))& G((methane -> (X(!pump) | X(methane))))& G(((X(highwater) & (!pump & !highwater)) -> X(X(pump))))& G((highwater -> (X(pump) | X(highwater))))& G((methane -> F(X(!pump))))& G((highwater -> F((X(pump) | X(methane)))))& G(((X(highwater) & highwater) -> X(X(pump))))& G((methane -> (X(!pump) | X(highwater))))& G(((X(highwater) & !methane) -> X(X(pump))))& G(((highwater & !methane) -> X(pump)))')

if [ "$output" -eq 1 ]; then
  echo "Strong specification's guarantees implies best specification's guarantees."
else
  echo "Verification failed: output is $output, expected 1"
fi

output=$(ltlfilt -c -f \
'!pump&G((highwater -> X(pump)))&G((methane -> X(!pump)))'\
  --equivalent-to \
  '!pump& G((highwater -> X(pump)))& G((highwater -> (X(pump) | X(methane))))& G((methane -> (X(!pump) | X(methane))))& G(((X(highwater) & (!pump & !highwater)) -> X(X(pump))))& G((highwater -> (X(pump) | X(highwater))))& G((methane -> F(X(!pump))))& G((highwater -> F((X(pump) | X(methane)))))& G(((X(highwater) & highwater) -> X(X(pump))))& G((methane -> (X(!pump) | X(highwater))))& G(((X(highwater) & !methane) -> X(X(pump))))& G(((highwater & !methane) -> X(pump)))')

if [ "$output" -eq 1 ]; then
  echo "Strong specification's guarantees is equivalent to the best specification's guarantees."
  exit 0
else
  echo "Verification failed: output is $output, expected 1"
  exit 1
fi
