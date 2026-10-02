# 16 — From a prediction to a plant action, and what it is worth

> **Corrected 2026-10-02 (morning), after the ClauDex round-1 review (`PLAN-v8-REVIEW-LOG.md`, findings 17–19).** "Same overload risk" was wrong. A symmetric 80% interval does not give a 10% upper tail, and a CI of −4.8 to +4.1 pp is not equivalence. The section below now uses:
> - a one-sided bound;
> - the policy as it would be deployed (OOD refusals fall back);
> - a pre-registered non-inferiority margin of +3 pp.
>
> **Result: the throughput gain survives (+1.9% [+0.8, +2.9]), but non-inferiority on overload risk is not shown (upper bound +4.8 pp).** So there is no throughput claim until a pilot.

*Written 2026-10-02 for the Top-5 refinement. Every number below was computed by code from real held-out predictions on public data. The file is named next to each number. Anything assumed is labelled **ASSUMED**. Anything simulated carries **sim_**. Nothing here is a site measurement.*

## 1. The problem we pitched, and the test a prediction must pass

Lab characterisation takes days and the ore changes by the hour, so the shift decides blind. The plant loses recovery and overspends on reagents.

A prediction is only worth something if **someone can act on it before the ore arrives**, and if it beats what they already know. "What they already know" is the strongest baseline (constitution rule 3): the average, the last lab assay, or the mine plan.

## 2. Each prediction against that test

| Prediction | Source | Who acts | Next step it changes | Effect on held-out data | Verdict |
|---|---|---|---|---|---|
| **Bond work index** (hardness) | belt hyperspectral (HIDSAG GEOMET) | control-room operator | mill feed rate, inside the site's envelope | **sim_ +1.9% throughput** (95% CI +0.8 to +2.9%); overload 9.6% vs 8.9%, **non-inferiority at +3 pp not shown** (upper bound +4.8 pp) | **promising, not proven safe** |
| Cu and Mo recovery, lime, pH | belt hyperspectral | shift metallurgist | collector and lime dosing | no significant difference against the strongest baseline | not decision-grade |
| 4E PGE grade | belt-type chemistry, Bushveld (Bachmann 2019) | grade controller | concentrator or low-grade stockpile | balanced accuracy **0.79 vs 0.82 for the mine-plan seam**: the seam routes better (difference CI −0.056 to −0.004) | **correction**: no value where the seam is known |
| Concentrate silica, 1 h ahead | plant tags (Kaggle flotation plant) | control room | reagent and air setpoints | never beats the last lab assay | negative result |
| Pentlandite vs pyrrhotite | microscope (KHANYA), LumenStone S2 | metallurgist | depressant and collector choice | IoU 0.50 from colour and texture, given perfect sulphide masks | exploratory |
| Cr₂O₃ in feed | belt XRF measures it directly | concentrator, smelter | chromite entrainment, blending | a measurement, not a prediction | design |

**Sources:**
- Hardness: `training/value-chain-20261002/results.json`, from `training/hidsag-v6-live-20261001/output/hidsag_v6_results.json`.
- Bushveld: `training/bushveld-xrf-pge-20261001/app_bushveld.json`.
- Plant: `training/plant-softsensor-20261001/results.json`.
- Microscope: `training/pentlandite-diagnostic-20261001/results.json`.

**What this means for the pitch.** One belt prediction clears the bar today: hardness. The belt's recovery and reagent predictions do not beat their baselines on public data, so **we do not claim reagent savings from the belt**. Recovery is the microscope's layer. The plant's own tags cannot forecast its own assay better than the last assay. That is the argument for measuring the ore first, not a weakness.

## 3. The measured case: hardness → mill feed rate

**Mechanism.** A ball mill is normally limited by its motor. Bond (1961) gives the energy per tonne as W = 10·Wi·(1/√P80 − 1/√F80) kWh/t. At a fixed grind target, tonnes per hour = power / W, which is proportional to 1/Wi.

