"""Diagnostics: are the rules too loose (random) or too tight (one entity
in twenty costumes)?"""
from __future__ import annotations

import itertools
import math
from collections import Counter

from . import seeds
from .rules import DrawStats, Ruleset


def _keys(v):
    return v if isinstance(v, list) else [v]


def entropy_ratio(counter: Counter, n_values: int) -> float:
    total = sum(counter.values())
    if total == 0 or n_values < 2:
        return 0.0
    h = -sum((c / total) * math.log(c / total) for c in counter.values())
    return h / math.log(n_values)


def similarity(a: dict, b: dict, traits: list[str]) -> float:
    same = 0.0
    for t in traits:
        x, y = set(_keys(a[t])), set(_keys(b[t]))
        same += len(x & y) / len(x | y)
    return same / len(traits)


def distribution(rs: Ruleset, n: int = 20, seed: str = "phase1", naive_n: int = 5000) -> str:
    stats = DrawStats()
    ents = [rs.draw(seeds.rng(seed, i), stats) for i in range(n)]
    out = [f"# GHOSTLIGHT Phase 1: trait distribution", "",
           f"Rules: `{rs.meta['id']}` version {rs.meta['version']}, {len(rs.rules)} rules. "
           f"Sample of {n} drawn from seed `{seed}`.", ""]

    out += ["## The twenty", "", "| # | kind | region | era | origin | manifestation | disposition | condition | remedy |",
            "|---|---|---|---|---|---|---|---|---|"]
    for i, e in enumerate(ents, 1):
        out.append(f"| {i} | {e['kind']} | {e['region']} | {e['era']} | {e['origin']} | {e['manifestation']} | "
                   f"{e['disposition']} | {e['conditions']} | {e['remedy']} |")

    out += ["", "## Spread per trait", "",
            "Coverage is how many of the possible values turned up. Evenness is entropy over the values that "
            "exist (1.0 is perfectly even, 0 is one value every time).", "",
            "| trait | coverage | evenness | most common |", "|---|---|---|---|"]
    for t in rs.order:
        c = Counter(k for e in ents for k in _keys(e[t]))
        nv = len(rs.traits[t])
        top = ", ".join(f"{k} ({v})" for k, v in c.most_common(3))
        out.append(f"| {t} | {len(c)}/{nv} | {entropy_ratio(c, nv):.2f} | {top} |")

    single = [t for t in rs.order if t not in rs.multi]
    sims = [similarity(a, b, rs.order) for a, b in itertools.combinations(ents, 2)]
    closest = max(itertools.combinations(range(n), 2), key=lambda p: similarity(ents[p[0]], ents[p[1]], rs.order))
    combos = Counter((e["origin"], e["manifestation"]) for e in ents)
    out += ["", "## Too tight?", "",
            f"- Mean pairwise similarity across all traits: **{sum(sims)/len(sims):.2f}** "
            "(0 shares nothing, 1 is identical).",
            f"- Most similar pair: #{closest[0]+1} and #{closest[1]+1} at "
            f"{similarity(ents[closest[0]], ents[closest[1]], rs.order):.2f}.",
            f"- Distinct origin and manifestation pairings: {len(combos)} of {n}.",
            f"- Dead ends while drawing: {stats.restarts} restarts for {n} entities."]
    if stats.dead_ends:
        out.append("- Where draws dead-ended: " + "; ".join(f"{k} ({v})" for k, v in stats.dead_ends.most_common(4)))

    rng = seeds.rng(seed, "naive")
    acc, rej = 0, Counter()
    for _ in range(naive_n):
        v = rs.violations(rs.naive(rng))
        if not v:
            acc += 1
        for rid in {x.rule_id for x in v}:
            rej[rid] += 1
    names = {r["id"]: r["name"] for r in rs.rules}
    out += ["", "## Too loose?", "",
            f"Of {naive_n} entities drawn with every rule ignored, **{acc} ({100*acc/naive_n:.2f}%)** would pass. "
            "That is how much work the rules do: a random draw from the lists almost never reads as coherent folklore.",
            "", "Share of random draws each rule rejects:", "", "| rule | rejects | name |", "|---|---|---|"]
    for rid, cnt in sorted(rej.items(), key=lambda x: -x[1]):
        out.append(f"| {rid} | {100*cnt/naive_n:.0f}% | {names[rid]} |")
    unused = [r["id"] for r in rs.rules if r["id"] not in rej]
    if unused:
        out.append(f"\nRules that never fired on a random draw: {', '.join(unused)}.")
    return "\n".join(out) + "\n"
