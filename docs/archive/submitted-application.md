> **THE RECORD — this is the abstract Mintek accepted. Not superseded, not wrong: it is what we submitted and were judged on.**
> The technical design has since moved on; see docs/01-design-v3.md.

# REEFPRINT — Mintek-SCi Grad Hackathon 2026 abstract

**Challenge Area to select:** Computer Vision for Real-Time Mineralogical Characterisation

**Paste everything between the two rules below into the Abstract field.** It is written as plain text so it survives a web form textarea without broken markdown. Replace anything in [SQUARE BRACKETS] before submitting.

---

REEFPRINT: DISTILLING LABORATORY MINERALOGY INTO REAL-TIME, UNCERTAINTY-AWARE PLANT CONTROL

Team: [TEAM NAME] | University: [UNIVERSITY]
Challenge Area: Computer Vision for Real-Time Mineralogical Characterisation


1. THE PROBLEM, AND THE PART OF IT THAT IS USUALLY MISSED

Mineralogical characterisation by SEM or XRD returns results in days. A concentrator makes decisions in minutes. That latency gap is the stated problem, and it is real. But three further observations shape what we intend to build.

First, mineralogy is a means, not an end. A plant does not act on a phase list; it acts on reagent dose, mill throughput, sorter setpoints and blending decisions. What governs metallurgical recovery is not only which minerals are present but their grain size, locking and association - their liberation characteristics. Composition is the tractable half of the problem. Texture is the valuable half.

Second, on Bushveld ores, overall classification accuracy is actively misleading. UG2 is approximately 50-75 vol% chromite, 15-30% pyroxene and 3-9% feldspar, while the platinum group metals concentrate in base-metal sulphides present at under 1 vol%. A model reporting 97% overall accuracy may have learned to predict "chromite" and missed the entire economic payload. We therefore commit in advance to reporting per-phase recall on the sub-1% sulphide class ahead of any aggregate metric, alongside the trivial majority-class baseline.

Third, the economic urgency is immediate and it is an energy problem. Comminution accounts for over 50% of a typical mine's total energy consumption, and electricity represents 35-40% of ferrochrome production cost. South African ferrochrome exports fell 63% under energy-cost pressure, with one of five Glencore-Merafe smelters operational in February 2026, before NERSA approved a preferential 62 c/kWh tariff in May 2026. The sector supports up to 185,000 direct and indirect jobs. From 1 January 2026 the carbon tax rate rose to R308 per tonne CO2e under Phase 2 of the Carbon Tax Act, rising to R462 by 2030. Every kilowatt-hour of avoidable grinding energy now carries both a tariff cost and a statutory carbon liability. Ore hardness is knowable before grinding - but only if you can see the ore's texture in time to act.

Framed correctly, then: this is not a mineral classification problem. It is a problem of inferring an unobservable, economically decisive ore property from cheap signals, fast enough and reliably enough to move a setpoint.


2. PROPOSED APPROACH: DON'T REPLACE THE LABORATORY - DISTIL IT

Our central design decision is to treat Mintek's automated mineralogy capability not as a dataset but as a teacher.

Every high-fidelity QEMSCAN or SEM-EDS map Mintek has ever produced is ground truth that already exists, already paid for. We propose training a low-cost optical "student" model to reproduce those maps from imagery obtainable in seconds rather than days. Recent published work demonstrates this is achievable: a U-Net trained on plane- and cross-polarised thin sections against QEMSCAN maps as targets reported R-squared above 0.97 on seen facies and 0.88 on unseen facies. That work was performed on carbonate rocks for petroleum applications. To our knowledge it has never been applied to Bushveld Complex ores, and never coupled to a live process control loop.

This reframing matters commercially as well as technically. We are not proposing that students have outperformed a multi-million-rand instrument. We are proposing to convert Mintek's existing instrument archive into a scalable data asset, and to extend the reach of a capability Mintek already owns.

REEFPRINT comprises five stages:

