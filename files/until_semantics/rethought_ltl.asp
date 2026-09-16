%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Background Knowledge
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% ---*** Domain independent Axioms ***---

% Time Relations Definitions
after(T2,T1,S):- % Base Case
    next(T2,T1,S).

after(T3,T1,S):- % Recursive Step
    next(T2,T1,S),
    after(T3,T2,S).

prev(T1,T2,S):-
    next(T2,T1,S).

% Temporal Operator Definitions
temporal_operator(current).
temporal_operator(next).
temporal_operator(prev).
temporal_operator(always).
temporal_operator(until).

% Timepoint of operation definitions

timepoint_of_op(current,T1,T1,S) :-
    trace(S),
    timepoint(T1,S).

timepoint_of_op(next,T1,T2,S) :-
    trace(S),
    timepoint(T1,S),
    timepoint(T2,S),
    next(T2,T1,S).

timepoint_of_op(prev,T1,T2,S) :-
    trace(S),
    timepoint(T1,S),
    timepoint(T2,S),
    prev(T2,T1,S).

timepoint_of_op(always,T1,T1,S) :-
    trace(S),
    timepoint(T1,S).

timepoint_of_op(always,T1,T2,S) :-
    trace(S),
    timepoint(T1,S),
    timepoint(T2,S),
    after(T2,T1,S).

% ---*** Domain dependent Axioms ***---

%guarantee -- g1
%	G((a=true->b=true))

guarantee(g1)

g_formula_holds(g1,T1,S):-
    trace(S),
    timepoint(T1,S),
    temporal_operator(always),
    implication_formula_holds(current,g1,0,T2,S),
    timepoint(T2,S) : timepoint_of_op(always,T1,T2,S).

implication_formula_holds(OP,g1,0,T2,S):-
    implication_formula_holds_vacuously(OP,g1,0,T1,S).

implication_formula_holds(OP,g1,0,T2,S):-
    implication_formula_holds_non_vacuously(OP,g1,0,T1,S).

implication_formula_holds_vacuously(OP,g1,0,T1,S):-
    trace(S),
    timepoint(T1,S),
    temporal_operator(OP),
    not lhs_implication_formula_holds(g1,0,T2,S),
    timepoint(T2,S) : timepoint_of_op(OP,T1,T2,S).

implication_formula_holds_non_vacuously(OP,g1,0,T1,S):-
    trace(S),
    timepoint(T1,S),
    temporal_operator(OP),
    lhs_implication_formula_holds(g1,0,T2,S),
    rhs_implication_formula_holds(g1,0,T2,S),
    timepoint(T2,S) : timepoint_of_op(OP,T1,T2,S).

lhs_implication_formula_holds(g1,0,T1,S):-
    trace(S),
    timepoint(T1,S),
    holds_at(a,T1,S).

rhs_implication_formula_holds(g1,0,T1,S):-
    trace(S),
    timepoint(T1,S),
    holds_at(b,T1,S).