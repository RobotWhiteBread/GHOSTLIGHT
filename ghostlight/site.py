"""Build the static site from the canon. Output goes to _site/, which is
never committed; the workflow rebuilds it on every run."""
from __future__ import annotations

import datetime as dt
import re
import shutil
from collections import defaultdict
from email.utils import format_datetime
from html import escape
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

from .canon import ROOT, config, entities, sightings
from .entity import load_prose
from .plate import plate
from .rules import Ruleset
from .sightings import load_voices


def md_inline(text: str) -> Markup:
    """The prose uses *asterisks* for local names; nothing else."""
    return Markup(re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escape(text)))


def rfc822(date: str) -> str:
    d = dt.datetime.fromisoformat(date).replace(hour=12, tzinfo=dt.timezone.utc)
    return format_datetime(d)


def build(out: Path | None = None) -> Path:
    out = out or ROOT / "_site"
    if out.exists():
        shutil.rmtree(out)
    (out / "entities").mkdir(parents=True)
    (out / "index").mkdir()
    shutil.copytree(ROOT / "static", out / "static")

    cfg = config()
    rs, prose, sv = Ruleset.load(), load_prose(), load_voices()
    ents = entities()
    sights = sightings()
    by_id = {e["id"]: e for e in ents}
    dossier = defaultdict(list)
    for s in sights:
        dossier[s["entity"]].append(s)
    for v in dossier.values():
        v.sort(key=lambda s: (s["year"], s["month"], s["day"]))

    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape(["html", "xml"]))
    env.filters["md"] = md_inline
    label = lambda trait, key: rs.value(trait, key)["label"]  # noqa: E731
    env.globals.update(site=cfg["site"], label=label, voices=sv["voices"], by_id=by_id,
                       built=dt.date.today().isoformat())

    for e in ents:
        tags = set(rs.value("manifestation", e["traits"]["manifestation"]).get("tags", []))
        e["plate"] = Markup(plate(e, tags))
        e["url"] = f"entities/{e['slug']}.html"
        e["dossier"] = dossier[e["id"]]

    # activity: entities and sightings, newest report first
    activity = [{"kind": "entity", "date": e["created"], "entity": e} for e in ents]
    activity += [{"kind": "sighting", "date": s["reported"], "entity": by_id[s["entity"]], "s": s} for s in sights]
    activity.sort(key=lambda a: (a["date"], a["kind"] == "sighting", a.get("s", {}).get("id", a["entity"]["id"])),
                  reverse=True)

    def render(name, path, **ctx):
        root = "../" * path.count("/")
        (out / path).write_text(env.get_template(name).render(root=root, **ctx), encoding="utf-8")

    newest = sorted(ents, key=lambda e: (e["created"], e["id"]), reverse=True)
    render("home.html", "index.html", newest=newest, activity=activity[:8], n_ents=len(ents), n_sights=len(sights))
    render("recent.html", "recent.html", activity=activity)
    render("about.html", "about.html", rules=rs.rules, cadence=cfg["cadence"], meta=rs.meta)
    for e in ents:
        render("entity.html", e["url"], e=e)

    def index_by(trait, title, path, order=None):
        groups = defaultdict(list)
        for e in ents:
            groups[e["traits"][trait]].append(e)
        keys = order or sorted(groups, key=lambda k: label(trait, k))
        sections = [(k, label(trait, k), sorted(groups[k], key=lambda e: e["entry"]["common_name"])) for k in keys if k in groups]
        render("index.html", path, title=title, trait=trait, sections=sections)

    index_by("region", "By region", "index/region.html")
    index_by("era", "By era", "index/era.html", order=list(rs.traits["era"]))
    index_by("manifestation", "By manifestation", "index/manifestation.html")
    index_by("kind", "By kind", "index/kind.html", order=list(rs.traits["kind"]))

    feed = env.get_template("feed.xml").render(items=activity[:60], rfc822=rfc822,
                                               base=cfg["site"]["base_url"].rstrip("/") + "/")
    (out / "feed.xml").write_text(feed, encoding="utf-8")
    (out / ".nojekyll").write_text("")
    return out
