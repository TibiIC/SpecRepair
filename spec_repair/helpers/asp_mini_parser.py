import re
from typing import Optional, Tuple

from py_ltl.formula import AtomicProposition


class ASPMiniParser:
    @staticmethod
    def parse(line: str) -> Optional[AtomicProposition]:
        if (line.startswith("#") or
                "\n" in line and
                "\r" in line or
                not line.strip()):
            return None
        line = line.strip().rstrip()
        holds_at_args = re.search(r'(not_)?holds_at\((\w+),\s*(\w+)', line)
        if holds_at_args:
            prefix, atom, _ = holds_at_args.groups()
            return AtomicProposition(name=atom, value=(prefix != 'not_'))
        else:
            return None

    @staticmethod
    def parse_adv(line: str) -> Optional[Tuple[AtomicProposition, int, str]]:
        if (line.startswith("#") or
                "\n" in line and
                "\r" in line or
                not line.strip()):
            return None
        line = line.strip().rstrip()
        holds_at_args = re.search(r'(not_)?holds_at\((\w+),\s*(\d+),\s*(\w+)\)', line)
        if holds_at_args:
            prefix, atom, time_str, trace_name = holds_at_args.groups()
            time_index = int(time_str)
            return AtomicProposition(name=atom, value=(prefix != 'not_')), time_index, trace_name
        else:
            return None