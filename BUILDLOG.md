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
