# KHANYA / REEFPRINT — where the project actually stands

**As of 2026-08-16.** Single source of truth for what exists, what does not, and
what to do next. `HANDOVER.md` is the running log; this file is the snapshot.

| | |
|---|---|
| Competition | Mintek SCi Grad Hackathon 2026, Problem 3 — **selected** (letter 14 Aug) |
| Abstract due | **30 Aug 2026** — 14 days out |
| Final hacking day | **1 Oct 2026**, on site at Mintek, 13:00 hard submission cutoff, 10-min pitch |
| Conference | 2 Oct 2026, compulsory; five finalists announced, then originality authentication |

**Brief's deliverable floor:** trained model identifying **>=3 mineral phases**,
an accuracy report, and demonstration of **operational feedback integration**.

---

## 1. The one-paragraph version

We have a working end-to-end pipeline — micrograph in, plant recommendation out —
and a real held-out result on five mineral phases that clears the brief's floor.
The pipeline's weakest link is the segmentation model itself: it fails completely
on the rarest phase, and when its output drives the advisor, **a third of the
operational recommendations change**, two of them in the direction that loses
metal. The honest position today is: *the system is real, the measurements are
real, the model is not yet good enough to trust*, and we can prove all three
statements with numbers in `reports/`.

---

## 2. What is DONE

### 2.1 Data (the original blocker, now half solved)

| Dataset | Status | Use |
|---|---|---|
| **LumenStone S2 v2** | Secured, 419 MB | **Primary.** 37 train / 12 test, 5 classes, pixel masks, native 3396x2547, author-defined split |
| FeM iron ore | Secured | Binary ore/resin only. Earlier result mIoU 0.872 — different task, does not meet the >=3 phase floor |
| MUMDMC2025 | Secured (583 images) | Dev proxy only. 8 specimens total; too specimen-poor for any honest accuracy claim |
| LITHOS-DATASET | **Ruled out** | Sedimentary/carbonate petrography — wrong rock type. Recorded so it is not rediscovered |
| Bushveld / UG2 / Merensky | **None public** | The remaining gap |

**Why S2 is defensible:** it is the Norilsk Group layered-ultramafic assemblage
(pyrrhotite, pentlandite, chalcopyrite, magnetite) — the same base-metal sulphide
assemblage carrying the PGM payload in Bushveld reef ores, same intrusion type.

**Where it breaks, and this must always be said in the same breath:** Norilsk is
*massive* sulphide. BMS is 62.8% of S2 pixels against <1 vol% in UG2. S2 is an
analogue for the **assemblage and its optical appearance, not its abundance**.

### 2.2 Segmentation — meets the brief's floor

Resize baseline, DeepLabv3+ResNet50, 12 epochs CPU, whole held-out sections:

| Class | % test pixels | IoU |
|---|---|---|
| pyrrhotite | 58.33 | 0.864 |
| background (resin) | 24.95 | 0.827 |
| chalcopyrite | 5.08 | 0.548 |
| pentlandite | 10.84 | 0.485 |
| **magnetite** | **0.79** | **0.000** |
| **mean** | | **0.545** |

Pixel accuracy 0.879. Source: `reports/lumenstone_s2_test_metrics.json`.

Five phases, pixel masks, held-out test never seen in training or checkpoint
selection. **This clears the brief's >=3 phase requirement.** It is also well
short of the published PSPNet+ResNet18 benchmark on S1+S2 (mIoU 0.88), which
should be stated rather than hidden.

### 2.3 Operational feedback — measured, not asserted

This was the weakest deliverable and is now the strongest differentiator.

- **Modal mineralogy** — phase area fractions computed as a proportion of *ore*
  area, excluding mounting resin (otherwise every number tracks how densely the
  section was mounted).
- **Liberation by particle composition** — grains in a polished section are
  separated by resin, so connected components of non-resin pixels are particles.
  A particle is liberated when the payload phase occupies >=50% of it; the index
  is the mass-weighted share of payload in liberated particles. Validated across
  all 12 test sections: spans 0%–100% and tracks the mineralogy correctly.
- **Role-based advisor** — reasons over metallurgical roles (payload / reject /
  oxide / gangue / deleterious), not mineral names. Swapping ore body changes a
  mapping in `src/modal.py`, not the decision logic, so REEFPRINT data drops in
  unchanged if Mintek releases any.

