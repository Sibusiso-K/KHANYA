# Judge-ready product workplan — 14 September 2026

This is the active presentation-readiness backlog for KHANYA / REEFPRINT. It
translates the competition brief, Mintek's published priorities and the current
repository evidence into work that can be demonstrated to judges. It does not
replace `WORKBOARD.md` as the cross-branch engineering record.

## Verdict

The repository contains a working computer-vision prototype and several pieces
of production-shaped engineering. It is not yet a production-ready mineral
processing product. The honest and competitive position is:

> **KHANYA is an offline, production-shaped mineral-characterisation prototype:
> it segments three sulphide phases in a reflected-light micrograph, derives
> traceable image measurements, and is being connected through a real OPC UA
> advisory interface to a separately labelled simulated plant consumer.**

Production readiness requires target-ore validation, a representative sampling
and preparation workflow, performance within an agreed process deadline,
commissioned decision limits, operational reliability evidence, cybersecurity
review and licence/transfer clearance. None can be replaced by presentation
wording. The competition target is therefore a coherent, working product
demonstration whose limits and path to deployment are visible.

## Competition and category

### What is verified for 2026

Mintek describes the 2026 convention as a platform for emerging researchers to
advance practical, research-driven mineral and metallurgical solutions. Its
published themes include:

- critical minerals: sustainable extraction and beneficiation;
- emerging technologies: artificial intelligence, process modelling and
  advanced extraction methods;
- energy and processing efficiency; and
- sustainability and the circular economy.

Sources:

