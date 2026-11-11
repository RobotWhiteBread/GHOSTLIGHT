# GHOSTLIGHT

**A generative field guide to hauntings that is never finished.**

A folklore grammar generates a new entity on a schedule, forever. Each one
arrives with its manner of manifestation, the region and era it belongs to,
the conditions under which it appears, the apotropaic remedy that wards it
off, and a log of reported sightings that keeps growing after the entity
itself is created. The whole thing publishes to a website that accretes over
months, so the canon deepens while you are not looking.

Named for the single bulb left burning on an empty stage, which theater
people leave on to keep the ghosts away.

## Why this one is different

Every other project on these lists has a finish line. This one runs
indefinitely and surprises its own author, which makes it the only piece
here that behaves like a living thing rather than an artifact.

The engineering is modest: a scheduled job, a generator, a static site
rebuild, a commit. The design problem is the hard part.

## The actual design problem

Folkloric coherence. A wisp that haunts crossroads should not also be warded
off by salt thrown over the shoulder at sea. Real folklore has internal
logic: the manner of death constrains the manner of haunting, the region
constrains the remedy, the era constrains the vocabulary of the account.

If the generator ignores that, every entity reads as a random draw from three
lists and the guide dies on arrival. If it respects it, the entries start to
feel discovered rather than assembled.

## Stack
Python for the generator and the constraint rules, Tracery for the grammar,
a static site generator for the public face, and a scheduled task to run it.

## Milestones
1. A rule system and grammar producing 20 entities that all obey one coherent
   folkloric logic, with the rules in an editable data file
2. Published as a static site that rebuilds and commits itself on a schedule,
   with a new entity appearing without you touching anything

## Stretch
Sighting accounts that accumulate over time in period-appropriate voices, so
an entity created in March has a thicker dossier by September than one
created last week.

## Relationship to HOLOTYPE

HOLOTYPE is biology: the constraint solver enforces anatomical plausibility
and the output is a finished printed book. GHOSTLIGHT is folklore: coherence
is narrative rather than physical, and it never completes. Shared machinery,
opposite temperaments.

## Next step
Write the folkloric rules for a single region and era before generating
anything. The rules are the project.
