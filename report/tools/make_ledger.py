"""Write report/PILOT_COST_LEDGER.csv (planning allowances, not quotes). Run from report/."""
import csv

FX = 16.4
staff_site = 480000 + 360000 + 280000 + 144000 + 318000
rows = [
    # line, rand_low, rand_high, tranche, proposed payer, release, commitment point, cancellation exposure, contingency
    ("Staff and site, months 1-2", staff_site / 3, staff_site / 3, "L1", "TIA (proposed)", "G0", "Contracts at G0", "Notice periods", "15% lab"),
    ("Staff and site, months 3-6", staff_site * 2 / 3, staff_site * 2 / 3, "L2", "TIA (proposed)", "Week-8 laboratory review", "Week 8", "Notice periods", "15% lab"),
    ("Microscope imaging kit", 120000, 120000, "L1", "TIA (proposed)", "G0", "Purchase at G0", "Non-recoverable", "15% lab"),
    ("Polished sections, first third (77 = 70 + 7 duplicates)", 154000 / 3, 154000 / 3, "L1", "TIA (proposed)", "G0", "Lab order", "Orders placed", "15% lab"),
    ("Polished sections, remaining", 154000 * 2 / 3, 154000 * 2 / 3, "L2", "TIA (proposed)", "Week-8 laboratory review", "Lab order", "Orders placed", "15% lab"),
    ("Bond tests, 20 bench composites", 20 * 1200 * FX, 20 * 1200 * FX, "L1", "Host (proposed)", "G0", "Lab order before week 8", "Orders placed", "15% lab"),
    ("Automated mineralogy, 20 bench composites", 20 * 2000 * FX, 20 * 2000 * FX, "L1", "TIA (proposed); eligibility follows belt component, unconfirmed", "G0", "Lab order before week 8", "Orders placed", "15% lab"),
    ("Automated mineralogy, 44 microscope specimens (10 cal + 30 locked + 4 repeats)", 44 * 2000 * FX, 44 * 2000 * FX, "L2", "TIA (proposed)", "Week-8 laboratory review", "Fortnightly batches", "Batches ordered", "15% lab"),
    ("Independent review, IP and data terms, close-out", 120000, 120000, "L2", "TIA (proposed)", "Week-8 laboratory review", "Contract", "Work done", "15% lab"),
    ("Bond tests, 24 shadow composites", 24 * 1200 * FX, 24 * 1200 * FX, "R-H", "Host (proposed)", "G1B pass", "After G1B", "Orders placed", "15% lab"),
    ("Automated mineralogy, 24 shadow composites", 24 * 2000 * FX, 24 * 2000 * FX, "R-M", "TIA (proposed); eligibility follows belt component, unconfirmed", "G1M pass", "After G1M", "Orders placed", "15% lab"),
    ("Laboratory contingency (15% of base)", 859000, 859000, "Reserve", "As line", "Documented risk event", "On release", "As released", "-"),
    ("Sensor lease deposit or bench hire; edge computer", 0.57e6, 0.90e6, "B1", "TIA/host 50:50 (team proposal)", "G0", "Lease signed", "Deposit and cancellation fee", "25% belt"),
    ("Installation, rest of sensor, belt sampling, vendor support", 2.71e6, 4.35e6, "B2", "TIA/host 50:50 (team proposal)", "Bench outcome matrix, week 8", "After matrix decision", "Lease and vendor terms", "25% belt"),
    ("Belt contingency (25%)", 50000 * FX, 80000 * FX, "Reserve", "As line", "Documented risk event", "On release", "As released", "-"),
    ("Pre-G0 feasibility stage (outside pilot total)", 0, 210000, "P0", "TIA or host (proposed)", "Joint co-lead and funder approval", "Written quotes", "Work done", "Cap"),
]
with open('PILOT_COST_LEDGER.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(["line", "rand_low", "rand_high", "tranche", "proposed_payer", "release_condition", "commitment_point", "cancellation_exposure", "contingency"])
    for r in rows:
        w.writerow([r[0], round(r[1]), round(r[2])] + list(r[3:]))
tot = {}
for r in rows:
    tot.setdefault(r[3], [0, 0])
    tot[r[3]][0] += r[1]; tot[r[3]][1] += r[2]
for k, v in tot.items():
    print(k, round(v[0]), round(v[1]))
print('pilot', round(sum(v[0] for k, v in tot.items() if k != 'P0')), round(sum(v[1] for k, v in tot.items() if k != 'P0')))
