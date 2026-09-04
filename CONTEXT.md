# CONTEXT — read this second, after CLAUDE.md

**Purpose:** you have just opened this folder in a new session, or on a different machine, or
after a week away. This file gets you from nothing to working in about five minutes. `CLAUDE.md`
is the constitution — *what is true and what the rules are*. This file is the situation report —
*where we are, what to do next, and what has already bitten us.*

Keep it current. A stale CONTEXT.md is worse than none, because it will be trusted.

- **Last updated:** 2026-09-04
- **Last commit at time of writing:** data-independent texture mechanics implemented on `reefprint`
- **Days to final:** 27 (final is 1 October 2026, 13:00 submission, 10-minute presentation)
- **Abstract deadline: 30 August 2026 — submitted and complete.** Drafted and rendered:
  [`docs/06-abstract.md`](docs/06-abstract.md) is the wording,
  [`docs/06-abstract.pdf`](docs/06-abstract.pdf) is what was sent. **The submission packet is
  complete and has no placeholders** — abstract, mentor
  request (we have no mentor, so we are asking Mintek to assign one), team-member details, and
  the email body are all in `submission/`, which is **gitignored because it carries all three
  members' SA ID numbers**. Do not move those into `docs/`; git history outlives a repo's
  visibility setting. What is genuinely still open: confirming "Team Sonar" is the registered
  team name, conference registration for 2 October, and a read-aloud voice pass on the abstract.

---

## 1. Read order

| # | File | Why |
|---|---|---|
| 1 | [`CLAUDE.md`](CLAUDE.md) | Constitution. The physics, the nine rules, the kill list. Outranks everything. |
| 2 | **this file** | Where we are and what to do next. |
| 3 | [`docs/BUILDLOG.md`](docs/BUILDLOG.md) | What we tried, what worked, what did not, and why. Append-only. |
| 4 | [`docs/00-STATUS.md`](docs/00-STATUS.md) | Which docs are current vs superseded. `docs/` holds four generations of design and they contradict each other on purpose. |
| 5 | [`docs/04-decisions/`](docs/04-decisions/) | ADRs. Three so far, all binding. ADR-0003 is the naming: **REEFPRINT, otherwise known as KHANYA**. |
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
| **1** | Rotation series in, per-pixel Stokes out, pentlandite dark / pyrrhotite lit, on screen | **Leg (a) phantom: PASSED**, 40.4× separation. **Leg (b) real public data: N3 measured, verdict `NEITHER`** ← *we are here*. Sibusiso ran `experiments/002-s3v2-geometry/run.py` against the real `S3_v2.zip` twice, identically: 29 sections, 116,000 pixels, 2nd-harmonic SNR 2.5× its floor, 4th-harmonic SNR 1.1×, threshold 5.0×. Neither harmonic clears detection. Not clearance for the Stokes inversion — see §8 N3 for why this leans stage, not neutral. |
| 2 | Falsification test computed, with CI | **Statistical core built and tested** (`reefprint.heads.falsification`, cluster-robust CR1 by locality, honest n = locality count). Proven against synthetic data with a known ground truth — a real texture effect detected, a real absence not manufactured. **Real Bushveld geochemistry now in hand for 3 of 4 required inputs** — `data/bushveld_thaba_chromitite/` (Bachmann 2019, Mendeley, CC BY 4.0, cited): 1,205 assay rows give `target` (real PGE grades), `Cr2O3_%` (half of `baseline_features`), and 317-borehole `localities`, all real, none synthetic. **`texture_features` is still the missing piece, and it is structurally missing, not administratively** — see §8. |
| 3 | Conformal coverage within band, per held-out locality | **implemented and tested** (`reefprint.trust.conformal`; Week 3 gate harness) |
| 4 | Zero silent failures under degraded input | **implemented and tested** (`reefprint.trust.quality`; explicit refusal for each named degradation) |
| 5 | End-to-end offline on one laptop | **implemented, tested, and verified** (`reefprint.viz.demo` + visible refusal path) |
| 6 | Backup demo video exists | **green** — paired host generated and verified the two-screen GIF from `experiments/004-backup-video` |

