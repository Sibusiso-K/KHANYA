"""REEFPRINT / KHANYA promo compositor.

python render.py preview T1 T2 ...   -> preview/frame_T.png
python render.py full [--nocap]      -> out/video.mp4 + out/timeline.json
"""
import os, sys, json, math, re, subprocess
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = os.path.dirname(os.path.abspath(__file__))
CAP = os.path.join(S, "cap")
STOCK = os.path.join(S, "stock")
FONTDIR = os.path.join(S, "fonts")
FF = r"C:\Users\USER\Desktop\REEFPRINT\.workbench\media-tools\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
MICRO = r"C:\Users\USER\Desktop\REEFPRINT\demo-images\test_11.jpg"
W, H, FPS = 1920, 1080, 30
VOICE = "en-ZA-LukeNeural"
VODIR = os.path.join(S, "vo", VOICE)
DUR = json.load(open(os.path.join(VODIR, "durations.json")))
WORDS = json.load(open(os.path.join(VODIR, "words.json")))
NARR = dict(json.load(open(os.path.join(S, "narration.json"), encoding="utf-8")))
MODE = sys.argv[1] if len(sys.argv) > 1 else "preview"
PREVIEW = MODE == "preview"
CAPTIONS = "--nocap" not in sys.argv

NAVY = (27, 45, 64)
BLUE = (34, 87, 141)
ACC = (236, 132, 56)
WHITE = (255, 255, 255)
BAR = 118

# ------------------------------------------------------------------ math helpers

def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def prog(t, a, b):
    return clamp((t - a) / (b - a)) if b > a else float(t >= a)


