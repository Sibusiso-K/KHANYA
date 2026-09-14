# 2026-09-14 — Anchor the brief and the literature in the rules, fix a stale number, spend the idle GPU

Plan agreed 14 Sep 2026, ahead of implementation. Kept verbatim (minus tooling scoping, which is a
session-local aside, not project state) so the reasoning behind the day's commits is inspectable
later without reconstructing it from the diff. Status of each workstream lives in `WORKBOARD.md`
§3 and `docs/09-brief-compliance.md`; this file is the record of *why*, not the live tracker.

## Context

**14 Sep 2026. Final 1 Oct 13:00 — 17 days. Feature freeze 25 Sep — 11 days.**
(`WORKBOARD.md` said 19 days; written on the 12th, stale — corrected in this session.)

This plan answers what the domain lead asked: where the official brief should live so every task
is measured against it, whether we meet it, how we win, and what to do with the Kaggle GPU quota,
licence-clean pretrained models, and the Featherless/HuggingFace API.

**Extended same day** after a literature pass on ore-microscopy segmentation: the domain lead asked
that the factors which actually drive the deliverables be found in the research and then **written
into the rules**, so every future task aims at them by default. That is Workstream I, and the
findings reorder Workstreams D2 and G below.

### Correction to a number reported earlier in this session

`khanya/main:reports/benchmark_s1_patches.json` was first read as **S1 mIoU 0.3295 vs the published
ResUNet's 0.8373** — a 2.5× gap. **That benchmark file is stale and the gap is far smaller.**
Verified directly:

| File | Committed | S1 mean IoU | chalcopyrite IoU |
|---|---|---:|---:|
| `reports/benchmark_s1_patches.json` | `1cda84d`, 17 Aug | 0.3295 | 0.0003 |
| `reports/lumenstone_s1_patches_test_metrics.json` | `ebf2b15`, 24 Aug | **0.7116** | **0.8652** |

