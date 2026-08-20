# BUILDLOG — what was tried, what worked, what did not

**Append-only.** Newest entry at the top. Never rewrite history here; if an entry turns out to be
wrong, add a new entry saying so and link back. This file and the commit log are the same story
told twice — the commit log says *what changed*, this says *why, and what we learned by getting
it wrong first*.

Rule 8 of the constitution: *commit early, commit often, including failures.* Finalists face
originality authentication after 2 October. A build log with no failures in it is not a record,
it is a press release.

**What goes in an entry**

| Field | Rule |
|---|---|
| Date + commit | absolute date, short SHA |
| Attempted | what we set out to do |
| Worked | with the evidence — a number, a test name, a command output |
| Did not work | the actual failure text where possible, not a paraphrase |
| Learned | only if it generalises. Otherwise leave it out. |
| Left open | anything that became a `docs/00-STATUS.md` finding or a red test |

---

## 2026-08-20 — session 4 · `4d849f7` the bridge, `e8a3273` the fourth-harmonic estimator

### Attempted

Two things, both about seams. Design the boundary where KHANYA's labelled masks meet a REEFPRINT
rotation series, without merging the two codebases. Then remove finding N3 as a *blocker* rather
than continuing to wait on it — build the estimator that leg (b) needs if the answer comes back
`FOURTH`, so that either verdict has a route.

### Worked

- **`reefprint.bridge` as a data contract, not a merge.** Sibusiso's own `JOINT-PLAN.md` §5 names
  merging two architectures as the largest schedule risk in the project, and it is correct. So the
  contract is *data* — two arrays and four strings. KHANYA can satisfy it by importing the package
  or by writing an `.npz` and never importing REEFPRINT at all. Labels flow in, measurements flow
  out, nothing flows back; a one-way boundary can be reasoned about, a two-way one becomes a merge
  by accident.

  Its real value is that three rules stop being documentation and become structural:

  | Rule | Before | Now |
  |---|---|---|
  | N3 | `require_analyser_rotation` on `RotationSeries`, bypassable | called unconditionally on the only path in, and `test_no_keyword_argument_can_disable_the_geometry_check` asserts the signature so no escape hatch can be added quietly |
  | Rule 2 | locality carried by convention | `LabelledSection.locality` required, never defaulted, error text names Rule 2 |
  | N2 | floor computed where someone remembered to | `MineralStatistic` carries `noise_floor_median` beside `anisotropy_median` in one frozen record; `median_over_floor` is the comparable number |

  The N2 test is the one worth keeping: `test_the_noise_floor_rises_as_reflectance_falls` puts
  pentlandite (R = 50) and chromite (R = 13) side by side, both **exactly** cubic, and asserts the
  *darker* phase reads the **larger** apparent anisotropy. That is the trap, stated as a passing
  test rather than as a warning in a docstring.

- **Raise-vs-skip, asymmetric on purpose.** Wrong geometry raises: which element rotated is a
  property of the acquisition protocol, constant across a dataset, and 47 identical skip records
  inviting someone to pool the zero survivors is worse than one exception naming the cause. Shape
  and angle-count problems skip, and report *both* shapes — their count is the diagnosis, one bad
  mask against a transposed archive. That second path is exactly the crash KHANYA's ten-mineral
  symmetry test is currently dying on.

- **`reefprint.polarim.extinction`.** `I(phi) = A0 + A4c cos4phi + A4s sin4phi`, least-squares per
  pixel, giving extinction depth `|r1-r2|² = 8·A4` and the extinction azimuth mod 90°. N3 is now a
  fork in the road rather than a wall.

- **The N3 failure is symmetric, and that was not obvious.** Fitting `4φ` to a rotating-analyser
  series returns an extinction amplitude of ~0 for every anisotropic grain over a uniform angle
  set — the same silent "everything is isotropic", arrived at from the other direction. Having
  built one guard and watched the first real caller walk around it,
  `RotationSeries.require_specimen_rotation` was written *at the same time as* the estimator, and
  `test_fitting_the_fourth_harmonic_to_an_analyser_series_is_silently_zero` proves the failure
  instead of asserting it: pyrrhotite's depth reads `< 1e-9` while the same pixels under the
  correct inversion read DOLP = 0.12 exactly.

