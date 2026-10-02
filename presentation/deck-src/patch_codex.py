"""Apply the ClauDex (Codex/Astra) round-1 corrections to build_deck.py and add the spectral slide."""
import os

D = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(D, "build_deck.py")
s = open(p, encoding="utf-8").read()

R = [
    ('KIN = json.load(open(os.path.join(SCR, "kinetics_test11.json")))',
     'KIN = json.load(open(os.path.join(D, "kinetics_test11.json")))'),
    ('("0 unsafe advisories against expert-mask advice on 12 held-out sections (raw pipeline: 2). Every disagreement became “verify”. 0 of 12 is an observation (95% upper bound 22%), not a guarantee.", {"color": MUTED})',
     '("historical checkpoint de7135a9 — 0 policy-defined unsafe disagreements with expert-mask advice on a reused 12-section benchmark (raw pipeline: 2); every disagreement became “verify”. 0 of 12 is an observation (95% upper bound 22%), not a guarantee.", {"color": MUTED})'),
    ('''f"A third of held-out sections got a confident optical answer (4/12; 95% CI {N['conf_lo']*100:.0f}–{N['conf_hi']*100:.0f}%); the rest were sent for review. Per 100 samples that avoids ≈ ${N['triage_point']:,.0f} of QEMSCAN time (range ${N['triage_lo']:,.0f}–${N['triage_hi']:,.0f})."''',
     '''f"A third of held-out sections got a confident optical answer (4/12; 95% CI {N['conf_lo']*100:.0f}–{N['conf_hi']*100:.0f}%); the rest went to review. If a prospective pilot shows those answers can safely replace the lab analysis: ≈ ${N['triage_point']:,.0f} per 100 samples at a 2017 list price (range ${N['triage_lo']:,.0f}–${N['triage_hi']:,.0f})."'''),
    ('headline(s, "Predict the next lab test before it runs.", y=1.15, size=32)',
     'headline(s, "Propose the next lab test before it runs.", y=1.15, size=32)'),
    ("ch.chart_title.text_frame.text = \"1 · test_11 grains in the paper's liberation classes (%)\"",
     "ch.chart_title.text_frame.text = \"1 · test_11 grains, area-share proxy in the paper's bins (%)\""),
    ("ch.chart_title.text_frame.text = \"2 · Predicted rougher recovery with the paper's class rates\"",
     "ch.chart_title.text_frame.text = \"2 · Hypothetical curve with the paper's borrowed rates\""),
    ('text(s, 9.7, 2.1, 2.9, 0.3, "3 · THE NEXT TEST, SUGGESTED"',
     'text(s, 9.7, 2.1, 2.9, 0.3, "3 · HYPOTHESES FOR THE NEXT TEST"'),
    ('''(f"≈{KIN['R']['1']*100:.0f}% of payload is predicted to float in the first minute — the interval the paper could not resolve.", {"color": RGBColor(0xC9, 0xD5, 0xE3)})''',
     '''(f"Under the borrowed rates ≈{KIN['R']['1']*100:.0f}% of payload floats in the first minute — the interval the paper could not resolve. Calibrate on this ore first.", {"color": RGBColor(0xC9, 0xD5, 0xE3)})'''),
    ("(\"REEFPRINT's grain map (minutes, optical) is binned into the five liberation classes of Moodley, Govender et al. (Mintek, 2026), then their first-order class rates predict recovery with time — before a flotation test or QEMSCAN run is booked.\", {\"color\": MUTED})",
     "(\"REEFPRINT's grain map (minutes, optical) is binned with the class boundaries of Moodley, Govender et al. (Mintek, 2026) using area share — an unvalidated proxy for their free-surface exposure. Their rates then give a hypothetical curve to help design the next test; it is not a prediction for this ore.\", {\"color\": MUTED})"),
    ('So we route each answer to the best expert.', 'Next, we route each answer to the best expert.'),
    ('nodes = [("Image in", 0.6, 3.55, MUTED),', 'tag(s, 0.6, 2.4, "ROADMAP")\nnodes = [("Image in", 0.6, 3.55, MUTED),'),
    ('REEFPRINT-KHANYA-Team-Sonar-pitch-v2.pptx', 'REEFPRINT-KHANYA-Team-Sonar-pitch-v3.pptx'),
]
for a, b in R:
    assert a in s, "missing: " + a[:90]
    s = s.replace(a, b)

