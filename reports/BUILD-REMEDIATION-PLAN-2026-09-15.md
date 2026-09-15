# Build remediation plan - PROPOSED, not decided

**Date:** 15 September 2026
**Status:** **Proposal. Not accepted by either branch owner.** Published
specifically so it can be attacked before anyone builds from it.
**Companion to:** `ADVERSARIAL-CRITIQUE-2026-09-15.md`, which says what is
wrong. This says what to do about it, and where it might itself be wrong.

Effort figures are **planning estimates, not measurements**, following the same
convention as the 12 September technical review.

---

## How to attack this document

Every item below carries a **kill criterion**: the specific thing that would
mean "do not do this". If you disagree with an item, the useful response is
either to trigger its kill criterion with evidence, or to argue the priority
order is wrong. Section 4 lists the assumptions this plan rests on that have
**not** been verified, which is where it is most likely to be wrong.

Sixteen days remain. Feature freeze is 25 September. That is nine working days
for everything below, and the plan deliberately proposes less work than that
window, because rehearsal and the backup video are not in this document and
must not be squeezed.

---

## 1. The plan, in priority order

### P1. Input eligibility gate

**Addresses:** the critique's most dangerous live-demo failure. Today, any
image at all gets confidently segmented. A judge who supplies their own photo
gets a confident plant recommendation about it. There is currently no gate and
no rehearsed answer.

**What:** fit simple statistics over the 37 training images - colour
distribution, predicted class-composition profile, mean softmax confidence -
and refuse inputs falling outside. **Label it exactly what it is: an input
eligibility heuristic, not a validated out-of-domain detector.** The wording
matters; the project has already corrected one OOD overclaim (`BACKUP-DEMO-
SCRIPT.md`, entry 58).

**Why it is worth more than it costs:** it converts the worst Q&A moment into
the strongest one. An unplanned input being refused in front of judges is the
refusal thesis working on a case the team did not choose.

**Acceptance test:** a non-micrograph image (photograph of anything) is refused
with a stated cause. A real held-out S2 test image is not refused. Both
verified in the running app, not only in unit tests.

**Effort:** ~1 day.