Without knowing the ore, the feed must be set for hard ore, so on softer ore the mill runs below what it could. Mill power, feed size and grind target cancel in every ratio below, **so no plant parameter was assumed to get the percentages**.

**Data.** 146 drill-core composites with v6 out-of-fold predictions.

**The upper bound.** A **one-sided 90% bound**: a cross-fold residual quantile, a CV+-style approximation (Barber et al. 2021). Exact CV+ needs every fold model's prediction at each sample, which v6 did not store, so validity is not claimed. Its empirical exceedance is **9.6%** [4.8, 14.4] against the 10% target.

**The deployed policy.** The feed is set for the bound. Out-of-distribution parcels fall back to the conservative setting (4 refused) or take the stricter of the two (5 borderline).

| Feed-rate policy | sim_ throughput vs no information | Parcels harder than planned | Energy shortfall on those parcels (1 − used/true) |
|---|---|---|---|
| No ore information: set for the training-fold 90th-percentile hardness | 0 (reference) | 8.9% [4.8, 13.7] | 10.1% |
| **Belt, as deployed (one-sided bound, OOD fallback)** | **+1.9% [+0.8, +2.9]** | **9.6% [4.8, 14.4]** | **4.1%** |
| Old comparator: upper end of the symmetric 80% interval | +2.0% [+1.0, +3.0] | 8.2% [4.1, 13.0] | 4.6% |
| Belt, point prediction (unsafe) | +13.6% [+12.3, +14.8] | 45.2% [37.0, 53.4] | 6.6% |
| Perfect information (ceiling) | +14.0% [+11.7, +16.4] | 0% | 0% |

**Gates for throughput.** The deployed policy beats no information on throughput:
- the CI excludes 0;
- Wilcoxon p ≈ 1×10⁻⁶;
- Mann-Whitney p < 0.0001;
- Cliff's δ = −0.40.

**The pre-registered risk test fails to pass.** Overload share is +0.7 pp higher. Its one-sided 95% upper bound is **+4.8 pp**, above the +3 pp margin, so **non-inferiority is not shown**. With 146 parcels the test has little power, so this is "not shown", not "shown worse". Under the plan's rule, **no throughput claim is made**.

**Ramp limits make overloads more frequent.** These are limits on how fast the feed may change per parcel, averaged over 200 random parcel orders, because HIDSAG has no time order:

| Ramp limit | Extra overloads |
|---|---|
| ±10% per parcel | +2.2 pp |
| ±5% per parcel | +4.3 pp |
| ±2% per parcel | +6.2 pp |

A real controller would need to cut feed fast and raise it slowly. That asymmetric design is untested here.

**Not simulated:**
- an APC/feedback baseline (HIDSAG is not a time series);
- stale data and transit time;
- stockpile mixing;
- downstream constraints.

**Reading.**
- The belt captures **13% of what perfect information would give**. That is the headroom a better hardness model could still take.
- When a parcel is harder than planned, the energy shortfall is smaller (4.1% vs 10.1% of the energy the ore needed). That is not a grind measurement.
- The point prediction overloads almost half the parcels, which is why the policy uses a bound.

**What it could be worth.** Nothing is claimed for throughput until a pilot shows that the overload risk is acceptable. Recovery value and break-even are in `training/economics-20261002/results.json` (revised): +1 pp of recovery is worth R64–153 M a year net at a Zondereinde-size plant (ASSUMED inputs), and the pilot breaks even at 0.04–0.26 pp. The Value tab computes both.

Not counted: fewer coarse-grind events, and fixed costs spread over more tonnes. Not netted: the scanner and its integration. The **Value** tab in REEFPRINT Live does this calculation with the site's own inputs.

## 4. Correction: Bushveld chemistry and the mine plan

We said belt-type chemistry beats the average guess for Pt, Rh and 4E. That is true, but the average is not the strongest baseline. A mine already knows which seam it is mining.

