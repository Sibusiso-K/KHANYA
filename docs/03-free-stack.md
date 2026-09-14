# REEFPRINT — the entirely free stack

**Team Sonar · 15 August 2026 · everything verified against a live source**

> **PARTIALLY SUPERSEDED, 2026-08-15.**
> §1 (knowledge) and §5 (compute) are **live**. §4 (data) and §7 (the pitch) are live **with an
> inline correction each** — the novelty claim in §4 and the past tense in §7.
> **§2 is now a design, not a plan** — nothing is built ([ADR-0002](04-decisions/0002-software-only-no-instrument-is-built.md)).
> **§3 is superseded by [`05-toolchain.md`](05-toolchain.md)** — it still lists Micro-Manager,
> ImageJ/Fiji and Bio-Formats, all three of which are out ([ADR-0001](04-decisions/0001-ome-tiff-via-tifffile-not-bioformats.md), ADR-0002).
> **§6 is superseded** — it is a purchase list totalling ≈R5,200 and the hardware budget is R0.
> Read it as the costed BOM we *present*, never as something we bought.
> The section headers below carry their own markers. Do not delete the stale content — it is the
> record of what was believed on 15 August, and the ADRs point back at it.

The v3 pivot to computational ore microscopy turns out to sit on top of a field that has been giving its foundations away for decades. Almost every component is free, and — more importantly — *authoritative* rather than improvised.

---

## 1. The knowledge — this closes your biggest gap

### Craig & Vaughan, *Ore Microscopy and Ore Petrography*, 2nd ed. — **fully open access**

The Mineralogical Society of America hosts the **entire textbook** free, whole or chapter by chapter.

http://www.minsocam.org/msa/openaccess_publications/craig_vaughan/

This is *the* standard reference. The chapters that matter to you:

| Chapter | Why |
|---|---|
| 1 — The Ore Microscope | the instrument you are rebuilding |
| 3 — Mineral Identification: Qualitative Methods | colour, bireflectance, anisotropy — your feature definitions |
| **5 — Quantitative Methods: Reflectance Measurement** | **the measurement protocol, calibration, standards** |
| 7 — Ore Mineral Textures | association, intergrowth, your texture features |
| 10 — Ore Mineral Assemblages | what occurs with what, and why |
| **11 — Applications of Ore Microscopy in Mineral Processing** | **literally your use case, written by the field** |

Your team has no metallurgist. The definitive text on exactly this technique is free. Read chapters 3, 5 and 11 this week — all five of you, not just the domain lead.

### The reference data — IMA/COM Quantitative Data File

The Commission on Ore Mineralogy's QDF covers **510 mineral species plus 125 compositional or structural variants, with reflectance spectra for every entry.** A searchable web database of the four standard COM wavelengths, compiled by C.J. Stanley at the Natural History Museum, is hosted by the Geological Survey of Finland:

http://projects.gtk.fi/com/results/reflectance_data.html

**This is your teacher.** You were going to distil Mintek's QEMSCAN archive. You don't need it — the international standard reference for identifying minerals by quantitative reflectance is free, authoritative, and is precisely what published automated systems compare against.

Also free: **RRUFF** (rruff.info — Raman, XRD, chemistry), **Mindat**, and MSA's *Handbook of Mineralogy*.

---

## 2. The instrument — open hardware  ⚠️ *design only, nothing is built*

> **ADR-0002.** Everything in this section is a costed design we present. No board, lens, stepper
> or polariser is purchased. The physics arguments are untouched — they are properties of the
> data, not of the instrument — but no number here may be quoted as measured.

### OpenFlexure Microscope

Open-source, 3D-printed, plastic-flexure stage with **sub-100 nm motorised positioning**, Raspberry Pi based, inverted geometry, driven by low-cost geared steppers. Full parts list and assembly instructions published.

https://openflexure.org/

**Basic build under $20. Fully automated research grade around $200.** There's also a **Delta Stage** variant for heavier optical assemblies — relevant if you're mounting a real objective.

You were going to design a rig. It's already designed, tested, documented and free.

### Polarisers — free from any dead LCD

Every discarded LCD panel — laptop, monitor, calculator — carries polarising film laminated to the glass. **One panel yields two polarisers.** Salvaged film shows extinction ratios of **1,200:1 to 2,800:1** and 42–45% transmittance at 550 nm, which is identical to film sold at **$25–65 per 100 mm square**.

Critical technique: **mechanical delamination, not solvents or heat.** Solvents swell the acrylic adhesive, cause micro-tearing and leave hazing. Watch for the diffusion layer some panels bond to the polariser — that one is harder to use off-screen.

Your rotating analyser and fixed polariser cost R0 and come out of e-waste. Say that on stage.

### Reflectance standards — use minerals

