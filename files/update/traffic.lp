%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Background Knowledge
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% ---*** Domain independent Axioms ***---

% Current timestep definitions
temporal_operator(current).

holds_at(current,F,P,S):-
    holds_at(F,P,S).

not_holds_at(current,F,P,S):-
    not_holds_at(F,P,S).

% Next timestep definitions
temporal_operator(next).

next_timepoint_exists(T1,S):-
    next(T2,T1,S).

% If the next time point does not exist,
% atom F holds and not holds weakly
common_weak(next,F,P,S):-
    trace(S),
    atom(F),
    timepoint(P,S),
    not next_timepoint_exists(P,S).

holds_at_weak(next,F,P,S):-
    common_weak(next,F,P,S).

not_holds_at_weak(next,F,P,S):-
    common_weak(next,F,P,S).

holds_at(next,F,P,S):-  % Weak Definition
    holds_at_weak(next,F,P,S).

not_holds_at(next,F,P,S):-  % Weak Definition
    not_holds_at_weak(next,F,P,S).

holds_at(next,F,P,S):- % Strong Definition
	next(P2,P,S),
	holds_at(current,F,P2,S).

not_holds_at(next,F,P,S):- % Strong Definition
	next(P2,P,S),
	not_holds_at(current,F,P2,S).

% Prev timestep definitions
temporal_operator(prev).

holds_at(prev,F,P,S):-
	next(P,P2,S),
	holds_at(current,F,P2,S).

not_holds_at(prev,F,P,S):-
	next(P,P2,S),
	not_holds_at(current,F,P2,S).

% Eventually timestep definitions
temporal_operator(eventually).

after(T2,T1,S):- % Base Case
    next(T2,T1,S).

after(T3,T1,S):- % Recursive Step
    next(T2,T1,S),
    after(T3,T2,S).

holds_at_weak(eventually,F,P,S):-
    trace(S),
    atom(F),
    timepoint(P,S),
    not next_timepoint_exists(P,S).

holds_at(eventually,F,P,S):- % Weak Definition
    holds_at_weak(eventually,F,P,S).

not_holds_at(eventually,F,P,S):- % Weak Definition
    holds_at_weak(eventually,F,P,S).

holds_at(eventually,F,P,S):- % Base Case (holds now)
    trace(S),
    atom(F),
    timepoint(P,S),
    holds_at(current,F,P,S).

holds_at(eventually,F,P,S):- % Strong Definition
    trace(S),
    atom(F),
    timepoint(P,S),
    after(P2,P,S),
    holds_at(current,F,P2,S).

not_holds_at(eventually,F,P,S):- % Base Case (not_holds now)
    trace(S),
    atom(F),
    timepoint(P,S),
    not_holds_at(current,F,P,S).

not_holds_at(eventually,F,P,S):- % Strong Definition
    trace(S),
    atom(F),
    timepoint(P,S),
    after(P2,P,S),
    not_holds_at(current,F,P2,S).

eq(T1,T2):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	T1 == T2.

:- 	contradiction_holds(current,F,T,S).
:- 	contradiction_holds(next,F,T,S),
    next_timepoint_exists(T,S).
:-  contradiction_holds(prev,F,T,S),
    not exist_diff_prev_timepoints(T,S).

contradiction_holds(OP,F,T,S) :-
    atom(F),
	trace(S),
	timepoint(T,S),
    not_holds_at(OP,F,T,S),
    holds_at(OP,F,T,S).

exist_diff_prev_timepoints(T,S) :-
	trace(S),
	timepoint(T,S),
	timepoint(T1,S),
	timepoint(T2,S),
	next(T,T1,S),
	next(T,T2,S),
	T1 != T2.

ev_temp_op(E) :-
    trace(S),
	timepoint(T,S),
    consequent_holds(eventually,E,T,S).

holds_non_vacuously(E, T, S):-
	exp(E),
	trace(S),
	timepoint(T,S),
	temporal_operator(OP),
	antecedent_holds(E, T, S),
	consequent_holds(OP, E, T, S).

holds_vacuously(E, T, S):-
	exp(E),
	trace(S),
	timepoint(T,S),
	not antecedent_holds(E, T, S).

holds(G, T, S):-
	timepoint(T,S),
	trace(S),
	exp(G),
	holds_non_vacuously(G, T, S).

