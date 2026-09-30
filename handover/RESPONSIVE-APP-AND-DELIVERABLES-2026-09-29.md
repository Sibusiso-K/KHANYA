# Responsive REEFPRINT app and Mintek deliverables

Updated 29 September 2026. Decision record for the phone/desktop app question. This is a scoped build recommendation, not a claim that a PWA, cloud backend, XRF integration, or 3D geology is already implemented.

## Can one responsive app be the product now?

Yes. REEFPRINT can be one browser application with role-appropriate views: a phone-sized capture/sync workflow and a desktop analysis/evidence workspace. The current KHANYA interface is already a local browser-based Streamlit app with an offline inlined dashboard. It accepts a reflected-light micrograph, runs the segmentation/advisory path, and has responsive evidence panels. It is not yet an installable PWA, a multi-user service, an offline sync client, or a phone-native geological compass. A PWA shell can be built over the current APIs after branch alignment; that alone does **not** establish model accuracy or a plant-control result.

The competition deliverable can be met without a production PWA. For judging, a laptop browser view with one real image, true predicted phase overlay, held-out report, and a demonstrated simulator parameter change is stronger and safer than adding login/cloud/mobile sync that is not needed to validate the science. If time permits, make the existing browser dashboard usable at phone widths and show a field sample card; label capture/sync as prototype unless it persists and survives offline/reconnect tests.

## Deliverable evidence map

| Brief item | Evidence to show | Current status / caveat |
|---|---|---|
| Trained tool identifies at least three mineral phases | LumenStone S2 v2 reflected-light input; predicted masks/overlay and class legend for chalcopyrite, pyrrhotite and pentlandite | Met as a retrospective dataset result; these three classes have non-zero pooled IoU. This is a Norilsk analogue, not South African ore. |
| Accuracy report | `reports/lumenstone_s2_patches_test_metrics.json` plus run provenance in `handover/S2-BASELINE-2026-09-29.md`; show per-class metrics and confusion/error examples | The historical report at the fixed benchmark checkpoint gives background 0.8709, chalcopyrite 0.5755, magnetite 0.0000, pyrrhotite 0.8695, pentlandite 0.5468 IoU; pooled mIoU 0.5725, pixel accuracy 0.8914, 12 held-out sections. This fails magnetite completely. It is not a fresh Kaggle score. |
| New Kaggle baseline report | `handover/S2-BASELINE-2026-09-29.md` | Separate run: checkpoint `fb78727d…`, pooled mIoU 0.4543 and pixel accuracy 0.7716. Three sulphides nonzero, magnetite 0.0000. Keep this report with this hash; do not blend it with the historical 0.5725 checkpoint. |
| Demonstration that model output can affect a plant parameter | On updated `main`, PR #6 added OPC UA exchange into a **simulated** `regrind_enabled` state, including preflight, stale/unsafe refusal and audit state. Show initial value -> accepted proposed command -> acknowledged simulator value; then show stale refusal leaves value unchanged. | Software integration evidence only; not a live PLC, plant response, optimal setting, recovery gain, or safety validation. Verify main at the stage and use its expected checkpoint/preflight. The current planning branch is behind the merged simulator change. |
| PWA and cross-device workflow | Responsive browser UI, upload/capture, sample metadata, prediction evidence and optional map | Useful product direction; not required for the three competition deliverables. Do not claim offline sync or phone XRF pairing until actually implemented/tested. |

The `0.5725` historical patch report can support the minimum three-sulphide floor, but it must be presented alongside the failed magnetite score and the limitations. The fresh Kaggle baseline is worse; it still has nonzero pooled IoU for three sulphides, but its chalcopyrite and pentlandite precision/IoU are weak. The CE+Dice candidate reached 0.5300 on validation patches only and has not had the held-out test evaluated; it is not a winner or a test report. Before staging, choose one exact checkpoint/report pair and make the visible file hash agree with the app preflight. Do not silently swap checkpoints.

## UI direction from the four mockups — 30 September