- **`crossing_ratio = dc/amplitude` turned out better than expected.** Working through an analyser
  uncrossed by `ε`, with `P = (r1+r2)/2` and `Q = (r1−r2)/2`:

  ```
  amplitude    = Q²/2                       — independent of ε
  crossing_ratio = 1 + 2 sin²ε (P/Q)²       — exact, not a small-angle expansion
  azimuth      = φ₀ + ε/2
  ```

  So leakage does **not** bias the depth. That is the actual argument for fitting the harmonic
  rather than reading a peak-to-trough range, which absorbs the pedestal in full. And since
  `P/Q ≈ 2/a`, the leak check gets *sharper* as the anisotropy weakens — half a degree of
  uncrossing reads 1.04 on pyrrhotite (a = 0.12) and 1.68 on chalcopyrite (a = 0.03). Weak
  anisotropy is precisely when an operator is tempted to uncross, and that is when this catches
  them. All three predictions verified at `rel=1e-9` against a forward model written independently
  from the reflection matrix, so a sign error in one is not shared by the other.

- **The `2/a` advantage pinned at its root.**
  `test_extinction_depth_is_quadratic_where_analyser_modulation_is_linear`: halve `a` and the
  extinction depth drops 4×, while DOLP drops 2×. This is what experiment 002's measured 38×
  noise-survival ratio comes from, and it is why the estimator is a fallback and never a
  substitute. The talk must not blur the two.

125 passed, 26 deselected. `ruff check .` clean.

### Did not work

- **First draft of `crossing_ratio`'s docstring claimed leakage "biases `extinction_depth` upward".
  It does not.** Writing the test made that obvious — the fitted `A4` is `Q²/2` regardless of `ε`.
  The claim was inherited from thinking about a peak-to-trough estimator, which *is* biased, and
  it survived into prose because nothing had checked it yet. Corrected in place before commit.
- **A first assertion of `crossing_ratio > 2.0` at half a degree of uncrossing failed at 1.042.**
  The derivation was exact to `1e-9`; the *magnitude* claim around it was invented. Replaced with
  the exact formula plus a test of the scaling — which is the more useful property anyway. Rule 1
  applies to adjectives in docstrings, not only to numbers in code.
- **`float()` on a `(1, 1)` array is a `TypeError` in NumPy 2.** The single-pixel test forward
  model returned `(n, 1, 1)`; dropping the spatial dims to `(n,)` matches the existing
  `_single_pixel` idiom in `test_polarim.py` and every recovered quantity reads as a plain float.

### Learned

**A guard is only as good as the narrowest path it sits on.** `require_analyser_rotation` was
correct, tested, and bypassed within a week — not maliciously, but because a caller who builds the
intensity array itself never touches the object carrying the guard. Moving it onto a *mandatory*
boundary and then asserting the function signature is the difference between a rule and a hope.

The corollary, applied for the first time here: when you find yourself building a second estimator
that can fail the same way, write its guard in the same commit. Not after the incident.

### Left open

`reefprint.bridge` measures `ANALYSER` series only — a stage archive raises at the boundary rather
than being routed to `extinction`. That is deliberate for now: the two produce different quantities
in different units and one measurement type per path is the point of the seam. Once experiment 002
returns a verdict, the losing branch can be deleted rather than plumbed.

The estimator's `bireflectance_contrast` needs a mean reflectance from outside the geometry, and
`reefprint.calibrate` does not exist yet. Until it does, any `a` from a stage archive is
conditional on a number this project cannot supply.

---

## 2026-08-20 — session 3 · `52711d3` OME-TIFF store, `19154c5` the geometry discriminator

### Attempted

Close week-1 leg (b): read a stored public rotation series through the same `RotationSeries`
container the phantom uses, and run the identical Stokes inversion on LumenStone S3 v2.

Then, on absorbing Sibusiso's KHANYA repo, stop leg (b) from running into finding N3 — and stop
his ten-mineral symmetry test from doing the same thing first.

### Worked

- **`reefprint.acquire.store`** round-trips a `RotationSeries` through OME-TIFF via `tifffile`,
  angles and geometry carried in the OME-XML header rather than in filenames. ADR-0001 holds; no
  JVM anywhere.

