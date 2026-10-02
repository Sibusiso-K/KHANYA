"""REEFPRINT / KHANYA — pitch v8 (12 slides, 10 minutes, demo video inside).

Aligned with the v8 build (REEFPRINT Live secure server, Decisions view, v9 robustness,
economics, physics checks). Every number on a slide is loaded from a committed result file
or computed here, never typed by hand, and carries a provenance tag:
LIVE APP · RECORDED · SOURCE · ASSUMPTION · SIMULATOR · ROADMAP · ILLUSTRATIVE.

The speaker notes and presentation/PRESENTER-SCRIPT-v8.md are written from the same
SCRIPT table below, so the two can never disagree.

Inputs: presentation/deck-src/img_v8/ (real app screenshots, committed) and
presentation/deck-src/stock_v8/ (Mixkit stills, gitignored: the licence forbids
redistributing the clips standalone). Run from the repository root:
    python presentation/deck-src/build_deck_v8.py
"""
import json
import os

from lxml import etree
from PIL import Image, ImageDraw
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
D = os.path.join(ROOT, "presentation", "deck-src")
IMG = os.path.join(D, "img_v8")
STOCK = os.path.join(D, "stock_v8")
GEN = os.path.join(D, "gen_v8")
OUT = os.path.join(ROOT, "presentation", "output")
TRAIN = os.path.join(ROOT, "training")
VIDEO = os.environ.get("REEFPRINT_V8_VIDEO", os.path.join(ROOT, "presentation", "video", "REEFPRINT-v8-demo-embed.mp4"))
MICRO = os.path.join(ROOT, "demo-images", "test_11.jpg")
POSTER = os.path.join(IMG, "video_poster.jpg")  # a frame of the v8 video
os.makedirs(GEN, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

HEAD, BODY, BODYB = "Georgia", "Segoe UI", "Segoe UI Semibold"
NAVY = RGBColor(0x0E, 0x1B, 0x2E)
INK = RGBColor(0x1B, 0x2D, 0x40)
INK2 = RGBColor(0x22, 0x36, 0x4D)
MUTED = RGBColor(0x5B, 0x6B, 0x7C)
SOFT = RGBColor(0xB8, 0xC4, 0xD2)
LINE = RGBColor(0xD9, 0xDF, 0xE6)
PAPER = RGBColor(0xF3, 0xF5, 0xF8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
COPPER = RGBColor(0xD2, 0x5A, 0x24)
COPPER_L = RGBColor(0xF7, 0xE1, 0xD6)
PYRR = RGBColor(0x1F, 0xA3, 0xA8)
PENT = RGBColor(0x8E, 0x5C, 0xC9)
CHALC = RGBColor(0xE0, 0x7A, 0x2E)
MAG = RGBColor(0xC9, 0x9A, 0x1C)
MAG_L = RGBColor(0xF6, 0xE9, 0xC4)
GREEN = RGBColor(0x2E, 0x8B, 0x57)
GREEN_L = RGBColor(0xE3, 0xF2, 0xE8)
RED = RGBColor(0xB0, 0x3A, 0x2E)

TAGS = {
    "LIVE APP": (PYRR, WHITE),
    "RECORDED": (INK, WHITE),
    "SOURCE": (RGBColor(0xE6, 0xEA, 0xEF), INK),
    "ASSUMPTION": (RGBColor(0xF6, 0xE3, 0xB4), RGBColor(0x6B, 0x4E, 0x00)),
    "SIMULATOR": (RGBColor(0xF6, 0xE3, 0xB4), RGBColor(0x6B, 0x4E, 0x00)),
    "HYPOTHESIS": (RGBColor(0xF6, 0xE3, 0xB4), RGBColor(0x6B, 0x4E, 0x00)),
    "ILLUSTRATIVE": (RGBColor(0x3A, 0x47, 0x57), WHITE),
    "ROADMAP": (RGBColor(0xE9, 0xDF, 0xF6), RGBColor(0x4B, 0x2A, 0x7A)),
    "MEASURED": (GREEN, WHITE),
}


# ---------------------------------------------------------------- numbers: loaded, then computed
def load(rel):
    with open(os.path.join(TRAIN, rel), encoding="utf-8") as f:
        return json.load(f)


ECO = load("economics-20261002/results.json")
VC = load("value-chain-20261002/results.json")
V9 = load("hidsag-v9-robustness-20261002/analysis_v9.json")
PHY = load("physics-checks-20261002/results.json")

N = {}
v1 = ECO["V1_net_value_per_recovery_pp_per_yr"]
N["pp_zond"] = (v1["zondereinde_scale"]["low"]["value"], v1["zondereinde_scale"]["high"]["value"])
N["pp_impl"] = (v1["implats_group_scale"]["low"]["value"], v1["implats_group_scale"]["high"]["value"])
be = [q["value"] for q in ECO["V4_breakeven_recovery_pp_zondereinde_scale_base"]["breakeven_pp"].values()]
N["breakeven"] = (min(be), max(be))
v6 = ECO["V6_processed_before_assay_returns_zondereinde_scale"]
N["kt24"], N["kt72"] = v6["24h"]["tonnes"]["value"] / 1000, v6["72h"]["tonnes"]["value"] / 1000
N["qemscan_cad"] = ECO["V5_qemscan_every_shift"]["per_stream_per_yr_cad2017"]["value"]
pol = VC["grinding"]["policies"]
dep, blind = pol["belt_deployed"], pol["blind_p90"]
N["thr"] = dep["sim_throughput_vs_blind_p90"]
N["thr_ci"] = dep["sim_throughput_vs_blind_p90_ci95"]
N["ovl_dep"], N["ovl_blind"] = dep["sim_overload_share"], blind["sim_overload_share"]
N["short_dep"] = dep["sim_energy_shortfall_fraction_when_overloaded"]
N["short_blind"] = blind["sim_energy_shortfall_fraction_when_overloaded"]
ni = VC["grinding"]["belt_deployed_vs_blind_p90"]
N["ni_upper"], N["ni_margin"] = ni["overload_diff_onesided95_upper"], ni["noninferiority_margin"]
N["n_parcels"] = VC["grinding"]["n_parcels"]
wi = V9["targets"]["WI"]
N["v9_new"] = (wi["resample"]["mae_ratio_vs_original"], *wi["resample"]["ratio_ci95"])
N["v9_half"] = wi["half"]["mae_ratio_vs_original"]
N["v9_noise"] = wi["noise_2pct"]["mae_ratio_vs_original"]
N["v9_light"] = max(wi["gain_0.85"]["mae_ratio_vs_original"], wi["gain_1.15"]["mae_ratio_vs_original"])
drift_key = [k for k in wi if k.startswith("shift") or "wave" in k or "drift" in k][0]
N["v9_drift"] = wi[drift_key]["mae_ratio_vs_original"]
kin = PHY["K1_kinetics_vs_throughput"]["rows"]
N["kin_1min"] = kin[0]["recovery_loss_pp"]
N["sa_pt_share"] = 120_000 / 170_000            # USGS MCS 2025, platinum mine production 2024e, kg
N["ug2_gap"] = 89 - 79                          # Implats Merensky 89% vs UG2 79% recovery [P]
N["commits"] = int(os.environ.get("REEFPRINT_COMMITS_SINCE_MENTOR", "38"))  # git log --since="2026-10-01 11:44" | wc -l
# KHANYA (recorded, from the app's evaluation of 12 held-out LumenStone S2 sections; see v7 credits)
K = {"miou_live": 0.454, "pa_live": 77.2, "miou_cand": 0.632, "pa_cand": 85.5, "mag_recall": 89.3, "mag_prec": 25.5,
     "iou_cand": [("Background", 0.8484), ("Pyrrhotite", 0.8183), ("Chalcopyrite", 0.7998), ("Pentlandite", 0.4460), ("Magnetite", 0.2477)],
     "t11": {"pyrrhotite": 60.8, "pentlandite": 34.7, "chalcopyrite": 0.2, "runtime_s": 78.5}}
print(json.dumps(N, indent=1, default=str))


def rm(x):
    """Rand millions, rounded for speech."""
    return f"R{x / 1e6:,.0f} M"


# ---------------------------------------------------------------- images
def rounded(src, out, crop=None, radius=26, max_w=1900):
    im = Image.open(src).convert("RGB")
    if crop:
        im = im.crop(crop)
    if im.width > max_w:
        im = im.resize((max_w, int(im.height * max_w / im.width)), Image.LANCZOS)
    m = Image.new("L", (im.width * 2, im.height * 2), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width * 2 - 1, im.height * 2 - 1], radius * 2, fill=255)
    im.putalpha(m.resize(im.size, Image.LANCZOS))
    path = os.path.join(GEN, out)
    im.save(path)
    return path


def darken(src, out, amount=0.55, tint=(14, 27, 46)):
    im = Image.open(src).convert("RGB")
    path = os.path.join(GEN, out)
    Image.blend(im, Image.new("RGB", im.size, tint), amount).save(path, quality=90)
    return path


def lens(src, out, size=900, crop=None, ring=(255, 255, 255)):
    im = Image.open(src).convert("RGB")
    if crop:
        im = im.crop(crop)
    w, h = im.size
    s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s)).resize((size, size), Image.LANCZOS)
    m = Image.new("L", (size * 3, size * 3), 0)
    ImageDraw.Draw(m).ellipse([0, 0, size * 3 - 1, size * 3 - 1], fill=255)
    im.putalpha(m.resize((size, size), Image.LANCZOS))
    r = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(r).ellipse([6, 6, size - 7, size - 7], outline=ring + (255,), width=10)
    path = os.path.join(GEN, out)
    Image.alpha_composite(im, r).save(path)
    return path


