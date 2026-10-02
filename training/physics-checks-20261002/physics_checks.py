"""Physical-possibility checks for the claims, computed (code does the arithmetic) with labelled assumptions.

K1  Flotation kinetics vs throughput. More tonnes through the same cells means shorter residence time. Using the
    first-order kinetics curve on slide 16 (Mintek kinetics framework, Moodley/Govender et al., applied to KHANYA's
    test_11 liberation classes: presentation/deck-src/kinetics_test11.json), fit R(t) = Rf(1-exp(-kf t)) + Rs(1-exp(-ks t))
    and compute the recovery lost when residence time falls by the throughput factor (1 + 1.9%). Plant residence time in
    lab-equivalent minutes is ASSUMED (lab-to-plant scale-up varies), so several are shown.
L1  Load curtailment (a candidate claim, tested and REJECTED). Eskom's mining curtailment: 20% of contracted supply for 10 h (14:00-24:00) at stage 6 [S]. If the
    mill is power-limited, tonnes = power / specific energy (Bond: proportional to Wi). With belt hardness known before
    reclaim (ROM / stockpile placement), the plant can send the softest parcels through during the curtailed window.
    Evaluated on the 146 REAL HIDSAG parcels: chosen by PREDICTED (out-of-fold) Wi, scored with TRUE Wi. sim_.
Run: python training/physics-checks-20261002/physics_checks.py -> results.json
"""
import json, math, os
import numpy as np
from scipy.optimize import curve_fit

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.normpath(os.path.join(HERE, "..", ".."))
out = {"note": __doc__.split("\n\n")[0]}

# ---------------- K1 kinetics
K = json.load(open(os.path.join(R, "presentation", "deck-src", "kinetics_test11.json")))
t = np.array([float(k) for k in K["R"]])
r = np.array([K["R"][k] for k in K["R"]])


def two_comp(x, rf, kf, rs, ks):
    return rf * (1 - np.exp(-kf * x)) + rs * (1 - np.exp(-ks * x))


p, _ = curve_fit(two_comp, t, r, p0=[0.7, 3.0, 0.25, 0.5], bounds=([0, 0, 0, 0], [1, 50, 1, 50]), maxfev=20000)
fit_rmse = float(np.sqrt(np.mean((two_comp(t, *p) - r) ** 2)))
gain = 0.0193   # measured sim_ throughput gain of the deployed policy (training/value-chain-20261002/results.json)
rows = []
for tau in (1.0, 2.0, 3.0, 5.0, 7.0, 10.0):
    r0, r1 = two_comp(tau, *p), two_comp(tau / (1 + gain), *p)
    rows.append({"residence_lab_equiv_min": tau, "recovery": round(float(r0), 4), "recovery_after_gain": round(float(r1), 4),
                 "recovery_loss_pp": round(float((r0 - r1) * 100), 3)})
out["K1_kinetics_vs_throughput"] = {
    "fit": {"Rf": p[0], "kf_per_min": p[1], "Rs": p[2], "ks_per_min": p[3], "rmse": fit_rmse},
    "source": "presentation/deck-src/kinetics_test11.json (slide 16: Mintek kinetics framework applied to KHANYA test_11 liberation)",
    "throughput_gain": gain, "rows": rows,
    "reading": "near the plateau the recovery cost of +1.9% tonnes is negligible; on the steep part of the curve it is not. A plant must know where its cells sit; the advice must check flotation residence time before raising feed.",
    "assumption": "ASSUMED lab-to-plant residence mapping; the curve is a modelled one (liberation classes x published rate constants), not a plant measurement"}

# ---------------- L1 load curtailment
V6 = json.load(open(os.path.join(R, "training", "hidsag-v6-live-20261001", "output", "hidsag_v6_results.json")))["records"]["GEOMET"]
ti = V6["targets"].index("WI")
S = sorted(V6["samples"], key=lambda s: s["sample"])
wi_true = np.array(V6["Y"], float)[:, ti]
wi_pred = np.array([s["pred"][ti] for s in S])
CUT, HOURS_CUT, DAY = 0.20, 10.0, 24.0


