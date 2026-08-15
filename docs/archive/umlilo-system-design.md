> **SUPERSEDED — historical record only, see docs/01-design-v3.md**

# UMLILO Platform — System Design Document

**Mintek-SCI Grad Hackathon 2026 · Rev A · July 2026**

---

## 0. The architectural thesis

Both problems reduce to the same skeleton:

> *An unobservable industrial state must be inferred from cheap signals, grounded in physics, quantified for uncertainty, and converted into a control action whose value is denominated in rands.*

So we do not build two projects. **We build one platform and instantiate it twice.**

| | Instantiation |
|---|---|
| **UMLILO-Furnace** | Problem 5. Unobservable state = freeze-lining thickness, slag chemistry, bath enthalpy. Cheap signal = electrical + thermocouple data. Action = power/feed/flux setpoints. |
| **UMLILO-Reef** | Problem 3. Unobservable state = mineral phase map, liberation characteristics. Cheap signal = multispectral imagery. Action = reagent dose, mill throughput, blend ratio. |

This matters strategically, not just aesthetically. Mintek's Office of Technology Transfer does not commercialise projects; it commercialises **platforms**. A judge who sees one architecture serving two problem statements sees an asset. A judge who sees a single-purpose model sees a coursework submission.

**Choose one for the abstract. Build the shared spine so the other is a two-week port. Say that in the pitch.**

---

## 1. The dominance layer — what nobody else will do

Everything below this line is standard good engineering. These eight items are the ones that make the gap unbridgeable, and every one of them is cheap.

### 1.1 Every coefficient comes from South African law

Most teams will invent their economics. Ours are gazetted:

| Coefficient | Value | Source |
|---|---|---|
| Energy tariff | Megaflex TOU bands; R10.83/kVA max demand on peak+standard; 4.26 c/kVARh reactive above 0.96 PF | Eskom *Schedule of Standard Prices*, effective 1 April 2026 |
| Grid emission factor | 0.94 tCO₂e/MWh (2023 DGGEF) | DFFE *South Africa's Grid Emission Factors Report*, gazetted |
| Carbon price | **R308/tCO₂e from 1 Jan 2026**, rising to R462 by 2030; basic tax-free allowance down 10 pp in 2026, 2.5 pp/yr thereafter | Carbon Tax Act, Phase 2 |
| Curtailment obligation | up to 20% load reduction, max 2 hours, on Eskom instruction | Eskom load curtailment framework |

This produces a closed economic chain with **no invented numbers anywhere**:

```
ΔkWh/t  ──×  Megaflex band price  ──────────────→  R energy saved
        └──×  0.94 tCO₂e/MWh  ──×  R308/tCO₂e  ──→  R carbon tax avoided
Δcampaign days ──× amortised rebuild cost  ──────→  R capital deferred
```

When a judge asks where a number came from, the answer is a government gazette. That ends the question — and it is the difference between a projection and a claim.

### 1.2 Deliver it as an IEC 63278 Asset Administration Shell

The Asset Administration Shell (AAS) is the *standardised* Industry 4.0 digital twin — IEC 63278-1 ED1, specified by the Industrial Digital Twin Association, structured as submodels (Nameplate, TechnicalData, OperationalState, and so on).

**And there is a production-grade Python implementation: Eclipse BaSyx Python SDK** — MIT licence, `pip install basyx-python-sdk`, AAS metamodel as Python objects, AASX package read/write, JSON/XML serialisation, and a specification-compliant Dockerised HTTP server.

So UMLILO ships as a conformant AAS with purpose-built submodels:

| Submodel | Contents |
|---|---|
| `Nameplate` | asset identity, furnace/plant ID |
| `TechnicalData` | design capacity, refractory spec, transformer limits |
| `OperationalState` | live state vector, including estimated unobservables |
| `EnergyAndEmissions` | kWh/t, tCO₂e, tariff band, carbon liability in rands |
| `ModelProvenance` | model version, training data hash, validation status, conformal coverage |
| `AdvisoryActions` | recommended setpoint deltas + confidence + abstention flag |

Nobody at a student hackathon delivers a standards-conformant digital twin. This single decision changes what category you are competing in.

### 1.3 Conform to OPC UA for Mining (OPC 40560)

The OPC Foundation publishes an official **OPC UA Companion Specification for Mining** — type definitions for mining machines, equipment, systems and services, aligned with IREDES, championed by the Global Mining Guidelines Group as the industry's common data language.

Model your address space on it rather than inventing node names. Cost: a day of reading. Benefit: your integration story is *the industry's own standard*, and you can say the words "OPC 40560" in Q&A.

