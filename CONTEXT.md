# CONTEXT — read this second, after CLAUDE.md

**Purpose:** you have just opened this folder in a new session, or on a different machine, or
after a week away. This file gets you from nothing to working in about five minutes. `CLAUDE.md`
is the constitution — *what is true and what the rules are*. This file is the situation report —
*where we are, what to do next, and what has already bitten us.*

Keep it current. A stale CONTEXT.md is worse than none, because it will be trusted.

- **Last updated:** 2026-08-20
- **Last commit at time of writing:** `19154c5` polarim: decide the rotation geometry from the frames, not from the filename
- **Days to final:** 42 (final is 1 October 2026, 13:00 submission, 10-minute presentation)

---

## 1. Read order

| # | File | Why |
|---|---|---|
| 1 | [`CLAUDE.md`](CLAUDE.md) | Constitution. The physics, the nine rules, the kill list. Outranks everything. |
| 2 | **this file** | Where we are and what to do next. |
| 3 | [`docs/BUILDLOG.md`](docs/BUILDLOG.md) | What we tried, what worked, what did not, and why. Append-only. |
| 4 | [`docs/00-STATUS.md`](docs/00-STATUS.md) | Which docs are current vs superseded. `docs/` holds four generations of design and they contradict each other on purpose. |
| 5 | [`docs/04-decisions/`](docs/04-decisions/) | ADRs. Two so far, both binding. |
| 6 | [`docs/02-gauntlet-findings.md`](docs/02-gauntlet-findings.md) | The adversarial review. **Read before proposing anything** — most good ideas here were already killed for a stated reason. |

Everything else is reference, and `docs/00-STATUS.md` tells you which parts of it are still true.

---

## 2. What this is, in one paragraph

REEFPRINT identifies opaque ore minerals and quantifies their deportment from reflected-light
microscopy, by recovering the **full linear Stokes vector at every pixel** from a rotating-analyser
image series. Hyperspectral reflectance cannot do this: chromite is an opaque spinel with no
molecular absorption features and it is 50–75 vol% of UG2 ore, so spectroscopy on chromitite is a
brightness meter. Reflected-light ore microscopy has identified these minerals since the 1940s by
quantitative reflectance, bireflectance and anisotropy under crossed polars. The measurement that
carries the project is that **pentlandite is cubic and stays dark through a full analyser
rotation while pyrrhotite is anisotropic and lights up** — and that split governs PGE deportment
and flotation response. It is software, evaluated on public data. **No instrument is built**
([ADR-0002](docs/04-decisions/0002-software-only-no-instrument-is-built.md)).

---

## 3. Where we are

| Week | Gate | State |
|---|---|---|
| **1** | Rotation series in, per-pixel Stokes out, pentlandite dark / pyrrhotite lit, on screen | **Leg (a) phantom: PASSED**, 40.4× separation. **Leg (b) real public data: BLOCKED on finding N3** ← *we are here*. The reader is built; whether the Stokes inversion may legally be run on S3 v2 is now a one-command question that needs the archive. |
| 2 | Falsification test computed, with CI | not started |
| 3 | Conformal coverage within band, per held-out locality | not started |
| 4 | Zero silent failures under degraded input | not started |
| 5 | End-to-end offline on one laptop | not started |
| 6 | Backup demo video exists | not started |

**Built and tested:** `reefprint.polarim.stokes` (the inversion),
`reefprint.polarim.geometry` (**which** rotation this is — finding N3),
`reefprint.acquire.series` (the acquisition boundary), `reefprint.acquire.store`
(OME-TIFF round-trip), `reefprint.acquire.phantom` (synthetic ground truth, both
geometries), `reefprint.viz.anisotropy` (the three-panel figure).

**Not built:** `calibrate`, `segment`, `texture`, `heads`, `trust`, `integrate`, and the
hardware-facing half of `acquire` (which, per ADR-0002, has no rig to drive). Each has failing tests naming exactly what
is missing — **the red test list is the backlog**, deliberately.

### The single next action

**Run `experiments/002-s3v2-geometry/run.py` against the real `S3_v2.zip` and settle N3.**

```bash
uv run python experiments/002-s3v2-geometry/run.py --archive path/to/S3_v2.zip
```

Everything else in leg (b) is built and waiting on the answer. The reader round-trips OME-TIFF,
the inversion is tested, the geometry discriminator is tested against both forward models and
smoke-tested through a synthetic archive of S3 v2's exact layout. What is missing is one fact
about the dataset:

- **`FOURTH` → N3 confirmed.** Leg (b) needs a fourth-harmonic estimator. The Stokes inversion
  must not touch this data, and the two must never be conflated in the talk.
- **`SECOND` → N3 refuted**, which is the better outcome. Leg (b) runs as originally planned.
- **`NEITHER`/`BOTH` → N3 stays open, leaning toward stage.** Not clearance.

**This machine cannot answer it.** The 5.2 GB archive is on Sibusiso's machine (KHANYA,
downloaded 2026-08-20); a `find` for it here returns nothing. It is one command on his laptop and
it gates the week-1 gate, so it is the thing to ask for first.

