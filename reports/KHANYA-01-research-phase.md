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

> **DRAFT SECTIONS — must be re-voiced before submission.** Sections 1, 2, 3, 4,
> 6, 8 and 10 were drafted from our own results, decisions and source list, but
> they have not yet been rewritten in our own voice. Mintek runs explicit
> AI-generation checks and originality is scored, so treat re-voicing as
> mandatory, not cosmetic. Claims marked **[CITE]** still need a reference
> attached; do not submit with any [CITE] marker remaining.

---

## 1. Problem statement

Problem 3 asks for real-time mineralogical characterisation from reflected-light
optical microscopy. Stated in our own terms: given a photomicrograph of a
polished ore section, identify which mineral phases are present and where, and
turn that into information a concentrator can act on while the ore is still being
processed.

The brief sets three deliverables, and we treat them as a floor rather than a
target:

1. a trained model identifying **at least three mineral phases**;
2. an **accuracy report** for that model;
3. a demonstration of **operational feedback integration**.

Our reading is that the third deliverable is where the problem actually lives.
Segmenting minerals in a polished section is a solved problem in the sense that
published benchmarks exist and are strong (section 4). What is not solved, and
what a concentrator would actually pay for, is the step from a labelled image to
a defensible instruction: grind finer, change reagent dosage, divert this feed, or
leave the circuit alone. We have therefore built the full chain and, critically,
measured how much of the segmentation model's error survives into the
recommendation. That measurement — not the segmentation score — is our central
contribution, and section 5.0.4 reports a case where improving segmentation
accuracy improved decisions not at all.

We also read "real-time" as a constraint on cost and turnaround rather than on
milliseconds. The relevant comparison is not a faster GPU; it is an optical
microscope and a trained model against an automated mineralogy instrument whose
capital cost and sample turnaround put it outside routine plant use (section 3).

## 2. Why this matters to the minerals sector

Poor mineralogical information is expensive in three distinct ways, and they
compound.

**Milling energy.** Comminution is the dominant energy consumer in a
concentrator, and grinding finer than necessary spends that energy for no
metallurgical return **[CITE — need a figure for comminution as a share of
concentrator energy]**. The decision of how fine to grind is a liberation
decision: grind until the valuable phase is sufficiently exposed to be recovered,
and no further. Without per-feed mineralogical information that decision is made
on a standing setpoint, which is by construction correct only for the average
ore. South African reef ores are not uniform — UG2 chromitite grades vary within
a single stope — so a standing setpoint is wrong in both directions much of the
time.

