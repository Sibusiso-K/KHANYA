"""What the levers could be worth: scenario arithmetic with provenance attached (rule 1 as a type: reefprint.quantity).

Revised after ClauDex round 1 (PLAN-v8-REVIEW-LOG.md, findings 20-24):
  * one stated valuation basis per scenario: contained 4E oz x ASSUMED payability x ASSUMED net 4E price, FX dated apart;
  * no gross "opportunity" headline: recovery value is net payable revenue; throughput is incremental CONTRIBUTION and
    only where the mill is the bottleneck; the Cr2O3 trade-off (Jones 2005) is evidence of a trade-off, not money;
  * break-even = (annualised installed capex + annual opex) / (net value per recovery pp), across a capex grid,
    because capex is unquoted (every capex number here is ASSUMED, "quote required");
  * provenance fixed: sampling cadence is ASSUMED; QEMSCAN price is CAD, 2017, a Canadian lab, excluding preparation.
CITED only when the primary document was read ([P] in docs/17). [S]/[N] inputs enter as ASSUMED ("indicative").
Nothing here is a measured saving. The only MEASURED input is our own sim_ result, itself under revision (PLAN-v8 step 1).

Run: python training/economics-20261002/economics.py  -> results.json
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))
from reefprint.quantity import assumed, cited, measured  # noqa: E402

OZ = cited(31.1034768, "g/oz", "troy ounce definition")
PP = cited(0.01, "", "one percentage point")
ONE = cited(1.0, "", "unity")

# ---- valuation basis (one per scenario; all ASSUMED because no site's net payable terms were read)
PRICE = {"low": assumed(25000, "ZAR/oz", "ASSUMED low net 4E price"),
         "base": assumed(32611, "ZAR/oz", "ASSUMED: Valterra 2025 realised rand PGM basket R32,611/oz [P] used as a proxy for a net 4E price (baskets differ)"),
         "high": assumed(47156, "ZAR/oz", "ASSUMED: Northam Zondereinde revenue per equivalent refined 4E oz F2026, indicative [N]")}
PAY = {"low": assumed(0.75, "", "ASSUMED payability (smelting/refining losses and charges, toll terms)"),
       "base": assumed(0.85, "", "ASSUMED payability"),
       "high": assumed(0.95, "", "ASSUMED payability")}
FX = assumed(17.61, "ZAR/USD", "ASSUMED: implied by Valterra 2025 rand/dollar basket ratio (R32,611 / $1,852) [P]; not an independently dated FX rate")

# ---- plant scale
zond_t = assumed(2247881, "t/yr", "indicative [S]: Northam F2025, Zondereinde tonnes milled")
zond_g = assumed(4.72, "g/t", "indicative [S]: Northam F2025, Zondereinde 4E mill head grade")
imp_t = assumed(26.29e6, "t/yr", "indicative [S]: Implats FY2025 tonnes milled, managed operations")
imp_g = assumed(4.0, "g/t", "ASSUMED for illustration: no verified Implats group head grade was read")
mog_t = assumed(14.7e6, "t/yr", "indicative [S]: Valterra 2025, Mogalakwena record tonnes milled")
mog_g = assumed(2.5, "g/t", "ASSUMED for illustration: Mogalakwena built-up head grade not read from a primary source")
rec_mog = assumed(0.79, "", "ASSUMED: Implats UG2 recovery (~79%, Impala fact sheet 2018 [P]) used as a stand-in; Platreef recovery not read")

# ---- our own result (under revision) and Mintek testwork
tput = measured(0.0201, "", "sim_ feed-rate policy on 146 real HIDSAG out-of-fold predictions (docs/16); under revision: the 'same risk' claim is withdrawn pending CV+ and non-inferiority")

# ---- lab
qem = cited(1500, "CAD/sample", "Saskatchewan Research Council QEMSCAN price list 4/2017 (Canadian lab, CAD, 2017): liberation analysis with predicted recovery [P]")
mount = cited(150, "CAD/sample", "SRC 4/2017: 30 mm block mount [P]")
prep = cited(800, "CAD/sample", "SRC 4/2017: crush, grind and sieve test samples [P]")
cadence = assumed(3 * 365, "samples/yr", "ASSUMED cadence: one composite per stream per shift, three shifts, every day")
lag = {"24h": assumed(24, "h", "indicative [S]: 4E fire assay turnaround in practice 24-72 h"),
       "72h": assumed(72, "h", "indicative [S]: 4E fire assay turnaround in practice 24-72 h")}
HOURS = cited(8760, "h/yr", "hours in a year")

# ---- ownership cost grid (no quotes exist; ASSUMED; the conclusion is tested for insensitivity across the grid)
CAPEX_USD = [assumed(v, "USD", f"ASSUMED installed capex scenario US${v:,.0f}: cameras (SWIR class US$50k-300k [S]), optics, enclosure, lighting, encoder, edge PC, integration, commissioning; quote required")
             for v in (0.5e6, 1.5e6, 3.0e6)]
OPEX_USD = [assumed(v, "USD", f"ASSUMED annual opex (per year) US${v:,.0f}: sampling, assays, Bond tests, maintenance, spares, purge air, lamps, software support; quote required")
            for v in (0.1e6, 0.3e6, 0.6e6)]
YEARS, RATE = 5, 0.10
CRF = assumed(RATE * (1 + RATE) ** YEARS / ((1 + RATE) ** YEARS - 1), "", f"ASSUMED capital recovery factor (per year), {YEARS} years at {RATE:.0%}")


def q(x):
    return {"value": x.value, "unit": x.unit, "provenance": x.provenance.name, "sources": list(x.all_sources)}


def net_value_per_pp(t, g, sc):
    """Net payable value of one percentage point of concentrator recovery, per year, in ZAR."""
    return t * g * PP / OZ * PAY[sc] * PRICE[sc]


R = {"note": __doc__.split("\n\n")[0], "basis": "contained 4E oz x ASSUMED payability x ASSUMED net 4E price; FX separate", "fx": q(FX)}

# V1 one percentage point of recovery, net payable, three valuation scenarios
R["V1_net_value_per_recovery_pp_per_yr"] = {name: {sc: q(net_value_per_pp(t, g, sc)) for sc in PRICE}
                                            for name, t, g in (("zondereinde_scale", zond_t, zond_g), ("implats_group_scale", imp_t, imp_g))}

# V2 throughput, ONLY for a mill-constrained plant: extra tonnes and revenue per tonne; contribution needs the site's variable cost
extra_t = mog_t * tput
rev_per_t = {sc: mog_g * rec_mog * PAY[sc] * PRICE[sc] / OZ for sc in PRICE}
R["V2_throughput_mill_constrained_only"] = {
    "extra_tonnes_per_yr": q(extra_t),
    "net_revenue_per_extra_tonne": {sc: q(v) for sc, v in rev_per_t.items()},
    "contribution_per_yr_if_variable_cost_is_fraction_of_revenue": {
        f"{int(f * 100)}pct": q(extra_t * rev_per_t["base"] * assumed(1 - f, "", f"ASSUMED incremental variable cost = {int(f * 100)}% of net revenue per tonne (mining/reclaim, milling, flotation, smelting/refining)"))
        for f in (0.25, 0.5, 0.75)},
    "zero_if": "the plant is ore-constrained (most underground PGM concentrators), or the extra tonnes move the bottleneck downstream",
    "transfer_caveat": "the +2.0% is a Chilean Cu-Mo drill-core result under revision; no confidence interval is transferred to rands"}

# V3 the Cr2O3 trade-off is evidence, not money
R["V3_cr2o3_tradeoff_evidence_only"] = {"jones_2005": "UG2 concentrate ~430 g/t at 87% recovery and 2.9% Cr2O3; >1000 g/t at >90% if Cr2O3 relaxed to 4-10% [P]",
                                        "reading": "recovery and concentrate quality trade off; better chromite control moves the operating point, by an amount only a pilot can measure"}

# V4 break-even recovery improvement across the capex/opex grid (Zondereinde scale, base valuation)
per_pp_usd = net_value_per_pp(zond_t, zond_g, "base") / FX
be = {}
for c in CAPEX_USD:
    for o in OPEX_USD:
        cost = c * CRF + o
        be[f"capex_{c.value / 1e6:.1f}M_opex_{o.value / 1e6:.1f}M"] = q(cost / per_pp_usd)
R["V4_breakeven_recovery_pp_zondereinde_scale_base"] = {"net_value_per_pp_usd": q(per_pp_usd), "breakeven_pp": be,
                                                        "formula": "(capex x CRF + opex) / net value per recovery pp"}

# V5 shift-speed QEMSCAN (why prediction, not more QEMSCAN)
per_stream = (qem + mount + prep) * cadence
R["V5_qemscan_every_shift"] = {"per_stream_per_yr_cad2017": q(per_stream), "reading": "a 2017 Canadian list price; a local quote is required; still days late"}

# V6 ore processed before the assay returns: exposure, not a loss
tph = zond_t / HOURS
R["V6_processed_before_assay_returns_zondereinde_scale"] = {k: {"tonnes": q(tph * v), "contained_oz": q(tph * v * zond_g / OZ)} for k, v in lag.items()}

# V7 Stokes equal-settling: a qualitative density-classification illustration, NOT a cyclone model
rho_c = assumed(4.5, "g/cm3", "textbook range 4.3-4.8 for chromite (ASSUMED midpoint)")
rho_s = assumed(3.0, "g/cm3", "textbook range 2.7-3.3 for silicate gangue (ASSUMED midpoint)")
ratio = ((rho_c - cited(1.0, "g/cm3", "water")) / (rho_s - cited(1.0, "g/cm3", "water"))).value ** 0.5
R["V7_stokes_illustration"] = {"equal_settling_size_ratio": ratio, "provenance": "ASSUMED",
                               "caveat": "industrial cyclone partition also depends on pressure, solids, viscosity, geometry, bypass and roping; measured mineral partition curves are needed before any control claim"}

json.dump(R, open(os.path.join(HERE, "results.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)

print(f"FX {FX.value} ZAR/USD [{FX.provenance.name}]  basis: {R['basis']}")
for name, d in R["V1_net_value_per_recovery_pp_per_yr"].items():
    print(f"V1 net value of +1 pp recovery, {name:22s} " + "  ".join(f"{sc}: R{v['value'] / 1e6:,.0f}M" for sc, v in d.items()) + "  [ASSUMED]")
print(f"V2 extra tonnes (mill-constrained only): {extra_t.value:,.0f} t/yr; net revenue/extra t base R{rev_per_t['base'].value:,.0f}; contribution base: " +
      ", ".join(f"{k} cost -> R{v['value'] / 1e6:,.0f}M" for k, v in R["V2_throughput_mill_constrained_only"]["contribution_per_yr_if_variable_cost_is_fraction_of_revenue"].items()))
print(f"V4 net value per pp (Zondereinde, base) US${per_pp_usd.value / 1e6:.2f}M; break-even pp across grid: " +
      f"{min(v['value'] for v in be.values()):.3f} to {max(v['value'] for v in be.values()):.3f} pp")
print(f"V5 QEMSCAN (incl. prep and mount) every shift per stream: CAD {per_stream.value:,.0f}/yr (2017 list) [{per_stream.provenance.name}]")
print("V6 " + "; ".join(f"{k}: {v['tonnes']['value']:,.0f} t processed before the assay returns" for k, v in R["V6_processed_before_assay_returns_zondereinde_scale"].items()))
print(f"V7 Stokes illustration: equal-settling ratio {ratio:.2f}")
