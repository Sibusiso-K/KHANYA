# How KHANYA wins — positioning, abstract, and the 10 minutes

Written 2026-08-17. Read with `STATUS.md` (what exists) and `MINTEK-FIT.md`
(why Mintek should care).

---

## 1. The problem with being a good computer-vision project

Every team in this category will bring a convolutional network, an accuracy
number and a demo. Judges will sit through several of them. Within that set we
do **not** win on accuracy — our mean IoU is 0.5725 against a published 0.8506 on
comparable data, and we trained on a laptop CPU. Any pitch that competes on model
quality puts us in the middle of the pack at best.

So we must not compete there. We compete one level up.

## 2. The distinguisher, in one sentence

> **Everyone else will show you a model. We are showing you the measurement that
> tells you whether a model is good enough to act on — and we found that the
> accuracy number everyone reports does not answer that question.**

That is a research finding, not a feature. It is defensible with our own held-out
numbers, it is transferable beyond our dataset, and it is the kind of thing a
research institute remembers after twenty pitches about accuracy.

## 3. The three assets nobody else will have

### 3.1 The decision-gap result — the crown jewel

We ran the full advisor twice over the same held-out sections, once on
ground-truth masks and once on predicted masks, and counted where the plant
instruction changed.

| | Mean IoU | Recommendation errors |
|---|---|---|
| resize model | 0.545 | 6 / 12 |
| patch model | **0.5725** | **6 / 12** |

**Improving segmentation changed the decisions not at all.** What did work was
repairing particle topology — with no retraining — taking errors from 6/12 to
4/12, and both together to **2/12 with liberation correlation 0.947**.

The mechanism is clean and explains itself in one line: IoU rewards getting grain
*interiors* right; liberation depends on grain *boundaries*. They are nearly
independent axes.

**Scope this claim carefully — we tested it on a second dataset and it did not
reproduce.** On LumenStone S1, topology repair did not reduce disagreement with
the ground-truth-mask run; it raised it, from 4/20 sections to 14/20
(`reports/decision_gap_s1_patches{,_refined}.json`, regenerated 2026-09-15).
Every one of those additional flips is a hedge to manual review, and **unsafe
errors are zero on S1 both with and without repair**.

**Corrected 2026-09-15 — the previous version of this paragraph was wrong in a
way that made the result look weaker than it is.** It said S1 segmentation was
"much weaker (mean IoU 0.33 against 0.57, two classes at effectively zero)" and
used that as a confound: no coherent structure left to repair. Both figures came
from a prediction cache four days older than the S1 checkpoint. The real numbers
invert the argument: **S1 mean IoU is 0.7116 against S2's 0.5725** — S1 is the
*stronger* segmentation — and **no S1 class is near zero** (lowest is tennantite
at 0.313). It is S2 that carries a class at zero, magnetite.

So the quality-floor escape hatch is gone. But regenerating the severity counts
alongside the flip counts showed the flip rate was the wrong metric to judge this
on, and the finding **does** replicate once the right one is used:

| | Flips | Unsafe | Conservative | Flagged |
|---|---|---|---|---|
| S2 raw | 6/12 | **2** | 3 | 1 |
| **S2 refined** | 6/12 | **0** | **0** | 6 |
| S1 raw | 4/20 | 0 | 1 | 3 |
| **S1 refined** | 14/20 | **0** | **0** | 14 |

Topology repair does not make the system disagree with ground truth less often.
It converts the disagreements from **silent errors into explicit hedges** - on
both datasets, unsafe and conservative errors go to zero and everything becomes a
request for manual verification.

**Say this, not the old line:** *"repairing particle topology did not make the
system more accurate - it made it stop being confidently wrong. Every error
became a request for a human to look."* That is the refusal thesis, measured, on
two datasets. State plainly that S1 is weak evidence for it (the raw S1 run had
only one error to remove and no unsafe ones), and do not claim a general law
about image-based mineralogy.

Handled well this is a strength rather than a retreat: we ran the generalisation
test that nobody asked us to run, reported that it failed, and can name the
experiment that would settle it. That is more convincing than an unchallenged
claim, and it is exactly what the originality authentication stage rewards.

### 3.2 A system that knows when it does not know

When the apparent 2D sulphide association index falls within the decision
threshold's uncertainty band, the advisor returns **"Marginal — verify before
acting"** and names both candidate actions instead of guessing.

**Corrected 2026-08-18, and this correction is itself part of the pitch.** The
band was originally the estimator's mean absolute error (±8.9%), used as a
symmetric half-width — a point estimate wearing the shape of a guarantee.
Checked against its own data: that fixed band actually covered only 67% of S2
sections and 45% of S1 sections, nowhere near what "uncertainty band" implies.
Replaced with **split conformal prediction** — the empirical 85th-percentile
residual under leave-one-out calibration, the highest level our n=12 test set
can support at all (1 − 1/(n+1) = 92.3% is the ceiling; we report the
achievable level, not a nominal one). The honest band is **±33.5%**, roughly
4× wider than what we shipped originally.

Say this plainly on stage: *we found our own uncertainty estimate was
overconfident, checked it, and fixed it before anyone else could find it for
us.* That is a stronger moment than a clean number would have been — it is
the originality-authentication story made visible in real time.

For Mintek this converts directly into **triage**: "verify" is exactly the signal
that should consume QEMSCAN time. Honesty becomes throughput.

### 3.3 A documented trail of honest science

