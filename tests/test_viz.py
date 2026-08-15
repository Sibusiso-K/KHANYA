"""reefprint.viz — the week-1 gate as a display, checked on the pixels it actually draws.

These assertions read the arrays back out of the figure rather than recomputing them. A test
that recomputes the anisotropy map and compares it to itself would pass while the figure showed
the reflectance panel twice, which is precisely the bug worth catching in a demo that has to
survive a projector and ten minutes.
"""

from __future__ import annotations

import numpy as np
import pytest

from reefprint.acquire.phantom import synthetic_rotation_series
from reefprint.polarim.stokes import stokes_from_rotation_series
from reefprint.viz.anisotropy import DISPLAY_ANISOTROPY_CEILING, anisotropy_figure

REFLECTANCE_PANEL, ANISOTROPY_PANEL, TRACE_PANEL = 0, 1, 2


@pytest.fixture
def gate():
    """The gate scene: a noisy phantom, its recovered Stokes image, and the figure."""
    phantom = synthetic_rotation_series(noise_pct=0.25, shape=(192, 256), seed=11)
    stokes = stokes_from_rotation_series(
        phantom.series.frames, phantom.series.angles_rad, project=True
    )
    figure = anisotropy_figure(
        phantom.series,
        stokes,
        labels=phantom.labels,
        phase_names={1: "pentlandite", 2: "pyrrhotite"},
    )
    return phantom, stokes, figure


def test_anisotropy_display_separates_isotropic_from_anisotropic_phases(gate):
    """**Week-1 gate, on screen.**

    The gate is not a number in a terminal. It is a display in which pentlandite stays dark
    through a full analyser rotation while pyrrhotite lights up.
    """
    phantom, _, figure = gate
    drawn = figure.axes[ANISOTROPY_PANEL].images[0].get_array()

    pentlandite = drawn[phantom.mask("pentlandite")].mean()
    pyrrhotite = drawn[phantom.mask("pyrrhotite")].mean()
    chromite = drawn[phantom.mask("chromite")].mean()

    assert pentlandite < 0.02, "pentlandite is cubic and must render dark"
    assert chromite < 0.05, "chromite is cubic and must render dark"
    assert pyrrhotite > 4 * pentlandite, "pyrrhotite must light up against pentlandite"


def test_the_two_maps_are_not_the_same_map(gate):
    """Panel 1 is the old project, panel 2 is this one. Drawing S0 twice would look fine."""
    _, stokes, figure = gate

    reflectance = figure.axes[REFLECTANCE_PANEL].images[0].get_array()
    anisotropy = figure.axes[ANISOTROPY_PANEL].images[0].get_array()

    assert np.asarray(reflectance) == pytest.approx(stokes.s0)
    assert np.asarray(anisotropy) == pytest.approx(stokes.anisotropy)


def test_the_anisotropy_colour_scale_is_fixed_not_stretched_to_the_data(gate):
    """An autoscaled colour bar turns pure noise into a convincing anisotropy map.

    The ceiling is a display decision and is pinned. It is never a classification threshold —
    any threshold that decides a mineral label has to be fitted and reported with an interval.
    """
    _, _, figure = gate
    assert figure.axes[ANISOTROPY_PANEL].images[0].get_clim() == (0.0, DISPLAY_ANISOTROPY_CEILING)


def test_the_rotation_traces_show_the_mechanism_not_just_the_result(gate):
    """Panel 3 is the one a sceptical judge reads: flat for cubic, modulating for anisotropic.

    Lines come in pairs — observed, then the fitted three-parameter model over it — in the
    order the phase names were given.
    """
    _, _, figure = gate
    lines = figure.axes[TRACE_PANEL].lines
    assert len(lines) == 4, "two phases, each with its observation and its fit"

    pentlandite, pentlandite_fit, pyrrhotite, pyrrhotite_fit = (
        np.asarray(line.get_ydata()) for line in lines
    )

    assert np.ptp(pentlandite) < 0.4, "cubic: flat through the rotation, bar the noise"
    assert np.ptp(pyrrhotite) > 2.0, "anisotropic: visibly modulating"

    # The fit tracks the data. Where it would not, the three-parameter model is wrong for that
    # phase, and the panel is the place that becomes visible.
    assert pentlandite_fit == pytest.approx(pentlandite, abs=0.2)
    assert pyrrhotite_fit == pytest.approx(pyrrhotite, abs=0.2)


def test_the_figure_says_so_when_it_has_no_labels_rather_than_drawing_an_empty_axis():
    """Rule 5 in miniature: a blank panel is a silent failure with extra steps."""
    phantom = synthetic_rotation_series(n_angles=6, shape=(16, 16))
    stokes = stokes_from_rotation_series(phantom.series.frames, phantom.series.angles_rad)

    figure = anisotropy_figure(phantom.series, stokes)

    assert not figure.axes[TRACE_PANEL].lines
    assert figure.axes[TRACE_PANEL].texts, "an empty panel must explain itself"


# ----------------------------------------------------------------------------------------------
# Not built. Red on purpose.
# ----------------------------------------------------------------------------------------------


@pytest.mark.placeholder
def test_demo_runs_fully_offline():
    """**Week-5 gate.** No network dependency on stage. One laptop."""
    pytest.fail("NOT BUILT — viz: offline end-to-end demo, week-5 gate")


@pytest.mark.placeholder
def test_refusals_are_visible_in_the_ui():
    """Rule 5 is a UI requirement as much as a modelling one.

    A refusal that renders as a blank panel is a silent failure with extra steps. The
    conservative default and its stated reason both have to be on screen.
    """
    pytest.fail("NOT BUILT — viz: refusal display")
