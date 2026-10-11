"""Render the report's hyperspectral figure from HIDSAG parcel GMET-0004 (REEFPRINT Live showcase data).
Every value comes from GMET-0004.json / GMET-0004.bin.gz on codex/pwa-phase-roadmap (ab33307)."""
import gzip, json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

S = os.path.dirname(os.path.abspath(__file__))
OUT = r"C:\Users\lovilocal.adm\Desktop\Claude Projects\KHANYA-workbench\report\figures\hsi_parcel_gmet0004.pdf"
meta = json.load(open(os.path.join(S, "GMET-0004.json")))
raw = gzip.decompress(open(os.path.join(S, "GMET-0004.bin.gz"), "rb").read())
A = meta["arrays"]

def arr(name):
    a = A[name]
    n = int(np.prod(a["shape"]))
    return np.frombuffer(raw, dtype=np.uint8, count=n, offset=a["offset"]).reshape(a["shape"]).astype(np.float64)

def cube(name):
    c = arr(name)
    lo = np.array(A[name]["band_min"]); hi = np.array(A[name]["band_max"])
    return lo + c / 255.0 * (hi - lo)

def fmap(name):
    lo, hi = A[name]["scale"]
    return lo + arr(name) / 255.0 * (hi - lo)

vn, sw = cube("vnir_low_cube"), cube("swir_low_cube")
wv_v, wv_s = np.array(meta["vnir_low_wavelengths"]), np.array(meta["swir_low_wavelengths"])
dark = arr("vnir_low_dark") > 0
print("vnir", vn.shape, "swir", sw.shape, "dark px", int(dark.sum()))

def band(c, wv, nm):
    return c[..., int(np.argmin(np.abs(wv - nm)))]

def stretch(x, m):
    v = x[~m]
    lo, hi = np.percentile(v, 2), np.percentile(v, 98)
    return np.clip((x - lo) / (hi - lo), 0, 1)

rgb = np.dstack([stretch(band(vn, wv_v, nm), dark) for nm in (650, 560, 470)])
rgb[dark] = 0
aloh, mgoh = fmap("map_swir_aloh"), fmap("map_swir_mgoh")
# the app stores band depth as a negative continuum-removed value; show depth as a positive number
aloh_d, mgoh_d = -aloh, -mgoh

def destripe(m):
    """Display only, as in the app's Destripe option: remove each detector column's offset."""
    m = m.copy(); m[dark] = np.nan
    col = np.nanmedian(m, axis=0)
    return m - col[None, :] + np.nanmedian(m)

aloh_d, mgoh_d = destripe(aloh_d), destripe(mgoh_d)

wi = meta["targets"]["WI"]
print("WI pred %.2f bound %.2f design %.2f true %.1f -> feed %.1f%%" % (
    wi["pred"], wi["hi_up"], wi["p90_train"], wi["true"], 100 * wi["p90_train"] / wi["hi_up"]))

plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"], "mathtext.fontset": "stix", "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8})
fig = plt.figure(figsize=(7.0, 1.95))
gs = fig.add_gridspec(1, 4, width_ratios=[1, 1, 1, 1.35], wspace=0.08)
for i, (img, title, cmap) in enumerate([(rgb, "(a) VNIR colour", None),
                                         (aloh_d, "(b) Al-OH, 2.2 $\\mu$m", "viridis"),
                                         (mgoh_d, "(c) Mg-OH, 2.3 $\\mu$m", "magma")]):
    ax = fig.add_subplot(gs[0, i])
    if cmap is None:
        ax.imshow(img, interpolation="nearest")
    else:
        lo, hi = np.nanpercentile(img, 2), np.nanpercentile(img, 98)
        ax.imshow(img, cmap=cmap, interpolation="nearest", vmin=lo, vmax=hi)
    ax.set_title(title, fontsize=7.5)
    ax.set_xticks([]); ax.set_yticks([])

ax = fig.add_subplot(gs[0, 3])
ax.yaxis.tick_right(); ax.yaxis.set_label_position("right")
mv = vn[~dark].mean(axis=0); ms = sw[~dark].mean(axis=0)
ax.plot(wv_v, mv / mv.max(), color="#1f6fb2", lw=1.1, label="VNIR")
ax.plot(wv_s, ms / ms.max(), color="#b4532a", lw=1.1, label="SWIR")
for lo, hi, lab in ((1350, 2000, "OH/H$_2$O"), (2000, 2250, "Al-OH"), (2250, 2400, "Mg-OH/CO$_3$")):
    ax.axvspan(lo, hi, color="0.5", alpha=0.12 if lab != "Al-OH" else 0.22, lw=0)
    ax.text((lo + hi) / 2, 0.06, lab, ha="center", fontsize=5.8, rotation=90, va="bottom")
ax.set_xlim(400, 2500); ax.set_ylim(0, 1.05)
ax.set_xlabel("Wavelength (nm)"); ax.set_ylabel("Normalised mean signal")
ax.set_title("(d) Parcel mean spectrum", fontsize=7.5)
ax.legend(fontsize=6, frameon=False, loc="lower left", bbox_to_anchor=(0.0, 0.0))
ax.spines[["top", "left"]].set_visible(False)
fig.savefig(OUT, bbox_inches="tight")
fig.savefig(OUT.replace(".pdf", ".png"), dpi=200, bbox_inches="tight")
print("saved", OUT)
