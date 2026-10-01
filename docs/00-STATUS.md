# Latest verified continuation — 1 October2026

Read CONTINUE-REEFPRINT-2026-10-01.md. Candidate evaluation COMPLETE and audited; mIoU0.632038/pixelaccuracy0.855093 but weak magnetiteprecision/common-phase regressions. Live weights unchanged. CI allfourgreen2b763b2. Assistantreadingfixlive; candidate report UI integration next.

# 00-STATUS — what is current, what is history

**Read this before reading anything else in `docs/`.**

This folder contains three generations of design. They contradict each other. That is
deliberate — the contradictions are the institutional memory. But only one generation is
true, and building from the wrong one is the cheapest way to waste a week.

Governing order of precedence:

```
CLAUDE.md  >  docs/01-design-v3.md  >  docs/02-gauntlet-findings.md  >  everything else
```

---

## Current — treat as true

| File | What it is |
|---|---|
| [`../CLAUDE.md`](../CLAUDE.md) | Project constitution. Outranks everything here. |
| [`../CONTEXT.md`](../CONTEXT.md) | **Situation report.** Where we are, the single next action, and the five things that have already bitten us. Read second, after CLAUDE.md. |
| [`BUILDLOG.md`](BUILDLOG.md) | Append-only record of what was tried, what worked, what failed. Rule 8 — the commit history is the originality defence and this is its prose companion. |
| [`12-pwa-phase-identification-roadmap-2026-09-30.md`](12-pwa-phase-identification-roadmap-2026-09-30.md) | User-selected Supabase / Cloudflare Pages / FastAPI application handoff and controlled phase-improvement queue. A plan for KHANYA's separate application history; no hosted app or improved checkpoint is claimed. |
| [`05-toolchain.md`](05-toolchain.md) | Every piece of software we install, when, and what we deliberately do not. Supersedes `03-free-stack.md` §3. |
| [`01-design-v3.md`](01-design-v3.md) | **The current design** for everything except the instrument. Computational ore microscope: quantitative reflectance + full linear Stokes polarimetry. Its 0.2–1.6 µm/px is now a *design target*, not something that will be measured — see ADR-0002 below. |
| [`02-gauntlet-findings.md`](02-gauntlet-findings.md) | Adversarial review findings and dispositions. **Why the design is what it is.** Read before proposing anything. |
| [`tools/gauntlet.md`](tools/gauntlet.md) | The adversarial review prompt. Re-run at week 3 and week 6 with real code attached. |
| `04-decisions/` | One ADR per significant decision. **[0001](04-decisions/0001-ome-tiff-via-tifffile-not-bioformats.md)** OME-TIFF via `tifffile`, not Bio-Formats. **[0002](04-decisions/0002-software-only-no-instrument-is-built.md)** Software only — no instrument is built. **[0003](04-decisions/0003-one-build-two-names-reefprint-and-khanya.md)** REEFPRINT, otherwise known as KHANYA; histories stay unmerged. |

> **ADR-0002 overrides the hardware content of every document in this folder, including
> `01-design-v3.md`.** Where a doc describes building, calibrating, or measuring on a rig, read it
> as a costed design. Nothing is bought. The optical *physics* in those docs is untouched — it is
> a property of the data, not of the instrument.

## Partially superseded — read with the header

| File | Status |
|---|---|
| [`03-free-stack.md`](03-free-stack.md) | **Mixed.** §1 knowledge and §5 compute are **live**. §4 data and §7 pitch are live **with an inline correction each** — the "that's your gap" novelty claim (finding N1) and the past tense on the R5,200 BOM. **§2 is a design, nothing is built** (ADR-0002). **§3 software table is superseded by [`05-toolchain.md`](05-toolchain.md)** — it lists Micro-Manager, ImageJ/Fiji and Bio-Formats, all three out (ADR-0001, ADR-0002). **§6 BOM is superseded** — hardware budget is R0; it is a costing we present, not a spend. |
| [`archive/reefprint-deployment-agents-training.md`](archive/reefprint-deployment-agents-training.md) | **Mixed.** §1 tiers, §2 degradation ladder / load-shedding / calibration drift, §4 training and compute plan, and §6 formats are **live**. §3 agent roster beyond Curator, §5 hyperspectral data stack, §7 capture modes, §8 capability stack are **obsolete**. |

