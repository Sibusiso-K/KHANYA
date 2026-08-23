# ADR-0003 — One build, two names: REEFPRINT, otherwise known as KHANYA

- **Date:** 2026-08-20
- **Status:** Accepted
- **Decider:** Lethabo Hoaeane (single technical decision-maker, CLAUDE.md)
- **Relates to:** CLAUDE.md rule 8 (commit history is the originality defence); JOINT-PLAN §5
  (two commit histories, named as a risk); the ten-minute narrative

## Context

The system exists as two codebases with two names and two commit histories.

**REEFPRINT** is the specification, the physics, and the measurement half: the constitution, the
ADRs, the Stokes inversion, the geometry discriminator, the fourth-harmonic estimator, the
acquisition boundary, the bridge. **KHANYA** is Sibusiso's build: the segmentation model, the
modal-mineralogy and liberation calculators, the conformal calibration machinery, and the
offline dashboard. They were built in parallel from the same design spec, and
[`JOINT-PLAN.md`](https://github.com/Sibusiso-K/KHANYA) already establishes that they are two
halves of one system rather than two competing attempts at the whole.

That leaves a naming problem which is not cosmetic. Two names in circulation for one submission
invites three failures:

1. A judge hears both and concludes there are two projects, or one project that could not decide
   what it was.
2. The ten-minute talk spends time on provenance instead of physics.
3. Documentation drifts, with modules described under whichever name their author used.

The obvious fix — pick one name, rename the other — costs more than it returns 42 days out. It
would mean renaming a Python package (`reefprint.*`), rewriting every import in both repos, and
invalidating the paths in every doc, ADR and experiment README, all for a label. It would also
blur the commit histories at precisely the moment they need to stay legible: finalists face
originality authentication after 2 October, and two clean parallel histories are better evidence
of independent work than one history with a rename commit in the middle of it.

## Decision

**The build is called REEFPRINT, otherwise known as KHANYA. Both names are correct, they name the
same system, and neither is deprecated.**

REEFPRINT leads: it is the name on the spec, the ADRs, the physics claim and the package
namespace. KHANYA is the same build's other name, and it is the better name for what the system
*does* — *khanya* is "to shine, to give light" in the Nguni languages, which is exactly the
measurement: what a mineral does under polarised light when the analyser turns. Pentlandite stays
dark. Pyrrhotite lights up.

In practice:

- **First mention in any external artefact** — abstract, slides, submission, README — reads
  "REEFPRINT (also known as KHANYA)" or "REEFPRINT / KHANYA". Every mention after that is
  REEFPRINT alone.
- **No code is renamed.** The `reefprint.*` package keeps its name; KHANYA's `src/*` keeps
  its. Import paths, module docstrings and test names are untouched.
- **No histories are merged.** REEFPRINT's history lives on the `reefprint` branch of the KHANYA
  repository, unmerged, so both are in one place to read and still separate to authenticate.

## Consequences

**Easier.** One product to talk about, with a name that carries meaning in a South African room
and a name that carries the geology. Both authors' work is findable under the name they used for
it. The originality trail stays two clean parallel histories.

**Harder.** Every external artefact now carries a small consistency obligation: give both names
once, then stop. A doc that says only "KHANYA" and never "REEFPRINT" is now a defect, and so is
the reverse.

**Foreclosed.** Renaming either package before 1 October. If the dual name proves confusing in
rehearsal, the fix is to change how the talk introduces it, not to rename modules.

## Alternatives rejected

| Option | Why not |
|---|---|
| Rename KHANYA's code to `reefprint.*` and merge | Costs a package rename, an import sweep across two repos, and a merge JOINT-PLAN §5 explicitly warns against — 42 days out, for a label. Also collapses the two histories that are the originality defence. |
| Rename REEFPRINT to KHANYA | Same cost, and it discards the name on every ADR, doc and experiment README, plus the package namespace. |
| Pick one name, leave the other repo untouched and unmentioned | Half of the built system becomes invisible in the submission, and the author of that half is uncredited. |
| Treat them as two separate projects | False. They share a spec, a seam (`reefprint.bridge` ↔ KHANYA's masks) and one submission. |

## What would change this

A judge, mentor or Mintek reviewer telling us in rehearsal that the dual name reads as
indecision rather than as one system with two authors. That is an observation about the audience,
and it would be answered by changing the introduction — not by renaming code.