Both inputs were previously fake: classifier confidences standing in for area
fractions, and liberation from a slider the presenter dragged. Both are gone.

### 2.4 The decision-gap analysis — our best original contribution

Per-class IoU says how wrong the mask is. It does not say whether being that
wrong changes what the plant is told to do. `src/decision_gap.py` runs the
advisor twice over the same 12 held-out sections — ground-truth masks vs
predicted — and records where the recommendation flips.

**4 of 12 flip (33%).** Source: `reports/decision_gap.json`.

| Section | Liberation truth → predicted | Effect | Direction |
|---|---|---|---|
| test_04 | 9% → 75% | "grind finer" → "continue at setpoint" | **unsafe** |
| test_05 | 4% → 58% | "grind finer" → "continue at setpoint" | **unsafe** |
| test_09 | 100% → 0% | "continue" → "grind finer" | conservative |
| test_02 | payload 1.0% → 0.0% | payload missed entirely | detection miss |

Two flips tell the plant to carry on while payload is locked in composite
particles — recoverable metal to tailings, the expensive direction of error.

### 2.5 Infrastructure

Offline Streamlit dashboard on the segmentation path; specimen-safe splitting;
per-class metrics; every reported claim traced to a JSON in `reports/`.
Lethabo has write access (confirmed active). Issue #1 opened summarising all of
this. **Note:** repo-collaborator *admin* is not grantable on a personal GitHub
repo — only read/write — so that was tried and abandoned; it needs an org.

---

## 3. What is NOT done

### 3.0 UPDATE 2026-08-16 (later): three approaches tried, magnetite diagnosed

**Patch sampling at native resolution works — for every class except magnetite.**
Whole-section held-out result, directly comparable to the resize baseline:

| Class | Resize (CE) | **Patch (CE)** |
|---|---|---|
| background | 0.827 | **0.871** |
| chalcopyrite | 0.548 | **0.576** |
| pyrrhotite | 0.864 | **0.870** |
| pentlandite | 0.485 | **0.547** |
| magnetite | 0.000 | **0.000** |
| **mean IoU** | 0.545 | **0.5725** |
| pixel accuracy | 0.879 | **0.8914** |

Source: `reports/lumenstone_s2_patches_test_metrics.json`. **Use the patch model
as the primary result from here on.**

**CE+Dice did not help.** Ran the full 8 epochs; best val patch mIoU 0.4739
against CE's 0.5384, and magnetite stayed at IoU 0.0000 every epoch. Three
independent approaches have now failed on magnetite: resize+CE, native
patches+CE, native patches+CE+Dice.

**Diagnosis — the model never predicts magnetite at all.** Zero pixels predicted
across the whole test set, against 33,469 in ground truth. This is total class
collapse, not poor boundary placement. Source:
`reports/magnetite_confusion.json`.

| Truth ↓ / Predicted → | background | chalcopyrite | magnetite | pyrrhotite | pentlandite |
|---|---|---|---|---|---|
| **magnetite** | **92.3%** | 0.0% | **0.0%** | 6.5% | 1.2% |
| **pentlandite** | 2.7% | 14.0% | 0.0% | **29.2%** | 54.2% |

Magnetite is absorbed into **background**, not into another sulphide. That is
mineralogically coherent: magnetite has low reflectance in reflected light — dark
grey, optically much closer to the dark mounting resin than to the bright
sulphides. The model is not confusing two minerals; it is failing to separate a
dark mineral from empty space. This also explains why neither more pixels
(native resolution) nor a rebalanced objective (Dice) helped — **neither
addresses a reflectance ambiguity.**

Second finding, worth naming in the report as domain knowledge rather than
generic error: **pentlandite is predicted as pyrrhotite 29.2% of the time.**
That is the classic exsolution-intergrowth problem — pentlandite exsolves as
flames within pyrrhotite and the two are similar bronze-cream colours. It is the
main reason pentlandite sits at ~0.55 rather than ~0.85.

**Untested hypothesis, do not state as fact yet:** if magnetite is being called
background, it is excluded from ore area, shrinking the denominator in modal
mineralogy and inflating the payload fraction — which is the direction of both
unsafe flips (test_04 payload 21%→41%, test_05 19%→50%). If it holds, it is a
clean causal chain from rare-class collapse to the expensive operational error.
Verify before putting it in the pitch.

