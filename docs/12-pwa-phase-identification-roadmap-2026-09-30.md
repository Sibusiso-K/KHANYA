# REEFPRINT / KHANYA: PWA and phase-identification handoff

**Decision date:** 30 September 2026. **Owner:** Lethabo. **Status:** implementation plan, not a deployment or a new accuracy result.

The user selected **Supabase + Cloudflare Pages + FastAPI** for the responsive phone/desktop application, **Kaggle for model experiments**, and Azure for Students only as an optional host for a Python container. This supersedes the *framework choice* in `handover/IMPLEMENTATION.md` (which says to retain Streamlit) for the longer-term product. It does **not** make the current Streamlit demo expendable before the 1 October pitch. Keep a working, offline demonstration and build the PWA in parallel behind a tested API contract. The two Git histories remain separate under ADR-0003; application changes belong on KHANYA's branch, and REEFPRINT measurement code enters only through the existing bridge.

## What is true today

- The literal challenge asks for at least three mineral phases identified from images, an accuracy report, and a demonstration of model output informing a plant parameter. The model and simulator must be real computations; plant benefit remains unmeasured.
- The stronger published KHANYA S2 checkpoint is tied to its own report: pooled five-class mIoU **0.5725** on 12 publisher test sections; chalcopyrite **0.5755**, pyrrhotite **0.8695**, pentlandite **0.5468**, magnetite **0.0000** IoU. A separate private Kaggle retrain scored **0.4543** and likewise missed magnetite. Do not swap checkpoints or mix their reports. See `handover/S2-BASELINE-2026-09-29.md` for the private run and KHANYA's merged PR #8 for the stronger checkpoint's report.
- S2 is reflected-light imagery from Norilsk polished sections. It does not establish accuracy on UG2, Platreef, field-phone photos, conveyor feed or a South African plant. The 12-image test has been examined already; do not treat it as a fresh tuning set.
- The existing KHANYA dashboard and simulated OPC UA path are usable evidence for the pitch. The hosted PWA is a product direction. No XRF instrument, physical polarimetric rig, site controller connection or paired South African phase labels have been demonstrated.

## Product boundary and chosen stack

| Part | First implementation | Why / constraint |
|---|---|---|
| Responsive UI | React + TypeScript PWA, static build on Cloudflare Pages | One codebase for phone capture and desktop analysis; installable where supported. Use plain browser access if install is unavailable. |
| Identity, records, storage | Supabase Auth, Postgres, Storage, generated API | Sample IDs, image metadata and report ownership live together. Use row-level security from the first shared deployment; private buckets and short-lived signed URLs for images. |
| Model service | FastAPI + pinned PyTorch checkpoint in a Docker image | Python owns preprocessing, phase inference, QC and evidence manifests. Start locally. Azure Container Apps with student credit is an optional CPU deployment only after measured memory, cold start, runtime and cost. |
| Training | Private Kaggle notebook and versioned run artifacts | GPU experiments are batch jobs, not the serving backend. Keep data, weights and credentials out of Git unless rights permit publication. |
| Delivery and checks | GitHub branch/PR, CI for UI/API/tests, versioned DB migrations and build manifest | A second developer can reproduce each change. Never put Supabase service-role keys in the browser. |

**Free-tier reality:** Supabase Free is limited and may pause inactive projects. Cloudflare Pages is suitable for the static UI, not the Torch model. Azure student credit is finite and GPU access is not implied. The demo must have a local/offline path; a cloud outage must not force a fake prediction. There is no signup needed for QGIS or local FastAPI. Supabase and Cloudflare accounts, project IDs, OAuth redirect URLs and optional Azure student eligibility are setup inputs, not secrets to paste into a chat or commit.

## Data contract and API boundary

Use one immutable `sample_id` (UUID) when the image, assay and location truly refer to the same specimen; otherwise leave them unlinked. Minimal tables: `samples`, `images`, `assays`, `model_runs`, `inferences`, `advisories`, `simulation_events`, `review_actions`. Each row has actor, event time, source/provenance and access owner. Inference records point to private original/mask/preview objects, plus model SHA, code SHA, class map version, image SHA, source dataset, device, QC status and timing. Phase **image-area percent**, XRF **elemental mass percent**, and lab **grade** are different quantities with different units.

