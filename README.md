# REEFPRINT

**A computational ore microscope.** A ~R5,000 instrument that identifies ore minerals and
quantifies their deportment by multispectral quantitative reflectance plus full linear Stokes
polarimetry, at 0.2–1.6 µm/pixel, with calibrated uncertainty and an explicit refusal mechanism.

Built for the Mintek-SCi Grad Hackathon 2026 — challenge: *Computer Vision for Real-Time
Mineralogical Characterisation*. Team Sonar. Final: 1 October 2026, Mintek Randburg.

---

## The one-sentence claim

> Published automated optical mineralogy uses **non-polarised** light. Adding full Stokes
> polarimetry to multispectral quantitative reflectance discriminates the base-metal
> sulphides — and that discrimination governs PGE deportment and flotation response.

Pentlandite is cubic: it stays dark through a full analyser rotation. Pyrrhotite is
anisotropic: it lights up. Pentlandite is the principal PGE host and it floats. Pyrrhotite is
depressed and carries little PGE. Telling them apart is the whole point.

## Start here

1. [`CLAUDE.md`](CLAUDE.md) — the project constitution. Outranks everything.
2. [`docs/00-STATUS.md`](docs/00-STATUS.md) — what is current, what is history, how we got here.
3. [`docs/01-design-v3.md`](docs/01-design-v3.md) — the current design.
4. [`docs/02-gauntlet-findings.md`](docs/02-gauntlet-findings.md) — what was already killed, and why.

**Do not propose anything listed as killed in the gauntlet findings without explicitly arguing
why the original objection no longer applies.**

## Development

Requires [`uv`](https://docs.astral.sh/uv/). Python 3.12.

```bash
uv sync
```

Heavy extras (`ml`, `integrate`, `dev-viz`, `hardware`) are opt-in — `uv sync --extra ml` — so
a clean checkout does not pull PyTorch to run the tests.

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
├── acquire/      analyser rotation, LED sequencing, camera control
├── calibrate/    reflectance standards, R% conversion, QDF lookup
├── polarim/      Stokes parameters, bireflectance, anisotropy
├── segment/      backbone + decoder
├── texture/      grain extraction, association matrix
├── heads/        entrainment risk · NFG load · oxidation index
├── trust/        ensemble, conformal, OOD gate, abstention
├── integrate/    OPC UA, OMF, AASX
└── viz/          UI
```

`experiments/` — numbered, each with its own README and result, including the failures.
`data/` — DVC-tracked. Raw data is never committed.

## Licence and provenance

Every dependency must be assignable to Mintek: permissive licences only for anything shipped.
See [`SBOM.md`](SBOM.md).

Commit history is the originality defence — finalists face originality authentication after
2 October. Commit early, commit often, including failures.
