% Structural LTL-to-ASP. This file assembles the rules; nothing else.
% Paths are relative to this file, so clingo can be run from anywhere.
%
%   ltl/time.asp            succ, has_succ, has_pred, reach
%   ltl/propositional.asp   atomic, negate, and/or, implies
%   ltl/future.asp          next, until, eventually, always
%   ltl/past.asp            previous
%   ltl/satisfiability.asp  sat
%
% The traces, symbols, formula and the semantics(strong|weak) choice are inputs,
% not rules, so they live with the case rather than here. The original worked
% example is ltl/example.asp:
%
%   clingo ltl2asp_ext.asp ltl/example.asp

#include "ltl/time.asp".
#include "ltl/propositional.asp".
#include "ltl/future.asp".
#include "ltl/past.asp".
#include "ltl/satisfiability.asp".
