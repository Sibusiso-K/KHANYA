# 007 — Leg (b), for real: registering S3 v2 and re-running the harmonic check

**Status: run on the real archive, on Kaggle, 2026-09-12/13. A genuine, mixed result — not a
clean verdict, and not yet a claim for the talk. Read *What this does not yet mean* before
quoting a number from this page.**

```bash
kaggle kernels push -p experiments/007-s3v2-registration
```

Ran as Kaggle kernel `lethabomh14/reefprint-p5-registration`, mounting the private
`lethabomh14/lumenstone-s3-v2-reefprint` (the real 5.2 GB `S3_v2.zip`, auto-extracted) and
`lethabomh14/reefprint-code` (this repo's `src/` and `experiments/002`–`007`) datasets. Not run
locally — a full section's frame stack needs ~5 GB once constructed
(`experiments/003-s3v2-extinction/`'s own docstring), and this project's local machine does not
reliably have that free (155 MB free of 8 GB, checked before routing this to Kaggle).

## What it does

For each section: load the real frame stack and its nominal per-frame angles (from filenames,
never estimated). Build two versions of the stack — **naive** (every frame de-rotated about the
*image centre* by its nominal angle: a coarse, approximate registration, not zero registration)
and **registered** (de-rotated about the *centre estimated* by
`reefprint.acquire.registration.estimate_rotation_centre`, a coarse-to-fine correlation search
validated on synthetic data with a known answer — `tests/test_registration.py`). Both are
restricted to the region `inscribed_region_mask` guarantees is real content in every frame, then
run through `reefprint.polarim.geometry.harmonic_signature`.

## Result — 5 sections measured, 7 skipped

| Section | Frames | Naive verdict | naive snr₂ / snr₄ | Registered verdict | reg. snr₂ / snr₄ | Offset (px, x,y) |
|---|---:|---|---:|---|---:|---|
| S3_test_01 | 71 | SECOND (analyser) | 12.54 / 4.44 | SECOND (analyser) | 11.67 / 4.83 | (−100.9, 31.6) |
| S3_test_02 | 72 | SECOND (analyser) | 11.18 / 3.54 | **BOTH (mixed)** | 11.29 / **5.56** | (−106.8, 23.5) |
| S3_test_03 | 72 | SECOND (analyser) | 9.35 / 2.78 | ~~FOURTH (stage)~~ ⚠️ see below | 3.19 / 5.29 | (−397.3, 40.8) |
| S3_test_07 | 24 | SECOND (analyser) | 6.89 / 2.09 | SECOND (analyser) | 5.97 / 2.49 | (−94.7, 72.1) |
| S3_test_12 | 24 | SECOND (analyser) | 7.11 / 2.68 | SECOND (analyser) | 6.14 / 2.48 | (−91.6, 64.0) |

`DETECTION_SNR = 5.0` throughout (the same declared threshold `experiments/002` uses). Skipped:
`S3_test_04` (one frame transposed relative to its mask — the known, isolated defect from session
16f), `S3_test_05/06/08/09/10/11` (0 rotation frames — static images, matching Sibusiso's earlier
finding that roughly 29 of 47 sections carry no rotation series at all).

Registration **found a real, non-trivial offset in every section it ran on** (`search_score >
search_score_at_zero_offset` in all 5 cases) — the offsets range from ~95 to ~400 pixels, on
2547×3396 frames, so 3–15% of the frame's width. None of these are small.

## The finding this session did not expect, and has not fully explained

**The "naive" condition — merely de-rotating each frame about the *image* centre, not the
estimated true one — already clears `DETECTION_SNR` for `snr_2` on all 5 measurable sections.**
That is a sharp break from the earlier N3 measurements (session 16d/17), which found `NEITHER`
on **every** section tried, on the same archive, using the same `harmonic_signature` estimator.

**Confirmed, 2026-09-13 — `experiments/008-n3-original-method-rerun/`.** N3's original,
unmodified method (`experiments/002-s3v2-geometry/run.py::read_section`, scattered pixel
positions from the raw, undecoded-and-unrotated frames — genuinely **zero** registration)
returns `NEITHER` on all 5 of these same sections, with every `snr_2` under 5.0 (1.78–4.43). This
script's "naive" condition already applies a coarse rotation correction (about the wrong centre,
but a rotation correction nonetheless) before sampling, and that is the entire difference: **any
sensible de-rotation recovers real per-pixel structure that zero registration cannot see at
all**, which is direct evidence *for* the project's registration thesis, not a contradiction of
N3's original finding. Full comparison table: `experiments/008-n3-original-method-rerun/
README.md`.

**The verdict is not uniform across sections, and two of five change under proper registration**:
`S3_test_02` gains a real `snr_4` (3.54 → 5.56) alongside its already-present `snr_2`, moving it
from a clean `SECOND` to `BOTH` — impure or mixed. `S3_test_03` **flips entirely**: its `snr_2`
collapses (9.35 → 3.19) while its `snr_4` clears threshold for the first time (2.78 → 5.29) —
proper registration turns what looked like a rotating-analyser section into what reads as a
stage rotation. CLAUDE.md's own geometry-experiment README already anticipated this outcome in
the abstract: *"the acquisition protocol should be constant across a dataset, so a split verdict
is itself a finding."*

**`S3_test_03`'s flip does NOT survive a visual check — checked 2026-09-13,
`experiments/009-s3test03-visual-check/`.** A single distinctive grain, tracked at two
independent angular separations (155° and 305° from the reference), sits in almost exactly the
same position under the **naive** (image-centre) and **registered** (−397 px offset)
de-rotations alike — the two are visually indistinguishable for this feature. A real 397-pixel
axis offset (≈12% of the frame's width) should displace that grain by a large, visible amount
between the two conditions; it does not. `S3_test_03`'s relative score improvement (×1.34) is
also one of the smaller of the five sections despite having the largest absolute offset — a
large offset with a modest score gain and no visible improvement is the profile of a search
that converged on structure elsewhere in the frame, not the specimen's true rotation axis.
**Do not report `S3_test_03` as `FOURTH`/stage.** `S3_test_01/02/07/12` are unaffected by this.

## What this does NOT yet mean

- **It does not close N3.** N3 asked whether S3 v2 is a stage or analyser archive; the *naive*
  vs zero-registration comparison is confirmed (above), but this result on its own says the
  archive's answer may not be single-valued across sections at all, which is a different,
  larger question the project has not previously had reason to ask.
- **It does not validate the registration estimator on real data**, only on synthetic data with a
  known answer (`tests/test_registration.py`). The found offsets are large and plausible for a
  loosely-mounted stage, but nothing here proves they are the *true* physical offsets rather than
  a spurious correlation-maximum the search converged to — a systematic check (does the found
  offset vary smoothly and continuously as frames are added or removed, the way a real physical
  constant should, rather than jumping around) has not been run.
- **It does not mean leg (b) is closed.** Five sections is a small, convenience sample driven by
  which sections happen to carry a full rotation series and a matching mask shape — not a
  claim about the other 42.
- **`S3_test_03`'s flip did not survive a visual check** (`experiments/009-s3test03-visual-check/`)
  — treat that row as unresolved, not as a finding, until a masked/tighter-radius re-run either
  confirms a smaller genuine offset or drops it back to `SECOND`.

## Left open, in priority order

1. ✅ **Done** — `experiments/008-n3-original-method-rerun/` confirmed the naive-condition
   discrepancy is a registration-methodology difference, not a bug.
2. ✅ **Done** — `experiments/009-s3test03-visual-check/` checked `S3_test_03`'s registered
   stack by eye at two angles; the found offset does not look like a genuine correction. See
   that experiment's *What would actually resolve it* for the follow-up (masked scoring, a
   tighter search radius, a second grain).
3. Widen from 5 to the full ~18 sections that do carry a rotation series, once 1–2 are resolved.
4. Map the mask through the same registration transform and re-run the per-mineral anisotropy
   bridge (`reefprint.bridge`) on a section that reads clean `SECOND`, to see whether the
   pentlandite/pyrrhotite split actually appears — the measurement the whole project is for.
