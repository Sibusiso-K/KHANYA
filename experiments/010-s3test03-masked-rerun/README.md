# 010 — Attempted mask fix for `S3_test_03`, and a more serious finding underneath it

**Status: the mask fix did not help, and investigating why surfaced a bigger problem — the
registration search is not reproducible run to run, on real data, even with unchanged code and
unchanged input.** This is a more important result than the mask fix it was looking for.

```bash
kaggle kernels push -p experiments/010-s3test03-masked-rerun
```

Ran as `lethabomh14/reefprint-p5-masked-rerun` (~7 min).

## What was attempted

Per `experiments/009-s3test03-visual-check/`'s recommendation: build a region-of-interest mask
excluding a 20% border margin and the darkest 15% of pixels (background/resin, per CLAUDE.md's
own reflectance table), and re-run the registration search with it, to see whether excluding
border content recovers a smaller, more trustworthy offset than the −397 px one the visual check
showed did not correspond to any real change in the specimen.

## What happened instead

| | Offset (full-res, x, y) | Verdict | snr₂ | snr₄ |
|---|---|---|---:|---:|
| **Session 23** (unmasked, this exact section, this exact code) | (−397.3, 40.8) | FOURTH | 3.19 | 5.29 |
| **This run, unmasked** (same code, same section, same input) | (−49.7, 5.1)×8 → downsampled coords shown | — | — | — |
| **This run, masked** | (−248.2, 402.5) | **NEITHER** | 3.61 | 0.92 |

The masked search did not find a smaller, more trustworthy offset — it found an **even larger**
one, and the resulting verdict got *worse* (`NEITHER`, both harmonics now below threshold,
against the naive condition's clean `SECOND` at 9.35). The mask made this section's result less
informative, not more.

**But the real finding is what turned up while checking that**: the *unmasked* search, run this
session with byte-for-byte the same code and the same section, found a completely different
offset than session 23 did. This is not a small numerical wobble — one run says the true centre
sits ~397 px from the image centre, the other says ~50 px, in a different direction.

## Ruling out the obvious explanations, in order

- **Not a code change.** `git diff` against the commit that produced session 23's result shows
  the unmasked code path (`roi_mask=None`) is untouched — the same `total_correlation` closure,
  the same `_coarse_to_fine_search`, no parameter defaults changed.
- **Not a data or decode difference.** This run's *naive* condition (a completely separate
  computation, using the same decoded frame stack but never touching the search at all) matches
  session 23's naive numbers **bit-for-bit**: `snr_2 = 9.350294830486483` in both, to sixteen
  significant figures. If the JPEG decode, the archive mount, or the frame ordering had drifted
  between Kaggle runs, this number would not match exactly. It does. The raw pixel data going
  into both runs is provably identical.
- **What's left: the search itself.** With identical code and identical input, the coarse-to-fine
  grid search reached a different answer. The working hypothesis: real mineral texture is
  self-similar at the scale of individual grains, so the correlation objective this search
  climbs likely has **multiple local optima of similar height** rather than one clear peak. The
  coarse (first) pass of the grid decides which optimum the refinement stays in, and with
  near-tied candidates, which one scores marginally higher can come down to floating-point
  summation order inside `warp`'s interpolation or `corrcoef`'s reduction — order that is not
  guaranteed identical run to run under multi-threaded BLAS, even with the same inputs and code.
  `_coarse_to_fine_search`'s own `if score > best_score` has no tie-break rule for exactly this
  situation (CLAUDE.md Rule 5: *sort every set traversal, tie-break every min/max* — this
  comparison does neither).

## Consequences — this affects more than `S3_test_03`

**No specific offset value reported for any section in `experiments/007-s3v2-registration/`
should be trusted to the precision it was quoted at.** `S3_test_01/02/07/12`'s registered
harmonic *verdicts* (`SECOND`/`SECOND`/`BOTH`/`SECOND`) were not re-checked for run-to-run
stability this session and may or may not be as fragile as `S3_test_03`'s turned out to be —
that is now an open question for all four, not a settled one. The naive condition and its
harmonic verdicts are unaffected: they do not depend on the search at all.

## What this needs before P5 can be trusted further

1. **A determinism check on the search itself** — run `estimate_rotation_centre` twice on the
   same real section, same environment, and confirm the offset matches bit-for-bit. If it does
   not even on the *same* run of Kaggle, the search has a bug beyond cross-run drift.
2. **A landscape diagnostic** — plot or tabulate the coarse grid's scores at every candidate for
   one section, to see directly whether there are multiple near-tied peaks (confirming the
   hypothesis) or a single clear one (which would point at something else entirely).
3. **A tie-break rule**, once the cause is confirmed, so `_coarse_to_fine_search` never lets
   floating-point noise decide between two candidates that are genuinely close.
4. Only after that: **re-run all five sections and check which verdicts are stable.**

None of this is a small follow-up. It is a real piece of engineering work, and it is exactly the
kind of thing ADR-0004 anticipated when it made P5 a research thread "only if time exists" —
this is the point where that condition needs re-checking against how much time is actually left.
