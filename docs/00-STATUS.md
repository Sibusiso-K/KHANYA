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
| [`01-design-v3.md`](01-design-v3.md) | **The current design.** Computational ore microscope: quantitative reflectance + full linear Stokes polarimetry at 0.2–1.6 µm/px. |
| [`02-gauntlet-findings.md`](02-gauntlet-findings.md) | Adversarial review findings and dispositions. **Why the design is what it is.** Read before proposing anything. |
| [`03-free-stack.md`](03-free-stack.md) | Resources: Craig & Vaughan (open access), IMA/COM QDF, OpenFlexure, LumenStone, IronOreRLM, CGS core library. |
| [`tools/gauntlet.md`](tools/gauntlet.md) | The adversarial review prompt. Re-run at week 3 and week 6 with real code attached. |
| `04-decisions/` | One ADR per significant decision. Currently empty. |

## Partially superseded — read with the header

| File | Status |
|---|---|
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

1. **The resolution gap closes.** A Raspberry Pi HQ camera with a reversed M12 lens reaches
   ~0.2 µm/px; SEM-MLA runs at ~3 µm/px. We stop inferring across three orders of magnitude
   and start measuring directly.
2. **Polarimetry splits the sulphides.** Pentlandite is cubic and stays dark through a full
   analyser rotation; pyrrhotite is anisotropic and lights up. That distinction governs PGE
   deportment — and it is the entire point of the project.

The defensible claim, kept narrow: published automated optical mineralogy uses **non-polarised**
light. Adding full Stokes polarimetry to multispectral quantitative reflectance discriminates
the base-metal sulphides.

---

## Findings still OPEN — these are not settled

| # | Finding | Where it bites |
|---|---|---|
| **F1** | Chromite-proxy collapse. v3 measures directly rather than inferring, but the falsification test still runs and the result is reported either way. | Week 2 gate |
| **F2 (partial)** | Talc/serpentine without SWIR is unproven. If it fails, drop to two properties. | Week 2, empirical |
| **S2** | Closed-loop confounding: plant history was generated under FloatStar control. No causal claim may be drawn from observational plant data. | Any use of the Kaggle flotation dataset |

Plus the blind spots in `02-gauntlet-findings.md` — particularly that **abstention fires exactly
when it is least safe** (novel texture triggers OOD; novel texture *is* an ore transition), and
that **adaptive illumination is a leakage channel** (freeze the schedule for all training data).

---

## Weekly gates

| Week | Gate — binary, on evidence |
|---|---|
| **1** | **Analyser rotates, pentlandite stays dark while pyrrhotite lights up, on screen** ← current |
| 2 | Falsification test computed, with CI |
| 3 | Conformal coverage within band, per held-out locality |
| 4 | Zero silent failures under degraded input |
| 5 | End-to-end offline on one laptop |
| 6 | Backup demo video exists |

Final: 1 October 2026, 13:00 submission, 10-minute presentation, Mintek Randburg.
