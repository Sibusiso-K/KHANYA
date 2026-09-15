# CLAUDE.md — REEFPRINT, otherwise known as KHANYA

Project constitution. Claude Code reads this at the start of every session. Keep it current; it outranks anything in `docs/`.

**Read [`WORKBOARD.md`](WORKBOARD.md) next — it is the shared board Lethabo and Sibusiso both read, and its §0 lists the corrections that beat every other document including parts of this one.** This file says what is *true* and what the *rules* are. `CONTEXT.md` says where we are, what the single next action is, and what has already bitten us — it is the file that lets a fresh session or a different machine pick up cold. Then [`docs/BUILDLOG.md`](docs/BUILDLOG.md) for what was tried and what failed, and [`docs/05-toolchain.md`](docs/05-toolchain.md) for what to install.

**Maintenance rule — these four are updated as work proceeds, not at the end.** Any session that changes the state updates `CONTEXT.md` (§3 next action, §5 if something bit you) and appends to `docs/BUILDLOG.md`. Any session that adds a dependency updates `SBOM.md` **and** `docs/05-toolchain.md` in the same commit. A stale `CONTEXT.md` is worse than none, because it will be trusted.

---

## What this is

**One build, two names.** REEFPRINT is the spec, the physics and the measurement half;
KHANYA is Sibusiso's build — segmentation, modal mineralogy, liberation, conformal
calibration, the offline dashboard. They are two halves of one system, not two projects.
Both names are correct and neither is deprecated
([ADR-0003](docs/04-decisions/0003-one-build-two-names-reefprint-and-khanya.md)): give both
on first mention in anything external, then REEFPRINT alone. **No code is renamed and no
histories are merged** — REEFPRINT's history lives on the `reefprint` branch of the KHANYA
repository, unmerged, because two clean parallel histories are the originality defence
(rule 8).

**REEFPRINT is a computational ore microscope.** It identifies ore minerals and quantifies their deportment by **multispectral quantitative reflectance plus full linear Stokes polarimetry**, with calibrated uncertainty and an explicit refusal mechanism.

**It is software, evaluated on public data. No instrument is built — see [ADR-0002](docs/04-decisions/0002-software-only-no-instrument-is-built.md).** The ~R5,000 rig is a costed design presented as a design. Never imply it exists. The 0.2–1.6 µm/pixel figure is a design target, not a measurement, and nothing may be derived from it.

Built for the Mintek-SCi Grad Hackathon 2026, challenge: *Computer Vision for Real-Time Mineralogical Characterisation*. Team Sonar — three members across three institutions (see §Single technical decision-maker). Final: 1 October 2026, 13:00 submission, 10-minute presentation. **Abstract due 30 August 2026, one page** — `docs/06-abstract.md`.

## What we are judged on — the brief, verbatim

Kept here because this file outranks everything else and a requirement stated anywhere else can go
stale without anyone noticing. It did: `docs/08-handover.md` §4 and `WORKBOARD.md` §2 carried two
copies that disagreed. **The ledger, [`docs/09-brief-compliance.md`](docs/09-brief-compliance.md),
is the single place where each of these maps to evidence — a path or a test name, never prose.**

> Identify **at least three distinct mineral phases** from provided image datasets · an
> **accuracy report** · a **demonstration of how the model's output can be used to adjust plant
> parameters** · real-time · integrates with existing sorting or flotation controls.

**Judged on:** Innovation · Feasibility · Impact · Technical Execution · Presentation Clarity.

Winners are announced only after MOTT's IP assessment on top-ranked entries, and **creators receive
invention credits** — so attributable authorship is part of winning, which is why ADR-0003 keeps two
clean unmerged histories and why we never ship someone else's trained weights.

**Three consequences that decide arguments.** (1) *The brief never asks for a state-of-the-art mIoU.*
Being close enough that the number is not a liability, then spending the remaining effort on the
five criteria, beats chasing +0.02. (2) *Three of the five criteria are not accuracy at all* —
Feasibility, Impact and Presentation Clarity are won by the refusal path, the offline demo and the
ten minutes. (3) *Mintek made UG2 commercially viable.* We are pitching a UG2 story to the people
who wrote the book, so one overclaim costs more here than anywhere else.

