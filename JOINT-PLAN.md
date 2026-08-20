# KHANYA + REEFPRINT — the joint plan

Written 2026-08-19 after reading Lethabo's REEFPRINT repo end to end. Read
alongside `PITCH.md` (positioning) and `STATUS.md` (KHANYA's current state).

**43 days to final. The submitted abstract is REEFPRINT's. The working
end-to-end code is KHANYA's. That gap is the thing to close, and it closes
better than either of us would have guessed.**

---

## 1. The convergence — this is the actual finding

Lethabo's core claim: **pentlandite is cubic, so it stays dark through a full
analyser rotation; pyrrhotite is anisotropic, so it lights up.** Phantom-validated
at 40.4x separation.

KHANYA's largest mineral-to-mineral error, measured on held-out data:
**pentlandite is predicted as pyrrhotite 29.2% of the time** (against 54.2%
correct). It is the worst confusion in the entire matrix, and I diagnosed it as
exsolution intergrowth — pentlandite exsolves as flames *inside* pyrrhotite, and
in unpolarised reflected light the two are similar bronze-cream colours.

**Lethabo's physics is the discriminator for exactly the pair my model cannot
separate.** Neither of us designed for this; we arrived at the same mineral pair
from opposite ends — his from PGE deportment first principles, mine from a
confusion matrix. That convergence is worth more in a pitch than either half
alone, and it is *evidence*, not narrative.

A second, quieter fit: KHANYA's robustness sweep found the model is effectively a
**colorimeter** — a 15% white-balance shift costs 0.39 mean IoU (72% of
performance), while blur and noise cost nothing. REEFPRINT's `calibrate/` module
(reflectance standards, R% conversion, QDF lookup) is precisely the fix, and it
is on his roadmap already. **I measured the disease; he specced the cure.**

## 2. What each side already has

| REEFPRINT module | State there | KHANYA equivalent | State here |
|---|---|---|---|
| `polarim/` | **Built**, phantom-passed 40.4x | — | nothing |
| `calibrate/` | not built | — | nothing (but the *need* is measured) |
| `segment/` | not built | DeepLabv3+ResNet50 | **built**, mIoU 0.5725 held-out |
| `texture/` | not built | watershed topology repair + particle composition | **built**, correlation 0.947 |
| `trust/` (conformal, abstention) | not built | conformal band, severity classes | **built**, 0 unsafe errors |
| `heads/` | not built | role-based advisor | **built** |
| `viz/` | partial | offline Streamlit dashboard | **built**, zero network calls |
| `integrate/` | not built | — | nothing |
| `acquire/` | half built | LumenStone loader, subset switch | **built** for S1/S2/S3 |

**Eight of REEFPRINT's nine modules are unbuilt. KHANYA has working, held-out-
validated code for five of them.** Conversely, REEFPRINT has the one thing KHANYA
cannot get from better modelling: a *physical* discriminator, plus the
calibration story that fixes KHANYA's worst deployment risk.

These are two halves of one system, not two competing entries.

## 3. The single highest-value experiment

> **Take KHANYA's measured 29.2% pentlandite -> pyrrhotite confusion, apply
> REEFPRINT's Stokes anisotropy to the same sections, and measure whether it
> drops.**

If it drops, that one number is the entire joint thesis on one slide: *a
segmentation model trained on colour cannot separate these two minerals; the
physics can; here is the before and after on held-out data.* It uses both
codebases, it is falsifiable, and it is exactly the kind of result that survives
originality authentication because neither half could have faked it alone.

If it does **not** drop, that is still publishable and still ours — it would say
the intergrowth is finer than the optical resolution, which is a real finding
about the limits of the method and a much better answer than silence.

### The unlock: LumenStone S3 v2

REEFPRINT's week-1 leg (b) needs a real rotation series. KHANYA already
downloaded S3 **v1** (273 MB) and *deliberately ruled out v2* — 5.2 GB, and the
extra bulk is **XPL rotations of the same sections**, which for segmentation are
near-duplicates that leak across train/test (the exact failure that made our
MUMDMC numbers worthless).

**For polarimetry those same rotations are not leakage — they are the
measurement.** Same file, opposite verdict, for a defensible reason on each side.
S3 v2 is the dataset that closes Lethabo's week-1 gate, and S3 contains
magnetite *and* hematite together, which also tests KHANYA's optical-argument
claim. Download it.

---

## 3a. CORRECTION (2026-08-19, same day): the experiment in section 3 cannot be run

Section 3 above proposed testing whether Stokes anisotropy fixes KHANYA's 29.2%
pentlandite -> pyrrhotite confusion. **That experiment is impossible with the
available data, and the error is mine.**

Pentlandite and pyrrhotite are in **S2**, which has no rotation series.
The XPL rotations are in **S3**, which contains neither mineral. The pair and
the measurement live in different datasets. Verified against
`SUBSET_CODES` before any code was written.

### The replacement is stronger, not a consolation

S3's eleven classes split cleanly by crystal symmetry - five isotropic (cubic:
pyrite, galena, sphalerite, magnetite, tennantite) against five anisotropic
(covellite, arsenopyrite, hematite, chalcopyrite, bornite). That is a
ten-mineral test of the general principle rather than a single pair.