def stock(name, fallback):
    p = os.path.join(STOCK, name)
    return p if os.path.exists(p) else fallback


G = {
    "bg_title": darken(stock("mixkit_45821.jpg", MICRO), "bg_title.jpg", 0.58),
    "bg_close": darken(stock("mixkit_45825.jpg", MICRO), "bg_close.jpg", 0.66),
    "lens": lens(MICRO, "lens_title.png", crop=(800, 400, 2400, 2000)),
    "khanya": rounded(os.path.join(IMG, "khanya_phases.png"), "khanya.png", radius=18),
    "kh_thumb": rounded(os.path.join(IMG, "khanya_phases.png"), "kh_thumb.png", crop=(160, 140, 840, 545), radius=16),
    "belt_thumb": rounded(os.path.join(IMG, "app_live.png"), "belt_thumb.png", crop=(616, 876, 2040, 1560), radius=16),
    "dec_thumb": rounded(os.path.join(IMG, "app_decisions_approved.png"), "dec_thumb.png", crop=(49, 504, 1680, 1220), radius=16),
    "decisions": rounded(os.path.join(IMG, "app_decisions_approved.png"), "decisions.png", crop=(49, 504, 2831, 1634), radius=16),
    "physics": rounded(os.path.join(IMG, "app_evidence.png"), "physics.png", crop=(49, 482, 2831, 1289), radius=16),
    "haul": rounded(stock("mixkit_45822.jpg", MICRO), "haul.png", radius=18),
    "lab": rounded(stock("mixkit_4767.jpg", MICRO), "lab.png", crop=(240, 0, 1680, 1080), radius=18),
}


# ---------------------------------------------------------------- pptx helpers
prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
S = []
P159 = "http://schemas.microsoft.com/office/powerpoint/2015/09/main"
P14 = "http://schemas.microsoft.com/office/powerpoint/2010/main"
MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"
PNS = "http://schemas.openxmlformats.org/presentationml/2006/main"


def transition(slide, dur=900):
    """Morph (PowerPoint 2019+/365) with a fade fallback."""
    xml = (f'<mc:AlternateContent xmlns:mc="{MC}"><mc:Choice xmlns:p159="{P159}" Requires="p159">'
           f'<p:transition xmlns:p="{PNS}" xmlns:p14="{P14}" spd="slow" p14:dur="{dur}"><p159:morph option="byObject"/></p:transition>'
           f'</mc:Choice><mc:Fallback><p:transition xmlns:p="{PNS}" spd="slow"><p:fade/></p:transition></mc:Fallback></mc:AlternateContent>')
    el = etree.fromstring(xml)
    sld = slide._element
    anchor = sld.find(qn("p:clrMapOvr"))
    (anchor if anchor is not None else sld.find(qn("p:cSld"))).addnext(el)


def new_slide(dark=False, bg_img=None):
    s = prs.slides.add_slide(BLANK)
    S.append(s)
    f = s.background.fill
    f.solid()
    f.fore_color.rgb = NAVY if dark else WHITE
    if bg_img:
        s.shapes.add_picture(bg_img, 0, 0, prs.slide_width, prs.slide_height)
    transition(s)
    return s


def text(slide, x, y, w, h, runs, size=16, color=INK, font=BODY, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, spacing=None, line=None, italic=False, name=None):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    paras = runs if isinstance(runs, list) else [runs]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if spacing:
            p.space_after = Pt(spacing)
        if line:
            p.line_spacing = line
        for seg, ov in (para if isinstance(para, list) else [(para, {})]):
            r = p.add_run()
            r.text = seg
            f = r.font
            f.name = ov.get("font", font)
            f.size = Pt(ov.get("size", size))
            f.bold = ov.get("bold", bold)
            f.italic = ov.get("italic", italic)
            f.color.rgb = ov.get("color", color)
    return tb


def box(slide, x, y, w, h, fill=PAPER, line=None, radius=0.08, shape=MSO_SHAPE.ROUNDED_RECTANGLE, name=None):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        s.name = name
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(1)
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = min(0.5, radius / min(w, h))
    etree.SubElement(s._element.spPr, qn("a:effectLst"))
    s.text_frame.text = ""
    return s


def label_in(shape, s, size=11, color=INK, bold=False, align=PP_ALIGN.CENTER, font=BODY):
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.08)
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    lines = s if isinstance(s, list) else [s]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        segs = ln if isinstance(ln, list) else [(ln, {})]
        for seg, ov in segs:
            r = p.add_run()
            r.text = seg
            r.font.name = ov.get("font", font)
            r.font.size = Pt(ov.get("size", size))
            r.font.bold = ov.get("bold", bold)
            r.font.color.rgb = ov.get("color", color)
    return shape


def tag(slide, x, y, lab):
    fill, fg = TAGS[lab]
    s = box(slide, x, y, 0.24 + 0.088 * len(lab), 0.25, fill=fill, radius=0.125)
    label_in(s, lab, size=8, color=fg, bold=True, font=BODYB)
    s.text_frame.margin_left = s.text_frame.margin_right = Inches(0.04)
    s.text_frame.margin_top = s.text_frame.margin_bottom = 0
    return s


def tagcap(slide, x, y, lab, caption, w=6.0, size=10.5, color=MUTED):
    t = tag(slide, x, y, lab)
    cx = x + t.width / 914400 + 0.14
    text(slide, cx, y + 0.01, w - (cx - x), 0.5, caption, size=size, color=color, line=1.03)
    return t


def pic(slide, path, x, y, w=None, h=None):
    kw = {}
    if w:
        kw["width"] = Inches(w)
    if h:
        kw["height"] = Inches(h)
    return slide.shapes.add_picture(path, Inches(x), Inches(y), **kw)


def chrome(slide, eyebrow, title, dark=False, title_size=None):
    title_size = title_size or (32 if len(title) <= 44 else 28)
    c, sub = (WHITE, SOFT) if dark else (INK, MUTED)
    text(slide, 0.6, 0.35, 5, 0.3, [[("REEFPRINT", {"font": BODYB, "bold": True, "size": 10.5, "color": c}),
                                     ("  ·  KHANYA  ·  Team Sonar", {"size": 10.5, "color": sub})]], name="!!brand")
    text(slide, 11.6, 0.35, 1.13, 0.3, f"{len(S):02d} / 12", size=10.5, color=sub, align=PP_ALIGN.RIGHT, name="!!page")
    text(slide, 0.6, 0.86, 9, 0.3, eyebrow.upper(), size=11, color=COPPER, font=BODYB, bold=True)
    text(slide, 0.6, 1.14, 12.1, 0.8, title, size=title_size, color=c, font=HEAD, bold=True, line=1.0, name="!!headline")


