"""Traceable camera-count to quantitative reflectance calibration."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from reefprint.quantity import Quantity, assumed

FloatArray = npt.NDArray[np.floating]

__all__ = [
    "QDF_VALUES",
    "ReflectanceStandard",
    "correct_counts",
    "qdf_value",
]


@dataclass(frozen=True, slots=True)
class ReflectanceStandard:
    """A measured standard at one wavelength, used to scale corrected counts to R%."""

    name: str
    wavelength_nm: int
    counts: FloatArray
    reflectance_pct: float

    def __post_init__(self) -> None:
        counts = np.asarray(self.counts, dtype=float)
        if counts.size == 0 or not np.isfinite(counts).all():
            raise ValueError("a reflectance standard needs finite, non-empty counts")
        if self.reflectance_pct <= 0 or not np.isfinite(self.reflectance_pct):
            raise ValueError("standard reflectance must be finite and positive")
        object.__setattr__(self, "counts", counts)

    @property
    def signal(self) -> float:
        """Mean corrected count, the denominator of the R% conversion."""
        return float(np.mean(self.counts))

    def convert(self, sample_counts: npt.ArrayLike) -> FloatArray:
        """Convert already-corrected sample counts to R% at this wavelength."""
        sample = np.asarray(sample_counts, dtype=float)
        if not np.isfinite(sample).all():
            raise ValueError("sample counts must be finite")
        if self.signal <= 0:
            raise ValueError("standard signal must be positive")
        return sample / self.signal * self.reflectance_pct


def correct_counts(
    raw_counts: npt.ArrayLike,
    *,
    dark_counts: npt.ArrayLike | None = None,
    flat_field: npt.ArrayLike | None = None,
) -> FloatArray:
    """Remove dark current and divide out spatial flat-field response.

    ``flat_field`` is expressed as a multiplicative response map around one (for example,
    ``0.8`` at a vignetted corner). It is applied after dark subtraction, before reflectance
    conversion, so vignetting cannot become a systematic mineral signal.
    """
    raw = np.asarray(raw_counts, dtype=float)
    if raw.size == 0 or not np.isfinite(raw).all():
        raise ValueError("raw counts must be finite and non-empty")
    dark = np.zeros_like(raw) if dark_counts is None else np.asarray(dark_counts, dtype=float)
    flat = np.ones_like(raw) if flat_field is None else np.asarray(flat_field, dtype=float)
    try:
        dark = np.broadcast_to(dark, raw.shape)
        flat = np.broadcast_to(flat, raw.shape)
    except ValueError as exc:
        raise ValueError("dark and flat-field arrays must broadcast to raw counts") from exc
    if not np.isfinite(dark).all() or not np.isfinite(flat).all():
        raise ValueError("dark and flat-field values must be finite")
    if np.any(flat <= 0):
        raise ValueError("flat-field response must be strictly positive")
    return (raw - dark) / flat


QDF_VALUES: dict[str, Quantity] = {
    "chromite": assumed(
        13.0, "R%", "CLAUDE.md approximate physics table; not a verified QDF record"
    ),
    "gangue/resin": assumed(
        4.75, "R%", "midpoint of CLAUDE.md approximate 4.5-5 range; not a verified QDF record"
    ),
}


def qdf_value(mineral: str) -> Quantity:
    """Return an approximate reference, NOT a verified QDF calibration standard.

    The historical function name is retained for compatibility. Wavelength-specific
    QDF records have not been supplied; these two values carry ASSUMED provenance.
    """
    key = mineral.strip().lower()
    try:
        return QDF_VALUES[key]
    except KeyError as exc:
        known = ", ".join(sorted(QDF_VALUES))
        raise KeyError(f"no QDF value recorded for {mineral!r}; known anchors: {known}") from exc
