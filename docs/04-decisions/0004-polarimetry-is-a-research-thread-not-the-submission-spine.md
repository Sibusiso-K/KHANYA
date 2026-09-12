# ADR-0004 — Polarimetry is a research thread, not the submission's spine

- **Date:** 2026-09-12
- **Status:** Accepted
- **Decider:** Lethabo Hoaeane (single technical decision-maker, CLAUDE.md)
- **Relates to:** ADR-0003 (two names, two histories) · `WORKBOARD.md` §0 C1 and §4 D1 ·
  `docs/BUILDLOG.md` sessions 17 and 18 · `khanya/main:reports/TECHNICAL-REVIEW-2026-09-12.md` ·
  CLAUDE.md §Weekly gates

## Context

Nineteen days before the final, two analyses arrived at the same conclusion from different
directions.

**First, the registration finding (session 17).** LumenStone S3 v2's rotation frames are not
registered: the field rotates with the specimen, so a given pixel is a different physical point in
every frame. Frame-to-frame correlation against `r000` decays along the *rotated-image control*
curve — `S3_test_01`: r005 **+0.7114** against a 5° control of **+0.6572**, r040 **+0.3129**
against a 45° control of **+0.2929** — where a registered polarimetric series stays high and flat.
Every per-pixel result computed on that archive therefore measured nothing, including all three
independent `NEITHER` verdicts and the full-codebook extinction run. The answer was reproducible
because the *bug* was reproducible; agreement across two machines tested determinism, not validity.

**Leg (b) of the week-1 gate has consequently never been run.** Whether a fourth-harmonic signal
survives proper registration is open and untested. Naive centred de-rotation does not repair it —
it helps dramatically on `S3_test_03` r005 (+0.3137 → +0.8142) and hurts on `S3_test_01` — so the
rotation centre is off-image-centre and varies by section. Closing it needs a per-frame transform
estimated from the data (log-polar phase correlation, or ECC), then restriction to the inscribed
region present at every angle, then the mask mapped through the same transform. That is a research
task of unbounded duration with no fallback if the answer is negative.

**Second, the external adversarial review.** Its verdict:

> *"The current positioning loses against a team that delivers the literal brief cleanly … Keep the
> existing segmentation pipeline; demonstrate chalcopyrite, pentlandite and pyrrhotite; connect its
> output through a real local OPC UA interface to an explicitly simulated circuit; and make one
> modest processability proxy auditable. Move polarimetry off the critical path."*

Against the brief's literal deliverables, three are unbuilt and all three are on the non-polarimetry
side: no processability head exists, no OPC UA server exists, and no latency benchmark exists
anywhere. The brief asks for ≥3 mineral phases, an accuracy report, a demonstration of plant-parameter
adjustment, real-time operation, and integration with sorting or flotation controls. **Polarimetry is
not named in any of them.**

A third consideration, found the same day and recorded as ADR-0005: the written specification of the
illumination path does not match what the polarimetry code implements. That is a cheap fix, but it
is evidence that the polarimetric claim is less settled than its test count suggests.

## Decision

**The submission's spine is segmentation → processability → plant interface, demonstrated offline
with a visible refusal. Polarimetry is presented as the measurement research component, honestly
labelled as validated on a synthetic phantom and not yet on real ore.**

The work queue is therefore, in order, with each item's acceptance test named in `WORKBOARD.md` §3:

| | Item | Acceptance test |
|---|---|---|
| **P1** | OPC UA advisory server and separate simulated control client | `tests/test_integrate.py::test_opc_ua_server_exposes_advisory_values` |
| **P2** | One processability head — fine-chromite entrainment risk | `tests/test_heads.py::test_fine_chromite_entrainment_risk_index` |
| **P3** | Latency benchmark on the shipped path, on named hardware | to be written |
| **P4** | Accuracy report with locality grouping, CIs and both baselines | `tests/test_heads_falsification.py::test_the_falsification_test_has_been_run_on_real_bushveld_data` |
| **P5** | Leg (b) registration | `tests/test_acquire.py::test_the_week_1_gate_runs_on_a_public_reflected_light_rotation_series` |

**P5 runs only if P1 through P4 are green.**

## What this decision does NOT do

- **It does not withdraw the polarimetric claim.** The Stokes inversion, the geometry
  discriminator, the fourth-harmonic estimator and the bridge remain built, tested and shipped.
  Nothing is deleted, and `reefprint.polarim` stays in the package.
- **It does not delete the phantom result.** Leg (a)'s 40.4× separation stands as what it always
  was: proof that the inversion recovers the parameters it was given. Per CLAUDE.md's trap 5 and
  ADR-0005, it is never presented as a result about real ore.
- **It does not concede that polarimetry failed.** Leg (b) has not been run. The honest statement
  is *untested*, not *negative*, and the distinction must be preserved in the talk.
- **It does not change the kill list.** Nothing on CLAUDE.md's *never cut* line moves: the
  falsification test, locality splits, conservative-default abstention, the SBOM and the backup
  video all stay.

## Consequences

**The talk gains a beat rather than losing one.** The old explanation of the S3 v2 result was a
null that turned out to be invalid. The replacement is stronger and true: *our trust layer refused
a public archive; we investigated why and found the frames aren't registered — a pixel is a
different grain in each frame.* That is a demonstration of the refusal machinery working on real
data, which is worth more than a null.

**A sharp reviewer's question now has an answer.** "How do you know those frames are registered?"
was previously unanswerable. It is now *"they are not, and we found that ourselves."*

**Two documents must be corrected before they reach a judge.** `ENDGAME.md` §3's framing table
cites the invalid extinction null as an asset, and the talk storyboard describes S3 v2 as a stage
rotation. Both live on `main`; per ADR-0003 they are Sibusiso's to fix and are not edited across
branches.

**Week 1's gate is reported as split, not passed.** Leg (a) passed on the phantom; leg (b) is
outstanding and untested. CLAUDE.md's gate table already says exactly this and does not change.

## Alternatives rejected

**Polarimetry stays the spine, registration becomes P1.** Rejected: it bets nineteen days on an
untested question with no fallback, and leaves two explicit brief deliverables unbuilt. If
registration succeeds and the 4φ signal is absent, there is no time left to build the plant
interface.

**Run P1 and P5 in parallel.** Rejected: one person works this branch. At T-19 parallel means both
land half-done, and the submission drill exists precisely to prevent that.
