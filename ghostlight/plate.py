"""Procedural plates: a small engraved-looking SVG for each entity, drawn only
from its own traits and seed."""
from __future__ import annotations

import math

from . import seeds

W, H = 360, 220
INK = "#e8dcc0"
GLOW = "#f3c46b"


def _horizon(region: str, rng) -> tuple[list[tuple[float, float]], float]:
    base = H * 0.68
    pts = []
    for i in range(0, W + 1, 6):
        x = i
        if region == "sandhills":
            y = base - 18 * abs(math.sin(i / 47 + rng.random() * 0.05)) - 6 * math.sin(i / 13)
        elif region == "flint_hills":
            y = base - 12 * math.sin(i / 70) - 4 * math.sin(i / 19)
        elif region == "high_plains":
            y = base - (8 if 120 < i < 220 else 0) + rng.uniform(-0.6, 0.6)
        elif region == "smoky_hill":
            y = base - (14 if 240 < i < 300 else 0) - 2 * math.sin(i / 9)
        else:
            y = base + rng.uniform(-0.8, 0.8)
        pts.append((x, y))
    return pts, base


def _hatch(rng, y0, y1, step=5, jitter=1.2):
    out = []
    y = y0
    while y < y1:
        out.append(f'<line x1="0" y1="{y:.1f}" x2="{W}" y2="{y + rng.uniform(-jitter, jitter):.1f}" />')
        y += step + (y - y0) * 0.06
    return "".join(out)


def _glyph(manifestation: str, tags: set[str], rng, gx: float, gy: float) -> str:
    if "light" in tags and manifestation != "fire_line":
        n = 6 if manifestation == "meadow_lights" else 1
        parts = []
        for i in range(n):
            x = gx + (i - n / 2) * 26 + rng.uniform(-6, 6)
            y = gy - 10 - rng.uniform(0, 18 if n > 1 else 0)
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="16" fill="url(#glow)" />'
                         f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="{GLOW}" />')
        return "".join(parts)
    if manifestation == "fire_line":
        d = " ".join(f"L{x},{gy - 2 - rng.uniform(0, 7):.1f}" for x in range(20, W - 20, 7))
        return f'<path d="M20,{gy} {d}" stroke="#d9734a" stroke-width="1.6" fill="none" />'
    if "figure" in tags:
        s = 1.0 if manifestation != "rider" else 1.25
        body = (f'<g transform="translate({gx:.1f},{gy:.1f}) scale({s})" fill="none" stroke="{INK}" stroke-width="1.4" opacity="0.75">'
                f'<circle cx="0" cy="-34" r="4" /><path d="M0,-30 L0,-12 M0,-26 L-6,-16 M0,-26 L6,-17 M0,-12 L-4,0 M0,-12 L4,0" />')
        if manifestation == "rider":
            body += '<path d="M-14,-10 Q0,-18 14,-10 L16,4 M-12,-10 L-14,4 M14,-10 Q20,-16 22,-22" />'
        return body + "</g>"
    if "wind" in tags or manifestation == "whirlwind":
        pts = []
        for i in range(60):
            t = i / 60
            r = 3 + t * 16
            pts.append(f"{gx + r * math.cos(t * 18):.1f},{gy - t * 60:.1f}")
        return f'<polyline points="{" ".join(pts)}" fill="none" stroke="{INK}" stroke-width="1" opacity="0.7" />'
    if manifestation in ("bell_ringing",):
        return (f'<path d="M{gx - 12},{gy - 4} Q{gx - 12},{gy - 34} {gx},{gy - 36} Q{gx + 12},{gy - 34} {gx + 12},{gy - 4} Z" '
                f'fill="none" stroke="{INK}" stroke-width="1.4" />'
                + "".join(f'<path d="M{gx + 18 + k * 7},{gy - 28} q6,8 0,16" stroke="{INK}" fill="none" opacity="{0.6 - k * 0.15}" />' for k in range(3)))
    if manifestation in ("singing_wire",) or "iron" in tags:
        posts = "".join(f'<line x1="{x}" y1="{gy}" x2="{x}" y2="{gy - 22}" />' for x in range(30, W - 20, 48))
        wires = "".join(f'<path d="M30,{gy - 8 - k * 6} Q{W / 2},{gy - 4 - k * 6} {W - 30},{gy - 8 - k * 6}" fill="none" />' for k in range(3))
        return f'<g stroke="{INK}" stroke-width="1" opacity="0.8">{posts}{wires}</g>'
    if "home" in tags or manifestation in ("knocking", "set_supper"):
        return (f'<g fill="none" stroke="{INK}" stroke-width="1.3"><path d="M{gx - 26},{gy} L{gx - 26},{gy - 22} L{gx},{gy - 36} '
                f'L{gx + 26},{gy - 22} L{gx + 26},{gy} Z" /><rect x="{gx - 5}" y="{gy - 14}" width="10" height="14" />'
                f'<rect x="{gx + 10}" y="{gy - 20}" width="8" height="7" fill="{GLOW}" opacity="0.8" /></g>')
    if "cold" in tags:
        return "".join(f'<circle cx="{gx + rng.uniform(-50, 50):.1f}" cy="{gy - rng.uniform(0, 60):.1f}" r="{rng.uniform(0.6, 1.8):.1f}" fill="{INK}" />' for _ in range(70))
    if "sound" in tags:
        return "".join(f'<path d="M{gx + k * 10},{gy - 30} q8,12 0,24" stroke="{INK}" fill="none" opacity="{0.85 - k * 0.15}" />' for k in range(5))
    if "heat" in tags:
        return "".join(f'<path d="M{gx - 40 + k * 8},{gy} q3,-8 0,-16 q-3,-8 0,-16" stroke="{GLOW}" fill="none" opacity="0.5" />' for k in range(11))
    return f'<circle cx="{gx}" cy="{gy - 20}" r="10" fill="none" stroke="{INK}" />'


