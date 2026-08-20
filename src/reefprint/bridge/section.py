"""What a labelled polished section is, on the wire between two codebases.

Deliberately thin. This module holds no model, no segmentation, and no mineralogical hypothesis
— in particular it does not know which minerals are cubic. That table is the thing under test,
so it belongs to the experiment making the claim, never to the plumbing carrying the data.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Mapping

    import numpy.typing as npt

    IntArray = npt.NDArray[np.integer]

__all__ = [
    "LabelProvenance",
    "LabelledSection",
    "PixelSelection",
    "select_pixels",
]

#: (height, width). A 1-D label array is a pixel list that has lost its geometry.
_LABEL_NDIM = 2


class LabelProvenance(StrEnum):
    """Where the labels came from. Required, because the two cannot be pooled.

    :data:`GROUND_TRUTH` — hand-drawn masks shipped with a public dataset. The measurement is
    then a statement about minerals.

    :data:`PREDICTED` — a segmentation model's output. The measurement inherits every error the
    model makes, and KHANYA's model confuses pentlandite for pyrrhotite 29.2% of the time. A
    number computed over predicted labels is a statement about *the model's idea of* minerals,
    which is a different and much weaker claim.

    Mixing the two silently averages a physics result with a model result. There is no honest
    interpretation of the mixture, which is why :func:`~reefprint.bridge.measure.group_by_locality`
    refuses it rather than warning about it.
    """

    GROUND_TRUTH = "hand-drawn ground-truth mask"
    PREDICTED = "segmentation model output"


@dataclass(frozen=True, slots=True)
class LabelledSection:
    """A per-pixel mineral label map, with the provenance needed to interpret it.

    Attributes:
        labels: Shape ``(height, width)``. Integer code per pixel.
        codebook: Code to mineral name. **Authoritative**: a code absent from it is treated as
            unlabelled and excluded from every statistic, and the excluded count is reported so
            the exclusion is visible rather than inferred. Resin and background belong here
            under their own names if they are to be measured, and absent if they are not.
        section_id: Identifies the physical section, e.g. ``"S3_train_33"``.
        locality: The geological locality the section came from, e.g. ``"Norilsk"``. **Required
            and never defaulted.** Rule 2 forbids splitting by section or patch, so a container
            that allowed locality to be forgotten would make every downstream conformal claim
            void without anything failing. It is cheap to carry and impossible to reconstruct.
        provenance: Ground truth or model output. See :class:`LabelProvenance`.
    """

    labels: IntArray
    codebook: Mapping[int, str]
    section_id: str
    locality: str
    provenance: LabelProvenance

    def __post_init__(self) -> None:
        labels = np.asarray(self.labels)
        if labels.ndim != _LABEL_NDIM:
            msg = f"labels must be (height, width), got shape {labels.shape}"
            raise ValueError(msg)
        if not np.issubdtype(labels.dtype, np.integer):
            msg = f"labels must be an integer dtype, got {labels.dtype}"
            raise TypeError(msg)
        if not self.locality:
            msg = (
                f"section {self.section_id!r} has no locality. Rule 2: splits are by locality, "
                f"never by section or patch, so a section without one cannot be held out."
            )
            raise ValueError(msg)
        object.__setattr__(self, "labels", labels)
        object.__setattr__(self, "codebook", MappingProxyType(dict(self.codebook)))

    @property
    def shape(self) -> tuple[int, int]:
        """Pixel grid, ``(height, width)``."""
        return (int(self.labels.shape[0]), int(self.labels.shape[1]))

    @property
    def n_pixels(self) -> int:
        return int(self.labels.size)

    def mineral_mask(self, name: str) -> npt.NDArray[np.bool_]:
        """Boolean mask for one mineral, by name.

        Raises:
            KeyError: The name is not in the codebook. A typo that silently returned an
                all-false mask would read as "this mineral is absent from the section".
        """
        codes = [code for code, mineral in self.codebook.items() if mineral == name]
        if not codes:
            msg = f"{name!r} is not in the codebook of {self.section_id!r}: {sorted(set(self.codebook.values()))}"
            raise KeyError(msg)
        mask = np.zeros(self.shape, dtype=bool)
        for code in codes:
            mask |= self.labels == code
        return mask

    def pixel_counts(self) -> dict[str, int]:
        """Labelled pixels per mineral name, omitting minerals with none present."""
        counts: dict[str, int] = {}
        present, totals = np.unique(self.labels, return_counts=True)
        for code, total in zip(present.tolist(), totals.tolist(), strict=True):
            name = self.codebook.get(int(code))
            if name is not None:
                counts[name] = counts.get(name, 0) + int(total)
        return counts

    @property
    def n_unlabelled(self) -> int:
        """Pixels whose code is absent from the codebook, and so excluded from measurement."""
        return self.n_pixels - sum(self.pixel_counts().values())


@dataclass(frozen=True, slots=True)
class PixelSelection:
    """Positions chosen from a mask, before a single frame has been decoded.

    The reason this type exists is memory. One LumenStone S3 section is 3396x2547 over 72
    rotation frames — 5.0 GB held as float64, which no laptop in this project will do, and the
    demo has to run on one laptop. But the *positions* worth measuring are decided by the mask
    alone, which is 8.6 MB. So: choose positions, then decode each frame once, read those
    positions out of it, and discard the frame. Peak memory becomes one frame.

    Attributes:
        ys: Row index of each selected pixel, shape ``(n,)``.
        xs: Column index of each selected pixel, shape ``(n,)``.
        section: The selected pixels as a ``(1, n)`` :class:`LabelledSection`, carrying the
            original's identity and codebook. Pass this to
            :func:`~reefprint.bridge.measure.measure_section` — the compact form is a section
            like any other, so there is one measurement path rather than two.
    """

    ys: IntArray
    xs: IntArray
    section: LabelledSection

    def __post_init__(self) -> None:
        if self.ys.shape != self.xs.shape:
            msg = f"ys {self.ys.shape} and xs {self.xs.shape} must match"
            raise ValueError(msg)
        if self.section.labels.shape != (1, self.ys.size):
            msg = (
                f"section labels {self.section.labels.shape} must be (1, {self.ys.size}) to "
                f"match the selected positions"
            )
            raise ValueError(msg)

    @property
    def n_pixels(self) -> int:
        return int(self.ys.size)

    def read_from(self, frame: npt.NDArray[np.number]) -> npt.NDArray[np.number]:
        """Pull the selected pixels out of one decoded frame, in selection order.

        Raises:
            ValueError: The frame's shape does not contain the selected positions. Reading past
                the edge of a transposed frame is exactly the crash this boundary exists to turn
                into a reported skip; here it is a caller error, because the frame arrived
                without the series that would have carried its shape.
        """
        height, width = frame.shape[:2]
        if self.ys.max(initial=-1) >= height or self.xs.max(initial=-1) >= width:
            msg = (
                f"selection spans {int(self.ys.max(initial=0)) + 1}x"
                f"{int(self.xs.max(initial=0)) + 1} but the frame is {height}x{width} — the "
                f"mask and the frames disagree, quite possibly transposed"
            )
            raise ValueError(msg)
        return frame[self.ys, self.xs]


def select_pixels(
    section: LabelledSection,
    *,
    max_per_mineral: int = 1200,
    min_per_mineral: int = 500,
    rng: np.random.Generator | None = None,
) -> PixelSelection | None:
    """Sample up to ``max_per_mineral`` labelled pixels of each mineral present.

    Sampling is per mineral rather than uniform over the section, because the quantity wanted is
    each mineral's own anisotropy distribution and modal abundance varies by orders of magnitude
    — a uniform sample of a chromitite is a sample of chromite. This makes the result a set of
    per-class distributions, and explicitly **not** an estimate of modal mineralogy. Anything
    needing modal proportions must count the mask, not this.

    Args:
        section: The labelled section to sample from.
        max_per_mineral: Cap per mineral. The statistics reported are medians and quartiles, so
            the return is in distribution shape rather than in n, and 1200 is far past where
            that stops improving.
        min_per_mineral: Minerals with fewer labelled pixels than this are dropped entirely
            rather than sampled thinly. A quartile over 40 pixels is not a quartile.
        rng: Seeded generator. Pass one; a default-seeded run is not reproducible and Rule 8
            wants failures to be re-runnable.

    Returns:
        The selection, or ``None`` if no mineral cleared ``min_per_mineral`` — an empty section
        is a normal outcome for a public archive, not an error.
    """
    generator = np.random.default_rng() if rng is None else rng
    chosen_ys: list[IntArray] = []
    chosen_xs: list[IntArray] = []
    chosen_codes: list[IntArray] = []

    for code in sorted(np.unique(section.labels).tolist()):
        if int(code) not in section.codebook:
            continue
        ys, xs = np.nonzero(section.labels == code)
        if ys.size < min_per_mineral:
            continue
        take = min(max_per_mineral, ys.size)
        picked = generator.choice(ys.size, size=take, replace=False)
        chosen_ys.append(ys[picked])
        chosen_xs.append(xs[picked])
        chosen_codes.append(np.full(take, int(code), dtype=np.int64))

    if not chosen_ys:
        return None

    ys = np.concatenate(chosen_ys)
    xs = np.concatenate(chosen_xs)
    codes = np.concatenate(chosen_codes).reshape(1, -1)
    compact = LabelledSection(
        labels=codes,
        codebook=section.codebook,
        section_id=section.section_id,
        locality=section.locality,
        provenance=section.provenance,
    )
    return PixelSelection(ys=ys, xs=xs, section=compact)