Five finalists go through **originality authentication** after the conference.
Our repository contains, in git history with dates:

- negative results kept rather than deleted (Dice loss failed; balanced sampling
  did not rescue magnetite)
- a diagnosis rather than a shrug (magnetite is never predicted at all; 92.3% of
  it becomes background; it is a reflectance ambiguity, which is why neither
  resolution nor loss weighting helped)
- **our own published figure retracted and corrected** (a 33% flip rate that
  turned out to be a measurement artefact; the honest number is 50%)
- a "numbers that must never be quoted" section listing our own misleading
  results

That trail cannot be fabricated retrospectively, and it is unusual. Most teams
will present only what worked. **At a research institute, showing what did not
work and why is a credibility multiplier, not a weakness.**

## 4. The abstract — due 30 August

One page. The first two sentences decide whether anyone reads carefully.

**Do not open with** "we built a CNN to classify minerals". That is the sentence
every other abstract opens with.

**Open with the tension.** Something in this shape, in your own words:

> Mineralogical vision models are reported by segmentation accuracy. We tested
> whether that number predicts operational usefulness, and on held-out ore
> sections it does not: raising mean IoU by 2.8 points changed none of the plant
> recommendations our system produced, while repairing particle geometry — with
> no retraining — removed two thirds of the recommendation errors.

Then, in order:

1. **What we built** — micrograph to segmentation to modal mineralogy to an
   apparent 2D sulphide association index by particle composition to a
   flotation recommendation. One learned stage; the rest deterministic and
   auditable.
2. **Evidence** — five phases, 12 held-out sections, mean IoU 0.5725, and the
   decision-error table. Give both numbers. The decision number is the point.
3. **The honesty mechanism** — uncertainty band derived from measured error;
   what it does to unsafe errors.
4. **Scope, stated plainly** — trained on Norilsk Ni-Cu-PGE sulphide, an
   assemblage analogue for Bushveld reef ores and explicitly not an abundance
   analogue. No chromite data, so no UG2 grade claim.
5. **The proposal to Mintek** — QEMSCAN maps as segmentation labels for optical
   images of the same sections (see MINTEK-FIT.md §3.4).

That last item matters more than it looks: it gives Mintek something to *do* with
us, not just something to score.

## 5. The 10 minutes on 1 October

Ten minutes is roughly 8 slides and no room for architecture diagrams. Judges
decide in the first ninety seconds whether this is another accuracy pitch.

| # | Slide | Purpose |
|---|---|---|
| 1 | The question: *does a more accurate model give better instructions?* | Frame it as an experiment, not a build |
| 2 | The plant problem: grind too fine and waste energy, too coarse and lose metal to tailings | Ground it in money before any ML |
| 3 | The pipeline, one diagram, 30 seconds | Show one learned stage, rest deterministic and auditable |
| 4 | **The answer: no.** IoU 0.545 → 0.5725, decisions 6/12 → 6/12 | The moment. Let it land; do not rush |
| 5 | **What did work** — topology repair, 6/12 → 2/12, correlation 0.128 → 0.947 | Resolution, with the liberation agreement chart |
| 6 | **Live demo on a marginal section** — the system says "verify", not a number | The memorable moment |
| 7 | Limits, named first: magnetite fails and here is exactly why; no SA ore | Credibility |
| 8 | The offer: QEMSCAN maps as labels; what we would build with Mintek | Give them a next step |

**Slide 6 is the one they will remember.** A demo that produces a confident
answer is forgettable; a demo that *declines to answer* and explains why is not.
Rehearse that moment specifically.

## 6. Framing the weaknesses before they are found

Judges will find these. Better that we name them first.

| Weakness | The framing that survives scrutiny |
|---|---|
| mIoU 0.5725 vs published 0.8506 | "Twelve CPU epochs against their full training budget — and we can show that closing that gap would not have changed our recommendations. That is the finding." |
| Magnetite IoU 0.000 | "Never predicted at all; 92.3% becomes background. It is a reflectance ambiguity, not a data-volume problem, which is why native resolution and a region-based loss both failed. We report four phases and a diagnosed fifth." |
| Norilsk, not Bushveld | "Same BMS assemblage, same intrusion type. An assemblage analogue, explicitly not an abundance analogue. Closing that needs your data, which is our proposal." |
| Small dataset | "37 training images. Which is why the interesting result is about the evaluation method rather than the model." |
| Thresholds unsourced | "Three of four are configurable plant parameters, not claims. The liberation floor is literature-backed." |

**Never** lead with pixel accuracy 89%. It is flattered by background and
pyrrhotite being 83% of pixels, and a mineralogist will take it apart.

## 7. What to do with the remaining time

Ranked by effect on winning, not by interest:

1. **The mentor / QEMSCAN-labelling request** (by 30 Aug). Highest leverage
   available: it converts our weakest point into a partnership.
2. **Re-voice the drafted report sections.** Originality is scored and
   authenticated. This is disqualification-class risk, not style.
3. **Build the economic case.** "This decision error costs X tonnes of
   recoverable metal per year" makes the flip-rate finding commercial rather than
   academic. Currently our money argument is three [CITE] markers.
4. **Rehearse slide 6 until the demo cannot fail**, offline, on the venue laptop.
5. Further modelling. Genuinely last — we have evidence it has poor returns.

## 8. The one-line answer to "so what?"

> A plant does not need a model that is right most of the time. It needs a model
> that knows which of its answers to trust. We built the second thing, and we can
> prove the difference.
