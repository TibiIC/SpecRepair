from enum import Enum
from typing import Set, List

import pandas as pd

from spec_repair.enums import ExpType, When


class LTLFormula:
    formula: str
    # >>>>> NOT YET IN USE >>>>>
    type: ExpType
    name: str
    antecedent: set[str]
    consequent: set[str]
    when: When

    # <<<<< NOT YET IN USE <<<<<

    def __init__(self, formula: str):
        if not isinstance(formula, str) or '\n' in formula:
            raise ValueError("Formula must be a one-line string.")
        self.formula = formula

    def __getattr__(self, name):
        # If the attribute is a string method, apply it to the stored formula
        if hasattr(self.formula, name) and callable(getattr(self.formula, name)):
            return getattr(self.formula, name)
        raise AttributeError(f"'LTLFormula' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        # Make the class immutable by preventing attribute changes after initialization
        if hasattr(self, "_data"):
            raise AttributeError("Cannot modify attributes of 'LTLFormula' object.")
        super().__setattr__(name, value)


class Assumption(LTLFormula):
    pass


class Guarantee(LTLFormula):
    pass


class Trace:
    variables: Set[str]
    path: List[Set[str]]

    def __init__(self, file_name: str):
        raise NotImplemented

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index >= len(self.path):
            raise StopIteration
        value = self.path[self.index]
        self.index += 1
        return value


Trace = str
CounterStrategy = List[str]
Spec = pd.DataFrame


class GR1FormulaType(Enum):
    ASM = "assumption|asm"
    GAR = "guarantee|gar"

    def __str__(self) -> str:
        return f"{self.value}"

    @staticmethod
    def from_str(value: str) -> "GR1FormulaType":
        if value in ["assumption", "asm"]:
            return GR1FormulaType.ASM
        elif value in ["guarantee", "gar"]:
            return GR1FormulaType.GAR
        raise ValueError(f"Unsupported value: {value}")

class GR1AtomType(Enum):
    SYS = "sys"
    ENV = "env"

    def __str__(self) -> str:
        return f"{self.value}"

    @staticmethod
    def from_str(value: str) -> "GR1AtomType":
        if value == "sys":
            return GR1AtomType.SYS
        elif value == "env":
            return GR1AtomType.ENV
        raise ValueError(f"Unsupported value: {value}")

class GR1TemporalType(Enum):
    INITIAL = "ini"
    INVARIANT = "G"
    JUSTICE = "GF"

    def __str__(self) -> str:
        return f"{self.value}"


class LTLFiltOperation(Enum):
    IMPLIES = "imply"
    EQUIVALENT = "equivalent-to"

    def __str__(self) -> str:
        return f"--{self.value}"

    def flag(self) -> str:
        return f"--{self.value}"
