# v9 robustness: result (2026-10-02 11:20)

The pre-registration (`PREREG.md`, commit 052cd72) and the analysis script (`analyse_v9.py`, commit cc71529) were both committed before the output existed. Full numbers: `analysis_v9.json`.

**How it works.** Each of the 146 GEOMET parcels is scored by the **fold model that never saw it**, on the variants below. The `original` variant reproduces v6's out-of-fold predictions exactly (max difference 0.0).

**Bond work index (the decision target): MAE ratio vs the published out-of-fold accuracy**

| Variant | MAE (kWh/t) | Ratio [95% CI] | Gate | OOD flagged / refused | Unflagged large errors* |
|---|---|---|---|---|---|
| original | 1.052 | 1.000 | — | 6.2% / 2.7% | 11.0% |
| **new capture (fresh pixels)** | 1.052 | **1.000 [0.991, 1.010]** | ≤ 1.10: **equivalent: PASS** | 6.2% / 2.7% | 11.6% |
| partial view (half scan) | 1.059 | 1.007 [0.986, 1.028] | ≤ 1.25: tolerant | 7.5% / 4.1% | 11.0% |
| noise 2% | 1.050 | 0.998 [0.979, 1.017] | ≤ 1.25: tolerant | 6.2% / 4.1% | 11.0% |
| light −15%, uncalibrated | 1.054 | 1.002 [0.998, 1.005] | reported | 6.2% / 2.7% | 11.0% |
| light +15%, uncalibrated | 1.057 | 1.005 [1.001, 1.010] | reported | 6.2% / 2.7% | 11.0% |
| **wavelength drift (1 band)** | **1.310** | **1.246 [1.155, 1.343]** | reported | 8.9% / 6.8% | **16.4%** |

\*A parcel whose error exceeds twice the mean error without being flagged by the OOD gate.

The other four targets behave the same way. New capture: 0.995–1.002. Wavelength drift: 1.12–1.43.

## What this proves, and what it does not

- **It proves that the accuracy report transfers to a new capture of the same ore.** A different pixel sample of the same material gives the same error. The same holds for a partial view, sensor noise and a ±15% change in light level: the features are normalised, so brightness hardly matters.
- **It exposes a real gap: wavelength-calibration drift.** A one-band shift (5 nm VNIR, 10 nm SWIR) raises the error by about 25%, and the OOD gate flags only a few more parcels. So the drift mostly arrives as **silent error**.
  - **Fix (added to the installation design):** a wavelength-calibration check against a reference with known absorption features, run at every white-reference cycle. If the measured feature positions move by more than half a band, refuse.
  - This is a hardware QA gate, not a model change.
- **About 11% of parcels have large errors the OOD gate does not flag,** even unperturbed. The one-sided conformal bound (≤ 10% exceedance) is what protects the decision, not the OOD gate alone.
- **It does not prove a new deposit or a new camera.** These are variants of the same HIDSAG scans. That external test is the pilot's shadow phase with Bond tests on Bushveld ore.
- **A foreign ore is not reliably refused.** v6 measured shifted-domain acceptance of 0–80% across folds. That gap remains.