SPECTRAL = r'''# ---- 13b SPECTRAL (hyperspectral at the right scale)
SPEC = json.load(open(os.path.join(D, "spectra.json"), encoding="utf-8"))
s = new()
brand(s); pagenum(s, 0)
eyebrow(s, 0.6, 0.85, "Hyperspectral, at the scale platinum lives")
headline(s, "A few colours of light separate platinum minerals\nthat an ordinary camera blurs together.", y=1.15, size=28)
order = [("sperrylite", "Sperrylite PtAs₂", COPPER), ("cooperite", "Cooperite PtS", MAG), ("pentlandite", "Pentlandite", PENT),
         ("pyrrhotite", "Pyrrhotite", PYRR), ("chalcopyrite", "Chalcopyrite", CHALC), ("magnetite", "Magnetite", MUTED), ("chromite", "Chromite", INK)]
wls = [400, 440, 480, 520, 560, 600, 640, 680, 700]
cd = CategoryChartData()
cd.categories = [str(w) for w in wls]
for key, label, col in order:
    cd.add_series(label, tuple(round(SPEC["spectra"][key][str(w)], 1) for w in wls))
gf = s.shapes.add_chart(XL_CHART_TYPE.LINE, Inches(0.5), Inches(2.25), Inches(7.6), Inches(4.45), cd)
ch = gf.chart
style_chart(ch, [c for _, _, c in order], legend=True, size=9)
ch.legend.position = XL_LEGEND_POSITION.RIGHT
for ser, (_, _, col) in zip(ch.plots[0].series, order):
    ser.format.line.color.rgb = col
    ser.format.line.width = Pt(3 if ser.name.startswith(("Sperrylite", "Cooperite")) else 1.75)
    ser.smooth = True
ch.has_title = True
ch.chart_title.text_frame.text = "Reflectance in air (%) vs wavelength (nm) — measured spectra"
ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(11)
ch.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
va = ch.value_axis; va.minimum_scale = 0; va.maximum_scale = 60
va.has_major_gridlines = True; va.major_gridlines.format.line.color.rgb = LINE; va.tick_labels.font.size = Pt(9)
ch.category_axis.tick_labels.font.size = Pt(9); ch.category_axis.format.line.color.rgb = LINE
F = SPEC["features"]
gap420 = F["sperrylite"]["R420"] - F["pentlandite"]["R420"]
gap640 = abs(F["sperrylite"]["R640"] - F["pentlandite"]["R640"])
x0 = 8.4
text(s, x0, 2.3, 4.3, 0.6, f"{gap420:.1f} pts", size=36, font=HEAD, bold=True, color=COPPER)
text(s, x0, 2.95, 4.3, 0.6, f"gap between sperrylite (Pt) and pentlandite at 420 nm — but only {gap640:.1f} pts at 640 nm. Blue light finds platinum.", size=11.5, color=MUTED, line=1.05)
tag(s, x0, 3.65, "SOURCE")
text(s, x0, 4.05, 4.3, 0.6, "Why not core-scale SWIR?", size=13, font=BODYB, bold=True)
text(s, x0, 4.38, 4.3, 1.0, "PGM grains are microns across and opaque; SWIR identifies minerals by vibrational absorption that opaque sulphides and chromite lack. The spectrum must be read through the microscope.", size=10.5, color=MUTED, line=1.05)
text(s, x0, 5.4, 4.3, 0.35, "Our build", size=13, font=BODYB, bold=True)
text(s, x0, 5.72, 4.3, 0.9, "6–8 narrow LED bands + a rotating polariser on the microscope, labelled pixel-for-pixel by QEMSCAN maps of the same polished sections.", size=10.5, color=MUTED, line=1.05)
tag(s, x0, 6.62, "ROADMAP")
source(s, "Spectra: Handbook of Mineralogy (Mineralogical Society of America), reflectance in air, mean of R1/R2 where bireflectant, from the IMA/COM Quantitative Data File. Two printed typos handled and logged in spectra.json.", y=6.98)
pic(s, G["lens_a"], 11.95, 0.7, w=0.8, name="!!lens")
morph(s)
notes(s, "SCRIPT_13b")

'''
anchor = "# ---- 14 ROADMAP & HYPOTHESES"
assert anchor in s
s = s.replace(anchor, SPECTRAL + anchor)
open(p, "w", encoding="utf-8").write(s)
print("patched")
