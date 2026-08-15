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
