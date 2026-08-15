> **SUPERSEDED — historical record only, see docs/01-design-v3.md**

# REEFPRINT v2 — hardened after the gauntlet

**Team Sonar · Wits · 15 August 2026**

v1 claimed to infer sub-10 µm PGM deportment from macro texture. Four independent adversarial reviews found that claim is probably redundant (chromite ratio already measured by on-stream XRF), partly impossible with the chosen optics (talc needs SWIR), statistically unmeasurable at n=30–100, and economically inverted (UG2 recovery is chrome-constrained, so the marginal ounce may be worth less than zero).

v2 keeps the method and changes the target.

---

# ROUND 5 — THE HARDENED DESIGN

## The new central claim

> **Three macro-visible ore properties constrain PGM flotation. None are measured before the mill. All three are already visible. Each maps to one control action.**

| Property | Why it constrains | Control action | Visible? |
|---|---|---|---|
| **Fine-chromite entrainment risk** | Cr₂O₃ above ~3% penalises the smelter; chrome solubility in slag is ~1.8%. Plants hold mass pull back to stay under the cap. | mass pull / froth depth ceiling | Yes — chromite is 50–75 vol%, opaque, high contrast |
| **Naturally-floating gangue load** (talc / serpentine) | Floats without collector, dilutes concentrate, drives depressant demand | depressant dose | **To be tested** — see risk below |
| **Surface oxidation state** | Sulphide surfaces tarnish with stockpile residence; genuinely destroys floatability; nobody measures it | collector dose / blend priority | Yes — tarnish is macro-visible |

This is a smaller claim than v1. It is also measurable, mechanistically defensible, and it targets the constraint a UG2 metallurgist actually manages.

**The oxidation index is the sleeper.** It is real, it is visible, it is unmeasured anywhere, and it is the one no competing team will think of.

## What survives from v1

Teacher–student distillation (teacher is now XRD/assay for visible phases — far cheaper labels). Calibrated abstention. Feedforward integration. The R6,000 rig. Standards conformance. The domain-shift benchmark.

## What dies, and why

| Killed | Reason |
|---|---|
| Inference of invisible PGM deportment | Probably redundant with on-stream Cr₂O₃; unfalsifiable at our n |
| Liberation at P80 | Property of ore × mill, not ore. No labels without MLA on milled product. Fights the chrome constraint. |
| Grindability → kWh/t | Bond work index needs ~10 kg and days per specimen. Infeasible. |
| T+45 as a hard claim | Transport delay is a *distribution* with variance ~ its mean, set by stockpile draw. Feedforward with mismatched dead time is worse than none. Demoted to a measured, distribution-aware stretch goal. |
| Underground mobile app | Precious Metals Act 37 of 2005 possession offence; cameras often banned underground; POPIA exposure |
| Trilingual copilot as specced | Bushveld is Setswana/Sepedi country, not isiZulu/Sesotho. One language, one credited native-speaker reviewer, 40-term validated glossary — or say "localisation-ready" and explain why |
| Frontier VLM in the loop | Data residency, network dependency at Randburg, unownable safety property |

## Licence rebuild — the stack must be assignable to Mintek

| Was | Problem | Now |
|---|---|---|
| DINOv3 | Non-transferable, no patent grant, unilaterally amendable, Californian jurisdiction | **Permissive backbone from `timm` (Apache-2.0), DINO-style SSL run by us.** Also strengthens originality — we trained it. |
| `asyncua` (LGPL-3.0) | Anti-tivoisation bites on a Pi *appliance* | Runs on the **site server (general-purpose computer)**, not the sealed edge device. Obligation resolved. |
| Hailo Dataflow Compiler | Proprietary, non-assignable, and ViT attention is what edge compilers reject | **Optional accelerator only.** Core path is plain ONNX Runtime. Never load-bearing. |
| Eclipse BaSyx | MIT in repo vs EPL-2.0 on project page | Pin the artefact, record the licence, state it in the SBOM |

Produce an **SBOM** with the licence of every dependency. That single artefact answers the MOTT officer completely.

## Attacking the redesign

