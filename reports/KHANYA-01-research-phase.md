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

*The differentiator. Thresholds in src/advisor.py, checked 2026-08-04:*

| Threshold | Value | Source | Status |
|---|---|---|---|
| Liberation floor | 0.50 | Recovery of composite particles drops considerably below ~50% surface exposure, further below ~25% (911 Metallurgist, "Grinding for Liberation and Flotation"). Olympic Dam grinds to P80 30um specifically to hit a liberation target (AusIMM 2024 Mill Operators' Conference). | SOURCED |
| Gangue dilution | 0.40 | No universal constant exists - economically this is the cutoff-grade concept (deposit- and commodity-price-specific: Wikipedia "Cutoff grade"). Current value is a demo placeholder, not derived from real economics. | UNSOURCED - placeholder |
| Goethite penalty | 0.15 | Goethite's practical downsides (needs agglomeration, dehydrates during sintering) are documented (IspatGuru, "The Sintering Process of Iron Ore Fines"), but no source gives a numeric threshold - plant-specific. Also: goethite doesn't appear in the MUMDMC igneous-silicate class set we're actually training on; this threshold is a holdover from the original iron-ore-themed scaffold and needs re-deriving for whichever mineral set the final submission uses. | UNSOURCED - wrong mineral set |

Honest framing for judges: one threshold is genuinely literature-backed, one is
an economics formula we haven't wired up, one doesn't apply to our current data
at all. Better to say this plainly than claim three sourced numbers we don't have.

## 8. Limitations

*Named honestly and first. The gap between the datasets' ore bodies and South
African ores. Single-modality optical. Dataset size.*

## 9. Open questions

- LumenStone access — awaiting reply from A. Khvostikov (ORCID 0000-0002-4217-7141).
- Can Mintek share polished-section imagery, or assign a P3 technical mentor?
- What exactly does the Mintek T&Cs / IP Agreement assign to MOTT?

## 10. References

*Full citations. See DATA-SOURCES.md for working links.*
