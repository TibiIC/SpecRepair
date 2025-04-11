from typing import List, Dict, Optional

from py_ltl.formatter import ILTLFormatter
from py_ltl.formula import LTLFormula, AtomicProposition, Not, And, Or, Until, Next, Globally, Eventually, Implies, \
    Prev, Top, Bottom

from collections import defaultdict


def antecedent_boilerplate(time, ops):
    return header_boilerplate(time, ops, implication_type="antecedent")

def consequent_boilerplate(time, ops):
    return header_boilerplate(time, ops, implication_type="consequent")

def header_boilerplate(time, ops: Optional[List[str]], implication_type: str):
    assert implication_type in ["antecedent", "consequent"]
    output = f"""\
{implication_type}_holds({{name}},{time},S):-
\ttrace(S),
\ttimepoint(T,S)\
"""
    if ops is not None:
        for op in ops:
            output += f",\n\troot_{implication_type}_holds({op},{{name}},0,{time},S)"
    return f"{output}."


class ASPFormulaFormatter(ILTLFormatter):
    def format(self, this_formula: LTLFormula) -> str:
        if not isinstance(this_formula, Globally):
            return self.format_initial(this_formula)
        else:
            return self.format_invariant(this_formula)

    def format_initial(self, this_formula: LTLFormula) -> str:
        match this_formula:
            case Implies(left=lhs, right=rhs):
                ops_antecedent_roots: Dict[str, str] = self.format_exp(lhs)
                ops_consequent_roots: Dict[str, str] = self.format_exp(rhs)
                output = header_boilerplate(time=0, )
                return f"{antecedent_roots}\n\n{consequent_roots}"
            case Globally(formula=formula):
                raise ValueError("Globally operator not supported in this formula")
            case _:
                ops_consequent_roots: Dict[str, List[LTLFormula]] = reformat_conjunction_to_op_atom_conjunction(this_formula)
                output = antecedent_boilerplate(time=0, ops=None)
                output += "\n\n"
                output += consequent_boilerplate(time=0, ops=ops_consequent_roots.keys())
                for i, (op, atoms) in enumerate(ops_consequent_roots.items()):
                    output += "\n\n"
                    output += self.format_boilerplate_root_holds(atoms, i).replace("{implication_type}", "consequent")
                return output


    def format_exp(self, this_formula: LTLFormula) -> str:
        assert not isinstance(this_formula, Globally)
        match this_formula:
            case AtomicProposition(name=name, value=value):
                if value is True:
                    return f"holds_at({name},T2,S)"
                elif value is False:
                    return f"not_holds_at({name},T2,S)"
                else:
                    raise ValueError(f"Unsupported value for atomic proposition: {value}")
            case Not(formula=formula):
                if isinstance(formula, AtomicProposition):
                    formula.value = not formula.value
                    return self.format(formula)
                else:
                    raise ValueError("Not operator not supported for this formula")
            case And(left=lhs, right=rhs):
                ops_atoms = reformat_conjunction_to_op_atom_conjunction(this_formula)
                output = self.format_boilerplate_holds(ops_atoms)
                for i, (_, atoms) in enumerate(ops_atoms.items()):
                    output += "\n\n"
                    output += self.format_boilerplate_root_holds(atoms, i)
                return output
            case Or(left=lhs, right=rhs):
                return f"({self.format(lhs)}|{self.format(rhs)})"
            case Implies(left=lhs, right=rhs):
                antecedent = complete_implication_part(self.format(lhs), "antecedent")
                consequent = complete_implication_part(self.format(rhs), "consequent")

                return f"{antecedent}\n\n{consequent}"
            case Next(formula=formula):
                ops_atoms = reformat_conjunction_to_op_atom_conjunction(this_formula)
                output = self.format_boilerplate_holds(ops_atoms)
                for i, (_, atoms) in enumerate(ops_atoms.items()):
                    output += "\n\n"
                    output += self.format_boilerplate_root_holds(atoms, i)
                return output
            case Prev(formula=formula):
                ops_atoms = reformat_conjunction_to_op_atom_conjunction(this_formula)
                output = self.format_boilerplate_holds(ops_atoms)
                for i, (_, atoms) in enumerate(ops_atoms.items()):
                    output += "\n\n"
                    output += self.format_boilerplate_root_holds(atoms, i)
                return output
            case Eventually(formula=formula):
                ops_atoms = reformat_conjunction_to_op_atom_conjunction(this_formula)
                output = self.format_boilerplate_holds(ops_atoms)
                for i, (_, atoms) in enumerate(ops_atoms.items()):
                    output += "\n\n"
                    output += self.format_boilerplate_root_holds(atoms, i)
                return output.replace("{implication_type}", "consequent")
            case Globally(formula=formula):
                if isinstance(formula, Eventually):
                    return f"G{self.format(formula)}"
                return f"G({self.format(formula)})"
            case Top():
                return ""
            case Bottom():
                return None
            case _:
                raise NotImplementedError(f"Formatter not implemented for: {type(this_formula)}")

    @staticmethod
    def format_boilerplate_holds(ops_atoms):
        output = f"{{implication_type}}_holds({{name}},T,S):-\n"
        output += "\ttrace(S),\n"
        output += "\ttimepoint(T,S)"
        for i, (op, atoms) in enumerate(ops_atoms.items()):
            output += f",\n\troot_{{implication_type}}_holds({op},{{name}},{i},T,S)"
        output += "."
        return output

    def format_boilerplate_root_holds(self, atoms, i):
        output = f"root_{{implication_type}}_holds(OP,{{name}},{i},T1,S):-\n"
        output += "\ttrace(S),\n"
        output += "\ttimepoint(T1,S),\n"
        output += "\tnot weak_timepoint(T1,S),\n"
        output += "\ttimepoint(T2,S),\n"
        output += "\ttemporal_operator(OP),\n"
        output += "\ttimepoint_of_op(OP,T1,T2,S)"
        for atom in atoms:
            output += f",\n\t{self.format_exp(atom)}"
        output += "."
        return output

