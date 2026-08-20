"""Rotation series on disk, as OME-TIFF.

OME-TIFF because the metadata rides *inside* the file. A plain TIFF stack plus a JSON sidecar
separates the provenance from the pixels the first time someone copies one and not the other,
and Rule 1 needs the provenance attached to the number. `tifffile` (BSD-3-Clause) rather than
Bio-Formats (GPL-2.0) — :doc:`ADR-0001 </04-decisions/0001-ome-tiff-via-tifffile-not-bioformats>`.
No JVM anywhere.

**What this module refuses to do is the point of it.** A stored stack from somebody else's
dataset does not tell you its analyser angles or which element was turning. Both are load-bearing
and neither is guessable:

* Assuming angles are evenly spread over pi is inventing ``n_angles`` numbers (Rule 1).
* Assuming the analyser rotated, when in fact the stage did, produces a uniformly-zero
  anisotropy map with no error raised — see :class:`~reefprint.acquire.series.RotationGeometry`.

So :func:`read_rotation_series` reads what the file states and demands the rest from the caller.
Files written by :func:`write_rotation_series` state everything and need no arguments.

The REEFPRINT payload lives in the OME ``<Description>`` element as JSON. That is a real OME
element, escaped by the XML writer, and readable by any OME-aware tool — which is the
"documented extension namespace, not silently dropped" that ADR-0001 committed to.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree

import numpy as np
import tifffile

from reefprint.acquire.series import RotationGeometry, RotationSeries

if TYPE_CHECKING:
    from pathlib import Path

    import numpy.typing as npt

    FloatArray = npt.NDArray[np.floating]

__all__ = ["PAYLOAD_SCHEMA", "read_rotation_series", "write_rotation_series"]

#: Version tag on the JSON payload. Bump it when the keys change, so a file written by an older
#: version is rejected loudly rather than half-understood.
PAYLOAD_SCHEMA = "reefprint.acquire.store/1"

#: OME-XML namespace `tifffile` writes.
_OME_NS = {"ome": "http://www.openmicroscopy.org/Schemas/OME/2016-06"}

#: (angle, y, x). Mirrors the container's own rule; repeated here so the error can name the file.
_SERIES_NDIM = 3


def write_rotation_series(
    series: RotationSeries,
    path: Path,
    *,
    compression: str | None = "zlib",
) -> Path:
    """Write a rotation series to OME-TIFF, angles and geometry included.

    Args:
        series: What to write. Frames are stored as float32 — the recovery is a least-squares
            fit whose conditioning is set by the angle set, not by the eighth decimal place of
            an intensity, and float64 doubles the file for nothing.
        path: Destination. Convention is ``*.ome.tif``; not enforced, because a caller with a
            reason is not required to argue with the library about a filename.
        compression: Passed to `tifffile`. ``"zlib"`` is lossless and roughly halves these
            files. ``None`` writes uncompressed.

    Returns:
        ``path``, so a call can be chained or asserted on.

    Raises:
        TypeError: ``series.metadata`` holds something JSON cannot represent. The offending
            key is named. It is not dropped silently — losing acquisition provenance on write
            is the exact failure OME-TIFF was chosen to prevent.
    """
    payload: dict[str, Any] = {
        "schema": PAYLOAD_SCHEMA,
        "angles_rad": [float(a) for a in series.angles_rad],
        "source": series.source,
        "geometry": series.geometry.name,
        "units": series.units,
        "metadata": series.metadata,
    }
    try:
        description = json.dumps(payload)
    except TypeError as exc:
        offending = [k for k, v in series.metadata.items() if not _is_json_safe(v)]
        msg = (
            f"series.metadata is not JSON-serialisable and would be lost on write; "
            f"offending key(s): {offending or 'unknown'}. Convert to plain types first."
        )
        raise TypeError(msg) from exc

    path.parent.mkdir(parents=True, exist_ok=True)
    tifffile.imwrite(
        path,
        np.asarray(series.frames, dtype=np.float32),
        ome=True,
        compression=compression,
        metadata={"axes": "ZYX", "Description": description},
    )
    return path


def read_rotation_series(
    path: Path,
    *,
    angles_rad: FloatArray | None = None,
    geometry: RotationGeometry | None = None,
    source: str | None = None,
    units: str | None = None,
) -> RotationSeries:
    """Load a rotation series from a TIFF stack.

    A file written by :func:`write_rotation_series` carries everything and the keyword
    arguments are unnecessary. Any other stack — a LumenStone XPL rotation, a folder someone
    converted, a stack from a microscope that knew nothing about this project — carries pixels
    and nothing else, and then ``angles_rad`` and ``geometry`` are **required**.

    Args:
        path: A TIFF or OME-TIFF holding ``(n_angles, height, width)``.
        angles_rad: Angle per frame. Required when the file does not state them. Supplying
            these for a file that *does* state them is an error rather than an override — two
            sources disagreeing about the angle axis is exactly the bug this container exists
            to catch, and picking a winner silently would hide it.
        geometry: Which element rotated. Required when the file does not state it. Read
            :class:`~reefprint.acquire.series.RotationGeometry` first; the wrong value here
            fails silently, not loudly.
        source: Overrides the provenance line. Defaults to what the file says, or to the
            filename when it says nothing.
        units: Intensity units. Defaults to what the file says, or ``"arbitrary"`` — never to
            ``"R%"``, which would be a calibration claim this module cannot make.

    Returns:
        A :class:`~reefprint.acquire.series.RotationSeries`, identical in content to the one
        written if it came from :func:`write_rotation_series`.

    Raises:
        ValueError: The file is not a 3-D stack; or it states no angles and none were given;
            or it states no geometry and none was given; or the file and the caller both state
            angles or geometry; or the payload schema is one this version does not know.
    """
    with tifffile.TiffFile(path) as handle:
        frames = handle.asarray()
        stated = _payload_from_ome(handle.ome_metadata) if handle.is_ome else None

    frames = np.asarray(frames, dtype=float)
    if frames.ndim != _SERIES_NDIM:
        msg = (
            f"{path.name} holds a {frames.ndim}-D array of shape {frames.shape}; a rotation "
            f"series is (n_angles, height, width). A single frame is not a series."
        )
        raise ValueError(msg)

    angles = _resolve_angles(path, stated, angles_rad, n_frames=frames.shape[0])
    resolved_geometry = _resolve_geometry(path, stated, geometry)

    stated_meta: dict[str, Any] = dict(stated.get("metadata", {})) if stated else {}
    stated_meta["read_from"] = str(path)
    if stated is None:
        stated_meta["angles_supplied_by"] = "caller — not recorded in the file"
        stated_meta["geometry_supplied_by"] = "caller — not recorded in the file"

    return RotationSeries(
        frames=frames,
        angles_rad=angles,
        source=source or (stated or {}).get("source") or f"stored series {path.name}",
        geometry=resolved_geometry,
        units=units or (stated or {}).get("units") or "arbitrary",
        metadata=stated_meta,
    )


# ----------------------------------------------------------------------------------------------
# Internals
# ----------------------------------------------------------------------------------------------


def _is_json_safe(value: object) -> bool:
    try:
        json.dumps(value)
    except TypeError:
        return False
    return True


def _payload_from_ome(ome_xml: str | None) -> dict[str, Any] | None:
    """Pull the REEFPRINT JSON out of the OME ``<Description>``, or ``None`` if it is not ours.

    An OME-TIFF written by anything else has a ``<Description>`` holding prose, or none at all.
    Both mean "this file does not state its angles", which the caller then has to supply — not
    an error here.
    """
    if not ome_xml:
        return None
    try:
        root = ElementTree.fromstring(ome_xml)
    except ElementTree.ParseError:
        return None

    element = root.find("./ome:Image/ome:Description", _OME_NS)
    if element is None or not element.text:
        return None
    try:
        payload = json.loads(element.text)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict) or "schema" not in payload:
        return None

    schema = payload["schema"]
    if schema != PAYLOAD_SCHEMA:
        msg = (
            f"file carries payload schema {schema!r}, this build understands "
            f"{PAYLOAD_SCHEMA!r}. Half-reading a metadata block is worse than not reading it."
        )
        raise ValueError(msg)
    return payload


def _resolve_angles(
    path: Path,
    stated: dict[str, Any] | None,
    supplied: FloatArray | None,
    *,
    n_frames: int,
) -> FloatArray:
    in_file = stated.get("angles_rad") if stated else None

    if in_file is not None and supplied is not None:
        msg = (
            f"{path.name} states its own analyser angles and angles_rad was also passed. "
            f"Refusing to pick a winner: a disagreement about the angle axis is the bug, not "
            f"a preference. Drop one."
        )
        raise ValueError(msg)
    if in_file is not None:
        return np.asarray(in_file, dtype=float)
    if supplied is not None:
        return np.asarray(supplied, dtype=float)

    msg = (
        f"{path.name} does not record its rotation angles, so they must be passed as "
        f"angles_rad (length {n_frames}). Assuming an even spread over pi would invent "
        f"{n_frames} numbers — Rule 1. Published sequences usually step in degrees over a full "
        f"360, which is neither even over pi nor in radians; convert deliberately."
    )
    raise ValueError(msg)


def _resolve_geometry(
    path: Path,
    stated: dict[str, Any] | None,
    supplied: RotationGeometry | None,
) -> RotationGeometry:
    name = stated.get("geometry") if stated else None
    in_file = RotationGeometry[name] if name in RotationGeometry.__members__ else None

    if in_file is not None and supplied is not None and in_file is not supplied:
        msg = (
            f"{path.name} states geometry {in_file.name} and {supplied.name} was passed. These "
            f"are different measurements, not different words for one. Fix the file or the call."
        )
        raise ValueError(msg)
    if in_file is not None:
        return in_file
    if supplied is not None:
        return supplied

    msg = (
        f"{path.name} does not record which element rotated. Pass geometry=. "
        f"RotationGeometry.ANALYSER only if the analyser turned while the polariser and the "
        f"specimen stayed put; a stage rotation under crossed polars is SPECIMEN and inverts "
        f"to zero anisotropy without raising anything."
    )
    raise ValueError(msg)
