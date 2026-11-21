"""The canon: an append-only record of every entity, sighting and tick.

Nothing here ever rewrites a file. New files are opened with mode 'x', which
fails if the file exists, and `guard` refuses any change to canon/ other than
an addition.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path

import yaml

from . import seeds
from .entity import combo_key, load_prose, make_entity
from .rules import Ruleset
from .sightings import check_sightings, load_voices, make_sighting

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / "canon"


def config() -> dict:
    with open(ROOT / "ghostlight.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _load_dir(d: Path) -> list[dict]:
    if not d.exists():
        return []
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(d.glob("*.json"))]


def entities() -> list[dict]:
    return _load_dir(CANON / "entities")


def sightings() -> list[dict]:
    return _load_dir(CANON / "sightings")


def ticks() -> list[dict]:
    return _load_dir(CANON / "ticks")


def fingerprint() -> str:
    h = hashlib.sha256()
    for p in sorted(CANON.rglob("*.json")):
        h.update(str(p.relative_to(CANON)).encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def chain_seed(cfg: dict | None = None) -> str:
    """The seed for the next tick: the master seed folded with the entire
    canon so far. It advances by itself every time anything is added."""
    cfg = cfg or config()
    return seeds.derive(cfg["master_seed"], fingerprint())


def write_new(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "x", encoding="utf-8") as fh:  # 'x': never overwrite
        json.dump(obj, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def _new_entity(date: str, seed: str, rs, prose) -> dict:
    ents = entities()
    eid = f"GL-{len(ents) + 1:04d}"
    e = make_entity(seeds.derive(seed, "entity"), rs, prose,
                    taken_names={x["entry"]["common_name"] for x in ents},
                    taken_combos={combo_key(x["traits"]) for x in ents})
    slugs = {x["slug"] for x in ents}
    if e["slug"] in slugs:
        e["slug"] = f"{e['slug']}-{eid.lower()}"
    record = {"id": eid, "created": date, **e}
    write_new(CANON / "entities" / f"{eid}.json", record)
    return record


def tick(date: str, force_entity: bool = False, allow_repeat: bool = False) -> dict:
    """One turn of the guide: maybe a new entity, and some new sightings."""
    cfg = config()
    rs, prose, sv = Ruleset.load(), load_prose(), load_voices()
    tick_path = CANON / "ticks" / f"{date}.json"
    if tick_path.exists() and not allow_repeat:
        return {"skipped": f"already ticked on {date}"}
    before = fingerprint()
    seed = chain_seed(cfg)
    rng = seeds.rng(seed, "tick")
    ents = entities()

    new = None
    due = not ents or (dt.date.fromisoformat(date) - dt.date.fromisoformat(max(e["created"] for e in ents))).days \
        >= cfg["cadence"]["entity_every_days"]
    if force_entity or due:
        new = _new_entity(date, seed, rs, prose)

    eligible = [e for e in ents if e["created"] < date]
    added = []
    if eligible:
        cad = cfg["cadence"]
        k = rng.choice(cad["sightings_base"]) + len(eligible) // cad["extra_per"]
        all_s = sightings()
        for e in rng.sample(eligible, min(k, len(eligible))):
            prior = [s for s in all_s if s["entity"] == e["id"]]
            s = make_sighting(e, prior, seeds.derive(seed, "sighting", e["id"]), date, len(prior) + 1, rs, prose, sv)
            write_new(CANON / "sightings" / f"{s['id']}.json", s)
            added.append(s["id"])

    record = {"date": date, "seed": seed, "canon_before": before,
              "entity": new["id"] if new else None, "sightings": added}
    if tick_path.exists():
        tick_path = tick_path.with_name(f"{date}-{len(list(tick_path.parent.glob(date + '*')))}.json")
    write_new(tick_path, record)
    return record


def found(date: str, n: int) -> list[str]:
    """Create the founding entities in one go. Each one still takes its seed
    from the canon as it stood the moment before it was written."""
    rs, prose = Ruleset.load(), load_prose()
    made = []
    for _ in range(n):
        seed = chain_seed()
        made.append(_new_entity(date, seed, rs, prose)["id"])
    write_new(CANON / "ticks" / f"{date}-founding.json",
              {"date": date, "founding": made, "note": "founding entities, created together"})
    return made


def check() -> list[str]:
    """Validate the whole canon: traits, prose, sightings, identity."""
    from .entity import lint
    rs, prose, sv = Ruleset.load(), load_prose(), load_voices()
    ents, sights = entities(), sightings()
    out = []
    ids, slugs, names = set(), set(), set()
    for e in ents:
        for v in rs.violations(e["traits"]):
            out.append(f"{e['id']}: {v}")
        for p in lint(prose, e["traits"], [e["entry"][k] for k in ("common_name", "local_name", "description",
                                                                   "first_account", "precaution")]):
            out.append(f"{e['id']}: {p}")
        for key, seen in (("id", ids), ("slug", slugs)):
            if e[key] in seen:
                out.append(f"{e['id']}: duplicate {key} {e[key]}")
            seen.add(e[key])
        if e["entry"]["common_name"] in names:
            out.append(f"{e['id']}: duplicate name")
        names.add(e["entry"]["common_name"])
    by_entity: dict[str, list] = {}
    for s in sights:
        by_entity.setdefault(s["entity"], []).append(s)
    emap = {e["id"]: e for e in ents}
    for eid, ss in by_entity.items():
        if eid not in emap:
            out.append(f"sightings filed for unknown entity {eid}")
            continue
        for s in ss:
            if s["reported"] <= emap[eid]["created"]:
                out.append(f"{s['id']}: reported on or before its entity was created")
        out.extend(check_sightings(emap[eid], ss, rs, prose, sv))
    return out


def reproduce(entity: dict) -> list[str]:
    """Regenerate an entity from its stored seed and compare."""
    rs, prose = Ruleset.load(), load_prose()
    ents = [e for e in entities() if e["id"] < entity["id"]]
    again = make_entity(entity["seed"], rs, prose,
                        taken_names={x["entry"]["common_name"] for x in ents},
                        taken_combos={combo_key(x["traits"]) for x in ents})
    diffs = [k for k in ("traits", "facts", "entry") if again[k] != entity[k]]
    return diffs


def guard(base: str = "HEAD") -> list[str]:
    """Refuse any change under canon/ that is not a pure addition, comparing
    the working tree and index against `base`."""
    def git(*args):
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    problems = []
    for line in git("diff", "--name-status", base, "--", "canon/").splitlines():
        status, *paths = line.split("\t")
        if not status.startswith("A"):
            problems.append(f"{status} {' '.join(paths)}: the canon is append-only")
    return problems