def day_tonnes(order_cut, order_rest, wi):
    """Equal-mass parcels; power P=1 normal, (1-CUT) in the window. Fill the window from order_cut, the rest from order_rest.
    Returns tonnes milled in a day relative to an uncurtailed day at the mean hardness."""
    e = wi / wi.mean()                      # relative energy per tonne (Bond: proportional to Wi at fixed F80/P80)
    budget_cut, budget_rest = (1 - CUT) * HOURS_CUT, DAY - HOURS_CUT     # energy units (P x hours)
    tonnes, used = 0.0, set()
    for budget, order in ((budget_cut, order_cut), (budget_rest, order_rest)):
        for i in order:
            if i in used:
                continue
            per = e[i] * 1.0                # energy to mill one tonne-unit of parcel i
            if budget <= 0:
                break
            take = min(1.0, budget / per)   # parcels are 1 tonne-unit each; partial at the end
            tonnes += take
            budget -= take * per
            used.add(i)
    return tonnes


rng = np.random.default_rng(3)
res = []
for rep in range(500):
    pool = rng.choice(len(wi_true), 60, replace=False)   # a day's reclaimable parcels (ASSUMED 60 equal parcels available)
    blind = list(rng.permutation(pool))
    soft_first = list(pool[np.argsort(wi_pred[pool])])     # by PREDICTED hardness
    hard_rest = soft_first[::-1]
    t_blind = day_tonnes(blind, blind, wi_true)
    t_belt = day_tonnes(soft_first, hard_rest, wi_true)
    t_oracle = day_tonnes(list(pool[np.argsort(wi_true[pool])]), list(pool[np.argsort(-wi_true[pool])]), wi_true)
    res.append((t_belt / t_blind - 1, t_oracle / t_blind - 1))
res = np.array(res)
uncut = DAY / 1.0
out["L1_load_curtailment"] = {
    "regime": "Eskom mining curtailment at stage 6: 20% of contracted supply for 10 h (14:00-24:00) [S]",
    "sim_gain_tonnes_belt_vs_blind_mean": float(res[:, 0].mean()), "sim_gain_p05_p95": [float(np.percentile(res[:, 0], 5)), float(np.percentile(res[:, 0], 95))],
    "sim_gain_oracle_mean": float(res[:, 1].mean()),
    "day_capacity_lost_to_curtailment_pct": round(CUT * HOURS_CUT / DAY * 100, 2),
    "assumptions": ["ASSUMED: the mill is power-limited and curtailment cuts mill power by the full 20% (mines usually shed other loads first, which makes this an upper bound on the problem)",
                    "ASSUMED: stockpile/ROM reclaim can choose parcels (belt at reclaim, not only at mill feed) and parcels are of equal mass",
                    "ASSUMED: Bond energy proportional to Wi at fixed grind; 60 reclaimable parcels per day drawn from the 146 real ones (500 repeats)",
                    "Selection uses out-of-fold PREDICTED Wi; tonnes are computed with TRUE Wi"],
    "verdict": "REJECTED as a tonnage claim",
    "reading": "Re-ordering ore cannot create tonnes: over a cycle the energy needed for all the ore is fixed, so sending soft ore through the curtailed window only defers the hard ore (the simulation loses tonnes, and so does an oracle). REEFPRINT does NOT claim a curtailment throughput gain. Its real roles under curtailment: (1) set the feed for the reduced power from the hardness bound, so the grind holds when power drops; (2) forecast the tonnes the window will lose from the hardness of the ore about to be reclaimed, for production planning."}
json.dump(out, open(os.path.join(HERE, "results.json"), "w"), indent=1)
k = out["K1_kinetics_vs_throughput"]
print("K1 fit:", {a: round(b, 3) for a, b in k["fit"].items()})
for row in rows:
    print(f"  tau {row['residence_lab_equiv_min']:>4} min: R {row['recovery']:.4f} -> {row['recovery_after_gain']:.4f}  loss {row['recovery_loss_pp']:.3f} pp")
l = out["L1_load_curtailment"]
print(f"L1 curtailment day: capacity lost {l['day_capacity_lost_to_curtailment_pct']}% of the day's energy; belt scheduling gains {l['sim_gain_tonnes_belt_vs_blind_mean']*100:+.2f}% tonnes "
      f"(p5-p95 {l['sim_gain_p05_p95'][0]*100:+.2f} to {l['sim_gain_p05_p95'][1]*100:+.2f}%), oracle {l['sim_gain_oracle_mean']*100:+.2f}%")
