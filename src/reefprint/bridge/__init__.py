"""The mask/series boundary — the only seam between KHANYA and REEFPRINT.

KHANYA labels pixels. REEFPRINT measures physics. The joint question is whether the physics
separates minerals the labels confuse, and answering it does not require either codebase to
become the other.

**Why a seam and not a merge.** ``JOINT-PLAN.md`` section 5 names merging two architectures as
the largest schedule risk in the project, and it is correct: a refactor that eats September
loses the competition regardless of how clean it ends up. So the contract here is *data* — two
arrays and four strings. KHANYA can satisfy it by importing this package, or by writing an
``.npz`` and never importing REEFPRINT at all. Neither repo has to move.

**Direction of flow.** Labels in, measurements out. Nothing flows back: this package never
returns a mask, never corrects one, and never trains on one. A one-way boundary can be reasoned
about; a two-way one becomes a merge by accident.

**What the boundary is for, beyond plumbing.** Three project rules are only enforceable at a
seam, so they are enforced here rather than left to whoever calls next:

* The rotation geometry is checked on every measurement, with no flag to skip it (finding N3).
  Two mirrored guards, not one: ``measure_section`` requires an analyser series and refuses a
  stage series; ``measure_section_extinction`` requires a stage series and refuses an analyser
  series. Whichever geometry a real archive turns out to be, the wrong estimator cannot run on
  it by accident either way.
* Locality is a required field, because Rule 2 forbids splitting by section.
* Every reported anisotropy carries the noise floor it sits on, because Rule 1 plus finding N2
  make a bare median meaningless. The extinction path's equivalent is
  ``crossing_ratio_median`` — see ``bridge/extinction.py`` for why raw extinction depth is not
  the same kind of number as DOLP and must not be compared between minerals the way DOLP is.
"""

from reefprint.bridge.extinction import (
    MineralExtinctionStatistic,
    SectionExtinctionMeasurement,
    measure_section_extinction,
)
from reefprint.bridge.measure import (
    MIN_PIXELS_PER_MINERAL,
    MineralStatistic,
    SectionMeasurement,
    group_by_locality,
    measure_section,
)
from reefprint.bridge.section import (
    LabelledSection,
    LabelProvenance,
    PixelSelection,
    select_pixels,
)

__all__ = [
    "MIN_PIXELS_PER_MINERAL",
    "LabelProvenance",
    "LabelledSection",
    "MineralExtinctionStatistic",
    "MineralStatistic",
    "PixelSelection",
    "SectionExtinctionMeasurement",
    "SectionMeasurement",
    "group_by_locality",
    "measure_section",
    "measure_section_extinction",
    "select_pixels",
]
