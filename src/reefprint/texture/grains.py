"""Grain extraction and mineral contact statistics from labelled maps."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage

__all__ = ["Grain", "association_matrix", "extract_grains"]


@dataclass(frozen=True, slots=True)
class Grain:
    """One connected component of a mineral label."""

    label: int
    mineral: str
    area_px: int
    centroid_yx: tuple[float, float]


def extract_grains(
    labels: np.ndarray,
    *,
    phase_names: dict[int, str] | None = None,
    connectivity: int = 1,
) -> tuple[Grain, ...]:
    """Extract connected grains independently within each positive mineral label."""
    image = np.asarray(labels)
    if image.ndim != 2:
        raise ValueError(f"labels must be a 2-D map, got shape {image.shape}")
    if not np.issubdtype(image.dtype, np.integer):
        raise TypeError("labels must contain integer mineral IDs")
    if connectivity not in (1, 2):
        raise ValueError("connectivity must be 1 (edges) or 2 (edges and corners)")
    structure = ndimage.generate_binary_structure(2, connectivity)
    names = phase_names or {}
    grains: list[Grain] = []
    for label in sorted(int(value) for value in np.unique(image) if value > 0):
        components, count = ndimage.label(image == label, structure=structure)
        for component in range(1, count + 1):
            ys, xs = np.nonzero(components == component)
            grains.append(
                Grain(
                    label=label,
                    mineral=names.get(label, f"label-{label}"),
                    area_px=int(ys.size),
                    centroid_yx=(float(ys.mean()), float(xs.mean())),
                )
            )
    return tuple(grains)


def association_matrix(
    labels: np.ndarray, *, phase_names: dict[int, str] | None = None
) -> tuple[tuple[str, ...], np.ndarray]:
    """Return symmetric fractions of total directed 4-neighbour mineral contacts.

    Each shared edge is counted in both directions. The entire matrix sums to one
    when contacts exist (otherwise zero); rows are not conditional probabilities.
    Row normalisation would destroy symmetry when phases have unequal contacts.
    """
    image = np.asarray(labels)
    if image.ndim != 2 or not np.issubdtype(image.dtype, np.integer):
        raise ValueError("labels must be a 2-D integer map")
    names = phase_names or {}
    ids = tuple(sorted(int(value) for value in np.unique(image) if value > 0))
    index = {label: position for position, label in enumerate(ids)}
    counts = np.zeros((len(ids), len(ids)), dtype=float)
    for axis in (0, 1):
        left = np.take(image, indices=range(image.shape[axis] - 1), axis=axis)
        right = np.take(image, indices=range(1, image.shape[axis]), axis=axis)
        mask = (left > 0) & (right > 0) & (left != right)
        for first, second in zip(left[mask].flat, right[mask].flat, strict=False):
            i, j = index[int(first)], index[int(second)]
            counts[i, j] += 1.0
            counts[j, i] += 1.0
    totals = counts.sum()
    normalised = np.divide(counts, totals, out=np.zeros_like(counts), where=totals > 0)
    return tuple(names.get(label, f"label-{label}") for label in ids), normalised
