from copy import deepcopy
from typing import FrozenSet

from spec_repair.interfaces.ioracle import IOracle
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.ltl_types import GR1FormulaType


def get_unrealisable_cores(
    spec: SpectraSpecification,
    oracle: IOracle,
) -> list[set[str]]:
    """
    Return all minimal unrealisable cores.
    """
    if oracle.is_realisable(spec):
        return []

    cores, _ = _get_unrealisable_cores(spec, oracle, {})
    return [set(core) for core in cores]


def _get_unrealisable_cores(
    spec: SpectraSpecification,
    oracle: IOracle,
    memo: dict[FrozenSet[str], bool],
) -> tuple[set[FrozenSet[str]], bool]:
    """
    Returns

        (minimal_cores, is_realisable)

    where

        minimal_cores

    is the set of all minimal unrealisable cores contained in this
    specification.
    """

    guarantees = frozenset(
        spec._formulas_df.loc[
            spec._formulas_df["type"] == GR1FormulaType.GAR,
            "name",
        ]
    )

    #
    # Memoised oracle
    #
    if guarantees not in memo:
        memo[guarantees] = oracle.is_realisable(spec)

    if memo[guarantees]:
        return set(), True

    child_cores: set[FrozenSet[str]] = set()
    has_unrealisable_child = False

    for guarantee in guarantees:
        child = deepcopy(spec)
        child.remove_formula(guarantee)

        cores, child_is_realisable = _get_unrealisable_cores(
            child,
            oracle,
            memo,
        )

        if child_is_realisable:
            continue

        has_unrealisable_child = True
        child_cores |= cores

    #
    # Every immediate subset is realisable.
    #
    # Therefore this specification is itself a minimal
    # unrealisable core.
    #
    if not has_unrealisable_child:
        return {guarantees}, False

    return child_cores, False