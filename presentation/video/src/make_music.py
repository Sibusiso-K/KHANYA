"""Original cinematic underscore, synthesised from scratch (no samples, no licence questions).

usage: python make_music.py OUT.wav TOTAL_SECONDS ACT2_START ACT3_START LOGO_HIT
"""
import sys
import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile

SR = 48000
out, total, a2, a3, hit = sys.argv[1], *map(float, sys.argv[2:6])
N = int(total * SR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "low", fs=SR, output="sos"), x)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x)


def saw(f, tt, phase=0.0):
    return 2 * ((f * tt + phase) % 1.0) - 1


def env_adsr(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    na, nr = min(na, n // 2), min(nr, n // 2)
    e[:na] = np.linspace(0, 1, na) ** 2
    e[n - nr:] *= np.linspace(1, 0, nr) ** 2
    return e


# A-minor-ish progression: Am, F, C, G (voicings as MIDI)
CHORDS = [[57, 60, 64, 69], [53, 57, 60, 65], [55, 60, 64, 67], [55, 59, 62, 67]]
ROOTS = [45, 41, 48, 43]
BPM = 96
beat = 60 / BPM
bar = 4 * beat
chord_len = 2 * bar  # 5 s

mix = np.zeros(N)

# ---- pad (whole piece), brighter in act 2 ----
pad = np.zeros(N)
k = 0
start = 0.0
while start < total:
    s0, s1 = int(start * SR), min(N, int((start + chord_len + 1.5) * SR))
    seg_t = t[s0:s1] - start
    seg = np.zeros(s1 - s0)
    for m in CHORDS[k % 4]:
        for det in (-0.07, 0.0, 0.07):
            seg += saw(midi(m) * (1 + det / 100 * 12), seg_t, rng.random()) * 0.05
    seg *= env_adsr(len(seg), 1.6, 1.8)
    pad[s0:s1] += seg
    start += chord_len
    k += 1
cut = np.where(t < a2, 700 + 600 * (t / max(a2, 1)), 1800)
pad = 0.6 * lp(pad, 900) + 0.4 * lp(pad, 2200)
pad *= np.interp(t, [0, 6, a2 - 2, a2 + 2, a3, total - 4, total], [0, 0.55, 0.6, 0.75, 0.8, 0.9, 0])
mix += pad * 0.55

# ---- low drone act 1 ----
drone = np.sin(2 * np.pi * midi(33) * t) * 0.5 + np.sin(2 * np.pi * midi(45) * t) * 0.2
drone *= np.interp(t, [0, 4, a2 - 1, a2 + 3, total], [0, 0.6, 0.7, 0.25, 0.2])
mix += drone * 0.35

# ---- pulse bass on eighths, from act 2 ----
bass = np.zeros(N)
step = beat / 2
n_steps = int(total / step)
for i in range(n_steps):
    st = i * step
    if st < a2 - 4 * beat or st > total - 3:
        continue
    ci = int(st // chord_len) % 4
    f = midi(ROOTS[ci])
    s0 = int(st * SR)
    ln = int(step * SR * 0.95)
    s1 = min(N, s0 + ln)
    tt = np.arange(s1 - s0) / SR
    e = np.exp(-tt * 9)
    bass[s0:s1] += (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt)) * e
bass = lp(bass, 400)
bass *= np.interp(t, [0, a2 - 2, a2 + 2, a3, total - 4, total], [0, 0, 0.8, 0.9, 1, 0])
mix += bass * 0.30

# ---- soft kick on beats + sidechain, act 2 onward ----
kick = np.zeros(N)
side = np.ones(N)
for i in range(int(total / beat)):
    st = i * beat
    if st < a2 or st > total - 3:
        continue
    s0 = int(st * SR)
    ln = int(0.35 * SR)
    s1 = min(N, s0 + ln)
    tt = np.arange(s1 - s0) / SR
    f = 50 + 70 * np.exp(-tt * 30)
    kick[s0:s1] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 10)
    dl = min(N, s0 + int(0.25 * SR))
    side[s0:dl] = np.minimum(side[s0:dl], 0.45 + 0.55 * np.linspace(0, 1, dl - s0) ** 0.7)
kick *= np.interp(t, [0, a2, a2 + 4, total], [0, 0, 1, 1])
mix = mix * side + kick * 0.22

# ---- arpeggio plucks, act 2 ----
arp = np.zeros(N)
sixteenth = beat / 4
pattern = [0, 2, 1, 3, 2, 1, 3, 2]
for i in range(int(total / sixteenth)):
    st = i * sixteenth
    if st < a2 + 2 * bar or st > total - 4:
        continue
    ci = int(st // chord_len) % 4
    m = CHORDS[ci][pattern[i % 8]] + 12
    s0 = int(st * SR)
    s1 = min(N, s0 + int(0.4 * SR))
    tt = np.arange(s1 - s0) / SR
    tone = np.sin(2 * np.pi * midi(m) * tt) + 0.25 * np.sin(2 * np.pi * 2 * midi(m) * tt)
    arp[s0:s1] += tone * np.exp(-tt * 14) * (0.7 if i % 4 else 1.0)
arp = lp(arp, 4000)
arp *= np.interp(t, [0, a2 + 2 * bar, a2 + 4 * bar, a3, total - 5, total], [0, 0, 0.6, 0.8, 0.8, 0])
mix += arp * 0.07

# ---- riser into act 2 and act 3, impact at logo ----
def riser(end_s, dur):
    s0, s1 = int((end_s - dur) * SR), int(end_s * SR)
    s0 = max(0, s0)
    n = s1 - s0
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    segs = 24
    for j in range(segs):
        a, b = j * n // segs, (j + 1) * n // segs
        fc = 300 + (6000 - 300) * (j / segs) ** 2
        out[a:b] = lp(noise[a:b], fc)
    out *= np.linspace(0, 1, n) ** 2.5
    return s0, s1, out


for end_s, dur, g in [(a2, 3.0, 0.10), (a3, 3.0, 0.08), (hit, 2.5, 0.10)]:
    s0, s1, r = riser(end_s, dur)
    mix[s0:s1] += r * g

s0 = int(hit * SR)
ln = int(3.5 * SR)
s1 = min(N, s0 + ln)
tt = np.arange(s1 - s0) / SR
boom = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-tt * 6)) / SR) * np.exp(-tt * 1.6)
boom += lp(rng.standard_normal(s1 - s0), 900) * np.exp(-tt * 5) * 0.4
mix[s0:s1] += boom * 0.5

# master: gentle high-pass, soft clip, normalise to -16 dBFS RMS-ish peak control
mix = hp(mix, 30)
mix = np.tanh(mix * 1.2) / 1.2
mix /= np.max(np.abs(mix)) + 1e-9
mix *= 0.8
stereo = np.stack([mix, np.roll(mix, int(0.012 * SR)) * 0.96], axis=1)
wavfile.write(out, SR, (stereo * 32767).astype(np.int16))
print("wrote", out, total, "s")
