# Current live analysis and deliverable evidence — 30 September 2026

## Approved demo checkpoint
The approved live-demo checkpoint is `de7135a96541a46dc0981a991cb954186c7cd669ea1c1b33914d1929ae9b1357` (`de7135a9`), selected for the best held-out mIoU reported in `reports/ACCURACY-REPORT.md` (mIoU 0.5725; pixel accuracy 0.8914). The recorded test_11 run below used `fb78727d` on the Lethabo host and must be rerun with `de7135a9` before its result is presented as approved evidence. No replacement numbers are invented here.

## Live model and measured accuracy
DeepLabV3 with ResNet-50 backbone (Torchvision/PyTorch), five pixel classes. Inference runs locally on this computer's CPU through FastAPI; Cloudflare supplies HTTPS and Supabase supplies authentication/private storage. Kaggle is training only, not the live inference endpoint.
Checkpoint SHA: fb78727d4859947d3605ccf9374f8defbc40897e9cf1b1922a52c1832d387067.
Measured full-section benchmark on 12 held-out S2 images: five-class pooled mIoU 0.4543; pixel accuracy 0.7716. Foreground-only macro IoU from the reported rounded class values is about 0.34895. Phase IoUs: chalcopyrite .3537, pyrrhotite .6866, pentlandite .3555, magnetite .0000; background .8756. Three distinct ore phases have nonzero IoU, but magnetite fails. This is a research baseline, not industry-grade mineral identification. Pixel accuracy is not mineral-phase accuracy, and these are Norilsk analogue images, not South African ore validation.

## User's completed live run
Result d262ae09fbef4f438e3d884a17eed9af, sample test_11. Six 512px fields, 18.2% section coverage; measured elapsed 53.862 seconds. Sampled-area predictions: chalcopyrite 0.174%, pyrrhotite 60.836%, pentlandite 34.662%, magnetite 0%, background 4.327%. They are predicted 2D area fractions, not assay grades or whole-section/3D abundance. 23 connected grains. Mean softmax confidence .55352 is not a calibrated probability of being correct. Advisor marginal; actual simulator event held 0 -> 0 below provisional .85 floor. No positive actuation can honestly be attributed to this run.
Cloud aggregate check confirmed three saved sample entries, one result and seven private bucket objects; no saved field-note record yet. Notes-save/reload remains to verify separately.

## Process deliverable
Actual user's output reaches the simulator decision gate and generates a result-linked hold event, available through Process and decision evidence export. Independent engineering smoke check called the existing OPC UA control transport with the explicit fixture advisory 'Grind finer': acknowledged applied regrind_enabled 0 -> 1 at local ephemeral opc.tcp://127.0.0.1:54193/reefprint/sim-advisory/. This proves transport/parameter actuation only; it was not a current-model prediction or plant trial. Positive model-to-control end-to-end case still requires an eligible real model result. Do not weaken confidence gates to make a demonstration look successful. No recovery, reagent-saving, validated P80 or plant-performance claim.

## Kaggle matched validation comparison
CE control COMPLETE; best epoch8; native full-validation foreground macro IoU .40989914. CE+Dice .43164839 on the matched single-seed validation protocol: +.02174925 absolute (2.17 percentage points). Magnetite IoU0 in both. This is an exploratory validation improvement from changing the loss, not a held-out test improvement, not a stability study and not a deployed checkpoint. Checkpoint selection did not evaluate test data. Keep the live model unchanged pending rare-phase fixes and justified evaluation.

## Spatial scope
Three.js 3D/plan/section viewer supports QGIS-compatible surveyed GeoJSON, sample linking and export. Default strata/topography are illustrative. No measured coordinates have been established for these S2 images; a 2D image cannot establish a subsurface orebody. QGIS is optional free authoring software; proprietary Leapfrog is not required. Imported points supply spatial context, not validated implicit geological modelling.

The historical record below is retained for provenance. Its original single-field 1->0 actuation and no-public-URL statements do not describe the current gated live app.

---
# REEFPRINT / KHANYA end-to-end local demo record

**Run date:** 30 September 2026 (Africa/Johannesburg)  
**Scope:** local, offline-capable research prototype in managed worktree `codex/launch-live-demo`.  
**Public URL / cloud deployment:** none. This is a local launch, not a cloud deployment.

## What was run

The existing Streamlit application was launched at `http://127.0.0.1:8501/` from `dashboard/app.py`. The UI loaded as **REEFPRINT :: KHANYA prototype — LumenStone S2 · Offline** and exposes three modes: live 512×512 field, full native-resolution section, and held-out S2 evidence. The application explicitly says performance on a new ore body is not established.

An end-to-end command-line run used the real held-out `test_01` micrograph and the local Kaggle S2 patch checkpoint, through the application's same single-field inference, modal-mineralogy, advisor, and simulated OPC UA control modules. It ran on CPU, with two Torch threads.

| Stage | Observed result |
|---|---|
| Model/checkpoint | DeepLabV3-ResNet50; strict state load: every key matched |
| Checkpoint SHA-256 | `fb78727d4859947d3605ccf9374f8defbc40897e9cf1b1922a52c1832d387067` |
| Input | LumenStone S2 held-out test image `test_01`; centre field 512×512 px |
| Fresh inference time | 12.776 s on this CPU host, excluding model-load time |
| Mean pixel confidence | 0.5316; advisor correctly labels this low / verify manually |
| Predicted field area | chalcopyrite 68.40%; magnetite 0%; pyrrhotite 0%; pentlandite 31.60% of the field |
| Ore area | 88.17% |
| Apparent 2D sulphide association index | 0.9677 over 15 connected particles; it is not a 3D liberation measurement |
| Advisor | “Continue at current setpoint” — low confidence, with an explicit reason |
| OPC UA simulator | Applied and acknowledged `regrind_enabled: 1 → 0` at a local ephemeral `opc.tcp://127.0.0.1:<port>/reefprint/sim-advisory/` endpoint |

