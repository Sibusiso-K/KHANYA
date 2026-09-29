# Implementation contract for Codex Luna or Claude Sonnet

## Start here

The user explicitly accepted **retraining** on 29 September 2026. Do not spend the next session searching indefinitely for the old checkpoint. The application branch is `codex/khanya-build-plan` in `C:\Users\USER\.codex\worktrees\khanya-build-plan\REEFPRINT`. Check for newer work before editing. Read [SETUP-AND-ASSETS.md](SETUP-AND-ASSETS.md) first. No implementation, package installation or training has been done by this planning change.

Priority order: **working trained model → fresh report → real advisory-to-simulated-parameter change → quality/sensitivity demonstration → rehearsal → optional assay/geography**. Retain Streamlit and existing templates. No new React/FastAPI/native-phone application is needed for the deadline.

## Sequential tickets and acceptance criteria

### P0 — environment, data and run provenance

Inspect `requirements.txt`, `src/segmentation/{model,lumenstone,patches,train_patches}.py`, `dashboard/app.py` and current tests. Create an isolated application venv. Download S2 v2 from its publisher, inspect archive paths, verify paired masks and create a manifest. Record code/data/environment hashes. Validate six validation images come only from publisher train; disclose unavailable specimen metadata.

Add a small preflight command (`src/preflight.py` is proposed; absent at inspection) that reports data version, checkpoint path/hash, class list, device, physics dependency import and offline assets. Missing weights or data must produce explicit unavailable states. No random-weight “analysis.” Ignore raw data/checkpoints/secrets in Git.

Acceptance: import smoke check and existing test suite pass; 37/12 source pairs verified; manifest written; failure-state check blocks inference without weights. Estimate: 1–2 hours plus download, not a guarantee.

### P1 — retrain the existing S2 model

Use the current DeepLabV3–ResNet50 implementation and explicit upstream pretrained enum. First time one representative epoch, then select an achievable training budget without looking at test scores. Preserve all prior reports; use a new run ID/output directory and ensure resume state belongs to that run. Record training settings, validation selection and final model hash. Default eight-epoch patch training is a baseline, not a promise of adequate quality; improve only if time/validation justify it.

Acceptance: a loadable checkpoint predicts a real image with the correct five-class output; all three selected sulphides are assessed, and failure to detect any is recorded rather than hidden. Training duration is measured on actual hardware. If time expires without a working three-phase model, acknowledge the unmet deliverable; a polished UI or ground-truth overlay does not fulfil it.

### P2 — freeze evaluation and the evidence package

Run full-section inference on the 12 S2 test images with no test-time model selection. Generate a fresh cache keyed by dataset/input/model hashes. Evaluate per-class IoU/precision/recall, pooled mIoU, pixel accuracy and confusion matrix. Separate strict and void-border protocols. Keep magnetite/background in the table. Show original image, predicted mask and labelled reference separately.

Add warm inference median/p95 over a documented number of runs, cold-start time and full-section runtime on named hardware. Timing starts at the declared stage; preprocessing/I/O/model loading must not disappear inside a “real-time” headline. Record all end-to-end stage times in addition to inference-only time. Aim for a usable single-field interaction; any numerical latency target is a target until measured.

Report association and advice disagreement against the same deterministic calculation on expert masks as **pipeline consistency**, not clinical/plant correctness. Bootstrap uncertainty at image/specimen level where possible; millions of correlated pixels are not millions of independent samples. The set is small and historically reused.

Outputs: versioned metrics JSON, `reports/accuracy-<run>.md`, confusion plot, failure examples, latency JSON and run manifest. Historical scores must stay labelled historical. Estimate after training: 1–3 hours plus full-section inference.

### P3 — make the control demonstration substantive

Existing `dashboard/opcua.py` sends observations and explicitly says `advisory_influenced=False`. Extend a separate simulator decision path; do not simply rename an acknowledged observation to “plant adjusted.” Suggested new module `src/process_simulator.py`, plus adapter changes and focused tests.

Proposed narrow policy:

