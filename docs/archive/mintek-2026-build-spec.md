> **SUPERSEDED — historical record only, see docs/01-design-v3.md**

# Mintek-SCI Grad Hackathon 2026 — Technical Build Spec

**Two candidate builds, fully specified.** Every library, price and free tier below was verified against a live source in July 2026. Where the honest answer is "this open-source path is weak," it says so.

- **UMLILO** — Problem 5, AI-driven optimisation of pyrometallurgical processes
- **REEFPRINT** — Problem 3, computer vision for real-time mineralogical characterisation

---

## PART 0 — Demo doctrine (applies to both)

Five rules. Every one of these is a lesson from teams that lost with better technology.

1. **The demo runs fully offline on a laptop.** Mintek's guest WiFi is not your friend on 2 October. Cloud is a September build tool only. Say this out loud to the judges — it reads as engineering maturity, not timidity.
2. **A backup video of the complete working demo exists by 28 September.** Non-negotiable. If the rig dies you keep talking over footage and lose nothing.
3. **The system must visibly refuse.** Every team shows their model working. Almost none show it *knowing when it is wrong*. Calibrated abstention is the single cheapest differentiator available to you.
4. **Every result converts to rands.** kWh/t, recovery points and campaign days are inputs. Rands per annum is the output. Electricity is 35–40% of ferrochrome production cost — a rand figure lands where an F1 score does not.
5. **The LLM never computes anything load-bearing.** It routes, explains and documents. Tools do the maths. Say this explicitly in the abstract; it inoculates you against "you bolted a chatbot on," which is the most common way a strong hackathon project loses credibility in Q&A.

---

# PART 1 — UMLILO

*Problem 5. "The furnace that thinks in rands."*

## 1.1 The honest problem with the physics layer

Read this before you commit, because it is the single fact that decides whether UMLILO is viable.

Open-source computational thermodynamics has good **solvers** and bad **oxide databases**. pycalphad, OpenCalphad, Thermochimica and ORNL's Equilipy all implement Gibbs energy minimisation properly. What they lack is industrial-grade thermodynamic descriptions of *slags, mattes and molten metallic solutions* — exactly what pyrometallurgy is made of. Those live in FactSage (commercial), which is precisely what Mintek uses alongside their own Pyrosim.

This is not fatal. It defines your architecture as a three-tier climb:

**Tier A — build your own reduced-order thermochemical core.** This is the honest, defensible, fully-yours foundation and it is what you demo.
- Species Gibbs energies from open data: NIST-JANAF tables, the `thermo` and `chemicals` packages (Caleb Bell), `Cantera` for gas-phase and condensed species
- Mass balance + energy balance on the furnace as a control volume
- A fitted slag activity model over the CaO–MgO–Al₂O₃–SiO₂–Cr₂O₃–FeO system (regular-solution or a simplified quasi-chemical form) — you *regress this against published data*, which is the key move
- Solve constrained equilibrium with `Pyomo` + IPOPT, or `scipy.optimize` with mass-balance constraints

**Tier B — wrap it in IDAES.** IDAES is the US DOE / NETL open-source process systems engineering framework, built on Pyomo, equation-oriented, with native support for steady-state and dynamic optimisation, uncertainty quantification, and automated fitting of thermodynamic submodels from experimental data. It explicitly lists critical mineral processing as an application area. Wrapping your furnace as an IDAES unit model instantly reframes you from "students who did regression" to "a process systems engineering team." Cheap credibility, real capability.

**Tier C — request supervised FactSage access in September.** Mintek has licences and is assigning you mentors. Asking for supervised access to generate high-fidelity teacher data is legitimate, shows you know what the real tool is, and gives you a fidelity ceiling. **Put this in the abstract as a stated intent.** It signals that you understand the domain's actual toolchain rather than reinventing it in ignorance.

### The validation move that wins the argument

