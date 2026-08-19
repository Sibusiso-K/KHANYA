# KHANYA — Mintek SCi Grad Hackathon 2026, Problem 3

Real-time mineralogical characterisation from reflected-light optical
microscopy: micrograph -> segmentation -> modal mineralogy -> liberation ->
plant recommendation. One learned stage (the CNN); everything downstream is
deterministic and auditable. Full explanation: [`STATUS.md`](STATUS.md).

**Status: selected.** Abstract due **30 Aug 2026**. Final hacking day **1 Oct**
(13:00 hard submission cutoff, 10-min pitch), conference 2 Oct. Team: Sibusiso
Khumalo, Lethabo.

## Start here

| Doc | Answers |
|---|---|
| [`STATUS.md`](STATUS.md) | What exists, what doesn't, what to build next — the current snapshot |
| [`HANDOVER.md`](HANDOVER.md) | Session-by-session log. Read the newest entry before pushing; add one after |
| [`PITCH.md`](PITCH.md) | How this wins: positioning, abstract structure, the 10-minute run of show |
| [`MINTEK-FIT.md`](MINTEK-FIT.md) | Why this matters to Mintek specifically, and what to ask them for |
| [`DATA-SOURCES.md`](DATA-SOURCES.md) | Every dataset considered, licence status, why each was kept or ruled out |
| [`reports/KHANYA-01-research-phase.md`](reports/KHANYA-01-research-phase.md) | The research report — every claim traces to a JSON in `reports/` |

## The headline result

Two segmentation models were compared on 12 held-out sections. The better one
scored +2.8 points of mean IoU — and produced **zero improvement** in plant
recommendations. Repairing particle topology, with no retraining, cut
recommendation errors by two thirds and drove unsafe errors (confidently
telling the plant to continue while payload is locked) to zero on both models.

**Conclusion: per-class IoU is a poor proxy for whether a system is safe to
act on.** Full result: report section 5.0.5–5.0.9.

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
dashboard/app.py             offline Streamlit demo — segmentation, liberation, verdict

src/{config,data,model,train,evaluate}.py            SUPERSEDED (MUMDMC classification
src/segmentation/{data,train,evaluate}.py             SUPERSEDED  pipelines) — kept only
                                                       so cited numbers stay reproducible.
                                                       See each file's docstring.
```

Two datasets, three checkpoints, one live pipeline: `lumenstone.py` +
`train_patches.py` is what the dashboard and every current number use.

## Setup

```bash
python -m venv .venv && .venv/Scripts/activate
pip install -r requirements.txt
```

Datasets are gitignored (`data/raw/`) — see `DATA-SOURCES.md` for download
links and licences. Place LumenStone under `data/raw/lumenstone/{S1,S2,S3}_v*/`.

```bash
python -m src.segmentation.train_patches            # train
python -m src.segmentation.train_patches --eval      # held-out test metrics
python -m src.decision_gap --model patches --refine  # decision-layer accuracy
streamlit run dashboard/app.py                       # offline demo
```

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
