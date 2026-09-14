"""Synchronous adapter from the Streamlit run to REEFPRINT's real OPC UA seam."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class PublishStatus:
    state: str
    message: str
    endpoint: str | None = None
    applied_heads: tuple[str, ...] = ()


def record_parameters(values: dict[str, float], *, stale: bool, now: float) -> dict[str, object]:
    """Build the explicit freshness contract used by the transport transaction."""
    return {
        "values": values,
        "advisory_influenced": False,
        "source": "KHANYA dashboard result",
        "unit": "%",
        "emitted_at": now - 2.0 if stale else now,
        "valid_for_seconds": 0.5 if stale else 30.0,
    }


def publish_result(values: dict[str, float], *, stale: bool = False,
                   stale_reason: str = "presenter demonstration", on_event=None) -> PublishStatus:
    """Publish a measured result and have the separate consumer acknowledge it."""
    try:
        from src.polarimetry import ensure_reefprint
        ensure_reefprint()
        from reefprint.integrate.advisory import AdvisoryRecord
        from reefprint.integrate.opcua_client import AppliedAdvisory, RefusedStaleAdvisory, SimulatedControlClient
        from reefprint.integrate.opcua_server import AdvisoryServer
    except (ImportError, RuntimeError) as exc:
        return PublishStatus("unavailable", f"OPC UA unavailable: {exc}")

    async def transaction() -> PublishStatus:
        now = time.time()
        record = AdvisoryRecord(**record_parameters(values, stale=stale, now=now))
        async with AdvisoryServer() as server:
            published = await server.publish(record)
            if on_event:
                on_event(f"Published to local OPC UA server {server.endpoint_url}: {', '.join(published)}")
            outcomes = []
            async with SimulatedControlClient(server.endpoint_url) as client:
                for head in published:
                    outcomes.append((head, await client.poll_and_apply(head, server.node_ids_for(head))))
            refused = [outcome for _head, outcome in outcomes if isinstance(outcome, RefusedStaleAdvisory)]
            applied = [head for head, outcome in outcomes if isinstance(outcome, AppliedAdvisory)]
            if refused:
                first = refused[0]
                if on_event:
                    on_event(f"Consumer refused stale record: {first.head}")
                return PublishStatus(
                    "refused",
                    f"Consumer refused stale record ({stale_reason}) · {first.head} age {first.age_seconds:.1f}s > validity {first.valid_for_seconds:.1f}s · nothing applied",
                    server.endpoint_url, tuple(applied),
                )
            return PublishStatus(
                "applied", f"Published {', '.join(published)} · consumer acknowledged and applied",
                server.endpoint_url, tuple(applied),
            )

    try:
        return asyncio.run(transaction())
    except (OSError, RuntimeError, TimeoutError) as exc:
        return PublishStatus("error", f"OPC UA transaction failed: {exc}")
