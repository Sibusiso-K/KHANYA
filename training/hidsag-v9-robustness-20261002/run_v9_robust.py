"""REEFPRINT hyperspectral v9-robustness: v6 on GEOMET + unseen-capture variants scored by the fold model that never saw the parcel. Based on v6 — the ClauDex-approved plan (PLAN-live-v6.md, 3 rounds with Codex gpt-6-astra).

Data: HIDSAG (Ehrenfeld et al. 2023, Scientific Data), CC0, Figshare 10.6084/m9.figshare.c.5983921.
  GEOMET   146 drill-core samples -> flotation / grinding lab tests        (units = samples; no hole ids exist)
  MINERAL1  99 plant-feed fractions -> QEMSCAN wt% (36 composites P#S#)     (units = composites)

Per outer fold (GEOMET KFold(5, shuffle, 42) over sorted samples; MINERAL1 GroupKFold(5) by composite):
  1. outer-training is split FIRST into proper-training (~70% of units) and calibration (~30% of units)
  2. inside proper-training only: inner grouped CV chooses, per target, among
       nl_*   v5 nonlinear features (normalised spectra, slopes, spread, band depths, k-means fractions)
       lin_*  linear-in-reflectance (standardised mean reflectance; predictions are affine under areal mixing)
       linb_* lin + synthetic areal blends of inner-training pairs (additive targets only)
     k-means, scaling, PLS/ridge/ET fits and blend generation never see validation units
  3. the ONE model fitted on proper-training gives calibration scores, displayed predictions, interval centres and
     explanations; split-conformal 80% intervals, one score per unit (max over a composite's fractions), k =
     ceil((n_cal+1)*0.8), unbounded if k > n_cal
  4. a full outer-training refit (same chosen candidates) is scored separately as "accuracy evaluation"
  5. wavelength-region occlusion with the whole feature pipeline recomputed; brightness / cluster ablations separately
  6. spectral OOD: Ledoit-Wolf on proper-training PCA scores, p95/p99 bands set on calibration units, evaluated on
     outer-test units and on the other record (shifted domain)
  7. matched-modality RGB: a simulated colour camera rendered from the SAME pixel pools (Gaussian bands 460/540/620 nm,
     FWHM 100 nm), same folds, same nested selection
  8. blends of outer-test parents (sim_), parents resampled for uncertainty (done in the local analysis)
  9. pre-registered showcase samples (seeded hash order, written before modelling) export compact cubes + per-sensor
     band-depth and cluster maps
Gates against v5 / baselines and all coverage statistics are computed locally from the per-sample output.
"""
import gzip, hashlib, json, math, os, re, shutil, sys, time, traceback, urllib.request, zipfile
import numpy as np

OUT = "/kaggle/working" if os.path.isdir("/kaggle/working") else os.path.abspath("out_v6")
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
from sklearn.cluster import MiniBatchKMeans
from sklearn.covariance import LedoitWolf
from sklearn.cross_decomposition import PLSRegression
from sklearn.decomposition import PCA
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold, KFold
from sklearn.preprocessing import StandardScaler

URLS = {"GEOMET": "https://ndownloader.figshare.com/files/38652824",
        "MINERAL1": "https://ndownloader.figshare.com/files/38652803"}
RECORDS = ["GEOMET"]
ADDITIVE = {"MINERAL1"}
SEED = 7
POOL = 1500
ALPHA = 0.2
GV = np.arange(410.0, 991.0, 5.0)
GS = np.arange(1010.0, 2491.0, 10.0)
WINDOWS = [(1380, 1460), (1880, 1960), (2160, 2230), (2235, 2270), (2300, 2360), (2370, 2400)]
VWINDOW = (860, 960)
REGIONS = [("vnir", 410, 700), ("vnir", 700, 990), ("swir", 1010, 1350), ("swir", 1350, 2000), ("swir", 2000, 2250),
           ("swir", 2250, 2400), ("swir", 2400, 2490)]
REGION_NAMES = ["VNIR 410-700 nm (visible colour)", "VNIR 700-990 nm (Fe3+ / Fe2+ crystal field)", "SWIR 1010-1350 nm",
                "SWIR 1350-2000 nm (OH / H2O)", "SWIR 2000-2250 nm (Al-OH: sericite, kaolinite)",
                "SWIR 2250-2400 nm (Mg-OH / CO3: chlorite, biotite, talc, carbonate)", "SWIR 2400-2490 nm"]
