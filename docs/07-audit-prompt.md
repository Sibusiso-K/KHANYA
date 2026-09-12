# Full audit + realignment prompt — Mintek-SCi Grad Hackathon 2026, Problem 3

Written 2026-09-12, **T-19 days** to the final. Paste everything between the rules into Astra
GPT 6 (or any frontier model). It is self-contained: it carries the brief, the true project
state including what just broke, the constraints, and the decisions needed.

Keep this file updated if the state changes before you run it — a prompt carrying a stale state
produces a confident, useless audit.

---

You are the lead technical reviewer for a team entering a national innovation competition with
19 days left. Your job is **not** to encourage us. Your job is to find every way this entry
loses, and then to design the version that wins.

## 0 — How you must operate (read before anything else)

1. **Adversarial by default.** If our approach is wrong, say so in the first paragraph and give
   the better one in full. A polite audit is a useless audit. We would rather be corrected now
   than beaten on 1 October.
2. **Never invent a number.** If you do not know a figure, write `UNKNOWN — needs measurement`
   and say what experiment would produce it. Do not estimate accuracy, latency, throughput, or
   cost and present it as fact. We will check.
3. **Separate what we have proven from what we have claimed.** Our own documents contain both.
   Where our evidence does not support our wording, quote our wording and say so.
4. **Every recommendation carries a cost in days.** We have 19. A recommendation without an
   honest time estimate is noise. Assume two part-time people plus one who is out of action.
5. **Distinguish "required by the brief" from "impressive to us."** The brief is the scoring
   surface. Anything that is not on it is either a differentiator you must justify, or a
   distraction you must name as one.
6. **Where you lack information about our repo, ask precisely.** List the exact files or numbers
   you would need. Do not fill gaps with assumptions.
7. **No LLM may compute a mineralogical or control value in the shipped system.** Language models
   may route, select, orchestrate, explain and generate UI. They may not decide what mineral a
   pixel is, or what a plant setpoint should be. If your proposed architecture violates this,
   it is rejected on sight — but tell us if you think the rule itself is wrong and why.

## 1 — The competition, verbatim

> **Mintek-SCi Grad Hackathon 2026** — an innovation challenge seeking groundbreaking,
> implementable solutions to real-world problems in South Africa's minerals, mining and
> metallurgy sector.
>
> Aims: *Ignite Innovation* — spark creativity and pioneering spirit. *Build Skills* — equip
> participants to develop impactful solutions. *Foster Collaboration* — encourage teamwork
> through development and presentation. *Respect IP* — promote innovation while ensuring
> intellectual property rights are protected via contractual agreements managed by the Mintek
> Office of Technology Transfer (MOTT).
>
> **Problem 3 — Computer Vision for Real-Time Mineralogical Characterisation**
>
> *Problem setting:* In mineral processing, understanding the mineralogical composition of the
> ore (phase identification) is critical for optimising recovery. Currently, this
> characterisation relies on slow, laboratory-based SEM or XRD analysis, which can take days.
> Without real-time feedback, processing plants cannot adjust to changes in ore quality, leading
> to inefficient chemical usage and lower mineral yields.
>
> *Challenge:* Develop a computer vision or machine learning algorithm that analyses
> high-resolution imagery or sensor data (e.g. hyperspectral) to identify mineral phases in
> real-time, predicts the "processability" of the ore based on its visual or spectral
> characteristics, and integrates with existing sorting or flotation controls to provide
> immediate operational feedback.
>
> *Deliverable:* A trained AI model or software tool capable of identifying **at least three
> distinct mineral phases** from provided image datasets. Submissions must include: **an accuracy
> report**; and **a demonstration of how the model's output can be used to adjust plant
> parameters.**

Final: **1 October 2026, 13:00 submission, 10-minute presentation.**

## 2 — What we actually have, told straight

**The project.** One build, two names. **REEFPRINT** is the physics and measurement half —
quantitative reflectance plus linear Stokes polarimetry, with a calibrated trust layer.
**KHANYA** is the segmentation, modal mineralogy, liberation and dashboard half. Software only;
**no instrument is built** and none will be. Our target ore is UG2 / Merensky Bushveld PGE ore.

**The physics premise.** Hyperspectral reflectance identifies minerals by molecular absorption
features. Chromite is an opaque spinel with none, and it is 50–75 vol% of UG2 ore — so
spectroscopy on chromitite is a brightness meter. Opaque ore minerals are instead identified by
quantitative reflectance, bireflectance and anisotropy under polarised light. Our differentiating
claim is per-pixel recovery of the **full linear Stokes vector** from a rotating-analyser series,
which adds an axis reflectance does not contain, and which splits the base-metal sulphides whose
behaviour governs PGE deportment (pentlandite: cubic, isotropic, PGE host, floats — versus
pyrrhotite: anisotropic, depressed, low PGE).

