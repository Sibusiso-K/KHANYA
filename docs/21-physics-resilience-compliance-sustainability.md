# 21 — Is it physically possible, and what happens when the power goes? Resilience, kinetics, radiation, compliance, waste, scale-up

*2026-10-02 (11:30). Tags: [P] primary-read · [V] vendor · [S] search summary (indicative, not citable until read) · sim_ simulated on real data · ASSUMED.*

**Computed evidence:**
- `training/physics-checks-20261002/results.json`
- `training/value-chain-20261002/results.json`
- `training/installation-20261002/sensor_geometry.json`
- `training/hidsag-v8-*`
- `training/hidsag-v9-robustness-20261002` (running)

## 1. Is it physically possible? Every claim against its physics and its proof

| Claim | The physics it rests on | How it was tested | Status |
|---|---|---|---|
| Belt hardness → feed rate gains tonnes | Bond (1961): energy per tonne ∝ Wi, so tonnes per hour = power ÷ energy per tonne | sim_ on 146 real held-out predictions; exact one-sided conformal bound; non-inferiority on overload | **+1.9% [+0.9, +2.9], non-inferior (+1.4 pp upper bound). Provisional** (disclosed method switch) |
| …without losing flotation recovery | First-order flotation kinetics R(t) = Rf(1−e^(−kf·t)) + Rs(1−e^(−ks·t)); +1.9% tonnes shortens residence time by 1.9% | Two-component fit (RMSE 0.001) to the Mintek-framework kinetics curve (slide 16) | **0.25 pp loss** at 1 lab-min equivalent; **0.10** at 2; **0.04** at 3; **~0 on the plateau**. So the feed rule must first check residence-time headroom |
| More tonnes under Eskom curtailment by sending soft ore through the cut hours | Energy is conserved over a cycle | sim_ with 500 days of 60 real parcels | **Rejected.** −3.8% (even an oracle loses 3.0%): the hard ore still has to be milled. Not claimed |
| Chromite entrainment costs PGM recovery | Mintek testwork: 87% recovery at 2.9% Cr₂O₃ vs >90% if Cr₂O₃ were relaxed to 4–10% **[P]** (Jones 2005) | Literature; not measured by us | Evidence of a trade-off, not money |
| Spirals recover by-product chromite | Gravity separation works at 75 µm–3 mm; < 53 µm reports to tails **[P]** (Molefe & Baloyi 2022) | Literature | A prompt for size-characterised streams only |
| The belt camera identifies ≥ 3 minerals | Vibrational SWIR absorption (Al-OH, Fe-OH, Mg-OH, H₂O) | Pre-registered test against QEMSCAN on 36 composites | **Not shown.** H2 ρ +0.27 is below the 0.30 minimum useful effect. **KHANYA's microscope carries ≥ 3 phases** |
| The camera resolves the ore on a fast belt | Line pitch = speed ÷ line rate | Computed from the SX25 datasheet **[P]** | 9–19 mm lines, 1.4–2.3 mm pixels. **Parcel-level, not particle-level** |
| It is real-time | Compute time per parcel | Measured | **92 ms median** (Kaggle 4-core CPU); 159 ms on this laptop |
| It works on a capture it has never seen | Generalisation | v9: new-capture, partial, gain, noise and wavelength-shift variants, scored by the fold model that never saw the parcel | **New capture: MAE ×1.00 [0.99, 1.01]: equivalent (gate passed).** Partial view, noise and ±15% light are tolerant. **Wavelength drift of one band: ×1.25, mostly not flagged.** Hence a wavelength-calibration gate (docs/18) |

## 2. Power cuts, load-shedding and curtailment: what the plant does, and what REEFPRINT does

**The context.**
- Mining and smelting draw about 10,000 MW, roughly 30% of Eskom's supply **[S]**.
- Curtailment asks mines to cut 10% at stages 1–2, 15% at stage 3 and 20% at stage 4. Under the stage-6 agreements, mining cuts **20% of contracted supply for 10 hours (14:00–24:00)** **[S]**.
- Reported impacts include RBPlat losing 154 hours to curtailments **[S]**.

