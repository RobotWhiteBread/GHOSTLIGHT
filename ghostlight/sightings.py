"""Phase 4: sightings that accrete on existing entities, and the checks that
keep every new account consistent with the entity and with every account
already on file."""
from __future__ import annotations

import calendar
from pathlib import Path

import yaml

from . import seeds
from .entity import base_symbols, lint, load_prose, person
from .grammar import Grammar
from .rules import DATA, Ruleset

NOW_YEAR = 2026


def load_voices(path: Path | None = None) -> dict:
    with open(path or DATA / "sightings.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def anniversary(entity: dict, sv: dict) -> tuple[int, int]:
    """The date of the death. Fixed by the entity's seed, so every
    anniversary sighting falls on the same day."""
    rng = seeds.rng(entity["seed"], "anniversary")
    months = sv["origin_months"].get(entity["traits"]["origin"], list(range(1, 13)))
    m = rng.choice(months)
    return m, rng.randint(1, 28)


def allowed_months(entity: dict, sv: dict) -> list[int]:
    cond = entity["traits"]["conditions"]
    if cond == "anniversary":
        return [anniversary(entity, sv)[0]]
    return sv["condition_months"].get(cond, list(range(1, 13)))


def detail_slots(entity: dict, rs: Ruleset, sv: dict) -> dict[str, dict]:
    man = entity["traits"]["manifestation"]
    excluded = set(sv.get("detail_exclude", {}).get(man) or [])
    slots = {}
    for group in sv["details"].values():
        if man in group["applies_to"]:
            for slot, spec in group.items():
                if slot != "applies_to" and slot not in excluded:
                    slots[slot] = spec
    return slots


def slot_options(entity: dict, spec: dict) -> list[str]:
    if "options" in spec:
        return spec["options"]
    sex = entity["facts"]["dead"]["sex"] if entity["traits"]["kind"] == "revenant" else None
    if sex == "f":
        return spec["options_f"]
    if sex == "m":
        return spec["options_m"]
    return spec["options_m"] + spec["options_f"]


def established(prior: list[dict]) -> dict[str, str]:
    out: dict[str, str] = {}
    for s in sorted(prior, key=lambda s: s["id"]):
        for k, v in s.get("details", {}).items():
            out.setdefault(k, v)
    return out


def format_date(y: int, m: int, d: int, style: str) -> str:
    if style == "iso":
        return f"{y:04d}-{m:02d}-{d:02d}"
    return f"{calendar.month_name[m]} {d}, {y}"


def make_sighting(entity: dict, prior: list[dict], seed: str, reported: str, number: int,
                  rs: Ruleset | None = None, prose: dict | None = None, sv: dict | None = None) -> dict:
    rs = rs or Ruleset.load()
    prose = prose or load_prose()
    sv = sv or load_voices()
    rng = seeds.rng(seed, "sighting", entity["id"])
    traits, facts = entity["traits"], entity["facts"]
    first = facts["year"]

    # voice and year
    voices = [(k, v) for k, v in sv["voices"].items() if v["years"][1] > first]
    key, voice = rng.choices(voices, weights=[v.get("weight", 1) for _, v in voices], k=1)[0]
    ry, rm, rd = (int(x) for x in reported.split("-"))
    lo, hi = max(first + 1, voice["years"][0]), min(ry, voice["years"][1])
    year = rng.randint(lo, hi)
    if traits["conditions"] == "anniversary":
        month, day = anniversary(entity, sv)
    else:
        month = rng.choice(allowed_months(entity, sv))
        day = rng.randint(1, 28)
    if (year, month, day) >= (ry, rm, rd):
        year -= 1  # nothing is reported before it happens

    # who saw it
    modern = key == "forum"
    first_person = voice.get("first_person", False)
    w = person(rng, prose, traits, role_pool=["a neighbor"])
    if modern:
        used = {s["witness"] for s in prior}
        w["name"] = rng.choice([h for h in sv["handles"] if h not in used] or sv["handles"])

    # what they saw: only the entity's own signs
    signs = sorted(rng.sample(traits["signs"], k=1))

    # details: reuse what is established; perhaps establish one more
    known = established(prior)
    slots = detail_slots(entity, rs, sv)
    details: dict[str, str] = {}
    new_slot = None
    if known and rng.random() < 0.6:
        k = rng.choice(sorted(known))
        details[k] = known[k]
    unset = sorted(set(slots) - set(known))
    if unset and rng.random() < 0.5:
        new_slot = rng.choice(unset)
        details[new_slot] = rng.choice(slot_options(entity, slots[new_slot]))

    # a citation of an earlier account, if this voice would know of one
    earlier = [s for s in prior if s["year"] < year]
    cite = None
    if key in ("forum", "oral_history", "newspaper") and earlier and rng.random() < 0.5:
        cite = rng.choice(sorted(earlier, key=lambda s: s["id"]))

    sym = base_symbols(rs, prose, traits, facts)
    sex = w["sex"]
    sym.update({
        "date": format_date(year, month, day, voice["date_format"]),
        "wname": w["name"], "wfirst": "I" if first_person else w["first"], "wsurname": w["surname"],
        "he_w": "I" if first_person else ("he" if sex == "m" else "she"),
        "report": sv["report"][traits["manifestation"]],
        "sign": [prose["signs"][k]["then"] for k in signs],
        "outcome": sv["outcome"][traits["disposition"]],
        "church": sv["church"][traits["community"]],
        "paper": sv["paper"][traits["region"]],
        "state": sv["state"][traits["region"]],
        "homeland": sv["homeland"][traits["community"]]["where"],
        "lang": sv["homeland"][traits["community"]]["lang"],
        "handle": w["name"],
        "age": str(rng.randint(58, 91)),
        "place_upper": facts["place_short"].upper(),
        "detail": " ".join(slots_or_known(slots, sv, k, v) for k, v in sorted(details.items())) or "",
    })
    # prefer a form of this voice not yet used for this entity
    used_forms = {s.get("form") for s in prior if s["voice"] == key}
    forms = [i for i in range(len(voice["body"])) if i not in used_forms] or list(range(len(voice["body"])))
    form = rng.choice(forms)
    body_tpl = voice["body"][form]
    if "#cite#" not in body_tpl:
        cite = None
    sym["when_past"] = prose["conditions"][traits["conditions"]]["past"]
    if cite:
        sym["cite"] = sv["cite"]
        sym["cite_voice"] = sv["voices"][cite["voice"]]["label"]
        sym["cite_year"] = str(cite["year"])
    else:
        sym["cite"] = sv["cite_none"]

    for attempt in range(12):
        g = Grammar(sym, seeds.rng(seed, "sighting-prose", entity["id"], attempt))
        body = g.expand(body_tpl)
        if first_person:
            for x, y in (("I has", "I have"), ("I says", "I say"), ("I was found", "I was found")):
                body = body.replace(x, y)
        body = " ".join(body.split())
        title = g.expand(rng.choice(voice["title"]))
        if not lint(prose, traits, [body, title]):
            break
    else:
        raise RuntimeError(f"no clean sighting for {entity['id']}: {lint(prose, traits, [body, title])}")

    return {
        "id": f"{entity['id']}-S{number:03d}",
        "entity": entity["id"],
        "seed": seed,
        "reported": reported,
        "voice": key,
        "year": year,
        "month": month,
        "day": day,
        "date": sym["date"],
        "witness": w["name"],
        "signs": signs,
        "details": details,
        "new_detail": new_slot,
        "cites": cite["id"] if cite else None,
        "form": form,
        "title": title,
        "text": body,
    }


def slots_or_known(slots, sv, slot, value):
    spec = slots.get(slot)
    if spec is None:
        for group in sv["details"].values():
            if slot in group and slot != "applies_to":
                spec = group[slot]
    return spec["mention"].replace("#value#", value)


def check_sightings(entity: dict, sightings: list[dict], rs: Ruleset, prose: dict, sv: dict) -> list[str]:
    """Every rule a sighting must obey. Returns problems; empty means sound."""
    out = []
    traits, facts = entity["traits"], entity["facts"]
    seen_details: dict[str, str] = {}
    slots = detail_slots(entity, rs, sv)
    by_id = {}
    for s in sorted(sightings, key=lambda s: s["id"]):
        sid = s["id"]
        v = sv["voices"][s["voice"]]
        if s["entity"] != entity["id"]:
            out.append(f"{sid}: filed under the wrong entity")
        if (s["year"], s["month"], s["day"]) >= tuple(int(x) for x in s["reported"].split("-")):
            out.append(f"{sid}: dated on or after the day it was reported")
        if s["year"] <= facts["year"]:
            out.append(f"{sid}: dated {s['year']}, before or at the first account in {facts['year']}")
        if not v["years"][0] <= s["year"] <= v["years"][1]:
            out.append(f"{sid}: a {s['voice']} cannot be dated {s['year']}")
        if s["month"] not in allowed_months(entity, sv):
            out.append(f"{sid}: month {s['month']} does not fit the condition '{traits['conditions']}'")
        if traits["conditions"] == "anniversary" and (s["month"], s["day"]) != anniversary(entity, sv):
            out.append(f"{sid}: anniversary sighting off the anniversary")
        if not set(s["signs"]) <= set(traits["signs"]):
            out.append(f"{sid}: reports signs the entity does not have: {set(s['signs']) - set(traits['signs'])}")
        new = [k for k in s["details"] if k not in seen_details]
        if len(new) > 1:
            out.append(f"{sid}: establishes more than one new detail")
        for k, val in s["details"].items():
            if k not in slots:
                out.append(f"{sid}: detail '{k}' does not apply to {traits['manifestation']}")
            if k in seen_details and seen_details[k] != val:
                out.append(f"{sid}: {k} is '{val}', but an earlier sighting established '{seen_details[k]}'")
            seen_details.setdefault(k, val)
        if s.get("cites"):
            c = by_id.get(s["cites"])
            if c is None:
                out.append(f"{sid}: cites {s['cites']}, which was not on file before it")
            elif c["year"] >= s["year"]:
                out.append(f"{sid}: cites an account from {c['year']}, which is not earlier")
            elif str(c["year"]) not in s["text"]:
                out.append(f"{sid}: cites {c['id']} but gets its year wrong")
        for p in lint(prose, traits, [s["text"], s["title"]]):
            out.append(f"{sid}: {p}")
        by_id[sid] = s
    return out
