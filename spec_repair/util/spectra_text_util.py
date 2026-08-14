"""
Canonical text for a Spectra specification, for use as a cache key.

`asm A; gar B` and `gar B; asm A` are the same specification and have the same
unrealisable cores, but differ as text, so a key taken from the raw text misses.
Sorting the declarations and the formula blocks makes the two agree.

**For keys only.** Nothing here may be fed to Spectra. `run_all_unrealisable_cores`
maps Spectra's output back onto expression names *by line number*
(`get_line_from_file(temp_spectra_file, core_num)`), so reordering the text that
is actually analysed would silently attach the wrong names to a core.
"""
from __future__ import annotations

import re
from typing import List, Tuple

# "assumption -- name", "guarantee -- name", and the asm/gar spellings.
_HEADER_RE = re.compile(r"^\s*(assumption|guarantee|asm|gar)\s*--\s*(\S+)\s*$")
_DECL_RE = re.compile(r"^\s*(env|sys|aux)\s+")
_MODULE_RE = re.compile(r"^\s*module\s+")


def _squash(text: str) -> str:
    """Collapse whitespace, so a tab-indented formula matches a space-indented one."""
    return re.sub(r"\s+", " ", text).strip()


def canonical_spectra_text(spectra_str: str) -> str:
    """
    A canonical rendering of `spectra_str`: same specification, same string.

    Sorts the variable declarations and the (name, formula) blocks, and collapses
    whitespace. Two specifications differing only in the order they were written
    therefore produce the same output, and hash the same.

    Deliberately conservative: anything not recognised as a declaration or a
    named formula block - a module line, a comment, a pattern definition, a
    `define` section - is kept in place and in order. An unrecognised construct
    then costs a cache miss rather than risking a wrong hit, and a specification
    this cannot parse still returns *something* stable, since the fallback is the
    whitespace-collapsed original.
    """
    lines = spectra_str.splitlines()

    module: List[str] = []
    declarations: List[str] = []
    blocks: List[Tuple[str, str, str]] = []   # (type, name, formula)
    other: List[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        header = _HEADER_RE.match(line)
        if header:
            # The formula is every line up to and including the one ending in ';'
            formula_parts: List[str] = []
            j = i + 1
            while j < len(lines):
                formula_parts.append(lines[j])
                if ";" in lines[j]:
                    break
                j += 1
            kind = "assumption" if header.group(1) in ("assumption", "asm") else "guarantee"
            blocks.append((kind, header.group(2), _squash(" ".join(formula_parts))))
            i = j + 1
            continue

        if _MODULE_RE.match(line):
            module.append(_squash(line))
        elif _DECL_RE.match(line):
            declarations.append(_squash(line))
        else:
            other.append(_squash(line))
        i += 1

    out: List[str] = []
    out.extend(module)
    out.extend(sorted(declarations))
    out.extend(other)
    out.extend(f"{kind} -- {name} {formula}" for kind, name, formula in sorted(blocks))
    return "\n".join(out)