def eio(x):
    x = clamp(x)
    return 4 * x * x * x if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def eout(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def win(t, a, b, fi=0.3, fo=0.3):
    """opacity window: fade in at a, fade out at b"""
    if t < a or t > b:
        return 0.0
    return min(eout(prog(t, a, a + fi)), (1 - eio(prog(t, b - fo, b))) if fo > 0 else 1.0)


# ------------------------------------------------------------------ sprites (premultiplied float32 RGBA)

from collections import OrderedDict


def _nbytes(v):
    if isinstance(v, np.ndarray):
        return v.nbytes
    if isinstance(v, tuple):
        return sum(_nbytes(x) for x in v)
    return 1024


class LRU(OrderedDict):
    """Byte-bounded cache: animated sprites (tracking, growing boxes) would otherwise exhaust RAM."""
    budget = 150 * 1024 * 1024

    def __init__(self):
        super().__init__()
        self.total = 0

    def __getitem__(self, k):
        v = super().__getitem__(k)
        self.move_to_end(k)
        return v

    def __setitem__(self, k, v):
        if k in self:
            self.total -= _nbytes(OrderedDict.__getitem__(self, k))
        super().__setitem__(k, v)
        self.total += _nbytes(v)
        while self.total > self.budget and len(self) > 1:
            _, old = self.popitem(last=False)
            self.total -= _nbytes(old)


_cache = LRU()


def font(w, size):
    k = ("f", w, size)
    if k not in _cache:
        if isinstance(w, str):
            _cache[k] = ImageFont.truetype(w, size)
        else:
            _cache[k] = ImageFont.truetype(os.path.join(FONTDIR, f"PublicSans-{w}.ttf"), size)
    return _cache[k]


def to_premul(img):
    a = np.asarray(img, dtype=np.float32) / 255.0
    a[..., :3] *= a[..., 3:4]
    return a


def text_img(text, w=600, size=40, color=WHITE, tracking=0.0):
    f = font(w, size)
    asc, desc = f.getmetrics()
    if tracking:
        widths = [f.getlength(c) + tracking for c in text]
        tw = int(sum(widths) - tracking) + 4
    else:
        tw = int(f.getlength(text)) + 4
    th = asc + desc
    pad = 4
    im = Image.new("RGBA", (tw + 2 * pad, th + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if tracking:
        x = pad
        for c, cw in zip(text, widths):
            d.text((x, pad), c, font=f, fill=color + (255,), anchor="la")
            x += cw
    else:
        d.text((pad, pad), text, font=f, fill=color + (255,), anchor="la")
    return im


def text_sprite(text, w=600, size=40, color=WHITE, tracking=0.0, shadow=False):
    k = ("t", text, w, size, color, tracking, shadow)
    if k in _cache:
        return _cache[k]
    im = text_img(text, w, size, color, tracking)
    if shadow:
        sh = Image.new("RGBA", (im.width + 40, im.height + 40), (0, 0, 0, 0))
        a = im.split()[3]
        blk = Image.new("RGBA", im.size, (0, 0, 0, 255))
        blk.putalpha(a.point(lambda v: v * 0.55))
        sh.paste(blk, (20, 22), blk)
        sh = sh.filter(ImageFilter.GaussianBlur(9))
        sh.alpha_composite(im, (20, 20))
        im = sh
    spr = to_premul(im)
    _cache[k] = spr
    return spr


def rrect_img(w, h, r, fill=(255, 255, 255, 255), stroke=None, sw=0, ss=3):
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], r * ss, fill=fill,
                        outline=stroke, width=int(sw * ss) if stroke else 0)
    return im.resize((w, h), Image.LANCZOS)


def card_sprite(w, h, r=14, fill=(255, 255, 255, 255), shadow=28, stroke=None, sw=0):
    k = ("card", w, h, r, fill, shadow, stroke, sw)
    if k in _cache:
        return _cache[k]
    pad = shadow
    im = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    if shadow:
        sh = rrect_img(w, h, r, fill=(0, 0, 0, 90))
        im.paste(sh, (pad, pad + shadow // 3), sh)
        im = im.filter(ImageFilter.GaussianBlur(shadow / 2.2))
    im.alpha_composite(rrect_img(w, h, r, fill=fill, stroke=stroke, sw=sw), (pad, pad))
    spr = (to_premul(im), pad)
    _cache[k] = spr
    return spr


def box_sprite(w, h, color=ACC, sw=3, r=10):
    w, h = max(8, int(w) // 2 * 2), max(8, int(h) // 2 * 2)
    k = ("box", w, h, color, sw, r)
    if k in _cache:
        return _cache[k]
    pad = 18
    stroke = rrect_img(w, h, r, fill=(0, 0, 0, 0), stroke=color + (255,), sw=sw)
    glow = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    g2 = rrect_img(w, h, r, fill=color + (40,), stroke=color + (255,), sw=sw * 3)
    glow.paste(g2, (pad, pad), g2)
    glow = glow.filter(ImageFilter.GaussianBlur(8))
    glow.alpha_composite(stroke, (pad, pad))
    spr = (to_premul(glow), pad)
    _cache[k] = spr
    return spr


def blit(dst, spr, x, y, alpha=1.0):
    """dst uint8 HxWx3 (modified in place); spr premul float RGBA; x,y top-left (float ok)."""
    if alpha <= 0.003:
        return
    x, y = int(round(x)), int(round(y))
    sh, sw = spr.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(dst.shape[1], x + sw), min(dst.shape[0], y + sh)
    if x1 <= x0 or y1 <= y0:
        return
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    d = dst[y0:y1, x0:x1].astype(np.float32) / 255.0
    a = s[..., 3:4] * alpha
    d = d * (1 - a) + s[..., :3] * alpha
    dst[y0:y1, x0:x1] = np.clip(d * 255.0 + 0.5, 0, 255).astype(np.uint8)


def blit_scaled(dst, spr, cx, cy, scale=1.0, alpha=1.0):
    if abs(scale - 1) > 0.01:
        h, w = spr.shape[:2]
        spr = cv2.resize(spr, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_LINEAR)
    h, w = spr.shape[:2]
    blit(dst, spr, cx - w / 2, cy - h / 2, alpha)


def pill_sprite(text, size=24, w=600, fg=NAVY, bg=(255, 255, 255, 245), padx=16, pady=9, shadow=18, tracking=0.0, dot=None):
    k = ("pill", text, size, w, fg, bg, padx, pady, shadow, tracking, dot)
    if k in _cache:
        return _cache[k]
    t = text_img(text, w, size, fg, tracking)
    dw = (size * 0.55 + 10) if dot else 0
    cw, ch = int(t.width + 2 * padx + dw), int(t.height + 2 * pady)
    card, pad = card_sprite(cw, ch, r=ch // 2, fill=bg, shadow=shadow)
    im = Image.fromarray(np.uint8(np.clip(card[..., :3] / np.maximum(card[..., 3:4], 1e-6) * 255, 0, 255)))
    im.putalpha(Image.fromarray(np.uint8(card[..., 3] * 255)))
    if dot:
        d = ImageDraw.Draw(im)
        rr = size * 0.28
        cx, cy = pad + padx + rr, pad + ch / 2
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=dot + (255,))
    im.alpha_composite(t, (int(pad + padx + dw), int(pad + pady)))
    spr = (to_premul(im), pad)
    _cache[k] = spr
    return spr


def cursor_sprite():
    k = ("cursor",)
    if k in _cache:
        return _cache[k]
    ss = 4
    pts = [(0, 0), (0, 34), (9, 26), (15, 39), (21, 36), (15, 24), (26, 24)]
    im = Image.new("RGBA", (40 * ss, 50 * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    P = [(4 * ss + x * ss, 3 * ss + y * ss) for x, y in pts]
    d.polygon(P, fill=(20, 24, 30, 255))
    inner = [(4 * ss + x * ss * 0.86 + 1.6 * ss, 3 * ss + y * ss * 0.86 + 3.0 * ss) for x, y in pts]
    d.polygon(inner, fill=(255, 255, 255, 255))
    im = im.resize((40, 50), Image.LANCZOS)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    blk = Image.new("RGBA", im.size, (0, 0, 0, 120))
    blk.putalpha(im.split()[3].point(lambda v: v * 0.45))
    sh.paste(blk, (2, 3), blk)
    sh = sh.filter(ImageFilter.GaussianBlur(2))
    sh.alpha_composite(im)
    spr = to_premul(sh)
    _cache[k] = spr
    return spr


# ------------------------------------------------------------------ images

def load(name):
    k = ("img", name)
    if k not in _cache:
        p = name if os.path.isabs(name) else os.path.join(CAP, name + ".png")
        im = cv2.imread(p, cv2.IMREAD_COLOR)
        _cache[k] = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    return _cache[k]


_seq_last = {}


def seq_frame(i):
    i = int(i)
    if _seq_last.get("i") != i:
        im = cv2.imread(os.path.join(CAP, "run", f"f{i:04d}.png"))
        _seq_last["i"] = i
        _seq_last["im"] = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    return _seq_last["im"]


def cam_clamp(img, cx, cy, z):
    ih, iw = img.shape[:2]
    hw, hh = W / (2 * z), H / (2 * z)
    cx = clamp(cx, hw, max(hw, iw - hw))
    cy = clamp(cy, hh, max(hh, ih - hh))
    return cx, cy


def camera(img, cx, cy, z):
    cx, cy = cam_clamp(img, cx, cy, z)
    M = np.float32([[z, 0, W / 2 - cx * z], [0, z, H / 2 - cy * z]])
    flags = cv2.INTER_CUBIC if z > 1.02 else cv2.INTER_LINEAR
    return cv2.warpAffine(img, M, (W, H), flags=flags, borderMode=cv2.BORDER_REPLICATE)


def zoom_frame(fr, z, cx=None, cy=None):
    if abs(z - 1) < 1e-3 and cx is None:
        return fr
    h, w = fr.shape[:2]
    cx = w / 2 if cx is None else cx
    cy = h / 2 if cy is None else cy
    M = np.float32([[z, 0, w / 2 - cx * z], [0, z, h / 2 - cy * z]])
    return cv2.warpAffine(fr, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


# ------------------------------------------------------------------ cinematic finishing

rng = np.random.default_rng(3)
GRAIN = [rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32) for _ in range(4)]
yy, xx = np.mgrid[0:H, 0:W]
rr = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
VIG = (1 - 0.32 * np.clip(rr / 1.25, 0, 1) ** 2.2).astype(np.float32)[..., None]
del yy, xx, rr


def cine_finish(fr, fi, grain=5.0, vig=True):
    f = fr.astype(np.float32)
    if vig:
        f *= VIG
    g = cv2.resize(GRAIN[fi % 4], (W, H), interpolation=cv2.INTER_LINEAR)
    f += g[..., None] * grain
    return np.clip(f, 0, 255).astype(np.uint8)


def bars(fr, h, label=None, label_r=None, alpha=1.0):
    h = int(round(h))
    if h <= 0:
        return fr
    fr[:h] = (fr[:h].astype(np.float32) * (1 - alpha)).astype(np.uint8)
    fr[H - h:] = (fr[H - h:].astype(np.float32) * (1 - alpha)).astype(np.uint8)
    if label and h > 40:
        spr = text_sprite(label, 600, 17, (200, 205, 210), tracking=2.2)
        blit(fr, spr, 60, h / 2 - spr.shape[0] / 2, 0.75 * alpha)
    if label_r and h > 40:
        spr = text_sprite(label_r, 500, 17, (200, 205, 210), tracking=1.2)
        blit(fr, spr, W - 60 - spr.shape[1], h / 2 - spr.shape[0] / 2, 0.75 * alpha)
    return fr


STOCKLABEL = "ILLUSTRATIVE STOCK FOOTAGE  ·  MIXKIT"


# ------------------------------------------------------------------ stock readers

class Stock:
    def __init__(self, vid, start, dur, size=(W, H), fx=0.5, fy=0.5, grade=True, dim=1.0):
        self.path = os.path.join(STOCK, f"v_{vid}.mp4")
        self.start, self.dur, self.size = start, dur, size
        w, h = size
        vf = (f"fps={FPS},scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,"
              f"crop={w}:{h}:(iw-{w})*{fx}:(ih-{h})*{fy}")
        if grade:
            vf += (",eq=contrast=1.07:saturation=0.88:brightness=-0.015,"
                   "colorbalance=rs=-0.035:bs=0.045:rh=0.045:bh=-0.035")
        if dim != 1.0:
            vf += f",colorlevels=romax={dim}:gomax={dim}:bomax={dim}"
        self.vf = vf
        self.p = None
        self.n = 0
        self.last = None

    def _open(self, t0, frames=None):
        cmd = [FF, "-v", "error", "-ss", f"{self.start + t0:.3f}", "-i", self.path]
        if frames:
            cmd += ["-frames:v", str(frames)]
        else:
            cmd += ["-t", f"{self.dur + 1.0:.3f}"]
        cmd += ["-vf", self.vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10 ** 7)

    def get(self, t):
        w, h = self.size
        if PREVIEW:
            p = self._open(max(0, t), frames=1)
            data = p.stdout.read(w * h * 3)
            p.wait()
            if len(data) == w * h * 3:
                self.last = np.frombuffer(data, np.uint8).reshape(h, w, 3).copy()
            return self.last if self.last is not None else np.zeros((h, w, 3), np.uint8)
        if self.p is None:
            self.p = self._open(0)
        k = int(round(t * FPS))
        while self.n <= k:
            data = self.p.stdout.read(w * h * 3)
            if len(data) < w * h * 3:
                break
            self.last = np.frombuffer(data, np.uint8).reshape(h, w, 3).copy()
            self.n += 1
        return self.last if self.last is not None else np.zeros((h, w, 3), np.uint8)

    def close(self):
        if self.p:
            self.p.kill()
            self.p = None


# ------------------------------------------------------------------ timeline

class Scene:
    def __init__(self, name, dur, fn, kind):
        self.name, self.dur, self.fn, self.kind = name, dur, fn, kind
        self.start = 0.0
        self.stocks = []

    @property
    def end(self):
        return self.start + self.dur


SC = []
CUE = {}
CLICKS = []
WHOOSH = []


def add(name, dur, fn, kind="ui", xf=0.45):
    s = Scene(name, dur, fn, kind)
    s.start = SC[-1].end - xf if SC else 0.0
    s.xf = xf if SC else 0.0
    SC.append(s)
    return s


def cue(key, t):
    CUE[key] = t
    return t + DUR[key]


def wt(key, word, nth=1):
    """absolute time of the nth word in a VO line starting with `word`"""
    c = 0
    for w, off, d in WORDS[key]:
        if w.lower().strip(".,:;").startswith(word.lower()):
            c += 1
            if c == nth:
                return CUE[key] + off
    raise KeyError(f"{key}:{word}")


def wend(key):
    w = WORDS[key][-1]
    return CUE[key] + w[1] + w[2]


# ------------------------------------------------------------------ overlays shared by UI scenes

def draw_chip(fr, t, tin, eyebrow, title):
    a = eout(prog(t, tin, tin + 0.5))
    if a <= 0:
        return
    e = text_img(eyebrow, 700, 17, ACC, tracking=2.4)
    ti = text_img(title, 800, 34, NAVY)
    cw = max(e.width, ti.width) + 48
    ch = e.height + ti.height + 30
    k = ("chip", eyebrow, title)
    if k not in _cache:
        card, pad = card_sprite(cw, ch, r=14, fill=(255, 255, 255, 250), shadow=26)
        im = Image.fromarray(np.uint8(np.clip(card[..., :3] / np.maximum(card[..., 3:4], 1e-6) * 255, 0, 255)))
        im.putalpha(Image.fromarray(np.uint8(card[..., 3] * 255)))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([pad, pad + 14, pad + 5, pad + ch - 14], 3, fill=ACC + (255,))
        im.alpha_composite(e, (pad + 26, pad + 12))
        im.alpha_composite(ti, (pad + 26, pad + 12 + e.height + 2))
        _cache[k] = (to_premul(im), pad)
    spr, pad = _cache[k]
    blit(fr, spr, 48 - pad - 30 * (1 - a), 112 - pad, a)


def draw_badge(fr, t, tin, tout, text, color=(230, 70, 60)):
    a = win(t, tin, tout, 0.4, 0.4)
    if a <= 0:
        return
    spr, pad = pill_sprite(text, size=19, w=700, fg=WHITE, bg=(14, 24, 36, 228), padx=18, pady=10, shadow=16, tracking=1.6, dot=color)
    blit(fr, spr, W - 48 - spr.shape[1] + pad, 112 - pad, a)
    pulse = 0.5 + 0.5 * math.sin(t * 6.0)
    # pulsing halo over the dot
    cx = W - 48 - spr.shape[1] + 2 * pad + 18 + 19 * 0.28
    cy = 112 + (spr.shape[0] - 2 * pad) / 2
    r = int(8 + 6 * pulse)
    ov = fr.copy()
    cv2.circle(ov, (int(cx), int(cy)), r, color, -1, cv2.LINE_AA)
    cv2.addWeighted(ov, 0.25 * a * (1 - pulse), fr, 1 - 0.25 * a * (1 - pulse), 0, fr)


def draw_callout(fr, t, tin, tout, text, ax, ay, dx, dy):
    a = win(t, tin, tout, 0.35, 0.3)
    if a <= 0:
        return
    k = eout(prog(t, tin, tin + 0.45))
    lx, ly = ax + dx * k, ay + dy * k
    spr, pad = pill_sprite(text, size=24, w=600, fg=NAVY, bg=(255, 255, 255, 250), padx=18, pady=10, shadow=22)
    sw, sh = spr.shape[1] - 2 * pad, spr.shape[0] - 2 * pad
    # label anchored so the line meets its nearest edge
    bx = lx - (sw if dx < 0 else 0)
    by = ly - sh / 2
    ov = fr.copy()
    ex = bx + (sw if dx < 0 else 0)
    cv2.line(ov, (int(ax), int(ay)), (int(ex), int(ly)), ACC, 3, cv2.LINE_AA)
    cv2.circle(ov, (int(ax), int(ay)), 9, ACC, -1, cv2.LINE_AA)
    cv2.circle(ov, (int(ax), int(ay)), 4, WHITE, -1, cv2.LINE_AA)
    cv2.addWeighted(ov, a, fr, 1 - a, 0, fr)
    blit(fr, spr, bx - pad, by - pad, a)


def draw_box(fr, t, tin, tout, x0, y0, x1, y1):
    a = win(t, tin, tout, 0.3, 0.3)
    if a <= 0:
        return
    grow = 10 * (1 - eout(prog(t, tin, tin + 0.4)))
    spr, pad = box_sprite(x1 - x0 + 16 + 2 * grow, y1 - y0 + 16 + 2 * grow)
    blit(fr, spr, x0 - 8 - grow - pad, y0 - 8 - grow - pad, a)


def draw_ripple(fr, t, tc, x, y):
    p = prog(t, tc, tc + 0.55)
    if p <= 0 or p >= 1:
        return
    r = int(10 + 38 * eout(p))
    ov = fr.copy()
    cv2.circle(ov, (int(x), int(y)), r, BLUE, -1, cv2.LINE_AA)
    cv2.addWeighted(ov, 0.30 * (1 - p), fr, 1 - 0.30 * (1 - p), 0, fr)
    ov = fr.copy()
    cv2.circle(ov, (int(x), int(y)), r, WHITE, 3, cv2.LINE_AA)
    cv2.addWeighted(ov, 0.8 * (1 - p), fr, 1 - 0.8 * (1 - p), 0, fr)


def blur_dim(fr, amt):
    if amt <= 0.01:
        return fr
    small = cv2.resize(fr, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), 3)
    bl = cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32)
    f = fr.astype(np.float32) * (1 - amt) + bl * amt
    f *= (1 - 0.42 * amt)
    return np.clip(f, 0, 255).astype(np.uint8)


def popout_sprite(img_key, region, scale):
    k = ("pop", img_key, region, scale)
    if k in _cache:
        return _cache[k]
    x0, y0, x1, y1 = region
    crop = load(img_key)[y0:y1, x0:x1]
    up = cv2.resize(crop, (int((x1 - x0) * scale), int((y1 - y0) * scale)), interpolation=cv2.INTER_CUBIC)
    h, w = up.shape[:2]
    pad = 40
    im = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    sh = rrect_img(w, h, 18, fill=(0, 0, 0, 150))
    im.paste(sh, (pad, pad + 14), sh)
    im = im.filter(ImageFilter.GaussianBlur(18))
    body = Image.fromarray(up).convert("RGBA")
    mask = rrect_img(w, h, 18, fill=(255, 255, 255, 255)).split()[3]
    body.putalpha(mask)
    im.alpha_composite(body, (pad, pad))
    ring = rrect_img(w, h, 18, fill=(0, 0, 0, 0), stroke=(255, 255, 255, 200), sw=2)
    im.alpha_composite(ring, (pad, pad))
    spr = (to_premul(im), pad, w, h)
    _cache[k] = spr
    return spr


# ------------------------------------------------------------------ UI scene engine

def interp_keys(keys, t):
    if t <= keys[0][0]:
        return keys[0][1:]
    for (ta, *va), (tb, *vb) in zip(keys, keys[1:]):
        if t <= tb:
            p = eio(prog(t, ta, tb))
            return tuple(a + (b - a) * p for a, b in zip(va, vb))
    return keys[-1][1:]


def ui_scene(dur, shots, cam, chip=None, boxes=(), callouts=(), popouts=(), cursor=None,
             clicks=(), badge=None, seq=None, local=True):
    """All times are scene-local seconds. Coordinates are image (screenshot) pixels."""

    def base_at(t, key):
        if key == "SEQ":
            t0, t1, i0, i1 = seq
            i = i0 + (i1 - i0) * clamp((t - t0) / (t1 - t0))
            return seq_frame(round(i))
        return load(key)

    def render(t, fi):
        cx, cy, z = interp_keys(cam, t)
        cur = [s for s in shots if s[0] <= t]
        cur_key = cur[-1][1] if cur else shots[0][1]
        img = base_at(t, cur_key)
        cxc, cyc = cam_clamp(img, cx, cy, z)
        fr = camera(img, cx, cy, z)
        if len(cur) >= 2 and t - cur[-1][0] < 0.35:
            prev = camera(base_at(t, cur[-2][1]), cx, cy, z)
            p = eio((t - cur[-1][0]) / 0.35)
            fr = cv2.addWeighted(fr, p, prev, 1 - p, 0)

        def S(x, y):
            return (x - cxc) * z + W / 2, (y - cyc) * z + H / 2

        for (tin, tout, x0, y0, x1, y1) in boxes:
            a0, b0 = S(x0, y0)
            a1, b1 = S(x1, y1)
            draw_box(fr, t, tin, tout, a0, b0, a1, b1)
        for (tin, tout, text, ax, ay, dx, dy) in callouts:
            sx, sy = S(ax, ay)
            draw_callout(fr, t, tin, tout, text, sx, sy, dx, dy)
        if cursor:
            pts = cursor
            if pts[0][0] - 0.3 <= t <= pts[-1][0] + 0.6:
                x, y = interp_keys(pts, t)
                sx, sy = S(x, y)
                for tc in clicks:
                    draw_ripple(fr, t, tc, sx, sy)
                a = min(eout(prog(t, pts[0][0] - 0.3, pts[0][0])), 1 - prog(t, pts[-1][0] + 0.2, pts[-1][0] + 0.6))
                press = any(0 <= t - tc < 0.15 for tc in clicks)
                spr = cursor_sprite()
                blit_scaled(fr, spr, sx + spr.shape[1] / 2 - 6, sy + spr.shape[0] / 2 - 5, 0.9 if press else 1.0, a)
        # popouts
        pa = 0.0
        for (tin, tout, key, region, scale, (pcx, pcy), hls) in popouts:
            pa = max(pa, win(t, tin, tout, 0.4, 0.35))
        if pa > 0:
            fr = blur_dim(fr, 0.85 * pa)
            for (tin, tout, key, region, scale, (pcx, pcy), hls) in popouts:
                a = win(t, tin, tout, 0.4, 0.35)
                if a <= 0:
                    continue
                spr, pad, w, h = popout_sprite(key, region, scale)
                sc = 0.94 + 0.06 * eout(prog(t, tin, tin + 0.45))
                blit_scaled(fr, spr, pcx, pcy + 18 * (1 - a), sc, a)
                for (hin, hout, x0, y0, x1, y1) in hls:
                    X0 = pcx + ((x0 - region[0]) * scale - w / 2) * sc
                    Y0 = pcy + 18 * (1 - a) + ((y0 - region[1]) * scale - h / 2) * sc
                    X1 = pcx + ((x1 - region[0]) * scale - w / 2) * sc
                    Y1 = pcy + 18 * (1 - a) + ((y1 - region[1]) * scale - h / 2) * sc
                    draw_box(fr, t, max(hin, tin + 0.2), min(hout, tout), X0, Y0, X1, Y1)
        if chip:
            draw_chip(fr, t, chip[0], chip[1], chip[2])
        if badge:
            draw_badge(fr, t, *badge)
        return fr

    return render


# ------------------------------------------------------------------ cinematic scenes

def stock_scene(vid, start, dur, z0=1.0, z1=1.08, pan=(0, 0), label=STOCKLABEL, label_r=None, fx=0.5, fy=0.5, dim=1.0):
    st = Stock(vid, start, dur + 1, fx=fx, fy=fy, dim=dim)

    def render(t, fi):
        fr = st.get(t)
        p = t / dur
        z = z0 + (z1 - z0) * p
        fr = zoom_frame(fr, z, W / 2 + pan[0] * p, H / 2 + pan[1] * p)
        fr = cine_finish(fr, fi)
        return bars(fr, BAR, label, label_r)

    render.stocks = [st]
    return render


def micro_scene(dur):
    big = cv2.cvtColor(cv2.imread(MICRO), cv2.COLOR_BGR2RGB)
    ih, iw = big.shape[:2]

    def render(t, fi):
        p = eio(t / dur)
        z = (W / iw) * (1.04 + 0.22 * p)
        cx, cy = iw * (0.5 + 0.06 * p), ih * (0.5 - 0.04 * p)
        M = np.float32([[z, 0, W / 2 - cx * z], [0, z, H / 2 - cy * z]])
        fr = cv2.warpAffine(big, M, (W, H), flags=cv2.INTER_AREA if z < 1 else cv2.INTER_LINEAR)
        fr = cine_finish(fr, fi, grain=3.0)
        return bars(fr, BAR, "REFLECTED-LIGHT MICROGRAPH", "LUMENSTONE S2  ·  TEST_11  ·  PUBLIC DATASET")

    return render


def make_xrf_scene(dur, start_abs):
    bg = Stock("32990", 1.0, dur + 1, dim=0.45)
    # micrograph mosaic + pentlandite mask from the real model output
    orig = load(os.path.join(CAP, "hi_view_Original.png"))[:, 496:1860]
    mask = load(os.path.join(CAP, "hi_view_Phase_mask.png"))[:, 496:1860].astype(int)
    r, g, b = mask[..., 0], mask[..., 1], mask[..., 2]
    pent = ((b > g + 35) & (r > g + 15)).astype(np.float32)
    pent = cv2.GaussianBlur(pent, (0, 0), 1.2)[..., None]
    CW = 1040
    CH = int(orig.shape[0] * CW / orig.shape[1])
    o = cv2.resize(orig, (CW, CH), interpolation=cv2.INTER_AREA).astype(np.float32)
    pm = cv2.resize(pent, (CW, CH), interpolation=cv2.INTER_AREA)[..., None]
    grey = o.mean(axis=2, keepdims=True) * 0.55
    purple = np.array([168, 102, 230], np.float32)
    hl = grey * (1 - pm) + (o * 0.35 + purple * 0.75) * pm
    o_u8 = np.clip(o, 0, 255).astype(np.uint8)
    hl_u8 = np.clip(hl, 0, 255).astype(np.uint8)
    elements = [("28", "Ni", "Nickel", "nickel"), ("29", "Cu", "Copper", "copper"),
                ("24", "Cr", "Chromium", "chrome"), ("16", "S", "Sulphur", "sulphur")]

    def tile(num, sym, name, glow=0.0):
        k = ("tile", sym, round(glow, 2))
        if k in _cache:
            return _cache[k]
        s = 176
        im = Image.new("RGBA", (s + 60, s + 60), (0, 0, 0, 0))
        border = ACC + (255,) if glow > 0.5 else (255, 255, 255, 200)
        body = rrect_img(s, s, 16, fill=(16, 26, 38, 215), stroke=border, sw=2.5)
        if glow > 0:
            gl = Image.new("RGBA", im.size, (0, 0, 0, 0))
            gg = rrect_img(s, s, 16, fill=ACC + (int(120 * glow),))
            gl.paste(gg, (30, 30), gg)
            im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(16)))
        im.alpha_composite(body, (30, 30))
        im.alpha_composite(text_img(num, 600, 22, (200, 210, 220)), (46, 40))
        sy = text_img(sym, 800, 78, WHITE)
        im.alpha_composite(sy, (30 + (s - sy.width) // 2, 30 + 40))
        nm = text_img(name, 500, 21, (210, 218, 226))
        im.alpha_composite(nm, (30 + (s - nm.width) // 2, 30 + s - 44))
        spr = to_premul(im)
        _cache[k] = spr
        return spr

    def render(t, fi):
        T = start_abs + t
        fr = bg.get(t)
        fr = zoom_frame(fr, 1.05 + 0.05 * t / dur)
        fr = cv2.GaussianBlur(fr, (0, 0), 2.5)
        fr = cine_finish(fr, fi, grain=4.0)
        t_xrf, t_el = wt("n03", "XRF"), wt("n03", "elements")
        t_n4 = CUE["n04"]
        t_min = wt("n04", "mineral", 2)
        t_free, t_lock = wt("n04", "free"), wt("n04", "locked")
        # header
        a1 = win(T, t_xrf - 0.1, t_n4 + 0.2, 0.4, 0.4)
        h1 = text_sprite("HANDHELD XRF", 800, 30, ACC, tracking=6)
        blit(fr, h1, W / 2 - h1.shape[1] / 2, 210, a1)
        s1 = text_sprite("reads the elements", 400, 44, WHITE)
        blit(fr, s1, W / 2 - s1.shape[1] / 2, 258, win(T, t_el - 0.1, t_n4 + 0.2, 0.4, 0.4))
        a2 = win(T, t_n4 + 0.1, 1e9, 0.5, 0)
        h2 = text_sprite("ELEMENTS ARE NOT MINERALS", 800, 30, ACC, tracking=6)
        blit(fr, h2, W / 2 - h2.shape[1] / 2, 150, a2)
        # tiles
        mv = eio(prog(T, t_n4 + 0.1, t_n4 + 1.1))
        for i, (num, sym, name, word) in enumerate(elements):
            tin = wt("n03", word)
            a = eout(prog(T, tin - 0.05, tin + 0.35))
            if a <= 0:
                continue
            glow = eout(prog(T, t_min, t_min + 0.5)) if sym == "Ni" else 0.0
            spr = tile(num, sym, name, glow)
            x_row = W / 2 + (i - 1.5) * 214
            y_row = 520
            x_col = 205
            y_col = 300 + i * 176
            x = x_row + (x_col - x_row) * mv
            y = y_row + (y_col - y_row) * mv + 30 * (1 - a)
            sc = 1.0 - 0.18 * mv
            blit_scaled(fr, spr, x, y, sc * (0.9 + 0.1 * a), a * (1.0 if sym == "Ni" or T < t_min else 1 - 0.45 * prog(T, t_min, t_min + 0.5)))
        # micrograph card
        ac = eout(prog(T, t_n4 + 0.6, t_n4 + 1.3))
        if ac > 0:
            cxp, cyp = 1130, 560
            x0, y0 = int(cxp - CW / 2), int(cyp - CH / 2 + 24 * (1 - ac))
            ph = eio(prog(T, t_min, t_min + 0.6))
            img = cv2.addWeighted(hl_u8, ph, o_u8, 1 - ph, 0) if ph > 0 else o_u8
            card, pad = card_sprite(CW + 8, CH + 8, r=14, fill=(255, 255, 255, 230), shadow=30)
            blit(fr, card, x0 - 4 - pad, y0 - 4 - pad, ac)
            region = fr[y0:y0 + CH, x0:x0 + CW]
            fr[y0:y0 + CH, x0:x0 + CW] = cv2.addWeighted(img, ac, region, 1 - ac, 0)
            lab = text_sprite("MODEL PREDICTION  ·  LUMENSTONE S2 TEST_11", 600, 15, (220, 226, 232), tracking=1.6)
            blit(fr, lab, x0, y0 + CH + 14, ac * 0.85)
            if ph > 0:
                tag = text_sprite("PENTLANDITE", 800, 30, WHITE, tracking=3)
                fm = text_sprite("(Fe,Ni)₉S₈  ·  carries the nickel", r"C:\Windows\Fonts\segoeuisl.ttf", 28, (232, 222, 250))
                bw = max(tag.shape[1], fm.shape[1]) + 36
                bh = tag.shape[0] + fm.shape[0] + 26
                card2, pad2 = card_sprite(bw, bh, r=12, fill=(14, 22, 34, 225), shadow=18)
                blit(fr, card2, x0 + 18 - pad2, y0 + 18 - pad2, ph)
                ov = fr.copy()
                cv2.rectangle(ov, (x0 + 18, y0 + 30), (x0 + 22, y0 + 18 + bh - 12), (168, 102, 230), -1)
                cv2.addWeighted(ov, ph, fr, 1 - ph, 0, fr)
                blit(fr, tag, x0 + 34, y0 + 26, ph)
                blit(fr, fm, x0 + 34, y0 + 26 + tag.shape[0] + 2, ph)
            for (tw_, label, col, xo) in [(t_free, "FREE  ·  floats", (60, 170, 110), 0), (t_lock, "LOCKED  ·  trapped in rock", ACC, 1)]:
                a = eout(prog(T, tw_ - 0.05, tw_ + 0.35))
                if a > 0:
                    spr, pad = pill_sprite(label, size=26, w=700, fg=WHITE, bg=col + (240,), padx=20, pady=11, shadow=20, tracking=1.0)
                    px = x0 + (0 if xo == 0 else CW - (spr.shape[1] - 2 * pad))
                    blit(fr, spr, px - pad, y0 + CH - 80 - pad + 16 * (1 - a), a)
        return bars(fr, BAR, STOCKLABEL + "  +  MOTION GRAPHIC")

    render.stocks = [bg]
    return render


def triptych_scene(dur, start_abs):
    pw = (W - 4 * 22) // 3
    ph = H - 2 * BAR
    clips = [Stock("40069", 1.0, dur + 1, size=(pw, ph), fx=0.5, fy=0.45),
             Stock("24078", 2.0, dur + 1, size=(pw, ph), fx=0.62, fy=0.5),
             Stock("42664", 0.5, dur + 1, size=(pw, ph), fx=0.48, fy=0.5)]
    labels = ["IN THE BAKKIE", "AT THE CORE YARD", "IN THE PLANT OFFICE"]
    words = [("bakkie", 1), ("phone", 1), ("desk", 1)]

    def render(t, fi):
        T = start_abs + t
        fr = np.full((H, W, 3), 8, np.uint8)
        for i, st in enumerate(clips):
            tin = wt("n07", words[i][0]) - 0.45
            a = eout(prog(T, tin, tin + 0.6))
            if a <= 0:
                continue
            p = st.get(t)
            p = zoom_frame(p, 1.04 + 0.04 * t / dur)
            x = 22 + i * (pw + 22)
            y = BAR + int(50 * (1 - a))
            hh = min(ph, H - BAR - y)
            reg = fr[y:y + hh, x:x + pw]
            fr[y:y + hh, x:x + pw] = cv2.addWeighted(p[:hh], a, reg, 1 - a, 0)
        fr = cine_finish(fr, fi, grain=4.0)
        for i in range(3):
            tin = wt("n07", words[i][0]) - 0.45
            a = eout(prog(T, tin + 0.25, tin + 0.8))
            spr = text_sprite(labels[i], 800, 28, WHITE, tracking=4, shadow=True)
            x = 22 + i * (pw + 22) + 36
            blit(fr, spr, x - 20, H - BAR - 92 - 20 + 10 * (1 - a), a)
            ov = fr.copy()
            cv2.line(ov, (x, H - BAR - 98), (x + int(56 * a), H - BAR - 98), ACC, 4, cv2.LINE_AA)
            cv2.addWeighted(ov, a, fr, 1 - a, 0, fr)
        return bars(fr, BAR, STOCKLABEL)

    render.stocks = clips
    return render


def order_quad(pts):
    pts = np.asarray(pts, np.float32).reshape(-1, 2)
    s = pts.sum(1)
    d = pts[:, 1] - pts[:, 0]
    return np.float32([pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]])


def quad_from_mask(m):
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    c = max(cnts, key=cv2.contourArea)
    if cv2.contourArea(c) < 4000:
        return None
    hull = cv2.convexHull(c)
    peri = cv2.arcLength(hull, True)
    ap = cv2.approxPolyDP(hull, 0.03 * peri, True)
    if len(ap) == 4:
        return order_quad(ap)
    return order_quad(cv2.boxPoints(cv2.minAreaRect(hull)))


def warp_into(fr, content, quad, alpha):
    qw = int(max(np.linalg.norm(quad[1] - quad[0]), 50))
    qh = int(max(np.linalg.norm(quad[3] - quad[0]), 50))
    c = cv2.resize(content, (qw * 2, qh * 2), interpolation=cv2.INTER_AREA)
    src = np.float32([[0, 0], [qw * 2, 0], [qw * 2, qh * 2], [0, qh * 2]])
    M = cv2.getPerspectiveTransform(src, quad)
    wc = cv2.warpPerspective(c, M, (fr.shape[1], fr.shape[0]), flags=cv2.INTER_LINEAR)
    a = alpha[..., None]
    return np.clip(fr * (1 - a) + wc * a, 0, 255).astype(np.uint8)


def laptop_title_scene(dur, start_abs):
    lap = Stock("48285", 3.0, dur + 1, grade=False)
    dash = load("d01_dashboard_real")
    brand = load(os.path.join(CAP, "hi_brand.png"))
    icon = brand[:, :82]
    g = icon.mean(axis=2)
    ia = np.clip((235 - g) / 160, 0, 1).astype(np.float32)
    icon_spr = np.dstack([ia, ia, ia, ia]).astype(np.float32)
    icon_spr = cv2.resize(icon_spr, (int(82 * 1.6), int(82 * 1.6)), interpolation=cv2.INTER_CUBIC)
    title_end = 3.4
    state = {"quad": None}

    def title_bg(t):
        return navy_bg(t)

    def render(t, fi):
        T = start_abs + t
        # --- laptop layer
        lt = max(0.0, t - (title_end - 0.6))
        fr = lap.get(lt)
        hsv = cv2.cvtColor(fr, cv2.COLOR_RGB2HSV)
        m = cv2.inRange(hsv, (58, 45, 60), (100, 255, 255))
        q = quad_from_mask(m)
        if q is not None:
            state["quad"] = q
        q = state["quad"]
        if q is not None:
            poly = np.zeros((H, W), np.uint8)
            cv2.fillConvexPoly(poly, q.astype(np.int32), 255)
            mm = cv2.dilate(m, np.ones((5, 5), np.uint8)) & poly
            alpha = cv2.GaussianBlur(mm, (0, 0), 1.2).astype(np.float32) / 255.0
            fr = warp_into(fr.astype(np.float32), dash, q, alpha)
            qc = q.mean(axis=0)
            qw = np.linalg.norm(q[1] - q[0])
            pz = eio(prog(t, dur - 2.9, dur))
            zt = W / qw * 1.0
            z = 1.0 + (zt - 1.0) * pz
            cx = W / 2 + (qc[0] - W / 2) * pz
            cy = H / 2 + (qc[1] - H / 2) * pz
            fr = zoom_frame(fr, z, cx, cy)
        bh = BAR * (1 - eio(prog(t, dur - 2.9, dur - 0.6)))
        fr = cine_finish(fr, fi, grain=3.0 * (1 - prog(t, dur - 2.0, dur)), vig=False)
        fr = bars(fr, bh, STOCKLABEL + "  ·  SCREEN: REAL REEFPRINT UI")
        # --- title card on top, fading out
        ta = 1 - eio(prog(t, title_end - 0.5, title_end + 0.2))
        if ta > 0:
            card = navy_bg(t)
            t_r = wt("n08", "REEFPRINT")
            a = eout(prog(T, t_r - 0.35, t_r + 0.3))
            trk = 34 * (1 - eout(prog(T, t_r - 0.35, t_r + 1.4))) + 10
            blit_scaled(card, icon_spr, W / 2, 330, 0.9 + 0.1 * a, a)
            ti = text_sprite("REEFPRINT", 900, 132, WHITE, tracking=2 * round(trk / 2))
            blit(card, ti, W / 2 - ti.shape[1] / 2, 410, a)
            t_k = wt("n08", "KHANYA")
            a2 = eout(prog(T, t_k - 0.5, t_k + 0.1))
            k2 = text_sprite("ALSO KNOWN AS  KHANYA", 600, 30, (190, 205, 222), tracking=8)
            blit(card, k2, W / 2 - k2.shape[1] / 2, 590, a2)
            t_m = wt("n08", "Mineral")
            a3 = eout(prog(T, t_m - 0.3, t_m + 0.3))
            k3 = text_sprite("Mineral intelligence from a micrograph.", 400, 40, WHITE)
            blit(card, k3, W / 2 - k3.shape[1] / 2, 660, a3)
            ov = card.copy()
            cv2.line(ov, (int(W / 2 - 60 * a2), 642), (int(W / 2 + 60 * a2), 642), ACC, 3, cv2.LINE_AA)
            card = cv2.addWeighted(ov, a2, card, 1 - a2, 0)
            fr = cv2.addWeighted(card, ta, fr, 1 - ta, 0)
        return fr

    render.stocks = [lap]
    return render


_navy = {}


def navy_bg(t):
    if "bg" not in _navy:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W * 0.5) / W) ** 2 + ((yy - H * 0.42) / H) ** 2)
        c0 = np.array([30, 58, 88], np.float32)
        c1 = np.array([9, 18, 30], np.float32)
        k = np.clip(r / 0.75, 0, 1)[..., None]
        _navy["bg"] = c0 * (1 - k) + c1 * k
        mic = cv2.cvtColor(cv2.imread(MICRO), cv2.COLOR_BGR2GRAY)
        _navy["mic"] = mic
    mic = _navy["mic"]
    ih, iw = mic.shape
    z = W / iw * (1.15 + 0.02 * t)
    M = np.float32([[z, 0, W / 2 - iw / 2 * z], [0, z, H / 2 - ih / 2 * z]])
    tex = cv2.warpAffine(mic, M, (W, H), flags=cv2.INTER_LINEAR).astype(np.float32)
    f = _navy["bg"] + (tex[..., None] - 128) * 0.10
    return np.clip(f, 0, 255).astype(np.uint8)


def phone_scene(dur):
    ph = Stock("28300", 1.0, dur + 1, grade=False)
    bgv = Stock("45821", 7.0, dur + 1)
    page = load("m_Workspace_full")
    state = {"quad": None}

    def render(t, fi):
        fr = ph.get(t).astype(np.int16)
        # zoom the source so the phone reads larger
        r, g, b = fr[..., 0], fr[..., 1], fr[..., 2]
        green = ((g - np.maximum(r, b)) > 38).astype(np.uint8) * 255
        n, lab, stats, _ = cv2.connectedComponentsWithStats(green, 8)
        border = np.zeros_like(green)
        inner = np.zeros_like(green)
        for i in range(1, n):
            x, y, w, h, area = stats[i]
            touches = x <= 1 or y <= 1 or x + w >= W - 1 or y + h >= H - 1
            if touches and area > 50000:
                border[lab == i] = 255
            elif area > 3000:
                inner[lab == i] = 255
        q = quad_from_mask(inner)
        if q is not None:
            state["quad"] = q
        q = state["quad"]
        f = fr.astype(np.float32)
        # despill
        mx = np.maximum(f[..., 0], f[..., 2])
        f[..., 1] = np.minimum(f[..., 1], mx * 1.08 + 6)
        # background replacement
        bgf = bgv.get(t)
        bgf = cv2.GaussianBlur(bgf, (0, 0), 7).astype(np.float32) * 0.85
        ba = cv2.GaussianBlur(border, (0, 0), 1.5).astype(np.float32)[..., None] / 255.0
        f = f * (1 - ba) + bgf * ba
        if q is not None:
            poly = np.zeros((H, W), np.uint8)
            cv2.fillConvexPoly(poly, q.astype(np.int32), 255)
            # inside the screen: green + small markers become screen; large non-green blobs are fingers
            nongreen = cv2.bitwise_and(poly, cv2.bitwise_not(green))
            n2, lab2, st2, _ = cv2.connectedComponentsWithStats(nongreen, 8)
            fill = np.zeros_like(green)
            for i in range(1, n2):
                if st2[i][4] < 2500:
                    fill[lab2 == i] = 255
            scr = cv2.bitwise_or(cv2.bitwise_and(green, poly), fill)
            scr = cv2.dilate(scr, np.ones((3, 3), np.uint8))
            a = cv2.GaussianBlur(scr, (0, 0), 1.0).astype(np.float32) / 255.0
            qw = np.linalg.norm(q[1] - q[0])
            qh = np.linalg.norm(q[3] - q[0])
            ph_w = page.shape[1]
            vh = int(ph_w * qh / qw)
            y0 = int(1650 + 650 * eio(prog(t, 0.6, dur - 0.6)))
            y0 = min(y0, page.shape[0] - vh)
            content = page[y0:y0 + vh]
            f = warp_into(f, content, q, a).astype(np.float32)
        fr = np.clip(f, 0, 255).astype(np.uint8)
        fr = zoom_frame(fr, 1.55, 905, 470)
        fr = cine_finish(fr, fi, grain=3.0)
        return fr

    render.stocks = [ph, bgv]
    return render


def montage_scene(dur, start_abs):
    cuts = [(0.0, Stock("4380", 3.0, 4.5)), (3.4, Stock("45825", 0.5, 4.5)), (6.8, Stock("45821", 6.0, dur - 6.8 + 1))]
    lines = [("n23", "Three", "3 mineral phases identified"),
             ("n23", "accuracy", "An accuracy report, every number traced"),
             ("n23", "path", "A plant decision that knows when not to act")]

    def render(t, fi):
        T = start_abs + t
        idx = max(i for i, (s, _) in enumerate(cuts) if t >= s)
        s0, st = cuts[idx]
        fr = st.get(t - s0)
        fr = zoom_frame(fr, 1.04 + 0.05 * (t - s0) / 3.4)
        if idx > 0 and t - s0 < 0.3:
            ps, pst = cuts[idx - 1]
            pf = zoom_frame(pst.get(t - ps), 1.04 + 0.05 * (t - ps) / 3.4)
            p = (t - s0) / 0.3
            fr = cv2.addWeighted(fr, p, pf, 1 - p, 0)
        fr = (fr.astype(np.float32) * 0.62).astype(np.uint8)
        fr = cine_finish(fr, fi, grain=4.0)
        for i, (k, w, txt) in enumerate(lines):
            tin = wt(k, w) - 0.15
            a = eout(prog(T, tin, tin + 0.5))
            if a <= 0:
                continue
            nxt = wt(lines[i + 1][0], lines[i + 1][1]) if i + 1 < len(lines) else 1e9
            dimk = 1 - 0.45 * prog(T, nxt, nxt + 0.4)
            spr = text_sprite(txt, 800, 62, WHITE, shadow=True)
            y = 300 + i * 150
            blit(fr, spr, 140 - 20 + 40 * (1 - a), y - 20, a * dimk)
            ov = fr.copy()
            cv2.line(ov, (140, y + 104), (140 + int(90 * a), y + 104), ACC, 5, cv2.LINE_AA)
            cv2.addWeighted(ov, a * dimk, fr, 1 - a * dimk, 0, fr)
        return bars(fr, BAR, STOCKLABEL)

    render.stocks = [c[1] for c in cuts]
    return render


def end_card(dur, start_abs):
    brand = load(os.path.join(CAP, "hi_brand.png"))
    icon = brand[:, :82]
    g = icon.mean(axis=2)
    ia = np.clip((235 - g) / 160, 0, 1).astype(np.float32)
    icon_spr = cv2.resize(np.dstack([ia, ia, ia, ia]), (120, 120), interpolation=cv2.INTER_CUBIC)

    def render(t, fi):
        fr = navy_bg(t + 10)
        a = eout(prog(t, 0.0, 0.7))
        blit_scaled(fr, icon_spr, W / 2, 268, 1, a)
        ti = text_sprite("REEFPRINT", 900, 120, WHITE, tracking=10)
        blit(fr, ti, W / 2 - ti.shape[1] / 2, 330 + 14 * (1 - a), a)
        a2 = eout(prog(t, 0.4, 1.1))
        k2 = text_sprite("ALSO KNOWN AS  KHANYA", 600, 28, (190, 205, 222), tracking=8)
        blit(fr, k2, W / 2 - k2.shape[1] / 2, 490, a2)
        ov = fr.copy()
        cv2.line(ov, (int(W / 2 - 70 * a2), 552), (int(W / 2 + 70 * a2), 552), ACC, 3, cv2.LINE_AA)
        cv2.addWeighted(ov, a2, fr, 1 - a2, 0, fr)
        a3 = eout(prog(t, 0.9, 1.6))
        l1 = text_sprite("TEAM SONAR", 800, 30, WHITE, tracking=7)
        blit(fr, l1, W / 2 - l1.shape[1] / 2, 590, a3)
        l2 = text_sprite("Lethabo Hoaeane   ·   Sibusiso Khumalo   ·   Ipeleng Modise", 400, 28, (210, 220, 232))
        blit(fr, l2, W / 2 - l2.shape[1] / 2, 640, a3)
        a4 = eout(prog(t, 1.4, 2.1))
        l3 = text_sprite("Mintek–SCi Grad Hackathon 2026  ·  Computer Vision for Real-Time Mineralogical Characterisation", 400, 22, (160, 178, 198))
        blit(fr, l3, W / 2 - l3.shape[1] / 2, 730, a4)
        return fr

    return render


DISCLOSE = [
    "Field, lab, bakkie and office scenes are Mixkit stock footage (free licence). Illustrative only:",
    "they are not REEFPRINT users, customers or sites.",
    "App footage is the real REEFPRINT / KHANYA workbench, recorded 1 October 2026, running live",
    "CPU inference on the public LumenStone S2 dataset.",
    "Active model fb78727d: mean IoU 0.454 on 12 held-out sections, magnetite IoU 0. Not approved for control.",
    "Retrained candidate 42646cfa (mIoU 0.632, same 12 sections) is quarantined and not deployed.",
    "Plant actions run in a local simulator. There is no live plant connection and no recovery gain is claimed.",
    "Narration is a synthetic voice (en-ZA). Music is an original composition made for this video.",
]


def disclose_card(dur):
    def render(t, fi):
        fr = navy_bg(t + 16)
        fr = (fr.astype(np.float32) * 0.8).astype(np.uint8)
        a = eout(prog(t, 0.0, 0.6))
        h = text_sprite("WHAT YOU JUST SAW", 800, 26, ACC, tracking=7)
        blit(fr, h, 200, 250, a)
        y = 320
        for i, line in enumerate(DISCLOSE):
            ai = eout(prog(t, 0.2 + i * 0.07, 0.8 + i * 0.07))
            spr = text_sprite(line, 400, 30, (225, 232, 240))
            cont = i in (1, 3)
            y += 8 if cont else 26
            blit(fr, spr, 200, y, ai)
            y += 38
        fo = 1 - prog(t, dur - 1.0, dur)
        return (fr.astype(np.float32) * fo).astype(np.uint8)

    return render


# ------------------------------------------------------------------ captions

def caption_chunks():
    out = []
    for key, text in NARR.items():
        if key not in CUE:
            continue
        parts = re.split(r"(?<=[.,:;?])\s+", text)
        phrases = []
        for p in parts:
            if phrases and (len(phrases[-1]) < 22 or len(p) < 14) and len(phrases[-1]) + len(p) < 70:
                phrases[-1] += " " + p
            else:
                phrases.append(p)
        final = []
        for p in phrases:
            if len(p) > 74:
                ws = p.split()
                mid = len(ws) // 2
                final += [" ".join(ws[:mid]), " ".join(ws[mid:])]
            else:
                final.append(p)
        ntext = len(text.split())
        wl = WORDS[key]
        nb = len(wl)
        idx = 0
        for j, p in enumerate(final):
            nw = len(p.split())
            wi = min(nb - 1, round(idx * nb / ntext))
            s = CUE[key] + wl[wi][1] - 0.05
            idx += nw
            if j + 1 < len(final):
                wj = min(nb - 1, round(idx * nb / ntext))
                e = CUE[key] + wl[wj][1] - 0.08
            else:
                e = CUE[key] + wl[-1][1] + wl[-1][2] + 0.35
            out.append((s, e, p))
    return out


def draw_caption(fr, T, chunks, cine):
    for s, e, txt in chunks:
        if s - 0.12 <= T <= e:
            a = min(eout(prog(T, s - 0.12, s + 0.1)), 1 - prog(T, e - 0.12, e))
            if cine:
                spr = text_sprite(txt, 500, 30, (240, 242, 245))
                blit(fr, spr, W / 2 - spr.shape[1] / 2, H - BAR / 2 - spr.shape[0] / 2 + 2, a)
            else:
                spr, pad = pill_sprite(txt, size=30, w=500, fg=(245, 247, 250), bg=(12, 20, 32, 205), padx=22, pady=10, shadow=0)
                blit(fr, spr, W / 2 - spr.shape[1] / 2, H - 58 - (spr.shape[0] - 2 * pad) - pad, a)
            return


# ------------------------------------------------------------------ build timeline

def build():
    global CLICKS, WHOOSH
    # ---------------- ACT 1
    a1 = add("A1 aerial", 5.6, None, "cine")
    a1.fn = stock_scene("45821", 0.5, a1.dur, 1.0, 1.07)
    cue("n01", a1.start + 1.3)
    a2 = add("A2 haul", 4.4, None, "cine", xf=0.4)
    a2.fn = stock_scene("45822", 8.5, a2.dur, 1.02, 1.1)
    cue("n02", a2.start + 0.3)
    a3 = add("A3 helmet", 4.6, None, "cine", xf=0.4)
    a3.fn = stock_scene("45753", 3.0, a3.dur, 1.04, 1.12)
    e3 = cue("n03", a3.start + 0.25)
    a4s = a3.end - 0.5
    c4 = e3 + 0.45
    e4 = c4 + DUR["n04"]
    a4 = add("A4 xrf", e4 + 0.9 - a4s, None, "cine", xf=0.5)
    cue("n04", c4)
    a4.fn = make_xrf_scene(a4.dur, a4.start)
    a5 = add("A5 lab", 3.6, None, "cine", xf=0.5)
    a5.fn = stock_scene("4767", 1.5, a5.dur, 1.02, 1.08)
    e5 = cue("n05", a5.start + 0.3)
    a6 = add("A6 scope", 3.5, None, "cine", xf=0.4)
    a6.fn = stock_scene("47783", 13.0, a6.dur, 1.05, 1.15)
    a7 = add("A7 micrograph", 3.3, None, "cine", xf=0.4)
    a7.fn = micro_scene(a7.dur)
    cue("n06", max(e5 + 0.15, a7.start + 0.15))
    a8 = add("A8 triptych", 8.2, None, "cine", xf=0.45)
    cue("n07", a8.start + 0.35)
    a8.fn = triptych_scene(a8.dur, a8.start)
    a9 = add("A9 title+laptop", 8.6, None, "cine", xf=0.45)
    cue("n08", a9.start + 0.35)
    a9.fn = laptop_title_scene(a9.dur, a9.start)
    WHOOSH.append(a9.start + 0.2)
    WHOOSH.append(a9.end - 0.6)

    # ---------------- ACT 2 (UI)
    b1 = add("B1 dashboard", 13.4, None, "ui", xf=0.5)
    cue("n09", b1.start + 0.4)
    L = lambda k, w, n=1: wt(k, w, n) - b1.start
    b1.fn = ui_scene(
        b1.dur, [(0, "d01_dashboard_real")],
        cam=[(0, 960, 540, 1.0), (L("n09", "held") - 0.4, 960, 540, 1.0), (L("n09", "held") + 0.8, 450, 640, 1.45), (b1.dur, 470, 640, 1.5)],
        chip=(0.5, "THE WORKBENCH", "Dashboard"),
        callouts=[(L("n09", "library") - 0.2, L("n09", "held") - 0.5, "Specimen library", 196, 292, 120, -70),
                  (L("n09", "readiness") - 0.2, L("n09", "held") - 0.5, "Model readiness", 1405, 590, -150, 90),
                  (L("n09", "evidence") - 0.2, L("n09", "held") - 0.5, "Recorded evidence", 1408, 362, -150, -90),
                  (L("n09", "held") + 0.7, b1.dur, "12 held-out sections · public LumenStone S2", 300, 470, 260, -60)],
        boxes=[(L("n09", "held") + 0.7, b1.dur, 108, 432, 600, 862)])

    b2 = add("B2 run", 15.2, None, "ui", xf=0.45)
    cue("n10", b2.start + 0.3)
    L = lambda k, w, n=1: wt(k, w, n) - b2.start
    tclick = 1.35
    CLICKS.append(b2.start + tclick)
    b2.fn = ui_scene(
        b2.dur, [(0, "d02_ws_before"), (1.55, "SEQ"), (11.4, "d03_ws_after")],
        seq=(1.55, 11.4, 0, 118),
        cam=[(0, 960, 540, 1.0), (1.6, 960, 540, 1.0), (2.6, 1080, 648, 1.25), (11.6, 1080, 648, 1.25), (13.0, 1180, 640, 1.25)],
        chip=(0.4, "STEP 1", "Run the analysis"),
        cursor=[(0.2, 1150, 620), (1.2, 1440, 364), (1.9, 1440, 364)],
        clicks=[tclick],
        badge=(2.0, 11.6, "REAL RUN  ·  LAPTOP CPU  ·  TIME-LAPSE, ABOUT 10X"),
        boxes=[(12.0, b2.dur, 1553, 975, 1805, 1000)],
        callouts=[(12.2, b2.dur, "Runtime 98.2 s, measured by the app", 1553, 988, -120, -150)])

    b3 = add("B3 phases", 10.0, None, "ui", xf=0.45)
    cue("n11", b3.start + 0.2)
    L = lambda k, w, n=1: wt(k, w, n) - b3.start
    t_py, t_pe, t_ch = L("n11", "Pyrrhotite"), L("n11", "pentlandite"), L("n11", "chalcopyrite")
    CLICKS += [b3.start + 0.9, b3.start + 3.2, b3.start + 4.6]
    b3.fn = ui_scene(
        b3.dur, [(0, "d04_view_Original"), (1.0, "d04_view_Phase_overlay"), (3.3, "d04_view_Phase_mask"), (4.7, "d04_view_Phase_overlay")],
        cam=[(0, 1000, 600, 1.15), (5.0, 1000, 600, 1.15), (6.2, 1180, 560, 1.18), (b3.dur, 1200, 560, 1.18)],
        chip=(0.3, "DELIVERABLE 1", "Mineral phases"),
        cursor=[(0.1, 600, 600), (0.85, 474, 429), (1.4, 474, 429), (3.1, 568, 429), (3.6, 568, 429), (4.5, 474, 429), (5.0, 474, 429)],
        clicks=[0.9, 3.2, 4.6],
        boxes=[(t_py - 0.1, b3.dur, 1550, 568, 1808, 612), (t_pe - 0.1, b3.dur, 1550, 631, 1808, 675), (t_ch - 0.1, b3.dur, 1550, 442, 1808, 486)],
        callouts=[(L("n11", "fraction") - 0.2, b3.dur, "Image-area fraction, not ore grade", 1555, 706, -170, 60)])

    b4 = add("B4 provenance", 9.6, None, "ui", xf=0.45)
    cue("n12", b4.start + 0.2)
    L = lambda k, w, n=1: wt(k, w, n) - b4.start
    reg = (1540, 728, 1820, 1046)
    b4.fn = ui_scene(
        b4.dur, [(0, "d03_ws_after")],
        cam=[(0, 1200, 560, 1.18), (b4.dur, 1260, 600, 1.22)],
        chip=(0.3, "TRUST", "Provenance on every result"),
        popouts=[(0.5, b4.dur, "d03_ws_after", reg, 1.9, (860, 600),
                  [(L("n12", "model"), b4.dur, 1550, 900, 1810, 922), (L("n12", "checkpoint"), b4.dur, 1550, 926, 1810, 948),
                   (L("n12", "runtime"), b4.dur, 1550, 977, 1810, 999), (L("n12", "uncalibrated") - 0.2, b4.dur, 1556, 795, 1800, 830)])])

    b5 = add("B5 grains", 11.0, None, "ui", xf=0.45)
    cue("n13", b5.start + 0.2)
    L = lambda k, w, n=1: wt(k, w, n) - b5.start
    t_lk = L("n13", "locked")
    b5.fn = ui_scene(
        b5.dur, [(0, "d05_grain4_top"), (t_lk - 0.3, "d06_xrf_validation")],
        cam=[(0, 1180, 640, 1.3), (t_lk - 0.35, 1180, 660, 1.3), (t_lk - 0.3, 1050, 360, 1.3), (b5.dur, 1050, 380, 1.3)],
        chip=(0.3, "LIBERATION", "Explore individual grains"),
        boxes=[(L("n13", "size") - 0.1, t_lk - 0.4, 755, 760, 885, 953), (L("n13", "size") - 0.1, t_lk - 0.4, 1556, 770, 1812, 815),
               (L("n13", "composition") - 0.1, t_lk - 0.4, 1556, 818, 1812, 840), (L("n13", "free") - 0.1, t_lk - 0.4, 1736, 842, 1792, 868),
               (t_lk, b5.dur, 1300, 268, 1372, 472)],
        callouts=[(L("n13", "free") + 0.1, t_lk - 0.4, "Grain 4 · 89.2% valuable mineral · FREE", 1736, 855, -560, -150),
                  (t_lk + 0.2, b5.dur, "Locked grains: value trapped in rock", 1300, 300, -420, -70)])

    b6 = add("B6 assay", 9.9, None, "ui", xf=0.45)
    cue("n14", b6.start + 0.2)
    L = lambda k, w, n=1: wt(k, w, n) - b6.start
    reg = (1538, 814, 1822, 1066)
    b6.fn = ui_scene(
        b6.dur, [(0, "d06_xrf_validation")],
        cam=[(0, 1050, 380, 1.3), (1.0, 1300, 700, 1.15), (b6.dur, 1320, 720, 1.18)],
        chip=(0.3, "CHEMISTRY", "XRF or lab assay alongside"),
        popouts=[(1.0, b6.dur, "d06_xrf_validation", reg, 2.3, (960, 560),
                  [(L("n14", "Attach") + 0.6, b6.dur, 1552, 968, 1680, 992), (L("n14", "measures") - 0.3, b6.dur, 1552, 1020, 1795, 1056)])])

    b7 = add("B7 report", 16.8, None, "ui", xf=0.45)
    cue("n15", b7.start + 0.3)
    L = lambda k, w, n=1: wt(k, w, n) - b7.start
    t_tw, t_mg = L("n15", "twelve"), L("n15", "Magnetite")
    t_says = L("n15", "report", 2)
    b7.fn = ui_scene(
        b7.dur, [(0, "d08_reports")],
        cam=[(0, 960, 540, 1.0), (t_tw - 0.3, 960, 540, 1.0), (t_tw + 0.7, 700, 640, 1.4), (t_mg - 0.2, 760, 640, 1.4), (t_mg + 0.8, 1000, 648, 1.25), (b7.dur, 1000, 648, 1.25)],
        chip=(0.3, "DELIVERABLE 2", "Accuracy report"),
        boxes=[(L("n15", "checkpoint") - 0.1, t_tw, 270, 484, 736, 500),
               (L("n15", "mean"), b7.dur, 112, 670, 212, 742), (L("n15", "pixel"), b7.dur, 270, 670, 368, 742),
               (t_mg, b7.dur, 444, 688, 1182, 706), (t_says - 0.1, b7.dur, 122, 974, 1798, 1012)],
        callouts=[(t_says, b7.dur, "Magnetite: not detected, and shown", 700, 993, 260, -80)])

    b8 = add("B8 candidate", 13.6, None, "ui", xf=0.45)
    cue("n16", b8.start + 0.2)
    L = lambda k, w, n=1: wt(k, w, n) - b8.start
    b8.fn = ui_scene(
        b8.dur, [(0, "d09_candidate")],
        cam=[(0, 960, 420, 1.25), (b8.dur, 1000, 400, 1.28)],
        chip=(0.3, "WHAT'S NEXT", "Retrained candidate"),
        boxes=[(L("n16", "0.632") - 0.1, b8.dur, 1468, 86, 1552, 132), (L("n16", "magnetite") - 0.1, b8.dur, 122, 498, 1798, 533),
               (L("n16", "false") - 0.1, b8.dur, 122, 168, 1798, 258), (L("n16", "quarantined") - 0.2, b8.dur, 1674, 2, 1803, 20)],
        callouts=[(L("n16", "quarantined"), b8.dur, "Candidate not deployed", 1674, 12, -140, 70)])

    b9 = add("B9 advisory", 14.3, None, "ui", xf=0.45)
    cue("n17", b9.start + 0.3)
    L = lambda k, w, n=1: wt(k, w, n) - b9.start
    reg = (655, 585, 1255, 692)
    b9.fn = ui_scene(
        b9.dur, [(0, "d10_process")],
        cam=[(0, 960, 540, 1.0), (1.6, 960, 600, 1.2), (b9.dur, 980, 610, 1.22)],
        chip=(0.3, "DELIVERABLE 3", "From mineralogy to a plant parameter"),
        boxes=[(L("n17", "mineralogy"), L("n17", "advisory") + 0.2, 112, 560, 625, 662), (L("n17", "advisory"), L("n17", "forty") - 0.3, 662, 590, 840, 610)],
        popouts=[(L("n17", "forty") - 0.2, b9.dur, "d10_process", reg, 2.6, (960, 560),
                  [(L("n17", "verify") - 0.1, b9.dur, 662, 590, 840, 610), (L("n17", "forty"), b9.dur, 662, 616, 1250, 634)])])

    b10 = add("B10 simulator", 12.6, None, "ui", xf=0.45)
    cue("n18", b10.start + 0.2)
    L = lambda k, w, n=1: wt(k, w, n) - b10.start
    tc = L("n18", "simulator") - 0.2
    CLICKS.append(b10.start + tc)
    t_held = L("n18", "held")
    b10.fn = ui_scene(
        b10.dur, [(0, "d10_process"), (tc + 0.5, "d11_process_sim")],
        cam=[(0, 980, 610, 1.22), (tc - 0.6, 1280, 640, 1.45), (b10.dur, 1300, 645, 1.5)],
        chip=(0.3, "SIMULATOR", "Test the setpoint"),
        cursor=[(0.2, 1100, 760), (tc - 0.1, 1383, 652), (tc + 0.8, 1383, 652)],
        clicks=[tc],
        boxes=[(tc + 0.8, b10.dur, 1756, 594, 1806, 614), (L("n18", "approved") - 0.2, b10.dur, 1306, 683, 1612, 701),
               (t_held - 0.1, b10.dur, 1306, 707, 1348, 730)],
        callouts=[(t_held + 0.1, b10.dur, "Not approved for control, so the setting is held", 1310, 718, -40, 110)])

    b11 = add("B11 export", 7.3, None, "ui", xf=0.45)
    cue("n19", b11.start + 0.2)
    L = lambda k, w, n=1: wt(k, w, n) - b11.start
    tc = L("n19", "record") - 0.1
    CLICKS.append(b11.start + tc)
    b11.fn = ui_scene(
        b11.dur, [(0, "d11_process_sim")],
        cam=[(0, 1300, 645, 1.5), (1.2, 1150, 740, 1.3), (b11.dur, 1160, 745, 1.32)],
        chip=(0.3, "AUDIT TRAIL", "Every decision, exported"),
        cursor=[(0.6, 1300, 900), (tc - 0.05, 1704, 805), (tc + 0.9, 1704, 805)],
        clicks=[tc],
        boxes=[(L("n19", "result"), b11.dur, 112, 772, 668, 836)])

    b12 = add("B12 spatial", 9.0, None, "ui", xf=0.45)
    cue("n20", b12.start + 0.2)
    L = lambda k, w, n=1: wt(k, w, n) - b12.start
    t_pl, t_se, t_3d = L("n20", "plan"), L("n20", "sections"), L("n20", "3D")
    CLICKS += [b12.start + t_pl - 0.25, b12.start + t_se - 0.25, b12.start + t_3d - 0.25]
    b12.fn = ui_scene(
        b12.dur, [(0, "d15_spatial_3D_model2"), (t_pl - 0.1, "d15_spatial_Plan_map"), (t_se - 0.1, "d15_spatial_EW_section"), (t_3d - 0.1, "d15_spatial_3D_model2")],
        cam=[(0, 960, 600, 1.12), (b12.dur, 940, 620, 1.18)],
        chip=(0.3, "GEOLOGY", "Spatial context"),
        cursor=[(t_pl - 0.9, 700, 500), (t_pl - 0.3, 468, 345), (t_se - 0.3, 572, 345), (t_3d - 0.3, 370, 345), (t_3d + 0.6, 370, 345)],
        clicks=[t_pl - 0.25, t_se - 0.25, t_3d - 0.25],
        boxes=[(L("n20", "synthetic") - 0.1, b12.dur, 322, 391, 522, 411)],
        callouts=[(L("n20", "synthetic", 2) - 0.2, b12.dur, "Synthetic geometry, labelled as synthetic", 522, 401, 140, 40)])

    b13 = add("B13 assistant", 8.8, None, "ui", xf=0.45)
    cue("n21", b13.start + 0.2)
    L = lambda k, w, n=1: wt(k, w, n) - b13.start
    tc = 1.7
    CLICKS.append(b13.start + tc)
    b13.fn = ui_scene(
        b13.dur, [(0, "d17_assistant_open"), (tc + 0.4, "d18_assistant_answer")],
        cam=[(0, 1400, 560, 1.2), (tc + 0.6, 1500, 620, 1.35), (b13.dur, 1510, 700, 1.4)],
        chip=(0.3, "EVIDENCE COMPANION", "Ask the evidence"),
        cursor=[(0.4, 1300, 700), (tc - 0.1, 1580, 470), (tc + 0.7, 1580, 470)],
        clicks=[tc],
        boxes=[(L("n21", "measured"), b13.dur, 1516, 931, 1586, 953), (L("n21", "predicted"), b13.dur, 1516, 886, 1584, 908),
               (L("n21", "simulated"), b13.dur, 1516, 992, 1586, 1014)])

    b14 = add("B14 phone", 4.4, None, "cine", xf=0.45)
    cue("n22", b14.start + 0.35)
    b14.fn = phone_scene(b14.dur)

    # ---------------- ACT 3
    c1 = add("C1 montage", 10.4, None, "cine", xf=0.5)
    cue("n23", c1.start + 0.4)
    c1.fn = montage_scene(c1.dur, c1.start)
    WHOOSH.append(c1.start)
    c2 = add("C2 end", 6.2, None, "card", xf=0.6)
    cue("n24", c2.start + 0.6)
    c2.fn = end_card(c2.dur, c2.start)
    c3 = add("C3 disclose", 8.0, None, "card", xf=0.6)
    c3.fn = disclose_card(c3.dur)
    return SC[-1].end


def build90():
    """90-second cut for the deck's demo slot: same footage, tighter narration."""
    global CLICKS, WHOOSH
    a1 = add("A1 aerial", 8.6, None, "cine")
    a1.fn = stock_scene("45821", 0.3, a1.dur, 1.0, 1.1)
    e1 = cue("n01", a1.start + 1.0)
    cue("n02", e1 + 0.45)
    a5 = add("A5 lab", 4.1, None, "cine", xf=0.45)
    a5.fn = stock_scene("4767", 1.5, a5.dur, 1.02, 1.08)
    e5 = cue("n05", a5.start + 0.25)
    a7 = add("A7 micrograph", e5 + 0.2 + DUR["n06"] + 0.5 - (a5.end - 0.4), None, "cine", xf=0.4)
    a7.fn = micro_scene(a7.dur)
    cue("n06", e5 + 0.2)
    a9 = add("A9 title+laptop", 8.4, None, "cine", xf=0.45)
    cue("n08", a9.start + 0.35)
    a9.fn = laptop_title_scene(a9.dur, a9.start)
    WHOOSH.append(a9.start + 0.2)
    WHOOSH.append(a9.end - 0.6)

    b2 = add("B2 run", 13.0, None, "ui", xf=0.5)
    cue("n10s", b2.start + 0.3)
    tclick = 1.3
    CLICKS.append(b2.start + tclick)
    b2.fn = ui_scene(
        b2.dur, [(0, "d02_ws_before"), (1.5, "SEQ"), (9.6, "d03_ws_after")],
        seq=(1.5, 9.6, 0, 118),
        cam=[(0, 960, 540, 1.0), (1.5, 960, 540, 1.0), (2.4, 1080, 648, 1.25), (9.8, 1080, 648, 1.25), (11.2, 1180, 640, 1.25)],
        chip=(0.4, "STEP 1", "Run the analysis"),
        cursor=[(0.2, 1150, 620), (1.15, 1440, 364), (1.8, 1440, 364)],
        clicks=[tclick],
        badge=(1.9, 9.8, "REAL RUN  ·  LAPTOP CPU  ·  TIME-LAPSE, ABOUT 12X"),
        boxes=[(10.2, b2.dur, 1553, 975, 1805, 1000)],
        callouts=[(10.4, b2.dur, "Runtime 98.2 s, measured by the app", 1553, 988, -120, -150)])

    b3 = add("B3 phases", 10.0, None, "ui", xf=0.45)
    cue("n11", b3.start + 0.2)
    L = lambda k, w, n=1: wt(k, w, n) - b3.start
    t_py, t_pe, t_ch = L("n11", "Pyrrhotite"), L("n11", "pentlandite"), L("n11", "chalcopyrite")
    CLICKS.extend([b3.start + 0.9, b3.start + 3.2, b3.start + 4.6])
    b3.fn = ui_scene(
        b3.dur, [(0, "d04_view_Original"), (1.0, "d04_view_Phase_overlay"), (3.3, "d04_view_Phase_mask"), (4.7, "d04_view_Phase_overlay")],
        cam=[(0, 1000, 600, 1.15), (5.0, 1000, 600, 1.15), (6.2, 1180, 560, 1.18), (b3.dur, 1200, 560, 1.18)],
        chip=(0.3, "DELIVERABLE 1", "Mineral phases"),
        cursor=[(0.1, 600, 600), (0.85, 474, 429), (1.4, 474, 429), (3.1, 568, 429), (3.6, 568, 429), (4.5, 474, 429), (5.0, 474, 429)],
        clicks=[0.9, 3.2, 4.6],
        boxes=[(t_py - 0.1, b3.dur, 1550, 568, 1808, 612), (t_pe - 0.1, b3.dur, 1550, 631, 1808, 675), (t_ch - 0.1, b3.dur, 1550, 442, 1808, 486)],
        callouts=[(L("n11", "fraction") - 0.2, b3.dur, "Image-area fraction, not ore grade", 1555, 706, -170, 60)])

    b7 = add("B7 report", 12.2, None, "ui", xf=0.45)
    cue("n15s", b7.start + 0.3)
    L = lambda k, w, n=1: wt(k, w, n) - b7.start
    t_mg = L("n15s", "Magnetite")
    t_says = L("n15s", "report", 2)
    b7.fn = ui_scene(
        b7.dur, [(0, "d08_reports")],
        cam=[(0, 960, 540, 1.0), (L("n15s", "Mean") - 0.4, 960, 540, 1.0), (L("n15s", "Mean") + 0.6, 700, 640, 1.4), (t_mg - 0.2, 760, 640, 1.4), (t_mg + 0.8, 1000, 648, 1.25), (b7.dur, 1000, 648, 1.25)],
        chip=(0.3, "DELIVERABLE 2", "Accuracy report"),
        boxes=[(L("n15s", "Mean") + 0.3, b7.dur, 112, 670, 212, 742), (L("n15s", "twelve"), b7.dur, 270, 670, 368, 742),
               (t_mg, b7.dur, 444, 688, 1182, 706), (t_says - 0.1, b7.dur, 122, 974, 1798, 1012)],
        callouts=[(t_says, b7.dur, "Magnetite: not detected, and shown", 700, 993, 260, -80)])

    b10 = add("B10 simulator", 11.8, None, "ui", xf=0.45)
    cue("n18s", b10.start + 0.2)
    L = lambda k, w, n=1: wt(k, w, n) - b10.start
    tc = L("n18s", "This") - 0.3
    CLICKS.append(b10.start + tc)
    t_held = L("n18s", "holds")
    b10.fn = ui_scene(
        b10.dur, [(0, "d10_process"), (tc + 0.5, "d11_process_sim")],
        cam=[(0, 960, 600, 1.15), (tc - 0.6, 1280, 640, 1.45), (b10.dur, 1300, 645, 1.5)],
        chip=(0.3, "DELIVERABLE 3", "Test a plant parameter"),
        cursor=[(0.3, 1100, 760), (tc - 0.1, 1383, 652), (tc + 0.8, 1383, 652)],
        clicks=[tc],
        boxes=[(tc + 0.8, b10.dur, 1756, 594, 1806, 614), (L("n18s", "approved") - 0.2, b10.dur, 1306, 683, 1612, 701),
               (t_held - 0.1, b10.dur, 1306, 707, 1348, 730)],
        callouts=[(t_held + 0.1, b10.dur, "Not approved for control, so the setting is held", 1310, 718, -40, 110)])

    c1 = add("C1 montage", 10.4, None, "cine", xf=0.5)
    cue("n23", c1.start + 0.4)
    c1.fn = montage_scene(c1.dur, c1.start)
    WHOOSH.append(c1.start)
    c2 = add("C2 end", 5.4, None, "card", xf=0.6)
    cue("n24", c2.start + 0.5)
    c2.fn = end_card(c2.dur, c2.start)
    c3 = add("C3 disclose", 6.6, None, "card", xf=0.6)
    c3.fn = disclose_card(c3.dur)
    return SC[-1].end


def frame_at(T, fi, chunks):
    active = [s for s in SC if s.start <= T < s.end]
    if not active:
        return np.zeros((H, W, 3), np.uint8)
    frames = []
    for s in active:
        frames.append((s, s.fn(T - s.start, fi)))
    if len(frames) == 1:
        fr = frames[0][1]
        kind = frames[0][0].kind
    else:
        (sa, fa), (sb, fb) = frames[0], frames[-1]
        p = eio((T - sb.start) / max(sb.xf, 1e-3))
        fr = cv2.addWeighted(fb, p, fa, 1 - p, 0)
        kind = sb.kind if p > 0.5 else sa.kind
    if T < 0.9:
        fr = (fr.astype(np.float32) * eio(T / 0.9)).astype(np.uint8)
    if CAPTIONS:
        draw_caption(fr, T, chunks, kind in ("cine", "card"))
    return fr


def main():
    CUT = "--cut90" in sys.argv
    total = build90() if CUT else build()
    chunks = caption_chunks()
    os.makedirs(os.path.join(S, "out"), exist_ok=True)
    tl = {"total": total, "scenes": [(s.name, round(s.start, 3), round(s.dur, 3), s.kind) for s in SC],
          "cues": CUE, "clicks": CLICKS, "whoosh": WHOOSH,
          "act2": [s.start for s in SC if s.name.startswith("B")][0],
          "act3": [s.start for s in SC if s.name.startswith("C1")][0],
          "hit": [s.start for s in SC if s.name.startswith("C2")][0],
          "captions": chunks}
    json.dump(tl, open(os.path.join(S, "out", "timeline90.json" if CUT else "timeline.json"), "w"), indent=1)
    print("total", round(total, 2))
    for s in SC:
        print(f"{s.name:18s} {s.start:7.2f} {s.dur:6.2f}")
    if MODE == "preview":
        os.makedirs(os.path.join(S, "preview"), exist_ok=True)
        for a in sys.argv[2:]:
            if a.startswith("--"):
                continue
            T = float(a)
            fr = frame_at(T, int(T * FPS), chunks)
            Image.fromarray(fr).save(os.path.join(S, "preview", f"f_{T:07.2f}.jpg"), quality=88)
            print("wrote", T)
        return
    def arg(name, default):
        return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default
    out = os.path.join(S, "out", arg("--out", "video_nocap.mp4" if not CAPTIONS else "video.mp4"))
    f_from = int(round(float(arg("--from", 0)) * FPS))
    f_to = arg("--to", None)
    enc = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
                            "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    n = int(math.ceil(total * FPS))
    if f_to is not None:
        n = min(n, int(round(float(f_to) * FPS)))
    import time
    t0 = time.time()
    for fi in range(f_from, n):
        T = fi / FPS
        fr = frame_at(T, fi, chunks)
        enc.stdin.write(np.ascontiguousarray(fr).tobytes())
        for s in SC:
            if s.end < T - 1:
                for st in getattr(s.fn, "stocks", []):
                    st.close()
        if fi % 150 == 0:
            el = time.time() - t0
            print(f"frame {fi}/{n}  T={T:.1f}s  {el:.0f}s elapsed  eta {el / max(fi, 1) * (n - fi):.0f}s", flush=True)
    enc.stdin.close()
    enc.wait()
    print("done", out)


if __name__ == "__main__":
    main()
