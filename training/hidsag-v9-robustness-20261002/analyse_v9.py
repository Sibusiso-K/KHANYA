"""v9 robustness analysis, exactly as PREREG.md (committed before the run; this script committed before its output).
Run: python training/hidsag-v9-robustness-20261002/analyse_v9.py -> analysis_v9.json"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "output", "hidsag_v9_robust_results.json")))["records"]["GEOMET"]
V6 = json.load(open(os.path.join(HERE, "..", "hidsag-v6-live-20261001", "output", "hidsag_v6_results.json")))["records"]["GEOMET"]
B = 4000
GATE = {"resample": 1.10, "half": 1.25, "noise_2pct": 1.25}
targets = R["targets"]
S = sorted(R["samples"], key=lambda s: s["sample"])
Y = np.array(R["Y"], float)
v6 = {s["sample"]: s for s in V6["samples"]}
names = list(S[0]["variants"].keys())
out = {"prereg": "PREREG.md", "n": len(S), "reproduces_v6_max_abs_diff": {}, "targets": {}}
for ti, t in enumerate(targets):
    out["reproduces_v6_max_abs_diff"][t] = float(max(abs(s["pred"][ti] - v6[s["sample"]]["pred"][ti]) for s in S))
rng = np.random.default_rng(5)
idx_boot = [rng.integers(0, len(S), len(S)) for _ in range(B)]
for ti, t in enumerate(targets):
    y = Y[:, ti]
    err = {k: np.abs(np.array([s["variants"][k]["pred"][ti] for s in S]) - y) for k in names}
    res = {}
    for k in names:
        ratio = err[k].mean() / err["original"].mean()
        boots = [err[k][b].mean() / err["original"][b].mean() for b in idx_boot]
        d2 = np.array([s["variants"][k]["ood_d2"] for s in S])
        p95 = np.array([s["ood_p95"] for s in S])
        p99 = np.array([s["ood_p99"] for s in S])
        flagged = d2 > p95
        big = err[k] > 2 * err["original"].mean()
        res[k] = {"mae": float(err[k].mean()), "mae_ratio_vs_original": float(ratio),
                  "ratio_ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
                  "flagged_borderline_or_refused": float(flagged.mean()), "refused": float((d2 > p99).mean()),
                  "silent_large_errors": float((big & ~flagged).mean())}
        if k in GATE:
            res[k]["gate_upper"] = GATE[k]
            res[k]["verdict"] = ("equivalent within +10%" if k == "resample" else "tolerant") if res[k]["ratio_ci95"][1] <= GATE[k] else "NOT shown within the gate"
    out["targets"][t] = res
json.dump(out, open(os.path.join(HERE, "analysis_v9.json"), "w"), indent=1)
print("reproduces v6 (max abs diff):", {k: round(v, 6) for k, v in out["reproduces_v6_max_abs_diff"].items()})
for t in ["WI"] + [x for x in targets if x != "WI"]:
    print("==", t)
    for k, v in out["targets"][t].items():
        print(f"  {k:12s} MAE {v['mae']:.3f} ratio {v['mae_ratio_vs_original']:.3f} CI {[round(a, 3) for a in v['ratio_ci95']]} "
              f"flagged {v['flagged_borderline_or_refused']*100:5.1f}% refused {v['refused']*100:5.1f}% silent-large {v['silent_large_errors']*100:4.1f}% {v.get('verdict', '')}")