**Recommended position:** stop attacking magnetite. Report a **four-phase**
result with magnetite as a named, diagnosed limitation. Four working phases
still clears the brief's >=3 floor, and a well-characterised failure with a
mineralogical explanation is worth more to judges than a fifth class we cannot
make work. If anything is tried, try increasing input bit depth / contrast
normalisation on the dark end, since that targets the actual mechanism.

### 3.1 The original hypothesis, now dead (retained for the record)

Magnetite scores **IoU 0.000** in the resize baseline. The stated hypothesis was
that the 6.6x linear downsample destroyed fine grains before the model saw them,
and the fix was patch-based sampling at native resolution.

**That hypothesis is not supported.** The patch model trained to epoch 7 at full
native resolution, with balanced sampling putting magnetite in roughly 44% of
patches (against its 1.84% area share), and **magnetite still scored IoU 0.0000
at every single epoch.** Resolution was not the binding constraint.

This reframes the problem for architecture purposes: magnetite is not failing
because it is *small*, it is failing because the model never learns to predict it
at all under plain cross-entropy. Sampling fixed exposure; it did not fix the
prior, and the loss remains dominated by pyrrhotite at 45% of pixels.

Caveat on the above: those are *balanced-patch validation* numbers, which are not
comparable to whole-section numbers. The whole-section evaluation of the patch
checkpoint is running now and is the figure that settles it.

### 3.2 Everything else outstanding

| Item | Status |
|---|---|
| Whole-section eval of patch model | **running now** |
| `decision_gap` re-run on patch model | blocked on the above |
| Diagnostic: what does magnetite get confused *with*? | not started — cheap and high value |
| Cross-validation instead of the 6-image val set | not started. Val is unrepresentative (45.8% vs 25.0% background); pentlandite scored 0.026 val vs 0.485 test, so checkpoint selection is near noise |
| Data for chromite / orthopyroxene / plagioclase / talc-serpentine | **4 of REEFPRINT's 5 phases still have no data** |
| Advisor thresholds | 1 of 4 literature-sourced; 3 are placeholders |
| Research report prose (sections 1, 2, 4, 6, 8, 10) | still skeleton |
| Energy / cost case | not started |
| R6,000 rig decision (REEFPRINT §3.13) | **open since 4 Aug** |
| Mintek mentor request + per-member admin | **due 30 Aug** |
| One-page abstract | Lethabo |
| Offline demo rehearsal on venue laptop | not started |

---

## 4. Architecture as it stands — for Lethabo

```
micrograph (3396x2547 reflected light, polished section)
        |
        v
  SEGMENTATION            DeepLabv3+ResNet50, 5 classes
        |                 src/segmentation/
        |                 two interchangeable paths:
        |                   - resize   (train_lumenstone.py)  mIoU 0.545
        |                   - patches  (train_patches.py)     native res, eval pending
        v
  labelled mask
        |
        v
  MODAL MINERALOGY        src/modal.py
        |                 area fractions as proportion of ORE (resin excluded)
        |                 -> mineral -> metallurgical ROLE mapping
        v
  LIBERATION              connected components = particles
        |                 mass-weighted share of payload in liberated particles
        v
  ADVISOR                 src/advisor.py — reasons over ROLES, not minerals
        |                 grind finer / adjust reagent / continue / flag
        v
  recommendation + confidence + explicit caveats
```

**Where uncertainty enters, in order of severity:**

1. **Segmentation error** — dominates. Quantified: 33% of recommendations flip.
2. **Rare-class blindness** — magnetite never predicted. In UG2 terms this is the
   sub-1% payload problem, which is the entire premise of REEFPRINT.
3. **Stereological bias** — liberation from 2D sections is biased *high* against
   true volumetric liberation. No correction applied, so our index is an upper
   bound: safe for "grind finer", unsafe for "continue at setpoint".
4. **Threshold provenance** — 3 of 4 advisor trip points are placeholders.
5. **Ore-body transfer** — S2 is an assemblage analogue, not an abundance one.

**The design property worth defending in the pitch:** the advisor consumes
*roles*, not mineral names. That is what makes the system a Bushveld tool rather
than a Norilsk tool — swap the mapping, keep the logic.

---

## 5. What should be done next, in priority order

**Before 30 Aug (abstract):**

