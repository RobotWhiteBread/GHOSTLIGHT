# GHOSTLIGHT: build prompts

---

## Phase 1: the folkloric rules, before any entities

```
I am building a generative field guide to hauntings. It must feel discovered
rather than randomly assembled, so the constraint system comes first.

Interview me before writing code: ask what regions and eras this guide
covers, what kinds of entity exist in its world, and what the house style of
the writing is. Do not generate anything until the folklore has a logic.

Then implement the rule system in Python:
- Traits: manner of origin, manner of manifestation, region, era, the
  conditions that summon it, the sensory signs of its presence, the
  apotropaic remedy, and its disposition toward the living
- Constraints linking them, so that the remedy fits the region, the
  manifestation fits the origin, and the signs fit the manifestation
- Rules in an editable data file, not in code
- On rejection, tell me which rule was violated

Generate 20 and show me the trait distribution. I want to see whether the
rules are too loose, which will read as random, or too tight, which will make
every entity a variation of one.
```

## Phase 2: the prose

```
Add generated entries in the voice of a 19th century folklore survey:
a common name, a local name in the region's idiom, a formal description, the
circumstances of first recorded account, and the recommended precaution.

Requirements:
- The prose must never contradict the traits. Tell me how you are
  guaranteeing that rather than hoping for it
- Vary sentence structure across entries, or twenty entries will read as one
  template filled in twenty times
- Period-appropriate vocabulary without descending into parody

Generate ten and let me mark which ones land. Then tell me what distinguished
the good ones, because that is what the generator needs more of.
```

## Phase 3: publish itself, forever

```
Make this run without me.

Build: a static site that presents the guide, a generator invocation that
adds exactly one new entity, and a GitHub Actions workflow on a cron
schedule that runs the generator, commits the new entity, and redeploys.

Requirements:
- Deterministic given a seed, so I can reproduce any entity, but the seed
  advances on its own so I do not know what is coming
- The new entity must never overwrite or alter an existing one. The canon is
  append-only
- An index by region, era, and manifestation type
- An RSS feed, so the guide can be subscribed to

Tell me the cadence you recommend and why. I suspect weekly is too fast and
monthly is too slow.
```

## Phase 4: accretion

```
Now the part that makes it alive. Existing entities should accumulate
reported sightings over time, so an older entry has a thicker dossier than a
new one.

Generate sightings as dated accounts in varied voices: a parish record, a
newspaper notice, a letter, a modern forum post. Each must be consistent with
that entity's established traits and with every sighting already recorded for
it.

Add a "recent activity" view so the site shows what has been reported lately
across the whole guide, rather than only what is new.
```
