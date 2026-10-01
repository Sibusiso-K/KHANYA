"""MINERAL1 Q2: does the spectrum add anything once process line and size fraction are known?

v6 analysis found the metadata-only baseline (median wt% for the same process line + size fraction) matches the
hyperspectral model (rule 3). This tests the nested question directly, the same shape as the falsification test:
    M0  metadata lookup (training median of the same line + fraction)
    M1  ridge on one-hot(line, fraction)                         -> metadata model
    M2  ridge on one-hot(line, fraction) + mean VNIR+SWIR spectrum -> metadata + spectrum
Outer GroupKFold(5) by composite; alpha chosen by grouped inner CV on the training composites only.
Gates (paired, composite level): cluster-bootstrap CI of the MAE difference, Wilcoxon (Holm across minerals),
Mann-Whitney + Cliff's delta (doctrine). Spectra: v5 per-sample mean spectra on the common grid (spectra_v5_MINERAL1).
"""
import json, os, re
import numpy as np
from scipy.stats import mannwhitneyu, wilcoxon
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

HERE = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(os.path.join(HERE, "..", "hidsag-v5-belt-20261001", "output", "spectra_v5_MINERAL1.jsonl"), encoding="utf-8")]
rows.sort(key=lambda r: r["sample"])
tags = [r["tags"] for r in rows]
line = [next((t for t in tg if re.match(r"^P\d+$", t)), "?") for tg in tags]
frac = [" ".join(t for t in tg if not re.match(r"^[PS]\d+$", t)) for tg in tags]
comp = np.array([next((t for t in tg if re.match(r"^P\d+$", t)), "?") + next((t for t in tg if re.match(r"^S\d+$", t)), "?") for tg in tags])
print("fractions:", sorted(set(frac)), "lines:", sorted(set(line)), "composites:", len(set(comp)))
keys = sorted({k for r in rows for k in r["y"]})
Y = np.array([[r["y"].get(k, np.nan) for k in keys] for r in rows], float)
okc = np.isfinite(Y).all(0) & (np.nanstd(Y, 0) > 1e-9)
keys = [k for k, o in zip(keys, okc) if o]
Y = Y[:, okc]
levels = sorted(set(zip(line, frac)))
L = np.array([[1.0 if (line[i], frac[i]) == lv else 0.0 for lv in levels] + [1.0 if line[i] == l else 0.0 for l in sorted(set(line))]
              + [1.0 if frac[i] == f else 0.0 for f in sorted(set(frac))] for i in range(len(rows))])
S = np.array([np.concatenate([r["vnir"], r["swir"]]) for r in rows], float)
n, T = Y.shape
ALPHAS = (0.1, 1, 10, 100, 1000)


def fit_pred(Xtr, ytr, Xte, gtr):
    best, bs = None, np.inf
    for a in ALPHAS:
        e = []
        for i, j in GroupKFold(4).split(Xtr, groups=gtr):
            sc = StandardScaler().fit(Xtr[i])
            m = Ridge(alpha=a).fit(sc.transform(Xtr[i]), ytr[i])
            e.append(np.abs(m.predict(sc.transform(Xtr[j])) - ytr[j]).mean())
        if np.mean(e) < bs:
            best, bs = a, np.mean(e)
    sc = StandardScaler().fit(Xtr)
    return Ridge(alpha=best).fit(sc.transform(Xtr), ytr).predict(sc.transform(Xte))


P0, P1, P2 = np.zeros((n, T)), np.zeros((n, T)), np.zeros((n, T))
for tr, te in GroupKFold(5).split(S, groups=comp):
    for i in te:
        same = [j for j in tr if (line[j], frac[j]) == (line[i], frac[i])] or [j for j in tr if frac[j] == frac[i]] or list(tr)
        P0[i] = np.median(Y[same], 0)
    for t in range(T):
        P1[te, t] = fit_pred(L[tr], Y[tr, t], L[te], comp[tr])
        P2[te, t] = fit_pred(np.hstack([L, S])[tr], Y[tr, t], np.hstack([L, S])[te], comp[tr])


def gate(y, a, b):
    e1, e0 = np.abs(y - a), np.abs(y - b)
    ug = np.unique(comp)
    idx = {u: np.flatnonzero(comp == u) for u in ug}
    rng = np.random.default_rng(1)
    v = [np.mean(e1[np.concatenate([idx[ug[i]] for i in rng.integers(0, len(ug), len(ug))])]) -
         np.mean(e0[np.concatenate([idx[ug[i]] for i in rng.integers(0, len(ug), len(ug))])]) for _ in range(1)]
    boots = []
    for _ in range(3000):
        b_ = np.concatenate([idx[ug[i]] for i in rng.integers(0, len(ug), len(ug))])
        boots.append(e1[b_].mean() - e0[b_].mean())
    d = np.array([e1[idx[u]].mean() - e0[idx[u]].mean() for u in ug])
    nz = d[d != 0]
    wp = float(wilcoxon(nz, alternative="less").pvalue) if len(nz) else 1.0
    return {"mae_new": float(e1.mean()), "mae_base": float(e0.mean()), "ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
            "wilcoxon_less": wp, "mannwhitney_less": float(mannwhitneyu(e1, e0, alternative="less").pvalue),
            "cliffs_delta": float(np.sign(e1[:, None] - e0[None, :]).mean())}


def holm(ps):
    ps = np.asarray(ps)
    o = np.argsort(ps)
    adj = np.empty_like(ps)
    run = 0.0
    for r, i in enumerate(o):
        run = max(run, (len(ps) - r) * ps[i])
        adj[i] = min(1.0, run)
    return adj


r2 = lambda y, p: float(1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum())
res = {}
for t, k in enumerate(keys):
    y = Y[:, t]
    best_meta = min((("lookup", P0[:, t]), ("ridge_meta", P1[:, t])), key=lambda kv: np.abs(y - kv[1]).mean())
    res[k] = {"r2_lookup": r2(y, P0[:, t]), "r2_meta_ridge": r2(y, P1[:, t]), "r2_meta_plus_spectrum": r2(y, P2[:, t]),
              "strongest_metadata_model": best_meta[0], "gate": gate(y, P2[:, t], best_meta[1])}
adj = holm([v["gate"]["wilcoxon_less"] for v in res.values()])
for (k, v), a in zip(res.items(), adj):
    g = v["gate"]
    g["wilcoxon_less_holm"] = float(a)
    g["verdict"] = "better" if (g["ci95"][1] < 0 and a < 0.05 and g["mannwhitney_less"] < 0.05) else (
        "worse" if g["ci95"][0] > 0 else "no significant difference")
json.dump({"note": __doc__, "n": n, "composites": int(len(set(comp))), "targets": res}, open(os.path.join(HERE, "mineral1_q2.json"), "w"), indent=1)
nb = sum(v["gate"]["verdict"] == "better" for v in res.values())
nw = sum(v["gate"]["verdict"] == "worse" for v in res.values())
print(f"spectrum adds over metadata: better {nb}, worse {nw}, of {len(res)}")
for k, v in sorted(res.items(), key=lambda kv: kv[1]["gate"]["ci95"][1]):
    g = v["gate"]
    print(f"  {k:22s} R2 lookup {v['r2_lookup']:.3f} meta {v['r2_meta_ridge']:.3f} meta+spec {v['r2_meta_plus_spectrum']:.3f} | "
          f"dMAE CI [{g['ci95'][0]:+.3f},{g['ci95'][1]:+.3f}] wilcoxon(holm) {g['wilcoxon_less_holm']:.3g} MW {g['mannwhitney_less']:.3g} -> {g['verdict']}")
