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

# LumenStone S1 - Berezovskoe polymetallic hydrothermal Cu-Pb-Zn-Au ore.
#
# Payload is the Cu-Pb-Zn sulphides. Two deliberate calls, both metallurgically
# motivated rather than convenient:
#
#   pyrite -> reject. Pyrite depression is standard practice in Cu-Pb-Zn
#   flotation; it dilutes concentrate grade and adds smelter sulphur load.
#
#   tennantite -> deleterious. Tennantite-tetrahedrite does carry copper, so
#   calling it deleterious rather than payload is a judgement: it is the main
#   arsenic and antimony host in ores of this type, and arsenic attracts
#   concentrate penalties that in practice dominate the decision. Recording the
#   trade-off rather than hiding it - this is a grade-versus-penalty call, and a
#   different smelter contract could justify the other choice.
S1_ROLES = {
    "background": "resin",
    "chalcopyrite": "payload",
    "galena": "payload",
    "sphalerite": "payload",
    "bornite": "payload",
    "pyrite": "reject",
    "tennantite": "deleterious",
}

# LumenStone S3 - high-temperature hydrothermal ore.
#
# Copper sulphides plus Pb-Zn are payload; pyrite is the rejection target as in
# S1. Arsenopyrite is the decisive call: it is the principal arsenic host and
# arsenic in concentrate attracts smelter penalties and, increasingly, outright
# rejection, so it is deleterious rather than merely barren. At 17.5% of S3
# pixels it is also abundant, which makes it the phase a real advisor for this
# ore would care most about. Magnetite and hematite are non-sulphide oxides that
# conventional sulphide flotation does not recover.
S3_ROLES = {
    "background": "resin",
    "chalcopyrite": "payload",
    "bornite": "payload",
    "covellite": "payload",
    "galena": "payload",
    "sphalerite": "payload",
    "pyrite": "reject",
    "arsenopyrite": "deleterious",
    "tennantite": "deleterious",
    "magnetite": "oxide",
    "hematite": "oxide",
}

# Union of every mineral across the subsets we run, so `analyse` needs no subset
# argument and a mineral keeps one role wherever it appears. Chalcopyrite is
# payload in both S1 and S2, which is consistent.
LUMENSTONE_ROLES = {**S1_ROLES, **S3_ROLES, **S2_ROLES}

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
    liberation: float | None  # None means no measurable payload particles
    n_particles: int
    payload_pixels: int
    # Retained particles that contain any payload: the particles the liberation
    # figure is actually computed over. None means not measured, and the advisor
    # treats that as too few rather than as enough.
    n_payload_particles: int | None = None

    @property
    def has_payload(self) -> bool:
        return self.payload_pixels > 0


# --- Boundary-topology refinement -------------------------------------------
#
# Raw connected components are brittle: predicted liberation came out
# UNCORRELATED with true liberation (+0.128 resize, -0.079 patch) even as mean
# IoU improved, because particle identity is a topological property. Three
# distinct failure modes, each with its own repair:
#
#   speckle      isolated misclassified pixels invent tiny particles, which
#                score as perfectly liberated and inflate the index
#                -> morphological opening
#   holes        a phase predicted as background INSIDE a grain punches a hole
#                that can split one particle into two. This is not hypothetical
#                here: magnetite is predicted as background 78.3% of the time
#                (reports/magnetite_confusion_patches.json, current patches
#                checkpoint; the 92.3% this comment carried until 2026-09-15 was
#                the superseded resize baseline), so magnetite inclusions become
#                holes
#                -> binary hole filling
#
#                MEASURED 2026-09-15, and it is not mainly about magnetite: of
#                the 3,518,530 pixels hole filling adds to the ore mask, only
#                3.7% are true magnetite and 83.5% are true background - i.e.
#                enclosed resin and pore space absorbed into the particle
#                envelope. Whether that absorption is metallurgically right is
#                an open judgement, not a settled one. See
#                reports/REFINEMENT-AUDIT-2026-09-15.md and
#                `python -m src.refinement_audit`.
#   merging      genuinely separate grains that touch are read as one particle,
#                whose composition is then an average of both
#                -> marker-controlled watershed on the distance transform
#
# Applied identically to ground-truth and predicted masks. The estimator is what
# is being changed, so both sides must use it or the comparison is meaningless.

# NOT TUNED. These three integers are hand-set and no sensitivity analysis has
# been run on them, yet the refinement they parameterise is load-bearing for
# every number this project reports: on 3 of 12 S2 test sections it moves
# liberation from ~0.00 to ~0.75-0.80 (reports/refinement_audit.json). Before
# the decision-gap result is presented as a finding, perturb these and confirm
# it survives. Tracked in reports/REFINEMENT-AUDIT-2026-09-15.md §5.1.
SPECKLE_KERNEL = 3
SEED_MIN_DISTANCE = 5   # px; distance-transform peaks closer to an edge than
                        # this are noise, not particle centres
PEAK_FOOTPRINT = 9


