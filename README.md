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

## Timeline

| Weeks | Goal |
|---|---|
| 1 | Data secured, IP agreement read, Mintek contacted |
| 2-3 | Baseline classification on >=3 phases |
| 4-5 | Segmentation + modal mineralogy |
| 6 | Operational feedback layer |
| 7 | Validation, failure analysis, energy case |
| 8 | Pitch, rehearse, freeze (event 1-2 Oct, Mintek Randburg) |

Feature freeze: end of week 7.