## What the literature says drives accuracy here

Ore-microscopy segmentation is a small, well-published field, and it has already answered several
questions we were about to answer by guessing. Each row is a **factor**, not a suggestion; each
carries its source. Full working and per-experiment status:
[`docs/09-brief-compliance.md`](docs/09-brief-compliance.md) §3.

| Factor | What the literature says | Where we stand |
|---|---|---|
| **Class-balanced patch sampling** | Sampling patch centres class-uniformly from probability maps is the standard fix for mineral class imbalance (Korshunov 2025; petroscope README) | ✅ done — `patches.py`, ~11× magnetite oversampling |
| **Colour normalisation *before* augmentation** | A Colour Correction Matrix (affine in LAB, CIEDE2000 loss) maps a distorted image to a reference colour space; brightness/colour augmentation is applied *on top* (Korshunov 2025) | ❌ neither. Our measured fragility: a 15% white-balance shift costs **0.39 mIoU** |
| **Polarisation as extra input channels** | XPL registered to PPL and fed to the network as additional channels improves segmentation — *from the dataset's own authors* (Korshunov 2025) | 🟡 this is the REEFPRINT thesis, taken further (full per-pixel Stokes, not two states) |
| **Registration by SIFT + RANSAC affine** | The published method for aligning rotated/XPL frames (Korshunov 2025). `skimage.feature.SIFT` + `skimage.measure.ransac`, BSD-3, already a dependency | ❌ we use a bespoke correlation grid search that `experiments/010` proved **non-reproducible run to run** |
| **Ensembling** | A weighted-voting Res-UNet ensemble beats every single member, and beats DeepLabV3 and PSPNet (Jiang 2024) | ❌ and `trust/ensemble` does not exist despite the repo map below |
| **Loss for rare classes** | Dice **+ Focal** (Jiang 2024). Dice alone is unstable while predictions are diffuse | 🟡 CE and CE+Dice tried; **Focal untried** |
| **Patch size and budget** | 256–384 px at ×50 (Korshunov 2025); ~3 h on one A6000 is the published compute budget | 🟡 we use 512; our own 512→2,560-patch step **was read as** mIoU 0.33 → 0.71 — ⚠️ **now in question, 2026-09-15**: the 0.3295 side of this claim is the *same* `benchmark_s1_patches.json` that turned out to be a stale cache (`ca2e02f`), and the pattern has now recurred twice elsewhere in this file (magnetite, tennantite) as "a number nobody checked which checkpoint it actually scored." Whether 0.3295 was ever an honest, contemporaneous measurement of the 512-patch checkpoint, or was already stale when first read, is unverified — asked Sibusiso directly rather than assume either way |

**The comparators, so nobody re-derives them:** petroscope's ResUNet on LumenStone **S1 v1**,
7 classes — mIoU **0.8373** (0.8506 void-borders), per-class 0.7464 (galena) to 0.9628 (pyrite).
Korshunov et al. on S1+S2, 10 classes — **magnetite 0.650, the worst of their ten**, pentlandite
0.790, pyrite 0.964, PA 0.96.

