#!/bin/bash

response='G(p -> F(s))'
pattern='!state & G((!state & ((!p) | (p & s)) & X(!state)) | (!state & (p & !s) & X(state)) | (state & (s) & X(!state)) | (state & (!s) & X(state))) & GF(!state)'

# Automaton for the pattern, with "state" still a visible AP
ltl2tgba -f "$pattern" > pattern.hoa

# Existentially project "state" away -- this is the automaton-level
# equivalent of "there exists a state-labeling satisfying pattern",
# which is the actual claim being made
autfilt --remove-ap=state pattern.hoa > pattern_hidden.hoa

# Automaton for the plain response formula
ltl2tgba -f "$response" > response.hoa

echo "--- after hiding 'state' ---"

if autfilt pattern_hidden.hoa --included-in=response.hoa -q; then
  echo "Pattern(no state) -> Response"
else
  echo "NOT Pattern(no state) -> Response"
fi

if autfilt response.hoa --included-in=pattern_hidden.hoa -q; then
  echo "Response -> Pattern(no state)"
else
  echo "NOT Response -> Pattern(no state)"
fi

if autfilt pattern_hidden.hoa --equivalent-to=response.hoa -q; then
  echo "Equivalent"
else
  echo "Different"
fi