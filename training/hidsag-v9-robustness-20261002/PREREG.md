# v9 robustness: does it still work on a capture it has never seen? (pre-registered 2026-10-02 11:15, before the run)

**Question.** The user asked whether the system can ingest a new image of the same ore that is not in our data and give an answer as accurate as the accuracy report, rather than working only on the exact data it was scored on. And it should refuse things it should not answer.

**Design** (patch of v6, GEOMET, the same 5 outer folds; asserted replacements in `patch_v9_robust.py`). For every test-fold parcel, the **fold model that never saw that parcel** scores these variants of its spectra:

| Variant | What it simulates |
|---|---|
| `original` | The v6 pixel sample. Reproduces the published out-of-fold predictions |
| `resample` | A **new capture of the same material**: an independent random sample of 1,500 pixels per sensor from the full pixel pool (different seed) |
| `half` | **A partial view**: pixels only from the first half of the pool (row-major, so roughly the top half of the scan) |
| `gain_0.85`, `gain_1.15` | **Lighting or reference drift, uncalibrated**: every pixel scaled by 0.85 or 1.15. A working white reference removes this in practice; this tests what happens if it fails |
| `noise_2pct` | **Sensor noise**: Gaussian noise with SD 2% of the mean signal, added per pixel and band |
| `shift_1band` | **Wavelength-calibration drift**: spectra shifted one band (5 nm VNIR, 10 nm SWIR) |

Plus the existing v6 measurement for a **foreign ore**: MINERAL1 plant-feed spectra scored by the GEOMET models.

**Pre-registered expectations and gates** (WI, the decision target; the other targets are reported too):

1. **`resample` must match the accuracy report.** The paired MAE ratio (variant / original) must have a 95% bootstrap upper bound ≤ **1.10** (equivalence within +10%). If it fails, the accuracy report does not transfer to a new capture, and we say so.
2. `half` and `noise_2pct`: reported with the same ratio; an upper bound ≤ 1.25 is called "tolerant".
3. `gain_*` and `shift_1band`: expected to degrade. What matters is whether the **OOD gate flags them** (borderline or refused rate) rather than silently mispredicting. Reported, not gated.
4. **Foreign ore:** the v6 per-fold acceptance (0.80, 0.11, 0.01, 0.21, 0.00) is already known to be inconsistent. It is reported as a gap.

**The honest limit, stated now.** These variants come from the same HIDSAG scans: a different pixel draw, a partial view, or a perturbation. They are **not** a new deposit or a new camera. A truly external test needs new samples, which is the pilot's shadow phase.