MAPS = {"vnir_fe3": ("vnir", 900, 760, 985), "swir_h2o": ("swir", 1910, 1830, 2000), "swir_aloh": ("swir", 2205, 2120, 2280),
        "swir_mgoh": ("swir", 2330, 2280, 2385)}
N_SHOW = {"GEOMET": 24, "MINERAL1": 12}


# ------------------------------------------------------------------ extraction

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


def load_cube(zf, member):
    tmpdir = os.path.join(TMP, "x")
    shutil.rmtree(tmpdir, ignore_errors=True)
    p = zf.extract(member, tmpdir)
    with h5py.File(p, "r") as f:
        key = "hsi_data" if "hsi_data" in f else list(f.keys())[0]
        a = np.asarray(f[key], dtype=np.float32)
    shutil.rmtree(tmpdir, ignore_errors=True)
    if a.ndim != 3:
        return None
    h, w, _ = a.shape
    return a[int(h * 0.05):max(int(h * 0.95), 1), int(w * 0.05):max(int(w * 0.95), 1)]


def clean_pixels(cube):
    px = cube.reshape(-1, cube.shape[2])
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
                out.append(v[kind]["path_hsi"])
    return out


def show_order(rec, samples):
    key = lambda s: hashlib.sha256(f"reefprint-v6|{rec}|{s}".encode()).hexdigest()
    return sorted(samples, key=key)[:N_SHOW[rec]]