- [Mintek's 2026 convention announcement](https://mintek.co.za/media/news/mintek-inviting-young-innovators-to-2026-science-conventionmintek-inviting-young-innovators-to-2026-science-convention.html)
- [Mintek-SCi 2026 information and registration](https://mintek.co.za/mintek-sci/programme/mintek-sci-%28science-convention-of-innovators%29.html)
- [Mintek's current PGM-industry priorities](https://mintek.co.za/media/news/mintek-calls-on-pgm-industry-to-engage-on-future-technologies-and-solutions.html)

The exact 2026 event slogan was not found in the official pages checked on 14
September. **"The Next Frontier: Emerging Scientists Driving Change" was the
2025 theme. Do not label it the 2026 theme without a 2026 source.**

### Where this entry belongs

The hackathon challenge area supplied to the team is **AI for Mineral
Processing**, Problem 3: **Computer Vision for Real-Time Mineralogical
Characterisation**.

Within the broader Mintek-SCi programme it fits primarily under **Emerging
Technologies**:

- computer vision and supervised AI;
- deterministic mineral-image measurement;
- process modelling; and
- process-control integration through an advisory interface.

It fits secondarily under **Critical Minerals / beneficiation** because the
intended deployment is PGE-bearing Bushveld ore. That is an industry target,
not a validation claim: the shipped segmentation checkpoint is trained and
evaluated on LumenStone S2, a Norilsk layered-ultramafic analogue, and has never
been tested on Bushveld ore.

### Judging criteria

The 2025 Mintek hackathon FAQ names Innovation, Feasibility, Impact, Technical
Execution and Presentation Clarity. No official 2026 judging rubric was found
in the material checked, so use these as a planning surface and verify them
against the team's 2026 competition pack. Source: [Mintek hackathon FAQ](https://mintek.co.za/site_content/content/documents/mintek90/mintek-grad-hackathon-faq.pdf).

| Criterion | What judges must be able to see | Evidence available now | Gap to close |
|---|---|---|---|
| Innovation | Mineral maps become guarded, traceable operational advice | Decision-gap analysis, abstention work, polarimetry research | One coherent end-to-end demonstration |
| Feasibility | Offline operation on ordinary plant IT with a real interface | Offline dashboard, CPU benchmark, OPC UA proof on `reefprint` | Full-image latency misses the target; branches are not wired together |
| Impact | A plant-relevant decision opportunity and credible path to benefit | PGE context and image-derived association proxy | No paired flotation outcomes or commissioned economic result |
| Technical execution | Named model, held-out phase metrics, failure handling, real transport | DeepLabV3-ResNet50, per-image reports, tests, OPC UA | Locality-independent intervals/baselines and integrated release test |
| Presentation clarity | One problem, one product, one live journey, explicit evidence scope | Dashboard and draft pitch | Two-name tax, stale documents and an incorrectly described OOD demonstration |

## The computer-vision model judges should see

The active model in `src/segmentation/model.py` is:

| Field | Value |
|---|---|
| Task | Five-class semantic segmentation |
| Architecture | **Torchvision DeepLabV3 with a ResNet-50 backbone** |
| Initial weights | `DeepLabV3_ResNet50_Weights.DEFAULT`; pin and report its explicit enum/revision before release |
| Fine-tuning data | LumenStone S2 v2 reflected-light polished-section images |
| Training regime | Native-resolution 512×512 balanced patches, cross-entropy loss |
| Inference | Overlapping/sliding 512×512 windows assembled into a full-section mask |
| Outputs | Background, chalcopyrite, magnetite, pyrrhotite and pentlandite |
| Demonstrated successes | Nonzero held-out IoU for chalcopyrite, pyrrhotite and pentlandite |
| Demonstrated failure | Magnetite IoU 0.000; the checkpoint predicts no magnetite pixels |

The previous documentation called this **DeepLabv3+**. That is inaccurate: the
code calls torchvision's `deeplabv3_resnet50`, which implements DeepLabV3. Use
the exact model name on screen, in the report and in the pitch.

The dashboard must show a compact model card beside the active sample:

> **Model:** DeepLabV3 · ResNet-50
>
> **Checkpoint:** KHANYA S2 native-patch model
>
> **Training domain:** LumenStone S2 v2 · public research dataset
>
> **Inference:** offline on this laptop
>
> **Scope:** Norilsk analogue; Bushveld validation pending

Before feature freeze, replace the human-readable checkpoint label with a short
cryptographic hash derived from the actual file and include the same hash in
the accuracy report.

## The live product story

The judge should experience one continuous causal chain:

1. **Select a mineral image.** The presenter selects a previously unseen,
   eligible reflected-light micrograph from a clearly labelled demonstration
   set. If no microscope/camera exists, say "select a micrograph" rather than
   "scan the mineral live".
2. **Validate the input.** Show format, dimensions, dataset/domain eligibility,
   scale availability and model/checkpoint identity. A decoder check alone is
   not a domain check.
3. **Actively segment it.** Display real progress as tiles are processed. Show
   the uploaded image and predicted phase mask side by side.
4. **Select and quantify phases.** Let the judge select a phase in the legend
   to highlight it; show area fraction, pixel count and class-specific evidence.
   This is a UI selection over model output, not a second AI decision.
5. **Analyse processability.** Compute the apparent 2D sulphide association
   index with its denominator, assumptions and eligibility state visible.
6. **Publish an advisory.** Send a versioned, expiring record over the real
   local OPC UA server.
7. **Consume it separately.** A labelled simulated plant client acknowledges
   the exact record and changes an illustrative simulated parameter.
8. **Show failure behaviour.** Submit a degraded, stale or explicitly
   unsupported input. The consumer must reject or abstain visibly and must not
   treat the preceding advisory as fresh.

The one-line stage claim is:

> "The image analysis is live and local, the OPC UA transport is real, and the
> plant is simulated because this prototype is not connected to an operating
> circuit."

## What "real time" can honestly mean here

Current measured segmentation performance on the named Windows AMD64 laptop:

| Path | Honest n | Mean | p95 | Scope |
|---|---:|---:|---:|---|
| One 512×512 model forward pass | 60 | 2.64 s | 3.60 s | Model only |
| One 3396×2547 section, sliding-window inference | 6 | 162.3 s | 195.7 s | Inference only |

Source: `reports/segmentation_latency.json`.

The previously proposed targets were p95 ≤5 seconds for a 512×512 field and
p95 ≤30 seconds for a full native section. The patch model-forward stage meets
the first target; the complete field-to-screen path has not been measured. The
full-section path misses its target by approximately 6.5×.

For the ten-minute presentation, implement **Live Field Mode**:

- predeclare a fixed 512×512 field as the live unit;
- decode and preprocess a real image, then run one fresh inference;
- show a visible timer and never use cached output as a fresh timing result;
- compute phase measurements, advice, OPC UA publication, client receipt and UI
  render in the same timed transaction;
- report end-to-end median, p95, maximum, failures and peak memory;
- use the full-section recording only as a separately labelled batch example.

Calling the cached three-image backup video "real-time inference" would be
misleading. It is a valid backup recording of real previously computed results.

An active full-section tile visualisation can show the model working, but it
does not reduce latency. If used, distinguish "progress visible in real time"
from "analysis completed within the process deadline."

## Industry applicability

The plausible deployment is a **supervisory mineralogical advisory**, not a
closed-loop autonomous controller:

```text
plant sample -> preparation and reflected-light imaging -> KHANYA segmentation
-> phase/association measurements -> eligibility and uncertainty -> OPC UA
-> historian / metallurgist / existing advanced-control layer
```

This fits Mintek because it sits between Mineral Processing & Characterisation
and Mining, Materials & Automation. It complements installed control products
by producing a traceable mineralogical input rather than claiming to replace
them.

Applicability must be demonstrated through these contracts:

- **Sample contract:** preparation, illumination, magnification, scale,
  orientation and sample/process timestamps.
- **Model contract:** supported ore/image domain, exact checkpoint, class set,
  preprocessing and known failures.
- **Measurement contract:** quantity, units, denominator, method, uncertainty
  and validity interval.
- **Control contract:** advisory ID, timestamp, expiry, policy version,
  acknowledgement and override state.
- **Operations contract:** offline startup, health state, logs, restart,
  version rollback and a declared fallback procedure.

The product is applicable to industry when these contracts are visible and
testable. It becomes production ready only after target-site validation and
commissioning.

## Remaining issues, in execution order

Effort estimates are planning estimates for part-time work, not measured
durations.

| Priority | Issue | Required work | Acceptance test | Owner | Effort |
|---|---|---|---|---|---:|
| P0 | Main dashboard stops before plant integration | Bridge one KHANYA result into `AdvisoryRecord`, publish through the REEFPRINT OPC UA server and show independent client acknowledgement | Fresh record applied to simulated parameter; stale/refused record not applied; UI displays both events | Both | 3–4 PT-days |
| P0 | No true image-level OOD or quality gate in KHANYA | Either integrate the relevant REEFPRINT gate with a validated reference or remove OOD wording and call the current state a low-payload refusal | Unsupported/degraded cases have predeclared causes; ordinary low payload is never labelled OOD | Sibusiso | 1–3 PT-days |
| P0 | Live computer vision is too slow at full resolution | Implement Live Field Mode and measure the whole field-to-client transaction | Fresh, uncached eligible 512×512 field completes within the declared target at measured p95 | Sibusiso | 2–3 PT-days |
| P0 | Model identity is absent from the result UI | Display architecture, training domain, checkpoint ID and offline runtime status | Screenshot and render test show the same identity as the loaded artifact | Sibusiso | 0.5–1 PT-day |
| P0 | Accuracy report lacks independent grouping and required baselines | Establish specimen/locality metadata if available; add majority, metadata-only and colour-only baselines; compute group-level intervals only at an honest grouping level | Report includes all denominators and says "unavailable" where independence cannot be established | Sibusiso | 3–4 PT-days; metadata dependent |
| P0 | Data/weight transfer rights unresolved | Obtain written LumenStone permission or isolate restricted artifacts; pin upstream weight licence and all shipped dependencies | Release manifest contains permission references and exact dependency/weight licences | Both | 1–2 PT-days plus external response |
| P1 | Advice contains uncommissioned thresholds and ore-objective assumptions | Mark every threshold as assumed/configured; remove universal Bushveld pyrrhotite-rejection language; expose policy version | UI and report cannot display an assumed threshold as validated plant guidance | Lethabo/domain lead | 1–2 PT-days |
| P1 | Processability proxy is not validated against flotation outcome | Keep the association metric as a structural proxy; show its derivation and define the target-site validation experiment | No recovery, grade, reagent or energy improvement is stated as measured | Both | 1 PT-day documentation |
| P1 | Cross-branch status overstates completed integration | Update `WORKBOARD.md` on `reefprint`, mirror it to `main`, then point stale status documents to it | Scoreboard reflects measured segmentation latency and distinguishes component proof from integrated demo | Both | 0.5–1 PT-day |
| P1 | Backup demo mislabels the S1 result as OOD detection | Rewrite the script after the P0 gate decision; label cached results and the reason for refusal exactly | Spoken script matches implemented condition and timing mode | Sibusiso | 0.5 PT-day |
| P1 | No release-level reliability exercise | Run repeated offline startup, inference, OPC UA disconnect/reconnect, stale record, bad image and missing checkpoint drills | One signed run sheet records results and exact artifact hashes | Both | 2 PT-days |
| P2 | Full native-section latency remains unsuitable for the live pitch | Profile tile overlap, CPU threading and ONNX FP32/INT8 only after Live Field Mode is stable | Optimisation retained only if phase metrics and decisions remain within predeclared tolerances | Sibusiso | 2–4 PT-days |
| P2 | Backup video does not yet exist | Record the actual release after integration and model identity are visible | Video plays offline on the presentation laptop and is copied to independent media | Both | 0.5 PT-day |
| P2 | Polarimetry remains research, not mineral validation | Keep it in the architecture/roadmap or appendix unless a valid acquisition passes a predeclared real-data gate | Main three-phase and integration demo does not depend on it | Lethabo | Capped at 2 PT-days |

If time collapses, cut ONNX optimisation, further polarimetry work and decorative
UI work before cutting the OPC UA bridge, live field inference, model identity,
accuracy report, rights register or failure rehearsal.

## Production-readiness claim ladder

Use the strongest claim whose evidence is complete:

| Claim | Minimum evidence | Current status |
|---|---|---|
| Working research prototype | Fresh inference, phase output and measured report | **Supported on S2** |
| Integrated industrial prototype | Above plus real protocol, separate consumer and failure path | Component pieces exist; **not integrated** |
| Pilot ready | Target-site sample workflow, target-ore labels, shadow-mode study and approved operating envelope | **Not supported** |
| Production ready | Commissioning, reliability/SLA, monitoring, security, maintenance, rights and operational ownership | **Not supported** |

The recommended stage phrase is **"production-shaped, offline industrial
prototype ready for a Mintek-led validation pilot."** Use "pilot ready" only
after Mintek or a target plant agrees that the supplied validation package is
sufficient.

## Ten-minute judge path

| Time | What happens | Criterion made visible |
|---|---|---|
| 0:00–0:45 | Define the laboratory-delay problem and the bounded product claim | Impact, clarity |
| 0:45–1:20 | Show the sample contract and exact DeepLabV3-ResNet50 model card | Technical execution |
| 1:20–2:20 | Run fresh Live Field Mode with an on-screen timer | Feasibility, real-time CV |
| 2:20–3:20 | Select/highlight the three detected sulphide phases and show phase evidence | Required model deliverable |
| 3:20–4:20 | Compute and explain the apparent 2D association proxy | Processability, rigour |
| 4:20–5:20 | Publish the advisory over real local OPC UA | Integration |
| 5:20–6:10 | Separate simulated client acknowledges and changes a labelled parameter | Operational feedback |
| 6:10–7:00 | Inject stale/degraded input; consumer refuses it visibly | Innovation, reliability |
| 7:00–8:00 | Show per-class report, magnetite failure, baselines and honest n | Technical credibility |
| 8:00–9:00 | Show the plant deployment path and what Mintek validation supplies | Industry applicability |
| 9:00–10:00 | State the specific ask and close with measured capability | Impact, clarity |

The memorable moment remains the separate consumer refusing an invalid or stale
result. It should happen after judges have seen the model run, so it reads as a
working safety behaviour rather than a substitute for working computer vision.

## Feature freeze exit criteria — 25 September

Do not freeze until all mandatory items are either passed or explicitly removed
from the stage claim:

- one-command offline launch from a clean release folder;
- exact model and checkpoint identity displayed;
- fresh Live Field Mode measured end to end;
- three sulphide phase outputs and magnetite failure visible in the report;
- real OPC UA publish/read/acknowledge transaction from a KHANYA result;
- explicit simulated-plant labelling;
- tested stale, degraded, missing-artifact and disconnect states;
- accuracy report with honest grouping limits and baselines;
- licence/permission register for every shipped artifact;
- actual offline backup video; and
- ten-minute rehearsal completed with at least one minute of recovery margin.