**It also gates his work, not just ours.** KHANYA's `src/polarimetry.py` feeds all 72 S3 v2 frames
straight into `stokes_from_rotation_series` for a ten-mineral symmetry test. If those frames are
stage rotations, that test returns a separation near 1.0 and reads as *"polarimetry does not work
on real ore"* — a false negative on an estimator bug, against the project's central claim. Do not
let that experiment run before this one does.

Named by the failing placeholder test
`tests/test_s3v2_reader.py::test_the_real_s3_v2_archive_has_been_measured`.

**Still open, and unchanged:** LumenStone has no named licence — informal "free to use in
research, cite the references", contact `khvostikov@cs.msu.ru`. Downloading is a user decision,
not an agent one.

---

## 4. Verify you are in a good state

```bash
uv sync
```

```bash
uv run ruff check . ; uv run ruff format --check .
```

```bash
uv run pytest -m "not placeholder" -q
```

Expect **86 passed, 26 deselected**. Anything less is a regression, not a quirk.

```bash
uv run pytest -m placeholder -q --no-header -rf
```

Expect **26 failed**. These are the backlog, not breakage. Each failure names the module and the
gate or rule it belongs to. CI runs them in a separate non-blocking job.

```bash
uv run python experiments/001-week1-gate/run.py
```

Expect a table ending `GATE  pyrrhotite / pentlandite anisotropy = 40.4x` and a figure written to
`experiments/001-week1-gate/output/week1-gate.png`.

---

## 5. The six things that will bite you

These are not hypothetical. Five of the six have already happened in this repo.

0. **A stage rotation inverts to zero anisotropy, silently, and nothing in the filename tells you
   which rotation you have.** The two geometries are not interchangeable: a rotating analyser
   modulates at `2θ`, a stage under crossed polars at `4φ`, and a 4φ signal has **no 2θ component
   at all**. Fit the Stokes model to a stage rotation and it returns `S1 = S2 = 0` for every
   anisotropic grain — no exception, no NaN, a physically realisable answer, **every anisotropic
   mineral reported as isotropic**. The only witness is `residual_rms`, sitting at exactly
   `S0/(2√2)`. Pinned by `test_a_crossed_polars_stage_rotation_inverts_to_zero_anisotropy`.
   `RotationSeries.geometry` therefore defaults to `UNKNOWN` rather than to the convenient answer,
   and `require_analyser_rotation()` must be called before any inversion.
   `reefprint.polarim.geometry.harmonic_signature` decides it from the frames. Open finding **N3**
   — and it is the one currently blocking the week-1 gate.

1. **The anisotropy noise floor goes as 1/S0.** A truly isotropic phase does not read zero. It
   reads `σ·√(8/n)·√(π/2) / S0` — so at σ = 0.25 R% and n = 36, gangue at R = 4.75% reads DOLP
   0.031 while pentlandite at R = 50% reads 0.003. **Any fixed anisotropy threshold is therefore a
   reflectance-dependent classifier wearing a disguise.** A rule fitted on bright sulphides will
   light up every dark grain on the section. Pinned by
   `test_the_anisotropy_noise_floor_scales_as_one_over_reflectance`. Open finding **N2**.

2. **The angle convention.** `cos 2θ` and `sin 2θ` have period π, so 0°/90°/180° gives only *two*
   independent equations, not three — `stokes_from_rotation_series` refuses it on the design
   matrix condition number. Separately, rotating the specimen by φ rotates (S1, S2) by **2φ**, and
   getting that sign backwards produces a Stokes image that is self-consistent, passes every
   realisability check, and is silently reflected about the analyser axis. **This bug was in the
   shipped code and a property test caught it.** Derivation is in the
   [`rotated_specimen` docstring](src/reefprint/acquire/series.py:68); do not "simplify" it.

3. **"Nobody uses polarised light" is FALSE.** Pirard, Lebichot & Krier (2007) is direct prior art
   on polarised-light imaging in ore microscopy. The narrow claim — *per-pixel full linear Stokes
   recovery*, which is not the same as imaging under crossed polars — appears to survive, but the
   paper is **unread**. Open finding **N1**. Read it before week 6. Do not discover this on stage.

4. **Provenance travels with the value, not in a comment.** Three of five phantom reflectances are
   `Provenance.PLACEHOLDER` and `test_no_placeholder_value_is_reported_as_measured` fails if one
   ever escapes into something presented as a measurement. Replacing them is an IMA/COM
   Quantitative Data File lookup, not a judgement call. Rule 1.

5. **The phantom proves the maths, not the mineralogy.** It is a test instrument whose only job is
   to produce a series with a closed-form correct answer, so a bug in the inversion cannot hide
   behind "real rocks are messy". Passing it is not evidence about minerals, and
   `experiments/001-week1-gate/README.md` says so in its own *What this does not show*. Never
   present leg (a) as more than it is.

---

## 6. Invariants — do not break these

From CLAUDE.md's nine rules, the ones that have already shaped code:

- **Never invent a number.** Flag every assumption in the code, not just the docs.
- **Split by locality, never by patch or image.** Patch splits void conformal exchangeability and
  silently invalidate every metric.
