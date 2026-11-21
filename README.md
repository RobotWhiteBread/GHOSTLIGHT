# GHOSTLIGHT

**A generative field guide to hauntings that is never finished.**

A folklore grammar enters a new entity on a schedule, forever. Each one
arrives with its manner of manifestation, the region and era it belongs to,
the conditions under which it appears, the remedy that wards it off, and a
dossier of reported sightings that keeps growing after the entity itself is
entered. The whole thing publishes to a website that accretes over months,
so the canon deepens while you are not looking.

Named for the single bulb left burning on an empty stage, which theater
people leave on to keep the ghosts away.

The first world is **the Great Plains, 1850 to 1930**: six regions from the
Sandhills to the High Plains, five eras from the trail years to the dry
years, eleven settler communities, and every kind of thing: revenants,
lights, spirits of land and weather, haunted objects and places. The voice is
a dry 19th century folklore survey that lets the quoted witnesses carry the
dread.

## How it works

| Piece | Where | What it does |
|---|---|---|
| The rules | `data/rules.yaml` | Every trait, every value, and 32 constraints linking them. Edit freely; the code only reads it. |
| The prose | `data/prose.yaml` | A phrase bank for every trait value, plus voice templates that carry no folklore of their own. |
| The sightings | `data/sightings.yaml` | Six voices (parish record, newspaper notice, letter home, Federal Writers' Project interview, oral history, forum post) and the details a sighting may establish. |
| The canon | `canon/` | One JSON file per entity, per sighting, per tick. Append-only. |
| The site | `templates/`, `static/` | Built to `_site/` and deployed to GitHub Pages. |
| The schedule | `.github/workflows/accrete.yml` | Every Monday: tick, guard, check, commit, deploy. |

### Coherence (Phase 1)

Rules are typed (`contains`, `features`, `years`, `needs_tags`, `opposed`,
`share`, `when`) and each has a plain-language `why` that the site publishes.
Traits are drawn one at a time and a value is never accepted if it breaks a
rule that can already be checked. To test a hand-built combination:

```
python -m ghostlight explain kind=haunt origin=drowned_ford region=high_plains
```

which prints every rule it breaks, by id and reason.

`reports/phase1_distribution.md` answers the too-loose, too-tight question.
Of 5,000 entities drawn with the rules ignored, under a tenth of a percent
would pass. Twenty drawn with the rules share only about 13 percent of their
traits on average, with no near-duplicates.

### Prose that cannot contradict its traits (Phase 2)

This is guaranteed by construction, not by hope:

1. Templates carry structure and voice only. Every claim about origin,
   manifestation, signs, conditions, remedy and temper is drawn from the
   phrase bank of the value the entity actually has.
2. Values list `markers`, words that belong to them alone. After an entry is
   written, a lint checks that no marker of any value the entity did *not*
   draw appears in the text. A failing entry is rewritten from the next
   sub-seed; if none pass, generation fails loudly rather than publishing.
3. The lint also rejects em and en dashes and any unexpanded grammar symbol.

Four interchangeable templates for each section, varied sentence order, and
per-entity facts (names, places, the year, what light people carried in that
era) keep twenty entries from reading as one form filled twenty times.
`reports/phase2_review.md` has ten entries to mark and notes on what
separated the good ones.

### Publishing itself (Phase 3)

- **Deterministic.** Every random choice descends from one seed through named
  branches. Each entity stores its seed; `python -m ghostlight entity --seed
  <seed>` regenerates it exactly, and `check` verifies that for the whole
  canon.
- **The seed advances on its own.** Each tick's seed is the master seed folded
  with a hash of the entire canon as it stands. Nobody picks it, and it
  changes every time anything is added.
- **Append-only.** New files are opened in exclusive-create mode, which fails
  if the file exists. `guard` fails the run if anything under `canon/` was
  modified, renamed or deleted, and runs on every tick and every push.
- **Indexes** by region, era, manifestation and kind, a recent-activity page,
  and an RSS feed at `/feed.xml`.

**Cadence: a weekly tick, a new entity every other week, sightings every week.**
Weekly entities would make the guide feel like a content feed, and readers
would stop opening each one. Monthly is long enough that a subscriber forgets
it exists. Every other week gives about 26 entries a year, while the weekly
sightings mean the guide visibly changes every Monday. Older entries
accumulate faster than new ones simply because they have been waiting
longer, and the number of sightings per week grows by one for every ten
entities on file. Both numbers live in `ghostlight.yaml`.

### Accretion (Phase 4)

Each week some existing entities receive a sighting, dated anywhere from
just after the first account to the present, in a voice that fits the year:
no forum posts in 1890, no parish registers in 2015. Every sighting is checked
against the entity and against every sighting already on file:

- it reports only the entity's own manifestation, condition and signs
- its month fits the condition (no haying in January), and anniversary
  sightings all fall on the same date, the date of the death
- small details (a light's color, what a rider wears, which way a whirlwind
  turns) are set once by whichever sighting first mentions them and can never
  change afterward
- a sighting that cites an earlier one ("there is a newspaper notice about it
  from 1911") cites one that exists, is earlier, and gets the year right
- nothing is dated after the day it was reported

## Running it

```
pip install -r requirements.txt
python -m ghostlight tick          # one weekly turn
python -m ghostlight check         # validate the whole canon
python -m ghostlight build         # site into _site/
python -m pytest -q                # tests, including a simulated four months
```

On Windows, open `_site\index.html` in a browser after building.

### Turning on the schedule

The workflow is in place. Two things only you can do in the repo settings:

1. **Pages.** Settings, Pages, Source: *GitHub Actions*. GitHub Pages on a
   private repository needs a paid plan (Pro, Team or Enterprise). On a free
   account, make the repository public or the deploy step will fail; the tick
   itself will still run and commit.
2. **Actions write access.** Settings, Actions, General, Workflow permissions:
   *Read and write*, so the tick can commit.

Then run the workflow once by hand (Actions, accrete, Run workflow) to
confirm, or wait for Monday.

## Relationship to HOLOTYPE

HOLOTYPE is biology: the constraint solver enforces anatomical plausibility
and the output is a finished printed book. GHOSTLIGHT is folklore: coherence
is narrative rather than physical, and it never completes. Shared machinery,
opposite temperaments.

## A note on sources

Every entity is invented, in the manner of settler folklore. Local names use
real public-domain folk vocabulary of the communities that settled the
plains (Czech *bludička*, Swedish *lyktgubbe*, Norwegian *draug*, German
*Irrlicht*). Indigenous sacred beings and ceremonies are deliberately left out
of the grammar; they are not ours to generate.

## Next

- A second world in its own rules file (Appalachia, or the British Isles),
  selected in `ghostlight.yaml`
- More precaution and testimony variants before the guide reaches fifty entries
- Public-domain engraving collage for the plates (see `REPOS.md`)
