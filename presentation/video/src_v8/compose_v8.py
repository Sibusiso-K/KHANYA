"""REEFPRINT / KHANYA v8 demo video compositor (about 2:25, 1920x1080, 30 fps).

Inputs: vo/<voice>/ (make_vo_v8.py), cap/app.webm + cap/marks.json (capture_v8.py, the real app),
Mixkit stock clips (STOCK, kept out of git: the licence forbids redistributing them standalone),
the real KHANYA screenshot in handover/, and the original synthesised score (../src/make_music.py).

python compose_v8.py [--preview T1,T2,...]  -> out/frame_T.png   (stills for checking)
python compose_v8.py                         -> ../REEFPRINT-v8-demo.mp4 (+ -embed.mp4) and out/timeline_v8.json

Every shot carries an on-screen provenance label: ILLUSTRATIVE STOCK, REAL APP, or a source tag.
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
VOICE = os.environ.get("REEF_VOICE", "en-GB-RyanNeural")
VODIR = os.path.join(HERE, "vo", VOICE)
OUTD = os.path.join(HERE, "out")
os.makedirs(OUTD, exist_ok=True)
W, H, FPS = 1920, 1080, 30
GAP = 0.45
DUR = json.load(open(os.path.join(VODIR, "durations.json")))
NARR = dict(json.load(open(os.path.join(HERE, "narration_v8.json"), encoding="utf-8")))
MARKS = json.load(open(os.path.join(HERE, "cap", "marks.json")))
FONT = r"C:\Windows\Fonts"


def F(name, size):
    return ImageFont.truetype(os.path.join(FONT, name), size)


SEG, SEGB, SEGSB, GEO, GEOB, GEOI = "segoeui.ttf", "segoeuib.ttf", "seguisb.ttf", "georgia.ttf", "georgiab.ttf", "georgiai.ttf"
if not os.path.exists(os.path.join(FONT, SEGSB)):
    SEGSB = SEGB
NAVY, INK2, COPPER, WHITE, SOFT = (14, 27, 46), (34, 54, 77), (210, 90, 36), (255, 255, 255), (184, 196, 210)
AMBER_BG, AMBER_FG = (246, 227, 180), (107, 78, 0)
TEAL = (31, 163, 168)

# ------------------------------------------------------------------ timeline
LEAD, EXTRA = 0.9, {"n07": 0.9, "n16": 0.5}   # pauses before these lines
cues, t = {}, LEAD
for k in [k for k, _ in json.load(open(os.path.join(HERE, "narration_v8.json"), encoding="utf-8"))]:
    t += EXTRA.get(k, 0.0)
    cues[k] = t
    t += DUR[k] + GAP
END_HOLD = 4.2
TOTAL = t + END_HOLD
KEYS = list(cues)


def span(k):
    i = KEYS.index(k)
    return cues[k], (cues[KEYS[i + 1]] if i + 1 < len(KEYS) else TOTAL)


# ------------------------------------------------------------------ sources
class Clip:
    """A stock clip read on demand, resized to 1080p, with a slow push-in."""
    def __init__(self, vid, start=0.0, speed=1.0):
        self.cap = cv2.VideoCapture(os.path.join(STOCK, f"v_{vid}.mp4"))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 25
        self.n = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.start, self.speed, self.last, self.lastf, self.pos = start, speed, -1, None, 0

    def frame(self, tl):
        i = int((self.start + tl * self.speed) * self.fps)
        period = 2 * (self.n - 1)
        i = i % period
        i = i if i < self.n else period - i                # ping-pong when a shot outlasts the clip
        if i != self.last:
            if i != self.pos:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ok, f = self.cap.read()
            self.pos = i + 1
            if ok:
                self.lastf = cv2.cvtColor(cv2.resize(f, (W, H), interpolation=cv2.INTER_LINEAR), cv2.COLOR_BGR2RGB)
            self.last = i
        return self.lastf


class AppRec:
    def __init__(self):
        self.cap = cv2.VideoCapture(os.path.join(HERE, "cap", "app.webm"))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 25
        self.n = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.last, self.lastf = -1, None

    def frame(self, ts):
        i = max(0, min(self.n - 1, int(ts * self.fps)))
        if i != self.last:
            if i != self.last + 1:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ok, f = self.cap.read()
            if ok:
                self.lastf = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
            self.last = i
        return self.lastf


APP = AppRec()
KH = np.array(Image.open(os.path.join(ROOT, "handover", "real-result-refined.png")).convert("RGB"))


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def crop_zoom(img, r0, r1, p):
    """Interpolate a crop rectangle (x0,y0,x1,y1) and scale it to the frame."""
    p = ease(p)
    x0, y0, x1, y1 = [a + (b - a) * p for a, b in zip(r0, r1)]
    sub = img[int(y0):int(y1), int(x0):int(x1)]
    return cv2.resize(sub, (W, H), interpolation=cv2.INTER_AREA if (x1 - x0) > W else cv2.INTER_CUBIC)


def push(img, p, z=0.06):
    s = 1 + z * ease(p)
    w, h = W / s, H / s
    return crop_zoom(img, (0, 0, W, H), ((W - w) / 2, (H - h) / 2, (W + w) / 2, (H + h) / 2), 1.0)


def darken(img, a):
    return (img.astype(np.float32) * (1 - a) + np.array(NAVY, np.float32) * a).astype(np.uint8)


# ------------------------------------------------------------------ overlays (RGBA, cached)
_cache = {}


def overlay(key, draw_fn):
    if key not in _cache:
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_fn(ImageDraw.Draw(im), im)
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
    if ov is None:
        return base
    rgb, a, (y0, y1, x0, x1) = ov
    a = a * alpha
    out = base.copy()
    out[y0:y1, x0:x1] = (base[y0:y1, x0:x1].astype(np.float32) * (1 - a) + rgb * a).astype(np.uint8)
    return out


def chip(d, x, y, txt, fill, fg, size=22):
    f = F(SEGB, size)
    w = d.textlength(txt, font=f)
    d.rounded_rectangle([x, y, x + w + 28, y + size + 18], radius=(size + 18) // 2, fill=fill)
    d.text((x + 14, y + 7), txt, font=f, fill=fg)


def label(kind):
    txt, fill, fg = {"stock": ("ILLUSTRATIVE STOCK · MIXKIT", (20, 30, 45, 200), WHITE),
                     "app": ("REAL APP · REPLAYED PUBLIC DATA (HIDSAG, CC0)", TEAL + (235,), WHITE),
                     "khanya": ("REAL APP · KHANYA · HELD-OUT LUMENSTONE S2 SECTION", TEAL + (235,), WHITE)}[kind]
    return overlay("lab_" + kind, lambda d, im: chip(d, 48, 44, txt, fill, fg, 20))


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
    """Split a narration line into caption chunks of at most two lines, timed by character share."""
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
        d = DUR[k] * len(c) / tot
        out.append((t0, t0 + d + (GAP if c is chunks[-1] else 0), c))
        t0 += d
    return out


CAPS = [c for k in KEYS for c in caption_chunks(k)]


def caption_ov(text):
    def draw(d, im):
        f = F(SEG, 38)
        lines = wrap(d, text, f, 1500)
        lh = 50
        h = lh * len(lines) + 30
        y0 = H - 70 - h
        wmax = max(d.textlength(l_, font=f) for l_ in lines)
        d.rounded_rectangle([W / 2 - wmax / 2 - 30, y0, W / 2 + wmax / 2 + 30, y0 + h], radius=18, fill=(8, 14, 24, 190))
        for i, l_ in enumerate(lines):
            d.text((W / 2 - d.textlength(l_, font=f) / 2, y0 + 12 + i * lh), l_, font=f, fill=WHITE)
    return overlay("cap_" + text, draw)


def big_stat(key, big, small, tag=None, pos="left", color=WHITE):
    def draw(d, im):
        x = 110 if pos == "left" else W - 900
        d.text((x, 300), big, font=F(GEOB, 120), fill=color)
        y = 450
        for l_ in wrap(d, small, F(SEG, 44), 820):
            d.text((x, y), l_, font=F(SEG, 44), fill=WHITE)
            y += 58
        if tag:
            chip(d, x, y + 22, tag, AMBER_BG + (255,), AMBER_FG, 22)
    return overlay(key, draw)


def title_card(key, lines, sub=None, bg=True):
    def draw(d, im):
        if bg:
            d.rectangle([0, 0, W, H], fill=NAVY + (255,))
        y = 380
        for txt, font, col in lines:
            d.text((W / 2 - d.textlength(txt, font=font) / 2, y), txt, font=font, fill=col)
            y += font.size + 30
        if sub:
            f = F(SEG, 34)
            d.text((W / 2 - d.textlength(sub, font=f) / 2, y + 30), sub, font=f, fill=SOFT)
    return overlay(key, draw)


VALUES = [("Teamwork", "three universities, one build"), ("Creativity", "a refusal that is useful"), ("Integrity", "failures stay on the page"),
          ("Respect and dignity", "a named person decides"), ("Results orientation", "paid only on measured value")]


def values_ov(n):
    def draw(d, im):
        d.rectangle([0, 0, W, H], fill=NAVY + (255,))
        f = F(SEGB, 26)
        d.text((110, 150), "MINTEK VALUES", font=f, fill=COPPER)
        d.text((110, 200), "“We do what we say we will do,", font=F(GEOI, 66), fill=WHITE)
        d.text((110, 285), "when we say we will do it.”", font=F(GEOI, 66), fill=WHITE)
        for i, (v, s) in enumerate(VALUES[:n]):
            x = 110 + i * 345
            d.rounded_rectangle([x, 470, x + 320, 640], radius=22, fill=(COPPER if v == "Integrity" else INK2) + (255,))
            d.text((x + 24, 495), v, font=F(SEGB, 30), fill=WHITE)
            for j, l_ in enumerate(wrap(d, s, F(SEG, 25), 275)):
                d.text((x + 24, 548 + j * 32), l_, font=F(SEG, 25), fill=(220, 227, 235))
        d.text((110, 700), "Mintek Shareholder Compact 2023", font=F(SEG, 22), fill=SOFT)
    return overlay(f"values_{n}", draw)


def end_ov():
    def draw(d, im):
        d.rectangle([0, 0, W, H], fill=NAVY + (215,))
        d.text((110, 300), "Read the ore on the belt.", font=F(GEOB, 104), fill=WHITE)
        d.text((110, 450), "REEFPRINT · KHANYA", font=F(SEGB, 46), fill=COPPER)
        d.text((110, 515), "Team Sonar  ·  Lethabo Hoaeane (Unisa) · Sibusiso Khumalo (Wits) · Ipeleng Modise (TUT)", font=F(SEG, 32), fill=WHITE)
        d.text((110, 640), "Mintek–SCi Grad Hackathon 2026  ·  Problem 3: Computer Vision for Real-Time Mineralogical Characterisation",
               font=F(SEG, 28), fill=SOFT)
        d.text((110, 690), "Pathway partners we are asking to work with: Mintek (truth lab, APC integration) · TIA (development funding)",
               font=F(SEG, 28), fill=SOFT)
        d.text((110, 900), "Stock scenes: Mixkit, illustrative. App screens: real, replayed public data. Narration: synthetic voice. Score: original.",
               font=F(SEG, 22), fill=SOFT)
    return overlay("end", draw)


def brand_ov(p):
    def draw(d, im):
        d.rectangle([0, 0, W, H], fill=NAVY + (255,))
        cx, cy = W / 2, 400
        for i, c in enumerate([(70, 110, 150), (130, 170, 205), WHITE]):   # the app's layered mark, drawn
            yy = cy + 40 - i * 34
            d.polygon([(cx - 90, yy), (cx, yy - 46), (cx + 90, yy), (cx, yy + 46)], fill=c + (255,))
        t1, f1 = "REEFPRINT", F(GEOB, 110)
        d.text((cx - d.textlength(t1, font=f1) / 2, 500), t1, font=f1, fill=WHITE)
        t2, f2 = "See the ore first. Then decide.", F(SEG, 48)
        d.text((cx - d.textlength(t2, font=f2) / 2, 650), t2, font=f2, fill=COPPER)
    return overlay("brand", draw)


# ------------------------------------------------------------------ shots
S01, S02, S03 = Clip("45821", 1.0), Clip("45822", 2.0), Clip("45753", 0.5)
S04, S05, S06a, S06b = Clip("4767", 1.0), Clip("47783", 4.0), Clip("42664", 0.5), Clip("45825", 0.5)
S14, S17 = Clip("4380", 1.0), Clip("45821", 6.0)
R_FULL = (0, 0, W, H)


def app_shot(k, r0, r1, off=0.0):
    t0, t1 = span(k)

    def fn(t):
        tl = t - t0
        img = APP.frame(MARKS[k] + off + tl)
        return comp(crop_zoom(img, r0, r1, tl / max(1.0, (t1 - t0) * 0.8)), label("app"))
    return fn


def stock_shot(k, clip, dark=0.25, extra=None, z=0.06):
    t0, t1 = span(k)

    def fn(t):
        tl = t - t0
        img = comp(darken(push(clip.frame(tl), tl / (t1 - t0), z), dark), label("stock"))
        if extra:
            for ov, a0 in extra:
                a = min(1.0, max(0.0, (tl - a0) / 0.5))
                if a > 0:
                    img = comp(img, ov, a)
        return img
    return fn


def n06(t):
    t0, t1 = span("n06")
    tl, mid = t - t0, (t1 - t0) * 0.42
    if tl < mid:
        img = darken(push(S06a.frame(tl), tl / mid), 0.35)
        img = comp(img, overlay("pending", lambda d, im: chip(d, 1180, 520, "RESULT PENDING · 48 h", (20, 30, 45, 220), (255, 214, 120), 34)),
                   0.55 + 0.45 * abs(np.sin(tl * 3.2)))
    else:
        img = darken(push(S06b.frame(tl - mid), (tl - mid) / (t1 - t0 - mid)), 0.35)
        img = comp(img, big_stat("kt", "18.5 kt", "of ore milled before a 72-hour assay returns, at a Zondereinde-size plant",
                                 "ASSUMPTION · 2.25 Mt/yr"), min(1, (tl - mid) / 0.5))
    return comp(img, label("stock"))


def n07(t):
    return comp(np.zeros((H, W, 3), np.uint8), brand_ov(0))


def n12(t):
    t0, t1 = span("n12")
    img = crop_zoom(KH, (270, 320, 1580, 1057), (290, 360, 1180, 861), (t - t0) / (t1 - t0))
    return comp(img, label("khanya"))


def n15(t):
    t0, t1 = span("n15")
    tl = t - t0
    img = darken(push(S14.frame(tl), tl / (t1 - t0)), 0.45)
    img = comp(img, big_stat("money", "R64–153M", "a year for one recovery point at one South African concentrator", "ASSUMPTION · assumed prices and payability"),
               min(1, tl / 0.6))
    return comp(img, label("stock"))


def n16(t):
    t0, t1 = span("n16")
    n = min(5, 1 + int((t - t0) / ((t1 - t0) * 0.6 / 5)))
    return comp(np.zeros((H, W, 3), np.uint8), values_ov(n))


def n17(t):
    t0, t1 = span("n17")
    tl = t - t0
    img = comp(darken(push(S17.frame(tl), tl / (t1 - t0), 0.1), 0.2), label("stock"))
    if t > cues["n17"] + DUR["n17"] - 0.6:
        img = comp(img, end_ov(), min(1, (t - (cues["n17"] + DUR["n17"] - 0.6)) / 0.8))
    return img


SHOTS = {
    "n01": stock_shot("n01", S01, 0.2),
    "n02": stock_shot("n02", S02, 0.2),
    "n03": stock_shot("n03", S03, 0.25),
    "n04": stock_shot("n04", S04, 0.4, [(big_stat("fa", "24–72 h", "for a fire assay to come back from the lab", "SOURCE [S]"), 0.8)]),
    "n05": stock_shot("n05", S05, 0.45, [(big_stat("qs", "US$1,500", "a sample for QEMSCAN mineral analysis, and days of queue", "SOURCE · SRC price list 2017"), 0.6)]),
    "n06": n06,
    "n07": n07,
    "n08": app_shot("n08", R_FULL, (356, 230, 1850, 1070)),
    "n09": app_shot("n09", R_FULL, (50, 230, 1140, 843)),
    "n10": app_shot("n10", (50, 230, 1140, 843), (50, 250, 1110, 846)),
    "n11": app_shot("n11", (0, 300, 1386, 1080), (20, 398, 1233, 1080)),
    "n12": n12,
    "n13": app_shot("n13", (40, 70, 1240, 745), (690, 70, 1890, 745)),
    "n14": app_shot("n14", (40, 60, 1460, 859), (60, 90, 1420, 855)),
    "n15": n15,
    "n16": n16,
    "n17": n17,
}


def shot_at(t):
    k = KEYS[0]
    for kk in KEYS:
        if t >= cues[kk] - (LEAD if kk == KEYS[0] else 0):
            k = kk
    return k


XF = {}


def frame(t):
    k = shot_at(t)
    img = SHOTS[k](t)
    i = KEYS.index(k)
    if i + 1 < len(KEYS):                     # 0.4 s crossfade into the next shot
        nxt = cues[KEYS[i + 1]]
        if t > nxt - 0.4:
            if KEYS[i + 1] not in XF:
                XF[KEYS[i + 1]] = SHOTS[KEYS[i + 1]](nxt)
            img2 = XF[KEYS[i + 1]]
            a = (t - (nxt - 0.4)) / 0.4
            img = (img.astype(np.float32) * (1 - a) + img2.astype(np.float32) * a).astype(np.uint8)
    if t < 0.6:                                # fade in from black
        img = (img.astype(np.float32) * (t / 0.6)).astype(np.uint8)
    if t > TOTAL - 0.8:
        img = (img.astype(np.float32) * max(0.0, (TOTAL - t) / 0.8)).astype(np.uint8)
    for c0, c1, txt in CAPS:                   # burned-in captions
        if c0 <= t < c1 and k not in ("n07",):
            img = comp(img, caption_ov(txt))
            break
    return img


# ------------------------------------------------------------------ audio
def build_audio(path):
    SR = 48000
    N = int((TOTAL + 0.3) * SR)
    mus_path = os.path.join(OUTD, "music_v8.wav")
    subprocess.run([sys.executable, os.path.join(ROOT, "presentation", "video", "src", "make_music.py"), mus_path, f"{TOTAL + 0.3:.2f}",
                    f"{cues['n04']:.2f}", f"{cues['n07']:.2f}", f"{cues['n07']:.2f}"], check=True)
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
    rms = np.sqrt(np.mean(vo[np.abs(vo) > 0.01] ** 2))
    vo *= 0.16 / max(rms, 1e-6)
    env = uniform_filter1d((np.abs(vo) > 0.008).astype(np.float32), size=int(0.6 * SR))
    duck = 0.55 - 0.40 * np.clip(env * 3, 0, 1)
    mix = mus * duck[:, None] * 0.8 + vo[:, None]
    mix /= max(1.0, np.abs(mix).max() / 0.95)
    wavfile.write(path, SR, (mix * 32767).astype(np.int16))


# ------------------------------------------------------------------ main
if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--preview":
        for ts in sys.argv[2].split(","):
            Image.fromarray(frame(float(ts))).save(os.path.join(OUTD, f"frame_{float(ts):06.2f}.png"))
        print("total", round(TOTAL, 2), {k: round(v, 2) for k, v in cues.items()})
        sys.exit(0)
    json.dump({"total": TOTAL, "cues": cues}, open(os.path.join(OUTD, "timeline_v8.json"), "w"), indent=1)
    silent = os.path.join(OUTD, "v8_silent.mp4")
    p = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    nf = int(TOTAL * FPS)
    for i in range(nf):
        p.stdin.write(frame(i / FPS).tobytes())
        if i % 300 == 0:
            print(f"frame {i}/{nf}", flush=True)
    p.stdin.close()
    p.wait()
    wav = os.path.join(OUTD, "v8_audio.wav")
    build_audio(wav)
    dest = os.path.join(ROOT, "presentation", "video", "REEFPRINT-v8-demo.mp4")
    subprocess.run([FF, "-v", "error", "-y", "-i", silent, "-i", wav, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", dest], check=True)
    emb = os.path.join(ROOT, "presentation", "video", "REEFPRINT-v8-demo-embed.mp4")
    subprocess.run([FF, "-v", "error", "-y", "-i", dest, "-c:v", "libx264", "-preset", "medium", "-crf", "26", "-vf", "scale=1600:-2",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", emb], check=True)
    print("done", dest, round(TOTAL, 2), "s")