**Mintek's own published Pyrosim and FactSage results are your free ground truth.** Rodney Jones' work on DC arc furnace ferroalloy smelting, the Pyrosim/FactSage ferrochrome simulation papers, and the SAIMM/pyrometallurgy.co.za archive contain published mass and energy balances for chromite smelting. Reproduce them with your Tier A core and report the deviation.

That single table — *our open-source core vs. Mintek's published FactSage balance, within X%* — is worth more than any accuracy metric you can produce. It says: we validated against you, using your own literature, and we were honest about the gap.

## 1.2 Architecture

Seven layers. Each one is independently demoable, which is your insurance against schedule slip.

```
[L7] Operator interface — React + three.js furnace cross-section, trilingual
[L6] Agentic layer     — copilot / scribe / overnight recalibration (tool-calling only)
[L5] Integration       — asyncua OPC-UA server → simulated plant DCS on a Pi
[L4] Decision          — do-mpc nonlinear MPC over the surrogate + grid/tariff objective
[L3] Uncertainty       — deep ensemble + conformal intervals + OOD gate
[L2] Surrogate         — PyTorch differentiable emulator → ONNX, sub-millisecond
[L1] Physics core      — equilibrium + energy ODE + freeze-lining thermal model
```

### L1 — Physics core (`umlilo-core`)

Three coupled components. The third is the one nobody else will have.

**Equilibrium module.** Tier A above. Given feed composition, temperature and power, returns phase split, slag composition, alloy composition, metal recovery and enthalpy demand.

**Dynamic energy balance.** Equilibrium alone is a static snapshot. A furnace is a thing with thermal inertia. Model it as an ODE system: arc power in, reaction enthalpy, shell/roof/offgas losses, tapping mass flow out, bath thermal mass. Solve with `scipy.integrate.solve_ivp` (stiff, use BDF/Radau). Now temperature has *momentum*, which is why ramping down badly is dangerous.

**Freeze-lining and refractory model — the differentiator.** 1D transient heat conduction through slag freeze layer → refractory → shell → water cooling, with a moving solidification boundary. `scipy` finite differences or `FiPy` for a cleaner formulation. Freeze-lining thickness becomes a **state variable**, and refractory wear integrates as a function of hot-face temperature and thermal cycling.

This is the mechanism that turns "we saved energy" into "we extended campaign life," and a furnace rebuild is a nine-figure event. It is also what makes curtailment *dangerous* rather than merely expensive, which is the entire dramatic core of your demo.

**Grid layer.** This runs on **real published data, not invented numbers** — Eskom publishes the full *Schedule of Standard Prices* for the 2026/27 year (effective 1 April 2026) as a public PDF, including the Megaflex time-of-use structure: peak/standard/off-peak × high/low demand season, the R10.83/kVA maximum demand charge on peak and standard periods, the 4.26 c/kVARh reactive energy charge above 0.96 power factor, and the public-holiday-as-Sunday rule. Parse it and drive your cost function from it. When a judge asks where your tariff numbers came from, the answer is "Eskom's own gazetted schedule," which ends the question.

Curtailment events as a stochastic process — Poisson arrivals with stage-dependent depth and duration. Objective function:

```
minimise  R/tonne contained metal
        + refractory damage cost (integrated thermal stress)
        + emissions penalty
subject to  freeze-lining thickness ≥ minimum
            slag basicity within window
            transformer / electrode current limits
            curtailment compliance (contractual, hard)
```

**No other team will optimise this objective.** Everyone else maximises recovery. You minimise cost under a constrained grid — which is what is actually killing South African smelting in 2026.

### L2 — Surrogate

The equilibrium solver takes seconds. Control needs milliseconds.

