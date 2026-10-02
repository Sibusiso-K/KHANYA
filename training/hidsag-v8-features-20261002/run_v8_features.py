"""REEFPRINT v8 features: continuum-removed absorption features per HIDSAG sample (GEOMET, MINERAL1). Data only; no modelling.

Prospectively specified in SPEC.md (committed before this run; MINERAL1 has been seen in v5/v6/Q2, so this is a
reanalysis, not untouched confirmation). Feature extraction follows the practice reviewed by Laukamp et al. 2021
(Minerals 11, 347): continuum removal by an upper convex hull, then within a fixed window the band minimum, refined by a
2nd-order polynomial through the minimum and its two neighbours (position), and relative depth 1 - CR(min).

Per sample, ALL crops pooled (as v6). Two masks, frozen here:
  mask_v6   finite pixels, then the darkest 5% by mean brightness removed (v6 clean_pixels rule)
  mask_none finite pixels only (sensitivity)
Two aggregations: PRIMARY = features of the pooled MEAN spectrum per sensor; SECONDARY = median of per-pixel features on
up to 3000 pixels. Pixel-area averages are not mass fractions; that limitation is stated, not fixed.
Also logs every record's identity (sample folder, crop tags, crop count, pixel counts) for the 99-vs-94 reconciliation.
"""
import json, os, shutil, time, urllib.request, zipfile
import numpy as np

OUT = "/kaggle/working" if os.path.isdir("/kaggle/working") else os.path.abspath("out_v8f")
TMP = "/tmp/hidsag"
os.makedirs(OUT, exist_ok=True)
os.makedirs(TMP, exist_ok=True)
try:
    import h5py
except ImportError:
    os.system("pip install -q h5py")
    import h5py

URLS = {"GEOMET": "https://ndownloader.figshare.com/files/38652824", "MINERAL1": "https://ndownloader.figshare.com/files/38652803"}
GV = np.arange(410.0, 991.0, 5.0)
GS = np.arange(1010.0, 2491.0, 10.0)
FEATURES = {  # name: (sensor, window_lo_nm, window_hi_nm)
    "aloh_2200": ("swir", 2150, 2240),
    "feoh_2250": ("swir", 2235, 2275),
    "mgoh_2330": ("swir", 2290, 2360),
    "h2o_1750_gypsum": ("swir", 1730, 1785),
    "h2o_1900": ("swir", 1880, 1960),
    "fe3_900": ("vnir", 850, 960),
}
SEED = 11
MAXPIX = 3000


def log(*a):
    print(*a, flush=True)


def download(name):
    dst = os.path.join(TMP, name + ".zip")
    if os.path.exists(dst) and os.path.getsize(dst) > 1e8:
        return dst
    with urllib.request.urlopen(URLS[name], timeout=900) as r, open(dst, "wb") as f:
        shutil.copyfileobj(r, f, length=16 * 1024 * 1024)
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
    return base[:nb * k].reshape(nb, k).mean(1)


def hull_cr(w, s):
    """Continuum removal by the upper convex hull (same construction as v6 continuum_removed)."""
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


def feature(w, cr, lo, hi):
    sel = np.flatnonzero((w >= lo) & (w <= hi))
    j = sel[np.argmin(cr[sel])]
    depth = float(1.0 - cr[j])
    pos = float(w[j])
    if 0 < j < len(w) - 1:  # 2nd-order polynomial through the minimum and its neighbours
        x, y = w[j - 1:j + 2], cr[j - 1:j + 2]
        a, b, _ = np.polyfit(x - w[j], y, 2)
        if a > 0:
            off = -b / (2 * a)
            if abs(off) <= (w[j + 1] - w[j]):
                pos = float(w[j] + off)
    return depth, pos


def feats_of_spectrum(sv, ss):
    out = {}
    crv, crs = hull_cr(GV, sv), hull_cr(GS, ss)
    for name, (sensor, lo, hi) in FEATURES.items():
        d, p = feature(GV if sensor == "vnir" else GS, crv if sensor == "vnir" else crs, lo, hi)
        out[name + "_depth"], out[name + "_pos"] = d, p
    return out


