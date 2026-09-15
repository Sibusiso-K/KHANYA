# 011 — SIFT+RANSAC vs the grid search, on the same five real S3 v2 sections

**Status: real-data result in hand. SIFT+RANSAC agrees closely with the grid search on 4 of 5
sections, and on the fifth — `S3_test_03`, the section experiment 010 found the grid search
non-reproducible on and experiment 009 showed its `FOURTH` verdict does not survive a visual
check — SIFT+RANSAC returns a small offset consistent with the other four sections and the
`SECOND` verdict the naive condition already gives.** This does not yet promote SIFT+RANSAC's
`S3_test_03` offset to a claim — per this project's own discipline (a "plausible" offset was
wrong once already on this exact section), it needs the same visual check experiment 009 ran
before anyone quotes it.

```bash
kaggle kernels push -p experiments/011-sift-ransac-registration
```

Ran as `lethabomh14/reefprint-p5-sift-ransac-registration`. **~3 hours**, CPU only — see
"Runtime, and a real finding about cost" below; this is not what was expected going in, and
the first push of this experiment had to be fixed once already (docs/BUILDLOG.md, this session,
"experiment 011's first Kaggle push ran for hours").

## The result

All five sections `experiments/007-010` already report on. `frames_used` is `MAX_SIFT_FRAMES=10`
(capped, evenly spaced across the rotation range — see `run.py`'s own docstring for why); the
grid search runs on every available frame, unchanged from 007. `det` is the real-data
determinism check — run on only the first usable section (`S3_test_01`), per Rule 10 discipline
that determinism is a property of the code, not something worth re-checking five times at the
cost this experiment turned out to have.

| Section | Naive verdict (snr₂/snr₄) | Grid offset (x,y) → verdict | SIFT+RANSAC offset (x,y) → verdict | Usable | Det. |
|---|---|---|---|---:|---|
| `S3_test_01` | SECOND (12.54/4.44) | (−100.9, 31.6) → **SECOND** | (−102.1, 36.2) → **SECOND** | 10/10 | **True** |
| `S3_test_02` | SECOND (11.18/3.54) | (−106.8, 23.5) → BOTH | (−104.4, 28.4) → BOTH | 10/10 | not checked |
| `S3_test_03` | SECOND (9.35/2.78) | **(−397.3, 40.8) → FOURTH** ⚠️ | **(−111.1, 21.6) → SECOND** | 10/10 | not checked |
| `S3_test_07` | SECOND (6.89/2.09) | (−94.7, 72.1) → SECOND | (−92.0, 74.9) → SECOND | 10/10 | not checked |
| `S3_test_12` | SECOND (7.11/2.68) | (−91.6, 64.0) → SECOND | (−90.1, 66.8) → SECOND | 8/10 | not checked |

**Read the offsets across rows before reading any single row.** Four of five sections — `01`,
`02`, `07`, `12` — sit in a tight, coherent band: x between −91 and −107, y between 21 and 75,
and the two methods agree with each other to within about 3–8 px on every one of them. That is
the shape a real, fairly consistent rig offset should have. `S3_test_03`'s grid-search offset
(−397, 41) is a clear outlier against that pattern; its SIFT+RANSAC offset (−111, 22) is not — it
sits squarely inside the same band as the other four, and its harmonic verdict (`SECOND`) matches
what the *naive*, zero-registration condition on that same section already reads, and what
`experiment 009`'s visual check already argued for over the grid search's `FOURTH`.

**The determinism check passed on real data.** `S3_test_01`, run twice inside the same process,
returned bit-for-bit identical `offset_xy` and per-frame diagnostics. This is the property
`experiments/010` proved the grid search does **not** have. It was checked once, not on every
section, deliberately — see `run.py`'s own docstring on why repeating it five times was the
actual cost driver in the first, broken version of this experiment.

## What this does and does not establish

- **Does not, on its own, overturn the grid search's `S3_test_03` retraction into a new claim.**
  `WORKBOARD.md` §0 C1 already withdrew that offset; this experiment adds evidence that
  SIFT+RANSAC's replacement is more plausible, not a visually-verified replacement. **The next
  step before any `S3_test_03` offset is quoted anywhere is the same visual check
  `experiments/009-s3test03-visual-check/` ran on the grid search's offset** — track a real grain
  across the registered stack and confirm it actually moves consistently with the claimed
  rotation, not just that the harmonic verdict looks better.
- **Does not check the grid search's own determinism on this run.** Only SIFT+RANSAC's
  determinism was checked here. Whether the grid search's `S3_test_03` answer would reproduce on
  a repeat run remains exactly the open question `experiments/010` left it as.
- **Is evidence for Rule 10, independent of what happens to `S3_test_03` specifically.** The
  published method was tried, it did not need repair to get an answer, and on the one section
  where the two methods disagree, it disagrees in the direction the rest of this project's own
  evidence (009's visual check, the naive condition's own verdict, the other four sections' offset
  magnitudes) already pointed.

## Runtime, and a real finding about cost, independent of the correctness result above

**Total wall-clock: ~3 hours** for 5 measurable sections (~11,000 s of the kernel's own reported
timeline) — much longer than `experiments/007`'s comparable grid-search-only run (~10 minutes for
12 sections attempted). The first version of this experiment made the mistake of running
SIFT+RANSAC on every frame, twice, on every section — fixed (`MAX_SIFT_FRAMES`, single-section
determinism check; see `docs/BUILDLOG.md`, this session). **After that fix, a new and unexpected
cost pattern showed up: per-section time did not track frame count.**

| Section | Frames | Wall-clock for this section |
|---|---:|---|
| `S3_test_01` | 71 | ~34 min |
| `S3_test_02` | 72 | ~22 min |
| `S3_test_03` | 72 | ~43 min |
| `S3_test_07` | **24** | **~42 min** |
| `S3_test_12` | **24** | **~41 min** |

`S3_test_07` and `S3_test_12` have a third of `S3_test_01`'s frame count and took *longer*. The
per-frame SIFT+RANSAC diagnostics point at the actual driver: **inlier counts, not frame counts**.
`S3_test_03`'s richest frame pair matched **17,074 inliers**; `S3_test_07` and `S3_test_12` also
ran into the thousands on several frames, while `S3_test_01`/`02` mostly stayed in the hundreds to
low thousands. `skimage.feature.match_descriptors` with `cross_check=True` is brute-force —
quadratic in keypoint count — so a section with unusually rich, fine mineral texture produces far
more SIFT keypoints and far more matching cost, **independent of how many frames it has**.
`MAX_SIFT_FRAMES` caps frame count; nothing in this run caps keypoint count per frame, and that
turned out to be the actual unbounded dimension.

**Not yet fixed, because the current result is usable and re-running costs another ~3 hours.**
If this estimator is run again, worth doing first: cap keypoints per frame (SIFT's own descriptor
array can be truncated to the top-N by response before matching) rather than assuming frame count
is the only cost lever. Left as a finding, per Rule 8/9, not as a blocker on today's result.
