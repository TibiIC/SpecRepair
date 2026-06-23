#!/bin/bash

common='!pump&G((highwater -> X(pump)))&G((highwater -> (X(pump) | X(methane))))&G((methane -> (X(!pump) | X(methane))))&G(((X(highwater) & (!pump & !highwater)) -> X(X(pump))))&G((highwater -> (X(pump) | X(highwater))))&G(((X(highwater) & highwater) -> X(X(pump))))&G((methane -> (X(!pump) | X(highwater))))&G(((X(highwater) & !methane) -> X(X(pump))))&G(((highwater & !methane) -> X(pump)))'
response='G((methane -> F(X(!pump))))& G((highwater -> F((X(pump) | X(methane)))))'
pattern='!dwyer_state_0 & G((!dwyer_state_0 & (!(methane) | ((methane) & (X(!pump)))) & X(!dwyer_state_0)) | (!dwyer_state_0 & ((methane) & !(X(!pump))) & X(dwyer_state_0)) | (dwyer_state_0 & (X(!pump)) & X(!dwyer_state_0)) | (dwyer_state_0 & !(X(!pump)) & X(dwyer_state_0))) & GF(!dwyer_state_0)&!dwyer_state_1 & G((!dwyer_state_1 & (!(highwater) | ((highwater) & ((X(pump) | X(methane))))) & X(!dwyer_state_1)) | (!dwyer_state_1 & ((highwater) & !((X(pump) | X(methane)))) & X(dwyer_state_1)) | (dwyer_state_1 & ((X(pump) | X(methane))) & X(!dwyer_state_1)) | (dwyer_state_1 & !((X(pump) | X(methane))) & X(dwyer_state_1))) & GF(!dwyer_state_1)'

# Automaton for the pattern, with "state" still a visible AP
ltl2tgba -f "$common&$pattern" > pattern.hoa

# Remove dwyer_state_0 and _1
autfilt --remove-ap=dwyer_state_0,dwyer_state_1 pattern.hoa > pattern_hidden.hoa

# Automaton for the plain response formula
ltl2tgba -f "$common&$response" > response.hoa

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
