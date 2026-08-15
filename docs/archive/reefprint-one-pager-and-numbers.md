> **SUPERSEDED — historical record only, see docs/01-design-v3.md**

# REEFPRINT — one-page abstract + the numbers behind it

**Team Sonar · University of the Witwatersrand · Due 30 August 2026**

Part 1 is the abstract to submit. Part 2 is your Q&A armour — the workings behind every number in it. Do not submit Part 2; know it cold.

---

# PART 1 — THE ONE-PAGER (paste this)

REEFPRINT: SEEING ORE PROCESSABILITY IN SECONDS, AND KNOWING WHEN NOT TO TRUST IT

Team Sonar | University of the Witwatersrand
Challenge: Computer Vision for Real-Time Mineralogical Characterisation


APPROACH

We do not attempt to replace Mintek's automated mineralogy laboratory. We distil it.

Every QEMSCAN and SEM-EDS map Mintek has produced is ground truth that already exists and is already paid for. REEFPRINT trains a low-cost optical "student" model to reproduce those maps from imagery captured in seconds rather than days, converting an existing instrument archive into a scalable data asset.

Two design commitments distinguish it. First, we predict processability, not just phases: a plant does not act on a mineral list, it acts on reagent dose, mill setpoint and blend ratio, and those are governed by texture - grain size, locking and association - not composition alone. Second, the system quantifies its own uncertainty and refuses to act when confidence is insufficient, holding the last-known-good setpoint. A model that is accurate but unaccountable will never be commissioned on a live plant.

Output is published as a feedforward channel into flotation and milling control. Feedforward from feed composition is a documented gap in flotation control, which remains predominantly feedback-driven.


METHODS AND TECHNOLOGIES

Teacher-student distillation: high-fidelity mineralogical maps registered to cheap-optics imagery (mutual-information registration, itk-elastix), used to supervise a self-supervised DINOv3 backbone with a segmentation decoder. Where only bulk assay exists, a learning-from-label-proportions objective trains a differentiable abundance head, removing the pixel-mask prerequisite. Augmentation is physically grounded via Hapke spectral mixing against USGS splib07 and ECOSTRESS libraries.

Five phases: chromite, orthopyroxene, plagioclase, base-metal sulphide, and alteration (talc/serpentine). Talc is deliberate - it is naturally floatable and drives depressant demand.

Texture converts to three committed response variables: liberation at target grind, floatable sulphide surface area as a reagent proxy, and a grindability proxy mapped to kWh/t.

Trust layer: deep ensemble plus split conformal prediction for distribution-free coverage, with a Mahalanobis out-of-distribution gate and Direct Standardisation calibration transfer for illumination drift.

Deployment target: Raspberry Pi 5 with a Hailo-8L AI HAT+ (13 TOPS), an eight-band LED dome at wavelengths selected by our own information-gain analysis, crossed polarisers and an AS7341 verification sensor - approximately R6,000 in total, versus six figures for a hyperspectral installation. Integration via OPC UA modelled on OPC 40560 (Companion Specification for Mining), delivered as an IEC 63278 Asset Administration Shell. Consistent with IEC 61511, REEFPRINT is an advisory layer strictly outside the safety instrumented system boundary, with no write path to any safety function.


EXPECTED OUTCOMES

Committed performance targets: abundance R-squared against the teacher instrument of 0.90 on seen lithologies and 0.75 on unseen; per-phase F1 of 0.85 on the four major phases; and - stated deliberately - base-metal sulphide recall of 0.70 or better on a class present at under 1 vol%. On UG2, aggregate accuracy is misleading: the ore is 50-75% chromite while the PGMs sit in sub-1% sulphides, so a 97%-accurate model can miss the entire economic payload. We report the minority class first, alongside the trivial majority-class baseline. Conformal coverage within 3 points of nominal; OOD detection at 0.95 true-positive rate; inference above 10 frames per second on device.

Modelled benefit for a 1.2 Mt/year UG2 concentrator, using published South African coefficients only: a 0.5-point recovery improvement is worth approximately R39 million per year at the H1 2026 realised basket price of USD 2,801/oz; a 3% comminution energy reduction saves roughly R1.1 million and 677 tCO2e, worth a further R208,000 at the Carbon Tax Act Phase 2 rate of R308/tCO2e. Mintek's own FloatStar case study reports a 1.5-point recovery gain against plant control, so 0.5 points from feedforward on an already-controlled circuit is a conservative target. Conservative case, at 0.25 points: R20 million per year, per concentrator.

Deliverables: the trained model and edge device; a full accuracy report including a purpose-built domain-shift benchmark (dust, water film, blur, lamp drift) which we intend to release openly; closed-loop replay against a feedback-only baseline; and a minimum-viable-sensor bill of materials for operations that cannot justify hyperspectral capital expenditure.

---

# PART 2 — Q&A ARMOUR: EVERY NUMBER, DERIVED

Assume a judge asks "where does R39 million come from?" This is the answer, in order.

## Reference plant assumptions

| Parameter | Value | Basis |
|---|---|---|
| Throughput | 1.2 Mt/yr (100,000 tpm) | Mid-range for SA UG2 concentrators. Eastplats Zandfontein 40,000→70,000 tpm; ARM Bokoni planned 120,000 tpm new plant. |
| 4E head grade | 4.5 g/t | Conservative. Published UG2 range 4.4–10.6 g/t. |
| Baseline 4E recovery | 85% | Published UG2 recoveries 80–88%; Eastern Limb 81–88%. |
| Comminution energy | 20 kWh/t | **Assumption, flagged.** UG2 milled to 80% passing 75 µm. To be calibrated against Mintek or plant data — say so if asked. |
| Blended electricity price | R1.50/kWh | **Assumption, flagged.** Megaflex 2026/27 ranges 120.03 c/kWh off-peak to 720.19 c/kWh high-demand peak, ex-VAT. A 24/7 plant sees all bands. |
| Grid emission factor | 0.94 tCO₂e/MWh | DFFE gazetted (2023 DGGEF). |
| Carbon tax | R308/tCO₂e | Carbon Tax Act Phase 2, from 1 Jan 2026. R462/t by 2030. |
| PGM basket | USD 2,801/oz | H1 2026 realised, up 85% YoY. |
| ZAR/USD | 16.21 | 14 August 2026. |

