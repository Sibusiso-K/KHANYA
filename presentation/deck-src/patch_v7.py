"""Deck v7: add 'Where it sits on site' (before the demo) and 'Hyperspectral before grinding — measured' (after evidence).
Every number on the results slide is read from the Kaggle output at build time; nothing is typed by hand."""
import os

D = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(D, "build_deck.py")
s = open(p, encoding="utf-8").read()

where = r'''# ---- 6b WHERE IT SITS ON SITE
s = new()
brand(s); pagenum(s, 0)
eyebrow(s, 0.6, 0.85, "Where it sits on site")
headline(s, "Three instruments, three speeds,\none screen in the control room.", y=1.15, size=30)
steps = ["Pit & stockpile", "Crusher", "Mill-feed belt", "Mill & cyclones", "Flotation", "Concentrate"]
for i, st in enumerate(steps):
    x = 0.6 + i * 2.06
    hot = st in ("Mill-feed belt", "Mill & cyclones")
    box(s, x, 2.45, 1.8, 0.62, fill=(NAVY if hot else PAPER), radius=0.1)
    text(s, x, 2.45, 1.8, 0.62, st, size=12, font=BODYB, bold=True, color=(WHITE if hot else INK), align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    if i < len(steps) - 1:
        a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + 1.83), Inches(2.66), Inches(0.2), Inches(0.2))
        a.fill.solid(); a.fill.fore_color.rgb = LINE; a.line.fill.background()
cards = [
    (0.6, "1 · Belt hyperspectral camera", "SECONDS · EVERY TONNE", PYRR,
     "VNIR + SWIR line scan over the mill-feed belt, edge PC beside it. Reads the gangue and alteration minerals (clays, micas, carbonates) that drive hardness, reagent use and recovery.",
     "Early warning: “ore change — harder, lower recovery, more lime”. Tested on public drill core: next slides.", "ROADMAP"),
    (4.78, "2 · REEFPRINT microscope", "WITHIN THE SHIFT", COPPER,
     "A polished section from the cyclone overflow or flotation feed, on any lab microscope camera. Sees the payable sulphides and how they are locked: liberation, not just chemistry.",
     "Grind and reagent advice — act · verify · hold — with a stated reason, an audit record and a refusal path.", "LIVE APP"),
    (8.96, "3 · QEMSCAN & lab assays", "DAYS · THE TEACHER", PENT,
     "Automated mineralogy and metallurgical tests on composites. Too slow to steer a shift, exact enough to label training data for both instruments.",
     "Re-trains the belt and microscope models; takes the samples REEFPRINT refuses.", "ROADMAP"),
]
for x, t1, t2, col, body, out, tg in cards:
    box(s, x, 3.35, 3.95, 3.0, fill=PAPER, radius=0.12)
    box(s, x + 0.2, 3.52, 0.3, 0.3, fill=col, shape=MSO_SHAPE.OVAL)
    text(s, x + 0.62, 3.5, 3.2, 0.35, t1, size=13.5, font=BODYB, bold=True)
    text(s, x + 0.62, 3.83, 3.2, 0.3, t2, size=9.5, font=BODYB, bold=True, color=col)
    text(s, x + 0.2, 4.2, 3.6, 1.2, body, size=10.5, color=MUTED, line=1.05)
    text(s, x + 0.2, 5.35, 3.6, 0.8, out, size=10.5, font=BODYB, bold=True, line=1.05)
    tag(s, x + 0.2, 6.0, tg)
box(s, 0.6, 6.5, 12.3, 0.42, fill=NAVY, radius=0.1)
text(s, 0.8, 6.5, 12.0, 0.42, [[("Control room:  ", {"font": BODYB, "bold": True, "color": RGBColor(0xF2, 0x9A, 0x6A)}),
     ("belt flag + microscope advisory + audit trail on one dashboard. Only a person-approved setpoint reaches the plant (OPC UA).", {"color": WHITE})]],
     size=11.5, anchor=MSO_ANCHOR.MIDDLE)
source(s, "Why two scales: a belt camera sees millimetre pixels of the host rock; platinum-group and base-metal sulphide grains are microns across and opaque (slide on reference spectra). Belt placement is a design proposal, not an installation.", y=7.02)
pic(s, G["lens_a"], 11.95, 0.7, w=0.8, name="!!lens")
morph(s)
notes(s, "SCRIPT_6b")

'''