Routing each interval to the concentrator or the stockpile against the training-fold median 4E (1.37 to 1.64 g/t across folds), with 1,112 intervals and 123 projects held out by project:

| Routing | Balanced accuracy | 4E metal sent to the mill | Below-cut-off mass sent to the mill |
|---|---|---|---|
| Belt chemistry model | 0.79 [0.74, 0.84] | 74.7% | 30.3% |
| **Mine-plan seam (median 4E of the seam)** | **0.82 [0.78, 0.86]** | **82.8%** | 31.7% |
| No information (everything to the mill) | 0.50 | 100% | 100% |

**Belt chemistry adds nothing to PGE routing where the seam is known.** It earns its place only where provenance is lost, such as blends, stockpiles and third-party ore. There it gives 0.79 against 0.50 for no information.

The Bushveld track stays as the South African proof that the method runs on Bushveld data. It is not a grade-control claim. `CLAUDE.md` rule 3 applies: the strongest baseline was available (`r2_seam_only` was already in `results.json`) and should have been the one quoted.

## 5. We tried to make it more accurate: v7, pre-registered, no gain

**What was tested.** `training/hidsag-v7-ens-20261002/PREREG.md`, written and committed (`11f0c23`) before the run, widened the model menu:
- gradient boosting;
- an RBF SVR;
- a fixed 5-model mean.

Everything else was identical, including folds and calibration, so v7 vs v6 is paired by sample. Kaggle `reefprint-hidsag-v7-ens` ran in 703 s.

**Result** (`compare_v7.json`): **no significant difference on any target.**
- Work index R² went from 0.479 to 0.483 (MAE 1.052 → 1.049).
- Mo recovery improved on the paired test (CI −1.42 to −0.38, Holm p 0.004) but failed the Mann-Whitney gate (p 0.17), so it is not called an improvement.
- Coverage stayed in band.

v6 stays deployed. The run also confirmed that GEOMET carries exactly five lab variables, all already modelled.

**What would make it more accurate.** The limit is the data, not the model menu:
- more samples, with drill-hole ids;
- hardness tests matched to the scanned material;
- A×b for SAG circuits;
- at a site, the plant's own historical feed-rate and power logs to replace the Bond simulation with a measured response.

## 6. Limits, stated before anyone asks

1. The hardness evidence is **Chilean porphyry Cu-Mo drill core, not Bushveld PGM ore**. It transfers as a method, not as numbers.
2. GEOMET has **no drill-hole ids**, so the split is by sample and absolute numbers may be optimistic. The paired policy comparison shares that bias on both sides.
3. The policy assumes a power-limited mill whose feed can follow each parcel. Bond's law is a ball-mill law. A SAG circuit needs A×b, and a surge bin or stockpile blurs parcel-by-parcel control.
4. These are **simulated policies on real held-out predictions**, not a plant trial. A pilot that logs feed rate, power and grind with and without the belt is the test.
5. HIDSAG's `WI` is treated as the Bond ball-mill work index in kWh/t, as earlier runs and the target registry do. The Bond (1961) citation is the textbook form; the primary paper was not re-read in this session.

## 7. Where everything is saved

| What | Path |
|---|---|
| This analysis | `training/value-chain-20261002/value_chain.py` → `results.json` |
| v7 pre-registration, run and comparison | `training/hidsag-v7-ens-20261002/` (`PREREG.md`, `patch_v7.py`, `run_v7.py`, `compare_v7.py`, `compare_v7.json`, `output/`) |
| Full-resolution display export | `training/hidsag-v6-live-20261001/export_hr/` (Kaggle `reefprint-hidsag-showcase-hr`) |
| The app and its data | `presentation/belt-monitor/` (`live/summary.json` hashes every source) |
| Earlier tracks | `training/hidsag-v6-live-20261001/`, `training/bushveld-xrf-pge-20261001/`, `training/plant-softsensor-20261001/`, `training/pentlandite-diagnostic-20261001/` |
| What was tried and why | `docs/BUILDLOG.md` (2026-10-02 entry) |
