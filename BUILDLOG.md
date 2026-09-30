## 2026-09-30 — authenticated Cloudflare demo and white workbench

White responsive React workbench now has Dashboard, Workspace, Samples, Spatial, Process and Reports; exact result-bound grain selection/export, keyboard navigation, protected image/download loading, account-scoped browser caches and private Supabase records. Supabase RLS/storage/schema deployed; bearer auth fails closed in public mode. Simulator sessions remain host-local and isolated, not durable cloud controls. No real plant connection.

Temporary user-approved HTTPS demo: https://arnold-orange-malpractice-transmitted.trycloudflare.com (upstream localhost:8766). Local offline research mode: http://127.0.0.1:8510. Both need this host running; this is not permanent Cloudflare Pages deployment. Public health/config reachable; unauthenticated sample requests return 401. A real human sign-in/upload round trip is still pending user login; SQL ownership/CAS checks and mocked auth tests are not that proof.

Verification: 69 focused workbench Python tests passed; frontend production build and TypeScript passed; two grain utility tests and two desktop/mobile browser tests passed, including no external HTTP requests in local mode. Credit: collaborator six-field sampling, input gates and grain evidence backend retained. CE+Dice validation experiment completed, magnetite IoU still zero; matched CE control launched on Kaggle. No held-out test improvement verified; deployed checkpoint remains mIoU 0.4543 / accuracy 0.7716. See reports/MODEL-TRAINING-AUDIT-2026-09-30.md, SUPABASE-DEPLOYMENT.md and UI-EVIDENCE-HANDOVER.md.

Next: human private workspace sign-in/upload persistence proof, permanent deployment after Azure MFA, matched training-control comparison without test-set tuning, evaluate selected final checkpoint once, and resolve open review blockers before merging Sibusiso PRs.
# REEFPRINT Build Log

## 2026-09-30 — dashboard shell and Kaggle checkpoint verification

- Reworked the Streamlit prototype shell to use one REEFPRINT / KHANYA masthead, grouped the analysis mode controls, and put micrograph upload beside the held-out example action. Removed repeated branding from the embedded results and landing fragments. Moved the landing/progress placeholders after the upload card so the empty-state dashboard cannot push the primary action below a tall iframe.
- Verified the running local preview at `http://127.0.0.1:8502/`; browser accessibility order is masthead → analysis mode → upload/example → dashboard. At the observed 788 px viewport the landing workbench collapses responsively; the responsive templates retain tablet/mobile breakpoints.
- Kaggle kernel `lethabomh14/reefprint-s2-v2-private-baseline-training` completed. The verified checkpoint SHA-256 is `fb78727d4859947d3605ccf9374f8defbc40897e9cf1b1922a52c1832d387067` (this is the checkpoint currently in this demo branch). On 12 held-out LumenStone S2 sections: pooled five-class mIoU **0.4543**, pixel accuracy **0.7716**; phase IoU: chalcopyrite **0.3537**, pyrrhotite **0.6866**, pentlandite **0.3555**, magnetite **0.0000**. This is **not an accuracy increase** over the separate KHANYA baseline report (mIoU 0.5725, pixel accuracy 0.8914). Keep the higher-scoring baseline for comparisons; do not claim this candidate improved accuracy. These are S2 analogue-dataset measurements, not validation on South African plant ore.
- Kaggle delivery status: the private notebook/kernel is complete and its run output bundle was retrieved and checksum-verified locally for inspection. The dataset is downloaded from its source at runtime; it is not attached as a Kaggle dataset asset. The run output/checkpoint archive is not committed to Git.
- Verification: `python -m compileall -q dashboard/app.py tests/test_render.py`; `python -m pytest tests/test_render.py tests/test_dashboard_inputs.py -q` — **20 passed**. The Streamlit preview is local-only. XRF hardware/data, surveyed 3D geology, production auth/API, and live plant control are not connected; the map and process changes remain clearly labelled illustrative/simulation-only.