result = r'''# ---- 8b HYPERSPECTRAL BEFORE GRINDING (measured, HIDSAG)
HS_PATH = r"C:\Users\USER\Desktop\REEFPRINT\training\hidsag-hyperspectral-20261001\output\hidsag_results.json"
HS_SHOT = r"C:\Users\USER\Desktop\REEFPRINT\presentation\belt-monitor\screenshot.png"
HS_CLIP = r"C:\Users\USER\Desktop\REEFPRINT\presentation\video\REEFPRINT-belt-monitor-embed.mp4"
if os.path.exists(HS_PATH):
    HS = json.load(open(HS_PATH, encoding="utf-8"))
    geo = HS["records"]["GEOMET"]["targets"]
    NICE_T = {"Cu rec": "Cu recovery", "Mo rec": "Mo recovery", "Lime cons": "Lime consumption", "PH": "Flotation pH", "WI": "Bond work index"}
    rows_hs = []
    for k, r in geo.items():
        sk = k.split(".")[-1]
        if sk not in NICE_T:
            continue
        b = r["best_model"]
        red = 100.0 * (1 - r[b]["mae"] / r["baseline"]["mae"])
        rows_hs.append((NICE_T[sk], r["n"], r[b]["r2"], r[b]["r2_ci95"], red, r["beats_baseline_mae"], b))
    rows_hs.sort(key=lambda t: -t[4])
    for t in rows_hs:
        print(f"HS {t[0]:18s} n={t[1]} R2={t[2]:.3f} [{t[3][0]:.2f},{t[3][1]:.2f}] err-reduction={t[4]:.1f}% beats={t[5]} model={t[6]}")
    wins = [t for t in rows_hs if t[5] and t[3][0] > 0]
    s = new()
    brand(s); pagenum(s, 0)
    eyebrow(s, 0.6, 0.85, "Hyperspectral, before grinding — measured, not promised")
    if wins:
        lo_r2, hi_r2 = min(t[2] for t in wins), max(t[2] for t in wins)
        hl = (f"From the spectrum alone, {len(wins)} of {len(rows_hs)} lab results beat the\naverage guess before milling — modestly (R² {lo_r2:.2f}–{hi_r2:.2f}).")
    else:
        hl = "Belt-style spectra did not yet beat the average guess.\nWe report it anyway."
    headline(s, hl, y=1.15, size=28)
    cd = CategoryChartData()
    cd.categories = [t[0] for t in rows_hs]
    cd.add_series("Error reduction vs average-guess baseline (%)", [round(t[4], 1) for t in rows_hs])
    gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.5), Inches(2.3), Inches(6.1), Inches(3.3), cd)
    ch = gf.chart
    style_chart(ch, [PYRR], legend=False, size=10)
    ch.has_title = True
    ch.chart_title.text_frame.text = "Out-of-fold error reduction vs predicting the average (%)"
    ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(11)
    ch.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
    pl = ch.plots[0]
    pl.gap_width = 60
    pl.has_data_labels = True
    pl.data_labels.number_format = '0"%"'
    pl.data_labels.number_format_is_linked = False
    pl.data_labels.font.size = Pt(10)
    for i, t in enumerate(rows_hs):
        pt = pl.series[0].points[i]
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = PYRR if (t[5] and t[3][0] > 0) else LINE
    va = ch.value_axis
    va.has_major_gridlines = True; va.major_gridlines.format.line.color.rgb = LINE; va.tick_labels.font.size = Pt(9)
    va.tick_labels.number_format = '0"%"'; va.tick_labels.number_format_is_linked = False
    ch.category_axis.tick_labels.font.size = Pt(10.5); ch.category_axis.format.line.color.rgb = LINE
    ch.category_axis.reverse_order = True
    tbl = s.shapes.add_table(len(rows_hs) + 1, 3, Inches(0.6), Inches(5.7), Inches(6.0), Inches(0.24 * (len(rows_hs) + 1))).table
    for i, wv in enumerate([2.4, 0.7, 2.9]):
        tbl.columns[i].width = Inches(wv)
    hdr = ["Lab result predicted", "n", "R² out-of-fold [95% bootstrap CI]"]
    for r_i in range(len(rows_hs) + 1):
        tbl.rows[r_i].height = Inches(0.22)
        for c_i in range(3):
            cell = tbl.cell(r_i, c_i)
            if r_i == 0:
                val = hdr[c_i]
            else:
                t = rows_hs[r_i - 1]
                val = [t[0], str(t[1]), f"{t[2]:.2f}  [{t[3][0]:.2f}, {t[3][1]:.2f}]"][c_i]
            cell.text = ""
            tf = cell.text_frame
            tf.margin_left = Inches(0.06); tf.margin_right = Inches(0.04); tf.margin_top = tf.margin_bottom = Inches(0.0)
            rr = tf.paragraphs[0].add_run(); rr.text = val
            rr.font.name = BODYB if r_i == 0 else BODY; rr.font.bold = r_i == 0; rr.font.size = Pt(9)
            rr.font.color.rgb = WHITE if r_i == 0 else INK
            cell.fill.solid(); cell.fill.fore_color.rgb = NAVY if r_i == 0 else (WHITE if r_i % 2 else PAPER)
    if os.path.exists(HS_CLIP) and os.path.exists(HS_SHOT):
        mv = s.shapes.add_movie(HS_CLIP, Inches(6.95), Inches(2.3), Inches(5.8), Inches(3.2625), poster_frame_image=HS_SHOT, mime_type="video/mp4")
        mv.name = "belt_video"
    elif os.path.exists(HS_SHOT):
        pic(s, HS_SHOT, 6.95, 2.3, w=5.8)
    text(s, 6.95, 5.62, 5.8, 0.3, "Belt Monitor (built today) replays held-out samples one by one, as a belt would. Silent here; narrated cut in presentation/video.", size=9.5, color=MUTED, line=1.0)
    tag(s, 6.95, 5.95, "RECORDED")
    box(s, 6.95, 6.3, 5.8, 0.62, fill=PAPER, radius=0.1)
    text(s, 7.1, 6.34, 5.55, 0.56, [[("Scope, said first: ", {"font": BODYB, "bold": True}),
         (f"{rows_hs[0][1]} porphyry Cu-Mo drill-core samples from Chile — not PGM ore, not a live belt. A site needs its own calibration samples.", {"color": MUTED})]],
         size=9.5, line=1.0, anchor=MSO_ANCHOR.MIDDLE)
    source(s, "Data: HIDSAG (Ehrenfeld et al., Scientific Data 2023), CC0, Figshare 10.6084/m9.figshare.c.5983921. VNIR+SWIR spectral statistics → PLS or ridge, 5-fold CV; "
              "the better of the two per target is chosen on the same out-of-fold score (mild optimism). Grey bars: not better than the average guess. Run: Kaggle, 1 Oct 2026.", y=7.0)
    pic(s, G["lens_a"], 11.95, 0.7, w=0.8, name="!!lens")
    morph(s)
    notes(s, "SCRIPT_8b")

'''

