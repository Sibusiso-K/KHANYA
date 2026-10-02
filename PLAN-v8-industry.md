# Plan: REEFPRINT v8 — from a demo to a pilot a Bushveld concentrator could start

_Round 0 — initial draft by Claude (Opus 5.5), 2026-10-02. To be reviewed adversarially by Codex (gpt-6-astra, xhigh, read-only)._

Evidence base:
- `docs/17-industry-landscape-roles-and-money.md`: the research dossier. Every fact is tagged [P] primary-read, [V] vendor claim, [N] news, or [S] search summary (not citable).
- `training/economics-20261002/economics.py`: the money, computed with `reefprint.quantity` provenance.
- `docs/16-decision-value-chain.md`: the one belt lever measured so far (hardness → feed rate, sim_ +2.0% [+1.0, +3.0]).
- The constitution (`CLAUDE.md`) and `WORKBOARD.md` §0 apply.

## Goal

Turn REEFPRINT Live from a replay demo into a **credible pilot package** for a Bushveld PGM concentrator. Judges and a plant manager should be able to read it as "you could start this on Monday".

**What it is:** a fusion, prediction and decision layer.
- It reads the sensors that already run 24/7: belt hyperspectral (new), cross-belt elements, slurry analysers, froth and size cameras.
- It predicts what the truth labs (fire assay, QEMSCAN, XRD) will report, with calibrated intervals.
- It proposes a specific, sourced action, routes uncertain cases up a human escalation ladder, and keeps a tamper-evident record of every call and its later lab outcome.

**Why.** The truth arrives in 24–72 h (fire assay) or days (QEMSCAN at $1,500 per liberation sample), while the plant runs three shifts a day.

**The money at stake** (formulas with labelled inputs, all ASSUMED-grade until a pilot measures them):

| Lever | Scale | Value per year |
|---|---|---|
| +1 pp concentrator recovery | Zondereinde-size plant | ≈ R111 M |
| +1 pp concentrator recovery | Implats group scale | ≈ R1.1 bn |
| The ≥3 pp chrome-constraint recovery gap Mintek reported | Zondereinde scale | ≈ R334 M |
| sim_ +2.0% throughput, only where the mill is the bottleneck | Mogalakwena scale | ≈ R612 M |

## Approach

### A. Reframe (docs and app copy)
1. **Retire "camera replaces the mineralogist".**
   - The microscope (KHANYA) becomes one cheap shift-lab input.
   - The product is the clock: prediction between lab results, plus decisions.
   - Update the app header, the Where view and README. Keep both names (ADR-0003).

### B. Mineral phases from the belt sensor, by physics (deliverable: ≥3 phases), pre-registered
2. **Feature mapping, not a trained classifier.** Kaggle run `reefprint-hidsag-v8-features` computes continuum-removed absorption features per pixel and per sample on HIDSAG GEOMET and MINERAL1 (all crops). The established method is the Tetracorder-style spectral feature mapping of Clark et al. 2003 and the CSIRO TSG/HyLogger scalars. The features:

   | Feature | Mineral group |
   |---|---|
   | Al-OH depth and position (2160–2230 nm) | white mica / sericite, kaolinite |
   | Kaolinite doublet (2165 / 2205 nm) | kaolinite |
   | Fe-OH 2250 nm | chlorite, biotite, epidote |
   | Mg-OH / CO₃ 2300–2350 nm | chlorite, biotite, actinolite, carbonate |
   | 1750 + 1940 nm | gypsum |
   | Fe³⁺ ~900 nm | Fe oxides |

3. **Validate against MINERAL1 QEMSCAN** (99 fractions, 36 composites). Mean wt%: muscovite/sericite 17.2, biotite 9.0, chlorite 7.4, anhydrite/gypsum 4.8, kaolinite 0.9, Fe oxides 0.75.
   - **Pre-registered hypotheses** (written and committed before the run):
     - H1: Al-OH depth ↑ with muscovite/sericite (+ kaolinite).
     - H2: Fe-OH 2250 + Mg-OH 2330 depth ↑ with chlorite + biotite.
     - H3: 1750 nm depth ↑ with anhydrite/gypsum.
     - H4: Fe³⁺ 900 nm depth ↑ with Fe oxides.
   - **Test:** size-fraction-stratified Spearman ρ, pooled within strata, with a cluster bootstrap over composites (36 units).
   - **Gate:** the 95% CI excludes 0 with the predicted sign, **and** the feature adds over the size-fraction + line metadata lookup in partial rank correlation. This is the lesson of the MINERAL1 withdrawal.
   - **Reporting:** each phase is reported pass, fail or inconclusive. "≥3 phases" is claimed only if ≥3 hypotheses pass.
4. **Per-pixel mineral maps** for the pre-registered showcase cubes. They replace the generic "clusters" layer as the default analysis layer. Each map is labelled with its feature and its validation status.