- Accepted evidence with a regrind-review advisory -> propose `regrind_enabled=true` in a **simulator**, pending operator confirmation.
- Accepted evidence that supports continue -> propose `regrind_enabled=false` in the simulator, also reviewed.
- Review/hold, unsupported image, stale data, missing result or failed connection -> do not apply a new setting; record the reason and leave the simulator's prior state explicit.
- Preserve existing advisory semantics. If the advisory cannot justify either command, remain review; never force a result for the demo.

This Boolean enable/bypass setting is an illustrative process parameter, not an engineered plant recommendation. If a numeric control is added, specify its unit, baseline, bounds, slew limit and arbitrary simulation basis. Do not invent dosage, optimum P80 or recovery curves. No connection to an actual PLC/DCS is part of this sprint.

Use a command ID, source result ID, model hash, event time, expiry, requested value, operator approval, interlock status, acknowledged value and reason. Use a simulator namespace. Apply atomically only after validating all prerequisites; duplicate IDs must be idempotent. Make the changed before/after state visible and save it to the audit trail.

Acceptance tests: accepted+approved command changes the actual simulator state; stale/unapproved/review/malformed commands do not; repeated command is not reapplied; connection failure yields a failure state, not success; reload shows the logged event. Run a real local OPC UA transaction and capture its acknowledgment. Estimate: 2–4 hours if the current seam is healthy.

### P4 — quality and decision-sensitivity screening

Implement bounded checks for corrupt input, dimensions/modality metadata, blur/saturation/exposure where measurable, and insufficient detected material. Unknown modality remains unknown; a file upload is not automatically reflected-light microscopy. Keep explainable checks separate from any uncalibrated neural score.

For an optional sensitivity test, run a fixed, clearly labelled exposure perturbation on an image copy and compare modal fractions/advice. This is a **stress test**, not a real second capture and not guaranteed uncertainty. Thresholds must be fixed using training/validation and domain judgement before final test scoring. Avoid tuning the gate to the known 12-image test cases.

Report coverage (accepted/total), refusals, error on accepted cases and total error/refusal tradeoff. A gate that rejects everything is not success. Do not call a fixed empirical margin a calibrated 95% guarantee. Check the current report's `0.335` band before presenting it. Show baseline/gated performance under identical conditions, not only the most dramatic example.

Acceptance: unsuitable/stale evidence cannot change simulator settings; stress test has labelled inputs and outputs; all test cases and coverage are reported. If the gate has no useful validation evidence, ship transparent quality flags plus mandatory human review instead of claiming reliability improvement. Estimate: 2–4 hours; cut elaborate overlays first.

### P5 — complete the ten-minute pitch and offline release

Reuse the existing image panel and templates; add only the evidence drawer, explicit states and process timeline needed for P0–P4. Build the eight-slide PowerPoint described in BUILD-PLAN.md with source footnotes and a methods appendix. Record a short backup of the actual trained pipeline and actual simulator; label playback honestly if used. Test launch on a fresh session with Wi-Fi off, including the physics dependency, weights, styles and images.

Acceptance: each organiser theme has a slide; three-phase report is linked; one command-change and one refusal example work; missing-weight fallback is honest; deck runs within ten minutes; local release manifest resolves all required files. No simulation screenshot presented as plant validation. Estimate: 2–3 hours excluding rehearsal refinements.

### P6 — chemistry and geography extension, only after P0–P5

Prefer CSV import into a local SQLite sample register and a depth strip for the available Bushveld data. Existing source may be referenced from the physics checkout or copied into ignored application data with attribution. Never commit unrelated personal/submission files.

The geography branch requires a validated coordinate-bearing dataset and local assets. Render a small real subset, not all global records. Use QGIS for CRS/data checks and local CesiumJS assets for a browser view only if useful. A map update should follow a committed sample record. Phone capture may be a small form/import; offline durable queue and deduplication require tests before claiming offline sync. Web geolocation often needs a secure context; localhost on the phone is not the laptop's LAN HTTP address. QField local-file capture or manual coordinate import is a valid simpler fallback.