- Sample the input space with Sobol sequences — `scipy.stats.qmc.Sobol`. Feed composition, power, feed rate, reductant ratio, flux addition, tapping schedule.
- Run 10⁵–10⁶ solves. Embarrassingly parallel: `joblib` locally, **Modal** for burst compute (serverless, container-native, genuinely the correct tool for this workload — you pay for seconds of parallel CPU, not an idle VM).
- Store as Parquet, query with **DuckDB**. No server, no ops, fast analytics on the corpus.
- Train an ensemble of PyTorch MLPs (or a Neural ODE for the dynamic part) to emulate the core. Export **ONNX**.

Because the surrogate is differentiable you get inversion for free: gradient-descend on setpoints to hit a target outcome. Pyrosim tells you what will happen. Yours tells you what to do.

**Optional escalation:** implement the dynamic surrogate as a physics-informed model in **NVIDIA PhysicsNeMo** (formerly Modulus, open-sourced in 2025). Enforce the energy balance as a soft constraint in the loss. Being able to say "our residual loss enforces the first law" is a genuinely strong Q&A moment. Treat as stretch — do not put it on the critical path.

### L3 — Uncertainty

- **Deep ensemble** (5 heads) for epistemic uncertainty. Cheap, robust, no tricks.
- **Conformal prediction** for distribution-free coverage: **MAPIE** (scikit-learn compatible, mature, largest community) or **crepes** (NumPy-based, roughly 10× faster for interval-on-limited-data). **TorchCP** if you want it native in PyTorch with GPU batching.
- **OOD gate**: Mahalanobis distance in surrogate latent space. Outside threshold → refuse, hold last-good setpoint, escalate to operator.

The gate is not a safety afterthought. It is a feature you demo deliberately.

### L4 — Decision

**Primary: nonlinear MPC via `do-mpc`.** Python, built on CasADi, handles nonlinear multi-stage MPC with hard constraints and moving-horizon estimation. Constraints are the point: you can *prove* the controller cannot drive freeze-lining below the safe minimum. A judge asking "what stops it wrecking the furnace?" gets a mathematical answer, not a reassurance.

**This is the load-bearing library choice, and it validates the whole architecture:** `do-mpc` ships native **ONNX interoperability** and native **OPC-UA interoperability**, plus a data sampling framework and sensitivity calculation. That means L2 → L4 → L5 — surrogate, controller, plant interface — is one coherent, documented, published toolchain rather than three things you duct-taped together. Say that in Q&A. It is the difference between an architecture and a pile.

**Secondary: RL agent** — wrap the surrogate in a `Gymnasium` environment, train SAC/PPO with `stable-baselines3`. Show the RL agent finding a *non-obvious* ramp-down profile that MPC's horizon misses. Use it as the "look what emerges" moment, with MPC as the shippable controller. This framing — RL for discovery, MPC for deployment — is exactly how serious process control teams talk, and it pre-empts the "you can't put RL in a plant" objection.

### L5 — Integration

**`asyncua`** (FreeOpcUa/opcua-asyncio) — LGPL, actively maintained, Python ≥3.10, `pip install asyncua`. This is how real plants talk. OPC-UA is not a hackathon flourish; it is the actual protocol.

Architecture: your controller is an OPC-UA **client**. A separate process on a Raspberry Pi is the OPC-UA **server**, playing the role of the plant DCS. Setpoint recommendations get written to server nodes; process values get read back. That is hardware-in-the-loop with zero fire risk, and it is *unmistakably real* to anyone who has worked in a plant.

### L6 — Agentic layer

Four agents. Each one earns its place; none of them do arithmetic.

**Operator Copilot.** Tool-calling agent with access to the surrogate, the MPC solver and the historian. Operator asks in natural language — *"Eskom just called stage 4, what do I do?"* — the agent runs counterfactuals through the actual solver and returns a ranked action list with rand figures and confidence intervals. The LLM chooses which tool to call and how to explain the result. It never computes the answer.

**Shift Handover Scribe.** Auto-drafts the shift report: what happened, what was changed and why, what the incoming shift must watch. A genuine, unglamorous industrial pain point, which is exactly why it reads as real rather than as demo-ware.

