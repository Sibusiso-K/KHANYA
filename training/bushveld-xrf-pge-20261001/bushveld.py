"""T4 — Bushveld chromitite: what can a belt elemental analyser (XRF / PGNAA-type chemistry) tell us about PGE grade?

Data: Bachmann et al. (2019) "Data for: Multivariate geochemical classification of chromitite seams in the Bushveld
Complex, South Africa", Mendeley Data V1, doi 10.17632/dc8jcnbcvk.1, CC BY 4.0 (cite the dataset and the paper,
J. African Earth Sciences 2019). 1,205 drill-core intervals, 317 boreholes, 124 projects; major oxides (XRF) and
Pt, Pd, Rh, Ir, Ru, Au (ICP, ppm); stratigraphic seam label. Rows the authors' own `Filter` marks 0 are excluded.

These are laboratory assays of core intervals, not belt measurements. The question is narrower and honest:
"given the bulk chemistry a cross-belt analyser measures (Cr2O3, FeO, SiO2, MgO, Al2O3, CaO), how well can seam and
PGE grade be inferred?" The answer decides whether a belt XRF/PGNAA signal is worth wiring to the PGE decision.

Rule 2: folds are grouped by ProjectCode (mine/project, the conservative locality); honest n = projects.
Rule 3: baselines = training mean / median, and the metadata-only baseline "seam known from the mine plan"
(training median grade of that seam). Two questions:
  Q1  chemistry alone vs the mean/median            (no seam information on the belt)
  Q2  chemistry + seam vs seam-only                 (does chemistry add anything if the seam is known?)
Model choice is nested inside each training fold (grouped inner CV). Grades are modelled as log1p(ppm).
Intervals: split-conformal 80% with calibration projects held out before selection; one randomly drawn interval
per calibration project is its score (one score per unit); coverage per target with Clopper-Pearson at project level
using one interval per test project, and the per-interval rate reported alongside.
Seam: multinomial classification from chemistry, balanced accuracy and per-seam recall vs the majority class.
"""
import json, math, os
import numpy as np
import pandas as pd
from scipy.stats import binomtest, mannwhitneyu, wilcoxon
from sklearn.ensemble import ExtraTreesClassifier, ExtraTreesRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "..", "..", "data", "bushveld_thaba_chromitite", "DataSet_Thaba_Classification.csv")
OX = ["Cr2O3_%", "FeO_%", "SiO2_%", "MgO_%", "Al2O3_%", "CaO_%"]
PGE = ["Pt_ICP_ppm", "Pd_ICP_ppm", "Rh_ICP_ppm", "Ir_ICP_ppm", "Ru_ICP_ppm"]
ALPHA = 0.2
SEED = 7


def load():
    df = pd.read_csv(CSV, sep=";")
    df = df[df["Filter"] == 1].copy()
    for c in OX + PGE + ["Au_ICP_ppm", "DepthFrom", "DepthTo"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=OX + PGE + ["Stratigraphy"])
    df["Stratigraphy"] = df["Stratigraphy"].astype(str).str.strip()   # source has "MG4" and "MG4 "
    df["Cr_Fe"] = df["Cr2O3_%"] / df["FeO_%"].clip(lower=0.1)
    df["Mg_Fe"] = df["MgO_%"] / df["FeO_%"].clip(lower=0.1)
    df["Al_Cr"] = df["Al2O3_%"] / df["Cr2O3_%"].clip(lower=0.1)
    df["4E_ppm"] = df["Pt_ICP_ppm"] + df["Pd_ICP_ppm"] + df["Rh_ICP_ppm"] + df["Au_ICP_ppm"].fillna(0)
    return df.reset_index(drop=True)


FEAT = OX + ["Cr_Fe", "Mg_Fe", "Al_Cr"]
TARGETS = ["Pt_ICP_ppm", "Pd_ICP_ppm", "Rh_ICP_ppm", "4E_ppm"]