**Mineralogist:** *"Chromite entrainment is a function of fines generation in the mill, not of feed texture."* — Partly true. Our claim is narrower: feed chromite **grain size distribution and boundary character** set the fines potential entering the mill. That is testable and it is our week-2 gate.

**Rival team:** *"Oxidation is confounded with lithology and weathering, and you have no residence-time labels."* — Correct, and this is the redesign's weakest joint. Mitigation: controlled ageing experiment — image the same specimens at day 0, 7, 14, 21. Cheap, in our control, and it produces a clean label nobody else will have.

---

# ROUND 6 — OUTPUT

## (a) Hardened architecture

```
CAPTURE      RGB + 8-band LED dome + crossed polarisers, fixed illumination schedule
             white-reference tile every session; all metadata → OME-TIFF header
   ↓
FEATURES     permissive backbone (timm, Apache-2.0), DINO-style SSL on rock corpus
   ↓
SEGMENT      chromite · pyroxene · plagioclase · sulphide · alteration
   ↓
TEXTURE      grain size distribution · association matrix · boundary character · tarnish index
   ↓
CONTROL EXP  ── regress out Cr₂O₃ + pyroxene fraction ── report residual signal ──┐
   ↓                                                                              │
THREE HEADS  entrainment risk · NFG load · oxidation state    (gradient boosting)  │
   ↓                                                                              │
TRUST        ensemble + conformal (locality-split) + OOD gate                      │
   ↓         abstain → emit CONSERVATIVE DEFAULT, never "unknown"                  │
   ↓                                                                              │
ADVISORY     feedforward INPUT TO FloatStar / MillStar (not parallel to it)        │
             OPC UA on site server · OMF block model · AASX twin                   │
                                                                                  │
             the residual-signal result is a headline deliverable ────────────────┘
```

## (b) Tech stack, justified per layer

| Layer | Choice | Why this and not the obvious alternative |
|---|---|---|
| Backbone | `timm` ViT/ConvNeXt, Apache-2.0, self-supervised by us | DINOv3 is unassignable. Training our own SSL is also our strongest originality claim. |
| Segmentation | `segmentation_models_pytorch` | Small, fast to iterate, replaceable |
| Heads | **XGBoost** | Small n, engineered features. Deep learning here would be fashion, not fit. |
| Uncertainty | `crepes` / MAPIE, **split by locality** | Patch-level splits void exchangeability. This is the fix for the fatal statistical finding. |
| OOD | Mahalanobis + **metadata-only baseline** | The metadata baseline is the cheapest leakage detector available |
| Serving | **ONNX Runtime** | Hailo compiler is non-assignable and rejects ViT attention. Accelerator optional. |
| Integration | `asyncua` on site server | LGPL obligations resolved off the appliance |
| Twin / spatial | BaSyx AASX · OMF block model | Opens in Leapfrog/Vulcan. A file a mine geologist can use. |
| Provenance | OME-TIFF + OME-XML | Instrument, channels, LED schedule, calibration state, operator, model version |
| Agents | Curator only, at first | The one that allocates scarce lab capacity. The other four are week-6 stretch. |

## (c) Methodology, and what would falsify us

**The falsification test is the project's headline.** State it in the pitch.

> **H₀: after controlling for Cr₂O₃ and pyroxene fraction, macro texture carries no additional predictive signal for flotation-relevant ore properties.**

Design: partial correlation and nested model comparison (baseline = Cr₂O₃ + pyroxene only; full = baseline + texture features), grouped by locality, with confidence intervals reported at our actual n. If we cannot reject H₀, we say so publicly and report the negative result. **A team that runs an experiment designed to kill its own idea, and reports the answer either way, is doing science.** Nobody else in that room will do this.

Evaluation protocol: locality-level group splits, never patch-level. Metadata-only baseline reported alongside every metric. Majority-class baseline reported alongside every classification metric. Macro-averaged, per-grain metrics. Every number with a confidence interval sized at honest n. Coverage reported per held-out locality, not marginally.

Controlled ageing experiment for oxidation labels: same specimens imaged day 0/7/14/21.

## (d) Six and a half weeks, gated

