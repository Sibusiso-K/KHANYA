# V1 cannot do what robustness.py's docstring asks, and the alternative is better

**Date:** 15 September 2026
**Evidence:** the LumenStone distribution table at
`imaging.cs.msu.ru/en/research/geology/lumenstone`, read directly 2026-09-15.
**Status:** experiment design. The V1 archive is downloaded and verified but has
not yet been opened (see §4).

---

## 1. The blocking fact: V1 has no masks

`src/robustness.py`'s docstring says:

> "For that, LumenStone V1 exists - the same samples imaged under varying real
> conditions [...] Real V1 evidence beats synthetic evidence and should replace
> this if there is time."

That plan is not executable as written. The dataset's own distribution table
states, per subset, exactly what each archive contains:

| Subset | Contents | Size |
|---|---|---|
| S1 v1 | images **+ masks** + visualizations | 535 MB |
| S2 v1 | images **+ masks** + visualizations | 242 MB |
| **V1 v1** | **images (3 variations)** - no masks | 100 MB |

`robustness.py` measures IoU against ground-truth masks. **V1 ships none**, so
it cannot be dropped into the existing harness, and "replace the synthetic
perturbations with real V1 evidence" cannot mean what it currently says.

## 2. The experiment V1 actually supports, which is stronger

V1 is 10 physical samples, each imaged 3 ways. The mineralogy is identical
across the three variations by construction - only the imaging changed. That
licenses a test that needs no ground truth at all:

**Self-consistency.** Run the pipeline on all three variations of a sample and
measure how far the outputs move. The sample did not change, so any movement is
imaging fragility, measured on real optical variation rather than on
`ImageEnhance.Brightness`.

Three levels, in increasing order of what matters:

1. **Mask agreement** - pairwise IoU between predictions on variant a, b, c of
   the same sample. Ceiling is 1.0 by construction. No masks needed: each
   prediction is the other's reference.
2. **Modal drift** - how far the reported mineral percentages move across
   variants of one sample.
3. **Recommendation stability** - does the advisor's *output* change when only
   the microscope changed? This is the one that matters, and it answers
   `robustness.py`'s own framing question verbatim: *"whether the model survives
   a different rig - which is the first question a Mintek metallurgist would ask
   before putting this in another lab."*

Level 3 is the project's thesis tested against reality: if the advice flips
because the lighting changed, the system is not deployable, and if it holds, that
is a far stronger claim than any IoU number.

**This is a better experiment than the one the docstring wanted**, and the
absence of masks is what forces it. An IoU-against-truth number on V1 would have
measured accuracy under perturbation; this measures whether the *decision* is
stable, which is what a plant actually consumes.

**Caveat to state up front:** n = 10 samples. This is a fragility probe, not a
robustness guarantee, and must be reported with the same care as the 12-section
results.

## 3. Unrelated unblock found on the same page

The S1 **v1** archive is publicly downloadable (535 MB, images + masks) from the
same table.

This reopens issue #5 ask 4. That ask was retracted as unsound because
`test_01.jpg`-`test_20.jpg` are positional filenames, so `set(v1_test) <=
set(v2_test)` establishes nothing - the only sound check is content hashing, and
that was thought to need images nobody had. **Those images are one download
away.** Hashing v1's 16 test images against v2's 20 would establish the subset
relation properly and enable the like-for-like comparison against the published
**0.8373** at zero GPU cost, which is what the ask was originally for.

Downloading for our own use is squarely inside the written grant ("free to use
the provided data in your own research work"); it is redistribution that is
unaddressed, and that question is open in
`REDISTRIBUTION-CONTRADICTION-2026-09-15.md`.

## 4. Status and what is needed

`data/raw/lumenstone/V1_v1.zip` is downloaded from the dataset's own Yandex Disk
link: **104,705,467 bytes**, sha256
`499c625ab8a3223c9f18e700bf463170010faf4badfb4f957900ab68bae95123`. That byte
count matches REEFPRINT's independently-obtained copy exactly, which is a real
cross-check of both downloads.

The archive has **not** been opened. Listing its contents was blocked twice by
the sandbox as downloaded-file provenance, which is correct behaviour on its
part. Extracting and running the pipeline over it needs that permission, since
the whole experiment is "process these downloaded images".
