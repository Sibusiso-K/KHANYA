# Handover, 2 October 2026 (afternoon): pitch v8, 3-minute video, the live QR app

Read this first in the next session. Then CONTEXT.md, then docs/BUILDLOG.md (top entries).
Branch: `codex/pwa-phase-roadmap` on remote `khanya` (Sibusiso-K/KHANYA). PR 15 has the team notes.

## 1. What exists now (all built from scripts; every number is loaded from result files)

| Deliverable | File | Rebuild |
|---|---|---|
| **Deck, 12 slides** (video embedded on slide 8, real QR on slide 12) | `presentation/output/REEFPRINT-KHANYA-Team-Sonar-pitch-v8.pptx` (not in git: large) | `python presentation/deck-src/build_deck_v8.py` |
| **Presenter script** (joke opener, 10 min, judge Q&A), generated from the speaker notes | `presentation/PRESENTER-SCRIPT-v8.md` | same command |
| **Demo video, 3:03**: pit → wait → laptop fly-through into the real app → belt scan, SWIR layers, clusters, 3D cube → decision → signed record → Ask REEFPRINT → KHANYA on a tablet → evidence → value → money → QR on a phone → Mintek values → end card | `presentation/video/REEFPRINT-v8-demo.mp4` (+ `-embed.mp4` for the deck; not in git) | see §4 |
| **Storyboard + provenance** of every shot | `presentation/video/STORYBOARD-v8.md` (describes the 2:25 cut; the 3:03 cut adds the device shots, spotlights and phone/QR beat, same rules) | — |
| **Live app (free, always on, laptop can be off)** | https://lethabomh14-reefprint.static.hf.space/index.html?guest=1 (Space: https://huggingface.co/spaces/LethaboMH14/reefprint) | `python presentation/belt-monitor/deploy/hf_static_deploy.py` |
| **QR code** (verified: decodes to the URL above) | `presentation/deck-src/img_v8/qr_live.png` | `python presentation/belt-monitor/deploy/make_qr.py <https-url> ../deck-src/img_v8/qr_live.png` |

**Deck order:**
1. Title: the real hyperspectral cube plus a cluster lens. The lens morphs across slides, like v6.
2. The problem: the brief's own words, a 24–72 h timeline wedge, 6–18.5 kt milled blind, and who waits.
3. Why it matters: about 71% of the world's platinum, the 10 pp UG2 gap, R64–153M per recovery point, about 50% of mine energy; chromite, load-shedding and ransomware.
4. Solution: three speeds, one decision; **TRL 4 (self-assessed)**; the brief ticked.
5. Deliverables 1 and 2: the phase map and the accuracy report, zeros included.
6. Deliverable 3: the plant setting (Decisions view, +1.9% sim_, kinetics check).
7. The brain: Sense / See / Doubt / Decide / Prove.
8. Demo video.
9. Feasibility: physics, robustness, **ransomware and hacking**, quantum-safe.
10. **The money, and why Mintek NEEDS it:**
    - who pays (pilot, then ≤ 20% of measured value);
    - the prize;
    - payback chart: 0.04–0.26 pp versus Valterra's +1 and +2 pp;
    - four reasons Mintek needs it: mandate, truth-lab work, feed-forward for MillStar/FloatStar, SA IP through MOTT.
11. Pathway with **TRL 4 → 8 along the timeline**, costs, partners, research, and 38 commits in 24 h.
12. Close: Mintek's Integrity value, the ask, and the QR.

## 2. App changes this session (all tested)