(a) TEACHER INGEST AND REGISTRATION. Spatially register high-fidelity mineralogical maps to cheap-optics imagery.
(b) DISTILLATION. Train a student segmenter to reproduce teacher maps, using weak supervision where only bulk assay labels exist.
(c) TEXTURE TO PROCESSABILITY. Convert segmentation into grain size distributions and mineral association matrices, then into three named metallurgical response variables.
(d) UNCERTAINTY GATE. Emit calibrated prediction intervals and detect out-of-distribution input. Where confidence is insufficient, the system abstains and holds the last-known-good setpoint.
(e) FEEDFORWARD INTEGRATION. Publish setpoint recommendations as a feedforward channel over OPC UA.

On stage (e) we note that Mintek's own StarCS, FloatStar and MillStar advanced process control platform is deployed in over 400 installations across 40 countries, and that feedforward control from feed composition is a documented gap in flotation control, which is predominantly feedback-driven. We are not proposing a competing dashboard. We are proposing a module that fills an identified gap in a platform Mintek already sells.


3. METHODOLOGY AND TECHNICAL STACK

3.1 Mineral phases. Five phases with materially different processing consequences: chromite, orthopyroxene, plagioclase, base-metal sulphide, and alteration minerals (talc/serpentine). This exceeds the required minimum of three. Talc is included deliberately: it is naturally floatable and is a known depressant-demand driver in PGM flotation, so its detection has direct reagent implications.

3.2 Registration. Multimodal registration by mutual information using SimpleITK / itk-elastix. We budget a full week for this. Misregistration silently corrupts every downstream label, and teams that treat it as a preprocessing afterthought train confidently on misaligned targets.

3.3 Student model. A self-supervised DINOv3 backbone with a lightweight decoder, implemented with segmentation_models_pytorch, with SAM-family models providing zero-shot grain boundary proposals as an auxiliary signal. Self-supervised pretraining is the correct response to label scarcity and permits us to begin training on public data before any Mintek dataset is released.

3.4 Weak supervision. Where only bulk XRD or assay values are available, we train through a differentiable abundance head using a learning-from-label-proportions objective. This dissolves the pixel-mask prerequisite that otherwise bottlenecks this class of problem.

3.5 Physics-grounded augmentation. Synthetic mixed spectra generated using Hapke radiative transfer mixing against USGS splib07 and ECOSTRESS reference spectral libraries - physically valid augmentation rather than arbitrary noise injection.

3.6 Processability targets. Three committed, measurable response variables:
  - Liberation at target grind P80, derived from grain size distribution and association matrix via a breakage/liberation model. We will state and quantify the two-dimensional stereological bias rather than conceal it.
  - Reagent demand proxy, from floatable sulphide surface area per tonne.
  - Grindability proxy mapped to specific comminution energy in kWh/t via a Bond/Morrell work index relation.

3.7 Uncertainty and calibration. A five-member deep ensemble for epistemic uncertainty; split conformal prediction (MAPIE / crepes) for distribution-free coverage guarantees; Mahalanobis distance in latent space as an out-of-distribution gate; and Direct Standardisation calibration transfer, borrowed from chemometrics, to handle illumination drift and sensor ageing.

3.8 Plant simulation for closed-loop proof. A flotation circuit modelled with Kelsall two-rate first-order kinetics producing grade-recovery curves, plus a Bond/Morrell comminution energy model. We generate a realistic 30-day feed series by sampling published Bushveld composition ranges across UG2, Merensky and Platreef, with step changes and drift, then replay it through (i) a feedback-only baseline and (ii) our feedforward channel.

3.9 Integration and standards conformance. Setpoint recommendations are published via an OPC UA server (asyncua) with an address space modelled on OPC 40560, the OPC Foundation's Companion Specification for Mining. The digital representation is delivered as an IEC 63278 conformant Asset Administration Shell using the Eclipse BaSyx Python SDK, exportable as an AASX package openable in standard industrial tooling.

