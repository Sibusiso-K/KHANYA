"""REEFPRINT hyperspectral v5 — stronger spectral features, nested model choice, and a moving-belt simulation.

Data: HIDSAG (Ehrenfeld et al. 2023, Scientific Data), CC0 on Figshare 10.6084/m9.figshare.c.5983921.
  GEOMET   drill core -> flotation / grinding lab tests (Cu rec, Mo rec, pH, lime, Bond WI)
  MINERAL1 plant feed -> QEMSCAN modal mineralogy (grouped by composite P#S#)
  MINERAL2 QEMSCAN modal mineralogy
  GEOCHEM  mill-feed ore -> XRF chemistry (the most belt-like record)

What is new against v3/v4 (all of it scored out-of-fold, nothing tuned on a held-out score):
  * every pixel spectrum is resampled onto one fixed grid (VNIR 410-990 nm / 5 nm, SWIR 1010-2490 nm / 10 nm)
  * brightness-normalised mean spectra + first derivative + per-band spread (illumination-robust)
  * continuum-removed absorption depths at the diagnostic OH / H2O / Al-OH / Fe-OH / Mg-OH-CO3 / Fe3+ windows
  * "bag of spectra": k-means on pixel spectral shapes (fitted on the training fold only), per-sample cluster fractions
  * candidates PLS(4/8/12), ridge, extra-trees, and their average, CHOSEN PER TARGET BY INNER CV — this removes the
    "best of two picked on the same out-of-fold score" optimism disclosed in v3
  * v3-style PLS re-run inside the same folds as the reference; three gates before "better": paired (cluster)
    bootstrap CI of the MAE difference excluding zero, Mann-Whitney p < 0.05, and Cliff's delta reported
  * belt simulation on held-out samples (sim_): short dwell (25/100/400 pixels), brightness x0.85/x1.15, 2% noise,
    a combined belt case, and — for additive targets — blended ore from two unseen samples
"""
import json, os, re, shutil, sys, time, traceback, urllib.request, zipfile
import numpy as np

OUT = "/kaggle/working" if os.path.isdir("/kaggle/working") else os.path.abspath("out_v5")
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
from scipy.stats import mannwhitneyu
from sklearn.cluster import MiniBatchKMeans
from sklearn.cross_decomposition import PLSRegression
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import GridSearchCV, GroupKFold, KFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

URLS = {"GEOMET": "https://ndownloader.figshare.com/files/38652824",
        "MINERAL1": "https://ndownloader.figshare.com/files/38652803",
        "MINERAL2": "https://ndownloader.figshare.com/files/38652797",
        "GEOCHEM": "https://ndownloader.figshare.com/files/38652791"}
RECORDS = ["GEOMET", "MINERAL1", "MINERAL2", "GEOCHEM"]
ADDITIVE = {"MINERAL1", "MINERAL2", "GEOCHEM"}  # wt% / grade: a blend is (approximately) the mass-weighted mean
SEED = 7
POOL = 1500
GV = np.arange(410.0, 991.0, 5.0)
GS = np.arange(1010.0, 2491.0, 10.0)
WINDOWS = [(1380, 1460), (1880, 1960), (2160, 2230), (2235, 2270), (2300, 2360), (2370, 2400)]
VWINDOW = (860, 960)
CANDS = ["pls4", "pls8", "pls12", "ridge", "et", "avg"]
SCEN = ["dwell_25", "dwell_100", "dwell_400", "bright_085", "bright_115", "noise_2pct", "belt_combo"]


# ------------------------------------------------------------------ download + per-sample extraction

def download(name):
    dst = os.path.join(TMP, name + ".zip")
    if os.path.exists(dst) and os.path.getsize(dst) > 1e8:
        return dst
    t0 = time.time()
    log("downloading", name)
    with urllib.request.urlopen(URLS[name], timeout=900) as r, open(dst, "wb") as f:
        shutil.copyfileobj(r, f, length=16 * 1024 * 1024)
    log("downloaded", name, round(os.path.getsize(dst) / 1e9, 2), "GB in", round(time.time() - t0), "s")
    return dst


def avg_matrix(src, dst, step):
    src = np.asarray(src, float)
    M = np.zeros((len(src), len(dst)), np.float32)
    for j, c in enumerate(dst):
        m = np.abs(src - c) <= step / 2
        if not m.any():
            m[np.argmin(np.abs(src - c))] = True
        M[m, j] = 1.0 / m.sum()
    return M


