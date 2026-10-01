"""T3 — real plant parameters: forecast % silica in flotation concentrate ahead of the lab assay.

Data: Kaggle "Quality Prediction in a Mining Process" (edumagalhaes), a real iron-ore flotation plant in Brazil,
Mar-Sep 2017, CC0-1.0 (read from the dataset metadata 2026-10-01). Iron ore, not PGM: this demonstrates how a model
output maps to real plant parameters and a forecast ahead of the assay (the brief's "adjust plant parameters").

Timing (PLAN-live-v6.md §B):
  * the `date` column is the hour bin; process tags are 20 s samples inside it -> completed hourly bins
  * lab assays (% Iron / % Silica Concentrate, and the feed grades) describe the hour bin and are ASSUMED available
    DELAY hours after the bin closes (default 2 h; sensitivity 1 h and 4 h)
  * issue time = end of bin t. Features: process bins t, t-1, t-2 and the latest lab values available by then.
    Target: silica of bin t+h (h = 1, 3 hours, clock-based; missing hours are never row-shifted).
Periods: train Mar-Jun, tune Jul, calibrate Aug, test Sep (frozen before Sep), 12 h purge at each boundary.
Baselines: persistence (latest available lab silica), training mean, training median.
Intervals: split-conformal (80%) on August residuals; September coverage with 24 h block bootstrap.
Explanations: tag-group occlusion (replace the group with its training mean) — associations, not causes.
Outputs: results.json (metrics, gates, coverage) and app_series.json (September hourly replay for the app).
"""
import json, math, os, sys
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "..", "..", "data", "kaggle_flotation", "MiningProcess_Flotation_Plant_Database.csv")
ALPHA = 0.2
LAB = ["% Iron Concentrate", "% Silica Concentrate", "% Iron Feed", "% Silica Feed"]
GROUPS = {"Reagents (starch, amina)": ["Starch Flow", "Amina Flow"],
          "Pulp (flow, pH, density)": ["Ore Pulp Flow", "Ore Pulp pH", "Ore Pulp Density"],
          "Column air flows": [f"Flotation Column 0{i} Air Flow" for i in range(1, 8)],
          "Column levels": [f"Flotation Column 0{i} Level" for i in range(1, 8)]}
PROC = [c for g in GROUPS.values() for c in g]


def load():
    df = pd.read_csv(CSV, decimal=",", parse_dates=["date"])
    hourly = df.groupby("date").agg({**{c: "mean" for c in PROC}, **{c: "first" for c in LAB}})
    hourly["n_rows"] = df.groupby("date").size()
    return hourly.sort_index()


def build(hourly, delay, h):
    idx = hourly.index
    full = pd.date_range(idx.min(), idx.max(), freq="h")
    H = hourly.reindex(full)
    rows = []
    for t in full:
        if pd.isna(H.loc[t, PROC[0]]):
            continue                                   # bin t must exist (completed)
        tgt_t = t + pd.Timedelta(hours=h)
        if tgt_t not in H.index or pd.isna(H.loc[tgt_t, "% Silica Concentrate"]):
            continue
        f = {}
        for lag in (0, 1, 2):
            tl = t - pd.Timedelta(hours=lag)
            for c in PROC:
                f[f"{c} [t-{lag}]"] = H.loc[tl, c] if tl in H.index else np.nan
        s_star = t - pd.Timedelta(hours=delay)        # latest lab bin available at issue time
        avail = H.loc[:s_star, "% Silica Concentrate"].dropna()
        if avail.empty:
            continue
        last = avail.index[-1]
        f["lab silica [latest]"] = H.loc[last, "% Silica Concentrate"]
        f["lab iron [latest]"] = H.loc[last, "% Iron Concentrate"]
        f["feed silica [latest]"] = H.loc[last, "% Silica Feed"]
        f["feed iron [latest]"] = H.loc[last, "% Iron Feed"]
        prev = avail.iloc[-3:]
        f["lab silica [mean of last 3]"] = prev.mean()
        f["lab age h"] = (t - last) / pd.Timedelta(hours=1)
        rows.append({"issue": t, "target_time": tgt_t, "y": H.loc[tgt_t, "% Silica Concentrate"], "persist": f["lab silica [latest]"], **f})
    return pd.DataFrame(rows)


