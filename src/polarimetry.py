"""Does Stokes anisotropy separate minerals that reflectance cannot?

    python -m src.polarimetry --inspect    # report S3 v2 rotation-series layout
    python -m src.polarimetry              # run the separation test

This is the KHANYA/REEFPRINT bridge (JOINT-PLAN.md). It imports Lethabo's
`reefprint.polarim.stokes` unchanged - the inversion is his, validated on his
phantom at 40.4x separation - and feeds it real LumenStone S3 v2 XPL rotation
series, with KHANYA's ground-truth masks supplying per-pixel mineral labels.

CORRECTION TO JOINT-PLAN section 3. That document proposed testing whether
polarimetry fixes KHANYA's 29.2% pentlandite -> pyrrhotite confusion. **That
experiment cannot be run.** Pentlandite and pyrrhotite are in S2, which has NO
rotation series; the rotations are in S3, which contains NEITHER mineral. The
pair and the measurement live in different datasets.

What S3 offers instead is a better test, not a consolation. Its eleven classes
split cleanly by crystal symmetry, giving five isotropic and five anisotropic
minerals rather than a single pair - and one of those pairs is **magnetite
(cubic, isotropic) against hematite (trigonal, anisotropic)**, which is exactly
the pair report section 3 claims optical microscopy can separate and SEM/BSE
cannot. That claim is currently asserted. This measures it.

Magnetite is also KHANYA's total segmentation failure (IoU 0.000 on S2,
predicted as background 92.3% of the time), so if anisotropy separates
magnetite from hematite it is doing work no amount of colour-based training
achieved.

THE N2 PROBLEM, and why the threshold is conformal rather than fixed.
REEFPRINT's open finding N2: the anisotropy noise floor scales as 1/S0, so a
truly isotropic phase does not read zero - it reads roughly
`sigma*sqrt(8/n)*sqrt(pi/2)/S0`. A fixed anisotropy threshold is therefore a
reflectance-dependent classifier in disguise, and a rule fitted on bright
sulphides lights up every dark grain. This module never fits a fixed threshold.
It bins by S0 and reports a conformal interval per bin, which is KHANYA's
existing calibration machinery (src/conformal.py) applied to Lethabo's physics.
"""
import argparse
import sys
import zipfile
from pathlib import Path

import numpy as np

from .segmentation import config

# Lethabo's inversion, imported unchanged. Not vendored, not reimplemented - if
# his Stokes code changes, this experiment changes with it, which is the point.
REEFPRINT_SRC = Path.home() / "Desktop" / "REEFPRINT - Copy" / "src"
if str(REEFPRINT_SRC) not in sys.path:
    sys.path.insert(0, str(REEFPRINT_SRC))

# Crystal symmetry governs whether a mineral modulates under analyser rotation.
# Cubic phases are optically isotropic and stay dark; everything else lights up.
# This table is domain input, not a fitted parameter - it is the hypothesis
# under test, so it is stated before any data is touched.
SYMMETRY = {
    "pyrite": "isotropic",          # cubic
    "galena": "isotropic",          # cubic, halite structure
    "sphalerite": "isotropic",      # cubic
    "magnetite": "isotropic",       # cubic spinel
    "tennantite": "isotropic",      # cubic
    "covellite": "anisotropic",     # hexagonal - very strongly anisotropic
    "arsenopyrite": "anisotropic",  # monoclinic - strongly anisotropic
    "hematite": "anisotropic",      # trigonal - distinctly anisotropic
    "chalcopyrite": "anisotropic",  # tetragonal - weakly anisotropic
    "bornite": "anisotropic",       # tetragonal at room temperature - weakly
    "background": "resin",          # not a mineral; excluded from the test
}

# The pair the optical argument in report section 3 rests on: both iron oxides,
# near-identical mean atomic number so BSE cannot split them, opposite symmetry
# so polarimetry should.
HEADLINE_PAIR = ("magnetite", "hematite")

S3V2_ZIP = config.ROOT / "data" / "raw" / "lumenstone" / "S3_v2.zip"
S3V2_DIR = config.ROOT / "data" / "raw" / "lumenstone" / "S3_v2"


def inspect_archive(limit=40):
    """Report the layout of the S3 v2 archive without extracting 5.2 GB.

    The rotation series is the reason for downloading v2 at all, and its
    on-disk convention is undocumented on the LumenStone page, so look before
    committing to a reader.
    """
    if not S3V2_ZIP.exists():
        print(f"not downloaded yet: {S3V2_ZIP}")
        return
    with zipfile.ZipFile(S3V2_ZIP) as archive:
        names = [n for n in archive.namelist() if not n.startswith("__MACOSX")]
    print(f"{len(names)} entries\n")
    tops = sorted({"/".join(n.split("/")[:3]) for n in names if n.count("/") >= 2})
    for top in tops[:limit]:
        count = sum(1 for n in names if n.startswith(top))
        print(f"  {top:60s} {count:5d}")
    keys = ("rot", "xpl", "ang", "deg", "pol")
    rotational = [n for n in names if any(k in n.lower() for k in keys)]
    print(f"\nentries whose path mentions rotation/XPL/angle: {len(rotational)}")
    for name in rotational[:12]:
        print("   ", name)


