# 013 — the sensitivity analysis `khanya/main`'s own audit assigned to this side of the seam

**Status: run, and it found two things.** One answers the question it was built to answer
(does topology refinement change *which* sections the decision-gap analysis flags, not just how
many — partially: the rate is stable, the specific sections are not fully the same, and the
sample is too small to say whether that is signal or noise). The other was not what this
experiment set out to find: **the project's own headline S2 mIoU depends heavily on which
averaging convention is used, and the two give materially different numbers — 0.5725 pooled vs
0.4671 per-section macro-averaged, bootstrap 95% CI [0.4116, 0.5362].**

```bash
uv run python experiments/013-decision-gap-refinement-sensitivity/run.py
```

Runs locally, no Kaggle needed — everything it reads is three small JSON files already committed
to `khanya/main`, fetched with `git show` at run time. No cross-branch code import (ADR-0003
stays intact) and no data transfer needed; anyone with this repo can reproduce it from this
branch alone.

## Why this exists

`reports/REFINEMENT-AUDIT-2026-09-15.md` (khanya/main, 15 Sep) measured two things about the
topology repair (`modal.refine_ore_mask`, `modal.watershed_particles`) and rejected both as
explanations for the decision-gap finding — it is not mostly masking the dead magnetite channel,
and it does not systematically bias liberation conservative. It noted, but did not check, that
the aggregate flip rate is identical (6/12) whether refinement is on or off, and flagged this as
needing a sensitivity analysis, assigned explicitly to "the REEFPRINT side of the seam under
ADR-0003 — it is a measurement question." This is that analysis.

## Finding 1 — the flip rate is stable, but not on the same sections

| Condition | Flip rate | 95% CI (bootstrap, n=12 sections, 2000 resamples) |
|---|---:|---|
| Raw predictions | 0.500 | [0.250, 0.750] |
| Refined predictions | 0.500 | [0.250, 0.750] |

Identical point estimate, identical (necessarily, at this n) interval. But the two conditions do
**not** flag the same sections:

- Flip under **both**: `test_03, test_04, test_05, test_09` (4 sections)
- Flip under **raw only**: `test_10, test_11`
- Flip under **refined only**: `test_06, test_08`

An exact McNemar test on the 4 discordant pairs gives **p = 1.0** — the 2-vs-2 split is exactly
what the null predicts, so this cannot reject "no difference." **That is not the same as
confirming there is no difference.** At 4 discordant pairs the test has essentially no power —
reported that way deliberately, per `reefprint.trust.bootstrap.PairedDisagreement.describe()`'s
own low-power note, rather than letting a non-significant p-value read as a clean result it
cannot support.

**Honest conclusion**: the aggregate 50% flip rate is not an artefact of the refinement choice —
that confound is cleared, which is a real point in the decision-gap finding's favour, same as
the audit's own two rejected hypotheses. But *which* sections flip is refinement-sensitive, and
with 12 sections there is not enough data to say whether that sensitivity is noise or a real
effect worth chasing further. Presenting the decision-gap result should name both facts, not just
the first one.

## Finding 2 — the headline S2 mIoU depends on which average is taken, and the gap is not small

`reports/lumenstone_s2_patches_test_metrics.json`'s top-level `mean_iou` (**0.5725**) is a
**pooled** statistic: TP/FP/FN are summed across all 12 test sections first, per-class IoU is
computed once from the pooled counts, then averaged across classes. Averaging each section's own
`per_image[...].mean_iou` **across sections instead** gives **0.4671**, bootstrap 95% CI
**[0.4116, 0.5362]** — independently verified twice (once inside this experiment's own code,
once in a standalone check against the raw JSON, both giving 0.46714846233419444).

**Ten of the twelve test sections score below the reported 0.5725 headline**:

| Section | mean IoU |
|---|---:|
| test_02 | 0.7275 |
| test_03 | 0.6588 |
| test_08 | 0.5038 |
| test_05 | 0.4716 |
| test_04 | 0.4662 |
| test_07 | 0.4534 |
| test_12 | 0.4425 |
| test_01 | 0.4127 |
| test_09 | 0.3749 |
| test_11 | 0.3769 |
| test_10 | 0.3775 |
| test_06 | 0.3400 |

Two sections (`test_02`, `test_03`) pull the pooled average up; a typical section performs
closer to 0.42–0.47 than to 0.57. Neither number is *wrong* — pooled and per-section-macro are
both legitimate, standard conventions, and this is the same shape of issue as the
1.58%/1.84%/0.792% magnetite-abundance mixup Sibusiso already found and fixed (issue #5): several
valid numbers circulating under one name, with the reader left to guess which one a slide means.

**Recommendation, consistent with that same fix**: state which convention any reported mIoU
uses, every time. If the pitch's headline number is the pooled 0.5725, say "pooled across test
sections" next to it — a judge who has just heard "0.88 published, we score 0.57" and then reads
`per_image` inside the same repository and finds a typical section closer to 0.45–0.47 will read
the gap between those two numbers as evasion, not as two valid statistics, unless the convention
is named up front.

## What this does and does not settle

- Does not say the decision-gap finding is wrong — same caveat the refinement audit itself gave.
  It says the finding rests on 12 sections with a flip-rate CI spanning [0.25, 0.75], and that a
  reader deserves to see that interval, not just the point estimate.
- Does not say 0.5725 is an inflated or dishonest number — it is a standard, defensible
  aggregation. It says the project has not yet stated, anywhere, which convention its headline
  figure uses, and the gap to the alternative convention is large enough (0.57 vs 0.47) that the
  choice is not a rounding matter.
- Does not extend to S1 — this experiment used only the committed S2 files the audit's own
  question was about. The same check on S1 (`lumenstone_s1_patches_test_metrics.json`) is a
  five-minute follow-up if it turns out to matter there too.

## Built alongside this

`reefprint.trust.bootstrap` — `cluster_bootstrap_ci` (percentile bootstrap over independent
units, seeded, predeclared resample count) and `paired_exact_test` (exact McNemar, not the
chi-squared approximation, honest about low power at small discordant counts). The plan's own
Workstream D specified this tool and never built it
(`docs/10-2026-09-14-literature-and-brief-plan.md`: "a section-level cluster bootstrap (~60
lines, 2,000 predeclared resamples)"); a concrete need from the other branch is what finally
produced it. 18 tests, `tests/test_trust_bootstrap.py`.