def period(ts):
    m = ts.month
    return "train" if m <= 6 else ("tune" if m == 7 else ("cal" if m == 8 else "test"))


def purge(df):
    keep = []
    for _, r in df.iterrows():
        p_issue, p_tgt = period(r["issue"]), period(r["target_time"])
        start = pd.Timestamp(year=r["issue"].year, month=r["issue"].month, day=1)
        keep.append(p_issue == p_tgt and (r["issue"] - start) >= pd.Timedelta(hours=12))
    return df[np.array(keep)]


def candidates():
    c = {f"ridge{a}": (lambda a=a: make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=a))) for a in (1, 10, 100)}
    for d, lr in ((3, 0.05), (6, 0.05), (3, 0.1)):
        c[f"hgb_d{d}_lr{lr}"] = (lambda d=d, lr=lr: HistGradientBoostingRegressor(max_depth=d, learning_rate=lr, max_iter=400, random_state=0))
    return c


def block_boot(fn, n, block=24, B=2000, seed=0):
    rng = np.random.default_rng(seed)
    nb = int(math.ceil(n / block))
    vals = []
    for _ in range(B):
        starts = rng.integers(0, max(1, n - block + 1), nb)
        idx = np.concatenate([np.arange(s, min(s + block, n)) for s in starts])[:n]
        vals.append(fn(idx))
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def cliffs(x, y):
    return float(np.sign(x[:, None] - y[None, :]).mean())


def run(hourly, delay, h, detail=False):
    df = purge(build(hourly, delay, h))
    feats = [c for c in df.columns if c not in ("issue", "target_time", "y", "persist")]
    P = df["issue"].map(period)
    tr, tu, ca, te = (df[P == p] for p in ("train", "tune", "cal", "test"))
    C = candidates()
    tune = {}
    for k, mk in C.items():
        m = mk().fit(tr[feats], tr["y"])
        tune[k] = float(np.abs(m.predict(tu[feats]) - tu["y"]).mean())
    best = min(sorted(tune), key=lambda k: tune[k])
    trtu = pd.concat([tr, tu])
    model = C[best]().fit(trtu[feats], trtu["y"])               # frozen before calibration and test
    cal_res = np.abs(model.predict(ca[feats]) - ca["y"].values)
    n_cal = len(cal_res)
    kq = int(math.ceil((n_cal + 1) * (1 - ALPHA)))
    q = float(np.sort(cal_res)[kq - 1]) if kq <= n_cal else float("inf")
    yt = te["y"].values
    pt = model.predict(te[feats])
    pers = te["persist"].values
    mean_b, med_b = float(trtu["y"].mean()), float(trtu["y"].median())
    e_m, e_p = np.abs(yt - pt), np.abs(yt - pers)
    e_mean, e_med = np.abs(yt - mean_b), np.abs(yt - med_b)
    n = len(yt)
    cover = (yt >= pt - q) & (yt <= pt + q)
    strongest = min((("persistence", e_p), ("training mean", e_mean), ("training median", e_med)), key=lambda kv: kv[1].mean())
    diff_ci = block_boot(lambda idx: e_m[idx].mean() - strongest[1][idx].mean(), n)
    p_mw = float(mannwhitneyu(e_m, strongest[1], alternative="less").pvalue)
    verdict = "better" if (diff_ci[1] < 0 and p_mw < 0.05) else ("worse" if diff_ci[0] > 0 else "no significant difference")
    res = {"delay_h": delay, "horizon_h": h, "model": best, "tune_mae": tune, "n": {"train": len(tr), "tune": len(tu), "cal": n_cal, "test": n},
           "q80": q, "k": kq,
           "test": {"mae_model": float(e_m.mean()), "mae_persistence": float(e_p.mean()), "mae_mean": float(e_mean.mean()), "mae_median": float(e_med.mean()),
                    "r2_model": float(1 - ((yt - pt) ** 2).sum() / ((yt - yt.mean()) ** 2).sum()),
                    "strongest_baseline": strongest[0], "mae_diff_vs_strongest_ci95_block": diff_ci, "mannwhitney_p_less": p_mw,
                    "cliffs_delta": cliffs(e_m, strongest[1]), "verdict": verdict,
                    "coverage": float(cover.mean()), "coverage_ci95_block": block_boot(lambda idx: cover[idx].mean(), n),
                    "width": 2 * q}}
    if detail:
        te = te.copy()
        te["pred"], te["lo"], te["hi"] = pt, pt - q, pt + q
        means = trtu[feats].mean()
        expl = []
        for gname, cols in list(GROUPS.items()) + [("Lab and feed history", [c for c in feats if "[latest]" in c or "last 3" in c])]:
            cols_f = [c for c in feats if any(c.startswith(x) for x in cols)] if gname != "Lab and feed history" else cols
            X = te[feats].copy()
            for c in cols_f:
                X[c] = means[c]
            expl.append((gname, pt - model.predict(X)))
        t_hi = float(np.percentile(trtu["y"], 75))
        series = []
        for j, (_, r) in enumerate(te.iterrows()):
            lo, hi = r["lo"], r["hi"]
            stale = r["lab age h"] > delay + 3
            if stale:
                dec = "conservative_default"
            elif lo >= t_hi:
                dec = "conservative_default"
            elif hi >= t_hi:
                dec = "verify"
            else:
                dec = "act"
            top = sorted(((g, float(d[j])) for g, d in expl), key=lambda kv: -abs(kv[1]))[:3]
            series.append({"issue": r["issue"].isoformat(), "target_time": r["target_time"].isoformat(), "y": float(r["y"]), "pred": float(r["pred"]),
                           "lo": float(lo), "hi": float(hi), "persist": float(r["persist"]), "decision": dec, "lab_age_h": float(r["lab age h"]),
                           "explain": [{"group": g, "delta": d} for g, d in top],
                           "tags": {c: (None if pd.isna(r[f"{c} [t-0]"]) else float(r[f"{c} [t-0]"])) for c in PROC}})
        res["app"] = {"threshold_upper_illustrative": t_hi, "series": series}
    return res