**Built and tested:** `reefprint.polarim.stokes` (the inversion),
`reefprint.polarim.extinction` (the fourth-harmonic estimator — leg (b)'s path if N3 is
confirmed), `reefprint.polarim.geometry` (**which** rotation this is — finding N3),
`reefprint.acquire.series` (the acquisition boundary), `reefprint.acquire.store`
(OME-TIFF round-trip), `reefprint.acquire.phantom` (synthetic ground truth, both
geometries), `reefprint.bridge` (labelled masks + a rotation series → per-mineral anisotropy
with its noise floor; the seam KHANYA hands data across — **now two mirrored guards**,
`measure_section` for an analyser series and `measure_section_extinction` for a stage one, each
unconditionally refusing the other's geometry), `reefprint.viz.anisotropy` (the three-panel
figure).

**Also built and tested:** `reefprint.trust.split` (rule 2), `reefprint.trust.baseline` (rule 3),
`reefprint.trust.abstain` (rule 5) — locality splits, trivial baselines, and conservative-default
abstention are no longer backlog. All three needed a second pass in sessions 8–10 to close a
shared defect: a comparison or interval that should have been gated on whether *n* could resolve
it, and silently wasn't. See `docs/BUILDLOG.md` sessions 8, 9, 10.

**Also built and tested:** `reefprint.heads.falsification` (the week-2 gate's statistical core —
cluster-robust CR1 inference on texture uplift, grouped by locality, `MIN_LOCALITIES_FOR_INFERENCE
= 5` refuses inference below that count per Rule 4, baseline R² reported per Rule 3). Proven only
against synthetic data so far — see `tests/test_heads_falsification.py`'s placeholder test for
what real data is still missing.

**Not built:** `heads`' three domain outputs (entrainment risk, NFG load, oxidation
index), `integrate`, and the
hardware-facing half of `acquire` (which, per ADR-0002, has no rig to drive). Each has failing tests naming exactly what
is missing — **the red test list is the backlog**, deliberately.

### The single next action

**Weeks 1–6 are green or closed with a documented reason.** The paired host ran the full
offline-demo path and materialised `output/reefprint-backup-demo.gif`. The next action on this
branch is to audit the remaining red placeholder docstrings and select one in-scope module; the
hardware-facing acquisition half remains intentionally out of scope under ADR-0002, and Week 2's
missing `texture_features` remains a domain-lead decision. **Week 3 implementation is complete on
`reefprint`.** `reefprint.trust.conformal` computes the
exact split-conformal Beta coverage band, combines held-out count noise with a Beta-Binomial
predictive interval, and audits every held-out locality separately, with locality-disjoint
calibration/test guards. The remaining Week 3 action is to run this audit
against the 12-section Kaggle prediction output supplied by `main`. Week 1's real-codebook /
extinction rerun belongs to `main` per the Sept 3 handoff and is not repeated on this branch.

The Week 1 routing notes below are historical context, not this branch's next action.

**N3 came back `NEITHER` a third time, 2026-08-27, on this machine, on the archive verified
byte-for-byte against Yandex's declared size — and the brightness-restricted re-run (the
targeted check that could have flipped it) moved 2θ SNR from 3.4x to 4.0x but still did not
clear the 5.0x threshold, while 4φ stayed flat at 1.8x.** `test_the_real_s3_v2_archive_has_been_
measured` is deleted; N3 has now been measured three times, independently, all `NEITHER`. Do
not run the Stokes inversion on S3 v2. Reasoning unchanged: extinction depth (stage, 4φ) scales
as bireflectance-squared, weaker; analyser modulation (2θ) scales as bireflectance directly, on
a bright S0, stronger. A geometry whose signal is the *weaker* one is more likely to vanish
under noise than one whose signal is stronger. A symmetric null is therefore asymmetric
evidence — it leans stage.