Acceptance: imported values/units exactly match source rows; missing/LOD values remain distinct; no duplicate sample on replay; original method/source retained; no coordinate -> no marker; real coordinate -> correct country/CRS; no unrelated assay/image join. Estimate: 3–6 hours for a modest register/view, longer for phone sync and terrain acquisition. Cut this from the deadline build if it threatens the required deliverables.

## Minimal record contracts

Use typed records/dataclasses or validation at module boundaries. The following fields are a specification, not an implemented API:

| Record | Required fields and rules |
|---|---|
| Sample | UUID, source record ID, material/batch if known, collection time with timezone, location nullable, CRS if located, uncertainty if known, notes, source hash |
| Assay | sample UUID, analyte, value nullable, unit, method, qualifier (measured/below detection/missing), LOD nullable, uncertainty nullable, analysis timestamp, measured/replay/synthetic label |
| Image | sample UUID only if genuine link, image hash, source dataset/version, modality, scale if known, acquisition metadata |
| Inference | result UUID, image/model/code hashes, class map, phase area fractions, QC status/reasons, runtime, output mask reference, produced time |
| Advisory | result UUID, supported proxy values, rule version, review/hold/propose state, explanation, expiry; no unauthorised mineral-to-grade conversion |
| Command | command UUID, advisory UUID, simulator tag/value/unit, approval, interlocks, expiry, requested/acknowledged states and times |

Store raw assay and inferred phase output separately. Percent image area, elemental wt%, oxide wt% and ppm require explicit distinct labels. Missing values must not be coerced to zero. Enforce UUID/source-ID deduplication and never use geographic proximity alone as a sample join.

## Deadline gates

- **29 September:** stage S2, establish runtime, start timed training and control-path work.
- **30 September:** freeze model, complete report/control demo and deck; rehearse. Revert optional changes that break the core.
- **1 October:** use verified release and backup, submit according to organiser instructions. Repository says 13:00 but supplied email only confirms the date.

These dates define priority, not a promise that unmeasured training will finish. Total estimates overlap only if team members actually work independently. A single implementer must cut P6 and optional P4 features first. Do not substitute mock predictions if P1 fails.

## Copy-paste prompt for Codex Luna or Claude Sonnet

```text
Continue KHANYA for Mintek Problem 3. Start in the managed application worktree
C:\Users\USER\.codex\worktrees\khanya-build-plan\REEFPRINT
on codex/khanya-build-plan, checking branch/status and any newer user changes.
Read handover/README.md, handover/IMPLEMENTATION.md,
handover/KAGGLE-TRAINING.md, handover/SETUP-AND-ASSETS.md,
EVIDENCE-REGISTER.md, BUILD-PLAN.md and PILOT-AND-BUSINESS.md.

I explicitly approve retraining the missing S2 model. Implement the ordered
P0–P5 plan: stage official S2 v2, isolate the environment, train the existing
DeepLabV3–ResNet50, preserve held-out evaluation, create a fresh per-class report,
then demonstrate a real local OPC UA exchange that changes an explicitly
simulated regrind parameter with review, expiry and an audit log. Existing
observation acknowledgment is not enough. Keep all historical results and
do not reuse them as the new model's scores. Run appropriate tests.

Keep the current Streamlit application. No paid APIs, purchases, quantum
integration or framework rewrite. The user intends to start training on Kaggle;
inspect their actual run and use the Kaggle guide. Measure training time before promising a deadline. Preserve
licences/provenance, never publish raw restricted data/weights or secrets.
Do not merge the separate REEFPRINT physics history. Inspect and reuse its
pinned integration dependency through the documented seam.

Then prepare the ten-minute PowerPoint, sources appendix, offline release and
truthful backup demo. Chemistry-to-3D is P6 only after the core works. Do not
invent coordinates, link unrelated assays to images, call a 2D proxy true
liberation, or claim simulated recovery as plant evidence. Keep the established
presentation and code names REEFPRINT (aka KHANYA).

Keep the handover current, commit and push completed source/docs to the
planning/implementation branch without force-pushing or merging main.
Report measured results and remaining limitations. Ask only for genuinely
missing access or decisions; continue independent work while waiting.
```
