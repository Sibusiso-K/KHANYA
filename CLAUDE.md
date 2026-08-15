# CLAUDE.md — REEFPRINT

Project constitution. Claude Code reads this at the start of every session. Keep it current; it outranks anything in `docs/`.

---

## What this is

**REEFPRINT is a computational ore microscope.** A ~R5,000 instrument that identifies ore minerals and quantifies their deportment by **multispectral quantitative reflectance plus full linear Stokes polarimetry**, at 0.2–1.6 µm/pixel, with calibrated uncertainty and an explicit refusal mechanism.

Built for the Mintek-SCi Grad Hackathon 2026, challenge: *Computer Vision for Real-Time Mineralogical Characterisation*. Team Sonar, University of the Witwatersrand. Final: 1 October 2026, 13:00 submission, 10-minute presentation.

## The physics — read this before proposing anything

Hyperspectral reflectance spectroscopy identifies minerals by **molecular absorption features**. Chromite is an opaque spinel with none, and it is **50–75 vol% of UG2 ore**. Spectroscopy on chromitite is a brightness meter. This is why the project pivoted.

Opaque ore minerals are identified by **quantitative specular reflectance (R%), bireflectance, and anisotropy under crossed polars** — reflected-light ore microscopy, standardised since the 1940s.

**Polarimetry splits the base-metal sulphides, and that is the whole point:**

| Mineral | Optics | Metallurgy |
|---|---|---|
| Pentlandite | cubic → **isotropic**, stays dark through full analyser rotation | principal PGE host, floats |
| Pyrrhotite | **moderate bireflectance**, anisotropic | depressed, low PGE |
| Chalcopyrite | weakly anisotropic | floats fast |
| Chromite | cubic, isotropic, R ≈ 13% | entrainment risk, smelter penalty |
| Gangue / resin | R ≈ 4.5–5% | discriminated by reflectance alone |

**The defensible claim (narrow, keep it narrow):** published automated optical mineralogy uses *non-polarised* light. Adding full Stokes polarimetry to multispectral quantitative reflectance discriminates the sulphides, and that discrimination governs PGE deportment and flotation response.

## Hard constraints

- **No proprietary Mintek data.** Public sources only.
- Free-tier compute only: Kaggle (30 h/wk), Colab, Lightning AI, Modal, CHPC if granted.
- Hardware budget ≈ R5,000. Polarisers salvaged from dead LCD panels.
- Every dependency must be **assignable to Mintek**. See licence rules below.
- Demo must run **fully offline on one laptop**. No network dependency on stage.

## Rules — non-negotiable

1. **Never invent a number.** Flag every assumption as an assumption, in the code and in the docs.
2. **Split by locality, never by patch or image.** Patch-level splits void conformal exchangeability and will silently invalidate every metric.
3. **Report the trivial baseline** (majority class, and metadata-only) alongside every metric. Always.
4. **Every metric carries a confidence interval sized at honest n.** At n≈100, conformal coverage SD is ~3pp — do not claim tighter than the arithmetic allows.
5. **Abstention emits a conservative default with a stated reason, never "unknown."** Abstention fires at ore transitions, which is when holding the last setpoint is the worst available action.
6. **No LLM computes a mineralogical or control value.** Agents route, select, orchestrate, explain.
7. **Licences:** permissive only for anything shipped. `timm` (Apache-2.0) not DINOv3 (non-transferable, no patent grant). `asyncua` (LGPL) runs on a general-purpose machine, never a sealed appliance. Hailo is an optional accelerator, never load-bearing. Maintain an SBOM.
8. **Commit early, commit often, including failures.** Finalists face originality authentication after 2 October. The commit history is the defence.
9. **The falsification test is a deliverable, not a risk.** Report the result either way.

## The falsification test — run this first

> **H₀: after controlling for Cr₂O₃ and pyroxene fraction, texture carries no additional predictive signal.**

Nested model comparison, grouped by locality, CIs at honest n. If H₀ cannot be rejected, say so publicly and pivot to the oxidation index, which does not depend on the residual.

## Repo layout

```
reefprint/
├── CLAUDE.md                    ← this file
├── README.md
├── pyproject.toml               uv, ruff, pytest
├── SBOM.md                      every dependency + licence
├── docs/
│   ├── 00-STATUS.md             what is current vs superseded
│   ├── 01-design-v3.md          current design
│   ├── 02-gauntlet-findings.md  adversarial review + dispositions
│   ├── 03-free-stack.md         resources, data, references
│   ├── 04-decisions/            one ADR per significant decision
│   └── archive/                 v1, v2, UMLILO — historical only
├── src/reefprint/
│   ├── acquire/                 µManager control, LED sequencing, analyser rotation
│   ├── calibrate/               reflectance standards, R% conversion, QDF lookup
│   ├── polarim/                 Stokes parameters, bireflectance, anisotropy
│   ├── segment/                 backbone + decoder
│   ├── texture/                 grain extraction, association matrix
│   ├── heads/                   entrainment risk · NFG load · oxidation index
│   ├── trust/                   ensemble, conformal, OOD gate, abstention
│   ├── integrate/               OPC UA, OMF, AASX
│   └── viz/                     UI
├── experiments/                 numbered, each with its own README + result
├── tests/                       pytest + hypothesis (physics invariants)
└── data/                        DVC-tracked, never committed raw
```

## Stack

Python 3.12 · `uv` · `ruff` · pytest + hypothesis · **Micro-Manager** (µManager, Python wrapper) for acquisition · ImageJ/Fiji · scikit-image · OpenCV · napari · PyTorch · `timm` (Apache-2.0) · `segmentation_models_pytorch` · XGBoost · `crepes`/MAPIE · ONNX Runtime · `asyncua` · `omf` (MIT) · Eclipse BaSyx · MLflow · DVC · OME-TIFF via Bio-Formats

Hardware: Raspberry Pi 5 · Pi HQ Camera · reversed M12 or microscope objective · **OpenFlexure** printed stage (sub-100 nm, open source) · steppers + PCA9685 · multispectral LED ring · salvaged LCD polarisers · acrylic-resin polished sections (ready in <3 h)

## Reference sources — free and authoritative

- **Craig & Vaughan, *Ore Microscopy and Ore Petrography* 2nd ed.** — full open access, MSA. Chapters 3, 5, 11 are essential.
- **IMA/COM Quantitative Data File** — 510 species, reflectance spectra; searchable at projects.gtk.fi/com/results/reflectance_data.html. **This is the teacher.**
- **LumenStone** — polished-section segmentation dataset, PPL + XPL
- **IronOreRLM** — 563 reflected-light images, domain-shift testing
- **CGS National Core Library**, Donkerhoek — 1,500 boreholes, real Bushveld

## Weekly gates

| Week | Gate — binary, on evidence |
|---|---|
| 1 | Analyser rotates, pentlandite stays dark while pyrrhotite lights up, on screen |
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
4. Single technical decision-maker — **name them in this file.**
