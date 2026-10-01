"""Build the soundtrack from out/timeline.json: narration + original music + UI clicks/whooshes, with ducking.

python mix.py            -> out/audio.wav
"""
import json, os, subprocess, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

S = os.path.dirname(os.path.abspath(__file__))
SR = 48000
VODIR = os.path.join(S, "vo", "en-ZA-LukeNeural")
TLN = sys.argv[1] if len(sys.argv) > 1 else "timeline.json"
OUTN = sys.argv[2] if len(sys.argv) > 2 else "audio.wav"
tl = json.load(open(os.path.join(S, "out", TLN)))
total = tl["total"] + 0.5
N = int(total * SR)

# ---- music
mpath = os.path.join(S, "out", "music_" + OUTN)
subprocess.run([sys.executable, os.path.join(S, "make_music.py"), mpath, f"{total:.2f}",
                f"{tl['act2']:.2f}", f"{tl['act3']:.2f}", f"{tl['hit']:.2f}"], check=True)
sr, mus = wavfile.read(mpath)
mus = mus.astype(np.float32) / 32768.0
mus = mus[:N] if len(mus) >= N else np.pad(mus, ((0, N - len(mus)), (0, 0)))

# ---- narration (mono)
vo = np.zeros(N, np.float32)
for key, t in tl["cues"].items():
    sr, x = wavfile.read(os.path.join(VODIR, key + ".wav"))
    x = x.astype(np.float32) / 32768.0
    if x.ndim > 1:
        x = x.mean(axis=1)
    s0 = int(t * SR)
    s1 = min(N, s0 + len(x))
    vo[s0:s1] += x[:s1 - s0]
# gentle presence lift + normalise narration to ~ -16 dBFS RMS over speech
sos = butter(2, [120, 9000], "band", fs=SR, output="sos")
vo = sosfilt(sos, vo).astype(np.float32)
speech = np.abs(vo) > 0.01
rms = np.sqrt(np.mean(vo[speech] ** 2)) if speech.any() else 0.1
vo *= (10 ** (-16 / 20)) / max(rms, 1e-6)

# ---- ducking envelope from narration
env = np.abs(vo)
win = int(0.25 * SR)
kern = np.ones(win, np.float32) / win
env = np.convolve(env, kern, mode="same")
env = np.clip(env / (np.percentile(env[speech], 60) + 1e-6), 0, 1) if speech.any() else env
# smooth attack/release
smooth = np.zeros_like(env)
a_att, a_rel = np.exp(-1 / (0.05 * SR)), np.exp(-1 / (0.6 * SR))
# vectorised approximation: downsample, IIR in python, upsample
step = 240
e_ds = env[::step]
out = np.zeros_like(e_ds)
prev = 0.0
aa, ar = np.exp(-step / (0.05 * SR)), np.exp(-step / (0.6 * SR))
for i, v in enumerate(e_ds):
    c = aa if v > prev else ar
    prev = c * prev + (1 - c) * v
    out[i] = prev
smooth = np.interp(np.arange(N), np.arange(len(out)) * step, out).astype(np.float32)
duck = 1.0 - 0.62 * smooth
music_gain = 10 ** (-13 / 20)
mus = mus * (music_gain * duck)[:, None]

# ---- sfx
rng = np.random.default_rng(11)
sfx = np.zeros(N, np.float32)


def lp(x, fc):
    return sosfilt(butter(2, fc, "low", fs=SR, output="sos"), x)


def hpf(x, fc):
    return sosfilt(butter(2, fc, "high", fs=SR, output="sos"), x)


for t in tl["clicks"]:
    s0 = int(t * SR)
    n = int(0.06 * SR)
    tt = np.arange(n) / SR
    click = (np.sin(2 * np.pi * 2400 * tt) * 0.5 + hpf(rng.standard_normal(n), 2000) * 0.5) * np.exp(-tt * 90)
    s1 = min(N, s0 + n)
    sfx[s0:s1] += click[:s1 - s0] * 0.10
for t in tl["whoosh"]:
    n = int(1.1 * SR)
    s0 = int((t - 0.55) * SR)
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    segs = 20
    for j in range(segs):
        a, b = j * n // segs, (j + 1) * n // segs
        ph = j / segs
        fc = 400 + 5000 * np.sin(np.pi * ph)
        out[a:b] = lp(noise[a:b], fc)
    out *= np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    s0 = max(0, s0)
    s1 = min(N, s0 + n)
    sfx[s0:s1] += out[:s1 - s0].astype(np.float32) * 0.06

mix = mus + (vo + sfx)[:, None]
# fade in/out
fi = int(0.6 * SR)
mix[:fi] *= np.linspace(0, 1, fi)[:, None]
fo = int(1.5 * SR)
mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
peak = np.max(np.abs(mix))
if peak > 0.97:
    mix *= 0.97 / peak
wavfile.write(os.path.join(S, "out", OUTN), SR, (mix * 32767).astype(np.int16))
print("audio", total, "s  peak", float(peak))
