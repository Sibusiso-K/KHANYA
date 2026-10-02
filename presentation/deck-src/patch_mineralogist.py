"""Insert 'Why not just a mineralogist?' + how-the-mine-makes-money slide after the QEMSCAN clarification."""
import os

D = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(D, "build_deck.py")
s = open(p, encoding="utf-8").read()

slide = r'''# ---- 2c WHY NOT A MINERALOGIST + HOW THE MINE MAKES MONEY
s = new()
brand(s); pagenum(s, 0)
eyebrow(s, 0.6, 0.85, "Impact: where the money is decided")
headline(s, "A mineralogist can name the minerals.\nThe shift needs a decision, now.", y=1.15, size=30)
box(s, 0.6, 2.35, 12.15, 0.95, fill=NAVY, radius=0.12)
text(s, 0.85, 2.45, 11.7, 0.8, [[("How a mine makes money:  ", {"font": BODYB, "bold": True, "color": RGBColor(0xF2, 0x9A, 0x6A)}),
     ("tonnes milled × head grade × ", {"color": WHITE}), ("recovery", {"font": BODYB, "bold": True, "color": WHITE}),
     (" × metal price.  Tonnes, grade and price are largely set. Recovery is decided on shift: grind, reagent, air, flotation time.", {"color": WHITE})]],
     size=14, anchor=MSO_ANCHOR.MIDDLE, line=1.1)
cols3 = ["", "Mineralogist at the microscope", "REEFPRINT on site"]
rows3 = [("Who / when", "Scarce specialist, usually in a central lab, day shift", "Anyone on site, any shift, on a laptop"),
         ("What you get", "Minerals named by eye; proportions need hours of manual point counting", "Phase % and free vs locked grains, quantified in minutes"),
         ("Consistency", "Depends on the person and the day", "Same image → same answer; model and checkpoint recorded"),
         ("Decision", "Interpretation left to the metallurgist", "Act · verify · hold, with a stated reason and an exported record"),
         ("When unsure", "Judgement call", "Refuses and refers the sample to the mineralogist or QEMSCAN")]
tbl = s.shapes.add_table(len(rows3) + 1, 3, Inches(0.6), Inches(3.5), Inches(12.15), Inches(2.95)).table
for i, wv in enumerate([2.1, 5.0, 5.05]):
    tbl.columns[i].width = Inches(wv)
for r in range(len(rows3) + 1):
    for c in range(3):
        cell = tbl.cell(r, c)
        val = cols3[c] if r == 0 else rows3[r - 1][c]
        cell.text = ""
        tf = cell.text_frame
        tf.margin_left = Inches(0.1); tf.margin_right = Inches(0.06); tf.margin_top = tf.margin_bottom = Inches(0.03)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        pp = tf.paragraphs[0]
        rr = pp.add_run(); rr.text = val
        rr.font.name = BODYB if (r == 0 or c == 0) else BODY
        rr.font.bold = r == 0 or c == 0
        rr.font.size = Pt(11.5)
        rr.font.color.rgb = WHITE if r == 0 else INK
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY if r == 0 else (RGBColor(0xE3, 0xF3, 0xF3) if c == 2 else (WHITE if r % 2 else PAPER))
text(s, 0.6, 6.55, 12.15, 0.45, [[("The mineralogist stays essential: ", {"font": BODYB, "bold": True}),
     ("REEFPRINT puts a quantified, audited first answer in front of the shift, and sends the hard samples to the expert.", {"color": MUTED})]],
     size=12)
source(s, "Revenue identity: standard mining economics (payable metal = tonnes × grade × recovery; revenue = payable metal × price). Value of a recovery change: slide 11. Mineralogist comparison: qualitative, from the team's process review — not a timed study.", y=7.05)
pic(s, G["lens_a"], 11.95, 0.7, w=0.8, name="!!lens")
morph(s)
notes(s, "SCRIPT_2c")

'''
anchor = "# ---- 3 WHO IT AFFECTS"
assert anchor in s
s = s.replace(anchor, slide + anchor)
s = s.replace("REEFPRINT-KHANYA-Team-Sonar-pitch-v5.pptx", "REEFPRINT-KHANYA-Team-Sonar-pitch-v6.pptx")
open(p, "w", encoding="utf-8").write(s)
print("ok")
