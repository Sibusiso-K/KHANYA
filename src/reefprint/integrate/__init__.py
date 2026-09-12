"""Integration: OPC UA, OMF, AASX.

Everything in this module is on the kill list, in this order: AASX, then OMF. ``asyncua`` is
LGPL-3.0 and runs on a general-purpose machine only — never on a sealed Pi appliance, because
LGPLv3 anti-tivoisation makes such a deliverable unassignable (gauntlet S3, SBOM.md).

Positioning, per gauntlet S6 and the "MINE" findings: Mintek owns MillStar and FloatStar. This
is an advisory that replaces a *laboratory turnaround*, not a controller that replaces theirs.

The dependency-free record boundary is :class:`reefprint.integrate.advisory.AdvisoryRecord`.
The optional OPC UA transport is :mod:`reefprint.integrate.opcua_server` (a real local server)
and :mod:`reefprint.integrate.opcua_client` (a separate simulated control client) — both need
the ``integrate`` extra (``uv sync --extra integrate``) and are not imported by this package's
``__init__`` so the record boundary stays importable without ``asyncua`` present.
"""
