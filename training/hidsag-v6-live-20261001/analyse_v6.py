"""Local analysis of the v6 Kaggle output (all statistics computed here, from per-sample out-of-fold rows).

Per target and record:
  * deployable pipeline (proper-training model) and full-refit accuracy: R2, MAE
  * baselines: proper-training mean / median, metadata-only (MINERAL1); strongest = lowest MAE
  * gates (paired, unit level): cluster-bootstrap 95% CI of the MAE difference, Wilcoxon signed-rank on unit-mean paired
    differences with Holm correction across targets in the record, matched-pairs rank-biserial; plus the doctrine's
    Mann-Whitney (unpaired) and Cliff's delta. "better" needs CI < 0, Holm-Wilcoxon < 0.05 and Mann-Whitney < 0.05.
      - v6 full-refit vs v5 published OOF (same folds; v5 rows matched by sample id)
      - v6 deployable vs the strongest baseline
      - hyperspectral deployable vs matched simulated-RGB deployable
  * coverage of the 80% split-conformal interval at the unit level (GEOMET sample; MINERAL1 composite = all fractions
    covered), Clopper-Pearson CI, median width; OOD refusal / borderline rates; shifted-domain acceptance per fold
  * blends (MINERAL1, sim_): R2 and MAE vs the mean baseline, CI by resampling parent pairs
"""
import json, os
import numpy as np
from scipy.stats import binomtest, mannwhitneyu, wilcoxon

HERE = os.path.dirname(os.path.abspath(__file__))
V6 = json.load(open(os.path.join(HERE, "output", "hidsag_v6_results.json")))
V5 = json.load(open(os.path.join(HERE, "..", "hidsag-v5-belt-20261001", "output", "hidsag_v5_results.json")))


def r2(y, p):
    ss = ((y - y.mean()) ** 2).sum()
    return float(1 - ((y - p) ** 2).sum() / ss) if ss > 0 else float("nan")


def holm(ps):
    ps = np.asarray(ps, float)
    order = np.argsort(ps)
    adj = np.empty_like(ps)
    m, run = len(ps), 0.0
    for r, i in enumerate(order):
        run = max(run, (m - r) * ps[i])
        adj[i] = min(1.0, run)
    return adj


def paired(y, p_new, p_old, units, B=3000, seed=1):
    e1, e0 = np.abs(y - p_new), np.abs(y - p_old)
    rng = np.random.default_rng(seed)
    ug = np.unique(units)
    idx = {u: np.flatnonzero(units == u) for u in ug}
    v = []
    for _ in range(B):
        b = np.concatenate([idx[ug[i]] for i in rng.integers(0, len(ug), len(ug))])
        v.append(e1[b].mean() - e0[b].mean())
    d = np.array([e1[idx[u]].mean() - e0[idx[u]].mean() for u in ug])
    nz = d[d != 0]
    try:
        wp = float(wilcoxon(nz, alternative="less").pvalue) if len(nz) else 1.0
        wq = float(wilcoxon(nz, alternative="greater").pvalue) if len(nz) else 1.0
    except ValueError:
        wp = wq = 1.0
    return {"mae_new": float(e1.mean()), "mae_old": float(e0.mean()), "diff": float(e1.mean() - e0.mean()),
            "ci95": [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))], "wilcoxon_less": wp, "wilcoxon_greater": wq,
            "rank_biserial": float(((d < 0).sum() - (d > 0).sum()) / max(len(d), 1)),
            "mannwhitney_less": float(mannwhitneyu(e1, e0, alternative="less").pvalue),
            "mannwhitney_greater": float(mannwhitneyu(e1, e0, alternative="greater").pvalue),
            "cliffs_delta": float(np.sign(e1[:, None] - e0[None, :]).mean()), "n_units": int(len(ug))}


def verdicts(results):
    """Holm across targets within a record, then the all-gates verdict."""
    for key in ("vs_v5", "vs_baseline", "hs_vs_rgb"):
        items = [(t, r[key]) for t, r in results.items() if r.get(key)]
        if not items:
            continue
        hl = holm([g["wilcoxon_less"] for _, g in items])
        hg = holm([g["wilcoxon_greater"] for _, g in items])
        for (t, g), a, b in zip(items, hl, hg):
            g["wilcoxon_less_holm"], g["wilcoxon_greater_holm"] = float(a), float(b)
            if g["ci95"][1] < 0 and a < 0.05 and g["mannwhitney_less"] < 0.05:
                g["verdict"] = "better"
            elif g["ci95"][0] > 0 and b < 0.05 and g["mannwhitney_greater"] < 0.05:
                g["verdict"] = "worse"
            else:
                g["verdict"] = "no significant difference"