### 1.4 Draw the IEC 61511 safety boundary explicitly

IEC 61511 requires the Safety Instrumented System to be **physically and functionally separated** from the basic process control system and from any advanced/advisory control layer — no shared I/O, no shared buses.

So the architecture states, in writing and on a slide:

> UMLILO is a **supervisory advisory layer above the BPCS and strictly outside the SIS boundary**. It writes recommendations to a read-only advisory namespace. It cannot write to any safety instrumented function. Operator acknowledgement is required before any setpoint is actioned. Loss of UMLILO degrades the plant to existing BPCS control with no safety consequence.

Every plant engineer in that room has spent a career worrying about exactly this. One paragraph tells them you are not dangerous. **This is the single highest-credibility sentence available to you, and it costs nothing but knowing to write it.**

### 1.5 Estimate the unobservable state properly

Freeze-lining thickness is not measured. Neither is real-time slag chemistry. Most teams would predict them and move on. The correct answer is **data assimilation**: couple the physics model to a state estimator so measurements continuously correct both the state *and* the model parameters.

- **Moving Horizon Estimation** — native in `do-mpc`, consistent with the MPC formulation
- **Ensemble Kalman Filter** — published work couples a PINN digital twin with an EnKF to assimilate plant measurements and update state estimates and process parameters simultaneously

Saying *"we don't predict the freeze lining, we estimate it, and the estimator corrects the physics as it goes"* is a graduate-level control answer to what everyone else will treat as a regression problem.

### 1.6 Map to ISO/IEC 42001

ISO/IEC 42001 (published December 2023) is the first international AI management system standard. Certification requires a **centralised registry of every model, its training data sources, and its intended use**.

You will not certify. You will *conform* — MLflow as the registry, model cards, documented intended-use and out-of-scope statements, and a one-page mapping to the relevant clauses. For a state-owned entity like Mintek, which will eventually have to answer governance questions about any AI it deploys, arriving with the governance artefacts already written is a commercialisation accelerant.

### 1.7 Refuse, visibly

Conformal abstention, demonstrated live and deliberately. Covered in the build spec; restated here because it is a *requirement*, not a nice-to-have: **FR-31**.

### 1.8 Trilingual operator interface

English / isiZulu / Sesotho. One day of work. Impossible to argue with. Nobody else will do it.

---

## 2. Stakeholders and actors

| Actor | Type | Interest |
|---|---|---|
| **Furnace / Plant Operator** | Human, primary | Needs an actionable recommendation in their own language, with a reason and a confidence |
| **Metallurgist** | Human | Needs to interrogate *why*, and to override |
| **Plant Manager** | Human | Needs rands, kWh/t, recovery, campaign life |
| **Energy Manager** | Human | Needs curtailment compliance and tariff optimisation |
| **BPCS / DCS** | System | Exchanges process values and advisory setpoints over OPC-UA |
| **Historian** | System | Source of time-series; sink for advisory audit trail |
| **LIMS / Assay Lab** | System | Ground-truth feed and product assays, lagged |
| **SIS** | System, boundary | **Explicitly out of scope. Never written to.** |
| **Recalibration Agent** | Autonomous | Overnight drift detection, retraining, gated promotion |
| **Mintek Mineralogy Lab** | External | Teacher instrument archive (Reef instantiation) |

---

## 3. Requirements Definition Specification

Traceable IDs. Every one maps to a test in §11.

### 3.1 Functional — Physics & Estimation

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Compute multiphase equilibrium (slag/alloy/gas) from feed composition, temperature and pressure | Must |
| FR-02 | Integrate a dynamic energy balance with bath thermal inertia, losses and tapping | Must |
| FR-03 | Model freeze-lining thickness as a state variable via transient conduction with a moving boundary | Must |
| FR-04 | Reproduce published Mintek/Pyrosim mass-energy balances within a declared tolerance | Must |
| FR-05 | Estimate unobservable states from available measurements via MHE or EnKF | Should |
| FR-06 | Assimilate lagged laboratory assays as delayed measurements | Should |
| FR-07 | Enforce mass, energy and second-law consistency as testable invariants | Must |

### 3.2 Functional — Surrogate & Prediction

| ID | Requirement | Priority |
|---|---|---|
| FR-10 | Generate a design-of-experiments corpus over the full operating envelope (Sobol) | Must |
| FR-11 | Train a differentiable surrogate emulating the physics core | Must |
| FR-12 | Predict ≥3 named process outcomes — recovery, specific energy, slag composition | Must (deliverable) |
| FR-13 | Surrogate inference ≤10 ms per evaluation | Must |
| FR-14 | Export to ONNX for portable and edge deployment | Must |
| FR-15 | Support gradient-based inversion — solve for setpoints given a target | Should |

