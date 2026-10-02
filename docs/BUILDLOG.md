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

## 2026-10-02 (10:55–11:25) — secure UI, physics checks, robustness on unseen captures, resilience and compliance

**Codex.** Round 2 was killed at the 33-minute background limit with no output. A ping showed the usage limit again (reset 13:54), so round 2 has not run. All work below is disclosed for it.

**Secure UI** (commit 96bb149):
- Sign-in or guest sandbox, and a role badge.
- Server CSV and photo uploads: encrypted, EXIF stripped.
- A **Decisions** view: a feed proposal from the exact one-sided bound inside a typed STIPULATED envelope, an arrival countdown, an immediate fallback, and the signed decision record.
- **Tested end to end** on the real secure server: guest and metallurgist flows, chain verified, signed checkpoint downloaded.
- Offline mode was regression-checked in every view and theme. One bug was found and fixed: the Decisions view was empty on a cold start.

**Physics checks** (`training/physics-checks-20261002`):
- **Kinetics:** +1.9% tonnes costs ≤ 0.25 pp recovery (1 lab-min), 0.04 pp at 3 min, and 0 on the plateau.
- **Load-curtailment tonnage claim: tested and REJECTED.** Re-ordering ore gave −3.8%, and an oracle −3.0%; energy is conserved.

**v9 robustness** (pre-registered; scored by fold models that never saw the parcel):
- **A new capture of the same ore keeps the accuracy:** MAE ×1.00 [0.99, 1.01], so the gate passes.
- A partial view, noise and ±15% light are tolerated.
- **A one-band wavelength drift gives ×1.25 error, mostly unflagged**, so a hardware wavelength-calibration gate was added to docs/18.

**Docs and app:**
- docs/21: physical possibility, power cuts, kinetics, radiation (we do not detect it), waste and water, equipment and energy, SA compliance, scale-up, gaps, evidence.
- The Evidence view gained a "physically possible" table; the Where view gained a power-loss card.

**PR 15:** comment posted.

**Learned.** A plausible money story (curtailment re-ordering) died to a two-line energy-conservation argument once it was simulated. It is worth simulating every "smart scheduling" claim before saying it.

## 2026-10-02 (08:00–08:55) — v8: industry research, ClauDex round 1, corrections, evidence runs, secure server

**Plan and review:**
- PLAN-v8 plus its addendum (security, PQC, deployment, business).
- Codex round 1 returned 40 findings (REVISE), all logged in PLAN-v8-REVIEW-LOG.md.
- Round 2 was paused by Codex's usage limit; it was relaunched at 08:52 and its result is pending.

**Corrections:**
- "Same overload risk" withdrawn.
- Economics restated as net value plus break-even (0.04–0.26 pp).
- Import refuses blank values.
- Every shipped asset is hashed.
- Advice rows rewritten as diagnostic prompts.

**Evidence:**
- **v8-model:** the exact one-sided bound gives +1.9% throughput, non-inferior on overload (+1.4 pp upper bound). This is provisional because of a disclosed method switch. Latency is 92 ms per parcel. The exported model loads locally.
- **v8-features:** no pre-registered hypothesis passes. H2 has ρ +0.27, below the minimum useful effect. The belt does not earn ≥3 phases; KHANYA carries that.

**Security:**
- Secure server (RBAC, sessions, CSRF, SQLite append-only ledger, Ed25519 + ML-DSA-65 checkpoints, ML-KEM-768 exports, encrypted EXIF-stripped uploads, guest sandbox).
- 17 tests pass; Bandit 0; pip-audit clean after upgrading cryptography.

**Docs:** 17 (industry dossier), 18 (installation and pilot), 19 (security), 20 (competitors and business).

