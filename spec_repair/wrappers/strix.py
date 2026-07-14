"""
Python wrapper for the Strix reactive synthesis tool.
https://github.com/meyerphi/strix
"""

import subprocess
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class OutputFormat(str, Enum):
    HOA = "hoa"
    AAG = "aag"
    AIGER = "aiger"
    BDD = "bdd"
    PG = "pg"


class LabelEncoding(str, Enum):
    STRUCTURED = "structured"
    BINARY = "binary"
    HEURISTIC = "heuristic"


class RealizabilityResult(str, Enum):
    REALIZABLE = "REALIZABLE"
    UNREALIZABLE = "UNREALIZABLE"


@dataclass
class StrixResult:
    realizable: Optional[bool]        # None if realizability was not checked
    output: str                        # raw stdout (controller or realizability verdict)
    stderr: str
    returncode: int


class Strix:
    def __init__(self, binary: str = "strix"):
        """
        Args:
            binary: path to the strix binary, or just "strix" if it's on PATH.
        """
        self.binary = binary

    def _run(self, args: list[str], timeout: Optional[float] = None) -> StrixResult:
        cmd = [self.binary] + args
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            raise TimeoutError(f"Strix timed out after {timeout}s running: {' '.join(cmd)}")

        # Strix prints REALIZABLE / UNREALIZABLE as the first line when
        # a controller is synthesized, or as the only output for --realizability.
        realizable = None
        first_line = stdout.strip().splitlines()[0] if stdout.strip() else ""
        if first_line == RealizabilityResult.REALIZABLE:
            realizable = True
        elif first_line == RealizabilityResult.UNREALIZABLE:
            realizable = False

        return StrixResult(
            realizable=realizable,
            output=stdout,
            stderr=stderr,
            returncode=proc.returncode,
        )

    def check_realizability(
        self,
        formula: str,
        ins: list[str],
        outs: list[str],
        timeout: Optional[float] = None,
    ) -> StrixResult:
        """Check whether an LTL formula is realizable, without synthesizing a controller."""
        args = [
            "--realizability",
            "-f", formula,
            f"--ins={','.join(ins)}",
            f"--outs={','.join(outs)}",
        ]
        return self._run(args, timeout=timeout)

    def synthesize(
        self,
        formula: str,
        ins: list[str],
        outs: list[str],
        output_format: OutputFormat = OutputFormat.HOA,
        label_encoding: Optional[LabelEncoding] = None,
        timeout: Optional[float] = None,
    ) -> StrixResult:
        """
        Synthesize a controller for an LTL formula.

        Args:
            formula:         LTL formula string.
            ins:             list of input proposition names.
            outs:            list of output proposition names.
            output_format:   HOA (Mealy machine) or AAG/AIGER (circuit).
            label_encoding:  optional label encoding strategy.
            timeout:         optional timeout in seconds.
        """
        if output_format == OutputFormat.AIGER:
            args = ["--aiger"]
        else:
            args = ["-o", output_format.value]

        args += [
            "-f", formula,
            f"--ins={','.join(ins)}",
            f"--outs={','.join(outs)}",
        ]

        if label_encoding is not None:
            args += ["-l", label_encoding.value]

        return self._run(args, timeout=timeout)