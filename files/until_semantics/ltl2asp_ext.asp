% semantics(strong).
semantics(weak).

% Time definitions & easy fills
succ(T+1,T,S) :- time(T,S), time(T+1,S).
has_succ(T,S) :- succ(_,T,S).
has_pred(T,S) :- succ(T,_,S).

reach(T,T,S) :- time(T,S).
reach(T,T2,S) :- reach(T,T1,S), succ(T2,T1,S).

% Propositional Operators
holds(T,X,S) :- trace(T,A,S), atomic(X,A).
holds(T,X,S) :- time(T,S), true(X).

holds(T,X,S) :- negate(X,F), time(T,S), not holds(T,F,S).

holds(T,X,S) :- conjunction(X,_), time(T,S), holds(T,F,S): conjunction(X,F).
holds(T,X,S) :- disjunction(X,F), time(T,S), holds(T,F,S).

holds(T,X,S) :- implies(X,F,G), time(T,S), not holds(T,F,S).
holds(T,X,S) :- implies(X,F,G), time(T,S), holds(T,F,S), holds(T,G,S).

% Temporal Operators
holds(T,X,S) :- next(X,F), time(T,S), holds(T2,F,S), succ(T2,T,S).
holds(T,X,S) :- next(X,F), time(T,S), not has_succ(T,S), semantics(weak).

holds(T,X,S) :- previous(X,F), succ(T,T1,S), holds(T1,F,S).
holds(T,X,S) :- previous(X,F), time(T,S), not has_pred(T,S), semantics(weak).

holds(T,X,S) :- until(X,F,G), holds(T,G,S).
holds(T,X,S) :- until(X,F,G), holds(T,F,S), holds(T2,X,S), succ(T2,T,S).

holds(T,X,S) :- until(X,F,G), holds(T,F,S), time(T,S), not has_succ(T,S), semantics(weak).

holds(T,X,S) :- eventually(X,F), holds(T,F,S).
holds(T,X,S) :- eventually(X,F), holds(T2,X,S), succ(T2,T,S).
holds(T,X,S) :- eventually(X,F), time(T,S), not has_succ(T,S), semantics(weak).

holds(T,X,S) :- always(X,F), time(T,S), holds(T2,F,S) : reach(T,T2,S).

% Satisfiability definition
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

