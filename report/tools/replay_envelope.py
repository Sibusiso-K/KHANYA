"""Envelope-clipped feed-rate replay, bound to pinned inputs (report Section 4.2, v15).

Inputs: training/hidsag-v6-live-20261001/output/hidsag_v6_results.json and
training/hidsag-v8-model-20261002/output/hidsag_v8_model_results.json at commit
ab333071d184fa8f853ea96e78fd81a2f948d547 (branch codex/pwa-phase-roadmap), read with `git show`.

Policy: the deployed policy of training/value-chain-20261002/value_chain.py (refused -> fold P90;
borderline -> max(bound, P90); pass -> one-sided 90% bound), then the feed is clipped to the
85-110% demonstration envelope, i.e. the hardness used is clipped to [P90/1.10, P90/0.85].
Throughput vs blind P90 = sum(P90)/sum(Wi_used) - 1 (equal-mass parcels).
Interval: the same cluster bootstrap as value_chain.py (units = samples, B = 4000, seed = 1,
2.5/97.5 percentiles). Run from the repository root: py -3 report/tools/replay_envelope.py
"""
import json, subprocess
import numpy as np

COMMIT = "ab333071d184fa8f853ea96e78fd81a2f948d547"


def load(path):
    return json.loads(subprocess.check_output(["git", "show", f"{COMMIT}:{path}"]))


def boot_ci(stat, units, B=4000, seed=1):
    rng = np.random.default_rng(seed)
    ug = np.unique(units)
    idx = {g: np.flatnonzero(units == g) for g in ug}
    v = [stat(np.concatenate([idx[ug[i]] for i in rng.integers(0, len(ug), len(ug))])) for _ in range(B)]
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]


R = load("training/hidsag-v6-live-20261001/output/hidsag_v6_results.json")["records"]["GEOMET"]
t = R["targets"].index("WI")
true = np.array(R["Y"], float)[:, t]
S = sorted(R["samples"], key=lambda r: r["sample"])
assert len(S) == len(true) == 146
fold = np.array([r["fold"] for r in S])
ood = np.array([r["ood"] for r in S])
units = np.array([r["sample"] for r in S])
p90 = np.array([np.percentile(true[fold != f], 90) for f in fold])
V8 = {r["sample"]: r for r in load("training/hidsag-v8-model-20261002/output/hidsag_v8_model_results.json")["records"]["GEOMET"]["samples"]}
ub90 = np.array([np.inf if V8[r["sample"]]["hi_up"][t] is None else V8[r["sample"]]["hi_up"][t] for r in S])
deployed = np.where(ood == "refused", p90, np.where(ood == "borderline", np.maximum(ub90, p90), ub90))
clipped = np.clip(deployed, p90 / 1.10, p90 / 0.85)


def gain(used, b=slice(None)):
    return float(p90[b].sum() / used[b].sum() - 1.0)


out = {"commit": COMMIT, "bootstrap": {"units": "samples", "B": 4000, "seed": 1, "interval": "percentile 2.5/97.5"}}
for name, used in (("deployed_unclipped", deployed), ("deployed_envelope_85_110", clipped)):
    out[name] = {"throughput_vs_blind_p90": gain(used),
                 "ci95": boot_ci(lambda b: gain(used, b), units),
                 "overload_share": float((true > used).mean())}
json.dump(out, open("report/evidence/replay_envelope.json", "w"), indent=2)
print(json.dumps(out, indent=2))
