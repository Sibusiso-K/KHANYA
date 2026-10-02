"""Build belt-monitor/data.json (+ copy RGB previews) from the Kaggle HIDSAG outputs.

python build_data.py --v3 <v3 output dir> [--v4 <v4 output dir>] [--v5 <v5 output dir>]

v3  : spectra for display (spectra_GEOMET.jsonl, wavelengths.json), RGB previews, and — without v5 — the GEOMET models.
v4  : MINERAL1 grouped results (mineral1_grouped_ci.json) for the feed-mineralogy view.
v5  : when present, GEOMET predictions come from v5's nested-CV choice, the feed-mineralogy view lists every v5 record,
      and the belt-robustness view is filled from the moving-belt simulation.
A target is shown on the belt only if its out-of-fold model beats the training-mean baseline.
"""
import argparse, json, os, random, shutil
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--v3", required=True)
ap.add_argument("--v4")
ap.add_argument("--v5")
A = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
WANT = ["Cu rec", "Mo rec", "Lime cons", "PH", "WI"]
NICE = {"Cu rec": "Cu recovery", "Mo rec": "Mo recovery", "Lime cons": "lime consumption", "PH": "pH", "WI": "Bond work index"}
SULPHIDES = {"Chalcopyrite", "Bornite", "Chalcosite/Digenite", "Covelite", "Pyrite", "Molybdenite"}
PRETTY = {"Anhydrite/Gypsum": "Anhydrite / gypsum", "Muscovite/Sericite": "Sericite (muscovite)", "Chalcosite/Digenite": "Chalcocite / digenite",
          "Covelite": "Covellite", "Bytownite_An80": "Bytownite", "Labradorite_An60": "Labradorite", "Andesina_An40": "Andesine",
          "Oligoclasa_An20": "Oligoclase", "Others Ti Minerals": "Other Ti minerals"}

# ---------------- spectra + wavelengths for display (v3, full resolution)
spectra = {}
for line in open(os.path.join(A.v3, "spectra_GEOMET.jsonl"), encoding="utf-8"):
    r = json.loads(line)
    spectra[r["sample"]] = r
wl_raw = json.load(open(os.path.join(A.v3, "wavelengths.json")))
first = next(iter(spectra.values()))
lens = {k: len(m) for k, m in zip(first["kinds"], first["mean"])}
wavelengths = {}
for kind, n in lens.items():
    base = wl_raw["wavelength_VNIR"] if kind == "vnir" else wl_raw["wavelength_SWIR"]
    k = len(base) // n
    wavelengths[kind] = [float(np.mean(base[i * k:(i + 1) * k])) for i in range(n)]

# ---------------- GEOMET models + per-sample predictions
models, per_sample, shown, hidden = {}, {}, [], []
if A.v5:
    V5 = json.load(open(os.path.join(A.v5, "hidsag_v5_results.json")))
    geo = V5["records"]["GEOMET"]["targets"]
    for k in WANT:
        if k not in geo:
            continue
        r = geo[k]
        trues = np.array([o["true"] for o in r["oof"]])
        preds = np.array([o["pred"] for o in r["oof"]])
        beats = r["vs_mean"]["verdict"] == "better"
        models[k] = {"r2": r["chosen"]["r2"], "r2_ci": r["chosen"]["r2_ci95"], "mae": r["chosen"]["mae"], "baseline_mae": r["mean_baseline_mae"],
                     "n": len(trues), "min": float(min(trues.min(), preds.min())), "max": float(max(trues.max(), preds.max())),
                     "p25": float(np.percentile(trues, 25)), "p75": float(np.percentile(trues, 75)), "v3_r2": r["v3pls"]["r2"],
                     "vs_v3": r["vs_v3pls"]["verdict"]}
        (shown if beats else hidden).append(k)
        if beats:
            for o in r["oof"]:
                per_sample.setdefault(o["sample"], {})[k] = {"true": o["true"], "pred": o["pred"], "baseline": o["mean"]}
    version, model_name, cv = "v5", "PLS / ridge / extra-trees, chosen per target by inner CV", "5-fold nested out-of-fold"
