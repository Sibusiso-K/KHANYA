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
import io
import json
import os
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

from .segmentation import config
from .segmentation.lumenstone import CODEBOOK

# Lethabo's inversion, imported unchanged. Not vendored, not reimplemented - if
# his Stokes code changes, this experiment changes with it, which is the point.
#
# WHICH REEFPRINT, AND WHY THE VERSION IS CHECKED. This used to hardcode
# `~/Desktop/REEFPRINT - Copy/src`, a snapshot taken before REEFPRINT grew its
# rotation-geometry discriminator (`polarim/geometry.py`, commit 19154c5). That
# is not cosmetic staleness. A snapshot without the discriminator will happily
# invert a *stage* rotation with the rotating-analyser model and return
# S1 = S2 = 0 for every anisotropic grain - no exception, no NaN, a perfectly
# realisable answer that reads as "anisotropy does not separate these minerals".
# That false negative is indistinguishable from a real null result, and it would
# be a null result about the one measurement the project rests on.
#
# So the tree is resolved by search, live-checkout first and the old snapshot
# last, and any candidate lacking the discriminator is rejected by name rather
# than silently used. Set REEFPRINT_SRC to override.
REEFPRINT_SRC_CANDIDATES = (
    Path.home() / "Desktop" / "REEFPRINT" / "src",                  # live checkout
    Path(__file__).resolve().parents[2] / "REEFPRINT" / "src",      # sibling checkout
    Path.home() / "Desktop" / "REEFPRINT - Copy" / "src",           # old snapshot, last
)

#: Present only from REEFPRINT commit 19154c5. Its absence is the tell that a
#: candidate predates the geometry discriminator.
GEOMETRY_MODULE = Path("reefprint") / "polarim" / "geometry.py"
STOKES_MODULE = Path("reefprint") / "polarim" / "stokes.py"


def _resolve_reefprint_src():
    """Locate a REEFPRINT source tree new enough to be safe to import.

    Raises:
        RuntimeError: nothing found, or everything found predates the geometry
            discriminator. Both are refusals with a stated reason - never a
            silent fallback, because the silent fallback is the bug.
    """
    override = os.environ.get("REEFPRINT_SRC")
    candidates = (Path(override),) if override else REEFPRINT_SRC_CANDIDATES
    found = [c for c in candidates if (c / STOKES_MODULE).exists()]
    if not found:
        raise RuntimeError(
            "no REEFPRINT source tree found. Checked: "
            + "; ".join(str(c) for c in candidates)
            + ". Set REEFPRINT_SRC to the repo's src/ directory."
        )
    for candidate in found:
        if (candidate / GEOMETRY_MODULE).exists():
            return candidate
    raise RuntimeError(
        "found REEFPRINT at "
        + "; ".join(str(c) for c in found)
        + " but none of them has " + str(GEOMETRY_MODULE) + ", so every one "
        "predates the rotation-geometry discriminator. Inverting a stage "
        "rotation with the rotating-analyser model returns S1 = S2 = 0 "
        "silently, which would read as 'polarimetry does not work on real "
        "ore'. Pull REEFPRINT to at least 19154c5, or point REEFPRINT_SRC at a "
        "checkout that has it."
    )


REEFPRINT_SRC = _resolve_reefprint_src()
if str(REEFPRINT_SRC) not in sys.path:
    sys.path.insert(0, str(REEFPRINT_SRC))


class GeometryMismatch(RuntimeError):
    """The archive's rotation geometry is not the one the Stokes model assumes.

    Raised rather than skipped, and raised out of the whole run rather than one
    section, because geometry is a property of the acquisition: if one S3 v2
    section is a stage rotation then all 47 are, and pooling the remaining 46
    into a null result is precisely the failure being prevented.
    """

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

# Real layout, found by --inspect (2026-08-20): each section is
# S3_v2/imgs/{split}/S3_{split}_NN/S3_{split}_NN_rDDD.jpg, 72 frames at 5deg
# steps over the full 360deg (0..355). Masks are one per section, at
# S3_v2/masks/{split}/S3_{split}_NN.png, code repeated across R/G/B exactly
# like v1 (segmentation/lumenstone.py) - verified against real pixel data,
# not assumed from the v1 convention.
ROTATION_RE = re.compile(r"_r(\d{3})\.jpg$")