**Overnight Recalibration Agent.** Genuinely autonomous MLOps: ingests the day's plant data, re-fits the surrogate residual, runs the full validation suite, and **only promotes the model if it passes every gate** — otherwise it rolls back and files a report. Orchestrate with **MLflow** as the model registry. This is agentic in the way that matters: an agent with authority, bounded by tests.

**Trilingual interface — English / isiZulu / Sesotho.** Plant operators on the Bushveld are not uniformly first-language English speakers. This costs you a day of work, is impossible to argue with, and no other team will do it. It is the highest impact-per-hour item in this entire document.

**Model choice.** Build against an API for quality (tool-calling is the requirement, not raw scale), and ship an **Ollama** fallback with a small local model so the copilot still functions with no WiFi on stage. Route through a single abstraction layer so the swap is one config line.

### L7 — Interface

- **FastAPI** backend, **React** frontend, **three.js** furnace cross-section: freeze-lining thickness animating as a live geometry, arc glow modulated by power, tapping events as visible flow. You have three CS students; use them.
- **Grafana** panel alongside it reading from Timescale — because it makes the whole thing look like a plant rather than a science project. Two visual registers, one showing physics and one showing operations, is disproportionately convincing.
- Fallback if time collapses: **Streamlit** or **NiceGUI**. Functional, ugly, ships in an afternoon.

### Data layer

| Purpose | Choice | Why |
|---|---|---|
| Plant time-series | **TimescaleDB** (Postgres + hypertables) | It is Postgres. Boring, reliable, industry-standard. QuestDB if you want raw ingest speed. |
| Simulation corpus | **DuckDB + Parquet** | 10⁶ rows, zero ops, fast analytics |
| Experiments + registry | **MLflow** | Required for the autonomous promotion gate |
| Data/model versioning | **DVC** or Git-LFS | Provenance for the originality check |
| Packaging | **uv** + `ruff` + `pytest` | Fast, modern, signals competence in the repo |

### Cloud

Deliberately minimal, and say why.

- **Dev**: local, Docker Compose
- **Burst simulation**: Modal (correct tool for parallel CPU bursts)
- **Training**: Kaggle (30 h/week, often P100) or Colab (15–30 h/week T4). Lightning AI offers monthly credits with academic verification. GCP gives $300 in new-user credits, Azure $200 — worth having as backup, not as plan.
- **Demo**: **localhost**. Nothing that matters depends on a network.

## 1.3 Hardware

Not required. Build it anyway — it is R1,000 for the best fifteen seconds of your presentation.

**The Curtailment Box.** Raspberry Pi (any model with GPIO) running the OPC-UA plant server, in a small enclosure with:
- One **big red physical button** labelled `ESKOM STAGE 4`
- An amber/green status LED pair
- Optionally a servo-driven analogue needle for bath temperature

A judge presses the button. Eskom curtails. The twin reacts live on the screen. The needle moves. **A judge who has physically triggered your demo is a judge who is invested in it.** No fire, no permits, no risk.

*Optional:* MLX90640 thermal camera (~R700) pointed at a heated plate as a live "furnace shell" thermal feed. Nice, not necessary. Do not let hardware onto the critical path.

## 1.4 Tests and proof

This is where hackathon projects are actually won, and where almost nobody invests.