**What is built and tested** (**314 passing tests, 7 deliberately-failing "backlog" tests**):
Stokes inversion; fourth-harmonic extinction estimator; a rotation-geometry discriminator; the
acquisition boundary; a synthetic phantom with analytic ground truth; the mask↔series bridge with
mirrored guards; traceable reflectance calibration; a **trust layer** — locality-disjoint
splitting, mandatory trivial baselines, conservative-default abstention, split-conformal coverage
audited per held-out locality, a degraded-input quality gate that refuses each named degradation,
and a provenance type that makes an unlabelled number a type error; an **offline demo path with a
visible refusal**; and a **generated backup demo video**.

**Gate status: weeks 3, 4, 5 and 6 are green.** Week 1 leg (a) passed. Week 1 leg (b) and week 2
are the open ones.

**What is still NOT built** — the seven backlog tests name it exactly:
- Week-1 gate on a public reflected-light rotation series (leg (b) — see below).
- The three domain heads: **fine-chromite entrainment risk, naturally-floating-gangue load,
  stockpile oxidation index.** These are our "processability" outputs and they do not exist yet.
- The falsification test run on real Bushveld data, and texture features controlling for Cr₂O₃
  and pyroxene fraction.
- **`integrate`: an OPC UA server exposing advisory values.** There is a dependency-free
  `AdvisoryRecord` boundary — carrying an `advisory_influenced` endogeneity flag from record zero
  — but **no server**. This is the brief's "integrates with … controls" deliverable and it is
  the largest single gap.

**`segment` inside REEFPRINT is a licence-guard backbone declaration, not a trained model.** The
trained segmentation model lives on the KHANYA side. Do not assume REEFPRINT segments anything.

**A positioning decision you must stress-test.** Our `integrate` module deliberately states:
*"Mintek owns MillStar and FloatStar. This is an advisory that replaces a laboratory turnaround,
not a controller that replaces theirs."* That is commercially shrewd — we do not tell the client
their control system is the problem. But the brief's literal words are *"integrates with existing
sorting or flotation controls to provide immediate operational feedback."* Tell us whether
advisory-only satisfies that requirement or quietly under-delivers against it, and how to
position so that it reads as respect for their installed base rather than as a missing feature.

**Week-1 gate, leg (a): PASSED.** On the synthetic phantom, 40.4× separation between the
anisotropic and isotropic phases. This proves the mathematics, not the mineralogy.

**Week-1 gate, leg (b): as of today, NOT RUN — and we only learned that this session.**
We spent three sessions and two machines measuring a geometry verdict on LumenStone S3 v2, the
public archive that ships "XPL rotation sequences". It returned `NEITHER` three times,
reproducibly. Today we found why: **the frames are not registered — the field rotates with the
specimen, so a given pixel is a different physical point in every frame.** Frame-to-frame
correlation decays along the rotated-image control curve (`S3_test_01`: r005 +0.7114 against a
5°-control of +0.6572; r040 +0.3129 against a 45°-control of +0.2929), where a registered
polarimetric series would stay high and flat. The full-codebook extinction run confirms the
damage: anisotropic phases read higher than isotropic in **15 of 29 sections** — coin-flip is
14.5 — with between-section spread **7×** the within-section spread across minerals, and the
estimator's own crossed-polars self-test reading **median 11.01** where ideal pins it at **1.0**.
Naive centred de-rotation does not reliably repair it, so the rotation centre is off-centre and
varies by section.

Read that carefully, because it is the most important fact in this document: **the reproducible
answer was a reproducible bug.** Agreement across machines tested our determinism, not our
validity. Leg (b) has never been run on valid input, and whether the signal survives proper
registration is an open question we have not yet answered.

**KHANYA's segmentation side has real, held-out numbers** on public polished-section data
(LumenStone S1/S2): mean IoU 0.872 / pixel accuracy 93.75% on one held-out evaluation, and a
documented failure — magnetite at IoU 0.000, predicted as background 92.3% of the time. Also
documented honestly: photometric robustness testing showed the model behaves as **"a colorimeter,
not a texture recogniser"**, and grey-world colour constancy failed.

**Our standing rules**, which any design you propose must satisfy: never invent a number and flag
every assumption in code; split by locality never by patch (we measured a patch split flattering
us by **126×**); report the trivial baseline — majority-class *and* metadata-only — beside every
metric; every metric carries a CI at honest *n*; abstention emits a conservative default with a
stated reason, never "unknown", and the type has no field for the previous value so holding the
last setpoint is unreachable; permissive licences only for anything shipped; the falsification
test is a deliverable whose result we publish either way.

