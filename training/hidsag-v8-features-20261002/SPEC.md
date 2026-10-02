# v8 spectral associations: prospective specification

Written 2026-10-02 07:55 SAST, before `run_v8_features.py` runs and before any v8 feature is seen. Committed first, so the order is visible in git.

**What this is and is not.**
- It is a **prospectively specified reanalysis**. MINERAL1's mineral abundances were seen in v5, v6 and Q2, and these hypotheses were chosen with those abundances in view (ClauDex round 1, finding 14).
- It is not untouched confirmation. Confirmation needs independent site samples.
- Passing features are reported as **validated spectral associations**, never as phase identification. The ≥3-phases deliverable rests on KHANYA's segmentation evidence.

**Features (frozen in the script).**
- Continuum removal by the upper convex hull. Minimum position by a 2nd-order polynomial through the minimum and its neighbours; relative depth = 1 − CR(min). This follows the practice reviewed in Laukamp et al. 2021, *Minerals* 11:347.
- Windows: Al-OH 2150–2240, Fe-OH 2235–2275, Mg-OH/CO₃ 2290–2360, gypsum H₂O 1730–1785, H₂O 1880–1960 (nuisance), Fe³⁺ 850–960 nm.
- **Primary aggregation:** features of the pooled mean spectrum per sensor, all crops, **v6 mask** (darkest 5% removed).
- **Sensitivity checks:** no dark mask, and the median of per-pixel features.

**Hypotheses, each with one endpoint.**

| | Feature depth | QEMSCAN group (wt%) | Status |
|---|---|---|---|
| H1 | Al-OH 2200 | Muscovite/Sericite + Kaolinite | in Holm |
| H2 | Fe-OH 2250 + Mg-OH 2330 (sum of depths) | Chlorite + Biotite | in Holm |
| H4 | Fe³⁺ 900 | Fe Oxides | in Holm |
| H3 | gypsum H₂O 1750 | Anhydrite/Gypsum (pooled label) | **exploratory**, excluded from Holm, because anhydrite is anhydrous |

**Estimator.**
1. **Partial Spearman ρ.** Rank the feature and the group wt% across the MINERAL1 records. Regress each rank vector by OLS on indicator variables for size fraction × process line. Take the Pearson correlation of the residuals.
2. **Size fraction and line** come from the crop tags: line = P#, fraction = the non-P#/S# tag (for example "coarse").
3. **Inference: cluster bootstrap.** 4,000 resamples of composites (P#S#), with all fractions of a composite resampled together. Two-sided 95% percentile CI. The p-value comes from the bootstrap distribution under the predicted sign.
4. **Holm** correction across H1, H2 and H4.
5. **Month-blocked sensitivity.** Clusters = S# (month) across lines.

**Gate.** A hypothesis passes if all three hold:
- the predicted sign is positive;
- the Holm-adjusted one-sided p is < 0.05;
- the point estimate is ≥ 0.30, the minimum useful effect.

Otherwise it is "inconclusive" (CI includes 0) or "fails" (the sign is wrong and the CI excludes 0).

**Power** is reported. About ρ = 0.5 is needed for 80% power at roughly 36 clusters with this adjustment, so "inconclusive" is a likely and acceptable outcome.

**Identity reconciliation.** Every MINERAL1 record's folder, crop count and tags are logged, and the 99 records are reconciled against the dataset paper's 94 physical samples before any test is run. If duplicates are found, they are collapsed to one record before analysis. That collapsing rule is fixed here.

**GEOMET.** The features are computed but not tested against GEOMET targets in this spec. GEOMET has no mineralogy labels.