### 3.3 Functional — Uncertainty & Trust

| ID | Requirement | Priority |
|---|---|---|
| FR-20 | Emit calibrated prediction intervals at a configurable confidence level | Must |
| FR-21 | Empirical conformal coverage within ±3 pp of nominal | Must |
| FR-22 | Detect out-of-distribution inputs and flag them | Must |
| FR-23 | Attribute predictions to input features (SHAP) and report physics-consistency residual | Should |

### 3.4 Functional — Decision & Control

| ID | Requirement | Priority |
|---|---|---|
| FR-30 | Recommend setpoints minimising rands per tonne of contained metal subject to hard constraints | Must |
| FR-31 | **Abstain and hold last-good setpoint when the OOD gate trips or coverage degrades** | Must |
| FR-32 | Guarantee no recommendation can violate freeze-lining minimum, slag basicity window, or electrical limits | Must |
| FR-33 | Respond to a curtailment instruction with a compliant, ranked ramp-down plan within 60 s | Must |
| FR-34 | Price every recommendation using gazetted tariff, emission factor and carbon rate | Must |
| FR-35 | Log every recommendation, its inputs, its rationale and the operator's response | Must |

### 3.5 Functional — Integration & Interface

| ID | Requirement | Priority |
|---|---|---|
| FR-40 | Expose an OPC-UA server with an address space modelled on OPC 40560 | Must |
| FR-41 | Publish the twin as an IEC 63278 conformant AAS with defined submodels | Should |
| FR-42 | Write advisory values only to a read-only advisory namespace; never to SIS | Must |
| FR-43 | Operator interface in English, isiZulu and Sesotho | Should |
| FR-44 | Natural-language copilot answering operational questions via tool calls only | Should |
| FR-45 | Auto-generate the shift handover report | Could |

### 3.6 Functional — Autonomy

| ID | Requirement | Priority |
|---|---|---|
| FR-50 | Nightly drift detection over the previous 24 h of data | Should |
| FR-51 | Retrain the residual model and evaluate against frozen gates | Should |
| FR-52 | **Promote a model only if all gates pass; otherwise roll back and file a report** | Should |
| FR-53 | Maintain a registry of every model, its training data hash and intended use (ISO/IEC 42001) | Should |

### 3.7 Non-functional

| ID | Requirement | Target |
|---|---|---|
| NFR-01 | Advisory loop latency, sensor to recommendation | ≤2 s |
| NFR-02 | Availability during demo | 100% offline-capable, zero network dependency |
| NFR-03 | Reproducibility | Any result regenerable from a git SHA + seed |
| NFR-04 | Test coverage on physics core | ≥85%, including property-based invariants |
| NFR-05 | Auditability | Full lineage: recommendation → model version → training data hash |
| NFR-06 | Safety | No write path to any SIS. Architecturally enforced, not policy-enforced. |
| NFR-07 | Degradation | Loss of UMLILO leaves plant under existing BPCS control, no safety impact |
| NFR-08 | Portability | Full stack via `docker compose up` on a laptop |
| NFR-09 | Edge inference (Reef) | ≥10 FPS on Pi 5 + Hailo-8L |
| NFR-10 | Data sovereignty | All processing local; no plant data leaves the site |

---

## 4. Use case model

### 4.1 Catalogue

| ID | Use case | Primary actor |
|---|---|---|
| UC-01 | Monitor furnace state in real time | Operator |
| UC-02 | **Respond to an Eskom curtailment instruction** | Energy Manager |
| UC-03 | Optimise setpoints for cost under current tariff band | Operator |
| UC-04 | Interrogate a recommendation | Metallurgist |
| UC-05 | Override a recommendation | Operator |
| UC-06 | Handle degraded/failed sensor input | System |
| UC-07 | Assimilate a lagged lab assay | System |
| UC-08 | Nightly autonomous recalibration | Recalibration Agent |
| UC-09 | Generate shift handover report | System |
| UC-10 | Report campaign economics | Plant Manager |
| UC-11 | Classify feed mineralogy and emit feedforward (Reef) | System |
| UC-12 | Flag a sample for lab labelling (Reef, active learning) | Agent |

### 4.2 UC-02 — Respond to a curtailment instruction *(the demo spine)*

