"""A separate, simulated control client that consumes advisory values and can refuse them.

Deliberately its own process boundary from :mod:`reefprint.integrate.opcua_server`: a real
plant integration would run the OPC UA client somewhere else entirely (a SCADA node, a
metallurgist's dashboard), and collapsing the two into one object would hide exactly the
acknowledgement-and-expiry contract this module exists to demonstrate.

Everything downstream of the OPC UA read is **simulated** and labelled that way — this
repository ships no controller and Mintek owns both real ones (MillStar, FloatStar). The
:class:`SimulatedPlantParameter` this client adjusts is a plain Python float with a name; it
never reaches anything that moves ore.

Refusal, not repair: :meth:`SimulatedControlClient.poll_and_apply` reads an advisory head, and
if it is stale (past its ``valid_for_seconds`` window from :class:`~reefprint.integrate.
advisory.AdvisoryRecord`) it does **not** apply it and returns an explicit
:class:`RefusedStaleAdvisory` outcome instead — never the last value it successfully applied.
That refusal is the same shape as rule 5's abstention machinery
(:mod:`reefprint.trust.abstain`) for the same reason: an advisory that is silently held past its
validity window is a stale number pretending to be current, and a control loop cannot tell the
difference from the outside.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from asyncua import Client

from reefprint.integrate.opcua_server import AdvisoryNodeIds

__all__ = [
    "AppliedAdvisory",
    "PollOutcome",
    "RefusedStaleAdvisory",
    "SimulatedControlClient",
    "SimulatedPlantParameter",
]


@dataclass(slots=True)
class SimulatedPlantParameter:
    """A single simulated plant setpoint. Not connected to anything real — see module docstring.

    ``history`` records every value this parameter has actually held, in order, so a test or a
    demo can show the moment an advisory changed it — and, just as importantly, the moment a
    stale advisory did *not*.
    """

    name: str
    value: float
    history: list[float] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.history.append(self.value)

    def set(self, value: float) -> None:
        self.value = value
        self.history.append(value)


@dataclass(frozen=True, slots=True)
class AppliedAdvisory:
    """The advisory was fresh and was applied to the simulated parameter."""

    head: str
    value: float
    emitted_at: float
    age_seconds: float


@dataclass(frozen=True, slots=True)
class RefusedStaleAdvisory:
    """The advisory was read but refused — never applied, never used to hold a prior value.

    There is deliberately no field carrying "the value that would have been applied" as
    something the caller could fall back to using anyway; that would just move rule 5's
    hold-the-last-setpoint failure mode one layer up. The only fields here describe *why* it was
    refused, for the operator's screen.
    """

    head: str
    emitted_at: float
    age_seconds: float
    valid_for_seconds: float


PollOutcome = AppliedAdvisory | RefusedStaleAdvisory
"""Every poll either applies a fresh advisory or explicitly refuses a stale one. No third,
silent state — the same discipline as :data:`reefprint.trust.abstain.Decision`."""


class SimulatedControlClient:
    """Connects to an :class:`~reefprint.integrate.opcua_server.AdvisoryServer` and, per head,
    either applies a fresh value to a :class:`SimulatedPlantParameter` or refuses a stale one.

    Node IDs are supplied per head via :class:`~reefprint.integrate.opcua_server.
    AdvisoryNodeIds`, the way a real client would carry them from an engineering configuration
    rather than browsing the server's address space at connection time.
    """

    def __init__(self, endpoint_url: str, *, timeout: float = 4.0) -> None:
        self._endpoint_url = endpoint_url
        self._timeout = timeout
        self._client: Client | None = None
        self._parameters: dict[str, SimulatedPlantParameter] = {}

    async def __aenter__(self) -> SimulatedControlClient:
        self._client = Client(url=self._endpoint_url, timeout=self._timeout)
        await self._client.connect()
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        if self._client is not None:
            await self._client.disconnect()
            self._client = None

    def parameter(self, head: str) -> SimulatedPlantParameter:
        """The simulated parameter this client maintains for ``head``, creating it at 0.0 if new."""
        if head not in self._parameters:
            self._parameters[head] = SimulatedPlantParameter(name=f"sim_{head}_setpoint", value=0.0)
        return self._parameters[head]

    async def poll_and_apply(
        self, head: str, node_ids: AdvisoryNodeIds, *, now: float | None = None
    ) -> PollOutcome:
        """Read one advisory head from the server and either apply it or refuse it.

        :param now: unix epoch seconds. Defaults to the wall clock; pass a fixed value in tests
            so staleness decisions are deterministic rather than racing the test runner.
        """
        if self._client is None:
            raise RuntimeError(
                "poll_and_apply() must run inside 'async with SimulatedControlClient(...)'"
            )
        current = time.time() if now is None else now

        value = await self._client.get_node(node_ids.value).read_value()
        emitted_at = await self._client.get_node(node_ids.emitted_at).read_value()
        valid_for_seconds = await self._client.get_node(node_ids.valid_for_seconds).read_value()

        age_seconds = current - emitted_at
        if age_seconds > valid_for_seconds:
            return RefusedStaleAdvisory(
                head=head,
                emitted_at=emitted_at,
                age_seconds=age_seconds,
                valid_for_seconds=valid_for_seconds,
            )

        self.parameter(head).set(float(value))
        return AppliedAdvisory(
            head=head, value=float(value), emitted_at=emitted_at, age_seconds=age_seconds
        )
