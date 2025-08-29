# Enum/Int allowance extension 

Spectra works with a plethora of value definitions, useful for expressing more than using pure boolean values.

Therefore, a simple extension is in order.

I replaced the duality of:
```python
holds_at(A,T,S).
not_holds_at(A,T,S).
```
with
```python
holds_at(A,V,T,S).
```
Where we now have V as a placeholder of the value the atom can take (e.g. bool={false,true}, int={0,1,2,3,4,5,6,7,8,9})..

The change is minimalistic when it comes to the ASP side, but it may be more involved in the code. To be added in a spare day, once the first paper draft is done.
