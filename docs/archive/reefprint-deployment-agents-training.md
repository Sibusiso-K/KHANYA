> **PARTIALLY SUPERSEDED — pipeline sections obsolete; deployment and compute sections current.**
>
> **LIVE:** §1 five tiers · §2 degradation ladder, load-shedding, calibration drift · §4 training and compute plan · §6 formats and standards.
>
> **OBSOLETE:** §3 agent roster beyond Curator · §5 hyperspectral data stack · §7 capture modes · §8 capability stack. See docs/01-design-v3.md and docs/02-gauntlet-findings.md.

# REEFPRINT — Deployment, Resilience, Agents, Training

**Team Sonar · Wits · Working document, rev A**

Everything from the brainstorm, written down. Assumes **zero data from Mintek** — public sources plus Wits-generated paired samples only.

---

## 1. How it sits and connects — five tiers

The governing rule: **every tier must survive the loss of every tier above it.** Mining sites lose power, lose connectivity, and go underground. A design that assumes the network is a design that has never been to a plant.

```
TIER 5  CLOUD (optional, corporate)     federated aggregation · cross-site registry
          ▲ model weights only, never raw ore data
TIER 4  SITE SERVER (plant room)        historian · OPC UA gateway · block model · UI host
          ▲ local network only, air-gapped from internet
TIER 3  EDGE DEVICE (plant floor)       Pi 5 + Hailo · capture + inference · local buffer
          ▲ ethernet or wifi, store-and-forward
TIER 2  MOBILE (field/underground)      phone app · capture + geotag · on-device lite model
          ▲ syncs opportunistically when it surfaces
TIER 1  ORE                             the thing that does not care about any of this
```

### What runs where

| Component | Edge (Pi) | Phone | Site server | Laptop | Cloud |
|---|---|---|---|---|---|
| Capture + calibration | ● | ● | | | |
| Segmentation inference | ● ONNX/Hailo | ○ quantised lite | ● | ● | |
| Cross-scale bridge | ● | | ● | ● | |
| Conformal + OOD gate | ● | ● | ● | ● | |
| Processability regressors | ● | | ● | ● | |
| Transport / Look-Ahead model | | | ● | ● | |
| OPC UA advisory server | | | ● | | |
| Historian (TimescaleDB) | buffer only | buffer only | ● | | |
| OMF block model | | | ● | ● | |
| Agents (active learning, orchestrator) | | | ● | ● | ○ |
| Federated aggregation | | | | | ● |
| UI | | ● | ● host | ● | |

● primary · ○ optional/degraded

### The phone tier is not a gimmick

A field geologist or sampler underground has no network and no laptop. The mobile app captures a specimen with a calibration card in frame, geotags it to a stope or block ID, runs a quantised model on-device for an immediate estimate with an uncertainty band, queues the full-resolution capture, and syncs when they surface. That is a real workflow, and it is also the best possible live demo: hand a judge a phone.

### Federated tier — what actually crosses the boundary

Only model weight deltas. Never imagery, never assays, never grades. This is the entire reason the federated framing works: no mining house will share ore data, and this architecture means they never have to. Mintek, as a state-owned national research body already present in 400+ installations through its control platform, is the only credible coordinator in the country.

---

## 2. Resilience — the mining realities nobody designs for

### The degradation ladder

Six defined states. The system always knows which one it is in, and says so on screen.

| Level | Condition | Behaviour |
|---|---|---|
| **L0 Full** | all tiers up | full advisory, feedforward active, block model updating |
| **L1 No cloud** | internet down | everything local continues. Federated sync queues. **No user-visible change.** |
| **L2 No site server** | plant network down | edge continues capture + inference + local buffer. Advisory shown on device, not written to OPC UA. |
| **L3 Edge only** | isolated device | capture, infer, store. Operator reads results off the device screen. |
| **L4 Advisory suspended** | OOD gate tripped, or calibration drift beyond tolerance, or state estimate not converged | **abstain.** Hold last-known-good setpoint. State the reason on screen. Alarm. |
| **L5 Dark** | REEFPRINT down entirely | plant reverts to existing BPCS control. **No safety consequence.** This is the designed failure mode, not an accident. |

L5 is the one to say out loud in the pitch. A system whose total failure is a non-event is a system a plant will actually commission.

### Load shedding and power interruption

South African specific and non-negotiable:

- **Edge device runs off a USB-C power bank.** A Pi 5 draws ~5–10 W. A 20,000 mAh bank carries it for hours. During load shedding the sensing layer simply does not stop — and that is a genuinely differentiating claim in this country.
- **Last-known-good setpoint is persisted to disk, not held in memory.** Power returns, the value survives.
- **Cold-start discipline.** On restore, the system does **not** resume with a stale state estimate. It enters an explicit re-convergence window and abstains until the estimator has settled. Resuming confidently on stale state is how these systems hurt people.
- Site server on UPS with clean shutdown; TimescaleDB WAL means no corruption on hard power loss.

### Connectivity — store and forward, always

