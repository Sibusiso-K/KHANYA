"""Re-size the MINERAL1 confidence intervals at honest n (REEFPRINT rule 4).

Kaggle v4 scored MINERAL1 out-of-fold with GroupKFold over composites (process line x monthly sample, e.g. P1S1),
but its bootstrap resampled the 99 size-fraction samples, which treats correlated fractions of one composite as
independent. This resamples the 36 composites instead (cluster bootstrap) from the saved out-of-fold predictions.

python grouped_ci.py  ->  output_v4/mineral1_grouped_ci.json
"""
import json, os, re
import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error

HERE = os.path.dirname(os.path.abspath(__file__))
V4 = os.path.join(HERE, "output_v4")
res = json.load(open(os.path.join(V4, "hidsag_results.json")))["records"]["MINERAL1"]["targets"]
group = {}
for line in open(os.path.join(V4, "spectra_MINERAL1.jsonl"), encoding="utf-8"):
    r = json.loads(line)
    m = re.search(r"(P\d).*?(S\d+)", r["tags"] + " " + r["sample"])
    group[r["sample"]] = m.group(1) + m.group(2) if m else r["sample"]


def cluster_ci(y, p, g, fn, n=4000, seed=0):
    rng = np.random.default_rng(seed)
    ug = sorted(set(g))
    idx = {k: np.flatnonzero(g == k) for k in ug}
    vals = []
    for _ in range(n):
        pick = rng.choice(len(ug), len(ug), replace=True)
        b = np.concatenate([idx[ug[i]] for i in pick])
        if np.var(y[b]) > 0:
            vals.append(fn(y[b], p[b]))
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


out = {"method": "cluster bootstrap over composites (P#S#), 4000 resamples, seed 0; point estimates unchanged from Kaggle v4",
       "targets": {}}
for k, r in sorted(res.items()):
    name = k.split(".")[-1]
    y = np.array([o["true"] for o in r["oof"]])
    p = np.array([o["pred"] for o in r["oof"]])
    b = np.array([o["baseline"] for o in r["oof"]])
    g = np.array([group[o["sample"]] for o in r["oof"]])
    best = r["best_model"]
    t = {"n_samples": int(len(y)), "n_composites": int(len(set(g))), "model": best,
         "r2": float(r2_score(y, p)), "r2_ci95_cluster": cluster_ci(y, p, g, r2_score),
         "mae": float(mean_absolute_error(y, p)), "baseline_mae": float(mean_absolute_error(y, b)),
         "beats_baseline_mae": bool(r["beats_baseline_mae"])}
    # paired: is the model's MAE below the baseline's, resampling composites?
    rng = np.random.default_rng(1)
    ug = sorted(set(g))
    idx = {kk: np.flatnonzero(g == kk) for kk in ug}
    diffs = []
    for _ in range(4000):
        bb = np.concatenate([idx[ug[i]] for i in rng.choice(len(ug), len(ug), replace=True)])
        diffs.append(np.abs(y[bb] - p[bb]).mean() - np.abs(y[bb] - b[bb]).mean())
    t["mae_minus_baseline_ci95_cluster"] = [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))]
    t["beats_baseline_ci_excludes_zero"] = bool(t["mae_minus_baseline_ci95_cluster"][1] < 0)
    assert abs(t["r2"] - r[best]["r2"]) < 1e-9
    out["targets"][name] = t
json.dump(out, open(os.path.join(V4, "mineral1_grouped_ci.json"), "w"), indent=1)
for name, t in sorted(out["targets"].items(), key=lambda kv: -kv[1]["r2"]):
    print(f"{name:22s} R2={t['r2']:.3f} cluster CI [{t['r2_ci95_cluster'][0]:.2f},{t['r2_ci95_cluster'][1]:.2f}]  "
          f"MAE {t['mae']:.3f} vs {t['baseline_mae']:.3f}  beats(CI)={t['beats_baseline_ci_excludes_zero']}  groups={t['n_composites']}")