Certified standards are the one genuinely expensive item. You may not need them. Gangue and epoxy resin sit at **R ≈ 4.5–5%**, and common phases have tabulated values in the QDF. Put a known mineral in frame — pyrite is ubiquitous and well-characterised — and calibrate internally against the QDF value. Self-calibration against known phases in the same section, for free.

---

## 3. The software — all free, all standard  ⛔ *SUPERSEDED by [`05-toolchain.md`](05-toolchain.md)*

> **Three rows in this table are wrong as of 15 August 2026.** Micro-Manager and ImageJ/Fiji were
> acquisition-side and there is no rig to drive (ADR-0002). Bio-Formats is **GPL-2.0** and
> unassignable — OME-TIFF goes through `tifffile` (BSD-3-Clause) instead (ADR-0001).
> [`05-toolchain.md`](05-toolchain.md) is the current answer to *what do we download*.
> The table is left intact as the record.

| Tool | Role | Note |
|---|---|---|
| **Micro-Manager (µManager)** | microscope/stage/camera/filter control | Free, open source, runs as an ImageJ plugin, cross-platform. **Python wrapper gives complete access to the hardware control core** — script your whole acquisition. |
| **ImageJ / Fiji** | image analysis backbone | The scientific standard. Huge plugin ecosystem. |
| **scikit-image · OpenCV · napari** | Python pipeline | segmentation, morphology, viewing |
| **Bio-Formats / OME-TIFF** | provenance-carrying image format | metadata in the header |
| PyTorch · `timm` (Apache-2.0) · `segmentation_models_pytorch` | modelling | permissive licences, assignable |
| `crepes` / MAPIE | conformal prediction | free |
| XGBoost | processability heads | free |
| `omf` (MIT) | block model export | free |
| DVC · MLflow · `uv` · `ruff` · pytest | engineering | free |

`PicRed_Biref` on GitHub is an ImageJ script for quantifying birefringence under polarised light — written for stained tissue, but the thresholding approach ports directly.

---

## 4. The data — open datasets that already exist

| Dataset | What | Why it matters |
|---|---|---|
| **LumenStone** | polished-section images with mineral segmentation labels, **PPL and XPL**, plus published colour-adaptation methods. **Subsets, confirmed 2026-09-14**: S1 (Berezovskoe, hydrothermal, 7 classes, 59+16 train/test v1 → 64+20 v2), S2 (Norilsk layered ultramafic, 5 classes, 23+6 → 37+12), S3 (high-T hydrothermal, 9 classes, 27+8 → 33+14+XPL rotations), **V1 (30 images, 10 samples × 3 imaging variations, for colour-adaptation methods — not yet used here, see `CLAUDE.md` factor table)**, P1/P2 (panorama stitching), ICM1 (tag annotations, "coming soon") | The closest thing to a purpose-built benchmark for exactly your task |
| **IronOreRLM** | 563 reflected-light microscopy images of iron ores, Indian mines | Real RLM imagery, different ore — good for domain-shift testing |
| **MUMDMC2025** | 14,400 photomicrographs, PPL/XPL at 72 rotations | rotation and polarisation physics; transmitted light, so complementary |
| **IMA/COM QDF** | reflectance spectra, 510 species | the reference labels |
| **CGS National Core Library** | 1,500 boreholes, 420 km, Donkerhoek | real Bushveld material, an hour away |
| USGS splib07 · ECOSTRESS · RockSL | spectral libraries | free |

**LumenStone terms of use, quoted verbatim** (read 2026-09-14, `imaging.cs.msu.ru/en/research/geology/lumenstone`):
*"You are free to use the provided data in your own research work. If you intend to publish research
work that uses this dataset, you have to cite the references whenever appropriate."* Recorded in
full in `SBOM.md`'s data table.

**Prior art to cite (and to beat):** *Deep learning semantic segmentation of opaque and non-opaque minerals from epoxy resin in reflected light microscopy* (Minerals Engineering); *Res-UNet Ensemble Learning for Semantic Segmentation of Mineral Optical Microscopy Images* (Jiang et al. 2024, *Minerals* 14:1281, doi:10.3390/min14121281); improved YOLOv8n for fine-grained mineral recognition; *Automated ore microscopy based on multispectral measurements of specular reflectance*. All of these use **non-polarised** light.

**Read in full 2026-09-14, and load-bearing for the accuracy work — not just prior art:**
**Korshunov, D.M. et al. (2025), "From visual diagnostics to deep learning: automatic mineral
identification in polished section images," *Mining Science and Technology (Russia)* 10(3):232–244,
doi:10.17073/2500-0632-2025-05-416, CC BY 4.0.** The LumenStone dataset authors' own paper: PSPNet +
ResNet18, class-balanced patch sampling, a Colour Correction Matrix, and — the finding that matters
most for our novelty claim — **XPL registered to PPL and fed to the network as extra input
channels, reported as an improvement.** Full factor-by-factor treatment: `CLAUDE.md` §"What the
literature says drives accuracy here" and `docs/09-brief-compliance.md` §3.

