"""Apply ClauDex round-2 corrections to build_deck.py (true numeric axes, multispectral wording, conditional claims)."""
import os

D = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(D, "build_deck.py")
s = open(p, encoding="utf-8").read()

R = [
    # imports for XY charts
    ("from pptx.chart.data import CategoryChartData", "from pptx.chart.data import CategoryChartData, XyChartData"),
    # slide 9 headline + complement
    ('headline(s, "Everyone measures minerals. We also measure\\nwhether the answer is safe to act on.", y=1.15, size=30)',
     'headline(s, "Everyone measures minerals. We also check whether\\nthe evidence is sufficient to act on.", y=1.15, size=30)'),
    ('("REEFPRINT routes only the uncertain samples to QEMSCAN, and hands checked setpoints to the controllers plants already run.", {})',
     '("REEFPRINT proposes referring uncertain samples to QEMSCAN — a workflow to validate prospectively — and handing checked setpoints to the controllers plants already run.", {})'),
    # slide 11 rec 2
    ('("The paper\'s stated future work is mineralogy of the timed concentrates; send only uncertain ones to QEMSCAN.", {"color": RGBColor(0xC9, 0xD5, 0xE3)})',
     '("The paper\'s stated future work is mineralogy of the timed concentrates; refer uncertain ones to QEMSCAN (workflow to be validated).", {"color": RGBColor(0xC9, 0xD5, 0xE3)})'),
    # spectral slide wording: multispectral, reference spectra suggest
    ('eyebrow(s, 0.6, 0.85, "Hyperspectral, at the scale platinum lives")',
     'eyebrow(s, 0.6, 0.85, "Spectral imaging, at the scale platinum lives")'),
    ('headline(s, "A few colours of light separate platinum minerals\\nthat an ordinary camera blurs together.", y=1.15, size=28)',
     'headline(s, "Reference spectra suggest a few narrow colours of\\nlight could separate platinum minerals.", y=1.15, size=28)'),
    ('gap between sperrylite (Pt) and pentlandite at 420 nm — but only {gap640:.1f} pts at 640 nm. Blue light finds platinum.',
     'gap between sperrylite (Pt) and pentlandite at 420 nm — only {gap640:.1f} pts at 640 nm. Discrimination on real sections, and any gain over RGB, are still untested.'),
    ('text(s, x0, 5.72, 4.3, 0.9, "6–8 narrow LED bands + a rotating polariser on the microscope, labelled pixel-for-pixel by QEMSCAN maps of the same polished sections."',
     'text(s, x0, 5.72, 4.3, 0.9, "Multispectral reflectance microscopy: 6–8 narrow LED bands + a rotating polariser, labelled pixel-for-pixel by QEMSCAN maps of the same polished sections."'),
    ('("9–18 months", "Closed loop", "Flotation trial with plant control · QEMSCAN-labelled multispectral / hyperspectral reflectance + polarisation microscopy", MAG)',
     '("9–18 months", "Closed loop", "Flotation trial with plant control · QEMSCAN-labelled multispectral reflectance + polarisation microscopy", MAG)'),
]
for a, b in R:
    assert a in s, "missing: " + a[:90]
    s = s.replace(a, b)

# --- kinetics chart -> XY scatter with numeric minutes
a = s.index("cd2 = CategoryChartData()")
b = s.index("ch.category_axis.tick_labels.font.size = Pt(9); ch.category_axis.format.line.color.rgb = LINE", a)
b = s.index("\n", b) + 1
kin_xy = '''cd2 = XyChartData()
ser2 = cd2.add_series("Hypothetical cumulative recovery (%)")
for tk in ["0.25", "0.5", "1", "3", "7", "20"]:
    ser2.add_data_point(float(tk), round(KIN["R"][tk] * 100, 1))
gf = s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_LINES, Inches(4.95), Inches(1.95), Inches(4.3), Inches(3.1), cd2)
ch = gf.chart
ch.has_legend = False
ch.font.name = BODY; ch.font.size = Pt(9); ch.font.color.rgb = INK
sr = ch.plots[0].series[0]
sr.format.line.color.rgb = PYRR; sr.format.line.width = Pt(2.5); sr.smooth = False
sr.marker.format.fill.solid(); sr.marker.format.fill.fore_color.rgb = PYRR
ch.has_title = True
ch.chart_title.text_frame.text = "2 · Hypothetical curve, borrowed rates (min)"
ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(10.5)
ch.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
pl = ch.plots[0]; pl.has_data_labels = True
pl.data_labels.number_format = '0"%"'; pl.data_labels.number_format_is_linked = False
pl.data_labels.position = XL_LABEL_POSITION.ABOVE; pl.data_labels.font.size = Pt(8.5)
va = ch.value_axis; va.maximum_scale = 100; va.minimum_scale = 0; va.has_major_gridlines = True
va.major_gridlines.format.line.color.rgb = LINE; va.tick_labels.font.size = Pt(8.5)
xa = ch.category_axis; xa.minimum_scale = 0; xa.maximum_scale = 20; xa.major_unit = 5
xa.tick_labels.font.size = Pt(8.5); xa.format.line.color.rgb = LINE; xa.has_major_gridlines = False
'''
s = s[:a] + kin_xy + s[b:]

# --- spectra chart -> XY scatter (lines, no markers) with numeric wavelength
a = s.index("wls = [400, 440, 480, 520, 600, 640, 680, 700]")
b = s.index("ch.category_axis.tick_labels.font.size = Pt(9); ch.category_axis.format.line.color.rgb = LINE", a)
b = s.index("\n", b) + 1
spec_xy = '''cd = XyChartData()
for key, label, col in order:
    ser = cd.add_series(label)
    for w in range(400, 701, 20):
        if key == "cooperite" and w == 560:
            continue  # printed R2 at 560 nm is out of sequence in the source; point omitted
        ser.add_data_point(w, round(SPEC["spectra"][key][str(w)], 1))
gf = s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS, Inches(0.5), Inches(2.25), Inches(7.6), Inches(4.45), cd)
ch = gf.chart
ch.font.name = BODY; ch.font.size = Pt(9); ch.font.color.rgb = INK
ch.has_legend = True; ch.legend.position = XL_LEGEND_POSITION.RIGHT; ch.legend.include_in_layout = False; ch.legend.font.size = Pt(9)
for ser, (_, _, col) in zip(ch.plots[0].series, order):
    ser.format.line.color.rgb = col
    ser.format.line.width = Pt(3 if ser.name.startswith(("Sperrylite", "Cooperite")) else 1.75)
    ser.smooth = False
ch.has_title = True
ch.chart_title.text_frame.text = "Reference reflectance in air (%) vs wavelength (nm)"
ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(11)
ch.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
va = ch.value_axis; va.minimum_scale = 0; va.maximum_scale = 60
va.has_major_gridlines = True; va.major_gridlines.format.line.color.rgb = LINE; va.tick_labels.font.size = Pt(9)
xa = ch.category_axis; xa.minimum_scale = 400; xa.maximum_scale = 700; xa.major_unit = 50
xa.tick_labels.font.size = Pt(9); xa.format.line.color.rgb = LINE; xa.has_major_gridlines = False
'''
s = s[:a] + spec_xy + s[b:]
s = s.replace("REEFPRINT-KHANYA-Team-Sonar-pitch-v3.pptx", "REEFPRINT-KHANYA-Team-Sonar-pitch-v4.pptx")
open(p, "w", encoding="utf-8").write(s)
print("patched")
