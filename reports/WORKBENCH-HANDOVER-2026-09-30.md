# START HERE — REEFPRINT / KHANYA continuation
Updated 30 September 2026. User requested a portable handover and GitHub push.

## Where the actual work is
- Application worktree: C:/Users/USER/.codex/worktrees/reefprint-pwa-live-mvp/REEFPRINT
- Application branch: codex/launch-live-demo, remote khanya = https://github.com/Sibusiso-K/KHANYA.git
- Existing application PR: https://github.com/Sibusiso-K/KHANYA/pull/15
- Desktop project C:/Users/USER/Desktop/REEFPRINT is the separate physics history. Do not mix Git histories or replace it with the application.
- Recovery source snapshot: handover/workbench-source-2026-09-30 under Desktop/REEFPRINT. Contains the NEW application files only; apply to the application checkout, not as a standalone project. No weights, source images, credentials or node_modules included.
- New working app: http://127.0.0.1:8510/ . Old 8501/8502 tabs are Streamlit versions. New API docs: http://127.0.0.1:8510/docs

## What was implemented
React 19 + TypeScript + Vite responsive white UI, following the user's approved three-panel mockup. Workspace (sample library, original/overlay/mask, phase composition), Samples table, Reports with JSON/source Markdown/print export, Spatial with orbitable Three.js specimen planes. Lucide icons; reusable native controls; responsive CSS.
FastAPI webapi/app.py serves frontend/dist and /api routes. Background single-worker jobs run the real DeepLabV3 ResNet50 checkpoint via existing inference modules. Local cache binds result to source-image and checkpoint SHA. Cached inference is labelled.
Per-specimen notes and assay CSV stored in browser localStorage, explicitly local; exportable. CSV expected element,value,unit. No hardware integration.
Guarded explicit simulator action: unverified uploads, low confidence, full-section mode, stale results and non-Grind-finer actions HOLD. Actual apply path calls existing local OPC UA seam, never a plant.

## Verified this session
- TypeScript + Vite production build passed twice, including final stale-result/selection fixes.
- Six new regression tests passed: unverified, low confidence, full section, stale, Continue holds; valid fresh Grind-finer eligibility.
- API live health: checkpoint present, 12 real samples, cloud_sync false.
- Real test_11 centre-field inference: 26.482 s including model setup, mean confidence 0.4944437444; advisory HOLD. Not a successful actuation.
- Real test_11 full-section inference: 396.592 s, confidence 0.5562464595, advisory-only; completed through browser-triggered job.
- Desktop browser showed actual imagery/overlay/composition and bound accuracy. Reports navigation verified; phone-width (390 px) Reports screenshot inspected.
- Installed Impeccable and Frontend Design skills used. Impeccable detector found one false positive: navigation underline mistaken for rounded-card accent.
- No claim of improved model accuracy. No new model training in this UI session.

## Model/report truth
Active SHA fb78727d4859947d3605ccf9374f8defbc40897e9cf1b1922a52c1832d387067.
Recorded Kaggle checkpoint metrics from reports/END-TO-END-LOCAL-DEMO-2026-09-30.md:
mIoU 0.4543, pixel accuracy 0.7716, 12 test images.
IoU: background .8756, chalcopyrite .3537, magnetite 0, pyrrhotite .6866, pentlandite .3555.
Historical stronger checkpoint de7135a... has mIoU .5725 and pixel accuracy .8914. Never assign those scores to the local Kaggle checkpoint.
Image-area percentages are not ore grade or volume fractions. Confidence is not accuracy.
Live centre crop is not six-field sampling and should not inherit the other branch's 2/12 actionable claim.

## Start again
In application worktree:
1. cd frontend; npm ci; npm run build; cd ..
2. Use existing .venv and .runtime_packages (private, ignored); requirements-web.txt plus repository requirements describe packages, but clean-environment install needs verification.
3. powershell -ExecutionPolicy Bypass -File scripts/start_workbench.ps1
   Script sets PYTHONPATH to .runtime_packages plus project and runs uvicorn webapi.app:app --host 127.0.0.1 --port 8510.
4. Open http://127.0.0.1:8510/ . Requires private S2 dataset and best.pt in existing paths; UI fails honestly if missing.
5. Tests: set same PYTHONPATH; .venv/Scripts/python.exe -m pytest tests/test_workbench_safety.py -q
6. Runtime process was uvicorn PID 27896, exec session 43170; verify current process before stopping/restarting.

## Highest-priority remaining work
1. Finish browser checks: Workspace mobile, Spatial orbit/select/render, upload then infer, local note/assay persistence, download reports, explicit simulator HOLD. Test actual OPC UA APPLY with a suitably validated model/result; do not force weak current predictions to act.
2. Add integration tests for API job lifecycle, source/result binding, malformed/oversized uploads, concurrency and result selection during running jobs. Current six tests cover refusal helper, not full transport.
3. Harden webapi: persistent immutable benchmark manifest rather than trusting whatever test files exist at startup; recheck checkpoint identity at simulation; audit cache integrity; validate report metrics from immutable machine-readable manifest rather than recorded Markdown constants.
4. Reconcile with Sibusiso's newer guarded six-field pipeline after review. Existing worktree is older than PR17/18; don't silently overwrite either implementation.
5. Improve source maintainability: App.tsx/styles.css are large and compact; split components and format. Three.js is lazy-loaded but ~500 kB; consider chunking.
6. Real geographic modelling needs collars, surveyed downhole traces, CRS, intervals and independently supported geological surfaces. Current 3D is specimen-image atlas with illustrative placement, not orebody reconstruction.
7. Supabase auth/tables/RLS/storage and Cloudflare hosting are NOT wired into this app. Keep loopback-only until auth/ownership/CORS/upload limits are reviewed. No secrets in frontend.
8. PWA manifest exists, but offline service worker/install flow not implemented or tested. Browser notes don't equal synced field capture.
9. Need DESIGN.md and .impeccable/design.json finish documentation plus full design review. No independent reviewer completed: backend subagent hit usage limit and root implemented API.
10. Update SBOM/dependency documentation and CI for new frontend/API; build logs and handover must accompany commits.

## PR monitor state
PR17 approved at 5fa30e3; our merge attempt was blocked by automatic review. Sibusiso subsequently merged #17 into khanya/speed (reported by GitHub during this continuation). PR13 head now 87ebfe540955e48fa962edadb7cbca21cdaba319 includes those fixes. PR18 new head 281e4e7b9cfea6320a449da37683c58743849f3e, phone layout/plain-language/stale-claim fixes, checks green. PR11 f8ca41c..., PR12 fb46b224... unchanged, changes requested. Need complete current review before merge. Do not repeat comments on same heads or bypass unresolved parent review.
User permits review/comment and eligible merge. Earlier automatic review specifically blocked #17 shared-branch merge; it was not bypassed by this agent.

## Continuation prompt
Continue REEFPRINT from handover/START-HERE-WORKBENCH-2026-09-30.md. Work in the application worktree and codex/launch-live-demo branch, not the Desktop physics history. Preserve the approved white mockup layout and real-data provenance. Verify port 8510, finish UI/API integration tests, resolve concrete defects, update build log, and push to existing PR15. Keep source data, model weights and secrets private. Review current Sibusiso PRs without duplicate comments. Do not claim cloud deployment, trained accuracy improvements, geographic reconstruction or simulator actuation that has not been verified.

