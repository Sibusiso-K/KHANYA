# REEFPRINT / KHANYA cloud connection runbook

**30 September 2026.** Target: a React/TypeScript PWA on Cloudflare Pages, Supabase for identity/records/private files, and a local FastAPI model service. Azure Container Apps is an optional later host for that Python service. This is a setup guide, **not** evidence that the new application is deployed. Implement application code on KHANYA's application history; this REEFPRINT branch records the decision and handoff.

## Current machine check

Node 24.18.0, npm 11.16.0, Python 3.11.9, uv 0.9.30 and Azure CLI are installed. Wrangler was not found on `PATH`. The present checkout has no `web/`, `api/` or Pages project yet. Azure's existing login state could not be read inside the restricted Codex shell (`PermissionError` on the user's `.azure/azureProfile.json`); a clean temporary CLI config reported `Please run 'az login'`. **This does not prove the user is signed out of Azure in their normal terminal.** Supabase is reported connected by the user; the target project and schema have not been verified here.

## 1. Cloudflare account and frontend

Use one **Git-integrated Pages** project for automatic preview/production deployments from KHANYA. In Cloudflare: **Workers & Pages → Create application → Pages → Connect to Git**, authorize the KHANYA repository, then select the actual frontend's root directory (`web/` once built), build command (`npm run build` for the planned Vite app), and output directory (`dist`). Do not create a Direct Upload Pages project first: Cloudflare says its setup mode cannot later be switched to Git integration. Pages serves static UI assets; it does not host the PyTorch/FastAPI model.

For local CLI access, in PowerShell inside the future `web/` folder:

```powershell
npm install --save-dev wrangler
npx wrangler login
npx wrangler whoami
```

`wrangler login` opens Cloudflare OAuth; no token needs to be pasted into source or chat. If the browser callback cannot return to the CLI, `npx wrangler login --device` uses a device code. Before the `web/` package exists, `npx wrangler login` can still be used from a separate temporary directory, but install Wrangler locally in the app when the package is built. Git-integrated Pages can be configured in the dashboard after CLI sign-in; the CLI login itself does **not** connect the GitHub repository.

Frontend build variables: `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY`, `VITE_API_BASE_URL`. The first two are public configuration, subject to RLS. Set them in Cloudflare Pages production/preview settings and in a local ignored `.env.local`. **Never put a Supabase secret/service-role key, Azure credential, Cloudflare API token, or model-file signing key into `VITE_*` or Git.** Configure Supabase Auth site URL and allowed redirect URLs for the final `pages.dev` hostname and local development URL. Use private buckets and RLS before uploading real specimens.

## 2. FastAPI locally

FastAPI is a Python framework, not an account to connect. Add an `api/` project in KHANYA's application history, and develop it locally before choosing cloud hosting:

```powershell
cd api
uv init --app
uv add "fastapi[standard]"
uv run fastapi dev main.py
```

The `uv init` command only applies when creating a fresh `api/` folder; adapt the entrypoint to the actual file. Verify `http://127.0.0.1:8000/docs` and a `GET /health` route. The frontend calls the configured API base URL. FastAPI verifies the Supabase user's JWT and sample ownership server-side, loads the pinned model/checkpoint, and writes provenance/results to Supabase. It must report `model_unavailable` when the checkpoint is absent rather than returning a plausible prediction. Development uses CORS restricted to the local frontend and the deployed Pages origins; production uses HTTPS. A local API is unreachable from the public Pages site, so a public end-to-end demo needs a hosted API or a separate local-only demo mode.

## 3. Optional Azure for Students API host

In a normal PowerShell terminal (outside the restricted Codex shell), inspect existing sign-in before creating resources:

```powershell
az account show --query "{name:name,id:id,state:state}" -o json
az login
az account list -o table
az account set --subscription "<YOUR-STUDENT-SUBSCRIPTION-ID>"
az account show --query "{name:name,id:id,state:state}" -o json
```

If browser sign-in fails, use `az login --use-device-code`. Select the intended student subscription; CLI sign-in does not create or deploy an application. Later, when the API Dockerfile and measured CPU/memory/cold-start are ready, prepare Azure Container Apps with `az extension add --name containerapp --upgrade` and the provider registrations `Microsoft.App` and `Microsoft.OperationalInsights`. Only then choose a region and deploy with `az containerapp up --name reefprint-api --resource-group <RESOURCE-GROUP> --location <REGION> --source ./api --ingress external --target-port 8000`, checking `az containerapp up --help` against the installed extension first. That command **creates billable resources** (potentially a registry, environment and logging workspace), so estimate usage and check available student credit before running it. GPU availability is not assumed. After deployment, set `VITE_API_BASE_URL` to the Azure HTTPS API URL and permit the Pages origins in CORS.

## Connection test, in order

1. `npx wrangler whoami` shows the intended Cloudflare account; `az account show` shows the intended student subscription if Azure is used. No access token is copied into chat.
2. Local PWA signs in through Supabase and uploads a small **fixture** to a private bucket. Confirm a different user cannot read it.
3. Local FastAPI `GET /health` responds, then one authenticated fixture inference returns the pinned model ID, phase mask and provenance; `/docs` exposes the contract. Verify absent-model and unauthorized-sample refusals.
4. Cloudflare Pages Git preview builds the frontend from the KHANYA branch; its auth redirect, sample list and upload work on phone and desktop.
5. Only after benchmarking and a cost check, optionally host the API on Azure. Re-run the same fixture and access-control tests over HTTPS. The simulator remains a reviewed, explicit action, never a direct production plant command.

## Sources (official)

- [Cloudflare Pages Git integration](https://developers.cloudflare.com/pages/get-started/git-integration/), [Direct Upload trade-off](https://developers.cloudflare.com/pages/get-started/direct-upload/), [Wrangler login and whoami](https://developers.cloudflare.com/workers/wrangler/commands/general/)
- [FastAPI CLI](https://fastapi.tiangolo.com/fastapi-cli/)
- [Azure CLI sign-in](https://learn.microsoft.com/en-us/cli/azure/authenticate-azure-cli), [Container Apps quickstart](https://learn.microsoft.com/en-us/azure/container-apps/get-started), [`az containerapp up`](https://learn.microsoft.com/en-us/cli/azure/containerapp)
- [Supabase changelog](https://supabase.com/changelog?types=breaking-change), [Supabase CLI](https://supabase.com/docs/guides/local-development/cli/getting-started)
