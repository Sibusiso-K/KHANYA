# Supabase workspace deployment

The dedicated REEFPRINT project is `uwdrfmwoivibnhpccwxe` in `eu-west-2`. The database migration creates owner-scoped samples, inference results and optimistic-version sample records. `reefprint-private` is a private 25 MB-per-object Storage bucket. Every request to Supabase uses the signed-in user's JWT and a publishable key; the server does not require a service-role key.

## Run the authenticated API

Copy these settings into the ignored `.workbench/cloud.env`:

```env
REEFPRINT_DEPLOYMENT=public
SUPABASE_URL=https://uwdrfmwoivibnhpccwxe.supabase.co
SUPABASE_PUBLISHABLE_KEY=<publishable project key>
```

From the repository, run `./scripts/start-cloud.ps1 -Port 8766`. This binds to loopback for an HTTPS reverse proxy or tunnel. Use one Uvicorn worker: inference jobs and simulator sessions are process-local. Deployment requires the model checkpoint and publisher-held-out images on the API host, along with the Python dependencies and built frontend. Supabase stores uploaded micrographs, inference image/grain artifacts, inference result JSON and sample records. The API's per-user filesystem cache can be reconstructed by opening the library. Simulator sessions and their decision-event log remain local to this host.

`GET /api/config` returns only public configuration. All workspace routes require `Authorization: Bearer <Supabase access token>`. `/api/health`, `/api/config` and the published accuracy report remain accessible before sign-in. The API validates each access token against Supabase Auth's user endpoint, rejects anonymous sign-ins, and keeps each user's uploads, caches, jobs, results and simulator sessions separate. Image requests must carry the bearer header; the frontend fetches them as authenticated blobs. Never place tokens in query strings.

With no Supabase settings, the local research demo allows workspace requests only from loopback. Explicit public mode without Supabase settings fails closed. Always use public mode for a reverse proxy or tunnel: its upstream TCP connection may itself come from loopback.

Email/password sign-up uses the Supabase project's confirmation settings. Confirmed account access has to be verified by the human owner; no human accounts or passwords are invented by deployment tooling. Set the Supabase Auth site URL and confirmation redirect allowlist to the eventual stable HTTPS application URL when available. A temporary tunnel hostname changes on restart.

## Verification performed

- Backend tests cover missing/forged bearer sessions, missing public configuration, non-loopback local access, anonymous-user refusal and separation of users' samples, jobs, results, filesystem caches and simulator sessions.
- A database transaction tested owner A's record creation, compare-and-swap update and stale-write rejection, forbidden owner reassignment, and user B's denied reads/writes to A's rows. Its generated test users and rows were rolled back.
- Schema inspection confirmed RLS on every application table, private storage and a security-invoker record RPC. Supabase security advisors returned no issues. The new foreign-key support index is initially reported as unused (informational).
- The local research records, inference, grain evidence, reports and simulator regression suites remain applicable.

Cloud operations fail visibly when Auth, Storage or the Data API is unavailable. A result is marked complete only after its artifacts and database row have been persisted. Sample records use a database compare-and-swap RPC, so stale writes return 409 without replacing the latest record.
