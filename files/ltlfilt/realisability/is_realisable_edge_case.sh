#!/bin/bash

INPUTS="methane,highwater"
OUTPUTS="pump"

INIT_ENV="(!highwater&!methane)"
INVARIANT_ENV="((pump->(!highwater|!methane)))"
JUSTICE_ENV=()

# System guarantees
INIT_SYS="(!pump)"
INVARIANT_SYS="((highwater->X(pump))&(methane->X(!pump)))"
JUSTICE_SYS=()

# ===============================================================

join_conj() {
  # Joins array elements as a conjunction of parenthesized GF(...) terms.
  # Echoes "true" if the array is empty.
  local arr=("$@")
  if [ ${#arr[@]} -eq 0 ]; then
    echo "true"
    return
  fi
  local out="GF($1)"
  shift
  for j in "$@"; do
    out="$out & GF($j)"
  done
  echo "$out"
}

JE_CONJ=$(join_conj "${JUSTICE_ENV[@]}")
JS_CONJ=$(join_conj "${JUSTICE_SYS[@]}")

COND_1="(($INIT_ENV) -> ($INIT_SYS))"
# COND_2="(($INIT_ENV) -> G(H($INVARIANT_ENV)->$INVARIANT_SYS))" historically doesn't exist
# G(H(p)->q) eq G((p & q) | !p | (!p W (p & !q & G!p)))
#COND_2="($INIT_ENV -> G(($INVARIANT_ENV & $INVARIANT_SYS) | !$INVARIANT_ENV | (!$INVARIANT_ENV W ($INVARIANT_ENV & !$INVARIANT_SYS & G!$INVARIANT_ENV))))"
# G(H(p)->q) eq G(p -> q) W !p
COND_2="($INIT_ENV -> (G(($INVARIANT_ENV) -> ($INVARIANT_SYS)) W !($INVARIANT_ENV)))"
COND_3="(($INIT_ENV & G($INVARIANT_ENV)) -> ($JE_CONJ->$JS_CONJ))"

# PHI="$COND_1 & $COND_2 & $COND_3"
PHI="$COND_1 & $COND_2 & $COND_3"

echo "Checking realizability of:"
echo "  $PHI"
echo "  inputs:  $INPUTS"
echo "  outputs: $OUTPUTS"
echo

ltlsynt --formula="$PHI" --ins="$INPUTS" --outs="$OUTPUTS" --realizability
strix -o hoa -f "$PHI" --ins="$INPUTS" --outs="$OUTPUTS"