Critically, and consistent with IEC 61511's requirement for separation between safety instrumented systems and control or advisory layers: REEFPRINT is a supervisory advisory layer sitting above the basic process control system and strictly outside the SIS boundary. It writes to a read-only advisory namespace. No write path to any safety instrumented function exists. Operator acknowledgement is required before action. Loss of REEFPRINT degrades the plant to existing control with no safety consequence.

3.10 Edge deployment. ONNX export to a Hailo-8L accelerator (13 TOPS) on a Raspberry Pi 5 AI HAT+, demonstrating real-time inference on plant-representative hardware rather than a laptop GPU.

3.11 Economic layer. Every result is converted to rands using gazetted South African coefficients only: Eskom's published Schedule of Standard Prices 2026/27 for Megaflex time-of-use bands and demand charges; the DFFE gazetted grid emission factor of 0.94 tCO2e/MWh; and the Carbon Tax Act Phase 2 rate of R308/tCO2e. No economic coefficient in our model is invented.

3.12 Governance. A central model registry (MLflow) recording every model version, its training data hash, intended use and out-of-scope use, mapped to the relevant clauses of ISO/IEC 42001, the international AI management system standard.

3.13 Physical demonstration rig. A self-funded bench rig of approximately R6,000: Raspberry Pi 5, HQ camera, a light dome with narrowband LEDs at wavelengths selected by our own information-gain band-selection analysis, crossed polarising film for petrographic imaging, a rotating stage, and an AS7341 11-channel spectral sensor for verification. The band-selection output is itself a deliverable: a hardware bill of materials specifying the minimum viable sensor that recovers the majority of the discriminative power of a full hyperspectral instrument, at a fraction of the capital cost. This has direct relevance to junior miners and to tailings retreatment operations that cannot justify hyperspectral capex.

3.14 Data risk mitigation. We will freeze our complete evaluation harness in Week 1 using public data - MUMDMC2025 (14,400 photomicrographs, five mineral classes, plane- and cross-polarised at 72 rotations), USGS splib07, ECOSTRESS and RockSL - before any Mintek dataset arrives. Our architecture is label-modality agnostic by design. If no dataset is released, the demonstration runs on public data. If a small dataset is released, self-supervised pretraining plus physics-based synthetic mixing is precisely the correct architecture for that regime. If a large dataset is released, the same code scales and we additionally publish an accuracy-versus-labelled-area curve, which quantifies for Mintek how much automated mineralogy instrument time a distilled model can displace.


4. EXPECTED OUTCOMES AND DELIVERABLES

Against the stated requirements:

(i) A trained model identifying five distinct mineral phases (requirement: at least three), deployed to edge hardware.

(ii) An accuracy report comprising: per-phase IoU and F1 with confusion matrix; per-phase recall on the sub-1% base-metal sulphide class reported ahead of aggregate accuracy; the trivial majority-class baseline stated explicitly; abundance R-squared against the teacher instrument; conformal coverage curves (empirical versus nominal); leave-one-orebody-out cross-validation testing UG2-to-Merensky generalisation; and degradation under an adversarial domain-shift benchmark of our own construction simulating dust, water film, vibration blur, lamp colour-temperature drift and calibration-tile drift. Domain shift is the dominant field failure mode for deployed vision systems in mineral processing and is rarely addressed at proof-of-concept stage. We intend to release this benchmark openly.

(iii) A demonstration of plant parameter adjustment: closed-loop replay against a feedback-only baseline, reporting change in recovery, change in kWh/t, change in reagent consumption, each converted to rands per annum and tonnes CO2e per annum using the gazetted coefficients above.

Additional deliverables: the minimum-viable-sensor bill of materials; the open domain-shift benchmark; an AASX digital twin package; model cards and a one-page integration guide targeting the StarCS interface; and the accuracy-versus-labelled-area curve.


5. HACKING TIMELINE (SEPTEMBER 2026)

