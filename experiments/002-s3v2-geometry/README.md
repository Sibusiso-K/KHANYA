# 002 — Which rotation is it? Settling N3 on LumenStone S3 v2

**Finding N3:** published "XPL rotation sequences" are almost certainly *stage* rotations under
fixed crossed polars, not *analyser* rotations. If that is true, week-1 leg (b) cannot use the
Stokes inversion at all.

**Status: NOT RUN on the real archive.** The discriminator is built, tested against both forward
models, and smoke-tested end to end through a synthetic archive of the correct layout. The
verdict on the actual 5.2 GB `S3_v2.zip` is outstanding, and until it exists **N3 is open**.

```bash
uv run python experiments/002-s3v2-geometry/run.py --archive path/to/S3_v2.zip
```

The archive is not in this repo — LumenStone's licence is informal and unnamed, see
`docs/05-toolchain.md` §5. Nothing is extracted; frames are decoded one at a time out of the zip
and discarded, so peak memory is one frame.

## Why this exists

The two geometries put their power in different harmonics, and no filename records which one was
turned:

| Geometry | Modulation | Recovers |
|---|---|---|
| Rotating analyser | `I(θ) = (S0 + S1cos2θ + S2sin2θ)/2` — **2nd harmonic** | full linear Stokes vector |
| Stage under crossed polars | `I(φ) = \|r₁−r₂\|²(1 − cos4φ)/8` — **4th harmonic** | extinction depth only |

A 4φ signal has **no 2θ component at all**. Fit the Stokes model to a stage rotation and it
returns `S1 = S2 = 0` for every anisotropic grain — no exception, no NaN, a perfectly realisable
answer, every anisotropic mineral silently reported as isotropic. Proven, not asserted:
`tests/test_acquire.py::test_a_crossed_polars_stage_rotation_inverts_to_zero_anisotropy`.

**The concrete risk this was built to stop.** KHANYA's `src/polarimetry.py` feeds all 72 S3 v2
frames straight into `stokes_from_rotation_series` for a ten-mineral symmetry test. If those are
stage rotations, that test returns a separation ratio near 1.0 and reads as *"polarimetry does not
work on real ore"* — a false negative that would kill the central claim on an estimator bug. So
N3 had to stop being an inference.

## How it decides

`reefprint.polarim.geometry.harmonic_signature` fits both harmonics **jointly**:

```
I(a) = A0 + A2c·cos2a + A2s·sin2a + A4c·cos4a + A4s·sin4a
```

Jointly, not sequentially: for a non-uniform angle set power leaks between the harmonics, and a
sequential fit would assign the leak to whichever was fitted first. Each amplitude is compared
against **its own** noise floor, read off the design matrix — `cov = σ²(AᵀA)⁻¹`, with the Rayleigh
factor `√(π/2)` for the magnitude of a two-component Gaussian. The verdict is the median SNR over
the top decile of modulating pixels, ranked on `max(A2, A4)` so the selection does not assume the
answer.

Four outcomes, and two of them are refusals: `SECOND`, `FOURTH`, `BOTH` (mixed, impure or
mislabelled) and `NEITHER` (nothing above the floor). **`BOTH` and `NEITHER` map to
`RotationGeometry.UNKNOWN`, never to `ANALYSER`** — the module cannot wave the Stokes inversion
through by failing to decide.

## What has actually been established

All on the phantom and on a synthetic archive, none on real ore:

- Both geometries are recovered correctly from their own forward model, including at S3 v2's
  exact angle set (72 frames, 5° steps, full 360°).
- The losing harmonic sits at **1.0×** its own floor, not merely "smaller" — which is what makes
  the floor calibrated rather than decorative.
- Pure noise returns `NEITHER`, not a confident answer.
- A stage rotation is **never** reported as an analyser rotation, across noise 0–20% and through
  8-bit quantisation. That is the one failure that would be unrecoverable.
- End to end through a zip, JPEG round-trip included: a known stage archive reads back `FOURTH`
  at snr 16.3 with the 2θ channel sitting at exactly 1.0× its floor.

### Two things measured on the way, one of which was wrong first

**8-bit quantisation costs neither geometry its verdict** (0–5% noise; stage snr_4 6.8 raw against
6.9 quantised). A null result on the real archive therefore cannot be blamed on the file format.

This replaces an earlier claim of a 3× quantisation penalty against the stage geometry, which was
**an artefact of casting negative intensities straight to `uint8`, which wraps rather than
clips**. At 5% noise 46% of a crossed-polars frame stack is below zero, because the signal sits on
a near-black field. Nothing in `src/` casts to an integer type, so no shipped code was affected —
but the trap is now pinned by the clip in `_to_eight_bit` and its docstring.

**The analyser geometry stays detectable through 38× more noise than the stage geometry**
(stage last detected at 5%, analyser at 200%). CLAUDE.md predicts the advantage is `2/a`, which
spans 16.7× to 66.7× across the phantom's anisotropic phases (pyrrhotite a = 0.12, chalcopyrite
a = 0.03). The measurement lands inside that band. This is a consistency check, not a derivation —
a detection-threshold ratio over a mixed field is a different quantity from a per-grain contrast
ratio — but it is the case for the rotating analyser, measured rather than asserted, and it is
**strongest exactly where the base-metal sulphides live**.

It also means a `NEITHER` on the real archive is **not neutral**: a null is far more likely if the
frames are stage rotations than if they are analyser rotations, so a null leans toward N3 being
true. The script says so in its own output rather than leaving it to be worked out later.

## Reading the output

Three conclusions, and only one of them is good news:

- **N3 CONFIRMED** (`FOURTH`) — stage rotations. Do not run the Stokes inversion on them. Leg (b)
  needs a fourth-harmonic estimator, and the two must never be conflated in the talk.
- **N3 REFUTED** (`SECOND`) — the inversion applies and leg (b) runs as originally planned.
- **NO VERDICT** (`NEITHER`/`BOTH`) — N3 stays open, leaning toward stage. Not clearance.

Sections are reported individually as well as pooled. The acquisition protocol should be constant
across a dataset, so **a split verdict is itself a finding** and the script warns on it.

A section whose mask and frames disagree on shape is **skipped with both shapes named, not
raised** — dying on the first mismatch hides how many are affected, which is the number that
decides whether it is one bad section or a transposed dataset. This is the failure that killed the
first real run.

## What this does not show

- **Nothing about the real archive.** Every number above is from a forward model or a synthetic
  zip built to the real layout. That proves the code, not the dataset.
- **`DETECTION_SNR = 5.0` is a declared decision threshold, not a physical constant.** So is the
  top-decile fraction, and so is `MAX_DESIGN_CONDITION`. All three are named constants with that
  written next to them.
- **Noise here is additive Gaussian and uniform.** A real detector is shot-noise limited. The 38×
  figure will need re-deriving against real frames; the direction is not in doubt, the magnitude
  is.
- **The verdict does not certify the data is usable** — only which model may be fitted to it.

`output/` is gitignored; the JSON report regenerates with the command above.