1. **Settle the magnetite question.** Finish the whole-section eval, then run the
   confusion diagnostic — is magnetite predicted as *anything*, and if so what?
   If it is systematically absorbed into pyrrhotite or background, that is a
   loss-function problem (Dice / Focal / Tversky), not a sampling one. Note
   petroscope's warning is specifically that *class weighting* does not work;
   region-based losses are a different mechanism and untested here.
2. **Decide abstract scope** — full five-phase REEFPRINT, or what we can
   evidence? Recommendation: claim what we can show, name the rest as the
   extension. Originality authentication goes better when claims match evidence.
3. **Rig decision, mentor request, admin.** Hard deadline, no technical blocker.

**September:**

4. Grouped cross-validation to replace the 6-image val set — current checkpoint
   selection is close to noise.
5. Re-run `decision_gap` on the improved model and show the flip rate coming
   down. **This before/after, framed as metal recovered rather than IoU, is the
   strongest slide available.**
6. Source the three placeholder thresholds, or state them as configurable plant
   parameters rather than claims.
7. Write the report prose; build the energy/cost case.

**Freeze 29 Sep.** Rehearse the demo offline, end to end, on the venue laptop.

---

## 5b. UPDATE 2026-08-16 (final): better segmentation did NOT buy better decisions

Both models re-measured at native resolution against the same ground truth:

| | Resize (CE) | Patch (CE) |
|---|---|---|
| Mean IoU | 0.545 | **0.5725** |
| **Recommendation flips** | **6/12 (50%)** | **6/12 (50%)** |
| Liberation correlation vs truth | +0.128 | **-0.079** |
| Liberation mean absolute error | 38.7% | 46.7% |

**+2.8 points of mean IoU produced zero change in decision quality**, and
predicted liberation is uncorrelated with true liberation — slightly *negative*
for the better model. Predicted liberation is currently noise.

Why, and it is structural: liberation comes from connected components, so
particle identity is a question of **topology**. A few misclassified boundary
pixels bridge two particles into one or split one in two, changing that
particle's payload fraction discontinuously. Per-class IoU rewards correct grain
*interiors*, which is nearly independent of correct grain *boundaries*.

**This supersedes the earlier 33% figure**, which was measured at 512x688 where
`MIN_PARTICLE_PIXELS` corresponds to a different physical grain size. Native is
the correct reference and is what a plant receives.

**What this means for the pitch.** The advisor's decision logic is validated — on
ground-truth masks it gives coherent recommendations across the full range of ore
textures. The *chain* is not validated, because segmentation cannot yet supply
accurate particle topology. That is an honest and defensible position, and the
finding itself is the most transferable thing we have: **in image-based
mineralogy, per-class IoU is a poor proxy for operational value.**

**Effort should now go to boundary topology, not class accuracy:** morphological
post-processing and watershed separation; a liberation estimator less brittle
than raw connected components (erode particles before measuring composition, or
an area-fraction proxy that degrades gracefully); or instance-aware segmentation
predicting particles directly. Chasing IoU is now demonstrably the wrong target.

---

## 5c. UPDATE 2026-08-16: watershed refinement — the fix works

Acting on 5b's conclusion (the bottleneck is particle topology, not class
accuracy), `src/modal.py` gained a refinement stage applied identically to
ground-truth and predicted masks, since the *estimator* is what changed:

- **speckle removal** (morphological opening) — isolated misclassified pixels
  were inventing tiny particles that scored as perfectly liberated
- **hole filling** — a phase predicted as background *inside* a grain punches a
  hole that splits one particle into two. Not hypothetical: magnetite is
  predicted as background 92.3% of the time, so every magnetite inclusion
  becomes a hole
- **marker-controlled watershed** on the distance transform — separates touching
  grains that raw connected components merge into one averaged particle

| Setup | Flips | Liberation corr. vs truth | Liberation MAE | Unsafe "continue" flips |
|---|---|---|---|---|
| resize, raw components | 6/12 (50%) | +0.128 | 38.7% | 2 |
| resize, watershed+fill | 4/12 (33%) | +0.709 | 16.4% | 1 |
| patch, raw components | 6/12 (50%) | -0.079 | 46.7% | 1 |
| **patch, watershed+fill** | **2/12 (17%)** | **+0.947** | **8.9%** | **0** |

Sources: `reports/decision_gap.json`, `reports/decision_gap_refined.json`,
`reports/decision_gap_patches.json`, `reports/decision_gap_patches_refined.json`.

