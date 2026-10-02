"""Portability smoke test: load the Kaggle-exported model locally and run one inference on synthetic pixel pools.
The input is meaningless; this proves the export loads and runs, and times it on this laptop."""
import json, time, importlib.util
import numpy as np, joblib

b = joblib.load("output/geomet_model.joblib")
spec = importlib.util.spec_from_file_location("fm", "output/geomet_model_features.py")
fm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fm)
rng = np.random.default_rng(0)
pv = rng.uniform(2000, 9000, (1500, len(fm.GV))).astype(np.float32)
ps = rng.uniform(2000, 9000, (1500, len(fm.GS))).astype(np.float32)
t = time.perf_counter()
xn = np.concatenate([fm.spec_feats(pv, ps), fm.hist_feats(b["kms"], pv, ps)])[None]
A, Bl = b["sn"].transform(xn), b["sl"].transform(fm.lin_feats(pv, ps)[None])
ti = b["targets"].index("WI")
k = b["best"][ti]
m = b["models"][k]
X = A if k.startswith("nl_") else Bl
z = np.column_stack([q.predict(X).ravel() for q in m]) if isinstance(m, list) else m.predict(X).reshape(1, -1)
zi = z[0, ti] if z.shape[1] > 1 else z[0, 0]
wi = float(zi * b["ys"][ti] + b["ym"][ti])
ms = (time.perf_counter() - t) * 1000
print(f"local inference ok ({k}): WI on synthetic pools = {wi:.2f} kWh/t (portability only), {ms:.1f} ms on this laptop")
v6 = {s["sample"]: s for s in json.load(open("../hidsag-v6-live-20261001/output/hidsag_v6_results.json"))["records"]["GEOMET"]["samples"]}
R8 = json.load(open("output/hidsag_v8_model_results.json"))["records"]["GEOMET"]
v8 = {s["sample"]: s for s in R8["samples"]}
d = np.array([v8[s]["pred"][ti] - v6[s]["pred"][ti] for s in v6])
print("v8 vs v6 WI out-of-fold prediction difference: max abs", round(float(np.abs(d).max()), 4), "mean abs", round(float(np.abs(d).mean()), 4))
