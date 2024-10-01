#ilasp_script

max_solutions = 10

ilasp.cdilp.initialise()
solve_result = ilasp.cdilp.solve()

c_egs = None
if solve_result is not None:
  c_egs = ilasp.find_all_counterexamples(solve_result)

conflict_analysis_strategy = {
  'positive-strategy': 'all-ufs',
  'negative-strategy': 'single-as',
  'brave-strategy':    'all-ufs',
  'cautious-strategy': 'single-as-pair'
}

solution_count = 0

while solution_count < max_solutions and solve_result is not None:
  if c_egs:
    ce = ilasp.get_example(c_egs[0]['id'])
    constraint = ilasp.cdilp.analyse_conflict(solve_result['hypothesis'], ce['id'], conflict_analysis_strategy)
  
    # An example with recorded penalty of 0 is in reality an example with an
    # infinite penalty, meaning that it must be covered. Constraint propagation is,
    # therefore, unnecessary.
    if ce['penalty'] != -1:
      c_eg_ids = list(map(lambda x: x['id'], c_egs))
      prop_egs = []
      if ce['type'] == 'positive':
        prop_egs = ilasp.cdilp.propagate_constraint(constraint, c_eg_ids, {'select-examples': ['positive'], 'strategy': 'cdpi-implies-constraint'})
      elif ce['type'] == 'negative':
        prop_egs = ilasp.cdilp.propagate_constraint(constraint, c_eg_ids, {'select-examples': ['negative'], 'strategy': 'neg-constraint-implies-cdpi'})
      elif ce['type'] == 'brave-order':
        prop_egs = ilasp.cdilp.propagate_constraint(constraint, c_eg_ids, {'select-examples': ['brave-order'],    'strategy': 'cdoe-implies-constraint'})
      else:
        prop_egs = [ce['id']]
  
      ilasp.cdilp.add_coverage_constraint(constraint, prop_egs)
  
    else:
      ilasp.cdilp.add_coverage_constraint(constraint, [ce['id']])

  solve_result = ilasp.cdilp.solve()

  if solve_result is not None:
    c_egs = ilasp.find_all_counterexamples(solve_result)
    if not c_egs:
      solution_count+=1
      debug_print(f'Solution {solution_count} (score {solve_result["expected_score"]})')
      print(ilasp.hypothesis_to_string(solve_result['hypothesis']))
      new_constraint_body = map(lambda x: f'nge_HYP({x})', solve_result["hypothesis"])
      # if you want to rule allow non-subset-minimal solutions uncomment this line and comment the one below.
      # new_constraint = f':- {",".join(new_constraint_body)}, #count' + "{ H : nge_HYP(H) }" + f' = {len(solve_result["hypothesis"])}.\n'
      new_constraint = f':- {",".join(new_constraint_body)}.\n'
      ilasp.cdilp.add_to_meta_program(new_constraint)


if solution_count == 0:
  print('UNSATISFIABLE')

ilasp.stats.print_timings()

#end.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Mode Declaration
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#modeh(antecedent_exception(const(expression_v), var(time), var(trace))).
#modeh(consequent_holds(eventually,const(expression_v), var(time), var(trace))).
#modeb(1,root_consequent_holds(eventually, const(expression_v), const(index), var(time), var(trace)), (positive)).
#modeb(2,holds_at(const(temp_op_v), const(usable_atom), var(time), var(trace)), (positive)).
#modeb(2,not_holds_at(const(temp_op_v), const(usable_atom), var(time), var(trace)), (positive)).
#constant(usable_atom,r1).
#constant(usable_atom,r2).
#constant(usable_atom,a).
#constant(usable_atom,g1).
#constant(usable_atom,g2).
#constant(index,0).
#constant(temp_op_v,current).
#constant(temp_op_v,next).
#constant(temp_op_v,prev).
#constant(temp_op_v,eventually).
#constant(expression_v, a_always).
#bias("
:- constraint.
:- head(antecedent_exception(_,V1,V2)), body(holds_at(_,_,V3,V4)), (V3, V4) != (V1, V2).
:- head(antecedent_exception(_,V1,V2)), body(not_holds_at(_,_,V3,V4)), (V3, V4) != (V1, V2).
:- body(holds_at(eventually,_,V1,_)), body(holds_at(eventually,_,V2,_)), V1 != V2.
:- head(antecedent_exception(_,V1,V2)), body(holds_at(next,_,_,_)).
:- head(antecedent_exception(_,V1,V2)), body(not_holds_at(next,_,_,_)).
:- head(antecedent_exception(_,V1,V2)), body(holds_at(prev,_,_,_)).
:- head(antecedent_exception(_,V1,V2)), body(not_holds_at(prev,_,_,_)).
:- head(antecedent_exception(a_always,V1,V2)), body(holds_at(eventually,_,_,_)).
:- head(antecedent_exception(a_always,V1,V2)), body(not_holds_at(eventually,_,_,_)).
:- head(antecedent_exception(_,_,_)), body(root_consequent_holds(_,_,_,_,_)).
:- head(consequent_holds(_,_,_,_)), body(holds_at(_,_,_,_)).
:- head(consequent_holds(_,_,_,_)), body(not_holds_at(_,_,_,_)).
:- head(consequent_holds(eventually,E1,V1,V2)), body(root_consequent_holds(eventually,E2,_,V3,V4)), (E1,V1,V2) != (E2,V3,V4).
").

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

%assumption -- a_always
%	G(a=true);

assumption(a_always).

antecedent_holds(a_always,T,S):-
	trace(S),
	timepoint(T,S),
	not antecedent_exception(a_always,T,S).

consequent_holds(current,a_always,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(current,a_always,0,T,S),
	not ev_temp_op(a_always).

root_consequent_holds(OP,a_always,0,T,S):-
	trace(S),
	timepoint(T,S),
	temporal_operator(OP),
	holds_at(OP,a,T,S).

%---*** Signature  ***---

atom(a).
atom(g1).
atom(g2).
atom(r1).
atom(r2).


%---*** Violation Trace ***---

#pos({entailed(trace_name_0)},{},{

trace(trace_name_0).
timepoint(0,trace_name_0).
not_holds_at(a,0,trace_name_0).
not_holds_at(g1,0,trace_name_0).
not_holds_at(g2,0,trace_name_0).
not_holds_at(r1,0,trace_name_0).
not_holds_at(r2,0,trace_name_0).
}).