> ⚠️ **Corrected 2026-09-15, twice.** First correction: "our magnetite problem is the literature's
> magnetite problem" was too generous, and Sibusiso's own forensics (issue #5) are why we know
> that now. Rebuilt against the real patches checkpoint over all 12 S2 test sections: of
> **821,587** true magnetite pixels, **0 are ever predicted as magnetite**, across **92.6
> million** test pixels — a dead output channel, not a weak score. Korshunov et al. get **0.650**
> on the same modality. Rarity alone does not explain it (S1 chalcopyrite at a similarly low train
> share still scores 0.8652), and it is not an optical limit of reflected-light imaging (someone
> else detects it) — the test-set abundance is **0.792%**, the number the model was actually
> scored on (three different abundance figures were circulating under one name before this
> correction — always name which one).
>
> **Second correction, same day**: the same S1 re-cache that fixed the stale 0.3295 benchmark
> (`ca2e02f`, khanya/main; corrected to **0.7116** plain / **0.7481** void-border, against
> published ResUNet S1v1 **0.8373 / 0.8506**) decomposed the S1 gap per class and found
> **tennantite alone is 60.8% of it** (IoU 0.3130 vs published 0.7601) — excluding tennantite the
> S1 gap is **-0.0469 across six classes**, with background/bornite/chalcopyrite effectively
> matched to published. Tennantite (3.917% of S1 train pixels) scores far worse than chalcopyrite
> (2.974%, IoU 0.8652) — rarity ruled out a second time, more cleanly, within one dataset rather
> than across two. **The class to name alongside magnetite is tennantite, and it is the larger
> effect of the two.** Both are low-reflectance-contrast phases against their neighbours
> (tennantite grey against other sulphides, magnetite dark against the mounting resin), both
> collapse, both are detected in the literature on this same modality — **the honest reading is a
> training-budget or model-capacity gap on low-reflectance-contrast phases specifically, not a
> per-class curiosity.** This is exactly what Workstream C's scaling study (J0/J1/J2) is
> positioned to test, with a falsifiable, pre-registered prediction now locked in before the run:
> `docs/11-pre-registered-morphology-sensitivity-and-scaling-predictions.md` §2.

Say the magnetite/tennantite gap with the citation — Korshunov's number is still the field's own hard class,
which is stronger than hiding a per-class zero inside a mean — but say the *size* of the gap
honestly too, now that it is measured.

> ⚠️ **Read before citing.** Korshunov et al. is CC BY 4.0 and fetchable in full. The Jiang et al.
> ensemble figures came from a search summary because MDPI returned 403, and **petroscope's
> training recipe is not in its README at all**. Anything not read from the source is **indicative,
> not citable** — the same failure mode as the Pirard 2007 abstract flagged below.

## The physics — read this before proposing anything

> **Our illumination is UNPOLARISED. No polariser sits in the illumination path**
> ([ADR-0005](docs/04-decisions/0005-unpolarised-illumination-with-a-rotating-analyser.md), 2026-09-12).
> The analyser is the only polarising element, and the polarisation we measure is *generated on
> reflection* by differential reflectance between a grain's eigen-axes: an isotropic grain returns
> unpolarised light (DOLP 0, flat through the rotation), an anisotropic one returns partially
> polarised light with DOLP equal to its bireflectance contrast. **Put a fixed polariser in the
> illumination path and this inverts** — at normal incidence an isotropic medium preserves the linear
> azimuth, so it reads DOLP 1 and `I(θ) = I₀cos²θ`, *full* modulation from a cubic mineral. The
> repository asserted the opposite in prose until 2026-09-12 while computing the correct thing; an
> external reviewer caught it. Pinned now by
> `test_an_isotropic_grain_under_a_fixed_polariser_modulates_fully`. **"Isotropic stays dark through a
> full rotation" is true of *specimen* rotation between crossed polars and false of *analyser*
> rotation — never write it about ours.**

SWIR hyperspectral mineral identification works on **molecular vibrational absorption features**. Chromite is an opaque spinel and has none, and it is **50–75 vol% of UG2 ore** — so SWIR spectroscopy on chromitite is close to a brightness meter. This is why the project pivoted. **Keep that claim narrow.** Chromite *does* have electronic (crystal-field) absorption in the VNIR, so "chromite has no absorption features" is false and must not be said; the defensible statement is about vibrational SWIR identification of an opaque spinel. The 50–75 vol% figure needs an ore-specific citation with its denominator stated — volume, mass and image-area fractions are not interchangeable.

Opaque ore minerals are identified by **quantitative specular reflectance (R%), bireflectance, and anisotropy under crossed polars** — reflected-light ore microscopy, standardised since the 1940s.

### Two rotation geometries, and they are not interchangeable

This is the trap that most threatens the week-1 gate, and it is not a naming quibble.

| Geometry | What turns | Modulation | Recovers |
|---|---|---|---|
| **Rotating analyser** | the analyser only — specimen fixed, **illumination unpolarised, no polariser in the path** (ADR-0005) | `I(θ) = (S0 + S1cos2θ + S2sin2θ)/2` — **2nd harmonic** | the full linear Stokes vector. **This is our claim.** |
| **Stage rotation under crossed polars** | the specimen, with polars fixed and crossed | `I(φ) = \|r₁−r₂\|²(1 − cos4φ)/8` — **4th harmonic** | extinction depth only. The classical observation since the 1940s. |

