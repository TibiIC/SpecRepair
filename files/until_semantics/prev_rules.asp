% PREV rules for ltl2asp_ext.asp - drop these in when you add past operators.
%
% Two operators, not one, and they are NOT the mirror of next/weak-next.
% A finite trace is a PREFIX: the future is open, so `next` needs a weak reading
% at the end; the past is CLOSED, because t=0 really is the beginning of the
% behaviour rather than a window onto unseen earlier states. So the strong/weak
% split for PREV is not about the trace being cut short - both readings are
% legitimate operators that differ on what "before the beginning" means, and
% both are primitive because neither defines the other.
%
%   prev(X,F)      Y F, "yesterday", strong.  At t=0: FALSE.
%   weakprev(X,F)  Z F, "weak yesterday".     At t=0: TRUE.
%
% They are duals:  !Y(f) === Z(!f).  That identity is why !PREV(x) cannot be
% rewritten as PREV(!x) - the correct dual needs the weak operator, which is
% exactly what a language with only one PREV cannot express.
%
% Spectra's PREV is Y. Measured, not assumed: G(PREV(a)) is unrealizable in
% Spectra while G(a) is realizable, which can only happen if PREV is false at
% t=0.
%
% Reference: Lichtenstein, Pnueli & Zuck, "The Glory of the Past" (1985);
% Manna & Pnueli, "The Temporal Logic of Reactive and Concurrent Systems:
% Specification" (1992), which write them as (-) and weak (-).

% Y f : the previous instant exists and f held there.
holds(T,X,S) :- prev(X,F), time(T,S), T > 0, holds(T-1,F,S).

% Z f : same, plus it holds vacuously at the very beginning.
holds(T,X,S) :- weakprev(X,F), time(T,S), T > 0, holds(T-1,F,S).
holds(T,X,S) :- weakprev(X,F), time(T,S), T = 0.

% Note there is deliberately no `semantics(strong)` / `semantics(weak)` guard
% here. Unlike next/eventually/until, the choice is not a reading of the same
% operator forced by the trace being finite - it is which of two different
% operators the formula names. A formula says Y or it says Z.
