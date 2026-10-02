"""Build run_v8_model.py from run_v6.py by asserted replacements. GEOMET only; v6 modelling unchanged, plus:
  * an EXACT one-sided split-conformal upper bound per sample (alpha 0.10), from SIGNED calibration scores, one score
    per calibration unit, k = ceil((n_cal+1)(1-alpha)): replaces the CV+-style approximation used locally (ClauDex r1 #17);
  * a deployable model fitted on ALL GEOMET samples under the same nested choice rule, exported as plain sklearn objects
    (no pickled custom classes) with the feature code, the OOD transform and versions (ClauDex r1 #39);
  * a CPU latency benchmark of per-parcel feature extraction + inference on Kaggle CPU (labelled: not the edge PC).
"""
from pathlib import Path

src = Path(__file__).resolve().parent.parent / "hidsag-v6-live-20261001" / "run_v6.py"
s = src.read_text(encoding="utf-8")


def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (old[:70], n)
    s = s.replace(old, new)


rep('"""REEFPRINT hyperspectral v6 — ', '"""REEFPRINT hyperspectral v8-model: v6 modelling on GEOMET + exact one-sided split-conformal bound + exported deployable model + CPU latency. Based on v6 — ')
rep('import gzip, hashlib, json, math, os, re, shutil, sys, time, traceback, urllib.request, zipfile\n',
    'import gzip, hashlib, json, math, os, re, shutil, sys, time, traceback, urllib.request, zipfile\nos.system("pip install -q scikit-learn==1.8.0 joblib")  # pin to the local version so the export loads (logged below)\n')
rep('RECORDS = ["GEOMET", "MINERAL1"]', 'RECORDS = ["GEOMET"]\nALPHA_UP = 0.10')
rep('''        q = np.sort(scores, 0)[k - 1] if k <= n_cal else np.full(T, np.inf)
''', '''        q = np.sort(scores, 0)[k - 1] if k <= n_cal else np.full(T, np.inf)
        sscores = np.array([[np.max(Y[units == u, t] - P[units == u, t]) for t in range(T)] for u in cu])   # SIGNED, one per unit
        k_up = int(math.ceil((n_cal + 1) * (1 - ALPHA_UP)))
        q_up = np.sort(sscores, 0)[k_up - 1] if k_up <= n_cal else np.full(T, np.inf)
''')
rep('''            per[i] = {"sample": names[i], "unit": str(units[i]), "fold": fo, "pred": P[i].tolist(), "lo": lo_i.tolist(), "hi": hi_i.tolist(),''',
    '''            per[i] = {"sample": names[i], "unit": str(units[i]), "fold": fo, "pred": P[i].tolist(), "lo": lo_i.tolist(), "hi": hi_i.tolist(),
                      "hi_up": [None if not np.isfinite(v) else float(v) for v in (P[i] + q_up)],''')
rep('''                          "q": [None if not np.isfinite(v) else float(v) for v in q], "unbounded": bool(k > n_cal),''',
    '''                          "q": [None if not np.isfinite(v) else float(v) for v in q], "unbounded": bool(k > n_cal),
                          "q_up": [None if not np.isfinite(v) else float(v) for v in q_up], "k_up": k_up,''')
rep('''            if names[i] in showcase and len(rows[i]["cubes"]) == 2:''', '''            if False:  # v8-model exports no showcase cubes''')
rep('''    return {"targets": keep, "n": n,''', '''    export_model(rec, rows, keep, Y, PV, PS, SPEC, S_lin, groups, additive, fold_info)
    return {"targets": keep, "n": n,''')
rep('"hidsag_v6_results.json"', '"hidsag_v8_model_results.json"', count=2)
rep('"version": "v6"', '"version": "v8-model"')

