# KHANYA accuracy report

**Submission:** Team Sonar, Mintek-SCi Grad Hackathon 2026, Problem 3.
**Model under report:** S2 checkpoint, sha256
`de7135a96541a46dc0981a991cb954186c7cd669ea1c1b33914d1929ae9b1357`.
**Date:** 29 September 2026. Every number below traces to a file in `reports/`,
named in each section. Nothing here is a plant measurement.

---

## Summary

| | |
|---|---|
| **Deliverable** | A trained model identifying at least three distinct mineral phases: **met**. |
| **Three phases** | Pyrrhotite **0.8695**, chalcopyrite **0.5755**, pentlandite **0.5468** IoU on 12 held-out sections. |
| **Headline** | Mean IoU **0.5725** over five classes (95% bootstrap interval **0.494-0.624**), pixel accuracy 0.8914. |
| **Fails** | Magnetite, a fourth class the brief does not require: **0.0000**, never predicted. |
| **vs trivial baselines** | Majority class 0.1167; colour-only 0.3948; model 0.5725. |
| **vs published work** | On the exact published S1 protocol: 0.7224 against 0.8506 (void-border), a gap of **-0.1282**. |
| **Reproducible?** | The checkpoint reproduces bit-for-bit. The training recipe does not: a second run scored 0.4543. |
| **Not established** | Performance on South African ore; plant benefit; robustness to lighting; end-to-end speed. |

---

## 1. What was evaluated

| Item | Value |
|---|---|
| Architecture | torchvision `deeplabv3_resnet50`: **DeepLabV3, not DeepLabV3+**, ResNet-50 backbone |
| Initialisation | `DeepLabV3_ResNet50_Weights.COCO_WITH_VOC_LABELS_V1`, pinned explicitly |
| Classes | background, chalcopyrite, magnetite, pyrrhotite, pentlandite |
| Checkpoint | `checkpoints/lumenstone_s2_patches/best.pt`, 168,313,587 bytes, trained 16 August 2026 |
| Data | LumenStone S2 v2 (Norilsk layered ultramafic Ni-Cu), reflected light, 3396x2547 px. Archive sha256 `64aebd10...`, 418,742,024 bytes |
| Split | Publisher split: 37 train (31 train + 6 validation, seed 42), **12 held-out test** |
| Training | 8 epochs x 64 native-resolution 512 px patches, batch 2, AdamW 2e-4, cross-entropy. Best validation patch mIoU 0.5384 |
| Inference | Full native-resolution sliding window (512 px tiles, 64 px overlap), accumulated as logits |

The dataset is cited under its publisher's terms (Korshunov et al. 2025,
doi:10.17073/2500-0632-2025-05-416), which grant research use with citation.

## 2. Held-out results

Source: `reports/lumenstone_s2_patches_test_metrics.json`, regenerated from the
checkpoint on 29 September and bit-for-bit identical to the committed version
(`reports/S2-REPRODUCTION-2026-09-29.md`). Void-border figures come from
`reports/benchmark_s2_patches.json`, which excludes pixels within 5 px of a
labelled boundary, as the published LumenStone protocol does.

| Class | IoU | IoU, void-border | Recall | Precision |
|---|---:|---:|---:|---:|
| background | 0.8709 | 0.9290 | 0.9198 | 0.9425 |
| **pyrrhotite** | **0.8695** | 0.8929 | 0.9343 | 0.9261 |
| **chalcopyrite** | **0.5755** | 0.6151 | 0.7161 | 0.7456 |
| **pentlandite** | **0.5468** | 0.5801 | 0.7420 | 0.6752 |
| magnetite | 0.0000 | 0.0000 | 0.0000 | undefined |
| **mean** | **0.5725** | **0.6034** | | |

Pixel accuracy is 0.8914 (void-border 0.9131). **It is dominated by background
and pyrrhotite and must not be quoted as "89% mineral identification".**

### How much to trust the headline: n = 12 sections

Source: `reports/s2_section_stats.json` (`python -m src.s2_section_stats`).

| Statistic | Value | 95% bootstrap interval |
|---|---:|---:|
| Pooled mean IoU (all test pixels in one confusion matrix) | 0.5725 | 0.494-0.624 |
| Mean of per-section mean IoU | 0.4671 | 0.412-0.534 |

Both are legitimate conventions and they differ. The pooled figure weights
large, easy sections more. **10 of the 12 sections score below 0.5725 on their
own** (range 0.340-0.728). The interval is a percentile bootstrap over sections
(2,000 resamples, seed 42), because a section, not a pixel, is the independent
unit. The per-section figure was first reported by REEFPRINT and reproduces
exactly here.

These 12 sections are the publisher's test split, reused throughout development:
**a benchmark, not a prospective validation**. LumenStone ships no specimen or
locality metadata, so the 12 may not be 12 independent specimens.

