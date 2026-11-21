"""Turning a seed into a finished entity: traits, fixed facts, and prose."""
from __future__ import annotations

import itertools
import re
import unicodedata
from pathlib import Path

import yaml

from . import seeds
from .grammar import Grammar
from .rules import DATA, DrawStats, Ruleset

FORBIDDEN_CHARS = {"\u2014": "em dash", "\u2013": "en dash"}
PROSE_FIELDS = ["common_name", "local_name", "description", "first_account", "precaution"]


def load_prose(path: Path | None = None) -> dict:
    with open(path or DATA / "prose.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def slugify(text: str) -> str:
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    t = re.sub(r"[^A-Za-z0-9]+", "-", t).strip("-").lower()
    return t


def river_ref(name: str) -> str:
    """'the Platte', but 'Elm Creek'."""
    return name if name.endswith("Creek") else f"the {name}"


def join_list(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


# ---------------------------------------------------------------------------
# facts: the concrete particulars drawn once and kept forever

def year_window(rs: Ruleset, traits: dict) -> tuple[int, int]:
    lo, hi = 1850, 1930
    for t in ("era", "origin", "community", "manifestation", "remedy"):
        y = rs.value(t, traits[t]).get("years")
        if y:
            lo, hi = max(lo, y[0]), min(hi, y[1])
    return lo, hi


def person(rng, prose, traits, role_pool=None, sex=None):
    c = prose["community"][traits["community"]]
    era = prose["era"][traits["era"]]
    sex = sex or rng.choice(["m", "m", "f"])
    given = rng.choice(c["given_m"] if sex == "m" else c["given_f"])
    surname = rng.choice(c["surnames"])
    roles = role_pool or (era["roles"] if sex == "m" else era["roles_f"])
    return {"name": f"{given} {surname}", "first": given, "surname": surname,
            "role": rng.choice(roles), "sex": sex}


def draw_facts(rs: Ruleset, prose: dict, traits: dict, seed: str) -> dict:
    rng = seeds.rng(seed, "facts")
    region = prose["region"][traits["region"]]
    comm = prose["community"][traits["community"]]
    era = prose["era"][traits["era"]]
    ob = prose["origin"][traits["origin"]]
    lo, hi = year_window(rs, traits)
    family = rng.choice(comm["surnames"])
    river = rng.choice(region["rivers"])
    spot = rng.choice(region["places"])
    watery = "water" in rs.tags(traits, ["origin", "manifestation"])
    if watery and rng.random() < 0.6:
        place, short = f"the {family} ford on {river_ref(river)}", f"{family} Ford"
    else:
        place, short = rng.choice([
            (f"{spot} on the {family} place", f"{family} Place"),
            (f"{spot} on {river_ref(river)}", river),
            (f"{spot} near the {family} place", f"{family} Place"),
        ])
    dead = person(rng, prose, traits, ob.get("dead_role"), ob.get("dead_sex"))
    witness = person(rng, prose, traits)
    return {
        "year": rng.randint(lo, hi),
        "family": family,
        "river": river,
        "place": place,
        "place_short": short,
        "dead": dead,
        "witness": witness,
        "light_src": rng.choice(era["light_src"]),
        "rig": rng.choice(era["rig"]),
        "people": rng.choice(comm["people"]),
        "term": rng.choice(comm.get("term_by_manifestation", {}).get(traits["manifestation"])
                           or comm["term"][traits["kind"]]),
    }


# ---------------------------------------------------------------------------
# grammar: everything the templates may say, all of it keyed by traits

def base_symbols(rs: Ruleset, prose: dict, traits: dict, facts: dict) -> dict:
    d = facts["dead"]
    sex = d["sex"]
    o = prose["origin"][traits["origin"]]
    m = prose["manifestation"][traits["manifestation"]]
    return {
        "dead": f"{d['role']} named {d['name']}",
        "dead_name": d["name"],
        "dead_first": d["first"],
        "he": "he" if sex == "m" else "she",
        "him": "him" if sex == "m" else "her",
        "his": "his" if sex == "m" else "her",
        "family": facts["family"],
        "place": facts["place"],
        "place_short": facts["place_short"],
        "river": facts["river"],
        "the_river": river_ref(facts["river"]),
        "year": str(facts["year"]),
        "light_src": facts["light_src"],
        "rig": facts["rig"],
        "people": facts["people"],
        "term": facts["term"],
        "witness": f"{facts['witness']['role']} named {facts['witness']['name']}",
        "region": rs.value("region", traits["region"])["label"],
        "kind_noun": prose["kind"][traits["kind"]]["noun"],
        "epithet": o["epithet"],
        "noun": m["noun"],
        "ohnoun": o.get("noun", m["noun"]),
        "origin_account": o["account"],
        "seen": m["seen"],
        "testimony": m["testimony"],
        "temper": prose["disposition"][traits["disposition"]]["temper"],
        "when": prose["conditions"][traits["conditions"]]["when"],
        "precaution": prose["remedy"][traits["remedy"]]["do"],
        "remedy_did": prose["remedy"][traits["remedy"]]["did"],
    }


def sign_phrases(prose: dict, traits: dict, form: str) -> list[str]:
    return [prose["signs"][k][form] for k in traits["signs"]]


# ---------------------------------------------------------------------------
# lint: the guarantee that prose never contradicts traits

def lint(prose: dict, traits: dict, texts: list[str]) -> list[str]:
    blob = "\n".join(texts)
    problems = []
    for ch, name in FORBIDDEN_CHARS.items():
        if ch in blob:
            problems.append(f"contains an {name}")
    if re.search(r"#[A-Za-z_]", blob):
        problems.append("unexpanded grammar symbol")
    for cat in ("origin", "manifestation", "remedy", "disposition", "conditions"):
        chosen = traits[cat]
        own = {mk.lower() for mk in prose[cat][chosen].get("markers", [])}
        for key, bank in prose[cat].items():
            if key == chosen:
                continue
            for mk in bank.get("markers", []):
                if mk.lower() in own:
                    continue
                if re.search(r"\b" + re.escape(mk), blob, re.IGNORECASE):
                    problems.append(f"{cat} marker '{mk}' belongs to '{key}', not '{chosen}'")
    return problems


# ---------------------------------------------------------------------------

def write_entry(rs, prose, traits, facts, seed, taken_names=frozenset(), attempts=16):
    last = None
    for attempt in range(attempts):
        rng = seeds.rng(seed, "prose", attempt)
        g = Grammar(base_symbols(rs, prose, traits, facts), rng)
        now = sign_phrases(prose, traits, "now")
        rng.shuffle(now)
        g.set("signs_now", join_list(now))
        g.set("sign_then", sign_phrases(prose, traits, "then"))
        tpl = prose["templates"]
        name = g.expand(rng.choice(tpl["common_name"][traits["kind"]]))
        words = name.lower().split()
        if any(a[:5] == b[:5] for a, b in itertools.combinations([w for w in words if len(w) > 3], 2)):
            last = [f"name '{name}' repeats a word"]
            continue
        if name in taken_names:
            last = [f"name '{name}' already in the canon"]
            continue
        entry = {
            "common_name": name,
            "local_name": g.expand(rng.choice(tpl["local_name"])),
            "description": g.expand(rng.choice(tpl["description"])),
            "first_account": g.expand(rng.choice(tpl["first_account"])),
            "precaution": g.expand(rng.choice(tpl["precaution"])),
        }
        problems = lint(prose, traits, list(entry.values()))
        if not problems:
            entry["prose_attempt"] = attempt
            return entry
        last = problems
    raise RuntimeError(f"no clean entry after {attempts} attempts: {last}")


def make_entity(seed: str, rs: Ruleset | None = None, prose: dict | None = None,
                taken_names=frozenset(), taken_combos=frozenset(), stats: DrawStats | None = None) -> dict:
    rs = rs or Ruleset.load()
    prose = prose or load_prose()
    for n in range(50):
        traits = rs.draw(seeds.rng(seed, "traits", n), stats)
        combo = combo_key(traits)
        if combo not in taken_combos:
            break
    facts = draw_facts(rs, prose, traits, seed)
    entry = write_entry(rs, prose, traits, facts, seed, taken_names)
    return {
        "seed": seed,
        "rules": f"{rs.meta['id']}@{rs.meta['version']}",
        "traits": traits,
        "facts": facts,
        "entry": entry,
        "slug": slugify(entry["common_name"]),
    }


def combo_key(traits: dict) -> str:
    return "|".join(traits[t] for t in ("kind", "origin", "manifestation", "region"))
