#!/bin/bash

INPUTS="methane,highwater"
OUTPUTS="pump,ti,ts"

INIT_ENV="(!highwater&!methane)"
INVARIANT_ENV="((pump->(!highwater|!methane)))"
JUSTICE_ENV=()

# Original system spec components
INIT_SYS_ORIG="(!pump)"
INVARIANT_SYS_ORIG="((highwater->X(pump))&(methane->X(!pump)))"

# Latch semantics for ti and ts as system invariants
# ti latches whether Is has held since the start: t'_I = ti (once set, stays)
# ts latches whether Ss has held since the start: t'_S = ts & Ss
# Initial values: ti = Is, ts = true
LATCH_INIT="(ti <-> $INIT_SYS_ORIG) & ts"
LATCH_INV="(X(ti) <-> ti) & (X(ts) <-> (ts & ($INVARIANT_SYS_ORIG)))"

JUSTICE_SYS=("ti" "ts")

# ===============================================================

join_conj() {
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

# Sep on (phi_e, phi_tilde_s):
# COND_1: trivially true since I_tilde_s = (ti = Is) & ts has no pump restriction
# COND_2: trivially true since S_tilde_s has no pump restriction
# But we still need the latch initialisation and invariant encoded

COND_1="(($INIT_ENV) -> ($LATCH_INIT))"
COND_2="($INIT_ENV -> (G(($INVARIANT_ENV) -> ($LATCH_INV)) W !($INVARIANT_ENV)))"
COND_3="(($INIT_ENV & G($INVARIANT_ENV)) -> ($JE_CONJ->$JS_CONJ))"

PHI="$COND_1 & $COND_2 & $COND_3"

echo "Checking realizability of:"
echo "  $PHI"
echo "  inputs:  $INPUTS"
echo "  outputs: $OUTPUTS"
echo

ltlsynt --formula="$PHI" --ins="$INPUTS" --outs="$OUTPUTS" --realizability
strix -o hoa -f "$PHI" --ins="$INPUTS" --outs="$OUTPUTS"