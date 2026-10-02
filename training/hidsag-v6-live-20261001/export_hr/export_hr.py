"""Full-resolution showcase export for REEFPRINT Live (display assets only; no modelling).

Re-extracts the SAME pre-registered showcase samples as v6 (first N by sha256('reefprint-v6|<record>|<sample>')) at full
HIDSAG low-product resolution (no 2x downsample), resampled onto the v6 wavelength grid, and stores each band as uint8
with its own min/max (display precision, about 0.4% of each band's range). Band-depth maps are computed on the full
grid before band thinning. Cluster maps are k-means on THIS scan's spectral shapes (display only), not the v6
training-fold clusters. Predictions, intervals and decisions are NOT recomputed: the app keeps v6's out-of-fold values.
Also copies HIDSAG's own RGB render of each scan for the belt view.
"""
import gzip, hashlib, json, os, shutil, time, urllib.request, zipfile
import numpy as np

OUT = "/kaggle/working" if os.path.isdir("/kaggle/working") else os.path.abspath("out_hr")
TMP = "/tmp/hidsag"
os.makedirs(OUT, exist_ok=True)
os.makedirs(TMP, exist_ok=True)
try:
    import h5py
except ImportError:
    os.system("pip install -q h5py")
    import h5py
from sklearn.cluster import MiniBatchKMeans

URLS = {"GEOMET": "https://ndownloader.figshare.com/files/38652824", "MINERAL1": "https://ndownloader.figshare.com/files/38652803"}
N_SHOW = {"GEOMET": 24, "MINERAL1": 12}
GV = np.arange(410.0, 991.0, 5.0)
GS = np.arange(1010.0, 2491.0, 10.0)
KEEP = {"vnir_low": (GV, 5.0, 3), "swir_low": (GS, 10.0, 2)}     # grid, step, keep every n-th band for display
MAPS = {"vnir_fe3": ("vnir_low", 900, 760, 985), "swir_h2o": ("swir_low", 1910, 1830, 2000),
        "swir_aloh": ("swir_low", 2205, 2120, 2280), "swir_mgoh": ("swir_low", 2330, 2280, 2385)}
MAX_W = 220


def log(*a):
    print(*a, flush=True)


def download(name):
    dst = os.path.join(TMP, name + ".zip")
    if os.path.exists(dst) and os.path.getsize(dst) > 1e8:
        return dst
    t0 = time.time()
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
    return base[:nb * k].reshape(nb, k).mean(1)


def band_depth(cube, grid, c, l, r):
    def at(w):
        j = int(np.argmin(np.abs(grid - w)))
        return cube[:, :, max(0, j - 1):min(len(grid), j + 2)].mean(2)
    Rc, Rl, Rr = at(c), at(l), at(r)
    return 1.0 - Rc / np.maximum(Rl + (Rr - Rl) * (c - l) / (r - l), 1e-9)


