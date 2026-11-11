# GHOSTLIGHT: repositories and references

Verified 2026-11-11.

## Generation

| Repo | What it gives you |
|---|---|
| https://github.com/galaxykate/tracery | Grammar-based text generation. The standard tool for this kind of work, and small enough to read in an afternoon |
| https://github.com/mxgmn/WaveFunctionCollapse | Constraint propagation. Read the README for the idea even if you do not use the code: locally consistent generation is exactly your problem |
| python-constraint, or https://github.com/Z3Prover/z3 | Real constraint solvers, when hand-rolled rules stop scaling |

## Publishing

| Tool | Notes |
|---|---|
| Eleventy (11ty) | Minimal static site generator, plain JavaScript, no framework ceremony |
| Astro | More capable, good if you want interactive bits later |
| Hugo | Fastest builds, Go templating |

Any of the three is fine. Pick the one whose templating you will tolerate,
because you will be editing templates more than you expect.

## Scheduling

- **GitHub Actions on a cron schedule** is the obvious host: it runs the
  generator, commits the new entity, and redeploys the site, all without a
  machine of yours being awake. Free for public repos and cheap for private.
- A local scheduled task works too, but then the canon only grows when your
  computer is on.

## Plates

Illustration options, in increasing order of effort:
- Procedural SVG from the entity's own traits
- Public-domain engraving collage, since 19th century spiritualist and
  folklore illustration is out of copyright
- A diffusion LoRA, which is literally the GRAIN project. Train on
  public-domain folklore plates and the two projects feed each other

## Reference

- Search terms: "apotropaic magic", "generative grammar constraints",
  "Aarne-Thompson-Uther index", "folklore motif index", "revenant folklore",
  "static site generator cron github actions"
- The Aarne-Thompson-Uther tale type index and Stith Thompson's motif index
  are the real-world versions of the structure you are building. Worth
  reading about before you invent your own taxonomy

## A note on sources

Keep this to invented entities and public-domain folklore. Generating a
pastiche of a living author's creatures, or of a specific modern franchise's
bestiary, turns a lovely project into someone else's intellectual property.
