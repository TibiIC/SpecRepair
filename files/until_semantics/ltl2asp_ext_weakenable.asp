holds(T,X,S) :- trace(T,A,S), atomic(X,A).
holds(T,X,S) :- time(T,S), true(X).

holds(T,X,S) :- next(X,F), holds(T+1,F,S).
holds(T,X,S) :- conjunction(X,_), time(T,S), holds(T,F,S): conjunction(X,F).
holds(T,X,S) :- disjunction(X,F), time(T,S), holds(T,F,S).
holds(T,X,S) :- negate(X,F), time(T,S), not holds(T,F,S).
holds(T,X,S) :- until(X,F,G), holds(T,G,S).
holds(T,X,S) :- until(X,F,G), holds(T,F,S), holds(T+1,X,S).
holds(T,X,S) :- implies(X,F,G), time(T,S), not holds(T,F,S).
holds(T,X,S) :- implies(X,F,G), time(T,S), holds(T,F,S), holds(T,G,S).
holds(T,X,S) :- always(X,F), time(T,S), holds(T2,F,S): time(T2,S), T2>=T.
sat(S) :- holds(0,X,S), root(X).

% symbol(X) :- atomic(_,X).
% { last_instant(T): T=0..5 } = 1.
% time(0..T) :- last_instant(T).
% { trace(T,A): symbol(A) } :- time(T).
% :- not sat.

symbol(a).
symbol(b).
symbol(c).

% Trace {} · {a}
trace_name(g1).
time(0..1,g1).
trace(1,a,g1).

% Trace {} · {b,c}
trace_name(g2).
time(0..1,g2).
trace(1,c,g2).

% Formula G(a → b v c)
root(0).
always(0,1).
implies(1,2,3).
atomic(2,a).
disjunction(3,4).
atomic(4,b).
atomic(4,c).

#show sat/1.

%#show holds/3.

