"""How cheap can the belt camera be? Simulate cheaper sensors from the HIDSAG hyperspectral means and re-score.

Each sensor is a set of Gaussian band responses applied to the measured per-sample mean spectrum:
  rgb        3 broad bands (460 / 540 / 620 nm, FWHM 100 nm)       — an ordinary colour camera
  led6       6 narrow VNIR bands (450-880 nm, FWHM 30 nm)            — mono camera + LED ring (REEFPRINT rig idea)
  vnir_hs    every VNIR band 400-1000 nm                              — silicon hyperspectral camera
  swir8      8 SWIR bands at diagnostic features (FWHM 30 nm)          — SWIR camera + filter wheel
  full_hs    every VNIR + SWIR band                                   — the HIDSAG instrument
Model: ridge or PLS chosen per target by inner CV (nested), features = band values / their mean + log brightness.
Folds: KFold(5) for GEOMET (no hole IDs), GroupKFold by composite for MINERAL1. CIs: bootstrap (cluster for MINERAL1).
This uses only mean spectra (no pixel spread), so "full_hs" here is weaker than v5 by construction; the comparison
between sensors is the point. Result: sensor_bands_results.json + printed table.
"""
import json, os, re
import numpy as np
from sklearn.cross_decomposition import PLSRegression
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import GroupKFold, KFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.join(HERE, "..", "hidsag-hyperspectral-20261001", "output")
V4 = os.path.join(HERE, "..", "hidsag-hyperspectral-20261001", "output_v4")
WL = json.load(open(os.path.join(V3, "wavelengths.json")))
SENSORS = {"rgb": [(460, 100), (540, 100), (620, 100)],
           "led6": [(450, 30), (520, 30), (590, 30), (660, 30), (760, 30), (880, 30)],
           "swir8": [(1300, 30), (1450, 30), (1650, 30), (1900, 30), (2165, 30), (2205, 30), (2260, 30), (2340, 30)]}
ORDER = ["rgb", "led6", "vnir_hs", "swir8", "full_hs"]


def wl_for(kind, n):
    base = np.asarray(WL["wavelength_VNIR"] if kind == "vnir" else WL["wavelength_SWIR"], float)
    k = len(base) // n
    return base[:n * k].reshape(n, k).mean(1)


def load(path, rec):
    rows = []
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        spec = {k: (wl_for(k, len(m)), np.asarray(m, float)) for k, m in zip(r["kinds"], r["mean"])}
        if "vnir" in spec and "swir" in spec:
            rows.append({"sample": r["sample"], "y": {k.split(".")[-1]: v for k, v in r["y"].items()}, "tags": r.get("tags", ""), "spec": spec})
    rows.sort(key=lambda r: r["sample"])
    return rows


def features(spec, sensor):
    if sensor == "vnir_hs":
        v = spec["vnir"][1]
        return np.concatenate([v / v.mean(), [np.log(v.mean())]])
    if sensor == "full_hs":
        v, s = spec["vnir"][1], spec["swir"][1]
        return np.concatenate([v / v.mean(), s / s.mean(), [np.log(v.mean()), np.log(s.mean())]])
    out = []
    for c, fw in SENSORS[sensor]:
        kind = "vnir" if c < 1000 else "swir"
        w, m = spec[kind]
        g = np.exp(-0.5 * ((w - c) / (fw / 2.355)) ** 2)
        out.append(float((g * m).sum() / g.sum()))
    out = np.asarray(out)
    return np.concatenate([out / out.mean(), [np.log(out.mean())]])


def candidates():
    c = {"ridge": lambda: make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-3, 4, 30)))}
    for nc in (2, 4, 8):
        c[f"pls{nc}"] = (lambda nc=nc: make_pipeline(StandardScaler(), PLSRegression(n_components=nc, scale=False)))
    return c


def nested_oof(X, y, groups):
    n = len(y)
    outer = list(GroupKFold(5).split(X, y, groups) if groups is not None else KFold(5, shuffle=True, random_state=42).split(X))
    pred = np.zeros(n)
    C = candidates()
    for tr, te in outer:
        gtr = groups[tr] if groups is not None else None
        inner = list(GroupKFold(4).split(tr, groups=gtr) if gtr is not None else KFold(4, shuffle=True, random_state=1).split(tr))
        score = {}
        for name, mk in C.items():
            if name.startswith("pls") and int(name[3:]) >= X.shape[1]:
                continue
            e = []
            for a, b in inner:
                m = mk().fit(X[tr[a]], y[tr[a]])
                e.append(np.abs(np.ravel(m.predict(X[tr[b]])) - y[tr[b]]).mean())
            score[name] = np.mean(e)
        best = min(sorted(score), key=lambda k: score[k])
        pred[te] = np.ravel(C[best]().fit(X[tr], y[tr]).predict(X[te]))
    return pred


def r2(y, p):
    return float(1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum())


def ci(y, p, groups, n=2000):
    rng = np.random.default_rng(0)
    g = groups if groups is not None else np.arange(len(y))
    ug = np.unique(g)
    idx = {k: np.flatnonzero(g == k) for k in ug}
    v = []
    for _ in range(n):
        b = np.concatenate([idx[ug[i]] for i in rng.integers(0, len(ug), len(ug))])
        v.append(r2(y[b], p[b]))
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]


def run(rec, rows, targets, grouped):
    groups = None
    if grouped:
        gl = []
        for r in rows:
            m = re.search(r"(P\d+).*?(S\d+)", r["tags"])
            gl.append(m.group(1) + m.group(2) if m else r["sample"])
        groups = np.array(gl)
    out = {}
    for t in targets:
        ok = [i for i, r in enumerate(rows) if t in r["y"]]
        y = np.array([rows[i]["y"][t] for i in ok], float)
        g = groups[ok] if groups is not None else None
        out[t] = {}
        for s in ORDER:
            X = np.stack([features(rows[i]["spec"], s) for i in ok])
            p = nested_oof(X, y, g)
            out[t][s] = {"r2": r2(y, p), "r2_ci95": ci(y, p, g), "n_bands": int(X.shape[1] - (2 if s == "full_hs" else 1))}
        print(f"{rec:8s} {t:22s} " + "  ".join(f"{s}={out[t][s]['r2']:+.2f}" for s in ORDER), flush=True)
    return out


geo = load(os.path.join(V3, "spectra_GEOMET.jsonl"), "GEOMET")
m1 = load(os.path.join(V4, "spectra_MINERAL1.jsonl"), "MINERAL1")
res = {"note": __doc__, "GEOMET": run("GEOMET", geo, ["Cu rec", "Mo rec", "Lime cons", "PH", "WI"], False),
       "MINERAL1": run("MINERAL1", m1, ["Chalcopyrite", "Pyrite", "Muscovite/Sericite", "Biotite", "Chlorite", "Kaolinite",
                                       "Quartz", "Anhydrite/Gypsum", "Calcite", "Molybdenite"], True)}
summary = {}
for rec in ("GEOMET", "MINERAL1"):
    for s in ORDER:
        kept = [res[rec][t][s]["r2"] / res[rec][t]["full_hs"]["r2"] for t in res[rec] if res[rec][t]["full_hs"]["r2"] > 0.2]
        summary[f"{rec}:{s}"] = {"median_share_of_full_hs_r2": float(np.median(kept)) if kept else None, "n_targets": len(kept)}
res["summary"] = summary
json.dump(res, open(os.path.join(HERE, "sensor_bands_results.json"), "w"), indent=1)
for k, v in summary.items():
    print(f"{k:22s} median share of full-hyperspectral R2: {v['median_share_of_full_hs_r2']}")
