"""From prediction to the next plant step: what each REEFPRINT prediction changes, measured on real held-out data.

Doctrine: code does the arithmetic; every policy result here is a simulation on REAL out-of-fold predictions (prefix sim_);
anything not measured is labelled ASSUMED and kept out of the measured numbers.

1. GRINDING (HIDSAG GEOMET, 146 drill-core samples, v6 out-of-fold predictions and 80% split-conformal intervals).
   Next step: the mill feed rate. Bond (1961): specific grinding energy W = 10 * Wi * (1/sqrt(P80) - 1/sqrt(F80)) kWh/t.
   For a power-limited mill at a fixed grind target, throughput = P / W, so throughput is proportional to 1 / Wi_used.
   Mill power, F80 and P80 CANCEL in every ratio below, so the relative results need no assumed plant parameters.
   Policies (all set before the ore reaches the mill; equal-mass parcels):
     blind_p90   feed rate set for the training-fold 90th-percentile Wi (no ore information; ~10% of parcels harder than planned)
     belt_hi     feed rate set for the belt's conformal upper bound (80% two-sided -> ~10% of parcels harder than planned by design)
     belt_point  feed rate set for the point prediction (aggressive; shown for contrast)
     oracle      feed rate set for the true Wi (the ceiling: perfect information)
   Measured per policy: throughput relative to blind_p90 (total tonnes / total hours), the share of parcels harder than
   planned ("overload": the mill cannot hold the grind and it coarsens), and the energy shortfall on those parcels.
   blind_p90 and belt_hi are matched on NOMINAL risk (both ~10%), fixed in advance, so no test information sets either.

2. GRADE ROUTING (Bachmann et al. 2019 Bushveld chromitite assays, 1,112 intervals, 123 projects, held out by project).
   Next step: send a parcel to the concentrator or to a low-grade stockpile, by predicted 4E against a cut-off.
   The cut-off is the training-fold median 4E (data-derived, fixed in advance; a site would use its economic cut-off).
   Compared: belt chemistry model, the mine-plan seam (training-fold median 4E of the parcel's seam: what a mine already
   knows), and no information (everything to the mill). Measured: balanced accuracy of the routing, the share of 4E metal
   sent to the mill, and the share of below-cut-off mass sent to the mill. Units = projects for every interval.

Run:  python training/value-chain-20261002/value_chain.py  ->  results.json (+ prints a summary)
"""
import json, os
import numpy as np
from scipy.stats import mannwhitneyu, wilcoxon

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
B_BOOT = 4000


def boot_ci(stat, units, B=B_BOOT, seed=1):
    """Cluster bootstrap over units (resample units with replacement, recompute the statistic)."""
    rng = np.random.default_rng(seed)
    ug = np.unique(units)
    idx = {g: np.flatnonzero(units == g) for g in ug}
    v = []
    for _ in range(B):
        b = np.concatenate([idx[ug[i]] for i in rng.integers(0, len(ug), len(ug))])
        v.append(stat(b))
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]


def cliffs(a, b):
    return float(np.sign(np.asarray(a)[:, None] - np.asarray(b)[None, :]).mean())


# ------------------------------------------------------------------ 1. grinding
ALPHA_UP = 0.10          # one-sided: the feed is set for a hardness the parcel should exceed only ~10% of the time
NI_MARGIN = 0.03         # pre-registered non-inferiority margin on overload share (PLAN-v8 D3), ASSUMED operating tolerance
RAMPS = (None, 0.10, 0.05, 0.02)   # max relative feed change per parcel (ASSUMED values; None = unlimited)
N_ORDERS = 200           # HIDSAG parcels have no time order, so ramp effects are averaged over random orders


def one_sided_bound(pred, resid, fold, alpha=ALPHA_UP):
    """Cross-fold one-sided upper bound: pred_i + the ceil((1-a)(n+1))-th smallest signed out-of-fold residual from the
    OTHER folds. A CV+-style approximation (Barber et al. 2021): exact CV+ needs each fold model's prediction at x_i, which
    v6 did not store, so finite-sample validity is not claimed; the empirical exceedance is reported instead."""
    ub = np.empty_like(pred)
    for f in np.unique(fold):
        r = np.sort(resid[fold != f])
        k = int(np.ceil((1 - alpha) * (len(r) + 1)))
        q = r[min(k, len(r)) - 1] if k <= len(r) else np.inf
        ub[fold == f] = pred[fold == f] + q
    return ub


