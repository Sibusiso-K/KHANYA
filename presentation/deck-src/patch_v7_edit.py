"""Tweak patch_v7.py before it runs: calibrated headline, silent embed clip, and a MINERAL1 (QEMSCAN-taught) slide."""
import io, os

D = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(D, "patch_v7.py")
s = io.open(p, encoding="utf-8").read()

rep = [
    ('''    if wins:
        hl = "From the spectrum alone, the model predicts\\n" + " and ".join(t[0].lower() for t in wins[:2]) + " before milling."
    else:''',
     '''    if wins:
        lo_r2, hi_r2 = min(t[2] for t in wins), max(t[2] for t in wins)
        hl = (f"From the spectrum alone, {len(wins)} of {len(rows_hs)} lab results beat the\\naverage guess before milling — modestly (R² {lo_r2:.2f}–{hi_r2:.2f}).")
    else:'''),
    ("REEFPRINT-belt-monitor-demo.mp4", "REEFPRINT-belt-monitor-embed.mp4"),
    ('''    text(s, 6.95, 5.62, 5.8, 0.3, "Belt Monitor (built today): replays the public samples one by one, as a belt would.", size=10, color=MUTED)''',
     '''    text(s, 6.95, 5.62, 5.8, 0.3, "Belt Monitor (built today) replays held-out samples one by one, as a belt would. Silent here; narrated cut in presentation/video.", size=9.5, color=MUTED, line=1.0)'''),
]
for a, b in rep:
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)