def main():
    hourly = load()
    print("hours", len(hourly), "from", hourly.index.min(), "to", hourly.index.max(), "rows/hour median", int(hourly["n_rows"].median()))
    out = {"data": "Kaggle edumagalhaes/quality-prediction-in-a-mining-process, CC0-1.0, iron-ore flotation plant (Brazil), Mar-Sep 2017",
           "assumptions": {"lab_delay_h": "ASSUMED 2 h after the bin closes; sensitivity at 1 h and 4 h",
                           "feed_grades": "treated as lab-type values with the same delay (conservative)",
                           "threshold": "upper band = training p75 of silica, illustrative, not a site specification"},
           "runs": []}
    for delay in (1, 2, 4):
        for h in (1, 3):
            r = run(hourly, delay, h, detail=(delay == 2))
            out["runs"].append({k: v for k, v in r.items() if k != "app"})
            t = r["test"]
            print(f"delay {delay}h horizon {h}h model {r['model']:14s} MAE {t['mae_model']:.3f} persist {t['mae_persistence']:.3f} "
                  f"mean {t['mae_mean']:.3f} R2 {t['r2_model']:.3f} vs {t['strongest_baseline']}: {t['verdict']} "
                  f"{[round(v, 3) for v in t['mae_diff_vs_strongest_ci95_block']]} cover {t['coverage']:.2f} {[round(v, 2) for v in t['coverage_ci95_block']]} width {t['width']:.2f}")
            if "app" in r:
                json.dump({"horizon_h": h, "delay_h": delay, "model": r["model"], "metrics": t, **r["app"]},
                          open(os.path.join(HERE, f"app_series_h{h}.json"), "w"))
    json.dump(out, open(os.path.join(HERE, "results.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