1. **Simulator validation against published Mintek balances.** Reproduce documented Pyrosim/FactSage ferrochrome mass-energy balances; report deviation with citations. **This is the headline credibility test.**
2. **Surrogate fidelity.** R²/MAPE vs. the full solver on held-out Sobol points — *and* a deliberate extrapolation test outside the training hull.
3. **Property-based physics tests.** Use `hypothesis` to generate random valid inputs and assert mass conservation, energy conservation and second-law compliance. **Unit tests that assert thermodynamics** is an unusual and beautiful thing to put on a slide.
4. **Conformal coverage.** Empirical vs. nominal coverage. It should sit on the diagonal. Show the plot.
5. **Closed-loop A/B — the money result.** MPC vs. a rule-based operator baseline across 1,000 simulated 30-day campaigns with stochastic curtailment. Report ΔkWh/t, Δrecovery, Δcampaign-life and ΔR/t **with confidence intervals**, because a single number is a claim and a distribution is evidence.
6. **The ablation that justifies the whole approach.** Physics-informed model vs. plain XGBoost, evaluated specifically on extrapolation. Show the naive model failing outside the training hull. That is the argument for everything you built.
7. **Adversarial/safety suite.** Stuck thermocouple, sensor dropout, feed assay error, instantaneous curtailment. Does it fail safe? Prove it.
8. **Latency budget.** Inference time vs. control loop period, with headroom.

## 1.5 Demo choreography — 8 minutes

| Time | Beat |
|---|---|
| 0:00 | One slide. One of five ferrochrome smelters running. 185,000 jobs. Exports down 63%. Silence after it. |
| 0:45 | The twin, live, 30 days compressed. Freeze lining breathing on screen. |
| 2:00 | **Judge presses the red button.** Eskom curtails 20%. |
| 2:15 | Baseline policy: bath chills, freeze lining thickens, recovery collapses, cost spikes. Let them watch it fail. |
| 3:00 | Enable UMLILO. Same event, replayed. Show the ramp profile it chose and the constraint it respected. |
| 4:30 | The numbers. ΔkWh/t, Δrecovery, campaign days, rands per annum. |
| 5:30 | Copilot, asked a question in isiZulu. Answers with figures and a confidence interval. |
| 6:30 | **Feed it garbage. Watch it refuse** and hold last-good setpoint. |
| 7:15 | Validation table: our core vs. Mintek's published balances. |
| 7:45 | Integration path. One slide. Stop talking. |

---

# PART 2 — REEFPRINT

*Problem 3. Distil Mintek's own instrument archive into cheap optics.*

## 2.1 Architecture

```
[L7] Interface        — live overlay + processability panel + setpoint delta, trilingual
[L6] Agentic layer    — autonomous geometallurgist: drift detection → active learning → retrain
[L5] Integration      — asyncua OPC-UA feedforward channel, StarCS-shaped
[L4] Processability   — 3 committed metallurgical response targets
[L3] Uncertainty      — conformal + OOD gate + abstention
[L2] Student model    — cheap-optics segmenter, self-supervised backbone
[L1] Teacher ingest   — QEMSCAN/SEM registration + distillation
```

### L1 — Teacher ingest and registration

The hard part, and the part to start on day one. Multimodal image registration between the teacher map and the cheap-optics image is where quality lives or dies.

- **`SimpleITK`** or **`itk-elastix`** for mutual-information-based multimodal registration
- **`scikit-image`** for preprocessing, `rasterio`/`spectral` (SPy) for cube handling
- **`hylite`** + **`hycore`** (`pip install hylite`) if hyperspectral or drill-core data arrives — purpose-built open-source toolboxes for spectral geology and hyperspectral drill core. Using the field's actual tooling rather than generic CV libraries is a small signal that reads loudly.

Budget a full week on registration. Every team that skips this produces a model trained on misaligned labels and does not know it.

### L2 — Student model

- **Backbone**: DINOv2/DINOv3 self-supervised features, frozen, plus a light decoder. Self-supervised pretraining on unlabelled imagery is the correct answer to label scarcity — and it lets you pretrain on public data *in Week 1, before Mintek's data arrives*.
- **Segmentation**: `segmentation_models_pytorch` (U-Net/SegFormer) for speed of iteration.
- **Grain boundaries**: SAM-family models for zero-shot boundary proposals as an auxiliary signal — there is recent published work on auto-prompted SAM for dual-modal grain segmentation in rock images.
- **Weak supervision**: when only bulk XRD/assay is available, train with a learning-from-label-proportions loss over a differentiable abundance head. This dissolves the pixel-mask bottleneck, which everyone else treats as a prerequisite.
- **Physics-grounded augmentation**: synthesise mixed spectra with Hapke mixing models against USGS splib07 / ECOSTRESS reference spectra. Physically valid synthetic data, not noise injection.