The OPC UA endpoint is created locally for the transaction and is not a persistent service. No PLC, plant, XRF instrument, phone, external cloud service, or production historian was connected. The simulated tag change demonstrates the requested **model output → process parameter** software path; it does not claim an engineered plant setpoint or a metallurgical recovery gain.

## Accuracy deliverable: which model and which numbers

The local checkpoint is Kaggle run `20260929-185547`, trained for 8 epochs with 64 native-resolution 512 px patches per epoch, batch size 2, learning rate 0.0002, on a Tesla T4. The publisher split has 37 train, 6 validation, and 12 held-out test images; the test split was not used for checkpoint selection. The source run manifest reports:

| Class | IoU | Recall |
|---|---:|---:|
| Background | 0.8756 | 0.9266 |
| Chalcopyrite | 0.3537 | 0.9287 |
| Magnetite | **0.0000** | **0.0000** |
| Pyrrhotite | 0.6866 | 0.7129 |
| Pentlandite | 0.3555 | 0.7128 |
| **Mean IoU (five classes)** | **0.4543** | — |
| **Pixel accuracy** | — | **0.7716** |

This model has nonzero held-out IoU for three distinct ore phases (chalcopyrite, pyrrhotite, pentlandite), so it clears the hackathon's numeric minimum, while failing magnetite completely. Pixel accuracy is dominated by common pixels and is not “77% mineral accuracy.” These are results on the publisher's S2 benchmark, not South African ore or a prospective plant trial.

**Do not substitute the existing `reports/ACCURACY-REPORT.md` headline here.** That report covers a different checkpoint (`de7135a…`) and reports mean IoU 0.5725 / pixel accuracy 0.8914. The local Kaggle run's checkpoint is `fb78727…` and scores 0.4543 / 0.7716. The newly trained run is worse on held-out aggregate IoU and still misses magnetite; it must not replace the stronger reported baseline.

## Verified repository checks

- `pytest tests -q`: **122 passed**, 2 warnings because pytest could not write its cache directory in the managed checkout.
- Checkpoint strict load: passed.
- Real held-out CPU inference: passed, 512×512 output.
- Local OPC UA simulated command transaction: passed and acknowledged.
- Streamlit health endpoint `/_stcore/health`: HTTP 200, body `ok`; dashboard root: HTTP 200.

## Architecture: live now vs planned

```text
LIVE LOCAL RESEARCH PROTOTYPE
Browser upload
  → Streamlit bridge (localhost)
  → PyTorch DeepLabV3-ResNet50 (512×512 live-field or slow full section)
  → semantic pixel mask + confidence
  → deterministic modal composition / association geometry
  → rule-based advisor with abstention
  → local OPC UA server
  → local simulated consumer
  → simulated regrind_enabled value + acknowledgement
```

```text
NOT CONNECTED / NEXT DEPLOYABLE ARCHITECTURE
Phone/PWA capture + offline queue
  → authenticated Supabase project (sample metadata, private image storage, RLS)
  → FastAPI inference/job API (validated input, model version and audit record)
  → versioned model worker (CPU/GPU; explicit quality/latency gates)
  → masks, phase metrics, uncertainty and signed sample result
  → responsive PWA: field capture on phone; overlays, evidence and reports on desktop
  → human-reviewed advisory / what-if simulator
  → OPC UA simulator first; any real control only after site engineering approval

Spatial extension: surveyed collar + downhole intervals + CRS → QGIS/PostGIS
for maps and sections → optional 3D viewer; no defensible 3D model without survey
and geological interval data. XRF values are elemental context, not phase labels.
```

Supabase project `uwdrfmwoivibnhpccwxe` was confirmed active, but has no REEFPRINT app tables, application storage buckets, app API, or deployed frontend attached. Cloudflare Pages/Wrangler and Azure deployment are not configured in this host. Therefore there is currently no remote login, mobile sync, hosted API, or shareable public demo URL.

## What remains before the hackathon submission is fully ready

1. Do not promote the weaker Kaggle run; retain `de7135a…` as the current accuracy-report baseline until a new run beats it under identical frozen evaluation.
2. Make a single source-controlled accuracy report for each checkpoint hash; include per-class IoU/recall/precision, confusion matrix, baselines, split, uncertainty intervals, and limitations.
3. For a polished live demo, show the actual mask/metrics from an approved image in the UI. Full native-resolution inference is slow on CPU; use Live Field mode and label it as a 512×512 field.
4. Finish Cloudflare Pages + FastAPI + Supabase deployment only after Wrangler/Cloudflare authorization and adding API schema, private storage policy, authentication and deployment configuration. Do not report Supabase as an app backend until the app writes and reads real sample records.
5. Keep process control simulation-only. Advisor thresholds include unsourced placeholders; a real plant trial requires site-specific mineralogy, mass-balance/assay reconciliation, metallurgist approval, safe PLC integration and controlled validation.