**What REEFPRINT must do:**

| Event | Plant reality | REEFPRINT behaviour (design) |
|---|---|---|
| **Short dip / brown-out** | Drives may trip | UPS ride-through for the edge PC, encoder and network. The camera and lamps may drop, and any parcel scanned while lamps are below the reference level is **refused** (white-reference gate), not predicted |
| **Power cut (minutes to hours)** | Mills and conveyors stop | Edge PC on UPS: finishes writing and **shuts down cleanly**. Ledger durability: SQLite WAL, append-only, torn-write recovery. Nothing is lost that was acknowledged |
| **Restart** | Mills restart under transient conditions | (1) Halogen warm-up and a **fresh white/dark reference before any prediction**. (2) The first parcels after a restart are likely out-of-distribution, so the **conservative envelope** applies until the gate passes. (3) Predictions older than the parcel's arrival are **stale → fallback** |
| **Curtailment (20% for 10 h)** | Less mill power | (1) The feed for reduced power is computed from the same hardness bound, so the **grind holds** instead of overloading. (2) A **tonnage forecast** for the window from the ore about to be reclaimed (production planning). **No tonnage gain is claimed** from re-ordering (§1) |
| **Network to the control room lost** | — | **Store-and-forward**: the edge keeps predictions and its local ledger; the control-room screen shows "stale" and the envelope fallback applies |
| **Whole site dark, or a cyber incident** | — | REEFPRINT runs **fully offline on one laptop** (constitution: offline demo). Signed checkpoints and offline backups allow a verified restore (docs/19 §5) |

**Why this keeps trust.** No decision is made on bad light, stale data or unfamiliar ore. The system says so, gives the safe setting, and records it. **Lost work time is not made worse by the tool.** The plant falls back to its normal procedure, never to "hold the last setpoint" (rule 5).

**Energy security context** (not our product): Northam's large solar programme is reported to save about R700 M a year **[S]**. South Africa's helium-cooled **HTMR-100** small modular reactor design needs no cooling water, targets mining and industrial complexes, and the government has signalled a 2,500 MW nuclear programme including SMRs **[S]**.

## 3. Reaction kinetics: where they enter the decision

- **Flotation (the next step after the mill).** Recovery rises with residence time along a kinetics curve (§1). Liberation classes set the rate constants: liberated grains float fast, locked ones slowly. KHANYA's liberation measurement plus the published rate constants gives the curve. The feed-rate rule therefore checks **residence-time headroom** before raising the feed: on the steep part of the curve, the extra tonnes cost recovery.
- **Reagent conditioning.** Collector and depressant adsorption needs contact time. A feed change shortens conditioning too, which is a reason the envelope ramps feed **up slowly**.
- **Smelting (downstream).** Above about **1.8% Cr₂O₃ in slag**, chromite spinel saturates and builds up **[P]** (Eksteen et al. 2011). That is why concentrate Cr₂O₃ is a hard constraint, and why entrainment control matters.

## 4. Radiation and nuclear: what it can and cannot do

**Does REEFPRINT detect radiation? No.** The camera senses reflected light at 0.4–2.5 µm. Ionising radiation (gamma, neutrons) needs a scintillator (NaI/CsI) or a semiconductor detector (HPGe). We will not claim otherwise.

**Can it help?** Yes, **as an added input**: a belt gamma-dose monitor beside the scanner would let REEFPRINT log NORM screening per parcel and **escalate** high readings. In South Africa, NORM in mining is regulated by the **National Nuclear Regulator**, with guides on occupational safety assessment (RG-0024) and on NORM tailings and waste rock (RG-0018) **[S]**. Whether a given PGM operation needs NORM monitoring is a site radiation assessment, not our call.

**Advantage over PGNAA.** Isotope cross-belt analysers use a Cf-252 neutron source that needs NNR authorisation **[S]**. REEFPRINT's optical sensor has **no radioactive source**.

## 5. Waste, emissions, water, safety: mechanisms (not yet measured savings)