def process_record(name):
    zpath = download(name)
    zf = zipfile.ZipFile(zpath)
    names = zf.namelist()
    wl = None
    for n in names:
        if "wavelength" in n.lower() and n.lower().endswith(".json"):
            wl = json.loads(zf.read(n))
            break
    base = {"vnir_low": np.asarray(wl["wavelength_VNIR"], float), "swir_low": np.asarray(wl["wavelength_SWIR"], float)}
    grid = {"vnir_low": (GV, 5.0), "swir_low": (GS, 10.0)}
    metas = sorted(n for n in names if n.lower().endswith("metadata.json"))
    samples = [os.path.basename(os.path.dirname(m)) for m in metas]
    showcase = show_order(name, samples)
    json.dump({"record": name, "rule": "first N by sha256('reefprint-v6|<record>|<sample>'), written before modelling",
               "samples": showcase, "written_unix": time.time()}, open(os.path.join(OUT, f"preregistered_showcase_{name}.json"), "w"), indent=1)
    log(name, "pre-registered showcase", showcase)
    rows, mats, skipped = [], {}, 0
    for i, jn in enumerate(metas):
        folder = os.path.dirname(jn)
        sample = os.path.basename(folder)
        meta = json.loads(zf.read(jn).decode("utf-8", "replace"))
        y = {k: float(v) for k, v in (meta.get("vars") or {}).items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
        pools, cubes = {}, {}
        for kind in ("vnir_low", "swir_low"):
            pxs = []
            for j, path_hsi in enumerate(crop_paths(meta, kind)):
                member = folder + "/" + path_hsi
                if member not in zf.NameToInfo:
                    continue
                cube = load_cube(zf, member)
                if cube is None:
                    continue
                nb = cube.shape[2]
                key = (kind, nb)
                if key not in mats:
                    mats[key] = avg_matrix(native_wl(base[kind], nb), *grid[kind])
                g = (cube.reshape(-1, nb) @ mats[key]).reshape(cube.shape[0], cube.shape[1], -1)
                if j == 0 and sample in showcase:
                    cubes[kind] = g.astype(np.float32)
                px = clean_pixels(g)
                if px is not None:
                    pxs.append(px)
            if pxs:
                pools[kind] = np.concatenate(pxs)
        if len(pools) < 2 or not y:
            skipped += 1
            continue
        rng = np.random.default_rng(SEED + i)
        pv = pools["vnir_low"][rng.choice(len(pools["vnir_low"]), min(POOL, len(pools["vnir_low"])), replace=False)]
        ps = pools["swir_low"][rng.choice(len(pools["swir_low"]), min(POOL, len(pools["swir_low"])), replace=False)]
        rng2 = np.random.default_rng(SEED + 7919 + i)
        FV, FS = pools["vnir_low"], pools["swir_low"]
        pv2 = FV[rng2.choice(len(FV), min(POOL, len(FV)), replace=False)]
        ps2 = FS[rng2.choice(len(FS), min(POOL, len(FS)), replace=False)]
        HV, HS = FV[: max(len(FV) // 2, 10)], FS[: max(len(FS) // 2, 10)]
        pvh = HV[rng2.choice(len(HV), min(POOL, len(HV)), replace=False)]
        psh = HS[rng2.choice(len(HS), min(POOL, len(HS)), replace=False)]
        rows.append({"sample": sample, "y": y, "tags": " ".join(crop_tags(meta)), "pv": pv, "ps": ps, "cubes": {},
                     "variants": {"resample": (pv2, ps2), "half": (pvh, psh)}})
    zf.close()
    os.remove(zpath)
    log(name, "samples", len(rows), "skipped", skipped, "showcase cubes", sum(1 for r in rows if len(r["cubes"]) == 2))
    return rows


# ------------------------------------------------------------------ features

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
    """v5 nonlinear feature block (identical definition)."""
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
    out.append(np.array(depths + [pos, 1.0 - float(crv[sel].min()), float(pv.mean() / max(ps.mean(), 1e-9)),
                                  float(np.log(max(pv.mean(), 1.0))), float(np.log(max(ps.mean(), 1.0)))]))
    return np.concatenate(out).astype(np.float32)


def lin_feats(pv, ps):
    """Mean reflectance on the grid: the mean of a pooled areal mixture is the pixel-share-weighted mean of its parts."""
    return np.concatenate([pv.mean(0), ps.mean(0)]).astype(np.float32)


def rgb_pixels(pv):
    out = []
    for c in (460.0, 540.0, 620.0):
        g = np.exp(-0.5 * ((GV - c) / (100.0 / 2.355)) ** 2)
        out.append((pv * g).sum(1) / g.sum())
    return np.stack(out, 1)


def rgb_feats(pv):
    q = rgb_pixels(pv)
    m = q.mean(0)
    s = q.sum(1, keepdims=True)
    chrom = (q / np.maximum(s, 1e-9)).mean(0)
    return np.concatenate([m / m.mean(), q.std(0) / m.mean(), chrom, np.percentile(q, 10, 0) / m.mean(), np.percentile(q, 90, 0) / m.mean(),
                           [np.log(max(m.mean(), 1.0))]]).astype(np.float32)


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


# ------------------------------------------------------------------ candidate model families

NL_RIDGE, LIN_RIDGE, LINB_RIDGE = (10, 100), (1, 10, 100, 1000), (10, 100)


def candidate_names(additive):
    c = ["nl_et"] + [f"nl_ridge{a}" for a in NL_RIDGE] + ["nl_pls8"] + [f"lin_ridge{a}" for a in LIN_RIDGE] + ["lin_pls4", "lin_pls8"]
    if additive:
        c += [f"linb_ridge{a}" for a in LINB_RIDGE]
    return c


def _pls(X, z, nc):
    return PLSRegression(n_components=max(1, min(nc, X.shape[0] - 2, X.shape[1])), scale=False).fit(X, z)


class Family:
    """All candidates fitted on one training partition; standardisation and blends are fitted inside it."""

    def __init__(self, Xnl, Xlin, Y, additive, seed):
        T = Y.shape[1]
        self.ym, self.ys = Y.mean(0), np.where(Y.std(0) > 1e-12, Y.std(0), 1.0)
        Z = (Y - self.ym) / self.ys
        self.sn = StandardScaler().fit(Xnl)
        A = self.sn.transform(Xnl)
        self.m = {"nl_et": ExtraTreesRegressor(n_estimators=300, min_samples_leaf=2, max_features=0.3, random_state=0, n_jobs=-1).fit(A, Z)}
        for a in NL_RIDGE:
            self.m[f"nl_ridge{a}"] = Ridge(alpha=a).fit(A, Z)
        self.m["nl_pls8"] = [_pls(A, Z[:, t], 8) for t in range(T)]
        self.sl = StandardScaler().fit(Xlin)
        B = self.sl.transform(Xlin)
        for a in LIN_RIDGE:
            self.m[f"lin_ridge{a}"] = Ridge(alpha=a).fit(B, Z)
        for nc in (4, 8):
            self.m[f"lin_pls{nc}"] = [_pls(B, Z[:, t], nc) for t in range(T)]
        if additive:
            rng = np.random.default_rng(seed)
            n = len(Xlin)
            i = rng.integers(0, n, 3 * n)
            j = (i + 1 + rng.integers(0, n - 1, 3 * n)) % n
            p = rng.choice([0.3, 0.5, 0.7], 3 * n)[:, None]
            Bb = self.sl.transform(p * Xlin[i] + (1 - p) * Xlin[j])
            Zb = p * Z[i] + (1 - p) * Z[j]
            Ba, Za = np.vstack([B, Bb]), np.vstack([Z, Zb])
            for a in LINB_RIDGE:
                self.m[f"linb_ridge{a}"] = Ridge(alpha=a).fit(Ba, Za)

    def predict(self, Xnl, Xlin, only=None):
        A, B = self.sn.transform(Xnl), self.sl.transform(Xlin)
        out = {}
        for k, m in self.m.items():
            if only is not None and k not in only:
                continue
            X = A if k.startswith("nl_") else B
            if isinstance(m, list):
                z = np.column_stack([q.predict(X).ravel() for q in m])
            else:
                z = m.predict(X).reshape(len(X), -1)
            out[k] = z * self.ys + self.ym
        return out


class RGBFamily:
    def __init__(self, X, Y):
        self.ym, self.ys = Y.mean(0), np.where(Y.std(0) > 1e-12, Y.std(0), 1.0)
        Z = (Y - self.ym) / self.ys
        self.sc = StandardScaler().fit(X)
        A = self.sc.transform(X)
        self.m = {f"rgb_ridge{a}": Ridge(alpha=a).fit(A, Z) for a in (1, 10, 100)}
        self.m["rgb_et"] = ExtraTreesRegressor(n_estimators=300, min_samples_leaf=2, max_features=0.5, random_state=0, n_jobs=-1).fit(A, Z)

    def predict(self, X):
        A = self.sc.transform(X)
        return {k: m.predict(A).reshape(len(A), -1) * self.ys + self.ym for k, m in self.m.items()}


def inner_splits(idx, groups):
    if groups is not None:
        g = groups[idx]
        k = min(4, len(np.unique(g)))
        return [(idx[a], idx[b]) for a, b in GroupKFold(k).split(idx, groups=g)]
    return [(idx[a], idx[b]) for a, b in KFold(4, shuffle=True, random_state=1).split(idx)]


def choose(idx, groups, PV, PS, S_lin, Y, additive, rgbX=None):
    """Nested choice inside a partition. Returns per-target best HS candidate and best RGB candidate."""
    T = Y.shape[1]
    names = candidate_names(additive)
    pred = {c: np.full((len(Y), T), np.nan) for c in names}
    rpred = {}
    for a, b in inner_splits(idx, groups):
        kms = fit_kmeans(PV, PS, a)
        Xa = np.stack([np.concatenate([SPEC[i], hist_feats(kms, PV[i], PS[i])]) for i in a])
        Xb = np.stack([np.concatenate([SPEC[i], hist_feats(kms, PV[i], PS[i])]) for i in b])
        fam = Family(Xa, S_lin[a], Y[a], additive, SEED)
        for c, v in fam.predict(Xb, S_lin[b]).items():
            pred[c][b] = v
        if rgbX is not None:
            for c, v in RGBFamily(rgbX[a], Y[a]).predict(rgbX[b]).items():
                rpred.setdefault(c, np.full((len(Y), T), np.nan))[b] = v
    best, rbest = [], []
    for t in range(T):
        mae = {c: float(np.nanmean(np.abs(pred[c][idx, t] - Y[idx, t]))) for c in names}
        best.append(min(names, key=lambda c: (mae[c], names.index(c))))
        if rpred:
            rn = sorted(rpred)
            rm = {c: float(np.nanmean(np.abs(rpred[c][idx, t] - Y[idx, t]))) for c in rn}
            rbest.append(min(rn, key=lambda c: (rm[c], rn.index(c))))
    return best, rbest


def pick(pred_dict, best):
    T = len(best)
    return np.column_stack([pred_dict[best[t]][:, t] for t in range(T)])


def occlude(px, lo, hi, grid, mu):
    sel = (grid >= lo) & (grid <= hi)
    out = px.copy()
    scale = px[:, ~sel].mean(1, keepdims=True) / max(float(mu[~sel].mean()), 1e-9)
    out[:, sel] = mu[sel][None, :] * scale
    return out


def band_depth_map(cube, grid, c, l, r):
    def at(w):
        j = int(np.argmin(np.abs(grid - w)))
        lo, hi = max(0, j - 1), min(len(grid), j + 2)
        return cube[:, :, lo:hi].mean(2)
    Rc, Rl, Rr = at(c), at(l), at(r)
    cont = Rl + (Rr - Rl) * (c - l) / (r - l)
    return 1.0 - Rc / np.maximum(cont, 1e-9)


def downsample(cube, max_h=64, max_w=128):
    h, w, b = cube.shape
    f = int(math.ceil(max(h / max_h, w / max_w, 1)))
    if f == 1:
        return cube
    h2, w2 = h // f, w // f
    return cube[:h2 * f, :w2 * f].reshape(h2, f, w2, f, b).mean((1, 3))


def export_showcase(rec, r, fold, kms, preds, lo, hi, thr, ood_state, expl, keep, y_true):
    d = os.path.join(OUT, "showcase", rec)
    os.makedirs(d, exist_ok=True)
    blobs, header = [], {"record": rec, "sample": r["sample"], "fold": int(fold), "tags": r["tags"], "arrays": {}}
    off = 0

    def add(name, arr, dtype, scale=None):
        nonlocal off
        a = np.ascontiguousarray(arr.astype(dtype))
        header["arrays"][name] = {"offset": off, "shape": list(a.shape), "dtype": str(a.dtype), "scale": scale}
        blobs.append(a.tobytes())
        off += a.nbytes

    for kind, grid, step, km in (("vnir_low", GV, 2, kms[0]), ("swir_low", GS, 2, kms[1])):
        cube = r["cubes"].get(kind)
        if cube is None:
            continue
        cube = downsample(np.nan_to_num(cube, nan=0.0))
        sub = cube[:, :, ::step]
        mx = float(np.percentile(sub, 99.9)) or 1.0
        add(kind + "_cube", np.clip(sub / mx * 65535, 0, 65535), np.uint16, scale=mx / 65535)
        header[kind + "_wavelengths"] = grid[::step].tolist()
        br = cube.mean(2)
        add(kind + "_dark", br <= np.percentile(br, 5), np.uint8)
        flat = cube.reshape(-1, cube.shape[2])
        lab = km.predict(flat / np.maximum(flat.mean(1, keepdims=True), 1e-9)).reshape(cube.shape[:2])
        add(kind + "_clusters", lab, np.uint8)
        for mname, (sensor, c, l, rr) in MAPS.items():
            if (sensor == "vnir") != (kind == "vnir_low"):
                continue
            m = band_depth_map(cube, grid, c, l, rr)
            vmin, vmax = float(np.percentile(m, 1)), float(np.percentile(m, 99))
            q = np.clip((m - vmin) / max(vmax - vmin, 1e-9) * 255, 0, 255)
            add("map_" + mname, q, np.uint8, scale=[vmin, vmax])
    header["targets"] = {k: {"true": float(y_true[t]), "pred": float(preds[t]), "lo": float(lo[t]), "hi": float(hi[t]),
                              "t_low": float(thr[0][t]), "t_high": float(thr[1][t]), "explain": expl[t]} for t, k in enumerate(keep)}
    header["ood"] = ood_state
    open(os.path.join(d, r["sample"] + ".json"), "w").write(json.dumps(header))
    with gzip.open(os.path.join(d, r["sample"] + ".bin.gz"), "wb", compresslevel=6) as fh:
        for b in blobs:
            fh.write(b)


# ------------------------------------------------------------------ the experiment

SPEC = None


def group_of(rec, r):
    if rec == "MINERAL1":
        m = re.search(r"(P\d+).*?(S\d+)", r["tags"])
        return m.group(1) + m.group(2) if m else r["sample"]
    return r["sample"]


def model_record(rec, rows, shift_rows):
    global SPEC
    rows = sorted(rows, key=lambda r: r["sample"])
    keys = sorted({k for r in rows for k in r["y"]})
    keep = [k for k in keys if sum(k in r["y"] and np.isfinite(r["y"][k]) for r in rows) >= 0.9 * len(rows)]
    rows = [r for r in rows if all(k in r["y"] and np.isfinite(r["y"][k]) for k in keep)]
    Y = np.array([[r["y"][k] for k in keep] for r in rows], float)
    ok = Y.std(0) > 1e-9
    keep = [k for k, o in zip(keep, ok) if o]
    Y = Y[:, ok]
    n, T = Y.shape
    additive = rec in ADDITIVE
    units = np.array([group_of(rec, r) for r in rows])
    groups = units if rec == "MINERAL1" else None
    log(rec, "n", n, "targets", T, "units", len(np.unique(units)), "additive", additive)
    PV, PS = [r["pv"] for r in rows], [r["ps"] for r in rows]
    SPEC = [spec_feats(PV[i], PS[i]) for i in range(n)]
    S_lin = np.stack([lin_feats(PV[i], PS[i]) for i in range(n)])
    RGB = np.stack([rgb_feats(PV[i]) for i in range(n)])
    SH_SPEC = np.stack([spec_feats(r["pv"], r["ps"]) for r in shift_rows]) if shift_rows else None
    outer = list(GroupKFold(5).split(np.zeros(n), groups=units) if groups is not None else KFold(5, shuffle=True, random_state=42).split(np.zeros(n)))
    per = [dict() for _ in range(n)]
    fold_info, blends = [], []
    names = [r["sample"] for r in rows]
    showcase = set(json.load(open(os.path.join(OUT, f"preregistered_showcase_{rec}.json")))["samples"])
    for fo, (tr, te) in enumerate(outer):
        t0 = time.time()
        # 1. split outer-training into proper-training / calibration BEFORE any selection
        rng = np.random.default_rng(SEED + 1000 * fo)
        ut = np.unique(units[tr])
        perm = rng.permutation(ut)
        n_cal_units = max(1, int(round(0.3 * len(ut))))
        cal_units = set(perm[:n_cal_units].tolist())
        cal = np.array([i for i in tr if units[i] in cal_units])
        ptr = np.array([i for i in tr if units[i] not in cal_units])
        # 2. nested choice inside proper-training only
        best, rbest = choose(ptr, groups, PV, PS, S_lin, Y, additive, rgbX=RGB)
        # 3. the one deployable model
        kms = fit_kmeans(PV, PS, ptr)
        XN = np.stack([np.concatenate([SPEC[i], hist_feats(kms, PV[i], PS[i])]) for i in range(n)])
        fam = Family(XN[ptr], S_lin[ptr], Y[ptr], additive, SEED + fo)
        P = pick(fam.predict(XN, S_lin), best)
        # conformity: one score per calibration unit (max over the unit's members)
        cu = sorted(cal_units)
        scores = np.array([[np.max(np.abs(Y[units == u, t] - P[units == u, t])) for t in range(T)] for u in cu])
        n_cal = len(cu)
        k = int(math.ceil((n_cal + 1) * (1 - ALPHA)))
        q = np.sort(scores, 0)[k - 1] if k <= n_cal else np.full(T, np.inf)
        thr_lo, thr_hi = np.percentile(Y[ptr], 25, 0), np.percentile(Y[ptr], 75, 0)
        # baselines fitted on proper-training (deployable) and on full outer-training (evaluation)
        base_mean, base_median = Y[ptr].mean(0), np.median(Y[ptr], 0)
        meta_pred = None
        if rec == "MINERAL1":
            def meta_key(r):
                line = re.search(r"(P\d+)", r["tags"])
                frac = [t for t in r["tags"].split() if not re.match(r"^[PS]\d+$", t)]
                return ((line.group(1) if line else "?"), " ".join(frac))
            mk = [meta_key(r) for r in rows]
            meta_pred = np.zeros((n, T))
            for i in te:
                same = [j for j in ptr if mk[j] == mk[i]] or [j for j in ptr if mk[j][1] == mk[i][1]] or list(ptr)
                meta_pred[i] = np.median(Y[same], 0)
        # 4. accuracy evaluation: full outer-training refit with the same chosen candidates
        kms_f = fit_kmeans(PV, PS, tr)
        XF = np.stack([np.concatenate([SPEC[i], hist_feats(kms_f, PV[i], PS[i])]) for i in range(n)])
        famf = Family(XF[tr], S_lin[tr], Y[tr], additive, SEED + 50 + fo)
        PF = pick(famf.predict(XF[te], S_lin[te]), best)
        # matched-modality RGB (deployable, proper-training)
        rg = RGBFamily(RGB[ptr], Y[ptr]).predict(RGB[te])
        PR = np.column_stack([rg[rbest[t]][:, t] for t in range(T)])
        # 6. OOD on proper-training PCA scores; bands from calibration units; evaluated on outer-test
        S_arr = np.stack(SPEC)
        sc = StandardScaler().fit(S_arr[ptr])
        pca = PCA(n_components=min(10, len(ptr) - 1), random_state=0).fit(sc.transform(S_arr[ptr]))
        lw = LedoitWolf().fit(pca.transform(sc.transform(S_arr[ptr])))
        d2 = lambda Z: lw.mahalanobis(pca.transform(sc.transform(Z)))
        cal_d2 = d2(S_arr[cal])
        p95, p99 = float(np.percentile(cal_d2, 95)), float(np.percentile(cal_d2, 99))
        te_d2 = d2(S_arr[te])
        # v9: unseen-capture variants of each test parcel, scored by THIS fold's model (which never saw the parcel)
        rngv = np.random.default_rng(SEED + 31 * fo)

        def shift1(a):
            out = np.empty_like(a)
            out[:, 1:] = a[:, :-1]
            out[:, 0] = a[:, 0]
            return out

        def score(pv_, ps_):
            sf = spec_feats(pv_, ps_)
            xn = np.concatenate([sf, hist_feats(kms, pv_, ps_)])[None]
            p_ = pick(fam.predict(xn, lin_feats(pv_, ps_)[None], only=set(best)), best)[0]
            return [float(v) for v in p_], float(d2(sf[None])[0])

        VAR = {}
        for i in te:
            pv0, ps0 = PV[i], PS[i]
            vs = {"original": (pv0, ps0), "resample": rows[i]["variants"]["resample"], "half": rows[i]["variants"]["half"],
                  "gain_0.85": (pv0 * 0.85, ps0 * 0.85), "gain_1.15": (pv0 * 1.15, ps0 * 1.15),
                  "noise_2pct": (pv0 + rngv.normal(0, 0.02 * float(pv0.mean()), pv0.shape).astype(np.float32),
                                 ps0 + rngv.normal(0, 0.02 * float(ps0.mean()), ps0.shape).astype(np.float32)),
                  "shift_1band": (shift1(pv0), shift1(ps0))}
            VAR[i] = {k: dict(zip(("pred", "ood_d2"), score(*v))) for k, v in vs.items()}
        sh = None
        if SH_SPEC is not None:
            sd = d2(SH_SPEC)
            sh = {"n": int(len(sd)), "accepted_le_p99": float(np.mean(sd <= p99)), "pass_le_p95": float(np.mean(sd <= p95))}
        # 5. occlusion on the deployable model for outer-test units
        mu_v = np.concatenate([PV[i] for i in ptr]).mean(0)
        mu_s = np.concatenate([PS[i] for i in ptr]).mean(0)
        xn_mean = XN[ptr].mean(0)
        nspec = len(SPEC[0])
        for pos, i in enumerate(te):
            expl = []
            occl = []
            for (sensor, lo_, hi_) in REGIONS:
                pv2 = occlude(PV[i], lo_, hi_, GV, mu_v) if sensor == "vnir" else PV[i]
                ps2 = occlude(PS[i], lo_, hi_, GS, mu_s) if sensor == "swir" else PS[i]
                xn = np.concatenate([spec_feats(pv2, ps2), hist_feats(kms, pv2, ps2)])[None]
                occl.append(pick(fam.predict(xn, lin_feats(pv2, ps2)[None], only=set(best)), best)[0])
            occl = np.array(occl)
            xb = XN[i].copy()[None]
            xb[0, nspec - 2:nspec] = xn_mean[nspec - 2:nspec]
            ab_bright = pick(fam.predict(xb, S_lin[i][None], only=set(best)), best)[0]
            xc = XN[i].copy()[None]
            xc[0, nspec:] = xn_mean[nspec:]
            ab_clu = pick(fam.predict(xc, S_lin[i][None], only=set(best)), best)[0]
            for t in range(T):
                deltas = P[i, t] - occl[:, t]
                order = np.argsort(-np.abs(deltas))
                expl.append({"regions": [{"region": REGION_NAMES[j], "delta": float(deltas[j])} for j in order[:3]],
                             "ablation_brightness": float(P[i, t] - ab_bright[t]), "ablation_clusters": float(P[i, t] - ab_clu[t])})
            state = "pass" if te_d2[pos] <= p95 else ("borderline" if te_d2[pos] <= p99 else "refused")
            lo_i, hi_i = P[i] - q, P[i] + q
            per[i] = {"sample": names[i], "unit": str(units[i]), "fold": fo, "pred": P[i].tolist(), "lo": lo_i.tolist(), "hi": hi_i.tolist(),
                      "variants": VAR[i], "ood_p95": p95, "ood_p99": p99,
                      "full_refit": PF[pos].tolist(), "rgb": PR[pos].tolist(), "mean": base_mean.tolist(), "median": base_median.tolist(),
                      "meta": (meta_pred[i].tolist() if meta_pred is not None else None), "t_low": thr_lo.tolist(), "t_high": thr_hi.tolist(),
                      "ood_d2": float(te_d2[pos]), "ood": state, "explain": expl, "choice": best, "rgb_choice": rbest}
            if False:  # v9 exports no showcase cubes
                export_showcase(rec, rows[i], fo, kms, P[i], lo_i, hi_i, (thr_lo, thr_hi), state, expl, keep, Y[i])
        # 8. blends of outer-test parents (sim_)
        if additive and len(te) >= 4:
            rb = np.random.default_rng(SEED + 7 * fo)
            order = rb.permutation(te)
            for pid, (a, b) in enumerate(zip(order[0::2], order[1::2])):
                for p in (0.3, 0.5):
                    N = 600
                    na = int(round(p * N))
                    pv = np.concatenate([PV[a][rb.choice(len(PV[a]), min(na, len(PV[a])), replace=False)],
                                         PV[b][rb.choice(len(PV[b]), min(N - na, len(PV[b])), replace=False)]])
                    ps = np.concatenate([PS[a][rb.choice(len(PS[a]), min(na, len(PS[a])), replace=False)],
                                         PS[b][rb.choice(len(PS[b]), min(N - na, len(PS[b])), replace=False)]])
                    xn = np.concatenate([spec_feats(pv, ps), hist_feats(kms, pv, ps)])[None]
                    pb = pick(fam.predict(xn, lin_feats(pv, ps)[None], only=set(best)), best)[0]
                    blends.append({"fold": fo, "pair": f"{fo}-{pid}", "p": p, "a": names[a], "b": names[b],
                                   "true": (p * Y[a] + (1 - p) * Y[b]).tolist(), "pred": pb.tolist(), "mean": base_mean.tolist()})
        fold_info.append({"fold": fo, "n_train": int(len(tr)), "n_proper": int(len(ptr)), "n_cal_units": n_cal, "k": k,
                          "q": [None if not np.isfinite(v) else float(v) for v in q], "unbounded": bool(k > n_cal),
                          "ood_p95": p95, "ood_p99": p99, "ood_shift": sh, "choices": best, "rgb_choices": rbest,
                          "seconds": round(time.time() - t0)})
        log(f"{rec} fold {fo + 1}/{len(outer)}: proper {len(ptr)} cal_units {n_cal} k {k} unbounded {k > n_cal} "
            f"ood_shift_accept {None if sh is None else round(sh['accepted_le_p99'], 2)} {time.time() - t0:.0f}s")
    return {"targets": keep, "n": n, "n_units": int(len(np.unique(units))), "grouped": groups is not None, "alpha": ALPHA,
            "folds": fold_info, "samples": per, "blends": blends, "Y": Y.tolist()}


def main():
    t0 = time.time()
    data = {}
    for rec in RECORDS:
        try:
            data[rec] = process_record(rec)
        except Exception as e:
            log("FAILED extraction", rec, repr(e))
            log(traceback.format_exc())
    summary = {"dataset": "HIDSAG (CC0)", "version": "v9-robustness", "plan": "PLAN-live-v6.md (ClauDex, Codex gpt-6-astra, APPROVED round 3)",
               "grid_vnir_nm": GV.tolist(), "grid_swir_nm": GS.tolist(), "region_names": REGION_NAMES, "records": {}}
    for rec in RECORDS:
        if rec not in data:
            continue
        other = [r for k, v in data.items() if k != rec for r in v]
        try:
            summary["records"][rec] = model_record(rec, data[rec], other)
        except Exception as e:
            log("FAILED modelling", rec, repr(e))
            log(traceback.format_exc())
            summary["records"][rec] = {"error": repr(e)}
        json.dump(summary, open(os.path.join(OUT, "hidsag_v9_robust_results.json"), "w"))
    summary["elapsed_s"] = round(time.time() - t0)
    json.dump(summary, open(os.path.join(OUT, "hidsag_v9_robust_results.json"), "w"))
    log("done in", summary["elapsed_s"], "s")


if __name__ == "__main__":
    main()
