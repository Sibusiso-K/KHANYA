# REEFPRINT (also known as KHANYA) — Mintek-SCi Grad Hackathon 2026

**One build, two names, two authors** ([ADR-0003](https://github.com/Sibusiso-K/KHANYA/blob/reefprint/docs/04-decisions/0003-one-build-two-names-reefprint-and-khanya.md)).
REEFPRINT is the specification, the physics and the measurement half — it lives
on the [`reefprint`](https://github.com/Sibusiso-K/KHANYA/tree/reefprint) branch
of this repository. KHANYA is this branch: the segmentation model, the modal
mineralogy and apparent 2D sulphide association index calculators, the
conformal calibration, and the offline dashboard. The two commit histories
are kept deliberately unmerged so
each author's contribution stays independently verifiable — Mintek's Office of
Technology Transfer runs an IP assessment on top-ranked entries before winners
are announced.

Challenge area: **AI for Mineral Processing**. Real-time mineralogical
characterisation from reflected-light optical microscopy: micrograph ->
segmentation -> modal mineralogy -> apparent 2D sulphide association index ->
plant recommendation. One learned stage (the CNN); everything downstream is
deterministic and auditable. Full explanation: [`STATUS.md`](STATUS.md).

**Status:** abstract submitted. In the build phase to the **1 Oct** hard
submission cutoff (13:00) and 10-minute pitch; conference 2 Oct. Team: Sibusiso
Khumalo, Lethabo Hoaeane, Ipeleng Modise (Team Sonar). Current plan of record:
[`ENDGAME.md`](ENDGAME.md).

## Start here

| Doc | Answers |
|---|---|
| [`JUDGE-READY-WORKPLAN.md`](JUDGE-READY-WORKPLAN.md) | **Active presentation-readiness backlog:** Mintek/category fit, exact CV model, real-time live demo contract, industry applicability, judging criteria and production-readiness gates |
| [`WORKBOARD.md`](WORKBOARD.md) | **Read this first.** The shared index and scoreboard — which of the other status docs to trust, who owns what, the open decisions. Authored on `reefprint`, mirrored here; edit it there, not on both branches |
| [`reports/ADVERSARIAL-CRITIQUE-2026-09-15.md`](reports/ADVERSARIAL-CRITIQUE-2026-09-15.md) | **The case against this submission.** Where the brief is missed, the six questions a judge can ask that we currently cannot answer, and the unexamined risks (AI authorship, MOTT, contributor trail). Read before rehearsing |
| [`reports/BUILD-REMEDIATION-PLAN-2026-09-15.md`](reports/BUILD-REMEDIATION-PLAN-2026-09-15.md) | **Proposed, not decided.** What to build in response to the critique, each item with a kill criterion, plus the assumptions it rests on that nobody has verified. Published to be attacked before anyone builds from it |
| [`reports/TECHNICAL-REVIEW-2026-09-12.md`](reports/TECHNICAL-REVIEW-2026-09-12.md) | Full adversarial technical review: evidence gaps, proposed redesign, accuracy report template, integration, IP/licensing and the 19-day submission plan — recommendations, not implemented fixes |
| [`ENDGAME.md`](ENDGAME.md) | **The plan of record** — who we present to, how we are scored, what is left to build, who builds it |
| [`STATUS.md`](STATUS.md) | What exists, what doesn't, what to build next — the current snapshot |
| [`HANDOVER.md`](HANDOVER.md) | Session-by-session log. Read the newest entry before pushing; add one after |
| [`PITCH.md`](PITCH.md) | Positioning, abstract structure, the 10-minute run of show |
| [`BACKUP-DEMO-SCRIPT.md`](BACKUP-DEMO-SCRIPT.md) | Exact sequence for recording the offline demo backup video (ENDGAME W7) — real images, verified results, not yet recorded |
| [`MINTEK-FIT.md`](MINTEK-FIT.md) | Why this matters to Mintek specifically, and what to ask them for |
| [`JOINT-PLAN.md`](JOINT-PLAN.md) | How the KHANYA and REEFPRINT halves join, and the seam between them |
| [`DATA-SOURCES.md`](DATA-SOURCES.md) | Every dataset considered, licence status, why each was kept or ruled out |
| [`reports/KHANYA-01-research-phase.md`](reports/KHANYA-01-research-phase.md) | The research report — every claim traces to a JSON in `reports/` |

## The headline results

**1. Better segmentation did not buy better decisions.** Two models were
compared on 12 held-out sections. The better one scored +2.8 points of mean IoU
— and produced **zero improvement** in plant recommendations. Repairing particle
topology, with no retraining, cut recommendation errors by two thirds and drove
unsafe errors (confidently telling the plant to continue while payload is
locked) to zero on both models when combined with the empirical uncertainty
band. These are retrospective results on 12 sections, not a deployment safety
guarantee. *Per-class IoU is a poor proxy for whether a
system is safe to act on.* Report §5.0.5–5.0.9.

**2. Chromite composition carries PGE signal beyond Cr₂O₃.** On 1,112 real
Bushveld chromitite assays across 305 boreholes (Bachmann 2019, LG/MG seams),
adding Cr# and Mg# to a Cr₂O₃-only baseline is a statistically significant
improvement — ΔR² = 0.0279, **p = 0.0002**, cluster-robust by borehole.
Effect size is modest and Cr# is arithmetically related to the baseline; both
caveats are stated in [`reports/chromite_pge_falsification.json`](reports/chromite_pge_falsification.json).

**3. Things we checked and could not claim.** The rotation geometry of the
public archive is not established by the data — investigating why found its
frames are not registered to each other, so no per-pixel measurement on it
(the earlier reported extinction result included) is valid; no public
texture-plus-chemistry dataset exists for UG2; no oxidation index is
computable from XRF majors. Each is documented with its evidence, and the
registration finding is still evolving on `reefprint`'s `WORKBOARD.md`. The
system that reports these is the product — see [`ENDGAME.md`](ENDGAME.md) §3.

## Repository map

```
src/
  segmentation/
    lumenstone.py          LumenStone S1/S2/S3 loader, class codebook, subset switch
    patches.py              native-resolution patch sampling, balanced by class
    train_lumenstone.py     resize baseline (whole-image, downsampled)
    train_patches.py        native-resolution training + eval (primary pipeline)
    losses.py               cross-entropy + soft Dice
    metrics.py               IoU / pixel accuracy, matches petroscope's protocol
    model.py, config.py     shared model builder + paths (used by everything above)
  modal.py                  segmentation mask -> modal mineralogy + liberation
  advisor.py                measurements -> plant recommendation, uncertainty band
  conformal.py               distribution-free calibration for the uncertainty band
  decision_gap.py            does better segmentation buy better decisions? (it doesn't, alone)
  benchmark.py                scores against the published LumenStone protocol
  robustness.py               photometric perturbation sweep (lighting, focus, noise)
  sampling_error.py           liberation variance across sub-fields of one section
  inspect_pipeline.py         per-section visual debugger, renders reports/figures/
  polarimetry.py              THE BRIDGE to REEFPRINT — imports reefprint.polarim /
                                reefprint.bridge unchanged, feeds them LumenStone S3 v2
                                rotation series with our masks as labels
  chromite_pge_falsification.py  Cr#/Mg# vs PGE grade on real Bushveld assays, through
                                reefprint.heads.falsification (week-2 gate)
dashboard/                   offline Stitch HTML dashboard before and after upload;
                             Streamlit only bridges the file to the real pipeline
scripts/                     run helpers (detached training launches)
logs/                        run logs, gitignored
reports/                     every number in the report, as JSON

src/{config,data,model,train,evaluate}.py            SUPERSEDED (MUMDMC classification
src/segmentation/{data,train,evaluate}.py             SUPERSEDED  pipelines) — kept only
                                                       so cited numbers stay reproducible.
                                                       See each file's docstring.
```

Two datasets, three checkpoints, one live pipeline: `lumenstone.py` +
`train_patches.py` is what the dashboard and every current number use.

**The seam.** `src/polarimetry.py` and `src/chromite_pge_falsification.py` are
the only files that cross into REEFPRINT, and they do it by importing it
unchanged — never by copying code. Point `REEFPRINT_SRC` at a checkout of the
`reefprint` branch, or clone it beside this one:

```bash
git worktree add --detach ~/Desktop/REEFPRINT origin/reefprint
```

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt pytest
```

Datasets are gitignored (`data/raw/`) — see `DATA-SOURCES.md` for download
links and licences. Place LumenStone under `data/raw/lumenstone/{S1,S2,S3}_v*/`.

```bash
python -m pytest tests/ -q                           # no dataset needed
python -m src.segmentation.train_patches            # train
python -m src.segmentation.train_patches --eval      # held-out test metrics
python -m src.decision_gap --model patches --refine  # decision-layer accuracy
python -m src.chromite_pge_falsification             # week-2 gate, Bushveld assays
python -m src.polarimetry                            # the REEFPRINT bridge
streamlit run dashboard/app.py                       # offline demo
```

The test suite runs without any dataset — it covers the decision layer, the
conformal calibration, the liberation measurement (including the sparse-upload
crash fixed in entry 23) and the archive parsing on the REEFPRINT seam. CI runs
it on every push, and separately asserts that `dashboard/` contains no network
references, because "runs offline" is a claim made on stage with the wifi off.

`KHANYA_SUBSET=S1` (or `S2`, `S3`) selects the dataset; unset defaults to S2,
which reproduces every number in the report exactly.

## Rules we hold ourselves to

- Split by **specimen**, never by image — same-specimen leakage inflates
  accuracy and judges in this field will ask.
- The demo runs **offline** on one laptop. No CDN calls anywhere (checked —
  a font import was found and removed for exactly this reason).
- Every claim in the report traces to a JSON file in `reports/`.
- Negative results are kept, not deleted. A retracted number stays in the
  history with the correction next to it.
- Write our own prose, cite sources — originality is scored and finalists go
  through explicit AI-generation authentication.

## Hard dates

| Date | What |
|---|---|
| **30 Aug** | One-page abstract; per-member admin (ID, T-shirt size, mentor request) |
| **1 Oct** | On site at Mintek. 08:00 report, **13:00 hard submission cutoff**, 14:00 presentations, **10 min/team** |
| 2 Oct | SCI Conference, attendance compulsory. Five finalists announced |

1 October is a working day with a submission deadline, not a presentation day.