def plate(entity: dict, manifestation_tags: set[str]) -> str:
    t = entity["traits"]
    rng = seeds.rng(entity["seed"], "plate")
    pts, base = _horizon(t["region"], rng)
    ground = "M0,%d " % H + " ".join(f"L{x},{y:.1f}" for x, y in pts) + f" L{W},{H} Z"
    day = t["conditions"] in ("drought_noon", "haying", "threshing")
    sky = ""
    if day:
        sky = f'<circle cx="{W * 0.78:.0f}" cy="40" r="14" fill="none" stroke="{INK}" stroke-width="1.2" />'
    else:
        stars = "".join(f'<circle cx="{rng.uniform(0, W):.1f}" cy="{rng.uniform(4, base - 40):.1f}" r="{rng.uniform(0.3, 1.1):.1f}" fill="{INK}" opacity="{rng.uniform(0.3, 0.9):.2f}" />' for _ in range(55))
        moon = rng.uniform(0.15, 0.85) * W
        sky = stars + f'<path d="M{moon:.0f},26 a12,12 0 1,0 10,18 a9,9 0 1,1 -10,-18 Z" fill="{INK}" opacity="0.85" />'
    water = ""
    if "water" in manifestation_tags or t["origin"] in ("drowned_ford", "well_cavein") or t["region"] == "platte":
        water = "".join(f'<line x1="{rng.uniform(0, W * 0.6):.0f}" y1="{base + 14 + k * 5}" x2="{rng.uniform(W * 0.5, W):.0f}" y2="{base + 14 + k * 5}" stroke="{INK}" opacity="0.35" />' for k in range(4))
    gx = rng.uniform(W * 0.3, W * 0.7)
    gy = min(y for x, y in pts if abs(x - gx) < 6) - 2
    grass = "".join(f'<line x1="{x:.1f}" y1="{H}" x2="{x + rng.uniform(-3, 3):.1f}" y2="{H - rng.uniform(6, 22):.1f}" />' for x in (rng.uniform(0, W) for _ in range(140)))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="Plate: {entity['entry']['common_name']}">
<defs><radialGradient id="glow"><stop offset="0" stop-color="{GLOW}" stop-opacity="0.9"/><stop offset="1" stop-color="{GLOW}" stop-opacity="0"/></radialGradient></defs>
<rect width="{W}" height="{H}" fill="#16130f"/>
<g stroke="{INK}" stroke-width="0.4" opacity="0.18">{_hatch(rng, 0, base, 6)}</g>
{sky}
<path d="{ground}" fill="#1d1913" stroke="{INK}" stroke-width="1.1"/>
<g stroke="{INK}" stroke-width="0.5" opacity="0.22">{_hatch(rng, base + 4, H, 4, 0.6)}</g>
{water}
<g stroke="{INK}" stroke-width="0.6" opacity="0.45">{grass}</g>
{_glyph(t["manifestation"], manifestation_tags, rng, gx, gy)}
<rect x="3" y="3" width="{W - 6}" height="{H - 6}" fill="none" stroke="{INK}" stroke-width="0.8" opacity="0.6"/>
</svg>'''
    eid = entity.get("id", "x").lower()
    return svg.replace('id="glow"', f'id="glow-{eid}"').replace("url(#glow)", f"url(#glow-{eid})")