- **Report the trivial baseline** — majority class *and* metadata-only — alongside every metric.
- **Every metric carries a CI at honest n.** Coverage SD is `√(0.9·0.1/n)`: ~3.0 pp at n = 100,
  ~6.7 pp at n = 20. Do not claim tighter than the arithmetic allows.
- **Abstention emits a conservative default with a stated reason, never "unknown."** Abstention
  fires at ore transitions, which is exactly when holding the last setpoint is the worst
  available action. (The submitted abstract says "holds the last-known-good setpoint" — that is
  now contradicted, deliberately. See §8.)
- **No LLM computes a mineralogical or control value.** Agents route, select, orchestrate, explain.
- **Permissive licences only for anything shipped.** Maintain [`SBOM.md`](SBOM.md) in the *same
  commit* that adds a dependency.
- **Commit early and often, including failures.** Originality authentication happens after
  2 October; the commit history is the defence.
- **The falsification test is a deliverable, not a risk.** Report the result either way.

Never cut, whatever else goes: falsification test · locality splits · conservative-default
abstention · SBOM · backup video.

---

## 7. What is decided

| ADR | Decision | Consequence you will feel |
|---|---|---|
| [0001](docs/04-decisions/0001-ome-tiff-via-tifffile-not-bioformats.md) | OME-TIFF via `tifffile`, **not** Bio-Formats | Bio-Formats is GPL-2.0 and unassignable. No JVM anywhere. Vendor formats (`.czi`, `.nd2`) convert offline by hand if ever needed. |
| [0002](docs/04-decisions/0002-software-only-no-instrument-is-built.md) | **Software only. No instrument is built.** | Hardware budget R0. The rig is a costed BOM presented as a design — never imply it exists. No claim about µm/pixel, exposure, LED response or achievable R% accuracy may come from measurement. |

**Single technical decision-maker: Lethabo Mphukuile** (Domain lead — Business Informatics /
prior metallurgical engineering). Breaks all architecture ties; the decision is written up as an
ADR the same day. Two standing checks on the role are in CLAUDE.md — the same person is the
rusty met-eng *and* owns the ten-minute narrative, and neither should quietly become the spec.

---

## 8. Still open

| # | Open item | Owner / when |
|---|---|---|
| **N1** | Pirard 2007 prior art unread. Retighten or defend the novelty claim. | before week 6 |
| **N2** | 1/S0 noise floor means no fixed anisotropy threshold is defensible. Any discrimination rule must condition on S0 and report an interval. | week 2+ |
| **N3** | **Is LumenStone S3 v2 a stage rotation or an analyser rotation?** Decidable in one command; the command needs the 5.2 GB archive, which is on Sibusiso's machine. Blocks week-1 leg (b), and blocks KHANYA's ten-mineral symmetry test from producing a false negative. | **now** — ask Sibusiso |
| **F1** | Chromite-proxy collapse — the falsification test runs regardless and the result is published either way. | week 2 gate |
| **F2** | Talc/serpentine without SWIR is unproven. If it fails, drop to two properties. | week 2, empirical |
| **S2** | Plant history was generated under FloatStar closed-loop control. No causal claim from observational plant data. | any use of the Kaggle flotation dataset |
| — | LumenStone licence is informal and unnamed. Get terms in writing before publishing anything derived. | email `khvostikov@cs.msu.ru` |
| — | CGS National Core Library sampling policy. | phone call |
| — | **The submitted abstract contradicts Rule 5.** It says the system "abstains and holds the last-known-good setpoint"; we now hold that this is the worst available action at an ore transition. Do not hide it — the honest framing is *we tested our own abstention policy, found it failed exactly when it mattered, and changed it.* | the talk |
| — | Commits carry a UNISA email address while all docs say Wits. Originality authentication happens after finalist selection; a university address on every commit is a thread an IP office could pull. | before 2 October |

---

## 9. Repo map, short version

```
CLAUDE.md            constitution — outranks everything
CONTEXT.md           this file — situation report
SBOM.md              every dependency + licence. Rule 7. Never cut.
docs/BUILDLOG.md     append-only: what was tried, what worked, what did not
docs/00-STATUS.md    which docs are current vs superseded
docs/05-toolchain.md every piece of software we install, and what we decided not to
docs/04-decisions/   ADRs
src/reefprint/       acquire · calibrate · polarim · segment · texture · heads · trust · integrate · viz
tests/               one file per module. Red tests are the backlog, by design.
experiments/         numbered, each with its own README stating the result AND what it does not show
data/                DVC-tracked, never committed raw
```

---

## 10. How to update this file

At the end of any session that changed the state:

1. Bump **Last updated**, **Last commit**, and **Days to final** at the top.
2. Move anything finished out of §3 and into `docs/BUILDLOG.md` with the result.
3. Rewrite **the single next action** in §3. There must be exactly one, and it must be small
   enough to start immediately.
4. If something bit you, add it to §5 in concrete terms — the failure, not the lesson.
5. If a decision was made, write the ADR the same day and add the row to §7.

If this file and the code disagree, the code is right and this file is a bug.
