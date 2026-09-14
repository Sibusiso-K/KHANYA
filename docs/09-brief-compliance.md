# 09 — Brief compliance ledger

**Requested by `docs/07-audit-prompt.md:258` and never built until now (2026-09-14).** This is the
one place where "have we met the brief?" is checkable rather than asserted. Evidence is a path or a
test/experiment name, never prose — if a row cannot point at something on disk, it is not done.

**Session ritual addition (see `WORKBOARD.md` §8): any session that changes a deliverable's state
updates its row here in the same commit.** A stale ledger is worse than none, because it will be
trusted — the same rule that governs `WORKBOARD.md` and `CONTEXT.md`.

---

## 1. The literal deliverables

> Identify **at least three distinct mineral phases** from provided image datasets · an
> **accuracy report** · a **demonstration of how the model's output can be used to adjust plant
> parameters** · real-time · integrates with existing sorting or flotation controls.

| Requirement | Evidence | Status | What a judge would see | Exceeds because… |
|---|---|---|---|---|
| ≥3 mineral phases | `khanya/main:reports/lumenstone_s1_patches_test_metrics.json` (7 classes, nonzero IoU for chalcopyrite 0.8652, galena, sphalerite among others); S2 config in `khanya/main:src/segmentation/lumenstone.py` names pyrrhotite/chalcopyrite/pentlandite | 🟡 Met on S1; **magnetite IoU 0.0000** (1.58% of pixels) — report per-class, do not hide it in the mean. Locality separation for the claim is unverified — see Rule 2 row below | Three-plus phases segmented with real per-pixel accuracy, not a demo classifier | Per-class reporting with an honest zero, rather than a mean that buries it |
| Accuracy report | Bushveld half: `experiments/006-bushveld-chromite-falsification/`, cross-checked bit-for-bit by an independent implementation (`docs/BUILDLOG.md` session 17-ish). Segmentation half: `reports/benchmark_s1_patches.json` — **stale, being regenerated, Workstream B** | 🟡 Bushveld half shipped. Segmentation half blocked on `best.pt` (not in repo) and per-image metrics | A number with a stated method, not a slide | `ScoredMetric` (`src/reefprint/trust/baseline.py`) refuses to construct without trivial baselines and an honest *n* — most accuracy reports at this scale don't refuse to lie |
| Plant-parameter demonstration | `src/reefprint/integrate/opcua_server.py`, `opcua_client.py` (real wire round trip, `tests/test_integrate.py`) **+ `src/reefprint/viz/advisory.py`, `src/reefprint/viz/demo.py` (on screen, `tests/test_viz.py`)** | ✅ **Wired into `reefprint.viz.demo.offline_demo()` 2026-09-15 — a judge now sees it.** Renders without a network read (the offline demo cannot open even a loopback socket, `test_demo_runs_fully_offline`); the identical acknowledgement-and-expiry decision (`AdvisoryRecord.is_expired`) is reproduced in-process — the real wire path is what `test_integrate.py` proves separately | An advisory publish → a simulated setpoint move → a stale advisory refused, setpoint unchanged, on screen | `RefusedStaleAdvisory`/`AdvisoryOutcome` have no field for the previous value — "hold the last setpoint" is unreachable through the type, not merely discouraged. Backup GIF regenerated 2026-09-15, now shows all three panels |
| Real-time | `src/reefprint/trust/latency.py`, `experiments/005-latency-benchmark/` — Stokes inversion and the OPC UA round trip measured, p95 nearest-rank | 🟡 Two REEFPRINT-side stages measured on named hardware. Segmentation inference latency (KHANYA) is unmeasured — Workstream C's J1/J2 kernels add it | A latency number with a spread, on stated hardware, not a single lucky run | p95 nearest-rank rather than a mean, which is what a plant operator actually needs to know |
| Integrates with controls | `src/reefprint/integrate/opcua_server.py` — real `asyncua.Server`; `tests/test_integrate.py` | ✅ Done | A working OPC UA server a judge can point a client at | Advisory, not controller — positioned as replacing a *laboratory turnaround*, not MillStar/FloatStar, which Mintek owns |
| Offline demo | `src/reefprint/viz/demo.py`; `experiments/004-backup-video/` | 🟢 Runs. Backup GIF exists but predates Workstream E's third panel | Full pipeline, screen to screen, no network | Backup video exists for the case the live demo breaks on stage |

