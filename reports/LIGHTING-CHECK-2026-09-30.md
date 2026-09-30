# Simulated lighting-perturbation check: an input-sensitivity diagnostic

**Date:** 30 September 2026 (wording revised after Lethabo's PR #11 review)
**Evidence:** `reports/lighting_check_trainval.json`
(`python -m src.lighting_check_validation`). The 12 held-out test sections were
**not used**.
**Code:** `src/stability.py`

> **Read these costs before any safety claim.** On sections the test set never
> touched, this check **discarded 4 of 5 correct confident recommendations**
> while catching 5 of 8 wrong ones. It **does not improve phase
> identification**. It **doubles the analysis time**: two live passes took
> 71-74 s end to end on this CPU when first measured (49 s after the PR #13
> speed-ups). It is one fixed, synthetic perturbation.

---

## What it does

The live six-field pipeline runs twice: once on the image as captured, and once
on a **copy of the same image with a fixed per-channel RGB offset subtracted**.
That is a simulated lighting perturbation, **not a second capture**. If a
confident recommendation changes between the two, no instruction is issued and
the simulated plant holds.

The offset is the **per-channel median of the real darkening** measured across
all ten registered LumenStone V1 pairs: R -34.8, G -32.5, B -29.6. Real
re-imaging darkened images by 25-37 levels per pair, and more in red than in
blue. There is no tuned threshold; the rule is that the action must not change.

## What it found, on sections the test set never touched

| | Unseen validation (n=6) | Training, seen by the model (n=31) | Together (n=37) |
|---|---:|---:|---:|
| Advice changed under the perturbation (any kind) | — | — | **24 of 37** |
| Confident advice before the check | 4 | 9 | 13 |
| ... of which unsafe against the expert reference | 3 | 5 | **8** |
| Unsafe after the check | 1 | 2 | **3** |
| Unsafe advice caught | 2 of 3 | 3 of 5 | 5 of 8 (63%) |
| **Correct** confident advice thrown away | 1 of 1 | 3 of 4 | **4 of 5 (80%)** |

The reference is the advisor run on the expert-annotated whole section, the
same reference policy `src/decision_gap.py` uses. It measures consistency with
expert labels, not plant truth.

## What that means, stated plainly

1. **The advice is sensitive to brightness far more often than not.** On 24 of
   37 sections, subtracting an offset the size of the darkening seen in real
   re-imaging changes what the system recommends.
2. **The check cuts unsafe advice from 8 to 3.**
3. **It does not tell good advice from bad.** It discarded correct confident
   advice more often (80%) than incorrect (63%), and 3 of the 4 confident calls
   that survive it are still unsafe. **It must not be presented as "the system
   catches its own mistakes".** It does not.
4. **What the evidence supports is a recommendation-stability check, nothing
   more.** It asks one question: does this recommendation survive one fixed,
   plausible brightness change? Most confident calls here do not, and the check
   withholds them, including some that would have been correct. It is not a
   measurement-system (gauge R&R) study: that would need repeated real captures
   across operators, instruments and conditions. An earlier version of this
   report used that comparison; it overreached and is withdrawn (Lethabo, PR #11
   review).
5. **The real fix is upstream.** Standardise illumination, or calibrate against
   a physical reflectance standard every session. REEFPRINT's calibration module
   exists but is not a drop-in (Lethabo, PR #7): the model was trained on
   uncalibrated RGB.

## A second finding this exposed

Against the expert-annotated whole section, the six-field pipeline's confident
calls were unsafe **8 of 13 times** on these 37 sections. On the 12 test
sections they agreed **3 of 3** (`reports/field_sampling_s2.json`). Both samples
are small. But it is consistent with the ±0.335 band, calibrated on **whole
sections**, being too narrow for the noisier six-field estimate, so six fields
reach confident calls the whole section would not. This bears on PR #10 and is
flagged there.

## Limits

- n=6 unseen validation sections. The 31 training sections were seen by the
  model, so its behaviour there is optimistic.
- One perturbation (a uniform per-channel offset). A different microscope also
  changes focus, glare and colour response.
- The live path costs a second pass over the same fields.
