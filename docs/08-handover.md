# HANDOVER — implementation session, T-19 to the final

**Written 2026-09-12. For a fresh session picking up the `reefprint` branch and writing code.**

Read this, then `CLAUDE.md` (constitution — outranks everything), then the two corrections in §2
of this file, which contradict documents you will otherwise trust. Then start at §6.

- **Final:** 1 October 2026, 13:00 submission, 10-minute presentation. **19 days.**
- **Branch:** `reefprint`. Local `main` tracks `khanya/reefprint`. Push with
  `git push khanya main:reefprint`.
- **Suite today:** 314 passing, 7 deselected backlog tests. That backlog **is** the work list.
- **Standing instruction, every session that changes state:** push, append to
  `docs/BUILDLOG.md`, and tell Sibusiso on
  [KHANYA issue #1](https://github.com/Sibusiso-K/KHANYA/issues/1). Treat it as part of "done".

---

## 1. The two halves, and who owns what

**One build, two names, two deliberately separate commit histories** (ADR-0003 — MOTT runs an IP
assessment on the top entries, and two clean parallel histories are the originality defence).

| | REEFPRINT — `reefprint` branch | KHANYA — `main` branch |
|---|---|---|
| Owns | Physics, measurement, trust layer, `integrate` | Segmentation model, dashboard, modal mineralogy |
| Person | Lethabo | Sibusiso |
| State | 314 tests, CI, ADRs, SBOM | 87 tests, Stitch dashboard, trained model |

**Stay on `reefprint`.** Work the other half needs crosses via the bridge pattern (KHANYA's
`src/polarimetry.py` imports `reefprint.*` unchanged) — never by copying code across. Blurring
the histories damages the thing that protects the team in the IP assessment.

## 2. Two corrections. Believe these over any other document in the repo.

### 2.1 N3 is withdrawn — S3 v2's frames are not registered

`ENDGAME.md`, older `CONTEXT.md` text, and the talk storyboard all state that the geometry
discriminator found S3 v2 to be "stage rotations" or "`NEITHER`, leaning stage", and that the
extinction estimator "found no separation". **All of that measured nothing.**

The frames are not registered: the field rotates with the specimen, so a given pixel is a
different physical point in every frame. Frame-to-frame correlation against r000 decays along the
*rotated-image control* curve (`S3_test_01`: r005 +0.7114 vs 5°-control +0.6572; r040 +0.3129 vs
45°-control +0.2929), where a registered polarimetric series stays high and flat. The full-codebook
extinction run showed anisotropic phases higher than isotropic in **15 of 29** sections against a
coin-flip expectation of 14.5, with between-section spread **7×** the within-section spread across
minerals, and the estimator's own crossed-polars self-test reading **median 11.01** where ideal
pins it at **1.0**.

All three independent `NEITHER` runs, and the brightness-quantile re-run, were measuring across
unregistered frames. The answer was reproducible because the *bug* was reproducible — agreement
across two machines tested determinism, not validity. Full detail: `docs/BUILDLOG.md` session 17.

**What this does NOT break — and this matters for the talk.** The geometry discriminator *refused
the input*, and refusing was correct. It caught an unusable series instead of returning a
confident wrong map. Talk beats 6 and 7 survive and arguably improve: the honest line is now
*"our discriminator refused this public archive, and when we investigated why, we found the
frames aren't registered — a pixel is a different grain in each frame."* That is a better
demonstration of the trust layer than the old explanation.

**What it DOES break:** any slide or sentence claiming the archive is a stage rotation, or citing
"extinction found no separation" as a calibration result. `ENDGAME.md` §3's framing table has
exactly such a row. **It must be corrected before it reaches a judge**, because "how do you know
those frames are registered?" is a question a sharp reviewer asks, and the honest answer today is
"they are not, and we found that ourselves."

**Leg (b) is not failed — it has never been run.** Whether a 4φ signal survives proper
registration is open and untested. Naive centred de-rotation does not fix it (helps a lot on
`S3_test_03` r005, +0.3137 → +0.8142; hurts on `S3_test_01`), so the rotation centre is
off-image-centre and varies by section.

### 2.2 The headline accuracy number is from the wrong task

Several places quote **"mean IoU 0.872 / pixel accuracy 93.75%"**. Today's adversarial review
established that this is the **older binary ore/resin (FeM) pipeline**, not phase segmentation.
The brief requires *phase* identification. The real, checked-in phase numbers:

| Evaluation | Test images | Mean IoU (incl. background) | Pixel accuracy |
|---|---:|---:|---:|
| S2 phase segmentation | 12 | **0.5725** | 89.14% |
| S1 phase segmentation | 20 | **0.7116** | 85.93% |
| Older binary ore/resin | — | 0.8722 | 93.75% |

Quote the phase numbers. Quoting 0.872 for phase identification is the single easiest way to lose
credibility with a judge who opens the repo.

## 3. How we are actually scored — this is known, not guessed

From the official FAQ: **Innovation · Feasibility · Impact · Technical Execution · Presentation
Clarity.** Winners are announced only after MOTT completes an IP assessment on the top-ranked
solutions, and creators receive invention credits — so attributable authorship is part of winning.

Two facts that should shape every decision:
- **Mintek made UG2 commercially viable.** We are pitching a UG2 story to the institution that
  created the UG2 industry. Relevance is free; every claim gets checked by people who wrote the
  book. One overclaim costs more here than anywhere else.
- **The 2025 winner's shape:** domain engineering first, AI as the multiplier — not an ML project
  wearing a mining hat.

## 4. The brief's literal deliverables, and where we stand

**Superseded 2026-09-14.** This table was accurate on 12 Sep and is not any more — P1–P5 shipped in
the intervening two days. Rather than let a second stale copy drift out of sync with `WORKBOARD.md`
§2 the way this one did, the deliverables and the current status now live in exactly one place:

**`CLAUDE.md` §"What we are judged on"** carries the brief verbatim (this file predates that
section, which is why it isn't there yet in the text above). **[`docs/09-brief-compliance.md`](09-brief-compliance.md)**
is the live traceability ledger — one row per requirement, evidence as a path or test name, never
prose. Read that instead of trusting any table copied into a handover document, including the one
this replaced.

## 5. Today's independent review reached a verdict worth taking seriously

> *"The current positioning loses against a team that delivers the literal brief cleanly … Keep
> the existing segmentation pipeline; demonstrate chalcopyrite, pentlandite and pyrrhotite;
> connect its output through a real local OPC UA interface to an explicitly simulated circuit;
> and make one modest processability proxy auditable. **Move polarimetry off the critical
> path.**"*
> — `reports/TECHNICAL-REVIEW-2026-09-12.md` on `khanya/main`

Two independent analyses (that review, and the registration finding in §2.1) now point the same
way: **polarimetry is a research thread, not the submission's spine.** The submission is
segmentation → processability → plant interface, demonstrated offline with a visible refusal.

That is a strategic call for Lethabo as technical decision-maker, not one to make by drifting.
**Confirm it before building.** If confirmed, write it up as an ADR the same day.

## 6. The work, in priority order

Priorities assume the §5 reframe is confirmed. Each item names its acceptance test. **Do not mark
anything done without running the test and reading the output** — the project's own history
includes a reproducible answer that was a reproducible bug.

### P1 — OPC UA advisory server (biggest gap, explicit deliverable)
`tests/test_integrate.py::test_opc_ua_server_exposes_advisory_values`

Build a **real local OPC UA server** exposing advisory values, plus a **separate simulated
control client** that consumes them and visibly changes a parameter. Then demonstrate it
**refusing stale or degraded input**.

- `asyncua` is **LGPL-3.0**: fine on a general-purpose machine, **never** a sealed appliance —
  anti-tivoisation would make the deliverable unassignable to Mintek. Say "runs on plant IT
  hardware", never "embedded in the sensor".
- Positioning already set in `integrate/__init__.py`: **an advisory that replaces a laboratory
  turnaround, not a controller replacing MillStar/FloatStar** (Mintek owns both). Keep it.
- Every record carries `advisory_influenced` from record zero — once an advisory moves the plant,
  later data is no longer observational. Keep that flag; it is a strength, say it out loud.
- Add an **acknowledgement and expiry contract**: an advisory that is not consumed within its
  validity window must expire rather than be actioned stale.
- Label every simulated element `sim_`. A judge must never wonder which parts were real.

### P2 — One processability head, built properly
`tests/test_heads.py::test_fine_chromite_entrainment_risk_index` (and two siblings)

Three heads are specified and none exist. **Build one well rather than three thinly** — the
review's recommendation and the right call at T-19.

- **Fine-chromite entrainment risk** is the strongest candidate: Cr₂O₃ is the binding constraint
  on UG2 flotation, and it is the most legible to a Mintek metallurgist.
- **Oxidation index** is the documented fallback that does *not* depend on the texture residual —
  but note it was found **not computable from XRF majors** (no Fe²⁺/Fe³⁺ split). Do not resurrect
  it without new data.
- **NFG load** (talc/serpentine) is unproven without SWIR — open question 1. If it fails, we drop
  to two properties rather than claim it anyway.
- Whatever ships must be a **clearly labelled structural proxy** with its inputs, assumptions and
  a stated interval — not a number presented as a measurement. `reefprint.quantity` enforces
  this; `DESIGN_TARGET` provenance never passes `require_reportable()`.

### P3 — Latency benchmark (the brief says "real-time"; we have no number)
No test exists yet — write one.

Measure the **shipped** path end to end on the demo laptop: decode → inference → postprocess →
advisory emit. Report per-sample latency with its spread, not a best case. State the hardware.
A claim of "real-time" without a measured number on named hardware is exactly the kind of
overclaim that is most expensive in this room.

### P4 — Accuracy report done honestly
`tests/test_heads_falsification.py::test_the_falsification_test_has_been_run_on_real_bushveld_data`

Use the phase numbers from §2.2, not the binary ones. Every metric needs: locality-disjoint
grouping (`reefprint.trust.split` — patch splits flattered us by **126×**), a CI at honest *n*
(`LocalitySplit.n_groups`, localities not sections), and **both** trivial baselines —
majority-class and metadata-only, with uplift measured against the *stronger* one
(`reefprint.trust.baseline.ScoredMetric` will not construct without them).

We have a real positive result to report: on 1,112 Bushveld chromitite assays across 305
boreholes, chromite composition (Cr#, Mg#) adds significant PGE signal beyond Cr₂O₃ —
ΔR² = 0.0279, **p = 0.0002**, cluster-robust by borehole. **State its caveats before a judge finds
them:** modest effect size, and Cr# is arithmetically related to the Cr₂O₃ baseline.

For the texture falsification specifically: the honest output is *"not testable with available
data"*, published with a missing-data specification. That is Rule 9 working, not a failure.

### P5 — Leg (b) registration — research thread, only if P1–P4 are green
Not on the critical path. If time exists: estimate a per-frame transform **from the data**
(log-polar phase correlation, or ECC), since the filename angle alone does not undo it. Then
restrict to the inscribed region present at every angle, map the mask through the same transform,
and only then re-run `harmonic_signature`. The Kaggle dataset and kernel are already set up —
a re-run is one `kaggle kernels push`.

## 7. Rules that bind every line you write

From `CLAUDE.md`. These are enforced in code, not by good intentions:

- **Never invent a number.** `reefprint.quantity.Quantity` carries provenance and a mandatory
  source; arithmetic keeps the *weakest* input's provenance. `DESIGN_TARGET` never passes
  `require_reportable()`.
- **Split by locality, never by patch or image.** Measured cost of getting this wrong: **126×**,
  in the flattering direction.
- **Report both trivial baselines** beside every metric, uplift against the stronger.
- **Every metric carries a CI at honest *n*.**
- **Abstention emits a conservative default with a stated reason, never "unknown."** The type has
  **no field for a previous value** — holding the last setpoint is unreachable, not merely
  discouraged. Note the submitted abstract says the system "holds the last-known-good setpoint";
  we now hold that this is the *worst* action at an ore transition. The honest framing is *we
  tested our own abstention policy, found it failed exactly when it mattered, and changed it.*
- **No LLM computes a mineralogical or control value.** Agents route, select, explain.
- **Permissive licences only** for anything shipped. LumenStone has **no named licence** — only
  informal "free to use in research, cite the references". Its `petroscope` companion is GPL-3.0:
  **data yes, library never.** Rights clearance is an open risk the review flags as possibly
  unclosable in 19 days.
- **Commit early and often, including failures.** The commit history is the IP defence.

## 8. Traps this project has already fallen into

1. **A reproducible answer can be a reproducible bug.** Three runs, two machines, one invalid
   measurement. Agreement tests determinism, not validity. Before trusting any result, ask what
   would make it *your* bug, and check that first.
2. **A stage rotation inverts to zero anisotropy silently** — no exception, no NaN, every
   anisotropic mineral reported isotropic. Only `residual_rms` witnesses it. Hence
   `RotationSeries.geometry` defaults to `UNKNOWN`, never the convenient answer.
3. **The anisotropy noise floor goes as 1/S0**, so any fixed threshold is a reflectance-dependent
   classifier in disguise (finding N2).
4. **Raw extinction depth is not contrast-normalised** and must not be compared between minerals
   of differing brightness — N2 in a new costume.
5. **The phantom proves the maths, not the mineralogy.** Never present leg (a)'s 40.4× as a
   result about real ore.
6. **A resumed download can be silently corrupt.** Verify size and checksum before trusting a
   large file — this cost a session already.

## 9. First actions for the new session

1. Confirm §5's reframe with Lethabo. **Do not start building until this is answered** — it
   decides whether P1–P4 or P5 leads.
2. `uv sync && uv run pytest -m "not placeholder" -q` → expect **314 passed, 7 deselected**.
   Anything less is a regression, not a quirk.
3. Read `docs/BUILDLOG.md` session 17 (the registration finding) and
   `khanya/main:reports/TECHNICAL-REVIEW-2026-09-12.md` (the adversarial review).
4. Start P1. It is the largest gap against an explicit deliverable, and it is the beat the demo
   needs.
5. Correct `ENDGAME.md`'s §3 framing table — it currently cites an invalid extinction null as an
   asset. That lives on `main`, so raise it with Sibusiso rather than editing across branches.
