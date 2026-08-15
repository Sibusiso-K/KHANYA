# REEFPRINT v3 — The Computational Ore Microscope

**Team Sonar · Wits · 15 August 2026**

---

## The aha

**We were doing the wrong physics.**

Hyperspectral reflectance spectroscopy identifies minerals by molecular absorption features — Mg-OH, Fe²⁺, carbonate bands. That is why it works beautifully on the alteration halos of the Iberian Pyrite Belt, and why the Elvira dataset looked like the right shape of data.

It fails on UG2 for a reason no amount of model architecture fixes: **chromite is an opaque spinel with no diagnostic absorption features, and it is 50–75% of the rock.** The gauntlet was right. Spectroscopy on chromitite is a brightness meter.

But opaque ore minerals have been identified for a century by completely different physics.

**Reflected-light ore microscopy.** Minerals are identified by *quantitative specular reflectance* (R%, calibrated against reference standards at R = 100, 50 and 0), by *bireflectance* (brightness change on rotation in plane-polarised light), and by *anisotropy* (colour and intensity change under crossed polars). That is the correct instrument for this ore, and it has been standardised, tabulated and taught since the 1940s.

Nobody has built it as a cheap computational instrument with modern learning on top.

---

## Why this resolves all four fatal findings

### 1. The resolution gap closes completely

This was the project-killer. It is now gone.

DIY Raspberry Pi HQ camera macro setups reach **0.173–1.64 µm per pixel** — a reversed M12 lens gets to ~0.2 µm/px, near the optical diffraction limit; a microscope objective gives ~1.64 µm/px. The Pimoroni microscope lens delivers roughly 60–900× magnification off the shelf.

**SEM-MLA operates at ~3 µm/pixel.**

So a R2,000 camera resolves *finer than the instrument we were trying to distil from.* We are no longer inferring micro-properties from macro texture across three orders of magnitude. **We are measuring at ore-microscopy resolution directly.** Base-metal sulphide grains are tens to hundreds of microns — comfortably resolved. PGM grains at 1–4 µm sit at the edge, and we don't need them: PGE deportment is governed by *which sulphide* hosts them and *where it sits*, both measurable at this scale.

### 2. It splits the base-metal sulphides — the mineralogist's worst objection

*"Base-metal sulphide as one class destroys the only thing I care about."* Correct. Polarimetry fixes it with physics rather than apology:

| Mineral | Optical behaviour | Metallurgical meaning |
|---|---|---|
| **Pentlandite** | Cubic → **isotropic**. Stays dark under crossed polars through full rotation. No bireflectance. Pale creamy-yellow. | Principal PGE host (Pd, Rh in solid solution). Floats. |
| **Pyrrhotite** | **Moderate bireflectance**, clearly anisotropic | Depressed, carries little PGE |
| **Chalcopyrite** | **Weakly anisotropic**, may appear isotropic | Floats fast |
| **Chromite** | Cubic spinel → isotropic, low R% (~13) | Entrainment risk, smelter penalty |
| Gangue / resin | R ≈ 4.5–5% | Discriminated by reflectance alone |

Rotate the analyser, watch what changes and what doesn't, and the sulphides separate. That is a hundred-year-old diagnostic that no competing team will be using.

### 3. Measurement becomes absolutely calibrated, not relative

Ore microscopy calibrates against **reflectance standards at R = 100, 50 and 0**. Reflectance is an absolute physical quantity in traceable units.

Hyperspectral reflectance drifts with lamp ageing, tile contamination and ambient leakage — which is why v1 needed Direct Standardisation, conformal widening and a whole domain-shift apparatus to compensate statistically. **Absolute calibration solves structurally what we were patching statistically.** Domain shift stops being a headline risk and becomes an ordinary QA check.

### 4. Oxidation is measured in the instrument's native units

Surface oxidation *is* a change in specular reflectance and colour. The shelf-life index stops being a proxy and becomes a direct measurement. And it's literature-backed for exactly this ore: *"The effect of heavy oxidation upon flotation and potential remedies for Merensky type sulfides"* (Minerals Engineering), plus documented floatability collapse in long-term open storage.

---

## The defensible invention — narrow, and real

Published automated optical mineralogy systems measure **specular reflectance with *non-polarised* light** across spectral bands, matched against a reference database. That's the state of the art (BGRIMM's Mineral Micro-master, Zeiss systems, the Minerals Engineering automated-ore-microscopy series).

**They deliberately leave polarisation on the table.**

> **Our claim: add full linear Stokes polarimetry to multispectral quantitative reflectance, because polarisation response is what discriminates pyrrhotite from pentlandite from chalcopyrite — and that distinction governs PGE deportment and flotation response. Then learn the cross-modal translation to mineral maps.**

That is one sentence, it is narrow, it is testable, and it is not in the literature. It's what MOTT can actually protect.

**Precedent for the learning half exists in a neighbouring field:** *"Unstained Stokes-To-H&E Cross-Modal Translation with Diffusion Prior."* Someone has translated Stokes polarimetric images into a target modality with a diffusion prior — in tissue. Nobody has done Stokes → mineral map.

---

## The instrument

