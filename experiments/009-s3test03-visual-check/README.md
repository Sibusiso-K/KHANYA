# 009 — S3_test_03's registered stack, looked at directly

**Status: checked by eye, at two independent angles. The verdict: the found offset looks
suspect, not confirmed.** This closes the second item in `experiments/007-s3v2-registration/
README.md`'s *Left open* list — with a result that argues against trusting `S3_test_03`'s
`FOURTH` (stage) verdict as it stands.

```bash
kaggle kernels push -p experiments/009-s3test03-visual-check
```

Ran as `lethabomh14/reefprint-p5-visual-check` (~3.5 min, one section, full resolution). Images
saved under `output/` (gitignored, same convention as every other experiment) — described here
so the finding is recorded even though the pictures themselves are not committed.

## What was checked

`S3_test_03`'s registration search found an offset of **(-397.3, +40.8) px** on a 2547×3396
frame — the largest of the five sections experiment 007 measured, and the one whose harmonic
verdict flipped from `SECOND` (analyser) under naive de-rotation to `FOURTH` (stage) under this
offset. A −397 px shift is about 12% of the frame's width: large enough that if it is real, a
prominent grain should sit visibly closer to the reference frame's version of itself after
*proper* registration than after the naive (image-centre) one.

This experiment de-rotates frame 30 (155° from the reference) and frame 60 (305° from the
reference) both ways — naively, about the image centre, and "registered", about the estimated
centre — and saves both next to the untouched reference frame, so the two corrections can be
compared directly against the same real grain rather than against each other's numbers.

## What the images show

**A single, distinctive, easily-tracked grain** — roughly rectangular, with a dark inclusion
near its top edge and a network of fine internal cracks — sits in almost exactly the same
position, at almost exactly the same size and orientation, in:

- the untouched reference frame,
- the **naive** de-rotation of frame 30 (155°),
- the **registered** de-rotation of frame 30,
- the **naive** de-rotation of frame 60 (305°), and
- the **registered** de-rotation of frame 60.

**At both angular separations, the naive and registered versions are visually indistinguishable
from each other for this grain.** If the true rotation axis really sat 397 pixels from the image
centre, the naive (image-centre) de-rotation should show this grain displaced by a large,
visible amount relative to the registered one — a whole grain-width or more, at this offset
relative to typical grain sizes on the section. It does not. The overlay images
(`overlay_naive.png` vs `overlay_registered.png`) tell the same story more diffusely: both show
substantial, similar-looking yellow (well-aligned) coverage across the section's interior, with
the registered overlay's boundary shifted in position but not obviously *more* internally
coherent than the naive one.

## Conclusion

**The visual evidence does not support trusting `S3_test_03`'s registered offset, or the
`FOURTH` (stage) verdict that followed from it, as currently computed.** The search's own
numbers are consistent with this: `S3_test_03`'s relative score improvement (naive 16.10 →
registered 21.60, ×1.34) is one of the *smaller* improvements among the five sections measured
— smaller than `S3_test_07`'s ×2.49 or `S3_test_02`'s ×1.92 — despite having by far the largest
absolute offset. A large offset paired with a modest score gain, and a dominant grain that looks
equally well-aligned either way, is the profile of a search that converged on structure elsewhere
in the frame (background texture, a resin boundary, JPEG artefacts) rather than the specimen's
true rotation axis.

**Recommendation: do not report `S3_test_03` as `FOURTH`/stage in any current form.** The
per-section table in `experiments/007-s3v2-registration/README.md` should carry a note pointing
here rather than presenting that row as settled. `S3_test_01`, `02`, `07` and `12`'s registered
verdicts are not affected by this finding — this check is specific to `S3_test_03`.

## What would actually resolve it

- **Re-run the search with a smaller `search_radius`** (e.g. 100 px instead of 40 px pre-scaling,
  i.e. cap the full-resolution search well under 397 px) and see whether a smaller, genuine
  offset is found instead, or whether the search still reaches for the same large one — the
  latter would at least rule out "search radius too generous" as the explanation.
- **Mask out the frame border and any resin/background region before scoring**, so the objective
  cannot be won by aligning non-specimen content.
- **Compare against a second grain, not just the one used here**, to rule out a coincidence where
  one particular grain happens to look aligned in both conditions by chance.
