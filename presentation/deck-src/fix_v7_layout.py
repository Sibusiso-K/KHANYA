"""QA fixes after the first PowerPoint render of v7: table overlapping the source on 8b, three-line headline on 8c,
appendix labelling of the reference-spectra slide."""
import io, os, re

D = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(D, "build_deck.py")
s = io.open(p, encoding="utf-8").read()

# 8b: fold R2 + CI into the category labels and drop the table
a = s.index("    tbl = s.shapes.add_table(len(rows_hs) + 1, 3, Inches(0.6), Inches(5.7)")
b = s.index("    if os.path.exists(HS_CLIP) and os.path.exists(HS_SHOT):")
s = s[:a] + s[b:]
rep = [
    ('    cd.categories = [t[0] for t in rows_hs]\n',
     '    cd.categories = [f"{t[0]} · R² {t[2]:.2f} [{t[3][0]:.2f}, {t[3][1]:.2f}]" for t in rows_hs]\n'),
    ('gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.5), Inches(2.3), Inches(6.1), Inches(3.3), cd)',
     'gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.5), Inches(2.3), Inches(6.3), Inches(4.0), cd)'),
    ('    ch.chart_title.text_frame.text = "Out-of-fold error reduction vs predicting the average (%)"',
     '    ch.chart_title.text_frame.text = f"Error reduction vs predicting the average — out-of-fold, n = {rows_hs[0][1]} (R², 95% bootstrap CI)"'),
    ('    ch.category_axis.tick_labels.font.size = Pt(10.5); ch.category_axis.format.line.color.rgb = LINE\n    ch.category_axis.reverse_order = True\n    if os.path',
     '    ch.category_axis.tick_labels.font.size = Pt(10); ch.category_axis.format.line.color.rgb = LINE\n    ch.category_axis.reverse_order = True\n    if os.path'),
    # 8c headline to two lines
    ('    headline(s, f"Taught by QEMSCAN, the camera estimated plant-feed\\nmineralogy for composites it had never seen: {n_win} of {n_t} minerals.", y=1.15, size=27)',
     '    headline(s, f"Taught by QEMSCAN, the camera predicted unseen composites:\\n{n_win} of {n_t} minerals beat the average guess.", y=1.15, size=26)'),
    # appendix labelling
    ('eyebrow(s, 0.6, 0.85, "Spectral imaging, at the scale platinum lives")',
     'eyebrow(s, 0.6, 0.85, "Appendix · spectral imaging, at the scale platinum lives")'),
    ('"Why not core-scale SWIR?"', '"Why not SWIR for the platinum itself?"'),
]
for a2, b2 in rep:
    assert s.count(a2) == 1, a2[:90]
    s = s.replace(a2, b2)
io.open(p, "w", encoding="utf-8").write(s)
print("ok")
