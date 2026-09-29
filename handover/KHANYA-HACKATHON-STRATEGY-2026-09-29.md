# KHANYA: the recommended hardware-free Problem 3 submission

29 September 2026. Research and design recommendation, incorporating the user's full brief. Existing code was inspected, including live GitHub main at `9181668`; no implementation, retraining or performance reproduction was performed in this investigation.

## The decision

Keep the existing computer-vision core. Present KHANYA as **a microscope-to-control assistant that identifies mineral phases, measures visible association, and withholds operational changes when evidence is unreliable**.

Use three sulphide targets: **chalcopyrite, pentlandite and pyrrhotite**, on the existing LumenStone S2 reflected-light microscopy task. This is the lowest-risk route to the exact deliverables because the repository already contains a trained-model workflow, phase metrics, an offline dashboard, association calculations and an OPC UA software seam. It does not establish performance on South African ores, and the model's magnetite failure must remain visible.

The pivot worth making is in emphasis: from broad mineral identification and attractive colored masks to **how image errors affect process decisions**. Do not pivot to field exploration, a new sensor modality or an unvalidated 3D ore body immediately before the recorded October 1 deadline.

No method can honestly guarantee a win or establish universal novelty from a quick search. Mineral segmentation, uncertainty-based annotation and flotation control all have prior art. The competitive contribution should be a reproducible, transparent combination tested against simple baselines—not the statement that nobody has used AI for this before.

## Why these phases and data

