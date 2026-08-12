from enum import Enum
from typing import Set, List, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from spec_repair.model.counter_trace import CounterTrace

class GR1FormulaType(Enum):
    ASM = "assumption|asm"
    GAR = "guarantee|gar"

    def __str__(self) -> str:
        return f"{self.value}"

    def to_str(self, short_version: bool = False) -> str:
        if short_version:
            return self.value.split("|")[1]
        else:
            return self.value.split("|")[0]


    @staticmethod
    def from_str(value: str) -> "GR1FormulaType":
        if value.lower() in ["assumption", "asm"]:
            return GR1FormulaType.ASM
        elif value.lower() in ["guarantee", "gar"]:
            return GR1FormulaType.GAR
        raise ValueError(f"Unsupported value: {value}")

    def to_asp(self) -> str:
        if self == GR1FormulaType.ASM:
            return "assumption"
        elif self == GR1FormulaType.GAR:
            return "guarantee"
        else:
            raise ValueError(f"Unsupported value: {self}")


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

    def __hash__(self):
        return hash(self.value)


class TemporalDialect(Enum):
    """
    How the always-operators are spelled when a specification is written out.

    Spectra accepts two spellings, and they are *not* interchangeable. The
    grammar puts them in different categories - `G` is an alias for `trans` and
    fills the `safety` field, while `alw`/`always` fills `stateInv` - and the
    controllers that come out differ: given an assumption-violating input, a
    `G` controller offers legal responses where an `alw` one rejects the input
    outright as a safety violation.

    case_study_3 needs `G`, because a violating step with no response cannot be
    completed and the trace would have to be fabricated. Other contexts may
    want `alw`; this is the switch.
    """
    G = "G"
    ALW = "alw"

    @property
    def invariant(self) -> str:
        return "G" if self is TemporalDialect.G else "alw"

    @property
    def justice(self) -> str:
        return "GF" if self is TemporalDialect.G else "alwEv"

    @staticmethod
    def default() -> "TemporalDialect":
        """`SPEC_REPAIR_TEMPORAL_DIALECT=alw` to switch, `G` unless it says so."""
        import os
        value = os.environ.get("SPEC_REPAIR_TEMPORAL_DIALECT", "G").strip().lower()
        return TemporalDialect.ALW if value in ("alw", "always") else TemporalDialect.G


class LTLFiltOperation(Enum):
    IMPLIES = "imply"
    EQUIVALENT = "equivalent-to"

    def __str__(self) -> str:
        return f"--{self.value}"

    def flag(self) -> str:
        return f"--{self.value}"


StopHeuristicType = Callable[[List[str], List["CounterTrace"]], bool]