**The loader is built, TDD'd, and now proven on 12 real full-resolution sections.**
`experiments/003-s3v2-extinction/run.py::load_section_as_specimen_series`, 4 passing tests in
`tests/test_s3v2_extinction_loader.py`, and — session 16f, 2026-08-28 — a Kaggle kernel run
(user's account, private dataset + kernel, both left in place for reuse) that loaded and
measured 9 of 12 attempted real sections at full 3396x2547 resolution, including the exact
`(71, 2547, 3396)` float64 array that OOM'd on the local machine. The memory blocker is
resolved: Kaggle's RAM handles it, no downsampling or bridge-module restructure was needed.

**What is actually next: substitute the real codebook and get an actual mineralogical result.**
The Kaggle run used an explicit placeholder codebook (`code_0`, `code_1`, ...) — Rule 6 still
applies, and the real per-mineral extinction-depth claim (pentlandite dark / pyrrhotite
extincting) needs KHANYA's real `.segmentation.lumenstone.CODEBOOK` substituted in. Re-running
is one `kaggle kernels push` once that mapping is available — the dataset and kernel are already
set up.

**One new real finding to flag, not yet investigated:** `S3_test_04` was skipped —
`"frame S3_test_04_r045.jpg shape (3396, 2547) != mask shape (2547, 3396)"`, a transposed frame
in a real section's rotation series. Not a loader bug (the "report, don't raise" design caught
it correctly); worth checking whether this is one corrupted file or a systematic issue.

Also left open, not investigated: the archive now reports **47 sections**, not the 29 prior
sessions' wording carried from Sibusiso's runs. Doesn't change the verdict — noted in
`docs/BUILDLOG.md` session 16d as an unexplained discrepancy worth a look.

**Historical Week 1 routing options (owned by `main`, not this branch):**

1. **Run the fourth-harmonic estimator (`reefprint.polarim.extinction`) on S3 v2 instead of
   forcing the Stokes path.** The estimator itself, and now the sanctioned bridge path onto it
   — `reefprint.bridge.measure_section_extinction`, mirroring `measure_section` guard for guard,
   built 2026-08-24 and TDD'd against the stage phantom (`tests/test_bridge_extinction.py`,
   9 tests) — are both built and tested. **What is still missing is only the real archive**: run
   `experiments/002-s3v2-geometry/run.py` first to confirm each section's geometry from the
   frames (`RotationSeries(geometry=RotationGeometry.SPECIMEN, ...)`), then call
   `measure_section_extinction` per section the way `measure_section` is called today. No new
   code is needed once someone has `S3_v2.zip` in hand — see the module docstring in
   `src/reefprint/bridge/extinction.py` for the one thing to get right: raw extinction depth is
   **not** contrast-normalised and must not be compared between minerals the way DOLP is; the
   licensed claim is only "extinguishes at all" vs "exactly dark". This is the leg-(b) path
   that matches the evidence in hand, not a downgrade — it recovers extinction depth per pixel,
   which the physics table at the top of this file already shows separates pentlandite
   (isotropic, no extinction) from pyrrhotite (anisotropic, extincts). **This is the pragmatic
   near-term route to closing week-1 leg (b)**, and it needs no new data.