**Left open:**
- process Codex round 2;
- UI wiring for login, upload and the decision record;
- Dockerfile, tunnel runbook and QR (the public deploy needs the owner's approval);
- the map;
- the mass balance;
- deck v8.

## 2026-10-02 (morning) — belt view, full-resolution scans, value chain, v7 (no gain), Bushveld correction

**Asked:** make the belt and scans look right, keep training for accuracy, and show whether each prediction helps the next plant step and what it is worth, backed by evidence.

**Display (REEFPRINT Live).**
- **Full-resolution scans.** Kaggle `reefprint-hidsag-showcase-hr` (290 s) re-exported the same pre-registered showcase samples without the 2× downsample: 80×117 px instead of 40×58, uint8 per band. The predictions, intervals and decisions stay v6's out-of-fold values.
- **Measured why the maps looked striped.** In the SWIR band-depth maps the column medians carry most of the pixel variance (column-median sd 46–54 of total 52–59, in display units) and are uncorrelated from one column to the next (lag-1 autocorrelation −0.1 to 0.36). That is detector pattern.
- **Display destriping**, labelled and toggleable. It removes only the high-pass part of the column medians. No prediction uses it.
- **Crisp integer scaling.**
- **A Belt mode.** Real scans ride a conveyor past a fixed line scanner, natural colour (R640/G550/B460) upstream and the analysis layer downstream.
- **Bug found by screenshot and fixed:** a belt cube cache smaller than the visible tiles thrashed and kept the page busy.

**Value chain** (`training/value-chain-20261002`, `docs/16-decision-value-chain.md`).
- **Hardness → mill feed rate**, simulated policies on 146 real out-of-fold predictions (Bond 1961; mill power, F80 and P80 cancel). Setting the feed for the upper end of the 80% interval gives **sim_ +2.0% throughput [+1.0, +3.0]**. Its overload risk matches the no-information P90 rule: 8.2% vs 8.9%, difference CI −4.8 to +4.1 pp. When a parcel is harder than planned, the energy shortfall is 5.0% vs 11.9%. All gates pass (Wilcoxon 1.2e−7, Mann-Whitney 4.2e−13, δ −0.48). This captures 14% of perfect information's +14.0%.
- **Correction: Bushveld.** Routing by belt chemistry gives balanced accuracy 0.79, against 0.82 for the mine-plan seam; the seam is better (CI −0.056 to −0.004). The earlier "chemistry beats the average for Pt/Rh/4E" used a weaker baseline than one already in `results.json` (`r2_seam_only`), which rule 3 should have caught. It is no longer presented as grade control.
- **Not decision-grade:** belt recovery, lime and pH (no significant difference against baseline), so no reagent-saving claim from the belt.

**v7, pre-registered** (`training/hidsag-v7-ens-20261002`, PREREG committed `11f0c23` before the run; Kaggle 703 s).
- **Tried:** widening the menu with gradient boosting, an RBF SVR and a fixed 5-model mean, with the same folds and calibration.
- **Did not work:** no significant difference on any target. Work index R² 0.479 → 0.483. Mo recovery improved on the paired test (Holm p 0.004) but failed Mann-Whitney (0.17). v6 stays.
- **Data check:** GEOMET has exactly five lab variables, all modelled.

**Learned.** The accuracy limit is the data (146 samples, no hole ids), not the model menu. The value of a prediction depends on the strongest baseline *the operator already has*, which for PGE grade is the mine plan.

**Left open.**
- Deck v8: withdraw slide 13 (MINERAL1) and reframe any Bushveld grade claim.
- A site pilot logging feed rate, power and grind.
- Re-record the Live demo with Belt mode.

## 2026-10-01 (night) — ClauDex v6 plan, REEFPRINT Live, real-plant and Bushveld tracks, and a correction

**Plan.** `PLAN-live-v6.md`, adversarially reviewed by Codex gpt-6-astra (read-only) over 3 rounds: 26 + 12 findings, then APPROVED. 37 were accepted; phone and LLM features were kept as R-3 under constraints. Log: `PLAN-live-v6-REVIEW-LOG.md`.

### T1 belt v6 (`training/hidsag-v6-live-20261001`, Kaggle 575 s)

- **Method.**
  - Calibration is split off before any selection.
  - Strict nesting covers k-means, scaling and blends.
  - Families: nonlinear, linear-in-reflectance, and blend-augmented linear.
  - Intervals are 80% split-conformal with one score per unit.
  - Explanations use occlusion with the pipeline recomputed.
  - OOD uses Ledoit–Wolf on PCA scores; RGB is a matched simulation.
  - Gates are run locally (`analyse_v6.py`).
- **Results.**
  - **v6 is not more accurate than v5** (no significant difference on any target). v5 was slightly flattered by a k-means leak.
  - **Only Bond work index beats its strongest baseline under all gates.** It is the only belt decision target.
  - 80% coverage is calibrated: median 0.82 for GEOMET (unit level) and 0.81 for MINERAL1 (simultaneous within composite).
  - The OOD gate refuses 3% of in-domain samples. Shifted-domain acceptance is 0–21% in four folds but 80% in one.
  - Hyperspectral beats simulated RGB on 2/5 GEOMET and 6/33 MINERAL1 targets, and is never worse.
  - Blends remain open (median R² −0.22).

### CORRECTION (rule 3, rule 9) — `mineral1_q2.py`

The MINERAL1 "camera reads QEMSCAN mineralogy" result is **explained by size fraction and process line**:
- a median lookup on those labels matches the spectral model;
- adding the spectrum to a metadata model helps on **0 of 33** minerals and hurts on 5;
- a size-fraction lookup alone gives chalcopyrite R² 0.92.

Deck v7 slide 13 ("31 of 33 minerals beat the average guess") is literally true but misleading, and is **withdrawn**. The doc-15 MINERAL1 lines are superseded. v4's claim was against the mean only; the metadata-only baseline required by rule 3 had not been run.

### T3 real plant (`training/plant-softsensor-20261001`, CC0 Kaggle flotation plant)

- **Method.**
  - Hourly completed bins and an ASSUMED lab delay (1/2/4 h).
  - Clock horizons of 1 and 3 h.
  - Periods: train Mar–Jun, tune Jul, calibrate Aug, test Sep, with purge gaps.
- **Result: the model never beats persistence** (last available assay). At delay 2 h, horizon 1 h: MAE 0.780 vs 0.738. Coverage was 71–78% at nominal 80%.
- **Reading:** plant tags react after the ore changes, which is the argument for measuring the ore first.

### T4 Bushveld (`training/bushveld-xrf-pge-20261001`, Bachmann et al. 2019, CC BY 4.0)

- **Data.** 1,112 intervals, 123 projects held out, LG6–MG4 seams.
- **Q1 (chemistry vs average).** Belt-type chemistry beats the average for Pt (R² 0.40), Rh (0.26) and 4E (0.42). It does not for Pd (0.21).
- **Q2 (chemistry on top of a known seam).** The extra gain over a seam already known from the mine plan passes the paired project tests (Wilcoxon p ≤ 0.01) but fails the doctrine's unpaired Mann–Whitney gate, so it is "no significant difference".
- **Seam from chemistry.** Balanced accuracy 0.42 vs 0.125.
- **Coverage.** 80–87% per project.

### T2 pentlandite diagnostic (`training/pentlandite-diagnostic-20261001`, exploratory)

- **Setup.** Oracle sulphide mask, so only pentlandite vs pyrrhotite is classified. HistGB on colour and texture. Trained on 31 sections, scored on the 6 audited validation sections; test sections never opened.
- **Result (pooled pentlandite IoU).** Colour + texture **0.499**, colour only 0.464, brightness only 0.288, all-pyrrhotite baseline 0.
- **Spread across sections.** From 0.92 (train_23) to 0 (train_27).
- **Reading.** Even with perfect sulphide detection, colour and texture reach only about 0.5. The Pn/Po confusion is a ceiling for ordinary reflected light. This is the case for the rotating-analyser axis (isotropic pentlandite vs anisotropic pyrrhotite). S2 images and weights are not shipped.

### REEFPRINT Live (`presentation/belt-monitor/`)

- **Views:** Live scan, Bushveld PGE, Plant, Lab & exports, Evidence, Where it sits. All six use the workbench design and three themes.
- **Live scan:** real cubes decoded in the browser, absorption and cluster maps, pixel spectra, a CSS 3D data cube, the total decision table, and an audit log with hashes.
- **Lab & exports:**
  - a typed registry with lab import (rejections listed with reasons) and reconciliation;
  - LIMS CSV with formula neutralisation; provenance JSON;
  - an OPC UA tag map, not a live server;
  - GeoJSON with null geometry;
  - a code-only shift report.
- **Assistant.** It routes only; templates render the answers. `server.py` holds the AIML / Featherless keys server-side.
- **Server security checks passed:** traversal and source files 404, bad host or origin 403, no token 401, oversize 413.
- **Camera.** Quality gates only, ending in a refusal.
- **Bug found by the browser test, not by the syntax check:** the `S.plant` store was not initialised, so boot failed. It is fixed.
- **Second bug found the same way:** the pentlandite baseline's undefined precision was written as `NaN`, which is invalid JSON, so the whole app failed to load. `build_live.py` now converts NaN and Infinity to null, writes with `allow_nan=False`, and every JSON file under `live/` is validated. Lesson: the end-to-end browser check after every rebuild is a required step, not optional.

## 2026-10-01 (evening) — Refinement for the Top-5 round: v5 hyperspectral, moving-belt simulation, cheap cameras, Belt Monitor restyle

**Why.** After the v6 pitch the judges asked us to refine. The team asked whether to keep the belt; what else is on the
market; who decides what; where the system sits; and what cheaper images could do. Plan and reasoning:
`docs/15-refinement-top5-strategy.md`. The verdict: keep the belt as layer 1 of one system (belt → microscope → QEMSCAN
teacher → one control-room screen), not a pivot.

**v5 training (Kaggle `lethabomh14/reefprint-hidsag-v5-belt`, 799 s, all four HIDSAG records)**
- **What changed.** Spectra are resampled onto a common grid, with brightness-normalised means, derivatives,
  continuum-removed band depths and bag-of-spectra k-means fractions (fitted on training folds only).
  PLS / ridge / extra-trees are **chosen per target by inner CV**. This removes the v3 "best of two on the same OOF
  score" optimism.
- **Three gates against a v3-style PLS in the same folds.**
- **GEOMET.** Cu recovery R² 0.42 [0.31, 0.51] — **better** than v3-style 0.26, all three gates. Mo recovery 0.45, Bond
  work index 0.48 and lime 0.32 have higher point estimates, but there is no significant difference against v3-style.
  pH (0.33) no longer beats the average guess under the gates, so it is dropped from the belt screen.
- **MINERAL1.** 30 of 33 minerals beat the average guess (grouped by 36 composites); chalcopyrite R² 0.90.
- **MINERAL2 (n = 20) and GEOCHEM (n = 28) are too small to learn from.** GEOCHEM Ca 0.77 is the standout (carbonate).
- **Moving-belt `sim_`.** ±15% lighting costs about 0 R² with the new features, against 0.04–0.58 lost by v3-style
  features. Fewer than ~100 pixels hurts. The combined belt case (100 px, +10% light, 2% noise) costs 0.07–0.20 R².
- **Blended ore is the open problem.** Median blend R² is −0.08 on MINERAL1. Next run trains on simulated blends.

**Cheap cameras (`sensor_bands.py`, local, mean spectra only).**
- **VNIR hyperspectral (silicon) alone:** kept ~98–109% of the full VNIR + SWIR skill on the median target, though Cu
  recovery still gained from SWIR.
- **6-band LED mono camera:** 65–90%.
- **RGB:** 53–60%.
- **Caveats:** talc's 2.31 µm feature is SWIR-only, and this is not PGM ore.

**Bug caught before reporting.** `sensor_bands.py` first failed because the v3 jsonl stores targets as `vars.<name>`;
fixed by normalising the key. **Not a bug, but recorded:** Playwright full-page screenshots of tall pages captured blank
mains mid-animation. The real browser renders correctly (checked via computed opacity); viewport screenshots are used
instead.

**Belt Monitor restyled to match the workbench (`presentation/belt-monitor/`).**
- **Look.** Public Sans (bundled, OFL), the two-layer brand mark with launch motion, and the masthead, panels,
  provenance block and copper active tab of the main app.
- **Themes.** White workbench / Mineral night / Field paper, with tokens copied from `codex/themes-launch`.
- **Four views.**
  - Belt: spectrum / absorption features / photo, predictions, and act · verify · conservative default.
  - Feed mineralogy: MINERAL1/2, GEOCHEM.
  - Belt robustness: sim tables and the cheap-camera table.
  - Where it sits: placement and a roles table.
- **Advice wording follows rule 5.** It shows a conservative default, never "hold the last setpoint". The first dark
  version is kept as `index-v1-dark.html`.

**Market and facts.** Plotlogic, Scantech/Thermo PGNAA, MineSense, TOMRA, Metso froth cameras, Mintek MillStar /
FloatStar, NVCL, USGS splib07, the UG2 Cr₂O₃ penalty and talc/CMC are all from web-search summaries and marked
**[indicative]** in docs/15 until read in full. The USGS ScienceBase download sits behind a browser check, so it is not
automated; a person downloads it.

## 2026-10-01 (afternoon) — Hyperspectral belt track on HIDSAG, Belt Monitor, deck v7, first ensemble member

**Why.** The team asked for hyperspectral imaging as the data, decided before grinding, with a place for it on site. The
honest version: a belt camera reads the host rock (gangue and alteration minerals) at millimetre pixels; platinum and
base-metal sulphide grains are microns and opaque, so they stay with the microscope. Two scales, one control room.

**What ran (Kaggle, `lethabomh14/reefprint-hidsag-hyperspectral`).** Per-sample VNIR + SWIR statistics (mean, std, p10,
p90, slope) → PLS or ridge, scored out-of-fold against the training-mean baseline.

- **GEOMET (v3), 146 drill-core samples, KFold 5 over samples.** All five lab results beat the average guess, modestly:
  Cu recovery R² 0.374 [0.14, 0.52], Mo recovery 0.374 [0.21, 0.51], Bond work index 0.355 [0.14, 0.48], pH 0.317
  [0.16, 0.45], lime consumption 0.270 [0.14, 0.38]; MAE 19.5–24.6% below baseline. **Limitation:** drill-hole IDs are
  not in the published metadata, so a by-hole (locality) split could not be enforced — may be optimistic (rule 2).
- **MINERAL1 — v3 was wrong, v4 is the result.** v3 read tags from a top-level key that does not exist (HIDSAG keeps
  them in `crops[].tags`), so every sample became its own group and size fractions of one composite could straddle
  folds. Caught on reading the metadata before reporting; v4 groups by composite (process line × month, 36 groups from
  99 samples) and now **refuses to run** if grouping collapses to ~one group per sample. `grouped_ci.py` re-sizes the
  CIs by cluster bootstrap over composites (rule 4). Result: 31 of 33 minerals beat the average guess (paired MAE
  difference CI excludes zero); chalcopyrite R² 0.894 [0.85, 0.93], sericite 0.898, biotite 0.906, anhydrite/gypsum
  0.936; failures: andesine, other Ti minerals. Read narrowly: sulphides have no SWIR features, so chalcopyrite is
  predicted through the alteration minerals that travel with it in this deposit — site-specific, needs site QEMSCAN.
- **Selection note:** the better of PLS/ridge per target is picked on the same out-of-fold score — mild optimism, stated
  on the slide.

**Belt Monitor** (`presentation/belt-monitor/`, offline, `python -m http.server 8530 --directory presentation/belt-monitor`):
replays 60 held-out GEOMET samples — spectrum, out-of-fold predictions with typical error and lab marker, an
illustrative quartile-based decision card. Labelled on screen as a replay, not a live belt. Narrated clip (Ryan, en-GB):
`presentation/video/REEFPRINT-belt-monitor-demo.mp4` (67 s), silent embed for the deck.

**Deck v7** (`presentation/output/REEFPRINT-KHANYA-Team-Sonar-pitch-v7.pptx`, 25 slides): + "Where it sits on site",
+ GEOMET results with the embedded clip, + "QEMSCAN teaches, the camera predicts" (MINERAL1); reference-spectra slide
moved to the appendix; notes trimmed and retimed by word count to ~10:16 at 165 wpm.

**Ensemble (validation only, no test set touched).** FCN seed 42 finished: alone 0.657 mIoU on the six validation
sections; equal-probability average with the quarantined candidate 42646cfa scored 0.691 vs 0.704 for 42646cfa alone —
**did not help mIoU**, though NLL/Brier/ECE improved. Pre-declared gate not passed; it stays out. DeepLab seed 43 still
running at 13:22. *Update 14:10:* DeepLab seed 43 finished — alone 0.614; averaged with 42646cfa 0.709 vs 0.704 alone on the same six validation sections (+0.005, within noise on n = 6, and calibration got worse: ECE 0.091 vs 0.062). No significant difference; gate not passed; stays out.

## 2026-10-01 (05:15–10:15) — British re-voice, the 10-minute deck, and the themes branch

### Attempted

Lethabo asked for a different English narration voice, the 10-minute PowerPoint and its script, the app
themes with a launch animation, and answers on phone photos, API keys and model training.

### Worked

- **Re-voice.** Five voice samples were offered (en-ZA Leah, en-NZ Mitchell, en-GB Ryan and Thomas, en-AU
  William), and Lethabo chose **en-GB-RyanNeural**.
  - Narration was regenerated at +6% rate, so the full cut still runs 224.4 s and the short cut 91.8 s.
    "bakkie" is respelled for speech only; the captions keep the real word.
  - Both cuts were re-rendered with every word-synced overlay re-timed. The Luke versions are kept in
    `presentation/video/luke-voice/`.
- **Deck.** `presentation/output/REEFPRINT-KHANYA-Team-Sonar-pitch.pptx` has 16 slides plus 2 appendices,
  built with python-pptx (`presentation/deck-src/build_deck.py`).
  - It passes `validate.py` and was checked slide by slide as real PowerPoint renders.
  - Charts are native; transitions are Morph with a recurring micrograph "lens".
  - Every number carries a provenance tag (LIVE APP, RECORDED, SOURCE, ASSUMPTION, ILLUSTRATIVE), and
    every derived figure is computed in the script.
  - Sources: USGS MCS 2025 (SA ≈ 71% of 2024 platinum mine production; reserves 63,000 t of
    >81,000 t), DMPR Mining Sector Performance 2024 (6.1% of GDP; 474,736 jobs), and Valterra H1 2026
    (R45,993 per PGM ounce sold, read from the PDF).
- **Script.** `presentation/PRESENTER-SCRIPT.md` is timed to 9:45, with a speaker split, a fictional
  user journey and a Q&A crib. The same script is in the speaker notes.
- **Themes branch.** `codex/themes-launch` (`540e29f`) finishes the uncommitted Codex theme pass in an
  isolated worktree, without touching the live demo.
  - It adds three themes, Settings, the brand-mark launch motion and the candidate report.
  - Two defects were found and fixed: the Mineral-night step bar was unreadable, and the model badge
    overflowed 375 px screens.
  - Checks: tsc and vite build; `themes.spec.ts` 3/3 in Edge; 36 backend tests passed.

### Did not work

- Running two render processes at once ran out of memory again (7.7 GB machine). `drive.py` now renders
  one process at a time and resumes from the last frame written.
- `os.replace` onto an MP4 that was open in a player failed with WinError 5. The new cut was renamed
  instead, and the old file moved to `luke-voice/`.
- The first theme-test run timed out waiting for Vite, then failed because Playwright's bundled browser
  was missing. Starting Vite manually and setting `REEFPRINT_BROWSER_CHANNEL=msedge` fixed both.

### Learned

- **The "half of sections answered" triage figure in `MINTEK-FIT.md` §3.1 is stale.** It predates the
  30 September evidence gate. With the shipped refined pipeline, `decision_gap_patches_refined.json`
  gives **4/12 confident answers** (1 continue, 3 grind finer); 8 are verify or too-few-particles.
  The exact 95% interval is 10–65%. The deck uses 4/12, and `MINTEK-FIT.md` still needs correcting.

### Left open

- Promote `codex/themes-launch` to the live demo only after the presentation, or on Lethabo's
  explicit say-so.
- Model training toward a specialist ensemble is designed (deck slide 13) but has not been run.

## 2026-10-01 — promo video for the final, built from the live workbench

### Attempted

Lethabo asked for an advert-style video to sit inside the presentation. The brief: open on a mine site; show
how the images are obtained (geologist in PPE, XRF, the lab); show where REEFPRINT gets opened (bakkie, phone,
office); then run through the whole app with narration, deliverables first. Before building it, the session
also pulled every branch from `Sibusiso-K/KHANYA` and launched the app.

### Worked

- **Repo state.** `git fetch --all --prune` found every local branch already equal to its remote, and
  upstream had deleted `khanya/evidence-sufficiency`. The newest work is `codex/launch-live-demo` @ `2b763b2`
  (PR 15, 00:50 today), which is the live workbench. Its Codex worktree has staged but uncommitted
  candidate-report work; this session did not touch it.
- **App launched and verified.** The local server on :8510 (no auth) returned 200. The public server on
  :8766 returned 401 to unauthenticated `/api/samples`, as designed.
- **Real footage only, for the product.** Headless Playwright at 1920×1080 captured every section,
  including a **fresh live inference** on `test_11`: 278 frames over 220 s, app runtime 98.2 s, source
  `fresh`. It also captured the assistant answer with its predicted, measured and simulated labels; the
  simulator's "Checkpoint is not approved for demo control. Setting held."; the candidate report
  (`42646cfa`, 0.632, "Candidate not deployed"); the opt-in synthetic spatial scene; and mobile at
  390×844@3x.
- **Field footage.** 13 Mixkit clips, each checked as "Mixkit Stock Video Free License" on its own clip
  page. The green-screen laptop and phone clips were keyed with real UI screenshots. Every stock shot
  carries an on-screen "ILLUSTRATIVE STOCK FOOTAGE · MIXKIT" label.
- **XRF beat, honest version.** The element tiles carry no values. The pentlandite highlight is the
  active model's own prediction on `test_11`, labelled "model prediction" on screen.
- **Sound.** Narration is 24 lines of edge-tts `en-ZA-LukeNeural`; its word timings drive the captions
  and on-screen text. Music and effects were synthesised in NumPy, with no samples.
- **Outputs** in `presentation/video/`: the full cut (3:44), a 90 s cut for the deck's demo slot,
  `.srt` captions, `CREDITS-AND-SOURCES.md` (every clip and every limit) and `NARRATION-AND-TIMELINE.md`.
  The MP4s are not committed because of their size. The generator source is committed in
  `presentation/video/src/`.

### Did not work

- **AI-generated people.** Gamma's `generate_image` returned 403 "Insufficient credits remaining"
  (free plan, 0 credits). Figma Weave video models returned "You haven't linked your Figma account to
  Weave yet."
- **Pexels and Pixabay** return 403 to scripted fetches. Mixkit worked.
- **First full render.** One process ran at 0.5 s per frame. Four parallel segments then failed with
  `numpy.core._exceptions._ArrayMemoryError` on a 7.7 GB machine with 0.4 GB free. The cause was the
  sprite cache: animated letter-spacing and growing highlight boxes cached a new sprite every frame. A
  byte-bounded LRU fixed it. The partial segments were still valid (ffmpeg finalises on stdin EOF), so
  only the missing frame ranges were re-rendered.
- **Invisible overlays in the first previews.** The fade-out term `prog(t, b, b - fo)` reversed the
  interval, and `prog` returns a step for b < a, so every box, callout, pop-out and caption had zero
  opacity. Fixed before the full render.
- **Wrong dashboard capture.** The `d01_dashboard` capture was actually the Workspace, because the app
  reopens the last section. The earlier real Dashboard capture replaced it.

### Learned

- Render a dozen preview frames before any long render. That caught three defects, each of which would
  have cost a full re-render.

### Left open

- The full cut is 3:44 and the deck's demo slot is 90 s, so use the 90 s cut there.
- The stock scenes are not South African sites. Location-specific footage needs Weave linked to Figma,
  plus approval to spend credits.

## 2026-09-30 — REEFPRINT design-skill setup — `3d382a3`

### Attempted

Add reusable UI implementation guidance to the REEFPRINT project for the planned responsive web app, using the supplied white dashboard and dark field-capture mockups as visual references.

### Worked

- Installed the upstream DaisyUI Codex skill into `.agents/skills/daisyui` with the documented `npx skills add saadeghi/daisyui --agent codex --yes` command; the installer reported one skill installed and no security alerts.
- Added `skills-lock.json` to pin the DaisyUI source and content hash.
- Verified Impeccable and Frontend Design already exist in the user's shared skill directory.
- Kept scope as design guidance only: the current dashboard is Streamlit/Jinja and does not use Tailwind, so DaisyUI is for the planned web-app UI rather than an unrelated dependency added to the prototype.

### Did not work

- TypeUI is distributed as an authenticated remote MCP connection, not a downloadable local skill. Its documented `codex mcp add typeui --url https://mcp.typeui.sh/mcp` could not be verified because this shell's Codex CLI fails with `failed to resolve CODEX_HOME: Could not find home directory`.
- OpenDesign's Codex plugin requires its desktop application version 0.17.0 or newer. No installation was found at the standard Windows application paths; per its installer instructions, the desktop installer step awaits user confirmation.

### Left open

Connect TypeUI after the Codex CLI can access its configuration, then install and verify OpenDesign's local MCP/plugin only after its desktop-app prerequisite is installed. The supplied mockups remain the visual acceptance references for future UI work.

---

## 2026-09-30 — grounded model improvement and live product specification

### Attempted

Turn the user's accuracy, live UI, professional reports, plant demonstration and 3D requirements into an implementable sequence aligned with the judging brief.

### Worked

- Inspected KHANYA main `57a6b665a5370e5d8ba49a16ffaf95451538bc1e`, including the accuracy report, trainer/sampler, Stitch-derived Jinja dashboard and OPC UA regrind command module.
- Identified `random.Random(None)` as an explicit training reproducibility defect and balanced-patch checkpoint selection as a validation/deployment mismatch. The new specification makes deterministic sampling/resume and whole-section validation the first ticket.
- Added `docs/14-model-ui-report-and-spatial-build-spec.md`: staged run budgets and promotion gates; UI/data/state contracts; separate sample/accuracy reports; approved and acknowledged simulated plant commands; honest assay/geographical 3D boundaries; Figma/reference design workflow, acceptance tests and implementation prompt.
- Verified primary references for Petroscope, ZEISS, Leapfrog, QGIS, Carbon Figma kits, Supabase Realtime, OpenSeadragon and deck.gl. Read the existing dashboard's explicit removal of fabricated accreditation, recovery and plant-connection claims; retain those corrections in the PWA.

### Did not work

- Original generated mockup images were not located in the searched workspace/repo paths. The existing Stitch-derived template is available as the initial visual reference. The public Figma preview did not fetch; no Figma design was inspected or modified. The UI Skills catalogue CLI stalled and was stopped; local baseline UI guidance was read.
- No training run or deployed UI is claimed from this planning change. Better accuracy remains an experimental outcome, subject to frozen validation gates.

### Left open

Implement P0/U0 in the application history, then train the staged candidates and complete one real inference→reviewed simulator action→report path. Exact mockup comparison needs the original assets or Figma node URLs. External South African specimens and plant trials are still needed for generalisation and impact claims.

---

## 2026-09-30 — cloud CLI and FastAPI connection handoff

### Attempted

Translate the chosen Supabase + Cloudflare Pages + FastAPI stack into exact login, Git integration, local API and optional Azure steps without assuming a cloud deployment already exists.

### Worked

- Added `docs/13-cloudflare-azure-fastapi-connection-2026-09-30.md` with the service boundaries, CLI commands, Git-integrated Pages setup, configuration names, acceptance checks and official docs.
- Checked the local toolchain: Node 24.18.0, npm 11.16.0, Python 3.11.9, uv 0.9.30 and Azure CLI are present. The application folders and Wrangler are not present in this checkout.

### Did not work

- The restricted Codex shell cannot read the user's existing Azure CLI profile (`PermissionError` on `.azure/azureProfile.json`). A clean temporary Azure config says `Please run 'az login'`; this is not evidence about the normal terminal's login state. No Cloudflare or Azure resources were created.

### Left open

Confirm the intended Cloudflare account and Azure student subscription in the user's normal terminal, create the KHANYA app skeleton after the pitch freeze, then test a real authenticated fixture path locally before any optional paid API deployment.

---

## 2026-09-30 — product stack and phase-identification implementation handoff

### Attempted

Turn the user's Supabase + Cloudflare Pages + FastAPI decision into a build sequence that Luna or
Claude Sonnet can execute, while preserving the 1 October evidence-backed demo and the separate
REEFPRINT/KHANYA histories.

### Worked

- Added `docs/12-pwa-phase-identification-roadmap-2026-09-30.md` with the service boundaries,
  sample/inference API contracts, phone and desktop user journeys, UI states, mineral experiment
  queue, acceptance gates, source anchors and a copy-paste implementation prompt.
- Checked the existing local handover and S2 baseline. The private Kaggle retrain reports 0.4543
  pooled five-class mIoU and misses magnetite; the stronger KHANYA checkpoint's merged accuracy
  report remains separate. The plan requires model/report hashes and does not transfer one run's
  scores to another.

### Did not work

- No cloud account or model service was provisioned in this planning step; the new stack has no
  observed deployment or latency result yet. The current local checkout is the REEFPRINT
  measurement history, whereas the application code is on KHANYA's separate history.

### Left open

Implement the authenticated app skeleton and real pinned-checkpoint path on KHANYA after the pitch
freeze; run the reproducibility and rare-class experiments on training/validation data; acquire
independent South African expert-labelled sections before any site-performance claim.

---

## 2026-09-15 — session 39 · found a real J0/J1/J2 blocker before it could burn a GPU-hour

### Attempted

S1/S2 data still not in from Sibusiso, so J0/J1/J2 cannot start — but the checkpoint construction
step it depends on could be checked in isolation. `khanya/main:src/segmentation/model.py`
constructs the model via `deeplabv3_resnet50(weights=DeepLabV3_ResNet50_Weights.DEFAULT, ...)`,
and torchvision's weight-loading machinery is known to fall back to a network download unless the
checkpoint is already in its own hub cache under an exact expected filename — mounting it as a
Kaggle dataset at an arbitrary path does not satisfy that. Worth verifying directly rather than
assuming either way, before it became the first thing to go wrong once real data landed.

### Worked

- `experiments/014-coco-checkpoint-offline-preflight/`: pushed to Kaggle (`enable_internet:
  false`, matching every training kernel this project will run), completed in under a minute.
- **Confirmed the risk was real.** `model.py`'s current construction call fails with
  `URLError: Temporary failure in name resolution` — it would have crashed at the very first line
  of any J0/J1/J2 kernel, discovered only after Sibusiso's data had already landed and a GPU-hour
  had already started.
- **Two fixes confirmed working, not just proposed** — each tested end-to-end (model construction
  plus a real forward pass on a dummy tensor, checked for the correct output shape, not just "no
  exception raised"): pre-copying the mounted checkpoint into torch's hub cache under the exact
  filename torchvision expects, or constructing with `weights=None` and loading the state dict
  explicitly (the cleaner of the two — 0 missing keys, 0 unexpected keys).
- Also re-verified the checkpoint's sha256 against `SBOM.md`'s record on a live Kaggle kernel
  independent of the machine that first staged it — matched.
- **Corrected a premature claim this session had itself made** — `docs/09-brief-compliance.md`
  said "training kernels can now construct the model" the moment the checkpoint was uploaded. It
  could not, until this preflight found out and fixed it. Corrected in place rather than left to
  stand on an assumption nobody had tested.
- Flagged to Sibusiso via issue #5 with both fixes and a clear recommendation; his call which one
  to take in `model.py`. `WORKBOARD.md` (new correction C6), `CONTEXT.md` updated. Suite: 368
  passed, 4 deselected, unchanged (no library code touched — new experiment only).

### Left open

- `model.py` itself is unmodified — the fix is Sibusiso's to apply, on his branch.
- J0/J1/J2 still cannot start until S1/S2 data lands; this preflight only clears one of the two
  remaining blockers.

---

## 2026-09-15 — session 38 · two pre-registered protocols, a seam-call correction, and the tennantite finding

### Attempted

Checked `khanya/main` and issue #5 for new activity after session 37's push and found three real
threads: Sibusiso corrected the sensitivity-analysis seam call from session 37 (it belongs on
`main`, not here), delivered the corrected S1 benchmark with a decomposition that changes the
project's own causal story, and made a substantive case for reversing the rehearsal-deferral
decision from session 36.

### Worked

- **Absorbed a correction to session 37's own work, not just to something upstream.** Sibusiso
  checked rather than assumed: `reefprint` has no `modal.py` or morphology code at any path, so
  the refinement audit's "this belongs on the REEFPRINT side" framing (which session 37 took at
  face value and I did too) was itself wrong — running a parameter-perturbation audit of code
  that only exists on `main` would have blurred the ADR-0003 attribution boundary MOTT assesses.
  Recorded plainly rather than defended.
- **Built the pre-registration protocol instead** — the genuinely REEFPRINT-shaped role Sibusiso
  proposed: fix the perturbation grid and falsification criterion for his morphology-constants
  sweep *before* he runs it, so the author of the code under test does not set the bar after
  seeing the result. `docs/11-pre-registered-morphology-sensitivity-and-scaling-predictions.md`
  §1: 14 configurations (one-factor-at-a-time over `SPECKLE_KERNEL`, `SEED_MIN_DISTANCE`,
  `PEAK_FOOTPRINT`, plus two joint extremes), with a hard falsification line — any configuration
  producing even one "unsafe" severity classification (currently zero under the shipped
  constants) kills the "driven to zero" claim, no averaging or cherry-picking allowed.
- **Same document, §2**: a falsifiable, pre-registered prediction for the J0/J1/J2 scaling curve,
  formalising the threshold Sibusiso proposed in prose (matched classes move ≤±0.03; tennantite
  and magnetite must each clear +0.10 absolute *and* 3× the matched classes' movement, or the
  training-budget causal claim reverts to "measured, unexplained").
- **Absorbed the S1 benchmark fix and its real finding.** `reports/benchmark_s1_patches.json`
  corrected to 0.7116 plain / 0.7481 void-border (`ca2e02f`). The decomposition matters more than
  the number: tennantite alone is 60.8% of the gap to published; excluding it, six classes gap at
  only -0.0469 with three effectively matched. Tennantite is *more* abundant than chalcopyrite in
  train pixels yet scores far worse — rarity ruled out a second time, within one dataset this
  time. `CLAUDE.md` corrected to name tennantite alongside magnetite as the same
  low-reflectance-contrast/training-budget failure mode, not magnetite alone.
- **Raised a doubt about a standing claim rather than let a pattern go unchecked a third time.**
  The project's own "512→2,560 patches moved mIoU 0.33→0.71" line rests on the *same*
  `benchmark_s1_patches.json` that has now been shown stale twice. Whether 0.3295 ever honestly
  measured the 512-patch checkpoint is unverified — flagged in `CLAUDE.md` and `WORKBOARD.md`
  rather than left standing on an assumption the same file has already broken twice elsewhere.
- Suite unaffected — no library code touched this session, docs and one new pre-registration file
  only.

### Left open

- **Whether the 0.33→0.71 patch-budget claim survives** — asked Sibusiso directly; not yet
  answered.
- **The rehearsal-deferral reversal** — Sibusiso made a substantive case (a first rehearsal's job
  is discovery, not polish, and does not depend on numbers that have not landed yet) and proposed
  one unpolished timed run-through this week. This reverses guidance already relayed to Lethabo on
  their behalf; surfaced back to them rather than decided here.
- Neither pre-registered protocol has been run yet — both are locked, not executed.

---

## 2026-09-15 — session 37 · `main`'s hostile self-audit, and the sensitivity analysis it assigned to this side

### Attempted

Checked `khanya/main` for new activity beyond issue #5 and found three documents Sibusiso
published independently: a hostile critique of the whole submission against Problem 3's brief, a
proposed remediation plan responding to it, and an audit of the topology-refinement code every
reported number rests on. The audit's own §5 assigned one item explicitly to "the REEFPRINT side
of the seam under ADR-0003": a sensitivity analysis on whether refinement changes which sections
a decision-gap comparison flags, not just how many.

### Worked

- **Read all three documents in full before acting** — the critique's six cold-answer questions
  are sharper than this branch's own prior assessment: the model fails at 1.84% abundance on the
  one rare phase tested, and UG2's actual payload is rarer still; the published benchmark on this
  data is 0.88, not the 0.8373 this branch had been anchoring on; three of four decision
  thresholds in `advisor.py` are unsourced placeholders; the conformal band spans two-thirds of
  the possible range and is calibrated on the same 12 sections it is evaluated on.
- **Built the tool the audit's item needed and the plan had specified but never built.**
  `reefprint.trust.bootstrap` — `cluster_bootstrap_ci` (percentile bootstrap over independent
  units, seeded per Rule 5, predeclared 2000 resamples per the plan's own spec) and
  `paired_exact_test` (exact McNemar on paired binary outcomes, not the chi-squared
  approximation, which is untrustworthy at hackathon-scale n). 18 tests,
  `tests/test_trust_bootstrap.py`, including a known textbook reference case (10 discordant
  pairs split 9-1 gives p ≈ 0.02148) to check the exact-test arithmetic independently of the
  real data it was about to be pointed at.
- **Applied it to `main`'s own already-committed evidence, no cross-branch code import, no data
  transfer** — `experiments/013-decision-gap-refinement-sensitivity/` reads three small JSONs via
  `git show khanya/main:...` at run time, reproducible by anyone with this repo alone.
- **Answered the assigned question, both ways.** The aggregate decision-gap flip rate (0.50) is
  not an artefact of refinement — real evidence in the finding's favour, clearing the confound
  the audit worried about. But raw and refined predictions do **not** flag the same six sections
  (4 agree, 2 flip only under raw, 2 only under refined); an exact McNemar test on the 4
  discordant pairs gives p = 1.0, which at this sample size is "cannot tell," not "confirmed the
  same" — reported that way explicitly, via `PairedDisagreement.describe()`'s own low-power note,
  rather than let a non-significant p-value be misread as a clean result.
- **Found something nobody had asked for and verified it twice before trusting it.** The
  headline S2 mIoU (0.5725, `reports/lumenstone_s2_patches_test_metrics.json`) is pooled across
  all 12 sections' pixels; averaging each section's own `mean_iou` instead gives **0.4671**,
  bootstrap 95% CI [0.4116, 0.5362] — computed once inside the experiment, once independently in
  a standalone check against the raw JSON, both agreeing to the same fifteen significant figures.
  **Ten of twelve sections score below the reported 0.5725.** Same shape of problem as the
  1.58%/1.84%/0.792% magnetite-abundance mixup C4 already found: two legitimate conventions, no
  stated label, and a large enough gap between them (0.57 vs 0.47) that a judge reading both
  numbers in the same repository could read the gap as evasion rather than as two valid
  statistics — unless the convention is named next to whichever one reaches a slide.
- `WORKBOARD.md` (new correction C5), `docs/09-brief-compliance.md`, `CONTEXT.md` updated in the
  same session. Suite: 350 → 368 passed, 4 deselected (+18).

### Left open

- The same pooled-vs-per-section-averaged check on S1 — not run this session, a five-minute
  follow-up if it turns out to matter there too.
- Whether the raw-vs-refined section disagreement (`test_10`/`test_11` vs `test_06`/`test_08`) is
  a real effect or noise remains genuinely unresolved at n=12 — flagged honestly rather than
  guessed at either way.
- The rest of the critique's findings (invented thresholds, the wide conformal band, the wrong-
  customer cost anchoring, AI-authorship/MOTT risk, the unattributed third team member) are
  `main`-side or human items this branch cannot act on directly — read `WORKBOARD.md` §0 C5 and
  the source documents before the pitch.

---

## 2026-09-15 — session 36 · four process questions from Sibusiso, before he writes issue #5 into HANDOVER.md

### Attempted

Sibusiso's follow-up on issue #5 raised four real questions rather than closing the thread:
checkpoint reproducibility, a shared report-provenance schema, what the day-20 freeze actually
buys given an unresolved checkpoint-distribution problem, and a joint rehearsal slot.

### Worked

- **Recommended Git LFS for `checkpoints/` on `main`**, and said why: it is the option that keeps
  the checkpoint tied to the commit history, which is the actual mechanism ADR-0003/Rule 8 already
  rely on as the MOTT originality defence. An external link (Kaggle, a plain download URL) breaks
  that chain for the one artifact the headline accuracy number depends on. Kaggle hosting is not
  wasted work either way — it answers a different question (kernel mounting under
  `enable_internet: false`), not the judging-reproducibility one.
- **Agreed to `checkpoint_sha` + `generated_at` as a shared convention**, and pointed out
  `reefprint` already has the generalised version of the same idea: `reefprint.quantity.Quantity`
  refuses to construct without a non-empty, contagious `source`. Worth stating in the eventual
  writeup as evidence the two branches converged on the same discipline independently rather than
  by copying — which is exactly the kind of thing that helps under MOTT's two-clean-histories
  originality defence.
- **Settled the ordering**: reproducibility (Q1) before scheduling any GPU time for J0/J1/J2,
  since an unresolved distribution problem on the current checkpoint is the same problem on a
  future one, just later.
- **Rehearsal deferred, not declined** — asked the user directly rather than inventing a date;
  answer was to hold off until J0/J1/J2 results exist, so there is something new to rehearse
  rather than a draft about to change.

### Left open

- Sibusiso to actually decide and implement the LFS (or alternative) migration on `main` — this
  session can recommend but not execute across the branch boundary (ADR-0003).
- The rehearsal slot itself, once data lands.

---

## 2026-09-15 — session 35 · sourced LumenStone V1 directly, closing the one open item left in session 34

### Attempted

`CONTEXT.md`/`WORKBOARD.md` §0 C4 left LumenStone V1 (the colour-adaptation subset) as unsourced
by either side. Rather than leave it as a standing cross-person ask, tried fetching it directly
from the dataset's own page.

### Worked

- The dataset's own summary table (`imaging.cs.msu.ru/en/research/geology/lumenstone`) names a
  direct Yandex Disk link for V1 (100 MB). Yandex Disk's public API
  (`cloud-api.yandex.net/v1/disk/public/resources/download`) converts a shared-folder URL into a
  real download URL without needing an account. Downloaded `V1_v1.zip`, 104,705,467 bytes,
  matching the published 100 MB exactly.
- **Verified, not assumed**: unzipped and counted — exactly 30 `.jpg` files (`001.jpg`… `010.jpg`,
  each with `a`/`b` variants), matching "10 samples × 3 imaging variations" precisely.
- Staged at `data/lumenstone/V1_v1.zip` (gitignored, same DVC-tracked convention as `S3_v2.zip`)
  and uploaded as a private Kaggle dataset, `lethabomh14/lumenstone-v1-reefprint`, so either
  branch's kernels can mount it the same way `lumenstone-s3-v2-reefprint` already is.
- `SBOM.md`, `docs/03-free-stack.md`, `WORKBOARD.md` §0 C4, `CONTEXT.md` updated. This closes the
  one item session 34 left open after Sibusiso's response.

### Left open

- Still needs someone (most naturally Sibusiso, since `robustness.py` lives on `khanya/main`) to
  actually re-run the robustness sweep against this real data and replace the synthetic
  white-balance/exposure numbers `robustness.py`'s own docstring already flags as the weaker
  evidence.

---

## 2026-09-15 — session 34 · Sibusiso answered issue #5: one plan item retracted, magnetite is worse than reported

### Attempted

Read and acted on Sibusiso's full response to [issue #5](https://github.com/Sibusiso-K/KHANYA/issues/5)
(three comments: the four asks answered, a self-correction of his own mislabelled model, and a
sharpened magnetite finding). Replied confirming the one thing he asked this side to decide.

### Worked

- **The stale benchmark is fixed on the other side, not blocked here any more.** Sibusiso
  independently confirmed the same diagnosis this session made (checkpoint 21 Aug, cache 17 Aug)
  and is regenerating `reports/benchmark_s1_patches.json` himself.
- **A real flaw in this session's own plan, caught before it produced a wrong claim.** The
  S1 v1/v2 test-stem check (Workstream D2, `docs/10-2026-09-14-literature-and-brief-plan.md`)
  assumed matching filenames meant matching images. Sibusiso: `test_01.jpg`–`test_20.jpg` are
  **positional, not identity-bearing** — if the authors renumbered when adding images between
  versions, the same filename in v1 and v2 is not provably the same photograph. The only sound
  version needs content-hashing the actual v1 image files, a separate, currently unavailable
  download. **Retracted rather than run** — exactly the kind of error Rule 1 exists to catch, and
  this time a collaborator caught it first.
- **J0/J1/J2 framing settled on the record**: replied confirming it is a scaling study reported
  as evidence, never an attempt to ship a checkpoint that touches the demo or the 25 Sep freeze —
  which is what the plan always meant, made explicit because he asked rather than assumed it.
  He sends S1+S2 on this basis.
- **The magnetite finding is the substantive result of this exchange, and it corrects a claim
  this project had already published in `CLAUDE.md`.** Sibusiso rebuilt the confusion matrix
  against the real patches checkpoint (catching and publicly correcting his own first attempt,
  which used the superseded "resize baseline" pipeline by mistake — kept visible in the thread
  rather than edited away, the same retraction discipline this project's own BUILDLOG runs on).
  Result, all 12 S2 test sections: of 821,587 true magnetite pixels, **0 are ever predicted as
  magnetite**, across 92.6 million test pixels — a dead output channel, not a weak score. Two
  arguments rule out the easy excuses: S1 chalcopyrite, at a similarly low train share, scores
  0.8652 (rarity alone is not it), and Korshunov et al. detect magnetite at 0.650 on the same
  modality (it is not an optical limit). **`CLAUDE.md`'s "our magnetite problem is the
  literature's magnetite problem" was too generous and has been corrected** — the honest reading
  is a training-budget or model-capacity gap on our side, which is a stronger reason to run the
  scaling study than "see if the mean improves."
- **Fixed a three-numbers-one-name problem.** 1.58% (ledger), 1.84% (`STATUS.md`, train share),
  0.792% (test share — the number the model was actually scored against) were all circulating as
  "the magnetite abundance." Standardised on the test share and labelled it, per Sibusiso's own
  argument: it is the stronger, more honest answer to "have you tested below 1% abundance" (yes,
  and it failed completely there), where the train-share number would have understated the case.
- `CLAUDE.md`, `WORKBOARD.md` §0 (new correction C4), `CONTEXT.md`, `docs/09-brief-compliance.md`
  all updated in the same session to carry the corrected framing.

### Left open

- S1+S2 data still incoming from Sibusiso; J0/J1/J2 cannot start until it lands.
- Whether magnetite's dead-channel failure is fixable by budget alone (this project's working
  hypothesis) or needs something more (a loss-function or sampling change) is not yet tested —
  the scaling study is designed to distinguish this, not assume it.

---

## 2026-09-15 — session 33 · the S3_test_03 visual check ran, and it is genuinely inconclusive — a real finding, not a failure

### Attempted

The next action session 32 left open: the visual check `experiments/009-s3test03-visual-check/`
ran on the grid search's `S3_test_03` offset, now owed to SIFT+RANSAC's offset before it can be
called a claim. Built `experiments/012-s3test03-sift-visual-check/`, extending 009's exact method
(same section, same sample-frame indices, same red/green overlay convention) to three candidates
side by side — naive, grid, SIFT+RANSAC.

### Worked (in the sense of "produced a real, checkable result" — not "confirmed the hoped-for answer")

- **Full-frame overlays for all three candidates read the same way 009's original naive/grid pair
  did**: broadly similar yellow-green coverage across the specimen interior, no candidate
  obviously more internally coherent by eye. This reproduces 009's own finding on the same
  section with a third candidate added, rather than contradicting it.
- **A zoomed, programmatically-selected landmark check** (local-variance maximum, chosen without
  looking first, to avoid picking a spot that happens to flatter one candidate) also did not
  resolve it — none of the three conditions showed an unambiguous, confidently-matched landmark
  against the reference.
- **A pixel-correlation re-check was tried and explicitly rejected as circular**: it favoured the
  grid search's own offset, which is exactly what should happen and proves nothing, since
  whole-frame correlation is literally `estimate_rotation_centre`'s own optimisation objective. A
  metric cannot arbitrate between two candidates when one of them was chosen to maximise it.
- **The working explanation is the one already on record**: `experiments/010`'s hypothesis that
  real mineral texture's self-similarity gives the correlation search multiple near-tied optima
  applies just as much to a human eye trying to match a grain by sight. `009`'s check worked
  because that section had one unusually distinctive, trackable grain (dark inclusion, fine
  internal cracks); this landmark, on this section, did not offer an equally decisive feature.
- **A new, non-visual argument surfaced by looking closely at numbers already in hand, not by
  anything visual**: `S3_test_03`'s SIFT-matched frame pairs found up to **17,074 inliers in a
  single frame**, every one independently required by RANSAC to be consistent with **one** rigid
  transform at under 1.5 px average residual. Thousands of independently-matched point
  correspondences agreeing with each other is a real cross-check the grid search has no
  equivalent of, and it does not depend on a human eye resolving a self-similar texture.

### Did not work

The visual check itself did not settle the question, which is the honest result to report — not
a confirmation dressed up as one, and not a retraction either. Full account, including the images
looked at and the reasoning for rejecting the correlation re-check:
`experiments/012-s3test03-sift-visual-check/README.md`.

### Left open

- **`S3_test_03`'s SIFT+RANSAC offset is still not a claim.** The case for it rests on
  determinism, cross-section consistency, harmonic-verdict agreement, and RANSAC inlier
  consistency — not on visual confirmation, which turned out not to be available on this section.
- The grid search's own determinism on real data remains unchecked, as it has been since
  `experiments/010`.
- `experiments/012`'s own recommendation, if more confidence than this is needed: check whether
  the RANSAC inlier-consistency argument holds on a second, independently-chosen frame pair not
  already used in the reported estimate — not another visual check, since this one showed that
  path does not resolve anything further on this section.

---

## 2026-09-15 — session 32 · SIFT+RANSAC vs the grid search on the real archive: determinism confirmed, `S3_test_03` looks recoverable

### Attempted

Ran the fixed `experiments/011-sift-ransac-registration` kernel to completion — the comparison
session 29's runtime fix made tractable. ~3 hours wall-clock, CPU only.

### Worked

- **Determinism confirmed on real data.** `S3_test_01` run twice in-process inside the kernel:
  bit-for-bit identical `offset_xy` and per-frame diagnostics. This is the exact property
  `experiments/010` proved the grid search does not have, now demonstrated on the estimator built
  to replace it — the strongest evidence yet that Rule 10's premise was right for this case.
- **Close agreement on 4 of 5 sections.** `S3_test_01/02/07/12`: grid and SIFT+RANSAC offsets
  agree to within 3–8 px, and every harmonic verdict matches between the two methods.
- **`S3_test_03` — the section that mattered most — SIFT+RANSAC's answer fits the pattern the
  grid search's answer broke.** Grid search: offset (−397, 41), verdict `FOURTH`, already
  retracted (`WORKBOARD.md` §0 C1, `experiments/009`'s visual check). SIFT+RANSAC: offset
  (−111, 22) — sitting inside the same tight band ((−91 to −107, 21 to 75)) the other four
  sections' offsets occupy — verdict `SECOND`, matching what the naive, zero-registration
  condition on that same section already reads. **Not promoted to a claim**: the same visual
  check that retracted the grid search's answer on this exact section has not yet been run on
  this one, and this project has already been burned once by a "plausible-looking" offset here.
- **A genuine, unexplained-until-now cost finding, reported per Rule 8/9 rather than buried.**
  Per-section runtime did **not** track frame count: `S3_test_07`/`S3_test_12` (24 frames each)
  took as long as `S3_test_01`/`S3_test_03` (71-72 frames). The per-frame diagnostics point at the
  real driver — `match_descriptors(cross_check=True)` is brute-force, quadratic in keypoint
  count, and `S3_test_03`'s richest frame pair matched **17,074 inliers**. Frame count was capped
  (`MAX_SIFT_FRAMES`, session 29's fix); keypoint count per frame was not, and turned out to be
  the actual unbounded dimension. Left unfixed — the current result is usable and a re-run costs
  another ~3 hours — but recorded in `experiments/011-sift-ransac-registration/README.md` so the
  next person to touch this estimator does not re-discover it from scratch.
- Full table, caveats, and the cost analysis: `experiments/011-sift-ransac-registration/README.md`.
  `WORKBOARD.md` §3 (P5), `CONTEXT.md` §3, and `docs/09-brief-compliance.md` updated in the same
  session.

### Left open

- **The visual check on SIFT+RANSAC's `S3_test_03` offset** — the actual next action on P5, same
  method as `experiments/009`.
- **The grid search's own determinism on real data remains unchecked.** This run only checked
  SIFT+RANSAC's determinism; whether the grid search's `S3_test_03` answer would reproduce on a
  repeat run is exactly the question `experiments/010` left open, still open.
- The keypoint-count cost driver is a real robustness gap in
  `estimate_rotation_centre_sift_ransac` for future use (a texture-rich real section can make one
  frame pair's matching arbitrarily expensive) — not fixed this session.

---

## 2026-09-15 — session 31 · widened the backbone licence guard to match the actual model (Workstream F)

### Attempted

`reefprint.segment.backbone.require_permissive_backbone()` permitted only `timm`/Apache-2.0 —
but KHANYA's real segmentation model (`khanya/main:src/segmentation/model.py`) is
`torchvision.models.segmentation.deeplabv3_resnet50`. A guard that would refuse the actual build,
had anyone called it, is a guard nobody trusts.

### Worked

- `PERMITTED_BACKBONES` replaces the single hardcoded pair — `timm`/Apache-2.0 and now
  `torchvision`/BSD-3-Clause. The check is exact: name **and** licence must both match a known
  entry, so a caller cannot satisfy it by passing the right name with a guessed licence string
  (`tests/test_segment.py::test_backbone_licence_check_is_exact_not_just_the_name`).
- **Read, not assumed**: torchvision's own `LICENSE` (BSD-3-Clause) covers the code and makes no
  statement about distributed pretrained weights; `DeepLabV3_ResNet50_Weights.DEFAULT`
  (`COCO_WITH_VOC_LABELS_V1`) is confirmed against torchvision's own model docs to be trained on a
  COCO subset restricted to the 20 Pascal VOC categories, with the ResNet50 backbone itself
  pretrained on ImageNet. Neither COCO nor ImageNet publish a blanket redistribution licence for
  their underlying images. **The architecture is licence-clean; the specific checkpoint is not**,
  and `SBOM.md`'s checkpoint table now says so as CONDITION, not OK — closing a row that
  previously read `*(none selected yet)*` while a COCO-pretrained checkpoint was already in use.
- Suite: 349 → 350 passed, 4 deselected (+1). `CONTEXT.md`/`WORKBOARD.md` counts and
  `docs/09-brief-compliance.md` updated in the same commit.

### Left open

- **The checkpoint itself is not yet pre-uploaded as a pinned Kaggle dataset.** Training kernels
  run `enable_internet: false`, so `DeepLabV3_ResNet50_Weights.DEFAULT` would fail at model
  construction on Kaggle as things stand — this blocks J0/J1/J2 (Workstream C) starting, separate
  from the S1/S2 data upload Sibusiso was asked for.
- The checkpoint's permission-chain caveat is recorded, not resolved — resolving it (a written
  clearance, or a decision to accept the risk and say so in the submission) is a domain-lead call,
  not a code fix.

---

## 2026-09-15 — session 30 · wired the plant-parameter advisory demo into the offline demo (Workstream E)

### Attempted

The brief's most judge-visible line — "demonstration of how the model's output can be used to
adjust plant parameters" — had a real, tested implementation (P1: `AdvisoryServer`,
`SimulatedControlClient`, `RefusedStaleAdvisory`) that nothing ever rendered on screen. Add the
third panel `docs/10-2026-09-14-literature-and-brief-plan.md`'s Workstream E specifies: advisory
published → simulated setpoint moves → stale advisory refused, setpoint unchanged.

### Worked

- **`src/reefprint/viz/advisory.py`** — `SimulatedSetpoint`, `AdvisoryOutcome`, `apply_or_refuse`,
  `advisory_figure`. Renders the setpoint's real history alongside an explicit refusal panel,
  mirroring `decision_figure`'s rule that a refusal is a coloured status, never a blank panel.
- **A real constraint caught before it became a bug**: `tests/test_viz.py::test_demo_runs_fully_offline`
  monkeypatches `socket.socket` to raise if the demo opens *any* socket, including a loopback one
  — and `AdvisoryServer` genuinely binds one to listen. Wiring the real OPC UA server/client into
  `offline_demo()` would have broken that test on the first run. Instead, `apply_or_refuse`
  reproduces `SimulatedControlClient.poll_and_apply`'s exact decision
  (`AdvisoryRecord.is_expired(now=...)`) directly against the record, with no network read —
  `AdvisoryRecord` is genuinely dependency-free by its own module docstring, so this needed no new
  dependency and no compromise on the "fully offline" guard. `SimulatedSetpoint` is a deliberate
  local reimplementation of `opcua_client.SimulatedPlantParameter`, not an import of it — that
  module does `from asyncua import Client` unconditionally at module scope, and importing it would
  have made the *offline* demo depend on the optional `integrate` extra just to draw a panel.
- **The module docstring says plainly what this is and is not**: the same acknowledgement-and-
  expiry contract as the real wire path (`tests/test_integrate.py::test_opc_ua_server_exposes_advisory_values`),
  shown without the network — not a substitute for that test, and not to be presented as the wire
  proof.
- `OfflineDemo` gained a third field, `advisory: Figure`. 4 new tests
  (`tests/test_viz.py`): a fresh advisory moves the setpoint, a stale one leaves it untouched with
  no history entry at all, `advisory_figure` refuses to render an applied outcome as a refusal
  (its own contract check), and the figure's refusal panel + held value are both actually on
  screen. `test_demo_runs_fully_offline` extended to assert the third panel's content, and still
  passes with the socket guard active.
- Suite: **345 → 349 passed, 4 deselected**. `CONTEXT.md`/`WORKBOARD.md` counts and
  `docs/09-brief-compliance.md`'s row updated in the same commit.

### Left open

- The real, networked OPC UA round trip remains proven only by `tests/test_integrate.py`; nothing
  in this session changes that coverage, by design.

**Follow-up, same day: Workstream F's remaining item — the COCO checkpoint is now pinned on
Kaggle.** `enable_gpu: true` training kernels run `enable_internet: false`, so
`DeepLabV3_ResNet50_Weights.DEFAULT` would fail to construct at all on Kaggle without the weight
pre-staged. Downloaded `https://download.pytorch.org/models/deeplabv3_resnet50_coco-cd0a2569.pth`
directly by HTTP (no `torch`/`torchvision` install needed locally — those are KHANYA's
dependency, not REEFPRINT's, and pulling multi-GB packages into this environment just to fetch one
160 MB file would have been the wrong tool). Verified: sha256
`cd0a25694c4a0f7106b38f4938bf90a874f2f241cc410b8f63c7024399538f06`, matching the `cd0a2569` prefix
torchvision embeds in its own filename as an integrity check — genuine, uncorrupted. Uploaded as a
private Kaggle dataset, `lethabomh14/torchvision-deeplabv3-resnet50-coco`. `SBOM.md`'s checkpoint
table updated with the full record. **This unblocks model construction on a training kernel; the
S1/S2 data upload (issue #5, still open) is the separate, remaining prerequisite for J0/J1/J2 to
actually run.**

**Follow-up, same day:** the backup GIF was still two screens — `experiments/004-backup-video/run.py`
only ever rendered `demo.gate` and `demo.refusal`, so it silently missed the new third panel.
Fixed (`experiments/004-backup-video/`): now renders `demo.advisory` too. Regenerated and viewed
frame-by-frame — all three screens render correctly, including the setpoint moving 0.0 → 0.62 and
the explicit refusal text (`fine_chromite_risk = 0.91 arrived 301s old, past its 300s validity
window`).

---

## 2026-09-14 — session 29 · experiment 011's first Kaggle push ran for hours; found and fixed the cost driver, not yet a real-data result

### Attempted

Ran `experiments/011-sift-ransac-registration` (session 28's SIFT+RANSAC estimator vs the
existing grid search, on the real S3 v2 archive) on Kaggle as
`lethabomh14/reefprint-p5-sift-ransac-registration`.

### Did not work

**The kernel did not finish.** `experiments/007-s3v2-registration`'s comparable job (grid search,
12 sections attempted, 5 measurable, full 3396x2547 resolution) completed in ~10 minutes. This one
was still `RUNNING` after several hours with no sign of finishing. Diagnosed rather than just
killed: the design ran `estimate_rotation_centre_sift_ransac` **twice per section** (the
determinism check) on **every "other" frame** (up to 71 per section) at `SIFT_DOWNSAMPLE=2`
(~2 megapixels each), and the estimator itself runs a fresh `SIFT().detect_and_extract()` on every
frame with no caching between the two calls. Worked backwards from the arithmetic: up to
~71 frames × 2 calls × up to 5-12 sections attempted is on the order of a thousand full
detect-and-extract-and-match-and-RANSAC passes, none of which existed in 007's design at all.
**Deleted the stuck kernel** (`kaggle kernels delete -y`) rather than wait it out or let it
silently keep consuming session time — it is a private, disposable Kaggle artefact, not a git
history or a repo file, and this project's own convention (sessions 16f, 23–26) already treats
kernel iteration as normal.

### Worked

- **`MAX_SIFT_FRAMES = 10`**: SIFT+RANSAC now runs on an evenly-spaced subsample of at most 10
  frames per section (`_evenly_spaced_indices`, deterministic — `np.linspace` rounded, not
  random), not all 71. The per-frame estimator's accuracy and determinism are properties of the
  method and its seeded RNG, not something 71 frames demonstrate better than 10.
- **The determinism check now runs on only the first usable section**, not every section — the
  same reasoning: determinism is a property of the code, checking it five times adds no
  information the first check didn't already give, at five times the cost.
- **The grid search and the full-resolution harmonic-verdict reconstruction are unchanged** — they
  were never the identified cost driver (007 already proves that part fits comfortably in ~10
  minutes at full resolution), so nothing there needed touching.
- Re-pushed as a fresh kernel version (same slug), currently running — result not yet in.

### Left open

- **Still no real-data result.** This session fixed a runtime problem, not the actual P5 question.
  The next check-in is whether the fixed kernel completes in a reasonable time and what it finds.
- If the fixed kernel is *still* too slow, the next lever is dropping `SIFT_DOWNSAMPLE` toward
  `GRID_DOWNSAMPLE`'s value (trading keypoint match quality for speed) rather than cutting
  `MAX_SIFT_FRAMES` further, since 10 frames is already a fairly thin basis for the per-frame
  diagnostic this method's whole value proposition rests on.

---

## 2026-09-14 — session 28 · built the published SIFT+RANSAC registration estimator, per Rule 10

### Attempted

Session 27 wrote Rule 10 (check the published method before inventing one) into `CLAUDE.md`,
motivated directly by `experiments/010`'s finding that the bespoke grid-search registration
estimator is not reproducible run to run on real data. This session applies the rule to the case
that motivated it: build Korshunov et al. 2025's published registration method — SIFT keypoint
matching + a RANSAC-fitted rigid transform — as a second estimator, and validate it the same way
the first one was validated, before running it on the real archive.

### Worked

- **`reefprint.acquire.registration.estimate_rotation_centre_sift_ransac`** — for each frame,
  SIFT keypoints are matched against the reference frame, a RANSAC-fitted `EuclideanTransform`
  (rotation + translation, no scale — appropriate for a rigid rotation) gives that frame's
  independent estimate of the true rotation centre by solving for the transform's fixed point
  (`c = R c + t` rearranges to `(I - R) c = t`), and the per-frame estimates are combined by
  median. No new dependency — `scikit-image` (BSD-3-Clause) already declares `SIFT`,
  `match_descriptors` and `ransac`.
- **Deterministic by construction, unlike the estimator it complements.** SIFT itself draws no
  randomness; `skimage.measure.ransac`'s sample selection does, and it takes an `rng` argument
  that was previously left to its own unseeded default in every reference I checked online —
  seeding it (`rng=0` by default) was the one-line fix the grid search's own missing tie-break
  rule needed and did not get. Confirmed directly: three repeated calls on identical synthetic
  input return bit-for-bit identical `offset_xy` and per-frame diagnostics.
- **Diagnosable per frame, which the grid search is not.** Each `SiftRansacFrameEstimate` carries
  `inlier_count`, `match_count`, `residual_rms`, and the independently fitted `fitted_angle_deg`
  compared against the frame's known nominal angle — so a bad frame can be identified and reasoned
  about, rather than only contributing silently to one combined number.
- **Validated on synthetic data**, mirroring the existing suite's own leg-(a) discipline
  (`tests/test_registration.py`, 6 new tests): recovers a known 8px/-5px off-centre offset to
  well under a pixel; a correctly-centred negative control reads within a pixel of zero; per-frame
  fitted angles agree with known nominal angles to within a degree with ≥8 inliers each; bit-for-
  bit determinism across repeated calls; refuses mismatched/empty input with the same contract as
  the existing estimator; and a frame sharing no structure with the reference correctly reports
  `centre_xy=None` rather than fabricating a number (Rule 1's discipline, applied at the seam
  where SIFT+RANSAC could otherwise return a low-confidence fit indistinguishable from a good one).
- Suite: **345 passed, 4 deselected** (+6). `CONTEXT.md` §4 and §7 and `WORKBOARD.md`'s two count
  lines updated in the same commit — the doc-count guard caught the stale 339 immediately, exactly
  what it is for.

### Did not work

Nothing failed. `ruff check` initially flagged two unused `image_centre` locals in the new tests
(left over from an earlier draft that computed `true_centre` relative to it) — removed.

### Learned

The synthetic test fixture already in this file (`_synthetic_field`: a flat noise field with 10
sparse blobs) does not give SIFT enough distinctive local structure to match reliably — it was
built for pixel correlation, a different kind of signal. A new fixture (`_sift_texture`: ~50 blobs
of varying radius and intensity) was needed specifically for SIFT's keypoint detector. Worth
remembering before reusing a synthetic fixture across estimators that work on genuinely different
principles.

### Left open

- **Not yet run against the real S3 v2 archive.** The next action: a new Kaggle kernel
  (`experiments/011-...`, following the `007`–`010` pattern) running this estimator on the same
  five real sections `experiments/010` found the grid search non-reproducible on, reporting its
  own determinism check on real data and comparing its offsets and per-frame diagnostics against
  the grid search's.
- Per Workstream G: if this estimator also disagrees or fails determinism on real data, the grid
  search's own fix (pinned thread counts, a tie-break rule, a landscape diagnostic) is still
  needed and has not been started.
- Whether to promote this into the "official" P5 estimator, keep both, or use disagreement between
  them as its own diagnostic is not yet decided — deferred until real-data results exist.

---

## 2026-09-14 — session 27 · anchored the brief and a literature pass in `CLAUDE.md`; found the S1 benchmark number was stale

### Attempted

The domain lead asked where the official hackathon brief should live so every task is measured
against it, whether we meet it, and what a literature review of ore-microscopy segmentation says
about how to close the gap to the published ResUNet benchmark (mIoU 0.8373) without using its
GPL-3.0 code or its trained weights.

### Worked

- **Found and corrected a stale benchmark artefact that made the project look 2.5× worse than it
  is.** `khanya/main:reports/benchmark_s1_patches.json` (committed `1cda84d`, 17 Aug) reports
  S1 mIoU **0.3295** against the published **0.8373** — but it scores *cached predictions* from
  the superseded 512-patch checkpoint (`src/benchmark.py`: *"Uses the CACHED predictions… no
  inference"*), and the model was retrained at 2,560 patches afterwards without the cache being
  remade. The real, current number — `reports/lumenstone_s1_patches_test_metrics.json`
  (`ebf2b15`, 24 Aug), same 7 classes, same 20 test images — is **0.7116**. Re-caching and
  re-running `src/benchmark.py` is the outstanding fix (zero GPU-hours), tracked as
  `docs/09-brief-compliance.md` §1 "Accuracy report".
- **`CLAUDE.md` now carries the brief and its judging criteria verbatim** in a new §"What we are
  judged on", and a new §"What the literature says drives accuracy here" — seven factors from
  three sources, each cited (petroscope README; **Korshunov et al. 2025**, *Mining Sci. & Tech.
  (Russia)* 10(3):232–244, doi:10.17073/2500-0632-2025-05-416, CC BY 4.0, the LumenStone dataset
  authors' own paper, fetched and read in full; **Jiang et al. 2024**, *Minerals* 14:1281,
  doi:10.3390/min14121281, read via search summary only — MDPI returned 403 on direct fetch, so
  its figures are marked indicative, not citable, until the PDF is read).
- **New Rule 10**: check the published method before inventing one. Retroactively explains
  `experiments/010`'s finding — our bespoke registration search is not reproducible, and
  Korshunov et al.'s published method (SIFT + RANSAC affine, `skimage`, BSD-3-Clause, already a
  declared dependency) is a zero-new-dependency fix nobody had tried.
- **The cross-version asterisk on 0.8373 turns out to be near-free to remove.** The LumenStone
  dataset page states each version contains all previous images plus additional samples — S1 v1
  is 59 train + 16 test, v2 is 64 train + 20 test — so if v1's 16 test stems are a subset of v2's
  20 (unverified, needs the filename list from Sibusiso), evaluating the existing checkpoint on
  those 16 gives a direct, like-for-like comparison at **zero GPU-hours**. This replaces a planned
  train-on-v1 retraining step.
- **Built the requirements-traceability ledger** `docs/09-brief-compliance.md`, requested by
  `docs/07-audit-prompt.md:258` and never built until now — one row per literal requirement,
  evidence as a path or test name.
- Updated `WORKBOARD.md` (stale day count 19 → 17, §2 gained an Evidence column, §8 gained two
  ritual steps), `docs/08-handover.md` §4 (superseded, now points at the ledger instead of
  carrying a second copy of the deliverables table), `docs/03-free-stack.md` (LumenStone subsets
  S1/S2/S3/V1/P1/P2/ICM1 recorded, plus the Korshunov citation), and `SBOM.md` (LumenStone's terms
  of use quoted verbatim, closing a standing VERIFY item — it was an unconfirmed informal claim,
  now a sourced quote).
- Full agreed plan recorded at `docs/10-2026-09-14-literature-and-brief-plan.md`.
- Suite: **339 passed, 4 deselected**, unchanged — no code touched this session, docs only.

### Did not work

Nothing failed. This was a research and documentation session; no code changed.

### Learned

Two of the four unresolved items on the project (the cross-version benchmark caveat, and the
LumenStone data licence VERIFY) were both closer to resolved than assumed — the dataset's own
page had the answer to both, and nobody had fetched it in full before today. **Rule 10 exists
because of this pattern repeating**: `experiments/010`'s non-reproducible search is the same
failure mode as an un-fetched licence page — a question answerable from a primary source, guessed
at instead.

### Left open

- The v1/v2 stem-subset check itself — needs the 16-name filename list from Sibusiso, not yet
  requested at time of writing.
- SIFT+RANSAC as a P5 registration method — proposed, not yet implemented or run.
- The Jiang et al. 2024 ensemble figures (mIoU 91.65) remain indicative until the PDF is read in
  full rather than via search summary.
- LumenStone V1 (the colour-adaptation subset) is not yet in this checkout or on Kaggle.

---

## 2026-09-13 — session 26 · the S3_test_03 mask fix failed, and found something worse: the search itself is not reproducible

### Attempted

Per experiment 009's recommendation: mask out the frame border and background before scoring, so
`S3_test_03`'s registration search cannot be won by aligning non-specimen content, and re-run.

### Worked, in the sense that it found the truth rather than a comforting answer

- **`experiments/010-s3test03-masked-rerun/`** adds `roi_mask` support to
  `reefprint.acquire.registration.estimate_rotation_centre` (a boolean array restricting which
  pixels the correlation objective scores), validated on controlled synthetic data first: a
  region carrying independent random noise (no genuine rotational relationship to anything, a
  stand-in for background that does not share the specimen's rotation) measurably dilutes the
  discrimination between the true offset and a wrong one when included, and excluding it via
  `roi_mask` sharpens that gap back up and still recovers the true offset accurately. Two new
  tests, 9/9 passing in `tests/test_registration.py`.
- **Run for real on Kaggle** (`lethabomh14/reefprint-p5-masked-rerun`, ~7 min): a mask excluding
  a 20% border margin and the darkest 15% of pixels (background/resin, per CLAUDE.md's own
  reflectance table). Result: the masked search found an **even larger** offset than before
  (−248, +403 vs the earlier −397, +41) and the resulting harmonic verdict got *worse*
  (`NEITHER`, both harmonics now under threshold, against the naive condition's clean `SECOND`
  at 9.35). The mask did not help.

### Did not work — and this is the real finding

**Checking why the mask made things worse surfaced that the search itself is not reproducible.**
This run's *unmasked* search — same code (checked with `git diff`: the unmasked path is
byte-identical to what produced session 23's result), same section, same archive — found an
offset of roughly (−50, +5), not session 23's (−397, +41). Four times smaller, different sign
structure, not a rounding-level difference.

Before concluding this was environmental drift (a Kaggle container image update, a different
JPEG decoder), checked the one thing that would prove or disprove it directly: this run's
*naive* condition — a completely separate computation from the search, using the same decoded
frame stack — matches session 23's naive numbers **bit-for-bit**: `snr_2 = 9.350294830486483` in
both runs, to sixteen significant figures. If decode, archive mount, or frame ordering had
drifted between the two Kaggle runs, this number would not match exactly. It does. The raw pixel
data feeding both runs is provably identical, and the code path is provably identical. The
search itself produced two different answers from the same inputs.

The working hypothesis, stated as a hypothesis and not asserted as fact: real mineral texture is
self-similar at the scale of individual grains, so the correlation objective the coarse-to-fine
search climbs likely has multiple local optima of similar height rather than one clear peak.
Which one the coarse (first) pass lands in can then come down to floating-point summation order
inside `warp`'s interpolation or `corrcoef`'s reduction — order not guaranteed identical run to
run under multi-threaded BLAS, even with unchanged code and unchanged input.
`_coarse_to_fine_search`'s own `if score > best_score` comparison has no tie-break rule for
exactly this situation — CLAUDE.md Rule 5 says sort every set traversal and tie-break every
min/max, and this comparison does neither.

### Learned

**A registration search validated only on synthetic data, where the true optimum is usually the
only real peak, can hide a landscape problem that only shows up on the noisier, more
self-similar texture real data actually has.** `tests/test_registration.py`'s synthetic cases
all use sparse, well-separated blob features specifically because they are easy to reason about
— which is also exactly the property that makes them a poor test of whether the objective has
competing near-tied optima. The gap between "passes on synthetic data" and "reproducible on real
data" is not the same gap as "passes on synthetic data" and "correct on real data," and this
session conflated them until the numbers stopped matching.

**Escalate immediately when a fix for a small problem uncovers a bigger one, rather than finish
the small fix first.** The mask fix was abandoned mid-investigation the moment the
non-reproducibility became visible, because continuing to tune the mask against a search that
cannot even reproduce its own prior answer would have produced more numbers with no more
trustworthiness than the ones already retracted.

### Left open, and now the priority order has changed

1. **A determinism check on the search**: run `estimate_rotation_centre` twice, same process,
   same environment, same real section — confirm it matches itself before asking whether it
   matches across environments.
2. **A landscape diagnostic**: tabulate the coarse grid's scores for one real section, to check
   directly whether multiple near-tied peaks exist (confirming the hypothesis) or whether
   something else is going on.
3. **A tie-break rule**, once the cause is confirmed.
4. **Only then**: re-run all five sections and check which of the previously reported verdicts
   (`S3_test_01/02/07/12`, not just `03`) are actually stable.
5. **This is the point to re-check ADR-0004's "P5 only if time exists" condition against how
   much time is actually left** — items 1-4 are real engineering work, not a quick follow-up,
   and P5 was never meant to consume time at this cost. Flagged to the user directly rather than
   continuing to spend Kaggle sessions on it unilaterally.
6. **P4's segmentation half** remains Sibusiso's, on `main` — unchanged from session 24.

---

## 2026-09-13 — session 25 · S3_test_03's stage-rotation flip does not survive looking at it

### Attempted

The last open item from experiment 007's list, asked for directly: visually check whether
`S3_test_03`'s registered stack looks like a properly aligned rotation series, or whether its
large found offset (-397 px, the biggest of the five sections measured) looks like an artefact.

### Worked

- **`experiments/009-s3test03-visual-check/`** de-rotates two frames (155 deg and 305 deg from
  the reference) two ways each — naively about the image centre, and "registered" about the
  estimated centre — and saves both next to the untouched reference, so the comparison is a
  picture, not a number to trust on faith.
- **Run on Kaggle** (`lethabomh14/reefprint-p5-visual-check`, ~3.5 min, one section at full
  resolution). Actually looked at the images (not just generated them): a single, distinctive
  grain — roughly rectangular, with a dark inclusion and a network of fine cracks — sits in
  almost exactly the same position under **both** the naive and the "registered" de-rotation, at
  **both** angular separations checked. A real 397-pixel axis offset, about 12% of the frame's
  width, should displace that grain by a large, visible amount between the two conditions. It
  does not.
- **The numbers agree with the picture, once looked at together.** `S3_test_03`'s relative score
  improvement (16.10 -> 21.60, ×1.34) is the second-smallest of the five sections measured,
  despite having by far the largest absolute offset. A large offset paired with a modest score
  gain and no visible improvement in the dominant grain is the profile of a search that converged
  on structure elsewhere in the frame (background, a resin boundary, JPEG artefacts) rather than
  the specimen's true rotation axis.
- **Retracted, in the record, not quietly dropped.** `experiments/007-s3v2-registration/
  README.md`'s table, prose and *Left open* list are all updated to say `S3_test_03`'s `FOURTH`
  verdict does not hold, with the reasoning kept rather than deleted — the same treatment N3's
  own withdrawal got in session 17, because a retracted result recorded honestly is worth more
  than one that quietly disappears. `S3_test_01/02/07/12` are unaffected and still hold.
- **P5's honest final state**: the naive-condition confirmation (session 24) and the four
  surviving per-section verdicts (`SECOND`/`SECOND`/`BOTH`/`SECOND`) are usable. `S3_test_03`
  needs the search itself fixed — masked scoring, a tighter radius — before it is re-tried, and
  that is a follow-up, not a blocker on the other four.

### Did not work

Nothing failed outright — this session's finding *is* that a previous session's finding does not
hold, which is a different thing from something failing.

### Learned

**A large found parameter paired with a small improvement in the objective is itself a signal,
and it is checkable before spending time on a visual inspection.** `S3_test_03`'s registration
score improved by only ×1.34 against `S3_test_07`'s ×2.49 for a search that moved the estimate
four times farther — that ratio was available the moment experiment 007 finished, and naming it
up front would have flagged the section as suspect before the visual check confirmed it, not
after. The numeric report and the picture should be read together next time, not the picture only
after the number has already been written into a table as if settled.

### Left open

- **Fix the `S3_test_03` search**: mask background/border content out of the correlation
  objective, try a tighter `search_radius`, and check against a second tracked grain before
  trusting any re-run's result.
- **Widen from 5 to the ~18 sections that carry a real rotation series**, using the four
  confirmed verdicts and the fixed search, not the retracted one.
- **Map the mask through the registration transform and re-run the anisotropy bridge** on a
  clean `SECOND` section — still the measurement the whole project exists to make, still not
  attempted on real data. Unchanged from session 23's *Left open*.
- **P4's segmentation half** remains Sibusiso's, on `main` — unchanged from session 24.

---

## 2026-09-13 — session 24 · N3's naive-condition discrepancy confirmed, not a bug; P4's segmentation half checked and found genuinely blocked

### Attempted

Two follow-ups the user asked for directly: re-run N3's original method on the same 5 sections
experiment 007 measured, and start P4's segmentation half (locality-disjoint phase-IoU with CIs
and both trivial baselines).

### Worked — the N3 re-run

- **`experiments/008-n3-original-method-rerun/`** calls `experiments/002-s3v2-geometry/run.py`'s
  own `read_section` and `harmonic_signature` unchanged, restricted to exactly the 5 section
  stems experiment 007 measured, so the comparison is apples to apples: same sections, same
  archive, same estimator, only the registration step differs.
- **Confirmed on Kaggle** (`lethabomh14/reefprint-p5-n3-rerun`, ~35 s — this method never warps a
  frame, so it is far cheaper than experiment 007's full-stack registration): N3's original,
  unmodified, zero-registration method returns `NEITHER` on **all 5** sections, `snr_2` ranging
  1.78-4.43, every value under the 5.0 threshold — exactly reproducing the historical finding.
  Experiment 007's "naive" condition (coarse de-rotation about the image centre, not zero
  registration) shows `snr_2` 6.89-12.54 on the identical 5 sections, clearing threshold in
  every case.
- **This settles the open item, and settles it as good news for the project's actual thesis, not
  a contradiction of it.** The two experiments do not disagree about the same measurement; they
  measure different starting points, and the result is direct evidence *for* the registration
  thesis (`WORKBOARD.md` §0 C1): a pixel that is a different physical grain in every frame
  carries no coherent modulation to detect at any harmonic — which is what N3's three original
  runs measured, correctly, on genuinely unregistered data — and the moment frames are even
  approximately realigned, real structure appears.
- Suite unaffected by this session's code (008 is a standalone Kaggle experiment script,
  no `src/` changes) — verification limited to linting `experiments/008-n3-original-method-rerun/`
  and a local smoke test against a tiny synthetic archive before spending Kaggle quota on the
  real run, same discipline as experiment 007.

### Did not work — P4's segmentation half, checked and found genuinely blocked

Before writing any code, checked what `khanya/main` actually has to build a locality-disjoint
accuracy report from. Found, and confirmed by reading rather than assuming:

- **No per-section or per-image metrics exist anywhere in `main`'s git history** — every
  committed report (`reports/lumenstone_s2_test_metrics.json`,
  `reports/lumenstone_s2_patches_test_metrics.json`, and siblings) is a single **pooled**
  confusion matrix over all 12 test images. A pooled TP/FP/FN cannot be un-pooled into
  per-locality estimates after the fact — the per-image breakdown was never recorded.
- **No locality manifest exists.** Grepped `main`'s segmentation code directly: `split_ids()`
  reads the archive's train/test directories and randomly selects validation image IDs from
  training. It does not consume, and there is nothing in the repository providing, a mapping
  from image ID to real-world locality (specimen, mine, or section-of-origin) — exactly the gap
  the external technical review's finding #2 already named.
- **The trained checkpoint is absent from this checkout too**, consistent with the technical
  review's own note that it could not find one in the clone it inspected.

**This is not a "not done yet" gap this session could close with more effort — it is missing the
raw material** (per-image or per-locality metrics, a locality manifest, the checkpoint) that
would have to exist before `reefprint.trust.split`/`trust.baseline`/`trust.conformal` could be
pointed at it at all. Building any of those three is Sibusiso's, on `main`, and none of it can be
faked or approximated from this side without contradicting rule 1.

### Learned

**Checking whether a task's inputs exist is itself worth reporting, even when the answer is
no.** The user asked for two things in one message; one had a clean, actionable path (a second
Kaggle kernel, ~35 seconds of compute) and the other did not exist to be started at all. Neither
answer earns silence — the second one earns a precise statement of exactly what is missing and
whose side it is on, so the next person does not re-discover the same gap by trying to build on
it directly.

### Left open

- **`S3_test_03`'s flip** — still the one remaining item before P5's result reaches a slide.
  Visual check of the registered stack.
- **P4's segmentation half** — raised to Sibusiso in the standing issue thread with the precise
  list of what is missing (per-image metrics, a locality manifest, the checkpoint), rather than
  left as a vague "still open" line.
- **Widen from 5 to the ~18 sections that carry a real rotation series**, once `S3_test_03` is
  resolved — unchanged from session 23.

---

## 2026-09-13 — session 23 · P5 run for real: a genuine, mixed, unverified registration result

### Attempted

P5 from `WORKBOARD.md`, approved after checking in: build and validate a per-frame registration
estimator, then run leg (b) for real — does registering S3 v2's frames let a harmonic clear its
detection floor? Two operational constraints surfaced before any real code ran: this machine had
**155 MB free of 8 GB**, and a full section's frame stack needs ~5 GB
(`experiments/003-s3v2-extinction/`'s own docstring) — so the real archive was never going to be
attempted here. Flagged to the user via `AskUserQuestion` rather than pushed through silently;
the user's answer was explicit: **run it on Kaggle**, which the project already had a private
dataset and code-mirror set up for (session 16f).

### Worked

- **`reefprint.acquire.registration.estimate_rotation_centre`** — a coarse-to-fine correlation
  search over the rotation-centre offset. Uses each frame's *known* nominal angle (from the
  acquisition record, never estimated) to reduce what would otherwise be a per-frame-pair blind
  registration problem to a single 2-D search for the whole series: the correct centre is the
  only offset where every frame's de-rotation is exactly the reference frame, so the score is
  maximised there rather than merely locally plausible.
- **Two wrong derivations tried and abandoned before this, on purpose recorded rather than
  hidden.** First: an algebraic derivation relating measured per-frame translations to the centre
  offset via a linear system, `A @ offset = b` — wrong twice (once from an incorrect operator,
  once from a coordinate-convention mismatch), because deriving the sign and transpose convention
  by hand is exactly the kind of thing this project's traps list warns about getting subtly
  wrong. Switched to direct optimisation instead, which does not depend on getting an algebraic
  sign right — it only needs the objective (correlation) to be correct, which is checkable by
  inspection (grid-scan the landscape, confirm the peak sits at the known synthetic answer).
- **A real bug found by validating, not by trusting the first result that ran without crashing.**
  The first version of `estimate_rotation_centre` passed the search offset directly as the
  absolute rotation point instead of adding it to the image centre first — it silently explored
  candidates near pixel (0, 0) instead of near the image centre, and still returned a
  plausible-looking number for every input, including a "correctly centred series" test that
  should have found zero and instead found ~18 pixels. Caught because the test suite includes a
  negative control (`test_a_correctly_centred_series_finds_zero_offset`) and a positive one with
  a *known* nonzero answer (`test_recovers_a_known_off_centre_rotation`), and both failed loudly
  rather than one silently compensating for the other. Pinned by a dedicated regression test,
  `test_estimate_rotation_centre_is_anchored_at_the_image_centre_not_the_origin`.
- **Validated on synthetic data, 7 tests, before touching anything real** — sub-pixel accuracy
  recovering a known off-centre offset, a negative control at zero offset, refusal on
  mismatched/empty input, and `inscribed_region_mask` checked for monotonic shrinkage as the
  centre moves off-axis and for staying inside frame bounds on a deliberately non-square,
  non-power-of-two shape.
- **Run for real, on Kaggle** (`lethabomh14/reefprint-p5-registration`, private, CPU only,
  ~10 minutes): mounted the existing `lumenstone-s3-v2-reefprint` (5.2 GB, session 16f) and a
  freshly-versioned `reefprint-code` dataset (added `registration.py` and `experiments/007`).
  `_DirArchive` duck-types `zipfile.ZipFile`'s interface against Kaggle's auto-extracted mount,
  matching session 16f's finding that an uploaded zip does not stay a zip on Kaggle.
- **The real result, 5 sections measured**: naive centred de-rotation (not zero registration —
  approximate, about the image centre) already clears `DETECTION_SNR` for the 2nd harmonic on
  all 5. Proper registration (estimated true centre) leaves `S3_test_01/07/12` at a clean
  `SECOND` (analyser), moves `S3_test_02` to `BOTH` (mixed — its snr_4 crosses threshold too),
  and **flips `S3_test_03` to `FOURTH`** (stage — its snr_2 collapses from 9.35 to 3.19 while
  snr_4 rises from 2.78 to 5.29). Every found offset is large: 95-397 pixels on 2547x3396
  frames, 3-15% of the frame width. Full table and every number:
  `experiments/007-s3v2-registration/README.md`.
- Suite: **330 -> 337 passed, 4 deselected unchanged** (7 new tests; no placeholder retired —
  P5 never had one, unlike P1-P4).

### Did not work / not yet explained

**The naive-condition result contradicts N3's original three independent `NEITHER` measurements,
and this session has a hypothesis, not a check, for why.** N3's original method
(`experiments/002-s3v2-geometry/run.py`) samples scattered pixel positions directly from raw,
undecoded, un-rotated frames — genuinely zero registration. This session's "naive" condition
already applies an approximate rotation correction (about the image centre) before sampling,
which is not the same starting point. The leading explanation — that any sensible de-rotation,
even about the wrong centre, recovers far more real per-pixel structure than none at all — is
physically plausible and consistent with everything else this session found, but **has not been
checked by running N3's exact original method against these same 5 sections side by side**, and
saying so is the point: this project's own traps list (`CLAUDE.md` §5.1) exists because a result
that overturns a prior finding this sharply needs that check before anyone trusts it, not after.

Transient local test flakiness was also observed and diagnosed, not chased: a full-suite run
mid-session reported 13 failures in `test_geometry.py`/`test_extinction.py` that a clean re-run
did not reproduce, consistent with the same severe memory pressure (155 MB free) that routed the
real archive work to Kaggle in the first place — subprocess-spawning tests are the most exposed
to this, confirmed by re-running the docs-count guard (which shells out to a fresh pytest
process) in isolation and getting a clean pass.

### Learned

**A result that contradicts a project's own prior finding is a reason to check the comparison
more closely, not a reason to report the newer number as the correction.** The naive condition
clearing threshold where N3 found nothing looks like progress; it is at least as likely to be
a methodology difference as a genuine improvement, and the README for this experiment says so
in its own words rather than letting the more flattering reading stand by default.

**Ask before spending unbounded time or touching a resource-constrained machine, even when
"carry on" has already been said once.** The session paused with `AskUserQuestion` when two new,
un-disclosed constraints surfaced mid-task (memory pressure discovered only once close to
running something that would hit it; an unvalidated estimator discovered only once tested) —
a general "keep going" from an earlier turn does not cover risks that were not yet visible when
that instruction was given.

### Left open

- **`S3_test_03`'s flip** — the largest offset found (-397 px) and the one verdict that inverted.
  Visual check of the registered stack before this section's result is trusted at all.
- **N3's original method, re-run against these same 5 sections**, to check the naive-condition
  hypothesis above rather than leave it asserted.
- **Widen from 5 to the ~18 sections that carry a real rotation series**, once the two items
  above are resolved.
- **Map the mask through the same transform and re-run the per-mineral anisotropy bridge** on a
  clean `SECOND` section — the actual measurement (pentlandite dark, pyrrhotite lit) the whole
  project exists to make, still not attempted on real data.
- **P4's segmentation half** remains Sibusiso's, on `main` — unchanged from session 22.

---

## 2026-09-12 — session 22 · P4 shipped: the Bushveld falsification, cross-checked bit-for-bit

### Attempted

Close the acceptance test named for P4: `tests/test_heads_falsification.py::
test_the_falsification_test_has_been_run_on_real_bushveld_data`. Its own docstring said "delete
this test and record the result in docs/BUILDLOG.md once it has run."

### Worked

- **Found, before writing anything, that the real run already existed — on `main`.** Git log
  search turned up `b58596c` (Sibusiso, 3 Sept): `src/chromite_pge_falsification.py` and a
  checked-in `reports/chromite_pge_falsification.json`, importing `reefprint.heads.falsification`
  unchanged via the bridge pattern. Read it before writing anything new — doctrine rule 1,
  extract don't infer, applied to a claim about the project's own history rather than a paper.
- **Built `experiments/006-bushveld-chromite-falsification/run.py`, reefprint-native**: same
  computation (Cr#/Mg# per Barnes & Roeder 2001, cluster-robust `evaluate_texture_uplift`), no
  import from `main`, using this branch's own copy of the Bachmann (2019) CSV. Result:
  **n_obs=1112, n_localities=305, baseline_r2=0.11193237858997018,
  full_r2=0.13980320644998467, delta_r2=0.02787082786001449,
  p_value=0.00018062196419940484** — **identical to Sibusiso's independent implementation to
  every one of seventeen significant figures.** Two separately written programs, same data, same
  number: this is the strongest verification a two-history split can produce, and it closes the
  gate honestly rather than by trusting a checked-in JSON on the other branch.
- **The literal H0 stays reported as untestable**, not quietly replaced by the pivot. Rewrote
  `tests/test_heads_falsification.py`'s module docstring to say both things at once (Rule 9): the
  texture-vs-Cr2O3-and-pyroxene H0 remains untestable (T1/T2 unresolved), and a narrower, real,
  accepted pivot has been run and is not the same claim.
- **`tests/test_bushveld_chromite_falsification.py`** (4 tests, CI-safe): a hand-worked check on
  the Cr#/Mg# arithmetic at round numbers, and three tests against a synthetic CSV built to the
  real column layout — same pattern as `test_s3v2_reader.py`, since `data/` is gitignored and
  CI cannot see the real 1,205-row file.
- **Caveats written into the experiment README before a judge finds them**: modest effect size;
  Cr# is arithmetically related to the Cr2O3 baseline; fitted in-sample association, not an
  out-of-locality predictive test; boreholes within a project may not be fully independent
  localities. The result is to be quoted as *"a separate geochemical association analysis,"*
  never as the texture H0 rejected.
- Suite: **326 → 330 passed**, deselected **5 → 4** (the placeholder deleted per its own
  instruction, not skipped). `CONTEXT.md` §4's guard now checks a third invariant too —
  `test_the_two_counts_partition_the_whole_suite` — caught the drift the same way as every
  prior session.

### Did not work

Nothing failed outright. The near-miss: the first version of
`test_load_rows_refuses_a_missing_file` matched on `"Mendeley"` (capitalised) against an error
message that says `"data.mendeley.com"` (lowercase, it's a URL) — caught immediately by running
the test rather than assuming the regex was right.

### Learned

**Before writing a falsification harness from scratch, grep the other branch's history for the
exact numbers CLAUDE.md already cites.** `docs/08-handover.md` quotes "ΔR² = 0.0279, p = 0.0002"
as an existing result without saying where the code lives; a two-minute `git log --all --oneline
| grep` found it committed on `main` three sessions ago. Reproducing it independently was still
the right call — the cross-check is worth more than trusting the number — but reproducing it
*blind*, without first reading what already existed, would have risked a second implementation
that quietly disagreed with the first for a reason neither script would have surfaced.

### Left open

- **The segmentation half of P4** — locality-disjoint phase-IoU with CIs and both trivial
  baselines, per C2's real S1/S2 numbers — needs KHANYA's held-out predictions and locality
  manifest. Sibusiso's, on `main`.
- **P5 (leg (b) registration)** is next in the queue per ADR-0004, gated on the domain lead
  confirming P1–P4 are sufficiently green to spend unbounded research time on it — not started
  without that confirmation, since P5 has no acceptance test and no time limit the way P1–P4 did.

---

## 2026-09-12 — session 21 · P3 shipped: latency measured on two REEFPRINT-side stages

### Attempted

Build P3: the brief says "real-time" and nothing in either half of the repository had ever
measured a number against that claim. Write the instrument first (doctrine rule 3), then run it.

### Worked

- **`reefprint.trust.latency.LatencyMeasurement` and `measure_stage`** — times `n` calls to a
  callable after discarded warm-up calls, reports mean, median, **p95** (nearest-rank, stated as
  coarse at small n) and standard deviation (`None` at n < 1, not a false zero), always with
  named hardware. Refuses construction with no hardware string or zero samples — a latency
  number that cannot be attributed to a machine cannot be compared against a re-run of itself.
- **Measured for real, not just tested**: `experiments/005-latency-benchmark/run.py` times the
  Stokes inversion at two representative phantom sizes and the OPC UA advisory publish+connect+
  read round trip on the actual local server built for P1. Result, this machine (Windows 11,
  AMD64): Stokes inversion ≈ 6.7 ms/call at 64×96, ≈ 105 ms/call at 192×256 (36 angles — the
  week-1 gate's own default); OPC UA round trip ≈ 8.3 ms/call including a fresh TCP connection
  every time. Report committed at `experiments/005-latency-benchmark/output/latency-report.md`.
- **The scope limitation is stated in four places, not implied**: the module docstring, the test
  file's module docstring, the experiment's README under its own "What this does NOT show"
  heading, and this entry. Segmentation inference, decode and postprocess are KHANYA's, on
  `main`, behind a trained checkpoint absent from this checkout — the technical review of
  2026-09-12 confirmed it was absent from the clone it inspected too. **No end-to-end
  "real-time" claim is made anywhere in this work**; what is claimed is narrower and true: two
  specific stages of the shipped path run fast enough on ordinary hardware to be an unlikely
  bottleneck, whatever number segmentation turns out to need.
- Suite: **322 → 326 passed**, deselected unchanged at 5 (P3 added tests, it did not retire a
  placeholder — there was no placeholder test for latency to begin with).

### Did not work

Nothing failed outright.

### Learned

**A latency report that states what it does not cover is worth more than one that is silent
about it.** The instrument itself (`LatencyMeasurement`) has no way to know it is being asked
to stand in for a claim about a pipeline it never touched — that check has to live in the
report and the docstring around it, every time, because the honest half of a partial benchmark
is the part a reader has to be told, not the part they can infer from what is missing.

### Left open

- **A matching benchmark on `main`** for segmentation inference, using the same
  `reefprint.trust.latency` instrument via the bridge pattern, reported in the same table —
  needed before any "real-time" sentence reaches the talk. Raised to Sibusiso.
- **P4 is next** — the accuracy report, done honestly with locality grouping, CIs and both
  trivial baselines. Acceptance test:
  `tests/test_heads_falsification.py::test_the_falsification_test_has_been_run_on_real_bushveld_data`.

---

## 2026-09-12 — session 20 · P2 shipped: the fine-chromite entrainment risk head

### Attempted

Build P2 from `WORKBOARD.md`: one processability head, built properly rather than three
thinly. Acceptance test: `tests/test_heads.py::test_fine_chromite_entrainment_risk_index`.

### Worked

- **`reefprint.heads.entrainment.fine_chromite_entrainment_risk`** — a structural proxy,
  `chromite_mass_fraction * fine_fraction * entrainment_factor * water_recovery`, grounded in
  the classical entrainment framework (Trahar 1976, Johnson 1972, formalised by Savassi et al.
  1998 as a size-dependent classification function `EF(d)` times water recovery `Rw`). Returns
  a `HeadEstimate` — the shared Rule-4 interval contract from session-earlier work.
- **The interval is a proven worst-case bound, not a statistical propagation.** All four inputs
  are `[0, 1]` fractions from a mix of measured, cited and assumed sources, not independent
  random draws — a normal-approximation CI would claim a precision the proxy does not have.
  Instead: for nonnegative `a_low <= a <= a_high` and `b_low <= b <= b_high`,
  `a_low*b_low <= a*b <= a_high*b_high` by monotonicity, chained across all four factors. Proven
  in the module docstring, checked by
  `test_the_worst_case_bound_brackets_the_point_estimate_for_any_valid_inputs` against inputs
  chosen to stress the chain (one factor near 1, one near 0, asymmetric ranges).
- **`BoundedFraction`** — a fraction plus its own `[low, high]`, mirroring
  `ConservativeDefault`'s validation shape deliberately, including refusing a `DESIGN_TARGET`
  input at construction — the earliest point Rule 1's contamination can be caught, before it
  could ever reach the multiplication.
- **`entrainment_risk_conservative_default`** wires Rule 5's own worked example: `trust.abstain`'s
  module docstring already names this exact head as `ASSUME_HIGH` ("over-dose the depressant,
  cut the feed, lose a little recovery"). `test_entrainment_risk_abstains_conservatively_high_not_low`
  checks both that a correctly-`ASSUME_HIGH` default emits its stated value, and that a
  wrongly-reassuring low-side default is refused at construction — the same inversion check
  `ConservativeDefault` already enforced, exercised through this head specifically.
- **Rule 6, kept deliberately intact.** The module computes the formula and refuses to choose
  `entrainment_factor` or `water_recovery` itself — those are a domain judgement (which
  literature classification curve, at what size cutoff; which plant's typical water recovery),
  and CLAUDE.md's blind spot 8 says a load-bearing mineralogical claim must not rest on one
  person's judgement, let alone this module's. Every value the test exercises is `ASSUMED` and
  labelled **illustrative** in its own source string, so nothing here can be mistaken for a real
  citation if quoted out of context.
- Suite: **317 → 322 passed, 6 → 5 deselected** (six new tests; one placeholder retired).
  `CONTEXT.md` §4's guard caught the drift twice in a row — once for the pass/deselect line,
  a second time when the fix itself used the wrong number (320 instead of the collected total of
  322, since `--collect-only` counts a currently-failing test too). Read what the guard actually
  measures before re-guessing the number by hand.

### Did not work

Nothing failed outright. The one thing worth recording: the first fix to `CONTEXT.md`'s count
line used **320** (passed-only, read off a `pytest -q` run), not **322** (the `--collect-only`
total the guard actually checks). The guard test caught the mismatch immediately — exactly
what it is for — but it is a reminder that "passed" and "collected" are different numbers
whenever something in the run is failing for an unrelated reason.

### Learned

**A bound proven correct in the docstring is worth writing a test that tries to break it, not
just one that happens to pass.** The first version of
`test_the_worst_case_bound_brackets_the_point_estimate_for_any_valid_inputs` used four similar,
comfortable inputs; the committed version deliberately mixes a near-1, a near-0 and two
asymmetric ranges, because a monotonicity proof that only gets exercised at gentle inputs has
not really been checked.

### Left open

- **Real `entrainment_factor` and `water_recovery` citations** — domain lead's call, not code.
  Nothing computed by this head may reach the accuracy report or a slide until those are real.
- **Wiring segmentation output (chromite mass fraction) into this head** is not done — folded
  into whichever task connects `reefprint.heads` to KHANYA's segmentation output across the
  bridge.
- **NFG load and oxidation index remain deferred**, per the WORKBOARD: NFG unproven without
  SWIR (open question 1), oxidation index not computable from the available XRF majors.
- **P3 is next** — the latency benchmark. No test exists yet; write one.

---

## 2026-09-12 — session 19 · P1 shipped: a real local OPC UA advisory server

### Attempted

Build the P1 item from `WORKBOARD.md`: a real local OPC UA server exposing advisory values, a
separate simulated control client, and a demonstration of refusing a stale advisory. Acceptance
test: `tests/test_integrate.py::test_opc_ua_server_exposes_advisory_values`.

### Worked

- **`reefprint.integrate.opcua_server.AdvisoryServer`** — a genuine `asyncua.Server`, not a
  mock. Binds `127.0.0.1` on a port chosen with a plain `socket` bind-then-release before the
  server starts, so the endpoint is known without introspecting `asyncua` internals. Publishes
  each advisory head under a `sim_advisories` folder as six OPC UA variables (value, unit,
  emitted_at, valid_for_seconds, advisory_influenced, source) and hands back opaque node IDs —
  a real integration is expected to have these from an engineering configuration, not from
  browsing the address space at runtime.
- **`reefprint.integrate.opcua_client.SimulatedControlClient`** — its own process boundary,
  connects over the wire, and either applies a fresh head to a `SimulatedPlantParameter` or
  returns `RefusedStaleAdvisory`. The refusal type has **no field for a prior value**, mirroring
  `trust.abstain.Abstention`'s discipline: the transport layer cannot become a place to re-invent
  "hold the last setpoint" just because the domain layer forbids it.
- **`AdvisoryRecord` extended** with `unit`, `emitted_at` (default `time.time()`),
  `valid_for_seconds` (default `inf`, so the existing test needed no change), finite-value
  validation on every entry, and `is_expired()`. `values` is now stored as a `MappingProxyType`
  internally — a frozen dataclass with a plain `dict` field was mutable through that field, which
  is the kind of bug that survives until someone mutates a record after passing it downstream.
- Verified end to end with a raw `asyncio.run` smoke script before writing the test, publish +
  read round trip confirmed on the actual API (asyncua 2.0.1) rather than assumed from memory —
  `add_folder`, `add_variable`, `write_value` and `NodeId.to_string()` are all coroutine or
  method signatures checked with `inspect.signature` first, because the library's version in
  this venv (2.0.1) was not something to assume matches whatever version training data implies.
- Test suite: **317 passed, 6 deselected** (was 315/7 — P1's test moved from placeholder-fail to
  passing, plus two new tests for the finite-value/expiry guards). `CONTEXT.md` §4's guard
  caught the stale count immediately, same as session 18.
- CI: `.github/workflows/ci.yml` now runs `uv sync --all-groups --extra integrate` in both jobs.
  Deliberately not `--all-extras` — the `ml` extra pulls PyTorch and this suite must stay
  runnable on a clean checkout without it.

### Did not work

Nothing failed outright; the main risk managed was API drift. `asyncua`'s public interface was
checked against the installed 2.0.1 wheel with `inspect.signature` before any server code was
written, specifically because an OPC UA server that silently used a wrong-generation API and
still imported cleanly would be exactly the kind of green-suite-wrong-code failure CLAUDE.md's
traps list warns about.

### Learned

**Verify a third-party async library's API against the installed version before writing against
it, not after.** A five-minute `inspect.signature` pass plus one throwaway smoke script (raw
`asyncio.run`, no test framework) caught the exact call shapes (`add_variable`'s positional
order, `NodeId.to_string()` vs `str()`, `Client` as an async context manager) before any of it
was load-bearing in the real module.

### Left open

- `verdict_state()`'s favourable-fallthrough bug is **KHANYA's**, on `main` — raised to
  Sibusiso in issue #4, not fixed here.
- Wiring `AdvisoryServer` + `SimulatedControlClient` into `reefprint.viz.demo`, and a latency
  measurement on the OPC UA path itself, are folded into **P3**.
- **P2 is next** — the fine-chromite entrainment risk head,
  `tests/test_heads.py::test_fine_chromite_entrainment_risk_index`.

---

## 2026-09-12 — session 18 · one shared board, and the illumination path does not match the code

*Numbering note: this file carries two merged counters — the 17 above is the newest `reefprint`
entry, and the 2x/3x series arrived with `main`'s rebase. Newest is still top, by date.*

### Attempted

Absorb `docs/08-handover.md` cold, verify the state it claims, and give Lethabo and Sibusiso a
single file they can both open to know what is being worked on — the repo carries eleven
overlapping status documents across two branches and they disagree.

### Worked

- **Baseline re-verified, not taken on trust.** `uv run pytest -m "not placeholder" -q` →
  **314 passed, 7 deselected** in 115.92 s. `uv run pytest -m placeholder -q` → **7 failed**,
  and the seven names match the documented backlog exactly.
- **`WORKBOARD.md` created** at repo root: corrections in force, lane ownership, the scoreboard
  against the brief's literal deliverables, the P1–P5 queue with acceptance tests, the open
  decisions, and the session ritual. It is the index, not a twelfth status document — it says
  which of the existing eleven to trust.
- **Two stale rows in `CONTEXT.md` corrected.** §3's week-1 table and §8's N3 row still reported
  the `NEITHER` verdict as a measurement, while a paragraph further down the same file said it was
  withdrawn. A file that contradicts itself will be quoted from the wrong half.

### Did not work — and this is the finding

**The constitution and the code disagree about whether a polariser is in the illumination path,
and the disagreement inverts the headline discriminator.** Found by reading finding #5 of
`khanya/main:reports/TECHNICAL-REVIEW-2026-09-12.md` against the source. `08-handover.md` does
not mention it.

- `src/reefprint/polarim/stokes.py:10` — *"under crossed polars an isotropic phase shows no
  modulation as the analyser turns"*. `CLAUDE.md`'s geometry table — *"analyser, with polariser
  and specimen fixed"*.
- With a fixed polariser this is **false**. Normal-incidence reflection off an isotropic medium
  preserves the linear azimuth, so (S0,S1,S2) = (I₀, I₀, 0), DOLP = 1, I(θ) = I₀cos²θ — *full*
  modulation. The review's counterexample is correct.
- **But the code does not implement that arrangement.** `acquire/phantom.py:203` sets
  `magnitude = anisotropy × reflectance_pct`, so DOLP = `anisotropy`, and `:98` sets cubic → 0.
  That is the forward model for **unpolarised incident light**, where polarisation is *generated*
  on reflection by differential reflectance between the eigen-axes: isotropic → DOLP 0,
  anisotropic → DOLP = (|r₁|²−|r₂|²)/(|r₁|²+|r₂|²) = bireflectance contrast. Both correct
  physics; different instruments.
- Corroboration that unpolarised is the intended model: `CLAUDE.md`'s own scaling argument
  (analyser modulation goes as `a`, extinction as `a²`) only holds under it.
- **So the forward model is sound and the prose names the wrong instrument.** The BOM's *"salvaged
  LCD polarisers"* (plural) is a third inconsistent statement of the same thing.
- Flagged in `CLAUDE.md` §Physics as an open block rather than rewritten — it is decision **D2**
  for the domain lead, not a typo, and rewriting the constitution's physics unilaterally is
  exactly what blind spot 11 warns about.

### Learned

**A correction that lands in one paragraph does not reach the table three screens up.** Session
17 withdrew N3 and wrote the withdrawal into `CONTEXT.md` §3's prose, and both the summary table
above it and the §8 row below it went on asserting the withdrawn verdict for a day. When a finding
is withdrawn, grep the whole file for the number, not just the section you were editing.

### Then both decisions were taken, same session

**D1 → [ADR-0004](04-decisions/0004-polarimetry-is-a-research-thread-not-the-submission-spine.md).**
Polarimetry comes off the critical path. Spine is segmentation → processability → plant interface.
Nothing is deleted and the claim is not withdrawn — leg (b) is *untested*, not *negative*.

**D2 → [ADR-0005](04-decisions/0005-unpolarised-illumination-with-a-rotating-analyser.md).**
Illumination is unpolarised; the prose named the wrong instrument. Corrected in `CLAUDE.md`,
`CONTEXT.md`, `README.md`, `src/reefprint/__init__.py` and `polarim/stokes.py`; BOM reconciled to
one analyser plus a depolarising diffuser; pinned by
`test_an_isotropic_grain_under_a_fixed_polariser_modulates_fully`.

**Two things the fix sharpened that the analysis had not:**

- **"Dark" was wrong twice over.** An unmodulated isotropic grain sits at `S0/2` throughout, and
  pentlandite at R ≈ 50% is among the *brightest* phases on the section. The word is **flat**.
- **The submitted abstract is clean.** Both its uses of "crossed polars" describe the classical
  stage-rotation discipline, not our instrument. Checked before assuming it needed a correction.

**And the repo caught its own drift.** Adding the counterexample test took the suite 314 → 315, and
`test_context_quotes_the_real_passing_and_deselected_counts` failed until `CONTEXT.md` §4 was
updated. Final state: **315 passed, 7 deselected**, ruff clean.

### Left open
- D3 (T1 texture dataset) · D4 (T2 pyroxene proxy) · D5 (LumenStone rights) · D6 (commit email).
- `ENDGAME.md` §3's framing table still cites the invalid extinction null as an asset. That file
  is on `main` — Sibusiso's to correct, per ADR-0003.

---

## 2026-09-12 — session 17 · S3 v2's frames are NOT REGISTERED. N3 was measuring nothing.

### Attempted

Pulled the Kaggle v4 result (real codebook, all 47 sections) and asked the week-1 leg (b)
question directly: within each section, do anisotropic phases show higher extinction depth than
isotropic ones?

### The result — a clean null, and then the reason for it

**No separation whatsoever.** Anisotropic higher than isotropic in **15 of 29** sections;
coin-flip expectation is 14.5. Median difference **+0.38 DN²** against a median within-section
spread across minerals of **13.3 DN²**. Background (resin, no crystal anisotropy) frequently
reads *higher* than arsenopyrite (strongly anisotropic) — e.g. `S3_test_01`, background 19.62 vs
arsenopyrite 17.66, with cubic pyrite highest in that section at 22.62.

**The dominant signal is the section, not the mineral.** Between-section spread of section
medians is **92.8 DN²** (16.8 to 109.6) — **7× the within-section spread across minerals**. That
is the signature of illumination/exposure, which is exactly what `bridge/extinction.py`'s own
docstring warned raw un-normalised depth would conflate ("finding N2 in a new costume").

**The estimator's own self-test fails.** `crossing_ratio` is pinned at 1.0 for ideal crossed
polars. Measured: **median 11.01, range 4.67–26.00** across 146 mineral-section pairs. An order
of magnitude off. These frames do not behave like a crossed-polars stage rotation.

### Then the actual cause, found by checking the obvious alternative before concluding

Before writing this up as "the data has no polarimetric signal", checked the explanation that
would make it **our** bug instead: are the frames registered at all?

**They are not. The field rotates with the specimen.** Frame-to-frame correlation against r000
decays along the *rotated-image control* curve, not a registered-field curve:

| section | r005 | 5° control | r040/045 | 45° control |
|---|---|---|---|---|
| S3_test_01 | +0.7114 | +0.6572 | +0.3129 | +0.2929 |
| S3_test_02 | +0.6671 | +0.6157 | +0.2675 | +0.1801 |
| S3_test_03 | +0.3734 | +0.3682 | +0.1834 | +0.2918 |

A registered polarimetric series holds high correlation across angles — only intensity modulates,
the grain structure is fixed. These track physical rotation of the image.

Naive centred de-rotation does **not** reliably fix it: dramatic recovery on `S3_test_03` r005
(+0.3137 → +0.8142) but it makes `S3_test_01` r005 and r040 *worse*. So the transform is a
rotation about a centre that is **not** the image centre and appears to vary by section — not a
clean centred rotation that a fixed `-angle` undoes.

### What this invalidates — state it plainly

**Every per-pixel result computed on this archive measured a pixel that is a different physical
point in each frame.** That includes:

- **N3's harmonic verdict (`NEITHER`), all three independent runs**, plus the brightness-quantile
  re-run. Two people measured it, identically, and the number was reproducible — because the
  *bug* was reproducible. N3 did not find "neither geometry"; N3 had no valid per-pixel time
  series to find a geometry in.
- **The entire extinction-depth result above.** The null is real but it is a null about
  unregistered data, which carries no information about polarimetry.

The reproducibility across two machines and three runs is worth naming as the lesson: it bought
confidence in an answer to a question that was never actually being asked. Agreement between runs
tests the pipeline's determinism, not its validity.

**Leg (b) is not failed. Leg (b) has never been run.** Whether a 4φ extinction signal survives
proper registration is now an open, testable question — and it is the first thing to test.

### Left open

- **Registration is the prerequisite nothing else can proceed without.** Needs a per-frame
  transform estimated from the data (log-polar phase correlation, or ECC/feature-based), not a
  fixed rotation by the filename angle. Rotation centre must be estimated per section.
- After registration, valid pixels are only the **inscribed region present at every angle** —
  the corners rotate out of frame. The honest denominator shrinks accordingly.
- **The mask can only be valid for one frame** (presumably r000). Any per-mineral statistic must
  map the mask through the same estimated transform, or be computed in r000's frame after
  de-rotating every other frame onto it.
- `CONTEXT.md` N3's wording, and every doc asserting "leaning stage", now overstates what was
  measured. Corrected there this session.

## 2026-09-05 — session 34 · reliability, provenance and test-selection audit

### Attempted

Audit the remaining implementation rather than force data-dependent placeholders
green. Work from a clean reefprint worktree: the older local checkout contains
pre-existing staged cross-branch changes and was preserved untouched.

### Worked

- Reject nonfinite inversion inputs and section leakage across locality names;
  malformed quality metadata now refuses instead of crashing.
- Association matrices normalize symmetric directed contacts globally; a hand-counted
  three-phase case pins the previously contradictory normalization contract.
- Approximate reflectance constants are ASSUMED, not falsely labelled verified QDF.
- The synthetic offline demo invokes the actual geometry guard and displays the
  refusal reason and conservative default provenance. Shared GIF canvases prevent
  clipping of its taller refusal panel.
- CI now triggers on reefprint pushes. The real advisory-record guard was hidden
  by a module-wide placeholder marker; it now runs in blocking CI.
- CPU-only Python verification on this host: **314 passed, 7 deselected**. Coverage
  before the marker correction was 92% statement/branch combined (313 tests).
  Ruff check and format checks pass. Regenerated GIF: two 1400 x 550 screens at
  four seconds each; inspected the refusal frame visually, no clipped reason.

### Did not work

Initial lint found existing import/annotation/format errors; corrected them without
changing scope. The placeholder run initially reported seven failures and one pass,
revealing the incorrectly excluded implemented test rather than eight missing builds.

### Left open

Seven explicitly red gates remain: public-series Stokes clearance, three domain
heads, real Bushveld falsification, texture/chemistry control, optional OPC UA.
No absent dataset, validated head, hardware or transport was fabricated. Approximate
reference values still need wavelength-specific sourcing before quantitative use.
The main dashboard's complete real-image rehearsal needs its validated checkpoint
and original micrographs; a synthetic backup is not equivalent evidence.

## 2026-09-04 — session 33 · documentation count correction

### Attempted

Apply the paired-host count from the `HeadEstimate` verification and close the two self-referential
documentation checks.

### Worked

`CONTEXT.md` §4 now quotes **301 passed, 8 deselected** and **8 placeholder failures**. The paired
report's 299 passed included the two count tests failing against the stale 302/7 quote; once the
quote matches, those two tests are expected to pass.

### Did not work

No code was changed; this was the same documentation-count feedback loop encountered earlier.

### Left open

The paired host should rerun `pytest -m "not placeholder"` and confirm both doc-count guards pass.

## 2026-09-04 — session 32 · interval-bearing head output contract

### Attempted

Close the data-independent `heads` placeholder requiring every emitted prediction to carry a
confidence interval.

### Worked

- Added `HeadEstimate`, requiring reportable estimate/lower/upper quantities, common units,
  confidence in (0, 1), and an estimate inside its interval.
- Replaced that one placeholder with real assertions; the three domain heads remain explicitly
  marked red because their formulas/data are not defensible yet.
- The expected non-placeholder suite is now **302 passed, 7 deselected**.

### Did not work

No domain head was fabricated from guessed coefficients; the interval contract is infrastructure,
not evidence that entrainment, NFG, or oxidation has been measured.

### Left open

The paired host should verify the updated count. A quick palette review of `reefprint.viz` follows;
any styling change will remain cosmetic and isolated from the dashboard branch.

## 2026-09-04 — session 31 · advisory provenance record boundary

### Attempted

Close the one remaining data-independent integration placeholder: the endogeneity flag that must
be present on every advisory record from the first observation.

### Worked

- Added dependency-free `AdvisoryRecord` with an explicit boolean
  `advisory_influenced` field and stable dictionary serialisation.
- Replaced the flag placeholder with real assertions; expected suite is now **301 passed,
  8 deselected**.

### Did not work

The OPC-UA transport placeholder remains red. `asyncua` is optional LGPL-3.0 integration and the
project has no sealed appliance or controller to ship under ADR-0002/gauntlet S3.

### Left open

The paired host should verify the updated count; remaining reds are the public-data/domain gates or
the explicitly excluded transport.

## 2026-09-04 — session 30 · texture mechanics implemented

### Attempted

Close the data-independent `texture` placeholders while preserving the Week-2 domain-data gate.

### Worked

- Added connected-component grain extraction with explicit integer-map and connectivity guards.
- Added symmetric, row-normalised 4-neighbour mineral-association statistics.
- Replaced the two mechanics placeholders with real assertions; the expected split is **300 passed,
  9 deselected**.

### Did not work

The falsification test remains a placeholder because no public texture-plus-chemistry dataset with
locality labels exists; no synthetic result was promoted to a real-data claim.

### Left open

The paired host should verify the updated count. The remaining red list is now domain/data or
explicitly out of scope under the project ADRs.

## 2026-09-04 — session 29 · calibration assertion API correction

### Attempted

Apply the paired-host failure report for the dark/flat calibration test.

### Worked

Changed the expected value from a nested Python list passed to `pytest.approx` to a 2-D NumPy
array, which `pytest.approx` supports. `correct_counts` itself was unchanged; the bug was solely
in the test assertion.

### Did not work

The paired run was 297 passed, 11 deselected with this single assertion error before the fix.

### Left open

The paired host should rerun to confirm the calibration correction returns the suite to zero real
failures.

## 2026-09-04 — session 28 · acquisition provenance guards

### Attempted

Review the remaining acquisition placeholders against ADR-0002 and implement only the
data-independent provenance contracts.

### Worked

- Added `require_frozen_illumination` to refuse training captures without an explicitly frozen
  schedule, closing the blind-spot-6 guard.
- Added `require_calibration_provenance` for instrument, standard, wavelength, and exposure fields,
  so an R% claim cannot pass with incomplete acquisition state.
- Replaced those two placeholders with real tests; the expected split is **298 passed,
  11 deselected**.

### Did not work

The public real-ore Week-1 placeholder remains red: its docstring requires a licensed analyser-
rotation dataset that is not present. No hardware driver or unlabeled archive was forced in.

### Left open

The paired host should verify the updated count. The real-data gate remains a domain/data
availability decision, not a code gap.

## 2026-09-04 — session 27 · heads scope decision

### Attempted

Review each remaining `tests/test_heads.py` docstring for an implementable contract, without
manufacturing mineralogical numbers where the project has no data or validated mapping.

### Worked

- Confirmed the interval requirement is already structural in `reefprint.trust`: predictions carry
  reportable quantities, and conformal coverage supplies the interval/audit layer.
- Confirmed the three domain heads remain legitimately open: no specified Cr₂O₃-to-entrainment
  model, SWIR-free talc/serpentine detector, or measured oxidation reference exists in this
  repository. Their placeholders stay red with the reason visible in their docstrings.

### Did not work

Building any of those three outputs from guessed coefficients would violate Rule 1 and turn the
Week 2 `texture_features` domain-lead block into an invented result.

### Left open

The remaining in-scope code backlog is now limited to data-independent utilities; acquisition and
integration placeholders still require their own ADR-0002/kill-list scope checks.

## 2026-09-04 — session 26 · segmentation scope guards implemented

### Attempted

Close the three `reefprint.segment` placeholders according to their docstrings without pulling
optional ML weights into the base suite.

### Worked

- Bound segmentation's locality-split and trivial-baseline requirements to the existing tested
  `reefprint.trust` guards.
- Added the explicit `timm`/Apache-2.0 backbone declaration and refusal for the blocked DINOv3
  alternative.
- Replaced all three placeholders with assertions; the expected non-placeholder suite is now
  **296 passed, 13 deselected**.

### Did not work

This host has no Python/uv runtime, so the segment tests were not run locally. The paired host must
verify the updated count and the existing trust guard behaviour.

### Left open

No trainable segmentation model or weights were invented; that remains optional and outside the
dependency-light gate.

## 2026-09-04 — session 23 · Week 6 backup-video generator

### Attempted

Produce the backup recording from the verified offline demo without introducing ffmpeg, a network
call, or a second source of truth for the talk.

### Worked

- Added `experiments/004-backup-video/run.py`, which renders the deterministic `offline_demo()`
  gate and refusal screens into a two-screen animated GIF using the already-declared Pillow
  dependency.
- Added an experiment README with the exact one-laptop command and the reason GIF is intentional.

### Did not work

This host has no Python/uv runtime, so the GIF could not be materialised here. The output directory
is ignored as regenerable experiment output; the paired host must run the generator.

### Left open

Run the generator on the paired host and retain the resulting GIF with the submission/demo media.

## 2026-09-04 — session 25 · calibration boundary implemented

### Attempted

Close the three `reefprint.calibrate` placeholders using the test docstrings as the contract:
counts-to-R%, cited QDF anchors, and dark/flat correction before conversion.

### Worked

- Added `ReflectanceStandard` with finite-count and positive-signal guards and per-wavelength R%
  conversion.
- Added `correct_counts` with broadcast-shape, finite-value, and positive-flat-field checks.
- Added cited QDF anchors for chromite (13%) and gangue/resin (4.75%), plus real assertions for all
  three former placeholders.

### Did not work

This host has no Python/uv runtime, so the calibration tests were not run locally. The paired host
should verify the updated suite count: **293 passed, 16 deselected**.

### Left open

No broader mineral database was invented; only the two values named by the test/docstring are
recorded. Remaining red placeholders are still subject to their own scope review.

## 2026-09-04 — session 24 · W8 status narrative refresh

### Attempted

Re-read the artefact front door after Weeks 5–6 closed, checking that a stranger sees the current
gate status rather than an old Week-1/Week-5 snapshot.

### Worked

- Updated `CONTEXT.md` to record the paired-host verification of the offline demo and the materialised
  backup GIF, and to make the next action the remaining-placeholder scope audit.
- Updated `docs/00-STATUS.md`'s current gate table and added ADR-0003 to its current-decision index.
- Left historical findings, archive documents, and deliberate red placeholders unchanged.

### Did not work

No code or path restructuring was needed; this was documentation drift, not an implementation gap.

### Left open

Choose the next red placeholder only after reading its own docstring and checking it against ADR-0002
and the Week 2 domain-lead block.

## 2026-09-04 — session 22 · Week 5 colorbar axis count correction

### Attempted

Correct the offline-demo test's figure-size assertion after paired-host verification.

### Worked

`anisotropy_figure` has three content panels and two image colorbars, so its honest figure axes
count is **5**, not 3. The test now asserts that documented count and explains the two additional
axes inline; the figure implementation remains unchanged.

### Did not work

The paired run reported 289 passed, 19 deselected, and this one failure before the correction.

### Left open

The paired host should rerun the non-placeholder suite to confirm 290 passed, 19 deselected.

## 2026-09-04 — session 21 · Week 5 offline viz and W8 artefact audit

### Attempted

Close the two `reefprint`-side Week 5 visualization placeholders and perform the surgical W8
front-door audit without moving paths or merging the two ADR-0003 histories.

### Worked

- Added `reefprint.viz.demo.offline_demo`, a deterministic synthetic rotation-series scene that
  constructs the Stokes/analyser gate entirely from local code.
- Added `reefprint.viz.decision.decision_figure`, which renders `SYSTEM REFUSED TO ANSWER`, the
  conservative default emitted, and the stated reason as figure text.
- Replaced both `tests/test_viz.py` placeholders with assertions, including a socket guard proving
  the demo does not open a network connection.
- Audited the repository: no stray tracked artefacts or stale non-historical cross-references were
  found. README now states the `main`/`reefprint` roles, names KHANYA, and records the deliberate
  non-merge under ADR-0003.

### Did not work

This host has no Python/uv runtime, so the suite was not run locally. The paired host must verify
the updated expectation of **290 passed, 19 deselected**.

### Left open

The paired combined offline run against `main`'s dashboard remains the final Week 5 integration
check; Week 6 and the remaining backlog are unchanged.

## 2026-09-04 — session 20 · suite-count documentation correction

### Attempted

Apply the paired host's verified pytest count to `CONTEXT.md` §4.

### Worked

- Updated the expected non-placeholder suite count from 286 to **288 passed, 21 deselected**.
  The extra passing test is the live documentation-count guard itself; the paired host confirmed
  this is the number that makes `test_context_quotes_the_real_passing_and_deselected_counts`
  green.

---

## 2026-09-04 — session 19 · Week 4 degraded-input quality gate

### Attempted

Build the Week 4 gate from `ENDGAME.md`: defocus, glare, poor polish, wrong exposure, and empty
field must never flow into a confident prediction.

### Worked

- Added `reefprint.trust.quality` with explicit `InputQualityMetrics`, calibration-sourced
  `QualityThresholds`, and a `QualityAssessment` that is either usable or a named refusal.
- Each required degradation is detected independently; multiple failures are retained together,
  and missing/non-finite/out-of-domain metadata becomes `MALFORMED_INPUT` rather than a pass.
- Added tests for a clean input, all five degraded cases, multi-failure reporting, and missing
  metadata. Week 4 is now implemented on this branch; no prediction value is produced by the
  quality gate itself.

### Left open

- The paired host must run the full suite and confirm both W1 and W2. Thresholds in the tests are
  explicitly synthetic calibration values and must be replaced by field calibration before any
  demo claim.

---

## 2026-09-04 — session 18 · Week 3 predictive-band correction

### Attempted

Resolve the Week 3 failure reported by the paired `main` session: a perfect 20/20 held-out
locality was outside the calibration-only Beta interval.

### Worked

- `CoverageBand` now retains the Beta shapes and derives a central Beta-Binomial predictive
  interval for each held-out locality. This combines calibration-set uncertainty with the
  held-out count's binomial noise; 20/20 is therefore not rejected merely because its observed
  proportion is at the edge of the calibration probability band.
- `LocalityCoverage.within_band` uses the predictive count interval, while the reported Beta
  probability band remains visible and the summary names covered/total counts plus predictive
  bounds.
- Added a regression test proving the 20/20 case is admissible and 0/20 is rejected. The paired
  session's reported failure is therefore addressed as a statistical design correction, not a
  weakened fixture.

### Left open

- The paired host should rerun the full suite and report the exact result. Week 4 remains the next
  queue item after that confirmation.

---

## 2026-09-03 — session 17 · Week 3 locality-held-out conformal coverage

### Attempted

Implement the next gate from the Sept 3 handoff: exact split-conformal coverage bands and a
per-held-out-locality audit on `reefprint`, without touching the unmerged `main` branch.

### Worked

- Added `reefprint.trust.conformal`. `coverage_band()` uses the finite-sample
  `Beta(n + 1 - l, l)` law, with `l = floor((n + 1) * alpha)`, rather than the stale Wald
  approximation. The resulting standard deviations are 2.96 percentage points at calibration
  n = 100 and 6.26 points at n = 20.
- Added `audit_coverage_by_locality()`, which refuses overlapping calibration/test localities,
  refuses a section assigned to two localities, and reports each held-out locality independently.
  Its honest calibration n counts independent localities, never pixels or patches.
- Replaced the two Week 3 red tests with synthetic tests covering per-locality reporting,
  locality-specific gate failure, Beta-band sizing, pixel-count inflation, and split leakage;
  the Week 4 degraded-input test remains explicitly marked as placeholder.
- Updated `CONTEXT.md` and the trust package documentation to reflect the Sept 3 handoff and the
  corrected Week 3 state. The branch's docs were stale (last updated Aug 28 and still naming the
  Week 1 codebook run); that Week 1 action remains assigned to `main`.

### Did not work / limitation

- This host has neither `uv` nor a Python executable, so the documented `uv sync` and pytest
  commands could not run locally. The implementation is constrained to the already-declared
  NumPy/SciPy stack and the tests are committed for execution in the project's normal environment.

### Left open

- Run the audit against the real 12-section Kaggle prediction output once `main` supplies the
  prediction sets. Week 4 remains the next unstarted gate after that run.

---

## 2026-08-28 — session 16f · Kaggle clears the memory blocker; loader proven on 12 real sections

### Attempted

Session 16e's blocker: the extinction loader is TDD'd correct, but a real section's frame stack
needs ~5 GB once `RotationSeries` constructs it, and this machine has 7.9 GB total / ~1 GB free.
Three options were on the table, undecided. Used the user's Kaggle account (30 h/week GPU quota,
though this needed only CPU RAM) instead of picking one unilaterally.

### Worked

- **Uploaded `S3_v2.zip` as a private Kaggle dataset** (`lethabomh14/lumenstone-s3-v2-reefprint`,
  confirmed with the user first since this is redistributing a third party's informally-licensed
  data to another service, not just a local download). Kaggle auto-extracts an uploaded zip into
  individual files rather than keeping it as one archive — the loader's `zipfile.ZipFile`
  interface had to be duck-typed against a real directory (`_DirArchive`, kernel-side only, not
  committed to the repo) rather than assumed to still be a zip.
- **Uploaded the repo's `src/` and `experiments/002`–`003` as a second, small private dataset**
  (`lethabomh14/reefprint-code`) so a Kaggle kernel could import `reefprint` without a full git
  clone.
- **Two path-discovery bugs, found and fixed via the kernel's own error logs**: v1 assumed
  `/kaggle/input/<dataset-id>` directly; the real mount nests one level deeper,
  `/kaggle/input/datasets/<owner>/<dataset-id>/...`. Fixed with a recursive, fragment-matching
  directory search instead of a guessed exact path — the kind of defensive lookup this project's
  loaders already use elsewhere (never assume a name resolves the way it "should").
- **Kernel version 3 completed clean**: 12 sections attempted, 9 measured successfully at full
  3396x2547 resolution (`S3_test_01/02/03/07/12/13/14`, `S3_train_01/02/03/04/05`), 3 skipped for
  "only 0 rotation frames" (matching Sibusiso's earlier finding that ~29 of 47 sections are
  static images with no rotation acquisition at all). The `(71, 2547, 3396)` float64 array that
  OOM'd locally — the literal failing case from session 16e — loaded and measured without
  incident on Kaggle's RAM.
- **A genuine new archive defect, caught rather than hidden**: `S3_test_04` skipped with
  `"frame S3_test_04_r045.jpg shape (3396, 2547) != mask shape (2547, 3396)"` — one frame in that
  section's rotation series is transposed relative to its own mask. The loader's "report, don't
  raise, on a shape mismatch" design (built and tested in session 16e against synthetic
  mismatches) worked correctly on a real, previously-unseen failure mode on the first real run
  that reached it.
- Codebook used was the same explicit placeholder as the local smoke test
  (`code_0`, `code_1`, ...) — the printed per-code extinction-depth numbers are a plumbing
  result, not a mineralogical one. No claim is made about which code is which mineral.

### Did not work / left open

- **The real codebook is still Sibusiso's to supply.** This run proves the pipeline works end to
  end on real data at real resolution; it does not yet produce week-1 leg (b)'s actual claim
  (pentlandite dark / pyrrhotite extincting), which needs KHANYA's real
  `.segmentation.lumenstone.CODEBOOK` substituted for the placeholder.
- The Kaggle dataset and kernel are left in place (private) for reuse rather than torn down —
  re-running with a real codebook once available is a `kaggle kernels push` away, not a
  re-upload.

### Follow-up, same day: `S3_test_04`'s transposed frame is isolated, not systematic

Scanned every frame in every section against its own mask's shape (1,195 frames, all 47
sections, decoded from the local verified archive). **Exactly one mismatch**:
`('S3_test_04', 45, (3396, 2547), (2547, 3396))` — the same one the Kaggle run already caught.
Nothing else in the archive has this defect. One corrupted/transposed file, not a systematic
acquisition or packaging issue. No action needed beyond what the loader already does (skip and
report); not worth a bug report to LumenStone's maintainers for one file in 1,195.

---

## 2026-08-27 — session 16e · extinction loader built and TDD'd; real archive OOMs on this machine

### Attempted

Session 16d's next action: build the loader wiring the real S3 v2 zip into
`reefprint.bridge.measure_section_extinction`, which was TDD'd against a synthetic stage series
but had nothing reading real archive frames into the `RotationSeries`/`LabelledSection` objects
it needs.

### Worked

- **`experiments/003-s3v2-extinction/run.py`**: `load_section_as_specimen_series()` decodes one
  section's mask and full rotation-frame stack from the zip, builds a `RotationSeries(geometry=
  SPECIMEN)` and `LabelledSection`, and hands both to `measure_section_extinction`. Refuses to
  run without a `--codebook` JSON file rather than deriving mineral names from mask pixel values
  — that mapping is a mineralogical judgement call KHANYA's `src/polarimetry.py` already makes
  via `.segmentation.lumenstone.CODEBOOK`, and Rule 6 reserves it for a human, not for this
  script to guess.
- **`tests/test_s3v2_extinction_loader.py`**, 4 tests, TDD against a synthetic archive built
  from the existing stage-rotation phantom (same pattern as `tests/test_s3v2_reader.py`):
  recovers a full-resolution series and section correctly, reports a shape mismatch and a
  too-few-frames case as data rather than crashing, and feeds cleanly into
  `measure_section_extinction` end to end. All pass.
- **Found and fixed a false claim before it shipped**: the module docstring originally claimed
  building the frame stack as float32 halves memory versus float64. It doesn't —
  `RotationSeries.__post_init__` (`reefprint.acquire.series:92`) unconditionally casts to
  float64 on construction regardless of what's passed in, a test failure caught this before the
  docstring went uncorrected. Fixed the docstring to state the real cost (~5 GB for a full
  3396x2547x72 section, not the ~2.5 GB float32 alone would cost) rather than the convenient
  number.

### Did not work

- **Smoke-tested against the real archive (one section, a throwaway placeholder codebook — no
  mineralogical claim made) and it OOM'd**: `numpy._core._exceptions._ArrayMemoryError: Unable
  to allocate 4.58 GiB for an array with shape (71, 2547, 3396)`. This machine has 7.9 GB total
  physical memory and ~1 GB free at the time of the run (`systeminfo`). The loader's plumbing is
  correct — proven by 4 passing tests against synthetic data at the real archive's layout — but
  full-resolution, whole-section-in-memory extinction measurement does not fit on this hardware.

### Learned

The float32-halves-memory claim would have shipped as a plausible-sounding but false statement
in a module docstring if the test suite hadn't been run before writing it down — worth noting as
a concrete instance of why Rule 1's discipline extends to code comments, not just reported
numbers.

### Left open

- **The real memory blocker needs one of three decisions, not a workaround chosen unilaterally
  here**: (1) run this on a machine with more RAM — Sibusiso's, or a cloud CPU instance; (2)
  downsample frame resolution before building the stack, which changes measurement precision
  and should be a stated, documented tradeoff, not a silent default; (3) restructure
  `measure_section_extinction`'s calling convention to stream over row-chunks instead of
  requiring a full frame stack in memory — a real change to the sanctioned bridge module,
  cross-cutting enough to need review before landing.
- Codebook is still a placeholder (`code_0`, `code_1`, ... from the real mask's actual codes
  `{0,1,2,6,8,9}` on section `S3_test_01`) — no mineralogical claim has been made on real data
  yet, deliberately.

---

## 2026-08-27 — session 16d · N3 measured a third time, on the verified archive, this machine

### Attempted

Session 16c's clean re-download finished and verified (5,227,181,560 bytes, exact match to
Yandex's declared size; `zipfile.testzip()` clean, 2,385 entries). Ran the placeholder test's own
instruction: `experiments/002-s3v2-geometry/run.py` against the real archive, for the first time
independently of Sibusiso's machine.

### Worked

- **Pooled default run** (3 usable of 6 sections read; 3 skipped on shape mismatch or zero
  frames — same failure mode session 11 already characterised): 2nd harmonic 3.4x its noise
  floor, 4th harmonic 1.8x, threshold 5.0x. `NEITHER`. Third independent confirmation of N3,
  now on a verified archive rather than an unverified one.
- **`--brightness-quantile 0.5` re-run**, the targeted check CONTEXT.md named as the way a
  `NEITHER` could still flip: restricting to the brightest 50% of pixels by fitted DC moved the
  2nd harmonic from 3.4x to 4.0x — closer, but still under the 5.0x threshold — while the 4th
  harmonic stayed flat at 1.8x. Per the script's own printed framing, failing on the *most
  favourable* subset (where an analyser signal has its best odds of surviving) is a stronger
  confirmation of stage than the pooled result alone, not a softer one.
- Archive now reports **47 sections**, not the 29 CONTEXT.md's prior wording carried from
  Sibusiso's runs — worth noting as a discrepancy, not yet explained (different sampling of
  `--sections`, or the archive layout itself differs from what was inspected in session 11).
  Does not change the verdict: still `NEITHER` on every check run so far.
- Deleted `test_the_real_s3_v2_archive_has_been_measured` per its own docstring instruction —
  N3 has now been measured against the real archive, three times, independently, all `NEITHER`.

### Did not work / open

- **The extinction-estimator path (leg (b)'s actual route forward) is not built.**
  `reefprint.bridge.measure_section_extinction` is TDD'd against a synthetic stage series, but
  nothing yet reads the real S3 v2 zip into the `RotationSeries`/`LabelledSection` objects it
  needs. `run.py`'s pixel-sampling approach (scattered positions, one frame decoded at a time)
  proves harmonic strength cheaply; it does not assemble the labelled per-mineral measurement
  that section-scale mineralogy needs. A naive full-resolution stack is large enough per section
  (3396x2547 x up to 72 angles) to need the same one-frame-at-a-time discipline `run.py` already
  uses, adapted to extinction rather than harmonic-strength sampling. Scoped as its own build,
  test-first, rather than rushed inline.

### Left open

- The extinction-path loader above — next session's actual next action.
- The 29-vs-47 section-count discrepancy — not investigated this session.
- N3 itself stays open per doctrine (a `NEITHER` verdict is not a closed question, it is a
  routed one) but leg (b) is licensed to proceed via the extinction estimator once its loader
  exists.

---

## 2026-08-27 — session 16c · the resumed download was silently corrupt

### Attempted

Download `S3_v2.zip` completed per the background task notification. Verified before trusting
it — Rule 3's habit applied to a file, not a metric.

### Did not work

- **The `-C -` resume corrupted the archive.** First attempt dropped at 1.6/5.23 GB
  (`curl: (56) Recv failure`, masked earlier by a `| tail` that reported exit 0 — see session
  16a). Re-resolved a fresh signed href and resumed with `curl -C -`. The result was 6.48 GB,
  not 5.23 GB, and not a valid zip (`zipfile.BadZipFile`). The fresh href likely didn't honour a
  byte-range request against the partial local file — curl appears to have appended a full
  second copy on top of the partial first one rather than truly resuming. **Lesson: don't trust
  `-C -` against a freshly re-resolved signed URL for this host; verify size and zip integrity
  before doing anything else with a downloaded archive, every time, not just when something
  looks wrong.**
- Deleted the corrupted file and restarted clean (no `-C -`) rather than trying to salvage or
  re-resume a second time — a corrupt 6.48 GB file is not a checkpoint worth preserving.

### Left open

Clean download restarted, in progress. Verify size (5,227,181,560 bytes exactly) **and**
`zipfile.testzip()` before running `experiments/002-s3v2-geometry/run.py` against it — both
checks, not just one; this session showed the size check alone would have caught it, but only
because the corruption happened to overshoot rather than undershoot the byte count.

## 2026-08-27 — session 16b · widened the texture search; the finding is an absence, checked properly

### Attempted

The user asked to search more broadly for a public dataset pairing texture (images), Cr2O3,
pyroxene fraction and locality for Bushveld/UG2, and to name a pivot if none exists — on the
premise that "calling won't help" (CGS). Surveyed six real candidate sources rather than
speculate.

### Worked — real candidates checked and precisely ruled out

- **GeoMet** (Zenodo 10.5281/zenodo.6336138, CC BY 4.0, Chilean porphyry copper).
  `drillholes.csv` downloaded and inspected directly: 2,000 rows, X/Y/Z continuous coordinates
  and 18 elements, **no discrete locality identifier** (would need spatial clustering to
  construct one — another judgement call) and **no images anywhere in the dataset**
  (comminution.csv and flotation.csv are physical test indices, not texture).
- **HIDSAG** (figshare, Nature Sci. Data 2023, CC BY 4.0) — genuinely pairs hyperspectral/RGB
  images with response variables (modal mineralogy %, recoveries) and has real sample-group
  structure (MINERAL1's process-line/composite IDs). Checked precisely and ruled out on domain
  grounds, not data quality: Chilean porphyry copper-molybdenum, not chromite/PGE, and the
  imagery is hyperspectral reflectance of loose composite samples, not reflected-light rotation
  series on polished sections — nothing in it maps onto `reefprint.polarim` or `reefprint.bridge`
  without a domain and instrument substitution the abstract would have to defend on its own
  terms. Recorded as a possible **out-of-domain pipeline check** (proves the statistical
  machinery on real non-synthetic data) but not as UG2 evidence, and not built this session —
  see "Left open."
- **Two real published studies pair chromite texture directly with chemistry on UG2/Bushveld
  chromitite** — Kaufmann et al. 2019 (*Economic Geology* 114(3):569–590,
  doi:10.5382/econgeo.4641, **same Thaba mine as the Bachmann CSV already in
  `data/bushveld_thaba_chromitite/`**) and Veksler et al. 2018 (*Journal of Petrology*
  59(6):1193, chromite crystal-size distribution through two UG2 drill profiles). Both
  paywalled, neither has a public data release found. **The overlap with Bachmann's mine is the
  useful part**: if either author would share underlying sample-level data on request, it could
  plausibly join to the boreholes already in hand by locality. This is an email to an academic
  author, not a call to a public institution — a materially cheaper ask than the CGS item, and
  authors on 2018–2019 papers are frequently willing.
- **A University of Pretoria PhD/MSc thesis** (open-access via `repository.up.ac.za`, chapter 6,
  "Identification of mineralogically and chemically different types of UG2 chromitite") plots
  **median chromite grain diameter** — an actual texture measurement — against Cr2O3, PGE grades
  and pentlandite content, across 14 samples in three groups (A1–A5, B1–B4, C1–C5). This is the
  closest match found to what the falsification test needs, in principle. **Ruled out on two
  independent grounds, either one sufficient alone:** (1) the numbers exist only as line-chart
  figures in a scanned PDF — reading precise values off a plotted line is exactly the "infer, not
  extract" failure the doctrine's first rule forbids, not a defensible data-entry method; (2)
  even with real numbers, three sample groups is below `MIN_LOCALITIES_FOR_INFERENCE = 5` — the
  module would refuse to run inference on it by design, correctly.

### Learned

**Real texture-plus-chemistry data for UG2 chromitite exists in the literature, but not as an
open, machine-readable, adequately-sized public dataset.** That is a different and more precise
statement than "no dataset was found," and worth keeping precise: the domain has been studied
this way, by multiple groups, on drill core from named mines — the barrier is publication format
(figures, not files) and sample count (single-digit to teens per study, because this kind of
petrographic work is slow), not that nobody has thought to measure both things together.

### Left open, for the domain lead

**No public source clears the bar to run the week-2 gate on real Bushveld chromitite texture, as
things stand.** Three live options, none decided here:

1. **Email Kaufmann and/or Veksler directly**, naming the overlap with the Bachmann mine already
   in hand. Cheapest, and the only option that could plausibly deliver real UG2 texture data at
   all before the final.
2. **Report the search itself as the week-2 finding, honestly**: real target, locality and half
   the baseline are in hand (session 16a); texture was sought specifically and does not exist
   publicly at a usable n; the gate is reported as blocked-on-data rather than run against
   invented or undersized numbers. Consistent with Rule 9's spirit even though this is a data
   absence, not a null result — the doctrine's rule 10 (state limitations before anyone asks)
   applies just as much here.
3. **Pivot to the oxidation index** per `CLAUDE.md`'s own named fallback — normally triggered by
   H0 not being rejected, but the practical effect of "the challenger variable cannot be
   obtained" is the same redirection, for a different and equally honest reason. Worth stating
   in the talk as a different failure mode from a null result, not folded into one.

## 2026-08-27 — session 16 · went and found the two datasets the backlog had been waiting on

### Attempted

Two open items had sat as "not yet found" for multiple sessions: the real `S3_v2.zip` (week-1
leg (b), N3), and any public dataset combining Cr2O3, pyroxene fraction, texture and locality
(week-2 falsification test). Both were treated as things to keep waiting for. Went and searched
instead.

### Worked

- **Found and started downloading the real LumenStone S3 v2 archive.** The project page
  (`imaging.cs.msu.ru/en/research/geology/lumenstone`) names the actual host: a Yandex Disk
  share, `https://disk.360.yandex.ru/d/1ItlsInqs3iiow`. Resolved to a direct download href via
  Yandex's public API (`cloud-api.yandex.net/v1/disk/public/resources/download`), which also
  confirmed the file identity independently of anything in this repo: `filename=S3_v2.zip`,
  `fsize=5227181560` — 5.23 GB, matching the figure `experiments/002-s3v2-geometry/run.py`'s own
  docstring already carried from session 11. Download started in the background to
  `data/lumenstone/S3_v2.zip` (gitignored, `data/**`). **In progress at time of writing** — the
  next session (or a wakeup later this one) runs `experiments/002-s3v2-geometry/run.py --archive
  data/lumenstone/S3_v2.zip` the moment it completes, which finally lets this machine reproduce
  N3 rather than take Sibusiso's two runs on faith. Licence: "free to use in your own research,
  cite the references" per the project page — same informal terms already recorded in
  `docs/05-toolchain.md`, nothing new to add there.
- **Found real Bushveld geochemistry.** `data.mendeley.com/datasets/dc8jcnbcvk` (Bachmann 2019,
  CC BY 4.0, DOI `10.17632/dc8jcnbcvk.1`, accompanying a *Journal of African Earth Sciences*
  paper on chromitite classification) — 1,205 borehole assay rows: Cr2O3 and five other major
  oxides, six PGE grades by ICP, stratigraphic seam (LG1–MG4), and 317 distinct `BH_ID`.
  Downloaded to `data/bushveld_thaba_chromitite/` (gitignored), with `SOURCE.md` recording
  citation obligations, the exact fetch method (Mendeley's public files API, not the SPA page —
  the page itself doesn't render a fetchable file list), and a column-by-column mapping against
  `evaluate_texture_uplift`'s four required arguments.
- **That mapping is the actual finding, and it is not "week 2 is unblocked."** The CSV supplies
  `target` (real PGE grades — not a proxy) and `localities` (317 boreholes, comfortably above
  `MIN_LOCALITIES_FOR_INFERENCE = 5`) cleanly. It supplies half of `baseline_features`: Cr2O3
  direct, but no pyroxene-fraction column — `SiO2_%`/`Al2O3_%`/`CaO_%` could support a
  chemistry-based silicate-fraction proxy, but computing one is a normative-mineralogy judgement
  call and Rule 6 forbids an LLM from making it, so it is flagged (CONTEXT.md T2) rather than
  derived. **It supplies no texture feature at all**, and the reason matters: this is bulk assay
  chemistry over depth intervals, with no polished-section imagery tied to those same intervals.
  Nothing in the file could become a texture feature by any amount of processing — the data that
  would answer the falsification test's actual question does not exist in this dataset, full
  stop.
- **Reframed the CGS item, because it was quietly promising more than it delivers.**
  `CONTEXT.md` had carried "CGS phone call still open" as if placing the call were the remaining
  step. It is not: even a granted CGS core request hands over physical core, not
  texture-ready images tied to specific assay depths, and `reefprint.segment` — the piece that
  would turn core photographs into a texture feature — is not built. Recorded as its own item
  (CONTEXT.md T1) so "we called CGS" cannot later be misread as "texture is solved."

### Did not work / friction

- **The Mendeley Data page itself does not render a file list to a plain fetch** — the dataset
  page is a client-rendered SPA and the description text alone doesn't name the file or give a
  URL. The public files API (`data.mendeley.com/public-api/datasets/<id>/files`) does, in one
  request, with a signed download URL. Worth remembering for any future Mendeley dataset: don't
  read the page, hit the API.
- **The Yandex Disk share link is not itself a download URL.** `disk.360.yandex.ru/d/...` returns
  an HTML viewer; the actual bytes come from Yandex's public resource-download API given that
  share URL as a `public_key` query parameter, which returns a time-limited signed `href`.

### Learned

Two "still open" items had accumulated sessions of being treated as blocked-on-someone-else
(Sibusiso's machine, a phone call to CGS) when both were actually blocked on nobody having spent
twenty minutes searching. That is worth naming plainly rather than filing under a generic
lesson: "not yet found" and "not findable" are different states, and CONTEXT.md's own wording
("almost certainly", "no evidence yet") had drifted toward describing the second when the honest
status was the first for both.

The Bushveld CSV also demonstrates the useful failure mode of *bringing back a real dataset that
still doesn't close the gate*. Rule 9's discipline — falsification is a deliverable, report the
result either way — has a document-hygiene analogue: finding real data that partially answers a
question is worth recording precisely, in a table naming exactly which required input it does
and does not supply, rather than either overselling it as unblocking or leaving it undocumented
because it didn't finish the job.

### Left open

- **LumenStone download in progress**; run `experiments/002-s3v2-geometry/run.py` the moment it
  completes and record whatever verdict comes back, `NEITHER` included, per Rule 9.
- **T1, T2 above** — texture remains genuinely absent, and a pyroxene-fraction proxy needs a
  domain decision before the week-2 gate can run on real data at all, even with the archive.
- **Neither dataset has yet been wired into `reefprint.heads.falsification` or
  `reefprint.bridge`.** Deliberately not built this session: gluing a loader onto a test that is
  still missing one of its four required inputs would produce code with nothing real to run
  against, which is scope for its own sake rather than progress.

## 2026-08-24 — session 15 · leg (b)'s missing half: a sanctioned path onto the extinction estimator

### Attempted

Merged three unmerged branches a concurrent session had left in the working tree (conformal
coverage's Beta-vs-binomial fix, the week-1 figure's geometry refusal — both described below),
then picked up CONTEXT.md's own stated single next action for week-1 leg (b): the fourth-harmonic
extinction estimator (`reefprint.polarim.extinction`) was built and tested, but nothing routed a
labelled section onto it the way `reefprint.bridge.measure_section` routes one onto the Stokes
inversion. `measure_section` calls `series.require_analyser_rotation()` unconditionally and
refuses a stage series (N3's guard); there was no mirror-image guard refusing an *analyser*
series fed to the extinction fit, which would silently discard its second-harmonic content the
same way a stage series silently zeroes out under the Stokes fit.

### Worked

- **`reefprint.bridge.extinction.measure_section_extinction`**, TDD'd against
  `crossed_polars_stage_series` (the stage phantom already built for N3), 9 new tests in
  `tests/test_bridge_extinction.py`: geometry refusal in both directions (an analyser series is
  refused with `require_specimen_rotation()`, same as an unknown-geometry series), shape
  mismatches and thin-angle counts skipped rather than raised (mirroring `measure_section`'s
  asymmetry between per-section defects and a wrong-geometry archive-wide one), the mineralogical
  payoff — pentlandite reads extinction depth exactly `0.0` while pyrrhotite extincts, recovered
  through the *other* geometry's own physics from the same phantom — and a `crossing_ratio`
  self-test carried per mineral, the extinction path's equivalent of the Stokes path's noise
  floor.
- **The module docstring is load-bearing, not decoration.** `extinction.py`'s own docstring
  already warns that raw extinction depth is not contrast-normalised — crossed polars block the
  unpolarised pedestal, so there is no `S0` to divide out, and comparing raw depth between two
  minerals compares their bireflectance *and* brightness at once, "finding N2 in a new costume".
  `bridge/extinction.py` restates that warning at the point someone will actually call this, and
  the returned `MineralExtinctionStatistic` is deliberately **not** shaped like `MineralStatistic`
  — no `s0_median` field exists to invite a normalisation nobody has the data to do honestly.
  The one claim it is licensed to make — a mineral is exactly dark vs extincts at all — needs no
  such normalisation, because zero is zero regardless of brightness.
- Wired into `reefprint.bridge`'s public exports, package docstring updated to describe both
  guards as one mirrored pair rather than describing only the older one.
- Two branches from a concurrent session, merged onto `main` after independent verification
  rather than trusted on the commit message:
  - **F3: conformal coverage is Beta, not binomial** (`bd4d4a8`, `ed34b10`). Coverage of a
    split-conformal calibration set of size `n` at miscoverage `alpha` is `Beta(n+1-l, l)`,
    `l = floor((n+1)*alpha)` — not the binomial Wald SE `sqrt(0.9*0.1/n)` the finding had used.
    Recomputed myself before merging: `n=100` gives 2.96pp exact vs 3.00pp Wald, `n=20` gives
    6.26pp vs 6.71pp — Wald is *larger*, meaning the original finding had the error's direction
    backwards (a second commit on the same branch caught and corrected its own first commit's
    "buys less precision than it promises," which should have read "overstates the spread").
    `tests/test_docs_conformal_figures.py` pins the corrected figures and was confirmed RED
    against the old ones first.
  - **viz: the week-1 gate figure refuses a geometry it cannot support** (`33bbced`).
    `anisotropy_figure()` never consulted `series.geometry` and hardcoded panel 3's x-axis label
    as "analyser angle (degrees)" regardless of what actually rotated — a silent wrong answer on
    the one figure the week-1 gate is argued from. Now the label follows `series.geometry` and a
    `SPECIMEN` or `UNKNOWN` series draws a visible refusal on the figure rather than a blank
    panel (Rule 5's pattern: still renders, cannot be mistaken for a valid result). This branch
    independently found and flagged the exact same abstract overclaim fixed in session 14
    (`6b32ef2`) — two separate audits landing on the same finding from different files is
    corroboration, not coincidence.
  - Both merged with `--no-ff` after reading the full commit bodies and re-deriving the key
    numbers rather than taking them on faith. `test_docs_counts_are_current.py` (added by the
    conformal branch) caught the resulting staleness in CONTEXT.md's pinned test count
    immediately after each merge — 253→256 after the first, 265→274 after this session's own
    addition — which is exactly the failure mode that test exists to catch.

### Did not work / friction

- **A concurrent session was creating and checking out branches in this same working tree** while
  this session was also committing. A commit made mid-session landed on whatever branch happened
  to be checked out (`fix-run-geometry`) instead of `main`, and had to be fast-forwarded after
  the fact. `git branch --show-current` before committing, from now on, in a tree anyone else
  might be touching concurrently.

### Learned

The repo layout comment in `CLAUDE.md` already says `bridge/` is "the only sanctioned route" from
masks plus frames to a per-mineral number — singular, at the time it was written, because only
the analyser geometry had a route. Building a second sanctioned route for the second geometry,
with its own mirrored guard, is not adding a feature so much as finishing the sentence: the
project's own physics table names two geometries, and only one had a path all the way through the
seam. The guard that stops the *wrong* geometry from being routed around is worth as much on the
new path as N3's original guard was on the old one — which is why it was built alongside the
estimator rather than after something used it wrong, the same reasoning `require_specimen_rotation`
itself gives for existing at all.

### Left open

- **The real archive still is not on this machine.** Everything above is proven against the
  synthetic stage phantom. The moment `S3_v2.zip` is available, leg (b) needs: confirm each
  section's geometry from the frames first (do not assume SPECIMEN from N3's aggregate lean —
  measure it per section, the same discipline N3 itself insists on), then call
  `measure_section_extinction` the way `measure_section` is called today.
- **No script yet drives `measure_section_extinction` over a real archive** the way
  `experiments/002-s3v2-geometry/run.py` drives the geometry discriminator. Writing one now
  would be guessing at the archive's exact directory layout beyond what `run.py` already
  reverse-engineered; better to reuse `run.py`'s section-reading code once the geometry is
  confirmed, than to duplicate it against untested assumptions.

## 2026-08-23 — session 14 · the abstract, and the domain lead's surname was wrong

### Attempted

Write the Mintek SCi Grad Hackathon abstract (**due 30 August 2026, one page**) and render it to
PDF. The letter names three required elements — proposed approach, methods or technologies,
expected outcomes or impact — and states that submissions undergo plagiarism, AI-generation, IP
and originality checks, and that external sources, data and contributions must be acknowledged.

### Worked

- **`docs/06-abstract.md`** — source of truth for the wording, 662 words of body text, plus
  working notes that are explicitly *not* part of the submitted page. The notes carry a
  **provenance table for every number on the page** (claim → source → Rule-1 rank), which is the
  thing that makes the page defensible under originality authentication rather than merely
  well-written.
- **Every number on the page is bounded in the sentence that carries it.** 40.4× is labelled "a
  phantom result, not an ore result"; the factor-of-126 split leak is labelled "on synthetic
  data"; the R5 000 rig is "costed as a design; no hardware is built, and no claim here depends on
  one" (ADR-0002). The 0.2–1.6 µm/pixel figure is **deliberately absent** — it is a design target
  spanning a factor of eight, and an abstract is exactly where such a number gets read as a spec.
- **The negative result is on the page, not hidden.** The N3 `NEITHER` verdict on LumenStone S3 v2
  (29 sections, 116 000 pixels) is stated, along with the decision to route to the fourth-harmonic
  estimator rather than force the convenient inversion. Rule 9's reasoning generalises past the
  falsification test: a team that has run something real has negative results to report, and a
  team that has run nothing does not.
- **Prior art is cited by name.** Pirard, Lebichot & Krier (2007) is real prior art on
  polarised-light *imaging* in ore microscopy. Pre-empting a judge who knows it costs one clause;
  being corrected on stage costs the claim.
- **`docs/06-abstract.html` + headless Chrome → `docs/06-abstract.pdf`, one page, verified.**
  Chrome is a tool we run, not a library we link, so **no SBOM or `05-toolchain.md` entry** — the
  same treatment `docs/05-toolchain.md` already gives git. Page count is checked mechanically:
  `grep -a -o "/Count [0-9]*" docs/06-abstract.pdf` must print `/Count 1`.

### Did not work

- **First render was two pages**, overflowing by 5.2 mm — about one line. Fixed by trimming size
  and paragraph gaps, *not* by cutting evidence and not by squeezing leading first (that is what
  makes a dense page look cramped).
- **Two typographic defects the page count would never have caught**, both found by rendering the
  PDF and *looking* at it rather than trusting that it compiled: `~R5 000` broke across a line
  boundary as `~R5` / `000`, and the author byline wrapped mid-affiliation (`BSc Electrical
  Engineering,` / `University of the Witwatersrand`). Fixed with `&nbsp;` on the numeral and by
  making each author a block unit. Both are the class of detail that separates a submitted
  document from a draft.
- **Measuring overflow in the browser beat guessing at the trim.** No PDF library is installed
  (`pypdf`, `pikepdf`, `fitz` all absent) and adding one to count pages would have been an SBOM
  entry bought for nothing. The screen CSS mirrors the print geometry exactly, so measuring the
  content box in the same engine that paginates gives the overflow in millimetres directly.

### Learned

**The domain lead's surname in the constitution was wrong, and it was inferred, not told.**
`CLAUDE.md` recorded **Lethabo Mphukuile**, taken from the git commit identity, with a note to
correct it if wrong. It is **Lethabo Hoaeane**, confirmed by Lethabo on 2026-08-22. It had already
propagated to `CONTEXT.md` and to the decider line of **all three ADRs** — the documents whose
whole purpose is to record who decided what. Corrected in those four files; **the earlier
entry in this log at "ADR-0001's decider filled in" is left standing, wrong, because this file is
append-only** — this paragraph is the correction it links to.

The generalisable part: a git commit identity is a *convenience string a person typed once*, not
a record of their name, and inferring an identity from one and then writing it into governance
documents is a Rule-1 violation wearing different clothes — a number you did not measure and a
name you were not told are the same mistake. It survived thirteen sessions because it was
plausible and nobody was asked.

Related: the abstract header had **"Team Sonar, University of the Witwatersrand"**, inherited from
`CLAUDE.md`. The team is three people across **three** institutions — Unisa, Wits and TUT. Also
corrected in `CLAUDE.md`. Institutions are written out in full on the submitted page;
abbreviations read as internal shorthand.

### Also this session · the mentor request

**We have no mentor.** Item 5 of the Mintek letter: *"If you require a mentor from Mintek, please
indicate this clearly so that we can assist with the appropriate support."*
`docs/07-mentor-request.md` → `.html` → `.pdf`, one page, same Chrome pipeline and same
typography as the abstract so the two attachments read as one set from one team.

The letter's substance is **an ordered list of the expertise we need**, not the request itself.
"Appropriate support" is a *matching* problem — Mintek cannot assign the right person without
knowing what is wanted, and a bare "we need a mentor please" spends the opportunity to get a good
match. The list is ordered, and says which single area matters most rather than asking for
everything.

Two things the letter does deliberately:

- **Names the gap plainly** — "None of us is a practising mineralogist, and several of our
  load-bearing claims are mineralogical." This is CLAUDE.md **blind spot 8** turned into an
  action: *no load-bearing mineralogical claim rests on the domain lead alone; book external calls
  instead.* A mentor request is the cheapest external check available to us, and naming the gap is
  precisely what makes the request matchable. The domain lead's prior metallurgical-engineering
  background is **not** claimed — still Lethabo's call, and the sentence is true without it.
- **Rules out the obvious objection before it is raised** — "We are not requesting data, samples
  or laboratory access." True (hard constraint: public sources only), and it removes the most
  likely reason to hesitate.

First draft ran **46.8 mm** over one page. Cut by tightening prose and folding "any one of these
would be valuable" into the list introduction — *not* by dropping the expertise list, which is the
only part Mintek cannot act without. A request for someone's scarce time that runs to two pages is
arguing against itself.

### Also this session · the submission packet, and a claim that was not true

Team details supplied, so the packet was completed: team-details PDF, the email body, and the
two documents above, all with **no placeholders**.

- **Three things that were wrong or unsafe, found by finishing rather than by looking for them:**
  1. **The abstract claimed "a continuous *public* commit history."** The KHANYA repo is
     **private**. That is a false statement on a document that goes through originality checks —
     worse than the placeholder we were fixing at the time. Now reads "a continuous, timestamped
     commit history," which is true today, stays true if the repo is opened later, and is the
     claim originality authentication actually cares about. Keeping the repo private until after
     1 October is also the right call competitively, so the wording should not be reverted.
  2. **SA ID numbers must not enter git.** `submission/` is gitignored and holds all three
     members' ID numbers and mobile numbers. The repo is private *today*; git history outlives a
     visibility setting, and the originality defence may yet require opening it. Deleting a file
     later does not remove it from history.
  3. **The ID numbers were checked, not trusted.** All three pass the Luhn check digit, are
     13 digits, carry citizenship digit `0`, and decode to valid dates of birth. Cheap, and a
     transposed digit would otherwise have reached Mintek. Rule 1's habit applied to someone
     else's data: verify before it leaves the building.
- **The team-details document is a document, not a paragraph in an email.** The letter asks for
  five fields per member; a table renders them in a form Mintek can file, and the same details are
  also inline in the email body so nothing depends on an attachment being opened.

### Also this session · the abstract asserted a geometry its own code refuses to name

Picked up from an unmerged branch (`fix-abstract-neither`, `d0ebaff`) produced by a concurrent
session's assumption-auditor, verified against the source, and applied.

**The claim that was wrong.** The submitted page said the S3 v2 result was "evidence that the
published 'rotation sequences' are stage rotations, not analyser rotations." It is not.
`HarmonicVerdict.NEITHER` means *no modulation above the noise floor*, and
`src/reefprint/polarim/geometry.py:99` maps it to `RotationGeometry.UNKNOWN` on purpose, with the
reason in the docstring: *"'I cannot tell' and 'it is the convenient one' must not be the same
value. Rule 1."* Only `SECOND` and `FOURTH` name a geometry.

So the abstract performed, on public data, exactly the substitution the discriminator exists to
refuse — on the same page that advertises **"acquisition geometry is measured, not assumed"**. A
judge who reads the code finds the page contradicting the build's most distinctive decision. It
now reads: *"the geometry of the published 'rotation sequences' is not established by this
archive, and the Stokes inversion is not licensed to run on it."* Weaker, supported, and
rhetorically no worse — "we checked, the data would not tell us, and we declined to assume" is
the same negative-result story, minus the falsifiable overclaim.

**Learned, and it generalises past this sentence.** The overclaim did not come from carelessness;
it came from `CLAUDE.md` §The physics, which says these archives are *"almost certainly stage
rotations."* That is a reasonable **prior from domain knowledge**. The abstract attributed it to
the **discriminator run**. Laundering a prior into a measurement by attribution is Rule 1's
failure mode with better manners — no number was invented, only its provenance was upgraded.
The provenance table now carries the reasoning so the next person to tighten this paragraph finds
out why the wording is careful first.

**Not changed:** `CONTEXT.md` §3 argues `NEITHER` leans stage on SNR grounds (extinction depth
scales as bireflectance *squared*, so a symmetric null is asymmetric evidence). That argument is
far more defensible than the abstract's flat assertion was, and it is a methodology call for
Lethabo and Sibusiso, not a drafting fix. Flagged, left alone.

**Repo hygiene note.** A concurrent session is creating and checking out branches in this working
tree (`swarm-test`, `fix-abstract-neither`, `fix-conformal-distribution`, `fix-run-geometry`).
This session's commits landed on whichever branch happened to be checked out and had to be
fast-forwarded onto `main` before pushing. Check `git branch --show-current` before committing
here.

### Left open

- **Whether Lethabo's credential line should carry "prior metallurgical engineering."** It is
  real, recorded in `CLAUDE.md`, and on a metallurgy submission it is the most relevant credential
  on the page — but a credential line on a submitted document should say exactly what the person
  claims, so it is not a drafting decision. Lethabo's call.
- **"Team Sonar" is unconfirmed** as the registered team name.
- **Mentor: requested, not yet supplied.** `docs/07-mentor-request.md` is drafted and rendered.
  **It carries one placeholder — a mobile number — and must not be sent with it in.** The email
  address on it (`lethabomphukuile14@gmail.com`) carries the *old, wrong* surname; ordinary enough
  that no reviewer will care, but it sits two lines below the correct name, so use a matching
  address if one exists.
- **Per-member admin** — ID number, T-shirt size, contact details. Conference registration for
  2 October is required of all selected teams.
- **Voice pass.** The letter runs AI-generation checks. The ideas and every number are the team's
  own and the commit history evidences that, but the prose should be read aloud and adjusted by
  whoever presents, so the abstract and the ten-minute talk sound like the same people.

---

## 2026-08-21 — session 13 · the week-2 gate gets a statistical core

### Attempted

Build the falsification test's statistics (Rule 9's H0: after controlling for Cr2O3 and pyroxene
fraction, texture carries no additional predictive signal), TDD, against synthetic data with a
known ground truth — no real Bushveld geochemistry is in hand yet.

### Worked

- **`reefprint.heads.falsification.evaluate_texture_uplift`**: OLS on a baseline model (Cr2O3 +
  pyroxene fraction) and a full model (+ texture), Wald test on the texture coefficients using a
  cluster-robust CR1 covariance (Cameron & Miller 2015, White 1980), clustered by locality — same
  reasoning as Rule 2's split-by-locality guard: observations sharing a locality share unmodeled
  geology, so a plain OLS standard error overstates confidence. F-scaled Wald statistic, small
  cluster finite correction `G/(G-1) * (n-1)/(n-k)`, p-value from `scipy.stats.f.sf`.
- **`MIN_LOCALITIES_FOR_INFERENCE = 5`** refuses (`ValueError`) below that cluster count, mirroring
  the project's other declared-threshold guards (`DETECTION_SNR` in `geometry.py`,
  `LocalitySplit`'s backstop) — Rule 4 as a bound: cluster-robust inference at a handful of
  clusters is not inference.
- **Rule 3 satisfied structurally**: the null model (Cr2O3 + pyroxene fraction, no texture) *is*
  the required trivial baseline, so `FalsificationResult.baseline_r2` is a required, always-present
  field, not bolted on.
- **Honest n reported explicitly**: `FalsificationResult.n_localities` vs `n_obs`, same pattern as
  `LocalitySplit.n_groups`.
- TDD: `tests/test_heads_falsification.py` written first (`ModuleNotFoundError` on the first run,
  the correct RED), then the module. 5 real tests green: a true zero texture effect is not
  rejected, a true nonzero one is, honest n is locality count not row count, too-few-localities
  refuses rather than printing a fake p-value, baseline/full R² both reported. Full suite: **249
  passed, 25 deselected** (placeholders). `ruff check` clean, `ruff format` clean after one
  reformat pass.

### Did not work

- First draft named the public function `test_texture_uplift` — pytest's `test_*` collection
  pattern picked up the *imported* function itself as a phantom test item in
  `tests/test_heads_falsification.py`'s namespace, which then errored trying to satisfy its
  parameters (`target`, `baseline_features`, ...) as fixtures:
  `tests/test_heads_falsification.py::test_texture_uplift ERROR ... fixture 'target' not found`.
  Fixed by renaming to `evaluate_texture_uplift` in both the module and the test file. Generalises:
  never name a public function under test with a `test_` prefix if the test file imports it by
  name — pytest's collector does not distinguish "imported" from "defined here."

### Learned

Rule 3's "trivial baseline" and the falsification test's H0 null model are the same object here —
worth naming, because it means Rule 3 needed no separate mechanism for this head, just an honest
field.

### Left open

- The week-2 gate is not closed: `tests/test_heads_falsification.py::test_the_falsification_test_has_been_run_on_real_bushveld_data`
  is a placeholder — no public dataset combining assay Cr2O3, pyroxene fraction, a texture
  feature, and locality labels has been identified, and the CGS National Core Library phone call
  (§8 open item) is still not made.
- Not routed through Sbu — this piece is self-contained synthetic-data scaffolding, touches
  nothing of his prior work, and needs no data or machine he has. No PR comment sent for it.

---

## 2026-08-21 — session 11 · N3 measured, twice, and the answer is `NEITHER`

### Attempted

Merge Sibusiso's fix for `experiments/002-s3v2-geometry/run.py` (PR #3,
`fix/pool-signatures-not-raw-frames` on the KHANYA repo) and record the real N3 result it
produced against the actual `S3_v2.zip` archive.

### Worked

- **The pooling bug and its fix, verified before merge.** The original `run.py` concatenated raw
  `(n_angles, n_pixels)` arrays across sections via `np.concatenate`, which requires every
  section to share `n_angles`. The real archive's usable sections range 24–72 frames, so it
  crashed on real data (never hit by the phantom, which is why leg (a) passing didn't catch it).
  Fix: call `harmonic_signature()` once per section at that section's native frame count — it
  already reduces the frame axis to two per-pixel arrays before pooling is needed — then
  concatenate the resulting per-pixel `amplitude_2/floor_2`, `amplitude_4/floor_4` arrays across
  sections and rerun the same selection-and-median rule `harmonic_signature()` uses internally
  (top `MODULATING_FRACTION` pixels by `max(amplitude_2, amplitude_4)`, median SNR over that
  selection). Traced against `src/reefprint/polarim/geometry.py` directly to confirm the pooling
  logic reuses the identical constants (`DETECTION_SNR`, `MODULATING_FRACTION`) and the identical
  `argpartition` selection, not an approximation of it. Tested in an isolated `git worktree`:
  ruff clean, 239/239 tests green. Merged as PR #3 (`gh pr merge 3 --merge`), local `main`
  fast-forwarded `c1e4b83` → `e3a7632`. Confirmed post-merge: 243/243 tests, ruff clean.
- **N3, measured on the real archive, twice, identically.** 29 of 47 sections have real rotation
  data (the other ~18 are single static images — genuinely no acquisition, checked directly, not
  a filename-parsing artefact). 116,000 pixels pooled. 2nd-harmonic SNR 2.5×, 4th-harmonic SNR
  1.1×, `DETECTION_SNR` threshold 5.0×. **Verdict: `NEITHER` clears detection.**
- **`NEITHER` is not neutral.** Extinction depth (stage, 4φ) scales as bireflectance-squared;
  analyser modulation (2θ) scales as bireflectance directly, on a bright S0 — a real signal
  advantage that grows as `2/a` (CLAUDE.md, "the physics"). A null on both harmonics is more
  consistent with a stage rotation buried in noise than an analyser rotation buried in noise,
  because the analyser signal has to be weaker still, relative to its own floor, to vanish the
  same way. Combined with experiment 002's separately measured 38× noise-tolerance gap between
  the two geometries, this leans the open finding toward stage, without closing it.

### Did not work

`uv sync` / `uv python install 3.12` failed reproducibly on Sibusiso's Windows machine
("Missing expected target directory for Python minor version link"), even after a clean cache
retry. Worked around with KHANYA's existing 3.13 venv via `PYTHONPATH`, after confirming
`geometry.py` has no 3.12-only syntax via `ast.parse`. Not yet reproduced here — flagged in case
it recurs; not yet written up in `docs/05-toolchain.md`.

### Learned

A symmetric non-detection (`NEITHER`) on a two-geometry discrimination is not symmetric evidence
when the two geometries' signals scale differently with the same physical quantity — the
asymmetry in *how* each signal degrades is itself informative, and should be stated explicitly
rather than reported as "inconclusive."

### Left open

N3 stays open (not `SECOND`, not cleanly `FOURTH`). Next action: route week-1 leg (b) through
`reefprint.polarim.extinction` (already built and tested) rather than forcing the Stokes
inversion on this archive; re-point KHANYA's ten-mineral symmetry test the same way. See
`CONTEXT.md` §3 and §8 for the full reasoning and the ordered list of what would actually resolve
N3 further. `docs/05-toolchain.md` still needs the `uv`-on-Windows note.

---

## 2026-08-21 — session 12 · a targeted re-run, not a new dataset

### Attempted

Give N3's `NEITHER` verdict a sharper test, per the strategy written into session 11's entry:
if an analyser signal exists at all in S3 v2, it should be least buried on the brightest
grains (2θ modulation scales as bireflectance directly, on a bright S0; 4φ scales as
bireflectance squared). Built `--brightness-quantile` for
`experiments/002-s3v2-geometry/run.py` so this is checkable on Sibusiso's machine without a
new archive.

### Worked

- **TDD'd against a hand-built `HarmonicSignature`, not the real archive** (still not on this
  machine). `test_pool_signatures_can_restrict_to_the_brightest_pixels` constructs 20 synthetic
  pixels, dim half at snr_2 = 2 (below `DETECTION_SNR`), bright half at snr_2 = 6 (above it);
  unrestricted pooling medians to 4 and stays `NEITHER`, restricting to the top half by `dc`
  isolates the bright group and flips the verdict to `SECOND`. Watched it fail first
  (`TypeError: unexpected keyword argument 'brightness_quantile'`), then implemented the
  minimal filter in `pool_signatures` (`experiments/002-s3v2-geometry/run.py`) — quantile the
  pooled `dc` array, keep pixels at or above it, before the existing modulating-fraction
  selection runs.  244/244 tests green (243 → 244), ruff clean.
- **Explicit about what a positive result would and wouldn't mean.** A `SECOND` verdict on the
  brightest-quantile subset is evidence for an analyser signal the unrestricted pool missed —
  not an automatic reversal of N3, since it needs the subset to also be large and representative
  enough to trust. `main()` prints that caveat directly rather than letting a subset flip read
  as a clean overturn.

### Did not work

N/A — this session added a capability, not a fix; nothing was broken first.

### Learned

A `NEITHER` verdict from pooling *everything* can still hide a real signal that only survives
on the most favourable pixels. Testing the favourable subset directly is worth doing before
treating a pooled null as final — but the result has to be reported with its own caveats, or a
subset-level positive quietly becomes a headline the full data doesn't support.

### Left open

The actual command — `--brightness-quantile 0.5` against the real archive — still needs
Sibusiso's machine; this session built and tested the capability, it did not run it. Update
`CONTEXT.md` / this file again once it has.

`docs/05-toolchain.md`'s `uv`-on-Windows note is now written (§1): the failure text, that root
cause wasn't isolated (Developer Mode vs. Defender, untested), the `PYTHONPATH` workaround used,
and what to try if it recurs. Nothing here needed an SBOM change — no dependency changed, only
what to do when the existing one misbehaves on Windows.

---

## 2026-08-21 — session 10 · a third instance, and this one had no gate at all

### Attempted

A deliberate sweep of `trust/` for the same defect class session 8 and 9 fixed — a comparison
that should account for whether *n* can resolve it, and silently doesn't. `split.py` is clean
(pure set logic, no thresholds). `baseline.py` was already fixed in session 9. `abstain.py`'s
`AbstentionAudit.concentrates_at_transitions` was not: a bare
`rate_during_ore_change > rate_when_stable`, comparing two proportions at two different sample
sizes, with **no resolvability check anywhere** — not degenerate at an edge, ungated everywhere.

### Worked

- **Demonstrated the defect before touching the fix.** 1 abstention out of 3 ore-change events
  (33.3%) vs 5 out of 20 stable (25.0%) read as `concentrates_at_transitions = True` — "blind
  spot 1" printed in the summary — despite `noise_during_ore_change` on the same line saying
  ±27.2%. The 8.3-point gap was inside its own printed standard error.
- **Considered and rejected the obvious port first.** The instinct was to reuse the
  single-proportion rule-of-three bound from each side and require the gap to exceed their sum
  — non-overlapping intervals. Traced it against the project's own canonical demonstration
  (2/2 abstained during 2 ore-change events, 0/13 stable) before writing anything: at n = 2,
  `bound_during_ore_change` is already `None` (`3/n >= 1`), so the sum-of-bounds approach would
  return unresolvable there too — silently flipping the headline "blind spot 1, in numbers"
  example from `True` to `False`. Too consequential to do by accident; not attempted.
- **Fisher's exact test instead** (`scipy.stats.fisher_exact`, one-sided `"greater"`). Published
  (Fisher 1922), exact rather than asymptotic, so it does not degenerate at small *n* or at
  p = 0/1 the way the Wald SE does. `scipy>=1.14` was already a declared, licensed dependency
  (BSD-3-Clause) — this is its first live caller in `src/reefprint/`.
- **The canonical example survives, and now says why.** Fisher's exact on the 2/2-vs-0/13 table
  gives p ≈ 0.0095 — significant, `concentrates_at_transitions` stays `True`,
  `test_abstention_concentrated_at_transitions_is_flagged_in_words` passes unmodified. The
  summary line used to read as a contradiction — "n = 2, which resolves nothing" next to "blind
  spot 1: refusals concentrate" two clauses later. It now reads `(Fisher's exact p = 0.010)`
  next to the claim, because the two clauses were always answering different questions (the
  rate's own precision vs. whether the *comparison* is real) and the line never said so.
  `resolves_nothing` was never wrong; it just wasn't the test that mattered.
- **`n_stable == 0` is a real, reachable state.** `audit_abstentions` only refuses
  `n_ore_change == 0`; an all-transition run passes it, and `rate_when_stable` returns its `0.0`
  convention rather than a measurement. `concentration_p_value` returns `None` there — no
  baseline, no p-value — rather than letting the comparison read the manufactured `0.0` as a
  real stable rate.
- **`summary()` gets a third state.** Direction down-or-equal (unchanged wording); direction up
  and significant (`"blind spot 1"` + p-value); direction up but *not* significant or with no
  baseline at all — a new clause, because `"do not concentrate"` there would overclaim safety
  exactly where *n* is weakest, which is the same mistake in the other direction.
- 4 new tests, all watched RED first (`AttributeError: no attribute 'concentration_p_value'`,
  then a live assertion failure showing `"blind spot 1"` printing on the noise scenario), then
  GREEN. 243 tests total (was 239), ruff clean. Full suite and every summary shape printed and
  read by eye — session 8's lesson, applied rather than restated a third time.

### Learned

The pattern from sessions 8 and 9 was "a degenerate value used as a threshold answers the same
way every time and says nothing about it." This one generalises the pattern one step further:
the threshold doesn't have to be degenerate to be missing. Two proportions compared directly,
with no resolvability check *at all*, is the same failure with the edge case removed — it fires
on point estimates at every *n*, not just at the extremes. Worth asking of any remaining
comparison in the package: not just "does this degenerate", but "is there a resolvability check
here in the first place."

### Left open

Nothing new. N3 remains the single next action for the project, unchanged by this session:

```
uv run python experiments/002-s3v2-geometry/run.py --archive path/to/S3_v2.zip
```

---

## 2026-08-20 — session 9 · the same degenerate SE in `baseline.py`, and it was worse there

### Attempted

Session 8's *Left open* flagged `ScoredMetric.noise_at_honest_n` as carrying the same
degenerate-Wald defect that had just been fixed in `abstain.py`, and deliberately did not fix
it in a rule-5 commit. This is that commit. It supersedes that *Left open* item.

Expected a mechanical port of the same three-part repair. It was not one — the same formula
failed **differently** here, and worse.

### Worked

- **In `abstain.py` the defect was loud; in `baseline.py` it was silent.** `abstain` printed
  `±0.0%` on the summary line, which is a visibly wrong number. `ScoredMetric` prints no
  interval at all in that state. What it does instead:

  ```python
  elif (noise := self.noise_at_honest_n) is not None and self.uplift <= noise:
  ```

  At a metric of exactly 1.0, `noise` is `0.0`, so the test is `uplift <= 0.0` — **never true
  for a positive uplift.** The middle verdict, the whole point of rule 3's three-state summary,
  **could not fire.** Measured before the fix:

  ```
  balanced accuracy = 1.000 (n = 12) · majority class 0.500 · metadata-only 0.950
    · +0.050 over the strongest baseline (0.950)
  ```

  Twelve localities out of twelve, against a metadata-only baseline of 0.95, reported as a
  clean win. The rule of three puts the 95% lower bound at **0.75 — below the baseline.** The
  correct reading is "we cannot tell", and it read as a result.

- **The fix, in four parts.** `noise_at_honest_n` returns `None` at exactly 0 and 1 as well as
  outside [0, 1]. New `bound_at_honest_n` is the rule of three (Hanley & Lippman-Hand 1983),
  `None` where `3/n >= 1`. New `resolution_at_honest_n` is the single number an uplift has to
  clear — one SE in the middle, the distance from the point estimate to the bound at the ends,
  which works out to `3/n` at both. `uplift_exceeds_noise` and `summary()` both go through it.

- **The two `None` reasons had to be told apart, and that is the part worth keeping.**
  `resolution_at_honest_n` is `None` for two unrelated reasons: *the question does not apply*
  (an RMSE has no binomial SE) and *the question applies and n cannot answer it* (a proportion
  pinned at an end with n ≤ 3). The old code had only the first case and fell back to the plain
  sign of the uplift, which for the second case is the over-claim all over again. Split with
  `_is_proportion`: not a proportion falls back to the sign as before; a proportion that n
  cannot resolve returns `False`, because no uplift clears a band spanning the range.

- **The coverage mismatch is stated, not hidden.** One SE is about 68%; the rule of three is
  95%. So a metric at an end is judged against a wider band than one in the middle. That is
  written into `resolution_at_honest_n`'s docstring as deliberate and in the conservative
  direction — the ends are where n tells you least, and a perfect score on twelve localities
  is the most flattering thing this class can be asked to report.

- **12 tests, 239 green overall**, ruff and format clean. Ten were watched fail first. The
  other two passed on the first run by design, because they are regression guards rather than
  RED tests: `test_the_middle_of_the_range_is_untouched_by_the_fix` and
  `test_a_perfect_score_that_clears_the_bound_still_reads_as_a_win`.

- **Read the output before calling it done**, which is session 8's lesson applied rather than
  restated. All seven summary shapes printed and checked by eye:

  ```
  1.000, n=12 vs 0.950 → uplift +0.050 ... is inside the 0.250 that n = 12 resolves
                          — 95% lower bound 0.750 by the rule of three
  1.000, n=12 vs 0.500 → +0.500 over the strongest baseline (0.500)
  1.000, n=3  vs 0.950 → uplift +0.050 ... cannot be resolved at all: n = 3 resolves
                          nothing at this end of the range
  0.000, n=12 vs -0.200 → ... is inside the 0.250 that n = 12 resolves
                          — 95% upper bound 0.250 by the rule of three
  0.620, n=12 vs 0.600 → ... is inside the ±0.140 that n = 12 resolves
  0.920, n=40 vs 0.600 → +0.320 over the strongest baseline (0.600)
  4.200, n=12 vs 9.000 → does not beat the strongest baseline (9.000, uplift -4.800)
  ```

  The second line is the one worth checking rather than assuming: a perfect score against a
  weak baseline still reads as a win, correctly, because the 0.750 lower bound is still above
  the 0.500 baseline. The conclusion survives the pessimistic end, which is exactly what the
  comparison against `3/n` is asking.

### Did not work

Nothing failed that was not supposed to. The ten RED tests failed for the stated reasons and
passed after the fix; no existing test needed changing, which is the useful signal here —
`test_noise_is_not_estimated_for_a_metric_that_is_not_a_proportion` asserts `"resolves" not in
summary` for an RMSE and still holds, so the new `_is_proportion` split did not disturb the
case that was already right.

### Learned

**The same bug is not the same bug.** The plan was to port a fix. What actually transferred was
the *diagnosis* — `sqrt(p(1-p)/n)` is zero at the ends — and not the symptom, the severity, or
the repair's shape. In `abstain` it printed a wrong number on a line a human reads. Here it
disabled a branch, and a disabled branch produces no output at all to notice. **The louder
instance was the less dangerous one**, and it was the one that got found first, because it
printed something.

**A degenerate value is most dangerous where it is used as a threshold.** Zero as a *reported*
quantity is a visibly silly interval. Zero as the right-hand side of `uplift <= noise` is a
comparison that always answers the same way, and there is nothing in the output to say so. Both
places used the identical expression. Worth checking the other comparisons in this package
against the same question: not "is this number right" but "what does this comparison do when
this number degenerates".

### Left open

- **N3 is still the single next action.** Nine sessions of guards, none of which touches it.
  One command on Sibusiso's machine:
  `uv run python experiments/002-s3v2-geometry/run.py --archive path/to/S3_v2.zip`
- **`TrivialBaselines` still assumes higher is better**, documented in its docstring and not
  enforced. Unchanged by this session, and now the only *stated assumption* left in this
  module.
- **The rule-of-three band and the one-SE band are different coverages** (95% against about
  68%). Documented as deliberate. If a reviewer objects, the answer is to quote a Wilson or
  Jeffreys interval throughout rather than to widen the middle — but that changes every number
  the package has already reported, so it is a decision, not a tidy-up.
- **Rule 4 is still prose.** These two fixes are rule 4 enforced in the two places that happened
  to compute an interval; nothing yet stops a metric being reported without one. That is the
  remaining placeholder `test_reported_coverage_interval_matches_honest_n`.
- **Still no caller** for `split`, `baseline`, `abstain` or `quantity` beyond the rule-1/rule-5
  seam. Unchanged.

---

## 2026-08-20 — session 8 · rule 5 becomes a type, and the guard is a missing field

### Attempted

Rule 5, the last of the silently-failing rules: *abstention emits a conservative default with a
stated reason, never "unknown."* Same treatment as 1, 2 and 3.

Rule 5 is the odd one out, because the failure it guards against is not a bad input. The other
three refuse something malformed — a leaked split, a bare metric, an unlabelled number. Rule 5's
failure is a system that does exactly what it was told: it abstains, correctly, at a genuine
ore transition, and then **holds the last setpoint**, which at a transition is the worst
available action. Nothing is malformed. Every value is real. The plant runs on the previous
ore's setpoint for as long as the refusal lasts.

So the guard could not be a validator. It had to be an **absence**.

TDD: 37 tests written first, watched fail against `NotImplementedError` stubs, then implemented.
Then four more, after the defect below.

### Worked

- **[`reefprint.trust.abstain`](../src/reefprint/trust/abstain.py).** `Abstention` has three
  fields — `default`, `reason`, `trigger` — and **no slot for a previous value**. Holding the
  last setpoint is not discouraged, it is unreachable: there is nowhere to put it.
  `test_an_abstention_cannot_carry_a_previous_value_to_hold` asserts that against
  `dataclasses.fields`, so re-adding one breaks a test rather than passing review.
  `value_to_act_on(decision)` takes one argument for the same reason — a signature of
  `(decision, previous)` is the whole bug, pre-installed.

- **This contradicts the submitted abstract, on purpose.** The abstract says the system
  "abstains and holds the last-known-good setpoint". `CONTEXT.md` §8 already recorded that as
  deliberate; it is now enforced rather than recorded.
  `test_an_abstention_emits_the_conservative_default_not_the_previous_prediction` is that
  contradiction as a test: steady state reads 0.12, the ore changes, and what reaches the
  controller is 0.90 rather than the held 0.12.

- **`"unknown"` is rejected by name.** Rule 5 names it specifically, so the guard does too:
  `unknown`, `n/a`, `na`, `none`, `error`, `tbd`, `?`, `-`, `--`, case- and space-insensitive.
  A blank reason is also refused. The reason is a required positional field, not an optional
  string that defaults to something polite.

- **Rule 1 meets rule 5 at the seam.** `ConservativeDefault.quantity` is a `Quantity` and is
  checked with `require_reportable()`, so a conservative default derived from a design target is
  refused **at construction**, not on the slide. This is `quantity.py`'s **first real caller** —
  the "nothing calls these guards yet" item that has been in *Left open* since session 6 is now
  half closed.

- **"Conservative" has a direction, and only the inversion is machine-checkable.**
  `ASSUME_HIGH` that emits the low half of its own range is a `ValueError`. The check is against
  the **midpoint**, which is the weakest possible statement of "on the safe side" — deliberately
  not a tuned threshold. *How far* along the safe side is domain judgement and is reported, not
  enforced: pinning defaults to the extreme is how you get operators who switch the system off,
  and that is a 100% abstention rate that never reports itself.

- **`audit_abstentions()` refuses a run with no ore-change events in it.** The only number left
  to report would be the aggregate, and quoting the aggregate is precisely blind spot 1's error.
  A gate that has never been tested through a transition has not been tested.

- **41 tests, 227 green overall** (`uv run pytest -m "not placeholder" -q`), ruff and format
  clean. The two rule-5 placeholders in `tests/test_trust.py` are built, so they were removed
  rather than left claiming `NOT BUILT`; deselected drops 26 → 24. `CONTEXT.md` §4 updated
  186 → 227 in the same commit.

### Did not work

**The 37 tests passed on the first run, and the defect was found by reading the printed line.**
The summary said:

```
abstention rate 13.3% overall · 100.0% during ore change (n = 2, ±0.0%) · 0.0% when stable ...
```

`±0.0%`. The Wald standard error `sqrt(p(1-p)/n)` is **exactly zero at p = 0 and p = 1**, so the
*least* informative observation available — two transitions, both refused — prints as the *most*
precise. That is invented precision, rule 4's exact prohibition, inside rule 5's own summary
line. Small runs land on those extremes constantly; this is not an edge case, it is the common
case early on.

Fixed with the **rule of three** (Hanley & Lippman-Hand 1983: 0 events in n gives a 95% upper
bound of 3/n), which is a published result and therefore satisfies rule 1 rather than being a
threshold chosen here. `noise_during_ore_change` now returns `None` at the extremes instead of
a false zero, and `bound_during_ore_change` covers them. Where even 3/n bounds nothing — n = 2,
where 3/n ≥ 1 — the line says *"which resolves nothing"* rather than printing a number:

```
100.0% during ore change (n = 2, which resolves nothing)
100.0% during ore change (n = 10, 95% lower bound 70% by the rule of three)
  0.0% during ore change (n = 10, 95% upper bound 30% by the rule of three)
 50.0% during ore change (n = 12, ±14.4%)
```

Four tests written for it first, watched fail (`4 failed, 37 passed`), then fixed.

**One of those four tests was wrong, and the implementation was right.** It asserted
`"0.0%" not in summary.split("when stable")[0]`, which caught the *stable* rate of 0.0% — a
correct number — rather than the conditional interval. Retargeted at the conditional
parenthetical. Fixing a wrong test, not bending a test to match code.

**A test of my own was internally inconsistent and would have proved nothing.**
`test_the_inversion_is_refused_in_the_other_direction_too` used `assumed(0.95, "percent", ...)`
against a 0.0–100.0 percent range. 0.95 already sits in the safe half, so a correct
implementation would have passed it. Fixed to `95.0` before implementing against it.

**A one-in-five flake in `test_polarim.py`, not caused by this work.** See *Left open*.

### Learned

**Session 7's boundary claim was wrong by one.** It said *"the four guards now cover every rule
that fails silently — rules 1, 2, 3 and the geometry hazard"* and concluded that was a reason to
stop. Rule 5 fails silently too, and worse than any of them: the others produce a number that is
wrong, this one produces a *plant that keeps running on the previous ore's setpoint* while the
software correctly reports that it has abstained. Nothing in the logs looks wrong. The lesson is
not that the boundary should have been drawn wider, it is that **"fails loudly" was assessed on
the software's output rather than on the process's behaviour**, and those are different
questions.

**Tests do not read output.** All 37 passed and not one of them asked whether the printed
precision was real, because every assertion was about values and refusals — the things a test
author naturally thinks to assert. The interval was rendered, not returned, so it lived in the
one place the suite did not look. Printing the summary and reading it took thirty seconds and
found a rule-4 violation inside a rule-5 guard. **Read the output of anything that formats a
number for a human.**

**The strongest guard was the field that is not there.** Rules 1, 2 and 3 are refusals — code
that runs and raises. Rule 5's core guard executes nothing: `Abstention` simply has no slot for
a previous value, and `value_to_act_on` has no parameter for one. There is no check to skip and
no error to catch, which makes it the only one of the four with no route around it at all. Where
a rule forbids an *action* rather than a *value*, look first for a field to leave out.

### Left open

- **N3 is still the single next action.** Eight sessions of guards, none of which touches it.
  One command on Sibusiso's machine:
  `uv run python experiments/002-s3v2-geometry/run.py --archive path/to/S3_v2.zip`
- **`ScoredMetric.noise_at_honest_n` has the same degenerate-Wald defect** that was just fixed
  here — it returns exactly 0 at a metric value of 0 or 1. That is rule 3's guard, so changing
  it is a separate decision and a separate commit, not something to fold into a rule-5 change.
  Flagged, not fixed.
- **`tests/test_polarim.py::test_recovery_does_not_require_uniform_angular_sampling` failed once
  in five full-suite runs** and passes in isolation, over eight random hypothesis seeds, and in
  four subsequent full-suite runs. The test already skips ill-conditioned draws
  (`cond(design) > 100.0`), so a failure means angles that **pass** the conditioning gate can
  still miss `rel=1e-7` — the threshold and the tolerance are not consistent with each other.
  Not caused by this session's work and not fixed in it. Reproduce with a full-suite run, not a
  single-file one; the draw appears to depend on global RNG state set by earlier tests.
- **Rule 5's second clause is built but has no real data behind it.** `audit_abstentions()`
  computes the conditional rate correctly; nothing yet produces a run of real decisions with
  real ore-change flags to feed it. That needs the OOD gate, which needs segmentation.
- **`abstain` has no caller either**, same as `split`, `baseline` and `quantity` before it.
  The first will be the demo path in `viz/`, which is where a refusal has to be *visible*.

---

## 2026-08-20 — session 7 · rule 1 becomes a type, and provenance is contagious

### Attempted

Session 6's *Learned* named this as the remaining silent-failure rule and said it was the
hardest, which was right. Rules 2 and 3 have a shape a guard can grab: a split is a pair of
sets, a metric is a number next to other numbers. Rule 1 has none. **An invented number and a
measured one are the same 64 bits.** `0.35` is `0.35` whether it came from a calibration run, a
textbook, a phantom, a plausible guess, or a spec for hardware that was never built. There is no
malformed state to detect — the number is fine. What is missing is everything *around* it.

So the guard could not be a check on the value, and this is the point the design turned on: it
had to be a property carried **with** the value, and it had to **propagate through arithmetic on
its own**. Contamination does not surface where the assumption is written. It surfaces three
functions downstream, in a variable named something reasonable like `grain_size_um`, at which
point nobody can tell.

TDD throughout: 30 tests written first, watched fail against `NotImplementedError` stubs, then
implemented. Nothing failed after implementation this time, which is a weaker signal than
session 6's disagreement — see *Learned*.

### Worked

- **[`reefprint.quantity`](../src/reefprint/quantity.py).** `Quantity` carries a `Provenance`
  and a **mandatory non-empty `source`**. Arithmetic keeps the **weakest** input's provenance
  and accumulates every source, deduplicated and ordered, so a derived number can always say
  what fed it. Five ranks:

  ```
  MEASURED  →  CITED  →  STIPULATED  →  ASSUMED  →  DESIGN_TARGET
    a result    published   true of the    a guess,    hardware that was
                value      phantom only    labelled    never built
  ```

- **`STIPULATED` is its own rank and that was deliberate.** Experiment 001's phantom ground
  truth is exactly true — of the phantom, and of nothing else. Folding it into `MEASURED` would
  let the week-1 gate's leg (a) quietly read as mineralogy, which is the exact conflation
  `CLAUDE.md` warns about two lines below the gate table.

- **`require_reportable()` is the boundary**, and `__float__` calls it. `float(q)` is the
  obvious way around any wrapper, so it is the route that had to be closed. A **flagged
  assumption passes** — rule 1 permits assumptions, it requires labels, and by the time you hold
  a `Quantity` it has one. `DESIGN_TARGET` never passes.

- **The number that makes ADR-0002 mechanical instead of a preference.** 47 px × **0.2** µm/px
  is 9.4 µm. 47 px × **1.6** µm/px is 75.2 µm. Same design target, a **factor of 8** apart. That
  is not a measurement with wide error bars; it is a figure that could be 9 µm or 75 µm,
  presented to three significant figures. `test_the_design_target_spans_a_factor_of_eight_so_it_
  is_not_a_number` asserts the ratio is exactly 8.0 and that **both** ends are refused.

- **Bare floats cannot join in.** `measured(1.0, "um", ...) + 2.0` raises `TypeError`, because
  the unlabelled literal is precisely the thing rule 1 is about. Units are checked on `+`/`-`
  and cancel on `×`/`÷` (`px` × `um/px` → `um`), because a scale factor is the usual doorway for
  an unlabelled number, and `px*um/px` in a caption is how it stays in.

- **30 tests, 186 green overall** (`uv run pytest -m "not placeholder" -q`), ruff and format
  clean. `CONTEXT.md` §4 updated 156 → 186 in the same commit, which is now the third session
  running where that number would otherwise have gone stale.

### Did not work

Two things needed fixing rather than accepting:

`_multiply_units` shipped its first draft with a vacuous guard — a loop over
`((right, left, left), (left, right, right))` testing `other is denominator`, which is
`True` by construction on both iterations. It gave the right answer for the wrong reason.
Rewritten to two cases and one condition.

`ruff` caught an en dash in `0.2–1.6 µm/pixel` in the module docstring (RUF002) and an
unescaped `match="CLAUDE.md 0.2-1.6 um/px"` in the test (RUF043 — the `.` are metacharacters).
Both are the same class of thing this module exists to stop: a string that looks right and
means something slightly different.

### Learned

**Nothing failed after implementation, and that is worth noticing rather than celebrating.**
Session 6's value came from a test disagreeing with the code once both existed — the
disagreement was where the third summary state came from. Here the tests and the implementation
agreed immediately, which means either the design was clear before it was written, or the tests
were not adversarial enough. Honest answer: some of both. The tests that would have caught a
weak design are the ones asserting *contagion in both directions* and *`float()` cannot escape*,
and those were written first for exactly that reason. But no test here asked a question the
design had not already answered.

**The four guards now cover every rule that fails silently.** Rules 1, 2, 3 and the geometry
hazard. What is left in prose — rules 4 through 9 — fails *loudly* or fails at review: a missing
CI is visible on the slide, an LLM computing a control value is visible in the code, a
non-permissive licence is visible in the SBOM. That is the boundary, and it is a reason to stop
adding guards rather than a reason to keep going.

### Left open

- **N3 is still the single next action.** Seven sessions of guards, none of which touches it.
  One command on Sibusiso's machine:
  `uv run python experiments/002-s3v2-geometry/run.py --archive path/to/S3_v2.zip`
- **Nothing calls `quantity` yet**, same as `split` and `baseline`. The first real caller is
  `calibrate/` — R% conversion is where cited QDF values meet measured intensities, which is
  the exact seam this type exists for. Written before its caller, deliberately.
- **`Quantity` does not vectorise.** It wraps a scalar. Per-pixel Stokes arrays cannot carry
  provenance this way, and pretending otherwise would be worse than not trying — the array-level
  answer is provenance on the *array*, not per element, and that is a different design.
- **The `higher is better` assumption in `TrivialBaselines`** is still documented, not enforced.

---

## 2026-08-20 — session 6 · rules 2 and 3 stop being prose

### Attempted

Session 5's *Learned* section named the next job and this is it. Rules 2 (locality splits) and 3
(trivial baseline) were paragraphs in `CLAUDE.md`. Both fail **silently** when ignored, which is
the property that makes prose the wrong medium — nothing prompts you to go and re-read a rule
you have already forgotten. Turn both into refusals, the same way `RotationGeometry` and
`LabelProvenance` already work.

TDD throughout: 28 tests written first, watched fail with `NotImplementedError` against stubs,
then implemented. The one test that failed *after* implementation was the interesting one — see
*Did not work*.

### Worked

- **Rule 2 — [`reefprint.trust.split`](../src/reefprint/trust/split.py).**
  `split_by_locality()` is the sanctioned constructor; `require_locality_disjoint()` is the
  backstop for the split someone builds by hand in a notebook, which is the route around any
  constructor. Refuses: a locality on both sides, a section filed under two localities, mixed
  label provenance, a held-out name absent from the data, holding out everything, and a
  single-locality dataset. Unmeasured sections are dropped **and counted** — a skipped section
  has no pixels, and leaving it in inflates the denominator.

  Typed against a `Grouped` Protocol rather than `SectionMeasurement`, deliberately: the failure
  happens at the *patch* level, so a guard that only accepts sections is absent exactly when it
  is needed.

- **The number that justifies it.** 192 synthetic patches, 24 sections, 6 localities, where the
  only signal in the feature is *which section this patch came from* — nothing transferable to
  learn. A 1-NN model scores **MAE 0.0017** under a shuffled patch split and **MAE 0.2119**
  under the honest locality split. **126x**, in the flattering direction, from a model that has
  learned nothing. `test_a_patch_level_split_reports_a_far_better_score_than_the_honest_one`.

- **Rule 3 — [`reefprint.trust.baseline`](../src/reefprint/trust/baseline.py).**
  `ScoredMetric` takes `baselines` as a **required field with no default**, so a metric without
  its trivial baselines is a `TypeError` rather than a slide. Uplift is measured against the
  *strongest* baseline, never the weakest — quoting the gap to majority class while
  metadata-only sits higher is the flattering error, and metadata-only is the baseline that most
  often wins. `NotApplicable(reason)` allows a baseline to be genuinely absent but never
  silently; both inapplicable at once is refused.

- **31 tests, 156 green overall** (`uv run pytest -m "not placeholder" -q`), ruff and format
  clean. `CONTEXT.md` §4 was claiming **86 passed** — stale since before session 5, and exactly
  the kind of number that gets trusted. Now 156.

### Did not work

One test failed after implementation, and it was right to:

```
test_a_metric_that_does_not_beat_the_baseline_says_so_in_words
assert "does not beat" in summary.lower()
E  AssertionError: ... '+0.020 over the strongest baseline (0.600)'
```

The test asserted that 0.62 against a 0.60 baseline should read as "does not beat". The
implementation said it beats it by 0.02. **Both were defensible and both were wrong.** +0.02 is
positive, so "does not beat" is a false statement; and +0.02 at n = 12 is a seventh of one
standard error, so reporting it as an uplift is worse than false, it is misleading in the exact
direction the rule exists to prevent.

Fixing the test to match the code would have been the easy move and the wrong one. Instead the
summary gained a **third state**, which is what the test was reaching for: below the baseline;
above it but inside the noise honest *n* resolves; above it by more than that.

```
balanced accuracy = 0.620 (n = 12) · majority class 0.500 · metadata-only 0.600 ·
uplift +0.020 over the strongest baseline (0.600) is inside the ±0.140 that n = 12 resolves
```

`√(p(1-p)/n)` is the formula this package already quoted for conformal coverage SD — reused, not
invented (rule 1). It returns `None` outside [0, 1], because a binomial SE on an RMSE would be an
invented number. `TrivialBaselines` assumes **higher is better**, which an error-like metric
violates; stated in the docstring as an assumption rather than silently mis-ranking.

### Learned

**Where two guards meet, the seam is where the dishonest number lives.** Rule 3 says report the
baseline. Rule 4 says carry a CI at honest n. Each is satisfiable alone by a report that is still
misleading: a baseline with no sense of scale, or a CI with nothing to compare against. The
number that survives both is the one worth putting on a slide, and it took a *failing test* to
find that seam — writing the assertion first is what produced a disagreement sharp enough to
notice. Tests written afterwards agree with the code by construction.

Two rules down. Rule 1 (never invent a number) is the remaining one that fails silently, and it
is the hardest to make structural, because an invented number is indistinguishable from a
measured one at the type level. The nearest available handle is provenance on the value itself —
the `LabelProvenance` pattern, one level down.

### Left open

- **N3 is still the single next action** and none of this touches it. One command on Sibusiso's
  machine.
- **Nothing calls these guards yet.** They are constructors and backstops with no caller until
  week 2's falsification test, which is the first thing that produces a metric. Guard written
  before the code that needs it, deliberately — the alternative is writing it afterwards, which
  is when the flattering split has already been run once.
- **The `higher is better` assumption in `TrivialBaselines`** is documented, not enforced. If an
  error-like head arrives (grain-size RMSE), that assumption needs a type, not a docstring.

---

## 2026-08-20 — session 5 · ADR-0003 the naming, and the guard that goes on someone else's machine

### Attempted

Three things, none of them physics. Settle what the system is *called*, now that it exists under
two names in two repositories. Get REEFPRINT's history somewhere Sibusiso can read it. And close
the gap between a warning written in `CONTEXT.md` and a check that actually runs.

### Worked

- **[ADR-0003](04-decisions/0003-one-build-two-names-reefprint-and-khanya.md): one build, two
  names.** REEFPRINT leads and KHANYA is the same system's other name; both are correct, neither
  is deprecated. The decision that matters is what it *forecloses*: **no package is renamed and
  no histories are merged.** Renaming `reefprint.*` 42 days out would cost an import sweep across
  two repos and blur the two parallel histories that are the rule-8 originality defence, all for
  a label. *Khanya* is "to shine, to give light" in the Nguni languages, which is a better
  description of the measurement than REEFPRINT is — that is a reason to keep the name, not a
  reason to switch to it.

- **REEFPRINT's history pushed to `Sibusiso-K/KHANYA` as the `reefprint` branch, unmerged.**
  Eleven commits, in one place to read, still separate to authenticate. `git fetch && git
  checkout reefprint`. JOINT-PLAN §5 names merging two architectures in 43 days as the single
  biggest risk; a branch is how you share code without taking that risk.

- **The false negative is now blocked in code.**
  [`Sibusiso-K/KHANYA#2`](https://github.com/Sibusiso-K/KHANYA/pull/2). `src/polarimetry.py`
  called `stokes_from_rotation_series` on raw arrays — bypassing `RotationSeries`, and therefore
  bypassing `require_analyser_rotation()`. It now runs `harmonic_signature()` first and refuses
  the whole run unless the verdict is `SECOND`, returning a report that carries the evidence and
  names the next step rather than `None` or a null result (rule 5).

  Refused at the run, not the section, deliberately: geometry is a property of the acquisition,
  so if one S3 v2 section is a stage rotation then all 47 are, and pooling the other 46 into a
  clean null is the exact failure being prevented.

- **The number that justifies the guard.** Synthetic pyrrhotite-like **stage** series at S3 v2's
  real layout — 72 frames, 5° steps, `r₁=0.40 r₂=0.354`, contrast *a* ≈ 0.12 — fed to the
  rotating-analyser inversion: **median anisotropy 1.5e-02**. A strongly anisotropic mineral,
  reported isotropic, no exception and no NaN. Guard verified both ways at the same layout:
  analyser series 2nd harmonic at **29.1×** its noise floor and 4th at 0.9× → passes; stage
  series 2nd at 1.0× and 4th at **65.3×** → refused.

### Did not work

Nothing failed, but one thing was worse than the previous session recorded. `CONTEXT.md` §3 said
KHANYA imported "a frozen snapshot predating the geometry discriminator". Listing it showed the
snapshot's `polarim/` directory in full:

```
~/Desktop/REEFPRINT - Copy/src/reefprint/polarim/
    __init__.py
    stokes.py
```

No `geometry.py`, no `extinction.py`. Not a stale copy of the module set — an inverter with no
way to check what it was inverting and no fallback for the answer coming back "wrong geometry".
The resolver now searches `$REEFPRINT_SRC` → live checkout → sibling checkout → that snapshot
last, and **rejects any candidate missing `polarim/geometry.py` by name**, because a resolver
that silently falls back to a stale tree reproduces the original bug one layer down.

### Learned

**A warning in a document is not a control.** `CONTEXT.md` already said, in bold, *"do not let
that experiment run before this one does"* — correct, prominent, and worth nothing at 2am on
someone else's laptop. The same sentence as a `raise` costs about forty lines and cannot be
skipped. Where a project rule protects against a *silent* wrong answer, prose is the wrong
medium: the whole hazard is that nothing prompts you to go and re-read the prose.

Generalises to the other standing rules. Locality splits (rule 2) and the trivial baseline
(rule 3) are currently prose in the constitution, and both fail silently when ignored.

### Left open

- **N3 itself is untouched by this.** The guard changes what happens when the archive is the
  wrong geometry; it does not say which geometry S3 v2 is. Still one command on Sibusiso's
  machine, still the single next action.
- **The ten-minute storyboard is a draft, not a running order.** Nine beats exist and are being
  refined. Recorded in `CONTEXT.md` §3 so it does not quietly become the specification —
  gauntlet blind spot 11, where the person who owns the narrative also owns the architecture.
- **The dual name now has to be applied consistently** to the abstract, slides and submission:
  both names on first mention, REEFPRINT alone after. A doc naming only one of them is a defect.

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

## 2026-09-30 — Application work preserved separately
Responsive React/FastAPI application implemented in attached KHANYA worktree, pushed as 63041cb to codex/launch-live-demo / PR15. Physics history is unchanged. Restart instructions: handover/START-HERE-WORKBENCH-2026-09-30.md. Recovery source snapshot: handover/workbench-source-2026-09-30/. Actual model runs and remaining limits are documented there.


## 2026-10-01 — actual tile predictions, spatial tools, voice and evidence assistant

Real inference telemetry replaces the decorative scanning animation. Completed predictor callbacks publish a source-aligned transparent PNG, native analysed-pixel counts, phase fractions, actual completed boxes and coverage. Unknown pixels never enter the progress denominator. The last completed field is outlined; the neural network computes a field/tile together, not a visible pixel-by-pixel reasoning sequence. Full-mode overlapping previews remain preliminary until final logit blending.

The white workbench now has refined typography, phone navigation, a prediction/original comparison slider and a research companion. The local helper explains server-resolved selected evidence, labels predicted/measured/simulated facts and proposes four bounded click-approved tasks. It does not pretend to be an LLM. Optional AIMLAPI/Featherless/Hugging Face/Ollama integrations require server-side configuration and explicit context sharing. No real provider key or live LLM call has been verified. Voice notes offer permission-based browser dictation, editable text drafts and a local recording/download fallback; real microphone transcription remains to be checked in a supported browser.

Spatial now includes an offline metric plan map, scale bar, coordinate query, pan/zoom/fit, corridor-filtered sections, 3D transparency and layer controls. Imported survey points can link to sample images; synthetic geometry is opt-in and labelled. These tools do not reconstruct an orebody from a micrograph. Survey imports remain account-scoped browser-local; notes/results use the existing authenticated backend and private Supabase storage.

## Evidence and tests
- 71 focused backend checks passed, including progress, source/result identity and tenant isolation.
- All seven serial browser tests passed: real-count UI, assistant approval, voice draft flow, provider consent, grain selection, phone/offline layout and spatial tools.
- TypeScript and production build passed. Five new spatial geometry checks passed in the delegated run.
- Actual trained-model inference on publisher test_11 completed in 78.475 seconds on local CPU: six 512px fields, 18.184% source coverage, 55.352% uncalibrated confidence. Result bb0ce7f8188c4da5b07dc0297f7f657d. Live overlays and the assistant were captured from real inference, not mocked predictions. Controlled browser speech/provider fixtures are not real service proofs.
- Actual screenshots and exported result are in Desktop REEFPRINT/handover: real-live-analysis-desktop.png, real-live-analysis-mobile.png, real-result-refined.png, real-assistant-evidence.png, real-progress-result.json.

## Model and deliverables
Active checkpoint remains fb78727d… DeepLabV3/ResNet-50, with recorded 12-section mIoU0.4543 / pixel accuracy0.7716 and magnetiteIoU0. The stronger approved de7135a9… weights have not been recovered on this host. No new test accuracy or recovery improvement is claimed. The guarded Process simulator continues to HOLD the unapproved live model. A separate OPC UA engineering fixture demonstrated0→1; it must not be represented as this live model's successful plant actuation. The three-phase demo and checkpoint-bound report remain available, with limits visible.

Both extended-dice and small-grain-dice Kaggle runs changed from RUNNING to COMPLETE during this release. Their validation audit is a separate report; do not deploy weights or infer held-out test improvement from validation alone.


Continuation: LIVE-UI-RELEASE-2026-10-01.md. Public restart and GitHub publication are verified separately below.


### Publication and live verification — 1 October 2026
Implementation commit0e2255c and merged release93729da pushed to KHANYA PR15. Collaborator commits3e68f12..a719efe retained, including model warmup and measured per-stage timing. Actual preview/count logic remains the common source for provisional phase aliases; unknown pixels stay excluded. Production bundle regenerated after resolving source/generated conflicts.

Post-merge:72 backend checks passed, two relevant desktop/mobile browser rechecks passed; earlier complete seven-browser suite passed. Public/health returned200, cloud_sync/auth_required true and warmed model_ready true; signed-out samples/assistant returned401. Existing user signed-in browser visibly loaded new UI and completed fresh public six-field inference in92.2s, then opened the evidence companion. Local8510 and public8766 restarted. Current process IDs:24020(local),5340(public); exec sessions43430 and18268. QA8770 is separate and can be stopped after use. Temporary tunnel remains the approved existing address.

GitHub workbench API, offline frontend and security checks passed. Base tests initially failed collection because one new API fixture imported optional FastAPI unconditionally; importorskip added to match other API fixtures, while dedicated API CI continues exercising it. CI after that correction must be checked; do not imply all checks are green until observed.

Both extended training runs audited COMPLETE. Native validation foregroundIoU0.6467023, allfiveIoU0.7036325, magnetiteIoU0.4094622/recall0.6948409. Smallgrain is weaker and regresses pentlandite. These are validation scores from selected checkpoints, not test accuracy or production gains. Native epoch12 chosen before a one-off test evaluation; the evaluation-only notebook is being reviewed/launched separately. Active hosted weights/report/gates are unchanged. See reports/EXTENDED-TRAINING-AUDIT-2026-09-30.md.

Sibusiso's eight open PR heads remain unchanged; author acknowledges retired Streamlit UI on19–22. Existing correctness and stacked-base review blockers remain; no duplicate comments or unsafe merge performed. See reports/PR-AUDIT-2026-10-01.md. Optional provider model options are documented; no key or real microphone/LLM call has been verified. An additional provider metadata check hit the approval service usage limit and was not bypassed.


## 1 October2026 — candidate test evaluation completed; assistant reading fix
Single private native-selected-test-20261001-v1 evaluation completed; two independent audits matched all12section matrices,103,795,344pixels, every score and source/checkpoint/protocol identity. Candidate42646cfa testmIoU0.632038, foreground0.577958, accuracy0.855093. MagnetiteIoU0.247730/recall0.893240/precision0.255289 exposes2,140,808FP; historical common-phase regression remains. Candidate not deployed or control-approved. Reports/reproduction artifacts copied, no images/weights/secrets. Completed training monitor deleted. Read CONTINUE-REEFPRINT-2026-10-01.md for facts and limits.
AllfourCIchecks passed9674b29 and2b763b2. The assistant now retains readable answer beginnings via internal conversation scrolling; three focused browser checks andproductionbuild passed. Fresh signed-in public UI returned the active model's correct report; actual screenshot saved privately onDesktop. Existingtemporarytunnel/auth scope preserved. Candidate report runtime/UI verification will be recorded after completion.
