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

#modeh(consequent_holds(const(expression_v), var(time), var(trace))).
#modeh(ev_temp_op(const(expression_v))).
#modeb(1,root_consequent_holds(eventually, const(expression_v), var(time), var(trace)), (positive)).
#constant(index,0..1).
#constant(expression_v, assumption2_1).
#bias("
    :- constraint.
    :- head(consequent_holds(E1,V1,V2)), body(root_consequent_holds(_,E2,V3,V4)), (E1,V1,V2) != (E2,V3,V4).
    :- head(ev_temp_op(_)), body(root_consequent_holds(_,_,_,_)).
    attribute(in_head(X)) :- head(X).
").
#inject("
  all_active.
  attribute(X) :- active(R), attribute(R, X).
  :- attribute(in_head(consequent_holds(E,_,_))), not attribute(in_head(ev_temp_op(E))).
").

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
temporal_operator(eventually).

% Timepoint of operation definitions

timepoint_of_op(current,T1,T1,S) :-
    trace(S),
    timepoint(T1,S),
    not weak_timepoint(T1,S).

timepoint_of_op(next,T1,T2,S) :-
    trace(S),
    timepoint(T1,S),
    not weak_timepoint(T1,S),
    timepoint(T2,S),
    next(T2,T1,S).

timepoint_of_op(prev,T1,T2,S) :-
    trace(S),
    timepoint(T1,S),
    timepoint(T2,S),
    not weak_timepoint(T1,S),
    not weak_timepoint(T2,S),
    prev(T2,T1,S).

timepoint_of_op(eventually,T1,T1,S) :-
    trace(S),
    timepoint(T1,S),
    not weak_timepoint(T1,S).

timepoint_of_op(eventually,T1,T2,S) :-
    trace(S),
    timepoint(T1,S),
    not weak_timepoint(T1,S),
    timepoint(T2,S),
    after(T2,T1,S).

% Weak Timepoint Definitions

weak_timepoint_atom(weak_t).

next_timepoint_exists(T1,S):-
    timepoint(T1,S),
    timepoint(T2,S),
    not weak_timepoint(T2,S),
    next(T2,T1,S).

weak_timepoint(X,S):-
    weak_timepoint_atom(X),
    timepoint(T,S),
    not next_timepoint_exists(T,S).

timepoint(T,S):-
    trace(S),
    weak_timepoint(T,S).

next(X,T,S):-
    weak_timepoint(X,S),
    timepoint(T,S),
    not weak_timepoint(T,S),
    not next_timepoint_exists(T,S).

holds_at(A,T,S):-
    atom(A),
    weak_timepoint(T,S),
    trace(S).

not_holds_at(A,T,S):-
    atom(A),
    weak_timepoint(T,S),
    trace(S).

root_consequent_holds(OP,E,T,S):-
    root_consequent_holds(OP,E,I,T,S).

% GR(1) Rules

:- 	contradiction_holds(A,T,S).

contradiction_holds(A,T,S) :-
    atom(A),
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
    not_holds_at(A,T,S),
    holds_at(A,T,S).

holds_non_vacuously(E, T, S):-
	exp(E),
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	antecedent_holds(E, T, S),
	consequent_holds(E, T, S).

holds_vacuously(E, T, S):-
	exp(E),
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	not antecedent_holds(E, T, S).

holds(G, T, S):-
	timepoint(T,S),
	not weak_timepoint(T,S),
	trace(S),
	exp(G),
	holds_non_vacuously(G, T, S).

holds(G, T, S):-
	timepoint(T,S),
	not weak_timepoint(T,S),
	trace(S),
	exp(G),
	holds_vacuously(G, T, S).

violation_holds(G,T,S):-
	exp(G),
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	not holds(G,T,S).

violated(S):-
	exp(G),
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	violation_holds(G,T,S).

entailed(S):-
	trace(S),
	not violated(S).

exp(E):-
	guarantee(E).

exp(E):-
	assumption(E).

% ---*** Domain dependent Axioms ***---

%assumption -- initial_assumption
%	highwater=false&methane=false;

assumption(initial_assumption).

antecedent_holds(initial_assumption,0,S):-
	trace(S),
	timepoint(0,S).

consequent_holds(initial_assumption,0,S):-
	trace(S),
	timepoint(0,S),
	root_consequent_holds(current,initial_assumption,0,0,S).

root_consequent_holds(OP,initial_assumption,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	not weak_timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(highwater,T2,S),
	not_holds_at(methane,T2,S).

%assumption -- assumption1_1
%	G(PREV(pump=true)&pump=true->next(highwater=false));

assumption(assumption1_1).

antecedent_holds(assumption1_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_antecedent_holds(prev,assumption1_1,0,T,S),
	root_antecedent_holds(current,assumption1_1,1,T,S).

root_antecedent_holds(OP,assumption1_1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	not weak_timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(pump,T2,S).

root_antecedent_holds(OP,assumption1_1,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	not weak_timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(pump,T2,S).

consequent_holds(assumption1_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(next,assumption1_1,0,T,S).

root_consequent_holds(OP,assumption1_1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	not weak_timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(highwater,T2,S).

%assumption -- assumption2_1
%	G(highwater=false|methane=false);

assumption(assumption2_1).

antecedent_holds(assumption2_1,T,S):-
	trace(S),
	timepoint(T,S),
	not antecedent_exception(assumption2_1,0,T,S).

consequent_holds(assumption2_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(current,assumption2_1,0,T,S),
	not ev_temp_op(assumption2_1).

root_consequent_holds(OP,assumption2_1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	not weak_timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(highwater,T2,S).

consequent_holds(assumption2_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(current,assumption2_1,1,T,S),
	not ev_temp_op(assumption2_1).

root_consequent_holds(OP,assumption2_1,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	not weak_timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(methane,T2,S).

%---*** Signature  ***---

atom(highwater).
atom(methane).
atom(pump).



%---*** Violation Trace ***---

#pos({entailed(trace_name_0)},{},{

trace(trace_name_0).
timepoint(0,trace_name_0).
timepoint(1,trace_name_0).
next(1,0,trace_name_0).

not_holds_at(highwater,0,trace_name_0).
not_holds_at(methane,0,trace_name_0).
not_holds_at(pump,0,trace_name_0).
holds_at(highwater,1,trace_name_0).
holds_at(methane,1,trace_name_0).
not_holds_at(pump,1,trace_name_0).
}).