2. **Run the highest-S0 pixel-selection re-run.** `pool_signatures` now takes
   `brightness_quantile` (`experiments/002-s3v2-geometry/run.py`, TDD'd against
   `tests/test_s3v2_reader.py::test_pool_signatures_can_restrict_to_the_brightest_pixels`):
   restricts pooling to pixels at or above that quantile of fitted DC (brightness) before taking
   the verdict, so the check runs on the grains where an analyser signal, if real, is least
   buried. One command on Sibusiso's machine, needs no new data:
   ```bash
   uv run python experiments/002-s3v2-geometry/run.py --archive path/to/S3_v2.zip --brightness-quantile 0.5
   ```
   If the brightest half clears `DETECTION_SNR` on the 2nd harmonic while the full pool doesn't,
   that's real evidence for `SECOND` on a subset, worth reporting alongside the pooled `NEITHER`
   rather than treated as an automatic reversal. If it doesn't clear either, that's a second,
   more targeted confirmation of stage — the archive's brightest pixels are exactly where an
   analyser signal has the best odds of surviving, so failing there closes off the most
   favourable case rather than leaving it unchecked.
3. **Look for a public archive with a *confirmed* rotating-analyser series**, if the talk still
   wants the three-Stokes-parameter result specifically. Candidates, honestly assessed:
   - **LumenStone S2** (Norilsk, same BMS assemblage) ships masks but — check before assuming —
     may not ship rotation series at all; it was never the rotation dataset, S3 v2 was.
   - **IronOreRLM** — reflected-light images, no stated rotation acquisition; unlikely to help
     without checking its acquisition protocol directly.
   - **CGS National Core Library** — real Bushveld material, but access is a phone call away
     (§8, still open) and there is no evidence yet it contains any analyser-rotation series.
   - Realistically: **no public archive is known to carry a documented rotating-analyser
     protocol.** S3 v2 was the candidate because it was labelled a "rotation sequence"; the
     labelling turned out to be ambiguous about geometry, which is exactly what N3 was checking.
     Searching for a "better archive" on this axis is a low-probability, unbounded-time path —
     don't block week-1 leg (b) on it.
4. **Report `NEITHER`, leaning stage, as the finding itself**, alongside the leg-(b) result run
   on the fourth-harmonic estimator. This is consistent with Rule 9 (falsification is a
   deliverable) and Rule 1 (never invent a number) — the honest story is "we checked which
   geometry this is, the data itself told us, and we routed to the estimator that matches,"
   which is a stronger claim for the talk than silently assuming the convenient geometry.

**Do not re-run the Stokes inversion on S3 v2** until either a confirmed-analyser dataset shows
up, or `pool_signatures` is re-run with a materially different pixel selection (e.g. restricting
to the highest-`S0` grains, where the analyser/stage SNR gap is a factor of `2/a` and widest) and
clears `DETECTION_SNR` on the 2θ side specifically. Absent that, treat this archive as `SPECIMEN`
geometry for all downstream work, including KHANYA's ten-mineral symmetry test (see below).

**It also gates his work, not just ours.** KHANYA's `src/polarimetry.py` feeds all 72 S3 v2 frames
straight into `stokes_from_rotation_series` for a ten-mineral symmetry test. If those frames are
stage rotations, that test returns a separation near 1.0 and reads as *"polarimetry does not work
on real ore"* — a false negative on an estimator bug, against the project's central claim. That
symmetry test should now be re-pointed at `reefprint.polarim.extinction`, not
`stokes_from_rotation_series`, given the measured `NEITHER` verdict.

Named by the failing placeholder test
`tests/test_s3v2_reader.py::test_the_real_s3_v2_archive_has_been_measured`.

**Still open, and unchanged:** LumenStone has no named licence — informal "free to use in
research, cite the references", contact `khvostikov@cs.msu.ru`. Downloading is a user decision,
not an agent one.

### The false negative is now blocked in code, not just warned about

