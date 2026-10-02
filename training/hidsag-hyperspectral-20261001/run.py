"""REEFPRINT hyperspectral track: can belt-style hyperspectral images predict lab results before grinding?

Data: HIDSAG (Ehrenfeld et al. 2023, Scientific Data, CC0 on Figshare 10.6084/m9.figshare.c.5983921.v1).
  GEOMET   146 drill-core samples -> Cu recovery, Mo recovery, pH, lime consumption, Bond work index (WI)
  MINERAL1 94 plant-feed samples   -> QEMSCAN modal mineralogy (wt%)
Method: per-sample spectral statistics (VNIR + SWIR) -> PLS / ridge regression, scored out-of-fold against the
trivial baseline (training mean). MINERAL1 folds are grouped by monthly composite so size fractions of the same
composite never straddle train and test (REEFPRINT rule 2). Nothing is tuned on a held-out score.
"""
import glob, json, os, re, shutil, sys, time, urllib.request, zipfile
import numpy as np

OUT = "/kaggle/working" if os.path.isdir("/kaggle/working") else os.path.abspath("out")
TMP = "/tmp/hidsag"
os.makedirs(OUT, exist_ok=True)
os.makedirs(TMP, exist_ok=True)
LOG = open(os.path.join(OUT, "log.txt"), "a")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + "\n")
    LOG.flush()


try:
    import h5py
except ImportError:
    os.system("pip install -q h5py")
    import h5py
from sklearn.cross_decomposition import PLSRegression
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold, GroupKFold, GridSearchCV
from sklearn.metrics import r2_score, mean_absolute_error

URLS = {"GEOMET": "https://ndownloader.figshare.com/files/38652824",
        "MINERAL1": "https://ndownloader.figshare.com/files/38652803"}
SKIP_KEYS = re.compile(r"(width|height|dims|crop|measure|path|file|kind|id$|^id|index|resolution|band|wavelength)", re.I)


def download(name):
    dst = os.path.join(TMP, name + ".zip")
    if os.path.exists(dst) and os.path.getsize(dst) > 1e8:
        return dst
    t0 = time.time()
    log("downloading", name)
    with urllib.request.urlopen(URLS[name], timeout=600) as r, open(dst, "wb") as f:
        shutil.copyfileobj(r, f, length=16 * 1024 * 1024)
    log("downloaded", name, round(os.path.getsize(dst) / 1e9, 2), "GB in", round(time.time() - t0), "s")
    return dst


