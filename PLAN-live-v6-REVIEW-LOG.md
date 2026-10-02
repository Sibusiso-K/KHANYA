# Plan Review Log: REEFPRINT Live v6 — real-data belt-to-decision showcase
Started 2026-10-01 20:00 SAST. MAX_ROUNDS=3. Critic: Codex gpt-6-astra (read-only, reasoning effort high per ~/.codex/config.toml). Builder/arbiter: Claude Opus 5.5.

## Round 1 — Codex (gpt-6-astra)

The plan has material problems in uncertainty, physical interpretation, specialist promotion, and security. I reviewed the requested repository files; no files were modified.

1. **A4 — “OOF residuals” does not specify CV+.** CV+ requires predictions from each corresponding fold model at the new input, combined with that fold’s residuals and finite-sample quantiles. Evaluating intervals on the same records used to construct them can leak labels even when the point predictions are OOF. Its worst-case guarantee also differs from nominal coverage. [Original paper](https://arxiv.org/pdf/1905.02928).  
   **Fix:** Specify the complete interval algorithm and evaluate the entire fitting/calibration procedure inside an additional untouched outer split; grouped split-conformal is simpler.

2. **A4, key decision 3 — The proposed binomial coverage CI uses an unjustified independence assumption.** MINERAL1’s 99 records are clustered within 36 composites; GEOMET’s 146 samples are not 146 established independent localities. Pooling targets adds further dependence. Grouped folds alone do not solve this.  
   **Fix:** Define coverage per target and sampling unit, use appropriate cluster uncertainty, report actual calibration-group counts, and explicitly qualify unknown locality dependence.

3. **A2–A3 — “Nested choice as in v5” inherits incomplete nesting.** In [run_v5.py](/C:/Users/USER/Desktop/REEFPRINT/training/hidsag-v5-belt-20261001/run_v5.py:390), k-means sees the inner validation inputs; the PLS comparator uses ungrouped `cv=4`, and `RidgeCV` does not respect composite groups. Creating blends before inner splitting would additionally leak parent labels.  
   **Fix:** Fit clustering, scaling, hyperparameters, and blend generation strictly within every inner training partition, keeping both parents and their composites outside validation.

4. **A3, G — The inherited “three gates” are statistically mismatched.** [v5’s gate](/C:/Users/USER/Desktop/REEFPRINT/training/hidsag-v5-belt-20261001/run_v5.py:332) applies independent-sample Mann–Whitney to paired errors and ignores composites in that test; Cliff’s delta is likewise an unpaired effect. Testing many minerals introduces multiplicity, and synthetic blends sharing parents are not independent observations.  
   **Fix:** Use paired composite-level inference, report paired effects, control multiplicity for improvement claims, and resample blend parents rather than generated mixtures.

5. **A3, C1, G — The baselines and selection policy can flatter the result.** Rule 3 requires metadata-only comparisons; mean-only comparisons omit the median baseline natural to MAE. “Skill kept” against a richer hyperspectral pipeline confounds modality with model/features. v6 is also designed after inspecting v5’s OOF failures.  
   **Fix:** Add median and available metadata-only baselines, match modality comparisons, preregister targets/showcase selection, and describe reused-fold improvements as exploratory.

6. **A1 — Affine consistency does not “fix blended ore by design.”** It proves \(f(\lambda x+(1-\lambda)z)=\lambda f(x)+(1-\lambda)f(z)\), including when both predictions are wrong. Pixel share need not equal dry-mass share; the [existing app builder](/C:/Users/USER/Desktop/REEFPRINT/presentation/belt-monitor/build_data.py:161) already labels that assumption.  
   **Fix:** Claim only consistency under a specified synthetic areal-mixture model and reserve physical blending claims for measured mixtures with known mass fractions.

7. **A6 — There is no defined joint VNIR–SWIR pixel input.** v5 independently pools and samples the two sensors, discarding spatial correspondence. HIDSAG’s cameras have different spatial resolutions, so concatenating arbitrary pixels would fabricate a spectrum. [HIDSAG methods](https://www.nature.com/articles/s41597-023-02061-x).  
   **Fix:** Verify registration and common spatial support for each crop, or display separate sensor maps without claiming a joint per-pixel prediction.

8. **A6 — Mean consistency is not mineral-map validation.** A sample-level sulphide predictor can exploit associated gangue; projecting it onto pixels does not locate that sulphide. Negative or over-100% outputs are possible, while clipping or renormalizing them generally destroys the claimed mean identity.  
   **Fix:** Present these as exploratory model-response maps, retain raw values for consistency checks, and use absorption/cluster maps as the main spatial evidence.

9. **A3 versus A5–A6 — The displayed explanation may explain the wrong model.** Nested selection can choose extra-trees or the nonlinear family, while the proposed reasons and pixel maps come from the linear family. A linear map’s mean then need not equal the displayed prediction.  
   **Fix:** Bind every prediction, explanation, interval, and map to its exact fitted model; clearly separate optional linear-surrogate diagnostics.

10. **A5 — Spectral contributions can become unsupported mineralogical explanations.** Standardized coefficients require standardized deviations; overlapping spectral groups can double-count. Correlated wavelengths make “top two” rankings unstable, and “VNIR Fe” does not establish an iron-related causal mechanism.  
    **Fix:** Verify intercept-plus-contributions reconstruction, use an exhaustive non-overlapping partition, and phrase results as model associations with wavelength regions.

11. **A7, E, F — The deployment computation is missing.** A static app plus a stdlib LLM proxy does not specify how uploaded photos or cubes execute ridge/ET models, preprocessing, OOD scoring, or CV+. The compact cube also differs from v5’s 266-band features and pooled spatial support.  
    **Fix:** Specify one inference runtime and versioned preprocessing contract, with numerical parity checks; otherwise label the experience as replay of precomputed results.

12. **B1–B4 — Hourly aggregation does not establish information availability.** A lab value timestamped at \(t\) may become available later; an hourly mean labelled \(t\) may include observations after the forecast issue time. Missing hours also make row shifts different from one- or three-hour forecasts.  
    **Fix:** Define sample, availability, and forecast timestamps; use as-of joins, completed time bins, explicit delay assumptions, and clock-based horizons.

13. **B6 — There is no clean calibration block, and time-series coverage is overstated.** August selects the model; reusing it for calibration compromises the usual split-conformal argument. Serial dependence and plant drift remain after a six-hour boundary purge. September hours are not independent Bernoulli coverage trials.  
    **Fix:** Separate chronological tuning and calibration periods, freeze before September, and report rolling coverage/width with block-based uncertainty and explicit dependence assumptions.

14. **C — A clicked grey patch cannot validate a phone prediction.** HIDSAG renders do not establish smartphone colour response, exposure, gamma, scale, background, or illumination equivalence. An arbitrary clicked pixel can satisfy the gate, and an accepted photo still has no demonstrated interval coverage.  
    **Fix:** Make arbitrary-photo uploads a quality/refusal demonstration until a labelled camera-domain dataset supports predictions and intervals.

15. **C2, E — Mahalanobis OOD is underspecified and potentially singular.** The current spectral grid has 266 features versus 146 GEOMET samples or 99 MINERAL1 records, so ordinary sample covariance cannot be inverted. Training-distance percentiles also do not establish detection performance on unseen domains.  
    **Fix:** Use training-only dimensionality reduction or shrinkage, calibrate thresholds on held-out groups, and measure both false refusals and acceptance of unsuitable inputs.

16. **D2 — Six reused sections are not an independent significance test.** The [audited protocol](/C:/Users/USER/Desktop/REEFPRINT/training/ensemble-validation-20261001/deeplab-seed43/protocol.json:194) explicitly states that these sections select checkpoints, locality independence is unestablished, and single-run gains are exploratory. Adding section-level gates does not undo adaptive selection.  
    **Fix:** Keep the specialist a validation-only candidate unless a frozen evaluation on genuinely independent specimens becomes available.

17. **D3, E — Specialist confidence cannot safely authorize overrides.** Pentlandite-centred sampling changes class prevalence; Dice/Focal outputs are not automatically calibrated probabilities. Binary “rest” is not specifically pyrrhotite, and a gain in standalone pentlandite IoU need not improve the fused segmentation. Existing general-model conformal calibration does not transfer to the router.  
    **Fix:** Freeze the routing rule, evaluate the complete fused model across all phases and absent-class sections, and independently recalibrate before promotion.

18. **Data/D — The PGE claim exceeds the labels.** Pentlandite is a relevant Pd host, but identifying it does not measure Pd content, discrete PGMs, or PGE recovery; published Bushveld work distinguishes these forms explicitly. “Hardest” is also unsupported without a comparative confusion analysis. [Primary mineralogical study](https://www.researchgate.net/publication/266938467_Mineralogical_siting_of_platinum-group_elements_in_pentlandite_from_the_Bushveld_Complex_South_Africa).  
    **Fix:** Say “PGM-relevant base-metal sulphide discrimination on Norilsk sections,” with no implied PGE assay or demonstrated Bushveld performance.

19. **Data — “All licence-checked” contradicts the audited shipping status.** The [S2 protocol](/C:/Users/USER/Desktop/REEFPRINT/training/ensemble-validation-20261001/deeplab-seed43/protocol.json:208) expressly leaves dataset and pretrained/derived checkpoint redistribution or commercial rights unapproved. A research-use grant is not evidence of assignability to Mintek.  
    **Fix:** Separate private research permission from shipping rights and attach artefact-specific permission evidence before distributing images or weights.

20. **Goal, B, F — The claimed end-to-end system consists of disconnected demonstrations.** HIDSAG ore measurements, Norilsk micrographs, and Brazilian plant tags are not paired observations. The plant sensor does not establish that image-derived mineralogy improves a plant decision, and CSV exports do not demonstrate delivery to plant systems.  
    **Fix:** Label the three evidence tracks explicitly, demonstrate a concrete local export/import round trip, and reserve the joined performance claim for paired pilot data.

21. **E — The decision policy remains undefined.** “Act / verify / default” lacks target thresholds, interval-crossing rules, conflicting-signal handling, stale-data behaviour, and approved conservative actions. The current builder derives quartiles from all true labels, including evaluation records; these are illustrative thresholds, not independent operational rules.  
    **Fix:** Freeze a deterministic policy using training-only or explicitly assumed thresholds, with interval-aware refusal and review-only defaults until site procedures exist.

22. **F5 — Reconciliation can silently compare incompatible quantities.** QEMSCAN mineral wt%, XRF elements/oxides, XRD phase fractions, and image-area fractions are not interchangeable. Duplicate IDs, size fractions, dry/wet basis, revisions, and unmatched specimens can invalidate MAE; shuffled showcase samples cannot establish temporal drift.  
    **Fix:** Enforce typed analytes, units, basis, sample/composite keys and timestamps, reject incompatible joins, and label reused HIDSAG labels as retrospective reconciliation.

23. **F7, risks — The numeric regex does not enforce truthful answers.** It accepts swapped samples, swapped units, reversed recommendations, incorrect interval endpoints, or “safe to act” without any number. An LLM can make a false claim entirely from allowed numeric tokens.  
    **Fix:** Render all quantitative claims and decisions from typed deterministic results; restrict generated prose to validated references or use templates throughout.

24. **F5–F7 — Imported CSVs create prompt-injection, HTML-injection, and spreadsheet-formula paths.** The current app interpolates values into `innerHTML`; new imported strings must not inherit that trust. A sample-name instruction could also steer `export` or `generate_report` if passed to a tool-capable LLM. [OWASP guidance](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html), [CSV injection](https://community.owasp.org/attacks/CSV_Injection).  
    **Fix:** Parse a bounded schema, render text safely, neutralize spreadsheet formulas, and enforce tool authorization independently of imported content and model output.

25. **F7 — Server-side keys do not prevent proxy abuse or secret exposure.** The plan lacks loopback binding, Host/Origin checks, session authorization, rate/token limits, timeouts, and a restricted static root. A naïve stdlib file handler also follows symlinks outside its served directory. [Python documentation](https://docs.python.org/3/library/http.server.html#security-considerations).  
    **Fix:** Bind locally, validate Host/Origin and session requests, allowlist upstreams/tools, cap spending and concurrency, and serve only approved assets with sanitized errors/logs.

26. **F/G — Auditability and acceptance criteria are too thin for “industry-grade.”** Logging successful predictions misses refusals, missing bands, invalid values, failed imports, stale data, interrupted scans, model mismatches, and provider failure. Animation speed is not inference latency. GeoJSON without coordinates cannot demonstrate parcel mapping.  
    **Fix:** Log inputs/model/calibration/policy hashes and every outcome, test offline failure paths and numerical parity, measure actual latency/memory, and export coordinate-free records as a join table or explicit null geometry.

The simpler credible implementation is one frozen HIDSAG replay with correctly evaluated intervals, absorption maps, deterministic decisions, and a typed lab reconciliation/export round trip. Keep the plant replay separate, the specialist experimental, and arbitrary-phone inference and LLM actions out of the first release.

VERDICT: REVISE
### Claude's response (round 1)
Accepted:
- **Accepted almost entirely.** I agreed with 1–26 except where noted below.
- **Intervals.** Grouped split-conformal inside each outer fold, at 80% (90% is not achievable at n_cal ≈ 9–29). Coverage is reported per target with a cluster bootstrap.
- **Nesting.** Strict nesting, including k-means, scaling, hyperparameters and blend generation, all within the inner-training partitions. Inner splits are grouped.
- **Gates.** Paired group-level gates with Holm correction added. The doctrine's Mann-Whitney and Cliff's delta are kept as additional gates, not replaced, because the user's doctrine requires them. "Better" now needs all of them.
- **Baselines.** Median and metadata-only baselines added. v6 is labelled exploratory.
- **Blends and maps.**
  - The blend claim is narrowed to synthetic areal mixtures.
  - **Per-pixel mineral prediction maps are dropped**, replaced by per-sensor absorption and cluster maps.
  - No joint VNIR–SWIR pixels.
- **Explanations.** Group occlusion on the exact displayed model.
- **Runtime.** The app is labelled as a replay of precomputed results.
- **Plant.** Rewritten: availability timestamps, assumed lab delay with sensitivity runs, clock horizons, separate tune and calibrate months, block bootstrap.
- **Phone.** A refusal and quality demo only.
- **OOD.** Shrinkage on PCA scores, with measured false refusals and acceptance of shifted inputs.
- **Specialist.** Validation-only, no override or promotion.
- **Wording.** The PGE claim is narrowed; licence and shipping rights are split by artefact.
- **Framing.** Three labelled evidence tracks.
- **Policy.** A deterministic decision policy from training-fold thresholds.
- **Lab round trip.** Typed reconciliation schema with rejection reasons.
- **Assistant.** The LLM routes only, and deterministic templates render every number and decision.
- **Security.** Injection defences, and server hardening (loopback, Origin, session token, allowlists, caps).
- **Audit and acceptance.** A full audit log, and acceptance criteria including latency, memory and failure paths.

Rejected or modified:
- **"Keep phone and LLM out of the first release":** partly rejected. The user asked for both explicitly. They are staged as R-3, after the core R-1 and R-2, under the constraints above. That keeps the user's requirement and removes the risks Codex named.

## Round 2 — Codex (gpt-6-astra)

The revision resolves most first-round concerns. These remaining issues are incorrect or incomplete implementations of accepted fixes. No files were modified.

1. **A4 — The interval uses the wrong model’s residuals.** You calibrate the reduced-training model, then centre intervals on the full-outer-training refit. Stating this mismatch does not preserve split-conformal validity. [Split-conformal construction](https://arxiv.org/pdf/2107.07511).  
   **Fix:** Use the same frozen reduced-training model for calibration, displayed predictions, explanations, and interval centres.

2. **A1/A4 — Calibration labels may still influence model selection.** “Fit the selected model on the rest” does not exclude calibration groups from the earlier family/hyperparameter selection. Holding them out only from the final fit is insufficient.  
   **Fix:** Partition outer-training into proper-training and calibration **before** any selection, and run all inner CV exclusively within proper-training.

3. **A4 — “Grouped split-conformal” still lacks a group-level score.** Holding out composites but pooling their individual absolute residuals gives multiple dependent scores per composite; using the number of composites in the quantile formula does not repair that.  
   **Fix:** Define the coverage event and one score per composite—for example, maximum residual across its fractions for simultaneous within-composite coverage—and count those scores.

4. **A4/key decision 2 — The calibration arithmetic and 90% claim are wrong.** A quarter of an outer-training set containing roughly 28–29 composites is roughly 7–8, not 9. At \(n_\mathrm{cal}=9\), a finite 90% interval uses the maximum residual; at 29 it uses rank 27. Also, 80% intervals are narrower than corresponding 90% intervals.  
   **Fix:** Compute actual fold-specific counts and \(k=\lceil(n_\mathrm{cal}+1)(1-\alpha)\rceil\), return an unbounded interval when \(k>n_\mathrm{cal}\), and justify 80% as a chosen trade-off.

5. **A4/H — Bootstrap coverage intervals can falsely report certainty.** If every evaluated composite is covered, resampling its coverage indicators produces a degenerate `[100%, 100%]` interval. This violates the intended honest-small-\(n\) reporting.  
   **Fix:** Add a boundary-safe uncertainty method for the defined independent evaluation unit, explicitly qualifying dependence from shared CV fits and unknown localities.

6. **A7 — The occlusion groups are not a non-overlapping wavelength partition.** Brightness and cluster fractions depend on wavelengths already listed; normalization, gradients, and band depths also cross those boundaries. Replacing a spectral block while leaving derived features unchanged creates internally inconsistent inputs.  
   **Fix:** Occlude defined raw wavelength regions and recompute the entire frozen feature pipeline; report brightness/cluster ablations separately as overlapping feature diagnostics.

7. **C1 — Matching the model family does not yet isolate modality.** RGB renders and hyperspectral means can differ in spatial support and rendering transformations. The existing pipeline saves the first RGB crop while pooling spectra across crops, so inheriting those assets compares different observations.  
   **Fix:** Match crops, masks, aggregation, folds, and tuning budgets; preferably derive RGB and hyperspectral features from identical source pixels using a fixed documented rendering operator.

8. **C2–C3 — The phone’s domain-distance calculation is still undefined.** The specified shift tests use spectra, whereas the phone supplies RGB pixels; a spectral PCA/Mahalanobis detector cannot score that input. “Held-out groups” also does not distinguish threshold calibration from evaluation.  
   **Fix:** Keep spectral OOD scoring within T1 with separate threshold/evaluation groups, and omit phone domain distance unless a separate RGB detector and evaluation are specified.

9. **E — The deterministic policy does not cover every valid input.** A Bond WI interval entirely below the normal band is favourable, crosses no threshold, and satisfies none of the listed outcomes. Exact-boundary cases, missing targets, “borderline” OOD, and the conservative recipe remain unspecified.  
   **Fix:** Write a total decision table with target-specific adverse directions, explicit boundary/missing-data handling, numerical OOD bands, and named review actions.

10. **G1 — The optional framing sentence defeats the accepted template-only fix.** “Increase lime dosing immediately” passes the stated digit/word filter; so does “Recovery is one hundred percent.” Both can introduce unsupported decisions or numbers.  
    **Fix:** Remove free-form framing, or select framing exclusively from deterministic approved templates.

11. **F7/G — “Never sent as instructions” is not an enforceable injection boundary.** CSV content supplied as *data* can still instruct a tool-routing model; typed arguments and allowlisted tool names do not establish that the requested action matches the user’s intent.  
    **Fix:** Send the router only the user’s request and trusted tool schema, keep imported content/tool results in deterministic processing, and validate argument scope independently.

12. **F5 — The reconciliation schema excludes a core T1 target.** Its closed `analyte_type` list includes recovery and work index but cannot represent lime consumption in kg/t. An export/import round trip therefore cannot faithfully cover the displayed T1 predictions.  
    **Fix:** Add a versioned target registry covering every displayed target, with permitted units, basis, conversions, and import/export round-trip checks.

VERDICT: REVISE
### Claude's response (round 2)
All 12 findings accepted:

1. **Same model for interval and prediction.** One frozen proper-training model gives the calibration scores, the displayed prediction, the interval centre and the explanations. A full refit is used only for the separately labelled v6-vs-v5 accuracy evaluation.
2. **Calibration split first.** Proper-training and calibration are split before any selection. All inner CV, k-means, scaling and blending stay inside proper-training.
3. **One score per composite.** Max residual across a composite's size fractions, so coverage means all fractions are covered at once.
4. **Exact arithmetic.** k = ⌈(n_cal+1)(1−α)⌉ on actual fold counts. When k > n_cal the interval is unbounded and shown as "not enough calibration data". 80% is justified as a chosen trade-off.
5. **Coverage bounds.** Clopper–Pearson at the unit level, with the dependence caveat.
6. **Occlusion.** Raw wavelength regions are occluded and the whole feature pipeline is recomputed. Brightness and cluster ablations are reported separately.
7. **Matched modality.** RGB is simulated from the same pixel pool with a documented operator; HIDSAG's own RGB renders are not used for the comparison.
8. **Phone.** No domain distance and no prediction; quality gates only. Spectral OOD is used only in T1, with separate calibration and evaluation units.
9. **Decision policy.** A total, top-down table with adverse directions, inclusive boundaries, unbounded and missing states, numeric OOD bands, freshness, and named review actions. Unit tests cover every row and boundary.
10. **No free-form LLM text** is ever shown.
11. **Router input.** The router sees only the user's question and the tool schema. Arguments are validated independently, and export and report need a user click.
12. **Target registry.** A versioned registry covers lime in kg/t and every displayed target, with conversions and a round-trip identity test.

## Round 3 — Codex (gpt-6-astra)

No remaining material blockers for implementation within the stated replay and experimental scope. The revision addresses the prior calibration, leakage, policy, and LLM safety findings, with the statistical dependence limitations explicitly disclosed.

No files were modified.

VERDICT: APPROVED
### Resolution
Converged: APPROVED after 3 rounds (38 findings total, 37 accepted, 1 modified: phone and LLM kept as R-3 under the stated constraints because the user asked for them). The user's same-turn request authorises the build; Claude builds.
