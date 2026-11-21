"""A small Tracery-compatible expander driven by an explicit RNG.

Supports #symbol#, #symbol.mod.mod#, and [symbol:text] actions. It is
written here rather than imported so that every choice comes from the RNG
we hand it, which keeps generation reproducible from a seed.
"""
from __future__ import annotations

import random
import re

TOKEN = re.compile(r"\[([A-Za-z_]\w*):([^\]]*)\]|#([^#]+)#")


def _a(s: str) -> str:
    if not s:
        return s
    first = s.lstrip("*")[:1].lower()
    return ("an " if first in "aeiou" else "a ") + s


def _cap(s: str) -> str:
    i = 0
    while i < len(s) and not s[i].isalpha():
        i += 1
    return s[:i] + s[i:i + 1].upper() + s[i + 1:]


MODS = {
    "a": _a,
    "capitalize": _cap,
    "lower": str.lower,
    "s": lambda s: s if s.endswith("s") else s + "s",
}


class Grammar:
    def __init__(self, rules: dict, rng: random.Random):
        self.rules = {k: (v if isinstance(v, list) else [v]) for k, v in rules.items()}
        self.rng = rng

    def set(self, name: str, value) -> None:
        self.rules[name] = value if isinstance(value, list) else [value]

    def expand(self, text: str, depth: int = 0) -> str:
        if depth > 30:
            raise RecursionError(f"grammar recursion too deep near: {text[:60]}")
        out, pos = [], 0
        for m in TOKEN.finditer(text):
            out.append(text[pos:m.start()])
            pos = m.end()
            if m.group(1):
                self.set(m.group(1), self.expand(m.group(2), depth + 1))
                continue
            name, *mods = m.group(3).split(".")
            if name not in self.rules:
                raise KeyError(f"grammar has no symbol '{name}'")
            piece = self.expand(self.rng.choice(self.rules[name]), depth + 1)
            for mod in mods:
                piece = MODS[mod](piece)
            out.append(piece)
        out.append(text[pos:])
        return "".join(out)
