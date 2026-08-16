# KHANYA — Research Phase Report

**Optical mineral characterisation for real-time ore processability**
Mintek-SCi Grad Hackathon 2026 — Problem 3

| | |
|---|---|
| Team | Sibusiso Khumalo (+2) |
| Status | Research phase |
| Started | 2026-08-04 |
| Event | 1–2 October 2026, Mintek, Randburg |

> Originality is a scored criterion and submissions undergo AI-generation checks.
> Every paragraph here must be our own prose, every claim cited. Do not paste
> generated text into this document.

---

## 1. Problem statement

*Restate Problem 3 in our own words. Name the three deliverables the brief
demands: a trained model identifying >= 3 mineral phases, an accuracy report, and
demonstration of operational feedback integration.*

## 2. Why this matters to the minerals sector

*The plant-level cost of poor mineralogical information. Milling energy. Recovery
losses to tailings. Turnaround time of conventional automated mineralogy.*

## 3. The optical argument

Core claim: SEM/BSE cannot reliably separate hematite from magnetite because
their average atomic numbers are near-identical. Reflected-light optical
microscopy can, on reflectance and colour.

*Develop this into the cost argument: an optical rig plus a trained model against
a multi-million-rand automated mineralogy instrument.*

## 4. State of the art

*See DATA-SOURCES.md for the reference list. Cover: DeepLabv3+ opaque/non-opaque
segmentation (2021), improved YOLOv8n fine-grained segmentation (2025),
polished-section segmentation and labelling (2025), Res-UNet ensembles.*

Benchmarks we are measured against:

| Work | Dataset | Metric |
|---|---|---|
| PSPNet + ResNet18 | LumenStone S1+S2 | mean IoU 0.88, PA 0.96 |
| ResUNet (petroscope) | LumenStone S1v1 | mean IoU 0.8373 |

*State plainly which number we are targeting and why.*

## 5. Data

*Summarise DATA-SOURCES.md. State access status honestly, including that
LumenStone access is unresolved at time of writing, and what the fallback is.*

### 5.0 Baseline run, 2026-08-04 — pipeline check, not an accuracy result

Trained ResNet18 (ImageNet-pretrained) on the MUMDMC2025 public sample: 583
images, 5 classes, **8 physical specimens total** (1-2 per class). 15 epochs,
CPU. Train accuracy 98.3%, loss 0.32 -> 0.03.

**This is not a reportable accuracy figure.** Every class has too few specimens
to hold any out for testing without either leaving a class with zero training
data or testing on a rotation-photo of a rock already seen in training - the
exact near-duplicate leakage this project's split logic (`src/data.py`) exists
to prevent. The 98.3% number shows the model memorised these 8 rocks; it says
nothing about generalisation. Value of this run: confirms the training pipeline,
data loader, and checkpointing all work correctly end to end.

Checked whether a larger version of this dataset is publicly available: the
paper (Scientific Data, 2025) describes 14,400 images / 2,880 per class, but the
figshare item actually linked to the paper's DOI (10.1038/s41597-025-05879-9,
figshare 28513535) publishes only one thumbnail image and a summary CSV - the
full dataset is not public. The 4.8GB file we obtained (figshare 29483204,
same dataset name, unofficial upload) is the only public version found and is
the 583-image/8-specimen set above. No larger public version exists as of this
writing.

