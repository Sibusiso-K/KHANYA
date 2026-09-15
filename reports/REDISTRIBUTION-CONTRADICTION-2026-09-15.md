# The submission is about to state something that is no longer true

**Date:** 15 September 2026
**Status:** BLOCKING a requested action. Not a licence opinion - a factual
contradiction between two branches that is scheduled to reach MOTT in writing.
**Raised by:** the request to upload `S1_v2` and `S2_v2` to Kaggle so J0/J1/J2
kernels can mount them.

---

## 1. What was asked, and why it is paused

The ask is to run `kaggle datasets create` on `data/raw/lumenstone/S1_v2`
(639 MB) and `S2_v2` (417 MB), matching how `S3_v2` and `V1` were staged, so
training kernels can mount them under `enable_internet: false`.

Technically it is a ten-minute job and nothing underneath it is blocked. It is
paused because of what `DATA-SOURCES.md` on `main` already commits us to saying.

## 2. The contradiction

`DATA-SOURCES.md` (`main`), under the 2026-09-13 team decision on LumenStone
terms, gives three reasons the position is defensible. Reason 1, verbatim:

> **We do not redistribute LumenStone's data at all.** `data/raw/` and
> `checkpoints/` are both gitignored - zero files from this dataset, and no
> trained weights derived from it, are present in the public repository that
> Mintek's Office of Technology Transfer will review.

The same section then instructs:

> **State this explicitly in the submission** rather than silently assuming it
> is resolved.

Meanwhile, on `reefprint`:

- `lethabomh14/lumenstone-s3-v2-reefprint` - `S3_v2.zip`, 5.2 GB, uploaded
- `lethabomh14/lumenstone-v1-reefprint` - `V1_v1.zip`, uploaded 2026-09-15

**Two LumenStone subsets have already been redistributed to a third-party host.**
The requested S1/S2 upload would make it four.

Reason 1 is narrowly true about the *git repository* and false about the
*project*. A sentence that survives only on the reading "we do not redistribute
it **in the repo**" is not a sentence to put in front of an IP assessment,
because the assessor can check Kaggle.

## 3. What the licence actually says, and what it does not

Correcting an error made while investigating this, before it propagates:
**LumenStone is not CC BY-NC-SA 4.0.** That is LITHOS-DATASET, a different
ruled-out dataset in the same file. LumenStone has no named OSI licence. Its
terms are an explicit written grant, quoted verbatim on `reefprint` from
`imaging.cs.msu.ru/en/research/geology/lumenstone`:

> "You are free to use the provided data in your own research work. If you
> intend to publish research work that uses this dataset, you have to cite the
> references whenever appropriate."

That is a **use** grant with a **citation** condition. It is silent on
redistribution. So the Kaggle uploads are not clearly forbidden - but they are
**not clearly permitted either**, and "silent" is the worst of the three
possible states to be in when the assessment is adversarial. A private Kaggle
dataset is still a hosted copy on infrastructure neither we nor the dataset
authors control, shared across accounts.

**This is not an accusation that the uploads were wrong.** They were a
reasonable engineering decision to get data onto offline kernels, made against a
licence that does not address the case. The problem is the written position that
contradicts them, not the uploads.

## 4. Two coherent resolutions. Pick one; do not ship the current state

**Option A - stop redistributing, keep the sentence.** Delete the two Kaggle
datasets, move S1/S2 to the kernels by a route that is not a public-platform
dataset, and keep reason 1 exactly as written. Cost: the offline-kernel workflow
needs rework, and J0/J1/J2 is delayed.

**Option B - keep the staging, rewrite the sentence.** Accept that we mirror the
data privately for compute, say so plainly in the submission, attach the required
citation and the source terms to every Kaggle dataset description, and keep them
private. Reason 1 becomes something like: *"No LumenStone data or derived weights
appear in the public repository. Private mirrors exist on Kaggle solely to make
the data reachable from offline training kernels; they carry the dataset's terms
and citation, and will be removed on request."*

**Option B is the honest one and is probably also the stronger one**, because it
describes what we actually did and shows we thought about it. Option A buys a
cleaner sentence at real cost and only if the deletions actually happen.

What must not happen is shipping reason 1 as written while four LumenStone
subsets sit on Kaggle.

## 5. Until this is decided

S1/S2 are **not** being uploaded. The blocker is a decision, not a transfer.

Whoever picks the option should also check whether the existing two Kaggle
dataset descriptions carry the LumenStone citation - under the written grant,
citation is the one condition that is unambiguous, and it binds regardless of
which option is chosen.
