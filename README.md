# REEFPRINT

*Otherwise known as **KHANYA** — one build, two names, both correct*
*([ADR-0003](docs/04-decisions/0003-one-build-two-names-reefprint-and-khanya.md)).*

**A computational ore microscope.** Software that identifies ore minerals and quantifies their
deportment by multispectral quantitative reflectance plus full linear Stokes polarimetry, with
calibrated uncertainty and an explicit refusal mechanism.

**It is software, evaluated on public data. No instrument is built**
([ADR-0002](docs/04-decisions/0002-software-only-no-instrument-is-built.md)). The ~R5,000 rig is
a costed bill of materials presented as a design, and 0.2–1.6 µm/pixel is a design target, not a
measurement.

Built for the Mintek-SCi Grad Hackathon 2026 — challenge: *Computer Vision for Real-Time
Mineralogical Characterisation*. Team Sonar. Final: 1 October 2026, Mintek Randburg.

---

## The one-sentence claim

> Published automated optical mineralogy — the Castroviejo/Pirard line, CAMEVA and AMCO —
> classifies on **multispectral specular reflectance**. Recovering the **full linear Stokes
> vector per pixel** from a rotating-analyser series adds an axis that reflectance does not
> contain, and that axis discriminates the base-metal sulphides whose split governs PGE
> deportment and flotation response.

Our illumination is **unpolarised**, with the analyser the only polarising element
([ADR-0005](docs/04-decisions/0005-unpolarised-illumination-with-a-rotating-analyser.md)).
Pentlandite is cubic, so the light it reflects stays unpolarised and its intensity is **flat**
through a full analyser rotation — DOLP 0. Pyrrhotite is anisotropic: it lights up. Pentlandite
is the principal PGE host and it floats. Pyrrhotite is depressed and carries little PGE. Telling
them apart is the whole point.

**Keep the claim narrow.** "Nobody uses polarised light" is false — Pirard, Lebichot & Krier
(2007) is direct prior art on polarised-light imaging in ore microscopy. Per-pixel Stokes
recovery is not the same thing as imaging under crossed polars, which is why the claim above
survives; the paper is still unread (open finding **N1**).

## Start here

1. [`CLAUDE.md`](CLAUDE.md) — the project constitution. Outranks everything.
2. [`CONTEXT.md`](CONTEXT.md) — **where we are, the single next action, and what has already bitten us.**
3. [`docs/BUILDLOG.md`](docs/BUILDLOG.md) — what was tried, what worked, what did not.
4. [`docs/00-STATUS.md`](docs/00-STATUS.md) — what is current, what is history, how we got here.
5. [`docs/01-design-v3.md`](docs/01-design-v3.md) — the current design.
6. [`docs/02-gauntlet-findings.md`](docs/02-gauntlet-findings.md) — what was already killed, and why.

**Do not propose anything listed as killed in the gauntlet findings without explicitly arguing
why the original objection no longer applies.**

## Development

Requires [`uv`](https://docs.astral.sh/uv/). Python 3.12.

```bash
uv sync
```

Heavy extras (`ml`, `integrate`, `viz`) are opt-in — `uv sync --extra ml` — so a clean checkout
does not pull PyTorch to run the tests. Full install list, including what we deliberately do
*not* install: [`docs/05-toolchain.md`](docs/05-toolchain.md).

```bash
uv run pytest
```

Placeholder tests marked `placeholder` fail on purpose: one per unbuilt module, so the red list
*is* the backlog. The real suite is `uv run pytest -m "not placeholder"` and it must stay green.

```bash
uv run ruff check . ; uv run ruff format --check .
```

Install the pre-commit hooks once after cloning:

```bash
uv run pre-commit install
```

## Layout

```
src/reefprint/
├── acquire/      RotationSeries — the acquisition boundary. Phantom, stored file, or a driver
│                 that does not exist (ADR-0002).
├── calibrate/    reflectance standards, R% conversion, QDF lookup
├── polarim/      Stokes parameters, bireflectance, anisotropy
├── segment/      backbone + decoder
├── texture/      grain extraction, association matrix
├── heads/        entrainment risk · NFG load · oxidation index
├── trust/        ensemble, conformal, OOD gate, abstention
├── integrate/    OPC UA, OMF, AASX
└── viz/          UI, deterministic offline demo, visible refusal renderer
```

`experiments/` — numbered, each with its own README and result, including the failures.
`data/` — DVC-tracked. Raw data is never committed.

## The other half

**KHANYA** is the same build's segmentation, modal-mineralogy, liberation, conformal-calibration,
and offline-dashboard half. It lives in this repository's `main` branch; this `reefprint` branch
carries REEFPRINT's acquisition, polarimetry, trust, bridge, and visualization half. The public
repository is [`Sibusiso-K/KHANYA`](https://github.com/Sibusiso-K/KHANYA).

The histories intentionally remain unmerged under ADR-0003 for originality and IP assessment.

The two are **not merged**. The seam between them is `reefprint.bridge` — labelled masks in
from KHANYA, per-mineral anisotropy out, each figure beside its own noise floor. That seam is
the only sanctioned route between the halves; see
[ADR-0003](docs/04-decisions/0003-one-build-two-names-reefprint-and-khanya.md).

## Licence and provenance

Every dependency must be assignable to Mintek: permissive licences only for anything shipped.
See [`SBOM.md`](SBOM.md).

Commit history is the originality defence — finalists face originality authentication after
2 October. Commit early, commit often, including failures.