def reg_candidates():
    c = {f"ridge{a}": (lambda a=a: make_pipeline(StandardScaler(), Ridge(alpha=a))) for a in (0.1, 1, 10)}
    c["et"] = lambda: ExtraTreesRegressor(n_estimators=400, min_samples_leaf=3, max_features=0.6, random_state=0, n_jobs=-1)
    return c


def design(df, with_seam, seams):
    X = df[FEAT].values
    if with_seam:
        S = np.stack([(df["Stratigraphy"].values == s).astype(float) for s in seams], 1)
        X = np.hstack([X, S])
    return X


def nested_pick(X, y, groups, idx):
    C = reg_candidates()
    gk = GroupKFold(min(4, len(np.unique(groups[idx]))))
    err = {k: [] for k in C}
    for a, b in gk.split(idx, groups=groups[idx]):
        A, B = idx[a], idx[b]
        for k, mk in C.items():
            m = mk().fit(X[A], y[A])
            err[k].append(np.abs(m.predict(X[B]) - y[B]).mean())
    return min(sorted(C), key=lambda k: np.mean(err[k]))


def cluster_boot_diff(e1, e0, groups, B=4000, seed=1):
    rng = np.random.default_rng(seed)
    ug = np.unique(groups)
    idx = {g: np.flatnonzero(groups == g) for g in ug}
    v = []
    for _ in range(B):
        b = np.concatenate([idx[ug[i]] for i in rng.integers(0, len(ug), len(ug))])
        v.append(e1[b].mean() - e0[b].mean())
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]


def gates(y, p_new, p_base, groups):
    e1, e0 = np.abs(y - p_new), np.abs(y - p_base)
    ci = cluster_boot_diff(e1, e0, groups)
    ug = np.unique(groups)
    d = np.array([e1[groups == g].mean() - e0[groups == g].mean() for g in ug])
    try:
        wp = float(wilcoxon(d, alternative="less").pvalue)
    except ValueError:
        wp = 1.0
    pos, neg = (d > 0).sum(), (d < 0).sum()
    rbc = float((neg - pos) / max(len(d), 1))
    mw = float(mannwhitneyu(e1, e0, alternative="less").pvalue)
    cliff = float(np.sign(e1[:, None] - e0[None, :]).mean())
    better = ci[1] < 0 and wp < 0.05 and mw < 0.05
    worse = ci[0] > 0
    return {"mae_new": float(e1.mean()), "mae_base": float(e0.mean()), "mae_diff_ci95_project_boot": ci, "wilcoxon_p_less_projects": wp,
            "matched_rank_biserial": rbc, "mannwhitney_p_less": mw, "cliffs_delta": cliff, "n_projects": int(len(ug)),
            "verdict": "better" if better else ("worse" if worse else "no significant difference")}