Start with the following FastAPI surface, versioned `/v1`. Exact paths are proposed and can be adjusted before frontend work if documented in OpenAPI:

| Endpoint | Input/output and guard |
|---|---|
| `POST /v1/inferences` | Authenticated image/object ID and sample ID; validate type, dimensions and ownership; return job/result ID and status. Refuse if the pinned checkpoint is unavailable. |
| `GET /v1/inferences/{id}` | QC flags, per-phase area and confidence summary, timings, model provenance, signed overlay link; authorize against the caller's sample. |
| `POST /v1/advisories/preview` | Inference ID plus versioned site rule set; return `propose`, `review`, or `hold` with reason. No direct plant command. |
| `POST /v1/simulator/events` | Explicit human approval for a fresh advisory; idempotent command ID; return requested/acknowledged simulator state and audit event. |
| `GET /v1/reports/{id}` | Download the immutable accuracy/evidence package for a named checkpoint and dataset split. |

The browser authenticates with Supabase. The API verifies the user token and ownership server-side. It does not accept a client-supplied “approved” flag without an authenticated actor and event record. Apply migrations in CI/staging before connecting production data. Start with a synchronous local inference if measured CPU latency permits; move to a queue only when requests or image sizes justify it. Avoid optimistic “complete” states before inference finishes.

## Phone and desktop user journeys

1. **Capture / import (phone):** user signs in, chooses or creates a sample, records notes and time, optionally GPS with accuracy/CRS and explicit permission, then adds a microscope image or assay CSV. A phone photo is labelled *unverified modality* and cannot silently enter the reflected-light model. Show upload progress, duplicate detection by image hash and offline/pending state. Offline queue is a later ticket until replay and conflict tests pass.
2. **Analyse (desktop or tablet):** choose a verified micrograph; the viewer shows original, predicted coloured mask, adjustable blend and zoom/pan at full resolution. A reference mask appears only when one exists and is plainly labelled “expert reference.” Clicking a pixel/grain shows class, confidence/uncertainty, image scale if known and provenance. The phase legend is categorical and stable across views.
3. **Interpret:** a side panel shows phase area fractions with denominator, quality flags, unknown/unmodelled share, 2D association and the model's limits. Show “magnetite not reliably identified by this checkpoint” beside its zero score; don't quietly drop the class. Low confidence, out-of-modality or missing model produces a visible `review/hold` state.
4. **Act (simulator):** a metallurgist sees the advisory's evidence and the current simulator setting; approval changes only the simulated regrind tag. Show request, approval, acknowledgement and before/after values on one timeline. The operator can open the exact image and rule version that led to the proposal. No recovery or reagent saving is shown without measured data.
5. **Compare / context:** the desktop map or borehole/depth strip shows *located samples with known CRS*. Clicking a marker opens the linked sample, assay and inferred phase record. If coordinates or downhole survey are absent, show a depth strip/table, not a fabricated 3D body. QGIS is the free tool for checking CRS and source layers; the PWA renders the approved exported geometry. XRF enters as a measured assay layer tied by sample ID, not as a pixel phase label.

### Visual layout and state rules

- Desktop: left sample queue/filter; large central image viewer; right phase/advisory panel; bottom event timeline and evidence drawer. Phone: one task at a time with large capture/status controls and a compact result card; full pixel inspection is available by opening the desktop view or landscape tablet.
- Use distinct badges for **measured**, **modelled**, **expert reference**, **simulated** and **not available**. Colour is never the sole status signal. Provide a legend and a colour-blind-safe palette.
- Every actionable panel displays the named sample, model version, run time and state (`queued`, `processing`, `ready`, `review`, `hold`, `error`). A pending upload cannot be represented as an analysed sample. On a model error, preserve the original image and explain the retry path.
- The primary showcase sequence is: real high-resolution image → model mask with three named phases → honest per-class accuracy drawer → phase/association summary → human-reviewed simulated parameter change → a bad/uncertain example that holds. Geography is supporting context, not the opening visual.

