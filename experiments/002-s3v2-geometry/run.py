"""Settle finding N3: what geometry are LumenStone S3 v2's rotation series, actually?

    uv run python experiments/002-s3v2-geometry/run.py --archive path/to/S3_v2.zip

N3 holds that published "XPL rotation sequences" are almost certainly *stage* rotations under
fixed crossed polars rather than *analyser* rotations. That is an inference from how anisotropy
has been observed since the 1940s, and the whole of week-1 leg (b) rests on it. This script
replaces the inference with a measurement, using :func:`reefprint.polarim.geometry.harmonic_signature`:
a stage rotation puts its power in the 4th harmonic, an analyser rotation in the 2nd, and the
two are separable from the frames alone.

**Why it matters, in one line:** if the frames are stage rotations, then feeding them to the
Stokes inversion returns ``S1 = S2 = 0`` for every anisotropic mineral — no exception, no NaN —
so a ten-mineral symmetry test would report a separation ratio near 1.0 and read as *polarimetry
does not work on real ore*, when it actually means *the model was fitted to the wrong harmonic*.

The archive is ~5.2 GB and is not in this repo (LumenStone's licence is informal and unnamed —
see `docs/05-toolchain.md` §5). Point ``--archive`` at wherever it lives. Nothing is extracted;
frames are decoded one at a time from the zip and discarded, so peak memory is one frame.

Sampling note: pixel *positions* are drawn from the section's mask, then each rotation frame is
decoded once and read at those positions. A full section is 3396x2547 across 72 frames, which is
far too large to hold as a stack, and the geometry verdict needs distribution shape rather than
an exhaustive census.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

from reefprint.polarim.geometry import (
    DETECTION_SNR,
    MODULATING_FRACTION,
    HarmonicSignature,
    HarmonicVerdict,
    harmonic_signature,
)

#: ``S3_v2/imgs/{split}/S3_{split}_NN/S3_{split}_NN_rDDD.jpg`` — 72 frames, 5 degree steps,
#: full 360. Layout confirmed against the real archive by KHANYA's ``src/polarimetry.py
#: --inspect`` on 2026-08-20; a keyword search for "rot"/"xpl" misses it entirely.
ROTATION_RE = re.compile(r"_r(\d{3})\.jpg$")

#: Pixels sampled per section. The verdict is taken over the modulating decile of these, so
#: this is the budget for the whole distribution, not for the evidence.
SAMPLES_PER_SECTION = 4000

#: Sections to read unless ``--sections`` says otherwise. The geometry is a property of the
#: acquisition protocol, so it should be identical across sections — and if it is not, that
#: is the finding, which is why each section is reported separately as well as pooled.
DEFAULT_SECTIONS = 6


def list_sections(names: list[str]) -> list[tuple[str, str]]:
    """``(split, stem)`` for every section carrying a ground-truth mask."""
    out: list[tuple[str, str]] = []
    for split in ("train", "test"):
        prefix = f"S3_v2/masks/{split}/"
        out.extend(
            (split, name[len(prefix) : -4])
            for name in names
            if name.startswith(prefix) and name.endswith(".png")
        )
    return sorted(out)


def section_frames(names: list[str], split: str, stem: str) -> list[tuple[int, str]]:
    """``[(degrees, zip_path), ...]`` for one section's rotation series, sorted by angle."""
    prefix = f"S3_v2/imgs/{split}/{stem}/{stem}_r"
    frames = [
        (int(match.group(1)), name)
        for name in names
        if name.startswith(prefix) and (match := ROTATION_RE.search(name))
    ]
    return sorted(frames)


