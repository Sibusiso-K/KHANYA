# Local backend records and cloud readiness — 2026-09-30

## Completed after spatial update e79b046

Sample records now use the running FastAPI backend instead of relying on browser storage. GET and PUT `/api/samples/{sid}/record` share an envelope `{sample_id,version,updated_at,record}`; saves require `expected_version`. Stale edits fail409 rather than silently overwriting another save. Existing browser drafts are loaded only when the server has no record; explicit save migrates them. The UI displays saved server version, unsaved changes and errors accurately. Assay CSV imports are validated and saved with the sample. Browser storage is only a best-effort draft backup.

Records persist beneath ignored `.workbench/records/` using a lock, temporary file, flush/fsync and atomic replace. Known sample IDs only; strict schema, coordinate bounds, finite nonnegative depths/assays, limits and unknown-key rejection. Local single-process storage only, no multi-worker/distributed lock or cloud ownership boundary. Cloud deployment remains blocked until authentication and per-user access are added.

Backend health is refreshed every30seconds. The UI does not label an unavailable API as connected indefinitely.

## Proof

- Frontend production build passes.
- 30 Python tests pass:23record cases and7safety/export tests. Previous12spatial parsing tests also pass.
- Browser saved a clearly labelled QA note on previously empty test_12; HTTP GET confirmed version1 and exact content. Reloading the page, opening test_12 and expanding notes restored the server note. The QA note was cleared through UI and persisted as version2. No pre-existing record was overwritten.
- Actual data/model/checkpoint performance unchanged. Real local model inference and simulation remain wired; no cloud deployment claimed.
- Local service restarted with record API, http://127.0.0.1:8510/. Use scripts/start_workbench.ps1 if stopped.

## Cloud blockers (verified read-only)

Azure CLI has cached enabled student-subscription metadata, but live resource discovery failed AADSTS50078 (expired MFA). Complete `az login` in your terminal. No proof yet of existing resources or remaining credits.

Supabase tools are not exposed in this chat, and no CLI credential or relevant environment configuration was found in the checked standard locations. Reconnect Supabase or provide the project's public URL and publishable/anon key through configuration; do not paste service-role keys into chat. The previous user approval to create a free project is not evidence that a project was created.

Cloudflare account/project/login are unverified. Wrangler is not installed in the inspected app/PATH/cache. Establish official CLI authentication (`npx wrangler login`) or connect the intended dashboard account; verify existing Pages projects before creating any. Actual frontend directory is frontend; Vite output frontend/dist.

## Next implementation

1. Resolve cloud access. Inspect the real Supabase schema/RLS/bucket/auth configuration before migrating.
2. Implement optional login/session, authenticated API requests including protected images, server token validation and owner-scoped data access. Negative ownership tests must precede shared deployment.
3. Configure HTTPS API origin/proxy for frontend fetches AND images/downloads; package checkpoint deliberately with private persistent artifact storage and restart-safe jobs.
4. Deploy backend, then frontend, and verify remotely: login, upload, inference, phase overlay, server record, report, simulator decision attachment. Public UI-only deployment does not meet this criterion.
5. Improve held-out evaluation and actual survey-based 3D interpretation separately; no synthetic geological demo should be reported as measured mineral inference.

Keep using the app worktree/branch and PR15. Desktop REEFPRINT has a different history. Both this file and the spatial handover belong in reports/ on GitHub and handover/ locally.