- **Fixed:** the Decisions countdown re-render wiped notes while typing; the note now survives and reaches the ledger. Playwright-verified.
- **Static mode (no server, e.g. the QR site):** the decision record becomes a *browser sandbox*, a SHA-256 hash chain in the visitor's browser, unsigned and labelled so. Approve, verify and checkpoint all work. Tested on the public URL: no errors.
- **Inside a frame** (the Hugging Face Space page), a banner offers "open full screen", because sign-in cookies do not work in third-party frames.
- **Server, for hosting** (`app_server.py`):
  - proxy-aware client IP (X-Forwarded-For; Azure's `ip:port` handled) plus **global per-path ceilings**, so all judges behind one proxy do not share one tiny limit;
  - `REEFPRINT_FRAME_ANCESTORS` (opt-in framing);
  - `REEFPRINT_SEED_USERS`: staff accounts from scrypt **hashes** at start, for hosts with no shell;
  - `manage.py hash-password` (hidden prompt).
  - 17/17 security tests pass.

## 3. What is still needed (in priority order)

1. **Full server on Azure.** Adds sign-in, a shared database, the post-quantum signed record and uploads. Blocked only by your Azure MFA having expired. In **your** terminal:
   - Sign in again:
     ```
     az logout
     az login --tenant ca9a8b8c-3ea3-4799-a43e-5510398e7a3b --scope https://management.core.windows.net//.default
     ```
   - Deploy: `cd presentation/belt-monitor`, then `python deploy/azure_deploy.py`.
     - It uses App Service B1 in South Africa North (about US$13 a month of student credit; stop it after judging).
     - It sets HTTPS-only, always-on and a random data key that is never printed.
     - If South Africa North is refused by the student-region policy, set `$env:REEFPRINT_AZ_LOCATION="northeurope"` and rerun.
   - Test it: `python <scratch>/test_static.py https://reefprint-sonar.azurewebsites.net/`. The same test works on any URL, and guest sign-in happens automatically with `?guest=1`.
   - Then point the QR at Azure (keep the HF link as the backup):
     - `python deploy/make_qr.py https://reefprint-sonar.azurewebsites.net/?guest=1 ../deck-src/img_v8/qr_live.png`
     - `$env:REEFPRINT_QR_URL="reefprint-sonar.azurewebsites.net"; python presentation/deck-src/build_deck_v8.py`
   - Staff accounts:
     - Run `python manage.py hash-password` locally.
     - Then `az webapp config appsettings set -n reefprint-sonar -g reefprint-rg --settings 'REEFPRINT_SEED_USERS=met1:metallurgist:<hash>' --output none`. Use single quotes: the hash contains `$`.
   - Limits:
     - data lives in `/tmp/reefprint`, so a restart clears the guest sandbox and creates new signing keys;
     - earlier checkpoints still carry their own public keys.
   - Hugging Face **Docker** Spaces need HF PRO (US$9/month); `deploy/hf_deploy.py` is ready if you take PRO instead.
2. **ClauDex round 2.** The Codex limit lifted at 13:54; the round was not run. The prompt is in `.workbench/claudex_round2_prompt.txt` (personal, not committed):
   ```
   codex exec -s read-only --json -o <scratch>/r2.txt "$(cat .workbench/claudex_round2_prompt.txt)" < /dev/null
   ```
   Run it with a 10-minute timeout, then log the result in PLAN-v8-REVIEW-LOG.md.
3. **Official logos** (Mintek, TIA, Team Sonar) were not supplied; text names are used. Drop PNGs in `presentation/video/src_v8/` and draw them in `end_ov()` (compose_v8b.py), and add them to slide 12.
4. **Sibusiso to confirm the KHANYA numbers** on slide 5 (PR 15 comment): 0.454 / 77.2% deployed; candidate 0.632 / 85.5%, magnetite recall 89% at precision 26%; test_11 at 78.5 s.
5. **Rehearse.** The script is 1,314 spoken words (excluding the video) in 10:10. That's fast; cut slide 7 or slide 9 talk if you run over. TRL 4 is our **self-assessment**; say so.
6. **The 2:25 storyboard** should get a short addendum describing the 3:03 cut's device and spotlight shots.

## 4. Rebuild the video (only after app changes)

- Needs the secure app on port 8531 (`python presentation/belt-monitor/app_server.py`) and the public static URL.
- Steps:
  1. Narration: `$env:REEF_NARR="narration_v8b.json"; $env:REEF_VODIR="v8b"; python presentation/video/src_v8/make_vo_v8.py`
  2. Recording: `python presentation/video/src_v8/capture_v8b.py` records the desktop and phone runs, plus the spotlight boxes.
  3. Composite: `python presentation/video/src_v8/compose_v8b.py`, about 35 min on this laptop. `--preview 60,120` renders stills.
- Stock clips (Mixkit, outside git) live in the session scratchpad `stock/`. Set `REEF_STOCK` if you move them. IDs: 45821, 48993, 46059, 45815, 45823, 23693, 4767, 47783, 42664, 45825, 4380, 22032, 23211; devices 48285 (laptop), 100088 (tablet), 28300 (phone).

## 5. Rules that still apply

- No proprietary Mintek data.
- Never print or commit keys (`.workbench/cloud.env`, `data_secure/`).
- External LLM routing stays off.
- No plant connection from the demo host.
- Mintek and TIA are named only as partners "we are asking to work with".
- Tags on every number.
- Push to `khanya` without force; tell Sbu on PR 15.