### C. Decisions a person can trust (HITL)
5. **Advice engine** (`advice.js` plus a JSON rule table). The rows come from docs/17 §6, each with its source:

   | Signal | Advice |
   |---|---|
   | Locked valuables | regrind |
   | Liberated but fine | kinetics or reagent |
   | Chromite fines entrained | water and froth depth (not depressant) |
   | Talc rising | depressant within a band |
   | Pyrrhotite/pentlandite shift | depressant/collector balance |
   | Harder ore | feed rate |

   Models only select the row and the state (with intervals). Thresholds come from training folds and are illustrative. The LLM never computes; it routes (unchanged).
6. **Escalation ladder with time budgets.**

   | Level | Who | Budget |
   |---|---|---|
   | L0 | auto-advice shown | — |
   | L1 | operator acknowledges | 5 min |
   | L2 | shift metallurgist decides | 30 min, when the interval crosses a threshold or OOD is borderline |
   | L3 | mineralogist or lab rush sample | within the shift, when OOD-refused or the classes conflict |
   | L4 | standard method (SOP card) as the conservative default | if a budget expires with no response |

   Every level emits the rule-5 conservative default with a reason; "hold last setpoint" is never offered.
7. **Decision ledger.** An append-only JSONL. Each record holds:
   - sha256(prev_hash + canonical JSON of the record), so it is tamper-evident;
   - role and a pseudonymous user id (POPIA: no names);
   - prediction, interval and policy row;
   - the advice and the human action (accept / modify / reject / escalate) with a free-text note;
   - later, the lab truth.

   Verify-chain button. Export. No blockchain: a hash chain gives the tamper evidence without the infrastructure.
8. **Scorecard (gamified, carefully).**
   - **What is scored:** when the lab truth returns, each call is scored by a proper scoring rule (interval hit and the log/Brier score of the stated confidence) and by **appropriate escalation**. Escalating when uncertain scores well; overriding a confident correct call scores badly.
   - **What is never scored:** volume or speed alone.
   - **Display:** team streaks and calibration badges. There is no individual leaderboard by default, because of South African labour relations and to avoid gaming.
   - **Precedent:** Plotlogic's Covalent case study used OreSense as "an objective benchmark for ore spotter performance" (SD 11.6 → 4.3) [V].
9. **Mass-balance helper.**
   - Two-product formula (yield, recovery from feed/concentrate/tails assays).
   - Weighted least-squares reconciliation of redundant assays (Lagrange multipliers, standard method), with the adjustments shown.
   - Input is the typed lab import already in the app. The demo input is a **stipulated example**, labelled.

### D. 3D and mapping (real data where it exists, labelled schematic where not)
10. **3D with three.js** (MIT, vendored locally, offline):
    - the hyperspectral cube with orbit controls and real faces (replacing the CSS 3D);
    - a **3D flowsheet** (ROM → crushers → belt + scanner → mill ↔ cyclones → rougher/cleaner flotation → concentrate / tails → spirals for chrome). Live replay tags and decision markers sit on the equipment. Labelled schematic.
11. **Map with MapLibre GL JS** (BSD-3, vendored, offline, no tile server):
    - South Africa and Bushveld context from Natural Earth (public domain);
    - a PGM operations point layer from **USGS MRDS** (public domain) or, failing that, town locations from Natural Earth, labelled "approximate";
    - a QGIS-like layer panel (toggle, legend, attribute table), a proposed pilot-site marker, and a downhole section view (Bachmann data have depths but no coordinates, so it is not placed on the map).

### E. Make it installable: equipment, edge cases, pilot
12. **Installation spec (docs/18) — where it sits, by name.**
    - Mill-feed conveyor after secondary crushing (ore < ~30 mm), before the mill. Optional ROM-stockpile reclaim belt.
    - **VNIR** line scan (Specim FX10-class, 400–1000 nm) **plus SWIR** 1000–2500 nm (Specim SWIR / SX25 or HySpex class). FX17 alone misses 2.2–2.35 µm.
    - Belt-speed encoder (the FX17 datasheet shows shaft-encoder triggering), broadband halogen line lights, an automated white-reference shutter, a burden-height laser/lidar.
    - Edge PC in an IP66 enclosure with vortex or AC cooling (camera rated +5 to +40 °C, **non-condensing**, IP52 [P]), purge air and an air knife for dust, an anti-condensation heater, anti-vibration mounts, UPS.
    - Network: OPC UA **read-only first** to the historian, then a write path to MillStar/FloatStar setpoints only after approval.
    - **No radioactive source** (vs PGNAA Cf-252, which needs National Nuclear Regulator authorisation [S]).
13. **Edge cases**, each with a detection rule in software and a response:
    - wet ore (1400/1900 nm water bands mask features; water-band gate refuses);
    - fines coating rocks;
    - empty or overloaded belt (burden height);
    - lamp ageing and white-reference drift;
    - dust on the window;
    - shadows;
    - belt-speed change;
    - flooding (Valterra Amandelbult, Feb 2025 [P]);
    - power dips;
    - stockpile blending lag;
    - ore-constrained vs mill-constrained plants (throughput value only where the mill is the bottleneck).