## 2026-09-30 — Responsive workbench implementation
Added frontend/ (React/TypeScript/Vite, white three-panel design) and webapi/ (local FastAPI inference, checkpoint-bound reports, guarded simulation). New app localhost:8510; old Streamlit remains separate. Production build passed; six new refusal tests passed; real test_11 centre inference 26.482 s and full-section 396.592 s. No accuracy improvement, cloud auth/sync, geographic orebody, or successful new actuation claimed. Full restart guide and remaining work: reports/WORKBENCH-HANDOVER-2026-09-30.md. User explicitly authorized the responsive redesign and asked to preserve/push for continuation.

## 2026-09-30 — spatial workbench and decision evidence
Added 3D/plan/section geological demo, validated QGIS GeoJSON survey import/link/export, Public Sans light UI refinement, dedicated Process screen and server-bound decision attachment. 12 spatial contract tests and 7 API safety/export tests pass; production build passes. Independent review fixes resolved. See reports/SPATIAL-UI-HANDOVER-2026-09-30.md for exact scope, provenance, verification and cloud follow-up. Model accuracy unchanged; cloud remains pending.


## 2026-09-30 — durable local sample records
Notes and assay CSV imports now save to versioned FastAPI records with atomic disk writes and stale-write protection. Browser save/reload verified; QA note removed. 30 Python tests and prior12spatial tests pass; frontend build passes. Cloud readiness audit found Azure expired MFA and no usable Supabase/Cloudflare project configuration in this session. See reports/LOCAL-RECORDS-HANDOVER-2026-09-30.md. No public deployment or accuracy improvement claimed.


Post-integration verification: remote 6b57daf merged without dropping its input-check refactor or grain helpers. Final combined focused backend/input suite: 74 passed; 12 spatial contracts, three grain utility/selection tests, two serial desktop/mobile browser tests passed. Regenerated bundle after merge. Public browser sign-in page verified; actual user cloud round trip pending.

Release check: GitHub PR15 revision 3eef67b passed all four reported checks (main tests, workbench API tests, offline frontend bundle/browser checks, GitGuardian). Temporary public URL returned HTTP200 after final restart; a short origin-refused window occurred during restart and was resolved. No PR merge performed while reviewer change requests remain outstanding.

Auth redirect fix: confirmed the project's sole registered user has email_confirmed_at set. Hosted Supabase Site URL was localhost:3000; changed it to the exact approved temporary HTTPS demo and added the same exact redirect allow-list entry. Sign-up now explicitly passes the current origin as emailRedirectTo. Existing confirmation emails may retain the old destination; already-confirmed users can return and sign in. Replace this temporary destination when permanent hosting is established.

User live-result audit: 53.862s CPU six-field inference, 18.2% coverage, 55.35% mean confidence, real simulator HOLD0->0. Supabase result/private files confirmed. OPC UA separate engineering fixture acknowledged0->1; not attributed to the user's model result. Kaggle CE COMPLETE: foreground validation IoU .409899 vs Dice .431648 (+2.17pp exploratory only), both magnetite0. Current report download now leads with this updated evidence and qualifies historical control claims. Browser inspection could not reconnect to tab; backend/storage artifacts verified instead.

Mineral-phase upgrade: launched two private Kaggle runs, extended-dice and small-grain-dice, both confirmed RUNNING. Matched seed42, CE+Dice, 24x192=4608 training patches (9x prior512); second adds 50% 256px training contexts resized to512 with nearest masks. Whole native validation unchanged; test not evaluated; no automatic deployment or accuracy gain claimed. Source bundle/protocol hashes and runnable notebook copies saved in training/phase-experiments. Added image scanning wait screen, actual backend stage/field counters, elapsed time, reduced-motion support and mobile layout; three browser tests passed. Backend progress callback verified by focused tests. Next: review logs/per-phase validation, especially magnetite, before selecting any new checkpoint.


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