### L3 — Uncertainty

Same stack as UMLILO: deep ensemble + MAPIE/crepes conformal intervals + Mahalanobis OOD gate. Plus **calibration transfer** methods borrowed from chemometrics (Direct Standardisation) to handle lamp drift and sensor ageing — a real deployment concern that shows you have thought past the demo.

### L4 — Processability heads

**Commit to three named metallurgical response variables.** "Processability" without committed targets is a vibe, and a Mintek mineralogist will say so.

1. **Liberation at target grind (P80)** — from grain size distribution and mineral association matrix, pushed through a breakage/liberation model. Pre-empt the 2D stereological bias question; do not hide from it.
2. **Reagent demand proxy** — floatable sulphide surface area per tonne, from segmented BMS area and grain perimeter.
3. **Grindability → kWh/t** — hardness proxy from texture, mapped through a Bond/Morrell work index relation. Converts directly to rands.

### L5 — Integration

Mintek owns **FloatStar / MillStar / StarCS**, with 400+ installations across 40 countries. Feedforward-from-feed-composition is a documented gap in flotation control, which their platform currently fills with feedback only.

So: do not build a generic dashboard. Emit a **feedforward mineralogy channel over OPC-UA** (`asyncua`) in a StarCS-shaped interface. You are filling a hole in their product, not competing with it.

### Plant simulator (needed for closed-loop proof)

- **Flotation**: first-order kinetics with mineral-class-specific rate constants (Kelsall two-rate form). Produces a grade-recovery curve.
- **Comminution**: Bond/Morrell work index → kWh/t.
- **Ore variability generator**: sample from published Bushveld composition ranges (UG2 vs. Merensky vs. Platreef) to synthesise a realistic 30-day feed series with step changes and drift.
- Replay that series through (a) baseline feedback-only control and (b) your feedforward channel. Report the delta.

Build the circuit in plain Python, or in **IDAES** if you want the same process-engineering credibility play as UMLILO.

### L6 — Agentic layer

**The Autonomous Geometallurgist.** Overnight it ingests the day's images, runs distribution-drift detection, and **selects the highest-information samples for human QEMSCAN labelling** — an active learning loop. Then it retrains, validates against frozen gates, and writes the shift report.

Active-learning sample selection is the defensible agentic play here, because the agent is deciding *where to spend a scarce, expensive human resource*. That is a real decision with real economics behind it, not a chat wrapper. Same trilingual interface, same "LLM never computes" rule.

## 2.2 Hardware — this is where REEFPRINT wins

For UMLILO hardware is a flourish. Here it is the demo.

**The rig:**

| Component | Notes | Approx |
|---|---|---|
| Raspberry Pi 5 (8 GB) | host | R1,800 |
| Pi Camera Module 3 or HQ Camera | HQ if you want the petrographic look | R700–1,600 |
| **Pi AI HAT+ (13 TOPS, Hailo-8L)** | real-time on-device segmentation | R1,500–2,000 |
| 6–8 narrowband LEDs + PCA9685 driver | *wavelengths chosen by your band-selection algorithm* | R400 |
| Crossed polarising film | photography shop; gives the PPL/XPL look | R300 |
| Stepper + driver for rotating stage | the 72-rotation trick from MUMDMC2025 | R300 |
| **AS7341 breakout** (Adafruit/SparkFun) | 11-channel, 350–1000 nm, I²C. ~US$15–20 as a breakout — ignore the ~US$181 industrial-package figure | R400 |
| 3D-printed or cardboard light dome | | R200 |
| **Total** | | **~R5,700–7,000** |

Sourceable in SA from Micro Robotics, Communica, DIY Electronics, Pi Shop.