def reformat_conjunction_to_op_atom_conjunction(formula) -> Dict[str, List[LTLFormula]]:
    match formula:
        case AtomicProposition(name=name, value=value):
            return {"current": [formula]}
        case Not(formula=formula):
            if isinstance(formula, AtomicProposition):
                return {"current": [formula]}
            else:
                raise ValueError("Not operator not supported for this formula")
        case And(left=lhs, right=rhs):
            lhs_format = reformat_conjunction_to_op_atom_conjunction(lhs)
            rhs_format = reformat_conjunction_to_op_atom_conjunction(rhs)
            return merge_dicts(lhs_format, rhs_format)
        case Or(left=lhs, right=rhs):
            raise ValueError("Or operator not supported for this operation")
        case Implies(left=lhs, right=rhs):
            raise ValueError("Implies operator not supported for this operation")
        case Next(formula=formula):
            if isinstance(formula, And):
                inner_format = reformat_conjunction_to_op_atom_conjunction(formula)
                assert inner_format.keys() == {"current"}
                return {"next": inner_format["current"]}
            assert isinstance(formula, AtomicProposition) or isinstance(formula, Not) or isinstance(formula, Top) or isinstance(formula, Bottom)
            return {"next": [formula]}
        case Prev(formula=formula):
            if isinstance(formula, And):
                inner_format = reformat_conjunction_to_op_atom_conjunction(formula)
                assert inner_format.keys() == {"current"}
                return {"prev": inner_format["current"]}
            assert isinstance(formula, AtomicProposition) or isinstance(formula, Not) or isinstance(formula, Top) or isinstance(formula, Bottom)
            return {"prev": [formula]}
        case Eventually(formula=formula):
            if isinstance(formula, And):
                inner_format = reformat_conjunction_to_op_atom_conjunction(formula)
                assert inner_format.keys() == {"current"}
                return {"eventually": inner_format["current"]}
            assert isinstance(formula, AtomicProposition) or isinstance(formula, Not) or isinstance(formula, Top) or isinstance(formula, Bottom)
            return {"eventually": [formula]}
        case Globally(formula=formula):
            raise ValueError("Implies operator not supported for this operation")
        case Top():
            return {"current": [formula]}
        case Bottom():
            return {"current": [formula]}
        case _:
            raise NotImplementedError(f"Reformatter not implemented for: {type(formula)}")


def complete_implication_part(formatted_string, implication_type: str):
    assert implication_type in ["antecedent", "consequent"]



def merge_dicts(*dicts):
    result = defaultdict(list)
    for d in dicts:
        for key, value in d.items():
            result[key].extend(value)
    return dict(result)