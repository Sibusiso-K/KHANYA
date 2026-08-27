"""The extinction-estimator loader — leg (b)'s actual route once N3 says SPECIMEN.

Mirrors ``tests/test_s3v2_reader.py``'s synthetic-archive pattern: the real archive is 5.2 GB
and not in this repo, but its layout is cheap to reproduce exactly, and a stage-rotation phantom
with a known forward model gives a closed-form answer to check the loader against — the same
discipline `experiments/001-week1-gate` and `experiments/002-s3v2-geometry` already use.

This module tests the *plumbing* (decode a section's mask and frames into `LabelledSection` /
`RotationSeries`, then hand them to `measure_section_extinction`), not a mineralogical claim
about the real archive. Rule 6: the codebook is supplied by the caller in every test here, never
guessed from mask pixel values, matching `experiments/003-s3v2-extinction/run.py`'s own refusal
to derive one.
"""

from __future__ import annotations

import importlib.util
import io
import sys
import zipfile
from pathlib import Path
from types import ModuleType

import numpy as np
import pytest
from PIL import Image

from reefprint.acquire.phantom import PHASES, crossed_polars_stage_series
from reefprint.acquire.series import RotationGeometry

CODEBOOK = {phase.label: phase.name for phase in PHASES}
SHAPE = (48, 64)


def _load_experiment(rel_path: str) -> ModuleType:
    path = Path(__file__).resolve().parents[1] / rel_path
    spec = importlib.util.spec_from_file_location(rel_path.replace("/", "_"), path)
    if spec is None or spec.loader is None:  # pragma: no cover - would mean the file vanished
        pytest.fail(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_geometry_experiment = _load_experiment("experiments/002-s3v2-geometry/run.py")
_extinction_experiment = _load_experiment("experiments/003-s3v2-extinction/run.py")
load_section_as_specimen_series = _extinction_experiment.load_section_as_specimen_series


def _write_archive(path, *, stem="S3_train_01", n_angles=24, frame_shape=None) -> np.ndarray:
    """A miniature S3 v2 archive built from a real stage-rotation forward model."""
    stage = crossed_polars_stage_series(n_angles=n_angles, shape=SHAPE, seed=3)
    frames = stage.series.frames
    scaled = np.clip(np.round(frames / max(frames.max(), 1e-9) * 255.0), 0.0, 255.0)

    with zipfile.ZipFile(path, "w") as archive:
        mask = (stage.labels + 1).astype(np.uint8)
        buffer = io.BytesIO()
        Image.fromarray(mask).save(buffer, format="PNG")
        archive.writestr(f"S3_v2/masks/train/{stem}.png", buffer.getvalue())

        for index, degrees in enumerate(range(0, 360, 360 // n_angles)):
            frame = scaled[index].astype(np.uint8)
            if frame_shape is not None:
                frame = np.zeros(frame_shape, dtype=np.uint8)
            buffer = io.BytesIO()
            Image.fromarray(frame).save(buffer, format="JPEG", quality=95)
            archive.writestr(
                f"S3_v2/imgs/train/{stem}/{stem}_r{degrees:03d}.jpg", buffer.getvalue()
            )
    return stage.labels


#: Same off-by-one the reader uses for the mask (0 is reserved, phase labels start at 0),
#: shifted up by one on write. The loader-facing codebook must match that shift.
_SHIFTED_CODEBOOK = {label + 1: name for label, name in CODEBOOK.items()}


def test_loader_recovers_a_full_resolution_series_and_labelled_section(tmp_path) -> None:
    archive_path = tmp_path / "S3_v2.zip"
    _write_archive(archive_path, n_angles=24)

    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        result = load_section_as_specimen_series(
            archive,
            names,
            "train",
            "S3_train_01",
            _geometry_experiment.section_frames,
            codebook=_SHIFTED_CODEBOOK,
            locality="phantom-locality",
        )

    assert not isinstance(result, str), f"expected success, got skip reason: {result}"
    section, series = result
    assert series.geometry is RotationGeometry.SPECIMEN
    assert series.frames.shape == (24, *SHAPE)
    # RotationSeries.__post_init__ unconditionally casts to float64 — see the loader's module
    # docstring for why this matters for the real archive's memory budget.
    assert series.frames.dtype == np.float64
    assert section.labels.shape == SHAPE
    assert section.locality == "phantom-locality"
    assert section.section_id == "S3_train_01"


def test_loader_reports_a_shape_mismatch_instead_of_crashing(tmp_path) -> None:
    archive_path = tmp_path / "S3_v2.zip"
    _write_archive(archive_path, n_angles=24, frame_shape=(8, 8))

    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        result = load_section_as_specimen_series(
            archive,
            names,
            "train",
            "S3_train_01",
            _geometry_experiment.section_frames,
            codebook=_SHIFTED_CODEBOOK,
            locality="phantom-locality",
        )

    assert isinstance(result, str)
    assert "shape" in result


def test_loader_reports_too_few_frames_instead_of_crashing(tmp_path) -> None:
    archive_path = tmp_path / "S3_v2.zip"
    _write_archive(archive_path, n_angles=24)

    # Truncate to 2 frames by rewriting a smaller archive under the same stem.
    with zipfile.ZipFile(archive_path) as src:
        names = src.namelist()
        mask_bytes = src.read("S3_v2/masks/train/S3_train_01.png")
        frame_names = sorted(n for n in names if "S3_train_01_r" in n)[:2]
        frame_bytes = {n: src.read(n) for n in frame_names}

    truncated_path = tmp_path / "truncated.zip"
    with zipfile.ZipFile(truncated_path, "w") as dst:
        dst.writestr("S3_v2/masks/train/S3_train_01.png", mask_bytes)
        for name, data in frame_bytes.items():
            dst.writestr(name, data)

    with zipfile.ZipFile(truncated_path) as archive:
        names = archive.namelist()
        result = load_section_as_specimen_series(
            archive,
            names,
            "train",
            "S3_train_01",
            _geometry_experiment.section_frames,
            codebook=_SHIFTED_CODEBOOK,
            locality="phantom-locality",
        )

    assert isinstance(result, str)
    assert "rotation frames" in result


def test_loader_output_feeds_measure_section_extinction_end_to_end(tmp_path) -> None:
    """The actual seam: loader output must be directly acceptable to the bridge function.

    Uses the phantom's known forward model, so pentlandite-equivalent (isotropic, label 0 in
    ``PHASES``) should come back with extinction depth near zero relative to an anisotropic
    phase — the same qualitative claim week-1's gate makes, checked on the loader path rather
    than asserted about it.
    """
    from reefprint.bridge.extinction import measure_section_extinction

    archive_path = tmp_path / "S3_v2.zip"
    _write_archive(archive_path, n_angles=24)

    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        result = load_section_as_specimen_series(
            archive,
            names,
            "train",
            "S3_train_01",
            _geometry_experiment.section_frames,
            codebook=_SHIFTED_CODEBOOK,
            locality="phantom-locality",
        )

    assert not isinstance(result, str)
    section, series = result
    measurement = measure_section_extinction(section, series, min_pixels=10)
    assert measurement.was_measured, measurement.skipped
    assert len(measurement.per_mineral) > 0