mineral = r'''# ---- 8c QEMSCAN TEACHES, HYPERSPECTRAL PREDICTS (HIDSAG MINERAL1, grouped by composite)
M1_PATH = r"C:\Users\USER\Desktop\REEFPRINT\training\hidsag-hyperspectral-20261001\output_v4\mineral1_grouped_ci.json"
if os.path.exists(M1_PATH):
    M1 = json.load(open(M1_PATH, encoding="utf-8"))["targets"]
    NICE_M = {"Anhydrite/Gypsum": "Anhydrite / gypsum", "Muscovite/Sericite": "Sericite (muscovite)", "Chalcosite/Digenite": "Chalcocite / digenite",
              "Covelite": "Covellite", "Bytownite_An80": "Bytownite", "Labradorite_An60": "Labradorite", "Andesina_An40": "Andesine",
              "Oligoclasa_An20": "Oligoclase", "Others Ti Minerals": "Other Ti minerals"}
    ranked = sorted(M1.items(), key=lambda kv: -kv[1]["r2"])
    n_t = len(ranked)
    n_win = sum(1 for _, t in ranked if t["beats_baseline_ci_excludes_zero"])
    n_comp = ranked[0][1]["n_composites"]
    n_samp = ranked[0][1]["n_samples"]
    pick = ranked[:8] + [kv for kv in ranked if kv[0] == "Molybdenite"] + ranked[-2:]
    print(f"M1 {n_win}/{n_t} beat baseline (cluster CI); composites={n_comp}")
    s = new()
    brand(s); pagenum(s, 0)
    eyebrow(s, 0.6, 0.85, "QEMSCAN teaches · the camera predicts — the new part")
    headline(s, f"Taught by QEMSCAN, the camera estimated plant-feed\nmineralogy for composites it had never seen: {n_win} of {n_t} minerals.", y=1.15, size=27)
    cd = CategoryChartData()
    cd.categories = [NICE_M.get(k, k) for k, _ in pick]
    cd.add_series("R² out-of-fold", [round(t["r2"], 2) for _, t in pick])
    gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.5), Inches(2.3), Inches(6.3), Inches(4.35), cd)
    ch = gf.chart
    style_chart(ch, [PENT], legend=False, size=10)
    ch.has_title = True
    ch.chart_title.text_frame.text = f"R² on held-out composites (QEMSCAN wt% as truth) — top 8, molybdenite, bottom 2 of {n_t}"
    ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(10.5)
    ch.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
    pl = ch.plots[0]
    pl.gap_width = 55
    pl.has_data_labels = True
    pl.data_labels.number_format = '0.00'
    pl.data_labels.number_format_is_linked = False
    pl.data_labels.font.size = Pt(9.5)
    for i, (k, t) in enumerate(pick):
        pt = pl.series[0].points[i]
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = (CHALC if k in ("Chalcopyrite", "Pyrite", "Molybdenite") else PENT) if t["beats_baseline_ci_excludes_zero"] else LINE
    va = ch.value_axis
    va.minimum_scale = 0; va.maximum_scale = 1.0
    va.has_major_gridlines = True; va.major_gridlines.format.line.color.rgb = LINE; va.tick_labels.font.size = Pt(9)
    ch.category_axis.tick_labels.font.size = Pt(10); ch.category_axis.format.line.color.rgb = LINE
    ch.category_axis.reverse_order = True
    cp = M1["Chalcopyrite"]
    x0 = 7.15
    text(s, x0, 2.3, 5.6, 0.6, f"{cp['r2']:.2f}", size=36, font=HEAD, bold=True, color=CHALC)
    text(s, x0 + 1.35, 2.38, 4.25, 0.7, f"R² for chalcopyrite, the copper mineral [95% CI {cp['r2_ci95_cluster'][0]:.2f}–{cp['r2_ci95_cluster'][1]:.2f}, resampling {cp['n_composites']} composites]. Typical error {cp['mae']:.2f} wt% vs {cp['baseline_mae']:.2f} for the average guess.",
         size=10.5, color=MUTED, line=1.05)
    tag(s, x0, 3.12, "RECORDED")
    text(s, x0, 3.5, 5.6, 0.35, "Read it honestly", size=13, font=BODYB, bold=True)
    text(s, x0, 3.82, 5.6, 1.1, "Sulphides have no SWIR fingerprint. The camera reads the sericite, biotite and gypsum that travel with chalcopyrite in this deposit. That link is site-specific, so every mine calibrates on its own QEMSCAN — which is exactly the job QEMSCAN keeps.",
         size=10.5, color=MUTED, line=1.05)
    text(s, x0, 4.98, 5.6, 0.35, "For Bushveld ore — untested", size=13, font=BODYB, bold=True)
    text(s, x0, 5.3, 5.6, 0.9, "The same loop would track the silicate gangue — pyroxene, plagioclase, chlorite, talc — that sets hardness and depressant demand. Platinum minerals stay with the microscope.",
         size=10.5, color=MUTED, line=1.05)
    tag(s, x0, 6.2, "ROADMAP")
    source(s, f"Data: HIDSAG MINERAL1 (CC0) — {n_samp} plant-feed size-fraction samples from {n_comp} composites (process line × month), porphyry Cu-Mo, Chile. GroupKFold by composite; CIs by cluster bootstrap over composites. "
              "Purple/orange: model error below the average guess with a 95% CI excluding zero; grey: not. Run: Kaggle v4, 1 Oct 2026; v3 grouping bug found and fixed the same day.", y=6.9)
    pic(s, G["lens_a"], 11.95, 0.7, w=0.8, name="!!lens")
    morph(s)
    notes(s, "SCRIPT_8c")

'''
a2 = "a2 = \"# ---- 9 COMPETITION\""
assert s.count(a2) == 1
s = s.replace("s = s.replace(a1, where + a1).replace(a2, result + a2)",
              "s = s.replace(a1, where + a1).replace(a2, result + mineral + a2)")
s = s.replace("result = r'''# ---- 8b", "mineral = r'''" + mineral.replace("'''", "") + "'''\n\nresult = r'''# ---- 8b", 1) if False else s
# define `mineral` inside patch_v7.py just before it is used
s = s.replace("a1 = \"# ---- 7 DEMO VIDEO\"", "mineral = " + repr(mineral) + "\n\na1 = \"# ---- 7 DEMO VIDEO\"", 1)
io.open(p, "w", encoding="utf-8").write(s)
print("ok")