Every capture is written locally first with a monotonic sequence number and content hash, then transmitted. Never the reverse. Sync is idempotent and resumable. Loss of network delays data, it never loses it and it never blocks a capture.

### Calibration drift — the silent killer

The white reference tile gets dusty. LEDs age. Ambient light leaks in.

- White reference check on every startup and every N captures.
- Drift within tolerance → apply Direct Standardisation correction transparently.
- Drift beyond tolerance → **widen prediction intervals rather than fail**, flag for cleaning, and if it exceeds a second threshold, escalate to L4 abstention.

Degrading confidence rather than degrading silently is the whole philosophy in one mechanism.

### Physical environment

Dust, water film, vibration, variable ambient light, belt stoppages, shift changes. All of these are in the **domain-shift benchmark** — we simulate each one and report accuracy degradation as a table. That benchmark is a deliverable and we release it openly.

Belt stoppage detection matters specifically: a stopped belt means the same rock is imaged repeatedly, which will silently bias any running average. Detect it, exclude the frames, log it.

---

## 3. Agent design — authority, tools, guardrails

Design rule: **an agent earns its place only if it makes a consequential decision that would otherwise consume scarce human expertise.** Everything else is a script.

Second rule, stated in the pitch before anyone can ask: **no agent computes a mineralogical or control value. Ever.** They route, select, orchestrate and explain. The models compute.

| Agent | Decides | Tools | May not | Escalates when |
|---|---|---|---|---|
| **Curator** (active learning) | which samples get sent for thin-section / lab work | embedding store, drift detector, information-gain scorer | exceed the weekly lab budget | budget exhausted, or drift exceeds threshold |
| **Petrographer** (domain retrieval) | which literature grounds a given interpretation | RAG over SAIMM / geometallurgy corpus, spectral libraries | assert a phase call; output without citation | no supporting source found |
| **Orchestrator** (experiments) | which ablations run tonight, which models get promoted | compute scheduler, MLflow registry, test harness | promote a model that fails any gate | any gate fails |
| **Copilot** (operator) | how to explain a recommendation, in which language | read-only access to model outputs and historian | compute or alter a setpoint | operator asks something outside scope |
| **Scribe** (handover/reporting) | what goes in the shift report and model card | historian, registry | edit or delete an audit record | — |

**The Curator is the one that matters.** Thin-section capacity at Wits is your hard bottleneck. An agent allocating that scarce resource by expected information gain is doing real optimisation under constraint, and it is solving *your* actual problem rather than a hypothetical plant's.

### The VLM disagreement detector

Not an agent — an independent second opinion feeding the abstention logic.

A frontier vision-language model describes the specimen petrographically, knowing nothing of the pipeline. When its description contradicts the specialist model's output, that is an abstention signal, because a generalist VLM and a fine-tuned specialist fail in *orthogonal* ways. The Mahalanobis gate catches inputs far from the training distribution; it cannot catch inputs that sit comfortably in-distribution but are structurally wrong. This can.

The VLM does not need to be good at petrography. Its *disagreement* only needs to correlate with our model being wrong. That is a clean empirical question, testable in a week, and **either outcome is a result worth reporting.**

### Model routing

Frontier model via API during build; local model via Ollama for the offline demo; one abstraction layer so the swap is a config line. **No LLM anywhere near the real-time control path** — latency and cost make that unacceptable in a plant, and a Measurement & Control judge will know it.

---

## 4. Training and compute plan

Realistic against free tiers. The discipline that makes it fit: **freeze the backbone early and iterate on heads.** Repeated backbone retraining is what blows the budget.

| What | Where | Rough cost | Notes |
|---|---|---|---|
| DINOv3 continued SSL pretraining | **Lightning AI** (student credits) | 10–20 GPU-hrs | Use a distilled **ViT-S/14**, not the 7B. LoRA, mixed precision, gradient checkpointing. This is the single biggest job — do it once, well. |
| Segmentation decoder | **Kaggle** (30 hrs/wk, P100) | 2–4 hrs per run | Datasets attach natively on Kaggle. Iterate here. |
| Cross-scale bridge | Kaggle | 1–2 hrs per run | Small model, small paired dataset. |
| Processability regressors | laptop CPU | minutes | XGBoost. Say so — it's the right tool and admitting it is a credibility marker. |
| Transport / Look-Ahead model | laptop / Kaggle | ~1 hr | Trained on the Kaggle flotation plant dataset. |
| Conformal calibration | laptop | minutes | Calibrated, not trained. |
| Plant simulator sweeps | **Modal** (serverless CPU burst) | pennies | Embarrassingly parallel; correct tool for the job. |
| Band selection | laptop | minutes | Mutual-information optimisation, not a model. |
| VLM disagreement experiment | API | ~$20 | One week, one clean result either way. |
| Edge compilation | laptop → Pi | — | ONNX → Hailo compiler. |

**Colab** (15–30 hrs/wk T4) as overflow. **CHPC** (Centre for High Performance Computing) is worth an application through Wits if anyone has a supervisor who can sponsor it — free to South African academics and it would remove every compute constraint at once.

