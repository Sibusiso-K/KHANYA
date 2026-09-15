# 11 — Two pre-registered protocols, locked before either run

**Written 2026-09-15, before either run it governs.** Both items are requests from Sibusiso,
each following the same reasoning: the person who authored the code (or chose the training
recipe) should not also be the one who sets the bar for whether it survives scrutiny, decided
after seeing the result. This is `reefprint.quantity.Quantity` refusing to construct without a
source, applied to an experimental protocol instead of a number — **the criterion needs a
provenance that is not the author of what it is testing.**

Neither section is edited after its run starts. If either protocol needs to change, that is a new
dated section below, never a silent edit to this one — the same discipline `docs/BUILDLOG.md`
already runs on.

---

## 1. Morphology-constants sensitivity analysis (khanya/main, `modal.py`)

**Owner of the run: Sibusiso.** `reefprint` has no `modal.py`, no liberation or morphology code
at any path — running this from here would blur exactly the attribution boundary ADR-0003 exists
to keep independently verifiable, which is what MOTT assesses. What is genuinely `reefprint`'s is
this protocol: the perturbation grid and the falsification criterion, fixed before the run.

### What is under test

`reports/REFINEMENT-AUDIT-2026-09-15.md` found the topology repair is load-bearing, not
cosmetic — on 3 of 12 S2 sections it moves liberation from ≈0.00 to ≈0.75–0.80 — and rests on
three hand-set, never-tuned constants:

```python
SPECKLE_KERNEL = 3
SEED_MIN_DISTANCE = 5
PEAK_FOOTPRINT = 9
```

The claim at risk: the decision-gap finding (flip rate 0.50, **0 "unsafe" severity
classifications** under the shipped constants) is a property of the segmentation, not an
artefact of these three unexamined numbers.

### The perturbation grid

One-factor-at-a-time (OAT): vary one constant across its grid, hold the other two at the shipped
value. Cheap, directly interpretable, and sufficient to answer "is the finding fragile to a
credible alternative choice" — a full factorial is not needed to answer that question, only to
map interactions, which is out of scope here.

| Constant | Shipped | Grid to test | Note |
|---|---:|---|---|
| `SPECKLE_KERNEL` | 3 | 1, 3, 5, 7 | Must stay odd (morphological kernel size). 1 = effectively no despeckling. |
| `SEED_MIN_DISTANCE` | 5 | 2, 5, 8, 12 | Watershed seed separation. 2 is aggressive over-segmentation; 12 is aggressive merging. |
| `PEAK_FOOTPRINT` | 9 | 3, 9, 15, 21 | Must stay odd. 3 ≈ unsmoothed peak detection; 21 is heavy smoothing. |

Plus two joint extremes, to catch an interaction the OAT sweep alone could miss cheaply:

- **All-aggressive**: `SPECKLE_KERNEL=7, SEED_MIN_DISTANCE=12, PEAK_FOOTPRINT=21` (maximum
  smoothing/merging in the same direction).
- **All-permissive**: `SPECKLE_KERNEL=1, SEED_MIN_DISTANCE=2, PEAK_FOOTPRINT=3` (minimum
  smoothing/merging in the same direction).

14 configurations total (4+4+4 OAT, minus the 3 shipped-value repeats already covered by the
baseline, plus 2 joint extremes = 3×3 + 1(baseline, already have it) + 2 = 12 new runs). Re-run
the decision gap (`decision_gap_patches_refined.json`'s own pipeline) under each.

### The falsification criterion — fixed now, not interpreted after

**Primary (the sharper claim, and the one worth protecting):** the shipped constants produce
**zero "unsafe" severity classifications**. This claim is **falsified** if **any** configuration
in the grid above produces **one or more "unsafe" classifications**. This is a hard line, not a
threshold to argue about afterwards — one unsafe classification under any credible alternative
parameterisation means "driven to zero" cannot be presented as a property of the method, only of
one specific, unvalidated choice of three constants.

**Secondary (the softer claim):** the flip rate (0.50 under both raw and refined) is **flagged as
sensitive** — not necessarily falsified, since `experiments/013`'s own bootstrap CI on this
statistic is already [0.25, 0.75] at n=12 and has little power to distinguish real movement from
noise at this sample size — if more than 4 of 12 sections change flip status (i.e., more
discordant pairs against the shipped baseline than `experiments/013` already found between raw
and refined, which was itself 4) under **any single** grid configuration. This is reported
alongside the primary criterion, not used alone to declare the finding dead.

**What survival looks like:** zero unsafe classifications across all 12 new configurations, and
no configuration produces materially more than 4 discordant sections against the shipped
baseline. **What does not count as survival:** picking the best-looking subset of the grid and
reporting only that — every configuration in the table above is reported, including the ones that
look bad.

---

## 2. J0/J1/J2 scaling-curve prediction (the training-budget/low-reflectance-contrast hypothesis)

**Owner of the run: Lethabo, on Kaggle (Workstream C).** This section exists because Sibusiso
asked for the same discipline applied here that he asked reefprint to apply to his own morphology
constants: state what the curve is predicted to do *before* running it, so a post-hoc story
cannot be fitted to whatever the curve turns out to show.

### The hypothesis under test

`ca2e02f` (khanya/main) decomposed the S1 gap to published: **tennantite alone is 60.8% of it**
(IoU 0.3130 vs published 0.7601), magnetite is a complete S2 failure (IoU 0.0000 vs published
0.650), and rarity does not explain either — tennantite (3.917% of S1 train pixels) scores far
worse than chalcopyrite (2.974%, IoU 0.8652), and published work detects both minerals on this
same modality. The proposed unifying cause: **both are low-reflectance-contrast phases against
their neighbours** (tennantite grey against other sulphides, magnetite dark against the mounting
resin), and the failure is a **training-budget/capacity limit**, not a limit of the imaging
modality.

### The falsifiable prediction

Classes already matched to published, per the same decomposition (background, bornite,
chalcopyrite — S1 void-border gap ≤ 0.02 each):

> **Predicted: IoU moves by no more than ±0.03 across the patch-budget sweep (2,560 → 40,000).**
> There is little room and no evidence-based reason for these to move much — they are already at
> the ceiling this architecture and this data can reach.

The two low-reflectance-contrast classes (tennantite, magnetite):

> **Predicted: IoU improves by a clearly larger margin than the matched classes' average
> movement** — concretely, at least **+0.10 absolute IoU**, and at least **3× the mean absolute
> change of the three matched classes**, somewhere across the sweep (not necessarily
> monotonically at every intermediate point; patch count is not the only source of run-to-run
> variance).

### Falsification

The training-budget/capacity hypothesis is **not supported by this evidence** if either
low-reflectance-contrast class fails to clear **both** thresholds above (the absolute +0.10 floor
and the 3× relative-to-matched-classes bar) across the full sweep. In that case: **the literature
table's claim should revert from "a training-budget gap" to "a measured failure with an unproven
cause"** — the honest position before this decomposition existed — rather than keep a causal
story the scaling curve itself did not support.

**A partial result is not a free pass to keep the strong claim.** If one of the two classes
clears the bar and the other does not, report both outcomes explicitly and downgrade the claim to
apply only to the class that cleared it.

### What this does not predict

Nothing here predicts the classes will reach published parity (0.7601, 0.650) — only that they
move disproportionately *if* the capacity hypothesis is the right one. Reaching parity is a much
higher bar this pre-registration does not require and the scaling study is not resourced to chase
(see `docs/10-2026-09-14-literature-and-brief-plan.md`'s own "do not chase the published number").
