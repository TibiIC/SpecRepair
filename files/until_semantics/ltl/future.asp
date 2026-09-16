% Temporal Operators - future

holds(T,X,S) :- next(X,F), time(T,S), holds(T2,F,S), succ(T2,T,S).
holds(T,X,S) :- w_next(X,F), time(T,S), not has_succ(T,S).

holds(T,X,S) :- until(X,F,G), holds(T,G,S).
holds(T,X,S) :- until(X,F,G), holds(T,F,S), holds(T2,X,S), succ(T2,T,S).

holds(T,X,S) :- w_until(X,F,G), holds(T,G,S).
holds(T,X,S) :- w_until(X,F,G), holds(T,F,S), holds(T2,X,S), succ(T2,T,S).
holds(T,X,S) :- w_until(X,F,G), holds(T,F,S), time(T,S), not has_succ(T,S).

holds(T,X,S) :- eventually(X,F), holds(T,F,S).
holds(T,X,S) :- eventually(X,F), holds(T2,X,S), succ(T2,T,S).
holds(T,X,S) :- w_eventually(X,F), time(T,S), not has_succ(T,S).

holds(T,X,S) :- always(X,F), time(T,S), holds(T2,F,S) : reach(T,T2,S).
