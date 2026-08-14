"""Modal mineralogy and liberation from a segmentation mask.

This is the bridge between the segmentation model and the advisor, and it is
where the "operational feedback integration" deliverable actually becomes real
rather than illustrative. Two measurements come out of a labelled mask:

  1. Modal mineralogy - area fraction of each phase, as a proportion of ORE
     area, not of the image. Resin is mounting medium, not ore; including it
     would make every number a function of how densely the section was mounted.

  2. Liberation - computed by particle composition, not asserted. Grains in a
     polished section are separated by resin, so connected components of
     non-background pixels are particles. For each particle we measure what
     fraction of it is the payload phase; a particle counts as liberated when
     that fraction clears LIBERATION_THRESHOLD. The reported liberation index
     is the share of total payload area sitting in liberated particles - i.e.
     mass-weighted, so one large locked grain matters more than several small
     free ones.

Stereological caveat, stated because it is a real limitation and a fair
question: this is a 2D section through 3D particles, so apparent liberation
from sections is biased HIGH relative to true volumetric liberation - a plane
can cut through the free-standing rim of a particle whose core is locked. Real
plant practice applies a stereological correction. We do not, so our liberation
index is an upper bound and must be reported as such.
"""
from dataclasses import dataclass

import numpy as np

# Metallurgical role per mineral, keyed by phase set. The advisor reasons over
# ROLES, not mineral names, so the same operational logic serves S2 today and
# the REEFPRINT phase set if Mintek releases data - swap the mapping, not the
# decision logic.
#
# payload      - carries the economic value; recovery of this is the objective
# gangue       - barren host, dilutes concentrate
# oxide        - not recovered by sulphide flotation; grinding/energy relevance
# reject       - floats readily but dilutes grade; the target of active rejection
# deleterious  - actively degrades flotation performance
#
# On S2, pyrrhotite is deliberately NOT payload. In magmatic Ni-Cu sulphide
# processing the value sits in pentlandite (Ni) and chalcopyrite (Cu), while
# pyrrhotite is the standard rejection target - it dilutes concentrate grade and
# drives smelter sulphur load, and "pyrrhotite rejection" is an established
# operating lever at Sudbury and on Norilsk ores. Caveat worth stating rather
# than hiding: pyrrhotite does carry some Ni and PGE in solid solution, so
# rejecting it is a grade-versus-recovery trade-off, not free money.
#
# Calling all three sulphides "payload" was the first thing tried, and it made
# liberation saturate at ~1.0 on every test section - in massive sulphide the
# payload IS the rock, so every particle trivially clears the threshold. That
# result is recorded in the research report as a real finding about what this
# measurement can and cannot discriminate, not quietly dropped.
S2_ROLES = {
    "background": "resin",
    "chalcopyrite": "payload",
    "pentlandite": "payload",
    "pyrrhotite": "reject",
    "magnetite": "oxide",
}

REEFPRINT_ROLES = {
    "Chromite": "oxide",
    "Orthopyroxene": "gangue",
    "Plagioclase": "gangue",
    "Base_Metal_Sulphide": "payload",
    "Talc_Serpentine": "deleterious",
}

# A particle is liberated when the payload occupies at least this fraction of
# it. 0.50 is the same figure the advisor uses as its liberation floor and
# carries the same sourcing: composite-particle recovery in conventional
# flotation drops considerably below ~50% exposure (911 Metallurgist, "Grinding
# for Liberation and Flotation").
LIBERATION_THRESHOLD = 0.50

# Particles smaller than this are dropped before liberation is computed. At
# a few pixels, a "particle" is as likely to be mask noise or a boundary
# artefact as a grain, and singletons would otherwise score as perfectly
# liberated and inflate the index.
MIN_PARTICLE_PIXELS = 64


@dataclass
class ModalResult:
    phase_fractions: dict      # mineral -> area fraction OF ORE (sums to ~1.0)
    role_fractions: dict       # role -> area fraction of ore
    ore_area_fraction: float   # ore / (ore + resin); mounting density, not grade
    liberation: float          # mass-weighted, upper bound - see module docstring
    n_particles: int
    payload_pixels: int

    @property
    def has_payload(self) -> bool:
        return self.payload_pixels > 0


def _connected_components(binary):
    """Label 4-connected components. Uses scipy when present (it ships with
    scikit-learn, already a dependency) and falls back to a union-find pass so
    the demo cannot die on a missing import at the venue."""
    try:
        from scipy import ndimage
        labelled, count = ndimage.label(binary)
        return labelled, count
    except ImportError:
        pass

    height, width = binary.shape
    labels = np.zeros((height, width), dtype=np.int32)
    parent = [0]

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    for y in range(height):
        for x in range(width):
            if not binary[y, x]:
                continue
            up = labels[y - 1, x] if y else 0
            left = labels[y, x - 1] if x else 0
            if up and left:
                labels[y, x] = min(up, left)
                union(up, left)
            elif up or left:
                labels[y, x] = up or left
            else:
                parent.append(len(parent))
                labels[y, x] = len(parent) - 1

    remap, count = {}, 0
    for y in range(height):
        for x in range(width):
            if labels[y, x]:
                root = find(labels[y, x])
                if root not in remap:
                    count += 1
                    remap[root] = count
                labels[y, x] = remap[root]
    return labels, count


def liberation_index(labels, payload_mask, background_index=0,
                     threshold: float = LIBERATION_THRESHOLD,
                     min_pixels: int = MIN_PARTICLE_PIXELS):
    """Share of payload area sitting in particles that are >=threshold payload.

    Returns (liberation, n_particles). Liberation is None when there is no
    payload in the field - that is "no measurement", which is a different
    statement from "zero liberation", and the advisor must not conflate them.
    """
    particles, _ = _connected_components(labels != background_index)
    payload_total = int(payload_mask.sum())
    if payload_total == 0:
        return None, 0

    ids, counts = np.unique(particles[particles > 0], return_counts=True)
    payload_counts = np.bincount(
        particles[payload_mask & (particles > 0)], minlength=int(ids.max()) + 1
    )

    liberated_payload, kept = 0, 0
    for particle_id, size in zip(ids, counts):
        if size < min_pixels:
            continue
        kept += 1
        payload_in_particle = int(payload_counts[particle_id])
        if payload_in_particle and payload_in_particle / size >= threshold:
            liberated_payload += payload_in_particle

    return liberated_payload / payload_total, kept


def analyse(labels, class_names, roles=None, background_index=0):
    """Labelled mask (H x W of class indices) -> ModalResult."""
    labels = np.asarray(labels)
    roles = roles or S2_ROLES

    counts = np.bincount(labels.ravel(), minlength=len(class_names))
    total = int(counts.sum())
    ore_total = total - int(counts[background_index])

    phase_fractions, role_fractions = {}, {}
    for index, name in enumerate(class_names):
        if index == background_index:
            continue
        fraction = counts[index] / ore_total if ore_total else 0.0
        phase_fractions[name] = float(fraction)
        role = roles.get(name, "gangue")
        role_fractions[role] = role_fractions.get(role, 0.0) + float(fraction)

    payload_indices = [
        i for i, name in enumerate(class_names) if roles.get(name) == "payload"
    ]
    payload_mask = np.isin(labels, payload_indices)
    liberation, n_particles = liberation_index(
        labels, payload_mask, background_index
    )

    return ModalResult(
        phase_fractions=phase_fractions,
        role_fractions=role_fractions,
        ore_area_fraction=(ore_total / total) if total else 0.0,
        liberation=liberation,
        n_particles=n_particles,
        payload_pixels=int(payload_mask.sum()),
    )
