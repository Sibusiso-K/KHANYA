# Plan: REEFPRINT Live v6: a real-data, industry-grade belt-to-decision showcase
_Round 2 revision by Claude (Opus 5.5), 2026-10-01 20:25 SAST, after Codex (gpt-6-astra) rounds 1 (26 findings) and 2 (12 findings), both REVISE. Changes are marked **[R1]** / **[R2]**._

## Goal

Make the Top-5-round showcase **real, correctly evaluated and safe**. **[R1]** It is framed as **three separately labelled evidence tracks**, not one joined result:

| Track | Data | What it shows | What it does not show |
|---|---|---|---|
| **T1 Belt (hyperspectral)** | HIDSAG, Chilean porphyry Cu-Mo | Lab results and QEMSCAN mineralogy predicted from spectra, with honest intervals, absorption maps, decisions, and a lab round trip | PGM ore; a live belt |
| **T2 Microscope** | LumenStone S2, Norilsk | Phase segmentation, liberation; a pentlandite-specialist *experiment* | PGE assay, Bushveld performance |
| **T3 Plant** | Kaggle flotation plant, Brazil iron ore, CC0 | How a model output maps to real plant parameters and a forecast ahead of the lab assay | That image-derived mineralogy improves a plant decision. That needs paired pilot data, which is the ask |

The joined claim (belt + microscope + plant on the same ore) is reserved for the pilot.

## Releases **[R1]**

- **R-1 (core, must ship):** T1 frozen replay with correctly evaluated intervals, absorption/cluster maps, the 3D data cube, a deterministic decision policy, and a typed lab-reconciliation and export round trip. Audit log, security baseline.
- **R-2:** the T3 plant replay as its own view; the T2 specialist as a validation-only experiment (no promotion).
- **R-3:** the AI assistant (LLM routes, templates speak), and phone/camera mode as a **quality-and-refusal demonstration** (no ore predictions from arbitrary photos).

The user asked for R-3 explicitly. It ships under the constraints below, after R-1 and R-2 are green.

## Data and permissions **[R1]**

| ID | Data | Permission | Use | Shipping |
|---|---|---|---|---|
| D1 | HIDSAG GEOMET, MINERAL1 | CC0 (Figshare) | T1 | Derived assets may ship |
| D2 | HIDSAG RGB renders | CC0 | RGB-model comparison (matched modality) | May ship |
| D3 | Kaggle flotation plant | CC0-1.0 (read from dataset metadata, 2026-10-01) | T3 | May ship derived hourly data |
| D4 | LumenStone S2 | Written research grant; **redistribution and commercial rights not established** (S2 protocol) | T2 experiment | **No S2 images or weights shipped in this app** |

No public labelled PGM or UG2 image set was found, so none is claimed. T2 wording: **"PGM-relevant base-metal-sulphide discrimination on Norilsk sections."** Pentlandite is a Pd host, but identifying it measures neither Pd nor discrete PGMs nor PGE recovery.

## Approach

### A. T1 belt models v6 (Kaggle, CPU)

1. **Strict nesting [R1].**
   - Every data-dependent step is fitted only on the inner-training partition of each inner fold: scaling, k-means, PLS components, ridge alpha, ET settings and blend generation.
   - Inner splits are grouped by composite wherever groups exist (MINERAL1); the PLS comparator is grouped too.
   - Outer folds: GEOMET KFold(5) (no group key exists; stated). MINERAL1 GroupKFold by composite.
2. **Model families.**
   - v5 nonlinear (ET on normalised spectra, band depths, clusters).
   - **Linear-in-reflectance**: ridge or PLS on mean reflectance on the common grid, standardised inside the fold.
   - For additive targets, the linear family with **blend augmentation**: synthetic areal mixtures of pairs of samples from the *same inner-training partition*; both parents' composites are absent from validation.
   - The nested inner CV picks one per target.
3. **Claims about blends [R1].**
   - "Affine-consistent under a synthetic areal-mixture model (pixel share standing in for mass share)" only.
   - Blend evaluation pairs parents from the outer test fold, and **resamples parents, not generated mixtures**.
   - No physical-blend claim without measured mixtures.