# Bounds decode+fit cost: 47 sections x up to 72 full-res JPEG decodes each is
# already the dominant cost, so pixels are subsampled per class per section
# rather than reading all ~8.65M pixels/frame. summarise_by_class only needs
# distribution shape (median, quartiles), not an exhaustive census.
MAX_SAMPLES_PER_CLASS = 1200
MIN_SAMPLES_PER_CLASS = 500  # matches summarise_by_class's own min_pixels floor


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
    # A keyword search ("rot", "xpl", ...) missed this archive's real
    # convention entirely (filenames end "_r000.jpg".."_r355.jpg", no word
    # containing those substrings) - found only by listing real filenames.
    # Matched on the actual pattern now, not a guess at naming.
    rotational = [n for n in names if ROTATION_RE.search(n)]
    print(f"\nentries matching the rotation-frame pattern (_rDDD.jpg): {len(rotational)}")
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


# --- The ten-mineral symmetry test on real S3 v2 data -----------------------
#
# demonstrate_n2() above is synthetic on purpose - closed-form ground truth so
# a failure is the estimator's, not the rocks'. This is the real measurement
# it exists to justify: pool labelled pixels from every S3 v2 section's
# rotation series and see whether anisotropy actually separates isotropic
# from anisotropic minerals, magnetite/hematite above all (JOINT-PLAN 3a/4).
#
# Train and test sections are pooled as one sample. The train/test leakage
# warning in segmentation/lumenstone.py ("rotations are near-duplicates, a
# naive split would leak them") is about MODEL GENERALISATION claims. Nothing
# here is trained or evaluated out-of-sample - this is a one-shot physics
# measurement over labelled pixels, so pooling every section is more data, not
# leakage.


def list_sections(names):
    """(split, section_id) for every section with a ground-truth mask."""
    out = []
    for split in ("train", "test"):
        prefix = f"S3_v2/masks/{split}/"
        stems = sorted(
            n[len(prefix):-4] for n in names
            if n.startswith(prefix) and n.endswith(".png")
        )
        out.extend((split, stem) for stem in stems)
    return out


def section_frames(names, split, stem):
    """[(degrees, zip_path), ...] for one section's rotation series, sorted."""
    prefix = f"S3_v2/imgs/{split}/{stem}/{stem}_r"
    frames = []
    for n in names:
        if not n.startswith(prefix):
            continue
        m = ROTATION_RE.search(n)
        if m:
            frames.append((int(m.group(1)), n))
    frames.sort()
    return frames