| Component | Purpose | ~Cost |
|---|---|---|
| Raspberry Pi 5 (8 GB) | host | R1,800 |
| Pi HQ Camera | sensor | R1,000 |
| Reversed M12 lens or microscope objective + extension tubes | **0.2–1.6 µm/px** | R600 |
| Rotating **analyser** (polarising film + stepper + PCA9685) | Stokes parameters via rotating analyser — samples are static, so single-shot is unnecessary | R500 |
| Fixed polariser | incident polarisation | R150 |
| Calibrated multispectral LED ring (6–8 bands) | quantitative R% per band | R400 |
| Reflectance standards (R = 100 / 50 / 0) | absolute calibration | R400 |
| XY stage (repurposed 3D printer or stepper stage) | scan and stitch large fields | R800 |
| Acrylic resin, grit, polishing cloth | sample prep | R500 |
| **Total** | | **≈ R6,150** |

A **polarisation camera** (Sony IMX250MZR, four on-chip analyser angles per 2×2 block, single-shot) would be the premium route — LUCID Phoenix/Triton, VA Imaging MER-502-79U3M-POL — but it's well outside budget. A rotating analyser gives identical Stokes parameters on static samples for about 3% of the cost. **Say that in the pitch.** It's the kind of decision that reads as engineering judgement.

**Sample prep is now cheap and fast:** the Minerals Engineering powder-based polished section method uses **acrylic resin to give ready-to-analyse sections in under three hours** — versus 10+ hours for epoxy — and it avoids the preferential particle sedimentation that biases epoxy mounts.

---

## The repositioning — an uncontested niche

| | What it does | Where |
|---|---|---|
| Blue Cube MQi | PGM g/t + Cr₂O₃ in slurry, 15-second intervals | **after** the mill |
| TOMRA / sensor-based sorting | bulk sorting decisions | **on** the belt |
| SEM-MLA / QEMSCAN | full quantitative mineralogy, days, R20m instrument | **in the lab** |
| **REEFPRINT** | quantitative mineralogy + deportment + oxidation, **minutes, R6,000** | **beside the lab** |

You are not competing with the on-line analysers or the sorters. **You are compressing the laboratory turnaround from days to minutes at 1/1000th of the capital cost.** The literature already concedes the thesis — *"automated reflected light optical microscopy represents an alternative and affordable technique compared to automated SEM for quantitative mineralogical analysis"* — and leaves your specific contribution open.

---

## The pitch line

> **"Everyone else is building a spectrometer. Spectroscopy is the wrong physics for chromite — it's opaque and featureless and it's three quarters of the rock. So we built the instrument this ore has actually needed for a hundred years: a computational ore microscope. Quantitative reflectance, full Stokes polarimetry, sub-micron pixels. Six thousand rand. It sees what a twenty-million-rand SEM sees, in minutes instead of days — and it can tell pentlandite from pyrrhotite, which is the only distinction that matters."**

---

## What survives, what changes

**Survives:** teacher–student distillation (teacher is now published R% reference tables plus any MLA maps we can get — and the reference tables are *free and standardised*). Calibrated abstention. Oxidation shelf-life index. Adaptive illumination (now adaptive *band and polarisation angle* selection — richer). The falsification experiment. Standards conformance. Advisory boundary statements. CGS core as sample source.

**Changes:** the deliverable is a bench instrument, not a conveyor scanner. Scope is sample-based, not on-line — which is more honest and dodges Blue Cube entirely.

**Dies:** hyperspectral framing. The macro-texture-infers-invisible-property claim. The T+45 conveyor look-ahead in its original form (it can return as *lab-turnaround* look-ahead: results in minutes means the plant acts hours earlier than it can today — same value, defensible mechanism).

---

## New risks, honestly

1. **Polish quality drives measurement quality.** Variable polish = variable reflectance. Mitigation: reflectance standards in every mount, and reject sections failing a flatness/quality check.
2. **Field of view versus resolution.** At 1 µm/px you see a very small area, so you need stage scanning and stitching, and representativity becomes a sampling-statistics question. Mitigation: the powder-based section method exists precisely to address representativity — cite Part 1 of that series.
3. **Existing automated optical mineralogy systems.** Zeiss and BGRIMM are in this space. Differentiation is the polarimetry, the cost, and the deportment/oxidation outputs. Know their systems before 1 October.
4. **Prep is a manual step.** Three hours, not three days — but not instant. Be precise about it rather than glossing.

---

## Revised ratings

| Criterion | v2 | **v3** | Why |
|---|---|---|---|
| Innovation & Creativity | 8 | **9.5** | Correct-physics pivot plus an unclaimed polarimetry gap in a mature field |
| Technical Feasibility | 6 | **8.5** | Resolution gap gone; absolute calibration; cheap prep; measuring not inferring |
| Impact & Value | 5 | **8.5** | Uncontested niche, credible cost argument, 1/1000th capex |
| Originality | 8.5 | **9** | One narrow protectable claim instead of an assembly |
| Clarity | 6 | **9** | "Everyone built a spectrometer. It's the wrong physics." One sentence. |

**The first three days:** buy polarising film, mount a specimen in acrylic, rotate the analyser, and watch pentlandite stay dark while pyrrhotite lights up. If you see that on a screen by Tuesday, you have the project.