def numeric_leaves(d, prefix=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(numeric_leaves(v, f"{prefix}{k}."))
    elif isinstance(d, (int, float)) and not isinstance(d, bool):
        out[prefix[:-1]] = float(d)
    return out


LAST_MEAN = []
# v4 re-runs MINERAL1 only (grouping fix). GEOMET is ungrouped by design and its v3 results stand.
RECORDS = ["MINERAL1"]


def cube_features(path):
    with h5py.File(path, "r") as f:
        key = "hsi_data" if "hsi_data" in f else list(f.keys())[0]
        a = np.asarray(f[key], dtype=np.float32)
    if a.ndim != 3:
        return None
    h, w, b = a.shape
    a = a[int(h * 0.05):int(h * 0.95) or h, int(w * 0.05):int(w * 0.95) or w]  # trim container edges
    px = a.reshape(-1, b)
    px = px[np.isfinite(px).all(axis=1)]
    bright = px.mean(axis=1)
    px = px[bright > np.percentile(bright, 5)]  # drop the darkest 5% (shadow, gaps)
    mean = px.mean(axis=0)
    LAST_MEAN.append(mean.tolist())
    feats = np.concatenate([mean, px.std(axis=0), np.percentile(px, 10, axis=0), np.percentile(px, 90, axis=0),
                            np.gradient(mean)])
    return feats


def process_record(name):
    zpath = download(name)
    zf = zipfile.ZipFile(zpath)
    names = zf.namelist()
    jsons = [n for n in names if n.lower().endswith(".json") and "wavelength" not in n.lower()]
    for n in names:
        if "wavelength" in n.lower() and n.lower().endswith(".json"):
            open(os.path.join(OUT, "wavelengths.json"), "wb").write(zf.read(n))
            break
    log(name, "zip members", len(names), "json", len(jsons))
    rows = []
    shown = False
    for jn in sorted(jsons):
        folder = os.path.dirname(jn)
        try:
            meta = json.loads(zf.read(jn).decode("utf-8", "replace"))
        except Exception as e:
            log("bad json", jn, e)
            continue
        if not shown:
            log("example json", jn, json.dumps(meta)[:1500])
            shown = True
        h5s = [n for n in names if n.startswith(folder + "/") and n.lower().endswith(".h5")]
        pick = {}
        for n in h5s:
            low = os.path.basename(n).lower()
            if "swir" in low and "low" in low:
                pick.setdefault("swir", n)
            elif "vnir" in low and "low" in low:
                pick.setdefault("vnir", n)
        if "swir" not in pick and h5s:
            pick["swir"] = h5s[0]
        feats = []
        LAST_MEAN.clear()
        ok = True
        for kind in ("vnir", "swir"):
            if kind not in pick:
                continue
            tmpdir = os.path.join(TMP, "x")
            shutil.rmtree(tmpdir, ignore_errors=True)
            p = zf.extract(pick[kind], tmpdir)
            f = cube_features(p)
            shutil.rmtree(tmpdir, ignore_errors=True)
            if f is None:
                ok = False
                break
            feats.append(f)
        if not ok or not feats:
            continue
        pngs = [n for n in names if n.startswith(folder + "/") and n.lower().endswith(".png")]
        if pngs:
            dst = os.path.join(OUT, "rgb", name)
            os.makedirs(dst, exist_ok=True)
            with open(os.path.join(dst, os.path.basename(folder) + ".png"), "wb") as fh:
                fh.write(zf.read(pngs[0]))
        y = {k: v for k, v in numeric_leaves(meta).items() if not SKIP_KEYS.search(k.split(".")[-1])}
        # v4: HIDSAG keeps tags inside crops[] (e.g. ["P1", "S1", "coarse"]); v3 read a top-level key that does not exist,
        # so every MINERAL1 sample became its own group and size fractions of one composite could straddle folds.
        ctags = sorted({str(t) for c in (meta.get("crops") or []) if isinstance(c, dict) for t in (c.get("tags") or [])})
        tags = " ".join(ctags) if ctags else str(meta.get("tags") or "")
        rows.append({"sample": folder, "x": np.concatenate(feats), "y": y, "tags": str(tags)})
        spec_out = os.path.join(OUT, "spectra_" + name + ".jsonl")
        with open(spec_out, "a") as fh:
            fh.write(json.dumps({"sample": os.path.basename(folder), "kinds": [k for k in ("vnir", "swir") if k in pick],
                                 "mean": [[round(v, 5) for v in m] for m in LAST_MEAN], "y": y, "tags": str(tags)}) + "\n")
    zf.close()
    os.remove(zpath)
    log(name, "samples with features", len(rows))
    return rows


def bootstrap_ci(y, p, fn, n=2000, seed=0):
    rng = np.random.default_rng(seed)
    idx = np.arange(len(y))
    vals = []
    for _ in range(n):
        b = rng.choice(idx, len(idx), replace=True)
        if np.var(y[b]) > 0:
            vals.append(fn(y[b], p[b]))
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def evaluate(rows, record, group_fn=None, min_n=15):
    keys = sorted({k for r in rows for k in r["y"]})
    X_all = np.stack([r["x"] for r in rows])
    results = {}
    for k in keys:
        mask = np.array([k in r["y"] for r in rows])
        y = np.array([r["y"].get(k, np.nan) for r in rows], dtype=float)
        mask &= np.isfinite(y)
        if mask.sum() < min_n or np.std(y[mask]) < 1e-9:
            continue
        X, yy = X_all[mask], y[mask]
        groups = np.array([group_fn(r) for r, m in zip(rows, mask) if m]) if group_fn else None
        n_splits = min(5, len(np.unique(groups))) if groups is not None else 5
        cv = GroupKFold(n_splits=n_splits) if groups is not None else KFold(5, shuffle=True, random_state=42)
        split = list(cv.split(X, yy, groups) if groups is not None else cv.split(X, yy))
        oof = {"baseline": np.zeros_like(yy), "pls": np.zeros_like(yy), "ridge": np.zeros_like(yy)}
        for tr, te in split:
            oof["baseline"][te] = yy[tr].mean()
            pls = GridSearchCV(make_pipeline(StandardScaler(), PLSRegression(scale=False)),
                               {"plsregression__n_components": [2, 4, 6, 8, 10, 12]}, cv=4, scoring="neg_mean_absolute_error")
            pls.fit(X[tr], yy[tr])
            oof["pls"][te] = pls.predict(X[te]).ravel()
            rid = make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-2, 4, 25)))
            rid.fit(X[tr], yy[tr])
            oof["ridge"][te] = rid.predict(X[te])
        res = {"n": int(len(yy)), "folds": len(split), "grouped": groups is not None,
               "n_groups": int(len(np.unique(groups))) if groups is not None else None,
               "y_mean": float(yy.mean()), "y_std": float(yy.std())}
        for m, p in oof.items():
            res[m] = {"r2": float(r2_score(yy, p)), "mae": float(mean_absolute_error(yy, p)),
                      "r2_ci95": bootstrap_ci(yy, p, r2_score), "mae_ci95": bootstrap_ci(yy, p, mean_absolute_error)}
        best = max(("pls", "ridge"), key=lambda m: res[m]["r2"])
        samples = [r["sample"] for r, m in zip(rows, mask) if m]
        res["oof"] = [{"sample": os.path.basename(sm), "true": float(t), "pred": float(pp), "baseline": float(bb)}
                      for sm, t, pp, bb in zip(samples, yy, oof[best], oof["baseline"])]
        res["best_model"] = best
        res["beats_baseline_mae"] = bool(res[best]["mae"] < res["baseline"]["mae"])
        results[k] = res
        log(f"{record} {k:40s} n={res['n']:3d}  best={best:5s} R2={res[best]['r2']:.3f} "
            f"[{res[best]['r2_ci95'][0]:.2f},{res[best]['r2_ci95'][1]:.2f}]  MAE={res[best]['mae']:.3f} vs baseline {res['baseline']['mae']:.3f}")
    return results


