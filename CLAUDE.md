# CLAUDE.md — REEFPRINT, otherwise known as KHANYA

Project constitution. Claude Code reads this at the start of every session. Keep it current; it outranks anything in `docs/`.

**Read [`CONTEXT.md`](CONTEXT.md) next.** This file says what is *true* and what the *rules* are. `CONTEXT.md` says where we are, what the single next action is, and what has already bitten us — it is the file that lets a fresh session or a different machine pick up cold. Then [`docs/BUILDLOG.md`](docs/BUILDLOG.md) for what was tried and what failed, and [`docs/05-toolchain.md`](docs/05-toolchain.md) for what to install.

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

Built for the Mintek-SCi Grad Hackathon 2026, challenge: *Computer Vision for Real-Time Mineralogical Characterisation*. Team Sonar, University of the Witwatersrand. Final: 1 October 2026, 13:00 submission, 10-minute presentation.

## The physics — read this before proposing anything

Hyperspectral reflectance spectroscopy identifies minerals by **molecular absorption features**. Chromite is an opaque spinel with none, and it is **50–75 vol% of UG2 ore**. Spectroscopy on chromitite is a brightness meter. This is why the project pivoted.

Opaque ore minerals are identified by **quantitative specular reflectance (R%), bireflectance, and anisotropy under crossed polars** — reflected-light ore microscopy, standardised since the 1940s.

### Two rotation geometries, and they are not interchangeable

This is the trap that most threatens the week-1 gate, and it is not a naming quibble.

| Geometry | What turns | Modulation | Recovers |
|---|---|---|---|
| **Rotating analyser** | analyser, with polariser and specimen fixed | `I(θ) = (S0 + S1cos2θ + S2sin2θ)/2` — **2nd harmonic** | the full linear Stokes vector. **This is our claim.** |
| **Stage rotation under crossed polars** | the specimen, with polars fixed and crossed | `I(φ) = \|r₁−r₂\|²(1 − cos4φ)/8` — **4th harmonic** | extinction depth only. The classical observation since the 1940s. |

A 4φ signal has **no 2θ component at all**. Fitting the Stokes model to a stage rotation returns `S1 = S2 = 0` for every anisotropic grain — no exception, no NaN, a perfectly realisable answer, **every anisotropic mineral silently reported as isotropic.** The only witness is `residual_rms`, which sits at exactly `S0/(2√2)`. Proven, not asserted: `test_a_crossed_polars_stage_rotation_inverts_to_zero_anisotropy`.

Hence `RotationSeries.geometry`, which defaults to `UNKNOWN` rather than to the convenient answer, and `require_analyser_rotation()`, which must be called before any Stokes inversion.

**Consequence for the data:** published "XPL rotation sequences" — LumenStone S3 v2, MUMDMC2025 — are almost certainly *stage* rotations, because that is how anisotropy has always been observed. **Verify before building on them** (open finding **N3**). If they are, leg (b) needs a fourth-harmonic estimator, not the Stokes inversion, and the two must never be conflated in the talk.

*Also worth knowing:* extinction depth goes as the **square** of bireflectance contrast `a`, while analyser modulation goes as `a` — so the rotating analyser's advantage is `2/a`, and it **grows as the anisotropy weakens**. That is a real argument for the instrument, and it is strongest exactly where the base-metal sulphides live.

**Polarimetry splits the base-metal sulphides, and that is the whole point:**

| Mineral | Optics | Metallurgy |
|---|---|---|
| Pentlandite | cubic → **isotropic**, stays dark through full analyser rotation | principal PGE host, floats |
| Pyrrhotite | **moderate bireflectance**, anisotropic | depressed, low PGE |
| Chalcopyrite | weakly anisotropic | floats fast |
| Chromite | cubic, isotropic, R ≈ 13% | entrainment risk, smelter penalty |
| Gangue / resin | R ≈ 4.5–5% | discriminated by reflectance alone |