out = {"records": {}}
for rec, R in V6["records"].items():
    if "targets" not in R:
        continue
    keep, S = R["targets"], R["samples"]
    Y = np.array(R["Y"])
    names = [s["sample"] for s in S]
    units = np.array([s["unit"] for s in S])
    v5t = V5["records"][rec]["targets"]
    v5map = {t: {o["sample"]: o["pred"] for o in v5t[t]["oof"]} for t in keep if t in v5t}
    res = {}
    for t, k in enumerate(keep):
        y = Y[:, t]
        P = np.array([s["pred"][t] for s in S])
        F = np.array([s["full_refit"][t] for s in S])
        G = np.array([s["rgb"][t] for s in S])
        lo, hi = np.array([s["lo"][t] for s in S]), np.array([s["hi"][t] for s in S])
        bases = {"mean": np.array([s["mean"][t] for s in S]), "median": np.array([s["median"][t] for s in S])}
        if S[0]["meta"] is not None:
            bases["metadata"] = np.array([s["meta"][t] for s in S])
        strongest = min(bases, key=lambda b: np.abs(y - bases[b]).mean())
        cov_unit = {}
        for u in np.unique(units):
            m = units == u
            cov_unit[u] = bool(np.all((y[m] >= lo[m]) & (y[m] <= hi[m])))
        kc, nc = sum(cov_unit.values()), len(cov_unit)
        ci = binomtest(kc, nc).proportion_ci(method="exact")
        fam = {}
        for s in S:
            f = s["choice"][t].split("_")[0]
            fam[f] = fam.get(f, 0) + 1
        entry = {"r2_deployable": r2(y, P), "mae_deployable": float(np.abs(y - P).mean()), "r2_full_refit": r2(y, F),
                 "mae_full_refit": float(np.abs(y - F).mean()), "r2_rgb": r2(y, G),
                 "baselines_mae": {b: float(np.abs(y - v).mean()) for b, v in bases.items()}, "strongest_baseline": strongest,
                 "coverage_units": kc / nc, "coverage_ci95": [float(ci.low), float(ci.high)], "n_units": nc,
                 "median_width": float(np.median(hi - lo)), "family_share_of_samples": fam,
                 "vs_baseline": paired(y, P, bases[strongest], units), "hs_vs_rgb": paired(y, P, G, units)}
        if k in v5map:
            p5 = np.array([v5map[k][n] for n in names])
            entry["r2_v5"] = r2(y, p5)
            entry["vs_v5"] = paired(y, F, p5, units)
        res[k] = entry
    verdicts(res)
    ood = [s["ood"] for s in S]
    folds = R["folds"]
    blend = None
    if R["blends"]:
        bl = R["blends"]
        pairs = sorted({b["pair"] for b in bl})
        bt = {}
        for t, k in enumerate(keep):
            yt = np.array([b["true"][t] for b in bl])
            pt = np.array([b["pred"][t] for b in bl])
            mt = np.array([b["mean"][t] for b in bl])
            pid = np.array([b["pair"] for b in bl])
            g = paired(yt, pt, mt, pid)
            bt[k] = {"r2": r2(yt, pt), "mae": float(np.abs(yt - pt).mean()), "mae_mean": float(np.abs(yt - mt).mean()), "diff_ci95_pairs": g["ci95"]}
        blend = {"n_blends": len(bl), "n_parent_pairs": len(pairs), "targets": bt,
                 "median_r2": float(np.median([v["r2"] for v in bt.values()])),
                 "beats_mean_ci": int(sum(v["diff_ci95_pairs"][1] < 0 for v in bt.values()))}
    out["records"][rec] = {"n": R["n"], "n_units": R["n_units"], "targets": res,
                           "ood": {"refused": ood.count("refused") / len(ood), "borderline": ood.count("borderline") / len(ood),
                                   "shift_accept_le_p99_per_fold": [f["ood_shift"]["accepted_le_p99"] if f["ood_shift"] else None for f in folds]},
                           "calibration": [{"n_cal_units": f["n_cal_units"], "k": f["k"], "unbounded": f["unbounded"]} for f in folds],
                           "blends": blend}
json.dump(out, open(os.path.join(HERE, "analysis_v6.json"), "w"), indent=1)

for rec, R in out["records"].items():
    T = R["targets"]
    print(f"\n=== {rec}: n={R['n']} units={R['n_units']} | OOD refused {R['ood']['refused']:.2f} borderline {R['ood']['borderline']:.2f} | shift accept per fold {R['ood']['shift_accept_le_p99_per_fold']}")
    print(f"    calibration: {R['calibration']}")
    cnt = lambda key, v: sum(1 for x in T.values() if x.get(key, {}).get("verdict") == v)
    print(f"    v6 vs v5: better {cnt('vs_v5','better')} worse {cnt('vs_v5','worse')} of {len(T)} | vs strongest baseline: better {cnt('vs_baseline','better')} | HS vs RGB: better {cnt('hs_vs_rgb','better')} worse {cnt('hs_vs_rgb','worse')}")
    cov = [x["coverage_units"] for x in T.values()]
    print(f"    coverage (units) median {np.median(cov):.2f} min {min(cov):.2f} max {max(cov):.2f}")
    show = list(T.items()) if rec == "GEOMET" else sorted(T.items(), key=lambda kv: -kv[1]["r2_full_refit"])[:10]
    for k, x in show:
        print(f"    {k:22s} R2 deploy {x['r2_deployable']:.3f} full {x['r2_full_refit']:.3f} v5 {x.get('r2_v5', float('nan')):.3f} rgb {x['r2_rgb']:.3f} | "
              f"vs v5 {x.get('vs_v5', {}).get('verdict', '-')} | vs {x['strongest_baseline']} {x['vs_baseline']['verdict']} | "
              f"cover {x['coverage_units']:.2f} [{x['coverage_ci95'][0]:.2f},{x['coverage_ci95'][1]:.2f}] width {x['median_width']:.3g} | fam {x['family_share_of_samples']}")
    if R["blends"]:
        b = R["blends"]
        print(f"    blends (sim_): {b['n_blends']} from {b['n_parent_pairs']} parent pairs; median R2 {b['median_r2']:.3f}; beats mean (pair-CI) {b['beats_mean_ci']}/{len(b['targets'])}")
