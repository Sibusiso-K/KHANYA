# Gauntlet findings and dispositions

Four independent adversarial reviews of REEFPRINT v1, August 2026. This is the institutional memory of *why the design is what it is*. Read it before proposing anything that was already killed.

Disposition key: **RESOLVED** — v3 fixes it · **OPEN** — still live, needs work · **ACCEPTED** — known risk, taken deliberately · **MINE** — my error, corrected.

---

## FATAL findings

### F1 · The chromite-proxy collapse — OPEN, and it is the week-2 test
In UG2, base-metal sulphides sit dominantly in interstitial silicate and at chromite–silicate boundaries. So the only macro variable plausibly co-varying with BMS content is the chromite:silicate ratio — and plants already measure Cr₂O₃ by on-stream XRF to ±0.5% in minutes. If the residual after controlling for Cr₂O₃ is zero, REEFPRINT v1 was a slow, expensive chrome meter.

**Disposition:** partly resolved — v3 measures at 0.2–1.6 µm/px rather than inferring from macro texture, so the mechanism is direct. But the falsification test still runs in week 2 and the result is reported either way.

### F2 · The optics cannot see two of five phases — RESOLVED
Chromite is opaque, R ≈ 13%, no diagnostic VNIR-SWIR features, and 50–75 vol% of the ore. Talc and serpentine need Mg-OH absorption at 2200–2350 nm (SWIR); an 8-band visible dome cannot reach it. Elvira transfers badly because its hyperspectral↔MLA relationship runs through phyllosilicate alteration halos that chromitite does not have.

**Disposition:** resolved by abandoning spectroscopy for quantitative reflectance + polarimetry — the correct physics for opaque minerals. Talc detection without SWIR remains OPEN (week-2 empirical question; if it fails, drop to two properties).

### F3 · Nothing was measurable at n = 30–100 — RESOLVED structurally, still bounded
Conformal coverage SD ≈ √(0.9×0.1/n). At n_cal = 100 that is 3.0 pp — you miss a ±3 pp band a third of the time with a perfect model. At realistic n_cal = 20, SD = 6.7 pp. R² = 0.90 on 15 test specimens carries CI ≈ [0.72, 0.97]; an unseen-R² target of 0.75 has CI ≈ [0.40, 0.91], indistinguishable from r = 0.63.

**Disposition:** v3's unit of analysis is the *grain*, not the specimen — thousands per section — which raises effective n by orders of magnitude. **But locality-level splits are still mandatory** and every CI must be sized honestly. Rule 4 in CLAUDE.md exists because of this finding.

### F4 · Chrome-constrained recovery inverts the economics — RESOLVED by repositioning
Chrome solubility in smelter slag is ~1.8%; UG2 concentrates already exceed 3%. Plants grind coarse and accept lower PGM recovery to stay under the cap. So the marginal ounce is the dirtiest ounce, priced at the average — and "liberation at target grind P80" fights the binding constraint.

**Disposition:** liberation-at-P80 killed. Cr₂O₃ entrainment risk became a primary output. Economics rebuilt around unlocking mass pull against the chrome ceiling — mechanism stated, number *not* invented pending plant data.

---

## My errors — MINE, corrected

- **Carbon double-count.** SA carbon tax is Scope 1 only. Purchased electricity is Scope 2, not taxable at the plant gate; Eskom pays its own Scope 1 and passes ~11 c/kWh through the tariff. The R208k line does not exist.
- **Energy saving wrong in kind.** Mills run at near-constant power — same tonnes, same power, no kWh saved. A comminution improvement monetises as *extra throughput at constant power*, a larger and different story.
- **20 kWh/t understated.** Silicate operating work index alone is ~32 kWh/t to 75 µm on an MF2 circuit.
- **Positioned against an abstract BPCS.** Mintek *owns* MillStar and FloatStar. "Reverts to BPCS control" told the authors of the flotation controller we didn't know their product existed.

---

## STRUCTURAL findings

