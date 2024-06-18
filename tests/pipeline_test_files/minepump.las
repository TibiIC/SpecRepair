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

#modeh(consequent_exception(const(expression_v), var(time), var(trace))).
#modeh(consequent_holds(eventually,const(expression_v), var(time), var(trace))).
#modeb(1,root_consequent_holds(eventually, const(expression_v), var(time), var(trace)), (positive)).
#modeb(2,holds_at(const(temp_op_v), const(usable_atom), var(time), var(trace)), (positive)).
#modeb(2,not_holds_at(const(temp_op_v), const(usable_atom), var(time), var(trace)), (positive)).
#constant(usable_atom,highwater).
#constant(usable_atom,methane).
#constant(usable_atom,pump).
#constant(temp_op_v,current).
#constant(temp_op_v,next).
#constant(temp_op_v,prev).
#constant(temp_op_v,eventually).
#constant(expression_v, guarantee1_1).
#constant(expression_v, guarantee2_1).
#bias("
:- constraint.
:- head(consequent_exception(_,V1,V2)), body(holds_at(_,_,V3,V4)), (V3, V4) != (V1, V2).
:- head(consequent_exception(_,V1,V2)), body(not_holds_at(_,_,V3,V4)), (V3, V4) != (V1, V2).
:- body(holds_at(eventually,_,V1,_)), body(holds_at(eventually,_,V2,_)), V1 != V2.
:- head(consequent_exception(_,V1,V2)), body(holds_at(next,_,_,_)).
:- head(consequent_exception(_,V1,V2)), body(not_holds_at(next,_,_,_)).
:- head(consequent_exception(_,V1,V2)), body(holds_at(prev,_,_,_)).
:- head(consequent_exception(_,V1,V2)), body(not_holds_at(prev,_,_,_)).
:- head(consequent_exception(guarantee1_1,V1,V2)), body(holds_at(eventually,_,_,_)).
:- head(consequent_exception(guarantee1_1,V1,V2)), body(not_holds_at(eventually,_,_,_)).
:- head(consequent_exception(guarantee2_1,V1,V2)), body(holds_at(eventually,_,_,_)).
:- head(consequent_exception(guarantee2_1,V1,V2)), body(not_holds_at(eventually,_,_,_)).
:- head(consequent_exception(guarantee1_1,V1,V2)), body(holds_at(next,pump,V1,V2)).
:- head(consequent_exception(guarantee2_1,V1,V2)), body(not_holds_at(next,pump,V1,V2)).
:- head(consequent_exception(_,_,_)), body(root_consequent_holds(_,_,_,_)).
:- head(consequent_holds(_,_,_,_)), body(holds_at(_,_,_,_)).
:- head(consequent_holds(_,_,_,_)), body(not_holds_at(_,_,_,_)).
:- head(consequent_holds(eventually,E1,V1,V2)), body(root_consequent_holds(eventually,E2,V3,V4)), (E1,V1,V2) != (E2,V3,V4).
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
    common_weak(next,F,P,S),
    not not_holds_at_weak(next,F,P,S).

not_holds_at_weak(next,F,P,S):-
    common_weak(next,F,P,S),
    not holds_at_weak(next,F,P,S).

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

:- 	atom(F),
	trace(S),
	timepoint(T,S),
	temporal_operator(OP),
	not_holds_at(OP,F,T,S),
	holds_at(OP,F,T,S),
	OP != eventually.

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

%guarantee -- initial_guarantee
%	pump=false;

guarantee(initial_guarantee).

antecedent_holds(initial_guarantee,0,S):-
	trace(S),
	timepoint(0,S).

consequent_holds(current,initial_guarantee,0,S):-
	trace(S),
	timepoint(0,S),
	root_consequent_holds(current,initial_guarantee,0,S),
	not ev_temp_op(initial_guarantee).

root_consequent_holds(OP,initial_guarantee,0,S):-
	trace(S),
	timepoint(0,S),
	temporal_operator(OP),
	not_holds_at(OP,pump,0,S).

%guarantee -- guarantee1_1
%	G(highwater=true->next(pump=true));

guarantee(guarantee1_1).

antecedent_holds(guarantee1_1,T,S):-
	trace(S),
	timepoint(T,S),
	holds_at(current,highwater,T,S).

consequent_holds(next,guarantee1_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(next,guarantee1_1,T,S),
	not ev_temp_op(guarantee1_1).

root_consequent_holds(OP,guarantee1_1,T,S):-
	trace(S),
	timepoint(T,S),
	temporal_operator(OP),
	holds_at(OP,pump,T,S).

root_consequent_holds(OP,guarantee1_1,T,S):-
	trace(S),
	timepoint(T,S),
	temporal_operator(OP),
	consequent_exception(guarantee1_1,T,S).
%guarantee -- guarantee2_1
%	G(methane=true->next(pump=false));

guarantee(guarantee2_1).

antecedent_holds(guarantee2_1,T,S):-
	trace(S),
	timepoint(T,S),
	holds_at(current,methane,T,S).

consequent_holds(next,guarantee2_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(next,guarantee2_1,T,S),
	not ev_temp_op(guarantee2_1).

root_consequent_holds(OP,guarantee2_1,T,S):-
	trace(S),
	timepoint(T,S),
	temporal_operator(OP),
	not_holds_at(OP,pump,T,S).

root_consequent_holds(OP,guarantee2_1,T,S):-
	trace(S),
	timepoint(T,S),
	temporal_operator(OP),
	consequent_exception(guarantee2_1,T,S).
%---*** Signature  ***---

atom(highwater).
atom(methane).
atom(pump).


%---*** Violation Trace ***---

#pos({entailed(trace_name_0)},{},{
trace(trace_name_0).

timepoint(0,trace_name_0).
timepoint(1,trace_name_0).
timepoint(2,trace_name_0).
timepoint(3,trace_name_0).
next(1,0,trace_name_0).
next(2,1,trace_name_0).
next(3,2,trace_name_0).

not_holds_at(current,highwater,0,trace_name_0).
not_holds_at(current,methane,0,trace_name_0).
not_holds_at(current,pump,0,trace_name_0).
holds_at(current,highwater,1,trace_name_0).
not_holds_at(current,methane,1,trace_name_0).
not_holds_at(current,pump,1,trace_name_0).
holds_at(current,highwater,2,trace_name_0).
not_holds_at(current,methane,2,trace_name_0).
holds_at(current,pump,2,trace_name_0).
holds_at(current,highwater,3,trace_name_0).
holds_at(current,methane,3,trace_name_0).
holds_at(current,pump,3,trace_name_0).

}).

%---*** Violation Trace ***---

#pos({entailed(counter_strat_0)},{},{

% CS_Path: ini_S0_DEAD

trace(counter_strat_0).

timepoint(0,counter_strat_0).
timepoint(1,counter_strat_0).
next(1,0,counter_strat_0).

not_holds_at(highwater,0,counter_strat_0).
not_holds_at(methane,0,counter_strat_0).
not_holds_at(pump,0,counter_strat_0).
holds_at(highwater,1,counter_strat_0).
holds_at(methane,1,counter_strat_0).
holds_at(pump,1,counter_strat_0).

}).