holds(G, T, S):-
	timepoint(T,S), trace(S),
	exp(G),
	holds_vacuously(G, T, S).

violation_holds(G,T,S):-
	exp(G),
	trace(S),
	timepoint(T,S),
	not holds(G,T,S).

violated(S):-
	exp(G),
	trace(S),
	timepoint(T,S),
	violation_holds(G,T,S).

entailed(S):-
	trace(S),
	not violated(S).

exp(E):-
	guarantee(E).

exp(E):-
	assumption(E).

% ---*** Domain dependent Axioms ***---

%assumption -- no_emergency_often
%	GF(emergency=false);

assumption(no_emergency_often).

antecedent_holds(no_emergency_often,T,S):-
	trace(S),
	timepoint(T,S).

consequent_holds(eventually,no_emergency_often,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(eventually,no_emergency_often,0,T,S).

root_consequent_holds(OP,no_emergency_often,0,T,S):-
	trace(S),
	timepoint(T,S),
	temporal_operator(OP),
	not_holds_at(OP,emergency,T,S).

%assumption -- carA_idle_when_red
%	G(carA=true&greenA=false->next(carA=true));

assumption(carA_idle_when_red).

antecedent_holds(carA_idle_when_red,T,S):-
	trace(S),
	timepoint(T,S),
	root_antecedent_holds(current,carA_idle_when_red,0,T,S).

root_antecedent_holds(OP,carA_idle_when_red,0,T,S):-
	holds_at(OP,carA,T,S),
	not_holds_at(OP,greenA,T,S).

consequent_holds(next,carA_idle_when_red,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(next,carA_idle_when_red,0,T,S),
	not ev_temp_op(carA_idle_when_red).

root_consequent_holds(OP,carA_idle_when_red,0,T,S):-
	trace(S),
	timepoint(T,S),
	temporal_operator(OP),
	holds_at(OP,carA,T,S).

%assumption -- carB_idle_when_red
%	G(carB=true&greenB=false->next(carB=true));

assumption(carB_idle_when_red).

antecedent_holds(carB_idle_when_red,T,S):-
	trace(S),
	timepoint(T,S),
	root_antecedent_holds(current,carB_idle_when_red,0,T,S).

root_antecedent_holds(OP,carB_idle_when_red,0,T,S):-
    temporal_operator(OP),
	holds_at(OP,carB,T,S),
	not_holds_at(OP,greenB,T,S).

consequent_holds(next,carB_idle_when_red,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(next,carB_idle_when_red,0,T,S),
	not ev_temp_op(carB_idle_when_red).

root_consequent_holds(OP,carB_idle_when_red,0,T,S):-
	trace(S),
	timepoint(T,S),
	temporal_operator(OP),
	holds_at(OP,carB,T,S).

%assumption -- carA_moves_when_green
%	G(carA=true&greenA=true->next(carA=false));

assumption(carA_moves_when_green).

antecedent_holds(carA_moves_when_green,T,S):-
	trace(S),
	timepoint(T,S),
	root_antecedent_holds(current,carA_moves_when_green,0,T,S).

root_antecedent_holds(OP,carA_moves_when_green,0,T,S):-
    temporal_operator(OP),
	holds_at(OP,carA,T,S),
	holds_at(OP,greenA,T,S).

consequent_holds(next,carA_moves_when_green,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(next,carA_moves_when_green,0,T,S),
	not ev_temp_op(carA_moves_when_green).

root_consequent_holds(OP,carA_moves_when_green,0,T,S):-
	trace(S),
	timepoint(T,S),
	temporal_operator(OP),
	not_holds_at(OP,carA,T,S).

%assumption -- carB_moves_when_green
%	G(carB=true&greenB=true->next(carB=false));

assumption(carB_moves_when_green).

antecedent_holds(carB_moves_when_green,T,S):-
	trace(S),
	timepoint(T,S),
	root_antecedent_holds(current,carB_moves_when_green,0,T,S).

root_antecedent_holds(OP,carB_moves_when_green,0,T,S):-
    temporal_operator(OP),
	holds_at(OP,carB,T,S),
	holds_at(OP,greenB,T,S).

consequent_holds(next,carB_moves_when_green,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(next,carB_moves_when_green,0,T,S),
	not ev_temp_op(carB_moves_when_green).

root_consequent_holds(OP,carB_moves_when_green,0,T,S):-
	trace(S),
	timepoint(T,S),
	temporal_operator(OP),
	not_holds_at(OP,carB,T,S).

%guarantee -- lights_not_both_red
%	G(greenA=false|greenB=false);

guarantee(lights_not_both_red).

antecedent_holds(lights_not_both_red,T,S):-
	trace(S),
	timepoint(T,S).

consequent_holds(current,lights_not_both_red,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(current,lights_not_both_red,0,T,S),
	not ev_temp_op(lights_not_both_red).

root_consequent_holds(OP,lights_not_both_red,0,T,S):-
	trace(S),
	timepoint(T,S),
	temporal_operator(OP),
	not_holds_at(OP,greenA,T,S).

root_consequent_holds(OP,lights_not_both_red,0,T,S):-
	trace(S),
	timepoint(T,S),
	temporal_operator(OP),
	not_holds_at(OP,greenB,T,S).

%guarantee -- carA_leads_to_greenA
%	G(carA=true->F(greenA=true));

guarantee(carA_leads_to_greenA).

antecedent_holds(carA_leads_to_greenA,T,S):-
	trace(S),
	timepoint(T,S),
	root_antecedent_holds(current,carA_leads_to_greenA,0,T,S).

root_antecedent_holds(OP,carA_leads_to_greenA,0,T,S):-
    temporal_operator(OP),
	holds_at(OP,carA,T,S).

consequent_holds(eventually,carA_leads_to_greenA,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(eventually,carA_leads_to_greenA,0,T,S).

root_consequent_holds(OP,carA_leads_to_greenA,0,T,S):-
	trace(S),
	timepoint(T,S),
	temporal_operator(OP),
	holds_at(OP,greenA,T,S).

%guarantee -- carB_lead_to_greenB
%	G(carB=true->F(greenB=true));

guarantee(carB_lead_to_greenB).

antecedent_holds(carB_lead_to_greenB,T,S):-
	trace(S),
	timepoint(T,S),
	root_antecedent_holds(current,carB_lead_to_greenB,0,T,S).

root_antecedent_holds(OP,carB_lead_to_greenB,0,T,S):-
    temporal_operator(OP),
	holds_at(OP,carB,T,S).

consequent_holds(eventually,carB_lead_to_greenB,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(eventually,carB_lead_to_greenB,0,T,S).

root_consequent_holds(OP,carB_lead_to_greenB,0,T,S):-
	trace(S),
	timepoint(T,S),
	temporal_operator(OP),
	holds_at(OP,greenB,T,S).

%guarantee -- red_when_emergency
%	G(emergency=true->greenA=false&greenB=false);

guarantee(red_when_emergency).

antecedent_holds(red_when_emergency,T,S):-
	trace(S),
	timepoint(T,S),
	root_antecedent_holds(current,red_when_emergency,0,T,S).

root_antecedent_holds(OP,red_when_emergency,0,T,S):-
    temporal_operator(OP),
	holds_at(OP,emergency,T,S).

consequent_holds(current,red_when_emergency,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(current,red_when_emergency,0,T,S),
	not ev_temp_op(red_when_emergency).

root_consequent_holds(OP,red_when_emergency,0,T,S):-
	trace(S),
	timepoint(T,S),
	temporal_operator(OP),
	not_holds_at(OP,greenA,T,S),
	not_holds_at(OP,greenB,T,S).

%---*** Signature  ***---

atom(carA).
atom(carB).
atom(emergency).
atom(greenA).
atom(greenB).


%---*** Violation Trace ***---

trace(trace_name_0).

timepoint(0,trace_name_0).
timepoint(1,trace_name_0).
next(1,0,trace_name_0).

holds_at(carB,0,trace_name_0).
holds_at(carA,0,trace_name_0).
holds_at(emergency,0,trace_name_0).
not_holds_at(greenA,0,trace_name_0).
not_holds_at(greenB,0,trace_name_0).
not_holds_at(carA,1,trace_name_0).
not_holds_at(carB,1,trace_name_0).
not_holds_at(emergency,1,trace_name_0).
not_holds_at(greenA,1,trace_name_0).
not_holds_at(greenB,1,trace_name_0).

#show violation_holds/3.

#show assumption/1.

#show guarantee/1.

#show entailed/1.