def native_wl(base, nb):
    base = np.asarray(base, float)
    if nb == len(base):
        return base
    k = len(base) // nb
    if k >= 1 and nb * k <= len(base):
        return base[:nb * k].reshape(nb, k).mean(1)
    raise ValueError(f"cannot map {nb} bands onto {len(base)} wavelengths")


def load_pixels(zf, member):
    tmpdir = os.path.join(TMP, "x")
    shutil.rmtree(tmpdir, ignore_errors=True)
    p = zf.extract(member, tmpdir)
    with h5py.File(p, "r") as f:
        key = "hsi_data" if "hsi_data" in f else list(f.keys())[0]
        a = np.asarray(f[key], dtype=np.float32)
    shutil.rmtree(tmpdir, ignore_errors=True)
    if a.ndim != 3:
        return None
    h, w, b = a.shape
    a = a[int(h * 0.05):max(int(h * 0.95), 1), int(w * 0.05):max(int(w * 0.95), 1)]
    px = a.reshape(-1, b)
    px = px[np.isfinite(px).all(axis=1)]
    if len(px) < 10:
        return None
    br = px.mean(axis=1)
    return px[br > np.percentile(br, 5)]


def crop_tags(meta):
    return sorted({str(t) for c in (meta.get("crops") or []) if isinstance(c, dict) for t in (c.get("tags") or [])})


def crop_paths(meta, kind):
    out = []
    for c in meta.get("crops") or []:
        if not isinstance(c, dict):
            continue
        for k, v in sorted(c.items()):
            if isinstance(v, dict) and kind in v and isinstance(v[kind], dict) and v[kind].get("path_hsi"):
                out.append((v[kind]["path_hsi"], v[kind].get("path_rgb")))
    return out


def f0_feats(px):
    """v3-style statistics (mean, std, p10, p90, slope of mean), here on the common grid so lengths always agree."""
    m = px.mean(0)
    return np.concatenate([m, px.std(0), np.percentile(px, 10, axis=0), np.percentile(px, 90, axis=0), np.gradient(m)])


def continuum_removed(w, s):
    hull = []
    for p in zip(w, s):
        while len(hull) >= 2:
            (x1, y1), (x2, y2) = hull[-2], hull[-1]
            if (x2 - x1) * (p[1] - y1) - (y2 - y1) * (p[0] - x1) >= 0:
                hull.pop()
            else:
                break
        hull.append(p)
    hw, hs = zip(*hull)
    return s / np.maximum(np.interp(w, hw, hs), 1e-9)


def spec_feats(pv, ps):
    out = []
    for px in (pv, ps):
        m = px.mean(0)
        sc = max(float(m.mean()), 1e-9)
        mn = m / sc
        out += [mn, np.gradient(mn), px.std(0) / sc]
    crs = continuum_removed(GS, ps.mean(0))
    depths = []
    for a, b in WINDOWS:
        sel = (GS >= a) & (GS <= b)
        depths.append(1.0 - float(crs[sel].min()))
    sel = (GS >= 2150) & (GS <= 2250)
    pos = float(GS[sel][np.argmin(crs[sel])]) / 1000.0
    crv = continuum_removed(GV, pv.mean(0))
    sel = (GV >= VWINDOW[0]) & (GV <= VWINDOW[1])
    # absolute brightness kept as two log terms: a belt is calibrated against a white tile, so it is real signal,
    # but it enters only here, so a lighting drift moves two features instead of every feature
    out.append(np.array(depths + [pos, 1.0 - float(crv[sel].min()), float(pv.mean() / max(ps.mean(), 1e-9)),
                                  float(np.log(max(pv.mean(), 1.0))), float(np.log(max(ps.mean(), 1.0)))]))
    return np.concatenate(out).astype(np.float32)


