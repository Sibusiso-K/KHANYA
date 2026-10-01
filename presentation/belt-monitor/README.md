# REEFPRINT Belt Monitor (hyperspectral, before grinding)

It has the same look as the KHANYA workbench: Public Sans, the brand mark, and the three themes (White workbench, Mineral night, Field paper). There are four views: Belt, Feed mineralogy, Belt robustness, and Where it sits. You can pick them with URL parameters, for example `?view=robust&theme=mineral-night&speed=3000`.

An offline, single-page replay of the belt hyperspectral track. It plays held-out HIDSAG drill-core samples one at a time, as a belt would: the measured VNIR + SWIR spectrum, the out-of-fold predictions of five lab results with their typical error and the real lab value, and an illustrative decision card.

It is a replay of public data. It is **not a live belt**, and the ore is **not PGM**. The page says so on screen.

```
python -m http.server 8530 --bind 127.0.0.1 --directory presentation/belt-monitor
```

Open `http://127.0.0.1:8530/`. Add `?speed=3000` to change the time per sample, in ms.

## Rebuilding the data

```
python presentation/belt-monitor/build_data.py --v3 training/hidsag-hyperspectral-20261001/output --v4 training/hidsag-hyperspectral-20261001/output_v4 --v5 training/hidsag-v5-belt-20261001/output
```

This reads the Kaggle outputs (`hidsag_results.json`, `spectra_GEOMET.jsonl`, `wavelengths.json`) and writes `data.json`. It also copies the RGB previews into `rgb/`. A target is shown only if its cross-validated model beats the training-mean baseline.

## What the numbers are

- **Data:** HIDSAG GEOMET (Ehrenfeld et al., *Scientific Data* 2023, CC0). It has 146 porphyry Cu-Mo drill-core samples from Chile.
- **Model (v5):** PLS, ridge or extra-trees, chosen per target by inner CV, on brightness-normalised spectra, absorption depths and pixel-cluster fractions; 5-fold nested CV over samples.
- **Split limitation:** the published metadata has no drill-hole IDs, so a by-hole split could not be enforced, and the scores may be optimistic.
- **Every value on screen** comes from a model that never saw that sample.
- **Decision-card thresholds** are dataset quartiles. They are illustrative, not site rules.

Run log: `docs/BUILDLOG.md`, entry for 2026-10-01 (afternoon).