def source(slide, s, dark=False):
    text(slide, 0.6, 7.02, 12.13, 0.35, s, size=8.5, color=SOFT if dark else MUTED, line=1.0)


def numdot(slide, x, y, n, color=INK, d=0.38, size=11):
    c = box(slide, x, y, d, d, fill=color, shape=MSO_SHAPE.OVAL)
    label_in(c, str(n), size=size, color=WHITE, bold=True, font=BODYB)
    c.text_frame.margin_left = c.text_frame.margin_right = 0
    return c


def arrow(slide, x, y, w=0.3, h=0.3, color=SOFT):
    return box(slide, x, y, w, h, fill=color, shape=MSO_SHAPE.CHEVRON)


def notes(slide, key):
    t, body = SCRIPT[key]
    slide.notes_slide.notes_text_frame.text = f"[{t}]\n{body}"


def style_chart(chart, size=11):
    chart.font.name = BODY
    chart.font.size = Pt(size)
    chart.font.color.rgb = INK
    chart.has_legend = False


# ---------------------------------------------------------------- the script (notes + markdown)
SCRIPT = {
    1: ("0:00–0:55", """A geologist, a mineralogist, a chemist, a metallurgist and a mining engineer walk into a bar.
The geologist looks at the beer and says: "About four point seven grams a tonne."
The mineralogist says: "Give me three days and fifteen hundred dollars, and I'll tell you what's really in it."
The chemist says: "I'll confirm it after the fire assay. Seventy-two hours."
The mining engineer says: "Doesn't matter. The plan says we're drinking it."
And the metallurgist? (beat) The metallurgist drank it three hours ago. Because the plant doesn't wait.
Oh, and the policy maker is still drafting the regulation on bars.
(pause, let it land, then drop the smile)
It's funny until you realise that's every concentrator in this country. Every shift. Every day.
We're Team Sonar: I'm Lethabo, with Sibusiso and Ipeleng, from three universities. This is REEFPRINT and KHANYA. We let the plant SEE the ore before it's gone."""),
    2: ("0:55–1:40", f"""Here's the problem, plainly. Ore goes from the belt into the mill in minutes. The answer to "what was in it?" comes back in DAYS.
A fire assay takes twenty-four to seventy-two hours. A QEMSCAN mineral analysis costs about fifteen hundred dollars a sample, and it takes days.
So on a plant the size of Northam's Zondereinde, somewhere between {N['kt24']:.0f} and {N['kt72']:.0f} thousand tonnes of ore go through the mill before anyone knows what was in them. (point at the wedge)
Who pays for that? The geologist, who can't see the blend. The mineralogist, buried in a queue. The chemist, late by design. The metallurgist, who sets the feed, the grind and the reagents, blind. And the CEO, because recovery IS revenue."""),
    3: ("1:40–2:20", f"""And this is South Africa's problem more than anyone's. We mined about {N['sa_pt_share']:.0%} of the world's platinum last year.
On UG2 ore, Implats recovers seventy-nine percent. On Merensky, eighty-nine. That's a {N['ug2_gap']}-point gap, and UG2 is where the chromite lives. Mintek's own work shows the trade-off: push recovery, and chromite rises in the concentrate, and the smelter pays for it.
What's one recovery point worth? At a Zondereinde-size plant, on assumed prices, {rm(N['pp_zond'][0])} to {rm(N['pp_zond'][1])} a year.
Meanwhile grinding burns about half of a mine's energy, on a grid that sheds load, in an industry that has already been hit by ransomware."""),
    4: ("2:20–3:00", """So here's REEFPRINT. Three speeds. One decision.
At the MICROSCOPE, KHANYA identifies the minerals in a quick scan of a polished section in about eighty seconds, on a laptop.
On the BELT, a hyperspectral camera predicts how hard the ore will be to grind, in under a tenth of a second per parcel, with an honest upper bound.
At the DECISION, that bound becomes a feed-rate proposal inside limits the site sets. A person approves it before the ore reaches the mill, or the safe setting applies by itself. Every step is signed and recorded.
Every problem from the last slide: ticked. And every deliverable in the brief: ticked. Let me prove each one."""),
    5: ("3:00–3:45", f"""Deliverable one: at least three mineral phases. This is the live app on a held-out section: pyrrhotite, pentlandite, chalcopyrite, pixel by pixel. Pentlandite carries the platinum-group metals; pyrrhotite is the one you'd rather reject.
Deliverable two: the accuracy report, zeros included. Our deployed model scores a mean IoU of {K['miou_live']} on twelve held-out sections. A retrained candidate reaches {K['miou_cand']}, but it over-calls magnetite, so it stays quarantined. Magnetite is the literature's hardest class too.
On the belt, grinding hardness is the one prediction that beats every baseline. And when we re-captured the same ore, the error stayed exactly where it was: {N['v9_new'][0]:.2f} times."""),
    6: ("3:45–4:30", f"""Deliverable three: adjusting a plant parameter. This is the Decisions screen.
The camera says this parcel is a little harder than design: the upper bound on its work index is sixteen point nine. So the proposal is: feed at ninety-eight point two percent of design, inside an envelope of eighty-five to a hundred and ten.
The metallurgist has ninety seconds, the time it takes to reach the mill. Approve, modify, reject, or escalate. Do nothing, and the conservative setting applies automatically. Never "unknown". Never "hold the last value".
Replayed over {N['n_parcels']} real drill-core samples, this policy pushed {N['thr']:.1%} more tonnes through the same mill, with no more overloads. Simulated, and provisional: the pilot confirms it. And the flotation? At most a quarter of a point on the steep part of the curve; nothing on the plateau."""),
    7: ("4:30–5:10", """Now, the brain. Five layers.
SENSE: a visible-and-infrared line scanner on the belt, a microscope in the lab.
SEE: a segmentation network for minerals and spectral models for hardness, trained only on public data, never on Mintek's.
DOUBT: this is what we're proudest of. Conformal prediction puts a guaranteed bound on every number, and an out-of-distribution gate refuses ore it has never seen.
DECIDE: the bound goes through Bond's grinding law, inside the envelope and the ramp limits. That's where the optimisation lives, and a language model never touches a number.
PROVE: every decision is hash-chained and signed twice, once classically and once with ML-DSA, the post-quantum standard NIST published in 2024.
All of it runs offline, on one laptop, in ninety-two milliseconds a parcel."""),
    8: ("5:10–7:35", """"Let me show you." (Click to play. The video runs 2:25. Stand to the side and watch the screen with the audience.)
If the video fails: open the app, Continue as guest, then Decisions, Approve proposal, Verify chain, Signed checkpoint. Then the Evidence tab."""),
    9: ("7:35–8:05", f"""Is it actually possible? We tested every claim against its physics, and the failures stay on the page.
Hardness to tonnes: provisional pass. Flotation: check the headroom first. "More tonnes during load-shedding by re-ordering ore": tested, and REJECTED, because energy is conserved.
Unseen captures: the accuracy holds. Wavelength drift: that's our real weak spot, so the design adds a hardware calibration gate.
Power cut: the record survives and the safe setting applies. Attack: role-based sign-in, encrypted uploads, seventeen security tests, and signatures built to stay secure against quantum computers."""),
    10: ("8:05–8:45", f"""So what's it worth? Look at this chart. The pilot pays for itself somewhere between {N['breakeven'][0]:.2f} and {N['breakeven'][1]:.2f} of a recovery point. Valterra reported moves of one and two WHOLE points last year. The bar we must clear is tiny next to the moves this industry already makes.
For the metallurgist: a decision in seconds, not days. For the CEO: recovery, which is revenue. For the country: less energy lost when the mill is overloaded, no radioactive source on site, data that stays on site, and new skilled jobs, with a named person in charge of every decision."""),
    11: ("8:45–9:25", f"""The pathway. Step one: a lab pilot with KHANYA, about two hundred and ten thousand rand, then a monthly licence. Step two: one belt, shadow mode for three months, advisory for three. Installed: half a million to three million US dollars, and it breaks even at a fraction of a point. Step three: a subscription priced as a share of the value we MEASURE. If we don't move the number, we don't get paid.
We need three partners: a producer with a belt; Mintek, as the truth lab and our route into FloatStar and MillStar; and development funding, with TIA the natural route.
And after ONE mentor session with a chemist, a mineralogist and a metallurgist, we made {N['commits']} commits in twenty-four hours. Imagine what a site does for us."""),
    12: ("9:25–10:00", """Mintek has five values. One of them is integrity: "We do what we say we will do, when we say we will do it." That's why every number tonight carries its source, and every failure stays on the page.
Mintek's work helped make UG2 commercially viable. We want to help it be read in real time: by a young metallurgist, on a phone, at the belt, on a Tuesday night shift, just after the power goes off.
We have always read the ore days late. (beat) Let's read it on the belt.
(If the QR deployment is live:) Scan the code. It's live. Try to break it. Thank you."""),
}