A 4φ signal has **no 2θ component at all**. Fitting the Stokes model to a stage rotation returns `S1 = S2 = 0` for every anisotropic grain — no exception, no NaN, a perfectly realisable answer, **every anisotropic mineral silently reported as isotropic.** The only witness is `residual_rms`, which sits at exactly `S0/(2√2)`. Proven, not asserted: `test_a_crossed_polars_stage_rotation_inverts_to_zero_anisotropy`.

Hence `RotationSeries.geometry`, which defaults to `UNKNOWN` rather than to the convenient answer, and `require_analyser_rotation()`, which must be called before any Stokes inversion.

**Consequence for the data:** published "XPL rotation sequences" — LumenStone S3 v2, MUMDMC2025 — are *expected* to be stage rotations, because that is how anisotropy has always been observed, but **this is a prior, not a measurement**. **N3's `NEITHER` verdict is WITHDRAWN**: S3 v2's frames are not registered, so every per-pixel result on that archive measured nothing (`WORKBOARD.md` §0 C1, `docs/BUILDLOG.md` session 17). **Leg (b) has never been run.** Verify registration *before* geometry, on any archive, before building on it. If a series does turn out to be a stage rotation, leg (b) needs a fourth-harmonic estimator, not the Stokes inversion, and the two must never be conflated in the talk.

*Also worth knowing:* extinction depth goes as the **square** of bireflectance contrast `a`, while analyser modulation goes as `a` — so the rotating analyser's advantage is `2/a`, and it **grows as the anisotropy weakens**. That is a real argument for the instrument, and it is strongest exactly where the base-metal sulphides live.

**Polarimetry splits the base-metal sulphides, and that is the whole point:**

| Mineral | Optics | Metallurgy |
|---|---|---|
| Pentlandite | cubic → **isotropic**, **flat** through full analyser rotation — DOLP 0, no modulation (*not* dark: at R ≈ 50% it is one of the brightest phases on the section) | principal PGE host, floats |
| Pyrrhotite | **moderate bireflectance**, anisotropic | depressed, low PGE |
| Chalcopyrite | weakly anisotropic | floats fast |
| Chromite | cubic, isotropic, R ≈ 13% | entrainment risk, smelter penalty |
| Gangue / resin | R ≈ 4.5–5% | discriminated by reflectance alone |

**The defensible claim (narrow, keep it narrow):** published automated optical mineralogy — the Castroviejo/Pirard line, CAMEVA and AMCO — classifies on *multispectral specular reflectance*. Recovering the **full linear Stokes vector per pixel** from a rotating-analyser series adds an axis that reflectance does not contain, and that axis discriminates the base-metal sulphides whose split governs PGE deportment and flotation response.

> ⚠️ **Prior-art risk, open, now narrower.** Do not say "nobody uses polarised light" — that is false and a judge may know it. **Pirard, Lebichot & Krier (2007), *Particle texture analysis using polarized light imaging and grey level intercepts*, Int. J. Mineral Processing 84:299–309** is direct prior art on polarised-light imaging in ore microscopy. 2026-08-28: the abstract (found via search indexing — ScienceDirect and an academia.edu mirror both blocked direct fetch, paywalled/403, so this is not a verified literal quote from the primary source, and the full paper is still unread) describes **plane-polarised static imaging for grain-boundary contrast, plus grey-level intercept stereology for grain-size distribution** — a single fixed polariser, no analyser rotation, no crossed polars, and no per-pixel Stokes recovery at all. That is further from our claim than the earlier "imaging under crossed polars" phrasing assumed, which strengthens the narrow claim's survival rather than threatening it — but "further based on an abstract" is not the same confidence as "read the full method section," so the full paper is still unread and still needed before week 6, at lower urgency than previously stated. A targeted search for Stokes polarimetry on sulphides returned nothing specific; that is weak support, not clearance.

## Hard constraints

