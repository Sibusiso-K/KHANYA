"""Input-quality gate for the Week-4 degraded-input test.

The gate is deliberately a boundary, not a repair step. It does not sharpen a defocused image,
remove glare, or infer a mineral from an empty field. It returns a usable result or a structured
refusal naming every failed quality check. Thresholds are supplied by a calibration run and carry
their source text; no field limit is silently invented here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

__all__ = [
    "InputQualityMetrics",
    "QualityAssessment",
    "QualityIssue",
    "QualityThresholds",
    "assess_input_quality",
]


class QualityIssue(StrEnum):
    """Failure modes that must not become confident predictions."""

    DEFOCUS = "defocus"
    GLARE = "glare"
    POOR_POLISH = "poor polish"
    WRONG_EXPOSURE = "wrong exposure"
    EMPTY_FIELD = "empty field"
    MALFORMED_INPUT = "malformed quality metadata"


@dataclass(frozen=True, slots=True)
class InputQualityMetrics:
    """Quality measurements calculated before model inference.

    ``sharpness`` is a non-negative focus score. The other fractions are normalised to [0, 1].
    ``exposure`` is a normalised mid-tone fraction; its acceptable range is calibration-specific.
    ``None`` means the metric could not be measured and is itself a refusal condition.
    """

    sharpness: float | None
    glare_fraction: float | None
    polish_defect_fraction: float | None
    exposure: float | None
    foreground_fraction: float | None


@dataclass(frozen=True, slots=True)
class QualityThresholds:
    """Calibrated quality limits, with provenance for every threshold bundle."""

    min_sharpness: float
    max_glare_fraction: float
    max_polish_defect_fraction: float
    min_exposure: float
    max_exposure: float
    min_foreground_fraction: float
    source: str

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("quality thresholds require a non-empty calibration source")
        if self.min_sharpness < 0.0 or not math.isfinite(self.min_sharpness):
            raise ValueError("min_sharpness must be a finite non-negative value")
        for name in (
            "max_glare_fraction",
            "max_polish_defect_fraction",
            "min_exposure",
            "max_exposure",
            "min_foreground_fraction",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0 or not math.isfinite(value):
                raise ValueError(f"{name} must be a finite fraction in [0, 1]")
        if self.min_exposure >= self.max_exposure:
            raise ValueError("min_exposure must be below max_exposure")


@dataclass(frozen=True, slots=True)
class QualityAssessment:
    """The only output of the quality gate: usable, or a named refusal."""

    metrics: InputQualityMetrics
    thresholds: QualityThresholds
    issues: tuple[QualityIssue, ...]

    @property
    def usable(self) -> bool:
        return not self.issues

    @property
    def refused(self) -> bool:
        return not self.usable

    @property
    def refusal_reason(self) -> str | None:
        if self.usable:
            return None
        names = ", ".join(issue.value for issue in self.issues)
        return f"input quality gate failed: {names} (thresholds: {self.thresholds.source})"

    def explain(self) -> str:
        """Render a reason suitable for logs or an operator-facing refusal."""
        if self.usable:
            return f"input quality accepted (thresholds: {self.thresholds.source})"
        return f"refused — {self.refusal_reason}"


def assess_input_quality(
    metrics: InputQualityMetrics,
    thresholds: QualityThresholds,
) -> QualityAssessment:
    """Return a result or a refusal for defocus, glare, polish, exposure, or empty field.

    Missing, non-finite, or out-of-domain measurements produce ``MALFORMED_INPUT`` rather than
    being coerced into a passing value. Multiple failures are retained, so a caller cannot fix one
    symptom and accidentally hide another.
    """
    issues: list[QualityIssue] = []
    values = {
        "sharpness": metrics.sharpness,
        "glare_fraction": metrics.glare_fraction,
        "polish_defect_fraction": metrics.polish_defect_fraction,
        "exposure": metrics.exposure,
        "foreground_fraction": metrics.foreground_fraction,
    }
    malformed = any(
        value is None
        or not math.isfinite(value)
        or (name != "sharpness" and not 0.0 <= value <= 1.0)
        or (name == "sharpness" and value < 0.0)
        for name, value in values.items()
    )
    if malformed:
        issues.append(QualityIssue.MALFORMED_INPUT)
        return QualityAssessment(metrics, thresholds, tuple(issues))

    assert metrics.sharpness is not None
    assert metrics.glare_fraction is not None
    assert metrics.polish_defect_fraction is not None
    assert metrics.exposure is not None
    assert metrics.foreground_fraction is not None
    if metrics.sharpness < thresholds.min_sharpness:
        issues.append(QualityIssue.DEFOCUS)
    if metrics.glare_fraction > thresholds.max_glare_fraction:
        issues.append(QualityIssue.GLARE)
    if metrics.polish_defect_fraction > thresholds.max_polish_defect_fraction:
        issues.append(QualityIssue.POOR_POLISH)
    if not thresholds.min_exposure <= metrics.exposure <= thresholds.max_exposure:
        issues.append(QualityIssue.WRONG_EXPOSURE)
    if metrics.foreground_fraction < thresholds.min_foreground_fraction:
        issues.append(QualityIssue.EMPTY_FIELD)

    return QualityAssessment(metrics, thresholds, tuple(issues))
