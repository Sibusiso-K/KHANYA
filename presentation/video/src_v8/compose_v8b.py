"""REEFPRINT / KHANYA demo video, 3-minute cinematic cut (1920x1080, 30 fps).

Real app screens (cap_b/, recorded by capture_v8b.py) are keyed into stock laptop, tablet and phone clips, the camera
zooms through the laptop screen into the app, and spotlights frame each element the narration names (boxes measured
from the live page). Stock scenes are labelled ILLUSTRATIVE; device shots say "stock device, real app on screen".

python compose_v8b.py [--preview T1,T2]   -> out_b/frame_T.png
python compose_v8b.py                      -> ../REEFPRINT-v8-demo.mp4 (+ -embed.mp4)
"""
import json, os, subprocess, sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
from scipy.ndimage import uniform_filter1d

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
FF = os.path.join(ROOT, ".workbench", "media-tools", "imageio_ffmpeg", "binaries", "ffmpeg-win-x86_64-v7.1.exe")
STOCK = os.environ.get("REEF_STOCK", r"C:\Users\USER\AppData\Local\Temp\claude\C--Users-USER-Desktop-REEFPRINT\ad003297-3f40-4fce-8044-df292eebbd73\scratchpad\stock")
VODIR = os.path.join(HERE, "vo", "v8b")
OUTD = os.path.join(HERE, "out_b")
os.makedirs(OUTD, exist_ok=True)
W, H, FPS, GAP = 1920, 1080, 30, 0.45
LINES = json.load(open(os.path.join(HERE, "narration_v8b.json"), encoding="utf-8"))
NARR, KEYS = dict(LINES), [k for k, _ in LINES]
DUR = json.load(open(os.path.join(VODIR, "durations.json")))
M = json.load(open(os.path.join(HERE, "cap_b", "marks.json")))
T, BOXES = M["t"], M["boxes"]
QR = os.path.join(ROOT, "presentation", "deck-src", "img_v8", "qr_live.png")
QR_URL = "lethabomh14-reefprint.static.hf.space"
FONT = r"C:\Windows\Fonts"
NAVY, INK2, COPPER, WHITE, SOFT, TEAL = (14, 27, 46), (34, 54, 77), (210, 90, 36), (255, 255, 255), (184, 196, 210), (31, 163, 168)
AMBER_BG, AMBER_FG = (246, 227, 180), (107, 78, 0)


def F(name, size):
    return ImageFont.truetype(os.path.join(FONT, name), size)


SEG, SEGB, GEOB, GEOI = "segoeui.ttf", "segoeuib.ttf", "georgiab.ttf", "georgiai.ttf"

# ------------------------------------------------------------------ timeline
LEAD, EXTRA, END_HOLD = 0.9, {"n08": 0.9, "n09": 0.2, "n22": 0.5}, 4.6
cues, t = {}, LEAD
for k in KEYS:
    t += EXTRA.get(k, 0.0)
    cues[k] = t
    t += DUR[k] + GAP
TOTAL = t + END_HOLD


def span(k):
    i = KEYS.index(k)
    return cues[k], (cues[KEYS[i + 1]] if i + 1 < len(KEYS) else TOTAL)


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