## 2. The five judging criteria → our evidence

| Criterion | Evidence |
|---|---|
| **Innovation** | Full per-pixel linear Stokes polarimetry from a rotating-analyser series, extending the dataset authors' own finding that polarisation channels improve segmentation (Korshunov et al. 2025) — see §3 below. Provenance-typed arithmetic (`src/reefprint/quantity.py`) — `DESIGN_TARGET` cannot leave the type unchecked |
| **Feasibility** | R0 hardware budget honestly stated (ADR-0002); every dependency permissively licensed and assignable to Mintek (`SBOM.md`); demo runs fully offline on one laptop |
| **Impact** | Advisory-not-controller framing avoids competing with Mintek's own MillStar/FloatStar; entrainment-risk head (`src/reefprint/heads/entrainment.py`) targets a named metallurgical cost |
| **Technical Execution** | Two independent implementations agreeing bit-for-bit on the Bushveld falsification result; `ScoredMetric` refuses a metric with no baseline; a documented record of retracting our own results (N3, `S3_test_03`, the illumination spec) rather than hiding them |
| **Presentation Clarity** | `reefprint.viz.demo` + backup GIF; ten-minute narrative drafted (`CONTEXT.md` §"The ten minutes") |

## 3. Literature factor → what we do → evidence

Read `CLAUDE.md` §"What the literature says drives accuracy here" first — this table is that
section with the evidence paths added. Rule 10 governs how these rows get written: name the
published method, say why we are or are not using it.

| Factor | Literature says | What we do | Evidence | Status |
|---|---|---|---|---|
| Class-balanced patch sampling | Sample patch centres class-uniformly from probability maps (Korshunov et al. 2025; petroscope README) | Done | `khanya/main:src/segmentation/patches.py` docstring, ~11× magnetite oversampling | ✅ |
| Colour normalisation before augmentation | Colour Correction Matrix (LAB, CIEDE2000) applied before brightness/colour augmentation (Korshunov et al. 2025) | Neither step exists | Measured fragility: `khanya/main:src/robustness.py` — 15% white-balance shift costs 0.39 mIoU | ❌ — Workstream D2 lever 6 |
| Polarisation as extra input channels | XPL→PPL registration, fed as extra channels, improves segmentation — from the dataset's own authors (Korshunov et al. 2025) | This is the REEFPRINT thesis, taken further: full per-pixel Stokes vector, not two states | `src/reefprint/polarim/`, `src/reefprint/bridge/` | 🟡 — independent validation of the direction, not the same claim |
| Registration by SIFT + RANSAC | The published XPL/PPL alignment method (Korshunov et al. 2025); `skimage.feature.SIFT` + `skimage.measure.ransac`, BSD-3, already a dependency | Built and validated on synthetic data 2026-09-14 — `estimate_rotation_centre_sift_ransac`, deterministic by construction (seeded `rng`). **Not yet run against the real archive** | `src/reefprint/acquire/registration.py`, `tests/test_registration.py` (6 tests) | 🟡 — Workstream G step 2, real-archive run outstanding |
| Ensembling | Weighted-voting Res-UNet ensemble beats every single member and beats DeepLabV3/PSPNet (Jiang et al. 2024) | Not built. `CLAUDE.md`'s repo map names `trust/ensemble`; it does not exist | `src/reefprint/trust/__init__.py` (mentions only) | ❌ — Workstream D2 lever 5, gated on J1/J2 finishing early |
| Loss for rare classes | Dice + Focal (Jiang et al. 2024); Dice alone unstable while predictions are diffuse | CE and CE+Dice tried; Focal untried | `khanya/main:src/segmentation/losses.py` | 🟡 — Workstream D2 lever 8 |
| Patch size and budget | 256–384 px at ×50; ~3 h on one A6000 is the published compute budget (Korshunov et al. 2025) | 512 px; 512→2,560-patch step already moved mIoU 0.33→0.71 in-project | `khanya/main:src/segmentation/patches.py:PATCH` | 🟡 — Workstream D2 lever 7 |

