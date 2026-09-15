# The advice changes when only the light changes

**Date:** 15 September 2026
**Evidence:** `reports/v1_consistency.json` (`python -m src.v1_consistency`,
run under `KHANYA_SUBSET=S1`) and `reports/exposure_control_s2.json`
(`python -m src.exposure_control`).
**Supersedes:** `V1-ROBUSTNESS-PLAN-2026-09-15.md`, which proposed this
experiment. Its design survived; one of its assumptions did not.

---

## 1. The result

Two independent in-domain experiments, one on real optical variation and one on
a synthetic control, agree:

| | n | mean mask IoU, same field twice | recommendation changed |
|---|---|---|---|
| **V1, real re-imaging** (S1 checkpoint) | 10 | **0.3213** | **5/10** |
| **S2 held-out, synthetic -35 RGB** | 12 | **0.4597** | **8/12** |

Nothing about the rock changed in either case. In the first, the same polished
section was photographed twice under different real conditions. In the second,
the same file was darkened by the exposure difference actually measured between
those V1 pairs. **On between half and two thirds of sections, the plant
recommendation changed.**

Individual cases are worse than the averages. V1 sample 005: liberation
**0.941 to 0.001**. V1 sample 004: **0.893 to 0.704**, a 36 percentage point
swing in reported phase composition. S2 `test_05`: **0.941 to unmeasurable**.

## 2. Why this is not the fragility we already knew about

`src/robustness.py` has measured photometric sensitivity for weeks. What it
measures is IoU against ground truth under perturbation - an accuracy question.
This measures whether **the same section gives the same instruction twice**,
which is the question a plant actually cares about, and it is answered against
the decision layer rather than against a pixel metric.

It also lands on the project's own thesis. The system is built to refuse when it
cannot tell. It does not currently refuse here: it changes its mind, confidently,
because someone adjusted the illumination.

## 3. The mistake made getting here, recorded because it nearly shipped

The first run of `v1_consistency` used the **S2** checkpoint and reported
**8/10** recommendation changes with 35.23 pp mean phase drift. That number is
an artefact and is retracted.

The dataset page states plainly: *"V1: A specialized dataset featuring **the
same samples as for S1** imaged under varying conditions."* S1 is Berezovskoe
hydrothermal ore; S2 is Norilsk. Running the S2 checkpoint on V1 is the
cross-dataset out-of-domain case `BACKUP-DEMO-SCRIPT.md` already uses as its
refusal beat - it measures domain mismatch, not illumination sensitivity.

Re-run with the S1 checkpoint, the effect is smaller (5/10, 16.08 pp) and real.
**The confound was inflating the result by roughly a factor of two.** This is
logged rather than quietly corrected because the dramatic number was the first
one produced, and a dramatic first number is exactly when this project is
supposed to look for the bug.

## 4. What was verified rather than assumed

- **Registration.** V1 ships three files per sample. `NNN` and `NNNb` are
  3396x2547 and pixel-registered: normalised cross-correlation **0.99 at zero
  shift on all ten samples**. `NNNa` is 4272x2848, a different camera, and peaks
  at **0.27** against the base image over a full scale-and-offset sweep - it does
  not image the same field and is **excluded**. Ten valid pairs, not fifteen.
  This check exists because the S3 rotation series was assumed registered and
  was not, invalidating every per-pixel measurement taken on it.
- **The archive.** 104,705,467 bytes, sha256 `499c625a...`, byte-identical to
  REEFPRINT's independently obtained copy.
- **The exposure difference is real, not trivial.** V1 `b` images are ~35 RGB
  points darker than their base across all three channels, measured on the exact
  centre crop that was scored. The control uses that measured magnitude.

## 5. Limits, stated before anyone quotes this

- **n = 10 and n = 12.** A fragility probe, not a robustness guarantee.
- **Centre 512 crop, not full sections.** The full sliding-window path may
  behave differently; `--full` exists and has not been run.
- **V1 carries no masks.** "Unstable" is not "wrong" - the model could be
  consistently wrong and appear stable. The S2 control is labelled and in-domain
  and is what makes the finding safe to state.
- **The control's shift is synthetic.** Its magnitude is measured, its form
  (uniform RGB offset) is not what a different microscope actually does.

## 6. What follows

1. **This belongs in the pitch, not buried.** It is the strongest available
   evidence for the project's central claim that mineralogical advice needs an
   abstention mechanism, and we found it against ourselves.
2. **The refusal layer does not currently cover it.** The advisor refuses on low
   payload and hedges near the liberation threshold. It has no notion of "this
   field was imaged under conditions I cannot vouch for". Whether that is
   buildable before 25 September is a separate question from whether it should
   be disclosed - it should.
3. **Do not fix this by retraining.** Feature freeze is 25 September and every
   headline number depends on the current checkpoints.
