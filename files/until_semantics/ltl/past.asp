% Temporal Operators - past

holds(T,X,S) :- previous(X,F), succ(T,T1,S), holds(T1,F,S).
holds(T,X,S) :- previous(X,F), time(T,S), not has_pred(T,S), semantics(weak).