def main():
    t0 = time.time()
    summary = {"dataset": "HIDSAG (CC0, Figshare 10.6084/m9.figshare.c.5983921.v1)", "started_unix": t0, "records": {}}
    which = sys.argv[1:] or RECORDS
    for rec in which:
        try:
            rows = process_record(rec)
            if rec == "MINERAL1":
                def grp(r):
                    m = re.search(r"(P\d).*?(S\d+)", r["tags"] + " " + r["sample"])
                    return m.group(1) + m.group(2) if m else r["sample"]
                gs = [grp(r) for r in rows]
                log("MINERAL1 groups", len(set(gs)), "from", len(gs), "samples:", sorted(set(gs))[:20])
                if len(set(gs)) >= len(gs) * 0.9:
                    raise RuntimeError("grouping failed: nearly one group per sample")
                res = evaluate(rows, rec, group_fn=grp)
            else:
                res = evaluate(rows, rec)
            summary["records"][rec] = {"n_samples": len(rows), "targets": res}
        except Exception as e:
            import traceback
            log("FAILED", rec, repr(e))
            log(traceback.format_exc())
            summary["records"][rec] = {"error": repr(e)}
        json.dump(summary, open(os.path.join(OUT, "hidsag_results.json"), "w"), indent=1)
    summary["elapsed_s"] = round(time.time() - t0)
    json.dump(summary, open(os.path.join(OUT, "hidsag_results.json"), "w"), indent=1)
    log("done in", summary["elapsed_s"], "s")


if __name__ == "__main__":
    main()