## Improve phase identification: controlled experiment queue

**Owner:** CV engineer with a mineralogist reviewing labels; a process metallurgist owns advisory thresholds. Pre-register runs and use train/validation for choices. Archive every run's seed, data/code/model hashes, split IDs, settings, validation curves, per-class confusion and failure images. The existing 12-image S2 publisher test remains a final regression set, not a tuning dashboard.

| Order | Experiment / diagnostic | Decision gate |
|---|---|---|
| M0 | Reproduce the current stronger checkpoint in the app and verify report/hash/cache integrity. Check S2 label mapping, void-border rule, magnetite pixel counts, duplicate images and exact preprocessing. | Same checkpoint produces its documented predictions; no stale cache. If unavailable, mark it unavailable rather than substitute the weaker Kaggle checkpoint. |
| M1 | Fix all random seeds including patch-centre sampling and worker processes. Run the existing recipe with three seeds and a run-specific output directory. | Variance and class confusion on validation are known; stop treating one run as a reliable improvement. |
| M2 | Inspect magnetite patches and false positives in the six validation images; test class-presence sampling and bounded rare-class oversampling against the M1 recipe. | Magnetite recall/IoU improves on validation without unacceptable loss on the three required sulphides; retain coverage and false-positive counts. |
| M3 | Compare CE, CE+Dice and focal/Dice under matched seeds, patches and compute. Separately test colour/reference correction and acquisition-quality gating; do not feed R% into the RGB model without retraining. | Select only a candidate that improves the predeclared validation objective and lighting stability. Report uncertainty and latency trade-offs. |
| M4 | Compare one published-style ResUNet or DeepLabV3+ baseline only after M0–M3 are reproducible. Use the same specimen/image split and evaluation code. | Keep a new architecture only for measured per-class and decision-level gains, not appearance alone. |
| M5 | Obtain independent South African polished sections with expert phase masks and acquisition metadata; reserve entire specimens or localities for external test. Where possible co-register SEM-EDS/QEMSCAN maps. | Establish transfer accuracy, abstention coverage and repeatability separately from Norilsk; only then consider plant-facing claims. |

Report **per-phase IoU, precision, recall, confusion, macro score, phase-area error, uncertainty/abstention coverage and full-section latency** with image/specimen denominators. Explicitly report both all-section and accepted-only results; a gate that refuses every image is not progress. Retain the current three-sulphide deliverable while improving magnetite. No need to add SAM, an LLM or quantum compute unless a matched experiment establishes a specific benefit.

## Milestones and acceptance

### D0 — 30 September / 1 October presentation gate

Freeze the known working checkpoint/report/demo; verify actual predictions, the accuracy report, a simulated parameter change and a refusal example. Prepare a timed 10-minute deck and backup video. Do not claim the new PWA is deployed or a faster model is proven. The organiser's supplied email confirms the **1 October date**, but not an hour; confirm submission time with the team.

### A1 — application skeleton after the pitch freeze

Create KHANYA application branch with `web/` (React PWA), `api/` (FastAPI), `supabase/migrations/` and a small fixture dataset. Supabase local CLI or hosted Free may be used; Cloudflare Pages Git integration deploys the static UI. Login, private image upload, sample list and an API health/model-availability response work on phone and desktop. CI runs typecheck, build, API tests and migration checks. No real ore upload is required for the first public preview.

### A2 — real model in the web experience

Load the pinned checkpoint with hash verification, run one real S2 image end to end and render the predicted mask, class legend, named run and evidence drawer. Compare shown figures with the frozen report. Full-size image navigation must be responsive and preserve original resolution. QC/error/hold states work without a hidden random-weight fallback. Measure cold and warm CPU latency and memory before choosing a host.

### A3 — decision and spatial context