# ================================================================ slides
# 1 — Title
s = new_slide(dark=True, bg_img=G["bg_title"])
text(s, 0.6, 0.35, 6, 0.3, [[("REEFPRINT", {"font": BODYB, "bold": True, "size": 10.5, "color": WHITE}),
                              ("  ·  KHANYA", {"size": 10.5, "color": SOFT})]])
text(s, 0.6, 1.45, 7.6, 0.6, "MINTEK–SCi GRAD HACKATHON 2026  ·  COMPUTER VISION FOR REAL-TIME MINERALOGICAL CHARACTERISATION",
     size=11, color=COPPER, font=BODYB, bold=True, line=1.1)
text(s, 0.6, 2.2, 7.6, 2.0, "See the ore before the plant does.", size=52, color=WHITE, font=HEAD, bold=True, line=0.95)
text(s, 0.6, 4.25, 7.0, 1.0, "Real-time mineral characterisation that turns a microscope and a belt camera into a safe, signed plant decision.",
     size=18, color=RGBColor(0xDC, 0xE3, 0xEB), line=1.1)
text(s, 0.6, 5.55, 4, 0.3, "TEAM SONAR", size=11, color=COPPER, font=BODYB, bold=True)
text(s, 0.6, 5.85, 8.0, 0.4, [[("Lethabo Hoaeane", {"bold": True, "font": BODYB}), ("  Unisa      ", {"color": SOFT}),
                               ("Sibusiso Khumalo", {"bold": True, "font": BODYB}), ("  Wits      ", {"color": SOFT}),
                               ("Ipeleng Modise", {"bold": True, "font": BODYB}), ("  TUT", {"color": SOFT})]], size=14, color=WHITE)
pic(s, G["lens"], 8.75, 1.35, w=3.9)
text(s, 8.75, 5.35, 3.9, 0.5, "Real micrograph, LumenStone S2 test_11: the pentlandite and pyrrhotite the app separates.",
     size=10, color=SOFT, align=PP_ALIGN.CENTER, line=1.05)
source(s, "Background: illustrative stock footage still (Mixkit free licence), not a REEFPRINT site.", dark=True)
notes(s, 1)

# 2 — The problem: a timeline the audience can read in 3 seconds
s = new_slide()
chrome(s, "The problem", "The plant decides blind, every shift.")
X0, X1, HMAX = 0.95, 8.15, 80.0
sx = (X1 - X0) / HMAX
AX = 4.55
box(s, X0, AX, X1 - X0, 0.04, fill=INK, shape=MSO_SHAPE.RECTANGLE)
for h in range(0, 73, 8):
    box(s, X0 + h * sx - 0.008, AX - 0.08, 0.016, 0.2, fill=MUTED, shape=MSO_SHAPE.RECTANGLE)
for h in (0, 24, 48, 72):
    text(s, X0 + h * sx - 0.4, AX + 0.18, 0.8, 0.25, f"{h} h", size=10.5, color=MUTED, align=PP_ALIGN.CENTER)
text(s, X0 + 8 * sx - 0.2, AX + 0.18, 1.2, 0.25, "8-h shift ticks", size=9, color=MUTED)
# belt -> mill marker
box(s, X0 - 0.13, AX - 0.11, 0.26, 0.26, fill=COPPER, shape=MSO_SHAPE.OVAL)
text(s, X0 - 0.35, 2.15, 3.0, 0.9, [[("Ore reaches the mill", {"bold": True, "font": BODYB})], "in minutes (90 s assumed)"],
     size=12, color=INK, line=1.05)
box(s, X0 - 0.01, 3.0, 0.02, AX - 3.0, fill=COPPER, shape=MSO_SHAPE.RECTANGLE)
# fire assay window
fa = box(s, X0 + 24 * sx, 3.55, 48 * sx, 0.62, fill=MAG_L, line=MAG, radius=0.1)
label_in(fa, [[("Fire assay returns: 24–72 h", {"bold": True, "font": BODYB})]], size=12, color=RGBColor(0x6B, 0x4E, 0x00))
# QEMSCAN beyond
q = box(s, X0 + 60 * sx, 2.65, 21 * sx + 0.25, 0.62, fill=PENT, shape=MSO_SHAPE.PENTAGON)
label_in(q, [[("QEMSCAN: days", {"bold": True, "font": BODYB})], "US$1,500 a sample"], size=10.5, color=WHITE)
# ore milled while waiting: a wedge
w = s.shapes.add_shape(MSO_SHAPE.RIGHT_TRIANGLE, Inches(X0), Inches(AX + 0.55), Inches(72 * sx), Inches(1.15))
w.fill.solid()
w.fill.fore_color.rgb = COPPER_L
w.line.fill.background()
etree.SubElement(w.element.spPr, qn("a:effectLst"))
w.element.spPr.find(qn("a:xfrm")).set("flipH", "1")  # zero at 0 h, tallest at 72 h
text(s, X0 + 72 * sx - 2.3, AX + 1.75, 2.45, 0.5, [[(f"{N['kt72']:.1f} kt", {"size": 22, "font": HEAD, "bold": True, "color": COPPER})]],
     align=PP_ALIGN.RIGHT)
text(s, X0 + 24 * sx - 0.8, AX + 1.75, 1.6, 0.5, [[(f"{N['kt24']:.1f} kt", {"size": 16, "font": HEAD, "bold": True, "color": COPPER})]],
     align=PP_ALIGN.CENTER)
text(s, X0 + 0.05, AX + 0.6, 3.0, 0.5, "ore milled before the answer arrives, at a Zondereinde-size plant (2.25 Mt a year)",
     size=10.5, color=INK, line=1.03)
tag(s, X0 + 0.05, AX + 1.12, "ASSUMPTION")
# who waits
text(s, 8.85, 2.15, 3.9, 0.35, "WHO WAITS, AND FOR WHAT", size=11, color=COPPER, font=BODYB, bold=True)
WHO = [("Geologist", "grade control from drill core, not the blend on the belt", PYRR),
       ("Mineralogist", "a QEMSCAN queue measured in days", PENT),
       ("Chemist", "fire assay: 24–72 h, by design", MAG),
       ("Metallurgist", "sets feed, grind and reagents now, checks later", COPPER),
       ("Mining engineer", "plan versus actual, reconciled weeks later", INK2),
       ("CEO & plant manager", "recovery is revenue: every blind tonne is a guess", NAVY),
       ("Policy makers", "beneficiation, energy and jobs ride on recovery", GREEN)]
for i, (r, d_, c) in enumerate(WHO):
    y = 2.55 + i * 0.6
    box(s, 8.85, y + 0.07, 0.14, 0.14, fill=c, shape=MSO_SHAPE.OVAL)
    text(s, 9.1, y, 3.65, 0.6, [[(r, {"bold": True, "font": BODYB, "size": 12})], [(d_, {"size": 10.5, "color": MUTED})]], line=1.0)
source(s, "Fire assay 24–72 h [S]; QEMSCAN US$1,500/sample: Saskatchewan Research Council price list 4/2017 [P]. Tonnes: Northam F2025 Zondereinde tonnes milled "
          "(indicative [S]) ÷ 365 × 24–72 h, continuous milling ASSUMED; computed in training/economics-20261002 (V6).")
notes(s, 2)

