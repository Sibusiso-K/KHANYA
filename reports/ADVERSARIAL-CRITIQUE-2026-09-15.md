# Adversarial critique - 16 days out

**Date:** 15 September 2026
**Context:** Requested by Sibusiso as a hostile read of the submission against
Mintek's Problem 3 brief, on the explicit instruction to show no mercy. This is
not a balanced assessment. It is the case *against* the project, written so the
team hears it here rather than from a judge.

It deliberately does not repeat the 2026-09-12 technical review
(`TECHNICAL-REVIEW-2026-09-12.md`), which covered evidence gaps and
implementation. This one attacks the **submission's competitive position and
its claims**, and it includes findings that review did not raise.

---

## The brief, verbatim, scored

> Develop a computer vision or machine learning algorithm that analyses
> high-resolution imagery or sensor data (e.g., hyperspectral) to identify
> mineral phases **in real-time**, predicts the **"processability"** of the ore
> based on its visual or spectral characteristics, and integrates with
> **existing** sorting or flotation controls to provide immediate operational
> feedback.

| Requirement | Reality | Verdict |
|---|---|---|
| High-resolution imagery | Reflected-light micrographs, native 3396x2547 | Met |
| Identify mineral phases **in real-time** | 5s for one 512x512 crop (~2% of a section); p95 195.7s for a full section | **Not met on the literal word** |
| Predict **processability** | An apparent 2D sulphide association index, explicitly unvalidated against any flotation outcome | Proxy, not prediction |
| Integrate with **existing** controls | Real OPC UA transport into a **simulated** plant | Half met |
| At least three mineral phases | Three sulphides with nonzero IoU, of five attempted | Met |
| Accuracy report | Per-class TP/FP/FN, per-image spread, trivial baselines | Exceeds the ask |
| Demonstrate plant parameter adjustment | Live publish plus consumer acknowledge and refuse | Met |

---

## 1. Fatal unless answered

### 1.1 The model fails on the abundance regime it is being pitched for

Magnetite is 1.84% of training pixels. **IoU 0.000.** Zero magnetite pixels
predicted anywhere in the test set. Total class collapse, reported honestly.

UG2's base-metal sulphides are **under 1 vol%**. The payload this project
proposes to detect in Bushveld ore is *rarer than the one class the model
completely failed to find*.

The three classes that work are 5%, 10% and 58% of pixels. The project has
therefore demonstrated competence at segmenting **abundant** phases and
demonstrated **failure** at a rare one. That is the wrong way round for the
stated target ore.

"Norilsk is an assemblage analogue" does not answer this. The failure is not
mineralogical, it is about abundance, and the single experiment in the relevant
abundance regime returned zero.

**Question to answer before the pitch:** why should a judge believe this
transfers to a sub-1% payload when it scored zero at 1.84%?

### 1.2 The published benchmark for this dataset is higher than ours

Mean IoU **0.5725**. The LumenStone authors' own published benchmark is
**0.88** (PSPNet+ResNet18 on S1+S2) and 0.8373 (ResUNet, S1v1) - see
`DATA-SOURCES.md` section 1. Their toolkit (`petroscope`) is a pip install with
pretrained weights.

A competitor who does nothing clever, and simply runs the dataset authors' own
baseline, reports a number roughly 54% higher than ours.

We have a real answer - whole-section native-resolution evaluation, no
void-border inflation, a different task framing - but it is a **second-order**
answer, and second-order answers lose to first-order numbers in a ten-minute
room. This must be raised by us, unprompted, early, in our own words. Said
defensively at minute eleven it reads as excuse-making.

### 1.3 Three of four decision thresholds are invented

From `src/advisor.py`'s own docstring:

- `LOW_LIBERATION = 0.50` - SOURCED.
- `PAYLOAD_FLOOR = 0.003` - **unsourced placeholder.**
- `REJECT_CEILING = 0.60` - **unsourced placeholder.**
- `DELETERIOUS_CEILING = 0.05` - **unsourced placeholder.**

The refusal beat that the entire talk is built around fires when payload drops
below a floor we invented. The honest answer to "how did you choose 0.3%?" is
"we did not, it is a placeholder" - which is true, and destroys the beat if it
arrives as a surprise.

### 1.4 The uncertainty band is so wide it may not mean anything

