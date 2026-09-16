% Structural LTL-to-ASP: a formula is an AST of facts, evaluated over traces.
%
% Rules are split by concern; this file only assembles them. Paths are relative
% to this file, so clingo can be run from anywhere.
%
%   ltl/time.asp            succ/first/last/reach, and lasso support
%   ltl/propositional.asp   atomic, negate, and/or, implies
%   ltl/future.asp          next, until, eventually, always  (+ strong/weak)
%   ltl/past.asp            previous (Y), weakprevious (Z)
%   ltl/satisfiability.asp  sat/1 and unsat/1
%
% A formula is a tree of numbered nodes:
%
%   root(N).                     the whole formula
%   atomic(N,a).  true(N).
%   negate(N,F).  conjunction(N,F)...  disjunction(N,F)...
%   implies(N,F,G).  until(N,F,G).
%   next(N,F).  previous(N,F).  weakprevious(N,F).
%   eventually(N,F).  always(N,F).
%
% A trace is named, has instants, and lists only the atoms TRUE at each:
%
%   trace_name(s).  time(0..2,s).  trace(1,a,s).
%   loop(1,s).                     OPTIONAL: makes s infinite, looping to 1
%
% Choose a reading for the future operators at the end of a FINITE trace:
%
%   semantics(strong).   the trace must show it
%   semantics(weak).     the trace must not refute it
%
% A lasso needs neither - its last instant has a successor, so the weak rules
% never fire. Exactly one semantics/1 fact should be present for finite traces.

#include "ltl/time.asp".
#include "ltl/propositional.asp".
#include "ltl/future.asp".
#include "ltl/past.asp".
#include "ltl/satisfiability.asp".
