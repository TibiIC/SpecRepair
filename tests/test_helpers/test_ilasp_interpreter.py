from typing import List, Tuple
from unittest import TestCase

from spec_repair.helpers.adaptation_learned import Adaptation
from spec_repair.helpers.ilasp_interpreter import ILASPInterpreter

def filter_useful_adaptations(potential_adaptations: List[Tuple[int, List[Adaptation]]]) -> List[List[Adaptation]]:
    ev_adaptations = [(score, adaptations) for score, adaptations in potential_adaptations if "ev_temp_op" in [adaptation.type for adaptation in adaptations] ]
    other_adaptations = [(score, adaptations) for score, adaptations in potential_adaptations if "ev_temp_op" not in [adaptation.type for adaptation in adaptations] ]
    top_adaptations = ([adaptations for score, adaptations in other_adaptations if score == min(other_adaptations, key=lambda x: x[0])[0]] +
                       [adaptations for score, adaptations in ev_adaptations if score == min(ev_adaptations, key=lambda x: x[0])[0]])
    return top_adaptations

class TestILASPInterpreter(TestCase):
    def test_extract_learned_possible_adaptations_raw(self):
        text = \
"""\
%% Solution 1 (score 1) 
ev_temp_op(assumption2_1).

%% Solution 2 (score 3) 
antecedent_exception(assumption2_1,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); not_holds_at(pump,V1,V2).

%% Solution 3 (score 3) 
antecedent_exception(assumption2_1,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(methane,V1,V2).

%% Solution 4 (score 3) 
antecedent_exception(assumption2_1,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(highwater,V1,V2).

%% Solution 5 (score 4) 
antecedent_exception(assumption2_1,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(highwater,V1,V2); holds_at(methane,V1,V2).

%% Solution 6 (score 4) 
antecedent_exception(assumption2_1,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(methane,V1,V2); not_holds_at(pump,V1,V2).

%% Solution 7 (score 4) 
antecedent_exception(assumption2_1,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(highwater,V1,V2); not_holds_at(pump,V1,V2).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Pre-processing                          : 0.031s
%% Hypothesis Space Generation             : 0.176s
%% Conflict analysis                       : 0.058s
%%   - Positive Examples                   : 0.058s
%% Counterexample search                   : 0.024s
%%   - CDOEs                               : 0s
%%   - CDPIs                               : 0.017s
%% Hypothesis Search                       : 0.007s
%% Total                                   : 0.296s
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\
"""

        solution = ILASPInterpreter.extract_learned_possible_adaptations_raw(text)
        self.assertEqual(len(solution), 7)
        expected_scores = [1, 3, 3, 3, 4, 4, 4]
        for i, (score, adaptation) in enumerate(solution):
            self.assertEqual(score, expected_scores[i])
            self.assertEqual(len(adaptation), 1)

        self.assertEqual(solution[0][1][0],
                         "ev_temp_op(assumption2_1).")
        self.assertEqual(solution[1][1][0],
                         "antecedent_exception(assumption2_1,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); not_holds_at(pump,V1,V2).")
        self.assertEqual(solution[2][1][0],
                         "antecedent_exception(assumption2_1,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(methane,V1,V2).")
        self.assertEqual(solution[3][1][0],
                         "antecedent_exception(assumption2_1,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(highwater,V1,V2).")
        self.assertEqual(solution[4][1][0],
                         "antecedent_exception(assumption2_1,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(highwater,V1,V2); holds_at(methane,V1,V2).")
        self.assertEqual(solution[5][1][0],
                         "antecedent_exception(assumption2_1,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(methane,V1,V2); not_holds_at(pump,V1,V2).")
        self.assertEqual(solution[6][1][0],
                         "antecedent_exception(assumption2_1,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(highwater,V1,V2); not_holds_at(pump,V1,V2).")

    def test_filter_adaptations(self):
        adaptations = [
            (1, [Adaptation("ev_temp_op", "assumption2_1", 0, [("current", "methane=true")])]),
            (3, [Adaptation("antecedent_exception", "assumption2_1", 0, [("current", "methane=true")])]),
            (3, [Adaptation("antecedent_exception", "assumption2_1", 0, [("current", "highwater=true")])]),
            (3, [Adaptation("antecedent_exception", "assumption2_1", 0, [("current", "pump=true")])]),
            (4, [Adaptation("antecedent_exception", "assumption2_1", 0, [("current", "methane=true")])]),
            (4, [Adaptation("antecedent_exception", "assumption2_1", 0, [("current", "highwater=true")])]),
            (4, [Adaptation("antecedent_exception", "assumption2_1", 0, [("current", "pump=true")])]),
        ]
        top_adaptations = filter_useful_adaptations(adaptations)
        self.assertEqual(len(top_adaptations), 4)

        self.assertEqual(top_adaptations[0][0], Adaptation("antecedent_exception", "assumption2_1", 0, [("current", "methane=true")]))
        self.assertEqual(top_adaptations[1][0], Adaptation("antecedent_exception", "assumption2_1", 0, [("current", "highwater=true")]))
        self.assertEqual(top_adaptations[2][0], Adaptation("antecedent_exception", "assumption2_1", 0, [("current", "pump=true")]))
        self.assertEqual(top_adaptations[3][0], Adaptation("ev_temp_op", "assumption2_1", 0, [("current", "methane=true")]))


    def test_extract_learned_possible_adaptations_raw_2(self):
        text = \