**Actor:** Energy Manager · **Trigger:** Eskom instructs load reduction · **Precondition:** twin online, state estimate converged

| # | Flow |
|---|---|
| 1 | Instruction received: required reduction %, duration, start time |
| 2 | System reads current state estimate, including freeze-lining thickness and bath enthalpy |
| 3 | System retrieves the applicable Megaflex band and carbon liability |
| 4 | MPC solves over the curtailment horizon plus recovery horizon, subject to hard constraints |
| 5 | System generates 3 ranked compliant plans, each with predicted recovery loss, ΔkWh/t, thermal-stress cost, carbon delta and total rand impact, each with a confidence interval |
| 6 | Plans presented in the operator's language |
| 7 | Operator acknowledges a plan |
| 8 | Setpoint trajectory written to the **advisory namespace** |
| 9 | BPCS actions it under existing operator authority |
| 10 | System logs instruction, plans, selection, outcome |

**Alternate A5a — no compliant plan exists within constraints:** System declares infeasibility, reports the binding constraint, escalates to the Metallurgist, holds last-good setpoint. *It does not return a plan that violates a constraint.*

**Alternate A2a — state estimate has not converged or OOD gate is tripped:** System abstains (FR-31), states why, recommends manual procedure.

**Postcondition:** Curtailment obligation met. Freeze lining never below minimum. Full audit trail written.

### 4.3 UC-06 — Degraded sensor input

| # | Flow |
|---|---|
| 1 | Sensor reads stuck, out of range, or drops out |
| 2 | Estimator flags inconsistency between measurement and physics-predicted value |
| 3 | System down-weights or rejects the channel, widens prediction intervals accordingly |
| 4 | If widened intervals breach the decision threshold → abstain, hold last-good setpoint, alarm |
| 5 | Log the event and the affected channel |

This use case is why the system is trustworthy. Demo it.

---

## 5. System model

### 5.1 State vector (Furnace instantiation)

```
Observed        z = [ arc voltage, arc current, electrode position, power factor,
                      shell thermocouples[1..n], cooling water ΔT and flow,
                      offgas temperature and composition, feed rate, feeder mass ]

Estimated       x = [ bath temperature, bath enthalpy,
                      freeze-lining thickness δ(θ),          ← unobservable
                      slag composition vector (CaO,MgO,Al₂O₃,SiO₂,Cr₂O₃,FeO),
                      alloy composition, refractory hot-face temperature,
                      cumulative thermal-stress damage D ]

Manipulated     u = [ arc power setpoint, feed rate, reductant ratio,
                      flux addition, tapping schedule ]

Exogenous       w = [ feed assay, Megaflex band, curtailment instruction,
                      ambient conditions ]

Outputs         y = [ metal recovery, specific energy kWh/t,
                      slag composition, tCO₂e, R/tonne contained metal ]
```

### 5.2 Domain entities

`Asset` (furnace/plant) · `Campaign` · `Shift` · `FeedLot` (assay) · `ProcessSample` (time-series) · `StateEstimate` · `Prediction` (with interval + coverage) · `Recommendation` (with rationale, economics, abstention flag) · `OperatorAction` · `ModelVersion` (with data hash, gates, promotion status) · `DriftEvent` · `CurtailmentEvent` · `EconomicSnapshot` (tariff band, carbon rate, emission factor as-at)

**Note the design decision:** `EconomicSnapshot` stores the gazetted coefficients *as at the time of the recommendation*. Tariffs and carbon rates change annually. Historical recommendations must remain reproducible against the prices that applied when they were made. This is the kind of detail that separates a system from a script.

---

## 6. Architecture

### 6.1 Level 1 — Context

```
   Operator ──┐                    ┌── Historian
 Metallurgist ─┤                    ├── LIMS
Plant Manager ─┼──▶ UMLILO ◀────────┤
Energy Manager ┘      │             ├── BPCS / DCS   (OPC-UA, advisory only)
                      │             └── Eskom tariff + curtailment feed
                      ▼
              ╔═══════════════════╗
              ║  SIS — OUT OF     ║   IEC 61511 boundary.
              ║  SCOPE. NO WRITE  ║   No shared I/O, no shared bus.
              ║  PATH EXISTS.     ║
              ╚═══════════════════╝
```

### 6.2 Level 2 — Containers