And it contains the pair that matters most to us: **magnetite (cubic,
isotropic) against hematite (trigonal, anisotropic)**. That is precisely the
pair report section 3 names as the thing SEM/BSE cannot separate and optical
can - a claim currently *asserted* in our report and never measured. It is also
KHANYA's total failure case: magnetite scores IoU 0.000 on S2 and is predicted
as background 92.3% of the time. If anisotropy splits magnetite from hematite,
it is doing work that no amount of colour-based training achieved.

The joint thesis is unchanged. Only the mineral pair changed, and it changed
toward the pair our own report already stakes its optical argument on.

## 3b. RESULT: REEFPRINT's open finding N2 is now closed

`src/polarimetry.py --n2`. N2 held that no fixed anisotropy threshold is
defensible because the noise floor scales as 1/S0, so a rule fitted on bright
sulphides lights up every dark grain. Measured, using N2's own stated numbers
(sigma = 0.25 R%, n = 36 angles):

| Population | Median anisotropy | Fixed-threshold FP rate | S0-conditioned FP rate |
|---|---|---|---|
| isotropic, bright (R=50%) | 0.0014 | 10.0% | 9.9% |
| isotropic, **dark** (R=4.75%) | 0.0146 | **98.1%** | **9.9%** |
| anisotropic (R=20%, m=0.08) | 0.0801 | 100% (detection) | 100% (detection) |

**A fixed threshold flags 98% of dark isotropic pixels as anisotropic.** The
S0-conditioned conformal bound holds at 10% in every bin by construction, and
loses nothing in detection sensitivity - genuinely anisotropic pixels are still
caught 100% of the time.

The 1/S0 law itself is confirmed in passing: bright and dark isotropic
populations sit at 0.0014 and 0.0146, a ratio of **10.4x**, against an S0 ratio
of 50/4.75 = **10.5x**. The noise floor scales as predicted.

**This is KHANYA's conformal machinery (`src/conformal.py`) applied to
REEFPRINT's physics**, and it is the clearest demonstration so far that the two
halves are worth more joined than separate: Lethabo identified the failure mode
and had it open as a blocking finding; the fix was already built on this side.

## 4. Plan, phased

### Phase 1 — before 30 Aug (abstract)

**Do not merge code yet.** The abstract needs one coherent story, not a
refactor.

1. **Agree the joint narrative.** Proposal: REEFPRINT is the thesis (physics
   that resolves a confusion colour cannot), KHANYA is the evidence chain that
   proves the confusion exists and the harness that turns a mask into a plant
   decision. One system, two measurement axes.
2. **Reconcile the phase set.** The submitted abstract commits to five Bushveld
   phases (chromite, orthopyroxene, plagioclase, BMS, talc/serpentine).
   **Neither repo has chromite data, and none is public** — KHANYA searched and
   documented it in `DATA-SOURCES.md`. The abstract must not imply UG2 grade
   estimation. Say assemblage analogue, name the gap.
3. **One mentor request, not two** — the QEMSCAN-labelling ask in
   `MINTEK-FIT.md` §3.4 serves both halves and is the highest-leverage thing
   either of us can send.

### Phase 2 — September, the bridge

4. Download S3 v2; build the OME-TIFF reader (Lethabo's named next action).
5. Run KHANYA's segmentation on S3 to get pentlandite/pyrrhotite masks.
6. Run REEFPRINT's Stokes inversion on the same sections' XPL rotations.
7. **Measure the confusion before and after.** This is item 3 above and the
   whole point.

### Phase 3 — late September, integrate only what the demo needs

8. Wire KHANYA's `trust/` equivalent (conformal + abstention) behind REEFPRINT's
   anisotropy output. This directly answers Lethabo's open finding **N2** — that
   no fixed anisotropy threshold is defensible because the noise floor scales as
   1/S0. Our conformal machinery already conditions on measured error and
   reports an interval instead of a threshold. **N2 is not an open problem for
   us; it is a solved one waiting to be connected.**
9. Freeze 29 Sep. Rehearse offline.

## 5. Risks, named

- **Merging two architectures in 43 days is itself the biggest risk.** Do not
  rewrite KHANYA into REEFPRINT's package layout, and do not port REEFPRINT into
  KHANYA's. Bridge them with a thin interface at the mask/series boundary and
  leave both repos intact. A refactor that eats September loses the competition
  regardless of how clean it is.
- **Two commit histories, one submission.** Finalists face originality
  authentication. Decide now how both repos are presented — the honest framing is
  two workstreams by two people that converged, which is *stronger* than one
  history, provided it is stated up front rather than discovered.
- **REEFPRINT's CONTEXT.md flags a commit-email mismatch** (UNISA on commits,
  Wits in docs). Same class of problem. Fix before 2 October.
- **REEFPRINT's abstract contradicts its own Rule 5** on abstention (holds
  last-known-good setpoint vs. that being the worst action at an ore transition).
  Lethabo already knows and has the right framing: *we tested our own abstention
  policy, found it failed exactly when it mattered, and changed it.* KHANYA's
  advisor already emits a conservative default with a stated reason rather than
  holding — the two are consistent once connected.
- **Both repos independently discovered the LumenStone licence is informal.**
  Duplicated effort. One email, one owner.

## 6. What I would say to Lethabo first

The pentlandite/pyrrhotite convergence, before anything else. He built a physical
discriminator for a mineral pair; I have a measured, held-out confusion matrix
showing that exact pair is where my model fails hardest. Neither of us knew the
other's number. That is the pitch, and everything in this document is downstream
of it.
