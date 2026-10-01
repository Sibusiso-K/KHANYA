"""Insert the 'not a QEMSCAN image' clarification slide after the problem slide."""
import os

D = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(D, "build_deck.py")
s = open(p, encoding="utf-8").read()

prep = '''G["qemscan"] = rounded(os.path.join(IMG, "qemscan_pisoliths.png"), os.path.join(GEN, "qemscan.png"), crop=(0, 0, 1350, 921), radius=22)
G["optical"] = rounded(MICRO, os.path.join(GEN, "optical.png"), crop=(300, 250, 3300, 2297), radius=22)
'''
anchor_g = 'G["thumb_sim"] = rounded('
i = s.index(anchor_g)
i = s.index("\n", i) + 1
s = s[:i] + prep + s[i:]

slide = r'''# ---- 2b NOT A QEMSCAN IMAGE
s = new()
brand(s); pagenum(s, 0)
eyebrow(s, 0.6, 0.85, "Clearing this up first")
headline(s, "Our input is not a QEMSCAN image. It is the cheap\nphoto that QEMSCAN can teach a model to read.", y=1.15, size=28)
pic(s, G["qemscan"], 0.6, 2.35, h=3.0)
tag(s, 0.6, 5.48, "SOURCE")
text(s, 0.6, 5.8, 4.5, 0.85, [[("QEMSCAN  ", {"font": BODYB, "bold": True}),
     ("electron beam + X-ray chemistry → false-colour mineral map. Reference-grade; central lab; days to weeks; $1,500 per sample on one 2017 price list.", {"color": MUTED})]],
     size=10.5, line=1.05)
ar = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(5.55), Inches(3.45), Inches(1.6), Inches(0.62))
ar.fill.solid(); ar.fill.fore_color.rgb = COPPER; ar.line.fill.background()
text(s, 5.35, 4.15, 2.0, 0.6, "teaches", size=16, font=HEAD, bold=True, color=COPPER, align=PP_ALIGN.CENTER)
text(s, 5.35, 4.55, 2.0, 0.6, "maps become labels", size=10, color=MUTED, align=PP_ALIGN.CENTER)
pic(s, G["optical"], 7.75, 2.35, h=3.0)
tag(s, 7.75, 5.48, "LIVE APP")
text(s, 7.75, 5.8, 4.6, 0.85, [[("Reflected-light microscope  ", {"font": BODYB, "bold": True}),
     ("light reflected off the same kind of polished section → a colour photo. Minutes; a microscope most labs own; what REEFPRINT reads today.", {"color": MUTED})]],
     size=10.5, line=1.05)
box(s, 0.6, 6.55, 12.15, 0.42, fill=NAVY, radius=0.1)
text(s, 0.8, 6.6, 11.8, 0.35, [[("New: ", {"font": BODYB, "bold": True, "color": RGBColor(0xF2, 0x9A, 0x6A)}),
     ("QEMSCAN teaches; cheap optical and multispectral images predict phases, liberation and the next lab test; uncertain samples go back to QEMSCAN.", {"color": WHITE})]],
     size=11, anchor=MSO_ANCHOR.MIDDLE)
source(s, "Left: real QEMSCAN mineral map of bauxite pisoliths, FEI Company / Intellection Pty via Wikimedia Commons, CC BY-SA 3.0. Right: LumenStone S2 test_11, public reflected-light micrograph. Price: SRC Advanced Microanalysis Centre list (2017); turnaround: ALS Global FAQ.", y=7.05)
morph(s)
notes(s, "SCRIPT_2b")

'''
anchor = "# ---- 3 WHO IT AFFECTS"
assert anchor in s
s = s.replace(anchor, slide + anchor)
s = s.replace("REEFPRINT-KHANYA-Team-Sonar-pitch-v4.pptx", "REEFPRINT-KHANYA-Team-Sonar-pitch-v5.pptx")
open(p, "w", encoding="utf-8").write(s)
print("ok")