`LIBERATION_MARGIN = 0.335`. Around a 50% floor that spans **16.5% to 83.5%**,
two thirds of the possible range. That is why 6 of 12 sections come back
marginal.

The hostile reading is fair: *the system is not abstaining selectively, it is
so uncertain it cannot answer half the time, and that has been rebranded as a
feature.*

Worse, the band is derived by leave-one-out over **the same 12 test sections
used for evaluation**. A deployment parameter calibrated on the test set, then
reported alongside performance on that same test set. Disclosed honestly in
`src/conformal.py`, but it means 0.335 carries no clean statistical meaning for
a new upload.

---

## 2. Serious

### 2.1 The advisor's role mapping may violate the project's own Rule 6

`src/modal.py` maps `pyrrhotite -> reject` for S2, `pyrite -> reject` and
`tennantite -> deleterious` for S1, and so on. The whole decision layer reasons
over these roles.

Those mappings are normative mineralogy judgements. They were written from a
literature reading, by an AI agent, and **no metallurgist has signed them off**.

Rule 6 of the project's own constitution forbids an LLM computing a new
normative-mineralogy method. A mineral-to-role mapping is exactly that kind of
judgement. The pitch line "a plant metallurgist can read `advisor.py` and see
why it said grind finer" is strong - but what they would be reading is a
dictionary an AI wrote. This needs either a domain sign-off or an explicit
statement that the mapping is a configurable assumption, not a claim.

### 2.2 The decision-gap result is weaker than the headline suggests

`src/decision_gap.py` compares **the advisor on predicted masks against the
advisor on ground-truth masks**. Same thresholds on both sides.

It therefore measures *"does segmentation error change our own rule's output?"*
It does **not** measure *"does better segmentation produce better metallurgical
decisions?"* There is no flotation outcome anywhere in this project.

Two further problems:

- **Effective n is unknown.** 12 sections, 6 flips, but LumenStone ships **no
  locality or specimen manifest** (confirmed by inspection, 2026-09-14). Those
  12 sections could be 12 specimens or 3 specimens with 4 sections each. We
  cannot state the independent sample size.
