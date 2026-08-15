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

from reefprint.polarim.stokes import intensity_at_angle

if TYPE_CHECKING:
    import numpy.typing as npt

    from reefprint.acquire.series import RotationSeries
    from reefprint.polarim.stokes import StokesImage

__all__ = ["anisotropy_figure"]

#: Anisotropy above this is drawn as "lights up". Provisional and display-only — it is a
#: colour-scale decision, never a classification threshold. Any threshold that decides a
#: mineral label has to be fitted and reported with an interval (Rule 4), not chosen here.
DISPLAY_ANISOTROPY_CEILING = 0.15


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
    axes.set_xlabel("analyser angle (degrees)")
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
