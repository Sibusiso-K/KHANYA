# v7 pre-registration: a wider model menu on GEOMET (written 2026-10-02, before the run)

**Question.** Does a wider model menu make the belt's held-out predictions more accurate than v6? The candidates are gradient boosting, an RBF SVR and a fixed 5-model mean. The main interest is the Bond ball-mill work index (WI), the one belt target that drives a decision.

**What changes.** Only the candidate menu (`patch_v7.py` lists every replacement, asserted).
- `nl_hgb`: HistGradientBoosting.
- `nl_svr`: RBF SVR.
- `ens5`: the unweighted mean of nl_et, nl_ridge100, nl_pls8, lin_ridge100 and lin_pls8. The members are fixed here, not chosen by results.

Selection stays nested inside proper-training. Everything else is the same as v6: data, grid, features, the outer KFold(5, shuffle, 42), the calibration split (seed 7 + 1000·fold), the 80% split-conformal rule, OOD and occlusion. Comparisons with v6 are therefore paired by sample.

**Gates (unchanged from v6).** v7 "beats" v6 on a target only if all three hold on the deployable absolute errors:
- a paired cluster-bootstrap 95% CI of the MAE difference excludes 0;
- the Holm-corrected Wilcoxon p is below 0.05;
- the Mann-Whitney p is below 0.05.

Cliff's delta is reported. Otherwise the verdict is "no significant difference" and v6 stays the deployed model. Coverage must stay within the v6 band: the unit coverage 95% CI contains 0.80.

**What would count as a failure.** A lower MAE that fails a gate is not called an improvement. Lower coverage is a regression even if the MAE improves.

**Known limit, stated now.** GEOMET has no drill-hole ids, so the split is by sample and both v6 and v7 may be optimistic in the same way. That does not bias the paired difference, but it does affect any absolute number.

**Also logged.** The coverage of every lab variable in the GEOMET metadata, to find further real targets for later runs. It is not used for selection here.