**Next step:** either find additional specimens for these 5 mineral classes
from another public source, or reduce scope to a defensible statement ("model
converges cleanly; specimen diversity is the open constraint") and pair it with
strong segmentation/advisor work where evaluation is more tractable.

### 5.0.1 Segmentation baseline, 2026-08-04 — real held-out result

Trained DeepLabv3+ResNet50 (ImageNet-pretrained) on FeM (ore/resin binary
segmentation, reflected-light microscopy, 81 distinct polished sections - no
rotation duplicates, so a plain image-level split is legitimate here, unlike
MUMDMC). Split 57 train / 12 val / 12 test, all at image level, 10 epochs, CPU.

**Held-out test set (12 unseen images), unlike the classification run above:**

| Metric | Value |
|---|---|
| Mean IoU | **0.872** |
| Pixel accuracy | **93.75%** |
| IoU - resin (background) | 0.836 |
| IoU - ore | 0.908 |

This is a legitimate number: the test images were never seen in training and
are not rotations/duplicates of training images. For context, the published
PSPNet+ResNet18 benchmark on LumenStone (a different, multi-class dataset)
reports mean IoU 0.88 - we are in the same range on a binary task with a much
smaller model budget (10 epochs, CPU, no GPU). Note this is ore-vs-resin, not
the REEFPRINT phase set (see DATA-SOURCES.md Section 0) - it demonstrates the
segmentation pipeline works, not phase-level performance on our actual target
classes.

### 5.0.2 LumenStone S2 multi-class baseline, 2026-08-14 — first result that meets the brief's floor

DeepLabv3+ResNet50 (ImageNet-pretrained), 12 epochs, CPU, plain cross-entropy,
images resized 3396x2547 -> 512x688. Split: 31 train / 6 val / 12 test, using the
authors' own train/test division with val carved from train. **Test set never
seen during training or checkpoint selection.**

| Class | % of test pixels | Test IoU |
|---|---|---|
| background (resin) | 24.95 | 0.827 |
| chalcopyrite | 5.08 | 0.548 |
| magnetite | 0.79 | **0.000** |
| pyrrhotite | 58.33 | 0.864 |
| pentlandite | 10.84 | 0.485 |
| **mean** | | **0.545** |

Pixel accuracy 0.879. Numbers in `reports/lumenstone_s2_test_metrics.json`.

This is five phases with pixel-level masks on a held-out test set, so it clears
the brief's >=3 phase requirement with a defensible number. It is also well short
of the published PSPNet+ResNet18 benchmark on S1+S2 (mIoU 0.88) and should be
presented as such: 12 CPU epochs at roughly one-sixth linear resolution, with no
patch-based sampling, is not a serious attempt at the benchmark.

**Magnetite fails completely.** IoU is 0.000 and magnetite is genuinely present
in the test set (0.79% of pixels), so this is total failure on the rare class,
not an artefact of absence. This is precisely the imbalance failure the
petroscope authors warn about (section 5.1) reproduced in our own numbers.
Two contributing causes, separable by experiment: the class is rare, and the
6.6x linear downsample from 3396x2547 destroys fine grains before the model ever
sees them. Patch-based sampling at native resolution addresses both and is the
next experiment.

**The validation set is too small to select on.** 6 images, and its composition
differs sharply from test (45.8% vs 25.0% background; magnetite 0.20% vs 0.79%).
Pentlandite scored 0.026 on val against 0.485 on test. Checkpoint selection on
best val mIoU is therefore close to noise, and grouped cross-validation over the
37 training sections would be a sounder protocol given how few images exist.

### 5.0.3 What the segmentation error costs at the decision layer

Per-class IoU says how wrong the mask is; it does not say whether being that
wrong changes what the plant is told to do. `src/decision_gap.py` runs the full
advisor path twice over the same 12 held-out sections - once on ground-truth
masks, once on predicted masks - and records where the recommendation changes.

> **Superseded 2026-08-16.** The 33% below was measured with both sides at
> 512x688. Because `MIN_PARTICLE_PIXELS` is a fixed pixel count, it represents a
> different *physical* grain size at each resolution, so that figure is tied to
> the working size rather than to the ore. Both models are now compared at
> **native resolution**, which is also what a plant would receive. The corrected
> figures are **6 of 12 (50%) for both the resize and the patch model** — see
> section 5.0.4, which supersedes this subsection's headline number. The
> per-section table below is retained because the failure *directions* it
> describes are unchanged.

**4 of 12 recommendations flip (33%)** at 512x688 reference — superseded, see
above. Numbers in `reports/decision_gap.json`.

| Section | Liberation, truth -> predicted | Change | Direction |
|---|---|---|---|
| test_02 | 0% -> not measurable | payload 1.0% -> 0.0%; "no payload detected" | detection miss |
| test_04 | 9% -> 75% | "grind finer" -> "continue at setpoint" | **unsafe** |
| test_05 | 4% -> 58% | "grind finer" -> "continue at setpoint" | **unsafe** |
| test_09 | 100% -> 0% | "continue at setpoint" -> "grind finer" | conservative |

The direction matters more than the count. Two flips tell the plant to continue
at setpoint on ore whose payload is in fact locked in composite particles - that
sends recoverable metal to tailings, and it is the expensive direction of error.
One flip is conservative, costing unnecessary grinding energy but no metal. One
is an outright detection miss on a 1% payload field: exactly the sub-1% failure
this project exists to argue about, occurring in our own pipeline.

Honest reading: **the segmentation model is not yet fit to drive this advisor.**
Reporting mIoU 0.545 alone would obscure that; the flip rate is the number that
reflects operational usefulness, and improving it is the priority before the
event.

Methodological note. Ground-truth masks are downsampled to the network's working
size before comparison. Compared at native resolution instead, the flip rate
reads 50% - but that figure is inflated, because the same physical grain carries
~44x fewer pixels in a prediction, so the minimum-particle-size filter discards
far more particles on the predicted side. Three of those six flips were artefacts
of scale, not model error. The like-for-like 33% is the honest figure.

### 5.0.4 Better segmentation did not produce better decisions

Both models evaluated at native resolution against the same ground truth, so the
comparison isolates model quality:

| | Resize (CE) | Patch (CE) |
|---|---|---|
| Mean IoU (whole sections) | 0.545 | **0.5725** |
| Pixel accuracy | 0.879 | **0.8914** |
| **Recommendation flips** | **6/12 (50%)** | **6/12 (50%)** |
| Liberation correlation with truth | +0.128 | **-0.079** |
| Liberation mean absolute error | 38.7% | 46.7% |

Sources: `reports/decision_gap.json`, `reports/decision_gap_patches.json`.

**Raising mean IoU by 2.8 points changed the flip rate not at all**, and left
predicted liberation essentially uncorrelated with true liberation — marginally
*negative* for the better-scoring model. Predicted liberation is, at present,
noise.

The mechanism is structural rather than statistical. Liberation is computed from
connected components, so particle identity depends on **topology**: a handful of
misclassified pixels along a grain boundary can bridge two particles into one or
split one into two, and either changes that particle's payload fraction
discontinuously. Per-class IoU rewards labelling grain *interiors* correctly,
which is nearly independent of whether grain *boundaries* are topologically
right. Optimising one does not optimise the other.

**Consequence for the deliverable, stated plainly:** the advisor's decision logic
is validated — on ground-truth masks it produces sensible, mineralogically
coherent recommendations across the full range of ore textures. What is not yet
validated is the *chain*, because the segmentation stage cannot yet supply
particle topology accurate enough to drive it. Reporting mean IoU alone would
completely hide this.

**Where effort should go** (and this is the practically useful conclusion): not
into per-class accuracy. Candidate directions, in order of expected value —
morphological post-processing and watershed separation to repair boundary
topology; a liberation estimator less brittle than raw connected components,
for example eroding particles before composition is measured, or an
area-fraction proxy that degrades gracefully; or instance-aware segmentation
that predicts particles directly rather than inferring them from a semantic mask.

This is arguably the project's most transferable finding: **in image-based
mineralogy, per-class IoU is a poor proxy for operational value**, and a plant
advisory system must be evaluated on the decisions it produces.

### 5.1 Methodological risk: class imbalance

Mineral class frequencies are naturally very unbalanced; some phases occupy a few
dozen pixels. The petroscope authors report that loss weighting and class
weighting do **not** resolve this, and use patch-based probability-map sampling
instead. Our approach must address this explicitly.

### 5.2 Methodological risk: specimen-level leakage

MUMDMC2025 images each specimen at 72 rotations. Splitting per image places
near-duplicates in both train and test and produces an accuracy that will not
survive questioning. All splits are grouped by specimen.

## 6. Proposed approach

*Pipeline: image -> segmentation -> phase area fractions -> liberation estimate ->
plant recommendation. Say where each stage's uncertainty comes from.*

## 7. Operational feedback layer

The differentiator, and as of 2026-08-14 the stage where the inputs are measured
rather than asserted. The full path is: micrograph -> segmentation -> modal
mineralogy -> liberation -> recommendation (`src/modal.py`, `src/advisor.py`).

### 7.1 Modal mineralogy

Phase area fractions are computed from the predicted mask as a proportion of
**ore area, excluding mounting resin**. Including resin would make every
reported fraction a function of how densely the section happened to be mounted
rather than of the ore itself. Resin coverage is reported separately, as a
data-quality signal: below 5% ore in the field the advisor declines to give a
recommendation instead of computing fractions from too few pixels.

### 7.2 Liberation, measured rather than asserted

Earlier versions of the demo took liberation from a slider the presenter dragged.
It is now computed. Grains in a polished section are separated by resin, so
connected components of non-resin pixels are particles; for each particle we
measure the fraction that is payload phase, and a particle counts as liberated
when that fraction clears 50%. The reported index is the share of total payload
**area** in liberated particles, so it is mass-weighted - one large locked grain
outweighs several small free ones.

Measured across the 12 held-out S2 test sections using ground-truth masks, the
index spans 0% to 100% and behaves the way the mineralogy says it should:
sections that are a few large massive-sulphide particles score near zero
(payload locked inside pyrrhotite), while sections of many small disseminated
grains score above 80%.

**Stereological limitation, stated first.** This is a 2D section through 3D
particles. A section plane can cut the free-standing rim of a particle whose
core is locked, so apparent liberation measured from sections is biased **high**
relative to true volumetric liberation. Plant practice applies a stereological
correction; we do not. Our liberation index is therefore an upper bound, which
means the case for grinding finer is always at least as strong as we report it -
the bias runs in the safe direction for that particular recommendation, and in
the unsafe direction for any "continue at setpoint" call.

### 7.3 Roles, not mineral names

The advisor reasons over metallurgical roles - payload, reject, oxide, gangue,
deleterious - with a per-deposit mineral-to-role mapping in `src/modal.py`.
Changing ore body changes a mapping, not the decision logic, so the same
operational layer serves LumenStone S2 now and the REEFPRINT phase set if Mintek
releases data.

On S2 the mapping is: pentlandite and chalcopyrite are payload, **pyrrhotite is
the rejection target**, magnetite is oxide. Pyrrhotite rejection is established
practice in magmatic Ni-Cu processing - it dilutes concentrate grade and drives
smelter sulphur load. The honest caveat is that pyrrhotite does carry some Ni and
PGE in solid solution, so rejecting it trades grade against recovery rather than
discarding pure waste.

### 7.4 A negative result worth reporting

The first role mapping tried called all three sulphides payload. Liberation then
saturated at ~100% on every test section - correct arithmetic, useless
measurement, because in massive sulphide the payload *is* the rock and every
particle trivially clears the threshold. This is recorded rather than quietly
fixed because it defines what the measurement can discriminate: liberation is
informative when the payload is dispersed in a contrasting host, which is the
UG2 case, and uninformative when the payload dominates the section.

### 7.5 Threshold sourcing status, checked 2026-08-14

| Threshold | Value | Source | Status |
|---|---|---|---|
| Liberation floor | 0.50 | Recovery of composite particles drops considerably below ~50% surface exposure, further below ~25% (911 Metallurgist, "Grinding for Liberation and Flotation"). Olympic Dam grinds to P80 30um specifically to hit a liberation target (AusIMM 2024 Mill Operators' Conference). | SOURCED |
| Payload floor | 0.003 | Answers "is there enough payload in this field to say anything at all". Needs a real per-deposit assay reference. | UNSOURCED - placeholder |
| Reject ceiling | 0.60 | Pyrrhotite rejection is established practice, but the fraction at which a plant acts is deposit- and smelter-contract-specific. | UNSOURCED - placeholder |
| Deleterious ceiling | 0.05 | Talc is naturally floatable and drives depressant demand in PGM flotation (REEFPRINT's own reason for including the phase), but no source gives a numeric fraction threshold. | UNSOURCED - placeholder |

Honest framing for judges: one threshold is literature-backed and three are
placeholders awaiting plant-specific numbers. The structure of the decision is
defensible; the exact trip points are not yet, and we would rather say so than
claim four sourced numbers we do not have. The previous goethite threshold has
been removed entirely - it was a holdover from the original iron-ore scaffold
and applied to no mineral in any dataset we now use.

## 8. Limitations

*Named honestly and first. The gap between the datasets' ore bodies and South
African ores. Single-modality optical. Dataset size.*

## 9. Open questions

- ~~LumenStone access~~ — **RESOLVED 2026-08-14.** Host is up, all subsets
  download without registration, usage agreement permits research use with
  citation. See DATA-SOURCES.md Section 1.
- ~~Can Mintek assign a P3 technical mentor?~~ — **ANSWERED by the acceptance
  letter:** teams needing a Mintek mentor must say so explicitly in the 30 Aug
  submission. Still open whether Mintek will share polished-section imagery —
  ask in the same message.
- What exactly does the Mintek T&Cs / IP Agreement assign to MOTT?
- Does the 30 Aug abstract commit us to the full REEFPRINT phase set, or can it
  be re-scoped to the phases we can actually evidence? Bears directly on whether
  the accuracy report is defensible on 1 October.

## 10. References

*Full citations. See DATA-SOURCES.md for working links.*
