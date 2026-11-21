"""The constraint engine.

Everything folkloric lives in data/rules.yaml. This module only knows how to
read rule types, draw traits that satisfy them, and explain violations.
"""
from __future__ import annotations

import itertools
import random
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parent.parent / "data"


@dataclass
class Violation:
    rule_id: str
    name: str
    detail: str

    def __str__(self) -> str:
        return f"{self.rule_id} {self.name}: {self.detail}"


@dataclass
class DrawStats:
    restarts: int = 0
    dead_ends: Counter = field(default_factory=Counter)


class Ruleset:
    def __init__(self, data: dict):
        self.data = data
        self.meta = data["meta"]
        self.order: list[str] = data["order"]
        self.multi: dict[str, list[int]] = data.get("multi", {})
        self.traits: dict[str, dict] = data["traits"]
        self.rules: list[dict] = data["rules"]
        self._check_shape()

    @classmethod
    def load(cls, path: Path | None = None) -> "Ruleset":
        path = path or DATA / "rules.yaml"
        with open(path, encoding="utf-8") as fh:
            return cls(yaml.safe_load(fh))

    # ----- shape -------------------------------------------------------
    def _check_shape(self) -> None:
        for t in self.order:
            if t not in self.traits:
                raise ValueError(f"order names unknown trait '{t}'")
        ids = [r["id"] for r in self.rules]
        dupes = [i for i, n in Counter(ids).items() if n > 1]
        if dupes:
            raise ValueError(f"duplicate rule ids: {dupes}")
        for r in self.rules:
            for t in refs(r):
                if t not in self.traits:
                    raise ValueError(f"rule {r['id']} names unknown trait '{t}'")

    # ----- lookups -----------------------------------------------------
    def value(self, trait: str, key: str) -> dict:
        return self.traits[trait][key]

    def keys(self, assigned: dict, trait: str) -> list[str]:
        v = assigned[trait]
        return v if isinstance(v, list) else [v]

    def values(self, assigned: dict, trait: str) -> list[dict]:
        return [self.value(trait, k) for k in self.keys(assigned, trait)]

    def tags(self, assigned: dict, traits) -> set[str]:
        out: set[str] = set()
        for t in traits:
            for v in self.values(assigned, t):
                out.update(v.get("tags", []))
                if t == "region":
                    out.update(v.get("features", []))
        return out

    # ----- checking ----------------------------------------------------
    def check_rule(self, rule: dict, a: dict) -> list[Violation]:
        t = rule["type"]
        out: list[str] = []
        if t == "contains":
            target = set(self.keys(a, rule["of"]))
            for k in self.keys(a, rule["trait"]):
                allowed = self.value(rule["trait"], k).get(rule["field"])
                if allowed is not None and not target & set(allowed):
                    out.append(f"{rule['trait']} '{k}' allows {rule['of']} {sorted(allowed)}, got {sorted(target)}")
        elif t == "features":
            have: set[str] = set()
            for v in self.values(a, rule["of"]):
                have.update(v.get(rule["of_field"], []))
            for k in self.keys(a, rule["trait"]):
                need = set(self.value(rule["trait"], k).get(rule["field"], []))
                missing = need - have
                if missing:
                    out.append(f"{rule['trait']} '{k}' needs {sorted(missing)}, which {rule['of']} '{a[rule['of']]}' lacks")
        elif t == "years":
            for ov in self.values(a, rule["of"]):
                oy = ov.get("years")
                for k in self.keys(a, rule["trait"]):
                    vy = self.value(rule["trait"], k).get("years")
                    if oy and vy and (vy[1] < oy[0] or vy[0] > oy[1]):
                        out.append(f"{rule['trait']} '{k}' exists {vy[0]} to {vy[1]}, {rule['of']} '{a[rule['of']]}' is {oy[0]} to {oy[1]}")
        elif t == "needs_tags":
            have = self.tags(a, rule["of"])
            for k in self.keys(a, rule["trait"]):
                need = self.value(rule["trait"], k).get(rule["field"])
                if need and not have & set(need):
                    out.append(f"{rule['trait']} '{k}' needs one of {sorted(need)} from {'/'.join(rule['of'])}")
        elif t == "opposed":
            ta = self.tags(a, [rule["a"]])
            for k in self.keys(a, rule["b"]):
                tb = set(self.value(rule["b"], k).get("tags", []))
                for x, y in rule["pairs"]:
                    if (x in ta and y in tb) or (y in ta and x in tb):
                        out.append(f"{rule['a']} '{a[rule['a']]}' is {x if x in ta else y}, {rule['b']} '{k}' is {y if x in ta else x}")
        elif t == "share":
            pool = self.tags(a, rule["with"]) & set(rule["tags"])
            hits = 0
            for k in self.keys(a, rule["trait"]):
                vt = set(self.value(rule["trait"], k).get("tags", []))
                if "any" in vt or vt & pool:
                    hits += 1
            if hits < rule.get("min", 1):
                out.append(f"{rule['trait']} {self.keys(a, rule['trait'])} shares nothing with {'/'.join(rule['with'])}")
        elif t == "when":
            if self._matches(rule["when"], a):
                hit = self._matches(rule["then"], a)
                if rule.get("mode", "require") == "require" and not hit:
                    out.append(f"{rule['then']['trait']} '{a[rule['then']['trait']]}' does not satisfy {self._describe(rule['then'])}")
                if rule.get("mode") == "forbid" and hit:
                    out.append(f"{rule['then']['trait']} '{a[rule['then']['trait']]}' is ruled out")
        else:
            raise ValueError(f"unknown rule type {t} in {rule['id']}")
        return [Violation(rule["id"], rule["name"], d) for d in out]

    def _matches(self, cond: dict, a: dict) -> bool:
        keys = set(self.keys(a, cond["trait"]))
        if "keys_any" in cond and keys & set(cond["keys_any"]):
            return True
        if "tags_any" in cond and self.tags(a, [cond["trait"]]) & set(cond["tags_any"]):
            return True
        return False

    @staticmethod
    def _describe(cond: dict) -> str:
        if "keys_any" in cond:
            return f"one of {cond['keys_any']}"
        return f"a tag from {cond['tags_any']}"

    def violations(self, a: dict, partial: bool = False) -> list[Violation]:
        out: list[Violation] = []
        for r in self.rules:
            if partial and not refs(r) <= a.keys():
                continue
            out.extend(self.check_rule(r, a))
        return out

    # ----- drawing -----------------------------------------------------
    def draw(self, rng: random.Random, stats: DrawStats | None = None, max_restarts: int = 500) -> dict:
        """Draw one entity's traits, trait by trait, never accepting a value
        that breaks a rule already checkable. Restarts on a dead end."""
        stats = stats or DrawStats()
        for _ in range(max_restarts):
            a: dict = {}
            ok = True
            for trait in self.order:
                pick = self._pick(trait, a, rng, stats)
                if pick is None:
                    ok = False
                    stats.restarts += 1
                    break
                a[trait] = pick
            if ok:
                assert not self.violations(a), self.violations(a)
                return a
        raise RuntimeError("could not satisfy the rules; see dead ends")

    def _pick(self, trait, a, rng, stats):
        options = list(self.traits[trait].items())
        if trait in self.multi:
            lo, hi = self.multi[trait]
            singles = [k for k, _ in options if not self.violations({**a, trait: [k]}, partial=True)
                       or self._only_share(self.violations({**a, trait: [k]}, partial=True))]
            n = rng.randint(lo, hi)
            if len(singles) < n:
                stats.dead_ends[f"{trait}: too few compatible values"] += 1
                return None
            for _ in range(80):
                combo = sorted(rng.sample(singles, n))
                if not self.violations({**a, trait: combo}, partial=True):
                    return combo
            stats.dead_ends[f"{trait}: no compatible combination"] += 1
            return None
        good, weights = [], []
        blocked = Counter()
        for k, v in options:
            vs = self.violations({**a, trait: k}, partial=True)
            if vs:
                for x in vs:
                    blocked[x.rule_id] += 1
                continue
            good.append(k)
            weights.append(v.get("weight", 1))
        if not good:
            stats.dead_ends[f"{trait}: blocked by {', '.join(r for r, _ in blocked.most_common(3))}"] += 1
            return None
        return rng.choices(good, weights=weights, k=1)[0]

    def _only_share(self, vs):
        ids = {r["id"] for r in self.rules if r["type"] == "share"}
        return all(v.rule_id in ids for v in vs)

    def naive(self, rng: random.Random) -> dict:
        """A draw that ignores every rule, for measuring how much the rules do."""
        a = {}
        for trait in self.order:
            keys = list(self.traits[trait])
            if trait in self.multi:
                lo, hi = self.multi[trait]
                a[trait] = sorted(rng.sample(keys, rng.randint(lo, hi)))
            else:
                a[trait] = rng.choice(keys)
        return a


def refs(rule: dict) -> set[str]:
    t = rule["type"]
    if t in ("contains", "features", "years"):
        return {rule["trait"], rule["of"]}
    if t == "needs_tags":
        return {rule["trait"], *rule["of"]}
    if t == "opposed":
        return {rule["a"], rule["b"]}
    if t == "share":
        return {rule["trait"], *rule["with"]}
    if t == "when":
        return {rule["when"]["trait"], rule["then"]["trait"]}
    raise ValueError(f"unknown rule type {t}")