def ramp(used_target, order, x):
    """Feed rate ∝ 1/Wi_used. Limit the relative feed change per parcel to ±x along a given parcel order."""
    if x is None:
        return used_target.copy()
    feed_t = 1.0 / used_target
    out = np.empty_like(used_target)
    prev = feed_t[order[0]]
    for j, i in enumerate(order):
        f = feed_t[i] if j == 0 else min(max(feed_t[i], prev * (1 - x)), prev * (1 + x))
        out[i] = 1.0 / f
        prev = f
    return out


def grinding():
    R = json.load(open(os.path.join(T, "hidsag-v6-live-20261001", "output", "hidsag_v6_results.json")))["records"]["GEOMET"]
    t = R["targets"].index("WI")
    Y = np.array(R["Y"], float)[:, t]
    S = sorted(R["samples"], key=lambda r: r["sample"])
    assert len(S) == len(Y) == 146
    fold = np.array([r["fold"] for r in S])
    pred = np.array([r["pred"][t] for r in S])
    hi80 = np.array([r["hi"][t] for r in S])
    ood = np.array([r["ood"] for r in S])
    true = Y
    p90 = np.array([np.percentile(true[fold != f], 90) for f in fold])     # training-fold P90: the envelope's conservative setting
    pmean = np.array([true[fold != f].mean() for f in fold])
    units = np.array([r["sample"] for r in S])                             # no drill-hole ids exist in GEOMET
    resid = true - pred                                                    # signed out-of-fold residuals
    ub90 = one_sided_bound(pred, resid, fold)
    # the policy as it would be deployed: refused -> conservative envelope; borderline -> the stricter; pass -> the bound
    deployed = np.where(ood == "refused", p90, np.where(ood == "borderline", np.maximum(ub90, p90), ub90))
    policies = {"blind_p90": p90, "blind_mean": pmean, "belt_symmetric80_hi (old, comparator)": hi80,
                "belt_onesided90_all": ub90, "belt_deployed": deployed, "belt_point": pred, "oracle": true}

    def rel_tput(used, ref, b=slice(None)):
        return float(ref[b].sum() / used[b].sum() - 1.0)                    # equal-mass parcels: hours ∝ Σ Wi_used

    out = {"n_parcels": int(len(true)), "units": "samples (GEOMET has no drill-hole ids: may be optimistic)",
           "ood_counts": {k: int((ood == k).sum()) for k in ("pass", "borderline", "refused")},
           "wi_true": {"mean": float(true.mean()), "sd": float(true.std()), "min": float(true.min()), "max": float(true.max())},
           "one_sided_bound": {"alpha": ALPHA_UP, "method": "cross-fold residual quantile (CV+-style approximation, Barber et al. 2021); validity not claimed",
                               "empirical_exceedance": float((true > ub90).mean()),
                               "empirical_exceedance_ci95": boot_ci(lambda b: float((true[b] > ub90[b]).mean()), units)},
           "policies": {}}
    for k, used in policies.items():
        over = true > used
        out["policies"][k] = {
            "sim_throughput_vs_blind_p90": rel_tput(used, p90),
            "sim_throughput_vs_blind_p90_ci95": boot_ci(lambda b: rel_tput(used, p90, b), units),
            "sim_overload_share": float(over.mean()),
            "sim_overload_share_ci95": boot_ci(lambda b: float((true[b] > used[b]).mean()), units),
            "sim_excess_energy_required_when_overloaded": float((true[over] / used[over] - 1).mean()) if over.any() else 0.0,
            "sim_energy_shortfall_fraction_when_overloaded": float((1 - used[over] / true[over]).mean()) if over.any() else 0.0,
        }
    # gates for the deployed policy vs blind P90, and the pre-registered non-inferiority test on overload share
    d = deployed - p90
    rng = np.random.default_rng(7)
    diffs = []
    for _ in range(B_BOOT):
        bi = rng.integers(0, len(true), len(true))
        diffs.append((true[bi] > deployed[bi]).mean() - (true[bi] > p90[bi]).mean())
    ni_upper = float(np.percentile(diffs, 95))                              # one-sided 95% upper bound
    gate = {"median_paired_diff_wi_used": float(np.median(d)),
            "wilcoxon_p_less": float(wilcoxon(d, alternative="less").pvalue) if np.any(d != 0) else 1.0,
            "mannwhitney_p_less": float(mannwhitneyu(deployed, p90, alternative="less").pvalue), "cliffs_delta": cliffs(deployed, p90),
            "throughput_ci95": out["policies"]["belt_deployed"]["sim_throughput_vs_blind_p90_ci95"],
            "overload_diff": float((true > deployed).mean() - (true > p90).mean()),
            "noninferiority_margin": NI_MARGIN, "overload_diff_onesided95_upper": ni_upper,
            "noninferior": bool(ni_upper <= NI_MARGIN)}
    gate["throughput_verdict"] = ("better" if gate["throughput_ci95"][0] > 0 and gate["wilcoxon_p_less"] < 0.05 and gate["mannwhitney_p_less"] < 0.05
                                  else "no significant difference")
    gate["claim"] = (f"throughput gain at no worse than +{NI_MARGIN:.0%} overload risk" if gate["noninferior"] and gate["throughput_verdict"] == "better"
                     else "no throughput claim: non-inferiority on overload risk not shown" if not gate["noninferior"] else "no significant throughput gain")
    out["belt_deployed_vs_blind_p90"] = gate
    # ramp limits over random parcel orders (no real time order exists)
    rr = {}
    orders = [np.random.default_rng(100 + i).permutation(len(true)) for i in range(N_ORDERS)]
    for x in RAMPS:
        tp, ov = [], []
        for o in orders:
            u = ramp(deployed, o, x)
            pb = ramp(p90, o, x)
            tp.append(rel_tput(u, pb))
            ov.append(float((true > u).mean() - (true > pb).mean()))
        rr["unlimited" if x is None else f"{int(x * 100)}pct_per_parcel"] = {
            "throughput_vs_blind_mean": float(np.mean(tp)), "throughput_p05_p95": [float(np.percentile(tp, 5)), float(np.percentile(tp, 95))],
            "overload_diff_mean": float(np.mean(ov)), "overload_diff_p05_p95": [float(np.percentile(ov, 5)), float(np.percentile(ov, 95))]}
    out["ramp_limits_over_random_orders"] = rr
    out["share_of_perfect_information_captured"] = float(out["policies"]["belt_deployed"]["sim_throughput_vs_blind_p90"] /
                                                         out["policies"]["oracle"]["sim_throughput_vs_blind_p90"])
    out["not_simulated"] = ["an APC/feedback baseline: HIDSAG samples are not a time series, so no dynamic baseline can be simulated honestly",
                            "stale data, belt-to-mill transit and stockpile mixing (no timing exists in the data)",
                            "downstream constraints (flotation capacity, concentrate handling)"]
    out["assumptions"] = ["ASSUMED: the mill is power-limited and its feed rate can follow each parcel within the ramp limit",
                          "ASSUMED: Bond's law applies (ball-mill energy); a SAG circuit also needs the A×b parameter, which HIDSAG lacks",
                          "ASSUMED: HIDSAG's WI is the Bond ball-mill work index in kWh/t, as earlier runs and the registry treat it",
                          "ASSUMED: non-inferiority margin +3 pp overload share (pre-registered in PLAN-v8 D3; a site sets the real margin)",
                          "Mill power, F80 and P80 cancel in every ratio: no plant parameter is needed for the relative results"]
    return out