else:
    res = json.load(open(os.path.join(A.v3, "hidsag_results.json")))
    geo = res["records"]["GEOMET"]["targets"]
    for full, r in geo.items():
        k = full.split(".")[-1]
        if k not in WANT:
            continue
        best = r["best_model"]
        trues = np.array([o["true"] for o in r["oof"]])
        preds = np.array([o["pred"] for o in r["oof"]])
        models[k] = {"r2": r[best]["r2"], "r2_ci": r[best]["r2_ci95"], "mae": r[best]["mae"], "baseline_mae": r["baseline"]["mae"],
                     "n": r["n"], "min": float(min(trues.min(), preds.min())), "max": float(max(trues.max(), preds.max())),
                     "p25": float(np.percentile(trues, 25)), "p75": float(np.percentile(trues, 75))}
        (shown if r["beats_baseline_mae"] else hidden).append(k)
        if r["beats_baseline_mae"]:
            for o in r["oof"]:
                per_sample.setdefault(o["sample"], {})[k] = {"true": o["true"], "pred": o["pred"], "baseline": o["baseline"]}
    version, model_name, cv = "v3", "PLS or ridge (best of two)", "5-fold out-of-fold"

rgb_src = os.path.join(A.v3, "rgb", "GEOMET")
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
samples.sort(key=lambda s: s["sample"])
random.Random(7).shuffle(samples)
samples = samples[:60]
ymax = max(max(max(s2["mean"]) for s2 in s["spectra"]) for s in samples)
mag = 10 ** np.floor(np.log10(ymax))
ymax = float(np.ceil(ymax / mag * 2) / 2 * mag)

# ---------------- feed mineralogy (QEMSCAN-taught; XRF for GEOCHEM)
COPY_M1 = ("<p><b>What it is.</b> {n} plant-feed size-fraction samples from {g} monthly composites (process line × month). "
           "QEMSCAN wt% is the truth. Folds never split a composite, and the confidence intervals resample composites, not samples.</p>"
           "<p><b>Why chalcopyrite works.</b> Sulphides have no SWIR fingerprint. The camera reads the sericite, biotite and gypsum that travel "
           "with chalcopyrite in this deposit. That link is site-specific, so every mine calibrates on its own QEMSCAN — which is the job QEMSCAN keeps.</p>"
           "<p><b>For Bushveld ore — untested.</b> The same loop would track the silicate gangue (pyroxene, plagioclase, chlorite, talc) that sets "
           "hardness and depressant demand. Platinum-group minerals stay with the microscope.</p>"
           "<p class='muted'>Coloured bars: model error below the average guess with a 95% CI excluding zero. Grey: not.</p>")
mineralogy = {"records": {}}
if A.v5:
    for rec, label, unit in (("MINERAL1", "Plant feed · QEMSCAN", "minerals"), ("MINERAL2", "QEMSCAN set 2", "minerals"),
                             ("GEOCHEM", "Mill feed · XRF", "assays")):
        R = V5["records"].get(rec)
        if not R or "targets" not in R:
            continue
        rows = [{"name": PRETTY.get(k, k), "r2": t["chosen"]["r2"], "ci": t["chosen"]["r2_ci95"], "beats": t["vs_mean"]["verdict"] == "better",
                 "sulphide": k in SULPHIDES, "vs_v3": t["vs_v3pls"]["verdict"]} for k, t in R["targets"].items()]
        hl = next((r for r in rows if r["name"] == "Chalcopyrite"), None) or max(rows, key=lambda r: r["r2"])
        sub = (f"{R['n']} samples" + (f" from {R['n_groups']} composites, grouped folds" if R.get("n_groups") else ", sample folds")
               + (" · QEMSCAN wt% as the truth" if rec.startswith("MINERAL") else " · XRF assays as the truth"))
        copy = COPY_M1.format(n=R["n"], g=R.get("n_groups") or R["n"]) if rec == "MINERAL1" else (
            f"<p><b>What it is.</b> {R['n']} samples, scored out-of-fold{', grouped by composite' if R.get('n_groups') else ''}. "
            + ("Mill-feed ore with XRF chemistry: the closest HIDSAG record to a camera on the feed belt." if rec == "GEOCHEM" else "A second QEMSCAN set.")
            + "</p><p class='muted'>Coloured bars: model error below the average guess with a 95% CI excluding zero. Grey: not.</p>")
        mineralogy["records"][rec] = {"label": label, "n": R["n"], "n_groups": R.get("n_groups"), "unit_label": unit, "rows": rows,
                                      "highlight": {"name": hl["name"], "r2": hl["r2"]}, "subtitle": sub, "copy": copy}
