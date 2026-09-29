# KHANYA: build and pitch handover

Updated 29 September 2026. This folder preserves the investigation and the build plan requested by the user. The user has approved **retraining** because the S2 checkpoint is missing locally. Application implementation is the next stage, when you begin implementation with Codex Luna or Claude Sonnet.

Read in this order:

1. [BUILD-PLAN.md](BUILD-PLAN.md) — problem, product, innovation, pitch and visual experience.
2. [EVIDENCE-REGISTER.md](EVIDENCE-REGISTER.md) — defensible claims, real data and limitations.
3. [KAGGLE-TRAINING.md](KAGGLE-TRAINING.md) — private S2 run status, output checklist and next-run guidance. The baseline result is in [S2-BASELINE-2026-09-29.md](S2-BASELINE-2026-09-29.md); the test-sealed CE+Dice validation experiment is in [S2-DICE-VALIDATION-2026-09-29.md](S2-DICE-VALIDATION-2026-09-29.md).
4. [IMPLEMENTATION.md](IMPLEMENTATION.md) — ordered tasks, contracts, acceptance checks and prompt for Codex Luna or Claude Sonnet.
5. [SETUP-AND-ASSETS.md](SETUP-AND-ASSETS.md) — actual machine readiness, downloads, accounts and training commands.
6. [PILOT-AND-BUSINESS.md](PILOT-AND-BUSINESS.md) — people, tests, budget, commercial assumptions and scale.

The older dated KHANYA documents remain detailed research context. These current documents take priority where schedules or recommendations differ. The S2 baseline report records the measured result; planning and business documents remain proposals, and nothing here claims production readiness.

## Repository state

- Repository: https://github.com/Sibusiso-K/KHANYA
- Inspected application main: `9181668cffd9350211a9a8a2cf0b44c80f8deaee`.
- Planning branch: `codex/khanya-build-plan`, based on that main.
- Managed application worktree on this computer: `C:\Users\USER\.codex\worktrees\khanya-build-plan\REEFPRINT`.
- Research/physics checkout: `C:\Users\USER\Desktop\REEFPRINT`. Its branch called main is a different history. Do not merge these histories or start application changes there by mistake.
- No app code, model weights, raw datasets or credentials are included in this planning change.

## Current readiness

**Planning and first baseline complete; CE+Dice validation experiment complete.** The private candidate improves the balanced-patch validation mIoU in one stochastic run, but magnetite remains missed and the sealed test set was not re-evaluated. Repeat validation-only runs and dashboard integration remain. See the dated experiment log for results and next steps.

The organiser's supplied email confirms a ten-minute PowerPoint due 1 October 2026. Its six themes are covered below. The repository separately says 13:00; the supplied email does not establish that time. Treat 30 September as the internal freeze and verify the organiser's exact time through the team.