## The recovery lever — where the money actually is

```
1,200,000 t/yr × 4.5 g/t          = 5,400,000 g 4E contained
5,400,000 g ÷ 31.1035 g/oz        = 173,613 oz contained
+0.5 recovery points              = 868 oz/yr additional
868 oz × USD 2,801                = USD 2,431,268
× 16.21                           = R39.4 million per year
```

**Conservative case at +0.25 points: R19.7 million per year.**

Anchor for defensibility: Mintek's own published FloatStar case study reports a **1.5 percentage point** nickel rougher recovery improvement against plant control, and 85% specification compliance versus 48%. We claim one third of that, because we are adding feedforward to a circuit that may already have APC, not replacing manual control.

**Caveat to state before they raise it:** this is gross contained value in concentrate. Net of smelter payability and downstream recovery the realised figure is lower. Say this yourself — volunteering the caveat is worth more than the number.

## The energy lever

```
1,200,000 t × 20 kWh/t            = 24 GWh/yr comminution
3% reduction                      = 720 MWh/yr
720,000 kWh × R1.50               = R1.08 million/yr
720 MWh × 0.94 tCO₂e/MWh          = 677 tCO₂e
677 × R308                        = R208,400/yr  (R312,700 at the 2030 rate)
```

**Total, target case: approximately R40.7 million per concentrator per year.**

## The finding you should say out loud

**Recovery dominates energy by roughly 35 to 1.** The energy and carbon story is real, nationally urgent, and rhetorically powerful — but the money is in recovery. Lead the pitch with the energy crisis, land the pitch on the recovery number. A team that knows which of its own levers is bigger reads as one that has actually done the analysis.

## Committed accuracy targets, and why each is set there

| Metric | Target | Rationale |
|---|---|---|
| Abundance R² vs teacher, seen lithologies | ≥ 0.90 | Published QEMSCAN-distillation precedent achieved 0.97 on carbonates. Bushveld is harder and finer-grained; we discount deliberately. |
| Abundance R² vs teacher, unseen | ≥ 0.75 | Precedent achieved 0.88 on unseen facies. Same discount. |
| Per-phase F1, four major phases | ≥ 0.85 | Standard for well-posed segmentation with adequate labels. |
| **BMS recall (<1 vol% class)** | **≥ 0.70 @ FPR ≤ 0.30** | The honest hard one. Setting this low and hitting it beats setting it high and missing. This is the number that proves you understand the ore. |
| Conformal coverage | within ±3 pp of nominal 90% | Distribution-free guarantee; verifiable, not aspirational. |
| OOD detection | TPR ≥ 0.95 @ FPR ≤ 0.05 | Governs the refusal behaviour. |
| kWh/t prediction | MAPE ≤ 10% | Feeds the economic claim directly. |
| On-device inference | ≥ 10 FPS | Conveyor-rate, on the R6,000 rig. |

Setting the sulphide recall target *low and explicitly* is a strategic choice. Every competing team will quote a high aggregate number. You will be the only team whose headline metric is the one that is actually hard — and you will hit it.

## The device, precisely

Raspberry Pi 5 (8 GB) · Raspberry Pi AI HAT+ 13 TOPS (Hailo-8L) · Pi HQ Camera · 8 narrowband LEDs on a PCA9685 driver, wavelengths chosen by information-gain band selection · crossed polarising film for petrographic imaging · stepper-driven rotating stage · AS7341 11-channel spectral sensor for verification · 3D-printed light dome. **≈ R6,000.** Sourceable from Micro Robotics, Communica, DIY Electronics or PiShop.

The band-selection result is itself a deliverable: a bill of materials for the minimum viable sensor that retains most of the discriminative power of a full hyperspectral instrument at roughly 1% of the cost.

## The ten capabilities, ranked by how few other teams will have them

1. Teacher distillation from QEMSCAN — precedent exists, never applied to Bushveld ore
2. Calibrated refusal — conformal intervals plus OOD gate, demonstrated live
3. Texture-to-processability rather than phase identification
4. Feedforward into Mintek's own control platform over OPC 40560
5. IEC 61511 advisory boundary stated explicitly
6. IEC 63278 Asset Administration Shell, exportable as AASX
7. Every economic coefficient drawn from South African statute and gazette
8. R6,000 sensor BOM replacing six-figure hyperspectral capex
9. Open domain-shift benchmark released publicly
10. Trilingual operator interface — English, isiZulu, Sesotho

Items 2, 5 and 7 are nearly free and are the ones a plant engineer will remember.

---

## Before 30 August

- **Request a Mintek mentor.** Ask specifically for the Mineralogy division, automated mineralogy or mineral processing. This is your route to teacher data and to an advocate in the finalist selection.
- **Start the public git repo today.** Finalists face originality authentication after the conference; verifiable commit history from before any Mintek data arrives is the defence.
- Submit per member: ID number, T-shirt size, contact details.
- The one-pager above runs ~640 words. If it overflows a page in your chosen format, cut the second paragraph of APPROACH first, then the Hapke sentence.