elif A.v4:
    M1 = json.load(open(os.path.join(A.v4, "mineral1_grouped_ci.json")))["targets"]
    rows = [{"name": PRETTY.get(k, k), "r2": t["r2"], "ci": t["r2_ci95_cluster"], "beats": t["beats_baseline_ci_excludes_zero"],
             "sulphide": k in SULPHIDES} for k, t in M1.items()]
    t0 = next(iter(M1.values()))
    cp = M1["Chalcopyrite"]
    mineralogy["records"]["MINERAL1"] = {"label": "Plant feed · QEMSCAN", "n": t0["n_samples"], "n_groups": t0["n_composites"], "unit_label": "minerals",
                                         "rows": rows, "highlight": {"name": "chalcopyrite", "r2": cp["r2"]},
                                         "subtitle": f"{t0['n_samples']} samples from {t0['n_composites']} composites · QEMSCAN wt% as the truth · grouped folds",
                                         "copy": COPY_M1.format(n=t0["n_samples"], g=t0["n_composites"])}

# ---------------- belt robustness (v5 simulation)
robustness = None
if A.v5:
    SC = ["dwell_25", "dwell_100", "dwell_400", "bright_085", "bright_115", "noise_2pct", "belt_combo"]
    LAB = {"dwell_25": "25 pixels", "dwell_100": "100 pixels", "dwell_400": "400 pixels", "bright_085": "light −15%", "bright_115": "light +15%",
           "noise_2pct": "2% noise", "belt_combo": "Belt case*"}
    rows = []
    for k in WANT:
        if k not in geo:
            continue
        r = geo[k]
        row = {"target": k, "full": r["chosen"]["r2"], "v3_full": r["v3pls"]["r2"], "v3_bright115": r["sim_v3pls_bright115"]["r2"]}
        row.update({s: r["sim_belt"][s]["r2"] for s in SC})
        rows.append(row)
    brows = []
    for rec in ("MINERAL1", "MINERAL2", "GEOCHEM"):
        R = V5["records"].get(rec)
        if not R or "targets" not in R:
            continue
        bl = [t["sim_blend"] for t in R["targets"].values() if "sim_blend" in t]
        if bl:
            brows.append({"record": rec, "n": len(bl), "beats": f"{sum(b['mae'] < b['mean_baseline_mae'] for b in bl)} / {len(bl)}",
                          "median_r2": float(np.median([b["r2"] for b in bl]))})
    robustness = {"scenarios": SC, "labels": LAB, "rows": rows,
                  "blend": {"subtitle": "Two unseen samples mixed 30/70 and 50/50 by pixel count; the truth is the weighted mean (sim_, assumes pixel share ≈ mass share)",
                            "rows": brows} if brows else None,
                  "copy": ("<p><b>Dwell.</b> A belt moves; the camera may see only a few hundred pixels of a given parcel. Predictions are re-made from 25, 100 and 400 random pixels.</p>"
                           "<p><b>Lighting and noise.</b> Brightness ×0.85 and ×1.15, and 2% sensor noise. The v5 features are brightness-normalised; the last column shows the "
                           "old v3 features under the same +15% lighting change.</p>"
                           "<p><b>*Belt case</b> = 100 pixels, +10% light and 2% noise together. Each effect alone is small; together they cost more, which is why the design averages over a time window and calibrates on a white tile.</p>""<p><b>Blended ore is the open problem.</b> Models trained on unmixed lab samples do not yet predict 30/70 and 50/50 blends well. The next training run adds simulated blends to the training folds.</p>"
                           "<p class='muted'>All rows are simulations on held-out lab samples (sim_). They test the model's sensitivity, not a real conveyor: dust, moisture, "
                           "particle size and belt speed are not modelled. A white-reference tile and dark frames on the real belt are part of the design.</p>")}

