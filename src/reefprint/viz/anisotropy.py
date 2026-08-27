"""The week-1 gate, on screen.

Three panels, because the argument needs all three:

1. **Reflectance (S0).** Pentlandite and pyrrhotite sit close together. This is the panel that
   shows why the problem is hard — brightness alone does not separate the two sulphides that
   matter, which is exactly why published automated optical mineralogy struggles with them.
2. **Anisotropy (DOLP).** Pentlandite goes dark. Pyrrhotite lights up. This is the gate.
3. **I(theta) through the rotation.** The mechanism, not the result: a flat trace for the cubic
   phase and a modulating one for the anisotropic phase. A judge who does not trust panel 2 can
   read panel 3 and check it by eye.

Panel 1 alone is the previous version of this project. Panel 2 is the current one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from matplotlib.figure import Figure

from reefprint.acquire.series import RotationGeometry
from reefprint.polarim.stokes import intensity_at_angle
from reefprint.trust.abstain import AbstentionTrigger

if TYPE_CHECKING:
    import numpy.typing as npt

    from reefprint.acquire.series import RotationSeries
    from reefprint.polarim.stokes import StokesImage

__all__ = ["anisotropy_figure"]

#: Anisotropy above this is drawn as "lights up". Provisional and display-only — it is a
#: colour-scale decision, never a classification threshold. Any threshold that decides a
#: mineral label has to be fitted and reported with an interval (Rule 4), not chosen here.
DISPLAY_ANISOTROPY_CEILING = 0.15

#: Panel-3 x-axis label, keyed by the geometry that actually produced the angle axis. The
#: Stokes story this figure tells (S0, DOLP, I(2 theta)) is only true for ANALYSER; SPECIMEN
#: and UNKNOWN get their own label rather than inheriting "analyser angle" by default.
_AXIS_LABEL_BY_GEOMETRY = {
    RotationGeometry.ANALYSER: "analyser angle (degrees)",
    RotationGeometry.SPECIMEN: "stage/specimen angle (degrees)",
    RotationGeometry.UNKNOWN: "rotation angle (degrees) — geometry not recorded",
}

#: What panel 3 says if a :class:`RotationGeometry` member is added and not mapped above.
#: Naming the gap beats a ``KeyError`` from a figure, and beats silently borrowing another
#: geometry's label.
_UNRECOGNISED_GEOMETRY_AXIS_LABEL = "rotation angle (degrees) — geometry not recognised"


def _geometry_refusal(geometry: RotationGeometry) -> str | None:
    """The refusal this figure owes a non-ANALYSER series, or ``None`` if none is owed.

    The gate's whole argument — S0 close, DOLP splits, I(theta) modulates at 2 theta — is a
    claim about a rotating-analyser series. Fed a SPECIMEN series it renders the same three
    panels over a 4 phi signal the 2 theta inversion cannot see, and every anisotropic grain
    comes back isotropic with nothing on screen to say why. Rule 5's pattern: refuse visibly,
    with a stated reason, rather than let the panels stand in for a claim they do not support.

    This deliberately does **not** build a :class:`~reefprint.trust.abstain.Abstention`.
    That type's job is to emit a conservative number a control loop can act on, and its
    ``direction`` is a domain claim about which end of a range is safe. There is no such
    claim to make here: a figure is not a setpoint, and asserting ``ASSUME_LOW`` on DOLP
    would assert *isotropic*, which per CLAUDE.md's mineral table reads as pentlandite —
    a mineralogical claim, undefended, arrived at from a rendering decision. Borrowing the
    type for its vocabulary while leaving ``emit()`` uncalled would be the appearance of
    Rule 5 without its substance. Only :class:`AbstentionTrigger` is reused, because its
    wording is the wording that should reach the screen.

    Args:
        geometry: The geometry recorded on the series being plotted.

    Returns:
        The refusal text to draw, or ``None`` when the geometry supports the figure.
    """
    if geometry is RotationGeometry.ANALYSER:
        return None
    if geometry is RotationGeometry.SPECIMEN:
        detail = (
            "series.geometry is SPECIMEN: the stage turned under fixed crossed polars, which "
            "modulates at 4*phi. The Stokes inversion this figure plots fits 2*theta, whose "
            "projection onto a 4*phi signal is zero, so every anisotropic grain reports as "
            "isotropic with no error raised."
        )
    else:
        detail = (
            "series.geometry is UNKNOWN: this series does not record which element rotated, "
            "so whether the Stokes inversion applies at all has not been established. "
            "UNKNOWN is not evidence for SPECIMEN — a discriminator verdict of NEITHER maps "
            "here, and 'I cannot tell' must not become 'it is the convenient one' (Rule 1)."
        )
    return (
        f"NO ANISOTROPY CLAIM CAN BE READ OFF THIS FIGURE\n"
        f"{AbstentionTrigger.UNSUPPORTED_GEOMETRY.value}.\n\n{detail}"
    )


def anisotropy_figure(
    series: RotationSeries,
    stokes: StokesImage,
    *,
    labels: npt.NDArray[np.integer] | None = None,
    phase_names: dict[int, str] | None = None,
    title: str = "REEFPRINT week-1 gate",
) -> Figure:
    """Render the reflectance map, the anisotropy map, and the per-phase rotation traces.

    Args:
        series: The rotation series the Stokes image was recovered from.
        stokes: Recovered per-pixel Stokes parameters.
        labels: Optional label map over the same grid. When given, panel 3 shows the mean
            I(theta) of each labelled phase, which is what makes the mechanism visible.
        phase_names: Optional ``{label: name}``. Labels without a name are not plotted.
        title: Figure suptitle.

    Returns:
        The figure. Not shown or saved — the caller decides, so this works headless in CI.
        Still rendered when ``series.geometry`` is SPECIMEN or UNKNOWN — this is the S3v2
        finding (N3) made visible — but with a stated refusal on the figure (Rule 5) so a
        judge cannot mistake it for a valid rotating-analyser result.
    """
    figure = Figure(figsize=(14.0, 4.6), layout="constrained")
    figure.suptitle(title, fontsize=13, fontweight="bold")
    reflectance_ax, anisotropy_ax, trace_ax = figure.subplots(1, 3)

    reflectance = reflectance_ax.imshow(stokes.s0, cmap="gray")
    reflectance_ax.set_title(f"Reflectance S0 ({series.units})\nbrightness alone", fontsize=10)
    reflectance_ax.set_axis_off()
    figure.colorbar(reflectance, ax=reflectance_ax, fraction=0.046)

    anisotropy = anisotropy_ax.imshow(
        stokes.anisotropy, cmap="inferno", vmin=0.0, vmax=DISPLAY_ANISOTROPY_CEILING
    )
    anisotropy_ax.set_title("Anisotropy (DOLP)\nisotropic dark, anisotropic bright", fontsize=10)
    anisotropy_ax.set_axis_off()
    figure.colorbar(anisotropy, ax=anisotropy_ax, fraction=0.046)

    _draw_traces(trace_ax, series, stokes, labels, phase_names)

    refusal = _geometry_refusal(series.geometry)
    if refusal is not None:
        # Along the top, spanning the full width, rather than centred over the panels. A
        # centred box occludes the very pixels a reader is trying to judge, and a panel
        # cropped out of a centred figure can lose the refusal entirely - which is the
        # failure this exists to prevent, reintroduced by the fix for it.
        figure.text(
            0.5,
            0.985,
            refusal,
            transform=figure.transFigure,
            ha="center",
            va="top",
            fontsize=9,
            fontweight="bold",
            color="firebrick",
            wrap=True,
            bbox={"boxstyle": "round", "facecolor": "white", "edgecolor": "firebrick"},
        )
    return figure


def _draw_traces(
    axes,  # noqa: ANN001 — matplotlib Axes, not usefully typed without pulling in the stub
    series: RotationSeries,
    stokes: StokesImage,
    labels: npt.NDArray[np.integer] | None,
    phase_names: dict[int, str] | None,
) -> None:
    degrees = np.degrees(series.angles_rad)
    axes.set_title("I(theta) through the rotation", fontsize=10)
    # .get() with an explicit fallback, not a bare subscript: a RotationGeometry member added
    # later would otherwise raise KeyError here while _geometry_refusal quietly treated it as
    # UNKNOWN, which is two different answers to one new enum value.
    axes.set_xlabel(_AXIS_LABEL_BY_GEOMETRY.get(series.geometry, _UNRECOGNISED_GEOMETRY_AXIS_LABEL))
    axes.set_ylabel(f"mean intensity ({series.units})")

    if labels is None or phase_names is None:
        axes.text(0.5, 0.5, "no label map supplied", ha="center", va="center")
        return

    for label, name in sorted(phase_names.items()):
        selected = labels == label
        if not selected.any():
            continue
        observed = series.frames[:, selected].mean(axis=1)
        axes.plot(degrees, observed, marker="o", markersize=3, linewidth=1.2, label=name)

        # The fit, drawn over the data. Where they diverge, the three-parameter model is
        # wrong for that phase — which is information, not an embarrassment.
        fitted = np.array(
            [
                float(intensity_at_angle(stokes, angle)[selected].mean())
                for angle in series.angles_rad
            ]
        )
        axes.plot(degrees, fitted, linestyle="--", linewidth=0.9, color="black", alpha=0.4)

    axes.legend(fontsize=8, loc="upper right")
    axes.margins(x=0.02)