**Our falsification test:** H₀ — after controlling for Cr₂O₃ and pyroxene fraction, texture
carries no additional predictive signal. The statistical core is built and tested with
cluster-robust inference grouped by locality. We have real Bushveld borehole geochemistry (1,205
assays, 317 boreholes, CC BY 4.0) giving us the target and part of the baseline — but **no
texture feature and no pyroxene fraction**, and we established by search that no public dataset
pairs polished-section imagery to those assay depth intervals.

## 3 — Constraints that are not negotiable

- **The demo must run fully offline on one laptop.** No network call on stage. This is a hard
  constraint, and it governs every hosting decision below.
- **Hardware budget R0.** Nothing is bought or built. Any rig is a costed design, presented as a
  design, never implied to exist.
- **No proprietary Mintek data.** Public sources only.
- **Permissive licences only** for anything shipped, because the work must be assignable to
  Mintek under a MOTT agreement. GPL is disqualifying for shipped components. Note: our main
  imagery source, LumenStone, has **no named licence** — only informal "free to use in research,
  cite the references" terms — and its companion library is GPL-3.0 (we use the data, never the
  library).
- Team of three across three institutions. One member is currently unavailable. Assume roughly
  two effective people for 19 days.

**Compute and services available:**
- **Kaggle** — 30 GPU-hours per week, on each of two accounts. Already in active use; we have the
  5.2 GB imagery archive and our code mirrored there as private datasets, with a working kernel.
- **Featherless AI, $25 credit**, with Hugging Face connected — inference over a large catalogue
  of open-weight models.