def sample_section(archive, names, split, stem, rng):
    """Sample up to MAX_SAMPLES_PER_CLASS labelled pixels per class from one
    section and run the geometry-appropriate inversion on just those pixels.

    A full section is 3396x2547 x 72 rotation frames - far too large to hold
    as a stack. Pixel POSITIONS are chosen from the mask alone (cheap), then
    each of the 72 frames is decoded once, the chosen positions read out of
    it, and the decoded frame discarded - so peak memory is one frame
    (~26 MB), never the full rotation stack.
    """
    frames = section_frames(names, split, stem)
    if len(frames) < 3:  # extinction_from_stage_series' own MIN_ANGLES floor
        return None

    with archive.open(f"S3_v2/masks/{split}/{stem}.png") as f:
        mask = np.array(Image.open(io.BytesIO(f.read())))
    codes = mask[:, :, 0] if mask.ndim == 3 else mask

    positions_by_code = {}
    for code in np.unique(codes):
        code = int(code)
        entry = CODEBOOK.get(code)
        if entry is None or SYMMETRY.get(entry[0]) in (None, "resin"):
            continue
        ys, xs = np.where(codes == code)
        if ys.size < MIN_SAMPLES_PER_CLASS:
            continue
        n = min(MAX_SAMPLES_PER_CLASS, ys.size)
        pick = rng.choice(ys.size, size=n, replace=False)
        positions_by_code[code] = (ys[pick], xs[pick])

    if not positions_by_code:
        return None

    all_ys = np.concatenate([p[0] for p in positions_by_code.values()])
    all_xs = np.concatenate([p[1] for p in positions_by_code.values()])
    class_codes = np.concatenate([
        np.full(p[0].shape, code, dtype=np.int64)
        for code, p in positions_by_code.items()
    ])

    # Full 360deg range (72 frames, 5deg steps) when every frame decodes
    # clean. extinction_from_stage_series' cos(4*phi)/sin(4*phi) terms repeat
    # every 90deg, not 180 - so this set is 18 distinct residues mod 90, each
    # repeated 4x, not 2x as it would be for the (unused, 180-periodic)
    # Stokes model. It validates degeneracy via the design matrix's condition
    # number, not exact duplicates - repeated-but-consistent rows improve
    # conditioning rather than breaking it, so all clean frames are used
    # rather than discarding any.
    good_degrees, rows = [], []
    for deg, name in frames:
        with archive.open(name) as f:
            frame = np.array(Image.open(io.BytesIO(f.read())).convert("L"))
        if frame.shape != codes.shape:
            # Real, isolated data fault (found: 1 of 72 frames in one S3 v2
            # section stored portrait instead of landscape, no EXIF tag
            # explaining it). One bad frame does not need to cost the whole
            # section - skip it, keep the other ~71 angles, which is still
            # far above MIN_ANGLES.
            print(f"    {split}/{stem} {name.rsplit('/', 1)[-1]}: shape "
                  f"{frame.shape} != mask {codes.shape}, skipping this frame")
            continue
        good_degrees.append(deg)
        rows.append(frame[all_ys, all_xs])

    if len(good_degrees) < 3:
        return None
    angles_rad = np.deg2rad(np.array(good_degrees, dtype=float))
    intensities = np.stack(rows)

    # Which element turned? Ask the frames, not the filename or the paper.
    # N3 (Lethabo, CONTEXT.md 2026-08-21): two independent runs on this exact
    # archive both came back NEITHER, leaning stage - "do not run the Stokes
    # inversion on S3 v2 as things stand... re-pointed at
    # reefprint.polarim.extinction, not stokes_from_rotation_series." A clean
    # SECOND verdict would mean this section really is a rotating-analyser
    # series, which extinction's pure-4th-harmonic model does not fit either -
    # still raised for the whole run rather than skipped, since geometry is a
    # property of the acquisition rig: if one section is the other geometry,
    # all 47 are, and continuing on the rest would silently pool a mismatched
    # estimator into the result.
    from reefprint.polarim.geometry import HarmonicVerdict, harmonic_signature

    signature = harmonic_signature(intensities, angles_rad)
    if signature.verdict is HarmonicVerdict.SECOND:
        raise GeometryMismatch(f"{split}/{stem}: {signature.explain()}")

    from reefprint.polarim.extinction import extinction_from_stage_series
    extinction = extinction_from_stage_series(intensities, angles_rad)
    return {
        # Extinction amplitude (~|r1-r2|**2, arbitrary intensity units) stands
        # in for Stokes anisotropy; dc (fitted mean level, not a calibrated
        # reflectance - extinction.py's own docstring: "no S0 in the data")
        # stands in for s0. summarise_by_class/conformal_threshold_by_s0 use
        # both only as relative, per-class/per-bin quantities, so neither
        # substitution changes their math - see extinction.py for why the two
        # are not on the same physical footing as Stokes' S0.
        "anisotropy": np.asarray(extinction.amplitude).ravel(),
        "s0": np.asarray(extinction.dc).ravel(),
        "class_codes": class_codes,
        "geometry": signature.explain(),
    }