Same seven classes in the same order, same 20 test images, same sliding-window-at-native-resolution
protocol. The benchmark file scores **cached predictions** (`src/benchmark.py`: *"Uses the CACHED
predictions in data/derived/… no inference"*) from the superseded 512-patch checkpoint; the model
was then retrained at 2,560 patches (`scripts/run_s1_retrain.cmd`) and the cache was never re-made.

**Two consequences, and they reorder the whole plan.**

1. **A stale artefact in `reports/` currently tells a judge we score 0.33 against a public 0.84.**
   Re-caching predictions and re-running `src/benchmark.py` fixes it at **zero GPU-hours** — the
   cheapest credibility gain available, and it happens first.
2. **512 → 2,560 patches moved mIoU 0.33 → 0.71.** In-project evidence that the binding constraint
   is *patches seen*, not architecture — the empirical case for spending the idle GPU on budget
   rather than a model swap.

The real position is **≈0.71 against a published 0.84**, cross-version (published is S1 v1, ours
v2) — respectable, not embarrassing. The cross-version caveat turns out to be removable without
retraining; see the research anchor, finding 3.

### Where the brief lived, and why that was a problem

The literal deliverables appeared **verbatim in two places that disagreed**: `WORKBOARD.md` §2
(current) and `docs/08-handover.md` §4 (stale — still said *"No OPC UA server"*, *"No latency
benchmark exists anywhere"*). `CLAUDE.md`, the constitution that outranks everything, did not carry
the deliverables at all — only the challenge title. There was no requirements-traceability ledger;
`docs/07-audit-prompt.md:258` asked for one and it was never built.

### Honest scorecard, 14 Sep

| Requirement | Where we actually are |
|---|---|
| ≥3 mineral phases | Three sulphides carry it on S2. Magnetite IoU **0.0000** (1.58% of pixels) — report per-class, say so plainly |
| Accuracy report | Bushveld half shipped, cross-checked bit-for-bit. Segmentation half blocked on per-image metrics + a checkpoint not in the repo |
| Plant-parameter demonstration | Built and tested (OPC UA + simulated client + stale-advisory refusal) — not wired into `reefprint.viz.demo`, so a judge never sees it |
| Real-time | Two REEFPRINT-side stages measured; segmentation inference unmeasured |
| Integrates with controls | ✅ genuinely done |
| Offline demo | 🟢 runs, backup GIF exists |

### Why ours can win

Already built, and of a kind other entries will not have: refusal is a **type**, not a warning
(`trust.abstain.Abstention` has no field for the previous value — "hold the last setpoint" is
unreachable); provenance travels through arithmetic (`DESIGN_TARGET` can never be reported);
advisory, not controller — a real OPC UA server with an acknowledgement-and-expiry contract,
positioned as replacing a *laboratory turnaround*, not MillStar/FloatStar, which Mintek owns; a
documented record of retracting our own results (N3, `S3_test_03`, the illumination spec — worth
more to a MOTT assessment than a clean-looking story); two independent implementations agreeing
bit-for-bit on the Bushveld result; and `ScoredMetric`, which refuses to construct without trivial
baselines and an honest *n*.

**One new argument from the literature pass, the strongest version of the thesis so far.** The
LumenStone authors — the people who built the dataset everyone benchmarks on — register XPL images
to PPL and feed them to the segmentation network as additional input channels (Korshunov et al.
2025), and report it as an improvement. That is independent validation, from the dataset's own
creators, that polarisation carries information reflectance does not. Our claim goes further on the
same axis: not two polarisation states as extra channels, but the full linear Stokes vector
recovered per pixel from a rotating-analyser series. Framed that way the novelty is a degree past
published practice in the same direction — far more defensible to a judge than a claim that nobody
has been here, and it retires the temptation to say "nobody uses polarised light", which `CLAUDE.md`
already forbids as false.

### Decisions taken (14 Sep)

- **Retraining: Lethabo drives it on Kaggle**, mounting KHANYA's training code as a private
  dataset — the pattern `experiments/007–010` already use. No cross-branch editing; ADR-0003 holds.
  Artefacts handed to Sibusiso to commit on `main`.
- **P5: fix the determinism, then re-run** — yields to the brief work if the freeze is threatened.
- **Entrainment head: ship as a clearly-labelled structural proxy**, illustrative constants and all,
  with provenance visible. No new domain claims.

---

## Plan

### Workstream A — anchor the brief (day 14, ~2 h, no dependencies)

- `CLAUDE.md`: a "What we are judged on" section — deliverables verbatim plus the five criteria.
- New `docs/09-brief-compliance.md` — the traceability ledger `07-audit-prompt.md` asked for. One
  row per literal requirement: `Requirement | Evidence (path/test/experiment) | Status | What a
  judge would see | Exceeds because…`. Evidence is a path or a test name, never prose. Second table:
  the five judging criteria → our evidence.
- `WORKBOARD.md`: §2 gains an Evidence column pointing at the ledger; fix the stale day count; §8
  gains "any session that changes a deliverable's state updates its ledger row in the same commit."
- `docs/08-handover.md` §4: replace the stale table with a pointer to the ledger, so the two copies
  cannot disagree again.

### Workstream B — the stale benchmark (day 14, zero GPU, highest value per hour)

Re-cache S1 predictions from the current checkpoint and re-run `src/benchmark.py`. Replaces 0.3295
with ≈0.71 in the file a judge would open. Blocked on the checkpoint, which is not in the repo — if
Sibusiso cannot produce `best.pt`, this waits on Workstream C.

### Workstream C — spend the GPU (days 15–20)

**Prerequisite, cross-person:** LumenStone S1 and S2 are on neither Kaggle nor this checkout (only
`S3_v2.zip`, 5.2 GB, is here). ~1.1 GB upload from Sibusiso, or re-fetch from source. Biggest
schedule risk, and it is coordination, not engineering.

**Three additions to that same ask, made once:**

- **LumenStone V1 — 30 images (10 samples × 3 imaging variations).** Converts
  `khanya/main:src/robustness.py` from synthetic perturbations to measured evidence, which its own
  docstring already says is the right thing.
- **The S1 v1 test-set stem list** (16 names). Runs the subset check in D2 and, if it holds,
  produces a directly-comparable number from the checkpoint we already have.
- **`best.pt`**, which Workstream B is blocked on.

Reuse, don't rewrite: `train_patches.py` is already env-parameterised (`KHANYA_SUBSET`,
`KHANYA_EPOCHS`, `KHANYA_PATCHES_PER_EPOCH`, `KHANYA_VAL_PATCHES`) with per-epoch `last.pt` resume.

**Vary exactly one factor first: the patch budget. Do not switch architecture** — 4–6 PT-days, voids
every downstream calibration.

| Job | Config | Patches | Est. wall-clock |
|---|---|---:|---|
| J0 probe | `EPOCHS=2 PATCHES_PER_EPOCH=256` | 512 | 20–40 min |
| J1 S2 long | `EPOCHS=80 PATCHES_PER_EPOCH=500 VAL_PATCHES=128` | 40,000 | 1.5–3 h |
| J2 S1 long | as J1, `KHANYA_SUBSET=S1` | 40,000 | 1.5–3 h |

Total ≈8–14 GPU-h of ~60 available. GPU-hours are not the constraint; the dataset upload and
attention are.

Kernel pattern: copy `experiments/007-s3v2-registration/{kernel_entry.py,kernel-metadata.json}`
into `experiments/011-kaggle-gpu-probe/`, `enable_gpu: true`. Emit per-image metrics and measure
inference latency with `reefprint.trust.latency.measure_stage`.

### Workstream D — benchmark honestly (days 21–23)

Held constant: S1 v2, the authors' 20-image test split, the `_LOOKUP` class map, sliding window
512/overlap 64, `border_width=5`, seed 42. Report both plain and void-border columns.

Rows: ① majority-class via `TrivialBaselines`; ② metadata-only →
`NotApplicable("LumenStone ships no per-section acquisition metadata")`; ③ colour-only per-pixel RGB
classifier (CPU, minutes) — answers "is it just a colorimeter?"; ④ compute-matched ablation
(512-patch checkpoint); ⑤ published ResUNet, cited, not recomputed.

Caveats in the JSON, not droppable prose: published is S1 v1, ours v2 — indicative unless the stem
check in D2 closes it; we did not re-run their model; our test set has been inspected repeatedly, so
this is retrospective, not clean held-out; `petroscope` is GPL-3.0 and not a dependency — protocol
reimplemented, numbers cited.

**On locality (Rule 2): partly "not closable".** Each subset is a single deposit — within-subset
locality generalisation is not estimable, honest *n* = 1. `ScoredMetric` refuses a flattering *n*,
and that refusal is the reportable result. What is doable: one real deposit-disjoint number (train
S2, evaluate on S1's shared classes, n=2 — expected to score badly), plus a section-level cluster
bootstrap labelled "understates locality uncertainty."

### Workstream D2 — how we approach or beat the published 0.8373

**Three different answers to "can we just use their model", and only one is yes.**

| Layer | Verdict |
|---|---|
| Their published numbers | **Yes** — citable. Already doing it. |
| `petroscope` code | **No.** GPL-3.0. Copyleft into a deliverable that must be assignable to Mintek is gauntlet finding S3. |
| Their trained weights | **No** — licensing is the lesser reason. Submitting someone else's trained mineral identifier into a MOTT assessment where "creators receive invention credits" forfeits the thing being assessed. |
| The architecture family | **Yes.** ResUNet is a ResNet encoder + U-Net decoder — available via `segmentation_models_pytorch` (MIT) with `timm` encoders (Apache-2.0). |

**Removing the cross-version asterisk — near-free.** "Each new version contains all previous images
plus additional samples" — S1 v1 is 59 train + 16 test, v2 is 64 train + 20 test. So:

1. Obtain v1's 16 test stems, check `set(v1_test) <= set(v2_test)` — minutes.
2. If it holds: evaluate the checkpoint already trained on exactly those 16 images. Direct,
   like-for-like against 0.8373, zero GPU-hours, zero contamination.
3. Only if it fails does the expensive train-on-v1/eval-on-v1 path return —
   `lumenstone.py:67`'s `SUBSET_VERSION` map makes that a one-line change.

Report the 16-image number with its own CI — n=16 is a wide interval.

**Levers already pulled — do not re-plan.** Native-resolution patches; balanced class centring
(~11× magnetite oversampling — precisely what petroscope's README recommends); LR tuned to 2e-4
because 1e-3 stalled minerals at IoU 0.0; flip augmentation with colour jitter deliberately
excluded because reflectance is the signal.

**Levers not yet pulled, in order of expected value per hour:**

1. **Patch budget** — 2,560 → 40,000. The one proven in-project lever (5× budget bought
   +0.38 mIoU). Env vars only.
2. **`BATCH_SIZE = 2` → 8–16 — a real accuracy lever, not just speed.** `train_patches.py` calls a
   plain `model.train()`, so BatchNorm runs in full training mode on batches of two — noisy
   statistics, poor eval behaviour. A CPU-era artefact, free to fix on a 16 GB GPU.
3. **Mixed precision** — absent. Roughly doubles throughput at 512², doubling patches per GPU-hour.
4. **The aux head is dead weight.** `aux_loss=True` but only `["out"]` is used in the loss.
   Torchvision's own recipe adds `0.4 × aux_loss`.
5. **Seed ensemble — the literature's strongest lever for this task, and it pays twice.** Jiang et
   al. 2024 report a weighted-voting Res-UNet ensemble at mIoU 91.65, explicitly outperforming
   individual members and beating DeepLabV3. For us: 3–5 seeded runs of J1/J2, and the same runs
   yield per-pixel disagreement — the calibrated-uncertainty and abstention evidence we claim to
   exceed on. First to cut if day 20 is at risk; last to cut if not. Needs `trust/ensemble.py`,
   which `CLAUDE.md`'s repo map names and which does not yet exist.
6. **Colour Correction Matrix before augmentation** (Korshunov et al.). Addresses our measured worst
   fragility — 15% white-balance shift costs 0.39 mIoU. Belongs in `reefprint/calibrate/`. Evaluated
   against LumenStone V1's 30 real images, not synthetic perturbations.
7. **Patch size 512 → 256–384**, the range the dataset authors use. Smaller patches at fixed memory
   mean larger batches for free and more diverse samples per step.
8. **Re-test the loss at full budget, and add Focal.** CE+Dice lost at 512 patches, but Dice is
   documented as unstable while predictions are diffuse — exactly the 512-patch regime. Focal is
   untried and is the literature's answer to rare classes (Jiang et al. use Dice + Focal).
9. **LR 1e-3 with `ReduceLROnPlateau`**, not flat 2e-4. Our stall at 1e-3 may have been the missing
   scheduler, not the rate — the authors run 1e-3 with plateau reduction and class-balanced
   sampling.
10. **Test-time augmentation** at inference — typically +0.01–0.03 mIoU for zero training cost, but
    multiplies inference time, trading against the real-time claim. Measure both, decide explicitly.

**Gated on budget saturating only:** encoder swap via `smp`+`timm` (also closes the COCO
weight-chain licence gap); or DINOv2-small frozen + a light head — well-motivated at 37 training
images, Apache-2.0. **A full architecture swap to ResUNet or PSPNet stays cut** — 4–6 PT-days, voids
every downstream calibration, and levers 1–9 are cheaper. Korshunov et al.'s own ~3 h on one A6000
is the literature's own compute budget: not a problem more GPU alone solves.

**The strategic point, above any single lever.** Nobody wins this hackathon on mIoU, and the brief
never asks for it — it asks for ≥3 phases, an accuracy report, a plant-parameter demonstration,
real-time, and control integration, judged on Innovation · Feasibility · Impact · Technical
Execution · Presentation Clarity. The right target is "close enough that the number is not a
liability", then spend the remaining days on what is actually scored. There is one axis where we
can genuinely exceed a published segmentation baseline: they report accuracy; we can report accuracy
plus calibrated uncertainty, an abstention rate, and a refusal path. "Comparable accuracy, and it
tells you when not to trust it" is a stronger claim to a plant audience than +0.02 mIoU.

---

## The research anchor — what the literature actually says drives this

Read 14 Sep. Three sources, all licence-clean to cite and reimplement from (the papers are CC BY;
only petroscope's code is GPL-3.0).

| Source | Method | Result |
|---|---|---|
| petroscope README (GPL-3.0 code, numbers citable) | ResUNet, S1 v1, 7 classes | mIoU 0.8373 / 0.8506 void-borders; per-class 0.7464 (galena) – 0.9628 (pyrite) |
| Korshunov et al. 2025, *Mining Sci. & Tech. (Russia)* 10(3):232–244, doi:10.17073/2500-0632-2025-05-416, CC BY 4.0 — the dataset authors | PSPNet + ResNet18, class-balanced patch sampling from probability maps, Colour Correction Matrix (LAB space, CIEDE2000 loss), XPL registered to PPL by SIFT + RANSAC affine and fed as extra input channels, patches 256–384 px, Adam 1e-3 with plateau reduction, rotation/scale/brightness/colour augmentation, ~3 h on one A6000 | per-mineral IoU 0.650 (magnetite) – 0.964 (pyrite); pentlandite 0.790; PA 0.96 |
| Jiang et al. 2024, *Minerals* 14:1281, doi:10.3390/min14121281 | Res-UNet ensemble, 5 learners, weighted-voting fusion; Dice + Focal loss; spatial-transformer block | mIoU 91.65 over 9 classes; "outperforms individual optimized Res-UNet models" and beats DeepLabV3 and PSPNet |

**Seven findings, in order of how much they change what we do.**

1. **We are on the architecture the field uses as the baseline to beat.** KHANYA runs
   DeepLabV3-ResNet50; Jiang et al. name DeepLabV3 as the classical comparator their ensemble beats.
   Not a case for a swap — a case for the cheaper lever, ensembling (finding 2).
2. **Ensembling is the highest-confidence lever in the literature for this task — and it buys our
   differentiator with the same GPU-hours.** `src/reefprint/trust/ensemble` is listed in `CLAUDE.md`'s
   repo layout and does not exist — only `__init__.py` mentions it.
3. **The v1/v2 asterisk is probably removable for free.** The dataset page: "Each new version
   contains all previous images plus additional samples." S1 v1 = 59 train + 16 test; v2 = 64 train
   + 20 test. If v1's 16 test stems are a subset of v2's 20, the directly-comparable number needs
   only the checkpoint we already have.
4. **LumenStone ships a colour/illumination subset we are not using.** V1: 30 images, 10 samples ×
   3 imaging variations, purpose "developing and testing color adaptation methods."
   `khanya/main:src/robustness.py`'s own docstring already names it and says real V1 evidence should
   replace the synthetic perturbations if there is time. The instrument (`white_balance`, `exposure`,
   `blur`, `noise`, `jpeg`) is built; only the data is missing.
5. **Our colour decision conflicts with the dataset authors', and the resolution strengthens both.**
   KHANYA excludes colour jitter because reflectance is the signal; Korshunov et al. use
   brightness/colour augmentation *and* a CCM normaliser. Sequence resolves it: calibrate first
   (CCM), then augment.
6. **The published registration method is SIFT + RANSAC, and we use neither.** Both are
   BSD-3-Clause via `scikit-image>=0.24`, already a declared dependency. A repo-wide grep finds no
   SIFT, RANSAC or `phase_cross_correlation` anywhere. Our bespoke coarse-to-fine correlation search
   is the thing `experiments/010` proved non-reproducible.
7. **Magnetite is the hardest class for the dataset authors too.** Their magnetite IoU is 0.650 —
   the worst of their ten — pentlandite 0.790 second-worst. Our 0.0000 is worse, but the *ordering*
   matches the literature, converting our result from embarrassment into citable expected difficulty.

**Terms of use, now settled:** the dataset page states verbatim — "You are free to use the provided
data in your own research work. If you intend to publish research work that uses this dataset, you
have to cite the references whenever appropriate." An explicit grant with a citation condition, not
an OSI licence.

### Workstream I — write the factors into the rules (day 14, ~1 h, no dependencies)

The durable half: every future task is measured against these, not remembered for one week.

- `CLAUDE.md` gains "What the literature says drives accuracy here" — the seven factors as one
  table, each with its citation — and **Rule 10**: check the published method before inventing one.
- `docs/09-brief-compliance.md` gains a third table — Factor → what the literature says → what we
  do → evidence path.
- `docs/03-free-stack.md` gains the three citations with DOIs, and the LumenStone V1/P1/P2/ICM1
  subsets, currently unrecorded.
- `SBOM.md` gains the LumenStone terms-of-use quote verbatim.
- `WORKBOARD.md` §8 gains: "if a task has a published method, the ADR or buildlog entry names it."

### Workstream E — put the plant-parameter adjustment on screen (day 24)

`reefprint.viz.demo.offline_demo()` renders only the anisotropy gate and a geometry refusal. Add a
third panel: advisory published → simulated setpoint moves → stale advisory refused, setpoint
unchanged. Regenerate the backup GIF. This is the brief's most judge-visible line and is currently
invisible.

### Workstream F — licence hygiene (day 15, pairs with C)

- Pre-upload the torchvision COCO weights as a Kaggle dataset, pinning `COCO_WITH_VOC_LABELS_V1` and
  its sha256 — fixes both the `enable_internet: false` kernel constraint and `SBOM.md`'s empty
  checkpoint table.
- `reefprint.segment.backbone.require_permissive_backbone()` permits only `timm`/Apache-2.0, which
  our own model does not satisfy. Widen deliberately to torchvision/BSD-3-Clause, test updated.

### Workstream G — P5 determinism (days 16–19, yields to A–E)

Fix, then re-run — but the research anchor changed what "fix" means.

1. A determinism test first, regardless — `estimate_rotation_centre` twice in one process on one
   real section, assert bit-equality.
2. **Try the published method before repairing the bespoke one (Rule 10).** SIFT + RANSAC via
   `scikit-image`, no new dependency, and diagnosable in a way a grid search is not — inlier count
   and residual explain *why* a section failed.
3. If SIFT+RANSAC also fails or disagrees: pin thread counts to remove BLAS reduction-order
   variance, and add the missing tie-break rule to `_coarse_to_fine_search`.
4. A landscape diagnostic tabulating coarse-grid scores — now a diagnosis of the old method, not a
   prerequisite.
5. Only then re-run the five sections.

**Hard rule: if any of A–E slips, P5 stops where it is.** Step 2 is cheap enough to run even under
pressure; steps 3–5 are not.

### Workstream H — scope the LLM tooling explicitly (day 14, in the ledger)

- Kaggle's $10/day, $100/month AI quota applies to Kaggle Benchmarks (LLM evaluation), not to GPU
  kernels. It does not fund this training. The resource that matters is 30 GPU-h/week.
- Featherless + HuggingFace (10 private models) must not touch the measurement path. Rule 6: no LLM
  computes a mineralogical or control value. The demo runs fully offline, so a live API call cannot
  be on stage.
- Legitimate uses: drafting and reviewing prose; code assistance; the Curator agent's
  route/select/explain role, which Rule 6 permits; HuggingFace as the download route for
  Apache-2.0 weights if the architecture question ever reopens.

### Sequencing, and the one hard gate

| Day | Action |
|---|---|
| 14 | A (anchor brief) · I (factors → rules, Rule 10) · B (re-cache + re-benchmark, zero GPU) · H (scoping) · one ask to Sibusiso: S1/S2 + `best.pt` + V1 (30 images) + the S1 v1 test stem list |
| 15 | F (weights dataset + SBOM row + guard) · prepare the D2 code changes on `main`: `BATCH_SIZE` and `PATCH` env-overridable, AMP, aux-loss term, focal loss, plateau scheduler · run the stem-subset check the moment the list lands |
| 16 | GATE: if the S1/S2 upload has not started, Workstream C is dead — ship 0.7116 and reallocate to D/E. Else push J0. V1 robustness re-run is not gated on this |
| 17–18 | J1 + J2 at the raised batch size and 256–384 patches · CCM normaliser built and evaluated against V1 · G starts in parallel, SIFT+RANSAC first |
| 19 | Re-cache, re-benchmark, build the 3-point scaling curve · one loss run at full budget (CE+Dice and focal) · decide TTA on measured accuracy-vs-latency · ensemble go/no-go from observed wall-clock, default no |
| 20 | MODEL FREEZE 18:00. Whatever exists is the checkpoint |
| 21–23 | D (baselines, `ScoredMetric`, bootstrap, cross-subset transfer, accuracy report) |
| 24 | E (demo panel + GIF) · recalibrate conformal/decision-gap against the frozen checkpoint |
| 25 | FEATURE FREEZE. Wording only |

**Freeze the model on the 20th, not the 25th**: roughly eight downstream JSONs are
checkpoint-derived and cannot start until it is locked.

**If we still lose to published** — at ~0.73 vs 0.85 we probably will — do not chase it. Ship the
scaling curve (512 → 2,560 → 40,000 patches; 0.33 → 0.71 → X) and name the cause: patches seen, one
architecture, no hyperparameter search. Nobody wins this on mIoU; the claim is "good enough to drive
an auditable decision, with a layer that refuses when it isn't."

### Risks, and the cheapest early signal for each

- **R1** loader-bound, not GPU-bound — signal: J0's patches/s and GPU utilisation.
- **R2** no internet in kernels — mitigated by F; signal: J0 fails in the first 60 s.
- **R3** S1/S2 upload never starts — the day-16 gate exists for exactly this.
- **R4** recalibration debt — a new checkpoint invalidates conformal, decision-gap, robustness and
  liberation-margin reports; if >6 h of re-derivation, freeze earlier than the 20th.
- **R5** magnetite may not be a budget problem — 1.58% of pixels, IoU 0.0000; if still 0.00 after
  ~5,000 patches, more GPU will not fix it.
- **R6** architecture temptation — not a discovery, a decision; gated on J1/J2 plateauing.
- **R8** v1/v2 contamination — downgraded and cheap to settle: `set(v1_test) <= set(v2_test)`,
  minutes, from the filename list. If it holds, quote the 16-section number with a CI or not at all.
- **R9** TTA trades against the real-time claim — measure both in the same run, decide explicitly.
- **R10** the ensemble collides with the day-20 freeze — every downstream calibration must then be
  recomputed against the ensemble, not a member. Decide on day 19 from observed wall-clock. Default
  no ensemble.
- **R11** the literature is read from abstracts and one README, not full method sections — the
  Jiang et al. ensemble figures came from a search summary (MDPI returned 403); petroscope's
  training recipe is not in its README at all. Treat as indicative, not citable, until the PDF is
  read.
- **R7** cross-branch — `ScoredMetric` is on `reefprint`, the metrics on `khanya/main`. Generate the
  accuracy report on `reefprint`, reading khanya's JSONs as data.

---

## Verification

- `uv run pytest -m "not placeholder" -q` → 339 passed, 4 deselected on 14 Sep; must not regress.
- `docs/09-brief-compliance.md` is a new file in `docs/`, so `CONTEXT.md` §4's doc-count guard fails
  on the same commit that adds it — update the count in that commit, not the next one.
- `uv run ruff check . && uv run ruff format --check .` clean.
- Ledger: open every path named in `docs/09-brief-compliance.md` — verify it exists, do not trust
  the table. Every literature row carries a DOI; anything not read from the paper itself is marked
  indicative (R11).
- Stale benchmark: `reports/benchmark_s1_patches.json` regenerated; `ours.mean_iou` ≈ 0.7116, not
  0.3295.
- Training: kernel completes with `enable_gpu: true`; per-image metrics downloaded; scaling curve
  monotone; latency measured on named hardware.
- Rule 3: the headline mIoU constructed through `ScoredMetric` — if it refuses, that refusal is the
  reportable result.
- Demo: `offline_demo()` renders three panels including the advisory applying and then being
  refused; GIF regenerated and viewed.
- P5: the new determinism test passes twice in a row on real data before any offset is quoted — for
  the SIFT+RANSAC estimator too, not only the grid search.
- Licence: `SBOM.md` checkpoint row present before any retrained weight is quoted anywhere;
  LumenStone's terms-of-use sentence quoted verbatim.
- Cross-version claim: the v1/v2 stem check is a printed set comparison in the experiment output,
  not a sentence in a README. If it holds, the 16-section number carries a CI, labelled n=16.
- Colour: the CCM result is measured on LumenStone V1's real 30 images. If V1 never arrives, the
  synthetic number stays and is labelled synthetic.
- Rule 10 in practice: pick any three decisions made after day 14 and check each names the published
  method it accepted or rejected.