- **Topology repair changes ground truth too** (`STATUS.md`: "the refinement
  changes ground-truth liberation too, sometimes a lot"). Both sides of the
  comparison are post-processed by the same step, so a large part of what is
  being measured may be the refinement rather than the model.

### 2.3 The impact number is anchored to the wrong customer

"About 50% of sections get a confident answer, saving a $1,500 QEMSCAN run."

- The interval is **[21%, 79%]** at n=12. At the low end, 79% still go to the
  lab, and the workflow has added a step for almost no saving. An economic case
  cannot rest on an interval that wide.
- The $1,500 is **Saskatchewan Research Council, April 2017, USD, Canada**.
  The customer is **Mintek, 2026, South Africa**. Nine years, a currency, a
  continent.
- **Mintek owns the QEMSCAN.** Their marginal cost per sample is instrument
  time and an operator, not a commercial price list. We are pitching cost
  savings on an instrument the customer already owns.

The defensible value proposition is **queue time and turnaround**, not money -
and we have no data on Mintek's actual turnaround.

### 2.4 The output granularity does not match how a plant operates

KHANYA produces a grind/no-grind recommendation **from one polished section**.
A flotation circuit's grind setpoint moves on a shift or campaign basis,
informed by many samples, assays, throughput and the existing control layer.

No plant changes P80 because one polished section said so. The brief asks for
"immediate operational feedback"; our feedback arrives at a granularity and
cadence a circuit does not act on. This is a product-logic gap, not an
engineering one, and a Mintek metallurgist will feel it immediately.

### 2.5 The entire empirical base is 12 images

Every number in the pitch - accuracy, decision gap, triage rate, latency
design targets, the conformal band - traces to 12 test images from one public
dataset, with 37 training images behind them, and no locality metadata.

---

## 3. Unexamined risks

### 3.1 AI authorship and the MOTT assessment

Every commit in this repository carries `Co-Authored-By: Claude`. `HANDOVER.md`
documents in detail that two AI agents wrote the majority of the code.

The commit history is being treated as the IP defence for MOTT's originality
assessment. It is simultaneously the most complete, timestamped, self-authored
record of AI authorship that could exist.

Three things the team does not currently have answers to:

1. **Does the Mintek-SCi hackathon have any rule on AI assistance** - a
   disclosure requirement, a restriction, anything? This is the single
   highest-value unknown in the project right now.
2. MOTT awards **invention credits to creators**. If most of the invention was
   executed by AI under human direction, what does the team claim?
3. If a judge asks "how much of this did you write?", what is the answer? A
   good answer exists - direction, domain judgement, verification, and the
   repeated refusal to fabricate - but it has to be decided in advance.

### 3.2 A third team member with no attributable trail

`README.md` lists Sibusiso Khumalo, Lethabo Hoaeane and **Ipeleng Modise**.
There is no commit, HANDOVER entry, or named contribution from Ipeleng anywhere
in this repository. If MOTT assesses contribution per person for invention
credits, that is a problem for them, for the team, or for both.

### 3.3 The dataset's origin, in a technology-transfer context

The decision not to seek LumenStone licensing clarification is defensible for a
research demonstration (`DATA-SOURCES.md` section 1). But a top-ranked placement
triggers a MOTT IP assessment of a submission built entirely on a dataset from
**Moscow State University**, under informal terms with no named licence, for a
South African state-owned entity's technology-transfer process.

That is a different question from the licence question, and the downside is
asymmetric: it cannot help us win, and it can complicate the prize.

### 3.4 Nobody outside the team has validated the premise

`MINTEK-FIT.md` is a document the team wrote about why Mintek should care. The
mentor ask was planned for 30 August. If no one at Mintek has confirmed the
problem framing, the entire Impact argument is self-generated.

---

## 4. Operational

- **Zero full rehearsals.** Sixteen days out, the ten minutes has never been run
  start to finish once.
- **No backup video.** `BACKUP-DEMO-SCRIPT.md` exists and has never been
  executed.
- Three distinct demo failures in seven days: a crash on the first tile, an
  `asyncua` venv desync showing "OPC UA UNAVAILABLE", and repeatedly flaky
  mode-switching. All fixed. All would have been fatal live.
- Cold model load is roughly 30 seconds. The 4.7s Live Field figure is **warm**.
  A sleeping laptop or a cleared cache turns the five-second beat into a
  thirty-five-second one.

---

## 5. The six questions to be able to answer cold

1. Your model scores 0.000 on the one rare phase it was given. UG2's payload is
   rarer still. Why should I believe this transfers?
2. The published benchmark on this dataset is 0.88. You report 0.57. Explain.
3. Three of your four decision thresholds are invented. On what basis should a
   plant act on them?
4. Your uncertainty band covers two thirds of the possible range. Is that
   calibration, or a model that does not know anything?
5. Your system says "grind finer" from one polished section. My grind setpoint
   moves once a shift. What do I do with this?
6. You have no South African ore, no flotation outcomes and no locality
   metadata. What exactly have you validated?

Most teams cannot answer one of these about their own work. Being able to answer
all six crisply **is** the differentiator - not that the system is better, but
that we know precisely where it is not.

---

## 6. What this critique does not say

The following are genuinely strong and should not be sacrificed while fixing the
above:

- The abstention architecture, and that the refusal reaches the transport layer
  (a separate consumer visibly declining a stale record) rather than stopping at
  a dashboard message.
- Real OPC UA with an expiry and acknowledgement contract. Most submissions will
  print a recommendation.
- An accuracy report with trivial baselines (majority-class 0.1167, colour-only
  0.3948 against the model's 0.5725). Rare at this level, and the colour-only
  result is real evidence against the "it is just a colorimeter" objection.
- A documented record of four separate refusals to fabricate, each with its
  evidence.

---

## 7. A correction to advice given earlier the same day

In conversation preceding this document, the recommendation was made to lead the
pitch with "better segmentation does not produce better plant decisions."

**That recommendation was too quick.** Section 2.2 above explains why: the
decision-gap experiment does not support that claim as stated, the effective n
is unknown, and the topology-repair confound has not been separated. The finding
is still interesting and still worth presenting - but as "segmentation error
rarely changes our rule's answer", with the limitations attached, not as a
headline claim about plant decisions.

Recorded here because a critique that does not audit its own advice is not a
critique.
