# Like-for-like against the published S1 benchmark, settled

**Date:** 15 September 2026
**Evidence:** `reports/benchmark_s1_v1_protocol.json`, `logs/v1v2_match.json`.
**Settles:** issue #5 ask 4, which was retracted on 15 September as unsound and
is now resolved properly.

---

## 1. What was wrong with the original plan, and what replaced it

The ask was for LumenStone S1 **v1**'s 16 test filenames, to check
`set(v1_test) <= set(v2_test)` and enable a direct comparison against the
published **0.8373**.

That was retracted because `test_01.jpg`-`test_20.jpg` are **positional**, not
identity-bearing: a filename match establishes a shared *slot*, not a shared
*image*, and a renumbering between versions would produce a "like-for-like"
comparison that silently was not one.

The sound check is content hashing, and it needed the v1 images. Those were
downloaded from the dataset's own Yandex Disk link: `S1_v1.zip`, **534,897,733
bytes** (published figure 535 MB), sha256 `80940fb7...`, unpacking to exactly
**59 train + 16 test** as published.

## 2. The membership result

All 16 v1 test images are **byte-identical** - sha256 over file bytes, not a
perceptual hash - to S1 v2 test images `test_01` through `test_16`.

**Zero** v1 test images appear anywhere in S1 v2's 64-image **train** set.

That second line is the one that mattered and it was not part of the original
ask. Our checkpoint is trained on v2's train split; had any v1 test image landed
there, the comparison would have been leakage-contaminated and worthless. It is
clean.

The positional guess turns out to have been *correct*. It is now **proven**
rather than assumed, which is the whole difference.

## 3. The like-for-like number

Our S1 checkpoint scored on exactly those 16 images, under petroscope's own
void-border protocol:

| class | ours | ours+void | published | pub+void | gap (void) | share of gap |
|---|---:|---:|---:|---:|---:|---:|
| tennantite | 0.3247 | 0.3479 | 0.7601 | 0.7706 | **-0.4227** | **47.1%** |
| galena | 0.4784 | 0.5068 | 0.7464 | 0.7630 | **-0.2562** | **28.6%** |
| sphalerite | 0.6061 | 0.6355 | 0.7534 | 0.7653 | -0.1298 | 14.5% |
| chalcopyrite | 0.8424 | 0.8916 | 0.9191 | 0.9363 | -0.0447 | 5.0% |
| pyrite | 0.9018 | 0.9286 | 0.9628 | 0.9732 | -0.0446 | 5.0% |
| background | 0.7985 | 0.8490 | 0.8326 | 0.8505 | -0.0015 | 0.2% |
| **bornite** | 0.8651 | **0.8975** | 0.8868 | 0.8955 | **+0.0020** | - |
| **MEAN** | **0.6881** | **0.7224** | 0.8373 | **0.8506** | **-0.1282** | |

Pixel accuracy 0.8581 plain, 0.8816 void-border.

**We match published on background, and beat it on bornite.** Two more classes
are within 0.045. Three carry the entire gap.

## 4. The uncomfortable part, stated because it is the point of doing this

**The gap is WORSE on the true protocol than on our own test set.**

| | mean IoU | void-border | gap to published |
|---|---:|---:|---:|
| v1 protocol, 16 images | 0.6881 | 0.7224 | **-0.1282** |
| our v2 test, 20 images | 0.7116 | 0.7481 | -0.1025 |

The four extra images in v2's test split were making us look **+0.0257**
better. Every previous statement of the S1 gap used the 20-image figure, which
is not what the published number was measured on.

**Use -0.1282, not -0.1025, whenever the published 0.8373 is in the sentence.**

## 5. A correction to something claimed earlier today

Entry 63 and commit `ca2e02f` reported that **tennantite is 60.8% of the S1
gap**. That is true of the 20-image v2 test set. On the correct 16-image v1
protocol it is **47.1%**, and **galena rises from 14.3% to 28.6%**.