| Area | Mechanism | What it would take to prove |
|---|---|---|
| **Less metal to tailings** | Every recovery point kept is metal not dumped in the TSF. At Zondereinde scale, +1 pp ≈ 3,400 oz/yr less 4E to tails (economics V1, ASSUMED inputs) | Plant mass balance, pilot on/off blocks |
| **Excess material: chrome in UG2 tails** | Chrome is recovered from UG2 tails by spirals; Valterra's chrome yields rose 0.3–0.5 pp in 2025 **[P]**. REEFPRINT's prompt: send a size-characterised stream to spirals, with a PGM-loss balance | Size-by-size tails assays |
| **Tailings governance** | GISTM (2020, 77 requirements); the Global Tailings Management Institute launched in South Africa in 2025 **[S]**; NEMWA residue regulations (2015) require characterisation and classification of residue **[S]**. REEFPRINT's per-parcel mineral record **adds to that characterisation** | Integration with the site's TSF data |
| **Energy / emissions** | Comminution is 1–4% of the world's electricity and about 50% of mine-site energy **[P]** (CEEC). Grinding is the plant's largest load (e.g. Impala's UG2 ball mill: 6.1 MW **[S]**). The right feed for the ore avoids over-grinding and overload, so kWh/t at the target grind falls | Mill power and grind logs, kWh/t before and after |
| **Water** | Recycled process water changes flotation: Cu²⁺, Pb²⁺ and Fe²⁺ activate gangue in UG2 and lower grade **[S]**; closed circuits reduce discharge **[S]**. A future REEFPRINT input is process-water chemistry, so the advice can say "your water, not your ore" | Water assays alongside flotation |
| **Safety** | Fewer manual grab samples at conveyors and launders; no radioactive source; refusal instead of guessing. The camera sits over a guarded conveyor, with lockout for maintenance (docs/18 §3) | Site risk assessment (MHSA) |

## 6. How it sits with the existing equipment (and the energy each uses)

| Stage | Typical equipment (by name) | Energy (indicative) | REEFPRINT's role |
|---|---|---|---|
| Crushing | Jaw, gyratory and cone crushers (Metso, FLSmidth, Sandvik) | about 2 kWh/t in surveyed concentrators **[S]** | none |
| Conveyance | Mill-feed conveyor with belt-speed encoder | small | **The scanner sits here** (SX25 + VNIR + halogen + reference; docs/18) |
| Milling | Primary and secondary ball mills (e.g. Impala UG2: 9.3 × 6.1 m, **6.1 MW** motor **[S]**); AG/SAG in some circuits | about 10–20 kWh/t **[S]** | **The feed proposal inside the envelope**; MillStar is the actuator |
| Classification | Hydrocyclones (Weir Cavex, Multotec) | pumping | Diagnostic prompt: chromite over-grinding (density classification) |
| Flotation | Mechanical cells (Outotec TankCell, Metso); **Jameson Cells** (Valterra Mogalakwena **[P]**); columns | about 2.6–4.8 kWh/t **[S]** | Residence-time check; reagent and water prompts; FloatStar is the actuator |
| By-product | Spirals (MetQ, Multotec) on tails | low | Prompt for size-characterised streams |
| Analysis | Blue Cube MQi (slurry), Courier-type XRF, froth cameras; fire assay, QEMSCAN/MLA (Mintek) | — | **Inputs and truth**; REEFPRINT fuses them and learns from them |
| Control and data | DCS, APC (MillStar/FloatStar), historian | — | Read via the DMZ; writes only after sign-off |

## 7. Policy, compliance and governance (South Africa first)

**Safety and mining law:**
- **Mine Health and Safety Act 29 of 1996**: risk assessment for any equipment at conveyors.
- **MPRDA**.
- **Mining Charter**: skills and local procurement.

**Environment:**
- **NEMA**, the environmental framework.
- **NEMWA** and its 2015 residue regulations, for tailings characterisation **[S]**.
- **National Water Act**, for water-use licences.

**Radiation:**
- **National Nuclear Regulator Act 47 of 1999**: NORM and sources **[S]**. We have no source.

**Data and cyber:**
- **POPIA**: the decision record holds personal information, so purpose, retention and non-disciplinary use are agreed.
- **Cybercrimes Act 19 of 2020**: incident reporting duties.
- **IEC 62443** (OT zones and conduits) and **ISO/IEC 27001** (ISMS) as the frameworks; docs/19.

**Tailings:** **GISTM**.

**AI governance** (how we run models):
- Versioned, frozen models in evaluation.
- Conformal intervals and OOD refusal.
- A human approves within an envelope.
- Every decision in a signed record.
- Promotion only through a chronological validation gate.
- Corrections published (MINERAL1, Bushveld, "same risk", curtailment).

## 8. From small scale to full scale

| Stage | What exists | What is proven there | Cost and people (ASSUMED) |
|---|---|---|---|
| 0. Replay (**now**) | Public data, app, secure server, models | Methods, honesty, latency, security | The team |
| 1. Bench | The camera on a lab conveyor with site samples + QEMSCAN/MLA at Mintek | Transfer to Bushveld ore; feature associations on real UG2/Merensky | Camera rental or loan; Mintek lab time |
| 2. Shadow (one belt) | Installed scanner; predictions logged only | Coverage under real conditions (wet, dust, curtailment); Bond-test agreement | docs/18 capex grid |
| 3. Advisory | The decision record in use | Decision quality; escalation burden | Site metallurgist time |
| 4. Coupled (one plant) | APC input within limits | KPI on/off blocks (recovery, Cr₂O₃, kWh/t) | Integration |
| 5. Fleet | Several concentrators; one truth lab | Transfer across reefs; model governance at scale | Subscription |

## 9. The gaps, plainly

- No Bushveld belt data.
- No APC comparison.
- No plant trial.
- The belt does **not** yet identify minerals.
- The OOD gate accepted 0–80% of a foreign ore across folds (inconsistent), and it barely flags wavelength drift (v9).
- The throughput non-inferiority is provisional.
- No radiation sensing.
- Water chemistry is not an input yet.
- The Dockerfile is unbuilt (no Docker on the dev laptop).
- No public deployment (it needs your approval).

## 10. Evidence needed to prove the application (the pilot's measurement list)

1. Belt scans + Bond WI tests on the same parcels (Bushveld ore).
2. QEMSCAN/MLA composites (feed, concentrate, tails), including refused parcels.
3. Mill power, feed rate, cyclone overflow P80, and flotation residence times, as time series.
4. Fire assays (head, concentrate, tails) and Cr₂O₃ in concentrate, residence-time aligned.
5. Usable coverage by moisture, dust and curtailment state.
6. On/off operating blocks with frozen models, against the APC baseline.
7. Restore test and security review (docs/19).

## 11. Skills, sovereignty, water

- **Skilled work.** It creates work for instrumentation technicians (enclosure, calibration), metallurgical data analysts (decision-record review) and a security/OT role. We do not claim job numbers.
- **Sovereignty and capability retention.**
  - Built in South Africa, on South African ore problems.
  - IP assessed by MOTT, with invention credits.
  - Mintek as the truth lab.
  - A permissive open stack with no foreign-cloud dependency: it runs offline.
  - Post-quantum signatures, so records stay verifiable long term.
- **Water.** Through the advice (water chemistry as a cause), not through hardware.

## 12. Will it work on an image it has never seen?

- **What the accuracy report already is.** Every number is **out-of-fold**: each parcel was scored by a model that never saw it. A new parcel of the same ore type, passing the OOD gate, should perform like the report.
- **v9 tested this directly.** A new capture of the same ore gives the same error (×1.00). Partial view, noise and light changes are tolerated. Wavelength-calibration drift is the one real gap (×1.25, mostly silent), so a hardware calibration gate was added (training/hidsag-v9-robustness-20261002/RESULT.md).
- **A different ore** should be refused, and the existing evidence says the gate is **not yet reliable** for that (§9).
- **A phone photo** is ingested and quality-checked, but gets **no ore prediction**, because no phone-camera dataset exists to validate one.