- **`reefprint.polarim.geometry.harmonic_signature` turns N3 from an inference into a
  measurement.** Joint fit of both harmonics,

  ```
  I(a) = A0 + A2c cos2a + A2s sin2a + A4c cos4a + A4s sin4a
  ```

  with each amplitude compared against **its own** noise floor read off the design matrix,
  `cov = σ²(AᵀA)⁻¹`, times the Rayleigh factor `√(π/2)` for the magnitude of a two-component
  Gaussian. Joint rather than sequential: on a non-uniform angle set power leaks between the
  harmonics and a sequential fit hands the leak to whichever was fitted first.

  Evidence it is calibrated rather than decorative: **the losing harmonic reads 1.0× its floor**,
  not merely "smaller" (`test_the_losing_harmonic_sits_at_its_own_noise_floor`, `snr_4 = 1.0 ±
  0.6` at 40% noise while `snr_2 > 10`). A floor wrong by a constant factor would still give the
  right verdict on clean data and fail on noisy data, which is the worst place to find out.

  Four verdicts, two of them refusals. `BOTH` and `NEITHER` map to `RotationGeometry.UNKNOWN`,
  **never to `ANALYSER`** — the module cannot wave the inversion through by failing to decide.

- **The end-to-end proof**, `test_the_discriminator_catches_what_the_stokes_inversion_silently_
  misses`: a stage rotation whose frames demonstrably modulate (`ptp > 0` on every anisotropic
  pixel) inverts to `anisotropy < 1e-9` everywhere, and the same frames are correctly read as
  `SPECIMEN` by the harmonic signature.

- **`experiments/002-s3v2-geometry/`** settles N3 against the real archive, decoding one frame at
  a time out of the zip so peak memory is one frame. Smoke-tested through a synthetic archive
  built to S3 v2's exact layout, JPEG round-trip included: a known stage archive reads back
  `FOURTH` at snr 16.3, with the 2θ channel at exactly 1.0× its floor.

- **`pillow` promoted from transitive to declared**, with `SBOM.md` and `docs/05-toolchain.md`
  rows in the same commit (Rule 7). Licence **MIT-CMU**, read from the installed distribution's
  own `License-Expression` metadata — the SPDX declaration attached to the wheel we actually
  install, not a guess.

86 passed, 26 deselected. ruff clean.

### Did not work

- **The first claim about 8-bit quantisation was wrong, and it was wrong in the flattering
  direction.** The smoke run returned `NEITHER` on a synthetic archive that was a pure stage
  rotation by construction. The story that fit was: crossed-polars intensity goes as
  bireflectance *squared* on a near-black field, so 8 bits should starve it while the analyser
  geometry, riding on a bright S0, survives. A sweep appeared to confirm it — stage detected at
  5% noise raw, undetected at 2% once quantised, analyser untouched. A 3× penalty, asymmetric,
  and a tidy consequence of the physics already in the constitution.

  It was an artefact of my own conversion. `np.ndarray.astype(np.uint8)` **wraps** negative
  values rather than clipping them, and

  ```
  stage frames at 5% noise: min=-0.26787  negatives=1419300 of 3110400 (45.63%)
  np.array([-1.0]).astype(np.uint8)  ->  [255]
  ```

  Nearly half of a crossed-polars stack is below zero, because the signal sits on a near-black
  field and the noise is additive and symmetric. Wrapping that many samples to arbitrary bright
  values destroys the 4th harmonic — which looks exactly like a quantisation penalty and is not
  one. With `np.clip(np.round(...), 0, 255)`, what a sensor and a JPEG encoder actually do:

  ```
  stage, 5% noise:  snr_4 = 6.8 raw   6.9 quantised   -> FOURTH either way
  ```

  **8-bit conversion costs neither geometry its verdict**, 0–5% noise. The caveat had already
  been written into `run.py` and a passing test had already been written to support it. Both were
  wrong, and the test was the more dangerous of the two: it asserted a true-sounding conclusion
  and passed for a reason that had nothing to do with it.

  Nothing in `src/` casts to an integer type — checked, not assumed — so no shipped code was
  affected. The trap is now pinned by the clip in `_to_eight_bit` and stated in its docstring.

### Learned — the 2/a advantage, measured

Chasing the quantisation story to ground produced the number it was a bad imitation of. Sweeping
noise until each geometry stops being detectable:

```
stage    : last detected at noise_pct 0.05,  missed at 0.08
analyser : last detected at noise_pct 2.0,   missed at 3.0
```