Tennantite and galena together are **75.7%** of the gap. The headline framing -
that the gap is concentrated in a few optically ambiguous phases rather than
spread across the model - survives and is if anything cleaner with two named
classes instead of one. But the specific figure 60.8% should not be repeated.

## 6. What this does to the low-contrast hypothesis

Galena joining tennantite is consistent with it. Galena is a grey lead sulphide;
tennantite is a grey Cu-As sulphosalt; both sit close in reflectance to their
neighbours, as magnetite does to the mounting resin on S2. The classes we match
or beat - bornite, pyrite, chalcopyrite - are the strongly coloured ones.

And published detects all of them: tennantite 0.7601, galena 0.7464, magnetite
0.650 (Korshunov). So the limit remains ours rather than the modality's, which
keeps this a training-budget claim and keeps J0/J1/J2 the experiment that tests
it. The pre-registered scaling prediction should name **galena** alongside
tennantite and magnetite.

## 7. Limits

- 16 images. Bootstrap intervals are not computed here.
- The published figures are read from petroscope's README table, not
  reproduced by us; we are comparing our measurement to their report.
- Our checkpoint trained on v2's 64-image train split; the published model
  trained on v1's 59. **More training data, worse result** - which is a fact
  about our training budget, not about the data.

---

## 8. Everything the 60.8% figure took with it

The retracted figure did not travel alone. `ca2e02f` published a decomposition
of the **20-image v2 test set** and described it as the gap to published, and
five derived numbers went with it. All five are superseded by the 16-image v1
protocol, which is what the published 0.8373 was actually measured on.

| Quantity | Published in `ca2e02f` (20-image) | Correct (v1 protocol, 16-image) |
|---|---:|---:|
| mean gap to published | -0.1025 | **-0.1282** |
| tennantite share of gap | 60.8% | **47.1%** |
| galena share of gap | 14.3% | **28.6%** |
| gap excluding tennantite | -0.0469 (six classes) | **-0.0791** (six classes) |
| classes "effectively matched" | three | **two** (background, bornite, within 0.01) |
| tennantite IoU quoted | 0.3130 | **0.3247** plain / 0.3479 void |

Two further figures that are *new* rather than corrected, and are the better
ones to quote:

- **Excluding tennantite and galena, the remaining five classes gap at
  -0.0437.** That is the honest version of "most of the model is close".
- **Four classes are within 0.05 of published**: background, bornite,
  chalcopyrite, pyrite.

### Where it propagated

On `main`: nowhere outside `HANDOVER.md` entry 63, which is append-only history
and is corrected by entry 66 directly above it. `PITCH.md`, `STATUS.md` and the
research report were never updated with it, which is the one piece of luck here.

On `reefprint`, six files carry it (ADR-0003: **not** ours to edit, flagged to
Lethabo on issue #5):

- `CLAUDE.md` line 89
- `CONTEXT.md` line 165
- `WORKBOARD.md` line 244
- `docs/09-brief-compliance.md` line 22
- `docs/11-pre-registered-morphology-sensitivity-and-scaling-predictions.md` line 97
- `docs/BUILDLOG.md` line 100

**`docs/11-...` is the urgent one.** It is the pre-registration for J0/J1/J2,
and a scaling prediction keyed to the wrong decomposition predicts movement in
the wrong classes. It names tennantite and magnetite; galena is the
second-largest contributor to the gap and is absent from it.

### The lesson, since this is the fourth of these today

A number was published with a decomposition attached, the decomposition was
correct for the set it was computed on, and nobody said which set that was. It
then travelled into six documents on another branch within hours, including a
pre-registration protocol.

`main`'s own `WORKBOARD.md` mirror predates the figure and is therefore *stale
but correct*, which is luck rather than process. The provenance convention
agreed on issue #5 - `checkpoint_sha` and `generated_at` on every report - would
not have caught this one, because the artifact was not stale: **it was correctly
computed on an unnamed evaluation set.** The convention needs a third field:
**which images the number is over.**