The public LumenStone S2 dataset supplies polished-section images and pixel labels for a layered-ultramafic mineral assemblage containing the three chosen sulphides and magnetite. The official page grants research use with citation; this is not the same thing as an unrestricted commercial/redistribution licence. The current code already uses this domain. [Dataset and terms](https://imaging.cs.msu.ru/en/research/geology/lumenstone)

Define an explicit illustrative Ni-Cu sulphide processing objective: distinguish the phases and quantify their apparent associations before suggesting additional characterization or regrind review. Any mineral-to-payload/reject mapping must be stated as specific to the chosen process scenario. In particular, pyrrhotite is not universally valueless, and sulphide identification does not measure PGE grade.

S1 is a useful secondary test of generalization and lighting robustness, with its own checkpoint and codebook. A higher S1 metric does not make S1 interchangeable with S2. V1 re-imaging belongs to S1 and lacks ground-truth masks. Use V1 for repeatability, not phase accuracy, and only use verified corresponding fields.

## The actual pipeline

```text
Held-out public microscope image / documented image replay
    → modality and capture-quality checks
    → KHANYA DeepLabV3–ResNet-50 segmentation
    → colored phase mask + unknown/quality display
    → phase area fractions + apparent 2D association + contact geometry
    → calibrated uncertainty / decision sensitivity
    → proposed process action, or request review / reacquisition
    → explicit controller interlocks and approval
    → real local OPC UA exchange
    → simulated plant control state and acknowledgement
```

The image replay substitutes for a microscope feed. New inference must actually run on the current image; replayed input is not live acquisition. A saved mask can support a clearly labelled backup, but cannot be timed as fresh inference. Measure model-load, preprocessing, inference, measurement, transport and display latency separately; show hardware and image size.

## The important existing gap

`dashboard/opcua.py` already publishes measurements such as `association_index` and `model_confidence` through a real local server and a simulated consumer. These are observation values. **A visible plant-parameter demonstration still needs a documented mapping from an accepted advisory to a process-control state.** A transport acknowledgement alone does not demonstrate better processability or recovery.

For the first credible control demonstration, add a simulated **regrind request/enable state**, with reason, timestamp, expiry, approval and acknowledgement. The default on uncertainty is to inhibit a new automatic adjustment and request review; the actual fail-safe response in a real plant would require site design. Test accepted, uncertain, stale and disconnected paths. Do not present an arbitrary reagent dosage or numerical grind setpoint as calibrated plant guidance.

If a judge needs a continuously valued parameter, use an explicitly illustrative bounded regrind-split setpoint in the simulator. Publish its assumed mapping and limits and keep that scenario apart from scientific accuracy results. The software-control demonstration is valid evidence of integration; its hypothetical setpoint is not a measured optimum.

## The strongest demonstration

1. Select a held-out image. Run fresh inference and show the three sulphides on the original image with a clear color legend.
2. Click an ambiguous region. Highlight its contacts and show how the image-derived association contributes to the proposed action. Keep area percentage and confidence separate.
3. Compare the predicted mask with the expert mask, then run the same frozen decision policy on each. This exposes when perception changes the action. The expert-mask result is a **reference-policy action**, not a proven metallurgical optimum.
4. Show a controlled exposure change, or a verified real re-imaging pair using the appropriate checkpoint. Re-run the model. Display any resulting change in mask, composition and advice.
5. Demonstrate the proposed quality/refusal gate: if evidence falls outside its validated conditions, the controller receives an explicit refusal and does not accept a new adjustment. This is an intended improvement; it has not been implemented or validated by this investigation.
6. Restore acceptable evidence, issue a supported advisory, and show the simulated regrind state changing after acknowledgement. Expire the record and demonstrate rejection of the stale update.

The repository already contains relevant evidence for step 4: 5/10 V1 pairs with the S1 model and 8/12 synthetically darkened S2 sections changed advice in a small centre-crop study. These are reported fragility findings, not independently reproduced here, and not a forecast of deployment failure rates. [Report](https://github.com/Sibusiso-K/KHANYA/blob/9181668cffd9350211a9a8a2cf0b44c80f8deaee/reports/ILLUMINATION-STABILITY-2026-09-15.md)

A clear presentation line is: **“We show which mineral decisions are supported, which image errors would change the action, and when the system must ask for better evidence.”**

## A feasible distinctive extension: decision sensitivity

An attractive optional feature is a **decision sensitivity overlay**. Highlight uncertain image regions that could change the downstream recommendation, rather than highlighting every uncertain pixel equally.

For a transparent prototype, take a small number of genuinely ambiguous connected regions, substitute plausible candidate labels under a documented scenario rule, recompute the same geometry/decision pipeline and flag action-changing regions. This is a counterfactual sensitivity analysis. Unless candidate sets and probabilities have been calibrated, it is not a probability map and must not be presented as one. Reject physically incompatible or unsupported candidates and never use arbitrary recoloring as evidence of a real mineral.

Compare it with a simple confidence/entropy overlay at a fixed number of reviewed regions: how often does review expose an action-changing error? Use held-out samples. It is an extension worth testing only after the three-phase accuracy report and complete control demo work. Active learning and mineral uncertainty already have prior work; this specific operational value must be established by an ablation, not claimed from its name. [Prior art](https://isprs-archives.copernicus.org/articles/XLVIII-2-W9-2025/123/2025/)

## Free tools and simulator choice

| Job | Recommended route | What it proves |
|---|---|---|
| Image data | LumenStone S2; S1/V1 for their separate validated uses | Phase accuracy against supplied masks; re-imaging consistency where available |
| Training/inference | Existing PyTorch/Torchvision code and project checkpoint | Your actual mineral segmentation, with checkpoint provenance |
| Image measurements | Existing NumPy/scikit-image pipeline | Mask geometry, area and 2D association |
| Industrial interface | Existing `asyncua` server/client and simulated consumer | A real protocol exchange, expiry and acknowledgement on one laptop |
| Demonstration simulation | Small deterministic controller/replay harness | How a measured output causes or inhibits a simulated parameter change |
| Charts/interface | Existing offline dashboard, locally bundled plotting/3D assets | Inspectable results without venue internet |
| Process-model research | Evaluate MODSIM availability or a cited reduced-order flotation model later | Scenario studies only until inputs and model parameters are validated |

[FreeOpcUa](https://github.com/FreeOpcUa/opcua-asyncio) supplies an open-source client and server. The MODSIM publisher currently advertises an open-source release, but its linked repository, build and licence were not verified in this investigation; do not make it a last-minute dependency. [Publisher](https://www.mineraltech.com/MODSIM/)

An open-source solver does not make a flotation prediction accurate. Recovery depends on the material, particle size/exposure, kinetics, reagents, operating conditions and calibration data. Published work using economic model predictive control relied on a calibrated, validated dynamic model and a laboratory cell. Do not borrow its performance numbers for KHANYA. [Flotation-control research](https://arxiv.org/abs/2410.19661)

The recommended short-term simulator is intentionally narrow: replay real held-out images, apply the frozen policy, exercise the actual message exchange and plot the simulated control state. It needs no invented recovery curve. A later kinetic simulator can show hypothetical consequences with parameters and uncertainty disclosed.

## Improving accuracy without gambling the submission

First reproduce the frozen checkpoint on the exact evaluation images and save code version, checkpoint hash, dataset version and evaluated sample IDs. The repository's newest corrections demonstrate why all four matter.

Then prioritize acquisition consistency: detect poor inputs and evaluate appropriate normalization. An attractive color correction is not automatically scientifically valid; it can destroy diagnostic reflectance differences. Fit/choose normalization on training/validation data and evaluate on held-out data. Do not tune on the 12 S2 test images because earlier reports exposed them.

If there is time and suitable compute, run a separately versioned training experiment with class-balanced patch sampling and a justified loss/augmentation change. Keep the existing checkpoint available. Promote a candidate only after the same held-out evaluation and latency tests. Do not promise that a larger network, SAM or a general vision-language model improves this task without measurements. SAM can assist annotation, but it does not supply mineral identities.

Use specimen-grouped splits where provenance permits; keep overlapping patches and repeat views of the same physical specimen together. If independent specimen identities cannot be established, report that limitation and use the official split without claiming stronger independence. Use an independent calibration set for coverage claims. Unlabelled V1 can test consistency, never establish correctness by itself.

The accuracy report should contain:

- Per-phase IoU, precision and recall; confusion matrix; macro metric with background inclusion stated.
- Phase-area error with its denominator stated; apparent association error against the same calculation on expert masks.
- Reference-policy action disagreements, separated into confident mismatches and explicit refusals.
- Error rate among accepted cases **and** coverage/refusal rate. A system that refuses everything is not useful.
- Lighting/blur/domain-shift results with source and perturbation conditions, plus clean-image acceptance.
- Fresh inference latency at stated image resolution and hardware, preferably a distribution over runs.

The existing magnetite failure remains in the report even if only the three sulphides are emphasized. No new performance value is asserted until rerun.

## Visual direction

Use a linked microscope-to-plant view: large real micrograph and phase overlay on the left; selected-region evidence and association in the middle; a compact schematic process circuit and actual simulated-control state on the right. An uncertainty or decision-sensitivity layer should link a problematic region directly to a withheld action. Pair every color with a mineral label.

Use 3D to orient the viewer within the **simulated process circuit**, if it improves the demo. Keep the actual micrograph plane inspectable. Extruding a 2D phase map may illustrate a concept, but it cannot be called reconstructed internal mineralogy. Geological terrain, FieldMove, QGIS and Leapfrog belong to a later field-to-lab workflow; they do not strengthen the core deliverable enough to justify their integration now.

## Order of work before October 1

1. Reproduce three-phase results and freeze the evidence bundle, checkpoint and working offline demo.
2. Complete one accepted advisory → simulated process parameter → acknowledgement path, plus stale/uncertain refusal.
3. Add capture-quality visibility and a reproducible robustness comparison. Claim prevention only after testing the gate on separate cases.
4. Build the linked visual explanation and record a backup. Add decision sensitivity only if the required path is stable.

This is a recommendation to win on alignment, credibility and a memorable experiment. The investigation does not establish that the proposed improvement works yet, that the system is production ready, that the approach is globally novel, or that it will win the competition.