**The analyser geometry stays detectable through 38× more noise than the stage geometry.**
CLAUDE.md predicts the advantage is `2/a` and that it *grows as the anisotropy weakens*; across
the phantom's anisotropic phases — pyrrhotite `a = 0.12`, chalcopyrite `a = 0.03` — that spans
16.7× to 66.7×. The measurement lands inside the band.

This is a consistency check, not a derivation: a detection-threshold ratio over a mixed field at a
declared SNR threshold is a different quantity from a per-grain contrast ratio. But it converts
the argument for the rotating analyser from a line of algebra into a measured number, and it is
strongest exactly where the base-metal sulphides live — which is the whole point.

It has a second consequence that matters for reading the real archive: **a `NEITHER` verdict is
not neutral.** A null is far more likely if the frames are stage rotations than if they are
analyser rotations, so a null leans toward N3 being *true*. `run.py` says so in its own output
rather than leaving it to be reasoned out later, and it is explicitly not clearance to invert.

### Learned — the risk arrived from the other repo, not this one

Sibusiso's KHANYA is a separate 46-commit repo that imports `reefprint.polarim.stokes` unchanged
across a path bridge. His `src/polarimetry.py::sample_section` feeds all 72 S3 v2 frames straight
into `stokes_from_rotation_series`, bypassing `require_analyser_rotation()` — which was committed
hours earlier and which he had no way to know about.

If S3 v2 is stage-rotation data, his ten-mineral symmetry test returns a separation ratio near
1.0 and reads as **"polarimetry does not work on real ore"**: a false negative against the
project's central claim, produced by an estimator bug, on the one experiment most likely to be
believed. Two people building carefully against a shared invariant is not enough when the
invariant is four hours old.

The general form, worth keeping: **an inference that everyone agrees with is still an inference,
and a shared codebase propagates it faster than it propagates the correction.** N3 had been
written into `CLAUDE.md` as "almost certainly" and that was sufficient to reason with and
insufficient to build on. It needed to become a file that answers the question.

Not incidentally: his comment asserting that duplicated rows at θ and θ+180 leave `cond(A)`
unchanged is **correct** — all singular values scale by √2, and the SNR improves by √2. It was
checked before being flagged, and not flagged.

### Decided

- N3 is decided **from the frames**, never from filenames, metadata, or the paper's prose.
  `RotationGeometry` defaults to `UNKNOWN` and refusals map there rather than to `ANALYSER`.
- Experiment scripts stay in numbered directories and are loaded **by path** in tests
  (`tests/test_s3v2_reader.py::_load_experiment`). An un-numbered importable copy would drift
  from the script that is actually run.
- A mask/frame shape mismatch is **skipped with both shapes named, not raised**. Dying on the
  first one hides how many there are, which is the number that decides whether it is one bad
  section or a transposed dataset. This is the failure that killed the first real run.

### Left open

- **N3 itself.** The discriminator is built and tested; it has **not been run on the real
  archive**. The 5.2 GB `S3_v2.zip` is on Sibusiso's machine — a `find` for it here returns
  nothing. One command, and it gates the week-1 gate. Pinned by the failing placeholder
  `tests/test_s3v2_reader.py::test_the_real_s3_v2_archive_has_been_measured`.
- **How the two repos join.** KHANYA's `JOINT-PLAN.md` §5 warns against rewriting either into the
  other; the bridge belongs at the mask/series boundary. Not yet designed.
- LumenStone's licence is still informal and unnamed.

## 2026-08-15 — session 2 · `9cc509c` ADR-0002, and the documents

### Attempted

Verify the four week-1 source modules under lint and test, fix what failed, commit. Then write
down the hardware decision the decision-maker had already made verbally, and produce the
onboarding documents — `CONTEXT.md`, this file, `docs/05-toolchain.md`.

### Worked

- **Week-1 gate leg (a) passes.** `experiments/001-week1-gate/run.py` reports
  `GATE  pyrrhotite / pentlandite anisotropy = 40.4x` at 36 analyser angles, σ = 0.25 R%,
  off-cone pixels 0.00%, residual RMS 0.2376 R%. The sharper variant — both sulphides forced to
  identical R = 44.0% so brightness cannot carry the separation — still separates. That is the
  point: reflectance alone would not do this.
- **Suite state: 53 passed, 25 deselected** (`-m "not placeholder"`), and **25 failed**
  (`-m placeholder`). Lint and format clean across 41 files.
- **Property-based testing earned its place immediately** — see the sign bug below. Hypothesis
  found in seconds what no example-based test in the file would have found at all.