- **No proprietary Mintek data.** Public sources only.
- Free-tier compute only: Kaggle (30 h/wk), Colab, Lightning AI, Modal, CHPC if granted.
- **Hardware budget is R0. Nothing is bought, nothing is built** (ADR-0002). The rig is a BOM. Any claim that needed a rig to measure it is now a citation or a flagged assumption.
- Every dependency must be **assignable to Mintek**. See licence rules below.
- Demo must run **fully offline on one laptop**. No network dependency on stage.

## Rules — non-negotiable

1. **Never invent a number.** Flag every assumption as an assumption, in the code and in the docs.
   **Enforced in code, not here:** `reefprint.quantity.Quantity` carries a `Provenance` and a
   mandatory non-empty `source`, and the provenance is **contagious** — arithmetic keeps the
   *weakest* input's provenance and accumulates every source, because contamination surfaces
   three functions from where the assumption was written. Five ranks, MEASURED → CITED →
   STIPULATED → ASSUMED → DESIGN_TARGET. `require_reportable()` is the boundary; `__float__`
   calls it, so the number cannot leave the type unchecked. A flagged assumption passes — rule
   1 permits assumptions, it requires labels. **DESIGN_TARGET never passes**, which is ADR-0002
   made mechanical: 47 px × 0.2 µm/px is 9.4 µm and 47 px × 1.6 is 75.2 µm — the same design
   target, a **factor of 8** apart. That is not a measurement with wide error bars.
