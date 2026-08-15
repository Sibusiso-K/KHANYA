# REEFPRINT — the entirely free stack

**Team Sonar · 15 August 2026 · everything verified against a live source**

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

## 2. The instrument — open hardware

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

## 3. The software — all free, all standard

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
| **LumenStone** | polished-section images with mineral segmentation labels, **PPL and XPL**, plus published colour-adaptation methods | The closest thing to a purpose-built benchmark for exactly your task |
| **IronOreRLM** | 563 reflected-light microscopy images of iron ores, Indian mines | Real RLM imagery, different ore — good for domain-shift testing |
| **MUMDMC2025** | 14,400 photomicrographs, PPL/XPL at 72 rotations | rotation and polarisation physics; transmitted light, so complementary |
| **IMA/COM QDF** | reflectance spectra, 510 species | the reference labels |
| **CGS National Core Library** | 1,500 boreholes, 420 km, Donkerhoek | real Bushveld material, an hour away |
| USGS splib07 · ECOSTRESS · RockSL | spectral libraries | free |

**Prior art to cite (and to beat):** *Deep learning semantic segmentation of opaque and non-opaque minerals from epoxy resin in reflected light microscopy* (Minerals Engineering); *Res-UNet Ensemble Learning for Semantic Segmentation of Mineral Optical Microscopy Images* (Minerals); improved YOLOv8n for fine-grained mineral recognition; *Automated ore microscopy based on multispectral measurements of specular reflectance*. All of these use **non-polarised** light. That's your gap.

---

## 5. The compute

**CHPC** — South Africa's National Centre for High Performance Computing, mandated to serve South African academia. Free to academic researchers. **chpc.ac.za.** Worth an application this week; it would remove every compute constraint you have.

Otherwise: Kaggle (30 hrs/week, P100), Colab (15–30 hrs/week T4), Lightning AI student credits, Modal for CPU burst, HuggingFace Spaces for hosting.

---

## 6. Revised bill of materials

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

---

## Sources

[Craig & Vaughan open access (MSA)](http://www.minsocam.org/msa/openaccess_publications/craig_vaughan/) · [IMA/COM reflectance database (GTK)](http://projects.gtk.fi/com/results/reflectance_data.html) · [QDF for Ore Minerals](https://link.springer.com/book/10.1007/978-94-011-1486-8) · [OpenFlexure Project](https://openflexure.org/) · [OpenFlexure Delta Stage](https://openflexure.org/projects/deltastage/) · [Micro-Manager](https://micro-manager.org/) · [µManager on ImageJ](https://imagej.net/software/micro-manager) · [LumenStone / polished section identification](https://mst.misis.ru/jour/article/view/974) · [IronOreRLM dataset](https://pubmed.ncbi.nlm.nih.gov/40534715/) · [Res-UNet mineral segmentation](https://doi.org/10.3390/min14121281) · [Semantic segmentation of opaque minerals in RLM](https://www.sciencedirect.com/science/article/abs/pii/S0892687521002363) · [RRUFF](https://rruff.info/ima/) · [CHPC](https://www.chpc.ac.za/) · [LCD polariser salvage method](https://www.improwis.com/projects/method_salvage_lcd_polarizers/) · [CGS National Core Library](https://www.geoscience.org.za/cgs/systems/publications/national-core-library/)
