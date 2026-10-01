"""Turn the Kaggle HIDSAG outputs into belt-monitor/data.json (+ copy RGB previews).

python build_data.py <kaggle_output_dir>
Only targets whose cross-validated model beats the trivial baseline (lower MAE) are shown as predictions;
the others are listed honestly in the model note.
"""
import json, os, random, shutil, sys
import numpy as np

SRC = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
res = json.load(open(os.path.join(SRC, "hidsag_results.json")))
geo = res["records"]["GEOMET"]["targets"]
short = {k: k.split(".")[-1] for k in geo}
WANT = ["Cu rec", "Mo rec", "Lime cons", "PH", "WI"]

spectra = {}
for line in open(os.path.join(SRC, "spectra_GEOMET.jsonl"), encoding="utf-8"):
    r = json.loads(line)
    spectra[r["sample"]] = r

wl_raw = json.load(open(os.path.join(SRC, "wavelengths.json")))
lens = {}
any_s = next(iter(spectra.values()))
for kind, m in zip(any_s["kinds"], any_s["mean"]):
    lens[kind] = len(m)


def flatten_lists(o, path=""):
    out = []
    if isinstance(o, dict):
        for k, v in o.items():
            out += flatten_lists(v, f"{path}{k}.")
    elif isinstance(o, list) and o and all(isinstance(x, (int, float)) for x in o):
        out.append((path[:-1], o))
    return out


cands = flatten_lists(wl_raw)
wavelengths = {}
for kind, n in lens.items():
    match = [(p, v) for p, v in cands if len(v) == n]
    if not match:  # spectrally binned cube (HIDSAG vnir_low uses spectral_binning 2): average consecutive centres
        for p, v in cands:
            for k in (2, 3, 4):
                if len(v) // k == n:
                    match.append((p + f"[bin{k}]", [sum(v[i * k:(i + 1) * k]) / k for i in range(n)]))
    pref = [m for m in match if kind in m[0].lower() and "low" in m[0].lower()] or [m for m in match if kind in m[0].lower()] or match
    if pref:
        wavelengths[kind] = [float(x) for x in pref[0][1]]
print("wavelength arrays:", {k: (len(v), v[0], v[-1]) for k, v in wavelengths.items()}, "candidates:", [(p, len(v)) for p, v in cands])

models, shown, hidden = {}, [], []
for k, r in geo.items():
    s = short[k]
    if s not in WANT:
        continue
    best = r["best_model"]
    trues = np.array([o["true"] for o in r["oof"]])
    preds = np.array([o["pred"] for o in r["oof"]])
    entry = {"r2": r[best]["r2"], "r2_ci": r[best]["r2_ci95"], "mae": r[best]["mae"], "baseline_mae": r["baseline"]["mae"],
             "n": r["n"], "model": best, "min": float(min(trues.min(), preds.min())), "max": float(max(trues.max(), preds.max())),
             "p25": float(np.percentile(trues, 25)), "p75": float(np.percentile(trues, 75))}
    models[s] = entry
    (shown if r["beats_baseline_mae"] else hidden).append(s)

per_sample = {}
for k, r in geo.items():
    s = short[k]
    if s not in shown:
        continue
    for o in r["oof"]:
        per_sample.setdefault(o["sample"], {})[s] = {"true": o["true"], "pred": o["pred"], "baseline": o["baseline"]}

rgb_src = os.path.join(SRC, "rgb", "GEOMET")
rgb_dst = os.path.join(HERE, "rgb")
os.makedirs(rgb_dst, exist_ok=True)
samples = []
for sid, t in per_sample.items():
    sp = spectra.get(sid)
    png = os.path.join(rgb_src, sid + ".png")
    if sp is None or not os.path.exists(png):
        continue
    shutil.copy(png, os.path.join(rgb_dst, sid + ".png"))
    samples.append({"sample": sid, "rgb": f"rgb/{sid}.png", "targets": t,
                    "spectra": [{"kind": kd, "mean": m} for kd, m in zip(sp["kinds"], sp["mean"]) if kd in wavelengths]})
random.Random(7).shuffle(samples)
samples = samples[:60]
ymax = max(max(max(s2["mean"]) for s2 in s["spectra"]) for s in samples)
mag = 10 ** np.floor(np.log10(ymax))
ymax = float(np.ceil(ymax / mag * 2) / 2 * mag)
nice = {"Cu rec": "Cu recovery", "Mo rec": "Mo recovery", "Lime cons": "lime consumption", "PH": "pH", "WI": "Bond work index"}
note = (f"PLS / ridge regression on VNIR + SWIR spectral statistics, {models[shown[0]]['n'] if shown else 0} HIDSAG drill-core samples, "
        f"5-fold cross-validation over samples (drill-hole IDs are not in the published metadata, so a by-hole split could not be enforced; scores may be optimistic). Shown: {', '.join(nice[s] for s in shown) or 'none'}. "
        + (f"Not better than the trivial baseline, so not shown: {', '.join(nice[s] for s in hidden)}." if hidden else ""))
data = {"order": [s for s in WANT if s in shown], "models": models, "samples": samples, "wavelengths": wavelengths, "ymax": ymax,
        "model_note": note,
        "footer": "Data: HIDSAG (Ehrenfeld et al., Scientific Data 2023), CC0, Figshare 10.6084/m9.figshare.c.5983921 — porphyry Cu-Mo drill core, "
                  "Chile; not PGM ore. Replay for demonstration; a site deployment needs its own calibration samples."}
json.dump(data, open(os.path.join(HERE, "data.json"), "w"), indent=0)
print("samples", len(samples), "shown", shown, "hidden", hidden)
for s in WANT:
    if s in models:
        m = models[s]
        print(f"{s:10s} R2={m['r2']:.3f} [{m['r2_ci'][0]:.2f},{m['r2_ci'][1]:.2f}] MAE={m['mae']:.3f} baseline={m['baseline_mae']:.3f} n={m['n']}")