Use the white mockup's legibility and calm hierarchy with the focused three-panel analysis flow from the dark scan mockup. Borrow the field timeline, confidence/quality controls, and explicit “simulator only” treatment from the other two. Keep a clear source label next to every value; the mockups' sample IDs, assay values, 3D layers, phase percentages, uncertainty bars, plant settings and charts are illustrative and must not be copied into live screens as if measured.

**Desktop workbench:** a restrained header holds project, site, sample/section selector, last sync and user role. Below it, use three responsive columns: (1) sample/section rail with depth, acquisition, notes, source files and linked assays; (2) the largest panel, showing the original micrograph and aligned model overlay with Raw / Overlay / Uncertainty controls, zoom, scale provenance and a stable named phase legend; (3) an evidence panel with the exact model/checkpoint, measured benchmark report link, per-phase IoU/precision/recall, current sample's pixel/area estimates, quality/refusal flags and next review action. The current-sample estimate must be labelled as model output; the benchmark score belongs to the named evaluation report and is not the sample's accuracy.

Below the three panels, show one compact traceable chain: **model output → human-reviewed advisory → simulator request (before/proposed) → acknowledged simulator state**. Approval must identify the reviewer and advisory revision. Always show “SIMULATOR ONLY · NO LIVE PLANT CONTROL”; an unacknowledged request is pending, not applied. Include a hold/refusal state beside the accepted example so users see how the system handles weak or stale evidence.

Keep **Geology / 3D** as a separate view that uses the available screen area for map, cross-section or depth strip. A 3D drillhole or terrain view requires actual collar coordinates, CRS, survey/depth intervals and a true sample join. If those are missing, use a measured depth table or say “location unavailable”; never draw an invented orebody. XRF stays in an assay-context card with element, concentration, unit, method, detection limit and source. It is elemental evidence, not mineral identification. Only pair it with an image when both records share a verified sample ID.

**Phone flow:** sign in → capture/create a sample record → add notes and optional GNSS with accuracy/CRS → attach a microscope image and/or assay export → see upload and analysis status. At small widths the desktop rail becomes a sample selector, the image stays first, and evidence/actions become stacked sections. Show a pending/offline badge only if a durable local queue is implemented and sync behavior is tested. An ordinary phone photo is not a valid microscope input unless the model has been trained/evaluated for it.

**Deliverable mapping in the interface:** the analysis view shows one real image with three or more named predicted phases; the Model/Reports view shows the frozen accuracy report for the exact checkpoint and makes failed classes visible; the lower process chain shows a real model result feeding a reviewed, acknowledged **simulated** parameter change, with a hold case. Do not label pixel accuracy “mineral identification accuracy” or use an uncalibrated score as reliable confidence. A PDF/sample report and the accuracy report are different outputs and must remain separate.

## Cloud connection handoff — current auth boundary

The Figma connector is authenticated with design-file access, but this handoff does not yet identify a REEFPRINT-specific Figma file. A dedicated Supabase project was created in the current organization after the user approved the $0/month project creation estimate: **REEFPRINT**, region `eu-west-2`, project ref `uwdrfmwoivibnhpccwxe`, state `ACTIVE_HEALTHY`. Its `public` schema is empty; no schema migration has been applied yet. Free-plan quotas and inactivity pausing still apply. Cloudflare and Azure are not needed for local UI/model development.

For Cloudflare Pages, connect the KHANYA repository through **Workers & Pages → Create application → Pages → Connect to Git** and authorize only the intended repository. Git integration gives automatic deploys and PR previews. If using Wrangler locally, run `npx wrangler login --use-keyring`, finish browser authorization, then `npx wrangler whoami`; report the Pages project name and account ID only. Never paste an API token into chat. For Azure, when FastAPI is ready to host, run `az login` and `az account show`; share the student subscription name/ID only if we are deploying. `az account set --subscription <id>` selects the intended subscription. The access token itself must stay local. Azure is optional: use Azure Container Apps only after the model API is containerized, health-checked and its student-credit budget is understood. No Cloudflare or Azure credential needs to be pasted here; browser/CLI login is the auth flow.

## What to build, in order