2. **Split by locality, never by patch or image.** Patch-level splits void conformal exchangeability and will silently invalidate every metric. **Enforced in code, not here:** `reefprint.trust.split.split_by_locality()` is the sanctioned constructor and `require_locality_disjoint()` is the backstop for splits built by hand. Measured cost of the leak, on synthetic patches whose only signal is section identity — patch split MAE **0.0017**, honest locality split MAE **0.2119**, a factor of **126**, in the flattering direction. Honest *n* is `LocalitySplit.n_groups`: localities, not sections.
3. **Report the trivial baseline** (majority class, and metadata-only) alongside every metric. Always. **Enforced in code, not here:** `reefprint.trust.baseline.ScoredMetric` takes `baselines` as a required field with **no default**, so a bare metric is a `TypeError` rather than a slide. Uplift is measured against the *strongest* baseline, never the weakest, and `summary()` distinguishes three states — below the baseline, above it but inside the noise honest *n* resolves, and above it by more than that. A baseline may be `NotApplicable`, but only with a stated reason (rule 5's pattern); both inapplicable at once is refused. The middle state uses the same rule-of-three repair as rule 5: at a metric of exactly 0 or 1 the Wald SE is zero, which would make the middle state **unreachable** and every perfect score a clean win, however few localities produced it.
4. **Every metric carries a confidence interval sized at honest n.** At n≈100, conformal coverage SD is ~3pp — do not claim tighter than the arithmetic allows.
5. **Abstention emits a conservative default with a stated reason, never "unknown."** Abstention fires at ore transitions, which is when holding the last setpoint is the worst available action.
   **Enforced in code, not here:** a refusal is a `reefprint.trust.abstain.Abstention`, which cannot be constructed without a `ConservativeDefault` **and** a reason, rejects `"unknown"`, `"n/a"`, `"tbd"` and their neighbours by name, and has **no field for the previous value** — so holding the last setpoint is not reachable through the type, it is not merely discouraged. The default is a `Quantity`, so rule 1 is checked at the seam: a conservative default derived from a design target is refused at construction. "Conservative" has a *direction*, and the machine-checkable bug is the **inversion** — `ASSUME_HIGH` emitting the low half of its own range is a `ValueError`; how far along the safe side is domain judgement and is reported, not enforced. `audit_abstentions()` **refuses a run containing no ore-change events**, because the only number left to report would be the aggregate, and quoting the aggregate is exactly blind spot 1's error. Where the conditional rate lands on 0 or 1 — which small runs do constantly — the Wald SE is exactly zero, so the *least* informative observation would print as the *most* precise; the rule of three (Hanley & Lippman-Hand 1983) is printed there instead, or the line says it resolves nothing.
6. **No LLM computes a mineralogical or control value.** Agents route, select, orchestrate, explain.
7. **Licences:** permissive only for anything shipped. `timm` (Apache-2.0) not DINOv3 (non-transferable, no patent grant). `asyncua` (LGPL) runs on a general-purpose machine, never a sealed appliance. Hailo is an optional accelerator, never load-bearing. Maintain an SBOM.
8. **Commit early, commit often, including failures.** Finalists face originality authentication after 2 October. The commit history is the defence.
9. **The falsification test is a deliverable, not a risk.** Report the result either way.
10. **Check the published method before inventing one.** For any task with an established method in
    the reflected-light microscopy literature — registration, colour adaptation, class balancing,
    loss choice — name the published method in the ADR or buildlog entry and say why we are or are
    not using it. A bespoke alternative is allowed; an *unexamined* one is not. Measured cost of
    skipping this: a bespoke correlation search that turned out not to be reproducible run to run
    (`experiments/010`), where SIFT+RANSAC was the published answer and `scikit-image` already
    shipped it as a dependency. See "What the literature says drives accuracy here" above.

## The falsification test — run this first

> **H₀: after controlling for Cr₂O₃ and pyroxene fraction, texture carries no additional predictive signal.**

Nested model comparison, grouped by locality, CIs at honest n. If H₀ cannot be rejected, say so publicly and pivot to the oxidation index, which does not depend on the residual.

## Repo layout

```
reefprint/
├── CLAUDE.md                    ← this file. Constitution.
├── CONTEXT.md                   situation report — read second, every session
├── README.md
├── pyproject.toml               uv, ruff, pytest
├── SBOM.md                      every dependency + licence
├── docs/
│   ├── BUILDLOG.md              append-only: what was tried, what worked, what did not
│   ├── 00-STATUS.md             what is current vs superseded
│   ├── 01-design-v3.md          current design
│   ├── 02-gauntlet-findings.md  adversarial review + dispositions
│   ├── 03-free-stack.md         resources, data, references (§2 §3 §6 superseded)
│   ├── 04-decisions/            one ADR per significant decision
│   ├── 05-toolchain.md          every piece of software we install, and what we do not
│   └── archive/                 v1, v2, UMLILO — historical only
├── src/reefprint/
│   ├── quantity.py              rule 1 as a type: provenance travels with the number.
│   ├── acquire/                 µManager control, LED sequencing, analyser rotation
│   ├── bridge/                  masks + series -> per-mineral anisotropy. The only sanctioned route.
│   ├── calibrate/               reflectance standards, R% conversion, QDF lookup
│   ├── polarim/                 Stokes parameters, bireflectance, anisotropy
│   ├── segment/                 backbone + decoder
│   ├── texture/                 grain extraction, association matrix
│   ├── heads/                   entrainment risk · NFG load · oxidation index
│   ├── trust/                   ensemble, conformal, OOD gate, abstention.
│   │                         `split.py` = rule 2, `baseline.py` = rule 3, `abstain.py` =
│   │                         rule 5. All three are refusals, not warnings.
│   ├── integrate/               OPC UA, OMF, AASX
│   └── viz/                     UI
├── experiments/                 numbered, each with its own README + result
├── tests/                       pytest + hypothesis (physics invariants)
└── data/                        DVC-tracked, never committed raw
```

## Stack

**What to actually install, and when: [`docs/05-toolchain.md`](docs/05-toolchain.md).** It also lists what we decided *not* to install and why, so nobody helpfully re-adds Bio-Formats. Licences are in [`SBOM.md`](SBOM.md), which governs.

Python 3.12 · `uv` · `ruff` · pytest + hypothesis · scikit-image · OpenCV · napari · PyTorch · `timm` (Apache-2.0) · `segmentation_models_pytorch` · XGBoost · `crepes`/MAPIE · ONNX Runtime · `asyncua` · `omf` (MIT) · Eclipse BaSyx · MLflow · DVC · **OME-TIFF via `tifffile`, not Bio-Formats** ([ADR-0001](docs/04-decisions/0001-ome-tiff-via-tifffile-not-bioformats.md) — Bio-Formats is GPL-2.0)

Micro-Manager and ImageJ/Fiji are **not** dependencies. They were acquisition-side; with no rig there is nothing to drive. Data comes in through `RotationSeries`, which is the acquisition boundary and takes a phantom, a stored public series, or a driver that does not exist.

Instrument design, **not built** (ADR-0002): Raspberry Pi 5 · Pi HQ Camera · reversed M12 or microscope objective · **OpenFlexure** printed stage (sub-100 nm, open source) · steppers + PCA9685 · multispectral LED ring · **one** salvaged LCD polariser as the rotating analyser, plus a depolarising diffuser on the illumination side — **not** a crossed pair (ADR-0005) · acrylic-resin polished sections. This is a BOM to present, not kit to buy.

## Reference sources — free and authoritative

- **Craig & Vaughan, *Ore Microscopy and Ore Petrography* 2nd ed.** — full open access, MSA. Chapters 3, 5, 11 are essential.
- **IMA/COM Quantitative Data File** — 510 species, reflectance spectra; searchable at projects.gtk.fi/com/results/reflectance_data.html. **This is the teacher.**
- **LumenStone** — polished-section segmentation dataset with pixel masks, ×50, 3396×2547. Informal terms ("free to use… cite the references"), **no named licence** — confirm before publishing anything derived. Two subsets matter: **S2** (Norilsk layered ultramafic — pyrrhotite, chalcopyrite, pentlandite, magnetite; the same Ni-Cu-PGE sulphide assemblage as the Merensky/UG2 BMS) and **S3 v2, which ships XPL *rotation* sequences** on strongly anisotropic ore minerals. S3's rotations are the public reflected-light data the week-1 gate's second leg runs on. The `petroscope` library that accompanies it is **GPL-3.0 — data yes, library never**.
- **IronOreRLM** — 563 reflected-light images, India. Domain-shift testing.
- **CGS National Core Library**, Donkerhoek — 1,500 boreholes, real Bushveld

## Weekly gates

| Week | Gate — binary, on evidence |
|---|---|
| 1 | Rotation series in, per-pixel Stokes out, pentlandite dark while pyrrhotite lights up, on screen. **Two legs:** (a) synthetic phantom with analytic ground truth — *passed, `experiments/001-week1-gate/`*; (b) the same inversion on a stored **public reflected-light rotation series** — outstanding. Leg (a) alone proves the maths, not the mineralogy; do not present it as more. |
| 2 | **Falsification test computed, with CI** |
| 3 | Conformal coverage within band, **per held-out locality** |
| 4 | Zero silent failures under degraded input |
| 5 | End-to-end offline on one laptop |
| 6 | Backup demo video exists |

## Kill list, in order

Federated layer → four of five agents (keep Curator) → adaptive illumination → AASX → OMF → multilingual UI → Hailo → T+45.

**Never cut:** falsification test · locality splits · conservative-default abstention · SBOM · backup video.

## Open questions

1. Can talc/serpentine be discriminated without SWIR? Empirical, week 2. If no, drop to two properties.
2. CGS sampling policy — phone call.
3. Polish quality control protocol.
4. ~~Single technical decision-maker~~ — **CLOSED, 2026-08-15.**

## Single technical decision-maker

**Lethabo Hoaeane** — Domain lead (BCom Business Informatics, Unisa / prior metallurgical
engineering).

*(Confirmed by Lethabo, 2026-08-22. Supersedes "Lethabo Mphukuile", which was inferred from the git
commit identity and was wrong — it appears in ADRs written before that date and should be corrected
wherever it is load-bearing.)*

**Team Sonar** is three people across three institutions: Lethabo Hoaeane (BCom Business
Informatics, Unisa), **Sibusiso Khumalo** (BSc Electrical Engineering, Wits — the KHANYA build),
**Ipeleng Modise** (BSc Computer Science, TUT).

Breaks all architecture ties. Not a consensus role: when the team splits on a technical
decision, this is the person who ends it, and the decision is written up as an ADR in
`docs/04-decisions/` the same day.

Two standing checks on this role, from the gauntlet blind spots:

- **Blind spot 8** — the domain lead is also the rusty met-eng, who tends to be treated as the
  oracle and to under-push against three CS majors. The tie-breaker role makes that worse, not
  better. No load-bearing mineralogical claim rests on this person alone; book two external
  calls instead.
- **Blind spot 11** — the same person owns the ten-minute narrative. Do not let the talk
  quietly become the specification.
