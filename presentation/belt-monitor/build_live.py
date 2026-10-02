"""Assemble presentation/belt-monitor/live/ for REEFPRINT Live (belt-monitor v3) from the measured outputs.

Inputs (all produced by code in training/):
  hidsag-v6-live-20261001/output/{hidsag_v6_results.json, showcase/}   T1 belt replay (deployable model, 80% intervals)
  hidsag-v6-live-20261001/{analysis_v6.json, mineral1_q2.json}         evidence bar per target
  plant-softsensor-20261001/{results.json, app_series_h1.json, app_series_h3.json}   T3 real plant
  bushveld-xrf-pge-20261001/{results.json, app_bushveld.json}          T4 Bushveld chemistry -> PGE
Outputs: live/summary.json, live/targets.json (versioned target registry), live/showcase/*, live/plant_h*.json,
live/bushveld.json, live/samples/*.csv (lab import files built from the real lab values, plus a deliberately bad
file for the refusal path). Every source file is hashed into summary.json (provenance).
"""
import csv, hashlib, json, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.normpath(os.path.join(HERE, "..", ".."))
T = os.path.join(R, "training")
LIVE = os.path.join(HERE, "live")
SRC = {"v6_results": os.path.join(T, "hidsag-v6-live-20261001", "output", "hidsag_v6_results.json"),
       "v6_analysis": os.path.join(T, "hidsag-v6-live-20261001", "analysis_v6.json"),
       "mineral1_q2": os.path.join(T, "hidsag-v6-live-20261001", "mineral1_q2.json"),
       "plant_results": os.path.join(T, "plant-softsensor-20261001", "results.json"),
       "plant_h1": os.path.join(T, "plant-softsensor-20261001", "app_series_h1.json"),
       "plant_h3": os.path.join(T, "plant-softsensor-20261001", "app_series_h3.json"),
       "bushveld_results": os.path.join(T, "bushveld-xrf-pge-20261001", "results.json"),
       "bushveld_app": os.path.join(T, "bushveld-xrf-pge-20261001", "app_bushveld.json"),
       "plan_review_log": os.path.join(R, "PLAN-live-v6-REVIEW-LOG.md"),
       "value_chain": os.path.join(T, "value-chain-20261002", "results.json"),
       "economics": os.path.join(T, "economics-20261002", "results.json")}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


os.makedirs(LIVE, exist_ok=True)
hashes = {k: sha(p) for k, p in SRC.items()}
A = json.load(open(SRC["v6_analysis"]))
Q2 = json.load(open(SRC["mineral1_q2"]))
V6 = json.load(open(SRC["v6_results"]))
PL = json.load(open(SRC["plant_results"]))
BV = json.load(open(SRC["bushveld_results"]))
BVA = json.load(open(SRC["bushveld_app"]))

# ---------------- showcase (T1)
dst = os.path.join(LIVE, "showcase")
if os.path.exists(dst):
    shutil.rmtree(dst)
shutil.copytree(os.path.join(T, "hidsag-v6-live-20261001", "output", "showcase"), dst)
show = {rec: sorted(f[:-5] for f in os.listdir(os.path.join(dst, rec)) if f.endswith(".json")) for rec in os.listdir(dst)}
# Display assets at full resolution (export_hr.py, Kaggle reefprint-hidsag-showcase-hr): same pre-registered samples, no 2x
# downsample, uint8 per band. Predictions, intervals, decisions and explanations stay v6's out-of-fold values.
HR = os.path.join(T, "hidsag-v6-live-20261001", "export_hr", "out", "showcase_hr")
n_hr = 0
for rec in show:
    for s in show[rec]:
        hj, hb = os.path.join(HR, rec, s + ".json"), os.path.join(HR, rec, s + ".bin.gz")
        if not (os.path.exists(hj) and os.path.exists(hb)):
            continue
        h6, hr = json.load(open(os.path.join(dst, rec, s + ".json"))), json.load(open(hj))
        h6["arrays"] = hr["arrays"]
        for k in ("vnir_low_wavelengths", "swir_low_wavelengths", "encoding", "clusters"):
            h6[k] = hr[k]
        h6["resolution"] = "full HIDSAG low product (5% border crop); v6 predictions unchanged"
        json.dump(h6, open(os.path.join(dst, rec, s + ".json"), "w"))
        shutil.copyfile(hb, os.path.join(dst, rec, s + ".bin.gz"))
        n_hr += 1
print("full-resolution display cubes merged:", n_hr)

# evidence bar per target: used in decisions only if the deployable model beat the strongest baseline (all gates)
evidence = {}
for rec, Rr in A["records"].items():
    evidence[rec] = {}
    for k, x in Rr["targets"].items():
        evidence[rec][k] = {"r2_deployable": x["r2_deployable"], "r2_full_refit": x["r2_full_refit"], "r2_v5": x.get("r2_v5"),
                            "r2_rgb": x["r2_rgb"], "strongest_baseline": x["strongest_baseline"],
                            "vs_baseline": x["vs_baseline"]["verdict"], "vs_v5": x.get("vs_v5", {}).get("verdict"),
                            "hs_vs_rgb": x["hs_vs_rgb"]["verdict"], "coverage": x["coverage_units"], "coverage_ci95": x["coverage_ci95"],
                            "median_width": x["median_width"], "used_in_decision": x["vs_baseline"]["verdict"] == "better"}