def noise_floor(sigma, n_angles, s0):
    """REEFPRINT finding N2: the anisotropy a *perfectly isotropic* phase reads.

    sigma*sqrt(8/n)*sqrt(pi/2)/S0 - the floor rises as reflectance falls, which
    is why a fixed threshold silently becomes a brightness classifier.
    """
    return sigma * np.sqrt(8.0 / n_angles) * np.sqrt(np.pi / 2.0) / np.maximum(s0, 1e-9)


def summarise_by_class(anisotropy, s0, labels, class_names, min_pixels=500):
    """Anisotropy distribution per mineral, with the S0 each was measured at.

    Reports median rather than mean: anisotropy is bounded in [0, 1] and its
    per-class distribution is skewed, so a mean is pulled by the tail from grain
    boundaries where two phases share a pixel.
    """
    rows = []
    for index, name in enumerate(class_names):
        if SYMMETRY.get(name) == "resin":
            continue
        mask = labels == index
        count = int(mask.sum())
        if count < min_pixels:
            continue
        values = anisotropy[mask]
        rows.append({
            "mineral": name,
            "symmetry": SYMMETRY.get(name, "unknown"),
            "n_pixels": count,
            "anisotropy_median": float(np.median(values)),
            "anisotropy_p25": float(np.percentile(values, 25)),
            "anisotropy_p75": float(np.percentile(values, 75)),
            "s0_median": float(np.median(s0[mask])),
        })
    return rows


def separation(rows):
    """Isotropic vs anisotropic separation, and the headline oxide pair.

    Reported as a ratio of medians, matching how REEFPRINT states its phantom
    result (40.4x), so the two numbers are directly comparable.
    """
    iso = [r["anisotropy_median"] for r in rows if r["symmetry"] == "isotropic"]
    ani = [r["anisotropy_median"] for r in rows if r["symmetry"] == "anisotropic"]
    out = {}
    if iso and ani:
        out["isotropic_median"] = float(np.median(iso))
        out["anisotropic_median"] = float(np.median(ani))
        out["separation_ratio"] = float(np.median(ani) / max(np.median(iso), 1e-9))
    by_name = {r["mineral"]: r for r in rows}
    first, second = HEADLINE_PAIR
    if first in by_name and second in by_name:
        out["headline_pair"] = {
            first: by_name[first]["anisotropy_median"],
            second: by_name[second]["anisotropy_median"],
            "ratio": float(by_name[second]["anisotropy_median"]
                           / max(by_name[first]["anisotropy_median"], 1e-9)),
        }
    return out


# --- N2: the S0-conditioned conformal threshold -----------------------------
#
# REEFPRINT's open finding N2 states the problem; this is the fix, and it is
# KHANYA's existing conformal machinery pointed at Lethabo's physics.
#
# A fixed anisotropy threshold cannot work because the noise floor rises as
# reflectance falls. Calibrating ONE threshold on bright sulphides guarantees
# false positives on dark gangue. The fix is not a cleverer threshold - it is to
# stop having one number at all: bin by S0, and within each bin take the
# (1-alpha) quantile of anisotropy over pixels KNOWN to be isotropic. That is a
# one-sided conformal bound, so the false-positive rate is <= alpha by
# construction in every bin, whatever the noise floor does.


