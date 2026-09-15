# WORKBOARD — the one file Lethabo and Sibusiso both read

**This is the shared board.** Between us we have eleven status documents across two branches, and
that is why nobody knows what is current. This file is the index and the scoreboard. It does not
replace the detail — it tells you which detail is still true and what is being worked on right now.

| | |
|---|---|
| **Last updated** | 2026-09-15 — **SIFT+RANSAC run against the real archive; the follow-up visual check on `S3_test_03` is genuinely inconclusive**, not a confirmation — the evidence for its offset remains non-visual (determinism, cross-section consistency, RANSAC inlier count). Also: advisory demo panel shipped, backup GIF regenerated, backbone guard widened, COCO checkpoint pinned on Kaggle |
| **Days to final** | **17** — final 1 October 2026, 13:00 hard submission, 10-minute pitch |
| **Freeze date** | **25 September** (feature freeze) · **30 September** (dry-run submission) |
| **REEFPRINT suite** | **350 passed, 4 deselected** — re-run and verified 2026-09-14 (+6 for the SIFT+RANSAC estimator's tests) |
| **KHANYA suite** | 87 passing (reported by main's audit; not re-run this session) |

**Detail lives elsewhere, and this file says which of it to trust:**

| Where | What it is | Trust it? |
|---|---|---|
| `CLAUDE.md` (reefprint) | Constitution — physics, the nine rules, the kill list | **Yes** — §Physics corrected 2026-09-12 per C3 |
| `CONTEXT.md` (reefprint) | Situation report | **Yes** — §3 table and §8 N3 row corrected 2026-09-12 per C1 |
| `docs/BUILDLOG.md` (reefprint) | Append-only record of what was tried | **Yes — this is the primary record** |
| `docs/08-handover.md` (reefprint) | Implementation handover, 12 Sept | Yes, and it is the parent of this file — but it **predates C3**, which it does not mention. Its §4 deliverables table was superseded 2026-09-14; it now points at the ledger |
| `docs/09-brief-compliance.md` (reefprint) | Requirements-traceability ledger, built 2026-09-14 | **Yes — this is the one place "have we met the brief?" is checkable, not asserted** |
| `STATUS.md`, `ENDGAME.md`, `JOINT-PLAN.md`, `PITCH.md` (main) | KHANYA's status set | Mixed — see C1 and C2 |
| `reports/TECHNICAL-REVIEW-2026-09-12.md` (main) | External adversarial review | Yes, as **feedback**. Findings 5 and 8 accepted (C3, P4); finding 6 accepted **in part** — see C3's last paragraph |

---

## 0. Corrections in force — these beat any other document in either branch

Anything below contradicts documents you will otherwise trust. Read them before writing a line.

### C1 — N3 is withdrawn. S3 v2's frames are not registered.

`ENDGAME.md`, older `CONTEXT.md` text and the talk storyboard state that the geometry
discriminator found S3 v2 to be a stage rotation, or `NEITHER` leaning stage, and that the
extinction estimator "found no separation". **All of that measured nothing.** The field rotates
with the specimen, so a given pixel is a different physical point in every frame. Correlation
against `r000` decays along the *rotated-image control* curve — `S3_test_01`: r005 **+0.7114** vs
5° control **+0.6572**; r040 **+0.3129** vs 45° control **+0.2929** — where a registered
polarimetric series stays high and flat.

- **What survives, and improves:** the discriminator *refused the input*, and refusing was
  correct. The honest line is *"our trust layer refused this public archive; we investigated why
  and found the frames aren't registered."* That is a better demonstration than the old one.
- **What must be deleted before a judge sees it:** any claim that the archive is a stage
  rotation, or that "extinction found no separation" is a calibration result. **`ENDGAME.md` §3's
  framing table has exactly such a row.** That file is on `main` — **Sibusiso's to fix.**
- **Leg (b) is not failed — it has never been run.** Whether a 4φ signal survives proper
  registration is open and untested.

Full detail: `docs/BUILDLOG.md` session 17.

### C2 — the headline accuracy number is from the wrong task

**"mean IoU 0.872 / pixel accuracy 93.75%" is the older binary ore/resin pipeline, not phase
segmentation.** The brief requires *phase* identification. Quote these instead:

| Evaluation | Test images | Mean IoU (incl. background) | Pixel accuracy |
|---|---:|---:|---:|
| **S2 phase segmentation** | 12 | **0.5725** | 89.14% |
| **S1 phase segmentation** | 20 | **0.7116** | 85.93% |
| ~~Older binary ore/resin~~ | — | ~~0.8722~~ | ~~93.75%~~ |

S2 per-class IoU: background 0.8709 · chalcopyrite 0.5755 · **magnetite 0.0000** · pyrrhotite
0.8695 · pentlandite 0.5468. The magnetite zero is real and must be stated, not buried — three
sulphides carry the "≥3 phases" deliverable, magnetite does not.

### C3 — RESOLVED 2026-09-12: the illumination is unpolarised, not crossed polars

**Status: CLOSED by [ADR-0005](docs/04-decisions/0005-unpolarised-illumination-with-a-rotating-analyser.md).**
Found this session by reading the code against the external review's finding #5; it was not in
`08-handover.md`. The prose is corrected across `CLAUDE.md`, `CONTEXT.md`, `README.md`,
`src/reefprint/__init__.py` and `polarim/stokes.py`, the BOM is reconciled to one analyser plus a
depolarising diffuser, and
`tests/test_polarim.py::test_an_isotropic_grain_under_a_fixed_polariser_modulates_fully` now pins
the counterexample so the false sentence cannot return. **The record of what was wrong is kept
below deliberately — it is a talk beat, not an embarrassment.**

The review claims our core sentence is false. Read literally against a *fixed polariser*, it is:

- `src/reefprint/polarim/stokes.py:10` says *"under crossed polars an isotropic phase shows no
  modulation as the analyser turns"*, and `CLAUDE.md`'s geometry table says the rotating-analyser
  arrangement has **"polariser and specimen fixed"**.
- With a fixed polariser, normal-incidence reflection off an isotropic grain **preserves the
  linear polarisation azimuth**. So (S0,S1,S2) = (I₀, I₀, 0), DOLP = **1**, and
  I(θ) = I₀cos²θ — *full* modulation. An isotropic grain goes dark at exactly one analyser angle
  (the crossed one), the same angle for every isotropic grain. The review is right about this.

**But the code does not implement that arrangement.** `acquire/phantom.py:203` sets
`magnitude = anisotropy × reflectance_pct`, so DOLP = `anisotropy`, and `phantom.py:98` sets
`anisotropy = 0.0` for cubic phases. That is the forward model for **unpolarised incident light**,
where polarisation is *generated* on reflection by differential reflectance between the eigen-axes:

- isotropic grain, unpolarised in → reflected light unpolarised → DOLP = 0 → no modulation ✔
- anisotropic grain, unpolarised in → DOLP = (|r₁|²−|r₂|²)/(|r₁|²+|r₂|²) = bireflectance contrast ✔

**So the forward model is sound; the sentence describing it names the wrong instrument.** Two
corroborations that the unpolarised reading is the intended one: `CLAUDE.md`'s own scaling
argument (analyser modulation goes as `a`, extinction as `a²`) only holds under this model, and
the phantom's numbers are internally consistent with it.

**What was done — it was a specification fix, not a physics rescue:**

1. ✅ The illumination arrangement is written down explicitly: **unpolarised (or depolarised)
   incident light with a rotating analyser** — *not* crossed polars.
2. ✅ Prose fixed. Note **"dark" was wrong twice over**: an unmodulated isotropic grain sits at
   `S0/2` throughout, and pentlandite at R ≈ 50% is one of the *brightest* phases on the section.
   The word is **flat**, not dark. The submitted abstract's two uses of "crossed polars" were
   checked and are **correct** — both describe the classical stage-rotation discipline, not ours.
3. ✅ Counterexample added as a test.
4. ✅ BOM reconciled — **one** analyser plus a depolarising diffuser, not a crossed pair.
5. ⚠ **Still outstanding, and it is the part that matters on stage.** The review's stronger point
   stands regardless of this fix: *the phantom validates
   recovery of the parameters we supplied it. It does not validate the mapping from crystal
   symmetry to those parameters.* `experiments/001-week1-gate/README.md` already says a version of
   this — make sure the talk does too.

**What we do NOT accept from the review:** its finding #6 asks us to drop the anti-hyperspectral
premise entirely. Chromite does have electronic (crystal-field) absorption features, so the
*blanket* phrasing "no absorption features" is wrong and should go. The narrower, defensible claim
— that molecular/vibrational SWIR mineral identification does not work on an opaque spinel that is
50–75 vol% of the ore — survives, and needs an ore-specific citation with a stated denominator
(volume vs mass vs image-area fraction are not interchangeable).

---

## 1. Lanes — who owns what

**One build, two names, two deliberately separate commit histories** (ADR-0003). MOTT runs an IP
assessment on the top entries; two clean parallel histories are the originality defence.
**Work crosses via the bridge pattern — KHANYA's `src/polarimetry.py` imports `reefprint.*`
unchanged. Never by copying code across branches.**

| | REEFPRINT — `reefprint` branch | KHANYA — `main` branch |
|---|---|---|
| Owns | Physics, measurement, trust layer, `integrate`, `heads` | Segmentation model, dashboard, modal mineralogy |
| Person | **Lethabo** | **Sibusiso** |
| State | 350 tests, CI, 5 ADRs, SBOM | 87 tests, Stitch dashboard, trained model |
| Push | `git push khanya main:reefprint` | `git push khanya main` |

**This file is edited on `reefprint` and mirrored to `main` by Sibusiso.** Do not edit it on both
sides — a shared board that disagrees with itself is worse than no board.

---

## 2. The scoreboard — the brief's literal deliverables

> Identify **at least three distinct mineral phases** from provided image datasets · an
> **accuracy report** · a **demonstration of how the model's output can be used to adjust plant
> parameters** · real-time · integrates with existing sorting or flotation controls.

**Full detail, evidence paths and the "exceeds because…" column now live in
[`docs/09-brief-compliance.md`](docs/09-brief-compliance.md) — this table is the summary, that is
the source of truth. Update both in the same commit.**

| Requirement | Status | Evidence | Owner |
|---|---|---|---|
| ≥3 mineral phases | 🟡 S2 gives nonzero IoU for three sulphides — **locality separation unverified**, magnetite IoU 0.0000 | ledger §1 row 1 | Sibusiso |
| Accuracy report | 🟡 **Bushveld chromite-composition result shipped, cross-checked bit-for-bit against an independent implementation.** Segmentation accuracy report (locality-disjoint IoU, CIs, baselines) still needs KHANYA's held-out predictions | ledger §1 row 2 | Both |
| Processability prediction | 🟡 **One head shipped** — fine-chromite entrainment risk, structural proxy with a worst-case bound; real literature constants still needed from the domain lead | `src/reefprint/heads/entrainment.py` | Lethabo |
| Integrates with controls | ✅ **Real local OPC UA server + separate simulated control client**, acknowledgement/expiry contract demonstrated | ledger §1 row 5 | Lethabo |
| Real-time | 🟡 **Two REEFPRINT-side stages benchmarked with a spread**, on named hardware — Stokes inversion and the OPC UA round trip. **Segmentation inference latency (KHANYA/main) is still unmeasured**; no end-to-end real-time claim exists yet | ledger §1 row 4 | Both |
| Offline demo | 🟢 `reefprint.viz.demo`, **three panels including the plant-parameter advisory/refusal**; backup GIF regenerated 2026-09-15 and shows all three | ledger §1 row 6 | Lethabo |

**Judged on:** Innovation · Feasibility · Impact · Technical Execution · Presentation Clarity.
Winners announced only after MOTT's IP assessment on top-ranked entries; creators receive
invention credits, so attributable authorship is part of winning. Full criterion-by-criterion
evidence: ledger §2.

**Two facts that shape every decision.** Mintek made UG2 commercially viable — we are pitching a
UG2 story to the people who wrote the book, so one overclaim costs more here than anywhere else.
And the 2025 winner's shape was domain engineering first, AI as the multiplier.

**The brief and the accuracy-driving literature are now both anchored in `CLAUDE.md`** (§"What we
are judged on" and §"What the literature says drives accuracy here") — read there for the seven
factors, each cited, and the new **Rule 10**: check the published method before inventing one.

---

## 3. The work queue

**The reframe is confirmed (ADR-0004), so this ordering is live — start at P1.** Each item names its acceptance test. **Nothing
is marked done without running the test and reading the output** — this project's own history
contains a reproducible answer that was a reproducible bug.

### P1 — OPC UA advisory server ✅ SHIPPED 2026-09-12

`tests/test_integrate.py::test_opc_ua_server_exposes_advisory_values` — **passing**, plus two
new tests for the finite-value/expiry-window guards and the round trip.

- **`reefprint.integrate.opcua_server.AdvisoryServer`** — a real local `asyncua.Server`
  (not a mock), bound to `127.0.0.1` on an ephemeral port, publishing every head under a
  `sim_advisories` folder. `asyncua` is **LGPL-3.0** — general-purpose machine only, never a
  sealed appliance; the module docstring says so and never claims embedding. Only importable
  with `uv sync --extra integrate`; `tests/test_integrate.py` skips cleanly without it via
  `pytest.importorskip`.
- **`reefprint.integrate.opcua_client.SimulatedControlClient`** — a separate process boundary
  that reads a head over the wire and either applies it to a `SimulatedPlantParameter` or
  returns `RefusedStaleAdvisory`. **No fallback field for a prior value exists on the refusal
  type** — the same discipline as `trust.abstain.Abstention`, applied at the transport layer
  so "hold the last setpoint" cannot re-enter through this seam either.
- **`AdvisoryRecord` extended**: `unit`, `emitted_at` (default `time.time()`), `valid_for_seconds`
  (default `inf`, back-compatible with the existing test), finite-value validation on every
  entry in `values`, and `is_expired()`. Internally stores `values` as a `MappingProxyType` so
  a caller cannot mutate a "frozen" record through its dict field after construction.
- **CI updated**: `.github/workflows/ci.yml` now runs `uv sync --all-groups --extra integrate`
  — deliberately *not* `--all-extras`, so the `ml` extra's PyTorch stays out of the default
  install per `pyproject.toml`'s "kept deliberately lean" note.
- **Still open, and it is P1's remainder, not P2's**: `verdict_state()`'s favourable-fallthrough
  bug named below belongs to **KHANYA's `src/decision_gap.py` on `main`**, not this branch —
  corrected in the issue to Sibusiso, not here. The demo script wiring `AdvisoryServer` +
  `SimulatedControlClient` into `reefprint.viz.demo` and a **latency measurement on the OPC UA
  path itself** are not yet done — folded into P3.
- Positioning kept as set in `integrate/__init__.py`: an advisory that replaces a *laboratory
  turnaround*, not a controller replacing MillStar or FloatStar (Mintek owns both).

### P2 — One processability head, built properly ✅ SHIPPED 2026-09-12 (fine-chromite entrainment risk)

`tests/test_heads.py::test_fine_chromite_entrainment_risk_index` — **passing**, plus five more
tests for the bound, the design-target refusal, and the abstention default.

- **`reefprint.heads.entrainment.fine_chromite_entrainment_risk`** — the structural proxy,
  `chromite_mass_fraction * fine_fraction * entrainment_factor * water_recovery` (Trahar 1976 /
  Johnson 1972 / Savassi et al. 1998 entrainment-factor framework). Returns a
  `HeadEstimate` with a **worst-case bound**, not a statistical confidence interval — the four
  inputs are a mix of measured, cited and assumed quantities, not independent random draws, and
  a normal-approximation CI would claim precision the proxy does not have. The bound is proven
  correct in the module docstring (product of nonnegative factors is monotone) and checked by
  `test_the_worst_case_bound_brackets_the_point_estimate_for_any_valid_inputs`.
- **`reefprint.heads.entrainment.BoundedFraction`** — a fraction plus its own `[low, high]`, all
  `Quantity`, mirroring `ConservativeDefault`'s validation shape. Kept local to this head until a
  second one (NFG load, oxidation index) needs the same contract.
- **This module computes the formula and nothing else.** It does not choose
  `entrainment_factor` or `water_recovery` — which literature classification curve, at what size
  cutoff, which plant's typical water recovery — because that is exactly the domain judgement
  Rule 6 forbids an LLM from making, and blind spot 8 says must not rest on one person either.
  Every value the test exercises is `ASSUMED`/`CITED` and labelled **illustrative** — **these are
  not the real numbers to quote in the accuracy report; the domain lead must supply and cite the
  real `entrainment_factor` and `water_recovery` before this head's output reaches a slide.**
- **`entrainment_risk_conservative_default`** wires Rule 5's own worked example (`trust.abstain`'s
  module docstring already names this exact head as `ASSUME_HIGH`) — an abstention on this head
  must not quietly default low, and the inversion check catches it if it does.
- **Oxidation index** is the documented fallback that does not depend on the texture residual —
  but it was found **not computable from XRF majors** (no Fe²⁺/Fe³⁺ split). Do not resurrect it
  without new data.
- **NFG load** (talc/serpentine) is unproven without SWIR — open question 1. If it fails we drop to
  two properties rather than claim it anyway.
- Review's naming point, accepted: call the existing liberation output an **"apparent 2D sulphide
  association index"** until specimen preparation and particle identity are verified. If these are
  intact polished sections rather than particulate mounts, connected regions separated by resin may
  not be feed particles at all. (This is KHANYA's output, on `main` — not built here.)
- **Still open, and it belongs to the domain lead, not to further code**: the real
  `entrainment_factor`/`water_recovery` citations, and which chromite `fine_fraction` size cutoff
  a UG2 grind curve actually supports. Feeding this head real segmentation output (chromite mass
  fraction) is also not wired up — folded into whichever integration task connects it.

### P3 — Latency benchmark ✅ SHIPPED 2026-09-12 (REEFPRINT-side stages only)

`tests/test_latency.py` — 4 tests passing. `reefprint.trust.latency` is the instrument
(`LatencyMeasurement`, `measure_stage`), reporting mean/median/**p95**/sd at honest *n*, never a
best case. `experiments/005-latency-benchmark/` runs it for real and commits the numbers.

- **Measured, on this hardware (Windows 11, AMD64):** Stokes inversion ≈ 6.7 ms/call at 64×96,
  ≈ 105 ms/call at 192×256 (36 angles, the week-1 gate's default); the OPC UA advisory
  publish+connect+read round trip ≈ 8.3 ms/call, including a fresh connection every time (the
  worst case a non-persistent client hits).
- **Not measured, and said so in the report, not discovered by a judge:** segmentation
  inference, decode, postprocess — KHANYA's stages, behind a trained checkpoint absent from
  this checkout (confirmed absent from the technical review's clone too). **No end-to-end
  "real-time" claim is made.** Closing this needs a matching benchmark on `main`, same
  instrument (importable via the bridge pattern), reported in the same table.
- p95, not just mean, is reported — a control loop cares about the tail it has to tolerate,
  not the average.

### P4 — the falsification gate, done honestly ✅ SHIPPED 2026-09-12 (Bushveld half)

The placeholder `tests/test_heads_falsification.py::test_the_falsification_test_has_been_run_on_real_bushveld_data`
is **deleted, per its own instruction** — something has run, and the result is recorded here and
in `docs/BUILDLOG.md` session 22.

- **The literal H0 remains untestable and that is the reported result** (Rule 9): `texture_features`
  is structurally missing (T1) and pyroxene fraction is not a column (T2). "Not testable with
  available data" is published with this missing-data specification, not silently dropped.
- **The accepted pivot HAS run on real data**: `experiments/006-bushveld-chromite-falsification/`
  reproduces, **reefprint-natively** (no import from `main` — per ADR-0003), whether chromite
  composition (Cr#, Mg#, Barnes & Roeder 2001) adds PGE signal beyond Cr₂O₃ alone, on
  **1,112 Bushveld chromitite assays across 305 boreholes**: **ΔR² = 0.0279, p = 0.0002**,
  cluster-robust by borehole.
- **Cross-checked, not just computed**: this run is **bit-for-bit identical to seventeen
  significant figures** against Sibusiso's independent implementation on `khanya/main`
  (`src/chromite_pge_falsification.py`, `reports/chromite_pge_falsification.json`) — two
  separately written programs on the same data landing on the same number is real verification,
  and it is the strongest form ADR-0003's two-history separation can produce.
- `tests/test_bushveld_chromite_falsification.py` (4 tests) exercises the CSV-parsing and
  cation-ratio harness against synthetic data — same reason `test_s3v2_reader.py` doesn't need
  the real S3 v2 archive: `data/` is gitignored, so CI checks the harness, and the real run
  (done once, by hand) is what's recorded.
- **Caveats stated before a judge finds them** (in the experiment README): modest effect size;
  Cr# is arithmetically related to the Cr₂O₃ baseline; it is *fitted* association, not an
  out-of-locality predictive evaluation; boreholes within one orebody are not automatically
  independent localities. Report it as *"a separate geochemical association analysis"* — **never**
  as evidence that texture predicts processability, and never as the texture H0 rejected.
- **Still open, and confirmed genuinely blocked, not just unscheduled** (checked 2026-09-13):
  every metrics file committed on `main` is a single **pooled** confusion matrix over all 12 S2
  test images — no per-image or per-locality breakdown exists to un-pool. `split_ids()` reads
  train/test directories and does not consume a locality manifest, and none exists in the repo.
  The trained checkpoint is also absent from this checkout. None of the three can be built or
  approximated from this side without contradicting rule 1 — this is Sibusiso's, on `main`, and
  needs new artefacts (per-image metrics, a locality manifest, the checkpoint) before
  `reefprint.trust.split`/`baseline`/`conformal` can be pointed at any of it.

### P5 — Leg (b) registration 🟡 RUN 2026-09-13, real result, NOT yet a claim

`reefprint.acquire.registration.estimate_rotation_centre` — a coarse-to-fine correlation search
over the rotation-centre offset, using each frame's *known* nominal angle (never estimated) to
reduce the search from a blind per-frame-pair problem to one 2-D search for the whole series.
Validated on synthetic data with a known offset (`tests/test_registration.py`, 7 tests) — **only
after fixing a real bug found while validating it**: the first version passed the search offset
directly as the rotation point instead of adding it to the image centre first, silently exploring
the wrong region of the plane while still returning plausible-looking numbers. Two earlier
algebraic derivations (relating measured translations to the centre offset via a linear system)
were also tried and abandoned as wrong before switching to direct correlation-search — see
`docs/BUILDLOG.md` session 23.

**Run for real on Kaggle** (`lethabomh14/reefprint-p5-registration`, ~10 min, CPU only) — not
locally, since a full section needs ~5 GB and this machine had 155 MB free. Full result and
caveats: `experiments/007-s3v2-registration/README.md`. Headline, **the naive-condition state,
which is solid**: naive centred de-rotation clears `DETECTION_SNR` for `snr_2` on all 5
measurable sections, confirmed against N3's original zero-registration method
(`experiments/008-n3-original-method-rerun/`, `NEITHER` on all 5 — a registration-methodology
difference, not a bug). **The registered-offset numbers are NOT solid — see below.**

**⚠️ 2026-09-13, escalated: the registration search is not reproducible on real data, with
unchanged code and unchanged input** (`experiments/010-s3test03-masked-rerun/README.md`).
Attempting the mask fix `experiments/009`'s visual check recommended for `S3_test_03` surfaced a
bigger problem underneath it: re-running the *unmasked* search on that same section, same code,
same archive, found a completely different offset than session 23 did (~50 px this time vs
~397 px before) — while the naive condition's own numbers, computed from the same decoded
frames, reproduce bit-for-bit across both runs. That rules out a data/decode difference and
narrows it to the search itself: the working hypothesis is that real mineral texture's
self-similarity gives the correlation objective multiple near-tied local optima, and the coarse
grid's `if score > best_score` has no tie-break rule for when floating-point noise decides
between them (CLAUDE.md Rule 5: sort every traversal, tie-break every min/max — this does
neither).

**Consequence: no specific registered-offset number for any of the 5 sections should be quoted
to the precision it was reported at** — `S3_test_01/02/07/12`'s registered verdicts were not
re-checked for run-to-run stability and may or may not be as fragile as `S3_test_03`'s turned
out to be. The mask fix itself also did not help — it found an even larger, still-wrong-looking
offset for `S3_test_03` and a *worse* verdict (`NEITHER`). **This is now a real, unbounded piece
of engineering work** (a determinism check on the search, a landscape diagnostic, then a
tie-break rule), not a quick follow-up, and it is the point ADR-0004's "P5 only if time exists"
condition needs re-checking against.

**2026-09-14 — a second, published estimator added, per Rule 10, before repairing the first.**
`reefprint.acquire.registration.estimate_rotation_centre_sift_ransac` — SIFT keypoint matching +
RANSAC-fitted rigid transform, per frame, the method Korshunov et al. 2025 (the LumenStone dataset
authors) publish for XPL/PPL registration on this same dataset family. Validated on synthetic data
the same way the grid search was (`tests/test_registration.py`, 6 new tests): recovers a known
off-centre offset to well under a pixel, a correctly-centred negative control reads near zero,
per-frame fitted angle agrees with the known nominal angle, and — **the property the grid search
turned out to lack** — bit-for-bit identical output across repeated calls on identical input,
because `skimage.measure.ransac`'s `rng` is seeded rather than left to draw from unseeded global
state. No new dependency (`scikit-image` already declared).

**2026-09-15 — run against the real archive (`experiments/011-sift-ransac-registration/`), and
the determinism check passed on real data.** `S3_test_01`, run twice in-process, returned
bit-for-bit identical output — the property `experiments/010` proved the grid search lacks. On
four of five sections (`01`, `02`, `07`, `12`) SIFT+RANSAC and the grid search agree closely, both
in offset (within ~3–8 px) and verdict. **On the fifth — `S3_test_03`, exactly the section the
grid search's `FOURTH` verdict was already retracted on (§0 C1) — SIFT+RANSAC returns offset
(−111, 22), sitting inside the same tight band the other four sections' offsets occupy, with
verdict `SECOND`, matching the naive condition's own reading and `experiment 009`'s visual-check
argument.** The grid search's own `S3_test_03` answer, (−397, 41), is the outlier against that
pattern. **This is not yet a quotable `S3_test_03` claim** — the same visual check 009 ran on the
grid search's offset has not yet been run on this one, and a "plausible" offset was already wrong
once on this exact section. Full table, caveats, and a genuine cost finding (per-section runtime
tracked inlier count, not frame count — up to 17,074 inliers on `S3_test_03`, driving ~40 min
sections even at 24 frames) in `experiments/011-sift-ransac-registration/README.md`.

**2026-09-15 — the visual check ran, and it is genuinely inconclusive, not a confirmation.**
`experiments/012-s3test03-sift-visual-check/`: `experiment 009`'s exact method, extended to three
candidates (naive/grid/sift) instead of one. Full-frame overlays for all three read the same way
`009`'s naive/grid pair already did — broadly similar yellow-green coverage, no candidate
obviously more coherent. A zoomed, programmatically-selected landmark did not resolve it either.
**A raw correlation re-check was tried and rejected as circular** — it favours the grid search's
own offset, unsurprising since whole-frame correlation is literally that search's optimisation
objective, so it cannot arbitrate between the two candidates. **The working explanation is the
same self-similarity `experiments/010` already named**: a texture rich enough to give a
correlation search multiple near-tied optima is rich enough that a human eye cannot always
distinguish a genuine grain match from a coincidental one either. `009`'s own check worked because
that section had one unusually distinctive, trackable grain; this landmark did not.

**What still favours SIFT+RANSAC's offset, none of it visual:** determinism on real data
(`experiments/011`), cross-section offset-magnitude consistency (011's four other sections),
harmonic-verdict agreement with the naive condition, and — the argument this experiment actually
adds — **up to 17,074 independently RANSAC-matched keypoint inliers in a single frame, all
consistent with one rigid transform at under 1.5 px residual**, a form of internal cross-check the
grid search has no equivalent of. Full writeup: `experiments/012-.../README.md`.

**Still not promoted to a claim.** The grid search's determinism status on the other four sections
remains the open question `experiments/010` left it as — only SIFT+RANSAC's determinism has been
checked, not the grid search's, on any run to date.

---

## 4. Open decisions — Lethabo's call, and the build waits on the first one

| # | Decision | Recommendation | State |
|---|---|---|---|
| **D1** | **Does polarimetry come off the critical path?** | **Yes — confirmed.** Submission spine is segmentation → processability → plant interface, demonstrated offline with a visible refusal. Polarimetry is the named measurement research component. Nothing is deleted and the claim is not withdrawn — leg (b) is *untested*, not *negative*. | ✅ **CLOSED 2026-09-12** — [ADR-0004](docs/04-decisions/0004-polarimetry-is-a-research-thread-not-the-submission-spine.md). P1 is unblocked. |
| **D2** | How to resolve **C3**? | **Adopt unpolarised.** Prose corrected in five files, BOM reconciled, counterexample test added. | ✅ **CLOSED 2026-09-12** — [ADR-0005](docs/04-decisions/0005-unpolarised-illumination-with-a-rotating-analyser.md). |
| **D3** | **T1** — the texture-plus-chemistry dataset does not exist publicly. Email Kaufmann/Veksler (same Thaba mine as the CSV in hand), report-as-blocked, or pivot? | Report as blocked *and* send the email — they are not exclusive. | OPEN |
| **D4** | **T2** — pyroxene fraction is not a column. Derive a normative silicate proxy from SiO₂/Al₂O₃/CaO with a cited method, or leave absent? | Leave absent unless a citation is found. Rule 6 forbids an LLM deriving it. | OPEN |
| **D5** | LumenStone rights. Informal "free to use, cite the references", **no named licence**; `petroscope` companion is GPL-3.0 (**data yes, library never**). The review flags this as possibly unclosable in 19 days. | Email `khvostikov@cs.msu.ru` now; prepare the fallback sentence. | OPEN |
| **D6** | Commits carry a UNISA email while all docs say Wits. Originality authentication follows finalist selection. | Reconcile before 2 October. | OPEN |

**Also settled and not to be relitigated:** the review's point that **pyrrhotite is not a universal
PGE reject phase** is accepted — Merensky work associates PGEs with chalcopyrite, pentlandite *and*
pyrrhotite. Remove default pyrrhotite-rejection advice from the Bushveld presentation and require
an explicit, versioned ore-and-objective recipe.

---

## 5. Rules that bind every line — enforced in code, not by good intentions

- **Never invent a number.** `quantity.Quantity` carries provenance and a mandatory source;
  arithmetic keeps the **weakest** input's provenance. `DESIGN_TARGET` never passes
  `require_reportable()`.
- **Split by locality, never by patch or image.** Measured cost of getting it wrong: **126×**, in
  the flattering direction (patch-split MAE 0.0017 vs honest 0.2119).
- **Report both trivial baselines** beside every metric; uplift against the stronger.
- **Every metric carries a CI at honest *n*.** Coverage SD ≈ 3.0 pp at n=100, 6.7 pp at n=20.
- **Abstention emits a conservative default with a stated reason, never "unknown."** The type has
  **no field for a previous value** — holding the last setpoint is unreachable, not discouraged.
  *The submitted abstract says the system "holds the last-known-good setpoint" and we now hold that
  this is the worst action at an ore transition.* Do not hide it: **we tested our own abstention
  policy, found it failed exactly when it mattered, and changed it.**
- **No LLM computes a mineralogical or control value.** Agents route, select, explain.
- **Permissive licences only** for anything shipped. SBOM updated in the *same commit* as the
  dependency.
- **Commit early and often, including failures.** The commit history is the IP defence.

**Never cut:** falsification test · locality splits · conservative-default abstention · SBOM ·
backup video. **Kill list, in order:** federated layer → four of five agents (keep Curator) →
adaptive illumination → AASX → OMF → multilingual UI → Hailo → T+45.

---

## 6. Traps this project has already fallen into

1. **A reproducible answer can be a reproducible bug.** Three runs, two machines, one invalid
   measurement. Agreement tests determinism, not validity. Before trusting a result, ask what would
   make it *your* bug and check that first.
2. **A stage rotation inverts to zero anisotropy silently** — no exception, no NaN, every
   anisotropic mineral reported isotropic. Only `residual_rms` witnesses it, sitting at exactly
   `S0/(2√2)`. Hence `RotationSeries.geometry` defaults to `UNKNOWN`.
3. **The anisotropy noise floor goes as 1/S0** (finding N2), so any fixed threshold is a
   reflectance-dependent classifier in disguise.
4. **Raw extinction depth is not contrast-normalised** and must not be compared between minerals of
   differing brightness — N2 in a new costume.
5. **The phantom proves the maths, not the mineralogy.** Never present leg (a)'s 40.4× as a result
   about real ore. C3 sharpens this: it does not even validate the symmetry→parameter mapping.
6. **A resumed download can be silently corrupt.** Verify size and checksum before trusting a large
   file — this cost a session already.
7. **Eleven status documents is why this file exists.** Adding a twelfth is not the fix.

---

## 7. Verify you are in a good state

```bash
uv sync && uv run ruff check . && uv run ruff format --check .
```

```bash
uv run pytest -m "not placeholder" -q
```

Expect **350 passed, 4 deselected**. Anything less is a regression, not a quirk.

```bash
uv run pytest -m placeholder -q --no-header -rf
```

Expect **4 failed** — the backlog, not breakage. As of 2026-09-12 (post-P1, P2, P4) they are:

| Test | Queue item |
|---|---|
| `test_heads.py::test_naturally_floating_gangue_load` | deferred — no SWIR (open question 1) |
| `test_heads.py::test_stockpile_oxidation_index` | deferred — no Fe²⁺/Fe³⁺ split |
| `test_texture.py::test_falsification_test_controls_for_cr2o3_and_pyroxene_fraction` | blocked — T1/T2 (the literal texture H0; see P4's closure note for the accepted pivot) |
| `test_acquire.py::test_the_week_1_gate_runs_on_a_public_reflected_light_rotation_series` | P5 |

---

## 8. Session ritual — this is what "done" means

Every session that changes state, no exceptions:

1. **Append to `docs/BUILDLOG.md`** — what was tried, what worked, what did not. Append-only.
2. **Update this file**: the date, the suite counts, the scoreboard row you moved, and §4 if a
   decision closed. If something bit you, add it to §6 as *the failure*, not the lesson.
3. **Update `CONTEXT.md` §3's single next action** if the next action changed.
4. **If a decision was made, write the ADR the same day** into `docs/04-decisions/`.
5. **If a dependency was added, update `SBOM.md` and `docs/05-toolchain.md` in the same commit.**
6. **If a deliverable's state changed, update its row in `docs/09-brief-compliance.md` in the same
   commit.** Evidence is a path or a test name, never prose — a row without one is not done.
7. **If a task had a published method, the ADR or buildlog entry names it and says why we are or
   are not using it** (Rule 10, `CLAUDE.md`).
8. **Commit and push** — `git push khanya main:reefprint`.
9. **Tell Sibusiso.** [Issue #5](https://github.com/Sibusiso-K/KHANYA/issues/5) is open, asking
   for `best.pt`, S1/S2, LumenStone V1, and the S1 v1 test-stem list — the Workstream B/C
   prerequisites. Otherwise, open a fresh issue on
   [Sibusiso-K/KHANYA](https://github.com/Sibusiso-K/KHANYA/issues) and link the commit.

A stale board is worse than none, because it will be trusted. **If this file and the code disagree,
the code is right and this file is the bug.**