q2 = Q2["targets"]
for k in evidence.get("MINERAL1", {}):
    if k in q2:
        evidence["MINERAL1"][k]["spectrum_adds_over_metadata"] = q2[k]["gate"]["verdict"]
        evidence["MINERAL1"][k]["r2_size_fraction_lookup"] = q2[k]["r2_lookup"]

# ---------------- target registry (versioned)
UNITS = {"Cu rec": ("recovery_%", "%"), "Mo rec": ("recovery_%", "%"), "Lime cons": ("reagent_kg_per_t", "kg/t"),
         "PH": ("ph", "pH"), "WI": ("work_index_kWh_per_t", "kWh/t")}
reg = {"version": "2026-10-01.1", "targets": []}
for k, (atype, unit) in UNITS.items():
    reg["targets"].append({"id": f"GEOMET:{k}", "record": "GEOMET", "analyte_type": atype, "unit": unit,
                           "units_accepted": {unit: 1.0, **({"g/t": 0.001} if unit == "kg/t" else {})}, "basis": "dry_mass", "size_fraction": "none"})
for k in V6["records"]["MINERAL1"]["targets"]:
    reg["targets"].append({"id": f"MINERAL1:{k}", "record": "MINERAL1", "analyte_type": "mineral_wt%", "unit": "wt%",
                           "units_accepted": {"wt%": 1.0, "%": 1.0}, "basis": "dry_mass", "size_fraction": "from_sample"})
for k in ["Pt_ICP_ppm", "Pd_ICP_ppm", "Rh_ICP_ppm", "4E_ppm"]:
    reg["targets"].append({"id": f"BUSHVELD:{k}", "record": "BUSHVELD", "analyte_type": "element_g_per_t", "unit": "g/t",
                           "units_accepted": {"g/t": 1.0, "ppm": 1.0, "ppb": 0.001}, "basis": "dry_mass", "size_fraction": "none"})
for k in ["Cr2O3_%", "FeO_%", "SiO2_%", "MgO_%", "Al2O3_%", "CaO_%"]:
    reg["targets"].append({"id": f"BUSHVELD:{k}", "record": "BUSHVELD", "analyte_type": "oxide_wt%", "unit": "wt%",
                           "units_accepted": {"wt%": 1.0, "%": 1.0}, "basis": "dry_mass", "size_fraction": "none"})
json.dump(reg, open(os.path.join(LIVE, "targets.json"), "w"), indent=1)

# ---------------- plant + bushveld copies
for k in ("plant_h1", "plant_h3"):
    shutil.copy(SRC[k], os.path.join(LIVE, k.replace("plant_", "plant_") + ".json"))
shutil.copy(SRC["bushveld_app"], os.path.join(LIVE, "bushveld.json"))

