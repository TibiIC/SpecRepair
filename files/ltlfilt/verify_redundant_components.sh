#!/bin/bash

original='G(F(!emergency))&
G((((carA & !greenA) & !carB) -> X(carA)))&
G((((carB & !greenB) & !carA) -> X(carB)))&
G(((carA & greenA) -> X(!carA)))&
G(((carB & greenB) -> X(!carB)))&
G(((carB & !greenB) -> (X(carB) | X(!carA))))&
G(((carA & !greenA) -> (X(carA) | !greenB)))&
G(((carA & !greenA) -> (X(carA) | X(!emergency))))&
G(((carB & !greenB) -> (X(carB) | !greenA)))&
G(((carB & !greenB) -> F(X(carB))))&
G(((carA & !greenA) -> (X(carA) | X(!carB))))&
G(((carA & !greenA) -> F(X(carA))))&
G((((carA & !greenA) & !emergency) -> X(carA)))'

best='G(F(!emergency))&
G((((carA & !greenA) & !carB) -> X(carA)))&
G((((carB & !greenB) & !emergency) -> X(carB)))&
G((((carB & !greenB) & !carA) -> X(carB)))&
G(((carA & greenA) -> X(!carA)))&
G(((carB & greenB) -> X(!carB)))&
G(((carB & !greenB) -> (X(carB) | X(!emergency))))&
G(((carB & !greenB) -> (X(carB) | X(!carA))))&
G(((carA & !greenA) -> (X(carA) | !greenB)))&
G(((carB & !greenB) -> (X(carB) | !greenA)))&
G(((carB & !greenB) -> F(X(carB))))&
G(((carA & !greenA) -> (X(carA) | X(!carB))))&
G(((carA & !greenA) -> F(X(carA))))'

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