mineral = '# ---- 8c QEMSCAN TEACHES, HYPERSPECTRAL PREDICTS (HIDSAG MINERAL1, grouped by composite)\nM1_PATH = r"C:\\Users\\USER\\Desktop\\REEFPRINT\\training\\hidsag-hyperspectral-20261001\\output_v4\\mineral1_grouped_ci.json"\nif os.path.exists(M1_PATH):\n    M1 = json.load(open(M1_PATH, encoding="utf-8"))["targets"]\n    NICE_M = {"Anhydrite/Gypsum": "Anhydrite / gypsum", "Muscovite/Sericite": "Sericite (muscovite)", "Chalcosite/Digenite": "Chalcocite / digenite",\n              "Covelite": "Covellite", "Bytownite_An80": "Bytownite", "Labradorite_An60": "Labradorite", "Andesina_An40": "Andesine",\n              "Oligoclasa_An20": "Oligoclase", "Others Ti Minerals": "Other Ti minerals"}\n    ranked = sorted(M1.items(), key=lambda kv: -kv[1]["r2"])\n    n_t = len(ranked)\n    n_win = sum(1 for _, t in ranked if t["beats_baseline_ci_excludes_zero"])\n    n_comp = ranked[0][1]["n_composites"]\n    n_samp = ranked[0][1]["n_samples"]\n    pick = ranked[:8] + [kv for kv in ranked if kv[0] == "Molybdenite"] + ranked[-2:]\n    print(f"M1 {n_win}/{n_t} beat baseline (cluster CI); composites={n_comp}")\n    s = new()\n    brand(s); pagenum(s, 0)\n    eyebrow(s, 0.6, 0.85, "QEMSCAN teaches · the camera predicts — the new part")\n    headline(s, f"Taught by QEMSCAN, the camera estimated plant-feed\\nmineralogy for composites it had never seen: {n_win} of {n_t} minerals.", y=1.15, size=27)\n    cd = CategoryChartData()\n    cd.categories = [NICE_M.get(k, k) for k, _ in pick]\n    cd.add_series("R² out-of-fold", [round(t["r2"], 2) for _, t in pick])\n    gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.5), Inches(2.3), Inches(6.3), Inches(4.35), cd)\n    ch = gf.chart\n    style_chart(ch, [PENT], legend=False, size=10)\n    ch.has_title = True\n    ch.chart_title.text_frame.text = f"R² on held-out composites (QEMSCAN wt% as truth) — top 8, molybdenite, bottom 2 of {n_t}"\n    ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(10.5)\n    ch.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True\n    pl = ch.plots[0]\n    pl.gap_width = 55\n    pl.has_data_labels = True\n    pl.data_labels.number_format = \'0.00\'\n    pl.data_labels.number_format_is_linked = False\n    pl.data_labels.font.size = Pt(9.5)\n    for i, (k, t) in enumerate(pick):\n        pt = pl.series[0].points[i]\n        pt.format.fill.solid()\n        pt.format.fill.fore_color.rgb = (CHALC if k in ("Chalcopyrite", "Pyrite", "Molybdenite") else PENT) if t["beats_baseline_ci_excludes_zero"] else LINE\n    va = ch.value_axis\n    va.minimum_scale = 0; va.maximum_scale = 1.0\n    va.has_major_gridlines = True; va.major_gridlines.format.line.color.rgb = LINE; va.tick_labels.font.size = Pt(9)\n    ch.category_axis.tick_labels.font.size = Pt(10); ch.category_axis.format.line.color.rgb = LINE\n    ch.category_axis.reverse_order = True\n    cp = M1["Chalcopyrite"]\n    x0 = 7.15\n    text(s, x0, 2.3, 5.6, 0.6, f"{cp[\'r2\']:.2f}", size=36, font=HEAD, bold=True, color=CHALC)\n    text(s, x0 + 1.35, 2.38, 4.25, 0.7, f"R² for chalcopyrite, the copper mineral [95% CI {cp[\'r2_ci95_cluster\'][0]:.2f}–{cp[\'r2_ci95_cluster\'][1]:.2f}, resampling {cp[\'n_composites\']} composites]. Typical error {cp[\'mae\']:.2f} wt% vs {cp[\'baseline_mae\']:.2f} for the average guess.",\n         size=10.5, color=MUTED, line=1.05)\n    tag(s, x0, 3.12, "RECORDED")\n    text(s, x0, 3.5, 5.6, 0.35, "Read it honestly", size=13, font=BODYB, bold=True)\n    text(s, x0, 3.82, 5.6, 1.1, "Sulphides have no SWIR fingerprint. The camera reads the sericite, biotite and gypsum that travel with chalcopyrite in this deposit. That link is site-specific, so every mine calibrates on its own QEMSCAN — which is exactly the job QEMSCAN keeps.",\n         size=10.5, color=MUTED, line=1.05)\n    text(s, x0, 4.98, 5.6, 0.35, "For Bushveld ore — untested", size=13, font=BODYB, bold=True)\n    text(s, x0, 5.3, 5.6, 0.9, "The same loop would track the silicate gangue — pyroxene, plagioclase, chlorite, talc — that sets hardness and depressant demand. Platinum minerals stay with the microscope.",\n         size=10.5, color=MUTED, line=1.05)\n    tag(s, x0, 6.2, "ROADMAP")\n    source(s, f"Data: HIDSAG MINERAL1 (CC0) — {n_samp} plant-feed size-fraction samples from {n_comp} composites (process line × month), porphyry Cu-Mo, Chile. GroupKFold by composite; CIs by cluster bootstrap over composites. "\n              "Purple/orange: model error below the average guess with a 95% CI excluding zero; grey: not. Run: Kaggle v4, 1 Oct 2026; v3 grouping bug found and fixed the same day.", y=6.9)\n    pic(s, G["lens_a"], 11.95, 0.7, w=0.8, name="!!lens")\n    morph(s)\n    notes(s, "SCRIPT_8c")\n\n'

a1 = "# ---- 7 DEMO VIDEO"
a2 = "# ---- 9 COMPETITION"
assert a1 in s and a2 in s and "6b WHERE IT SITS" not in s
s = s.replace(a1, where + a1).replace(a2, result + mineral + a2)
s = s.replace("REEFPRINT-KHANYA-Team-Sonar-pitch-v6.pptx", "REEFPRINT-KHANYA-Team-Sonar-pitch-v7.pptx")
open(p, "w", encoding="utf-8").write(s)
print("ok")
