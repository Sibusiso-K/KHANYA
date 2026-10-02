"""v7 vs v6 on GEOMET, paired by sample, with the gates fixed in PREREG.md before the run.

v7 beats v6 on a target only if: paired bootstrap 95% CI of the MAE difference excludes 0 (below), Holm-corrected Wilcoxon
p < 0.05, and Mann-Whitney p < 0.05 on the deployable absolute errors. Cliff's delta reported. Coverage must stay in band.
"""
import json, math, os
import numpy as np
from scipy.stats import mannwhitneyu, wilcoxon

HERE = os.path.dirname(os.path.abspath(__file__))
V6 = json.load(open(os.path.join(HERE, "..", "hidsag-v6-live-20261001", "output", "hidsag_v6_results.json")))["records"]["GEOMET"]
V7 = json.load(open(os.path.join(HERE, "output", "hidsag_v7_results.json")))["records"]["GEOMET"]
assert V6["targets"] == V7["targets"]
s6 = {r["sample"]: r for r in V6["samples"]}
s7 = {r["sample"]: r for r in V7["samples"]}
names = sorted(s6)
assert names == sorted(s7)
Y6, Y7 = np.array(V6["Y"]), np.array(V7["Y"])
assert np.allclose(Y6, Y7)
order = sorted(range(len(V6["samples"])), key=lambda i: V6["samples"][i]["sample"])
assert [V6["samples"][i]["sample"] for i in order] == names
Y = Y6  # rows follow the sorted sample order (model_record sorts rows by sample)
assert all(s6[n]["fold"] == s7[n]["fold"] for n in names), "folds differ: the comparison would not be paired"


def boot(d, B=4000, seed=1):
    rng = np.random.default_rng(seed)
    v = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(B)]
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]


def wilson(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [c - h, c + h]


out, ps = {}, []
for t, k in enumerate(V6["targets"]):
    y = Y[:, t]
    for kind in ("pred", "full_refit"):
        e6 = np.abs(np.array([s6[n][kind][t] for n in names]) - y)
        e7 = np.abs(np.array([s7[n][kind][t] for n in names]) - y)
        d = e7 - e6
        res = {"mae_v6": float(e6.mean()), "mae_v7": float(e7.mean()), "diff_ci95": boot(d),
               "wilcoxon_p_less": float(wilcoxon(d, alternative="less").pvalue) if np.any(d != 0) else 1.0,
               "mannwhitney_p_less": float(mannwhitneyu(e7, e6, alternative="less").pvalue),
               "cliffs_delta": float(np.sign(e7[:, None] - e6[None, :]).mean()),
               "r2_v6": float(1 - (e6 ** 2).sum() / ((y - y.mean()) ** 2).sum()) if False else None}
        r6 = np.array([s6[n][kind][t] for n in names]); r7 = np.array([s7[n][kind][t] for n in names])
        res["r2_v6"] = float(1 - ((r6 - y) ** 2).sum() / ((y - y.mean()) ** 2).sum())
        res["r2_v7"] = float(1 - ((r7 - y) ** 2).sum() / ((y - y.mean()) ** 2).sum())
        out.setdefault(k, {})[kind] = res
        if kind == "pred":
            ps.append((k, res["wilcoxon_p_less"]))
    lo = np.array([s7[n]["lo"][t] for n in names]); hi = np.array([s7[n]["hi"][t] for n in names])
    cov = int(((y >= lo) & (y <= hi)).sum())
    out[k]["coverage_v7"] = {"rate": cov / len(y), "ci95": wilson(cov, len(y))}
    out[k]["median_width_v6_v7"] = [float(np.median(np.array([s6[n]["hi"][t] - s6[n]["lo"][t] for n in names]))),
                                    float(np.median(hi - lo))]
# Holm over the five deployable comparisons
m = len(ps)
for rank, (k, p) in enumerate(sorted(ps, key=lambda x: x[1])):
    out[k]["pred"]["wilcoxon_p_holm"] = min(1.0, p * (m - rank))
# enforce monotonicity of Holm-adjusted p
prev = 0.0
for k, p in sorted(ps, key=lambda x: x[1]):
    prev = max(prev, out[k]["pred"]["wilcoxon_p_holm"])
    out[k]["pred"]["wilcoxon_p_holm"] = prev
for k in out:
    r = out[k]["pred"]
    cov_ok = out[k]["coverage_v7"]["ci95"][0] <= 0.80 <= out[k]["coverage_v7"]["ci95"][1]
    better = r["diff_ci95"][1] < 0 and r["wilcoxon_p_holm"] < 0.05 and r["mannwhitney_p_less"] < 0.05
    worse = r["diff_ci95"][0] > 0
    out[k]["verdict"] = ("v7 better" if better and cov_ok else "v7 worse" if worse else "no significant difference") + ("" if cov_ok else " (coverage out of band)")
json.dump({"prereg": "PREREG.md", "n": len(names), "targets": out}, open(os.path.join(HERE, "compare_v7.json"), "w"), indent=1)
for k, v in out.items():
    r = v["pred"]
    print(f"{k:10s} MAE v6 {r['mae_v6']:.3f} v7 {r['mae_v7']:.3f}  diff CI {[round(x, 3) for x in r['diff_ci95']]}  Holm p {r['wilcoxon_p_holm']:.3f}  MW p {r['mannwhitney_p_less']:.3f}  "
          f"δ {r['cliffs_delta']:+.3f}  R² {r['r2_v6']:.3f}->{r['r2_v7']:.3f}  cov {v['coverage_v7']['rate']:.3f}  -> {v['verdict']}")