## The record — not wrong, just not current

| File | Status |
|---|---|
| [`archive/submitted-application.md`](archive/submitted-application.md) | **The abstract Mintek accepted.** This is what we submitted and were judged on. It is a historical fact, not an error. Do not "correct" it. Where it conflicts with v3, v3 governs the build — but the submission stands as the record. |

## Superseded — historical only

`archive/mintek-2026-build-spec.md` · `archive/umlilo-system-design.md` ·
`archive/reefprint-v2-hardened.md` · `archive/reefprint-one-pager-and-numbers.md`

Each carries a SUPERSEDED header. Useful for tracing *why* a decision was made. Never a
source of truth for *what to build*.

---

## How we got here — three pivots in one week

**v1 — "distil the QEMSCAN archive."** Infer sub-10 µm PGM deportment from macro texture
using hyperspectral drill-core imagery, feedforward to plant control at T+45 minutes.

Four independent adversarial reviews found four fatal problems (see `02-gauntlet-findings.md`):

- **F1** The only macro variable plausibly co-varying with base-metal-sulphide content is the
  chromite:silicate ratio — and plants already measure Cr₂O₃ by on-stream XRF in minutes. v1
  risked being a slow, expensive chrome meter.
- **F2** Chromite is opaque with no diagnostic VNIR-SWIR absorption features and is 50–75 vol%
  of UG2. Talc and serpentine need SWIR. The optics could not see two of five phases.
- **F3** Nothing was statistically measurable at n = 30–100 specimens.
- **F4** UG2 recovery is chrome-constrained, so "liberation at target grind" fights the binding
  constraint rather than relieving it.

**v2 — "three visible properties."** Kept the method, changed the target: fine-chromite
entrainment risk, naturally-floating-gangue load, surface oxidation state. Smaller, measurable,
mechanistically defensible. Killed liberation-at-P80, grindability→kWh/t, and T+45 as a hard claim.

**v3 — "we were doing the wrong physics."** The pivot that resolves F1 and F2 structurally
rather than by retreat. Spectroscopy identifies minerals by *molecular absorption*; opaque ore
minerals have none. They have been identified for a century by **quantitative specular
reflectance, bireflectance, and anisotropy under crossed polars** — reflected-light ore
microscopy, standardised since the 1940s.

Two consequences:

1. **The resolution gap closes** — *on paper*. A Raspberry Pi HQ camera with a reversed M12 lens
   is calculated to reach ~0.2 µm/px against SEM-MLA's ~3 µm/px. Since ADR-0002 that is an
   argument about the design, not a measurement, and must be presented as one.
2. **Polarimetry splits the sulphides.** Pentlandite is cubic and stays dark through a full
   analyser rotation; pyrrhotite is anisotropic and lights up. That distinction governs PGE
   deportment — and it is the entire point of the project.

The defensible claim, kept narrow: published automated optical mineralogy classifies on
**multispectral specular reflectance**. Recovering the full linear Stokes vector per pixel adds
an axis reflectance does not contain, and that axis splits the base-metal sulphides.

**pivot 4 — "we are not building it."** 2026-08-15, [ADR-0002](04-decisions/0002-software-only-no-instrument-is-built.md).
No hardware is purchased. The rig becomes a costed BOM; evaluation runs on public data. This
works only because `RotationSeries` is the acquisition boundary — a rotation series is a rotation
series whether the analyser was turned by a stepper, by a hand on a Leitz stage, or by a forward
model, and `reefprint.polarim` never learns which. Read the ADR for what it costs, including the
half of the week-1 gate it turns into a phantom.

---

## Findings still OPEN — these are not settled