4. **Intervals [R2]: split-conformal with a calibration partition set aside before any selection.**
   - **(a) Split first.** In each outer fold, the outer-training set is first split into **proper-training** (~70% of units) and **calibration** (~30% of units).
     - Units are composites for MINERAL1 and samples for GEOMET.
     - The split is seeded and grouped.
     - All model-family choice, hyperparameter search, inner CV, k-means, scaling and blend generation run **only inside proper-training**.
   - **(b) One frozen model.** The single model selected and fitted on proper-training is used for:
     - calibration scores;
     - the displayed prediction;
     - the interval centre;
     - the explanations.

     The same model also produces the deployable-pipeline accuracy that is reported.
   - **(c) Scores.** One conformity score per calibration unit:
     - GEOMET: |y − ŷ| per sample.
     - MINERAL1: max |y − ŷ| over the size fractions of the composite. The coverage event is *all fractions of a composite covered* (simultaneous within-composite coverage), stated in the app.
   - **(d) Quantile.**
     - k = ⌈(n_cal + 1)(1 − α)⌉ using the fold's actual n_cal.
     - If k > n_cal, the interval is **unbounded** and shown as "not enough calibration data".
     - α = 0.2: 80% is a chosen trade-off between width and achievability at these n, not because 90% is impossible. Actual fold counts are reported.
   - **(e) Coverage on the outer-test units**, per target. Uncertainty is **Clopper–Pearson at the unit level** (boundary-safe), with the dependence caveat (shared CV fits; unknown GEOMET localities) stated beside it.
   - **(f) Separate accuracy evaluation.** For the v6-vs-v5 comparison only, a full-outer-training refit is scored. It is labelled "accuracy evaluation". The app shows only the deployable conformal pipeline from (b).
5. **Baselines [R1].**
   - Training mean, **training median** (natural for MAE), and a **metadata-only baseline** where metadata exist: MINERAL1 size-fraction tag and process line, as group medians.
   - Uplift is measured against the strongest baseline (rule 3).
6. **Comparison v6 vs v5 [R1].** Same outer folds.
   - Paired per-sample errors are aggregated to the group level (composite; sample for GEOMET).
   - **Gates:**
     - (a) paired cluster-bootstrap 95% CI of the MAE difference excludes 0;
     - (b) Wilcoxon signed-rank on group-level paired differences, p < 0.05 after **Holm correction across targets within a record**;
     - (c) paired effect size reported (matched-pairs rank-biserial);
     - plus the doctrine's Mann-Whitney and Cliff's delta, kept as additional reported gates.
   - "Better" requires all of them.
   - **Exploratory label:** v6 was designed after reading v5's out-of-fold failures and reuses the same folds.
7. **Explanations [R2].**
   - **Wavelength-region occlusion with the full pipeline recomputed.**
     - Raw pixel spectra are partitioned into contiguous, non-overlapping wavelength regions per sensor:
       - VNIR 410–700 and 700–990;
       - SWIR 1010–1350, 1350–2000, 2000–2250, 2250–2400 and 2400–2490.
     - For each region, replace the sample's raw pixel values in that region with the proper-training mean spectrum. It is scaled to the sample's brightness outside the region, so the occluded spectrum stays physically plausible.
     - Then recompute **every** derived feature (normalisation, gradients, band depths, cluster fractions) and record Δprediction.
   - Brightness and cluster ablations are reported separately as overlapping feature diagnostics, not as part of the partition.
   - Phrasing is "the model's prediction depends most on the 2000–2250 nm region (Al-OH absorption)": an association, not a mechanism, and non-additive.
8. **Absorption and cluster maps (the computer vision layer) [R1].**
   - Per sensor, never a fabricated joint pixel: SWIR continuum-removed depth maps at Al-OH ~2.2 µm and Mg-OH/CO₃ ~2.33 µm; VNIR Fe³⁺ ~0.9 µm depth; the k-means cluster map (training-fold fit) per sensor.
   - **No per-pixel mineral prediction maps.** A sample-level model projected onto pixels does not locate minerals.
9. **Showcase selection [R1].**
   - Pre-registered and written before export: the first 24 GEOMET and 12 MINERAL1 samples in sorted order of a seeded hash of the sample id. They are not chosen by result.
   - Compact cubes per sensor (≤ 64×128, ~60 bands, uint16, gzip), ≤ 25 MB total.

### B. T3 real plant parameters (local) **[R1 rewritten]**

1. **Timestamps.**
   - Each 20 s row has a sample timestamp. Lab values are hourly and repeated across rows.
   - **Assumed availability delay of the lab assay: 2 h after the sample hour.** Flagged ASSUMPTION; a sensitivity run uses 1 h and 4 h.
2. **Features at issue time t:** completed hourly bins (t−1h, t] of process tags, plus as-of-joined lab values available by t (sample hour ≤ t−delay).
   - The target is silica at clock time t+h (h = 1, 3 h). Missing hours are not row-shifted.
   - % iron concentrate is excluded at any time after t−delay.
