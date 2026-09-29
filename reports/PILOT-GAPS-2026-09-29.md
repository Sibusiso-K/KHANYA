# From demo to pilot: the five things we do not yet prove

**Date:** 29 September 2026
**Status:** for discussion with Lethabo (PR). Proposal, not a decision.
**Builds on:** `handover/PILOT-AND-BUSINESS.md` on `codex/khanya-build-plan`,
whose stage table puts a **laboratory shadow pilot** directly after the
hackathon workstation: "site specimens and expert labels; repeatability;
measured report turnaround; no process commands". This document asks what it
takes to get there, gap by gap.

As of `ced0ca8` all three literal deliverables can be demonstrated: three
phases identified on held-out data (reproduced 29 September, sha256
`de7135a9`), accuracy evidence in `reports/`, and a simulated plant parameter
driven over real OPC UA. The team wants more than a demo: a solution that is
one credible step from a pilot. These are the gaps between the two.

## Decisions agreed, 29 September (Lethabo's review of this PR)

| # | Decision |
|---|---|
| 1 | **On stage, claim only** that the research prototype identifies the labelled S2 phases with the reported held-out accuracy, and demonstrates a simulator-only advisory-to-parameter path. **Do not claim** reduced reagent use, higher recovery, or faster sample-to-answer. |
| 1 | **Shadow pilot measures:** specimen-level agreement with expert labels; coverage and abstention; unsafe-advisory count *with its denominator*; repeatability; paired sample-to-reviewed-result turnaround. Plant reagent and recovery records are for exploratory association only while no commands are sent. **8-12 weeks is a planning estimate** that depends on partner access, not a commitment. |
| 2 | **The pitch's primary ask:** a partner lab supplying representative labelled South African polished sections, with expert phase labels, specimen identity and acquisition metadata; holdout grouped by specimen. USGS imagery is a qualitative stability check only, and only if acquisition is comparable. No accuracy claims from it, and it must not delay submission. |
| 3 | **First customer:** a lab that already prepares and images suitable sections. We have not shown removal of an SEM/XRD queue or measured turnaround, and we do not remove preparation. No verified lab contact or turnaround figure exists. |
| 4 | **Decision-level reporting alongside IoU**, with the unsafe criterion defined and thresholds locked *before* evaluation. Zero unsafe in 12 is not a zero rate (see gap 4's correction). **Seed fix and J0/J1/J2 after the freeze**, train/validation only, never tuned on the 12 test sections. CE+Dice (0.5300 val) does not replace the stage checkpoint. |
| 5 | **Reflectance calibration is not ready** to sit in front of the current model (see gap 5). **For this submission, disclose the lighting fragility**; do not add an unvalidated gate. The consistency gate is a future experiment with predefined perturbations on V1 and train/validation images only. |

Still open: the five clause-plan questions in `CHALLENGE-CLAUSES-2026-09-29.md`,
added after this review.

---

## 1. No evidence it reduces chemical use or raises yield

**What we have.** One simulated Boolean (`regrind_enabled`) moved by the
advisory. No plant data of any kind. The only recovery figures in the evidence
register (E3, Mintek FloatStar: 0.51% Pb, 0.12% Zn) belong to a different system
at a different site and must not be borrowed.

**What a pilot needs.** Not a control loop. A **shadow run**: the tool reads
every section the site lab already images, logs its advisory and its hold or
refuse decisions, and sends no commands. Afterwards those logs are compared
with the lab's own results and the plant's reagent and recovery records for the
same shifts. The first measurable claims are decision-level, not savings:
how often the advisory agreed with the lab, how much earlier it arrived, and how
often it correctly held.

**Question for Lethabo.** What is the strongest *outcome* claim we can defend on
stage without plant data? Is "we define the shadow pilot and its metrics" enough,
or should the pitch commit to specific pilot KPIs and a duration?

## 2. The ore is Norilsk nickel-copper, not South African feed

**What we have.** LumenStone S2 (Norilsk, layered ultramafic) and S1 (Berezovskoe
hydrothermal). REEFPRINT holds real Bushveld chemistry (Bachmann, E7), but no
imagery; the two are not paired samples. USGS mafic/ultramafic thin sections
(E12, CC0) exist but carry no pixel masks.

**What a pilot needs.** Labelled polished sections from the target ore,
grouped by specimen so the holdout is honest, then fine-tuning and a fresh
evaluation. Norilsk and Bushveld/Platreef are both magmatic Ni-Cu-PGE sulphide
systems, so the three phases we detect are relevant. But relevance is not
performance, and nothing here measures performance on South African feed.

**Question for Lethabo.** Should the pitch's single ask be exactly this: a
partner lab supplying a small set of labelled South African sections? Could the
unlabelled USGS imagery serve before then as a domain-shift check (consistency,
not accuracy), the way we used V1?

## 3. Sections still need preparation, and we have not measured how long

**What we have.** Nothing measured. Earlier discussion said "hours"; that figure
is **unsourced** and must not reach a slide. Our 4.7 s is interpretation time
for one field, not sample-to-answer time.

**What a pilot needs.** A timed breakdown at a real lab: collection, transport,
mounting and polishing, imaging, analysis, sign-off. Then state plainly which
stages we shorten (queueing and analysis) and which we do not (preparation).
The plan's first customer is a lab that *already* prepares polished sections for
SEM. For them, preparation is already paid for, and what we remove is the wait
for the instrument.

**Question for Lethabo.** Do we pitch to that lab customer, where preparation is
a sunk cost, or to the plant, where it is not? And do either of us have a
contact who could give real turnaround numbers before the pitch?

## 4. Accuracy is moderate on two of the three phases

**What we have.** Chalcopyrite 0.5755 and pentlandite 0.5468 IoU, pyrrhotite
0.8695, on 12 held-out sections. The training recipe is **non-reproducible**:
`src/segmentation/patches.py:156` samples training patches with
`random.Random(None)`, and two runs of the same recipe landed 0.12 mIoU apart.
The budget (8 epochs x 64 patches) is small. Your CE+Dice validation run (0.5300)
has not yet beaten the existing checkpoint's validation (0.5384).

**What a pilot needs.** Seeded, reproducible training; the pre-registered
budget-scaling runs (J0/J1/J2, `docs/11` on `reefprint`); multiple seeds with the
spread reported; then site fine-tuning. The bar should arguably be
**decision-level, not IoU**. On S2 the refined pipeline had zero unsafe
advisories out of 12 (`reports/decision_gap_patches_refined.json`), even at
moderate IoU.

> **Corrected after Lethabo's review.** This paragraph first ended: *"For a
> screening advisory, 'never confidently wrong' may matter more than a few IoU
> points."* That overclaims. Zero unsafe advisories in 12 sections is an
> observation, not a rate: with 0 events in n=12, the exact one-sided 95% upper
> bound on the unsafe rate is **22.1%** (1 − 0.05^(1/12)). The honest statement
> is "0 of 12 observed; consistent with an unsafe rate of up to about 22%".
> "Never confidently wrong" must not be used.

**Question for Lethabo.** Do we agree that the pilot's accuracy bar is
decision-level (unsafe rate and coverage), with IoU reported alongside? And do
we fix the seeding and run J0/J1/J2 before or after submission?

## 5. Lighting fragility is disclosed, not gated

**What we have.** The advisory changed on 5/10 real V1 re-imaged pairs and 8/12
S2 sections under a measured exposure shift
(`reports/ILLUMINATION-STABILITY-2026-09-15.md`). The advisor has no refusal for
"imaged under conditions I cannot vouch for".

**What a pilot needs, in two layers:**
- **Fix it at acquisition.** Calibrate every session against a physical
  reflectance standard. REEFPRINT already has
  `reefprint.calibrate.reflectance` (`ReflectanceStandard`, `correct_counts`:
  camera counts to quantitative R%), which is how reflected-light mineralogy
  normally removes exposure and lamp drift. It needs a standard imaged each
  session, which LumenStone and V1 do not have. That makes it pilot work, not a
  demo feature.

  > **Not ready, per Lethabo's review.** The module outputs calibrated R%;
  > KHANYA's model was trained on RGB images with its own normalisation.
  > Putting calibration in front of it changes the model's input distribution,
  > so it needs paired calibrated training and evaluation before it can be
  > claimed. It is a pilot research item, not a drop-in fix.
- **Catch what calibration misses.** Run each field twice, original and one
  fixed perturbed copy, and hold if the advice flips. It needs no training, and
  its validation evidence must come from V1 pairs and train/validation images,
  never the 12 test sections.

**Question for Lethabo.** Is your reflectance calibration ready to sit in front
of KHANYA's model in a pilot, through the bridge, as `ensure_reefprint` already
does for OPC UA? Should the consistency gate go in before the freeze, or is
disclosing the fragility the more honest position for this submission?

---

## What this changes for 1 October

Nothing in this document should delay the deck, the backup video or the
rehearsal. The point is that the last slide can say precisely what the shadow
pilot would measure, what it needs from a partner, and which of these five gaps
it closes. That is the difference between "here is a demo" and "here is the
first stage of a deployable system".