Week 1 - Foundation. Public-data spine established; evaluation harness frozen and version-controlled before any Mintek data is ingested; self-supervised pretraining initiated; registration pipeline built and tested; plant simulator implemented. Gate: harness reproduces a published baseline result.

Week 2 - Distillation. Mintek data ingest and registration; weak-supervision training loop; five-phase segmenter trained; three processability heads implemented; bench rig v1 assembled and radiometrically calibrated. Gate: abundance R-squared against teacher exceeds threshold on held-out samples.

Week 3 - Trust and integration. Conformal calibration and OOD gate; domain-shift benchmark constructed and evaluated; ONNX export and Hailo edge deployment; OPC UA advisory channel; closed-loop A/B results generated. Gate: empirical conformal coverage within tolerance of nominal; zero silent failures under degraded input.

Week 4 - Consolidation. Feature freeze; ablation studies including band selection and full-versus-selected spectral sets; accuracy report compiled; AAS package validated; backup demonstration video recorded; adversarial Q&A rehearsal against a hostile internal reviewer.

Submission by 1 October; live demonstration 1-2 October at Mintek, Randburg.


6. TEAM AND ROLE ALLOCATION

Our team comprises [N] members: [N] Computer Science students with data science and machine learning specialisation, one Electrical Engineering student with data science and ML capability, and one Business Informatics student with AI engineering capability and prior metallurgical engineering study. Collectively the team holds six top-three placings across competitive hackathons and recently placed in the top six at Discovery GradHack.

  - Domain lead (Business Informatics / prior metallurgical engineering): orebody and process narrative, phase definitions, processability target specification, plant-adjustment presentation, and internal red-teaming.
  - Sensing and edge (Electrical Engineering): band selection, LED dome design, radiometric normalisation and calibration transfer, ONNX quantisation, edge deployment, OPC UA hardware-in-the-loop.
  - Distillation core (CS): registration, segmentation architecture, weak-supervision objective.
  - Decision layer (CS): processability heads, liberation model, conformal gate, plant simulator, integration shim.
  - Evaluation and reproducibility (CS): frozen harness, domain-shift benchmark, CI, model registry, demonstration interface.


7. ORIGINALITY, PROVENANCE AND INTELLECTUAL PROPERTY

All work will be developed by the named team members. We will maintain a public-history version-controlled repository from day one, including failed experiments and reverts, providing verifiable development provenance. Our evaluation harness is frozen on public datasets in Week 1, timestamped before any Mintek data is received. All prior art on which we build - notably published work on QEMSCAN-supervised thin-section segmentation, conformal prediction methods, and Hapke spectral mixing - will be explicitly cited. We acknowledge and accept that intellectual property arising will be governed by contractual agreement managed by the Mintek Office of Technology Transfer, and we have structured the work as a modular, integrable capability precisely to make that pathway straightforward.


8. WHY THIS SOLUTION MATTERS

A model that is accurate but unaccountable will never be commissioned on a live plant. The differentiating commitment in REEFPRINT is that the system knows when it does not know, says so, and safely declines to act - and that every claim it makes is priced in rands using coefficients drawn from South African statute and gazette. We are building for the conditions the South African minerals sector actually faces in 2026: constrained energy, statutory carbon liability, declining head grades, and an urgent national interest in retaining beneficiation capacity onshore.

---

## Notes before you submit

**Length.** This runs roughly two pages of dense plain text — at the top of the stated 1–2 page guidance. If you want it shorter, cut in this order: section 7 (compress to three sentences), then 3.12, then 3.5. Do not cut sections 1, 2, 4 or 5.

**Placeholders to replace:** `[TEAM NAME]`, `[UNIVERSITY]`, `[N]` in section 6 (twice — total members, and number of CS students).

**One decision left.** Section 6 currently describes five members. If you fill the sixth seat with a geology, mineralogy or chemical engineering student before you submit, add them and say so — it materially strengthens the domain-credibility case.

**Also required today:** university permission letter, and ID/passport plus proof-of-status upload for every member.