def read_section(
    archive: zipfile.ZipFile,
    names: list[str],
    split: str,
    stem: str,
    rng: np.random.Generator,
    *,
    n_samples: int = SAMPLES_PER_SECTION,
) -> dict[str, object]:
    """Sample one section's rotation series at mask-derived positions.

    Returns a dict carrying either ``intensities``/``angles_rad`` or a ``skipped`` reason. It
    never raises on a shape mismatch: a mask that does not match its own frames is a fact about
    the archive worth reporting per section, and dying on the first one hides how many there are.
    """
    frames = section_frames(names, split, stem)
    if len(frames) < 5:
        return {"skipped": f"only {len(frames)} rotation frames"}

    with archive.open(f"S3_v2/masks/{split}/{stem}.png") as handle:
        mask = np.array(Image.open(io.BytesIO(handle.read())))
    codes = mask[:, :, 0] if mask.ndim == 3 else mask

    # Peek at one frame before sampling positions, so a mismatch is reported rather than hit
    # as an IndexError halfway through decoding 72 JPEGs.
    with archive.open(frames[0][1]) as handle:
        probe = np.array(Image.open(io.BytesIO(handle.read())).convert("L"))
    if probe.shape != codes.shape:
        return {
            "skipped": "mask/frame shape mismatch",
            "mask_shape": list(codes.shape),
            "frame_shape": list(probe.shape),
        }

    # Sample anywhere that is labelled at all. Which mineral a pixel is does not matter here —
    # the question is which harmonic the acquisition put the modulation in, and the strongest
    # modulators answer it whatever they turn out to be.
    ys, xs = np.where(codes > 0)
    if ys.size < n_samples:
        return {"skipped": f"only {int(ys.size)} labelled pixels"}
    pick = rng.choice(ys.size, size=n_samples, replace=False)
    ys, xs = ys[pick], xs[pick]

    intensities = np.empty((len(frames), n_samples), dtype=float)
    for i, (_deg, name) in enumerate(frames):
        with archive.open(name) as handle:
            frame = np.array(Image.open(io.BytesIO(handle.read())).convert("L"))
        if frame.shape != codes.shape:
            return {
                "skipped": f"frame {name.rsplit('/', 1)[-1]} shape differs from mask",
                "mask_shape": list(codes.shape),
                "frame_shape": list(frame.shape),
            }
        intensities[i] = frame[ys, xs]

    return {
        "intensities": intensities,
        "angles_rad": np.deg2rad(np.array([d for d, _ in frames], dtype=float)),
        "degrees": [d for d, _ in frames],
    }


def modulation_depth_dn(intensities: np.ndarray) -> float:
    """Median peak-to-peak, in digital numbers, over the top decile of modulating pixels.

    Reported so a null verdict can be told apart from an empty field: if the strongest pixels
    barely move, there was nothing to measure, whatever the geometry.

    It is deliberately *not* used as a quantisation threshold. That was tried and it was wrong:
    8-bit clip-and-round costs neither geometry its verdict at any noise level tested, 0 to 10
    percent (stage snr_4 6.8 raw against 6.9 quantised at 5 percent). The earlier claim of a 3x
    quantisation penalty was an artefact of casting negative intensities straight to ``uint8``,
    which wraps rather than clips - and at 5 percent noise 46 percent of a crossed-polars frame
    stack is below zero, because the signal sits on a near-black field. See
    ``tests/test_geometry.py`` and docs/BUILDLOG.md, 2026-08-20.
    """
    swing = np.ptp(intensities, axis=0)
    top = swing >= np.quantile(swing, 0.90)
    return float(np.median(swing[top]))