def run_symmetry_test(seed=20260820, verbose=True):
    """Pool every S3 v2 section into one anisotropy-vs-symmetry measurement.

    Returns a JSON-able report, or None if S3 v2 has not been downloaded.
    """
    if not S3V2_ZIP.exists():
        print(f"not downloaded yet: {S3V2_ZIP}")
        return None

    rng = np.random.default_rng(seed)
    aniso_parts, s0_parts, code_parts = [], [], []
    with zipfile.ZipFile(S3V2_ZIP) as archive:
        names = [n for n in archive.namelist() if not n.startswith("__MACOSX")]
        sections = list_sections(names)
        if verbose:
            print(f"{len(sections)} sections\n")
        try:
            for i, (split, stem) in enumerate(sections):
                result = sample_section(archive, names, split, stem, rng)
                if result is None:
                    if verbose:
                        print(f"  [{i + 1}/{len(sections)}] {split}/{stem}: skipped "
                              f"(no rotation series or no labelled pixels)")
                    continue
                if verbose:
                    print(f"  [{i + 1}/{len(sections)}] {split}/{stem}: "
                          f"{result['class_codes'].size} pixels")
                aniso_parts.append(result["anisotropy"])
                s0_parts.append(result["s0"])
                code_parts.append(result["class_codes"])
        except GeometryMismatch as exc:
            # A refusal carrying its reason, not a None and not a null result.
            # Reached only on a clean SECOND verdict: this section looks like
            # a genuine rotating-analyser series, which extinction's pure-4th-
            # harmonic model does not fit - the opposite surprise from the one
            # N3 found archive-wide (NEITHER, leaning stage).
            print("\nREFUSED: the extinction (stage-rotation) model does not "
                  "apply to this archive.")
            print(f"  {exc}")
            print("  This section reads as a rotating-analyser series - "
                  "reefprint.polarim.stokes may be the right estimator here "
                  "after all; re-check N3 before assuming it applies to "
                  "every section.")
            return {
                "refused": "rotation geometry is not a stage rotation",
                "evidence": str(exc),
                "n_sections": len(sections),
                "next_step": "reefprint.polarim.stokes (2nd-harmonic estimator)",
            }

    if not aniso_parts:
        print("no sections yielded usable pixels")
        return None

    anisotropy = np.concatenate(aniso_parts)
    s0 = np.concatenate(s0_parts)
    codes = np.concatenate(code_parts)

    present = sorted(set(codes.tolist()))
    class_names = [CODEBOOK[c][0] for c in present]
    index_of = {c: i for i, c in enumerate(present)}
    labels = np.array([index_of[c] for c in codes], dtype=np.int64)

    rows = summarise_by_class(anisotropy, s0, labels, class_names)
    sep = separation(rows)

    symmetry_of = np.array([SYMMETRY.get(CODEBOOK[c][0]) for c in codes])
    is_isotropic = symmetry_of == "isotropic"
    is_anisotropic = symmetry_of == "anisotropic"
    bins = conformal_threshold_by_s0(anisotropy, s0, is_isotropic)
    flagged = apply_threshold(anisotropy, s0, bins)

    if verbose:
        print(f"\n{len(codes)} pixels pooled across {len(class_names)} classes")
        print(f"{'mineral':16s}{'symmetry':12s}{'n':>8s}{'aniso median':>14s}")
        for r in rows:
            print(f"{r['mineral']:16s}{r['symmetry']:12s}{r['n_pixels']:>8d}"
                  f"{r['anisotropy_median']:>14.4f}")
        if "headline_pair" in sep:
            hp = sep["headline_pair"]
            a, b = HEADLINE_PAIR
            print(f"\nheadline pair {a} vs {b}: "
                  f"{hp[a]:.4f} vs {hp[b]:.4f}, ratio {hp['ratio']:.2f}x")

    return {
        "n_sections": len(sections),
        "n_pixels_sampled": int(codes.size),
        "per_class": rows,
        "separation": sep,
        "conformal_bins": [
            {**b, "threshold": None if not np.isfinite(b["threshold"]) else b["threshold"]}
            for b in bins
        ],
        "detection_rate_on_known_anisotropic":
            float(flagged[is_anisotropic].mean()) if is_anisotropic.any() else None,
        "false_positive_rate_on_known_isotropic":
            float(flagged[is_isotropic].mean()) if is_isotropic.any() else None,
    }


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

    report = run_symmetry_test()
    if report is None:
        return
    out_path = config.ROOT / "reports" / "polarimetry_s3.json"
    out_path.write_text(json.dumps(report, indent=2))
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
