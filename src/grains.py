"""Grain-level mineralogy from a predicted phase map: what a metallurgist reads.

The advisor needs one number (the association index). A professional wants to
look inside it: each grain's composition, estimated weight percent, which
minerals touch which, and liberation by grain size. Everything here is computed
from the same predicted mask and the SAME particle split as src/modal.py
(refined ore mask, watershed, particles of at least MIN_PARTICLE_PIXELS), so the
grain list always agrees with the counts on the result screen.

Units. Sizes are in pixels unless MICRONS_PER_PIXEL is set. The LumenStone
dataset page and its paper give the magnification (x50) and image size
(3396 x 2547 px) but no pixel size, so no micron value is assumed here.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

import numpy as np

from . import modal

# Set KHANYA_MICRONS_PER_PIXEL once the imaging scale is confirmed; until then
# every size is reported in pixels and labelled as such.
_scale = os.environ.get("KHANYA_MICRONS_PER_PIXEL")
MICRONS_PER_PIXEL = float(_scale) if _scale else None

# Typical measured densities, g/cm3: midpoints of the ranges on mindat.org
# (chalcopyrite 4.1-4.3, pentlandite 4.6-5.0, pyrrhotite 4.58-4.65,
# magnetite 5.17-5.18). Weight percent = area percent x density, normalised.
# Area fraction estimates volume fraction on a random section (Delesse), so
# this is an estimate, not an assay.
DENSITY_G_CM3 = {"chalcopyrite": 4.2, "pentlandite": 4.8, "pyrrhotite": 4.61, "magnetite": 5.175}

# Size classes by equivalent circle diameter, in pixels (doubling bins).
SIZE_EDGES_PX = (0, 16, 32, 64, 128, 256, float("inf"))


@dataclass
class Grain:
    id: int
    area_px: int
    ecd_px: float
    phases: dict  # phase name -> share of the grain's classified pixels
    payload_fraction: float
    liberated: bool
    bbox: tuple  # (x0, y0, x1, y1)

    def as_dict(self):
        return {"id": self.id, "area_px": self.area_px, "ecd_px": round(self.ecd_px, 1),
                "phases": {k: round(v, 4) for k, v in self.phases.items()},
                "payload_fraction": round(self.payload_fraction, 4),
                "liberated": self.liberated, "bbox": list(self.bbox)}


@dataclass
class GrainReport:
    grain_map: np.ndarray            # int32, 0 = not a kept grain
    grains: list = field(default_factory=list)
    weight_percent: dict = field(default_factory=dict)   # phase -> % of ore
    association: dict = field(default_factory=dict)      # phase -> {neighbour -> % of its boundary}
    liberation_by_size: list = field(default_factory=list)
    microns_per_pixel: float | None = None

    @property
    def n_grains(self):
        return len(self.grains)

    @property
    def n_payload_grains(self):
        return sum(g.payload_fraction > 0 for g in self.grains)


def _roles(roles):
    return roles or modal.LUMENSTONE_ROLES


def particle_map(labels, background_index=0, refine=True, min_pixels=modal.MIN_PARTICLE_PIXELS):
    """The advisor's particle split, with particles below min_pixels removed."""
    ore = labels != background_index
    if refine:
        ore = modal.refine_ore_mask(ore)
        particles, _ = modal.watershed_particles(ore)
    else:
        particles, _ = modal._connected_components(ore)
    particles = np.asarray(particles, dtype=np.int32)
    ids, counts = np.unique(particles[particles > 0], return_counts=True)
    small = ids[counts < min_pixels]
    if len(small):
        particles[np.isin(particles, small)] = 0
    return particles


def weight_percent(phase_fractions, densities=DENSITY_G_CM3):
    """Estimated weight percent of the ore phases that have a known density."""
    mass = {p: phase_fractions.get(p, 0.0) * d for p, d in densities.items()}
    total = sum(mass.values())
    return {p: (100.0 * m / total if total else 0.0) for p, m in mass.items()}


