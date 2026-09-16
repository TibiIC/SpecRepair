% Past operators: Y (previous) and Z (weakprevious).
%
% These are TWO OPERATORS, not two readings of one, and that is why neither is
% guarded by semantics(strong|weak). The distinction is not caused by a trace
% being cut short:
%
%   * the FUTURE of a finite prefix is unknown, so `next` at the end genuinely
%     needs a reading, chosen by the toggle;
%   * the PAST of instant 0 is not unknown - there is nothing before the
%     beginning of a behaviour. t=0 is the first instant even when the behaviour
%     is infinite. Both operators are total; they simply disagree about what
%     "before the beginning" evaluates to.
%
%     previous(X,F)      Y F   at t=0 -> FALSE
%     weakprevious(X,F)  Z F   at t=0 -> TRUE
%
% They are duals:  !Y(f) === Z(!f)  and  !Z(f) === Y(!f).  Neither defines the
% other without the boundary case, which is why past-LTL takes both as
% primitive (Lichtenstein, Pnueli & Zuck, "The Glory of the Past", 1985;
% Manna & Pnueli 1992, where they are written (-) and weak (-)).
%
% Consequence worth stating: a language with only ONE previous operator cannot
% express the negation of the other. That is exactly why the GR(1) translation
% in spec_repair leaves !PREV(x) as an opaque literal instead of rewriting it to
% PREV(!x) - the correct dual is Z(!x), which it has no way to write.
%
% Spectra's PREV is Y. Measured, not assumed: G(PREV(a)) is unrealizable in
% Spectra while G(a) is realizable, and with `a` a system variable the only
% proposition the system cannot satisfy is PREV(a) at t=0.
%
% Tying either of these to semantics(weak) would make Y silently become Z
% whenever the future reading changed, and would make the duality unwriteable,
% since a single formula could then not name both.
%
% Both use `pred`, not `succ`: see ltl/time.asp for why the loop edge must not
% be traversed backwards, and `past_on_lasso/1` for how the remaining caveat is
% surfaced.

holds(T,X,S) :- previous(X,F),     pred(T,T1,S), holds(T1,F,S).

holds(T,X,S) :- weakprevious(X,F), pred(T,T1,S), holds(T1,F,S).
holds(T,X,S) :- weakprevious(X,F), time(T,S), not has_pred(T,S).
