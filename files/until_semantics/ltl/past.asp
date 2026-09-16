% Temporal Operators - past

holds(T,X,S) :- previous(X,F), succ(T,T1,S), holds(T1,F,S).

holds(T,X,S) :- w_previous(X,F), succ(T,T1,S), holds(T1,F,S).
holds(T,X,S) :- w_previous(X,F), time(T,S), not has_pred(T,S).

holds(T,X,S) :- since(X,F,G), holds(T,G,S).
holds(T,X,S) :- since(X,F,G), holds(T,F,S), holds(T1,X,S), succ(T,T1,S).

holds(T,X,S) :- w_since(X,F,G), holds(T,G,S).
holds(T,X,S) :- w_since(X,F,G), holds(T,F,S), holds(T1,X,S), succ(T,T1,S).
holds(T,X,S) :- w_since(X,F,G), holds(T,F,S), time(T,S), not has_pred(T,S).

holds(T,X,S) :- once(X,F), holds(T,F,S).
holds(T,X,S) :- once(X,F), holds(T1,X,S), succ(T,T1,S).

holds(T,X,S) :- historically(X,F), time(T,S), holds(T1,F,S) : reach(T1,T,S).