**Hackathon/stage build (offline first):**

1. Bring the implementation branch forward to the reviewed main commit containing PR #6; retain the two-name/author history and do not merge the separate REEFPRINT physics branch history.
2. Preserve Streamlit + the current inlined responsive UI for the stage. It already keeps model files local and can run without a cloud login or internet after setup. Fix the mobile viewport issues that matter for the demo, not the whole framework.
3. Keep FastAPI as a later API boundary if an independent web frontend is needed. Wrap the existing Python inference and advisor; do not reimplement or duplicate them in JavaScript. Routes can be `POST /samples`, `POST /predict`, `GET /reports/{id}`, and `POST /simulator/commands` (simulator route must reject live endpoints by construction).
4. Keep the first phone workflow modest: sample ID, timestamp, location if the phone grants permission, notes, photo capture/upload, and an XRF CSV/manual result attachment. Persist locally and export a bundle. Browser geolocation needs a secure context; an intranet phone-to-laptop demo should use HTTPS or provide coordinate entry. The XRF is **not connected** without a brand/model/protocol; manual/CSV import is a truthful first integration.
5. For later offline capture, add a service worker and IndexedDB queue with UUID/idempotency, explicit pending/synced/error states, and tests for reload/retry/duplicate sync. Keep high-resolution images and metadata linked by immutable IDs/hashes.

**Free/open-source implementation choices:**

| Need | First choice | Why / limits |
|---|---|---|
| UI and PWA | React + Vite + TypeScript + CSS/Tailwind (all open-source), or keep Streamlit during the stage | React gives stronger phone/desktop navigation and installable PWA control. Streamlit is faster to retain and already renders current evidence. Choose one UI at a time; avoid a framework rewrite before the core demo is frozen. |
| Python model/API | Existing PyTorch code; optional FastAPI (MIT) wrapper | Keep inference in Python, with same offline machine/model. Kaggle is for training, not a durable production API. A free cloud CPU may cold-start or lack RAM for this ~160 MiB checkpoint; measure before hosting. |
| Local records | SQLite now; PostgreSQL/PostGIS later | No account, payment, or network needed for judging. QGIS reads GeoPackage/CSV for spatial checks. |
| Desktop spatial QA | QGIS Desktop | Free/open-source GIS for CRS, sample maps and 3D map view. It is not a Leapfrog geological implicit modeller. |
| Phone field capture | REEFPRINT sample form/PWA or QField | QField is a free/open-source QGIS-based field collection app. It is a proven alternative for generic GIS forms, but not a replacement for structural-clino measurements unless that specific workflow is implemented. |
| Browser map | Leaflet/MapLibre for 2D; CesiumJS only if the 3D context adds real value | Plot actual coordinate-bearing samples, assay and model layers with CRS/provenance. Start with points and depth intervals. No interpolated orebody surfaces until there is enough validated drillhole/geology data. |
| XRF | Manual entry/CSV first; vendor SDK/export protocol later | Elemental wt%/ppm is different from image-area phase %, and is not phase identification. Preserve device, units, method, timestamp, calibration and detection-limit metadata. Do not infer phases from elements without validated mineralogical constraints. |
| Simulator | Existing local OPC UA simulator path | The stage needs an observable changed simulator state and refusal case; this is not plant control. |

## Free backend and auth choice

Do not add a hosted backend to the stage-critical flow. Keep local inference + simulator working offline. If a multi-user cloud prototype is needed after the pitch, start with **Supabase Free** as the application data layer (managed Postgres, Auth, Storage, API, enable PostGIS); keep the model inference FastAPI service separately deployable or local. Current official limits list 2 free projects, 500 MB database, 50,000 MAU, 1 GB file storage and 5 GB egress; free projects pause after one week of inactivity and there are no paid-plan backups. This makes it convenient for a small prototype, not a production guarantee. Keep the service interfaces portable so data can move to a mine-controlled Postgres/PostGIS.

