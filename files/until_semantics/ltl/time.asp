% Time: the successor relation, the ends of a trace, and reachability.
%
% Everything temporal is defined against `succ/3` rather than T+1 arithmetic, so
% that a trace can be a finite line OR a lasso - a finite prefix that loops back
% on itself and therefore denotes an INFINITE behaviour. Adding the back edge is
% the only difference between the two, and nothing downstream has to know.

succ(T2,T1,S) :- time(T1,S), time(T2,S), T2 = T1+1.

first(T,S)  :- time(T,S), not has_pred(T,S).
last(T,S)   :- time(T,S), not time(T+1,S).

% A lasso: `loop(L,S)` says the instant after S's last one is L, not nothing.
% With the back edge present the last instant HAS a successor, so every
% weak-semantics rule below stops firing on its own - an infinite behaviour
% needs no end-of-trace reading, and gets none.
succ(L,T,S) :- loop(L,S), last(T,S), time(L,S).

has_succ(T,S) :- succ(_,T,S).

% The PAST uses a strictly linear step, deliberately excluding the loop edge.
%
% A lasso folds two different moments onto one position: instant 0 is both the
% START of the behaviour, which has no past, and a point inside the cycle, which
% does. Future operators cannot tell those apart and do not need to. Past
% operators can, and the folded representation cannot express the difference -
% this is why past-LTL over lassos is normally done on an unfolding rather than
% on the loop itself.
%
% So `pred` never traverses the back edge: Y and Z are evaluated against the
% behaviour's real beginning, which is the correct reading at t=0, and t=0 is
% where sat/1 asks. Inside a cycle, under `always`, a past operator on a lasso
% describes the FIRST pass only. `past_on_lasso/1` below marks any trace where
% that caveat is live, so the situation is visible rather than silently wrong.
pred(T,T1,S) :- time(T,S), time(T1,S), T = T1+1.
has_pred(T,S) :- pred(T,_,S).

past_on_lasso(S) :- loop(_,S), previous(_,_).
past_on_lasso(S) :- loop(_,S), weakprevious(_,_).

% Reflexive-transitive closure of succ. On a lasso this is cyclic, which is what
% makes `always` and `eventually` quantify over the infinite unfolding without
% unrolling it.
reach(T,T,S)  :- time(T,S).
reach(T,T2,S) :- reach(T,T1,S), succ(T2,T1,S).

% True when S denotes an infinite behaviour rather than a finite prefix.
infinite(S) :- loop(_,S).
