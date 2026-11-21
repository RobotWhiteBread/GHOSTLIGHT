"""GHOSTLIGHT command line.

  python -m ghostlight sample [--n 20]        Phase 1: draw entities, report the distribution
  python -m ghostlight explain kind=... ...     check a hand-made combination, name broken rules
  python -m ghostlight review [--n 10]          Phase 2: write sample entries for marking
  python -m ghostlight entity --seed SEED       regenerate an entity from its seed
  python -m ghostlight found --n 3              create the founding entities
  python -m ghostlight tick [--date D]          one weekly turn: maybe an entity, some sightings
  python -m ghostlight check                    validate the whole canon
  python -m ghostlight guard [--base REF]       fail if anything in canon/ was modified or deleted
  python -m ghostlight build                    build the static site into _site/
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from . import canon
from .entity import load_prose, make_entity
from .report import distribution
from .rules import Ruleset

ROOT = Path(__file__).resolve().parent.parent


def cmd_sample(a):
    text = distribution(Ruleset.load(), n=a.n, seed=a.seed)
    if a.write:
        Path(a.write).parent.mkdir(parents=True, exist_ok=True)
        Path(a.write).write_text(text, encoding="utf-8")
        print(f"wrote {a.write}")
    else:
        print(text)


def cmd_explain(a):
    rs = Ruleset.load()
    traits = {}
    for pair in a.traits:
        k, v = pair.split("=", 1)
        traits[k] = v.split(",") if k in rs.multi else v
    missing = [t for t in rs.order if t not in traits]
    vs = rs.violations(traits, partial=True)
    if missing:
        print(f"(not given, so rules that need them were skipped: {', '.join(missing)})")
    if not vs:
        print("No rule is broken.")
    for v in vs:
        print(f"  {v}")
    sys.exit(1 if vs else 0)


def cmd_review(a):
    rs, prose = Ruleset.load(), load_prose()
    out = ["# GHOSTLIGHT Phase 2: entries for marking", "",
           "Put an x in the box for each entry that lands. The ones that do not land are as useful as the ones that do.", ""]
    for i in range(a.n):
        e = make_entity(f"{a.seed}-{i}", rs, prose)
        en, t = e["entry"], e["traits"]
        out += [f"## [ ] {i + 1}. {en['common_name']}", "",
                f"*{t['kind']}, {t['region']}, {t['era']}, {t['origin']}, {t['manifestation']}, {t['conditions']}*", "",
                en["local_name"], "", en["description"], "", en["first_account"], "", en["precaution"], ""]
    Path(a.write).write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {a.write}")


def cmd_entity(a):
    print(json.dumps(make_entity(a.seed), indent=2, ensure_ascii=False))


def cmd_found(a):
    print(canon.found(a.date, a.n))


def cmd_tick(a):
    print(json.dumps(canon.tick(a.date, force_entity=a.force_entity, allow_repeat=a.repeat), indent=2))


def cmd_check(a):
    problems = canon.check()
    for e in canon.entities():
        diffs = canon.reproduce(e)
        if diffs:
            problems.append(f"{e['id']}: does not reproduce from its seed ({', '.join(diffs)} differ)")
    for p in problems:
        print(p)
    n_e, n_s = len(canon.entities()), len(canon.sightings())
    print(f"{n_e} entities, {n_s} sightings: {'OK' if not problems else f'{len(problems)} problem(s)'}")
    sys.exit(1 if problems else 0)


def cmd_guard(a):
    problems = canon.guard(a.base)
    for p in problems:
        print(p)
    print("canon is append-only: OK" if not problems else "canon was altered")
    sys.exit(1 if problems else 0)


def cmd_build(a):
    from .site import build
    out = build(Path(a.out) if a.out else None)
    print(f"built {out}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="ghostlight", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    today = dt.date.today().isoformat()

    s = sub.add_parser("sample"); s.add_argument("--n", type=int, default=20); s.add_argument("--seed", default="phase1")
    s.add_argument("--write"); s.set_defaults(f=cmd_sample)
    s = sub.add_parser("explain"); s.add_argument("traits", nargs="+"); s.set_defaults(f=cmd_explain)
    s = sub.add_parser("review"); s.add_argument("--n", type=int, default=10); s.add_argument("--seed", default="review")
    s.add_argument("--write", default="reports/phase2_review.md"); s.set_defaults(f=cmd_review)
    s = sub.add_parser("entity"); s.add_argument("--seed", required=True); s.set_defaults(f=cmd_entity)
    s = sub.add_parser("found"); s.add_argument("--n", type=int, default=3); s.add_argument("--date", default=today); s.set_defaults(f=cmd_found)
    s = sub.add_parser("tick"); s.add_argument("--date", default=today); s.add_argument("--force-entity", action="store_true")
    s.add_argument("--repeat", action="store_true", help="allow a second tick on the same date"); s.set_defaults(f=cmd_tick)
    s = sub.add_parser("check"); s.set_defaults(f=cmd_check)
    s = sub.add_parser("guard"); s.add_argument("--base", default="HEAD"); s.set_defaults(f=cmd_guard)
    s = sub.add_parser("build"); s.add_argument("--out"); s.set_defaults(f=cmd_build)
    a = p.parse_args(argv)
    a.f(a)


if __name__ == "__main__":
    main()
