# Edge Case Discovered

The running of `ILASP minepump_antecedent_ex.las` yields the following as the 10th result:
```bash
%% Solution 10 (score 4) 
antecedent_exception(assumption2_1,0,V1,V2) :- timepoint_of_op(next,V1,V3,V2); holds_at(methane,high,V3,V2); holds_at(methane,low,V3,V2).
```
The most likely culprit is the encoding of the virtual future timepoint and "next", that being
```python
timepoint_of_op(next,T1,T2,S) :-
    trace(S),
    timepoint(T1,S),
    not weak_timepoint(T1,S),
    timepoint(T2,S),
    next(T2,T1,S).
```
As we can see, next can be defined for the value at a weak timepoint, where an atom may have multiple values.