def process_record(name):
    zpath = download(name)
    zf = zipfile.ZipFile(zpath)
    names = zf.namelist()
    wl = None
    for n in names:
        if "wavelength" in n.lower() and n.lower().endswith(".json"):
            wl = json.loads(zf.read(n))
            open(os.path.join(OUT, "wavelengths.json"), "wb").write(zf.read(n))
            break
    base_v, base_s = np.asarray(wl["wavelength_VNIR"], float), np.asarray(wl["wavelength_SWIR"], float)
    metas = sorted(n for n in names if n.lower().endswith("metadata.json"))
    log(name, "zip members", len(names), "metadata files", len(metas))
    rows, skipped, mats = [], 0, {}
    spec_out = open(os.path.join(OUT, f"spectra_v5_{name}.jsonl"), "w")
    for i, jn in enumerate(metas):
        folder = os.path.dirname(jn)
        meta = json.loads(zf.read(jn).decode("utf-8", "replace"))
        if i < 3:
            log("example", name, folder, "vars:", list((meta.get("vars") or {}).keys())[:40], "tags:", crop_tags(meta))
        y = {k: float(v) for k, v in (meta.get("vars") or {}).items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
        pools, rgb = {}, None
        for kind, base, grid, step in (("vnir_low", base_v, GV, 5.0), ("swir_low", base_s, GS, 10.0)):
            pxs = []
            for path_hsi, path_rgb in crop_paths(meta, kind):
                member = folder + "/" + path_hsi
                if member not in zf.NameToInfo:
                    continue
                px = load_pixels(zf, member)
                if px is None:
                    continue
                nb = px.shape[1]
                key = (kind, nb)
                if key not in mats:
                    mats[key] = avg_matrix(native_wl(base, nb), grid, step)
                pxs.append(px @ mats[key])
                if kind == "vnir_low" and rgb is None and path_rgb and (folder + "/" + path_rgb) in zf.NameToInfo:
                    rgb = folder + "/" + path_rgb
            if pxs:
                pools[kind] = np.concatenate(pxs)
        if len(pools) < 2 or not y:
            skipped += 1
            continue
        rng = np.random.default_rng(SEED + i)
        f0 = np.concatenate([f0_feats(pools["vnir_low"]), f0_feats(pools["swir_low"])]).astype(np.float32)
        pv = pools["vnir_low"][rng.choice(len(pools["vnir_low"]), min(POOL, len(pools["vnir_low"])), replace=False)]
        ps = pools["swir_low"][rng.choice(len(pools["swir_low"]), min(POOL, len(pools["swir_low"])), replace=False)]
        sample = os.path.basename(folder)
        tags = crop_tags(meta)
        rows.append({"sample": sample, "y": y, "tags": " ".join(tags), "f0": f0, "fs": spec_feats(pv, ps), "pv": pv, "ps": ps})
        spec_out.write(json.dumps({"sample": sample, "vnir": [round(float(v), 2) for v in pv.mean(0)],
                                   "swir": [round(float(v), 2) for v in ps.mean(0)], "y": y, "tags": tags}) + "\n")
        if rgb:
            d = os.path.join(OUT, "rgb", name)
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, sample + ".png"), "wb") as fh:
                fh.write(zf.read(rgb))
    spec_out.close()
    zf.close()
    os.remove(zpath)
    log(name, "samples with both sensors", len(rows), "skipped", skipped)
    return rows


# ------------------------------------------------------------------ models

def fit_kmeans(PV, PS, idx, k=12):
    rng = np.random.default_rng(SEED)
    kms = []
    for pools in (PV, PS):
        X = np.concatenate([pools[i][rng.choice(len(pools[i]), min(300, len(pools[i])), replace=False)] for i in idx])
        X = X / np.maximum(X.mean(1, keepdims=True), 1e-9)
        kms.append(MiniBatchKMeans(n_clusters=k, random_state=0, n_init=3, batch_size=2048).fit(X))
    return kms


def hist_feats(kms, pv, ps):
    out = []
    for km, px in zip(kms, (pv, ps)):
        lab = km.predict(px / np.maximum(px.mean(1, keepdims=True), 1e-9))
        out.append(np.bincount(lab, minlength=km.n_clusters) / len(lab))
    return np.concatenate(out).astype(np.float32)