def main():
    for rec in ("GEOMET", "MINERAL1"):
        z = zipfile.ZipFile(download(rec))
        names = z.namelist()
        wl = json.loads(z.read(next(n for n in names if "wavelength" in n.lower() and n.endswith(".json"))))
        base = {"vnir_low": wl["wavelength_VNIR"], "swir_low": wl["wavelength_SWIR"]}
        metas = sorted(n for n in names if n.lower().endswith("metadata.json"))
        samples = {os.path.basename(os.path.dirname(m)): m for m in metas}
        show = sorted(samples, key=lambda s: hashlib.sha256(f"reefprint-v6|{rec}|{s}".encode()).hexdigest())[:N_SHOW[rec]]
        log(rec, "showcase", show)
        od = os.path.join(OUT, "showcase_hr", rec)
        os.makedirs(od, exist_ok=True)
        for s in show:
            folder = os.path.dirname(samples[s])
            meta = json.loads(z.read(samples[s]))
            crop = next(c for c in meta["crops"] if isinstance(c, dict))
            entry = next(v for k, v in sorted(crop.items()) if isinstance(v, dict) and "vnir_low" in v)
            header, blobs, off = {"record": rec, "sample": s, "arrays": {}, "encoding": "uint8 per band (band_min, band_max)",
                                  "clusters": "k-means on this scan's spectral shapes (display only)"}, [], 0

            def add(name, arr, extra):
                nonlocal off
                a = np.ascontiguousarray(arr.astype(np.uint8))
                header["arrays"][name] = {"offset": off, "shape": list(a.shape), "dtype": "uint8", **extra}
                blobs.append(a.tobytes())
                off += a.nbytes

            for kind, (grid, step, every) in KEEP.items():
                tmp = os.path.join(TMP, "x")
                shutil.rmtree(tmp, ignore_errors=True)
                p = z.extract(folder + "/" + entry[kind]["path_hsi"], tmp)
                with h5py.File(p, "r") as f:
                    key = "hsi_data" if "hsi_data" in f else list(f.keys())[0]
                    a = np.asarray(f[key], dtype=np.float32)
                shutil.rmtree(tmp, ignore_errors=True)
                h, w, nb = a.shape
                a = a[int(h * .05):max(int(h * .95), 1), int(w * .05):max(int(w * .95), 1)]
                a = np.nan_to_num(a, nan=0.0)
                g = (a.reshape(-1, nb) @ avg_matrix(native_wl(base[kind], nb), grid, step)).reshape(a.shape[0], a.shape[1], -1)
                if g.shape[1] > MAX_W:
                    f_ = int(np.ceil(g.shape[1] / MAX_W))
                    h2, w2 = g.shape[0] // f_, g.shape[1] // f_
                    g = g[:h2 * f_, :w2 * f_].reshape(h2, f_, w2, f_, -1).mean((1, 3))
                sub = g[:, :, ::every]
                bmin, bmax = np.percentile(sub, 0.5, axis=(0, 1)), np.percentile(sub, 99.5, axis=(0, 1))
                q = np.clip((sub - bmin) / np.maximum(bmax - bmin, 1e-6) * 255, 0, 255)
                add(kind + "_cube", np.round(q), {"band_min": bmin.round(3).tolist(), "band_max": bmax.round(3).tolist()})
                header[kind + "_wavelengths"] = grid[::every].tolist()
                br = g.mean(2)
                add(kind + "_dark", br <= np.percentile(br, 5), {})
                flat = g.reshape(-1, g.shape[2])
                shape_ = flat / np.maximum(flat.mean(1, keepdims=True), 1e-9)
                km = MiniBatchKMeans(n_clusters=8, random_state=0, n_init=3, batch_size=2048).fit(shape_[np.random.default_rng(0).choice(len(shape_), min(4000, len(shape_)), replace=False)])
                add(kind + "_clusters", km.predict(shape_).reshape(g.shape[:2]), {})
                for mname, (k2, c, l, r) in MAPS.items():
                    if k2 != kind:
                        continue
                    m = band_depth(g, grid, c, l, r)
                    vmin, vmax = float(np.percentile(m, 1)), float(np.percentile(m, 99))
                    add("map_" + mname, np.clip((m - vmin) / max(vmax - vmin, 1e-9) * 255, 0, 255), {"scale": [vmin, vmax]})
                if kind == "vnir_low" and entry[kind].get("path_rgb") and (folder + "/" + entry[kind]["path_rgb"]) in z.NameToInfo:
                    os.makedirs(os.path.join(OUT, "rgb_hr", rec), exist_ok=True)
                    open(os.path.join(OUT, "rgb_hr", rec, s + ".png"), "wb").write(z.read(folder + "/" + entry[kind]["path_rgb"]))
            open(os.path.join(od, s + ".json"), "w").write(json.dumps(header))
            with gzip.open(os.path.join(od, s + ".bin.gz"), "wb", compresslevel=9) as fh:
                for b in blobs:
                    fh.write(b)
            log(rec, s, {k: v["shape"] for k, v in header["arrays"].items() if k.endswith("_cube")}, round(os.path.getsize(os.path.join(od, s + ".bin.gz")) / 1e6, 2), "MB")
        z.close()
        os.remove(os.path.join(TMP, rec + ".zip"))
    log("done")


if __name__ == "__main__":
    main()