**The demo, and it is fifteen seconds:** a judge drops a rock chip into the dome. LEDs strobe through the selected bands. Live segmentation overlay appears on screen. Three processability numbers appear. A setpoint delta appears. The whole loop, on a real physical rock, in front of them.

**Then the kill shot.** Hand them something the model has never seen — a piece of concrete, or a wet sample — and **the conformal gate refuses.** *"Out of distribution. Holding last-good setpoint."* That is the moment you win the room, and it costs you nothing but the discipline to build the gate.

**Physical handout:** the Minimum Viable Spectrum bill of materials, printed. *Here are the six wavelengths. Here is the R6k rig. Here is the fraction of a 300-band hyperspectral system's discriminative power we retain.* Put paper in a judge's hand and your idea leaves the room with them.

## 2.3 Tests and proof

1. **Per-phase IoU/F1 and confusion matrix** — with recall on the sub-1% base-metal-sulphide class reported **separately and first**. Overall accuracy is a lie on UG2 and you should say so.
2. **Trivial baseline** — report majority-class accuracy explicitly, to kill the accuracy illusion before a judge does it for you.
3. **Abundance R² vs. teacher** — the distillation fidelity metric.
4. **The dirt benchmark** — synthetic dust, water film, vibration blur, lamp colour-temperature drift, calibration-tile drift. Report degradation as a table. Domain shift kills these systems in the field and no hackathon touches it. Consider publishing it as an open benchmark; that is a real contribution and both MOTT and a paper like it.
5. **Leave-one-orebody-out CV** — train UG2, test Merensky. Generalisation, not memorisation.
6. **Accuracy vs. labelled-area curve** — tells Mintek how much QEMSCAN time they can stop spending. That curve *is* the commercialisation argument.
7. **Conformal coverage curves** — empirical vs. nominal.
8. **Closed-loop A/B in the flotation sim** — Δrecovery, ΔkWh/t, Δreagent, in rands.
9. **Latency/FPS on Pi + Hailo** — on screen, live, during the demo.
10. **Band ablation** — full spectral set vs. your selected six. This is the evidence behind the hardware BOM.

## 2.4 The 1 September hedge

The architecture is label-modality agnostic, which is the entire point. Freeze the evaluation harness in **Week 1, on public data, before Mintek's data arrives** — it de-risks the build and gives you verifiable provenance for the originality check.

- **No data arrives**: build on MUMDMC2025 (14,400 photomicrographs, 5 mineral classes, PPL and XPL at 72 rotations, on FigShare), USGS splib07, ECOSTRESS, RockSL, plus Hapke-synthesised mixtures. The demo runs regardless.
- **Tiny dataset (n≈20)**: self-supervised pretraining plus physics-synthetic mixing is *precisely* the right architecture for this case, and conformal reports small-n honestly instead of lying.
- **Huge dataset**: same code scales. Publish the accuracy-vs-labelled-area curve as a bonus result.

---

# PART 3 — Shared engineering

**Repo**: monorepo, `uv` for packaging, `ruff` for lint, `pytest` + `hypothesis` for tests, pre-commit hooks, GitHub Actions CI running the full validation suite on every push. Docker Compose for the demo stack.

**Provenance for the originality check**: commit early and often from day one. A git history with real incremental commits, failed experiments and honest reverts is the strongest possible answer to an AI-generation flag. Write the abstract yourselves — a named orebody, a rand figure, a cited failure mode and one contrarian claim are things generators do not produce.

**Deliverables beyond the code**: model cards, a one-page integration guide, and a short technical report. Make MOTT's job easy and you make the commercialisation conversation easy.

**Timeline (four weeks, September)**

