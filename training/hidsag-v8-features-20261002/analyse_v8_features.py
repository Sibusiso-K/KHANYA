"""Analysis of the v8 spectral features against MINERAL1 QEMSCAN, exactly as SPEC.md (written and committed before any
feature output existed). Run: python training/hidsag-v8-features-20261002/analyse_v8_features.py -> analysis_v8_features.json
"""
import json, math, os, re
import numpy as np
from scipy.stats import norm, rankdata

HERE = os.path.dirname(os.path.abspath(__file__))
F = json.load(open(os.path.join(HERE, "output", "hidsag_v8_features.json")))
B = 4000
HYP = {  # id: (feature keys summed, QEMSCAN labels summed, in_holm)
    "H1": (["aloh_2200_depth"], ["Muscovite/Sericite", "Kaolinite"], True),
    "H2": (["feoh_2250_depth", "mgoh_2330_depth"], ["Chlorite", "Biotite"], True),
    "H4": (["fe3_900_depth"], ["Fe Oxides"], True),
    "H3": (["h2o_1750_gypsum_depth"], ["Anhydrite/Gypsum"], False),
}
MIN_EFFECT = 0.30


def tags_of(r):
    return sorted({t for ct in r["crop_tags"] for t in ct})


def parse(r):
    tg = tags_of(r)
    j = " ".join(tg)
    m = re.search(r"(P\d+).*?(S\d+)", j)
    line, month = (m.group(1), m.group(2)) if m else ("?", "?")
    frac = " ".join(t for t in tg if not re.match(r"^[PS]\d+$", t)) or "none"
    return line, month, line + month, frac


def partial_spearman(x, y, D):
    rx, ry = rankdata(x), rankdata(y)
    beta_x, *_ = np.linalg.lstsq(D, rx, rcond=None)
    beta_y, *_ = np.linalg.lstsq(D, ry, rcond=None)
    ex, ey = rx - D @ beta_x, ry - D @ beta_y
    if ex.std() < 1e-12 or ey.std() < 1e-12:
        return 0.0
    return float(np.corrcoef(ex, ey)[0, 1])


def design(strata):
    lv = sorted(set(strata))
    D = np.ones((len(strata), 1))
    if len(lv) > 1:
        D = np.column_stack([D] + [(np.array(strata) == v).astype(float) for v in lv[1:]])
    return D


def stat(idx, x, y, strata):
    return partial_spearman(x[idx], y[idx], design([strata[i] for i in idx]))


def boot(x, y, strata, clusters, seed=1):
    rng = np.random.default_rng(seed)
    uc = sorted(set(clusters))
    members = {c: [i for i, cc in enumerate(clusters) if cc == c] for c in uc}
    vals = []
    for _ in range(B):
        idx = [i for c in rng.choice(uc, len(uc), replace=True) for i in members[c]]
        vals.append(stat(np.array(idx), x, y, strata))
    return np.array(vals)


def power(rho, n, alpha):
    return float(norm.cdf(math.atanh(rho) * math.sqrt(max(n - 3, 1)) - norm.ppf(1 - alpha)))