def refine_ore_mask(binary):
    """Speckle removal then hole filling on the ore/background binary."""
    import numpy as np
    from scipy import ndimage

    try:
        import cv2
        kernel = np.ones((SPECKLE_KERNEL, SPECKLE_KERNEL), np.uint8)
        cleaned = cv2.morphologyEx(
            binary.astype(np.uint8), cv2.MORPH_OPEN, kernel
        ).astype(bool)
    except ImportError:
        cleaned = ndimage.binary_opening(binary, iterations=1)

    return ndimage.binary_fill_holes(cleaned)


def watershed_particles(binary):
    """Split touching grains via marker-controlled watershed.

    Seeds are local maxima of the Euclidean distance transform: the centre of
    each grain is further from background than the neck joining two grains, so
    two touching grains yield two seeds and the watershed line falls on the neck.
    Falls back to plain connected components if OpenCV is unavailable, so the
    venue demo cannot die on a missing import.
    """
    import numpy as np
    from scipy import ndimage

    distance = ndimage.distance_transform_edt(binary)
    peaks = (
        (distance == ndimage.maximum_filter(distance, size=PEAK_FOOTPRINT))
        & (distance > SEED_MIN_DISTANCE)
    )
    markers, count = ndimage.label(peaks)
    if count == 0:
        return ndimage.label(binary)

    try:
        import cv2
    except ImportError:
        return ndimage.label(binary)

    # cv2.watershed floods from markers over an image; the inverted distance
    # transform makes grain necks the ridges that flooding stops at.
    relief = distance.max() - distance
    relief = (255 * relief / max(relief.max(), 1e-6)).astype(np.uint8)
    relief = np.repeat(relief[:, :, None], 3, axis=2)

    markers = markers.astype(np.int32) + 1
    markers[~binary] = 1                      # background basin
    markers[binary & (markers == 1)] = 0      # unknown, to be flooded
    cv2.watershed(relief, markers)

    markers[markers <= 1] = 0                 # background and watershed lines
    return markers, int(markers.max())


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
                     min_pixels: int = MIN_PARTICLE_PIXELS,
                     refine: bool = False):
    """Share of payload area sitting in particles that are >=threshold payload.

    Returns (liberation, n_particles); see liberation_stats for the payload
    particle count as well."""
    liberation, kept, _ = liberation_stats(
        labels, payload_mask, background_index, threshold, min_pixels, refine
    )
    return liberation, kept


def liberation_stats(labels, payload_mask, background_index=0,
                     threshold: float = LIBERATION_THRESHOLD,
                     min_pixels: int = MIN_PARTICLE_PIXELS,
                     refine: bool = False):
    """Share of payload area sitting in particles that are >=threshold payload.

    Returns (liberation, n_particles, n_payload_particles). Liberation is None when there is no
    payload in a retained particle - that is "no measurement", which is a
    different statement from "zero liberation", and the advisor must not
    conflate them. Payload outside retained particles stays in the denominator
    when a measurement exists, preserving the estimator's conservative policy.
    """
    ore = labels != background_index
    if refine:
        ore = refine_ore_mask(ore)
        particles, _ = watershed_particles(ore)
    else:
        particles, _ = _connected_components(ore)
    payload_total = int(payload_mask.sum())
    if payload_total == 0:
        return None, 0, 0

    ids, counts = np.unique(particles[particles > 0], return_counts=True)
    if not len(ids):
        # Payload pixels exist but survived no particle - the morphological
        # opening can erase a thin or isolated grain entirely. Report "not
        # measurable" rather than crashing on an empty reduction, which is the
        # same distinction the advisor draws between an unmeasured field and a
        # barren one. Reachable from the dashboard on a sparse upload.
        return None, 0, 0

    payload_counts = np.bincount(
        particles[payload_mask & (particles > 0)], minlength=int(ids.max()) + 1
    )

    liberated_payload, measured_payload, kept, with_payload = 0, 0, 0, 0
    for particle_id, size in zip(ids, counts):
        if size < min_pixels:
            continue
        kept += 1
        payload_in_particle = int(payload_counts[particle_id])
        measured_payload += payload_in_particle
        with_payload += payload_in_particle > 0
        if payload_in_particle and payload_in_particle / size >= threshold:
            liberated_payload += payload_in_particle

    if measured_payload == 0:
        return None, kept, 0
    return liberated_payload / payload_total, kept, with_payload


def analyse(labels, class_names, roles=None, background_index=0,
            refine: bool = False):
    """Labelled mask (H x W of class indices) -> ModalResult."""
    labels = np.asarray(labels)
    if labels.ndim != 2 or labels.size == 0 or not np.issubdtype(labels.dtype, np.integer):
        raise ValueError("labels must be a non-empty 2-D integer mask")
    if not class_names or not 0 <= background_index < len(class_names):
        raise ValueError("class_names must include the background index")
    if labels.min() < 0 or labels.max() >= len(class_names):
        raise ValueError("labels contain a class index absent from class_names")
    roles = roles or LUMENSTONE_ROLES

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
    liberation, n_particles, n_payload_particles = liberation_stats(
        labels, payload_mask, background_index, refine=refine
    )

    return ModalResult(
        phase_fractions=phase_fractions,
        role_fractions=role_fractions,
        ore_area_fraction=(ore_total / total) if total else 0.0,
        liberation=liberation,
        n_particles=n_particles,
        payload_pixels=int(payload_mask.sum()),
        n_payload_particles=n_payload_particles,
    )
