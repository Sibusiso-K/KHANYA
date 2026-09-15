# 012 — S3_test_03's registered stack, three ways, looked at directly

**Status: checked by eye, at two zoom levels, against the full 3396×2547 archive.** Result:
**genuinely inconclusive, the same way `experiments/009`'s single-candidate check on this exact
section was — not a clean confirmation of SIFT+RANSAC's offset, and not a clean refutation
either.** The `S3_test_03` offset from `experiments/011-sift-ransac-registration/` is **still not
promoted to a claim**, but for a more specific reason than "not yet checked": the check was run,
and this section's texture does not resolve it by eye.

```bash
kaggle kernels push -p experiments/012-s3test03-sift-visual-check
```

Ran as `lethabomh14/reefprint-p5-sift-visual-check` (~43 min — `S3_test_03` specifically is the
section with the highest SIFT keypoint/inlier counts of the five measured, per
`experiments/011`'s own cost finding, and that dominates this kernel's runtime even for a
single-section check). Images saved under `output/` (gitignored, same convention as every other
experiment).

## What was checked

Exactly `experiments/009`'s method, extended to three candidates instead of one: the same
section, the same sample-frame indices (1, 10, 30, 60), the same red/green overlay convention
(reference in red, de-rotated frame in green — clean yellow-white reads as aligned, coloured
fringing reads as misaligned). `grid_offset = (-397.3, 40.8)` (unchanged from 007/009);
`sift_offset = (-111.1, 21.6)` (matches `experiments/011` exactly, confirming this kernel's
independent recomputation is itself deterministic).

**Full-frame overlays** (`overlay_naive.png`, `overlay_grid.png`, `overlay_sift.png`, all at
frame 30, 155° from the reference): all three read the same way `009` found the naive/grid pair
did — **substantial, broadly similar-looking yellow-green coverage across the specimen interior,
with no one candidate obviously more internally coherent than the others at a glance.** This is
not a new finding; it reproduces `009`'s own conclusion on the same section, now with a third
candidate added to the comparison and the same result.

**A zoomed, landmark-level check**, to see whether a full-frame overlay was hiding a decisive
local difference `009`'s original whole-image comparisons might have washed out. A high-texture,
border-avoiding landmark was located programmatically (local variance maximum, not chosen by eye,
to avoid picking a spot that happens to flatter one candidate) and cropped identically across
reference, naive, grid, and sift at frame 30. **None of the three conditions showed a clean,
confidently-matched landmark against the reference at this crop** — all three showed genuine
mineral texture, plausible in isolation, but not an obvious 1:1 match to the reference's specific
grain shapes. Widening to a zoomed red/green overlay at the same landmark: naive read mostly as
separated red and green with little overlap; grid and sift both showed a mix of yellow (aligned)
and orange/red fringing (misaligned) patches, with neither one uniformly better than the other at
this specific zoom.

## Why this does not settle it, and why that is itself informative

- **The self-similarity hypothesis already on record explains this well.** `experiments/010`'s
  README names it directly: "real mineral texture's self-similarity gives the correlation
  objective multiple near-tied local optima." The same self-similarity that makes the *search*
  hard to trust also makes the *visual check* hard to trust — a texture rich enough to fool a
  correlation search by eye-catching but spurious matches is, by the same token, rich enough that
  a human eye cannot always tell a genuine grain match from a coincidental one either.
- **A raw pixel-correlation re-check was tried and rejected as circular.** Computing normalized
  cross-correlation between the reference and each candidate at sampled patches gave the *grid
  search's* offset the highest score — unsurprising and uninformative, since whole-frame pixel
  correlation is *exactly* `estimate_rotation_centre`'s own optimisation objective. A metric
  cannot arbitrate between two candidates when one of them was chosen specifically to maximise
  that metric. This is not evidence for the grid search; it is a reminder that correlation-based
  re-checks of a correlation-based search prove nothing new.
- **`009`'s own visual check worked because that section had one unusually distinctive,
  easily-tracked grain** (a rectangular grain with a dark inclusion and a network of fine internal
  cracks — described in that experiment's own README). `S3_test_03`'s texture at the landmark
  checked here does not offer an equally distinctive, unambiguous feature to track by eye. This
  is a property of the *section*, not a flaw in the method transferred from 009.

## What still favours SIFT+RANSAC's offset over the grid search's, independent of this visual check

None of this depends on eyeballing a landmark:

1. **Determinism, on real data.** `experiments/011`: `S3_test_03`'s neighbours in the same run
   (`S3_test_01`) reproduced bit-for-bit across two calls. The grid search has never demonstrated
   this on real data, and `experiments/010` proved it explicitly lacks it.
2. **Cross-section consistency.** SIFT+RANSAC's `S3_test_03` offset, (−111, 22), sits inside the
   same tight band ((−91 to −107, 21–75)) the other four sections' offsets — from *both* methods
   — occupy. The grid search's own `S3_test_03` answer, (−397, 41), is the one number in the
   entire five-section, two-method table that does not fit that pattern.
3. **Harmonic-verdict agreement with the naive condition.** SIFT+RANSAC's registered stack reads
   `SECOND`, matching what the *zero-registration* naive condition on this same section already
   reads. The grid search's registered stack is the only one of the fifteen naive/grid/sift
   readings across all five sections that disagrees with its own section's naive reading in
   *kind* (`SECOND` → `FOURTH`), not just in SNR magnitude.
4. **RANSAC inlier consistency — the argument this section adds that the visual check could not.**
   `S3_test_03`'s SIFT-matched frame pairs found up to **17,074 inliers in a single frame**, every
   one of them independently required by RANSAC to be consistent with **one** rigid transform at
   under 1.5 px average residual. That is thousands of independently-matched point
   correspondences agreeing with each other, not a single whole-frame statistic that a
   self-similar texture could fool the way pixel correlation can. The grid search has no
   equivalent internal cross-check to offer against it.

## Verdict

**Not promoted to a claim.** The visual check this section owed, per `009`'s own precedent, has
now been run and does not resolve the question either way — an honest null result, not a
confirmation. The reasons to prefer SIFT+RANSAC's offset over the grid search's remain what they
were before this experiment (determinism, cross-section consistency, harmonic-verdict agreement),
now joined by the RANSAC inlier-consistency argument above, which this experiment surfaced by
looking closely at the numbers already in hand rather than by anything visual. **If `S3_test_03`'s
offset needs to be reported with more confidence than that, the next step is not another visual
check on this section — it is checking whether the same RANSAC inlier-consistency argument holds
up on a second, independently-chosen frame pair not already used in the reported estimate**, since
everything above still traces back to the same ten sampled frames `experiments/011` used.
