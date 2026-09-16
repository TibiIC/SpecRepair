% Future operators: next, until, eventually, always.
%
% On a FINITE trace these have two readings, and they differ only at the last
% instant, because that is the only place the trace runs out of evidence:
%
%   semantics(strong)  the trace must SHOW it     X a at the end  -> false
%   semantics(weak)    the trace must not REFUTE it              -> true
%
% On a lasso the question does not arise: the last instant has a successor via
% the back edge, `has_succ` holds there, and every weak rule below is guarded by
% `not has_succ`, so they simply never fire. An infinite behaviour has exactly
% one reading and gets it automatically.
%
% `always` deliberately has NO weak variant. A counterexample inside the trace
% is final - no extension can repair a violation that already happened - so both
% readings agree and a toggle would be noise.

holds(T,X,S) :- next(X,F), time(T,S), succ(T2,T,S), holds(T2,F,S).
holds(T,X,S) :- next(X,F), time(T,S), not has_succ(T,S), semantics(weak).

% a U b : b now, or a now and the whole obligation again from the next instant.
holds(T,X,S) :- until(X,F,G), holds(T,G,S).
holds(T,X,S) :- until(X,F,G), holds(T,F,S), succ(T2,T,S), holds(T2,X,S).
% Weak until at the end: the left side held all the way out, and the trace
% stopped before it could refute the obligation.
holds(T,X,S) :- until(X,F,G), holds(T,F,S), time(T,S),
                not has_succ(T,S), semantics(weak).

holds(T,X,S) :- eventually(X,F), holds(T,F,S).
holds(T,X,S) :- eventually(X,F), succ(T2,T,S), holds(T2,X,S).
holds(T,X,S) :- eventually(X,F), time(T,S), not has_succ(T,S), semantics(weak).

holds(T,X,S) :- always(X,F), time(T,S), holds(T2,F,S) : reach(T,T2,S).