def main():
    recs = [r for r in F["records"]["MINERAL1"] if "skipped" not in r]
    # identity reconciliation (SPEC): duplicates = identical QEMSCAN vector AND identical tags -> collapse to one
    keyed, dups = {}, []
    for r in recs:
        k = (tuple(sorted((a, round(b, 6)) for a, b in r["vars"].items())), tuple(tags_of(r)))
        if k in keyed:
            dups.append((keyed[k]["sample"], r["sample"]))
        else:
            keyed[k] = r
    rows = list(keyed.values())
    ident = {"records_in_file": len(F["records"]["MINERAL1"]), "skipped": len(F["records"]["MINERAL1"]) - len(recs),
             "duplicates_collapsed": dups, "records_analysed": len(rows), "dataset_paper_physical_samples": 94,
             "crop_count_distribution": {str(k): int(v) for k, v in zip(*np.unique([r["n_crops"] for r in rows], return_counts=True))}}
    parsed = [parse(r) for r in rows]
    strata = [p[0] + "|" + p[3] for p in parsed]          # line x fraction
    comp = [p[2] for p in parsed]
    month = [p[1] for p in parsed]
    ident["n_composites"] = len(set(comp))
    ident["n_months"] = len(set(month))
    ident["strata"] = sorted(set(strata))
    out = {"spec": "SPEC.md", "identity": ident, "hypotheses": {}}
    for mask, agg in (("mask_v6", "primary_mean_spectrum"), ("mask_none", "primary_mean_spectrum"), ("mask_v6", "secondary_median_pixel")):
        key = f"{mask}/{agg}"
        res = {}
        for h, (fk, lab, in_holm) in HYP.items():
            x = np.array([sum(r[mask][agg][f] for f in fk) for r in rows])
            y = np.array([sum(r["vars"].get(l, 0.0) for l in lab) for r in rows])
            rho = stat(np.arange(len(rows)), x, y, strata)
            bc = boot(x, y, strata, comp)
            bm = boot(x, y, strata, month, seed=2)
            p_one = float((np.sum(bc <= 0) + 1) / (B + 1))
            res[h] = {"feature": fk, "qemscan_group": lab, "in_holm": in_holm, "partial_spearman": rho,
                      "ci95_cluster_composite": [float(np.percentile(bc, 2.5)), float(np.percentile(bc, 97.5))],
                      "ci95_cluster_month": [float(np.percentile(bm, 2.5)), float(np.percentile(bm, 97.5))],
                      "p_one_sided_positive": p_one,
                      "raw_spearman": float(np.corrcoef(rankdata(x), rankdata(y))[0, 1]),
                      "feature_vs_fraction_only_r2": float(1 - np.var(rankdata(x) - design(strata) @ np.linalg.lstsq(design(strata), rankdata(x), rcond=None)[0]) / np.var(rankdata(x)))}
        holm = sorted([(h, v["p_one_sided_positive"]) for h, v in res.items() if v["in_holm"]], key=lambda t: t[1])
        m, prev = len(holm), 0.0
        for i, (h, p) in enumerate(holm):
            prev = max(prev, min(1.0, p * (m - i)))
            res[h]["p_holm"] = prev
        for h, v in res.items():
            lo, hi = v["ci95_cluster_composite"]
            ph = v.get("p_holm", v["p_one_sided_positive"])
            if v["partial_spearman"] >= MIN_EFFECT and ph < 0.05 and v["in_holm"]:
                v["verdict"] = "pass: validated spectral association"
            elif hi < 0:
                v["verdict"] = "fail: wrong sign"
            elif lo > 0 and not v["in_holm"]:
                v["verdict"] = "exploratory: positive"
            elif lo > 0:
                v["verdict"] = "positive but below the minimum useful effect or Holm"
            else:
                v["verdict"] = "inconclusive"
        out["hypotheses"][key] = res
    nclu = ident["n_composites"]
    out["power"] = {f"rho_{r}": power(r, nclu, 0.05 / 3) for r in (0.3, 0.4, 0.5, 0.6)}
    out["power_note"] = f"Fisher-z approximation with n = {nclu} composites and a Bonferroni-level alpha of 0.05/3 one-sided (conservative vs Holm)"
    json.dump(out, open(os.path.join(HERE, "analysis_v8_features.json"), "w"), indent=1)
    print("identity:", {k: v for k, v in ident.items() if k != "strata"})
    for key, res in out["hypotheses"].items():
        print("==", key)
        for h, v in res.items():
            print(f"  {h} {'+'.join(v['qemscan_group']):32s} rho {v['partial_spearman']:+.3f} CI {[round(a, 3) for a in v['ci95_cluster_composite']]} "
                  f"month-CI {[round(a, 3) for a in v['ci95_cluster_month']]} p1 {v['p_one_sided_positive']:.4f} holm {v.get('p_holm', float('nan')):.4f} "
                  f"raw {v['raw_spearman']:+.3f} -> {v['verdict']}")
    print("power", out["power"])


if __name__ == "__main__":
    main()