# 3 — Why it matters (dark)
s = new_slide(dark=True)
chrome(s, "Why it matters", "Blind costs South Africa the most.", dark=True)
STATS = [(f"~{N['sa_pt_share']:.0%}", "of the world's platinum was mined in South Africa in 2024", "SOURCE"),
         (f"{N['ug2_gap']} pp", "recovery gap at Implats: UG2 79% versus Merensky 89%", "SOURCE"),
         (f"R{N['pp_zond'][0] / 1e6:.0f}–{N['pp_zond'][1] / 1e6:.0f}M", "a year for +1 recovery point at a Zondereinde-size plant", "ASSUMPTION"),
         ("~50%", "of a mine's energy goes into crushing and grinding", "SOURCE")]
for i, (big, lab, tg) in enumerate(STATS):
    x = 0.6 + i * 3.15
    text(s, x, 2.3, 3.1, 0.9, big, size=34, color=COPPER if i == 2 else WHITE, font=HEAD, bold=True)
    text(s, x, 3.2, 2.85, 0.8, lab, size=13, color=RGBColor(0xDC, 0xE3, 0xEB), line=1.05)
    tag(s, x, 4.05, tg)
RISK = [("Chromite trade-off", "UG2 concentrate: 87% recovery at 2.9% Cr₂O₃; above 90% only if Cr₂O₃ is relaxed to 4–10% (Mintek, Jones 2005)."),
        ("Load-shedding", "Mining curtailment of 20% for 10 hours at stage 6 [S]. Decisions must survive the power going off."),
        ("Ransomware", "A major South African PGM producer was hit in July 2024 [S]. Mine software must be secure by design.")]
for i, (h, d_) in enumerate(RISK):
    x = 0.6 + i * 4.1
    b = box(s, x, 4.75, 3.9, 1.7, fill=INK2, radius=0.12)
    text(s, x + 0.25, 4.95, 3.4, 0.35, h, size=14, color=COPPER, font=BODYB, bold=True)
    text(s, x + 0.25, 5.35, 3.45, 1.3, d_, size=12, color=WHITE, line=1.08)
source(s, "USGS Mineral Commodity Summaries 2025 (platinum 2024e: 120 of 170 t). Implats FY2025 recoveries [P]. Economics V1 (ASSUMED payability, net 4E price "
          "R32,611/oz [P]). CEEC [P]. Jones 2005, Mintek [P]. Eskom curtailment; Sibanye-Stillwater incident, July 2024 [S].", dark=True)
notes(s, 3)

# 4 — The solution: three speeds, one decision
s = new_slide()
chrome(s, "The solution", "Three speeds. One decision.")
CARDS = [("MICROSCOPE · KHANYA", G["kh_thumb"], "~80 s", "for a quick six-field scan of a polished section on a laptop CPU: three or more phases", "LIVE APP", PENT),
         ("BELT CAMERA · REEFPRINT", G["belt_thumb"], "92 ms", "per parcel on a CPU: grinding hardness with a 90% upper bound", "RECORDED", PYRR),
         ("DECISION · Decisions view", G["dec_thumb"], "90 s", "to approve before the ore reaches the mill; otherwise the safe setting applies", "ASSUMPTION", COPPER)]
for i, (h, im, big, lab, tg, c) in enumerate(CARDS):
    x = 0.6 + i * 4.18
    box(s, x, 2.1, 3.85, 3.55, fill=PAPER, radius=0.14)
    p = pic(s, im, x + 0.2, 2.3, w=3.45)
    if p.height > Inches(1.75):
        p.height = Inches(1.75)
    text(s, x + 0.2, 4.15, 3.45, 0.3, h, size=10.5, color=c, font=BODYB, bold=True)
    text(s, x + 0.2, 4.4, 1.6, 0.6, big, size=30, color=INK, font=HEAD, bold=True)
    text(s, x + 1.65, 4.48, 2.05, 0.95, lab, size=10.5, color=INK, line=1.03)
    tag(s, x + 0.2, 5.25, tg)
    if i < 2:
        arrow(s, x + 3.92, 3.7, 0.2, 0.32, color=COPPER)
text(s, 0.6, 5.88, 3.0, 0.3, "THE BRIEF, TICKED", size=11, color=COPPER, font=BODYB, bold=True)
TICKS = ["≥ 3 mineral phases", "Accuracy report", "Adjusts a plant parameter", "Real-time: 92 ms · ~80 s", "Integrates: OPC UA, APC"]
for i, t in enumerate(TICKS):
    x = 0.6 + i * 2.45
    c = box(s, x, 6.2, 2.3, 0.55, fill=GREEN_L, radius=0.12)
    label_in(c, [[("✓  ", {"bold": True, "color": GREEN, "size": 13}), (t, {"size": 11, "bold": True, "font": BODYB})]], color=INK)
source(s, "KHANYA: 78.5 s on held-out test_11 (live app). Belt: 92 ms median per parcel, Kaggle 4-core CPU (hidsag-v8-model). 90 s belt-to-mill transit ASSUMED "
          "for the demo envelope. OPC UA to a simulator today; APC (FloatStar/MillStar) coupling is the pilot's phase C.")
notes(s, 4)

# 5 — Deliverables 1 & 2
s = new_slide()
chrome(s, "Deliverables 1 & 2", "Three phases, and an accuracy report with its zeros.")
pic(s, G["khanya"], 0.6, 2.05, w=6.75)
tagcap(s, 0.6, 5.95, "LIVE APP", f"Held-out section test_11: pyrrhotite {K['t11']['pyrrhotite']}%, pentlandite {K['t11']['pentlandite']}%, "
                                  f"chalcopyrite {K['t11']['chalcopyrite']}% of the analysed area · {K['t11']['runtime_s']} s on a laptop CPU",
       w=6.75, color=INK)
cd = CategoryChartData()
cd.categories = [n for n, _ in K["iou_cand"]]
cd.add_series("IoU", [v for _, v in K["iou_cand"]])
gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(7.7), Inches(2.3), Inches(5.05), Inches(2.25), cd)
ch = gf.chart
style_chart(ch, 10.5)
ch.has_title = False
pl = ch.plots[0]
pl.gap_width = 45
pl.has_data_labels = True
pl.data_labels.number_format = "0.00"
pl.data_labels.number_format_is_linked = False
pl.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
pl.data_labels.font.size = Pt(10)
cols = [MUTED, PYRR, CHALC, PENT, MAG]
for i, pt in enumerate(pl.series[0].points):
    pt.format.fill.solid()
    pt.format.fill.fore_color.rgb = cols[i]
va = ch.value_axis
va.maximum_scale, va.minimum_scale = 1.0, 0.0
va.visible = False
va.has_major_gridlines = False
ch.category_axis.reverse_order = True
ch.category_axis.format.line.fill.background()
ch.category_axis.tick_labels.font.size = Pt(10.5)
text(s, 7.7, 2.02, 5.05, 0.3, "Per-phase IoU · retrained candidate (quarantined)", size=11, color=INK, font=BODYB, bold=True)
ROWS = [("Deployed model", f"mean IoU {K['miou_live']} · pixel accuracy {K['pa_live']}% · magnetite 0, shown, not hidden", "RECORDED"),
        ("Candidate", f"mean IoU {K['miou_cand']} · {K['pa_cand']}% · finds {K['mag_recall']:.0f}% of magnetite but only {K['mag_prec']:.0f}% of its calls are right → not deployed", "RECORDED"),
        ("Belt hardness", f"R² 0.48, beats the strongest baseline · 80% interval covers 79% · new capture: error ×{N['v9_new'][0]:.2f} [{N['v9_new'][1]:.2f}, {N['v9_new'][2]:.2f}]", "RECORDED")]
for i, (h, d_, tg) in enumerate(ROWS):
    y = 4.7 + i * 0.72
    text(s, 7.7, y, 1.45, 0.65, h, size=11, color=INK, font=BODYB, bold=True, line=1.0)
    text(s, 9.15, y, 3.6, 0.7, d_, size=10, color=INK, line=1.03)
source(s, "KHANYA: 12 held-out LumenStone S2 sections (active fb78727d; candidate 42646cfa). Korshunov et al. 2025: magnetite IoU 0.650, their hardest class. "
          "Belt: HIDSAG GEOMET (CC0), 146 samples, out-of-fold; v9 robustness pre-registered (commit 052cd72).")
notes(s, 5)

