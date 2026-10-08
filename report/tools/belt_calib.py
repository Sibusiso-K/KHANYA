"""Bound calibration numbers + per-sample CSV for the report's calibration figure.
Reproduces value_chain.py's arrays from the committed v6 and v8 results (branch codex/pwa-phase-roadmap)."""
import json, os
import numpy as np
S_ = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(S_, "v6.json")))["records"]["GEOMET"]
t = R["targets"].index("WI")
Y = np.array(R["Y"], float)[:, t]
S = sorted(R["samples"], key=lambda r: r["sample"])
fold = np.array([r["fold"] for r in S]); pred = np.array([r["pred"][t] for r in S]); ood = np.array([r["ood"] for r in S])
true = Y
p90 = np.array([np.percentile(true[fold != f], 90) for f in fold])
V8 = {r["sample"]: r for r in json.load(open(os.path.join(S_, "v8.json")))["records"]["GEOMET"]["samples"]}
assert all(abs(V8[r["sample"]]["pred"][t] - r["pred"][t]) < 1e-9 for r in S)
ub = np.array([np.nan if V8[r["sample"]]["hi_up"][t] is None else V8[r["sample"]]["hi_up"][t] for r in S])
deployed = np.where(ood == "refused", p90, np.where(ood == "borderline", np.maximum(ub, p90), ub))
print("n", len(true), "finite bounds", np.isfinite(ub).sum())
print("exceedance (true > bound) %.4f" % np.nanmean(true > ub))
w = ub - pred
print("bound margin above prediction: mean %.3f median %.3f min %.3f max %.3f kWh/t" % (np.nanmean(w), np.nanmedian(w), np.nanmin(w), np.nanmax(w)))
print("mean bound %.3f, mean design p90 %.3f, mean true %.3f" % (np.nanmean(ub), p90.mean(), true.mean()))
feed = p90 / deployed
print("deployed feed vs design: mean %.4f median %.4f min %.4f max %.4f" % (feed.mean(), np.median(feed), feed.min(), feed.max()))
print("share of parcels where deployed proposal < design feed (bound harder than design): %.3f" % (feed < 1 - 1e-12).mean())
print("share at exactly design feed (conservative/refused): %.3f" % (np.isclose(feed, 1)).mean())
print("outside demo envelope 85-110%%: below %.3f above %.3f" % ((feed < 0.85).mean(), (feed > 1.10).mean()))
print("ood", {k: int((ood == k).sum()) for k in ("pass", "borderline", "refused")})
with open(os.path.join(S_, "calib.csv"), "w") as f:
    f.write("true,pred,bound,ood\n")
    for a, b, c, o in zip(true, pred, ub, ood):
        f.write("%.3f,%.3f,%.3f,%s\n" % (a, b, c, o))
print("wrote calib.csv")

# envelope-clipped replay (85-110% of design feed), same throughput formula as value_chain.py
rng = np.random.default_rng(1)
def rel(used, b): return p90[b].sum() / used[b].sum() - 1
clip_used = p90 / np.clip(p90 / deployed, 0.85, 1.10)
for name, u in (("deployed", deployed), ("deployed_clipped_85_110", clip_used)):
    bs = [rel(u, rng.integers(0, 146, 146)) for _ in range(4000)]
    print("%-26s tput %+.4f CI [%+.4f, %+.4f]  overload %.4f" % (name, rel(u, slice(None)), np.percentile(bs, 2.5), np.percentile(bs, 97.5), (true > u).mean()))
