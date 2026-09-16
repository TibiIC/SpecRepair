% Propositional Operators

holds(T,X,S) :- trace(T,A,S), atomic(X,A).
holds(T,X,S) :- time(T,S), true(X).

holds(T,X,S) :- negate(X,F), time(T,S), not holds(T,F,S).

holds(T,X,S) :- conjunction(X,_), time(T,S), holds(T,F,S): conjunction(X,F).
holds(T,X,S) :- disjunction(X,F), time(T,S), holds(T,F,S).

holds(T,X,S) :- implies(X,F,G), time(T,S), not holds(T,F,S).
holds(T,X,S) :- implies(X,F,G), time(T,S), holds(T,F,S), holds(T,G,S).
