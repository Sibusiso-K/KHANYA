"""The deterministic, fully offline Week-5 demo scene."""

from __future__ import annotations

from dataclasses import dataclass

from matplotlib.figure import Figure

from reefprint.acquire.phantom import synthetic_rotation_series
from reefprint.polarim.stokes import stokes_from_rotation_series
from reefprint.quantity import assumed, stipulated
from reefprint.trust.abstain import (
    Abstention,
    AbstentionTrigger,
    Conservatism,
    ConservativeDefault,
)
from reefprint.viz.anisotropy import anisotropy_figure
from reefprint.viz.decision import decision_figure

__all__ = ["OfflineDemo", "offline_demo"]


@dataclass(frozen=True, slots=True)
class OfflineDemo:
    """Both screens the demo needs: the physics gate and its visible refusal."""

    gate: Figure
    refusal: Figure


def offline_demo() -> OfflineDemo:
    """Build the demo entirely from local code and the synthetic phantom.

    No URL, file download, font fetch, or service client is used. The phantom is explicitly a
    test instrument, not evidence about mineralogy; the real-data claim remains separate.
    """
    phantom = synthetic_rotation_series(noise_pct=0.25, shape=(64, 96), seed=20260904)
    stokes = stokes_from_rotation_series(
        phantom.series.frames,
        phantom.series.angles_rad,
        project=True,
    )
    gate = anisotropy_figure(
        phantom.series,
        stokes,
        labels=phantom.labels,
        phase_names={1: "pentlandite", 2: "pyrrhotite"},
    )
    conservative_default = ConservativeDefault(
        applies_to="fine-chromite entrainment risk",
        quantity=assumed(0.90, "", "offline demo conservative default; synthetic scene"),
        direction=Conservatism.ASSUME_HIGH,
        low=stipulated(0.0, "", "risk index range [0, 1] by construction"),
        high=stipulated(1.0, "", "risk index range [0, 1] by construction"),
    )
    refusal = decision_figure(
        Abstention(
            default=conservative_default,
            reason="rotation geometry is not established; refusing a mineral map",
            trigger=AbstentionTrigger.UNSUPPORTED_GEOMETRY,
        ),
        title="REEFPRINT refusal path",
    )
    return OfflineDemo(gate=gate, refusal=refusal)
