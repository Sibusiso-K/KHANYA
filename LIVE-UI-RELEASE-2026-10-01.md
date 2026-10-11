# REEFPRINT live interface release — 1 October 2026

## What was built
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

## Where to continue
Actual KHANYA checkout: C:/Users/USER/.codex/worktrees/reefprint-pwa-live-mvp/REEFPRINT, branch codex/launch-live-demo, remote khanya, PR15. Desktop REEFPRINT is a separate physics Git history; do not push this application from that history. A source snapshot (excluding secrets, model weights and raw imagery) is in handover/latest-live-ui-source.

The temporary authenticated demo is https://arnold-orange-malpractice-transmitted.trycloudflare.com/ and requires this computer, backend8766 and Cloudflare tunnel to stay running. Start public service with scripts/start-cloud.ps1, local with .venv/Scripts/python.exe -m uvicorn webapi.app:app --host127.0.0.1 --port8510. Use actual syntax --host 127.0.0.1 and --port 8510. Never print .workbench/cloud.env or credentials.

Resume prompt: Read LIVE-UI-RELEASE-2026-10-01.md, STATUS.md, BUILDLOG.md, reports/ASSISTANT-AND-VOICE-HANDOVER-2026-09-30.md and EXTENDED-TRAINING-AUDIT report if present. Inspect git status and remote before editing; preserve collaborator changes. Confirm public auth/health and actual tile previews, review training validation without test tuning, recover approved weights by exact SHA if available, verify real voice/provider setup privately, and implement durable cloud survey storage next. Keep notes/results, report and simulated controls provenance-bound. Commit/push through KHANYA PR15 and update both this handover and Desktop copy.

Release state when saved: implementation verified locally; commit/push and public restart verification are recorded in the follow-up BUILDLOG entry, rather than assumed here.


### Publication and live verification — 1 October 2026
Implementation commit0e2255c and merged release93729da pushed to KHANYA PR15. Collaborator commits3e68f12..a719efe retained, including model warmup and measured per-stage timing. Actual preview/count logic remains the common source for provisional phase aliases; unknown pixels stay excluded. Production bundle regenerated after resolving source/generated conflicts.

Post-merge:72 backend checks passed, two relevant desktop/mobile browser rechecks passed; earlier complete seven-browser suite passed. Public/health returned200, cloud_sync/auth_required true and warmed model_ready true; signed-out samples/assistant returned401. Existing user signed-in browser visibly loaded new UI and completed fresh public six-field inference in92.2s, then opened the evidence companion. Local8510 and public8766 restarted. Current process IDs:24020(local),5340(public); exec sessions43430 and18268. QA8770 is separate and can be stopped after use. Temporary tunnel remains the approved existing address.

GitHub workbench API, offline frontend and security checks passed. Base tests initially failed collection because one new API fixture imported optional FastAPI unconditionally; importorskip added to match other API fixtures, while dedicated API CI continues exercising it. CI after that correction must be checked; do not imply all checks are green until observed.

Both extended training runs audited COMPLETE. Native validation foregroundIoU0.6467023, allfiveIoU0.7036325, magnetiteIoU0.4094622/recall0.6948409. Smallgrain is weaker and regresses pentlandite. These are validation scores from selected checkpoints, not test accuracy or production gains. Native epoch12 chosen before a one-off test evaluation; the evaluation-only notebook is being reviewed/launched separately. Active hosted weights/report/gates are unchanged. See reports/EXTENDED-TRAINING-AUDIT-2026-09-30.md.

Sibusiso's eight open PR heads remain unchanged; author acknowledges retired Streamlit UI on19–22. Existing correctness and stacked-base review blockers remain; no duplicate comments or unsafe merge performed. See reports/PR-AUDIT-2026-10-01.md. Optional provider model options are documented; no key or real microphone/LLM call has been verified. An additional provider metadata check hit the approval service usage limit and was not bypassed.