## 3. Confusion matrix

Pixel counts over all 12 sections; rows are ground truth, columns are
predictions. Source: `reports/magnetite_confusion_patches.json` (its IoUs
reproduce the table above exactly).

| truth \ predicted | background | chalcopyrite | magnetite | pyrrhotite | pentlandite |
|---|---:|---:|---:|---:|---:|
| background | 23,818,553 | 211,987 | 0 | 1,477,476 | 388,149 |
| chalcopyrite | 83,863 | 3,777,020 | 0 | 164,868 | 1,248,469 |
| magnetite | 643,451 | 673 | 0 | 138,272 | 39,191 |
| pyrrhotite | 648,978 | 984,808 | 0 | 56,571,212 | 2,342,447 |
| pentlandite | 77,203 | 91,370 | 0 | 2,735,419 | 8,351,935 |

The main confusions are between the three sulphides. Chalcopyrite loses 1.25M
pixels to pentlandite, and pentlandite 2.74M to pyrrhotite.

## 4. Does deep learning add anything? Trivial baselines

Source: `reports/lumenstone_s2_trivial_baselines.json`. Same split, same metric.

| Method | Mean IoU | Pixel accuracy |
|---|---:|---:|
| Majority class everywhere | 0.1167 | 0.5833 |
| Colour-only nearest centroid | 0.3948 | 0.5413 |
| **KHANYA (DeepLabV3)** | **0.5725** | **0.8914** |

Colour alone gets part of the way. The three sulphides' mean RGB colours are
nearly identical, so separating them needs texture and context, which is what
the network adds. A metadata-only baseline is not possible: LumenStone ships
none.

## 5. Where it fails: magnetite

