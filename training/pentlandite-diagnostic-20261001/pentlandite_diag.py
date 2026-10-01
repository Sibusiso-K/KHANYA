"""T2 exploratory diagnostic: how separable are pentlandite and pyrrhotite from colour and texture, once the sulphides
are found?  ("PGM-relevant base-metal-sulphide discrimination on Norilsk sections" — PLAN-live-v6.md §D)

Pentlandite is the main Pd carrier among Bushveld base-metal sulphides; pyrrhotite is the bright, similar-looking
sulphide it must be told apart from. REEFPRINT's physics thesis is that a rotating analyser separates them
(pentlandite isotropic, pyrrhotite anisotropic). This asks how far ordinary reflected-light colour and texture get.

Data: LumenStone S2 v2 (written research grant; images and derived weights are NOT shipped). Codes: 5 pyrrhotite,
7 pentlandite. Split: the audited protocol's 6 validation sections (train_06, 21, 13, 10, 23, 27) are the evaluation
set; the other 31 training sections train. The 12 test sections are never opened.
ORACLE: only pixels whose true class is pyrrhotite or pentlandite are classified (stage 1 assumed perfect), so these
numbers isolate the Pn/Po discrimination and are not comparable to full-segmentation IoU.
Models: colour-only vs colour + multi-scale texture, HistGradientBoosting, balanced pixel sampling. Baseline:
"all pyrrhotite" (pentlandite IoU 0) and a brightness-only classifier. n = 6 sections: exploratory, no gates claimed.
"""
import io, json, os, zipfile
import numpy as np
from PIL import Image
from scipy import ndimage
from sklearn.ensemble import HistGradientBoostingClassifier

HERE = os.path.dirname(os.path.abspath(__file__))
ZIP = os.path.join(HERE, "..", "..", "data", "lumenstone", "kaggle_s2_training_input", "S2_v2.zip")
VAL = ["train_06", "train_21", "train_13", "train_10", "train_23", "train_27"]
PO, PN = 5, 7
DS = 2
rng = np.random.default_rng(7)


def load(z, stem):
    img = Image.open(io.BytesIO(z.read(f"S2_v2/imgs/train/{stem}.jpg"))).convert("RGB")
    msk = Image.open(io.BytesIO(z.read(f"S2_v2/masks/train/{stem}.png")))
    w, h = img.size
    img = np.asarray(img.resize((w // DS, h // DS), Image.BILINEAR), np.float32)
    m = np.asarray(msk)[..., 0] if np.asarray(msk).ndim == 3 else np.asarray(msk)
    m = m[::DS, ::DS][: img.shape[0], : img.shape[1]]
    return img, m


def features(img):
    R, G, B = img[..., 0], img[..., 1], img[..., 2]
    Y = 0.299 * R + 0.587 * G + 0.114 * B
    s = R + G + B + 1e-3
    col = [R, G, B, Y, (R - G) / s, (G - B) / s, (R - B) / s]
    tex = []
    for k in (5, 15, 31):
        mu = ndimage.uniform_filter(Y, k)
        tex += [mu, np.sqrt(np.maximum(ndimage.uniform_filter(Y * Y, k) - mu * mu, 0)), ndimage.uniform_filter((R - G) / s, k), ndimage.uniform_filter((G - B) / s, k)]
    gm = np.hypot(ndimage.sobel(Y, 0), ndimage.sobel(Y, 1))
    tex += [gm, ndimage.uniform_filter(gm, 9)]
    return np.stack(col, -1), np.stack(col + tex, -1)


def main():
    z = zipfile.ZipFile(ZIP)
    stems = sorted({os.path.basename(n)[:-4] for n in z.namelist() if n.startswith("S2_v2/imgs/train/") and n.endswith(".jpg")})
    train = [s for s in stems if s not in VAL]
    assert len(train) == 31 and all(v in stems for v in VAL)
    Xc, Xf, y = [], [], []
    for s in train:
        img, m = load(z, s)
        fc, ff = features(img)
        for cls, lab in ((PO, 0), (PN, 1)):
            idx = np.flatnonzero(m.ravel() == cls)
            if len(idx) == 0:
                continue
            pick = rng.choice(idx, min(5000, len(idx)), replace=False)
            Xc.append(fc.reshape(-1, fc.shape[-1])[pick]); Xf.append(ff.reshape(-1, ff.shape[-1])[pick]); y.append(np.full(len(pick), lab))
        print("train", s, "Po", int((m == PO).sum()), "Pn", int((m == PN).sum()), flush=True)
    Xc, Xf, y = np.vstack(Xc), np.vstack(Xf), np.concatenate(y)
    models = {"brightness only": HistGradientBoostingClassifier(max_iter=200, random_state=0).fit(Xc[:, [3]], y),
              "colour only": HistGradientBoostingClassifier(max_iter=300, random_state=0).fit(Xc, y),
              "colour + texture": HistGradientBoostingClassifier(max_iter=400, max_depth=8, random_state=0).fit(Xf, y)}
    res = {"note": __doc__, "train_sections": len(train), "val_sections": VAL, "downsample": DS, "train_pixels": int(len(y)), "per_section": {}, "pooled": {}}
    pooled = {k: np.zeros(3) for k in models}            # tp, fp, fn for pentlandite
    for s in VAL:
        img, m = load(z, s)
        fc, ff = features(img)
        sel = (m == PO) | (m == PN)
        truth = (m[sel] == PN).astype(int)
        res["per_section"][s] = {"po_pixels": int((m == PO).sum()), "pn_pixels": int((m == PN).sum())}
        for k, mdl in models.items():
            X = (fc[sel][:, [3]] if k == "brightness only" else fc[sel] if k == "colour only" else ff[sel])
            p = mdl.predict(X)
            tp, fp, fn = int(((p == 1) & (truth == 1)).sum()), int(((p == 1) & (truth == 0)).sum()), int(((p == 0) & (truth == 1)).sum())
            pooled[k] += [tp, fp, fn]
            res["per_section"][s][k] = {"pn_iou": tp / max(tp + fp + fn, 1), "pn_precision": tp / max(tp + fp, 1), "pn_recall": tp / max(tp + fn, 1),
                                        "po_iou": int(((p == 0) & (truth == 0)).sum()) / max(int(((p == 0) | (truth == 0)).sum()), 1)}
        print(s, {k: round(v["pn_iou"], 3) for k, v in res["per_section"][s].items() if isinstance(v, dict)}, flush=True)
    for k, (tp, fp, fn) in pooled.items():
        res["pooled"][k] = {"pn_iou": tp / max(tp + fp + fn, 1), "pn_precision": tp / max(tp + fp, 1), "pn_recall": tp / max(tp + fn, 1)}
    res["pooled"]["all pyrrhotite (baseline)"] = {"pn_iou": 0.0, "pn_precision": float("nan"), "pn_recall": 0.0}
    json.dump(res, open(os.path.join(HERE, "results.json"), "w"), indent=1)
    for k, v in res["pooled"].items():
        print(f"POOLED {k:26s} pentlandite IoU {v['pn_iou']:.3f}  precision {v['pn_precision']:.3f}  recall {v['pn_recall']:.3f}")


if __name__ == "__main__":
    main()