def association(labels, class_names, background_index=0):
    """Share of each phase's boundary shared with each neighbour, 4-connected.

    "resin" is the free surface (contact with background). This is the
    mineral-association view a QEMSCAN report gives, measured on the predicted map.
    """
    n = len(class_names)
    counts = np.zeros((n, n), dtype=np.int64)
    for a, b in ((labels[:, :-1], labels[:, 1:]), (labels[:-1, :], labels[1:, :])):
        edge = a != b
        np.add.at(counts, (a[edge], b[edge]), 1)
        np.add.at(counts, (b[edge], a[edge]), 1)
    result = {}
    for i, name in enumerate(class_names):
        if i == background_index:
            continue
        total = counts[i].sum()
        if not total:
            continue
        result[name] = {("resin" if j == background_index else class_names[j]): round(float(100.0 * counts[i, j] / total), 1)
                        for j in range(n) if j != i and counts[i, j]}
    return result


def grain_report(labels, class_names, roles=None, background_index=0, refine=True,
                 microns_per_pixel=None, phase_fractions=None):
    """phase_fractions: pass result.phase_fractions from modal.analyse when the
    caller already has it, so the (slow) analysis is not run twice."""
    labels = np.asarray(labels).astype(np.int64)
    roles = _roles(roles)
    grain_map = particle_map(labels, background_index, refine)
    n_classes = len(class_names)
    payload = np.array([roles.get(name) == "payload" for name in class_names])
    ids = np.unique(grain_map[grain_map > 0])
    grains = []
    if len(ids):
        # per-grain phase pixel counts in one pass
        flat = grain_map.ravel().astype(np.int64) * n_classes + labels.ravel()
        table = np.bincount(flat, minlength=(int(ids.max()) + 1) * n_classes).reshape(-1, n_classes)
        ys, xs = np.nonzero(grain_map)
        owner = grain_map[ys, xs]
        order = np.argsort(owner, kind="stable")
        owner, ys, xs = owner[order], ys[order], xs[order]
        starts = np.searchsorted(owner, ids)
        ends = np.searchsorted(owner, ids, side="right")
        for gid, s, e in zip(ids, starts, ends):
            row = table[gid].astype(float)
            row[background_index] = 0.0
            area = int(e - s)
            classified = row.sum()
            phases = {class_names[j]: float(row[j] / classified) for j in range(n_classes)
                      if j != background_index and row[j] > 0} if classified else {}
            payload_px = row[payload].sum()
            fraction = payload_px / area if area else 0.0
            grains.append(Grain(
                id=int(gid), area_px=area, ecd_px=float(2.0 * np.sqrt(area / np.pi)),
                phases=phases, payload_fraction=float(fraction),
                liberated=bool(payload_px and fraction >= modal.LIBERATION_THRESHOLD),
                bbox=(int(xs[s:e].min()), int(ys[s:e].min()), int(xs[s:e].max()), int(ys[s:e].max())),
            ))
    if phase_fractions is None:
        phase_fractions = modal.analyse(labels, class_names, roles=roles,
                                        background_index=background_index, refine=refine).phase_fractions
    by_size = []
    for lo, hi in zip(SIZE_EDGES_PX[:-1], SIZE_EDGES_PX[1:]):
        members = [g for g in grains if lo <= g.ecd_px < hi and g.payload_fraction > 0]
        payload_area = sum(g.payload_fraction * g.area_px for g in members)
        freed = sum(g.payload_fraction * g.area_px for g in members if g.liberated)
        by_size.append({"from_px": lo, "to_px": None if hi == float("inf") else hi,
                        "payload_grains": len(members),
                        "payload_area_px": int(round(payload_area)),
                        "liberated_share": (round(freed / payload_area, 4) if payload_area else None)})
    return GrainReport(
        grain_map=grain_map, grains=grains,
        weight_percent=weight_percent(phase_fractions),
        association=association(labels, class_names, background_index),
        liberation_by_size=by_size,
        microns_per_pixel=microns_per_pixel if microns_per_pixel is not None else MICRONS_PER_PIXEL,
    )