- **AIML API** — additional hosted model access.
- Local: one Windows laptop, **7.9 GB RAM** (this has already been a real constraint — a
  full-resolution frame stack OOM'd locally and had to move to Kaggle).

## 4 — The decisions I need you to make, with reasoning

For each, give a recommendation, the two strongest alternatives, what would change your mind, and
the cost in days.

1. **Model.** Train our own, fine-tune a pretrained backbone, or use a foundation/promptable
   segmentation model? Name specific architectures and specific pretrained weights, with licence
   for each (Apache-2.0 or MIT strongly preferred; note we have deliberately avoided DINOv3 for
   its non-transferable licence and absent patent grant). We have ~60 Kaggle GPU-hours/week
   across two accounts — tell us what is actually achievable in that budget, and what is not.
2. **Housing.** Where does the model live at demo time, given the demo must run fully offline on
   one laptop? Be explicit about the implication for Featherless/AIML — can they be in the
   development loop but not the inference path, and if so what exactly do we use them for?
   Address quantisation/export (ONNX? int8?) and the latency that results.
3. **"Real-time" needs a number.** The brief uses the word. What frame-rate or per-sample latency
   would a judge from a processing plant consider real-time for this application, and what is the
   defensible measurement protocol on our hardware? We currently have **no latency benchmark at
   all** — design it.
4. **The three phases.** The deliverable requires ≥3 distinct mineral phases. Which three (or
   more) should we commit to, given our data and our magnetite failure? What does the accuracy
   report contain, at what honest *n*, with which baselines and which split?
5. **Processability — none of it is built yet, and it is half the brief.** Fine-chromite
   entrainment risk, naturally-floating-gangue load and stockpile oxidation index exist as named,
   failing tests and nothing more. How do we define and defend a "processability" prediction that
   a metallurgist finds credible rather than invented? Ground each in published metallurgy and
   cite it. Then tell us honestly whether to build all three in 19 days or **one, properly** —
   and if one, which.
6. **Plant integration — our largest gap, and an explicit deliverable.** We have an
   `AdvisoryRecord` boundary but no OPC UA server. Design the smallest honest thing that
   satisfies "integrates with existing sorting or flotation controls to provide immediate
   operational feedback" and can be demonstrated live, offline, without a plant. Consider a local
   OPC UA server, a simulated flotation response consuming our mineralogy output, and a setpoint
   recommendation with visible abstention. Tell us exactly how to label the simulated parts so it
   reads as rigour rather than as a mock-up. Note a licence trap we have already flagged
   internally: `asyncua` is LGPL-3.0, which we hold is fine on a general-purpose machine but
   **not** on a sealed appliance, because anti-tivoisation would make that deliverable
   unassignable to Mintek. Confirm or correct that reading, and say what it means for how we
   describe the deployment target on stage.
   Also address the **endogeneity problem** we have already built a flag for: once an advisory
   influences plant operation, the plant data it later trains on is no longer observational. Our
   records carry `advisory_influenced` from record zero. Tell us whether a judge will see that as
   sophistication or as an admission, and how to present it.
7. **Agents.** Is a multi-step agent system justified here, or is it complexity that costs us
   credibility with an industrial audience? If justified, specify each agent's exact role, why a
   deterministic component could not do it, and how the no-LLM-computes-a-mineralogical-value rule
   is enforced structurally rather than by policy.
8. **Leg (b), the polarimetry.** Given 19 days and the registration finding: is fixing
   registration on the critical path, or is it a research thread that runs beside the submission?
   If we fix it, specify the method concretely. If we drop it, tell us what the differentiating
   claim becomes instead — because reflectance-plus-CNN is what every other team will submit.

## 5 — Things I suspect are wrong. Attack these specifically.

- The polarimetry story may be **too deep for the room**. Judges may be metallurgists and
  technologists, not optical physicists. Is our differentiator legible in 10 minutes?
- We may be **solving a harder problem than the brief asks**, and losing to a team that did the
  literal thing well. Say so if you think it.
- Our abstract, already submitted, says the system "abstains and **holds the last-known-good
  setpoint**". We have since concluded that holding the last setpoint is the *worst* available
  action at an ore transition, and our code makes it structurally unreachable. We must reconcile
  this publicly. Draft the framing.
- We may be **over-indexed on internal rigour** — provenance types, guards, falsification — that
  judges never see. How much of it is scoreable, and how do we make the rest visible in the ten
  minutes without turning the talk into a methods lecture?
- Our headline honest result may read as **"it didn't work."** Tell us how to present a withdrawn
  verdict and a registration bug as evidence of engineering maturity without sounding defensive —
  or tell us to leave it out entirely and why.

## 6 — What you must produce

1. **Requirements traceability matrix.** Every literal requirement in the brief → what we have
   today → the gap → what closes it → days → owner. Flag anything that cannot be closed in 19.
2. **Verdict, in one paragraph, up front.** Do we win with this? If not, what changes.
3. **The redesign**, in whatever depth it needs: architecture, data flow, model choice, the
   inference path, the trust layer, the plant interface, and the UI.
4. **The UI and software showcase spec.** Screen by screen. What a judge sees, in what order,
   what they click, what changes on screen, and what the system does when it refuses to answer.
   Include the empty, loading, degraded and abstaining states — we care more about those than the
   happy path.
5. **The demo choreography.** A 10-minute beat sheet with timings, tied to what scores. Name the
   single moment intended to make a judge sit up, and justify why it will.
6. **A 19-day plan** with a hard feature freeze, what gets cut first, and a submission dry-run at
   least a day early.
7. **An accuracy report template** we can fill — the exact tables, splits, baselines and interval
   arithmetic, so we cannot accidentally report something flattering.
8. **A failure drill.** What breaks on stage, what the backup is, and what we say while it breaks.

## 7 — Now the part I did not ask for. Cover it anyway.

- **IP and disclosure.** The competition runs IP through MOTT contractual agreements. We have been
  publishing to a public GitHub repository and uploading datasets and models to Kaggle and Hugging
  Face. Tell us plainly whether public disclosure before an IP agreement damages patentability or
  our negotiating position, what we should make private *today*, and what we should keep public
  because commit history is our originality defence. These pull in opposite directions — resolve
  the tension, do not just name it.
- **Licence chain-of-title for a deliverable that transfers to Mintek.** Walk the chain: training
  data (LumenStone, *no named licence*), pretrained weights, every dependency. Where is the
  assignment blocked? What do we have to replace, relicense, or get in writing — and how fast can
  a permission email realistically come back?
- **Judging rubric.** We do not have one. Infer the most probable scoring dimensions for a
  state-owned minerals research organisation running a grad hackathon, weight them, and score us
  against them honestly. Then tell us what to do differently.
- **The competition we will actually face.** Imagine the three strongest rival submissions to this
  specific problem statement. Describe them concretely. Then tell us where each beats us and how
  we counter-position without simply claiming to be more rigorous.
- **The metallurgist's objection.** Write the hardest question a Mintek process metallurgist asks
  in Q&A, and the answer that survives it. Then the second-hardest.
- **Scale and deployment reality.** A plant runs 24/7 in dust, vibration and variable light, on
  ore that drifts. What breaks about our approach in month two, and what in our design shows we
  thought about it?
- **What "and more" looks like.** The brief asks for three phases, an accuracy report and a
  demonstration. Tell us the one or two additions that make a judge say *we did not ask for this
  and now we want it*, that are achievable in 19 days, and that do not jeopardise the required
  deliverables. Rank them by ratio of impressiveness to risk.
- **Anything we have not thought of.** You have the full picture above. Use it.

Begin with the verdict paragraph. Then the traceability matrix. Then everything else.
