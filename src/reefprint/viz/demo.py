"""The deterministic, fully offline Week-5 demo scene."""

from __future__ import annotations

from dataclasses import dataclass, replace

from matplotlib.figure import Figure

from reefprint.acquire.phantom import synthetic_rotation_series
from reefprint.acquire.series import RotationGeometry
from reefprint.integrate.advisory import AdvisoryRecord
from reefprint.polarim.stokes import stokes_from_rotation_series
from reefprint.quantity import assumed, stipulated
from reefprint.trust.abstain import (
    Abstention,
    AbstentionTrigger,
    Conservatism,
    ConservativeDefault,
)
from reefprint.viz.advisory import SimulatedSetpoint, advisory_figure, apply_or_refuse
from reefprint.viz.anisotropy import anisotropy_figure
from reefprint.viz.decision import decision_figure

__all__ = ["OfflineDemo", "offline_demo"]


@dataclass(frozen=True, slots=True)
class OfflineDemo:
    """The three screens the demo needs: the physics gate, its visible refusal, and the
    plant-parameter advisory contract — published, applied, then refused when stale.
    """

    gate: Figure
    refusal: Figure
    advisory: Figure


def offline_demo() -> OfflineDemo:
    """Build the demo entirely from local code and the synthetic phantom.

    No URL, file download, font fetch, or service client is used. The phantom is explicitly a
    test instrument, not evidence about mineralogy; the real-data claim remains separate.
    """
    phantom = synthetic_rotation_series(noise_pct=0.25, shape=(64, 96), seed=20260904)
    phantom.series.require_analyser_rotation()
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
        title="REEFPRINT / KHANYA — synthetic phantom (not real ore)",
    )
    conservative_default = ConservativeDefault(
        applies_to="fine-chromite entrainment risk",
        quantity=assumed(0.90, "", "offline demo conservative default; synthetic scene"),
        direction=Conservatism.ASSUME_HIGH,
        low=stipulated(0.0, "", "risk index range [0, 1] by construction"),
        high=stipulated(1.0, "", "risk index range [0, 1] by construction"),
    )
    # Deliberately remove geometry metadata from a synthetic input. The actual
    # production guard supplies the refusal; it is not a scripted verdict.
    unsupported = replace(
        phantom.series, geometry=RotationGeometry.UNKNOWN, source="synthetic demo input"
    )
    try:
        unsupported.require_analyser_rotation()
    except ValueError as exc:
        reason = str(exc)
    else:
        raise RuntimeError("the geometry guard accepted an unsupported demo input")
    refusal = decision_figure(
        Abstention(
            default=conservative_default,
            reason=reason,
            trigger=AbstentionTrigger.UNSUPPORTED_GEOMETRY,
        ),
        title="REEFPRINT / KHANYA — synthetic input, actual geometry refusal",
    )

    # Third panel: the plant-parameter advisory contract — CLAUDE.md's brief deliverable
    # ("demonstration of how the model's output can be used to adjust plant parameters"), built
    # and tested end-to-end over a real local OPC UA server (`tests/test_integrate.py`) but never
    # wired into anything a judge would actually see, until now. Runs the identical
    # acknowledgement-and-expiry decision without a network read — see `reefprint.viz.advisory`'s
    # module docstring for why the offline demo cannot open even a loopback socket to demonstrate
    # the wire path itself.
    setpoint = SimulatedSetpoint(name="sim_fine_chromite_risk_setpoint", value=0.0)
    fresh_advisory = AdvisoryRecord(
        values={"fine_chromite_risk": 0.62},
        advisory_influenced=False,
        source="offline demo",
        unit="fraction",
        emitted_at=1_700_000_000.0,
        valid_for_seconds=300.0,
    )
    apply_or_refuse(fresh_advisory, "fine_chromite_risk", setpoint, now=1_700_000_005.0)
    stale_advisory = AdvisoryRecord(
        values={"fine_chromite_risk": 0.91},
        advisory_influenced=False,
        source="offline demo",
        unit="fraction",
        emitted_at=1_700_000_000.0,
        valid_for_seconds=300.0,
    )
    refused = apply_or_refuse(stale_advisory, "fine_chromite_risk", setpoint, now=1_700_000_301.0)
    advisory = advisory_figure(
        setpoint, head="fine_chromite_risk", refused_value=0.91, refused_outcome=refused
    )

    return OfflineDemo(gate=gate, refusal=refusal, advisory=advisory)
