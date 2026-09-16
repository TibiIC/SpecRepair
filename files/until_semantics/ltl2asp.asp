holds(T,X,S) :- trace(T,A,S), atomic(X,A).
holds(T,X,S) :- time(T,S), true(X).

holds(T,X,S) :- next(X,F), holds(T+1,F,S).
holds(T,X,S) :- conjunction(X,_), time(T,S), holds(T,F,S): conjunction(X,F).
holds(T,X,S) :- negate(X,F), time(T,S), not holds(T,F,S).
holds(T,X,S) :- until(X,F,G), holds(T,G,S).
holds(T,X,S) :- until(X,F,G), holds(T,F,S), holds(T+1,X,S).
sat(S) :- holds(X,0,S), root(X).

% symbol(X) :- atomic(_,X).
% { last_instant(T): T=0..5 } = 1.
% time(0..T) :- last_instant(T).
% { trace(T,A): symbol(A) } :- time(T).
% :- not sat.

symbol(a).
symbol(b).

% Trace {} · {a}
trace_name(g1).
time(0..1,g1).
trace(1,a,g1).

% Formula G(a → b)  ≡  ¬(true U (a ∧ ¬b))
root(0).
negate(0,1).
until(1,2,3).
true(2).
conjunction(3,4).
conjunction(3,5).
atomic(4,a).
negate(5,6).
atomic(6,b).

#show sat/1.

#show holds/3.