**Comparators, so nobody re-derives them:** petroscope ResUNet, LumenStone S1 v1, 7 classes — mIoU
**0.8373** (0.8506 void-borders), per-class 0.7464 (galena)–0.9628 (pyrite). Korshunov et al., S1+S2,
10 classes — magnetite **0.650** (worst of their ten), pentlandite 0.790, pyrite 0.964, PA 0.96.

> ⚠️ **Read-before-cite status.** Korshunov et al. 2025 is CC BY 4.0 and was fetched and read in
> full 2026-09-14. The Jiang et al. 2024 ensemble figures (mIoU 91.65) came from a search summary —
> MDPI returned 403 on direct fetch — and petroscope's training recipe is not in its README at all.
> Both are **indicative, not citable**, until the primary source is read. Same failure mode as the
> Pirard 2007 abstract flagged in `CLAUDE.md`.

## 4. Licence and terms-of-use grants recorded here (not elsewhere, until `SBOM.md` is updated)

**LumenStone terms of use, verbatim** (`https://imaging.cs.msu.ru/en/research/geology/lumenstone`,
read 2026-09-14): *"You are free to use the provided data in your own research work. If you intend
to publish research work that uses this dataset, you have to cite the references whenever
appropriate."* An explicit grant with a citation condition, not an OSI licence — record it as that.

**A skill (as in an AI coding assistant's packaged instruction set) is a development-time tool, not
a dependency. It enters `SBOM.md` only if its code ships in the delivered system.**

**Workstream F, backbone guard widened 2026-09-15.**
`reefprint.segment.backbone.require_permissive_backbone()` previously permitted only
`timm`/Apache-2.0, while KHANYA's actual model (`khanya/main:src/segmentation/model.py`) is
`torchvision.models.segmentation.deeplabv3_resnet50` — a guard that would have refused the real
build had anyone called it. Widened to a `PERMITTED_BACKBONES` mapping including
`torchvision`/BSD-3-Clause (`src/reefprint/segment/backbone.py`, `tests/test_segment.py`).
**This checks the library/architecture licence only.** The `DeepLabV3_ResNet50_Weights.DEFAULT`
checkpoint's own permission chain — COCO (20-class VOC subset) → ImageNet-pretrained ResNet50
backbone — is **not** cleared by torchvision's BSD-3-Clause code licence and is recorded honestly
as **CONDITION**, not OK, in `SBOM.md`'s checkpoint table. **Still outstanding**: pre-uploading
the checkpoint as a pinned Kaggle dataset (sha256 recorded) so `enable_gpu: true` training kernels
— which run `enable_internet: false` — can construct the model at all.

## 5. LLM tooling boundary (Workstream H)

- Kaggle's $10/day, $100/month AI quota applies to **Kaggle Benchmarks** (LLM evaluation), not to
  GPU kernels. It does not fund training. The resource that matters is 30 GPU-h/week.
- Featherless + HuggingFace (10 private models) must not touch the measurement path — Rule 6: no LLM
  computes a mineralogical or control value. The demo runs fully offline on one laptop, so a live API
  call cannot be on stage at all.
- Legitimate uses: drafting and reviewing prose; code assistance; the Curator agent's
  route/select/explain role (Rule 6 permits this); HuggingFace as the download route for
  Apache-2.0 weights if the architecture question ever reopens.
- **We deliberately kept the LLM out of the measurement loop.** Stated here as a design decision,
  because it is the kind of thing that plays well with an audience that values auditability over
  cleverness — and because Rule 6 is otherwise just a constraint nobody gets credit for following.
