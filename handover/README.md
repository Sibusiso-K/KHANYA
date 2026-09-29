# KHANYA: build and pitch handover

Updated 30 September 2026. This folder preserves the investigation and the build plan requested by the user. The user has approved private **retraining** because the S2 checkpoint is missing locally. The dedicated REEFPRINT Supabase project is now active but has an empty schema. Cloudflare Pages and Azure remain optional setup tasks. Application implementation is the next stage, with Codex Luna or Claude Sonnet.

Read in this order:

1. [BUILD-PLAN.md](BUILD-PLAN.md) — problem, product, innovation, pitch and visual experience.
2. [EVIDENCE-REGISTER.md](EVIDENCE-REGISTER.md) — defensible claims, real data and limitations.
3. [KAGGLE-TRAINING.md](KAGGLE-TRAINING.md) — private S2 run status, output checklist and next-run guidance. The baseline result is in [S2-BASELINE-2026-09-29.md](S2-BASELINE-2026-09-29.md); the test-sealed CE+Dice validation experiment is in [S2-DICE-VALIDATION-2026-09-29.md](S2-DICE-VALIDATION-2026-09-29.md).
4. [IMPLEMENTATION.md](IMPLEMENTATION.md) — ordered tasks, contracts, acceptance checks and prompt for Codex Luna or Claude Sonnet.
5. [SETUP-AND-ASSETS.md](SETUP-AND-ASSETS.md) — actual machine readiness, downloads, accounts and training commands.
6. [PILOT-AND-BUSINESS.md](PILOT-AND-BUSINESS.md) — people, tests, budget, commercial assumptions and scale.
7. [PR-6-REVIEW-2026-09-29.md](PR-6-REVIEW-2026-09-29.md) — review/merge record and how REEFPRINT fits with FieldMove Clino, QGIS/QField and Leapfrog Geo.
8. [PR-7-REVIEW-2026-09-29.md](PR-7-REVIEW-2026-09-29.md) — review position on the proposed shadow pilot, domain transfer, metrics and reflectance calibration.
9. [RESPONSIVE-APP-AND-DELIVERABLES-2026-09-29.md](RESPONSIVE-APP-AND-DELIVERABLES-2026-09-29.md) — maps each Mintek deliverable to measured evidence and recommends a free-first responsive/PWA, API, spatial and cloud path.

The older dated KHANYA documents remain detailed research context. These current documents take priority where schedules or recommendations differ. The S2 baseline report records the measured result; planning and business documents remain proposals, and nothing here claims production readiness.

## Repository state

- Repository: https://github.com/Sibusiso-K/KHANYA
- Inspected application main: `9181668cffd9350211a9a8a2cf0b44c80f8deaee`.
- Planning branch: `codex/khanya-build-plan`, based on that main.
- Managed application worktree on this computer: `C:\Users\USER\.codex\worktrees\khanya-build-plan\REEFPRINT`.
- Research/physics checkout: `C:\Users\USER\Desktop\REEFPRINT`. Its branch called main is a different history. Do not merge these histories or start application changes there by mistake.
- No app code, model weights, raw datasets or credentials are included in this planning change.

## Current readiness

**Planning and first baseline complete; next validation-only candidate prepared.** The prior private CE+Dice run improved its balanced-patch validation score in one stochastic run, but magnetite remained missed and the sealed test set was not re-evaluated. A new deterministic candidate selects checkpoints using full-section validation and has not run yet. See [Kaggle training handoff](KAGGLE-TRAINING.md) and the dated experiment log.

Sibusiso's simulated plant-parameter PR [#6](https://github.com/Sibusiso-K/KHANYA/pull/6) was reviewed and squash-merged after tests and security checks passed. Its simulator-only scope and the recommended mobile/desktop tool workflow are documented in [PR-6-REVIEW-2026-09-29.md](PR-6-REVIEW-2026-09-29.md).

The challenge floor is supported by the historical S2 patch report (three nonzero sulphide IoUs, with magnetite failed); the fresh Kaggle baseline is a separate, lower-scoring result. The old planning branch does not contain PR #6's simulator change, so stage from updated main and match the model hash to its report/preflight. See [responsive app and deliverables](RESPONSIVE-APP-AND-DELIVERABLES-2026-09-29.md).

The organiser's supplied email confirms a ten-minute PowerPoint due 1 October 2026. Its six themes are covered below. The repository separately says 13:00; the supplied email does not establish that time. Treat 30 September as the internal freeze and verify the organiser's exact time through the team.

Sibusiso PRs [#10](https://github.com/Sibusiso-K/KHANYA/pull/10), [#11](https://github.com/Sibusiso-K/KHANYA/pull/11) and [#12](https://github.com/Sibusiso-K/KHANYA/pull/12) are under review. CI/security checks pass, but #10 has unresolved statistical and duplicated-field evidence issues; #11 and #12 are stacked on it and have additional comments. None is currently eligible to merge.
