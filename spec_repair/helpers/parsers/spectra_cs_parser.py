"""
Parser for the Spectra CLI counter-strategy format.

The spectra-cli tool (https://github.com/SpectraSynthesizer/spectra-cli) emits
counter-strategies as a flat list of transition strings of the form:

    SRC -> DST {in1:false, in2:true} / {out1:false};

This module converts that representation into the structured CounterStrategy
class, replacing the legacy `CounterStrategy = list[str]` type alias.
"""

from __future__ import annotations

import re

from spec_repair.helpers.counter_strategy import CounterStrategy, CSTransition


class SpectraCSParser:
    """
    Parses the Spectra CLI counter-strategy format into a CounterStrategy.

    Input: either the raw tool output (as a multi-line string) or the
    already-extracted list of transition strings (the legacy CounterStrategy
    list[str] type).
    """

    # "INI -> S0 {highwater:false, methane:false} / {pump:false};"
    _TRANSITION_RE = re.compile(
        r"(\w+)\s*->\s*(\w+)"          # SRC -> DST
        r"\s*\{([^}]*)\}"              # { inputs }
        r"\s*/\s*\{([^}]*)\}"          # / { outputs }
    )
    _ASSIGNMENT_RE = re.compile(r"(\w+)\s*:\s*(true|false)")

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    @classmethod
    def from_lines(cls, lines: list[str]) -> CounterStrategy:
        """
        Parse from the legacy list[str] representation, e.g.:

            ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
             'S0 -> DEAD {highwater:true, methane:true} / {pump:true};']
        """
        transitions = [
            t
            for line in lines
            for t in cls._parse_line(line)
        ]
        return CounterStrategy(transitions)

    @classmethod
    def from_str(cls, text: str) -> CounterStrategy:
        """
        Parse from the raw spectra-cli output string, e.g. as returned by
        subprocess.  Lines that don't match the transition pattern are ignored.
        """
        return cls.from_lines(text.splitlines())

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    @classmethod
    def _parse_line(cls, line: str) -> list[CSTransition]:
        m = cls._TRANSITION_RE.search(line)
        if not m:
            return []
        source, target, inputs_str, outputs_str = m.groups()
        return [
            CSTransition(
                source=source,
                target=target,
                inputs=cls._parse_assignments(inputs_str),
                outputs=cls._parse_assignments(outputs_str),
            )
        ]

    @classmethod
    def _parse_assignments(cls, s: str) -> dict[str, bool]:
        return {
            m.group(1): m.group(2) == "true"
            for m in cls._ASSIGNMENT_RE.finditer(s)
        }