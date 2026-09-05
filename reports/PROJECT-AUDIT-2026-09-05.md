# Project audit — 5 September 2026

## Outcome and scope

Audited the main decision pipeline, actual Stitch dashboard, REEFPRINT physics,
trust checks, offline demo, test selection, CI and documentation. Changes stay
in their respective histories; no merge or code-copy bridge was introduced.
Starting revisions: main `cc07c66`, reefprint `2f08bca`.

This is a software reliability audit, not an independent validation of trained
model accuracy, orebody transfer, scientific novelty or licensing compliance.

## Main fixes

- Unmeasurable liberation is unknown, not zero: particle filtering cannot silently
  turn an absent payload measurement into a grind recommendation.
- Reject nonfinite/out-of-range measurements and invalid segmentation labels.
- Validate conformal inputs and reject undersized CLI inputs clearly. Corrected
  leave-one-out terminology and finite-sample reporting.
- Disabled torchvision's implicit backbone download for offline model creation.
- Pure main helpers no longer require a developer-specific REEFPRINT checkout;
  physics discovery happens when the bridge is actually invoked.
- Stitch templates escape untrusted text. Missing checkpoints, unsupported
  subsets and bad image files have explicit refusal/error paths. Checkpoint
  metadata participates in cache keys. Reagent intervention is not coloured green.
- Removed the implication that a fixed mean S2 interval provides conformal coverage
  on new uploads; corrected team spelling and stale status/setup documentation.

## REEFPRINT fixes (separate branch)

- Nonfinite frames/angles fail before Stokes/extinction inversion.
- Locality splits also reject the same section masquerading under two localities.
- Malformed quality metadata produces a refusal instead of a numeric type crash.
- Association matrices use symmetric directed-contact normalization: entries sum
  to one globally, rather than claiming incompatible row normalization/symmetry.
- Approximate reflectance constants are labelled ASSUMED, not verified QDF values.
- The offline demo calls the production geometry guard; synthetic provenance and
  the conservative default's provenance are visible. Backup frames use a shared
  canvas so the taller refusal reason is not cropped.
- CI listens to reefprint pushes. An implemented advisory-record test is restored
  to blocking CI instead of being hidden under a module-wide placeholder marker.
- Existing Ruff errors and live documentation test counts were corrected.

## Verification

- Main: **87 passed**. Overall measured statement coverage **21%**, including
  unexecuted training/analysis scripts; renderer **98%**, input handling **95%**,
  advisor **94%**. Passing unit tests do not imply whole-project coverage.
- REEFPRINT: **314 passed / 7 deselected**. Measured **92% combined statement/branch
  coverage** in the preceding 313-test run; the final marker correction restores
  one already-passing advisory test to blocking CI.
- Main critical Python lint and whitespace checks passed; REEFPRINT Ruff checks
  passed. Regression tests cover offline construction, hostile template strings,
  three synthetic verdict states, measurement failures and locality leakage.
- Actual browser inspection: the integrated Stitch page renders and states
  “Analysis unavailable”, explains the missing validated checkpoint and issues
  no recommendation. This verifies refusal UI, not successful inference.
- The backup animation is synthetic physics followed by a real guard refusal;
  regenerated and visually checked: two 1400 x 550 screens, four seconds each,
  with the complete refusal reason and default visible. It is not a recording
  of a real ore sample or full dashboard inference.

## Remaining limitations and next actions

1. Restore the validated S2 checkpoint and original micrographs, then run the
   confident/marginal/refusal cases and full offline talk sequence. Neither
   artifact is present here; no substitute model was fabricated. The previously
   suggested report montage is not a valid input micrograph.
2. Main's fixed 0.335 band is a retrospective S2 reference. Independent,
   exchangeable locality calibration and target-domain measurements are needed
   before claiming future coverage or operational safety.
3. Seven explicit placeholders remain: public-series Stokes gate (geometry not
   cleared), three domain heads, real Bushveld falsification, texture/chemistry
   control, and optional OPC UA transport. Data-dependent work needs domain-lead
   direction; no hardware was force-built under ADR-0002.
4. Complete release licence/provenance review, including bundled fonts and
   wavelength-specific reflectance references. This audit gives no legal signoff.
5. An older local checkout has 166 pre-existing staged cross-branch changes.
   It was preserved untouched; a clean reefprint audit worktree was used instead.
   Do not commit that index wholesale.

The next highest-value step is restoring the validated runtime artifacts and
performing the real end-to-end rehearsal, not inventing more placeholder logic.