# ------------------------------------------------------------------ 2. grade routing
def routing():
    A = json.load(open(os.path.join(T, "bushveld-xrf-pge-20261001", "app_bushveld.json")))
    rows = A["rows"]
    k = "4E_ppm"
    true = np.array([r["pge"][k]["true"] for r in rows], float)
    pred = np.array([r["pge"][k]["pred"] for r in rows], float)
    fold = np.array([r["fold"] for r in rows])
    seam = np.array([r["seam"].strip() for r in rows])
    proj = np.array([r["project"] for r in rows])
    cut = np.array([np.median(true[fold != f]) for f in fold])
    seam_pred = np.zeros(len(rows))
    for f in np.unique(fold):
        tr, te = fold != f, fold == f
        med = {s: float(np.median(true[tr & (seam == s)])) for s in np.unique(seam[tr])}
        glob = float(np.median(true[tr]))
        seam_pred[te] = [med.get(s, glob) for s in seam[te]]
    above = true >= cut
    pols = {"belt_chemistry": pred >= cut, "mine_plan_seam": seam_pred >= cut, "no_information_all_to_mill": np.ones(len(rows), bool)}

    def metrics(send, b=slice(None)):
        a, s, tv = above[b], send[b], true[b]
        tpr = (s & a).sum() / max(a.sum(), 1)
        tnr = (~s & ~a).sum() / max((~a).sum(), 1)
        return {"balanced_accuracy": float((tpr + tnr) / 2), "metal_to_mill": float(tv[s].sum() / tv.sum()),
                "low_grade_mass_to_mill": float((s & ~a).sum() / max((~a).sum(), 1)), "mass_to_mill": float(s.mean())}

    out = {"n_intervals": int(len(rows)), "n_projects": int(len(np.unique(proj))), "cut_off": "training-fold median 4E (ppm = g/t)",
           "cut_off_values_g_per_t": sorted({round(float(c), 3) for c in cut}), "policies": {}}
    for name, send in pols.items():
        m = metrics(send)
        m["balanced_accuracy_ci95"] = boot_ci(lambda b: metrics(send, b)["balanced_accuracy"], proj)
        m["metal_to_mill_ci95"] = boot_ci(lambda b: metrics(send, b)["metal_to_mill"], proj)
        m["low_grade_mass_to_mill_ci95"] = boot_ci(lambda b: metrics(send, b)["low_grade_mass_to_mill"], proj)
        out["policies"][name] = m
    c, s = pols["belt_chemistry"], pols["mine_plan_seam"]
    out["chemistry_minus_seam_balanced_accuracy_ci95"] = boot_ci(lambda b: metrics(c, b)["balanced_accuracy"] - metrics(s, b)["balanced_accuracy"], proj)
    lo, hi_ = out["chemistry_minus_seam_balanced_accuracy_ci95"]
    out["chemistry_vs_seam"] = "chemistry better" if lo > 0 else ("seam better" if hi_ < 0 else "no significant difference")
    out["assumptions"] = ["ASSUMED: parcels of equal mass; the cut-off is data-derived, not an economic cut-off",
                          "Seam baseline = what the mine plan already knows; belt chemistry must beat it to add value",
                          "Units for every interval are projects (rule 2); 4E = Pt+Pd+Rh+Au as reported"]
    return out