def conformal_threshold_by_s0(anisotropy, s0, is_isotropic, n_bins=6, alpha=0.10):
    """Per-S0-bin anisotropy thresholds calibrated on known-isotropic pixels.

    Returns one threshold per bin such that at most `alpha` of calibration
    isotropic pixels in that bin exceed it. Distribution-free: no assumption
    that the noise is Gaussian, which matters because the ratio of two noisy
    quantities is not.
    """
    edges = np.quantile(s0[is_isotropic], np.linspace(0, 1, n_bins + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    out = []
    for low, high in zip(edges[:-1], edges[1:]):
        in_bin = is_isotropic & (s0 >= low) & (s0 < high)
        n = int(in_bin.sum())
        if n < 20:
            out.append({"s0_low": float(low), "s0_high": float(high),
                        "n_calib": n, "threshold": float("nan")})
            continue
        # Conformal quantile: the ceil((n+1)(1-alpha))-th smallest value, which
        # is the smallest bound with a finite-sample guarantee at this n.
        k = int(np.ceil((n + 1) * (1 - alpha)))
        k = min(k, n)
        out.append({"s0_low": float(low), "s0_high": float(high), "n_calib": n,
                    "threshold": float(np.sort(anisotropy[in_bin])[k - 1])})
    return out


def apply_threshold(anisotropy, s0, bins):
    """Classify pixels anisotropic, using each pixel's own S0 bin threshold."""
    flagged = np.zeros(anisotropy.shape, dtype=bool)
    for b in bins:
        if not np.isfinite(b["threshold"]):
            continue
        sel = (s0 >= b["s0_low"]) & (s0 < b["s0_high"])
        flagged |= sel & (anisotropy > b["threshold"])
    return flagged


def demonstrate_n2(sigma=0.25, n_angles=36, n_per_group=4000, alpha=0.10, seed=0):
    """Show a fixed threshold fails where the S0-conditioned one holds.

    Synthetic on purpose, and following REEFPRINT's own phantom discipline: the
    ground truth is known in closed form, so a failure here is the estimator's
    and cannot hide behind "real rocks are messy". Uses N2's own stated numbers
    - sigma = 0.25 R%, n = 36 angles, gangue at R = 4.75% against bright
    sulphide at R = 50%.
    """
    rng = np.random.default_rng(seed)
    angles = np.linspace(0, np.pi, n_angles, endpoint=False)

    def series(true_s0, modulation, n):
        base = true_s0 * (1.0 + modulation * np.cos(2 * angles)[:, None])
        return base + rng.normal(0.0, sigma, size=(n_angles, n))

    from reefprint.polarim.stokes import stokes_from_rotation_series

    # Three populations: bright isotropic, DARK isotropic (the trap), and a
    # genuinely anisotropic phase at intermediate reflectance.
    groups = {
        "isotropic, bright (R=50%)":  (50.0, 0.0),
        "isotropic, dark (R=4.75%)":  (4.75, 0.0),
        "anisotropic (R=20%, m=0.08)": (20.0, 0.08),
    }
    aniso, s0s, names = [], [], []
    for name, (r, m) in groups.items():
        st = stokes_from_rotation_series(series(r, m, n_per_group), angles)
        aniso.append(np.asarray(st.anisotropy).ravel())
        s0s.append(np.asarray(st.s0).ravel())
        names += [name] * n_per_group
    anisotropy = np.concatenate(aniso)
    s0 = np.concatenate(s0s)
    names = np.array(names)
    truly_isotropic = np.char.startswith(names, "isotropic")

    print(f"N2 demonstration: sigma={sigma} R%, n={n_angles} angles, "
          f"alpha={alpha:.0%}\n")
    print(f"{'population':30s}{'median aniso':>14s}{'predicted floor':>17s}")
    print("-" * 61)
    for name, (r, _m) in groups.items():
        sel = names == name
        print(f"{name:30s}{np.median(anisotropy[sel]):>14.4f}"
              f"{noise_floor(sigma, n_angles, r):>17.4f}")

    # A single threshold calibrated ONLY on the bright isotropic population -
    # exactly the mistake N2 warns about.
    bright = names == "isotropic, bright (R=50%)"
    k = int(np.ceil((bright.sum() + 1) * (1 - alpha)))
    fixed = float(np.sort(anisotropy[bright])[min(k, bright.sum()) - 1])

    bins = conformal_threshold_by_s0(anisotropy, s0, truly_isotropic,
                                     alpha=alpha)
    conditioned = apply_threshold(anisotropy, s0, bins)

    print(f"\nfixed threshold calibrated on bright isotropic only: {fixed:.4f}")
    print(f"{'population':30s}{'fixed FP rate':>15s}{'S0-conditioned':>16s}")
    print("-" * 61)
    for name in groups:
        sel = names == name
        fp_fixed = float((anisotropy[sel] > fixed).mean())
        fp_cond = float(conditioned[sel].mean())
        label = "(detection)" if "anisotropic" in name and "iso" not in name[:4] else ""
        print(f"{name:30s}{fp_fixed:>15.1%}{fp_cond:>16.1%} {label}")

    dark = names == "isotropic, dark (R=4.75%)"
    print(f"\nthe trap: a fixed threshold flags "
          f"{float((anisotropy[dark] > fixed).mean()):.0%} of DARK ISOTROPIC "
          f"pixels as anisotropic;\nthe S0-conditioned bound flags "
          f"{float(conditioned[dark].mean()):.0%}, holding to alpha in every "
          f"bin by construction.")
    return {"fixed_threshold": fixed, "bins": bins}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect", action="store_true",
                        help="report the S3 v2 archive layout and exit")
    parser.add_argument("--n2", action="store_true",
                        help="demonstrate the S0-conditioned conformal "
                             "threshold against a fixed one")
    args = parser.parse_args()

    if args.inspect:
        inspect_archive()
        return

    if args.n2:
        demonstrate_n2()
        return

    if not S3V2_DIR.exists():
        print(f"S3 v2 not extracted at {S3V2_DIR}.")
        print("Run --inspect once the download finishes; the layout should "
              "drive the reader rather than a guess.")
        return

    print("Rotation-series reader pending archive inspection.")


if __name__ == "__main__":
    main()
