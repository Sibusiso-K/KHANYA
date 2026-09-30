# Current live analysis and deliverable evidence — 30 September 2026

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