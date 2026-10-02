# 20 — Competitors, where we differ, who we sell to, what it costs, who we need

*2026-10-02. Tags as in docs/17: [P] primary-read, [V] vendor claim, [N] news, [S] search summary, ASSUMED = our assumption. Money uses `training/economics-20261002/results.json`. Nothing here is a quote or a contract.*

## 1. Who is already out there

| Company / product | Layer | What it does | Evidence | Stronger than us at | Where REEFPRINT differs |
|---|---|---|---|---|---|
| **Blue Cube MQi** (Stellenbosch; Draslovka) | slurry sensor | In-line diffuse-reflectance analyser. At Northam: PGM g/t and Cr₂O₃ %, 15 s updates, R² 0.84 / 0.92 vs lab | [S] | Installed (>100 units [S]), in the pipe, measures the PGM stream directly | We read **ore before the mill** (belt), and add mineralogy-taught predictions, refusal and decisions. Blue Cube is an **input**, not a rival |
| **Plotlogic OreSense** | face / belt hyperspectral | Ore/waste classification; scan-to-result < 20 min; ore-spotter SD 11.6 → 4.3 | [V] | Field-proven hardware, mining-face workflows | Plant-side decisions (feed rate, reagent prompts), PGM/chromite physics, calibrated intervals with a typed fallback |
| **MineSense ShovelSense** | shovel XRF | Bucket-by-bucket grade; Copper Mountain recovered 342 kt of ore from waste (C$3.6 M) | [V] | Production deployments, ore-routing at the source | Mineralogy and plant response; not elements |
| **Thermo CB Omni, Scantech GEOSCAN, RTI AllScan** | cross-belt PGNAA/PFTNA | Bulk elements through the burden | [S] | Penetrates the whole burden; the industry standard for elements | No radioactive source; mineral (not element) information; we **fuse** their elements where present |
| **IntelliSense.io brains.app** | AI process optimisation | Physics-informed digital twins + ML; flotation recovery +1–3% at a South American copper operation | [V] | Deployed optimisation apps, scale, awards | Ore-side, mineralogy-taught input with conformal refusal; open validation and **published corrections**; PGM focus |
| **PETRA MAXTA** (Maptek since March 2026) | AI value-chain twins | Predicts plant performance from ore data; tailings grade 6 h ahead | [V] | Hundreds of deployments [V]; mine-to-mill integration | Real-time belt mineralogy and a human-in-the-loop decision record; cost |
| **Mintek FloatStar / MillStar** | APC | Stabilisation and optimisation; FloatStar uses feed chemistry for mass-pull setpoints; Vale +2.7% recovery over 400 days | [P] | The actuator; decades in SA plants | **Partner, not rival.** We would be an uncertainty-aware input inside its limits |
| **QEMSCAN / MLA / TIMA** (e.g. at Mintek) | truth lab | Phases, liberation, association | [P] price list | The truth | We predict between truth results; their composites retrain us |
| Froth and size cameras (Metso, Outotec, WipWare, Split) | process cameras | Froth state, rock size | [S] | Installed base | Ore mineralogy upstream of both |

**Said honestly.** We are **not** "way better" than proven vendors. They have deployments; we have a validated prototype on public data. What we have that we have not found combined elsewhere:

1. **Mineralogy-taught belt predictions with calibrated one-sided bounds** (exact split-conformal), a refusal path and a **typed conservative envelope**: no "unknown", no "hold the last setpoint".
2. **Validation in the open, including our own corrections.** MINERAL1 withdrawn, Bushveld reframed, "same risk" withdrawn and then re-tested. All of it is in git.
3. **PGM/UG2 physics in the advice.** The chromite entrainment vs recovery trade-off (Jones, Mintek 2005), the spiral size window, and the diagnostic prompts gated on validated inputs.
4. **Security by design, with post-quantum-signed decision records** (docs/19). Relevant because Sibanye-Stillwater, an SA PGM major, was hit by ransomware in July 2024 [S].
5. **Offline-first and cheap.** No radioactive source, parcel-level SWIR, classical models (92 ms/parcel on a 4-core CPU, measured).

**Gaps we still have** (and what we are building):
- no Bushveld belt data (pilot);
- no APC comparison (pilot);
- no field hardware (ADR-0002: design only);
- three spectral associations not yet tested (v8-features, running);
- authentication and the deployment (Track S/D, in progress).

## 2. Who we pitch to, and why they would pay