---

## 5. Data sources — the confirmed public stack

| Source | What it gives | Role |
|---|---|---|
| **HZDR Elvira** (RODARE) | 7 km hyperspectral drill core + **24 SEM-MLA mineral maps** | **The cross-scale bridge.** Paired macro↔micro. Method also published by HZDR. |
| **Kaggle "Quality Prediction in a Mining Process"** | real flotation plant time series: hourly lab silica, reagent dose, pH, air flow, froth levels | Look-Ahead / transport lag / lagged-label learning |
| **MUMDMC2025** (FigShare) | 14,400 photomicrographs, PPL+XPL, 72 rotations | SSL pretraining and rotation/polarisation physics. **Caveat: Egyptian granite minerals, only plagioclase overlaps UG2.** |
| **Tinto** (HZDR) | 3D hyperspectral point clouds, VNIR/SWIR/LWIR | spectral pretraining |
| **Hyperspectral geometallurgy benchmark** (Minerals 2026) | purpose-built benchmark | evaluation |
| **USGS splib07 · ECOSTRESS · RockSL** | reference spectra | Hapke synthetic mixing |
| Kaggle rock/mineral hand-specimen sets | macro imagery | macro-scale pretraining |
| **Wits School of Geosciences** | **paired macro + thin section, Bushveld ore, generated by us** | the differentiator, and it settles IP completely |

Target: **30–100 paired specimens** from Wits. That number is the negotiation.

---

## 6. Formats and standards — the output contract

| Output | Format | Why |
|---|---|---|
| Imagery + provenance | **OME-TIFF** (OME-XML in header) | embeds instrument, channels, exposure, LED sequence, calibration state, operator, model version |
| Spectral cubes | ENVI `.hdr` / `.dat` | de facto standard; `hylite` reads it natively |
| Orebody heatmap | **OMF** block model | opens directly in Leapfrog, Vulcan, Micromine, Deswik. GMG-governed, v2.0 adds block models |
| Live advisory | **OPC UA**, address space per **OPC 40560** | the industry's own companion spec for mining |
| Digital twin | **AASX** (IEC 63278) | opens in any standard AAS viewer |
| Results tables | Parquet | analytics |
| Governance | PDF model cards, ISO/IEC 42001-mapped registry | commercialisation readiness |

### Two "what we are not" statements

Both are credibility moves, and both are free.

1. **IEC 61511:** advisory layer strictly outside the SIS boundary. No write path to any safety function exists.
2. **SAMREC:** operational geometallurgical estimates only. **Not** a SAMREC-compliant Mineral Resource statement. Informs the Competent Person; does not replace them.

---

## 7. Capture modes — the physics, correctly

**Macro / conveyor: line scan (pushbroom).** Not video. A single pixel row; the second spatial dimension comes from belt motion. Hyperspectral is inherently pushbroom — slit and grating mean the sensor's Y axis is *wavelength*, not space. Requires known belt velocity. Belt-stoppage detection is mandatory, or repeated frames silently bias every running average.

**Micro / specimen: structured angular sweep.** Rotation under crossed polars, because extinction angle, birefringence and pleochroism are all angle-dependent. This is why MUMDMC2025 captures 72 positions. It looks like video; it is physics.

**Adaptive illumination (the swing):** the dome fires one band, updates its posterior, and selects the next wavelength by expected information gain over the phases it is currently uncertain about. Bayesian experimental design inside the illumination loop. **Must have a fixed-sequence fallback that produces identical outputs** — hardware never sits on the critical path.

---

## 8. The full capability stack

Ranked by how few competing teams will have them.

1. Cross-scale inference — infer the invisible (sub-10 µm PGM in BMS) from visible macro texture
2. Calibrated refusal — conformal + OOD + VLM disagreement, demonstrated live
3. The Look-Ahead — forecast what the plant experiences at T+45, not what the rock is now
4. Adaptive illumination — the sensor chooses its own next measurement
5. Curator agent — allocating scarce lab capacity by information gain
6. Federated national layer — Mintek as coordinator; weights cross the boundary, ore data never does
7. OMF block model export — a file a mine geologist can just open
8. OPC 40560 + IEC 63278 conformance
9. IEC 61511 and SAMREC boundary statements
10. Gazetted economics — every coefficient from SA statute
11. R6,000 sensor BOM replacing six-figure hyperspectral capex
12. Open domain-shift benchmark
13. Trilingual operator interface
14. Degradation ladder with L5 as a designed non-event
15. Power-bank operation through load shedding

---

## 9. Open questions to close

- Wits Geosciences: how many paired specimens, and by when?
- Real conveyor-to-flotation transport lag for a UG2 concentrator (mentor question)
- Comminution specific energy kWh/t for UG2 (still an unsourced assumption)
- Blended Megaflex tariff for a continuous concentrator (still an unsourced assumption)
- Does the VLM disagreement signal actually correlate with error? One week to find out.
- Who is the single technical decision-maker on this team?