3. **Periods.** Train Mar–Jun, tune Jul, calibrate Aug, test Sep, frozen before Sep, with purged 12 h gaps between periods.
4. **Baselines:** persistence (last available lab silica), training mean and median.
5. **Intervals:** split-conformal from August. On September, report **rolling coverage and width** with **block bootstrap** (24 h blocks). Serial dependence and drift are stated.
6. **Decision support only.** Above-spec forecasts surface the top occlusion groups of tags, labelled correlational, with "controlled trial needed". The spec limit is a stated ASSUMPTION, not a site rule.

### C. RGB and phone **[R2]**

1. **Matched-modality comparison from identical source pixels.**
   - RGB is rendered from the same per-sample pixel pool as the hyperspectral features, using a fixed, documented operator: Gaussian band integration at 460 / 540 / 620 nm, FWHM 100 nm. This is a simulated RGB camera.
   - Same folds, same model families, same tuning budget.
   - HIDSAG's own RGB renders are not used for the comparison: they come from a different crop and aggregation.
2. **Phone or webcam in the app: quality gates only.** Focus (Laplacian variance), exposure clipping, and a user-marked grey-card patch (mean and spread within bounds).
   - **No domain-distance score and no ore prediction.** The outcome is always "outside the validated domain → route to the lab or microscope", with the failed or passed checks listed.
   - A labelled camera-domain dataset is the stated prerequisite for predictions.
3. **Spectral OOD (T1 only).**
   - Ledoit–Wolf shrinkage on proper-training PCA scores (k ≤ 10).
   - The threshold (p95 = borderline, p99 = refuse) is set on the **calibration partition**.
   - Evaluated on the **outer-test units**: false-refusal rate, and acceptance of shifted inputs (MINERAL1 plant-feed spectra and GEOCHEM spectra presented to the GEOMET model). Calibration and evaluation units never overlap.

### D. T2 pentlandite specialist (Kaggle GPU, experiment only) **[R1]**

- Run on the audited scaffolding: 6 reused validation sections, no test evaluation, 2 h cap.
- Report pentlandite and pyrrhotite IoU / precision / recall and the confusion against 42646cfa, as **exploratory**.
- **No routing override, no promotion.** A fused-model evaluation across all phases, recalibration and independent specimens are listed as prerequisites.

### E. Decision policy: deterministic, frozen, a total table **[R2]**

**Per-target adverse direction:**

| Target | Adverse direction | Named review action |
|---|---|---|
| Cu recovery | low | Send the sample to the microscope; review the collector dose |
| Mo recovery | low | Notify the moly circuit |
| Lime consumption | high | Review lime pre-dosing |
| Bond WI | high | Review the feed rate with the control room |

pH is not displayed (it does not beat the baseline under the gates).

**Thresholds:** t_adverse = the proper-training p25 (low-adverse) or p75 (high-adverse). Labelled illustrative.

**Per-target state** (interval [lo, hi]; boundaries are inclusive on the adverse side):

| State | Low-adverse target | High-adverse target |
|---|---|---|
| **clear** | lo > t | hi < t |
| **crossing** | lo ≤ t < hi | lo < t ≤ hi |
| **adverse** | hi ≤ t | lo ≥ t |

- A favourable interval (entirely on the good side) counts as **clear**.
- An unbounded interval counts as **crossing**.
- A missing target is **missing**.

**Inputs:**
- **OOD score s:** s ≤ p95 → pass; p95 < s ≤ p99 → borderline; s > p99 → refused.
- **Data freshness:** fresh / stale (older than a stated window).

**Decision table (evaluated top-down; the first match wins):**

| # | Condition | Decision |
|---|---|---|
| 1 | refused **or** stale | **Conservative default — review only**: route to the lab / microscope |
| 2 | ≥ 2 targets *adverse* | **Conservative default — review only**: list every named review action for the adverse targets |
| 3 | 1 target *adverse* | **Verify**: that target's named action |
| 4 | any *crossing* **or** any *missing* **or** borderline | **Verify**: name the uncertain targets |
| 5 | otherwise (all clear, OOD pass, fresh) | **Act**: continue at setpoint; next microscope check on schedule |

Policy version, thresholds, OOD bands and hashes are written to every audit record. Unit tests cover every row and every boundary.

### F. App: REEFPRINT Live (belt-monitor v3, workbench design, 3 themes)

1. **Labelled as a replay of precomputed out-of-fold results [R1].** Runtime inference is a roadmap Python service, and no browser-side model execution is claimed.
2. **Live scan view.**
   - The real per-sensor cubes stream line by line, with selectable absorption or cluster maps and the spectrum under the cursor.
   - When the scan completes, predictions are revealed with their **split-conformal 80% intervals**, the occlusion reasons, and a decision per role.