# ---------------- lab import samples (real lab values; retrospective)
sd = os.path.join(LIVE, "samples")
os.makedirs(sd, exist_ok=True)
Yg = V6["records"]["GEOMET"]
keep = Yg["targets"]
idx = {s["sample"]: i for i, s in enumerate(Yg["samples"])}
with open(os.path.join(sd, "lab_GEOMET_showcase.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["sample_id", "target_id", "value", "unit", "basis", "size_fraction", "revision", "timestamp"])
    for s in show.get("GEOMET", []):
        i = idx[s]
        for t, k in enumerate(keep):
            w.writerow([s, f"GEOMET:{k}", round(Yg["Y"][i][t], 4), UNITS[k][1], "dry_mass", "none", 1, "2026-10-01T08:00:00"])
rows = BVA["rows"]
with open(os.path.join(sd, "assay_BUSHVELD_icp.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["sample_id", "target_id", "value", "unit", "basis", "size_fraction", "revision", "timestamp"])
    for r in rows[:120]:
        sid = f"{r['bh']}@{r['from']:.2f}-{r['to']:.2f}"
        for k in ["Pt_ICP_ppm", "Rh_ICP_ppm", "4E_ppm"]:
            w.writerow([sid, f"BUSHVELD:{k}", r["pge"][k]["true"], "g/t", "dry_mass", "none", 1, "2026-10-01T08:00:00"])
with open(os.path.join(sd, "BAD_mixed_import.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["sample_id", "target_id", "value", "unit", "basis", "size_fraction", "revision", "timestamp"])
    s0 = show["GEOMET"][0]
    w.writerow([s0, "GEOMET:WI", 13.2, "kWh/t", "dry_mass", "none", 1, "2026-10-01T08:00:00"])
    w.writerow([s0, "GEOMET:WI", 13.4, "kWh/t", "dry_mass", "none", 1, "2026-10-01T08:00:00"])          # duplicate revision
    w.writerow([s0, "GEOMET:Cu rec", 88, "kg/t", "dry_mass", "none", 1, "2026-10-01T08:00:00"])        # wrong unit
    w.writerow([s0, "GEOMET:Lime cons", 0.2, "kg/t", "wet_mass", "none", 1, "2026-10-01T08:00:00"])    # wrong basis
    w.writerow(["NOT-A-SAMPLE", "GEOMET:WI", 12, "kWh/t", "dry_mass", "none", 1, "2026-10-01T08:00:00"])  # unknown sample
    w.writerow([s0, "XRD:quartz", 31, "wt%", "dry_mass", "none", 1, "2026-10-01T08:00:00"])           # unknown target
    w.writerow([s0, "GEOMET:Mo rec", "=HYPERLINK(\"x\")", "%", "dry_mass", "none", 1, "2026-10-01T08:00:00"])  # formula
    w.writerow([s0, "GEOMET:Cu rec", "", "%", "dry_mass", "none", 1, "2026-10-01T08:00:00"])                    # blank is not zero
    w.writerow([s0, "GEOMET:PH", 8.1, "pH", "none", "none", 1, "not-a-time"])                                 # unreadable timestamp
with open(os.path.join(sd, "xrf_BUSHVELD_belt.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["sample_id", "target_id", "value", "unit", "basis", "size_fraction", "revision", "timestamp"])
    for r in rows[120:160]:
        sid = f"{r['bh']}@{r['from']:.2f}-{r['to']:.2f}"
        for k, v in r["ox"].items():
            w.writerow([sid, f"BUSHVELD:{k}", v, "wt%", "dry_mass", "none", 1, "2026-10-01T08:00:00"])

# ---------------- summary
pl = {f"delay{r['delay_h']}_h{r['horizon_h']}": {"model": r["model"], **{k: r["test"][k] for k in ("mae_model", "mae_persistence", "mae_mean", "verdict", "coverage", "coverage_ci95_block", "width", "strongest_baseline")}, "n_test": r["n"]["test"]} for r in PL["runs"]}
summary = {"built": "2026-10-02", "hashes_sha256": hashes, "showcase": show, "evidence": evidence, "value": json.load(open(SRC["value_chain"])), "economics": json.load(open(SRC["economics"], encoding="utf-8")),
           "v6_records": {rec: {"n": A["records"][rec]["n"], "n_units": A["records"][rec]["n_units"], "ood": A["records"][rec]["ood"],
                                "calibration": A["records"][rec]["calibration"], "blends": A["records"][rec]["blends"] and {k: v for k, v in A["records"][rec]["blends"].items() if k != "targets"}}
                          for rec in A["records"]},
           "plant": {"runs": pl, "assumptions": PL["assumptions"], "data": PL["data"]},
           "bushveld": {"data": BV["data"], "n_intervals": BV["n_intervals"], "n_projects": BV["n_projects"], "n_boreholes": BV["n_boreholes"],
                        "seam": BV["seam_classification"],
                        "targets": {t: {k: v for k, v in x.items() if k.startswith("r2") or k.startswith("coverage") or k.startswith("Q") or k.startswith("seam_only")} for t, x in BV["targets"].items()}},
           "pentlandite": (lambda d: {"pooled": d["pooled"], "per_section": {k: {m: v[m]["pn_iou"] for m in ("brightness only", "colour only", "colour + texture")} for k, v in d["per_section"].items()}, "val_sections": d["val_sections"], "train_sections": d["train_sections"]})(json.load(open(os.path.join(T, "pentlandite-diagnostic-20261001", "results.json")))),
           "policy": {"version": "belt-policy-1", "alpha": 0.2, "adverse": {"Cu rec": "low", "Mo rec": "low", "Lime cons": "high", "WI": "high", "PH": "none"},
                      "actions": {"Cu rec": "Send the sample to the microscope; review collector dose", "Mo rec": "Notify the moly circuit",
                                  "Lime cons": "Review lime pre-dosing", "WI": "Review feed rate with the control room"},
                      "ood": "pass <= calibration p95 < borderline <= p99 < refused"}}
def _clean(o):
    """JSON has no NaN/Infinity: undefined rates (e.g. precision of a class never predicted) become null."""
    if isinstance(o, float) and (o != o or o in (float("inf"), float("-inf"))):
        return None
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_clean(v) for v in o]
    return o


# Hash every file shipped in live/ (except summary.json itself), so "every source is hashed" is literally true.
summary["shipped_assets_sha256"] = {os.path.relpath(os.path.join(dp, f), LIVE).replace(os.sep, "/"): sha(os.path.join(dp, f))
                                    for dp, _, fs in sorted(os.walk(LIVE)) for f in sorted(fs) if f != "summary.json"}
json.dump(_clean(summary), open(os.path.join(LIVE, "summary.json"), "w"), indent=1, allow_nan=False)
size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(LIVE) for f in fs)
print("live/ built:", {k: len(v) for k, v in show.items()}, "showcase samples;", round(size / 1e6, 1), "MB total")
print("decision targets (beat strongest baseline):", {rec: [k for k, v in e.items() if v["used_in_decision"]] for rec, e in evidence.items()})