| Week | UMLILO | REEFPRINT |
|---|---|---|
| 1 | Tier A physics core + validation against published balances + frozen test harness | Public-data spine + frozen eval harness + self-supervised pretraining |
| 2 | Sobol corpus + surrogate + freeze-lining model + Curtailment Box | Mintek ingest + registration + weak supervision + processability heads + rig v1 |
| 3 | MPC + conformal gate + closed-loop A/B + copilot | Conformal + dirt benchmark + edge deploy + closed-loop numbers |
| 4 | Freeze. Ablations. Report. Backup video. Hostile Q&A drills. | Same. |

**Roles**

- **Ex-metallurgy (BCom BI)** — domain lead and **Q&A shield**. Owns the orebody/process narrative, defines the target variables, presents the plant-adjustment slide, red-teams the team weekly. This person takes the hostile question. Not a CS student.
- **Electrical Engineering** — sensing, optics, edge. Band selection, LED dome, radiometric calibration, ONNX quantisation, the Pi rig, OPC-UA hardware-in-the-loop.
- **CS 1** — modelling core (physics solver / distillation and segmentation).
- **CS 2** — decision layer: MPC or processability heads, conformal gate, OPC-UA shim, plant simulator.
- **CS 3** — frozen eval harness, CI, reproducibility, frontend and demo UI.

---

# PART 4 — Honest risk register

| Risk | Which | Mitigation |
|---|---|---|
| Open slag thermodynamics too weak for credible fidelity | UMLILO | Tier A reduced-order core validated against published balances; request FactSage access; state the limitation in the abstract rather than hiding it |
| Registration between teacher and student modalities fails | REEFPRINT | Week 1 priority, one full week budgeted, `itk-elastix` with MI metric |
| Scope sprawl — seven layers, four weeks, five people | Both | The closed-loop demo is sacred. Everything else is explicitly cuttable, in a written priority order agreed in Week 1. |
| Hardware fails on stage | Both | Rig is a prop, never the critical path. Backup video. Software demo runs standalone. |
| "You bolted a chatbot on" | Both | State the LLM-never-computes rule in the abstract and repeat it in the pitch |
| Physics theatre — invoking Hapke or liberation modelling loosely | Both | State assumptions explicitly, name the stereological bias, validate against something published |
| Sounding like you are replacing a Mintek division | Both | You amplify their archive and fill a gap in their platform. Say so twice. |
| Demo dies on Mintek's WiFi | Both | Everything runs on localhost |

---

## Verified stack reference

**Thermodynamics / process** — pycalphad · OpenCalphad · Thermochimica (ORNL) · Equilipy (`pip install equilipy`, needs a Fortran compiler, Python 3.10–3.14) · Cantera · `thermo`/`chemicals` · **IDAES** (DOE/NETL, Pyomo-based) · Pyomo + IPOPT · FactSage *(commercial — request supervised access)*

**ML / UQ** — PyTorch · ONNX Runtime · DINOv2/v3 · `segmentation_models_pytorch` · SAM 2 · **MAPIE** / **crepes** / **TorchCP** · NVIDIA **PhysicsNeMo** *(stretch)*

**Control** — **`do-mpc`** (CasADi-based NMPC) · Gymnasium + stable-baselines3 · **`asyncua`** (`pip install asyncua`, LGPL, Python ≥3.10)

**Spectral / imaging** — `hylite` + `hycore` · `spectral` (SPy) · scikit-image · SimpleITK / itk-elastix

**Data** — TimescaleDB · DuckDB + Parquet · MLflow · DVC

**Infra** — uv · ruff · pytest + hypothesis · Docker Compose · GitHub Actions · Modal *(burst CPU)* · Kaggle 30 h/wk · Colab 15–30 h/wk · Lightning AI *(student credits)*

**Hardware** — Raspberry Pi 5 · Pi AI HAT+ 13 TOPS (Hailo-8L) · AS7341 breakout (~US$15–20) · PCA9685 · MLX90640 *(optional)*

**Public datasets** — MUMDMC2025 (FigShare, DOI 10.6084/m9.figshare.29483204) · USGS splib07 · ECOSTRESS Spectral Library v1.0 · RockSL