Wire the existing advisory logic to an explicit simulator endpoint, with approval/idempotency/freshness and audit history. Add assay import and a depth strip; add map markers only from source coordinates validated in QGIS. Show XRF elemental readings with method, units and detection limits when available. No assay-to-image join without matching sample identity.

### A4 — model improvement and external evidence

Run M0–M4 on Kaggle with a fixed validation objective; preserve the best old checkpoint until a candidate beats it by the registered criteria. Seek Mintek/partner lab specimens for M5. Only after external data and process records exist should the team estimate sample-to-answer savings, recovery benefit or site-specific operating rules.

## Setup checklist for the implementer

1. Check the latest KHANYA main and open PRs before editing; retain the separate REEFPRINT branch. Read `reports/ACCURACY-REPORT-2026-09-29.md` (merged PR #8), current advisor/OPC UA code, and the existing dashboard. Use the real current paths if the report name differs.
2. Confirm access to Supabase and Cloudflare. Create a *development* project/site, record project IDs and redirect URLs in a private setup note; keep keys in local environment/host secrets. Enable email login, RLS policies and private Storage before real uploads.
3. Build the API contract and fixture flow locally first. Verify token ownership in tests. Commit schema migrations, OpenAPI contract and a `.env.example` containing names only.
4. Containerize the model API and benchmark memory/latency on the actual target. Check Azure for Students eligibility and the Container Apps estimate only if cloud inference is needed. Do not assume a permanently free GPU or always-on host.
5. On every meaningful build step, update the app branch's handover/build log and open a PR. Do not overwrite older accuracy artifacts or publish raw S2 images, checkpoints or tokens.

## Copy-paste implementation prompt for Luna or Claude Sonnet

```text
Continue REEFPRINT (aka KHANYA) from docs/12-pwa-phase-identification-roadmap-2026-09-30.md. The user chose Supabase + Cloudflare Pages + FastAPI for one responsive PWA, with Kaggle for private training and Azure for Students only as an optional Python-container host. The current 1 October demo and accuracy report must remain usable.

First inspect the latest KHANYA main, open PRs and application checkout; read merged PR #8's accuracy report and the present dashboard, model, advisor and simulator code. Do not merge the separate REEFPRINT history. Implement A1 then A2 on an isolated application branch with source-only commits and a PR. Start with a fixture; add Supabase Auth/Postgres/private Storage with RLS, versioned migrations, a React/TypeScript phone/desktop PWA, and a Dockerized FastAPI inference boundary. Show model unavailable, QC hold and error states honestly. Run one real S2 image through the pinned checkpoint and display original/mask/phase report with hash and source provenance. Test ownership, builds and real inference; update the build log.

After the UI/API path works, implement A3's reviewed simulator action and depth/assay context. Keep XRF and geographic layers distinct from pixel-level phase inference. For model work, follow M0–M4 using train/validation only and frozen external test, with run manifests and per-class metrics; focus first on magnetite failure and reproducibility. Preserve the stronger checkpoint until a measured candidate surpasses it. Do not claim plant impact, South African transfer or real-time full-section operation without measurements. Report what is built, measured and still missing.
```

## Source anchors

- Supabase [pricing](https://supabase.com/pricing), [CLI](https://supabase.com/docs/guides/local-development/cli/getting-started), [MCP](https://supabase.com/docs/guides/ai-tools/mcp)
- Cloudflare [Pages limits](https://developers.cloudflare.com/pages/platform/limits/) and [Workers limits](https://developers.cloudflare.com/workers/platform/limits/)
- FastAPI [container guidance](https://fastapi.tiangolo.com/deployment/docker/); Azure [student offer](https://azure.microsoft.com/en-us/free/students) and [Container Apps billing](https://learn.microsoft.com/en-us/azure/container-apps/billing)
- [LumenStone publisher dataset](https://imaging.cs.msu.ru/en/research/geology/lumenstone) and authors' [Petroscope code](https://github.com/xubiker/petroscope)

Prices, quotas and availability can change; verify them at deployment time. These source links are planning evidence, not proof that the app has been deployed.