| Week | Work | **Gate (binary, on evidence)** |
|---|---|---|
| **1** (18–24 Aug) | Specimen access secured. Rig v1. Frozen eval harness on public data. Locality-split protocol written. | **Rocks in hand + harness reproduces a published baseline.** No rocks → pivot to public-data-only scope immediately. |
| **2** (25–31 Aug) | Segmentation on 5 phases. Texture extractor. **THE CONTROL EXPERIMENT.** One-page abstract submitted 30 Aug. | **Residual-signal result computed, with CI.** Positive → proceed. Null → pivot to oxidation-only, which needs no chromite residual. |
| **3** (1–7 Sep) | Three heads trained. Controlled ageing experiment started. Conformal calibration, locality-split. | **Coverage within band per locality, with honest CI.** |
| **4** (8–14 Sep) | Domain-shift benchmark. OOD gate. Conservative-default logic. FloatStar-shaped advisory output. | **Zero silent failures under degraded input.** |
| **5** (15–21 Sep) | OPC UA + OMF + AASX. Integration. UI. **Integration happens here, before crunch.** | **End-to-end runs offline on one laptop.** |
| **6** (22–28 Sep) | Ablations. Accuracy report. Backup video. Hostile Q&A drills. | **Backup video exists.** Non-negotiable. |
| **6.5** (29–30 Sep) | Freeze. Rehearse. Travel. | Nothing new is built. |

Overlay all five academic calendars in week 1. Three CS students in the same year share modules, so their crunch weeks are perfectly correlated — capacity goes to near zero in one specific week, not to an average. Schedule integration before it. Keep the rig off campus.

## (e) Kill list, in order

1. Federated layer → one slide
2. Four of five agents (keep Curator)
3. Adaptive illumination → fixed schedule (it is also a leakage channel: freeze it for all training data regardless)
4. AASX export
5. OMF export
6. Multilingual UI → "localisation-ready", explained
7. Hailo acceleration → CPU ONNX
8. T+45 → drop to a measured RTD distribution, stated as future work

**Never cut:** the control experiment, locality splits, conservative-default abstention, the SBOM, the backup video.

## (f) Ten minutes

| Min | Beat |
|---|---|
| 0:00 | Cr₂O₃ is the binding constraint on every UG2 circuit in the country, and nobody measures what drives it before the mill. |
| 1:00 | Three visible properties, three control actions. One slide. |
| 2:00 | **"We designed an experiment to prove our own idea was redundant."** The control experiment, and the result. |
| 4:00 | Live: rock in the rig → segmentation → three numbers → advisory delta. |
| 6:00 | **Live refusal.** Feed it Egyptian granite. Watch it decline and hold a conservative default. |
| 7:00 | Where it fits: a feedforward input to FloatStar, not a competitor to it. Outside the SIS boundary. Not a SAMREC statement. |
| 8:00 | What we did not claim, and why. Honest limits. |
| 9:00 | Ask. Stop. |

**The sentence a judge repeats on 2 October:** *"They ran an experiment designed to kill their own idea, and told us the answer."*

**Three questions, rehearsed:**
- *"How is this different from Blue Cube?"* — Blue Cube measures slurry after the mill. We measure rock before it. Our claim is lead time, and here is the RTD distribution that bounds it.
- *"Isn't this just a chrome meter?"* — That is exactly what we tested. Here is the residual after controlling for Cr₂O₃.
- *"What is your abstention rate?"* — [number]. Conditioned on ore-change events it is [number], because refusing at a transition is the failure mode that matters.

## (g) Open questions, ranked by how much they block

1. **Specimen access at Wits Geosciences** — gates everything. Resolve this week. Fallback: Council for Geoscience National Core Library (public Bushveld core).
2. **Can talc/serpentine be detected without SWIR?** Empirical, week 2. If not, drop to two properties.
3. Wits IP position under the IPR-PFRD Act 51 of 2008 — one email to Wits Enterprise.
4. Precious Metals Act permit cover for holding PGM-bearing material.
5. Real UG2 stockpile residence-time distribution — mentor question.
6. Who is the single technical decision-maker. Decide today.
