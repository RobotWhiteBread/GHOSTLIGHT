"""Run with: python -m pytest -q"""
import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ghostlight import seeds  # noqa: E402
from ghostlight.entity import lint, load_prose, make_entity  # noqa: E402
from ghostlight.rules import Ruleset  # noqa: E402
from ghostlight.sightings import check_sightings, load_voices, make_sighting  # noqa: E402

RS, PROSE, SV = Ruleset.load(), load_prose(), load_voices()


def test_every_draw_obeys_every_rule():
    for i in range(300):
        assert RS.violations(RS.draw(seeds.rng("t", i))) == []


def test_every_value_is_reachable():
    seen = {t: set() for t in RS.order}
    for i in range(1500):
        a = RS.draw(seeds.rng("reach", i))
        for t in RS.order:
            seen[t].update(a[t] if isinstance(a[t], list) else [a[t]])
    for t in RS.order:
        assert seen[t] == set(RS.traits[t]), f"{t} never draws {set(RS.traits[t]) - seen[t]}"


def test_violations_are_named():
    bad = {"kind": "haunt", "origin": "drowned_ford"}
    ids = {v.rule_id for v in RS.violations(bad, partial=True)}
    assert "R01" in ids


def test_prose_banks_cover_every_value():
    for cat in ("origin", "manifestation", "disposition", "conditions", "signs", "remedy", "region", "community", "era", "kind"):
        assert set(PROSE[cat]) == set(RS.traits[cat]), cat


def test_entries_are_clean_and_reproducible():
    for i in range(150):
        e = make_entity(f"p{i}", RS, PROSE)
        assert lint(PROSE, e["traits"], list(e["entry"].values())[:5]) == []
        assert make_entity(f"p{i}", RS, PROSE) == e


def test_no_em_dashes_anywhere_in_data():
    for p in (ROOT / "data").glob("*.yaml"):
        text = p.read_text(encoding="utf-8")
        assert "\u2014" not in text and "\u2013" not in text, p


def test_sightings_stay_consistent():
    for i in range(80):
        e = make_entity(f"s{i}", RS, PROSE)
        e["id"] = f"GL-{i:04d}"
        prior = []
        for n in range(1, 12):
            prior.append(make_sighting(e, prior, f"s{i}-{n}", "2026-11-21", n, RS, PROSE, SV))
        assert check_sightings(e, prior, RS, PROSE, SV) == []


def test_contradicting_detail_is_caught():
    from ghostlight.sightings import detail_slots
    e = next(x for x in (make_entity(f"detail{i}", RS, PROSE) for i in range(200)) if detail_slots(x, RS, SV))
    e["id"] = "GL-9999"
    prior = []
    for n in range(1, 30):
        prior.append(make_sighting(e, prior, f"d{n}", "2026-11-21", n, RS, PROSE, SV))
    with_detail = [s for s in prior if s["details"]]
    if not with_detail:
        pytest.skip("this manifestation has no detail slots")
    s = dict(with_detail[-1])
    k = next(iter(s["details"]))
    s["details"] = {k: "something else entirely"}
    s["id"] = "GL-9999-S999"
    assert any("established" in p for p in check_sightings(e, prior + [s], RS, PROSE, SV))


@pytest.fixture()
def sandbox(tmp_path):
    dst = tmp_path / "gl"
    shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns(".git", "_site", "canon", "__pycache__"))
    run = lambda *a: subprocess.run([sys.executable, "-m", "ghostlight", *a], cwd=dst, capture_output=True, text=True)  # noqa: E731
    subprocess.run(["git", "init", "-q"], cwd=dst, check=True)
    return dst, run


def test_simulated_months_and_append_only(sandbox):
    dst, run = sandbox
    assert run("found", "--n", "2", "--date", "2026-01-01").returncode == 0
    d = dt.date(2026, 1, 5)
    for _ in range(16):
        r = run("tick", "--date", d.isoformat())
        assert r.returncode == 0, r.stderr
        d += dt.timedelta(days=7)
    assert "skipped" in run("tick", "--date", (d - dt.timedelta(days=7)).isoformat()).stdout
    r = run("check")
    assert r.returncode == 0, r.stdout
    assert run("build").returncode == 0
    assert (dst / "_site" / "feed.xml").exists()

    subprocess.run(["git", "add", "-A"], cwd=dst, check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"], cwd=dst, check=True)
    assert run("guard").returncode == 0
    victim = next((dst / "canon" / "entities").glob("*.json"))
    data = json.loads(victim.read_text())
    data["entry"]["common_name"] = "Something Else"
    victim.write_text(json.dumps(data))
    assert run("guard").returncode == 1