**The defensible claim (narrow, keep it narrow):** published automated optical mineralogy — the Castroviejo/Pirard line, CAMEVA and AMCO — classifies on *multispectral specular reflectance*. Recovering the **full linear Stokes vector per pixel** from a rotating-analyser series adds an axis that reflectance does not contain, and that axis discriminates the base-metal sulphides whose split governs PGE deportment and flotation response.

> ⚠️ **Prior-art risk, open.** Do not say "nobody uses polarised light" — that is false and a judge may know it. **Pirard, Lebichot & Krier (2007), *Particle texture analysis using polarized light imaging and grey level intercepts*** is direct prior art on polarised-light imaging in ore microscopy. Imaging under crossed polars is *not* per-pixel Stokes recovery, which is why the narrow claim above survives — but the paper must be read before week 6 and the distinction stated in the talk, not discovered on stage. A targeted search for Stokes polarimetry on sulphides returned nothing specific; that is weak support, not clearance.

## Hard constraints

- **No proprietary Mintek data.** Public sources only.
- Free-tier compute only: Kaggle (30 h/wk), Colab, Lightning AI, Modal, CHPC if granted.
- **Hardware budget is R0. Nothing is bought, nothing is built** (ADR-0002). The rig is a BOM. Any claim that needed a rig to measure it is now a citation or a flagged assumption.
- Every dependency must be **assignable to Mintek**. See licence rules below.
- Demo must run **fully offline on one laptop**. No network dependency on stage.

## Rules — non-negotiable

1. **Never invent a number.** Flag every assumption as an assumption, in the code and in the docs.
2. **Split by locality, never by patch or image.** Patch-level splits void conformal exchangeability and will silently invalidate every metric. **Enforced in code, not here:** `reefprint.trust.split.split_by_locality()` is the sanctioned constructor and `require_locality_disjoint()` is the backstop for splits built by hand. Measured cost of the leak, on synthetic patches whose only signal is section identity — patch split MAE **0.0017**, honest locality split MAE **0.2119**, a factor of **126**, in the flattering direction. Honest *n* is `LocalitySplit.n_groups`: localities, not sections.
3. **Report the trivial baseline** (majority class, and metadata-only) alongside every metric. Always. **Enforced in code, not here:** `reefprint.trust.baseline.ScoredMetric` takes `baselines` as a required field with **no default**, so a bare metric is a `TypeError` rather than a slide. Uplift is measured against the *strongest* baseline, never the weakest, and `summary()` distinguishes three states — below the baseline, above it but inside the noise honest *n* resolves, and above it by more than that. A baseline may be `NotApplicable`, but only with a stated reason (rule 5's pattern); both inapplicable at once is refused.
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
│   ├── acquire/                 µManager control, LED sequencing, analyser rotation
│   ├── bridge/                  masks + series -> per-mineral anisotropy. The only sanctioned route.
│   ├── calibrate/               reflectance standards, R% conversion, QDF lookup
│   ├── polarim/                 Stokes parameters, bireflectance, anisotropy
│   ├── segment/                 backbone + decoder
│   ├── texture/                 grain extraction, association matrix
│   ├── heads/                   entrainment risk · NFG load · oxidation index
│   ├── trust/                   ensemble, conformal, OOD gate, abstention.
│   │                         `split.py` = rule 2, `baseline.py` = rule 3, both as refusals.
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

Instrument design, **not built** (ADR-0002): Raspberry Pi 5 · Pi HQ Camera · reversed M12 or microscope objective · **OpenFlexure** printed stage (sub-100 nm, open source) · steppers + PCA9685 · multispectral LED ring · salvaged LCD polarisers · acrylic-resin polished sections. This is a BOM to present, not kit to buy.

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

**Lethabo Mphukuile** — Domain lead (Business Informatics / prior metallurgical engineering).

*(Name taken from the git commit identity. Correct the spelling here if it is wrong — it goes
on every ADR.)*

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