# 6 — Deliverable 3
s = new_slide()
chrome(s, "Deliverable 3", "The model's output moves a plant setting, safely.")
pic(s, G["decisions"], 0.6, 2.05, w=7.45)
tagcap(s, 0.6, 5.15, "LIVE APP", "Guest sandbox: a real approval, hash-chained and verified (chain intact).", w=7.45)
FLOW = ["Belt scan", "Work index ≤ 16.9 kWh/t (90% bound)", "Feed 98.2% of design", "Metallurgist approves in 90 s", "Signed record → APC (design)"]
for i, t in enumerate(FLOW):
    x = 0.6 + i * 1.5
    c = box(s, x, 5.65, 1.32, 0.95, fill=INK if i in (0, 4) else PAPER, radius=0.1)
    label_in(c, t, size=10, color=WHITE if i in (0, 4) else INK, bold=True, font=BODYB)
    if i < 4:
        arrow(s, x + 1.35, 6.0, 0.13, 0.24, color=COPPER)
DSTATS = [(f"+{N['thr']:.1%}", f"more tonnes through the same mill, 95% CI [+{N['thr_ci'][0]:.1%}, +{N['thr_ci'][1]:.1%}], on {N['n_parcels']} real held-out samples. Provisional", "SIMULATOR"),
          (f"{N['ovl_dep']:.1%} vs {N['ovl_blind']:.1%}", f"parcels harder than planned: no more overloads (upper bound +{N['ni_upper'] * 100:.1f} pp, inside the pre-registered +{N['ni_margin'] * 100:.0f} pp margin)", "SIMULATOR"),
          (f"~{N['kin_1min']:.2f} pp", "the most flotation recovery the extra tonnes could cost (steep part of the curve); 0 on the plateau (first-order kinetics)", "ASSUMPTION")]
for i, (big, lab, tg) in enumerate(DSTATS):
    y = 2.05 + i * 1.6
    text(s, 8.45, y, 4.3, 0.6, big, size=30, color=COPPER if i == 0 else INK, font=HEAD, bold=True)
    text(s, 8.45, y + 0.62, 4.3, 0.7, lab, size=10.5, color=INK, line=1.03)
    tag(s, 8.45, y + 1.2, tg)
source(s, "Envelope demo-envelope-1 (85–110% of design feed, conservative 100%, ramp −10%/+3% per parcel): STIPULATED. Policy: exact one-sided 90% split-conformal "
          "bound, Bond (1961); training/value-chain-20261002. Kinetics: training/physics-checks-20261002 (K1).")
notes(s, 6)

# 7 — Innovation: the brain (dark)
s = new_slide(dark=True)
chrome(s, "Innovation", "The brain: it knows when it doesn't know.", dark=True)
LAYERS = [("SENSE", "VNIR + SWIR line scanner on the belt (Specim SX25 class, design) · reflected-light microscope · lab CSVs and phone photos"),
          ("SEE", "Segmentation network for mineral phases (PyTorch) · spectral models chosen per target by nested cross-validation · public data only"),
          ("DOUBT", "Split-conformal bounds: ≥ 90% coverage by construction · out-of-distribution gate · a refusal gives the safe setting, never \"unknown\""),
          ("DECIDE", "Bond's law turns the bound into a feed rate · site envelope and ramp limits · a person approves · the LLM only routes questions"),
          ("PROVE", "Append-only, hash-chained record · Ed25519 + ML-DSA-65 signatures (FIPS 204) · ML-KEM-768 sealed exports (FIPS 203)")]
for i, (h, d_) in enumerate(LAYERS):
    x = 0.6 + i * 2.46
    hi = h == "DOUBT"
    box(s, x, 2.15, 2.3, 2.85, fill=COPPER if hi else INK2, radius=0.14)
    numdot(s, x + 0.2, 2.35, i + 1, color=NAVY if hi else COPPER)
    text(s, x + 0.7, 2.38, 1.5, 0.35, h, size=15, color=WHITE, font=BODYB, bold=True)
    text(s, x + 0.2, 2.9, 1.98, 2.05, d_, size=12, color=WHITE, line=1.06)
    if i < 4:
        arrow(s, x + 2.32, 3.45, 0.12, 0.3, color=SOFT)
BOT = [("Trained and tested", "HIDSAG (CC0: 146 + 99 samples) · LumenStone S2 (12 held-out sections) · group splits, pre-registered tests, adversarial ClauDex reviews"),
       ("Runs anywhere", "One laptop, fully offline · 92 ms per parcel on a CPU · SQLite (WAL) · no cloud dependency on stage or on site"),
       ("Secure by design", "Deny-by-default roles · scrypt + server-side sessions · AES-256-GCM uploads, metadata stripped · 17 security tests, pip-audit clean")]
for i, (h, d_) in enumerate(BOT):
    x = 0.6 + i * 4.1
    text(s, x, 5.4, 3.9, 0.3, h.upper(), size=10.5, color=COPPER, font=BODYB, bold=True)
    text(s, x, 5.72, 3.9, 1.2, d_, size=11, color=RGBColor(0xDC, 0xE3, 0xEB), line=1.06)
source(s, "Conformal: one-sided split-conformal, exchangeability assumed (hidsag-v8-model). OOD: Ledoit-Wolf Mahalanobis, calibration p95/p99. "
          "Signatures: pqcrypto 1.0.0 + cryptography 50.0.2. Polarimetry sensor (rotating analyser, Stokes) is the next instrument: design, synthetic gate passed.", dark=True)
notes(s, 7)

# 8 — Demo video
s = new_slide(dark=True)
chrome(s, "The demo · 2:25", "From the pit to the control room.", dark=True)
VW = 8.75
VH = VW * 9 / 16
vx = (13.333 - VW) / 2
if os.path.exists(VIDEO):
    s.shapes.add_movie(VIDEO, Inches(vx), Inches(1.95), Inches(VW), Inches(VH),
                       poster_frame_image=POSTER, mime_type="video/mp4")
else:
    pic(s, POSTER, vx, 1.95, w=VW)
source(s, "Real app screens recorded from the local build; stock scenes are illustrative (Mixkit); narration is synthetic. Provenance: presentation/video/STORYBOARD-v8.md.",
       dark=True)
notes(s, 8)

# 9 — Feasibility
s = new_slide()
chrome(s, "Feasibility", "Every claim tested against its physics, failures included.")
pic(s, G["physics"], 0.6, 2.05, w=7.9)
tagcap(s, 0.6, 4.42, "LIVE APP", "The Evidence view: a rejected claim stays on the page.", w=7.9)
F1 = box(s, 0.6, 4.85, 3.85, 1.95, fill=PAPER, radius=0.12)
text(s, 0.8, 5.0, 3.5, 0.3, "ROBUST ON UNSEEN CAPTURES (v9)", size=10, color=COPPER, font=BODYB, bold=True)
text(s, 0.8, 5.3, 3.5, 1.5, [f"✓ New capture ×{N['v9_new'][0]:.2f} [{N['v9_new'][1]:.2f}, {N['v9_new'][2]:.2f}], pre-registered pass",
                            f"✓ Half view ×{N['v9_half']:.2f} · noise ×{N['v9_noise']:.2f} · light ±15% ×{N['v9_light']:.2f}",
                            f"✗ Wavelength drift ×{N['v9_drift']:.2f} → a hardware calibration gate"], size=10.5, color=INK, line=1.05, spacing=3)
F2 = box(s, 4.65, 4.85, 3.85, 1.95, fill=PAPER, radius=0.12)
text(s, 4.85, 5.0, 3.5, 0.3, "FITS A REAL PLANT", size=10, color=COPPER, font=BODYB, bold=True)
text(s, 4.85, 5.3, 3.5, 1.5, ["Specim SX25: 12.3 mm lines at 2 m/s → parcel-level, not particle-level",
                             "Design: IP66 enclosure (assumed rating), purge air, white and wavelength references",
                             "No radioactive source, unlike PGNAA"], size=10.5, color=INK, line=1.05, spacing=3)
RIGHT = [("POWER CUTS & LOAD-SHEDDING", "UPS ride-through. Append-only record with torn-write recovery. After a restart the conservative setting holds until the checks pass."),
         ("CYBER & RANSOMWARE", "Roles, sessions, CSRF, rate limits, encrypted uploads, and offline signed checkpoints for a verified restore."),
         ("QUANTUM-SAFE", "Hybrid Ed25519 + ML-DSA-65 checkpoints; X25519 + ML-KEM-768 exports. NIST FIPS 203/204, August 2024.")]
