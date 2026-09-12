# WORKBOARD — the one file Lethabo and Sibusiso both read

**This is the shared board.** Between us we have eleven status documents across two branches, and
that is why nobody knows what is current. This file is the index and the scoreboard. It does not
replace the detail — it tells you which detail is still true and what is being worked on right now.

| | |
|---|---|
| **Last updated** | 2026-09-12, 21:10 SAST — **P2 (fine-chromite entrainment risk) SHIPPED** |
| **Days to final** | **19** — final 1 October 2026, 13:00 hard submission, 10-minute pitch |
| **Freeze date** | **25 September** (feature freeze) · **30 September** (dry-run submission) |
| **REEFPRINT suite** | **322 passed, 5 deselected** — re-run and verified 2026-09-12 (+6 for P2's entrainment-risk head, one more placeholder now built) |
| **KHANYA suite** | 87 passing (reported by main's audit; not re-run this session) |

**Detail lives elsewhere, and this file says which of it to trust:**

| Where | What it is | Trust it? |
|---|---|---|
| `CLAUDE.md` (reefprint) | Constitution — physics, the nine rules, the kill list | **Yes** — §Physics corrected 2026-09-12 per C3 |
| `CONTEXT.md` (reefprint) | Situation report | **Yes** — §3 table and §8 N3 row corrected 2026-09-12 per C1 |
| `docs/BUILDLOG.md` (reefprint) | Append-only record of what was tried | **Yes — this is the primary record** |
| `docs/08-handover.md` (reefprint) | Implementation handover, 12 Sept | Yes, and it is the parent of this file — but it **predates C3**, which it does not mention |
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
| State | 314 tests, CI, 3 ADRs, SBOM | 87 tests, Stitch dashboard, trained model |
| Push | `git push khanya main:reefprint` | `git push khanya main` |

**This file is edited on `reefprint` and mirrored to `main` by Sibusiso.** Do not edit it on both
sides — a shared board that disagrees with itself is worse than no board.

---

## 2. The scoreboard — the brief's literal deliverables

> Identify **at least three distinct mineral phases** from provided image datasets · an
> **accuracy report** · a **demonstration of how the model's output can be used to adjust plant
> parameters** · real-time · integrates with existing sorting or flotation controls.

| Requirement | Status | Owner |
|---|---|---|
| ≥3 mineral phases | 🟡 S2 gives nonzero IoU for three sulphides — **locality separation unverified** | Sibusiso |
| Accuracy report | 🟡 Partial — needs honest grouping, CIs, trivial baselines | Both |
| Processability prediction | 🟡 **One head shipped** — fine-chromite entrainment risk, structural proxy with a worst-case bound; real literature constants still needed from the domain lead | Lethabo |
| Integrates with controls | ✅ **Real local OPC UA server + separate simulated control client**, acknowledgement/expiry contract demonstrated | Lethabo |
| Real-time | 🔴 **No latency benchmark exists anywhere** | Sibusiso |
| Offline demo | 🟢 `reefprint.viz.demo`, backup GIF exists | Lethabo |

**Judged on:** Innovation · Feasibility · Impact · Technical Execution · Presentation Clarity.
Winners announced only after MOTT's IP assessment on top-ranked entries; creators receive
invention credits, so attributable authorship is part of winning.

**Two facts that shape every decision.** Mintek made UG2 commercially viable — we are pitching a
UG2 story to the people who wrote the book, so one overclaim costs more here than anywhere else.
And the 2025 winner's shape was domain engineering first, AI as the multiplier.

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

### P3 — Latency benchmark · no test exists yet, write one

The brief says "real-time" and we have no number. Measure the **shipped** path end to end on the
demo laptop: decode → inference → postprocess → advisory emit. Report per-sample latency **with its
spread, not a best case**, and state the hardware. A "real-time" claim without a measured number on
named hardware is the most expensive kind of overclaim in this room.

### P4 — Accuracy report done honestly · `tests/test_heads_falsification.py::test_the_falsification_test_has_been_run_on_real_bushveld_data`

Use C2's phase numbers, not the binary ones. Every metric needs locality-disjoint grouping
(`reefprint.trust.split`), a CI at honest *n* (`LocalitySplit.n_groups` — localities, not
sections), and **both** trivial baselines with uplift against the *stronger* one
(`trust.baseline.ScoredMetric` will not construct without them).

We have a real positive result: on **1,112 Bushveld chromitite assays across 305 boreholes**,
chromite composition (Cr#, Mg#) adds significant PGE signal beyond Cr₂O₃ — **ΔR² = 0.0279,
p = 0.0002**, cluster-robust by borehole. **State its caveats before a judge finds them:** modest
effect size; Cr# is arithmetically related to the Cr₂O₃ baseline; it is *fitted* association, not
an out-of-locality predictive evaluation; and boreholes within one orebody are not automatically
independent localities. Report it as *"a separate geochemical association analysis"* — **never** as
evidence that texture predicts processability or that H₀ was rejected.

For the texture falsification itself the honest output is **"not testable with available data"**,
published with a missing-data specification. That is Rule 9 working, not a failure.

### P5 — Leg (b) registration · research thread, only if P1–P4 are green

Not on the critical path. If time exists: estimate a per-frame transform **from the data**
(log-polar phase correlation, or ECC) — the filename angle alone does not undo it. Naive centred
de-rotation does not fix it (helps a lot on `S3_test_03` r005, +0.3137 → +0.8142; hurts on
`S3_test_01`), so the rotation centre is off-image-centre and varies by section. Then restrict to
the inscribed region present at every angle, map the mask through the same transform, and only then
re-run `harmonic_signature`. Kaggle dataset and kernel are already set up — one `kaggle kernels push`.

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

Expect **322 passed, 5 deselected**. Anything less is a regression, not a quirk.

```bash
uv run pytest -m placeholder -q --no-header -rf
```

Expect **5 failed** — the backlog, not breakage. As of 2026-09-12 (post-P1, post-P2) they are:

| Test | Queue item |
|---|---|
| `test_heads.py::test_naturally_floating_gangue_load` | deferred — no SWIR (open question 1) |
| `test_heads.py::test_stockpile_oxidation_index` | P2 (deferred — no Fe²⁺/Fe³⁺ split) |
| `test_heads_falsification.py::test_the_falsification_test_has_been_run_on_real_bushveld_data` | **P4** |
| `test_texture.py::test_falsification_test_controls_for_cr2o3_and_pyroxene_fraction` | P4 (blocked — T1/T2) |
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
6. **Commit and push** — `git push khanya main:reefprint`.
7. **Tell Sibusiso.** Issue #1 is closed; open a fresh issue on
   [Sibusiso-K/KHANYA](https://github.com/Sibusiso-K/KHANYA/issues) and link the commit.

A stale board is worse than none, because it will be trusted. **If this file and the code disagree,
the code is right and this file is the bug.**