def main():
    res = {"note": __doc__.split("\n\n")[0], "grinding": grinding(), "routing": routing(),
           "sources": {"grinding": "training/hidsag-v6-live-20261001/output/hidsag_v6_results.json (Kaggle reefprint-hidsag-v6-live)",
                       "routing": "training/bushveld-xrf-pge-20261001/app_bushveld.json (bushveld.py, GroupKFold by ProjectCode)",
                       "bond": "Bond, F.C. (1961) Crushing and grinding calculations, Br. Chem. Eng. 6:378-385, 543-548 (textbook form; primary not re-read this session)"}}
    json.dump(res, open(os.path.join(HERE, "results.json"), "w"), indent=1)
    g, r = res["grinding"], res["routing"]
    print("GRINDING (146 parcels, Wi %.1f ± %.1f kWh/t)" % (g["wi_true"]["mean"], g["wi_true"]["sd"]))
    for k, v in g["policies"].items():
        print(f"  {k:12s} throughput vs blind_p90 {v['sim_throughput_vs_blind_p90']*100:+6.2f}% {[round(x*100, 2) for x in v['sim_throughput_vs_blind_p90_ci95']]}"
              f"  overload {v['sim_overload_share']*100:5.1f}% {[round(x*100, 1) for x in v['sim_overload_share_ci95']]}  shortfall {v['sim_energy_shortfall_fraction_when_overloaded']*100:4.1f}%")
    print("  one-sided bound:", g["one_sided_bound"], " OOD:", g["ood_counts"])
    print("  gate deployed vs blind_p90:", {k: (round(v, 6) if isinstance(v, float) else v) for k, v in g["belt_deployed_vs_blind_p90"].items()})
    for k, v in g["ramp_limits_over_random_orders"].items():
        print(f"  ramp {k:22s} throughput {v['throughput_vs_blind_mean']*100:+5.2f}% (orders p5-p95 {[round(x*100, 2) for x in v['throughput_p05_p95']]})  overload diff {v['overload_diff_mean']*100:+5.2f} pp")
    print("  share of perfect-information gain captured: %.2f" % g["share_of_perfect_information_captured"])
    print("ROUTING (%d intervals, %d projects, cut-offs %s g/t)" % (r["n_intervals"], r["n_projects"], r["cut_off_values_g_per_t"]))
    for k, v in r["policies"].items():
        print(f"  {k:28s} bal.acc {v['balanced_accuracy']:.3f} {[round(x, 3) for x in v['balanced_accuracy_ci95']]}  metal to mill {v['metal_to_mill']*100:5.1f}%"
              f"  low-grade mass to mill {v['low_grade_mass_to_mill']*100:5.1f}%  mass to mill {v['mass_to_mill']*100:5.1f}%")
    print("  chemistry - seam balanced accuracy CI", [round(x, 3) for x in r["chemistry_minus_seam_balanced_accuracy_ci95"]], "->", r["chemistry_vs_seam"])


if __name__ == "__main__":
    main()