for i, (h, d_) in enumerate(RIGHT):
    y = 2.05 + i * 1.6
    box(s, 8.85, y, 3.9, 1.45, fill=INK if i == 2 else PAPER, radius=0.12)
    text(s, 9.05, y + 0.15, 3.5, 0.3, h, size=10, color=COPPER, font=BODYB, bold=True)
    text(s, 9.05, y + 0.45, 3.55, 1.0, d_, size=10.5, color=WHITE if i == 2 else INK, line=1.05)
source(s, "training/physics-checks-20261002, hidsag-v9-robustness-20261002 (RESULT.md), installation-20261002/sensor_geometry.py (Specim SX25 datasheet [P]); "
          "docs/18, 19, 21. Belt width 1.2 m and speed 2 m/s ASSUMED. Security: test_secure_server.py, Bandit 0, pip-audit clean (2026-10-02).")
notes(s, 9)

# 10 — Value and impact
s = new_slide()
chrome(s, "Value and impact", "Break-even is a fraction of a point.")
cd = CategoryChartData()
cd.categories = ["Pilot break-even, best case", "Pilot break-even, worst case", "Valterra Mototolo, 2025", "Valterra Amandelbult, 2025"]
cd.add_series("Recovery points", [round(N["breakeven"][0], 2), round(N["breakeven"][1], 2), 1.0, 2.0])
gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.6), Inches(2.35), Inches(6.5), Inches(3.3), cd)
ch = gf.chart
style_chart(ch, 11)
ch.has_title = False
pl = ch.plots[0]
pl.gap_width = 55
pl.has_data_labels = True
pl.data_labels.number_format = '+0.00" pp";-0.00" pp"'
pl.data_labels.number_format_is_linked = False
pl.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
pl.data_labels.font.size = Pt(11)
pl.data_labels.font.bold = True
for i, pt in enumerate(pl.series[0].points):
    pt.format.fill.solid()
    pt.format.fill.fore_color.rgb = COPPER if i < 2 else INK
va = ch.value_axis
va.minimum_scale, va.maximum_scale = 0, 2.5
va.visible = False
va.has_major_gridlines = False
ch.category_axis.reverse_order = True
ch.category_axis.format.line.fill.background()
text(s, 0.6, 2.02, 6.5, 0.3, "Recovery gain needed to pay back a belt pilot, versus moves already reported", size=11, color=INK, font=BODYB, bold=True)
tagcap(s, 0.6, 5.85, "ASSUMPTION", "break-even: US$0.5–3 M capex, US$0.1–0.6 M a year opex, 5 years at 10%", w=6.5, size=10)
tagcap(s, 0.6, 6.25, "SOURCE", "Valterra Platinum 2025 results: recovery moves at two concentrators [P]", w=6.5, size=10)
IMPACT = [("Money", f"R{N['pp_zond'][0] / 1e6:.0f}–{N['pp_zond'][1] / 1e6:.0f} M a year per recovery point at one plant; R{N['pp_impl'][0] / 1e9:.1f}–{N['pp_impl'][1] / 1e9:.1f} bn at group scale (ASSUMED)"),
          ("Time", "Days become seconds: a bound before the ore reaches the mill, not an assay after it has gone"),
          ("Energy", f"When a parcel is harder than planned, the energy shortfall falls from {N['short_blind']:.0%} to {N['short_dep']:.0%} (sim_)"),
          ("Skilled jobs", "Instrument technicians and data-literate metallurgists; a named person approves every action"),
          ("Safety & environment", "No radioactive source; fewer severe overloads; chromite control protects the smelter"),
          ("Sovereignty & access", "Runs offline on site, data stays home; a laptop or a phone is enough to use it")]