class Fitted:
    def __init__(self, X, Y):
        T = Y.shape[1]
        self.ym, self.ys = Y.mean(0), np.where(Y.std(0) > 1e-12, Y.std(0), 1.0)
        Z = (Y - self.ym) / self.ys
        self.sc = StandardScaler().fit(X)
        Xs = self.sc.transform(X)
        self.pls = {}
        for nc in (4, 8, 12):
            c = max(1, min(nc, Xs.shape[0] - 2, Xs.shape[1]))
            self.pls[nc] = [PLSRegression(n_components=c, scale=False).fit(Xs, Z[:, t]) for t in range(T)]
        self.ridge = RidgeCV(alphas=np.logspace(-2, 4, 25), alpha_per_target=True).fit(Xs, Z)
        self.et = ExtraTreesRegressor(n_estimators=300, min_samples_leaf=2, max_features=0.3, random_state=0, n_jobs=-1).fit(Xs, Z)

    def predict(self, X):
        Xs = self.sc.transform(X)
        out = {f"pls{nc}": np.column_stack([m.predict(Xs).ravel() for m in ms]) for nc, ms in self.pls.items()}
        out["ridge"] = self.ridge.predict(Xs).reshape(len(Xs), -1)
        out["et"] = self.et.predict(Xs).reshape(len(Xs), -1)
        out["avg"] = (out["pls8"] + out["ridge"] + out["et"]) / 3
        return {k: v * self.ys + self.ym for k, v in out.items()}


def perturb(pv, ps, scen, rng):
    def sub(px, n):
        return px[rng.choice(len(px), min(n, len(px)), replace=False)]

    def noise(px, f):
        return px + rng.normal(0, 1, px.shape).astype(np.float32) * (f * px.mean(1, keepdims=True))

    if scen.startswith("dwell_"):
        n = int(scen.split("_")[1])
        return sub(pv, n), sub(ps, n)
    if scen.startswith("bright_"):
        f = int(scen.split("_")[1]) / 100.0
        return pv * f, ps * f
    if scen == "noise_2pct":
        return noise(pv, 0.02), noise(ps, 0.02)
    if scen == "belt_combo":
        a, b = sub(pv, 100) * 1.1, sub(ps, 100) * 1.1
        return noise(a, 0.02), noise(b, 0.02)
    raise ValueError(scen)


def r2(y, p):
    ss = ((y - y.mean()) ** 2).sum()
    return float(1 - ((y - p) ** 2).sum() / ss) if ss > 0 else float("nan")


def boot_ci(fn, y, p, groups, n=2000, seed=0):
    rng = np.random.default_rng(seed)
    g = groups if groups is not None else np.arange(len(y))
    ug = np.unique(g)
    idx = {k: np.flatnonzero(g == k) for k in ug}
    vals = []
    for _ in range(n):
        b = np.concatenate([idx[ug[i]] for i in rng.integers(0, len(ug), len(ug))])
        if np.var(y[b]) > 0:
            vals.append(fn(y[b], p[b]))
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def cliffs_delta(x, y):
    d = np.sign(x[:, None] - y[None, :])
    return float(d.mean())


def gates(y, p_new, p_old, groups):
    e1, e0 = np.abs(y - p_new), np.abs(y - p_old)
    rng = np.random.default_rng(1)
    g = groups if groups is not None else np.arange(len(y))
    ug = np.unique(g)
    idx = {k: np.flatnonzero(g == k) for k in ug}
    diffs = []
    for _ in range(2000):
        b = np.concatenate([idx[ug[i]] for i in rng.integers(0, len(ug), len(ug))])
        diffs.append(e1[b].mean() - e0[b].mean())
    ci = [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))]
    p_less = float(mannwhitneyu(e1, e0, alternative="less").pvalue)
    p_greater = float(mannwhitneyu(e1, e0, alternative="greater").pvalue)
    delta = cliffs_delta(e1, e0)
    if ci[1] < 0 and p_less < 0.05:
        verdict = "better"
    elif ci[0] > 0 and p_greater < 0.05:
        verdict = "worse"
    else:
        verdict = "no significant difference"
    return {"mae_diff": float(e1.mean() - e0.mean()), "mae_diff_ci95": ci, "mannwhitney_p_less": p_less,
            "mannwhitney_p_greater": p_greater, "cliffs_delta": delta, "verdict": verdict}


def group_of(rec, r):
    if rec in ("MINERAL1", "MINERAL2", "GEOCHEM"):
        m = re.search(r"(P\d+).*?(S\d+)", r["tags"])
        if m:
            return m.group(1) + m.group(2)
    return None