3. **3D data cube** built from real faces of the cube.
4. **Plant view (T3).**
5. **Typed lab round trip [R1][R2].**
   - A **versioned target registry** (`targets.json`) covers every displayed target. Each entry has:
     - id and analyte type: mineral_wt% | element_wt% | oxide_wt% | phase_wt%_xrd | recovery_% | reagent_kg_per_t | work_index_kWh_per_t;
     - permitted units with explicit conversions (e.g. g/t ↔ kg/t);
     - basis (dry mass / image area);
     - size-fraction semantics.
   - Import CSVs follow a bounded schema: `sample_id, target_id, value, unit, basis, size_fraction, revision, timestamp`, validated against the registry.
   - A **round-trip test** exports every displayed target, re-imports it, and requires identity.
   - Incompatible joins are rejected (mineral vs element, area vs mass, dry vs wet, size fraction mismatch, duplicates, unmatched ids), each with a reason.
   - Reconciliation shows MAE and bias, labelled **retrospective** (reused HIDSAG labels).
   - Exports: LIMS CSV (with formula neutralisation), provenance JSON, an OPC UA tag-map CSV (not a live server), and the GeoJSON / join table with **null geometry** plus a `source_location_id` left for the fleet system.
6. **Audit log [R1]:** every outcome — prediction, refusal, invalid input, failed import, stale data, interrupted scan, provider failure. Each record carries input / model / calibration / policy hashes.
7. **Safety [R1].**
   - Imported strings are rendered with `textContent` only; sample ids are validated by regex.
   - Imported content is never sent to an LLM as instructions.
   - Exports neutralise leading `= + - @`.

### G. AI assistant (R-3) **[R2]**

1. **The LLM is a router only.**
   - Its input is **only the user's typed question plus the trusted tool schema**. No imported content, no tool results, no data values, no history containing them.
   - Its output is one allowlisted tool name plus typed arguments.
2. **Arguments are validated independently of the model:**
   - sample ids must exist in the loaded data and match the regex;
   - views are from an enum;
   - `export` and `generate_report` require a user click to confirm.
   - Invalid → "I can't do that", with the reason.
3. **All answers are rendered by deterministic, approved templates** from typed tool output. **No free-form LLM text is ever shown.** The model only chooses the template, through the tool it picks.
4. **Server (`server.py`, stdlib):**
   - binds 127.0.0.1; checks Host / Origin; a per-run session token is embedded in the served page;
   - static allowlist (no listing, no symlinks);
   - upstream allowlist (`api.aimlapi.com`, `api.featherless.ai`); timeouts; max tokens; rate limit and a daily cap;
   - sanitised errors; the key is never logged or returned.
   - Env vars: `REEFPRINT_LLM_PROVIDER`, `REEFPRINT_LLM_MODEL`, `AIML_API_KEY` / `FEATHERLESS_API_KEY`.
5. **Offline:** a deterministic intent parser routes to the same tools.

### H. Acceptance criteria [R1]

- Every reported number reproduces from a script, and the result JSONs are hashed in the BUILDLOG.
- Per-target interval coverage with cluster CIs.
- v6 vs v5 gates per target, plus Holm.
- Plant: rolling coverage on September, and the persistence baseline beaten or not, said either way.
- Measured app load time and peak memory on the showcase assets.
- A failure-path test list run: missing bands, NaNs, bad CSV, stale plant data, provider down, offline.
- Server security checks: wrong Origin → 403, no token → 401, path traversal → 404.

## Key decisions & trade-offs (contestable)

1. Absorption and cluster maps, not model-projected mineral maps. Less flashy, defensible.
2. Split-conformal with calibration set aside before selection, 80% as a chosen width/achievability trade-off; unbounded intervals shown honestly when calibration is too small.
3. The phone is refusal-only; there are no predictions until camera-domain labels exist.
4. The LLM routes and templates speak. Less "chatty", but no invented numbers.
5. Three labelled evidence tracks; the joined claim waits for the pilot.
6. A replay of precomputed results, not live browser inference: honest and offline.

## Risks / open questions

- Strict nesting multiplies compute (k-means and ET inside inner folds): estimate ~40–60 min on Kaggle CPU.
- Calibration sets are tiny (MINERAL1 ~8–10 composites per fold), so intervals may be wide or unbounded. That is the honest result, and it is shown as such.
- The plant data's lab delay is unknown; sensitivity runs bound it.
- Cube registration between sensors is unverified, so there are no joint pixels.

## Out of scope

- Live OPC UA server; real belt hardware.
- Any change to the KHANYA live app or worktree.
- Real geospatial coordinates.
- PGM-ore hyperspectral claims; promotion of the specialist; phone-photo ore predictions.
- Deck rebuild (later).