- **The placeholder-marker pattern is working.** `pytest.mark.placeholder` splits CI into a
  blocking `check` job and an informational `gates` job, so the red list *is* the backlog and
  nothing has to be tracked outside the repo. `test_stored_rotation_series_loads_from_ome_tiff`
  is currently the whole of the next task, expressed as a failing test.
- **Provenance-on-the-value works.** Reflectances carry a `Provenance` `StrEnum` on the value
  itself, not in a comment, and `test_no_placeholder_value_is_reported_as_measured` fails if a
  `PLACEHOLDER` ever escapes into something presented as measured. Rule 1 with teeth.
- **`matplotlib.figure.Figure` rather than `pyplot`** — no global state, no display backend, and
  the viz tests can read arrays back out of the figure (`figure.axes[i].images[0].get_array()`)
  and assert on what was actually drawn rather than on what was passed in.

### Did not work

- **A real sign bug shipped in `RotationSeries.rotated_specimen`.** It subtracted φ where it
  should add. Rotating the specimen by φ rotates (S1, S2) by **2φ**; getting the sign backwards
  produces a Stokes image that is *self-consistent*, passes every physical-realisability check,
  and is silently reflected about the analyser axis. Hypothesis produced two distinct
  counterexamples (`assert 1.0 == -0.6536…`, `assert -0.909… == 0.909…`). Fixed to `+ phi_rad`
  and the derivation is now in the docstring. **The test was also rewritten to go through the
  shipped method** — the original reimplemented the angle shift, so it could only ever agree with
  itself.
- **`float()` on a numpy array of shape (1,)** raises
  `TypeError: only 0-dimensional arrays can be converted to Python scalars` under numpy 2.x. Was
  a test bug, not a code bug. Use `.item()`.
- **`# noqa: PLR2004` on a rule that is not enabled** → `RUF100 unused noqa`. `PL` is not in the
  ruff select list. Replaced the magic number with a named module constant `_FRAME_NDIM = 3`,
  which reads better anyway.
- **`ruff format` rewraps a multi-line `if` into something worse.** Pre-empted by extracting the
  condition into a named variable (`design`, `WELL_CONDITIONED`). Fighting the formatter is not
  a strategy; naming the thing is.
- **PowerShell here-strings break `git commit -m`.** A message containing apostrophes ("didn't")
  and `&` fragmented into multiple git pathspecs. **Fix: write the message to a file and use
  `git commit -F <path>`.** This will happen again — every commit message in this project has
  prose in it.

### Learned — the anisotropy noise floor, and why it matters

Derived from the design matrix, not guessed: the rotating-analyser inversion has covariance
`cov = σ²(4/n)·diag(1, 2, 2)`, so S1 and S2 each carry independent noise `σ√(8/n)`, their
magnitude is Rayleigh-distributed, and a **truly isotropic** phase therefore reads

```
E[DOLP | isotropic] = σ · √(8/n) · √(π/2) / S0
```

Confirmed against the run output to three significant figures and pinned by
`test_the_anisotropy_noise_floor_scales_as_one_over_reflectance` across R = 4.75–50% and
n = 12–36.

Two consequences that constrain everything downstream:

1. **Any fixed anisotropy threshold is a reflectance-dependent classifier in disguise.** At
   σ = 0.25 R%, n = 36: gangue at R = 4.75% reads DOLP ≈ 0.031 from pure noise while pentlandite
   at R = 50% reads ≈ 0.003. A rule fitted on bright sulphides lights up every dark grain on the
   section. Discrimination must condition on S0 and report an interval.
2. **The floor falls only as 1/√n.** Halving it costs four times the frames. Averaging is not a
   free lunch and there is no exposure trick that beats the arithmetic.

Promoted to repo-level open finding **N2**.

### Learned — the prior-art position is weaker than we had been saying

"Nobody uses polarised light in ore microscopy" is **false**, and a judge may know it. **Pirard,
Lebichot & Krier (2007), *Particle texture analysis using polarized light imaging and grey level
intercepts*** is direct prior art on polarised-light imaging in this exact field. The claim has
been retightened to *per-pixel full linear Stokes recovery*, which is not the same thing as
imaging under crossed polars — but **the paper is unread**. Open finding **N1**, must be closed
before week 6. Do not discover this on stage.

A targeted search for Stokes polarimetry applied to sulphides returned nothing specific. That is
weak support, not clearance.

