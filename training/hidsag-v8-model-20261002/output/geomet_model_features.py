# Feature code exported verbatim from run_v8_model.py (v6 definitions)
import numpy as np
GV = np.arange(410.0, 991.0, 5.0)
GS = np.arange(1010.0, 2491.0, 10.0)
WINDOWS = [(1380, 1460), (1880, 1960), (2160, 2230), (2235, 2270), (2300, 2360), (2370, 2400)]
VWINDOW = (860, 960)

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


def hist_feats(kms, pv, ps):
    out = []
    for km, px in zip(kms, (pv, ps)):
        lab = km.predict(px / np.maximum(px.mean(1, keepdims=True), 1e-9))
        out.append(np.bincount(lab, minlength=km.n_clusters) / len(lab))
    return np.concatenate(out).astype(np.float32)