| Container | Tech | Responsibility |
|---|---|---|
| `physics-core` | Python, Pyomo + IPOPT, scipy, IDAES | Equilibrium, energy ODE, freeze-lining conduction |
| `corpus-gen` | Modal, joblib, Sobol | Parallel DOE generation → Parquet |
| `surrogate` | PyTorch → ONNX Runtime | Fast differentiable emulator, ensemble |
| `estimator` | do-mpc MHE / EnKF | State + parameter assimilation |
| `uncertainty` | MAPIE / crepes, Mahalanobis OOD | Intervals, coverage, abstention decision |
| `optimiser` | do-mpc (CasADi) NMPC | Constrained economic optimisation |
| `econ` | Python, parsed gazette data | Tariff, emission factor, carbon liability |
| `opcua-gw` | asyncua, OPC 40560 model | Advisory namespace, process value ingest |
| `aas-shell` | Eclipse BaSyx Python SDK | IEC 63278 submodels + conformant HTTP server |
| `agents` | tool-calling LLM, Ollama fallback | Copilot, scribe, recalibration |
| `api` | FastAPI | REST/WebSocket for the UI |
| `ui` | React + three.js + i18n | Furnace visualisation, trilingual advisory panel |
| `historian` | TimescaleDB | Time-series, recommendations, audit |
| `corpus` | DuckDB + Parquet | Simulation corpus analytics |
| `registry` | MLflow | Model versions, gates, ISO 42001 registry |
| `plant-sim` | Python + asyncua server (on a Pi) | Hardware-in-the-loop plant emulation |

**`do-mpc` is the load-bearing choice:** it ships native ONNX *and* native OPC-UA interoperability plus a data sampling framework and sensitivity calculation — so `surrogate` → `optimiser` → `opcua-gw` is one documented, published toolchain rather than three things bolted together.

### 6.3 Level 3 — `physics-core` components

```
physics-core/
├── thermo/        species Gibbs energies (NIST-JANAF, thermo/chemicals)
│                  slag activity model, regressed against published data
├── equilibrium/   constrained Gibbs minimisation (Pyomo + IPOPT)
├── dynamics/      bath energy ODE, stiff solver (BDF/Radau)
├── lining/        1D transient conduction, moving solidification boundary
├── wear/          thermal-stress integration → cumulative damage D
├── invariants/    mass / energy / second-law assertions (hypothesis)
└── validation/    reproduce published Mintek balances, report deviation
```

---

## 7. Data architecture

TimescaleDB — PostgreSQL with hypertables. Abridged DDL; the real schema carries constraints and indexes throughout.