14. **Pilot plan, three phases.**
    - **Shadow** (3 months): predictions logged, no actions; QEMSCAN 2×/week composites; fire-assay shift composites as truth.
    - **Advisory** (3 months): operator and metallurgist act via the ledger.
    - **Coupled**: OPC UA to the APC after sign-off.
    - **Statistics:** pre-registered KPIs (recovery, Cr₂O₃ in concentrate, kWh/t, reagent g/t). On/off block design in the style of the FloatStar Vale study (≈400 days) [P]; doctrine gates.
    - **Budget:** camera classes [S] plus quotes needed. Break-even is expressed as **the recovery improvement that pays the capex** (computed, e.g. a fraction of a pp at Zondereinde scale).
15. **Who uses it.** A role-to-screen table for operator, metallurgist, mineralogist, geologist, chemist/lab, manager and smelter, matched to the app's views.

### F. Orchestration and where models run
16. **Where each model runs.**
    - **Edge PC at the belt:** calibration, feature extraction, the per-sample classical models (ridge / PLS / ET; small, deterministic, cheap) and OOD.
    - **Control-room server:** fusion of belt, analysers, froth and size; conformal intervals; the policy and escalation; the ledger.
    - **Lab:** a retraining pipeline triggered by each returning QEMSCAN or assay batch, with drift monitoring.
    - **Optional LLM router** (AIML / Featherless, small open model): routing only, never data.
    - A diagram in the Where view.

### G. Deliverables ledger
17. Map every brief deliverable to the evidence path in `docs/09-brief-compliance.md`:

    | Brief deliverable | Evidence |
    |---|---|
    | ≥3 mineral phases | B; plus KHANYA microscope phases |
    | Accuracy report | B + docs/16 + v6/v7 |
    | Plant-parameter demo | C + docs/16 |
    | Real-time | edge pipeline timing |
    | Integration with sorting/flotation controls | OPC UA tag map to FloatStar/MillStar; LIMS export |

### H. Proof
18. Browser end-to-end check of every view and theme, plus a ledger chain-verify test, advice-rule unit tests and mass-balance unit tests (known textbook identities). Commit, push, BUILDLOG, CONTEXT, tell Sbu.

## Key decisions and tradeoffs (contestable)

- **D1 — Physics feature mapping over a trained mineral classifier.** It cannot learn the size-fraction shortcut that sank MINERAL1, it needs no labels, and it is the published practice. Cost: lower ceiling than a good supervised model, and features overlap (chlorite and biotite share 2250/2330).
- **D2 — Validation design.** Stratify by size fraction, cluster bootstrap over composites (n = 36), and require added value over metadata. This is weak power at n = 36; we accept "inconclusive" as an outcome.
- **D3 — Money as formulas with provenance, not a headline.** Every rand is ASSUMED-grade, because the tonnage and grade inputs are [S]/[N]. We show ranges and the break-even, and say "until a pilot measures it".
- **D4 — Throughput value only for mill-constrained plants.** Underground PGM concentrators are usually ore-constrained, so the honest lever there is energy and grind stability.
- **D5 — Hash-chained JSONL, not blockchain.** Tamper-evident, offline, auditable, cheap.
- **D6 — The gamification scores calibration and appropriate escalation, never volume or speed;** no individual leaderboard by default.
- **D7 — three.js and MapLibre vendored offline** rather than CesiumJS/deck.gl. Smaller, permissive (MIT / BSD-3), and the demo must run with no network.
- **D8 — Optical (VNIR+SWIR) rather than PGNAA for the new sensor.** No radioactive source; mineral (not just element) information. Cost: surface-only and blind to opaque phases. So we **fuse** elements from existing analysers rather than replace them.
- **D9 — Integrate with Blue Cube, Courier, froth cameras and Mintek APC, not compete.** REEFPRINT is the layer above.
- **D10 — The LLM stays a router.** No LLM computes a mineralogical or control value (rule 6).

## Risks and open questions

- Kaggle download or feature definition errors, and the risk of multiple-testing inflation across hypotheses H1–H4 (use Holm across the 4).
- MRDS may not hold usable PGM operation points; then we fall back to Natural Earth towns, labelled approximate.
- App size and performance with three.js + MapLibre + full-resolution cubes (budget ≤ 50 MB total, ≤ 3 s first paint locally).
- Overclaiming money: every [S] input must stay labelled; Codex should attack any line that reads as a promise.
- Labour and privacy: the ledger and scorecard must not become a surveillance tool (POPIA, unions).
- Time: the Top-5 re-presentation date is unknown, so the build must stay shippable after each step.

## Out of scope

- Buying or building hardware (ADR-0002).
- Any claim of measured savings.
- Training on the LumenStone test set.
- Changing KHANYA's live worktree or servers.
- Real OPC UA writes.
- Closed-loop control.
- A cloud deployment.
