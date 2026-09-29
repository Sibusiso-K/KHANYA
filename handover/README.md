# KHANYA: build and pitch handover

Updated 29 September 2026. This folder preserves the investigation and the build plan requested by the user. The user has approved **retraining** because the S2 checkpoint is missing locally. Application implementation is the next stage, after switching to Luna.

Read in this order:

1. [BUILD-PLAN.md](BUILD-PLAN.md) — problem, product, innovation, pitch and visual experience.
2. [EVIDENCE-REGISTER.md](EVIDENCE-REGISTER.md) — defensible claims, real data and limitations.
3. [LUNA-IMPLEMENTATION.md](LUNA-IMPLEMENTATION.md) — ordered tasks, contracts, acceptance checks and copy-paste prompt.
4. [SETUP-AND-ASSETS.md](SETUP-AND-ASSETS.md) — actual machine readiness, downloads, accounts and training commands.
5. [PILOT-AND-BUSINESS.md](PILOT-AND-BUSINESS.md) — people, tests, budget, commercial assumptions and scale.

The older dated KHANYA documents remain detailed research context. These five documents take priority for the current plan where schedules or recommendations differ. None constitutes a new accuracy result or a production deployment claim.

## Repository state

- Repository: https://github.com/Sibusiso-K/KHANYA
- Inspected application main: `9181668cffd9350211a9a8a2cf0b44c80f8deaee`.
- Planning branch: `codex/khanya-build-plan`, based on that main.
- Managed application worktree on this computer: `C:\Users\USER\.codex\worktrees\khanya-build-plan\REEFPRINT`.
- Research/physics checkout: `C:\Users\USER\Desktop\REEFPRINT`. Its branch called main is a different history. Do not merge these histories or start application changes there by mistake.
- No app code, model weights, raw datasets or credentials are included in this planning change.

## Current readiness

**Planning ready; model execution not ready yet.** Python, Node, Git and repository push access were verified. The existing physics environment has pytest and asyncua, but lacks torch, torchvision, pandas and Streamlit. S2 images and trained weights were not found in either supplied project folder, GitHub releases or workflow artifacts. Retraining is explicitly accepted by the user. The first Luna task is a reproducible S2 training and evaluation run, not a dashboard rewrite.

The organiser's supplied email confirms a ten-minute PowerPoint due 1 October 2026. Its six themes are covered below. The repository separately says 13:00; the supplied email does not establish that time. Treat 30 September as the internal freeze and verify the organiser's exact time through the team.