The model predicts magnetite **exactly zero times** across all **103,795,344**
test pixels (section 3's column), a dead output channel rather than a weak class.
78.3% of true magnetite is predicted as background (the dark mounting resin);
the rest as the sulphides.

Magnetite is **0.79%** of test pixels (821,587 of 103,795,344), and about 1.84%
of training pixels (`STATUS.md`). Published work detects magnetite on this
modality (0.650, Korshunov et al.), so the failure is a limit of this model's
capacity and training budget, not of reflected light. **Three phases meet the
brief; the report does not claim four.**

> An earlier project figure of "92.6 million test pixels" was an arithmetic
> error; the confusion matrix totals 103,795,344.

## 6. Against published results: the like-for-like S1 comparison

No published S2-only benchmark exists, so the comparison is made on S1
(Berezovskoe hydrothermal, seven classes) with KHANYA's separate S1 checkpoint.
It uses the **exact 16 test images** the published ResUNet result used,
established by sha256 byte-identity against S1 v2, with zero overlap into our
training data. Source: `reports/benchmark_s1_v1_protocol.json`,
`reports/S1-V1-LIKE-FOR-LIKE-2026-09-15.md`.

| Class | KHANYA, void-border | Published ResUNet, void-border | Gap |
|---|---:|---:|---:|
| bornite | 0.8975 | 0.8955 | **+0.0020** |
| background | 0.8490 | 0.8505 | -0.0015 |
| pyrite | 0.9286 | 0.9732 | -0.0446 |
| chalcopyrite | 0.8916 | 0.9363 | -0.0447 |
| sphalerite | 0.6355 | 0.7653 | -0.1298 |
| galena | 0.5068 | 0.7630 | -0.2562 |
| tennantite | 0.3479 | 0.7706 | -0.4227 |
| **mean** | **0.7224** | **0.8506** | **-0.1282** |

We match published work on two classes and trail it overall. Tennantite and
galena, grey phases close in reflectance to their neighbours, account for 75.7%
of the gap. The published figure is read from its authors' table, not
reproduced by us.

## 7. Decision-level results

IoU does not decide what the plant is told. Sources:
`reports/decision_gap_patches.json`, `reports/decision_gap_patches_refined.json`.

The advisor is run twice on each held-out section, once on the model's mask and
once on the expert-drawn mask, and disagreements are classified.

- **Unsafe:** the model's advice says *Continue at current setpoint* where the
  expert-mask advice does not; or it gives any other non-hedged advice where the
  expert-mask advice says *Grind finer* (`classify()` in `src/decision_gap.py`).
- **Conservative:** the model acts where it need not.
- **Flagged:** the model hedges to manual review.

This measures **consistency with the same rules applied to expert labels**, not
metallurgical correctness.

| Pipeline | Disagreements | Unsafe | Conservative | Flagged |
|---|---:|---:|---:|---:|
| Raw particle segmentation | 7/12 | 2 | 0 | 5 |
| With topology refinement (shipped) | 8/12 | **0** | **0** | 8 |

These figures include the evidence-sufficiency gate added on 30 September
(PR #10): no advice from fewer than 9 payload-bearing particles. **9 is a
provisional, conservative operating floor, not a statistical bound**: the
binomial argument first used to motivate it does not hold for an area-weighted
index over spatially dependent particles (Lethabo, PR #10 review). Before it, the
raw pipeline made 5 confident errors (2 unsafe, 3 conservative) and the refined
one disagreed on 6/12, all hedges. The gate turned the three conservative errors
into refusals. On the refined pipeline it refused two more sections, test_02 and
test_07, where the model found 5 and 8 payload particles against the expert's 12
and 13. The two remaining raw unsafe errors (test_03, test_04) had enough particles:
the raw estimator put their association near 100% where the expert-mask value
was under 11%. That is the broken raw particle identity the refinement exists to
fix, which is why the shipped pipeline is the refined one.

Refinement does not reduce disagreement. It removes the confident errors,
unsafe ones included, leaving only requests for review. **Zero unsafe in 12 is an observation,
not a rate**: the exact one-sided 95% upper bound on the unsafe rate is
**22.1%**. The thresholds were not locked before this evaluation, and three of
the advisor's four thresholds are marked **UNSOURCED placeholder** in
`src/advisor.py` (`PAYLOAD_FLOOR`, `REJECT_CEILING`, `DELETERIOUS_CEILING`).

## 8. Reproducibility

- **The checkpoint reproduces exactly.** A fresh evaluation on 29 September
  matched the committed metrics bit-for-bit.
- **The training recipe does not.** `src/segmentation/patches.py:156` samples
  training patches with an unseeded generator. A second run of the identical
  recipe on identical data (REEFPRINT, Kaggle T4, 29 September) scored **0.4543**
  mean IoU. The figures in this report describe **this checkpoint, not the
  method**.
- `python -m src.preflight` refuses to run the demonstration unless the
  checkpoint's sha256 matches the one above.

## 9. Robustness to lighting

Source: `reports/ILLUMINATION-STABILITY-2026-09-15.md`. Measured on centre
512 px fields.

| Test | n | Advice changed |
|---|---:|---:|
| S2 held-out, synthetic exposure shift of -35 RGB (the magnitude measured in real re-imaging) | 12 | **8** |
| LumenStone V1, real re-imaged pairs of the same sections (S1 checkpoint) | 10 | **5** |

**The model's advice is sensitive to illumination.** No gate for it is in the
submission; the fragility is disclosed instead.

## 10. Speed

Source: `reports/segmentation_latency.json`. CPU only, Windows 11 laptop.

| Stage | n | Mean | p95 |
|---|---:|---:|---:|
| One 512 px field, model forward pass only | 60 | 2.64 s | 3.60 s |
| One whole section (test_01), sliding window | 6 (one image) | 162.3 s | 195.7 s |

Against the design targets set in the technical review: the 5 s p95 target for
a field is met for the model forward pass, but end-to-end field time is not
recorded in a report file. The 30 s p95 target for a full image is **not met** on
this CPU. Section preparation is not included. No GPU timing exists yet.

**A single field is not the section.** One centre field held 0-20
payload-bearing particles and matched the whole section's advice on **0 of 12**
held-out sections once the evidence gate applies (4 of 12 before it,
`reports/s2_section_stats.json`). The live path therefore samples **six fields**
across the section: they match the whole section's advice on **9 of 12**
(`reports/field_sampling_s2.json`). The six-field grid was fixed by a latency
budget before this was measured, not chosen on the test set. Live end to end,
including the on-screen progress, six fields took 17.2 s on this CPU in one
dashboard run. That is a single observation, not a measured distribution.

## 11. Limitations

1. Norilsk and Berezovskoe ore. **No South African ore has been evaluated.**
2. 12 held-out sections, reused throughout development, possibly not
   independent specimens.
3. Magnetite is never detected.
4. The advice is sensitive to lighting (section 9).
5. The training recipe is not reproducible (section 8).
6. Decision-level results are consistency with a reference policy whose
   thresholds are partly unsourced (section 7).
7. Latency is CPU-only, has small n, and excludes preparation.
8. The plant-parameter demonstration is a simulation. No plant data exists, and
   no claim is made about reagent use, recovery or turnaround.

## 12. Reproduce

```bash
python -m src.preflight                         # checkpoint hash, data, model, OPC UA
python -m src.segmentation.train_patches --eval  # section 2, full-section inference
python -m src.s2_section_stats                  # section 2 intervals, section 10 live vs full
python -m src.benchmark                         # void-border protocol
KHANYA_SUBSET=S1 python -m src.benchmark        # section 6
python -m src.decision_gap --model patches --refine   # section 7
python -m src.exposure_control                  # section 9, S2 control
```