# ---------------- cheaper cameras (sensor_bands.py, mean spectra only)
sensors = None
sb_path = os.path.join(os.path.dirname(A.v5), "sensor_bands_results.json") if A.v5 else None
if sb_path and os.path.exists(sb_path):
    SB = json.load(open(sb_path))
    CAM = [("rgb", "Ordinary RGB camera", "3 broad colour bands"), ("led6", "Mono camera + LED ring", "6 narrow VNIR bands"),
           ("swir8", "SWIR camera + filter wheel", "8 diagnostic SWIR bands"), ("vnir_hs", "VNIR hyperspectral (silicon)", "every band 400-1000 nm"),
           ("full_hs", "VNIR + SWIR hyperspectral", "every band 400-2500 nm (HIDSAG instrument)")]
    sensors = {"rows": [{"id": c, "name": nm, "bands": bd,
                         "geomet_share": SB["summary"][f"GEOMET:{c}"]["median_share_of_full_hs_r2"],
                         "mineral1_share": SB["summary"][f"MINERAL1:{c}"]["median_share_of_full_hs_r2"],
                         "cu_rec": SB["GEOMET"]["Cu rec"][c]["r2"], "wi": SB["GEOMET"]["WI"][c]["r2"],
                         "chalcopyrite": SB["MINERAL1"]["Chalcopyrite"][c]["r2"]} for c, nm, bd in CAM],
               "note": ("Simulated from the HIDSAG mean spectra with Gaussian band responses; same nested CV for every camera. Mean spectra only (no "
                        "pixel spread), so absolute R² is lower than v5; compare cameras, not runs. Share = median of camera R² / full-hyperspectral R² "
                        "over targets where full R² > 0.2. Not PGM ore; talc's main feature (~2.31 µm) is SWIR-only.")}

note_hidden = f" Not better than the trivial baseline, so not shown: {', '.join(NICE[s] for s in hidden)}." if hidden else ""
data = {"version": version, "model_name": model_name, "cv": cv, "order": [s for s in WANT if s in shown], "models": models, "samples": samples,
        "wavelengths": wavelengths, "ymax": ymax, "mineralogy": mineralogy, "robustness": robustness, "sensors": sensors,
        "model_note": f"{model_name}; {cv}; drill-hole IDs are not in the metadata, so the split is by sample and may be optimistic.{note_hidden}",
        "footer": "Data: HIDSAG (Ehrenfeld et al., Scientific Data 2023), CC0, Figshare 10.6084/m9.figshare.c.5983921 — porphyry Cu-Mo, Chile; not PGM ore. "
                  "Replay for demonstration; a site deployment needs its own calibration samples. Font: Public Sans (SIL OFL 1.1)."}
json.dump(data, open(os.path.join(HERE, "data.json"), "w"), indent=0)
print(version, "samples", len(samples), "shown", shown, "hidden", hidden, "mineralogy", list(mineralogy["records"]), "robustness", bool(robustness))
for s in WANT:
    if s in models:
        m = models[s]
        print(f"{s:10s} R2={m['r2']:.3f} [{m['r2_ci'][0]:.2f},{m['r2_ci'][1]:.2f}] MAE={m['mae']:.3f} baseline={m['baseline_mae']:.3f} n={m['n']}"
              + (f"  v3 R2={m['v3_r2']:.3f} vs v3: {m['vs_v3']}" if "v3_r2" in m else ""))