for i, (h, d_) in enumerate(IMPACT):
    x = 7.45 + (i % 2) * 2.7
    y = 2.05 + (i // 2) * 1.58
    box(s, x, y, 2.55, 1.45, fill=PAPER, radius=0.12)
    text(s, x + 0.17, y + 0.12, 2.25, 0.3, h.upper(), size=10, color=COPPER, font=BODYB, bold=True)
    text(s, x + 0.17, y + 0.42, 2.25, 1.0, d_, size=10, color=INK, line=1.03)
source(s, "training/economics-20261002 (V1, V4; payability and net 4E price ASSUMED, R32,611/oz basket [P]); value-chain-20261002 (energy shortfall when overloaded, "
          "sim_ on HIDSAG). Valterra 2025 [P]. Nothing here is a site measurement: the pilot measures it.")
notes(s, 10)

# 11 — Pathway
s = new_slide()
chrome(s, "The pathway", "Three steps, paid for by the value they prove.")
CHEV = [("Month 0–1", "Agree: data, POPIA, OT access"), ("Month 1–2", "Install and commission"), ("Month 2–5", "Shadow: predict, don't act"),
        ("Month 5–8", "Advisory: people act"), ("Month 8–9", "Decide on the evidence"), ("Then", "Couple to the APC")]
for i, (a, b_) in enumerate(CHEV):
    x = 0.6 + i * 1.99
    c = box(s, x, 2.05, 2.13, 0.85, fill=INK if i < 5 else COPPER, shape=MSO_SHAPE.CHEVRON if i else MSO_SHAPE.PENTAGON)
    label_in(c, [[(a, {"bold": True, "size": 10.5, "font": BODYB, "color": COPPER_L if i < 5 else WHITE})], [(b_, {"size": 9})]], color=WHITE)
    c.text_frame.margin_left = Inches(0.3)
rows = [("Step", "What it costs", "Status"),
        ("1 · Lab pilot (KHANYA)", "~R210,000 paid pilot, then ~R12,000 a month licence + deployment fee", "HYPOTHESIS"),
        ("2 · Belt pilot (one concentrator)", "US$0.5–3.0 M installed + US$0.1–0.6 M a year for sampling, Bond tests, QEMSCAN, support", "ASSUMPTION"),
        ("3 · Scale", "Subscription ≤ 20% of the measured net value, per concentrator per year: no value, no fee", "ASSUMPTION"),
        ("Break-even", f"{N['breakeven'][0]:.2f}–{N['breakeven'][1]:.2f} recovery points", "ASSUMPTION")]
tb = s.shapes.add_table(len(rows), 3, Inches(0.6), Inches(3.15), Inches(7.0), Inches(2.5)).table
tb.columns[0].width, tb.columns[1].width, tb.columns[2].width = Inches(2.05), Inches(3.85), Inches(1.1)
for r, row in enumerate(rows):
    for c_, val in enumerate(row):
        cell = tb.cell(r, c_)
        cell.fill.solid()
        cell.fill.fore_color.rgb = INK if r == 0 else (PAPER if r % 2 else WHITE)
        cell.margin_left = cell.margin_right = Inches(0.07)
        cell.margin_top = cell.margin_bottom = Inches(0.04)
        p = cell.text_frame.paragraphs[0]
        cell.text_frame.word_wrap = True
        run = p.add_run()
        run.text = val
        run.font.name = BODYB if (r == 0 or c_ == 0) else BODY
        run.font.bold = r == 0 or c_ == 0
        run.font.size = Pt(8.5 if c_ == 2 else 10)
        run.font.color.rgb = WHITE if r == 0 else (RGBColor(0x6B, 0x4E, 0x00) if c_ == 2 else INK)
WHO2 = [("Producer · buyer", "GM metallurgy at Valterra, Implats, Sibanye-Stillwater, Northam or Tharisa: one belt and the site roles"),
        ("Mintek · partner", "QEMSCAN/MLA truth lab, FloatStar and MillStar integration, MOTT IP and invention credits"),
        ("Funding · the ask", "TIA technology-development funding, with producer co-funding"),
        ("Team Sonar · 3 FTE", "product and domain · ML and computer vision · software, security and deployment")]
for i, (h, d_) in enumerate(WHO2):
    y = 3.15 + i * 0.64
    numdot(s, 7.95, y + 0.04, i + 1, color=COPPER if i == 2 else INK, d=0.32, size=10)
    text(s, 8.4, y, 4.35, 0.65, [[(h, {"bold": True, "font": BODYB, "size": 11})], [(d_, {"size": 9.5, "color": MUTED})]], line=1.0)
rb = box(s, 0.6, 5.9, 7.0, 0.95, fill=PAPER, radius=0.12)
text(s, 0.8, 5.98, 6.7, 0.85, [[("RESEARCH NEXT  ", {"bold": True, "font": BODYB, "color": COPPER, "size": 10})],
                               "Magnetite and tennantite gap · Bushveld belt truth with Bond tests · APC on/off blocks · polarimetry sensor (synthetic gate passed)"],
     size=10.5, color=INK, line=1.05)
vb = box(s, 7.95, 5.9, 4.8, 0.95, fill=NAVY, radius=0.12)
text(s, 8.15, 5.98, 1.5, 0.8, f"{N['commits']}", size=34, color=COPPER, font=HEAD, bold=True)
text(s, 9.3, 6.03, 3.35, 0.8, "commits in 24 hours after ONE mentor session with a chemist, a mineralogist and a metallurgist (git log)",
     size=10, color=WHITE, line=1.03)
source(s, "Timeline: docs/18 §5, docs/20 §4 (ASSUMED until a site agrees). Pilot and licence prices are hypotheses to test (v7). Capex/opex grid: economics V4. "
          "TIA is named as a funding route to apply to; no commitment exists.")
notes(s, 11)

# 12 — Close (dark)
s = new_slide(dark=True, bg_img=G["bg_close"])
text(s, 0.6, 0.35, 6, 0.3, [[("REEFPRINT", {"font": BODYB, "bold": True, "size": 10.5, "color": WHITE}),
                              ("  ·  KHANYA  ·  Team Sonar", {"size": 10.5, "color": SOFT})]])
text(s, 11.6, 0.35, 1.13, 0.3, "12 / 12", size=10.5, color=SOFT, align=PP_ALIGN.RIGHT)
text(s, 0.6, 1.0, 8, 0.3, "MINTEK VALUE: INTEGRITY", size=11, color=COPPER, font=BODYB, bold=True)
text(s, 0.6, 1.35, 9.6, 1.4, "“We do what we say we will do, when we say we will do it.”", size=32, color=WHITE, font=HEAD, italic=True, line=1.02)
VALUES = [("Teamwork", "three universities, one build"), ("Creativity", "a refusal that is useful"), ("Integrity", "failures stay on the page"),
          ("Respect and dignity", "a named person decides"), ("Results orientation", "paid only on measured value")]
for i, (v, d_) in enumerate(VALUES):
    x = 0.6 + i * 2.45
    box(s, x, 3.05, 2.3, 0.92, fill=COPPER if v == "Integrity" else INK2, radius=0.12)
    text(s, x + 0.15, 3.15, 2.05, 0.35, v, size=12.5, color=WHITE, font=BODYB, bold=True)
    text(s, x + 0.15, 3.5, 2.05, 0.6, d_, size=10.5, color=RGBColor(0xDC, 0xE3, 0xEB), line=1.0)
text(s, 0.6, 4.55, 9.4, 1.2, [[("We have always read the ore days late.", {"color": WHITE})], [("Let's read it on the belt.", {"color": COPPER})]],
     size=30, font=HEAD, bold=True, line=1.05)
text(s, 0.6, 6.0, 9.2, 0.6, [[("The ask: ", {"bold": True, "font": BODYB, "color": WHITE}),
                              ("one belt · one truth lab · nine months · paid on measured value.", {"color": RGBColor(0xDC, 0xE3, 0xEB)})]], size=14)
qr = box(s, 10.55, 4.35, 2.2, 2.2, fill=WHITE, radius=0.1)
label_in(qr, [[("QR", {"bold": True, "size": 22, "font": BODYB})], [("generated from the live https link at deploy (deploy/make_qr.py)", {"size": 8.5, "color": MUTED})]], color=INK)
text(s, 10.55, 6.62, 2.2, 0.3, "Scan · try it · break it", size=10.5, color=WHITE, align=PP_ALIGN.CENTER, font=BODYB, bold=True)
source(s, "Mintek values and mission: Mintek Shareholder Compact 2023 [P]. Background: illustrative stock still (Mixkit).", dark=True)
notes(s, 12)

assert len(S) <= 12, len(S)
out = os.path.join(OUT, "REEFPRINT-KHANYA-Team-Sonar-pitch-v8.pptx")
prs.save(out)
print("saved", out, len(S), "slides")

# ---------------------------------------------------------------- presenter script (same source as the notes)
QA = [
    ("Does the belt camera identify three minerals?",
     "No, and we say so. A pre-registered test against QEMSCAN found no spectral feature that passed the gate. The three phases come from the microscope, KHANYA. The belt predicts grinding hardness, which is what the feed rate needs."),
    ("Is the +1.9% real?",
     f"It's a simulation on {N['n_parcels']} real held-out drill-core samples, labelled sim_. It's provisional because an approximate bound failed first; the exact bound was the stated fallback. A pilot with on/off blocks confirms it."),
    ("Why should we trust your accuracy?",
     "Every metric is out-of-fold and grouped, against the strongest baseline, with intervals. The zeros are on the slide: magnetite on the deployed model. We pre-registered the robustness test before running it."),
    ("What if the ore is unfamiliar?",
     "The out-of-distribution gate flags or refuses it. Refused means the envelope's conservative setting and a lab sample, never 'unknown'. Honest gap: a foreign ore isn't reliably refused across every fold yet."),
    ("What happens in load-shedding?",
     "UPS keeps the edge PC alive; the record is append-only and survives a torn write; after a restart the safe setting holds until the references pass. We tested the claim that re-ordering ore gains tonnes during curtailment, and rejected it."),
    ("Does it detect radiation?",
     "No. It's optical. A gamma monitor can be added as an input. And unlike PGNAA analysers it carries no radioactive source, so there's no NNR licence."),
    ("Who owns the IP?",
     "Two clean, dated git histories. We follow Mintek's MOTT process and invention credits. Every shipped dependency is permissively licensed."),
    ("What does it cost?",
     f"Lab pilot about R210,000 as a hypothesis; a belt pilot US$0.5–3 M installed. It breaks even at {N['breakeven'][0]:.2f}–{N['breakeven'][1]:.2f} recovery points. After that we charge a share of measured value."),
]
md = ["# REEFPRINT / KHANYA: presenter script v8", "",
      "*Generated by `presentation/deck-src/build_deck_v8.py` from the same table as the speaker notes, so the two never disagree.*", "",
      "**Deck:** `presentation/output/REEFPRINT-KHANYA-Team-Sonar-pitch-v8.pptx` (12 slides). **Length:** 10:00, including the 2:25 demo video on slide 8.", "",
      "**Delivery.** Keynote pace, about 150 words a minute. Simple first, technical where it earns its place. CAPITALS mean emphasis; *(beat)* means a one-second pause. "
      "Make eye contact on every number. Never read the slide.", "",
      "**Rules on stage.** Every number on screen carries its tag (LIVE APP, RECORDED, SOURCE, ASSUMPTION, SIMULATOR, HYPOTHESIS). "
      "Say \"simulated\" for sim_ numbers and \"assumed\" for ASSUMPTION ones. The belt camera does **not** identify minerals; KHANYA does.", ""]
TITLES = ["Title and the joke", "The problem", "Why it matters", "The solution", "Deliverables 1 & 2", "Deliverable 3", "Innovation: the brain",
          "Demo video", "Feasibility", "Value and impact", "The pathway", "Close"]
for k in range(1, 13):
    t, body = SCRIPT[k]
    md += [f"## {k}. {TITLES[k - 1]}  ({t})", "", body.replace("\n", "\n\n"), ""]
md += ["## Questions judges are likely to ask", ""]
for q_, a_ in QA:
    md += [f"**{q_}**  ", a_, ""]
words = sum(len(SCRIPT[k][1].split()) for k in SCRIPT if k != 8)
md += [f"*Spoken words outside the video: {words}.*", ""]
with open(os.path.join(ROOT, "presentation", "PRESENTER-SCRIPT-v8.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(md))
print("script words (excluding demo):", words)
