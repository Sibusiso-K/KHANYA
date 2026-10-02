"""Build run_v7.py from run_v6.py by exact, asserted replacements (one change per line item, nothing else moves).

v7 = v6 with a wider, pre-registered model menu on GEOMET only (MINERAL1's mineralogy claim is withdrawn):
  + nl_hgb  HistGradientBoosting per target on the v5 nonlinear features
  + nl_svr  RBF SVR per target on the same features
  + ens5    fixed, unweighted mean of nl_et, nl_ridge100, nl_pls8, lin_ridge100, lin_pls8 (members fixed in advance)
Selection is still nested inside proper-training; folds, calibration split, conformal rule, OOD and occlusion are unchanged.
Also logs every lab variable's coverage in GEOMET metadata, so other real targets can be found.
"""
from pathlib import Path

src = Path(__file__).resolve().parent.parent / "hidsag-v6-live-20261001" / "run_v6.py"
s = src.read_text(encoding="utf-8")


def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (old[:60], n)
    s = s.replace(old, new)


rep('"""REEFPRINT hyperspectral v6 — ', '"""REEFPRINT hyperspectral v7: v6 plus a wider pre-registered model menu (nl_hgb, nl_svr, ens5), GEOMET only. Based on v6 — ')
rep('RECORDS = ["GEOMET", "MINERAL1"]', 'RECORDS = ["GEOMET"]')
rep("from sklearn.ensemble import ExtraTreesRegressor\n",
    "from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor\nfrom sklearn.svm import SVR\n")
rep('''    c = ["nl_et"] + [f"nl_ridge{a}" for a in NL_RIDGE] + ["nl_pls8"] + [f"lin_ridge{a}" for a in LIN_RIDGE] + ["lin_pls4", "lin_pls8"]''',
    '''    c = ["nl_et"] + [f"nl_ridge{a}" for a in NL_RIDGE] + ["nl_pls8"] + [f"lin_ridge{a}" for a in LIN_RIDGE] + ["lin_pls4", "lin_pls8"]
    c += ["nl_hgb", "nl_svr", "ens5"]''')
rep('''        self.m["nl_pls8"] = [_pls(A, Z[:, t], 8) for t in range(T)]''',
    '''        self.m["nl_pls8"] = [_pls(A, Z[:, t], 8) for t in range(T)]
        self.m["nl_hgb"] = [HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=5,
                                                          l2_regularization=1.0, random_state=0).fit(A, Z[:, t]) for t in range(T)]
        self.m["nl_svr"] = [SVR(C=1.0, epsilon=0.1, gamma="scale").fit(A, Z[:, t]) for t in range(T)]''')
rep('''        A, B = self.sn.transform(Xnl), self.sl.transform(Xlin)
        out = {}
        for k, m in self.m.items():
            if only is not None and k not in only:
                continue''',
    '''        A, B = self.sn.transform(Xnl), self.sl.transform(Xlin)
        out = {}
        need = None if only is None else (set(only) | (set(ENS) if "ens5" in only else set()))
        for k, m in self.m.items():
            if need is not None and k not in need:
                continue''')
rep('''            out[k] = z * self.ys + self.ym
        return out


class RGBFamily:''',
    '''            out[k] = z * self.ys + self.ym
        if (only is None or "ens5" in only) and all(k in out for k in ENS):
            out["ens5"] = np.mean([out[k] for k in ENS], 0)
        return out


ENS = ("nl_et", "nl_ridge100", "nl_pls8", "lin_ridge100", "lin_pls8")


class RGBFamily:''')
rep('''    keys = sorted({k for r in rows for k in r["y"]})
''', '''    keys = sorted({k for r in rows for k in r["y"]})
    VAR_COV = {k: int(sum(k in r["y"] and np.isfinite(r["y"][k]) for r in rows)) for k in keys}
    log(rec, "lab variable coverage", VAR_COV)
''')
rep('''    return {"targets": keep, "n": n,''', '''    return {"var_coverage": VAR_COV, "targets": keep, "n": n,''')
rep('''            if names[i] in showcase and len(rows[i]["cubes"]) == 2:''', '''            if False:  # v7 exports no showcase cubes; the display assets come from v6 and export_hr''')
rep('"hidsag_v6_results.json"', '"hidsag_v7_results.json"', count=2)
rep('"version": "v6"', '"version": "v7"')
rep('"plan": "PLAN-live-v6.md (ClauDex, Codex gpt-6-astra, APPROVED round 3)"',
    '"plan": "v6 plan + PREREG.md in hidsag-v7-ens-20261002 (menu widened only)"')

out = Path(__file__).resolve().parent / "run_v7.py"
out.write_text(s, encoding="utf-8")
print("wrote", out, len(s))