# ------------------------------------------------------------------ sources
class Vid:
    def __init__(self, path, start=0.0, size=(W, H)):
        self.cap = cv2.VideoCapture(path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 25
        self.n = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.start, self.size, self.last, self.lastf, self.pos = start, size, -1, None, 0

    def frame(self, tl, pingpong=True):
        i = int((self.start + tl) * self.fps)
        if pingpong:
            per = 2 * (self.n - 1)
            i %= per
            i = i if i < self.n else per - i
        i = max(0, min(self.n - 1, i))
        if i != self.last:
            if i != self.pos:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ok, f = self.cap.read()
            self.pos = i + 1
            if ok:
                f = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
                self.lastf = cv2.resize(f, self.size, interpolation=cv2.INTER_LINEAR) if self.size else f
            self.last = i
        return self.lastf


def stock(vid, start=0.0, native=False):
    return Vid(os.path.join(STOCK, f"v_{vid}.mp4"), start, None if native else (W, H))


APP = Vid(os.path.join(HERE, "cap_b", "app.webm"), 0.0)
PHONE = Vid(os.path.join(HERE, "cap_b", "phone.webm"), 0.0, None)
KH = np.array(Image.open(os.path.join(ROOT, "handover", "real-result-refined.png")).convert("RGB"))[300:1080, 0:1600]


def crop_zoom(img, r, out=(W, H)):
    x0, y0, x1, y1 = [int(round(v)) for v in r]
    sub = img[max(0, y0):min(img.shape[0], y1), max(0, x0):min(img.shape[1], x1)]
    return cv2.resize(sub, out, interpolation=cv2.INTER_AREA if (x1 - x0) > out[0] else cv2.INTER_CUBIC)


def lerp_rect(a, b, p):
    p = ease(p)
    return [u + (v - u) * p for u, v in zip(a, b)]


def push(img, p, z=0.07):
    s = 1 + z * ease(p)
    w, h = W / s, H / s
    return crop_zoom(img, ((W - w) / 2, (H - h) / 2, (W + w) / 2, (H + h) / 2))


def darken(img, a):
    return (img.astype(np.float32) * (1 - a) + np.array(NAVY, np.float32) * a).astype(np.uint8)


def fit169(x0, y0, x1, y1, pad=110):
    x0, y0, x1, y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
    w, h = x1 - x0, y1 - y0
    if w / h < 16 / 9:
        w = h * 16 / 9
    else:
        h = w * 9 / 16
    w, h = min(w, W), min(h, H)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    x0, y0 = min(max(0, cx - w / 2), W - w), min(max(0, cy - h / 2), H - h)
    return [x0, y0, x0 + w, y0 + h]


# ------------------------------------------------------------------ overlays
_cache = {}


def overlay(key, fn):
    if key not in _cache:
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fn(ImageDraw.Draw(im), im)
        arr = np.array(im)
        ys, xs = np.nonzero(arr[..., 3])
        if len(ys) == 0:
            _cache[key] = None
        else:
            y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
            a = arr[y0:y1, x0:x1].astype(np.float32) / 255.0
            _cache[key] = (a[..., :3] * 255.0, a[..., 3:4], (y0, y1, x0, x1))
    return _cache[key]


def comp(base, ov, alpha=1.0):
    if ov is None or alpha <= 0:
        return base
    rgb, a, (y0, y1, x0, x1) = ov
    a = a * min(1.0, alpha)
    out = base.copy()
    out[y0:y1, x0:x1] = (base[y0:y1, x0:x1].astype(np.float32) * (1 - a) + rgb * a).astype(np.uint8)
    return out


def chip(d, x, y, txt, fill, fg, size=22, font=SEGB):
    f = F(font, size)
    w = d.textlength(txt, font=f)
    d.rounded_rectangle([x, y, x + w + 30, y + size + 20], radius=(size + 20) // 2, fill=fill)
    d.text((x + 15, y + 8), txt, font=f, fill=fg)


def label(kind):
    txt, fill = {"stock": ("ILLUSTRATIVE STOCK · MIXKIT", (20, 30, 45, 200)),
                 "app": ("REAL APP · REPLAYED PUBLIC DATA (HIDSAG, CC0)", TEAL + (235,)),
                 "device": ("STOCK DEVICE · REAL APP ON SCREEN", TEAL + (235,)),
                 "khanya": ("STOCK DEVICE · REAL KHANYA RESULT, HELD-OUT LUMENSTONE S2", TEAL + (235,))}[kind]
    return overlay("lab_" + kind, lambda d, im: chip(d, 48, 44, txt, fill, WHITE, 20))


def wrap(d, text, font, maxw):
    lines, cur = [], ""
    for w_ in text.split():
        t_ = (cur + " " + w_).strip()
        if d.textlength(t_, font=font) <= maxw:
            cur = t_
        else:
            lines.append(cur)
            cur = w_
    return lines + ([cur] if cur else [])


def caption_chunks(k):
    words, chunks, cur = NARR[k].split(), [], ""
    for w_ in words:
        if len(cur) + len(w_) + 1 > 84 and cur:
            chunks.append(cur)
            cur = w_
        else:
            cur = (cur + " " + w_).strip()
    chunks.append(cur)
    tot = sum(len(c) for c in chunks)
    out, t0 = [], cues[k]
    for c in chunks:
        dd = DUR[k] * len(c) / tot
        out.append((t0, t0 + dd + (GAP if c is chunks[-1] else 0), c))
        t0 += dd
    return out


CAPS = [c for k in KEYS for c in caption_chunks(k)]


def caption_ov(text):
    def draw(d, im):
        f = F(SEG, 38)
        lines = wrap(d, text, f, 1500)
        h = 50 * len(lines) + 30
        y0 = H - 70 - h
        wmax = max(d.textlength(l_, font=f) for l_ in lines)
        d.rounded_rectangle([W / 2 - wmax / 2 - 30, y0, W / 2 + wmax / 2 + 30, y0 + h], radius=18, fill=(8, 14, 24, 195))
        for i, l_ in enumerate(lines):
            d.text((W / 2 - d.textlength(l_, font=f) / 2, y0 + 12 + i * 50), l_, font=f, fill=WHITE)
    return overlay("cap_" + text, draw)


def big_stat(key, big, small, tag=None, x=110, color=WHITE):
    def draw(d, im):
        d.text((x, 300), big, font=F(GEOB, 120), fill=color)
        y = 450
        for l_ in wrap(d, small, F(SEG, 44), 820):
            d.text((x, y), l_, font=F(SEG, 44), fill=WHITE)
            y += 58
        if tag:
            chip(d, x, y + 22, tag, AMBER_BG + (255,), AMBER_FG, 22)
    return overlay(key, draw)


def spotlight(key, boxes):
    """Dim everything except the named boxes; copper outline and a label chip on each (source-frame coordinates)."""
    def draw(d, im):
        d.rectangle([0, 0, W, H], fill=NAVY + (110,))
        for x, y, w, h, lab in boxes:
            d.rectangle([x - 8, y - 8, x + w + 8, y + h + 8], fill=(0, 0, 0, 0))
        for x, y, w, h, lab in boxes:
            d.rounded_rectangle([x - 8, y - 8, x + w + 8, y + h + 8], radius=14, outline=COPPER + (255,), width=5)
            f = F(SEGB, 26)
            tw = d.textlength(lab, font=f)
            cx = min(max(10, x - 8), W - tw - 40)
            cy = y - 58 if y > 70 else y + h + 16
            d.rounded_rectangle([cx, cy, cx + tw + 32, cy + 44], radius=22, fill=COPPER + (255,))
            d.text((cx + 16, cy + 6), lab, font=f, fill=WHITE)
    return overlay(key, draw)


def end_ov():
    def draw(d, im):
        d.rectangle([0, 0, W, H], fill=NAVY + (220,))
        d.text((110, 250), "Read the ore on the belt.", font=F(GEOB, 100), fill=WHITE)
        d.text((110, 400), "REEFPRINT · KHANYA", font=F(SEGB, 46), fill=COPPER)
        d.text((110, 465), "Team Sonar · Lethabo Hoaeane (Unisa) · Sibusiso Khumalo (Wits) · Ipeleng Modise (TUT)", font=F(SEG, 30), fill=WHITE)
        d.text((110, 580), "Mintek–SCi Grad Hackathon 2026 · Problem 3: Computer Vision for Real-Time Mineralogical Characterisation", font=F(SEG, 26), fill=SOFT)
        d.text((110, 625), "Pathway partners we are asking to work with: Mintek (truth lab, APC integration) · TIA (development funding)", font=F(SEG, 26), fill=SOFT)
        q = Image.open(QR).convert("RGB").resize((300, 300), Image.NEAREST)
        d.rounded_rectangle([1490, 250, 1820, 600], radius=20, fill=WHITE + (255,))
        im.paste(q, (1505, 265))
        d.text((1500, 615), "Scan · try it live", font=F(SEGB, 28), fill=WHITE)
        d.text((110, 940), "Stock scenes and devices: Mixkit, illustrative. App screens: real, replayed public data. Narration: synthetic voice. Score: original.",
               font=F(SEG, 22), fill=SOFT)
    return overlay("end", draw)


def brand_ov():
    def draw(d, im):
        d.rectangle([0, 0, W, H], fill=NAVY + (255,))
        cx, cy = W / 2, 400
        for i, c in enumerate([(70, 110, 150), (130, 170, 205), WHITE]):
            yy = cy + 40 - i * 34
            d.polygon([(cx - 90, yy), (cx, yy - 46), (cx + 90, yy), (cx, yy + 46)], fill=c + (255,))
        for txt, f, y, col in [("REEFPRINT", F(GEOB, 110), 500, WHITE), ("See the ore first. Then decide.", F(SEG, 48), 650, COPPER)]:
            d.text((cx - d.textlength(txt, font=f) / 2, y), txt, font=f, fill=col)
    return overlay("brand", draw)


VALUES = [("Teamwork", "three universities, one build"), ("Creativity", "a refusal that is useful"), ("Integrity", "failures stay on the page"),
          ("Respect and dignity", "a named person decides"), ("Results orientation", "paid only on measured value")]


def values_ov(n):
    def draw(d, im):
        d.rectangle([0, 0, W, H], fill=NAVY + (255,))
        d.text((110, 150), "MINTEK VALUES", font=F(SEGB, 26), fill=COPPER)
        d.text((110, 200), "“We do what we say we will do,", font=F(GEOI, 66), fill=WHITE)
        d.text((110, 285), "when we say we will do it.”", font=F(GEOI, 66), fill=WHITE)
        for i, (v, s_) in enumerate(VALUES[:n]):
            x = 110 + i * 345
            d.rounded_rectangle([x, 470, x + 320, 640], radius=22, fill=(COPPER if v == "Integrity" else INK2) + (255,))
            d.text((x + 24, 495), v, font=F(SEGB, 30), fill=WHITE)
            for j, l_ in enumerate(wrap(d, s_, F(SEG, 25), 275)):
                d.text((x + 24, 548 + j * 32), l_, font=F(SEG, 25), fill=(220, 227, 235))
        d.text((110, 700), "Mintek Shareholder Compact 2023", font=F(SEG, 22), fill=SOFT)
    return overlay(f"values_{n}", draw)


# ------------------------------------------------------------------ green-screen keying
def order_quad(pts):
    pts = np.array(pts, np.float32)
    s, df = pts.sum(1), np.diff(pts, axis=1).ravel()
    return np.array([pts[np.argmin(s)], pts[np.argmin(df)], pts[np.argmax(s)], pts[np.argmax(df)]], np.float32)


def green_mask(f):
    hsv = cv2.cvtColor(f, cv2.COLOR_RGB2HSV)
    return cv2.inRange(hsv, (35, 70, 70), (85, 255, 255))


def screen_quad(mask, interior=False):
    n, lab, st, _ = cv2.connectedComponentsWithStats(mask)
    best, area = None, 0
    hh, ww = mask.shape
    for i in range(1, n):
        x, y, w, h, a = st[i]
        touches = x == 0 or y == 0 or x + w >= ww or y + h >= hh
        if interior and touches:
            continue
        if a > area:
            best, area = i, a
    if best is None:
        return None, None
    comp_ = (lab == best).astype(np.uint8) * 255
    cs, _ = cv2.findContours(comp_, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    c = max(cs, key=cv2.contourArea)
    hull = cv2.convexHull(c)
    ap = cv2.approxPolyDP(hull, 0.03 * cv2.arcLength(hull, True), True).reshape(-1, 2)
    quad = order_quad(ap if len(ap) == 4 else cv2.boxPoints(cv2.minAreaRect(c)))
    return quad, comp_


def key_into(frame, src, quad, region_mask):
    h, w = frame.shape[:2]
    sh, sw = src.shape[:2]
    Mx = cv2.getPerspectiveTransform(np.float32([[0, 0], [sw, 0], [sw, sh], [0, sh]]), quad)
    warped = cv2.warpPerspective(src, Mx, (w, h), flags=cv2.INTER_LINEAR)
    poly = np.zeros((h, w), np.uint8)
    cv2.fillConvexPoly(poly, quad.astype(np.int32), 255)
    m = cv2.GaussianBlur(cv2.bitwise_and(region_mask, poly), (5, 5), 0).astype(np.float32)[..., None] / 255.0
    return (frame.astype(np.float32) * (1 - m) + warped.astype(np.float32) * m).astype(np.uint8)


# ------------------------------------------------------------------ shots
S = {k: stock(v, s) for k, v, s in [("aerial", "45821", 1.0), ("pit", "48993", 1.0), ("excav", "46059", 0.5), ("dump", "45815", 0.5),
                                     ("dusty", "45823", 0.5), ("control", "23693", 1.0), ("lab", "4767", 1.0), ("micro", "47783", 4.0),
                                     ("office", "42664", 0.5), ("road", "45825", 0.5), ("plant", "4380", 1.0), ("eng", "22032", 0.5),
                                     ("ctrl2", "23211", 0.5), ("aerial2", "45821", 6.0)]}
LAPTOP, TABLET, PHONESTK = stock("48285", 0.6, native=True), stock("100088", 0.3, native=True), stock("28300", 2.0, native=True)


def stock_shot(k, clips, dark=0.22, extras=(), z=0.07):
    t0, t1 = span(k)

    def fn(t):
        tl = t - t0
        n = len(clips)
        seg = min(n - 1, int(tl / ((t1 - t0) / n)))
        sl = tl - seg * (t1 - t0) / n
        img = darken(push(S[clips[seg]].frame(sl), sl / ((t1 - t0) / n), z), dark)
        for ov, a0 in extras:
            img = comp(img, ov, (tl - a0) / 0.5)
        return comp(img, label("stock"))
    return fn


def app_shot(k, boxes_key=None, zoom=True):
    t0, t1 = span(k)
    boxes = BOXES.get(boxes_key or k, [])
    if boxes:
        x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes)
        x1 = max(b[0] + b[2] for b in boxes); y1 = max(b[1] + b[3] for b in boxes)
        target = fit169(x0, y0, x1, y1, 140)
    else:
        target = [0, 0, W, H]
    sp = spotlight("spot_" + k, boxes) if boxes else None

    def fn(t):
        tl = t - t0
        src = APP.frame(T[k] + tl, pingpong=False)
        if sp is not None:
            src = comp(src, sp, (tl - 0.9) / 0.5)
        r = lerp_rect([0, 0, W, H], target, (tl - 0.3) / 1.6) if zoom else [0, 0, W, H]
        return comp(crop_zoom(src, r), label("app"))
    return fn


def laptop_shot(t):
    """n09: the app keyed into a stock laptop; in the last 1.4 s the camera flies into the screen."""
    t0, t1 = span("n09")
    tl, dur = t - t0, t1 - t0
    f = LAPTOP.frame(tl).copy()
    m = green_mask(f)
    quad, comp_ = screen_quad(m)
    app = APP.frame(T["n09"] + tl, pingpong=False)
    if quad is not None:
        f = key_into(f, app, quad, m)
    f = cv2.resize(f, (W, H), interpolation=cv2.INTER_CUBIC)
    p = (tl - (dur - 1.4)) / 1.4
    if p > 0 and quad is not None:
        q = quad * (W / LAPTOP.lastf.shape[1])
        rect = fit169(q[:, 0].min(), q[:, 1].min(), q[:, 0].max(), q[:, 1].max(), 0)
        f = crop_zoom(f, lerp_rect([0, 0, W, H], rect, p))
        if p > 0.75:
            a = (p - 0.75) / 0.25
            f = (f.astype(np.float32) * (1 - a) + app.astype(np.float32) * a).astype(np.uint8)
    return comp(f, label("device"))


def tablet_shot(t):
    t0, t1 = span("n17")
    tl = t - t0
    f = TABLET.frame(tl).copy()
    m = green_mask(f)
    quad, _ = screen_quad(m)
    if quad is not None:
        f = key_into(f, KH, quad, m)
    f = push(cv2.resize(f, (W, H), interpolation=cv2.INTER_CUBIC), tl / (t1 - t0), 0.05)
    return comp(f, label("khanya"))


QR_IMG = cv2.resize(np.array(Image.open(QR).convert("RGB")), (330, 330), interpolation=cv2.INTER_NEAREST)


def phone_shot(t):
    t0, t1 = span("n21")
    tl = t - t0
    f = PHONESTK.frame(tl).copy()
    hh, ww = f.shape[:2]
    m = green_mask(f)
    bg = cv2.GaussianBlur(darken(S["aerial"].frame(tl + 3), 0.35), (0, 0), 6)
    bg = cv2.resize(bg, (ww, hh))
    quad, scr = screen_quad(m, interior=True)
    back = cv2.bitwise_and(m, cv2.bitwise_not(scr if scr is not None else np.zeros_like(m)))
    bm = cv2.GaussianBlur(back, (5, 5), 0).astype(np.float32)[..., None] / 255.0
    f = (f.astype(np.float32) * (1 - bm) + bg.astype(np.float32) * bm).astype(np.uint8)
    if quad is not None:
        ph = PHONE.frame(tl * 0.9, pingpong=False)
        f = key_into(f, ph, quad, scr)
    f = cv2.resize(f, (W, H), interpolation=cv2.INTER_AREA)
    # the real QR code, on the right
    x0, y0 = 1420, 300
    f[y0 - 20:y0 + 350, x0 - 20:x0 + 350] = 255
    f[y0:y0 + 330, x0:x0 + 330] = QR_IMG
    f = comp(f, overlay("qrtxt", lambda d, im: (d.text((1400, 680), "Scan · it opens on your phone", font=F(SEGB, 30), fill=WHITE),
                                              d.text((1400, 725), QR_URL, font=F(SEG, 24), fill=SOFT))))
    return comp(f, label("device"))


def n07(t):
    t0, t1 = span("n07")
    tl, mid = t - t0, (t1 - t0) * 0.42
    if tl < mid:
        img = darken(push(S["office"].frame(tl), tl / mid), 0.35)
        img = comp(img, overlay("pending", lambda d, im: chip(d, 1180, 520, "RESULT PENDING · 48 h", (20, 30, 45, 220), (255, 214, 120), 34)),
                   0.55 + 0.45 * abs(np.sin(tl * 3.2)))
    else:
        img = darken(push(S["road"].frame(tl - mid), (tl - mid) / (t1 - t0 - mid)), 0.35)
        img = comp(img, big_stat("kt", "18.5 kt", "of ore milled before a 72-hour assay returns, at a Zondereinde-size plant", "ASSUMPTION · 2.25 Mt/yr"),
                   (tl - mid) / 0.5)
    return comp(img, label("stock"))


def n20(t):
    t0, t1 = span("n20")
    tl = t - t0
    img = darken(push(S["plant"].frame(tl), tl / (t1 - t0)), 0.45)
    img = comp(img, big_stat("money", "R64–153M", "a year for one recovery point at one South African concentrator; the pilot breaks even at 0.04–0.26 of a point",
                             "ASSUMPTION · assumed prices and payability"), tl / 0.6)
    return comp(img, label("stock"))


def n22(t):
    t0, t1 = span("n22")
    n = min(5, 1 + int((t - t0) / ((t1 - t0) * 0.6 / 5)))
    return comp(np.zeros((H, W, 3), np.uint8), values_ov(n))


def n23(t):
    t0, t1 = span("n23")
    tl, half = t - t0, (cues["n23"] + DUR["n23"] - t0) * 0.5
    clip = "eng" if tl < half else "ctrl2"
    img = comp(darken(push(S[clip].frame(tl if tl < half else tl - half), 0.5, 0.05), 0.25), label("stock"))
    if t > cues["n23"] + DUR["n23"] - 0.6:
        img = comp(img, end_ov(), (t - (cues["n23"] + DUR["n23"] - 0.6)) / 0.8)
    return img


SHOTS = {
    "n01": stock_shot("n01", ["aerial"], 0.18),
    "n02": stock_shot("n02", ["pit", "excav"], 0.18),
    "n03": stock_shot("n03", ["dump", "dusty"], 0.2),
    "n04": stock_shot("n04", ["control"], 0.25),
    "n05": stock_shot("n05", ["lab"], 0.4, [(big_stat("fa", "24–72 h", "for a fire assay to come back from the lab", "SOURCE [S]"), 0.8)]),
    "n06": stock_shot("n06", ["micro"], 0.45, [(big_stat("qs", "US$1,500", "a sample for QEMSCAN mineral analysis, and days of queue", "SOURCE · SRC price list 2017"), 0.6)]),
    "n07": n07,
    "n08": lambda t: comp(np.zeros((H, W, 3), np.uint8), brand_ov()),
    "n09": laptop_shot,
    "n10": app_shot("n10"), "n11": app_shot("n11"), "n12": app_shot("n12"), "n13": app_shot("n13"),
    "n14": app_shot("n14"), "n15": app_shot("n15"), "n16": app_shot("n16"),
    "n17": tablet_shot,
    "n18": app_shot("n18"), "n19": app_shot("n19"),
    "n20": n20, "n21": phone_shot, "n22": n22, "n23": n23,
}
XF = {}


def shot_at(t):
    k = KEYS[0]
    for kk in KEYS:
        if t >= cues[kk] - (LEAD if kk == KEYS[0] else 0):
            k = kk
    return k


def frame(t):
    k = shot_at(t)
    img = SHOTS[k](t)
    i = KEYS.index(k)
    if i + 1 < len(KEYS):
        nxt = cues[KEYS[i + 1]]
        if t > nxt - 0.4 and KEYS[i + 1] != "n10":       # the laptop fly-through cuts straight into the app
            if KEYS[i + 1] not in XF:
                XF[KEYS[i + 1]] = SHOTS[KEYS[i + 1]](nxt)
            a = (t - (nxt - 0.4)) / 0.4
            img = (img.astype(np.float32) * (1 - a) + XF[KEYS[i + 1]].astype(np.float32) * a).astype(np.uint8)
    if t < 0.6:
        img = (img.astype(np.float32) * (t / 0.6)).astype(np.uint8)
    if t > TOTAL - 0.8:
        img = (img.astype(np.float32) * max(0.0, (TOTAL - t) / 0.8)).astype(np.uint8)
    for c0, c1, txt in CAPS:
        if c0 <= t < c1 and k != "n08":
            img = comp(img, caption_ov(txt))
            break
    return img


def build_audio(path):
    SR = 48000
    N = int((TOTAL + 0.3) * SR)
    mus_path = os.path.join(OUTD, "music_v8b.wav")
    subprocess.run([sys.executable, os.path.join(ROOT, "presentation", "video", "src", "make_music.py"), mus_path, f"{TOTAL + 0.3:.2f}",
                    f"{cues['n05']:.2f}", f"{cues['n08']:.2f}", f"{cues['n08']:.2f}"], check=True)
    sr, mus = wavfile.read(mus_path)
    mus = mus.astype(np.float32) / 32768.0
    mus = mus[:N] if len(mus) >= N else np.pad(mus, ((0, N - len(mus)), (0, 0)))
    vo = np.zeros(N, np.float32)
    for k in KEYS:
        sr, x = wavfile.read(os.path.join(VODIR, k + ".wav"))
        x = x.astype(np.float32) / 32768.0
        x = x.mean(axis=1) if x.ndim > 1 else x
        s0 = int(cues[k] * SR)
        vo[s0:s0 + len(x)] += x[:max(0, min(len(x), N - s0))]
    vo *= 0.16 / max(np.sqrt(np.mean(vo[np.abs(vo) > 0.01] ** 2)), 1e-6)
    env = uniform_filter1d((np.abs(vo) > 0.008).astype(np.float32), size=int(0.6 * SR))
    mix = mus * (0.55 - 0.40 * np.clip(env * 3, 0, 1))[:, None] * 0.8 + vo[:, None]
    mix /= max(1.0, np.abs(mix).max() / 0.95)
    wavfile.write(path, SR, (mix * 32767).astype(np.int16))


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--preview":
        for ts in sys.argv[2].split(","):
            Image.fromarray(frame(float(ts))).save(os.path.join(OUTD, f"frame_{float(ts):06.2f}.png"))
        print("total", round(TOTAL, 2), {k: round(v, 1) for k, v in cues.items()})
        sys.exit(0)
    silent = os.path.join(OUTD, "v8b_silent.mp4")
    p = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    nf = int(TOTAL * FPS)
    for i in range(nf):
        p.stdin.write(frame(i / FPS).tobytes())
        if i % 300 == 0:
            print(f"frame {i}/{nf}", flush=True)
    p.stdin.close()
    p.wait()
    wav = os.path.join(OUTD, "v8b_audio.wav")
    build_audio(wav)
    dest = os.path.join(ROOT, "presentation", "video", "REEFPRINT-v8-demo.mp4")
    subprocess.run([FF, "-v", "error", "-y", "-i", silent, "-i", wav, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", dest], check=True)
    emb = os.path.join(ROOT, "presentation", "video", "REEFPRINT-v8-demo-embed.mp4")
    subprocess.run([FF, "-v", "error", "-y", "-i", dest, "-c:v", "libx264", "-preset", "medium", "-crf", "26", "-vf", "scale=1600:-2",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", emb], check=True)
    print("done", dest, round(TOTAL, 2), "s")