| # | Finding | Where it bites |
|---|---|---|
| **F1** | Chromite-proxy collapse. v3 measures directly rather than inferring, but the falsification test still runs and the result is reported either way. | Week 2 gate |
| **F2 (partial)** | Talc/serpentine without SWIR is unproven. If it fails, drop to two properties. | Week 2, empirical |
| **S2** | Closed-loop confounding: plant history was generated under FloatStar control. No causal claim may be drawn from observational plant data. | Any use of the Kaggle flotation dataset |
| **N1** *(new, 2026-08-15)* | **Prior art on polarised-light ore imaging.** Pirard, Lebichot & Krier (2007), *Particle texture analysis using polarized light imaging and grey level intercepts*. "Nobody uses polarised light" is false. The narrow claim — per-pixel Stokes recovery, not imaging under crossed polars — appears to survive, but the paper is unread. | The ten-minute talk. Read before week 6. |
| **N2** *(new, 2026-08-15)* | **Anisotropy noise floor goes as 1/S0.** `E[DOLP \| isotropic] = σ√(8/n)·√(π/2)/S0`, confirmed to 3 s.f. in `experiments/001-week1-gate/`. Any fixed anisotropy threshold is therefore a reflectance-dependent classifier in disguise: dark gangue reads ~10× pentlandite's apparent anisotropy from identical noise. | Every discrimination rule downstream. Threshold must be conditioned on S0 and reported with an interval. |
| **N3** *(new, 2026-08-20)* | **Which element rotated is not recorded, and getting it wrong is silent.** Published "XPL rotation sequences" are almost certainly *stage* rotations (4th harmonic) rather than *analyser* rotations (2nd harmonic). Fitting the Stokes model to a stage rotation returns `S1 = S2 = 0` for every anisotropic grain — no exception, no NaN. `reefprint.polarim.geometry.harmonic_signature` now decides it from the frames, and `experiments/002-s3v2-geometry/` settles it against the archive — **but that has not been run**: the 5.2 GB `S3_v2.zip` is on Sibusiso's machine. | **Week-1 leg (b).** If confirmed, leg (b) needs a fourth-harmonic estimator and the Stokes inversion must not touch this data. |

Plus the blind spots in `02-gauntlet-findings.md` — particularly that **abstention fires exactly
when it is least safe** (novel texture triggers OOD; novel texture *is* an ore transition), and
that **adaptive illumination is a leakage channel** (freeze the schedule for all training data).

---

## Weekly gates

| Week | Gate — binary, on evidence |
|---|---|
| **1** | Rotation series in, per-pixel Stokes out, pentlandite dark while pyrrhotite lights up, on screen — **phantom passed; real S3 v2 measured `NEITHER` and routed away from Stokes**. |
| 2 | Falsification test computed, with CI — **statistical core built; texture features remain a domain-lead block** |
| 3 | Conformal coverage within band, per held-out locality — **implemented and tested** |
| 4 | Zero silent failures under degraded input — **implemented and tested** |
| 5 | End-to-end offline on one laptop — **implemented, tested, and paired-host verified** |
| 6 | Backup demo video exists — **paired-host verified two-screen GIF generated from the offline demo** |

Final: 1 October 2026, 13:00 submission, 10-minute presentation, Mintek Randburg.


## Latest verified application update — 1 October 2026

Actual model tiles now produce live previews/counts, with unknown pixels excluded. White workbench polish, original/prediction comparison, spatial map/sections/layers and voice/evidence assistant are implemented. 71 backend checks and seven serial browser tests passed, plus production build. Real test_11 inference took78.475s; no improved held-out accuracy claimed. Both extended Kaggle runs completed and are being audited. Public release/push status is documented in BUILDLOG. See LIVE-UI-RELEASE-2026-10-01.md for source snapshot, limitations and resume prompt. Current hosted model is unapproved fb78727d, so simulator HOLD is expected.

Historical status follows; the entries below must not be read as the current release state.