| # | Finding | Disposition |
|---|---|---|
| S1 | **Transport lag is a distribution, not a delay.** Coarse ore stockpiles hold days of live capacity with severe size segregation; variance ≈ mean. Feedforward with mismatched dead time is *worse than none*. | T+45 demoted. May return as *lab-turnaround* look-ahead: minutes instead of days means the plant acts hours earlier. **ACCEPTED** as reframed. |
| S2 | **Closed-loop confounding.** Plant history was generated under FloatStar control, so any model learned from it identifies the inverse of the controller. Simulated A/B against a "feedback-only baseline" is self-referential. | **OPEN.** Any use of the Kaggle plant dataset must state this. Do not claim causal effect from observational plant data. |
| S3 | **Licence stack unassignable.** DINOv3 non-transferable, no patent grant, unilaterally amendable, Californian jurisdiction. `asyncua` LGPL triggers anti-tivoisation on a sealed Pi appliance. Hailo compiler EULA is non-assignable. | **RESOLVED.** `timm` Apache-2.0 backbone; `asyncua` on general-purpose hardware; Hailo optional. SBOM mandatory. |
| S4 | **Instrument access was a single unhedged dependency** gating 100% of the graded deliverable. | **RESOLVED.** Wits dropped; CGS National Core Library primary, commercial specimens backup, and oxidation physics demonstrable on any sulphide-bearing rock. |
| S5 | **IP vesting under IPR-PFRD Act 51 of 2008** — IP from publicly financed R&D vests in the institution. | **RESOLVED** by using no university facilities. Own laptops, own money, own specimens, public data. |
| S6 | **Blue Cube MQi already exists** — Stellenbosch-founded, measures PGM g/t *and* Cr₂O₃ in platinum flotation streams at 15-second intervals, installed at Northam. | **RESOLVED by repositioning.** Blue Cube measures slurry after the mill. We replace the *lab*: days → minutes at 1/1000th capex. Rehearse this answer. |

---

## BLIND SPOTS worth keeping visible

1. **Abstention fires exactly when it is least safe.** Novel texture triggers OOD; novel texture *is* an ore transition. Refusals correlate positively with the moments that matter. → Rule 5: conservative default with a reason, never "unknown." Report abstention rate *conditioned on ore-change events*.
2. **Precious Metals Act 37 of 2005** — possession of unwrought PGM-bearing material without a permit is an offence. Scientific permits exist. Check cover before holding samples.
3. **Material transfer agreements** on mine-sourced specimens may make the open benchmark unreleasable.
4. **Originality authentication happens *after* finalist selection.** You could be told you placed, then disqualified. Commit history and a dated per-person decision log are the defence. Be able to whiteboard the conformal derivation cold.
5. **"Liberation at P80" is not a property of ore** — it is ore × comminution device. Any liberation claim must state its reference protocol.
6. **Adaptive illumination is a leakage channel.** Acquisition state correlates with collection time, which correlates with labels. → Freeze the schedule for all training data; adaptivity is inference-only. Add a **metadata-only baseline** as a leakage detector.
7. **Correlated crunch weeks.** Three CS students in the same year share modules, so capacity goes to near zero in one specific week rather than averaging. Overlay all five calendars in week 1 and schedule integration *before* it.
8. **The rusty met-eng will be treated as the oracle and will under-push** against three CS majors. Forbid them being the sole source of any load-bearing claim; book two external calls instead.
9. **Framing risks.** Never say "reduces manual sampling burden" to a Randburg audience — say sampler-augmenting. And Bushveld operations are Setswana/Sepedi country, not isiZulu/Sesotho; one language with a credited native-speaker reviewer, or say "localisation-ready" and explain why.
10. **Endogeneity.** A feedforward advisory changes the blending decisions that generate the ore it predicts. Log an "advisory-influenced" flag on every record now, or month-three drift will be uninterpretable.
11. **Ten minutes is a filter, not a reward.** Finalists are announced the next day. What decides it is the one sentence a judge repeats to another judge. Currently: *"they ran an experiment designed to kill their own idea, and told us the answer."*
12. **Nouns are an attack surface.** A rival can defeat a 25-component architecture by counting the components out loud in Q&A. Depth goes in the written submission; one idea goes in the talk.

---

## Adjacent capabilities identified as nearly free

- **Fine-chromite entrainment risk index** — Cr₂O₃ is the binding constraint on UG2 flotation. *Adopted as a primary output.*
- **Talc / naturally-floating-gangue feedforward** for depressant dosing. *Adopted, pending the SWIR question.*
- **Stockpile oxidation index** — sulphide surfaces tarnish with residence time, destroying floatability; macro-visible; unmeasured anywhere. *Adopted, and it is the strongest single idea in the project.*
- **Sampling representativity flagging** using the same OOD machinery. *Available, unclaimed.*
