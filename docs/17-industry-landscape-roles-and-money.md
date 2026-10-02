# 17 — What mines actually use, who decides what, and where the money is lost

*Research dossier, 2026-10-02. It is the evidence base for the refined build (PLAN-v8). Every factual line carries a tag:*

| Tag | Meaning |
|---|---|
| **[P]** | primary document read: text extracted from the source itself |
| **[V]** | vendor's own published claim, read from the vendor's document. Real, but not independent |
| **[N]** | secondary news or summary of a primary report |
| **[S]** | search-engine summary only. **Indicative, not citable** until the source is read (constitution: "Read before citing") |

*Money arithmetic is not done in this file. It is done by code in `training/economics-20261002/economics.py`, which carries the same tags into its output.*

---

## 1. The correction that reframes the product

**Reflected-light ore microscopy is not how a plant gets its mineralogy today.**
- Quantitative process mineralogy moved to SEM-based automated mineralogy (QEMSCAN, MLA, TIMA, Mineralogic) and to XRD. Optical microscopy "was being left aside in favour of SEM" **[S]** (Minerals 10(11):1004, 2020; Minerals Engineering 2011 review).
- Automated *optical* mineralogy is still argued to be a cost-effective alternative **[S]** (Minerals Engineering 2022 review). It is not the plant standard.

**What this means for us.** A mineralogist with a microscope can already name the phases. Doing that with a camera is not the product.

**The real gap is the clock.**
- The truth (QEMSCAN, fire assay, XRD) arrives in **days or the next shift**.
- The plant runs **24/7, three shifts a day**.
- So the shift decides blind.

The product is the layer that **predicts, every few seconds, what the lab will say**, from sensors that run continuously, and turns it into a decision a person approves. The truth labs keep teaching it. The KHANYA microscope stays as one cheap shift-lab input, not the centre.

---

## 2. Who decides what, with which tool, how often, and what a wrong call costs

| Role | Decisions they own | Tools they use today (by name) | Cadence | How a wrong or late call loses money |
|---|---|---|---|---|
| **Geologist / grade controller, ore spotter** | Ore vs waste per block or bucket; which reef or stockpile; dilution control | Blast-hole or face sampling, assays, core logging; HyLogger / Corescan core scanners; shovel XRF (MineSense ShovelSense **[V]**); face or belt hyperspectral (Plotlogic OreSense **[V]**) | per load, per shift | Ore to the waste dump, waste to the mill. Copper Mountain recovered ~342,000 t of ore from waste in under 6 months on two shovels and a loader **[V]** (MineSense case study). Ore-spotter variance fell from SD 11.6 to 4.3 with OreSense outputs **[V]** (Plotlogic Covalent case study) |
| **Mineralogist** | Which minerals carry the metal, whether they are liberated or locked, and why tails are lost | QEMSCAN / MLA / TIMA (automated SEM-EDS), XRD, optical microscopy for qualitative checks | composites, weekly to monthly | Late answers. A liberation analysis costs **$1,500 per sample** (+$150 block mount, +$800 crush/grind/sieve; Saskatchewan Research Council price list, 4/2017, Canadian lab) **[P]** |
| **Chemist / assay lab** | Grades of feed, concentrate and tails; metal accounting | Fire assay (PGM 4E), ICP, XRF fusion; shift composites from cross-stream cutters | 8–12 h composites; results next shift or later | Fire-assay turnaround "as short as 8 hours, but in practice … up to 24–72 hours" **[S]**. "Head, concentrate and tailings grades have frequently been unavailable until the following shift or even the following day" **[S]** |
| **Plant metallurgist** | Grind target, collector / depressant / activator doses, mass pull, circuit changes; reconciles the mass balance | Lab assays, mass-balance software (two-product formula, least-squares reconciliation), on-stream analysers, froth cameras, APC | per shift, daily | Recovery points lost. Valterra reported concentrator recoveries **+1 pp at Mototolo and +2 pp at Amandelbult** in 2025: the size of moves that get reported to investors **[P]** |
| **Control-room operator** | Mill feed rate, water, densities, cell levels, air; reacting to upsets | DCS / SCADA; APC such as Mintek **MillStar** and **FloatStar** (now marketed by Molycop) | seconds to minutes | Throughput and stability. FloatStar at Vale Cauê: recovery "up to 2.7%", over 400 days on/off **[P]** (Knights et al., SAIMM 2012). MillStar "throughput increased by 6–10%" **[S]** (Molycop page) |
| **Smelter / concentrate buyer** | Accept, penalise or blend concentrate on Cr₂O₃, MgO, Cu+Ni, S | Concentrate assays, blending plans | per delivery | Furnace build-ups and penalties. At Lonmin, blending "is managed with two factors only: Cr₂O₃ and Cu+Ni. Both … have a maximum specification" **[P]** (Eksteen et al., SAIMM 2011) |