- **Buyer:** the concentrator manager or GM metallurgy at a South African PGM producer: Valterra Platinum, Implats, Sibanye-Stillwater, Northam, Tharisa, ARM. They own recovery, concentrate quality (Cr₂O₃) and mill throughput.
- **Partner and channel: Mintek.** Truth lab (QEMSCAN/MLA), APC integration (FloatStar/MillStar), and MOTT IP assessment with invention credits (the competition terms).
- **Why they pay:** recovery points are worth money. +1 pp is **R64–153 M/yr net** at a Zondereinde-size plant and **R0.6–1.5 bn/yr** at Implats-group scale (ASSUMED inputs, economics V1). The pilot breaks even at **0.04–0.26 pp** (V4).
  - Valterra reported recovery moves of **+1 pp (Mototolo) and +2 pp (Amandelbult)** in 2025 [P]. Moves of that size happen and get reported.
  - Ours are unmeasured until a pilot.

## 3. What it would cost them (all ASSUMED; quotes required)

| Item | Range (ASSUMED) | Basis |
|---|---|---|
| Pilot installed capex (one belt) | US$0.5–3.0 M | economics V4 grid; SWIR camera class US$50k–300k [S] |
| Pilot opex (sampling, assays, Bond tests, QEMSCAN composites, maintenance, support) | US$0.1–0.6 M/yr | V4 grid |
| Subscription after a successful pilot | priced at ≤ 20% of **measured** net value (ASSUMED share), per concentrator per year | value-based; no measured value yet, so no number |
| QEMSCAN at shift cadence (what prediction replaces) | CAD 2.7 M/yr per stream (2017 list incl. prep and mount) | economics V5, [P] SRC price list |

## 4. How long, with whom

**Timeline (ASSUMED, from docs/18):**
- Month 0–1: site agreement, data access, POPIA and OT approvals.
- Month 1–2: install and commission.
- Months 2–5: **shadow**.
- Months 5–8: **advisory**.
- Month 8–9: decision.
- Then coupling to APC.

**Team:**

| Role | Who | FTE in pilot (ASSUMED) |
|---|---|---|
| Domain and product lead, decisions (single technical decision-maker) | Lethabo Hoaeane | 1.0 |
| ML / computer vision (KHANYA segmentation, models) | Sibusiso Khumalo | 1.0 |
| Software, security, deployment | Ipeleng Modise | 1.0 |
| Process metallurgist | site or Mintek mentor | 0.3 |
| Mineralogist (QEMSCAN/MLA truth) | Mintek | 0.2 |
| Instrumentation engineer (install, enclosure, encoder) | site | 0.3 |
| OT/IT security officer (historian read, DMZ) | site | 0.1 |
| Information officer and workforce representative (decision-record policy) | site | as needed |

## 5. What one mentor session produced (measured from git, not claimed)

Since the mentor framework entered the deck (2026-10-01 11:44 — the session with a chemist, a mineralogist and a metallurgist), **27 commits in about 28 hours** on this branch. Among them:

- **Kaggle runs:** HIDSAG v3–v8, the moving-belt simulation, the full-resolution export, the exact-bound re-run, spectral features.
- **Four ClauDex adversarial reviews** (Codex gpt-6-astra).
- **Three published self-corrections:**
  - MINERAL1 (camera reading mineralogy) withdrawn;
  - Bushveld grade routing reframed (the mine-plan seam is better);
  - "same overload risk" withdrawn, then re-tested with the exact bound.
- **REEFPRINT Live**, with 7 views:
  - a belt replay of real scans;
  - the Bushveld PGE track;
  - a real-plant track;
  - lab import and exports;
  - the value chain;
  - the evidence;
  - where it sits.
- **docs/16–20:** value chain, the industry dossier with tagged sources, the installation and pilot design, security, and this document.
- **A deployable model:** exported, it loads locally, and runs in 92 ms per parcel on Kaggle CPU.

**What this says to a sponsor.** With daily access to their chemist, mineralogist and metallurgist, plus site data, the loop of question → measurement → correction runs at this speed. The bottleneck becomes site data, not the team.

## 6. Risk register (top items)

| Risk | Mitigation |
|---|---|
| The method does not transfer to Bushveld ore | Shadow phase with QEMSCAN and Bond truth; a 2025 Merensky hyperspectral study [S] suggests the sensing layer transfers |
| Wet ore makes refusals common | Coverage reported by condition; the fallback is budgeted |
| No gain over the existing APC | On/off block design; stop rules |
| Cyber attack or ransomware | docs/19: segmentation, least privilege, offline immutable backups, PQ-signed records |
| Labour or privacy objections to decision records | Purpose, retention and non-disciplinary use agreed first; no individual scores |
| Overclaiming to a Mintek audience | Every rand carries its assumption label; corrections are public |
