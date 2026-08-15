# ADR-0002 — Software only. No instrument is built.

- **Date:** 2026-08-15
- **Status:** Accepted
- **Decider:** Lethabo Mphukuile
- **Relates to:** CLAUDE.md hard constraints · week-1 and week-5 gates · gauntlet **H1/H2** (build risk) · [ADR-0001](0001-ome-tiff-via-tifffile-not-bioformats.md)

## Context

CLAUDE.md described a ~R5,000 physical instrument: Pi 5, HQ camera, OpenFlexure stage, steppers
on a PCA9685, a multispectral LED ring, polarisers salvaged from dead LCD panels, and resin
polished sections. Every weekly gate through week 5 was written assuming it existed.

The decision-maker has ruled that none of it is being bought.

This is not a small edit to the plan. Roughly half of the original week-1 through week-3 schedule
was build-and-calibrate work, and the entire training-data story assumed captures from a
purpose-built rig. Removing the rig removes both, and the honest question is whether anything
survives. It does, for one reason: **the physics that carries the claim is a property of the data,
not of the instrument that produced it.** A rotating-analyser series is a rotating-analyser
series whether the analyser was turned by a stepper motor, by a graduate student's hand on a
Leitz stage in 2019, or by a forward model. `reefprint.polarim` never learns which.

## Decision

**REEFPRINT is a software system evaluated on public data. No hardware is purchased or built.**

Concretely:

1. `RotationSeries` is the acquisition boundary. Everything upstream of it is pluggable: a
   synthetic phantom, a replay of a stored public rotation series, or — if a rig ever exists —
   a driver. Nothing downstream may ask which.
2. The instrument becomes a **costed design with a bill of materials**, presented as a design, not
   as a built thing. The BOM is defensible engineering work and should be shown. It must never be
   photographed, described, or implied to exist.
3. Evaluation runs on public datasets only, which was already a hard constraint for a different
   reason (no proprietary Mintek data). The two constraints now point the same way.

## Consequences

### What this costs, stated plainly

- **The week-1 gate's "on screen" half is met on a phantom, not on a specimen.** A phantom proves
  the inversion is correct; it proves nothing about minerals. Reported as such in
  `experiments/001-week1-gate/README.md`, which says so in its own *What this does not show*.
- **No claim about µm/pixel, exposure, LED spectral response, polariser extinction ratio, or
  achievable R% accuracy may be made from measurement.** All of those were to be established on
  the rig. Any number of that kind is now either a published figure with a citation or an
  assumption flagged as one (Rule 1). CLAUDE.md's "0.2–1.6 µm/pixel" is a *design target* and is
  now labelled as one.
- **The week-4 degraded-input gate loses its most honest source of degradation.** Real defocus,
  real polish damage, real stage slip. Synthetic corruption is a weaker test and must be
  described as weaker.
- **A judge may reasonably ask "so you didn't build it".** The answer is that the discriminating
  measurement was implemented and tested against public reflected-light data, and that the
  instrument design is costed and specified — not that a rig exists.

### What this buys

- **Six weeks of build-and-calibrate risk is gone**, including the two failure modes with no
  recovery path inside the schedule: a stage that will not hold sub-micron position, and polished
  sections that never reach a usable finish.
- **The evaluation harness can be frozen this week**, which is what the submitted abstract already
  committed to and which the original gate order did not actually deliver.
- **Reproducibility improves.** Public data plus permissive code is checkable by a third party.
  A one-off rig in a Johannesburg flat is not.
- **The offline demo (week 5) gets easier, not harder** — no device to fail on stage.

### What does not change

The falsification test, locality splits, conservative-default abstention, the SBOM and the backup
video are all on the never-cut list and none of them depended on the rig.

## Alternatives rejected

| Option | Why not |
|---|---|
| Buy a reduced rig (polarisers + a webcam, no stage) | Still money, still build time, and it produces data of unknown quality that would be presented as measurement. Worse than a phantom, because it looks like evidence. |
| Borrow Wits microscope time | Would be genuinely better data. Not rejected on merit — rejected as a *dependency*: it is not under the team's control on a six-week clock, and gauntlet **S5** notes that university facilities re-open the IP question that "no facilities" currently closes. Pursue it as upside, never as a plan. |
| Simulate the instrument in full (optical model, sensor model) | Elaborate, and a simulator's agreement with itself is not evidence. The phantom is deliberately minimal for the same reason. |
| Drop polarimetry, do reflectance-only on public images | This is the v1 that already died. Chromite has no absorption features; reflectance alone is a brightness meter on chromitite. |

## What would change this

Someone donating microscope access with a rotating stage, under terms that do not create an IP
claim. That would upgrade the second leg of the week-1 gate from stored public rotations to
captured ones — it would not change the architecture, because `RotationSeries` was designed for
exactly that substitution.