```sql
CREATE TABLE asset (
  asset_id        TEXT PRIMARY KEY,
  asset_type      TEXT NOT NULL,          -- 'dc_arc_furnace' | 'flotation_circuit'
  design_capacity_mw NUMERIC,
  refractory_spec JSONB,
  aas_id          TEXT UNIQUE             -- IEC 63278 AAS identifier
);

CREATE TABLE campaign (
  campaign_id  BIGSERIAL PRIMARY KEY,
  asset_id     TEXT REFERENCES asset,
  started_at   TIMESTAMPTZ NOT NULL,
  ended_at     TIMESTAMPTZ,
  end_reason   TEXT                       -- 'planned_rebuild' | 'breakout' | ...
);

-- Raw process signals. Hypertable, partitioned on time.
CREATE TABLE process_sample (
  ts        TIMESTAMPTZ NOT NULL,
  asset_id  TEXT NOT NULL REFERENCES asset,
  tag       TEXT NOT NULL,                -- OPC 40560-aligned tag name
  value     DOUBLE PRECISION,
  quality   SMALLINT NOT NULL,            -- OPC-UA StatusCode
  PRIMARY KEY (asset_id, tag, ts)
);
SELECT create_hypertable('process_sample','ts');

-- Lagged laboratory truth. valid_at ≠ reported_at: this is the whole point.
CREATE TABLE assay (
  assay_id    BIGSERIAL PRIMARY KEY,
  asset_id    TEXT REFERENCES asset,
  stream      TEXT NOT NULL,              -- 'feed' | 'concentrate' | 'slag' | 'alloy'
  valid_at    TIMESTAMPTZ NOT NULL,       -- when the sample was taken
  reported_at TIMESTAMPTZ NOT NULL,       -- when the lab returned it
  composition JSONB NOT NULL,
  method      TEXT                        -- 'XRF' | 'QEMSCAN' | 'ICP'
);

-- Estimated state, including unobservables.
CREATE TABLE state_estimate (
  ts               TIMESTAMPTZ NOT NULL,
  asset_id         TEXT NOT NULL REFERENCES asset,
  model_version_id BIGINT NOT NULL,
  state            JSONB NOT NULL,        -- full x vector
  covariance       JSONB,                 -- EnKF ensemble spread
  converged        BOOLEAN NOT NULL,
  PRIMARY KEY (asset_id, ts)
);
SELECT create_hypertable('state_estimate','ts');

CREATE TABLE prediction (
  prediction_id    BIGSERIAL PRIMARY KEY,
  ts               TIMESTAMPTZ NOT NULL,
  asset_id         TEXT REFERENCES asset,
  model_version_id BIGINT NOT NULL,
  target           TEXT NOT NULL,         -- 'recovery' | 'kwh_per_t' | 'slag_comp'
  point_estimate   DOUBLE PRECISION,
  interval_lower   DOUBLE PRECISION,
  interval_upper   DOUBLE PRECISION,
  nominal_coverage NUMERIC,               -- e.g. 0.90
  ood_score        DOUBLE PRECISION,
  ood_flag         BOOLEAN NOT NULL
);

-- Gazetted economics, frozen at decision time. Non-negotiable for reproducibility.
CREATE TABLE economic_snapshot (
  snapshot_id       BIGSERIAL PRIMARY KEY,
  ts                TIMESTAMPTZ NOT NULL,
  tariff_band       TEXT NOT NULL,        -- 'peak'|'standard'|'offpeak'
  season            TEXT NOT NULL,        -- 'high_demand'|'low_demand'
  energy_c_per_kwh  NUMERIC NOT NULL,
  demand_r_per_kva  NUMERIC NOT NULL,
  grid_ef_t_per_mwh NUMERIC NOT NULL,     -- 0.94 (DFFE 2023 DGGEF)
  carbon_r_per_t    NUMERIC NOT NULL,     -- 308.00 from 2026-01-01
  source_document   TEXT NOT NULL         -- citation string
);

CREATE TABLE recommendation (
  rec_id            BIGSERIAL PRIMARY KEY,
  ts                TIMESTAMPTZ NOT NULL,
  asset_id          TEXT REFERENCES asset,
  trigger           TEXT NOT NULL,        -- 'periodic'|'curtailment'|'operator_request'
  curtailment_id    BIGINT,
  setpoints         JSONB,                -- NULL when abstaining
  abstained         BOOLEAN NOT NULL,
  abstain_reason    TEXT,
  binding_constraint TEXT,
  rationale         TEXT NOT NULL,
  economic_snapshot_id BIGINT REFERENCES economic_snapshot,
  delta_kwh_per_t   NUMERIC,
  delta_recovery_pp NUMERIC,
  delta_tco2e       NUMERIC,
  delta_rand        NUMERIC,
  confidence        NUMERIC,
  model_version_id  BIGINT NOT NULL,
  solve_ms          INTEGER
);

CREATE TABLE operator_action (
  action_id     BIGSERIAL PRIMARY KEY,
  rec_id        BIGINT REFERENCES recommendation,
  ts            TIMESTAMPTZ NOT NULL,
  operator_id   TEXT,
  decision      TEXT NOT NULL,            -- 'accepted'|'modified'|'rejected'|'ignored'
  modified_setpoints JSONB,
  reason        TEXT,
  ui_language   TEXT                      -- 'en'|'zu'|'st'
);

-- ISO/IEC 42001 model registry
CREATE TABLE model_version (
  model_version_id  BIGSERIAL PRIMARY KEY,
  name              TEXT NOT NULL,
  git_sha           TEXT NOT NULL,
  training_data_hash TEXT NOT NULL,
  intended_use      TEXT NOT NULL,
  out_of_scope_use  TEXT NOT NULL,
  gates             JSONB NOT NULL,       -- every gate + pass/fail
  promoted          BOOLEAN NOT NULL,
  promoted_by       TEXT,                 -- 'recalibration_agent' | human
  promoted_at       TIMESTAMPTZ
);

CREATE TABLE curtailment_event (
  curtailment_id  BIGSERIAL PRIMARY KEY,
  asset_id        TEXT REFERENCES asset,
  instructed_at   TIMESTAMPTZ NOT NULL,
  required_pct    NUMERIC NOT NULL,
  duration_min    INTEGER NOT NULL,
  complied        BOOLEAN,
  actual_reduction_pct NUMERIC
);
```

**Retention:** `process_sample` continuous-aggregated to 1-minute rollups after 30 days. `recommendation`, `operator_action` and `model_version` retained indefinitely — they are the audit trail, and audit trails do not expire.

---

## 8. Interface specification

### 8.1 OPC-UA address space (OPC 40560-aligned)