Firebase is a good quick web/mobile identity option with generous Spark quotas for Auth, Firestore and Hosting, but it is less natural for relational assay/sample/spatial joins. Its Spark plan does not allow paid Google Cloud products such as Cloud Run, which matters if the Python/PyTorch FastAPI model is to run there; phone SMS is separately billed. It remains a reasonable Auth-only option if the team already knows Firebase, with the Python inference service elsewhere.

Azure Container Apps has a consumption free grant (180,000 vCPU-seconds, 360,000 GiB-seconds and 2 million external requests/month on the official page), but resource overages and adjacent services can cost money. Azure for Students currently advertises $100 credit for 12 months, subject to eligibility and then service shutdown unless upgraded. Consider only if the team verifies eligibility, sets budget alerts, and understands shutdown/overage behavior. Do not call any cloud plan “free forever” or store plant images in a public bucket.

Use Figma for screen architecture, visual tokens and review; it is not the app runtime, auth provider or database. The connected Figma workflow can produce the design and exportable references; implement the chosen design in the repository. Lovable can scaffold a disposable React prototype, but the current free plan has limited build/Cloud credits and generated cloud components should not become a required dependency. Keep source in KHANYA GitHub and ensure all secrets live outside the repo.

Official current pricing/source checks (recheck before signup):

- [Supabase Free plan and limits](https://supabase.com/docs/guides/platform/billing-on-supabase)
- [Supabase PostGIS guide](https://supabase.com/docs/guides/database/extensions/postgis)
- [Firebase pricing](https://firebase.google.com/pricing) and [Spark plan limitations](https://firebase.google.com/docs/projects/billing/firebase-pricing-plans)
- [Azure Container Apps billing](https://learn.microsoft.com/en-us/azure/container-apps/billing) and [Azure for Students](https://azure.microsoft.com/en-us/free/students)
- [QField free/open-source licence](https://docs.qfield.org/get-started/license/) and [QFieldCloud self-hosting](https://docs.qfield.org/reference/qfieldcloud/self_hosted/)
- [Leapfrog Geo licence requirement](https://help.seequent.com/Geo/4.1/en-GB/Content/licences/licences.htm)
- [Lovable pricing](https://lovable.dev/pricing)

## Acceptance checklist before calling a PWA or deliverable complete

- [ ] One frozen checkpoint hash is used by both inference and its accuracy report; per-class scores, failed classes and test protocol visible in the UI.
- [ ] Run one representative image from the documented modality, show original/overlay/legend and actual runtime; no screenshot-only mock prediction.
- [ ] Use at least three nonzero-scoring phase labels; explicitly display magnetite miss and domain shift caveat.
- [ ] From the real model/advisor output, show a bounded simulator parameter transition and audit/acknowledgment. Show an abstain/stale case that leaves state untouched.
- [ ] Label all process outputs “simulated”; no implied recovery, reagent or mill optimisation measurement.
- [ ] Phone width (360 px) and desktop width (1440 px) remain readable; keyboard, contrast, accessible labels and non-colour-only class legend work.
- [ ] If calling it a PWA: manifest/install succeeds, HTTPS behavior is tested, offline sample write survives restart, sync retries are idempotent, conflict/error behavior is visible, and images are hash-linked.
- [ ] If cloud auth is enabled: protected API verifies tokens server-side, access policies isolate users/organisations, storage is private by default, and secrets are outside Git.
- [ ] QGIS/3D plots only verified coordinates and preserve CRS/depth/provenance; no false spatial joins or unvalidated orebody interpolation.

## Tool distinction

We are **not** recreating Leapfrog Geo wholesale. It is licensed commercial 3D geological modelling software. For the hackathon, QGIS plus a browser map handles coordinates, sample points, assay overlays, simple depth sections and 3D camera context for free. That is enough to make XRF and samples explorable, not enough to claim Leapfrog-equivalent implicit modelling or resource estimation. QField is an optional generic mobile GIS client. REEFPRINT's own phone/PWA adds the model-linked image workflow that QGIS/QField do not provide out of the box. Do not buy or depend on FieldMove Clino; a small sample/photo/location form is not a structural-geology clinometer and should be named accordingly.