def main():
    t0 = time.time()
    res = {"spec": "SPEC.md", "features": FEATURES, "records": {}}
    for rec in ("GEOMET", "MINERAL1"):
        z = zipfile.ZipFile(download(rec))
        names = z.namelist()
        wl = json.loads(z.read(next(n for n in names if "wavelength" in n.lower() and n.lower().endswith(".json"))))
        base = {"vnir_low": wl["wavelength_VNIR"], "swir_low": wl["wavelength_SWIR"]}
        metas = sorted(n for n in names if n.lower().endswith("metadata.json"))
        mats, rows = {}, []
        for jn in metas:
            folder = os.path.dirname(jn)
            meta = json.loads(z.read(jn).decode("utf-8", "replace"))
            crops = [c for c in (meta.get("crops") or []) if isinstance(c, dict)]
            ident = {"sample": os.path.basename(folder), "n_crops": len(crops),
                     "crop_tags": [sorted(str(t) for t in (c.get("tags") or [])) for c in crops],
                     "vars": {k: v for k, v in (meta.get("vars") or {}).items() if isinstance(v, (int, float)) and not isinstance(v, bool)}}
            pools = {}
            for kind, grid, step in (("vnir_low", GV, 5.0), ("swir_low", GS, 10.0)):
                px_all = []
                for c in crops:
                    for k, v in sorted(c.items()):
                        if not (isinstance(v, dict) and kind in v and isinstance(v[kind], dict) and v[kind].get("path_hsi")):
                            continue
                        member = folder + "/" + v[kind]["path_hsi"]
                        if member not in z.NameToInfo:
                            continue
                        tmp = os.path.join(TMP, "x")
                        shutil.rmtree(tmp, ignore_errors=True)
                        pth = z.extract(member, tmp)
                        with h5py.File(pth, "r") as f:
                            key = "hsi_data" if "hsi_data" in f else list(f.keys())[0]
                            a = np.asarray(f[key], dtype=np.float32)
                        shutil.rmtree(tmp, ignore_errors=True)
                        if a.ndim != 3:
                            continue
                        h, w_, nb = a.shape
                        a = a[int(h * .05):max(int(h * .95), 1), int(w_ * .05):max(int(w_ * .95), 1)]
                        if (kind, nb) not in mats:
                            mats[(kind, nb)] = avg_matrix(native_wl(base[kind], nb), grid, step)
                        g = a.reshape(-1, nb) @ mats[(kind, nb)]
                        px_all.append(g[np.isfinite(g).all(1)])
                if px_all:
                    pools[kind] = np.concatenate(px_all)
            if len(pools) < 2:
                ident["skipped"] = "missing a sensor"
                rows.append(ident)
                continue
            rng = np.random.default_rng(SEED)
            for mask in ("mask_v6", "mask_none"):
                sv_pool, ss_pool = pools["vnir_low"], pools["swir_low"]
                if mask == "mask_v6":
                    sv_pool = sv_pool[sv_pool.mean(1) > np.percentile(sv_pool.mean(1), 5)]
                    ss_pool = ss_pool[ss_pool.mean(1) > np.percentile(ss_pool.mean(1), 5)]
                ident[mask] = {"n_px_vnir": int(len(sv_pool)), "n_px_swir": int(len(ss_pool)),
                               "primary_mean_spectrum": feats_of_spectrum(sv_pool.mean(0), ss_pool.mean(0))}
                iv = rng.choice(len(sv_pool), min(MAXPIX, len(sv_pool)), replace=False)
                is_ = rng.choice(len(ss_pool), min(MAXPIX, len(ss_pool)), replace=False)
                n = min(len(iv), len(is_))   # sensors are not co-registered: pair pixels only to reuse the function
                per = [feats_of_spectrum(sv_pool[iv[i]], ss_pool[is_[i]]) for i in range(n)]
                ident[mask]["secondary_median_pixel"] = {k: float(np.median([p[k] for p in per])) for k in per[0]}
            rows.append(ident)
        z.close()
        os.remove(os.path.join(TMP, rec + ".zip"))
        res["records"][rec] = rows
        log(rec, "samples", len(rows), "skipped", sum(1 for r in rows if "skipped" in r), round(time.time() - t0), "s")
        json.dump(res, open(os.path.join(OUT, "hidsag_v8_features.json"), "w"))
    res["elapsed_s"] = round(time.time() - t0)
    json.dump(res, open(os.path.join(OUT, "hidsag_v8_features.json"), "w"))
    log("done", res["elapsed_s"])


if __name__ == "__main__":
    main()