```
Objects/
└── Mintek/
    └── Furnace_01/                        ← MiningEquipmentType
        ├── Identification/                (OPC 40560 standard set)
        ├── ProcessValues/        [R]      arc V, arc I, thermocouples[], flows
        ├── StateEstimate/        [R]      bath T, freeze-lining δ, slag composition
        └── Advisory/             [R]      ← UMLILO writes here. Read-only to plant.
            ├── RecommendedSetpoints/
            ├── PredictionInterval/
            ├── Confidence
            ├── Abstained            (Boolean)
            ├── AbstainReason        (String)
            ├── BindingConstraint    (String)
            ├── EconomicImpactRand
            └── ModelVersion
```

**There is no node under any SIS branch. There is no write method targeting one.** The absence is the design.

### 8.2 AAS submodels

Served by the BaSyx Python SDK's spec-compliant HTTP server; exportable as an AASX package a judge can open in any AAS viewer. *Handing a judge a file that opens in standard industrial tooling is a different kind of demo.*

### 8.3 REST (abridged)

```
GET  /state/{asset_id}                    → current estimate + convergence
GET  /predict/{asset_id}                  → outcomes + intervals + OOD flag
POST /recommend                           → {trigger, horizon} → ranked plans | abstention
POST /curtailment                         → {pct, duration} → 3 ranked compliant plans
POST /copilot                             → {question, lang} → tool-grounded answer
GET  /economics/snapshot                  → active gazetted coefficients + citation
GET  /audit/{rec_id}                      → full lineage: rec → model → data hash
WS   /stream/{asset_id}                   → live state for the three.js view
```

---

## 9. End-to-end flow — the curtailment path

```
Eskom instruction
   → econ resolves Megaflex band, grid EF, carbon rate  → EconomicSnapshot (frozen)
   → estimator returns x̂ and convergence flag
        └─ not converged? ─────────────────────────────→ ABSTAIN, alarm, log. Stop.
   → uncertainty computes intervals + OOD score
        └─ OOD or coverage degraded? ──────────────────→ ABSTAIN, hold last-good. Stop.
   → optimiser solves NMPC over curtailment + recovery horizon, hard constraints
        └─ infeasible? ───────────────────────────────→ report binding constraint, escalate
   → 3 ranked plans, each priced in rands with a confidence interval
   → agents render into operator language, with rationale
   → UI presents; operator acknowledges
   → opcua-gw writes to Advisory/ namespace only
   → BPCS actions under existing operator authority
   → historian logs instruction, plans, selection, outcome, model lineage
   → aas-shell updates OperationalState + AdvisoryActions submodels
```

Three of the eight steps can terminate in refusal. **That ratio is the product.**

---

## 10. Standards conformance matrix

| Standard | Scope | How we conform |
|---|---|---|
| **IEC 63278-1** | Asset Administration Shell | Six purpose-built submodels via Eclipse BaSyx Python SDK; AASX export |
| **OPC 40560** | OPC UA for Mining companion spec | Address space modelled on standard types; IREDES-aligned |
| **IEC 62541** | OPC UA | `asyncua`, StatusCode quality propagation |
| **IEC 61511** | Functional safety | Advisory layer strictly outside SIS; no write path; graceful degradation (NFR-06/07) |
| **ISO/IEC 42001** | AI management system | Central model registry with training data hashes and intended-use statements (FR-53) |
| **Carbon Tax Act (Phase 2)** | Emissions liability | R308/tCO₂e applied in the objective function |
| **Eskom Schedule of Standard Prices 2026/27** | Tariff | Megaflex TOU bands, demand and reactive charges parsed from gazette |
| **DFFE Grid Emission Factors Report** | Scope 2 | 0.94 tCO₂e/MWh |

Put this table on a slide. It is the single most disorienting thing you can show a panel that expects student work.

---

## 11. Verification & validation matrix