### Decided

**[ADR-0002](04-decisions/0002-software-only-no-instrument-is-built.md) — software only, no
instrument is built.** Hardware budget R0. The ~R5,000 rig becomes a costed BOM presented as a
design.

This survives only because `RotationSeries` is the acquisition boundary: a rotation series is a
rotation series whether the analyser was turned by a stepper, by a hand on a Leitz stage in 2019,
or by a forward model, and `reefprint.polarim` never learns which. The ADR states the cost rather
than reframing it as a win — no claim about µm/pixel, exposure, LED response, polariser
extinction or achievable R% accuracy may now come from measurement, and the week-4 degraded-input
gate loses real defocus and real polish damage.

Also decided: **ADR-0001's decider filled in** (Lethabo Mphukuile), which closes CLAUDE.md open
question 4.

### Left open

`N1` Pirard 2007 unread · `N2` the 1/S0 floor · LumenStone licence is informal and unnamed
(`khvostikov@cs.msu.ru`) · `docs/03-free-stack.md` §3 and §6 now contradict ADR-0001 and ADR-0002
and are marked superseded in place.

---

## 2026-08-15 — session 1 · `76de236` week-1 gate, `28f374b` scaffold, `c1af1a5` constitution

### Attempted

Stand the repo up from nothing: constitution, design docs, gauntlet findings, a working
environment, and the first physics — rotating-analyser Stokes recovery with a synthetic phantom
that has a closed-form correct answer.

### Worked

- **`uv` as the whole environment story.** One lockfile, one command, no conda. `uv sync` from a
  clean checkout produces a working test suite without pulling PyTorch, because everything heavy
  is an optional extra (`ml`, `integrate`, `viz`).
- **One failing test per unbuilt module, committed on purpose.** Eight modules exist as
  directories with a red test naming exactly what is missing. `--strict-markers` and
  `--strict-config` mean a typo in a marker is an error, not a silently-skipped test.
- **The physics core.** `I(θ) = (S0 + S1·cos2θ + S2·sin2θ)/2`, least-squares inverted per pixel.
  Frozen slotted dataclasses for the Stokes container, `typing.Protocol` +
  `@runtime_checkable` for the acquisition boundary so the phantom and a future file reader are
  interchangeable without inheritance.
- **The identity that makes the whole project one measurement rather than two.**
  `(I_max − I_min)/(I_max + I_min) = √(S1² + S2²)/S0 = DOLP`. The degree of linear polarisation
  *is* the normalised bireflectance contrast of classical ore microscopy. One quantity carries
  both the optics and the mineralogy.
- **Refusing an ill-conditioned angle set rather than returning a plausible answer.**
  `cos 2θ` and `sin 2θ` have period π, so 0°/90°/180° gives only *two* independent equations, not
  three. `stokes_from_rotation_series` checks the design-matrix condition number and refuses.
  A silent rank-deficient least-squares fit would have been the worst possible failure mode: an
  answer, with no error, that is wrong.

### Did not work

- **`picamera2` / `python-prctl` will not build on Windows.** `python-prctl` is Linux-only and
  pip drags it in. The `hardware` extra was **removed entirely** rather than made conditional —
  the Pi is a deployment target, not something a dev laptop should have to resolve. The reasoning
  is preserved as a comment in `pyproject.toml` so nobody re-adds it. (ADR-0002 later made the
  whole question moot.)
- **`Bio-Formats` was in the constitution's stack line and cannot be.** It is GPL-2.0, and the
  deliverable must be assignable to Mintek — the same failure mode gauntlet finding S3 raised and
  the DINOv3 removal was meant to close. Solving it for the model backbone and then reintroducing
  it at the I/O layer would leave the licence argument no better than v1's.
  → **[ADR-0001](04-decisions/0001-ome-tiff-via-tifffile-not-bioformats.md): `tifffile`,
  BSD-3-Clause.** No JVM anywhere.

### Learned

The pivot that produced this repo — v1 hyperspectral → v3 reflected-light polarimetry — is
recorded in `docs/00-STATUS.md` under *How we got here*, and the four fatal findings that forced
it are in `docs/02-gauntlet-findings.md`. Read those before proposing anything; most good ideas
have already been killed here for a stated reason.

### Left open

Everything past `polarim`, `acquire` and `viz`. Deliberately — the red test list is the backlog.
