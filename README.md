# Mintek-SCi Grad Hackathon 2026 — Problem 3

Real-time mineralogical characterisation from reflected-light optical microscopy.

**Deliverable floor (from the brief):** trained model identifying **>= 3 mineral phases**,
accuracy report, and demonstration of **operational feedback integration**.

## Pitch

Ore processability advisor: image -> phase identification -> modal mineralogy ->
plant recommendation (grind finer / adjust dosage / divert feed).

Why optical and not SEM: BSE detectors cannot separate hematite from magnetite
(near-identical average atomic number). Reflected light can, on reflectance and colour.

## Layout

```
src/config.py     paths, class list, hyperparameters
src/data.py       dataset + SPECIMEN-LEVEL splits (never split by image)
src/model.py      ResNet backbone, swappable
src/train.py      training loop, checkpoints
src/evaluate.py   per-class P/R/F1, confusion matrix -> reports/
src/advisor.py    phase fractions -> plant recommendation
dashboard/app.py  Streamlit demo (must run offline)
```

## Setup

```bash
python -m venv .venv && .venv/Scripts/activate
pip install -r requirements.txt
```

Then read `data/README.md` and place the datasets.

```bash
python -m src.train
python -m src.evaluate
streamlit run dashboard/app.py
```

## Rules we hold ourselves to

- Split by **specimen**, not by image. Same-specimen leakage inflates accuracy and
  judges in this field will ask.
- The demo runs **offline** on one laptop. Assume venue wifi fails.
- Every claim in the report traces to a number in `reports/`.
- Write our own prose and cite sources — originality is a scored criterion with
  explicit AI-generation checks.

## Status: SELECTED

Acceptance letter received 2026-08-14 (Boitumelo Lekalakala, Mintek SCI Grad
Hackathon 2026). Prizes R25,000 / R15,000 / R10,000; strong teams may be
considered for vacation work at Mintek. AI tools are permitted, but all
submissions undergo **plagiarism, AI-generation, IP and originality checks**, and
external sources, data and contributions must be acknowledged — the five finalist
teams go through explicit originality authentication after the conference.

## Hard dates

| Date | What |
|---|---|
| **30 Aug 2026** | **One-page abstract due** — approach, methods/technologies, expected outcomes/impact |
| 30 Aug 2026 | Per-member admin due: ID number, T-shirt size, contact details, mentor name + contact — or a clear request for a Mintek mentor |
| **1 Oct 2026** | **Final hacking day, on site at Mintek.** Physical attendance required. 08:00 teams report and continue development; **13:00 hard submission deadline**; 14:00 presentations begin; **10 minutes per team** to the judging panel |
| 2 Oct 2026 | Mintek SCI Conference — attendance and registration required for all selected teams. Five finalists announced here |

Note the shape of 1 October: it is a working day with a 13:00 cutoff, not a
presentation day. Anything not finished and submitted by 13:00 does not count,
and the pitch is 10 minutes.

## Plan to 1 October

| Window | Goal |
|---|---|
| to 30 Aug | Abstract submitted. LumenStone S2 downloaded, multi-class segmentation running |
| Sep wk 1-2 | Real held-out multi-class result (>=3 phases). Modal mineralogy from segmented areas |
| Sep wk 3 | Operational feedback layer wired to segmented area fractions, not classifier confidences |
| Sep wk 4 | Validation, failure analysis, energy/cost case, originality + acknowledgement pass |
| 29 Sep | **Feature freeze.** Offline demo rehearsed end to end on the venue laptop |
| 1 Oct | On site: refine only. Submit by 13:00 |