export = r'''

def export_model(rec, rows, keep, Y, PV, PS, SPEC, S_lin, groups, additive, fold_info):
    """Deployable model on ALL samples (same nested choice rule), exported as plain sklearn objects + feature code."""
    global SPEC_ALL
    try:
        import inspect, platform, joblib, sklearn
        n = len(rows)
        allidx = np.arange(n)
        best, _ = choose(allidx, groups, PV, PS, S_lin, Y, additive)
        kms = fit_kmeans(PV, PS, allidx)
        XN = np.stack([np.concatenate([SPEC[i], hist_feats(kms, PV[i], PS[i])]) for i in range(n)])
        fam = Family(XN, S_lin, Y, additive, SEED)
        S_arr = np.stack(SPEC)
        sc = StandardScaler().fit(S_arr)
        pca = PCA(n_components=min(10, n - 1), random_state=0).fit(sc.transform(S_arr))
        lw = LedoitWolf().fit(pca.transform(sc.transform(S_arr)))
        ood_thr = {"p95": float(np.median([f["ood_p95"] for f in fold_info])), "p99": float(np.median([f["ood_p99"] for f in fold_info])),
                   "rule": "median over the 5 outer folds of the calibration-unit percentiles (deployment approximation)"}
        q_up = {t: float(np.median([f["q_up"][j] for f in fold_info if f["q_up"][j] is not None])) for j, t in enumerate(keep)}
        bundle = {"targets": keep, "best": best, "kms": kms, "sn": fam.sn, "sl": fam.sl, "ym": fam.ym, "ys": fam.ys,
                  "models": {k: fam.m[k] for k in sorted(set(best))}, "ood": {"scaler": sc, "pca": pca, "lw": lw, **ood_thr},
                  "q_up_median_over_folds": q_up, "grid_vnir": GV, "grid_swir": GS, "pool": POOL, "seed": SEED,
                  "windows": WINDOWS, "vwindow": VWINDOW}
        joblib.dump(bundle, os.path.join(OUT, "geomet_model.joblib"), compress=3)
        code = "# Feature code exported verbatim from run_v8_model.py (v6 definitions)\nimport numpy as np\n" + \
               f"GV = np.arange(410.0, 991.0, 5.0)\nGS = np.arange(1010.0, 2491.0, 10.0)\nWINDOWS = {WINDOWS!r}\nVWINDOW = {VWINDOW!r}\n\n" + \
               "\n\n".join(inspect.getsource(f) for f in (continuum_removed, spec_feats, lin_feats, hist_feats))
        open(os.path.join(OUT, "geomet_model_features.py"), "w").write(code)
        lat = []
        for i in range(min(40, n)):
            t1 = time.perf_counter()
            xn = np.concatenate([spec_feats(PV[i], PS[i]), hist_feats(kms, PV[i], PS[i])])[None]
            pick(fam.predict(xn, lin_feats(PV[i], PS[i])[None], only=set(best)), best)
            float(lw.mahalanobis(pca.transform(sc.transform(spec_feats(PV[i], PS[i])[None])))[0])
            lat.append((time.perf_counter() - t1) * 1000)
        rawv = np.random.default_rng(0).random((89 * 130, 471), dtype=np.float32)
        raws = np.random.default_rng(1).random((89 * 130, 268), dtype=np.float32)
        Mv, Ms = avg_matrix(np.linspace(400, 1000, 471), GV, 5.0), avg_matrix(np.linspace(1000, 2500, 268), GS, 10.0)
        t1 = time.perf_counter()
        for _ in range(10):
            rawv @ Mv; raws @ Ms
        map_ms = (time.perf_counter() - t1) * 100
        meta = {"record": rec, "n_train": int(n), "best": best, "targets": keep, "sklearn": sklearn.__version__, "numpy": np.__version__,
                "python": platform.python_version(), "cpu": platform.processor() or platform.machine(), "cpus": os.cpu_count(),
                "latency_ms_features_plus_inference_plus_ood": {"median": float(np.median(lat)), "p95": float(np.percentile(lat, 95)), "n": len(lat)},
                "latency_ms_grid_mapping_synthetic_raw_size": map_ms,
                "latency_note": "Kaggle CPU, not the edge PC; per parcel from an already-sampled pixel pool (POOL px per sensor); grid mapping timed on a synthetic array of the raw cube size",
                "q_up_median_over_folds": q_up, "ood": ood_thr}
        json.dump(meta, open(os.path.join(OUT, "geomet_model_meta.json"), "w"), indent=1)
        log("exported model", meta["latency_ms_features_plus_inference_plus_ood"], "map_ms", round(map_ms, 1), "sklearn", sklearn.__version__)
    except Exception as e:
        log("EXPORT FAILED", repr(e))
        log(traceback.format_exc())

'''
rep('''def main():''', export.lstrip("\n") + '''def main():''')
out = Path(__file__).resolve().parent / "run_v8_model.py"
out.write_text(s, encoding="utf-8")
print("wrote", out, len(s))
