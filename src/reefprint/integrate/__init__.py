"""Integration: OPC UA, OMF, AASX.

Everything in this module is on the kill list, in this order: AASX, then OMF. ``asyncua`` is
LGPL-3.0 and runs on a general-purpose machine only — never on a sealed Pi appliance, because
LGPLv3 anti-tivoisation makes such a deliverable unassignable (gauntlet S3, SBOM.md).

Positioning, per gauntlet S6 and the "MINE" findings: Mintek owns MillStar and FloatStar. This
is an advisory that replaces a *laboratory turnaround*, not a controller that replaces theirs.

The dependency-free record boundary is :class:`reefprint.integrate.advisory.AdvisoryRecord`.
"""