---

## 3. The instruments in plants today, what each cannot tell you, and where we fit

| Principle | Products (by name) | Where it sits | What it measures | What it cannot give the shift | Edge cases |
|---|---|---|---|---|---|
| **PGNAA / PFTNA cross-belt** | Thermo Scientific CB Omni Agile; Scantech GEOSCAN; RTI AllScan | Conveyor, through the full burden | Bulk elements, minute by minute | Minerals, liberation, PGM at g/t | Isotope-source versions use **Cf-252** (licensing with South Africa's National Nuclear Regulator **[S]**; Cf-252 at $60/µg from US DOE **[S]**). Neutron-generator versions also exist (e.g. RTI AllScan) **[S]**. Analyser prices quoted from US$50k–200k up to >$500k installed **[S, market report: low confidence]** |
| **LIBS on belt** | SECOPTA MineralLIBS; Laser Distance Spectrometry | Conveyor surface | Elements, seconds | Surface only; minerals | Dust on optics, laser safety **[S]** |
| **On-stream XRF (slurry)** | Courier-type analysers | Flotation feed, concentrate, tails pipes | Cu, Ni, Fe, Cr and similar | **PGM at a few g/t is a trace-level problem for XRF**; reported precious-metal OSA precisions are 35–70 ppb in purpose-built designs **[S]** | Sample lines block; matrix effects **[S]** |
| **Diffuse-reflectance slurry spectroscopy** | **Blue Cube MQi** (Stellenbosch; now Draslovka) | In the process pipe | PGM g/t and Cr₂O₃ % at Northam's flash flotation; updates every 15 s; R² 0.84 (PGM), 0.92 (Cr₂O₃) **[S]**; >100 analysers installed **[S]** | The mineralogical cause (liberation, association) | **The closest South African prior art to an optical approach. Integrate with it, never pitch against it** |
| **Froth cameras** | Metso VisioFroth; Outotec FrothSense; Blue Cube TempoTrack | Above flotation cells | Bubble size, froth speed, colour, stability | The ore-side cause | Lighting, splash |
| **Particle-size cameras** | Split-Online; Metso VisioRock; WipWare | Conveyors, crusher discharge | Rock size distribution | Mineralogy | Dust, fines hidden under coarse |
| **Hyperspectral (VNIR/SWIR)** | Plotlogic OreSense (face, stockpile, belt) **[V]**; Specim FX17 / SWIR / SX25 cameras | Belt, face, core | Mineral classes with vibrational features (micas, clays, talc, chlorite, carbonates, Fe-oxides) | Opaque phases, chromite matrix (see CLAUDE.md physics) | **FX17: 900–1700 nm, IP52, +5 to +40 °C non-condensing, shaft-encoder trigger [P datasheet]**. It misses the 2.2–2.35 µm Al-OH / Mg-OH features, so a 1000–2500 nm camera is needed (USD 50k–300k **[S]**) |
| **Shovel XRF** | MineSense ShovelSense **[V]** | Shovel bucket | Grade per bucket | Mineralogy, plant response | Vibration, impact |
| **Sensor-based ore sorting** | TOMRA (XRT, optical, NIR) | Before the mill | Accept or reject per particle | Plant-wide decisions | Particle size window |
| **Automated mineralogy (the truth)** | QEMSCAN, MLA, TIMA, Mineralogic | Lab | Phases, liberation, association | Shift speed | $500–1,500 per sample **[P SRC]**; market about US$59 M (2024) **[S, market report]** |
| **APC (the actuator)** | Mintek MillStar, FloatStar, StarCS | DCS | Stabilises levels, flows and mill load. FloatStar's published work also uses **feed chemistry** to suggest mass-pull setpoints within operator limits **[P]** (Knights et al. 2012) | An uncertainty-aware **mineralogical** input with a refusal path | **Our output would be one more input, inside its limits** |

**Where REEFPRINT fits, said narrowly** (corrected after ClauDex round 1). Each tool measures one thing in one place. APC already uses process and, in FloatStar's case, feed-chemistry inputs. Its mineralogical truth (QEMSCAN, fire assay) arrives days late. The claim is **incremental, uncertainty-aware ore information** over existing analyser and APC workflows. It is not an empty niche, and the increment has to be demonstrated against those workflows in a pilot.

REEFPRINT is the **fusion, prediction and decision layer**:
- It takes the signals that already run 24/7: belt hyperspectral, cross-belt elements, slurry analysers, froth and size cameras.
- It predicts the next truth-lab answer with a calibrated interval.
- It proposes a specific action with a reason, routes uncertain cases to a person, and learns from every QEMSCAN and assay that comes back.

We found no published system that joins these. **We did not search exhaustively**, and Blue Cube, Plotlogic and the APC vendors are the closest.

---

## 4. The physics that decides the money in a Bushveld concentrator

**The ore.**
- UG2 ore is about **30% Cr₂O₃**, against about 0.1% for Merensky **[P]** (R.T. Jones, Mintek, *An overview of Southern African PGM smelting*, 2005).
- UG2 PGM grade is 4.4–10.6 g/t; Merensky is about 4–10 g/t **[P]** (ibid.).
- UG2 PGM grains are mostly **< 10 µm** **[P]** (Molefe & Baloyi, SAIMM 8th PGM Conference 2022). PGMs associate with base-metal sulphides and silicates more than with chromite **[S]**.

**Grind (liberation) and its limits.**
- UG2 is commonly ground to 70–80% passing 75 µm **[S]**.
- Conventional flotation works best at about 20–150 µm. Fines lose bubble collisions; coarse particles detach **[S]**.
- Spiral gravity concentrators work best at **75 µm–3 mm**, and chromite below 53 µm tends to report to the tails **[P]** (Molefe & Baloyi 2022, citing Falconer 2003).

**Density and inertia: why chromite is over-ground.** Hydrocyclones classify by settling velocity, which grows with density × size² (Stokes). Chromite (SG about 4.5) settles like a coarser silicate (SG about 3), so it returns to the mill more often and is ground finer than it needs to be. Fine chromite is then *entrained* into the flotation concentrate with the water, and that is exactly the smelter's Cr₂O₃ problem. The equal-settling ratio is computed in `economics.py` from Stokes' law, as a **qualitative illustration only**. Industrial cyclone partition also depends on pressure, solids concentration, viscosity, geometry, bypass and roping. How much chromite is over-ground at a plant needs **measured mineral-specific partition curves**. The SG values are textbook and are flagged.

**Grindability.**
- Sources conflict on chromite against silicate work index in UG2: 12.3 vs 13.9 kWh/t (AG pilot), or 15 vs 32 kWh/t (another study) **[S, unresolved]**.
- What is agreed: the chromite : silicate ratio changes mill energy. That ratio is what a belt sensor can see (chromite is dark and featureless; silicates carry Mg-OH and Fe features).

**The smelter constraint.**
- Cr₂O₃ solubility in slag is about 1.8% **[P]** (Eksteen et al. 2011).
- Impala's permitted furnace-feed Cr₂O₃ rose from about 0.8% to about 1.8%, and its UG2 concentrate ran at about 1.6–1.7% **[P]** (Jones 2005).

**The trade-off that costs PGM recovery.** Mintek testwork made UG2 concentrate at about 430 g/t and **87% recovery at 2.9% Cr₂O₃**. "Even higher grades (more than 1000 g/t) could be achieved at even higher recoveries (more than 90 per cent), if the constraint on the Cr₂O₃ content was relaxed (to between 4 and 10 per cent)" **[P]** (Jones 2005).

So **the chrome limit costs recovery**. Every unit of chromite kept out of the concentrate *by knowing where it comes from* (overground fines, entrainment at high water recovery) buys back PGM recovery.

**Floatable gangue.** Talc (naturally floatable gangue) is depressed with CMC or guar. At 300 g/t almost all of it is removed from a Merensky concentrate **[S]**. Over-dosing depresses valuable minerals too **[S]**. The belt's SWIR Mg-OH feature is the early warning for talc.

**By-product.** Chrome from UG2 tails is a revenue stream. Valterra reported chrome yields up 0.3–0.5 pp in 2025 **[P]**.

---

## 5. Production scale, and what the levers are worth

These are inputs to `economics.py` (revised after ClauDex round 1: net payable value, contribution only where the mill is the bottleneck, break-even, no gross headlines); the outputs are there, not here.

| Operation | Fact | Tag |
|---|---|---|
| Northam Zondereinde | 2,247,881 t milled, F2025; 4.72 g/t 4E mill head | [S] (annual report via search) |
| Northam group | F2026 4E basket **USD 2,338/oz** (F2025: 1,372); Zondereinde revenue per refined 4E oz **R47,156**; group cash cost **R27,376/4E oz** | [N] (Investing.com summary of Northam's results slides) |
| Valterra Platinum | 2025 average realised basket **R32,611 per PGM oz** (USD 1,852); year-end USD 2,562; total production 3,200,600 oz; own-mined 2,060,300 oz (down, after flooding at Amandelbult) | [P] |
| Valterra Mogalakwena | record 14.7 Mt milled; throughput-led, blending lower-grade stockpiles (a mill-constrained open pit) | [S] / [P] that tonnes rose |
| Implats | 26.29 Mt milled FY2025, managed [S]. "PGMs in Merensky ore are recovered at around 89%, while that in UG2 is recovered at around 79%"; ore is allocated to the UG2 plant "for higher chromium grade material" | recovery and routing: [P] (Impala fact sheet, Dec 2018) |
| Comminution | "Comminution consumes 1–4% of all electrical power generated in the world (7–10% in Australia)"; "About 50% of minesite energy consumption is in comminution" | [P] (Napier-Munn, JKMRC/CEEC presentation) |
| Eskom | direct-customer tariffs +12.74% from 1 April 2025 | [S] |

**Edge case on throughput value.** Many underground PGM concentrators are **ore-supply-constrained**, so mill throughput gains only pay where the mill is the bottleneck: open pits with stockpiles (Mogalakwena), tailings retreatment, or toll ore. Where ore is the constraint, hardness knowledge pays through **energy per tonne and a stable grind**, which protects recovery, not through extra tonnes.

---

## 6. Physical vs chemical routes, by liberation and size: diagnostic prompts, not rules

*Revised after ClauDex round 1 (findings 2–5). These are **prompts for the metallurgist**, conditional on site deportment, size-by-size recovery and reagent-response evidence. They are not automatic rules.*

Each row names the **validated measurement it needs**. In the app, a row with no validated input is **shown disabled**, with that requirement as its reason.

| Observation (the prerequisite measurement) | What to examine | Why, and the caveat |
|---|---|---|
| Valuable minerals **locked** (needs liberation by QEMSCAN/MLA, or validated KHANYA liberation on *this* stream) | Whether a finer grind or regrind would release them; existing regrind capacity; overgrinding risk | Partial surface exposure can still float, so "locked → regrind" is not automatic |
| Liberated but **fine** valuable minerals (needs size-by-size liberation and recovery) | Fine-particle kinetics, residence time, reagent and frother response | Collision probability falls with size **[S]**. PGM *grain* size is not the flotation *particle* size |
| **Chromite entrained** into the concentrate (needs Cr₂O₃ in the concentrate and water recovery: an assay or an analyser such as Blue Cube MQi) | **Reduce entrainment through site-tested water-recovery, air and froth-depth adjustments, subject to PGM-recovery limits** | Entrainment is hydraulic, so a depressant does not stop it. Froth depth, air, frother and solids interact (a shallower froth often *raises* entrainment) |
| Recovering **chromite** as a by-product (needs a size-characterised stream) | Spirals only on a stream in their working range (about 75 µm–3 mm **[P]**), with a PGM-loss balance first | Spirals lose the ultrafine (< 53 µm) chromite **[P]**, so they do not fix fine entrainment |
| **Talc / naturally floatable gangue** rising (needs a validated talc or Mg-OH association; **not yet validated**) | Depressant dose within the site's tested band | Over-dosing depresses valuables **[S]** |
| **Pyrrhotite / pentlandite** balance shifting (needs phase evidence on this ore: microscope or QEMSCAN) | Depressant and collector balance; pH | Site deportment decides whether pyrrhotite carries PGM. "Pyrrhotite carries little PGM" is not universal |
| **Harder ore** (Bond WI; **validated on HIDSAG**, docs/16) | The feed-rate proposal inside the site's approved envelope | The only row with a validated input in this build |

---

## 6b. Bushveld-specific leads found during review (not yet read)

- **Hyperspectral on Bushveld PGE ore exists in the literature.** A 2025 *Minerals Engineering* study (S0892687525005102) combined VNIR (380–1000 nm), SWIR (1000–2500 nm) and LWIR (7.7–12.3 µm) hyperspectral imaging with portable XRF on Merensky Reef drill core. It was validated against reference methods for "real-time, high-throughput ore characterisation" **[S]**. This is the nearest published support for transferring the belt layer from Chilean Cu-Mo to Bushveld ore, and it should be read before the pitch.
- **Mintek already operates the truth lab.** It runs SEM, EPMA, XRD, XRF, micro-XRF, 3D tomography, LA-ICP-MS, FTIR, MLA and QEMSCAN (Mining Weekly, 26 June 2026) **[S]**. In the pilot, Mintek is therefore the natural source of the QEMSCAN/MLA composites that retrain the model, and the business fit is a **service partnership**, not a competitor.
- **Map data is available.** USGS MRDS (public domain) returns 178 PGE-coded sites with coordinates in the Bushveld bounding box (26–31°E, 23–26.5°S), including "Northam Platinum" (plant), "Rustenburg Mine", "Impala Platinum", "Amandelbult Mine", "Union Mine", "Western Platinum Mine" and "Kroondal Chrome Mine" **[P]** (WFS query, 2026-10-02). Its locations are historical database points, not survey-grade.

## 7. What we will not claim

- We have **no Bushveld belt hyperspectral data**. The belt evidence is Chilean Cu-Mo (HIDSAG).
- We have no plant trial. Every rand figure in `economics.py` is a **formula with labelled inputs**, not a measured saving.
- Every **[S]** line above is a lead, not a citation, until someone reads the source.
