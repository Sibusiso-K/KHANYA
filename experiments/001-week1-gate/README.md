# 001 — Week-1 gate: linear Stokes polarimetry separates the sulphides

**Gate:** *"Analyser rotates, pentlandite stays dark while pyrrhotite lights up, on screen."*

**Status: passed on the phantom. Not yet run on real reflected-light data.** That distinction is
the whole honest reading of this experiment — see *What this does not show*.

```bash
uv run python experiments/001-week1-gate/run.py
```

## What it does

Forward-models a rotation series from five phases with known Stokes vectors, inverts it with
`stokes_from_rotation_series`, and renders the anisotropy map. No fitting, no training, no
thresholds — the recovery is a three-parameter least-squares inversion of

```
I(θ) = (S0 + S1·cos 2θ + S2·sin 2θ) / 2
```

over 36 analyser positions spread across 180°, with 0.25 R% of Gaussian noise added.

## Result

Seed 11, 192×256 px, 36 angles, noise σ = 0.25 R%. Off-cone pixels: 0.00%. Residual RMS: 0.238 R%.

| phase | true R% | fitted S0 | true DOLP | fitted DOLP | reflectance provenance |
|---|---|---|---|---|---|
| gangue/resin | 4.75 | 4.75 | 0.000 | **0.031** | constitution |
| pentlandite | 50.00 | 50.00 | 0.000 | **0.003** | PLACEHOLDER |
| pyrrhotite | 38.00 | 38.00 | 0.120 | 0.120 | PLACEHOLDER |
| chalcopyrite | 44.00 | 44.00 | 0.030 | 0.030 | PLACEHOLDER |
| chromite | 13.00 | 13.00 | 0.000 | **0.011** | constitution |

**Pyrrhotite reads 40.4× the anisotropy of pentlandite.** Recovery of S0 and of the anisotropic
phases' DOLP is exact to three decimals.

`tests/test_polarim.py::test_anisotropy_separates_sulphides_that_reflectance_cannot` runs the
sharper version: it gives pentlandite and pyrrhotite *identical* R = 44.0%, so brightness carries
no information at all, and the separation survives. That is the claim — polarimetry adds an
orthogonal axis rather than re-describing contrast.

## The finding that matters more than the gate

The three isotropic phases do not read zero. They read **0.031, 0.011, 0.003** — in exact
inverse proportion to their reflectance. This is not a bug and it is not noise in the loose
sense; it is analytic. For evenly spaced angles the design matrix gives
`cov = σ²·(4/n)·diag(1, 2, 2)`, so S1 and S2 each carry `σ√(8/n)` of independent noise, their
magnitude is Rayleigh-distributed, and

```
E[DOLP | isotropic]  =  σ · √(8/n) · √(π/2) / S0
```

Predicted floor at σ = 0.25, n = 36: gangue 0.0311, chromite 0.0114, pentlandite 0.0030. Observed:
0.031, 0.011, 0.003. Pinned by
`tests/test_polarim.py::test_the_anisotropy_noise_floor_scales_as_one_over_reflectance`, which
holds to 3% across R = 4.75–50% and n = 12–36.

Two consequences, both traps:

1. **Any fixed anisotropy threshold is a reflectance-dependent classifier in disguise.** A rule
   fitted on bright sulphides will light up every dark grain on the section. Gangue at R ≈ 4.75%
   reads ten times pentlandite's apparent anisotropy from identical noise. Whatever
   discrimination rule reaches the heads must be conditioned on S0, and its threshold has to be
   fitted and reported with an interval (Rule 4) — never picked by eye off this figure.
   `DISPLAY_ANISOTROPY_CEILING` in `reefprint.viz.anisotropy` is a colour-scale decision and is
   documented as never being a classification threshold.
2. **The floor falls as 1/√n.** Quadrupling the analyser positions halves it. That converts
   "how long does one field of view take to acquire" into arithmetic, before any rig exists.

## What this does not show

- **The phantom is not evidence about minerals.** It is a test instrument: its only job is to
  produce a series whose correct answer is known in closed form, so a bug in the inversion cannot
  hide behind "real rocks are messy". Passing it proves the maths, not the mineralogy.
- **Three of five reflectances and three of five anisotropies are PLACEHOLDER**, carried in
  `Provenance.PLACEHOLDER` on the value itself and enforced by
  `tests/test_acquire.py::test_no_placeholder_value_is_reported_as_measured`. The pyrrhotite
  anisotropy of 0.12 is a guess consistent with "moderate" in the constitution. Replacing these
  is an IMA/COM Quantitative Data File lookup, not a judgement call.
- **The one bit the gate rests on is not a guess.** Pentlandite and chromite are cubic, so their
  anisotropy is exactly zero by symmetry. That is `Provenance.SYMMETRY`, and it is the only
  mineralogical claim this experiment makes.
- **No real reflected-light ore data has been through this yet.** LumenStone S3 v2 ships XPL
  rotation sequences on strongly anisotropic ore minerals; running the same inversion on those is
  the second leg of the gate and is blocked on the reader
  (`tests/test_acquire.py::test_stored_rotation_series_loads_from_ome_tiff`), not on the physics.
- **Noise here is additive Gaussian and identical everywhere.** A real detector is shot-noise
  limited, so σ scales with √I, which *flattens* the 1/S0 floor rather than removing it. The
  direction of the trap is unchanged; the magnitude will need re-deriving against a real sensor.

## Figure

`output/week1-gate.png` (gitignored — regenerate with the command above).

Left: S0. Pentlandite, chalcopyrite and pyrrhotite are all bright and hard to tell apart. This
panel is the previous version of this project. Middle: DOLP on a fixed 0–0.15 scale. The cubic
phases go black; pyrrhotite lights up. Right: mean I(θ) per phase with the fitted model dashed
over it — flat for cubic, modulating for anisotropic. A judge who does not trust the middle panel
can read the right-hand one by eye.