def pool_signatures(
    signatures: list[HarmonicSignature],
    *,
    detection_snr: float = DETECTION_SNR,
    modulating_fraction: float = MODULATING_FRACTION,
) -> tuple[float, float, HarmonicVerdict, int, int]:
    """Combine per-section harmonic signatures into one verdict, without requiring
    a common frame count across sections.

    THE BUG THIS REPLACES. The original pooling concatenated raw (n_angles, n_pixels)
    frame arrays across sections before calling harmonic_signature once on the
    result, which requires every section to share n_angles exactly. The real S3 v2
    archive does not: usable sections range from 24 to 72 frames. Trimming every
    section down to the smallest (24) is not neutral - it throws away up to two
    thirds of the rotation series on the richer sections, for no statistical reason.

    THE FIX. harmonic_signature already reduces the frame axis to two PER-PIXEL
    numbers: amplitude_2/floor_2 and amplitude_4/floor_4 (see its docstring - these
    are per-pixel arrays, independent of how many frames a given section's fit used
    once the fit is done). Frame count differences are therefore already absorbed
    into each pixel's own floor before pooling needs to happen at all. So: call
    harmonic_signature once per section at that section's NATIVE frame count and
    angles (already done in the per-section loop above), then concatenate the
    resulting per-pixel amplitude/floor arrays across sections, and re-run exactly
    the same selection-and-median rule harmonic_signature uses internally - top
    `modulating_fraction` pixels by max(amplitude_2, amplitude_4), median SNR over
    that selection. Every frame every section actually captured contributes.

    Returns (snr_2, snr_4, verdict, n_pixels_pooled, n_sections_pooled).
    """
    amplitude_2 = np.concatenate([sig.amplitude_2.ravel() for sig in signatures])
    amplitude_4 = np.concatenate([sig.amplitude_4.ravel() for sig in signatures])
    floor_2 = np.concatenate([sig.floor_2.ravel() for sig in signatures])
    floor_4 = np.concatenate([sig.floor_4.ravel() for sig in signatures])

    snr_2_map = np.divide(amplitude_2, floor_2, out=np.zeros_like(amplitude_2), where=floor_2 > 0)
    snr_4_map = np.divide(amplitude_4, floor_4, out=np.zeros_like(amplitude_4), where=floor_4 > 0)

    strength = np.maximum(amplitude_2, amplitude_4)
    n_pixels = strength.size
    n_keep = max(1, round(modulating_fraction * n_pixels))
    selected = np.argpartition(strength, n_pixels - n_keep)[n_pixels - n_keep :]

    snr_2 = float(np.median(snr_2_map[selected]))
    snr_4 = float(np.median(snr_4_map[selected]))

    has_2 = snr_2 >= detection_snr
    has_4 = snr_4 >= detection_snr
    if has_2 and has_4:
        verdict = HarmonicVerdict.BOTH
    elif has_2:
        verdict = HarmonicVerdict.SECOND
    elif has_4:
        verdict = HarmonicVerdict.FOURTH
    else:
        verdict = HarmonicVerdict.NEITHER

    return snr_2, snr_4, verdict, n_pixels, len(signatures)