> ⚠️ **The sentence that used to end this paragraph — "that's your gap" — was too broad and is
> withdrawn (finding N1, 2026-08-15).** Those four papers use non-polarised light; **the field
> does not.** *Pirard, Lebichot & Krier (2007), Particle texture analysis using polarized light
> imaging and grey level intercepts* is direct prior art on polarised-light imaging in ore
> microscopy, and it is **unread**. The surviving claim is narrower: **per-pixel full linear
> Stokes recovery**, which is not the same thing as imaging under crossed polars. Read the paper
> before week 6 and state the distinction in the talk rather than discovering it on stage.

---

## 5. The compute

**CHPC** — South Africa's National Centre for High Performance Computing, mandated to serve South African academia. Free to academic researchers. **chpc.ac.za.** Worth an application this week; it would remove every compute constraint you have.

Otherwise: Kaggle (30 hrs/week, P100), Colab (15–30 hrs/week T4), Lightning AI student credits, Modal for CPU burst, HuggingFace Spaces for hosting.

---

## 6. Revised bill of materials  ⛔ *SUPERSEDED — nothing is bought*

> **ADR-0002. Hardware budget is R0.** This is the BOM we *present* as a design, and the R5,200
> figure is a costing, not a spend. Nothing on this list exists. Never imply it does — and never
> let "≈R5,200" drift into the talk as though a rig were assembled and measured.

| Item | Cost |
|---|---|
| Raspberry Pi 5 (8 GB) | R1,800 |
| Pi HQ Camera | R1,000 |
| Objective / reversed M12 lens | R600 (or salvage a dead microscope) |
| **Polarisers ×2** | **R0** — dead LCD |
| Steppers ×3 + driver | R400 |
| 3D printed OpenFlexure parts | R500 print service, or free with access |
| LED ring + PCA9685 | R400 |
| Reflectance standards | **R0** — internal calibration against QDF values |
| Acrylic resin, grit, cloth | R500 |
| **Total** | **≈ R5,200** |

Textbook R0. Reference database R0. Instrument design R0. Control software R0. Analysis software R0. Training data R0. Compute R0. Samples R0.

---

## 7. What this changes about the pitch

You are not a student team improvising on a budget. You are a team that noticed the entire foundation of quantitative ore microscopy — the textbook, the international reference database, the instrument design, the control software — has been open for years, and that nobody had assembled it into a working computational instrument with polarimetry and modern learning on top.

**"Five thousand rand and a broken monitor"** is a better line than any capex comparison you could construct. And it makes the tailings-and-junior-miner impact argument real rather than rhetorical — because if it costs R5,000, it actually is deployable by an operation that will never buy an SEM.

> ⚠️ **Say it in the conditional, always** (ADR-0002). *"This is a R5,000 bill of materials"* is
> true. *"We built it for R5,000"* is not, and one careless past tense turns a strong line into a
> false claim under originality authentication. The honest version is stronger anyway: the whole
> foundation of quantitative ore microscopy has been open for years, we assembled it into working
> software, and the instrument it targets costs five thousand rand on paper.

---

## Sources

[Craig & Vaughan open access (MSA)](http://www.minsocam.org/msa/openaccess_publications/craig_vaughan/) · [IMA/COM reflectance database (GTK)](http://projects.gtk.fi/com/results/reflectance_data.html) · [QDF for Ore Minerals](https://link.springer.com/book/10.1007/978-94-011-1486-8) · [OpenFlexure Project](https://openflexure.org/) · [OpenFlexure Delta Stage](https://openflexure.org/projects/deltastage/) · [Micro-Manager](https://micro-manager.org/) · [µManager on ImageJ](https://imagej.net/software/micro-manager) · [LumenStone / polished section identification](https://mst.misis.ru/jour/article/view/974) · [LumenStone dataset page (MSU)](https://imaging.cs.msu.ru/en/research/geology/lumenstone) · [petroscope (GPL-3.0, data yes, code never)](https://github.com/xubiker/petroscope) · [IronOreRLM dataset](https://pubmed.ncbi.nlm.nih.gov/40534715/) · [Res-UNet mineral segmentation](https://doi.org/10.3390/min14121281) · [Semantic segmentation of opaque minerals in RLM](https://www.sciencedirect.com/science/article/abs/pii/S0892687521002363) · [RRUFF](https://rruff.info/ima/) · [CHPC](https://www.chpc.ac.za/) · [LCD polariser salvage method](https://www.improwis.com/projects/method_salvage_lcd_polarizers/) · [CGS National Core Library](https://www.geoscience.org.za/cgs/systems/publications/national-core-library/)