**Recovery losses to tailings.** Under-grinding is the opposite failure. A
valuable grain locked inside a composite particle presents little exposed
surface, is not collected by the flotation reagent, and reports to tailings.
Recovery of composite particles falls considerably once surface exposure drops
below roughly 50%, and further below 25% (911 Metallurgist, "Grinding for
Liberation and Flotation"). Olympic Dam runs a two-stage grind — P80 75 µm
followed by a regrind to P80 30 µm — specifically to hit a liberation target
(AusIMM 2024 Mill Operators' Conference), which shows liberation is treated as a
real operating lever and not a laboratory abstraction. Metal lost to tailings is
lost permanently; unlike a grade penalty it cannot be recovered downstream.

**Turnaround time.** Conventional automated mineralogy — QEMSCAN and comparable
SEM-based systems — produces excellent quantitative mineralogy, but as a
laboratory service with sample preparation, queueing and reporting in between
**[CITE — need a turnaround figure]**. By the time the answer arrives the ore
that generated it has been processed. Information that cannot reach the circuit
within the residence time of the feed cannot change the outcome for that feed. A
measurement that is less precise but available immediately can be worth more
operationally than a precise one that is available next week.

The economic case for this project rests on the third point. We are not proposing
to beat SEM-based mineralogy on accuracy. We are proposing that a cheap optical
measurement, delivered fast enough to act on and honest about its own
uncertainty, changes decisions that a slow precise measurement cannot reach.

## 3. The optical argument

Core claim: SEM/BSE cannot reliably separate hematite from magnetite because
their average atomic numbers are near-identical. Reflected-light optical
microscopy can, on reflectance and colour.

This matters beyond the specific mineral pair, because it establishes that
optical microscopy is not merely the cheap approximation of electron microscopy —
there are discriminations it makes *better*. Backscattered-electron contrast is a
function of mean atomic number, so phases that differ in structure or oxidation
state but not in composition are poorly separated by it. Reflected light responds
to different physics: reflectance, colour and anisotropy under polarised light,
which track crystal structure and bonding rather than atomic mass alone.

The cost argument follows from this. An automated mineralogy instrument is a
capital purchase in the millions of rand plus a service contract and a trained
operator **[CITE — need an indicative instrument cost]**. A reflected-light
microscope with a digital camera is orders of magnitude cheaper, is already
present in most metallurgical laboratories, and requires the same polished
section that SEM work already needs. The marginal cost of adding a trained model
to an existing microscope is close to zero, which means the technique is
deployable at a scale that instrument-based mineralogy is not — at every plant
rather than at one central laboratory.

Our own results add a caveat to this argument that we would rather state than have
a judge find. Reflected light discriminates well between phases that differ in
reflectance and colour, and poorly between phases that do not. Our model fails
completely on magnetite, and section 5.0.2 shows why: magnetite is dark and low in
reflectance, so it is confused with the dark mounting resin rather than with
another mineral. The optical argument is real but it is not unconditional, and the
honest form of it names the discriminations optical microscopy cannot make.

## 4. State of the art

Deep learning on polished-section reflected-light imagery is an established
research area with a consistent recent direction: encoder-decoder semantic
segmentation architectures, transferred from general computer vision, applied to
mineral phase maps.

DeepLabv3+ has been applied to opaque/non-opaque segmentation of iron ore
sections (Filippo et al., *Minerals Engineering* 170, 2021), which is also the
source of the FeM dataset we used for our earliest pipeline check. More recent
work pushes toward finer-grained and instance-level tasks: an improved YOLOv8n
for fine-grained mineral segmentation (*Minerals Engineering*, 2025) and
segmentation-and-labelling workflows for polished sections (*Mining, Metallurgy &
Exploration*, 2025). Res-UNet ensembles have been reported for mineral optical
microscopy (*Minerals* 14(12), 1281). The Moscow State University group behind the
LumenStone dataset has published both the dataset and a toolkit, `petroscope`,
containing their class definitions, a ResUNet baseline and dataset-wide IoU
metrics.

Two points from that literature shaped our design directly. First, the
`petroscope` authors state that mineral class imbalance is severe and that loss
weighting and class weighting do **not** resolve it, and they use patch-based
probability-map sampling instead. We took this seriously, implemented balanced
patch sampling, and confirmed both that it helps the classes it can help and that
it does not rescue a class failing for a different reason (sections 5.0.2, 5.0.4).
Second, the published benchmarks are all reported as segmentation metrics —
per-class or mean IoU — and we found no work measuring whether that metric
predicts the quality of a downstream operating decision. That gap is where we
positioned our contribution.

Benchmarks we are measured against:

| Work | Dataset | Metric |
|---|---|---|
| PSPNet + ResNet18 | LumenStone S1+S2 | mean IoU 0.88, PA 0.96 |
| ResUNet (petroscope) | LumenStone S1v1 | mean IoU 0.8373 |

**Which number we target, stated plainly.** We are not targeting mean IoU 0.88,
and we do not claim to approach it. Our best whole-section result is mean IoU
0.5725 on LumenStone S2 (section 5.0.2), achieved with 12 CPU epochs and no GPU.
The published benchmarks use substantially more compute and the patch-based
sampling infrastructure their authors developed for the purpose. Claiming
benchmark parity would be false and trivially checkable.

What we target instead is the decision. Our claim is that the recommendation
error rate of the full chain — measured as the proportion of held-out sections
where the advisor's instruction changes between ground-truth and predicted masks —
is a more honest measure of operational value than IoU, and that it can be driven
down by means other than raising IoU. Section 5.0.5 supports this: repairing
particle topology took the flip rate from 6 sections in 12 to 2, while IoU gains
alone took it from 6 to 6.

### 4.1 Which benchmarks apply to this problem, and which do not

Worth stating explicitly, because it is a fair question and the intuitive answer
is wrong.

**The standard computer-vision benchmarks do not apply.** ImageNet, COCO, PASCAL
VOC, KITTI, Cityscapes, Open Images, ADE20K, YouTube-8M and Visual Genome are all
**natural-image** benchmarks — photographs of objects, people, street scenes and
video. Evaluating this model against any of them would produce a number with no
meaning, for three independent reasons:

1. **Disjoint label spaces.** Our classes are chalcopyrite, pyrrhotite,
   pentlandite, magnetite and mounting resin. None of them exists in any of those
   benchmarks, and none of their classes exists in our data. There is nothing to
   score against.
2. **Different imaging physics.** A natural photograph records scene radiance
   under uncontrolled illumination. A reflected-light micrograph records mineral
   **reflectance** under calibrated illumination at fixed magnification, where
   absolute grey level and colour are the diagnostic signal. This is why we
   deliberately apply no colour jitter in augmentation — a transformation that is
   harmless on Cityscapes destroys the information our task depends on.
3. **Different failure economics.** Those benchmarks score whether a pixel is
   labelled correctly. Nothing in them measures whether an error changes a
   downstream decision, which is the question this project exists to answer.

**One genuine connection.** ImageNet is already in this pipeline: the ResNet50
backbone is ImageNet-pretrained before fine-tuning on 37 mineral images.
Low-level features — edges, textures, boundaries — transfer usefully across
domains, and with a dataset this small that pretraining is doing substantial
work. So ImageNet is a component, not a yardstick.

**A second, weaker connection.** Our metric protocol — per-class IoU, mean IoU
and pixel accuracy — comes from the PASCAL VOC and Cityscapes segmentation
lineage. We inherit the measurement convention while rejecting the datasets, and
that is the correct relationship.

**The benchmarks that do apply** are the published results on the same imagery:

| Work | Dataset | Result | Comparability to ours |
|---|---|---|---|
| PSPNet + ResNet18 | LumenStone **S1+S2** combined | mean IoU 0.88, PA 0.96 | Indicative. Reported jointly across two subsets, so not directly comparable to our S2-only figure |
| ResUNet (petroscope) | LumenStone **S1 v1** | mean IoU 0.8373 | **Closest available.** Same subset we are now training on, though we use v2 (more images, possibly revised annotations) and carve our own validation set from train |
| DeepLabv3+ (Filippo et al. 2021) | FeM, binary ore/resin | — | Same architecture and task as our earliest run (our mean IoU 0.872) |

This matters for an honest reading of our position. Until now we had trained only
on S2, while the strongest published numbers are reported on S1 or on S1+S2
jointly — so we had **no directly comparable figure at all**, and our 0.5725 was
being informally compared against 0.88 measured on different data. The S1 run
now in progress produces the first number that sits alongside the ResUNet 0.8373
on the same subset. We expect to remain below it, and the reasons are stated in
section 8: twelve CPU epochs against their full training budget.

**A benchmark that does not exist.** There is no established benchmark for
*decision quality* from mineralogical images — no dataset pairs micrographs with
the operating decision a metallurgist would take. That absence is why we
constructed the recommendation-flip measurement in section 5.0.3 rather than
adopting one, and it is the gap our contribution sits in.

## 5. Data

Our primary dataset is **LumenStone S2 v2** — 37 training and 12 test
reflected-light images of polished ore sections at 3396×2547 px, with
pixel-level masks for five classes: chalcopyrite, magnetite, pyrrhotite,
pentlandite, and resin background. The split is the authors' own. Access was
blocked when we began (the host returned HTTP 500 on 2026-08-04) and cleared on
2026-08-14; the data now downloads without registration under a usage agreement
permitting research use with citation.

**Why S2 specifically, and where the analogy stops.** S2 is drawn from the
Norilsk Group — layered ultramafic intrusions hosting magmatic Ni-Cu-PGE
sulphide. Pyrrhotite, pentlandite and chalcopyrite are the same base-metal
sulphide assemblage that carries the PGM payload in Bushveld UG2 and Merensky
reef ores, and both are layered ultramafic-mafic intrusions rather than the
hydrothermal or sedimentary settings covered by every other public dataset we
located. The transfer argument is therefore about ore genesis and mineral
assemblage, not about convenience.

It is important to state where that analogy fails, because a reviewer will ask.
Norilsk ore is *massive* sulphide: across S2's training images the base-metal
sulphides occupy 62.8% of pixels, against under 1 vol% in UG2. **S2 is an
analogue for the assemblage and its optical appearance, not for its abundance.**
Any claim we make from S2 transfers as "these phases are separable in reflected
light at these accuracies", and explicitly not as "we can detect sub-1% BMS in
UG2". That second claim is a different and harder problem, and our magnetite
result (section 5.0.2) is direct evidence of how hard rare-phase detection is.

Two secondary datasets were used and are reported for completeness rather than as
results. **FeM** (Zenodo 5014700, CC-BY-4.0) provided an early pipeline check on
binary ore/resin segmentation; it has only two classes and does not satisfy the
≥3 phase requirement. **MUMDMC2025** was used as a development proxy while
LumenStone was inaccessible; the only publicly obtainable version contains 8
physical specimens, too few to hold any out for testing, so no accuracy claim is
made from it.

**No public dataset covering the full REEFPRINT phase set was found.** Four of
its five target phases — chromite, orthopyroxene, plagioclase, talc/serpentine —
still have no imagery available to us. We searched specifically for Bushveld, UG2,
Merensky and Platreef material and found published papers rather than datasets.
LITHOS-DATASET (211,604 patches, 25 classes) was evaluated and ruled out: it is a
sedimentary and carbonate petrography dataset, the wrong rock type entirely. Full
licence status and reasoning for every candidate is recorded in `DATA-SOURCES.md`.

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

### 5.0.5 Repairing particle topology — the result to lead with

Section 5.0.4 concluded that per-class accuracy was the wrong target and that
particle topology was the binding constraint. Acting on that, `src/modal.py`
gained a refinement stage applied identically to ground-truth and predicted
masks (the estimator is what changed, so both sides must use it):

- **morphological opening** — isolated misclassified pixels were inventing tiny
  particles that scored as perfectly liberated and inflated the index
- **binary hole filling** — a phase predicted as background *inside* a grain
  punches a hole that splits one particle into two. This directly repairs a
  known failure: magnetite is predicted as background 92.3% of the time, so
  every magnetite inclusion was fragmenting its host grain
- **marker-controlled watershed** on the Euclidean distance transform — the
  centre of a grain lies further from background than the neck joining two
  touching grains, so distance-transform peaks seed one marker per grain and the
  watershed line falls on the neck

| Setup | Flips | Liberation corr. | MAE | Unsafe "continue" |
|---|---|---|---|---|
| resize + raw components | 6/12 (50%) | +0.128 | 38.7% | 2 |
| resize + refined | 4/12 (33%) | +0.709 | 16.4% | 1 |
| patch + raw components | 6/12 (50%) | -0.079 | 46.7% | 1 |
| **patch + refined** | **2/12 (17%)** | **+0.947** | **8.9%** | **0** |

**The two interventions are complementary.** Better segmentation alone changed
nothing; better topology alone helped substantially; together they reduce
recommendation error to 2 sections in 12 and eliminate every flip in the
expensive direction. Improved per-class accuracy was not worthless — it was
unusable until topology was accurate enough to exploit it. This is the central
methodological result of the project: **in image-based mineralogy, segmentation
quality and particle-topology fidelity are separate axes, and operational value
requires both.**

**What still fails, and it is instructive.** Both surviving flips sit on the
liberation threshold: test_04 truth 40% against predicted 74%, test_05 truth 32%
against predicted 52%, with the floor at 50%. test_05 clears it by two points.
The residual failure is therefore *threshold brittleness* rather than gross
measurement error — within roughly one mean-absolute-error of the trip point, the
recommendation is effectively a coin toss. The correct response is a declared
uncertainty band: where the liberation estimate falls within the estimator's own
error margin of a threshold, the honest output is "marginal — verify" rather than
a confident instruction.

### 5.0.6 Robustness: the model is a colorimeter, not a texture recogniser

Every image in this project came from one laboratory, one microscope (Carl Zeiss
AxioScope 40) and one camera (Canon Powershot G10). Nothing in the numbers above
says whether the model survives a different rig, which is the first question that
matters for deployment. `src/robustness.py` applies controlled photometric
perturbations to the held-out sections and re-measures IoU with the ground-truth
masks untouched, so any drop is pure fragility rather than changed mineralogy.

| Perturbation | Mean IoU | Change | Pixel accuracy |
|---|---|---|---|
| baseline | 0.5448 | — | 0.879 |
| soft focus, 1.5 px Gaussian | 0.5451 | **+0.0004** | 0.879 |
| sensor noise, sigma 8 | 0.5441 | -0.0007 | 0.878 |
| JPEG quality 40 | 0.5309 | -0.014 | 0.870 |
| contrast x0.70 | 0.5151 | -0.030 | 0.863 |
| exposure -30% | 0.4427 | -0.102 | 0.796 |
| exposure +30% | 0.3017 | -0.243 | 0.413 |
| white balance, warm | 0.1772 | **-0.368** | 0.263 |
| white balance, cool | **0.1531** | **-0.392** | 0.317 |

Source: `reports/robustness_s2_resize.json`.

**The model is almost entirely dependent on absolute colour and brightness, and
close to indifferent to spatial detail.** Blurring, adding sensor noise, or
compressing to JPEG 40 costs essentially nothing. A 15% white-balance shift costs
**72% of performance in relative terms**, with pixel accuracy collapsing from
0.879 to 0.263.

Two conclusions follow, and they point in opposite directions.

**This confirms the optical premise of section 3.** We argued that reflected
light discriminates minerals on reflectance and colour rather than on
composition-dependent contrast. The model has evidently learned exactly that: it
is using photometry, not texture. The argument is no longer an assertion about
physics, it is a measured property of the trained system.

**It is also the single largest deployment risk in the project.** A different
illuminant, a different colour-temperature setting, or an operator adjusting a
camera by eye, and performance falls to a level indistinguishable from noise. Any
claim that this transfers to another laboratory is unsupported without
illumination control.

Note the asymmetry between over- and under-exposure: +30% costs more than twice
what -30% costs, because highlight saturation destroys reflectance information
irreversibly while underexposure merely compresses it. Practical implication: an
operator should err toward under-exposing.

**The remedy is domain-standard, which is why this is a manageable limitation
rather than a fatal one.** Quantitative reflectance microscopy already requires
calibrated illumination — reflectance is measured against known standards
precisely because absolute grey level is the quantity of interest. Our
requirement is therefore the one the discipline already imposes, and the honest
framing is that the system needs a calibrated illumination reference, not that it
is unusually brittle.

**Scope of this experiment, stated so it is not overclaimed.** These are
synthetic perturbations of the same underlying photographs. They probe exposure,
white balance, focus and sensor response. They do **not** reproduce a genuinely
different optical train, objective, or section preparation. LumenStone V1 — the
same samples imaged under varying real conditions, built by the dataset authors
for colour-adaptation research — is the proper test and remains unused.

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

The pipeline has four stages. Each is a separate source of error, and we treat
them separately because — as section 5.0.4 shows — reducing error in one does not
necessarily reduce error at the output.

```
micrograph (3396x2547, reflected light, polished section)
   -> SEGMENTATION        DeepLabv3+ResNet50, 5 classes
   -> MODAL MINERALOGY    area fractions as a proportion of ore
   -> LIBERATION          particle composition from repaired topology
   -> RECOMMENDATION      role-based advisor, with uncertainty band
```

**Stage 1, segmentation.** DeepLabv3+ResNet50, ImageNet-pretrained, five classes.
Two training regimes were built and kept separate so they remain comparable: a
resize baseline, and patch-based sampling at native resolution with patch centres
drawn to balance class exposure. Uncertainty here is per-class and strongly
non-uniform: pyrrhotite reaches IoU 0.87 while magnetite reaches 0.00.

**Stage 2, modal mineralogy.** Phase area fractions are computed as a proportion
of **ore** area, excluding mounting resin. Including resin would make every
reported fraction a function of how densely the section happened to be mounted
rather than of the ore. Resin coverage is reported separately as a data-quality
signal, and below 5% ore in the field the advisor declines to recommend rather
than compute fractions from too few pixels. Uncertainty here is inherited from
stage 1 and is asymmetric: a phase misassigned to background does not merely
vanish from the numerator, it shrinks the denominator too.

**Stage 3, liberation.** Grains in a polished section are separated by resin, so
connected components of non-resin pixels are particles. For each particle we
measure the fraction that is payload phase; a particle counts as liberated when
that fraction reaches 50%, and the reported index is the mass-weighted share of
payload area sitting in liberated particles. Raw connected components proved far
too brittle for this (section 5.0.4), so the mask is first repaired: morphological
opening removes speckle, hole filling repairs grains fragmented by interior
misclassification, and marker-controlled watershed separates touching grains.
Uncertainty here is **topological** rather than proportional — it does not scale
smoothly with pixel error, because a single bridging pixel merges two particles
and changes their measured composition discontinuously.

**Stage 4, recommendation.** The advisor reasons over metallurgical **roles** —
payload, reject, oxide, gangue, deleterious — rather than mineral names, with the
mineral-to-role mapping held separately. Changing ore body therefore changes a
mapping, not the decision logic, which is what allows the same system to serve
LumenStone S2 today and the REEFPRINT phase set if Bushveld data becomes
available. Uncertainty here is **threshold brittleness**: near a trip point a
small measurement error flips the output, so liberation estimates falling within
the estimator's own measured error of the 50% floor return "marginal — verify"
rather than a confident instruction.

**Why this decomposition matters.** Our headline methodological finding is that
stage 1 and stage 3 errors are close to independent. Improving segmentation from
mean IoU 0.545 to 0.5725 changed the recommendation error rate not at all, while
repairing stage 3 topology — with no retraining whatsoever — took it from 6
sections in 12 to 4, and the two together reached 2 in 12. A pipeline of this
shape cannot be tuned by optimising its first stage alone.

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

Named first and without hedging. Each of these is a limitation we found
ourselves, and each is evidenced elsewhere in this report.

**1. The model fails completely on one of its five phases.** Magnetite scores IoU
0.000 and is never predicted anywhere in the test set — zero pixels against
33,469 in ground truth. It is absorbed into the resin background 92.3% of the
time, which is consistent with its low reflectance: it is optically closer to dark
mounting medium than to the bright sulphides. Native-resolution patch sampling and
a region-based Dice loss were both tried and neither moved it, because neither
addresses a reflectance ambiguity. We therefore present this as a **four-phase
result with a diagnosed fifth-phase failure**, which still meets the brief's
three-phase floor.

**2. The ore body is an assemblage analogue, not an abundance analogue.** S2 is
Norilsk massive sulphide at 62.8% BMS by area; UG2 is under 1 vol%. Our results
support claims about optical separability of this mineral assemblage and do not
support claims about detecting sub-1% phases in Bushveld ore.

**3. Four of the five REEFPRINT target phases have no data at all.** Chromite,
orthopyroxene, plagioclase and talc/serpentine were never trained on. The
role-based advisor is designed so they drop in without changing decision logic,
but that is an architectural provision, not a result.

**4. Liberation is measured from 2D sections and is an upper bound.** A section
plane can cut the free-standing rim of a particle whose core is locked, so
apparent liberation from sections is biased **high** relative to true volumetric
liberation. Plant practice applies a stereological correction; we do not. The bias
runs in the safe direction for "grind finer" and in the unsafe direction for
"continue at setpoint" — which is precisely the recommendation we can least afford
to get wrong.

**5. The validation set is too small to select on.** Six images, with a
composition materially different from the test set (45.8% versus 25.0%
background). Pentlandite scored 0.026 on validation and 0.485 on test, so
checkpoint selection by best validation mIoU is close to arbitrary. Grouped
cross-validation over the 37 training sections would be the sound protocol and we
did not have the compute budget for it.

**6. Three of four advisor thresholds are unsourced placeholders.** Only the 50%
liberation floor is literature-backed. The payload floor, reject ceiling and
deleterious ceiling are plausible but not derived from plant economics or assay
data, and should be presented as configurable plant parameters rather than as
findings.

**7. Single modality, and a very small dataset.** Reflected light only, no
cross-polarised or hyperspectral information that might separate magnetite from
resin. Forty-nine images in total, from one deposit group, imaged on one
microscope with one camera. Nothing here demonstrates robustness to a different
laboratory's imaging conditions, and the LumenStone V1 subset — the same samples
imaged under varying conditions, built precisely for colour-adaptation testing —
would be the right way to probe that. We did not use it.

**8. Everything was trained on CPU.** Twelve epochs, no GPU, well short of the
published benchmarks' compute. Our numbers should be read as a lower bound on what
this architecture achieves on this data, not as its ceiling.

**9. Compute constraints shaped the experiment, not just the results.** Full
sliding-window inference over 12 native-resolution sections takes over an hour on
CPU, which limited how many configurations we could evaluate end to end. We
mitigated this by caching predicted masks so policy changes re-score in seconds,
but the number of training regimes we could compare was genuinely limited by
hardware.

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

Working links for all of these are in `DATA-SOURCES.md`. **Citation formatting is
not yet consistent and several entries need volume, page or accession details
completed before submission.**

**Datasets**

1. Khvostikov, A., Korshunov, D., Sorokin, D., Krylov, A., Boguslavsky, M.
   *LumenStone dataset.* Laboratory of Mathematical Methods of Image Processing,
   Faculty of Computational Mathematics and Cybernetics, and Department of
   Geochemistry and Economics of Mineral Resources, Faculty of Geology, Lomonosov
   Moscow State University. Subset S2 v2 (released 2025-06-15), 37 train / 12
   test, five classes. Accessed 2026-08-14. Used under the stated data usage
   agreement permitting research use with citation.
2. Filippo, M. P. et al. *FeM dataset — reflected-light microscopy of itabiritic
   iron ore with binary ore/resin masks.* Zenodo record 5014700, CC-BY-4.0.
3. *MUMDMC2025 DataSet.* figshare 29483204 (public sample). Paper: *Scientific
   Data* (2025), DOI 10.1038/s41597-025-05879-9. Used as a development proxy
   only; no accuracy claim is made from it.
4. Ruiz Puentes, P. et al. *LITHOS-DATASET.* Kaggle; companion to "Towards
   Automated Petrography", NeurIPS 2025 Datasets and Benchmarks, arXiv:2511.00328.
   CC BY-NC-SA 4.0. **Evaluated and ruled out** — sedimentary/carbonate
   petrography, wrong rock type.

**Methods and benchmarks**

5. Filippo, M. P. et al. (2021) DeepLabv3+ segmentation of opaque and non-opaque
   phases in reflected-light microscopy of iron ore. *Minerals Engineering* 170,
   107007.
6. Improved YOLOv8n for fine-grained mineral segmentation. *Minerals Engineering*
   (2025). **[CITE — authors, volume, article number]**
7. Segmentation and labelling of polished sections. *Mining, Metallurgy &
   Exploration* (2025), DOI 10.1007/s42461-025-01205-4.
8. Res-UNet ensemble for mineral optical microscopy. *Minerals* 14(12), 1281,
   DOI 10.3390/min14121281.
9. Korshunov, D. et al. From visual diagnostics to deep learning. *Mining Science
   and Technology*. **[CITE — volume, issue, pages]**
10. Khvostikov, A. et al. *petroscope* — Python toolkit for microscopic geological
    image analysis. https://github.com/xubiker/petroscope. Source of the
    LumenStone class codebook used in our label mapping, the ResUNet baseline, and
    the statement that class weighting does not resolve mineral class imbalance.

**Metallurgical sources**

11. 911 Metallurgist. *Grinding for Liberation and Flotation.* Source for the
    liberation floor: composite-particle recovery falls considerably below ~50%
    surface exposure and further below ~25%.
12. AusIMM (2024) Mill Operators' Conference — Olympic Dam two-stage grind, P80
    75 µm then regrind to P80 30 µm, to meet a liberation target. **[CITE — paper
    title and authors]**
13. IspatGuru. *The Sintering Process of Iron Ore Fines.* Consulted for goethite
    behaviour during earlier iron-ore-themed scoping; **no longer cited in the
    body** and retained here only to record what was reviewed.

**Still required before submission**

- A figure for comminution as a share of concentrator energy consumption
  (section 2).
- A turnaround figure for QEMSCAN or comparable SEM-based automated mineralogy
  (section 2).
- An indicative capital cost for an automated mineralogy instrument (section 3).
- Sources, or explicit reclassification as configurable plant parameters, for the
  payload floor, reject ceiling and deleterious ceiling (section 7.5).
- Confirmation of how Mintek's terms and IP agreement treat externally licensed
  datasets used in a submission.