"""\
%% Solution 1 (score 6) 
antecedent_exception(carB_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(carA,V1,V2).
antecedent_exception(carA_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); not_holds_at(greenB,V1,V2).

%% Solution 2 (score 6) 
antecedent_exception(carA_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); not_holds_at(greenA,V1,V2).
antecedent_exception(carB_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(emergency,V1,V2).

%% Solution 3 (score 6) 
antecedent_exception(carB_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(carB,V1,V2).
antecedent_exception(carA_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(carB,V1,V2).

%% Solution 4 (score 6) 
antecedent_exception(carB_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(carA,V1,V2).
antecedent_exception(carA_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); not_holds_at(greenA,V1,V2).

%% Solution 5 (score 6) 
antecedent_exception(carA_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(carA,V1,V2).
antecedent_exception(carB_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(emergency,V1,V2).

%% Solution 6 (score 6) 
antecedent_exception(carB_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(carB,V1,V2).
antecedent_exception(carA_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(emergency,V1,V2).

%% Solution 7 (score 6) 
antecedent_exception(carB_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(carA,V1,V2).
antecedent_exception(carA_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(carB,V1,V2).

%% Solution 8 (score 6) 
antecedent_exception(carA_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); not_holds_at(greenB,V1,V2).
antecedent_exception(carB_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(emergency,V1,V2).

%% Solution 9 (score 6) 
antecedent_exception(carA_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(carA,V1,V2).
antecedent_exception(carB_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(carB,V1,V2).

%% Solution 10 (score 6) 
antecedent_exception(carB_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(carA,V1,V2).
antecedent_exception(carA_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(emergency,V1,V2).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Pre-processing                          : 0.035s
%% Hypothesis Space Generation             : 0.339s
%% Conflict analysis                       : 0.302s
%%   - Positive Examples                   : 0.302s
%% Counterexample search                   : 0.033s
%%   - CDOEs                               : 0s
%%   - CDPIs                               : 0.033s
%% Hypothesis Search                       : 0.03s
%% Total                                   : 0.745s
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\
"""

        solution = ILASPInterpreter.extract_learned_possible_adaptations_raw(text)
        self.assertEqual(len(solution), 10)
        for score, adaptation in solution:
            self.assertEqual(score, 6)
            self.assertEqual(len(adaptation), 2)

        self.assertEqual(solution[0][1][0], "antecedent_exception(carB_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(carA,V1,V2).")
        self.assertEqual(solution[0][1][1], "antecedent_exception(carA_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); not_holds_at(greenB,V1,V2).")
        self.assertEqual(solution[1][1][0], "antecedent_exception(carA_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); not_holds_at(greenA,V1,V2).")
        self.assertEqual(solution[1][1][1], "antecedent_exception(carB_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(emergency,V1,V2).")
        self.assertEqual(solution[2][1][0], "antecedent_exception(carB_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(carB,V1,V2).")
        self.assertEqual(solution[2][1][1], "antecedent_exception(carA_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(carB,V1,V2).")
        self.assertEqual(solution[9][1][0], "antecedent_exception(carB_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(carA,V1,V2).")
        self.assertEqual(solution[9][1][1], "antecedent_exception(carA_idle_when_red,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(emergency,V1,V2).")
