"""Build run_v9_robust.py from run_v6.py (asserted replacements). GEOMET only; v6 modelling unchanged; each test-fold
parcel is re-scored by the fold model that never saw it, on new-capture / partial / perturbed variants (PREREG.md)."""
from pathlib import Path

src = Path(__file__).resolve().parent.parent / "hidsag-v6-live-20261001" / "run_v6.py"
s = src.read_text(encoding="utf-8")


def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (old[:70], n)
    s = s.replace(old, new)


rep('"""REEFPRINT hyperspectral v6 — ', '"""REEFPRINT hyperspectral v9-robustness: v6 on GEOMET + unseen-capture variants scored by the fold model that never saw the parcel. Based on v6 — ')
rep('RECORDS = ["GEOMET", "MINERAL1"]', 'RECORDS = ["GEOMET"]')
rep('''        rows.append({"sample": sample, "y": y, "tags": " ".join(crop_tags(meta)), "pv": pv, "ps": ps, "cubes": cubes})''',
    '''        rng2 = np.random.default_rng(SEED + 7919 + i)
        FV, FS = pools["vnir_low"], pools["swir_low"]
        pv2 = FV[rng2.choice(len(FV), min(POOL, len(FV)), replace=False)]
        ps2 = FS[rng2.choice(len(FS), min(POOL, len(FS)), replace=False)]
        HV, HS = FV[: max(len(FV) // 2, 10)], FS[: max(len(FS) // 2, 10)]
        pvh = HV[rng2.choice(len(HV), min(POOL, len(HV)), replace=False)]
        psh = HS[rng2.choice(len(HS), min(POOL, len(HS)), replace=False)]
        rows.append({"sample": sample, "y": y, "tags": " ".join(crop_tags(meta)), "pv": pv, "ps": ps, "cubes": {},
                     "variants": {"resample": (pv2, ps2), "half": (pvh, psh)}})''')
rep('''        te_d2 = d2(S_arr[te])
''', '''        te_d2 = d2(S_arr[te])
        # v9: unseen-capture variants of each test parcel, scored by THIS fold's model (which never saw the parcel)
        rngv = np.random.default_rng(SEED + 31 * fo)

        def shift1(a):
            out = np.empty_like(a)
            out[:, 1:] = a[:, :-1]
            out[:, 0] = a[:, 0]
            return out

        def score(pv_, ps_):
            sf = spec_feats(pv_, ps_)
            xn = np.concatenate([sf, hist_feats(kms, pv_, ps_)])[None]
            p_ = pick(fam.predict(xn, lin_feats(pv_, ps_)[None], only=set(best)), best)[0]
            return [float(v) for v in p_], float(d2(sf[None])[0])

        VAR = {}
        for i in te:
            pv0, ps0 = PV[i], PS[i]
            vs = {"original": (pv0, ps0), "resample": rows[i]["variants"]["resample"], "half": rows[i]["variants"]["half"],
                  "gain_0.85": (pv0 * 0.85, ps0 * 0.85), "gain_1.15": (pv0 * 1.15, ps0 * 1.15),
                  "noise_2pct": (pv0 + rngv.normal(0, 0.02 * float(pv0.mean()), pv0.shape).astype(np.float32),
                                 ps0 + rngv.normal(0, 0.02 * float(ps0.mean()), ps0.shape).astype(np.float32)),
                  "shift_1band": (shift1(pv0), shift1(ps0))}
            VAR[i] = {k: dict(zip(("pred", "ood_d2"), score(*v))) for k, v in vs.items()}
''')
rep('''            per[i] = {"sample": names[i], "unit": str(units[i]), "fold": fo, "pred": P[i].tolist(), "lo": lo_i.tolist(), "hi": hi_i.tolist(),''',
    '''            per[i] = {"sample": names[i], "unit": str(units[i]), "fold": fo, "pred": P[i].tolist(), "lo": lo_i.tolist(), "hi": hi_i.tolist(),
                      "variants": VAR[i], "ood_p95": p95, "ood_p99": p99,''')
rep('''            if names[i] in showcase and len(rows[i]["cubes"]) == 2:''', '''            if False:  # v9 exports no showcase cubes''')
rep('"hidsag_v6_results.json"', '"hidsag_v9_robust_results.json"', count=2)
rep('"version": "v6"', '"version": "v9-robustness"')
out = Path(__file__).resolve().parent / "run_v9_robust.py"
out.write_text(s, encoding="utf-8")
print("wrote", out, len(s))