def model_record(rec, rows):
    rows = sorted(rows, key=lambda r: r["sample"])
    keys = sorted({k for r in rows for k in r["y"]})
    keep = [k for k in keys if sum(k in r["y"] and np.isfinite(r["y"][k]) for r in rows) >= 0.9 * len(rows)]
    rows = [r for r in rows if all(k in r["y"] and np.isfinite(r["y"][k]) for k in keep)]
    Y = np.array([[r["y"][k] for k in keep] for r in rows], float)
    ok = Y.std(0) > 1e-9
    keep = [k for k, o in zip(keep, ok) if o]
    Y = Y[:, ok]
    n, T = Y.shape
    gl = [group_of(rec, r) for r in rows]
    groups = np.array(gl) if all(gl) and len(set(gl)) < 0.9 * n else None
    log(rec, "n", n, "targets", T, "groups", (len(set(gl)) if groups is not None else "none (one per sample)"))
    if n < 20 or T == 0:
        return {"n": n, "error": "too few samples or targets"}
    X0 = np.stack([r["f0"] for r in rows])
    S = np.stack([r["fs"] for r in rows])
    PV, PS = [r["pv"] for r in rows], [r["ps"] for r in rows]
    nsp = min(5, len(np.unique(groups))) if groups is not None else 5
    outer = list(GroupKFold(nsp).split(X0, Y, groups) if groups is not None else KFold(5, shuffle=True, random_state=42).split(X0))
    P = {c: np.full((n, T), np.nan) for c in ("v3pls", "chosen", "mean", "v3pls_bright115")}
    SIM = {sc: np.full((n, T), np.nan) for sc in SCEN}
    choice = [[] for _ in range(T)]
    blends = []
    for fo, (tr, te) in enumerate(outer):
        t0 = time.time()
        kms = fit_kmeans(PV, PS, tr)
        H = np.stack([hist_feats(kms, PV[i], PS[i]) for i in range(n)])
        XN = np.hstack([S, H])
        for t in range(T):
            gs = GridSearchCV(make_pipeline(StandardScaler(), PLSRegression(scale=False)),
                              {"plsregression__n_components": [2, 4, 6, 8, 10, 12]}, cv=4, scoring="neg_mean_absolute_error")
            gs.fit(X0[tr], Y[tr, t])
            P["v3pls"][te, t] = gs.predict(X0[te]).ravel()
            P["v3pls_bright115"][te, t] = gs.predict(X0[te] * 1.15).ravel()
        P["mean"][te] = Y[tr].mean(0)
        gtr = groups[tr] if groups is not None else None
        ni = min(4, len(np.unique(gtr))) if gtr is not None else 4
        inner = list(GroupKFold(ni).split(tr, groups=gtr) if gtr is not None else KFold(4, shuffle=True, random_state=1).split(tr))
        cp = {c: np.full((len(tr), T), np.nan) for c in CANDS}
        for itr, iva in inner:
            pr = Fitted(XN[tr[itr]], Y[tr[itr]]).predict(XN[tr[iva]])
            for c in CANDS:
                cp[c][iva] = pr[c]
        imae = {c: np.abs(cp[c] - Y[tr]).mean(0) for c in CANDS}
        best = [min(CANDS, key=lambda c: (imae[c][t], CANDS.index(c))) for t in range(T)]
        fit = Fitted(XN[tr], Y[tr])
        pr = fit.predict(XN[te])
        for t in range(T):
            P["chosen"][te, t] = pr[best[t]][:, t]
            choice[t].append(best[t])
        rng = np.random.default_rng(SEED + 100 * fo)
        for sc in SCEN:
            Xs = []
            for i in te:
                pv, ps = perturb(PV[i], PS[i], sc, rng)
                Xs.append(np.concatenate([spec_feats(pv, ps), hist_feats(kms, pv, ps)]))
            prs = fit.predict(np.stack(Xs))
            for t in range(T):
                SIM[sc][te, t] = prs[best[t]][:, t]
        if rec in ADDITIVE and len(te) >= 4:
            order = rng.permutation(te)
            for a, b in zip(order[0::2], order[1::2]):
                for p in (0.3, 0.5):
                    N = 600
                    na = int(round(p * N))
                    pv = np.concatenate([PV[a][rng.choice(len(PV[a]), min(na, len(PV[a])), replace=False)],
                                         PV[b][rng.choice(len(PV[b]), min(N - na, len(PV[b])), replace=False)]])
                    ps = np.concatenate([PS[a][rng.choice(len(PS[a]), min(na, len(PS[a])), replace=False)],
                                         PS[b][rng.choice(len(PS[b]), min(N - na, len(PS[b])), replace=False)]])
                    prb = fit.predict(np.concatenate([spec_feats(pv, ps), hist_feats(kms, pv, ps)])[None])
                    yb = p * Y[a] + (1 - p) * Y[b]
                    blends.append((yb, np.array([prb[best[t]][0, t] for t in range(T)]), Y[tr].mean(0)))
        log(f"{rec} fold {fo + 1}/{len(outer)} done in {time.time() - t0:.0f}s")
    names = [r["sample"] for r in rows]
    res = {"n": n, "n_groups": int(len(np.unique(groups))) if groups is not None else None, "folds": len(outer), "targets": {}}
    for t, k in enumerate(keep):
        y = Y[:, t]
        ent = {"v3pls": {"r2": r2(y, P["v3pls"][:, t]), "mae": float(np.abs(y - P["v3pls"][:, t]).mean())},
               "chosen": {"r2": r2(y, P["chosen"][:, t]), "mae": float(np.abs(y - P["chosen"][:, t]).mean()),
                          "r2_ci95": boot_ci(r2, y, P["chosen"][:, t], groups)},
               "mean_baseline_mae": float(np.abs(y - P["mean"][:, t]).mean()),
               "choices": {c: choice[t].count(c) for c in CANDS if choice[t].count(c)},
               "vs_v3pls": gates(y, P["chosen"][:, t], P["v3pls"][:, t], groups),
               "vs_mean": gates(y, P["chosen"][:, t], P["mean"][:, t], groups),
               "sim_belt": {sc: {"r2": r2(y, SIM[sc][:, t]), "mae": float(np.abs(y - SIM[sc][:, t]).mean())} for sc in SCEN},
               "sim_v3pls_bright115": {"r2": r2(y, P["v3pls_bright115"][:, t]), "mae": float(np.abs(y - P["v3pls_bright115"][:, t]).mean())},
               "oof": [{"sample": s, "true": float(a), "pred": float(b), "v3pls": float(c), "mean": float(d)}
                       for s, a, b, c, d in zip(names, y, P["chosen"][:, t], P["v3pls"][:, t], P["mean"][:, t])]}
        if blends:
            yb = np.array([b[0][t] for b in blends])
            pb = np.array([b[1][t] for b in blends])
            mb = np.array([b[2][t] for b in blends])
            ent["sim_blend"] = {"n_blends": len(blends), "r2": r2(yb, pb), "mae": float(np.abs(yb - pb).mean()),
                                "mean_baseline_mae": float(np.abs(yb - mb).mean())}
        res["targets"][k] = ent
        g = ent["vs_v3pls"]
        log(f"{rec} {k:24s} v3pls R2={ent['v3pls']['r2']:.3f}  v5 R2={ent['chosen']['r2']:.3f} "
            f"[{ent['chosen']['r2_ci95'][0]:.2f},{ent['chosen']['r2_ci95'][1]:.2f}]  vs v3: {g['verdict']} "
            f"(dMAE {g['mae_diff']:+.3g}, delta {g['cliffs_delta']:+.2f})  belt_combo R2={ent['sim_belt']['belt_combo']['r2']:.3f}  "
            f"v3 bright115 R2={ent['sim_v3pls_bright115']['r2']:.3f}")
    return res


def main():
    t0 = time.time()
    summary = {"dataset": "HIDSAG (CC0, Figshare 10.6084/m9.figshare.c.5983921)", "version": "v5",
               "grid_vnir_nm": GV.tolist(), "grid_swir_nm": GS.tolist(), "records": {}}
    which = sys.argv[1:] or RECORDS
    for rec in which:
        try:
            rows = process_record(rec)
            summary["records"][rec] = model_record(rec, rows)
        except Exception as e:
            log("FAILED", rec, repr(e))
            log(traceback.format_exc())
            summary["records"][rec] = {"error": repr(e)}
        json.dump(summary, open(os.path.join(OUT, "hidsag_v5_results.json"), "w"), indent=1)
    summary["elapsed_s"] = round(time.time() - t0)
    json.dump(summary, open(os.path.join(OUT, "hidsag_v5_results.json"), "w"), indent=1)
    log("done in", summary["elapsed_s"], "s")


if __name__ == "__main__":
    main()
