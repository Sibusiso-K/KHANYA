"""A real local OPC UA advisory server. Not a mock -- a genuine :class:`asyncua.Server`.

Positioning, per CLAUDE.md and gauntlet finding S6: this is an advisory that replaces a
*laboratory turnaround*, not a controller that replaces MillStar or FloatStar -- Mintek owns
both. The server publishes structural-proxy values under a ``sim_advisories`` folder for a
plant historian or SCADA layer to subscribe to; it issues no setpoints and closes no loops.
Every value published here already passed through
:class:`reefprint.integrate.advisory.AdvisoryRecord`, which is where rule 1's provenance and
rule 5's abstention machinery live -- this module is a transport boundary, not a place that
computes anything.

``asyncua`` is **LGPL-3.0**: dynamically linked, user-replaceable, fine on a general-purpose
machine. It must never ship inside a sealed appliance -- LGPLv3 Section 4 / GPLv3 Section 6
anti-tivoisation would make the deliverable unassignable to Mintek (SBOM.md, gauntlet finding
S3). Say "runs on plant IT hardware", never "embedded in the sensor".

This module is only importable with the ``integrate`` extra installed
(``uv sync --extra integrate``) -- it is optional and stays out of the default dependency set
on purpose, per the "kept deliberately lean" note in ``pyproject.toml``.
"""

from __future__ import annotations

import contextlib
import socket
from dataclasses import dataclass

from asyncua import Server, ua

from reefprint.integrate.advisory import AdvisoryRecord

__all__ = ["AdvisoryNodeIds", "AdvisoryServer"]

_NAMESPACE_URI = "urn:reefprint:sim-advisory"
_FOLDER_NAME = "sim_advisories"


@dataclass(frozen=True, slots=True)
class AdvisoryNodeIds:
    """The OPC UA node IDs published for one advisory head.

    Opaque to the caller by design: a real consumer is expected to have these from an
    engineering configuration (an OPC UA companion specification, a historian tag list), the
    way a plant integration actually works, not from browsing the address space at runtime.
    """

    value: str
    unit: str
    emitted_at: str
    valid_for_seconds: str
    advisory_influenced: str
    source: str

    def as_tuple(self) -> tuple[str, ...]:
        return (
            self.value,
            self.unit,
            self.emitted_at,
            self.valid_for_seconds,
            self.advisory_influenced,
            self.source,
        )


