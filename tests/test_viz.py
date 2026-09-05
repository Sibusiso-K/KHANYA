"""reefprint.viz — the week-1 gate as a display, checked on the pixels it actually draws.

These assertions read the arrays back out of the figure rather than recomputing them. A test
that recomputes the anisotropy map and compares it to itself would pass while the figure showed
the reflectance panel twice, which is precisely the bug worth catching in a demo that has to
survive a projector and ten minutes.
"""

from __future__ import annotations

import dataclasses
import socket

import numpy as np
import pytest

import reefprint.viz.anisotropy as anisotropy_module
from reefprint.acquire.phantom import synthetic_rotation_series
from reefprint.acquire.series import RotationGeometry
from reefprint.polarim.stokes import stokes_from_rotation_series
from reefprint.quantity import assumed, stipulated
from reefprint.trust.abstain import (
    Abstention,
    AbstentionTrigger,
    Conservatism,
    ConservativeDefault,
)
from reefprint.viz.anisotropy import DISPLAY_ANISOTROPY_CEILING, anisotropy_figure
from reefprint.viz.decision import decision_figure
from reefprint.viz.demo import offline_demo

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


@pytest.mark.parametrize(
    ("geometry", "expected_label"),
    [
        (RotationGeometry.ANALYSER, "analyser angle (degrees)"),
        (RotationGeometry.SPECIMEN, "stage/specimen angle (degrees)"),
        (RotationGeometry.UNKNOWN, "rotation angle (degrees) — geometry not recorded"),
    ],
)
def test_panel_3_x_axis_label_follows_series_geometry(geometry, expected_label):
    """The axis is "analyser angle" only when an analyser actually turned.

    Hardcoding it regardless of ``series.geometry`` is the defect this figure had: a SPECIMEN
    series would render with a label asserting a claim the data does not support.
    """
    phantom = synthetic_rotation_series(n_angles=6, shape=(16, 16))
    stokes = stokes_from_rotation_series(phantom.series.frames, phantom.series.angles_rad)
    series = dataclasses.replace(phantom.series, geometry=geometry)

    figure = anisotropy_figure(series, stokes)

    assert figure.axes[TRACE_PANEL].get_xlabel() == expected_label


def test_an_analyser_series_renders_with_no_refusal(gate):
    """ANALYSER is the geometry this figure's whole argument is about. No refusal is owed."""
    _, _, figure = gate
    assert len(figure.texts) == 1, "only the suptitle, no geometry refusal"


@pytest.mark.parametrize("geometry", [RotationGeometry.SPECIMEN, RotationGeometry.UNKNOWN])
def test_a_non_analyser_series_still_renders_but_refuses_visibly(geometry):
    """Rule 5: the figure still renders, but a judge cannot mistake it for a valid result.

    A SPECIMEN series inverted with the 2-theta Stokes model returns zero anisotropy for every
    anisotropic grain, silently, unless something on the figure says so. This is that something.
    """
    phantom = synthetic_rotation_series(n_angles=6, shape=(16, 16))
    stokes = stokes_from_rotation_series(phantom.series.frames, phantom.series.angles_rad)
    series = dataclasses.replace(phantom.series, geometry=geometry)

    figure = anisotropy_figure(series, stokes)

    assert len(figure.texts) == 2, "suptitle plus a visible geometry refusal"
    refusal_text = figure.texts[-1].get_text()
    assert geometry.name in refusal_text or "not established" in refusal_text
    # The three panels still render — this is a refusal on top of the figure, not a blank one.
    assert figure.axes[REFLECTANCE_PANEL].images
    assert figure.axes[ANISOTROPY_PANEL].images


@pytest.mark.parametrize("geometry", [RotationGeometry.SPECIMEN, RotationGeometry.UNKNOWN])
def test_the_refusal_does_not_sit_on_top_of_the_panels_it_is_warning_about(geometry):
    """Present is not the same as visible.

    The first version of this drew the refusal at figure-centre, over the two image panels.
    That occludes the pixels a reader is trying to judge, and a screenshot cropped to one
    panel loses the warning entirely — reintroducing the silent-wrong-result failure inside
    the fix for it. The refusal belongs clear of the panels, so pin that rather than trusting
    it to stay put.
    """
    phantom = synthetic_rotation_series(n_angles=6, shape=(16, 16))
    stokes = stokes_from_rotation_series(phantom.series.frames, phantom.series.angles_rad)
    series = dataclasses.replace(phantom.series, geometry=geometry)

    figure = anisotropy_figure(series, stokes)
    _, refusal_y = figure.texts[-1].get_position()

    panel_tops = [figure.axes[panel].get_position().y1 for panel in (0, 1, 2)]
    assert refusal_y > max(panel_tops), (
        f"refusal at y={refusal_y} overlaps panels topping out at {max(panel_tops)}"
    )


def test_an_unmapped_geometry_names_the_gap_rather_than_raising(monkeypatch):
    """A RotationGeometry member added later must not make the figure crash or lie.

    A bare dict subscript would raise KeyError from inside a rendering call, and silently
    borrowing another geometry's label would be worse. The axis says it does not recognise
    the geometry, which is the honest answer and the one Rule 1 asks for.
    """
    phantom = synthetic_rotation_series(n_angles=6, shape=(16, 16))
    stokes = stokes_from_rotation_series(phantom.series.frames, phantom.series.angles_rad)
    series = dataclasses.replace(phantom.series, geometry=RotationGeometry.UNKNOWN)

    monkeypatch.delitem(anisotropy_module._AXIS_LABEL_BY_GEOMETRY, RotationGeometry.UNKNOWN)

    figure = anisotropy_figure(series, stokes)

    assert (
        figure.axes[TRACE_PANEL].get_xlabel()
        == "rotation angle (degrees) — geometry not recognised"
    )


def test_demo_runs_fully_offline(monkeypatch):
    """**Week-5 gate.** No network dependency on stage. One laptop."""

    def network_is_forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("the offline demo attempted to open a network socket")

    monkeypatch.setattr(socket, "socket", network_is_forbidden)
    demo = offline_demo()

    # Three content panels plus one colorbar axis for each image panel.
    assert len(demo.gate.axes) == 5
    assert demo.gate.axes[ANISOTROPY_PANEL].images
    assert "SYSTEM REFUSED TO ANSWER" in "\n".join(text.get_text() for text in demo.refusal.texts)


def test_refusals_are_visible_in_the_ui():
    """Rule 5 is a UI requirement as much as a modelling one.

    A refusal that renders as a blank panel is a silent failure with extra steps. The
    conservative default and its stated reason both have to be on screen.
    """
    default = ConservativeDefault(
        applies_to="fine-chromite entrainment risk",
        quantity=assumed(0.90, "", "test conservative default; synthetic UI fixture"),
        direction=Conservatism.ASSUME_HIGH,
        low=stipulated(0.0, "", "risk index range"),
        high=stipulated(1.0, "", "risk index range"),
    )
    figure = decision_figure(
        Abstention(
            default=default,
            reason="the input is outside every calibrated locality",
            trigger=AbstentionTrigger.OUT_OF_DISTRIBUTION,
        )
    )
    rendered = "\n".join(text.get_text() for text in figure.texts)

    assert "SYSTEM REFUSED TO ANSWER" in rendered
    assert "the input is outside every calibrated locality" in rendered
    assert "Conservative default emitted: 0.9" in rendered