def main() -> None:
    # The verdict strings carry em-dashes and the Windows console is cp1252 by default.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True, help="path to S3_v2.zip")
    parser.add_argument("--sections", type=int, default=DEFAULT_SECTIONS)
    parser.add_argument("--samples", type=int, default=SAMPLES_PER_SECTION)
    parser.add_argument("--seed", type=int, default=20260820)
    args = parser.parse_args()

    if not args.archive.exists():
        raise SystemExit(f"not found: {args.archive}")

    rng = np.random.default_rng(args.seed)
    per_section: list[dict[str, object]] = []
    signatures: list[HarmonicSignature] = []
    depths: list[float] = []  # per-section modulation depth; see note at pooling

    with zipfile.ZipFile(args.archive) as archive:
        names = [n for n in archive.namelist() if not n.startswith("__MACOSX")]
        sections = list_sections(names)
        print(f"{len(sections)} sections in archive; reading {min(args.sections, len(sections))}\n")
        print(f"{'section':22s}{'frames':>7s}{'snr 2theta':>12s}{'snr 4phi':>10s}  verdict")
        print("-" * 78)

        for split, stem in sections[: args.sections]:
            data = read_section(archive, names, split, stem, rng, n_samples=args.samples)
            if "skipped" in data:
                print(f"{stem:22s}{'-':>7s}{'-':>12s}{'-':>10s}  SKIPPED: {data['skipped']}")
                per_section.append({"section": stem, **data})
                continue

            intensities = data["intensities"]
            angles = data["angles_rad"]
            signature = harmonic_signature(intensities, angles)
            print(
                f"{stem:22s}{signature.n_angles:>7d}{signature.snr_2:>12.1f}"
                f"{signature.snr_4:>10.1f}  {signature.verdict.name}"
            )
            per_section.append(
                {
                    "section": stem,
                    "n_frames": signature.n_angles,
                    "snr_2": signature.snr_2,
                    "snr_4": signature.snr_4,
                    "verdict": signature.verdict.name,
                    "geometry": signature.geometry.name,
                }
            )
            signatures.append(signature)
            depths.append(modulation_depth_dn(intensities))

    if not signatures:
        raise SystemExit("\nno section yielded a usable rotation series — nothing to conclude")

    # Pooled per PIXEL statistics, not per raw frame - see pool_signatures docstring.
    # This is what lets sections with 24 frames and sections with 72 frames combine
    # without truncating the richer ones down to the poorest.
    snr_2, snr_4, verdict, n_pixels, n_pooled = pool_signatures(signatures)
    frame_counts = sorted({sig.n_angles for sig in signatures})

    print(
        f"POOLED over {n_pooled} sections, {n_pixels} pixels "
        f"(native frame counts used per section: {frame_counts})"
    )
    print(
        f"2nd harmonic at {snr_2:.1f}x its noise floor, 4th harmonic at {snr_4:.1f}x, "
        f"threshold {DETECTION_SNR:.1f}x. Verdict: {verdict.value}."
    )
    print(
        f"Modulation depth, top decile, median across sections: "
        f"{float(np.median(depths)):.1f} DN of 255 (range "
        f"{min(depths):.1f}-{max(depths):.1f})."
    )
    print("=" * 78)

    verdicts = {row.get("verdict") for row in per_section if "verdict" in row}
    if len(verdicts) > 1:
        print(
            f"\nWARNING: sections disagree on geometry ({sorted(verdicts)}). The acquisition "
            "protocol should be constant across a dataset; a split verdict is itself a finding."
        )

    if verdict is HarmonicVerdict.FOURTH:
        print(
            "\nN3 CONFIRMED. These are stage rotations under crossed polars, not analyser\n"
            "rotations. The linear Stokes inversion must NOT be run on them — it would report\n"
            "every anisotropic mineral as isotropic, silently. Week-1 leg (b) needs a\n"
            "fourth-harmonic estimator, and the two must never be conflated in the talk."
        )
    elif verdict is HarmonicVerdict.SECOND:
        print(
            "\nN3 REFUTED, and this is the better outcome. The series carry 2nd-harmonic\n"
            "modulation, so the Stokes inversion applies directly and week-1 leg (b) can run\n"
            "on this data as originally planned. Record how the acquisition achieved this."
        )
    else:
        print(
            f"\nNO VERDICT ({verdict.name}). Neither geometry is cleanly supported.\n"
            "Do not proceed to an inversion on this basis; N3 stays open."
        )
        print(
            "\nThis NO VERDICT is not neutral evidence, and it leans toward a stage rotation.\n"
            "A 4-phi signal goes as bireflectance SQUARED; a 2-theta signal goes as\n"
            "bireflectance itself, on top of a bright S0. On the phantom the analyser geometry\n"
            "stays detectable through 38x more noise than the stage geometry does (measured\n"
            "2026-08-20; CLAUDE.md predicts 2/a, which spans 16.7x to 66.7x across these\n"
            "phases). So a null is far more likely if these are stage rotations than if they\n"
            "are analyser rotations. It is NOT clearance to run the Stokes inversion.\n"
            "N3 stays open, and open-but-leaning."
        )

    out_dir = Path(__file__).parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "archive": str(args.archive),
        "samples_per_section": args.samples,
        "seed": args.seed,
        "detection_snr": DETECTION_SNR,
        "modulation_depth_dn_median": float(np.median(depths)),
        "modulation_depth_dn_range": [min(depths), max(depths)],
        "pooled": {
            "n_sections": n_pooled,
            "n_pixels": n_pixels,
            "native_frame_counts": frame_counts,
            "snr_2": snr_2,
            "snr_4": snr_4,
            "verdict": verdict.name,
            "geometry": verdict.to_geometry().name,
        },
        "per_section": per_section,
    }
    out_path = out_dir / "s3v2-geometry.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