**The two changes are complementary, and that is the finding.** Better
segmentation alone bought nothing (50% -> 50%). Better estimator alone helped
(50% -> 33%). Together they reach 17% with liberation correlation 0.947 and
**zero flips in the expensive direction** — no section is told to continue at
setpoint while its payload is locked. Improved per-class accuracy was not
useless; it was *unusable* until particle topology was repaired well enough to
exploit it. Reporting either change in isolation would have understated both.

### 5d. UPDATE 2026-08-16: uncertainty band, and a correction

The advisor now returns **"Marginal - verify before acting"** when liberation
falls within `LIBERATION_MARGIN` (0.089) of the 0.50 floor. That width is the
estimator's own mean absolute error on the held-out sections, not a chosen
number, and must be re-derived if the estimator changes. Ground truth is scored
with margin 0, since an annotation carries no estimator error.

Flips are now classified by consequence, because counting a hedge the same as a
confident wrong instruction would hide the band's entire effect:

| Config | Flips | unsafe | conservative | flagged |
|---|---|---|---|---|
| resize + refined + band | 4/12 (33%) | **0** | 1 | 3 |
| patch + refined + band | 2/12 (17%) | **1** | 0 | 1 |

**Correction to the earlier claim of "zero unsafe flips" for patch+refined.**
That used a narrow definition counting only a predicted "Continue at current
setpoint". The severity classifier is stricter and correct: test_04 has truth
liberation 40% ("grind finer") against predicted 74% ("adjust reagent dosage").
The plant does not grind, so locked payload still reports to tailings - unsafe
by consequence even though the action is not literally "continue". **The honest
figure is 1 unsafe, not 0.**

**The better model is the less safe one here, and that is worth presenting.** On
test_04 the resize model predicts 55%, inside the band, and hedges; the patch
model predicts 74%, outside the band, and is confidently wrong. Higher average
accuracy, worse calibration on the case that matters. The trade-off is real:
patch is more decisive (half the disagreements), resize is safer (no metal at
risk). In flotation an unnecessary check is cheaper than lost metal, so **for a
deployed advisory system the resize+band configuration is the defensible
default**, with patch reserved for where a human reviews the output.

Note the flip rate barely moves when the band is added. That is the point: the
band does not remove disagreements, it converts dangerous ones into honest ones.
Anyone reading flip rate alone will conclude nothing improved.

**Both remaining patch flips straddle the liberation threshold** — test_04 truth 40%
vs predicted 74%, test_05 truth 32% vs predicted 52%, against a 0.50 floor.
test_05's prediction clears the threshold by two points. So what survives is not
gross error but *threshold brittleness*: near 0.50 a small liberation error
flips the recommendation. That argues for a declared uncertainty band around
each threshold — reporting "marginal, verify" rather than a confident action
when the estimate sits within the model's own error margin (currently ~9% MAE).
Worth building before the event; it is cheap and it directly addresses the
failure mode that remains.

**Liberation correlation went from +0.128 to +0.709 and error more than halved —
by changing the estimator, on the WEAKER model, with no retraining.** This
confirms the 5b diagnosis directly: the binding constraint was particle
topology, and repairing topology recovers most of the decision quality that
better per-class accuracy could not buy.

Note the refinement changes ground-truth liberation too, sometimes a lot
(test_10: 82% -> 3% as 209 particles become 51). That is the point rather than a
problem — the raw estimator was counting annotation speckle as liberated
particles, so the refined figure is the more faithful measurement of both
sides. It does mean **all liberation numbers predating this change are
superseded.**

Requires `opencv-python` (watershed) and `scipy`; both fall back gracefully to
plain connected components if absent, so the venue demo cannot die on an import.

---

## 6. Numbers that must never be quoted

- **33% flip rate** — measured at 512x688, where `MIN_PARTICLE_PIXELS` means a
  different physical grain size. **50% at native resolution, for both models**,
  is the correct figure (section 5b). The earlier note in this file claiming 33%
  was the honest number is itself superseded — the ruler was wrong, not just the
  alignment.
- **Patch-model validation IoUs** — computed on balanced patches, which flatter
  rare classes by construction. Only whole-section `--eval` numbers are
  comparable to the baseline.
- **MUMDMC 98.3%** — train-set fit on 8 specimens. Memorisation, not accuracy.
- **FeM mIoU 0.872** — real, but a *binary* ore/resin task. It does not meet the
  >=3 phase floor and must not be presented as if it does.
