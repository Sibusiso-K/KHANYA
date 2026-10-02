"""What the levers are worth, computed with provenance attached (rule 1 as a type: reefprint.quantity).

Every input is a Quantity: CITED only when the primary document was read (docs/17 tag [P]); search-summary and news
values ([S], [N]) enter as ASSUMED with the word "indicative" in the source, because the constitution says a value not
read from its source is not citable. Arithmetic keeps the WEAKEST provenance, so every output says honestly what it is.
Outputs are scenarios (formula x labelled inputs), not measured savings. The only MEASURED input is our own sim_ result.

Run: python training/economics-20261002/economics.py  -> results.json
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))
from reefprint.quantity import assumed, cited, measured  # noqa: E402

OZ = cited(31.1034768, "g/oz", "troy ounce definition")
PP = cited(0.01, "", "one percentage point")

# ---- prices and FX
basket_zar = cited(32611, "ZAR/oz", "Valterra Platinum annual results 2025 short form: average realised rand basket R32,611 per PGM ounce [P]")
basket_usd = cited(1852, "USD/oz", "Valterra Platinum annual results 2025 short form: average realised dollar basket $1,852 per PGM ounce [P]")
fx = basket_zar / basket_usd                                                       # implied ZAR per USD, same document
north_rev = assumed(47156, "ZAR/oz", "indicative [N]: Investing.com summary of Northam F2026 slides, Zondereinde revenue per equivalent refined 4E oz")

# ---- plants (scale)
zond_t = assumed(2247881, "t/yr", "indicative [S]: Northam annual integrated report F2025 via search, Zondereinde tonnes milled")
zond_g = assumed(4.72, "g/t", "indicative [S]: Northam annual integrated report F2025 via search, Zondereinde 4E mill head grade")
imp_t = assumed(26.29e6, "t/yr", "indicative [S]: Implats FY2025 tonnes milled, managed operations, via search")
imp_g = assumed(4.0, "g/t", "ASSUMED for illustration: no verified Implats group head grade was read")
mog_t = assumed(14.7e6, "t/yr", "indicative [S]: Valterra 2025, Mogalakwena record tonnes milled, via search")
mog_g = assumed(2.5, "g/t", "ASSUMED for illustration: Mogalakwena built-up head grade not read from a primary source")
rec_ug2 = assumed(0.79, "", "indicative [S]: Implats fact sheet via search, UG2 concentrator recovery about 79%")

# ---- our own measured result and Mintek testwork
tput = measured(0.0201, "", "sim_ feed-rate policy on 146 real HIDSAG out-of-fold predictions (training/value-chain-20261002/results.json)")
tput_lo = measured(0.0096, "", "lower 95% CI of the same sim_ result")
tput_hi = measured(0.0301, "", "upper 95% CI of the same sim_ result")
cr_gap = cited(3.0, "", "Jones (Mintek) 2005: UG2 concentrate 87% recovery at 2.9% Cr2O3; 'more than 90 per cent' if Cr2O3 relaxed to 4-10% [P] (lower bound of the gap, in percentage points)")

# ---- lab
qem = cited(1500, "CAD/sample", "Saskatchewan Research Council QEMSCAN price list 4/2017: liberation analysis with predicted recovery [P]")
mount = cited(150, "CAD/sample", "SRC 4/2017: 30 mm block mount [P]")
shifts = cited(3 * 365, "samples/yr", "24/7 operation, three shifts a day, one composite per stream per shift")
assay_lag_lo = assumed(24, "h", "indicative [S]: 4E fire assay turnaround in practice 24-72 h")
assay_lag_hi = assumed(72, "h", "indicative [S]: 4E fire assay turnaround in practice 24-72 h")
hours = cited(8760, "h/yr", "hours in a year")


def oz_per_pp(t, g):
    """Contained 4E ounces gained by one percentage point of concentrator recovery."""
    return t * g * PP / OZ


def q(x):
    return {"value": x.value, "unit": x.unit, "provenance": x.provenance.name, "sources": list(x.all_sources)}


def money(x_zar):
    usd = x_zar / fx
    return {"zar": q(x_zar), "usd": q(usd)}


R = {"note": __doc__.split("\n\n")[0], "fx_zar_per_usd_implied": q(fx)}

# E1  one percentage point of recovery
e1 = {}
for name, t, g in (("zondereinde_scale", zond_t, zond_g), ("implats_group_scale", imp_t, imp_g), ("per_1Mt_at_4.72gpt", assumed(1e6, "t/yr", "normalisation: one million tonnes milled per year"), zond_g)):
    oz = oz_per_pp(t, g)
    e1[name] = {"oz_per_pp_per_yr": q(oz), "value_per_pp_per_yr_valterra_basket": money(oz * basket_zar)}
e1["zondereinde_scale"]["value_per_pp_per_yr_northam_rev_per_oz"] = money(oz_per_pp(zond_t, zond_g) * north_rev)
R["E1_one_recovery_point"] = e1

# E2  the chrome-constraint recovery gap (>= 3 pp) on a UG2 plant the size of Zondereinde
e2_oz = oz_per_pp(zond_t, zond_g) * cr_gap
R["E2_chrome_constraint_gap_zondereinde_scale"] = {"oz_per_yr": q(e2_oz), "value_per_yr": money(e2_oz * basket_zar),
    "reading": "upper bound of what better chromite control is worth if the whole Mintek testwork gap were bought back; partial capture is the realistic case"}

# E3  measured sim_ throughput gain at a mill-constrained plant (Mogalakwena scale)
e3 = {}
for lab, f in (("point", tput), ("ci_low", tput_lo), ("ci_high", tput_hi)):
    extra_t = mog_t * f
    oz = extra_t * mog_g / OZ * rec_ug2  # recovery assumption is labelled; Platreef recovery not read
    e3[lab] = {"extra_tonnes_per_yr": q(extra_t), "extra_oz_per_yr": q(oz), "value_per_yr": money(oz * basket_zar)}
R["E3_throughput_mill_constrained_mogalakwena_scale"] = {**e3, "transfer_caveat": "HIDSAG is Chilean Cu-Mo; the +2.0% is a method result, not a Platreef measurement"}

# E4  what shift-speed QEMSCAN would cost (why prediction, not more QEMSCAN)
per_stream = (qem + mount) * shifts
R["E4_qemscan_every_shift"] = {"per_stream_per_yr": q(per_stream), "three_streams_feed_conc_tails": q(per_stream * cited(3, "", "feed, concentrate, tails")),
                               "reading": "still days late: price buys truth, not speed"}

# E5  ore processed blind before the assay returns (exposure, not a loss)
tph = zond_t / hours
for lab, lag in (("24h", assay_lag_lo), ("72h", assay_lag_hi)):
    tonnes = tph * lag
    oz = tonnes * zond_g / OZ
    R.setdefault("E5_processed_before_assay_returns_zondereinde_scale", {})[lab] = {"tonnes": q(tonnes), "contained_oz": q(oz), "contained_value": money(oz * basket_zar)}

# E6  Stokes equal-settling: chromite settles like a coarser silicate, so cyclones send it back to the mill
rho_c = assumed(4.5, "g/cm3", "textbook range 4.3-4.8 for chromite (ASSUMED midpoint)")
rho_s = assumed(3.0, "g/cm3", "textbook range 2.7-3.3 for pyroxene/plagioclase gangue (ASSUMED midpoint)")
rho_w = cited(1.0, "g/cm3", "water")
ratio = math.sqrt(((rho_c - rho_w) / (rho_s - rho_w)).value)
R["E6_stokes_equal_settling"] = {"silicate_size_equivalent_to_1um_chromite": {"value": ratio, "unit": "um per um", "provenance": "ASSUMED",
                                 "sources": list(((rho_c - rho_w) / (rho_s - rho_w)).all_sources) + ["Stokes' law: v ∝ (ρs-ρw)·d²"]},
                                 "reading": f"a {round(50 * ratio)} µm silicate settles like a 50 µm chromite, so chromite is classified as 'coarse' and returns to the mill until it is finer: over-grinding, fines, entrainment"}

json.dump(R, open(os.path.join(HERE, "results.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def show(label, m):
    print(f"{label:62s} R{m['zar']['value']:>16,.0f}   US${m['usd']['value']:>14,.0f}   [{m['zar']['provenance']}]")


print(f"implied FX {fx.value:.2f} ZAR/USD [{fx.provenance.name}]")
for k, v in e1.items():
    show(f"E1 +1 pp recovery, {k} ({v['oz_per_pp_per_yr']['value']:,.0f} oz/yr)", v["value_per_pp_per_yr_valterra_basket"])
show("E1 +1 pp, zondereinde, at Northam revenue per oz", e1["zondereinde_scale"]["value_per_pp_per_yr_northam_rev_per_oz"])
show(f"E2 chrome-constraint gap >=3 pp, zondereinde scale ({e2_oz.value:,.0f} oz)", R["E2_chrome_constraint_gap_zondereinde_scale"]["value_per_yr"])
for lab, v in e3.items():
    show(f"E3 throughput {lab} ({v['extra_tonnes_per_yr']['value']:,.0f} t/yr)", v["value_per_yr"])
print(f"E4 QEMSCAN every shift per stream: CAD {per_stream.value:,.0f}/yr; three streams CAD {per_stream.value * 3:,.0f}/yr [{per_stream.provenance.name}]")
for lab, v in R["E5_processed_before_assay_returns_zondereinde_scale"].items():
    show(f"E5 processed blind before assay ({lab}): {v['tonnes']['value']:,.0f} t", v["contained_value"])
print(f"E6 Stokes: 50 µm chromite settles like {50 * ratio:.0f} µm silicate (ratio {ratio:.2f}) [ASSUMED densities]")