class AdvisoryServer:
    """A local OPC UA server exposing :class:`AdvisoryRecord` values as OPC UA variables.

    Binds to localhost by default, on an ephemeral port chosen before the server starts so the
    caller can learn the endpoint without asking ``asyncua`` to introspect its own bound socket.
    Async context-manager usage is the intended shape::

        async with AdvisoryServer() as server:
            await server.publish(record)
            ...
            # server.stop() runs automatically, including on an exception
    """

    def __init__(self, *, host: str = "127.0.0.1", port: int | None = None) -> None:
        self._host = host
        self._port = port if port is not None else _free_port(host)
        self._server = Server()
        self._namespace_index: int | None = None
        self._advisory_folder = None
        self._nodes: dict[str, AdvisoryNodeIds] = {}
        self._started = False

    @property
    def endpoint_url(self) -> str:
        return f"opc.tcp://{self._host}:{self._port}/reefprint/sim-advisory/"

    @property
    def published_heads(self) -> tuple[str, ...]:
        return tuple(self._nodes)

    def node_ids_for(self, head: str) -> AdvisoryNodeIds:
        """The node IDs for one head, once it has been published at least once.

        :raises KeyError: if ``head`` has never appeared in a published record. Publishing is
            what creates the nodes -- there is nothing to hand out before that.
        """
        try:
            return self._nodes[head]
        except KeyError:
            raise KeyError(
                f"{head!r} has never been published on this server. Published heads: "
                f"{sorted(self._nodes)!r}"
            ) from None

    async def start(self) -> None:
        await self._server.init()
        self._server.set_endpoint(self.endpoint_url)
        self._server.set_server_name("REEFPRINT sim advisory server")
        self._namespace_index = await self._server.register_namespace(_NAMESPACE_URI)
        objects = self._server.nodes.objects
        self._advisory_folder = await objects.add_folder(self._namespace_index, _FOLDER_NAME)
        await self._server.start()
        self._started = True

    async def stop(self) -> None:
        if self._started:
            await self._server.stop()
            self._started = False

    async def __aenter__(self) -> AdvisoryServer:
        await self.start()
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.stop()

    async def publish(self, record: AdvisoryRecord) -> tuple[str, ...]:
        """Write every head in ``record`` onto the server, creating nodes on first sight.

        :returns: the head names published, in the order ``record.values`` iterates them.

        There is no separate "commit" step: each OPC UA variable write in the loop below is
        already atomic, and a client reading mid-loop sees old values for heads not yet reached
        rather than a torn record -- acceptable here because every field of one head is written
        before the next head starts, and a consumer is expected to key on ``emitted_at`` per
        head, not on cross-head simultaneity.
        """
        if not self._started:
            raise RuntimeError("start() must be awaited before publish()")
        assert self._namespace_index is not None
        assert self._advisory_folder is not None
        ns = self._namespace_index

        published: list[str] = []
        for head, value in record.values.items():
            if head not in self._nodes:
                self._nodes[head] = await self._create_head_nodes(ns, head)
            ids = self._nodes[head]
            await self._write(ids.value, float(value), ua.VariantType.Double)
            await self._write(ids.unit, record.unit, ua.VariantType.String)
            await self._write(ids.emitted_at, float(record.emitted_at), ua.VariantType.Double)
            await self._write(
                ids.valid_for_seconds, float(record.valid_for_seconds), ua.VariantType.Double
            )
            await self._write(
                ids.advisory_influenced, bool(record.advisory_influenced), ua.VariantType.Boolean
            )
            await self._write(ids.source, record.source, ua.VariantType.String)
            published.append(head)
        return tuple(published)

    async def _write(self, node_id: str, value: object, variant_type: ua.VariantType) -> None:
        await self._server.get_node(node_id).write_value(value, variant_type)

    async def _create_head_nodes(self, ns: int, head: str) -> AdvisoryNodeIds:
        assert self._advisory_folder is not None
        folder = await self._advisory_folder.add_folder(ns, head)
        value = await folder.add_variable(ns, "value", 0.0, ua.VariantType.Double)
        unit = await folder.add_variable(ns, "unit", "", ua.VariantType.String)
        emitted_at = await folder.add_variable(ns, "emitted_at", 0.0, ua.VariantType.Double)
        valid_for = await folder.add_variable(ns, "valid_for_seconds", 0.0, ua.VariantType.Double)
        influenced = await folder.add_variable(
            ns, "advisory_influenced", False, ua.VariantType.Boolean
        )
        source = await folder.add_variable(ns, "source", "", ua.VariantType.String)
        for variable in (value, unit, emitted_at, valid_for, influenced, source):
            await variable.set_writable(True)
        return AdvisoryNodeIds(
            value=value.nodeid.to_string(),
            unit=unit.nodeid.to_string(),
            emitted_at=emitted_at.nodeid.to_string(),
            valid_for_seconds=valid_for.nodeid.to_string(),
            advisory_influenced=influenced.nodeid.to_string(),
            source=source.nodeid.to_string(),
        )


def _free_port(host: str) -> int:
    """An ephemeral TCP port, chosen and released before the server binds it for real.

    There is a race between releasing the socket here and the server binding it -- vanishingly
    unlikely on localhost in a test process, and the alternative (asking ``asyncua`` to
    introspect its own bound address) couples this module to internals this project does not
    control the API of.
    """
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind((host, 0))
        return sock.getsockname()[1]