def main():
    df = load()
    groups = df["ProjectCode"].astype(str).values
    seams = sorted(df["Stratigraphy"].unique())
    n = len(df)
    print("intervals", n, "boreholes", df["BH_ID"].nunique(), "projects", len(np.unique(groups)), "seams", seams)
    outer = list(GroupKFold(5).split(np.zeros(n), groups=groups))
    res = {"data": "Bachmann et al. 2019, Mendeley 10.17632/dc8jcnbcvk.1, CC BY 4.0", "n_intervals": n,
           "n_projects": int(len(np.unique(groups))), "n_boreholes": int(df["BH_ID"].nunique()), "seams": seams,
           "seam_counts": df["Stratigraphy"].value_counts().to_dict(), "targets": {}, "seam_classification": {}}
    oof_seam = np.empty(n, dtype=object)
    oof_seam_proba = np.zeros((n, len(seams)))
    preds = {t: {"chem": np.zeros(n), "chem_seam": np.zeros(n), "seam_only": np.zeros(n), "mean": np.zeros(n), "median": np.zeros(n),
                 "lo": np.zeros(n), "hi": np.zeros(n)} for t in TARGETS}
    cal_meta = []
    fold_of = np.zeros(n, int)
    thr = {t: np.zeros((n, 2)) for t in TARGETS}
    for fo, (tr, te) in enumerate(outer):
        rng = np.random.default_rng(SEED + fo)
        ug = np.unique(groups[tr])
        cal_g = set(rng.permutation(ug)[:max(2, int(round(0.25 * len(ug))))].tolist())
        cal = np.array([i for i in tr if groups[i] in cal_g])
        ptr = np.array([i for i in tr if groups[i] not in cal_g])
        # seam classifier (chemistry only), nested over two candidates inside proper-training
        Xc = df[FEAT].values
        cands = {"logreg": lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=1.0)),
                 "et": lambda: ExtraTreesClassifier(n_estimators=400, min_samples_leaf=2, random_state=0, n_jobs=-1)}
        score = {}
        for k, mk in cands.items():
            s = []
            for a, b in GroupKFold(4).split(ptr, groups=groups[ptr]):
                m = mk().fit(Xc[ptr[a]], df["Stratigraphy"].values[ptr[a]])
                s.append(balanced_accuracy_score(df["Stratigraphy"].values[ptr[b]], m.predict(Xc[ptr[b]])))
            score[k] = np.mean(s)
        bk = max(sorted(score), key=lambda k: score[k])
        clf = cands[bk]().fit(Xc[tr], df["Stratigraphy"].values[tr])
        oof_seam[te] = clf.predict(Xc[te])
        pr = clf.predict_proba(Xc[te])
        for j, s in enumerate(clf.classes_):
            oof_seam_proba[te, seams.index(s)] = pr[:, j]
        for t in TARGETS:
            y = np.log1p(df[t].values)
            Xa, Xb = design(df, False, seams), design(df, True, seams)
            ka = nested_pick(Xa, y, groups, ptr)
            kb = nested_pick(Xb, y, groups, ptr)
            ma = reg_candidates()[ka]().fit(Xa[ptr], y[ptr])          # deployable (proper-training) model
            mb = reg_candidates()[kb]().fit(Xb[ptr], y[ptr])
            # conformal on calibration projects: one random interval per project
            cal_pick = np.array([rng.choice(np.flatnonzero(groups == g)) for g in sorted(cal_g)])
            sc = np.abs(y[cal_pick] - ma.predict(Xa[cal_pick]))
            ncal = len(sc)
            k = int(math.ceil((ncal + 1) * (1 - ALPHA)))
            q = float(np.sort(sc)[k - 1]) if k <= ncal else float("inf")
            pa = ma.predict(Xa[te])
            preds[t]["chem"][te] = pa
            preds[t]["chem_seam"][te] = mb.predict(Xb[te])
            preds[t]["lo"][te], preds[t]["hi"][te] = pa - q, pa + q
            preds[t]["mean"][te] = y[ptr].mean()
            thr[t][te] = [float(np.percentile(df[t].values[ptr], 25)), float(np.percentile(df[t].values[ptr], 75))]
            fold_of[te] = fo
            preds[t]["median"][te] = np.median(y[ptr])
            seam_med = {s: np.median(y[ptr][df["Stratigraphy"].values[ptr] == s]) if (df["Stratigraphy"].values[ptr] == s).any() else np.median(y[ptr]) for s in seams}
            preds[t]["seam_only"][te] = [seam_med[s] for s in df["Stratigraphy"].values[te]]
            cal_meta.append({"fold": fo, "target": t, "n_cal_projects": ncal, "k": k, "q_log": q, "models": [ka, kb]})
        print(f"fold {fo}: proper {len(ptr)} cal projects {len(cal_g)} seam model {bk}")
    yS = df["Stratigraphy"].values
    maj = pd.Series(yS).value_counts().idxmax()
    res["seam_classification"] = {"balanced_accuracy": float(balanced_accuracy_score(yS, oof_seam)),
                                  "majority_class": maj, "balanced_accuracy_majority": float(balanced_accuracy_score(yS, np.array([maj] * n))),
                                  "accuracy": float((oof_seam == yS).mean()),
                                  "recall_per_seam": {s: float((oof_seam[yS == s] == s).mean()) for s in seams}}
    print("seam balanced accuracy", round(res["seam_classification"]["balanced_accuracy"], 3), "majority", round(res["seam_classification"]["balanced_accuracy_majority"], 3))
    for t in TARGETS:
        y = np.log1p(df[t].values)
        P = preds[t]
        base = min(("mean", "median"), key=lambda b: np.abs(y - P[b]).mean())
        q1 = gates(y, P["chem"], P[base], groups)
        q2 = gates(y, P["chem_seam"], P["seam_only"], groups)
        q3 = gates(y, P["seam_only"], P[base], groups)
        cover = (y >= P["lo"]) & (y <= P["hi"])
        rng = np.random.default_rng(3)
        one = np.array([rng.choice(np.flatnonzero(groups == g)) for g in np.unique(groups)])
        k1 = int(cover[one].sum())
        ci = binomtest(k1, len(one)).proportion_ci(method="exact")
        r2 = lambda p: float(1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum())
        res["targets"][t] = {"space": "log1p(ppm)", "r2_chem": r2(P["chem"]), "r2_chem_seam": r2(P["chem_seam"]), "r2_seam_only": r2(P["seam_only"]),
                             "Q1_chem_vs_" + base: q1, "Q2_chem_plus_seam_vs_seam_only": q2, "seam_only_vs_" + base: q3,
                             "coverage_per_interval": float(cover.mean()), "coverage_one_per_project": k1 / len(one),
                             "coverage_one_per_project_ci95": [float(ci.low), float(ci.high)], "n_projects": int(len(one))}
        print(f"{t:12s} R2 chem {res['targets'][t]['r2_chem']:.3f} | chem+seam {res['targets'][t]['r2_chem_seam']:.3f} | seam-only {res['targets'][t]['r2_seam_only']:.3f} "
              f"| Q1 {q1['verdict']} | Q2 {q2['verdict']} ({q2['mae_diff_ci95_project_boot'][0]:+.3f},{q2['mae_diff_ci95_project_boot'][1]:+.3f}) "
              f"| cover {cover.mean():.2f} / per-project {k1}/{len(one)} [{ci.low:.2f},{ci.high:.2f}]")
        print(f"   Q2 detail: wilcoxon(projects) p={q2['wilcoxon_p_less_projects']:.3g} mann-whitney p={q2['mannwhitney_p_less']:.3g} cliff={q2['cliffs_delta']:+.3f} rbc={q2['matched_rank_biserial']:+.2f}")
    res["calibration"] = cal_meta
    # app replay: intervals as parcels, grouped by borehole and ordered by depth
    app = []
    for i in range(n):
        r = df.iloc[i]
        app.append({"fold": int(fold_of[i]), "thr": {t: thr[t][i].tolist() for t in TARGETS}, "project": r["ProjectCode"], "bh": r["BH_ID"], "from": float(r["DepthFrom"]), "to": float(r["DepthTo"]), "seam": r["Stratigraphy"],
                    "seam_pred": oof_seam[i], "seam_conf": float(oof_seam_proba[i].max()),
                    "ox": {c: float(r[c]) for c in OX},
                    "pge": {t: {"true": float(r[t]), "pred": float(np.expm1(preds[t]["chem"][i])), "lo": float(max(0.0, np.expm1(preds[t]["lo"][i]))),
                                "hi": (float(np.expm1(preds[t]["hi"][i])) if np.isfinite(preds[t]["hi"][i]) else None)} for t in TARGETS}})
    json.dump(res, open(os.path.join(HERE, "results.json"), "w"), indent=1)
    beats = {t: res["targets"][t][[k for k in res["targets"][t] if k.startswith("Q1_")][0]]["verdict"] == "better" for t in TARGETS}
    json.dump({"note": "out-of-fold, grouped by project; grades in ppm; intervals 80% split-conformal on log1p scale; thr = proper-training p25/p75 of the fold",
               "beats_baseline": beats, "seam_balanced_accuracy": res["seam_classification"]["balanced_accuracy"],
               "seam_balanced_accuracy_majority": res["seam_classification"]["balanced_accuracy_majority"],
               "seams": seams, "rows": app}, open(os.path.join(HERE, "app_bushveld.json"), "w"))


if __name__ == "__main__":
    main()