| Test | Verifies | Method | Gate |
|---|---|---|---|
| T-01 Published-balance replication | FR-04 | Reproduce documented Mintek/Pyrosim ferrochrome balances | deviation within declared tolerance, cited |
| T-02 Physics invariants | FR-07 | `hypothesis` property-based: mass, energy, second law | zero violations over 10⁴ random valid inputs |
| T-03 Surrogate fidelity | FR-11 | R²/MAPE on held-out Sobol points | R² ≥ 0.98 in-hull |
| T-04 Extrapolation | FR-11 | Evaluate outside training hull vs. XGBoost baseline | physics-informed degrades gracefully; baseline does not |
| T-05 Conformal coverage | FR-21 | Empirical vs. nominal, plotted | within ±3 pp across the range |
| T-06 OOD detection | FR-22 | Injected anomalies + genuinely novel conditions | TPR ≥ 0.95 at FPR ≤ 0.05 |
| T-07 Constraint inviolability | FR-32 | 10⁵ randomised MPC solves | **zero** constraint violations |
| T-08 Closed-loop A/B | FR-30 | 1000 × 30-day campaigns, stochastic curtailment, vs. rule-based baseline | ΔkWh/t, Δrecovery, Δcampaign days, ΔR/t **with CIs** |
| T-09 Curtailment response | FR-33 | Simulated instructions across the state space | compliant plan or declared infeasibility ≤60 s, 100% |
| T-10 Degraded sensor | UC-06 | Stuck / dropped / drifting channels | abstains or widens correctly, never fails silent |
| T-11 Latency | NFR-01, FR-13 | Percentile timing under load | p99 ≤ 2 s end-to-end |
| T-12 Audit completeness | NFR-05 | Random recommendation → trace to data hash | 100% traceable |
| T-13 Offline operation | NFR-02 | Full demo with network physically disconnected | passes |
| T-14 SIS isolation | NFR-06 | Static analysis + address-space audit for any write path | **zero** paths found |
| T-15 AAS conformance | FR-41 | Validate against IDTA schema; open AASX in third-party viewer | validates and opens |
| T-16 Edge inference (Reef) | NFR-09 | FPS on Pi 5 + Hailo-8L | ≥10 FPS |

T-04, T-07 and T-14 are the three that end arguments. T-04 justifies the architecture. T-07 proves it is safe. T-14 proves the safety is structural rather than promised.

---

## 12. Techno-economic model

For the MOTT commercialisation conversation, which is where the vacation-work offer actually comes from.

**Per-furnace annual benefit** = energy saved × tariff + tCO₂e avoided × R308 + campaign extension × amortised rebuild cost + recovery uplift × metal price

**Costs:** engineering integration, sensing where required, licence, support.

**Report:** NPV at a stated discount rate, simple payback, and a sensitivity tornado over the three or four coefficients that dominate. Be explicit that recovery uplift is the least certain input and show the case that survives without it.

**Addressable market framing:** the ferrochrome sector alone directly and indirectly supports up to 185,000 jobs, and exports fell 63% under energy-cost pressure. Mintek's control platform already sits in 400+ installations across 40 countries — that is the distribution channel, and it is theirs, not yours. Frame yourself as a module for a product they already sell.

---

## 13. Deployment

**Demo (2 October):** single laptop, `docker compose up`, plus one Raspberry Pi over ethernet running `plant-sim` as an OPC-UA server with the physical curtailment button. Zero internet. Ollama-served local model for the copilot. Backup video on a second device.

**September build:** local dev; Modal for corpus burst; Kaggle/Colab for training; MLflow local; GitHub Actions running T-01 through T-12 on every push.

**Notional production:** on-premise beside the BPCS, air-gapped from the internet, advisory namespace only. No plant data leaves the site (NFR-10). Say this — mining companies care about it more than almost anything else you could offer.

---

## 14. What to cut, in order

Agreed in Week 1 and written down, because scope discipline under pressure is a decision you make in advance or not at all.

Sacred: physics core (FR-01/02/03), validation against published balances (FR-04), surrogate (FR-11/12), conformal + abstention (FR-20/31), MPC with hard constraints (FR-30/32), curtailment response (FR-33), closed-loop A/B (T-08), the demo.

Cut in this order: (1) shift scribe · (2) AAS submodels beyond OperationalState · (3) RL agent · (4) three.js view → Streamlit · (5) EnKF → simpler MHE · (6) nightly agent → manual retrain with the same gates · (7) two of three languages.

**Never cut:** abstention, hard constraints, published-balance validation, the SIS boundary statement. Those four are the identity of the project.

---

## Appendix — key sources

Eskom *Schedule of Standard Prices 2026/27* · DFFE *Grid Emission Factors Report* (0.94 tCO₂e/MWh) · Carbon Tax Act Phase 2 (R308/tCO₂e from 1 Jan 2026) · IEC 63278-1 / IDTA AAS specification · Eclipse BaSyx Python SDK · OPC UA Companion Specification Mining (OPC 40560) · IEC 61511 SIS/BPCS separation · ISO/IEC 42001 · `do-mpc` (ONNX + OPC-UA interop) · IDAES (DOE/NETL) · Mintek Pyrosim / FactSage published ferrochrome balances · Mintek FloatStar/MillStar/StarCS (400+ installations)
