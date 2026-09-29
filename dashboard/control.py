"""Advisory -> simulated plant parameter, over REEFPRINT's real OPC UA seam.

`dashboard/opcua.py` publishes measurements and the consumer mirrors each one
into a setpoint of the same name, rebuilt on every upload. That shows the
transport works; it does not show a recommendation changing a plant setting.
This module does: one explicitly simulated Boolean tag, `regrind_enabled`,
driven by the advisor's action, carried across uploads by the caller.

Only two actions command it. Every abstaining action (Marginal, Flag, No
recommendation) issues no command, so the setting holds - a hold is the
absence of a command, not a stale record. Reagent actions target a parameter
this simulator does not model, so they do not touch regrind either. The tag is
illustrative: it is not an engineered plant recommendation or a P80 target.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

REGRIND_HEAD = "regrind_enabled"


@dataclass(frozen=True)
class CommandStatus:
    state: str  # applied | held | refused | unavailable | error
    before: float
    after: float
    reason: str
    endpoint: str | None = None


def command_for(action: str) -> tuple[float | None, str]:
    """The regrind value an advisory action requests, or None with why it requests nothing."""
    if action == "Grind finer":
        return 1.0, "confident low-liberation advisory: regrind requested"
    if action == "Continue at current setpoint":
        return 0.0, "within specification: regrind not requested"
    if action.startswith("Adjust reagent dosage"):
        return None, "advisory targets reagent dosage, which this simulator does not model: no regrind command"
    return None, "advisory is abstaining: no command issued, setting held for review"


def command_parameters(value: float, action: str, *, stale: bool, now: float) -> dict[str, object]:
    """Same freshness contract as dashboard.opcua.record_parameters, for one command tag."""
    return {
        "values": {REGRIND_HEAD: value},
        # The sampled section was not produced under an earlier command, which
        # is what this field records (REEFPRINT blind spot 10).
        "advisory_influenced": False,
        "source": f"KHANYA advisor: {action}",
        "unit": "",  # 1 = regrind enabled, 0 = bypass
        "emitted_at": now - 2.0 if stale else now,
        "valid_for_seconds": 0.5 if stale else 30.0,
    }


def send_command(action: str, before: float, *, stale: bool = False, on_event=None) -> CommandStatus:
    """Command the simulated regrind tag from `action`, starting from the plant's current value."""
    value, reason = command_for(action)
    if value is None:
        return CommandStatus("held", before, before, reason)
    try:
        from src.polarimetry import ensure_reefprint
        ensure_reefprint()
        from reefprint.integrate.advisory import AdvisoryRecord
        from reefprint.integrate.opcua_client import RefusedStaleAdvisory, SimulatedControlClient
        from reefprint.integrate.opcua_server import AdvisoryServer
    except (ImportError, RuntimeError) as exc:
        return CommandStatus("unavailable", before, before, f"OPC UA unavailable: {exc}")

    async def transaction() -> CommandStatus:
        record = AdvisoryRecord(**command_parameters(value, action, stale=stale, now=time.time()))
        async with AdvisoryServer() as server:
            await server.publish(record)
            if on_event:
                on_event(f"Command {REGRIND_HEAD}={value:g} published to {server.endpoint_url}")
            async with SimulatedControlClient(server.endpoint_url) as client:
                # The consumer starts from the plant's actual state, not a fresh 0.0.
                client.parameter(REGRIND_HEAD).set(before)
                outcome = await client.poll_and_apply(REGRIND_HEAD, server.node_ids_for(REGRIND_HEAD))
                after = client.parameter(REGRIND_HEAD).value
            if isinstance(outcome, RefusedStaleAdvisory):
                return CommandStatus(
                    "refused", before, after,
                    f"consumer refused stale command {REGRIND_HEAD}={value:g} "
                    f"(age {outcome.age_seconds:.1f}s > "
                    f"validity {outcome.valid_for_seconds:.1f}s): setting unchanged",
                    server.endpoint_url,
                )
            return CommandStatus("applied", before, after, reason, server.endpoint_url)

    try:
        return asyncio.run(transaction())
    except (OSError, RuntimeError, TimeoutError) as exc:
        return CommandStatus("error", before, before, f"OPC UA command failed: {exc}")