The paragraph above used to end at *"do not let that experiment run before this one does"*,
which is an instruction a tired person ignores at 2am. It is now a guard.
[`Sibusiso-K/KHANYA#2`](https://github.com/Sibusiso-K/KHANYA/pull/2) makes
`src/polarimetry.py` call `harmonic_signature()` before it inverts, and refuse the whole run
— with the evidence and the next step named — unless the verdict is `SECOND`. It also stops
that module importing `~/Desktop/REEFPRINT - Copy/src`, a snapshot whose `polarim/` holds
`stokes.py` and nothing else: no discriminator, no fourth-harmonic fallback.

Measured while writing the guard, on a synthetic pyrrhotite-like **stage** series at S3 v2's
real layout (72 frames, 5° steps, contrast *a* ≈ 0.12): the unguarded Stokes fit returns
**median anisotropy 1.5e-02**. A strongly anisotropic mineral, reported isotropic, no error
raised. That is the number to quote when anyone asks why the geometry check is worth code.

### The ten minutes is drafted, not decided

A nine-beat storyboard exists (0:00–8:45, built around a live demo that **declines** to
answer at 5:45) and it is a **draft under refinement, not a committed running order**. Do not
treat it as spec, and do not let it start driving what gets built — gauntlet blind spot 11 is
exactly this failure, and the person who owns the narrative also owns the architecture.
The gates in §3 decide what gets built. The talk describes what was built.

### Rules 2 and 3 are guards now, not paragraphs

Same treatment as the geometry hazard above, and for the same reason: both rules protect
against a *silent* wrong answer, and prose cannot defend against a failure whose whole nature
is that nothing prompts you to go and re-read the prose.

**Rule 2 — [`reefprint.trust.split`](src/reefprint/trust/split.py).**
`split_by_locality()` is the sanctioned constructor; `require_locality_disjoint()` is the
backstop for the split someone builds by hand in a notebook, which is the route around any
constructor. It refuses a locality on both sides, a section filed under two localities, mixed
label provenance, a held-out name that is not in the data (a typo there gives you an empty test
set and a perfect score), and holding out everything. Unmeasured sections are dropped **and
counted**, because a skipped section has no pixels and leaving it in inflates the denominator.

The number: on synthetic patches whose only signal is section identity — 192 patches, 24
sections, 6 localities — a 1-NN model scores **MAE 0.0017** under a shuffled patch split and
**MAE 0.2119** under the honest locality split. A factor of **126**, in the flattering
direction, from a model that has learned nothing transferable at all. `test_a_patch_level_split_
reports_a_far_better_score_than_the_honest_one` pins it.

`LocalitySplit.n_groups` is the honest *n* for rule 4 — localities, not sections. Six sections
from three localities is n = 3. Quoting n = 6 narrows every CI by √2, and that is arithmetic a
judge can redo in their head.

**Rule 3 — [`reefprint.trust.baseline`](src/reefprint/trust/baseline.py).**
`ScoredMetric` takes `baselines` as a required field with **no default**: a metric without its
trivial baselines is a `TypeError`, not a slide. Uplift is measured against the *strongest*
baseline, never the weakest — quoting the gap to majority class while metadata-only sits higher
is the flattering error, and metadata-only is the baseline that most often wins.

`summary()` reports three states, not two: below the baseline, above it but inside the noise
honest *n* resolves, and above it by more than that. The middle state is the one that matters.
`0.62` next to a `0.60` baseline reads as a result; at n = 12 the standard error is
`√(0.62·0.38/12) ≈ 0.14`, so `+0.02` is a seventh of one SE. It is positive, so "does not beat"
would be false, and it is nothing, so silence would be worse. The line reads:

```
balanced accuracy = 0.620 (n = 12) · majority class 0.500 · metadata-only 0.600 ·
uplift +0.020 over the strongest baseline (0.600) is inside the ±0.140 that n = 12 resolves
```

The SE formula is the one this package already quoted for conformal coverage, not a threshold
invented here (rule 1). It returns `None` outside [0, 1], because a binomial SE on an RMSE is an
invented number. `TrivialBaselines` assumes **higher is better** — stated in its docstring as an
assumption, because an error-like metric ranks its baselines backwards otherwise.

A baseline may be `NotApplicable`, but only with a stated reason — rule 5's pattern, one level
up. Both inapplicable at once is refused: that is a metric with nothing to compare against,
which is the state rule 3 exists to forbid.

**The three states had a fourth failure mode, found while fixing rule 5's version of it.**
`sqrt(p(1-p)/n)` is exactly zero at p = 0 and p = 1, and in `ScoredMetric` that did not print a
false `±0.000` — it did something quieter. The middle verdict fires on `uplift <= noise`, and
`uplift <= 0.0` is never true for a positive uplift, so **at a metric of exactly 1.0 the middle
state could not fire at all.** Twelve localities out of twelve against a 0.95 baseline read as
`+0.050 over the strongest baseline`, a clean win, when the rule of three puts the 95% lower
bound at **0.75 — below the baseline.** Fixed the same way as `abstain`: `None` at the ends,
the rule of three where it bounds something, and where even that spans the range (n ≤ 3) the
line says *"resolves nothing"* rather than falling back to the clean-win wording.

### Rule 1 is a guard now too, and it is the one that had to be contagious

[`reefprint.quantity`](src/reefprint/quantity.py). The hardest of the four to make structural,
because there is nothing malformed to detect: an invented number and a measured one are the
same 64 bits. `0.35` is `0.35` whether it came from a calibration run, a textbook, a phantom,
a plausible guess, or a spec for hardware that was never built. What is missing is everything
*around* the number.

So the guard is not a check on the value. `Quantity` carries a `Provenance` and a **mandatory
non-empty** `source`, and the provenance **propagates through arithmetic, weakest input wins**.
That is the part that had to be automatic: the contamination surfaces three functions from where
the assumption was written, in a variable named something reasonable like `grain_size_um`.

```
MEASURED  →  CITED  →  STIPULATED  →  ASSUMED  →  DESIGN_TARGET
  a result    published   true of the    a guess,    hardware that was
              value      phantom only    labelled    never built
```

`require_reportable()` is the boundary — call it wherever a number stops being an intermediate
and starts being a claim. `__float__` calls it, so the number cannot leave the type by the one
obvious route around any wrapper. A flagged assumption **passes**: rule 1 permits assumptions,
it requires labels, and by the time you hold a `Quantity` it has one.

`DESIGN_TARGET` never passes, and that is ADR-0002 made mechanical rather than a preference.
The number that makes the case: 47 px × **0.2** µm/px is 9.4 µm; 47 px × **1.6** µm/px is 75.2 µm.
Same design target, a **factor of 8** apart. A grain size derived from it is not a measurement
with wide error bars — it is a figure that could be 9 µm or 75 µm, printed to three significant
figures. `test_the_design_target_spans_a_factor_of_eight_so_it_is_not_a_number` pins it.

Bare floats cannot join in: `measured(1.0, "um", ...) + 2.0` is a `TypeError`, because the bare
literal is exactly the thing rule 1 is about. Units are checked on `+`/`-` and cancel on `×`/`÷`
(`px` × `um/px` → `um`), because a scale factor is the usual doorway for an unlabelled number.

### Rule 5 is a guard now, and the thing it removes is a *field*

[`reefprint.trust.abstain`](src/reefprint/trust/abstain.py). The other three guards refuse bad
inputs. This one is mostly about what is **not** on the type: `Abstention` has `default`,
`reason` and `trigger`, and **no slot for the previous value**. Holding the last setpoint is not
discouraged here, it is unreachable — there is nowhere to put it.
`test_an_abstention_cannot_carry_a_previous_value_to_hold` asserts that against
`dataclasses.fields`, so re-adding one breaks a test rather than passing review.

`value_to_act_on(decision)` takes one argument for the same reason. A signature of
`(decision, previous)` is the whole bug, pre-installed.

Everything else follows from "a refusal still emits a number":

- No `Abstention` without a `ConservativeDefault` **and** a reason, and `"unknown"`, `"n/a"`,
  `"tbd"`, `"?"` and their neighbours are rejected **by name**, case- and space-insensitively.
  Rule 5 names `"unknown"` specifically, so the guard does too.
- The default is a `Quantity`, so **rule 1 meets rule 5 at the seam**. A conservative default
  derived from a design target is refused at construction. This is `quantity.py`'s first real
  caller — the "nothing calls these guards yet" item from sessions 6 and 7 is now half closed.
- "Conservative" has a **direction**, and the mechanically detectable bug is the **inversion**:
  `ASSUME_HIGH` that emits the low half of its own range is a `ValueError`. *How far* along the
  safe side is domain judgement and is reported, not enforced — pinning defaults to the extreme
  is how you get operators who switch the system off, which is a 100% abstention rate that never
  reports itself.
- `audit_abstentions()` **refuses a run with no ore-change events in it.** The only number left
  to report would be the aggregate, and quoting the aggregate is precisely blind spot 1's error.
  A gate that has never been tested through a transition has not been tested.

One thing here was not found by a test. The 37 tests passed on the first run; the defect turned
up by *reading the printed line*, which said `100.0% during ore change (n = 2, ±0.0%)`. The Wald
SE `sqrt(p(1-p)/n)` is exactly zero at p = 0 and p = 1, so the **least** informative observation
prints as the **most** precise — invented precision, rule 4's exact prohibition, in rule 5's
own summary. Small runs land on those extremes constantly. Fixed with the **rule of three**
(Hanley & Lippman-Hand 1983: 0 events in n → 95% upper bound 3/n), which is published and so
satisfies rule 1; where even that bounds nothing — n = 2, where 3/n ≥ 1 — the line now says
*"which resolves nothing"* rather than printing a number.

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

Expect **300 passed, 9 deselected**. Anything less is a regression, not a quirk.

```bash
uv run pytest -m placeholder -q --no-header -rf
```

Expect **9 failed**. These are the backlog, not breakage. Each failure names the module and the
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

- **Never invent a number.** Flag every assumption in the code, not just the docs. `quantity.Quantity`
  carries a `Provenance` and a mandatory `source`, and arithmetic keeps the **weakest** input's
  provenance. `require_reportable()` at every boundary; `DESIGN_TARGET` never passes it (ADR-0002 —
  the 0.2 and 1.6 µm/px ends of that range are a **factor of 8** apart).
- **Split by locality, never by patch or image.** Patch splits void conformal exchangeability and
  silently invalidate every metric — measured at **126x** in the flattering direction. Use
  `trust.split.split_by_locality()`, or `require_locality_disjoint()` if you built the split by
  hand. Honest *n* is `LocalitySplit.n_groups`: localities, not sections.
- **Report the trivial baseline** — majority class *and* metadata-only — alongside every metric.
  `trust.baseline.ScoredMetric` will not construct without them. Uplift is measured against the
  *strongest* baseline, never the weakest.
- **Every metric carries a CI at honest n.** Coverage SD is `√(0.9·0.1/n)`: ~3.0 pp at n = 100,
  ~6.7 pp at n = 20. Do not claim tighter than the arithmetic allows.
- **Abstention emits a conservative default with a stated reason, never "unknown."** Abstention
  fires at ore transitions, which is exactly when holding the last setpoint is the worst
  available action. (The submitted abstract says "holds the last-known-good setpoint" — that is
  now contradicted, deliberately. See §8.) Guard: `trust.abstain.Abstention`, which has **no
  field for a previous value**, so the abstract's version of this is not reachable through the
  type. `audit_abstentions()` refuses a run with no ore-change events in it.
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

**Single technical decision-maker: Lethabo Hoaeane** (Domain lead — Business Informatics /
prior metallurgical engineering). Breaks all architecture ties; the decision is written up as an
ADR the same day. Two standing checks on the role are in CLAUDE.md — the same person is the
rusty met-eng *and* owns the ten-minute narrative, and neither should quietly become the spec.

---

## 8. Still open

| # | Open item | Owner / when |
|---|---|---|
| **N1** | Pirard 2007 prior art — full paper still unread (paywalled, both ScienceDirect and an academia.edu mirror blocked direct fetch), but 2026-08-28 the abstract (via search indexing, not a verified literal quote) narrowed the risk: plane-polarised static grain-boundary imaging + grey-level intercept stereology, no analyser rotation, no per-pixel Stokes recovery — further from our claim than assumed. See CLAUDE.md's prior-art note. Full text still needed before week 6, lower urgency than previously. | before week 6 |
| **N2** | 1/S0 noise floor means no fixed anisotropy threshold is defensible. Any discrimination rule must condition on S0 and report an interval. | week 2+ |
| **N3** | **Is LumenStone S3 v2 a stage rotation or an analyser rotation?** **Measured, twice, identically: `NEITHER` clears `DETECTION_SNR` (2θ SNR 2.5×, 4θ SNR 1.1×, threshold 5.0×), leaning stage on the physics (extinction scales as bireflectance², weaker; analyser modulation scales as bireflectance, stronger — a symmetric null favours the weaker signal's geometry).** Not closed — open until either a confirmed-analyser archive turns up or a pixel-selection re-run clears the 2θ threshold. Route leg (b) and KHANYA's ten-mineral symmetry test through `reefprint.polarim.extinction`, not the Stokes inversion, until then. | open — route around it, see §3 |
| **F1** | Chromite-proxy collapse — the falsification test runs regardless and the result is published either way. | week 2 gate |
| **F2** | Talc/serpentine without SWIR is unproven. If it fails, drop to two properties. | week 2, empirical |
| **S2** | Plant history was generated under FloatStar closed-loop control. No causal claim from observational plant data. | any use of the Kaggle flotation dataset |
| — | LumenStone licence is informal and unnamed. Get terms in writing before publishing anything derived. | email `khvostikov@cs.msu.ru` |
| — | CGS National Core Library sampling policy. | phone call |
| **T1** | **Widened search, 2026-08-27 (session 16b): no public, machine-readable, adequately-sized texture-plus-chemistry dataset for UG2/Bushveld chromitite was found.** Checked and ruled out precisely, not assumed absent: GeoMet (Zenodo, copper, no images at all), HIDSAG (figshare, real images+response but wrong commodity — porphyry Cu-Mo, hyperspectral not reflected-light), two paywalled studies on the exact right material with no data release (Kaufmann 2019 — *same mine as the Bachmann CSV already in hand* — and Veksler 2018), and a UP thesis with real chromite grain-diameter data that exists only as an unextractable line chart over 3 sample groups (below `MIN_LOCALITIES_FOR_INFERENCE = 5` even if the numbers could be read off it). **Solving this structurally needs `reefprint.segment` (not built) run on polished sections tied to real assay depth intervals** — CGS access alone does not hand that over. **Cheapest live option: email Kaufmann or Veksler directly**, naming the Thaba-mine overlap with data already in hand — materially cheaper than the CGS phone call. See `docs/BUILDLOG.md` session 16b for the full list and why each was ruled out. | domain lead's call — email vs. report-as-blocked vs. pivot to oxidation index |
| **T2** | **Pyroxene fraction is not a column in the Bushveld CSV either.** `SiO2_%`/`Al2O3_%`/`CaO_%` could support a chemistry-based silicate-fraction proxy (a normative mineralogy calculation), but deriving one is a mineralogical judgement call — Rule 6 forbids an LLM computing it, and it has not been derived here. Domain lead's call, with a literature citation for whichever normative method is chosen. | before week 2 gate is claimed complete |
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
src/reefprint/       quantity.py (rule 1) · acquire · bridge · calibrate · polarim · segment · texture · heads · trust (rules 2, 3, 5) · integrate · viz
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