**Kill criterion:** if the heuristic cannot separate a real micrograph from an
arbitrary photo without also refusing legitimate S2 test images, ship nothing
and instead rehearse a spoken answer ("we have no domain gate; this is what we
would build and why"). A gate that refuses valid inputs is worse than none.

### P2. Settle whether magnetite fails on rarity or on contrast

**Addresses:** critique finding 1.1, the sharpest single attack available:
*the model scores 0.000 at 1.84% abundance, and UG2's payload is under 1%.*

That attack assumes the failure mode is **rarity**. `STATUS.md` already argues
it is **reflectance contrast** - magnetite is dark grey, optically closer to the
mounting resin than to the bright sulphides. If that is demonstrably the cause,
the attack largely collapses.

**What:** check the existing S1 per-class results
(`reports/lumenstone_s1_patches_test_metrics.json`, 20 test images, mean IoU
0.7116) against S1 class pixel shares. **If S1 contains a rare but optically
bright phase that the model detects well, that is direct evidence that rarity
is not the failure mode.**

**Effort:** ~1 hour, no retraining, no new data.

**Kill criterion:** if S1 has no rare-but-bright class, or if its rare classes
also fail, the contrast hypothesis is unsupported and **must not be claimed**.
In that case the honest position is the current one: a measured failure with an
unproven cause.

**Do not** attempt to fix magnetite by retraining. Three approaches have
already failed (resize+CE, patches+CE, patches+CE+Dice) and a new checkpoint
invalidates every number in the pitch, the backup script, the conformal band
and the baselines, nine days before freeze.

### P3. Preflight check

**Addresses:** three distinct environment failures in seven days (tile-progress
crash, `asyncua` venv desync showing "OPC UA UNAVAILABLE", flaky mode switching).
All three would have been fatal on stage. All three are detectable in seconds.

**What:** one command that verifies and prints green/red: checkpoint present and
hash-matching; `asyncua` importable **in the venv the demo actually runs
under**; model loads; OPC UA round trip completes; the three demo images
produce their expected documented numbers.

**Acceptance test:** deliberately break each condition in turn and confirm the
check catches it.

**Effort:** ~0.5 day.

**Kill criterion:** none. This is insurance, and the failure history justifies
it on its own.

### P4. Separate the decision-gap confound before it reaches a slide

**Addresses:** critique finding 2.2. Topology repair modifies ground truth as
well as predictions (`STATUS.md`: "the refinement changes ground-truth
liberation too, sometimes a lot"). The decision-gap comparison may therefore be
measuring the refinement rather than the model.

**What:** run the decision gap with refinement disabled on both sides, and with
it enabled, and report both.

**Effort:** a few hours, no retraining.

**Kill criterion:** this one has no kill criterion either, but it has a real
downside risk: **the result may weaken or destroy the project's most
interesting finding.** That is the point. Better to learn it now than under
questioning.

### P5. Cheap credibility and robustness

- **Warm the model at application start**, not on first upload. The 4.7s Live
  Field figure is *warm*; cold is roughly 30s. A sleeping laptop turns the
  five-second beat into a thirty-five-second one.
- **Per-phase confidence** in the modal mineralogy panel, not one aggregate
  number.
- **Bootstrap intervals** on the headline metrics across the 12 sections.
  Directly answers "what is your n?" and costs almost nothing.

**Effort:** ~1 day for all three.

**Kill criterion:** drop any of these the moment they collide with rehearsal
time.

---

## 2. Explicitly not doing

- **No new demo features.** Four surfaces already exist (Live Field, Full
  Section with tile animation, Evidence, OPC UA). Each is failure surface.
- **No retraining.** See P2.
- **No ONNX or INT8 work.** `JUDGE-READY-WORKPLAN.md` already lists it first
  for cutting.
- **No further polarimetry.** Off the critical path (ADR-0004); the registration
  search was found non-deterministic on real data.
- **No refactoring.** Nine working days to freeze.

---

## 3. What this plan does not cover, and must not crowd out

Rehearsal (three full timed run-throughs), the backup video recording, hostile
Q&A practice, and the human and external items in `HANDOVER.md` entry 60 and the
critique's sections 3 and 4. **Those outrank everything in section 1.** If the
build work threatens them, the build work loses.

---

## 4. Assumptions this plan makes that have NOT been verified

This is where the plan is most likely to be wrong, and where critique is most
useful.

1. **P2 assumes S1 contains a rare but optically bright class.** This has not
   been checked. The per-class S1 numbers exist in the repository; nobody has
   read them against the class pixel shares. If the assumption is false, P2
   produces nothing and its hour is wasted (acceptably).
2. **P1 assumes simple colour and composition statistics can separate a
   micrograph from an arbitrary photograph.** Plausible, untested. It may
   require more than colour statistics, which would push it past one day.
3. **P1 also assumes the gate will not refuse legitimate S2 inputs.** With 37
   training images defining "in domain", the distribution estimate is thin.
4. **P3 assumes the demo laptop is this machine or a faithful copy of it.** If
   the presentation runs on different hardware, the preflight check is still
   useful but its expected-value assertions need re-baselining there.
5. **The whole plan assumes the current checkpoint is frozen.** If anyone
   retrains, most numbers in the pitch, the backup script and the baselines
   require re-verification, and this plan's effort estimates are void.

---

## 5. Open questions the plan cannot resolve

- Is the magnetite result better presented as a **failure** or as a **measured
  optical limit of the modality**? The second is stronger and may be true, but
  P2 has to support it first.
- Should the pitch lead with the decision-gap finding at all? P4 answers this,
  and an earlier recommendation to lead with it has already been retracted
  (critique section 7).
- Does the input eligibility gate belong in the live demo, or is a spoken
  acknowledgement of its absence more honest? P1's kill criterion decides.
