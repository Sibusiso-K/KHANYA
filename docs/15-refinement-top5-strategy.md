# 15 — Refinement for the Top-5 round: one problem, one system, three speeds

*Written 2026-10-01 evening, after the v6 pitch. The judges asked us to refine. This is the plan and the reasoning behind it.*

**How to read the sources.** Anything marked **[indicative]** came from a web-search summary, not from a primary document we have read. The rule from `CLAUDE.md` applies: it is not citable on a slide until someone reads the source. Results marked **[measured]** were produced by our own code, and the file is named alongside.

---

## 0. The verdict: keep the belt, but as layer 1 of the same system, not a pivot

The problem we pitched has three parts:

- Lab characterisation takes days.
- Ore changes by the hour.
- So the shift decides blind, and the plant loses recovery and overspends on reagents.

No single sensor closes that gap. Each instrument answers a different question at a different speed:

| Layer | Where | Speed | Question it answers | Status |
|---|---|---|---|---|
| **1. Belt hyperspectral** | mill-feed belt (also ROM / crusher discharge) | seconds | "Has the ore just changed? Harder, more floatable gangue, lower expected recovery?" | **[measured]** on public data: HIDSAG v3/v4, v5 running |
| **2. REEFPRINT microscope** | shift lab: feed, concentrate **and tails** | within the shift | "Why? Are the valuable sulphides liberated or locked, and where are we losing them?" | live app, LumenStone |
| **3. QEMSCAN + lab assays** | central lab, composites | days | "What is the truth?" It labels training data for layers 1 and 2. | the teacher, not a competitor |
| **Control room** | one screen | — | Act · verify · conservative default, with a reason. Only a setpoint a person approves goes to the plant. | design |

The belt is what turns "faster lab" into **before grinding**, and before grinding is where the money is. The microscope stays essential, because a belt camera sees millimetre pixels of host rock while PGM and base-metal sulphide grains are microns across and opaque.

### Gaps we created ourselves, and must say before a judge does

1. **The belt evidence is on Chilean porphyry Cu-Mo, not Bushveld PGM ore.** It transfers as a *method*, not as numbers.
2. **There are no drill-hole IDs in HIDSAG GEOMET.** The split is by sample, so scores may be optimistic. MINERAL1 is properly grouped by composite.
3. **The microscope needs a polished section.** That takes minutes to an hour, not seconds, which is why it is layer 2 and not layer 1.
4. **Magnetite and tennantite are weak** in the microscope model (`CLAUDE.md`); the quarantined candidate (42646cfa) stays quarantined.
5. **Every rand of value is still an assumption** until a pilot measures it.

---

## 1. What is already out there, and the gap we fill

| Category | Examples | What it measures | Speed | What it does not give the shift |
|---|---|---|---|---|
| Cross-belt elemental analysers (PGNAA / PFTNA) | Scantech GEOSCAN; Thermo Fisher CB Omni Agile | Bulk **elements** through the full belt depth | minute by minute | Minerals, liberation, a reason for a recovery change |
| Belt / face hyperspectral + lidar | Plotlogic OreSense (deployed since 2019, mounted over conveyors) [indicative] | Material classes on the belt or face | real time | Public material emphasises ore/waste and grade control; we found no description of a link to flotation kinetics or a microscope second opinion |
| Shovel-mounted XRF | MineSense ShovelSense (XRF, ~20 scans/s per bucket, truck diversion) [indicative] | Grade per bucket | seconds | Mineralogy, liberation |
| Sensor-based particle sorting | TOMRA (XRT, optical) | Particle density / colour, to accept or reject | milliseconds | Plant-wide decisions |
| Froth cameras | Metso VisioFroth, FrothSense+ (bubble size, froth speed, colour, stability) [indicative] | Flotation **symptoms** | seconds | The ore-side cause |
| Advanced process control | Mintek MillStar / FloatStar, now also listed by Molycop. Reported MillStar throughput +6–10% and FloatStar recovery up to 1% [indicative] | Stabilises levels, flows, mill load | seconds to minutes | A mineralogy input: it reacts to the process, not to the ore |
| Automated mineralogy | QEMSCAN, MLA, TIMA, Mineralogic | Minerals, liberation, association | days (queue) | Shift-speed answers |
| Core scanning | CSIRO HyLogger / Corescan; open NVCL data, >1.6 million m of core [indicative] | Core mineralogy | logging time | Plant feed in real time |

**Positioning, said narrowly.** Each tool measures one thing in one place. What we have not found described is the chain:

> belt spectra → QEMSCAN-taught mineralogy → microscope liberation → a kinetics-based recovery forecast (from the Mintek paper we used) → an advice with a refusal path → the existing APC.

Say "we found no published system that joins these", never "nobody does this". And **sell the join to Mintek's APC, not against it.** FloatStar and MillStar are the actuators; we would be a new input to them.

---

## 2. Roles: who decides what, and which signal they need

| Role | Decision | When | Signal | Money lever |
|---|---|---|---|---|
| Control-room operator | Mill feed rate, water, circuit stability | minutes | Belt flag: **harder ore** (Bond work index ↑) | Throughput, kWh per tonne |
| Shift metallurgist | Collector / depressant / lime dose; grind target; air and residence | hours | Belt **reagent and recovery forecast** + microscope **liberation** | Recovery, reagent cost |
| Concentrator manager | Blend and stockpile policy; campaigns | daily | Trends; tails losses by liberation class | Tonnes × recovery, smelter penalties |
| Geologist / grade control | Dig plan, routing to stockpiles | hours to a day | Belt or face hyperspectral by parcel | Dilution, blend consistency |
| Lab mineralogist | Which samples go to QEMSCAN | daily | REEFPRINT's **refusal queue** | QEMSCAN spend where it matters |
| Smelter / concentrate sales | Concentrate specification | per shipment | Forecast **Cr₂O₃ / MgO** in concentrate | Penalties: UG2 concentrators are penalised above ~1.5% Cr₂O₃ [indicative] |

**The Bushveld version of the story.** UG2 run-of-mine ore is roughly 50–80% chromite [indicative]. Talc, at around 1 wt%, is the main naturally floatable gangue and is depressed with CMC-type depressants [indicative]. So for UG2 the belt layer would forecast:

- the **chromite load**, which feeds the Cr₂O₃ penalty risk;
- the **talc and floatable gangue**, which sets the depressant dose;
- the **hardness**, which sets throughput.

The microscope then answers whether the base-metal sulphides and PGM carriers are liberated. All of this is untested on Bushveld ore, and the pilot is what tests it.

---

## 3. What should be built, and where it sits

1. **Mill-feed belt: VNIR + SWIR line scan + edge PC.** Primary early warning. A white-reference tile and dark frames handle calibration.
2. **ROM stockpile or crusher discharge: same camera, optional.** Earlier warning, so blending can react.
3. **Cyclone overflow / flotation feed: REEFPRINT microscope every shift.** Liberation and a grind or reagent decision.
4. **Tails (and concentrate): REEFPRINT microscope.** This is the strongest new use, because it answers "*what did we lose and why?*":
   - **locked** → grind finer;
   - **liberated but fine** → kinetics and reagent;
   - **chromite in concentrate** → entrainment and penalty.
   It maps one-to-one onto the liberation classes in the Mintek kinetics paper.
5. **QEMSCAN composites: monthly.** Retrains both models; takes the refused samples.
6. **Control room: one screen**, with OPC UA into the existing APC only after a person approves.

The Belt Monitor (`presentation/belt-monitor/`, "Where it sits" view) shows this layout.

---

## 4. Cheap images we can use for mineral phases, and what each is good for

| Source | Cost class | What computer vision can get | Good for |
|---|---|---|---|
| Reflected-light microscope + any camera on polished sections (ours) | low | Phases, grains, liberation | Feed, concentrate, tails |
| Same microscope on grain mounts of tails or concentrate | low | Losses by liberation class | "Why did we lose it?" |
| Ordinary RGB camera over a belt | very low | Particle size, lithology and colour classes — **not** minerals directly | Hardness and blend proxies |
| Mono camera + LED ring (6–8 narrow VNIR bands) | low | Coarse mineral discrimination | Cheap belt layer (tested below) |
| SWIR camera + filter wheel (8 diagnostic bands) | medium | Clays, micas, carbonates, talc, chlorite | Gangue and reagent demand (tested below) |
| Full VNIR + SWIR hyperspectral | high | All of the above, best accuracy | The reference belt sensor |
| SEM-BSE images | lab | Phases by grey level (mean atomic number) | Cheaper than full QEMSCAN |
| Drill-core photos + open HyLogger data | free data | Lithology, alteration | Geometallurgical domains |
| Froth camera images | vendor | Froth state | Flotation symptoms |
| Satellite multispectral / hyperspectral (Sentinel-2, EnMAP) | free data | Alteration at pit and tailings scale | Not for plant control |

**[measured] Cheap-sensor experiment:** `training/hidsag-v5-belt-20261001/sensor_bands.py`. It simulates each camera from the HIDSAG spectra and re-scores, so "how much accuracy does a cheaper camera keep?" is a number, not an opinion. Results are in §7.

---

## 5. What to predict, for whom, and why it pays

| Prediction | Who | From which layer | Why it pays (lever, not a promise) |
|---|---|---|---|
| Hardness (Bond WI) | Operator, manager | Belt | Set feed rate before hard ore reaches the mill: throughput, energy |
| Recovery forecast | Metallurgist | Belt + microscope + kinetics | Revenue = tonnes × grade × **recovery** × price |
| Reagent demand (lime, depressant) | Metallurgist | Belt | Dose ahead, not after the upset |
| Floatable gangue / talc | Metallurgist | Belt (SWIR Mg-OH feature) | Concentrate grade, depressant cost |
| Cr₂O₃ in concentrate (UG2) | Metallurgist, sales | Belt (chromite load) + microscope (entrainment) | Smelter penalty avoided |
| Tails losses by liberation class | Manager | Microscope on tails | Regrind or reagent change, aimed at the actual loss |
| Next lab test (Mintek paper) | Lab, metallurgist | Microscope + kinetics | Fewer, better lab tests |
| Which samples need QEMSCAN | Mineralogist | Refusal queue | QEMSCAN money spent only where uncertain |

The value per recovery point stays the one on the deck's value slide, which is an **assumption** until a pilot measures it.

---

## 6. Data we can use now, and the technique for each

| Data | Licence | Links | Technique |
|---|---|---|---|
| HIDSAG GEOMET / MINERAL1 / MINERAL2 / GEOCHEM | CC0 | hyperspectral ↔ lab tests ↔ QEMSCAN ↔ XRF | Continuum-removed band depths; bag-of-spectra clustering; PLS / ridge / extra-trees with nested CV; grouped folds; moving-belt simulation (v5) |
| LumenStone | written grant, cite | reflected light ↔ phase masks | Segmentation (live) |
| Mintek kinetics paper (Moodley, Govender et al.) | read, cited | QEMSCAN liberation ↔ flotation kinetics | First-order kinetics per liberation class (slide 16) |
| Kaggle "Quality Prediction in a Mining Process" (Brazilian iron-ore flotation, 20 s sensors, Mar–Sep 2017) [indicative] | **licence unverified** | process data ↔ concentrate silica | Soft sensor: forecast concentrate quality hours ahead of the assay. Use only after the licence is confirmed |
| USGS Spectral Library v7 | public domain [indicative] | pure mineral spectra (chromite, talc, pyroxene, plagioclase) | `sim_` linear unmixing test for UG2 belt feasibility. Its download page sits behind a browser check, so someone downloads it by hand; we do not automate around it |
| NVCL HyLogger | open access, licence to confirm | core spectra ↔ interpreted mineralogy | Geometallurgical domaining |

**Next technique to add:** conformal prediction intervals on the belt predictions, which REEFPRINT already uses for the microscope. They replace "typical error" with an interval that has stated coverage at honest n.

---

## 7. Results

### Training v5 (Kaggle `reefprint-hidsag-v5-belt`)

**[measured]** `training/hidsag-v5-belt-20261001/output/hidsag_v5_results.json` (Kaggle, 799 s). Out-of-fold, nested model choice. Three gates before "better": cluster/paired bootstrap CI of the MAE difference excludes zero, Mann-Whitney p < 0.05, Cliff's delta reported.

**GEOMET — lab tests from drill-core spectra (n = 146, sample folds, no hole IDs)**

| Lab result | v5 R² [95% CI] | v3-style PLS, same folds | v5 vs v3-style | Beats the average guess (3 gates) | Belt case* R² |
|---|---|---|---|---|---|
| Cu recovery | 0.42 [0.31, 0.51] | 0.26 | better (δ -0.13) | better | 0.32 |
| Mo recovery | 0.45 [0.33, 0.55] | 0.30 | no significant difference (δ -0.11) | better | 0.29 |
| Lime consumption | 0.32 [0.20, 0.44] | 0.16 | no significant difference (δ -0.11) | better | 0.13 |
| Flotation pH | 0.33 [0.17, 0.46] | 0.31 | no significant difference (δ -0.01) | no significant difference | 0.19 |
| Bond work index | 0.48 [0.30, 0.59] | 0.32 | no significant difference (δ -0.08) | better | 0.35 |

*Belt case = 100 pixels, +10% light, 2% noise together (`sim_`).

- v3 itself reported Cu recovery R² 0.374 with a best-of-two choice on the same out-of-fold score; v5's 0.42 removes that optimism and still comes out higher.
- pH no longer clears the stricter gates against the average guess, so the Belt Monitor stops showing it.

**Other records**

| Record | n | Targets | Beat average guess (3 gates) | Median R² v5 | Median R² v3-style | Note |
|---|---|---|---|---|---|---|
| MINERAL1 | 99 | 33 | 30 / 33 | 0.63 | 0.59 | grouped by composite (36); chalcopyrite R² 0.90 |
| MINERAL2 | 20 | 25 | 3 / 25 | -0.11 | -0.39 | only 20 samples, sample folds: too small to learn |
| GEOCHEM | 28 | 18 | 4 / 18 | 0.13 | -0.13 | only 28 samples; Ca (carbonate) R² 0.77 is the standout |

**Moving-belt simulation (`sim_`): median change in R² over targets with R² > 0.3**

| Record | 25 px | 100 px | 400 px | light −15% | light +15% | 2% noise | belt case | v3-style features, +15% light |
|---|---|---|---|---|---|---|---|---|
| GEOMET | -0.079 | -0.024 | -0.007 | -0.006 | -0.003 | -0.019 | -0.141 | -0.044 |
| MINERAL1 | -0.062 | -0.011 | -0.004 | -0.000 | -0.000 | -0.008 | -0.069 | -0.195 |
| GEOCHEM | -0.381 | -0.031 | -0.026 | -0.000 | -0.002 | -0.055 | -0.204 | -0.583 |

- **Lighting drift is solved by design.** The brightness-normalised features lose about nothing at ±15%, while the v3-style features lose 0.04–0.58 R².
- **Short dwell matters below ~100 pixels.** The combined belt case costs 0.07–0.20 R², which is why the design averages over a time window and calibrates on a white tile.
- **Blended ore is the open problem.** On MINERAL1, the model beat the average guess on blends for 19 of 33 minerals, but the median blend R² was -0.08. Next run: simulated blends inside the training folds.

### Cheap-sensor simulation

**[measured]** `training/hidsag-v5-belt-20261001/sensor_bands_results.json`. Mean spectra only (no pixel spread), so absolute R² is lower than v5; compare the cameras, not the runs.

| Camera | Skill kept · lab tests (GEOMET) | Skill kept · QEMSCAN minerals (MINERAL1) | R² Cu recovery | R² chalcopyrite |
|---|---|---|---|---|
| Ordinary RGB camera | 53% | 60% | 0.27 | 0.53 |
| Mono camera + 6-LED ring | 65% | 90% | 0.25 | 0.85 |
| SWIR camera + 8 filters | 71% | 86% | 0.25 | 0.84 |
| VNIR hyperspectral (silicon) | 109% | 98% | 0.26 | 0.89 |
| VNIR + SWIR hyperspectral | 100% | 100% | 0.35 | 0.89 |

**Reading.** On this ore, on the median target, a silicon VNIR hyperspectral camera (400–1000 nm) did about as well as the full VNIR + SWIR instrument. It varies by target: for Cu recovery the SWIR bands still added skill (0.35 vs 0.26). A 6-band LED camera kept 65–90% of the skill, and plain RGB about 53–60%.

Two cautions apply:

- Talc's main absorption (~2.31 µm) is SWIR-only, and talc is the depressant problem on UG2.
- For Bushveld ore the band set must be re-chosen: chromite and pyroxene have VNIR crystal-field features. The UG2 pilot decides.

---

## 8. What to show in the Top-5 round

1. **The same deck story, tightened to one sentence:**
   > Read the ore before it is milled (belt), explain it within the shift (microscope), teach both with QEMSCAN — one screen, one decision, with a refusal path.
2. **A roles slide** (§2): one question per role, and the signal that answers it.
3. **The belt evidence**, with v5 robustness and the cheap-sensor curve, plus the scope caveats said first.
4. **The tails use case** as the new "where else": what did we lose, and why.
5. **The ask, made sharper:** a UG2 pilot with Mintek. One belt camera (or a lab bench scanner on composites first), QEMSCAN-labelled composites, and microscope sections from the same feed, so that for the first time all three layers are measured on the same Bushveld samples.

## Sources (web; marked [indicative] above until read in full)

- Plotlogic OreSense — https://plotlogic.com/products/oresense/ ; TechCrunch 2022 — https://techcrunch.com/2022/03/21/plotlogic-scoops-up-18m-to-put-hyperspectral-imaging-to-work-in-the-mines/
- Thermo Fisher CB Omni Agile — https://www.thermofisher.com/us/en/home/industrial/cement-coal-minerals/online-analyzers/solutions/cb-omni-agile.html ; Scantech GEOSCAN-M — https://im-mining.com/2020/08/24/scantechs-geoscan-m-heart-bulk-ore-sorting-mining/
- MineSense ShovelSense — https://minesense.com/wp-content/uploads/2022/08/Automated-Smart-Truck-Diversions_White-Paper-Aug-2022.pdf
- Metso FrothSense+ — https://www.metso.com/globalassets/portfolio/leaflet-frtohsense-en-19.10.pdf
- Mintek MillStar / FloatStar — https://mintek.co.za/clusters/miningmaterialsautomation/measurement-and-control/mac-casestudies/a-complementary-milling-and-flotation-advanced-process-control-system-at-a-platinum-concentrator.pdf.pdf ; https://www.molycop.com/services/process-optimisation/advanced-control/floatstar
- UG2 chromite, Cr₂O₃ penalty, talc / CMC — https://www.sgs.com/en/-/media/sgscorp/documents/corporate/brochures/sgs-min-tp2004-02-pgm-ore-processing-at-ug-2-concentrator-in-south-africa.cdn.en.pdf ; https://www.sciencedirect.com/science/article/pii/S0892687524000335
- Kaggle flotation dataset — https://www.kaggle.com/datasets/edumagalhaes/quality-prediction-in-a-mining-process
- NVCL — https://www.auscope.org.au/nvcl ; USGS splib07 — https://www.sciencebase.gov/catalog/item/5807a2a2e4b0841e59e3a18d


---

## 9. v6 update (2026-10-01 night): supersedes parts of §7

### Corrections

- **MINERAL1 (§7, "Other records") is superseded.** The spectral model's skill on plant-feed QEMSCAN mineralogy is explained by **size fraction and process line**. A metadata lookup matches it, and the spectrum adds nothing on top (0 of 33 minerals better, 5 worse; `mineral1_q2.json`). Do not present "the camera reads feed mineralogy".
- **GEOMET (§7) after strict nesting.** Only the Bond work index beats its strongest baseline under all gates. v6 matches v5 on accuracy (v5 was slightly flattered by a k-means leak), with calibrated 80% intervals.

### New, real, South African

**Bushveld chromitite chemistry → PGE.** Bachmann et al. 2019, held out by project. Belt-type chemistry predicts Pt, Rh and 4E better than the average guess, and the seam better than the majority class. This is the honest XRF-to-PGM link to show Mintek.

### New, real plant

**Real plant soft sensor (iron ore, CC0).** It does not beat the last assay once leakage is closed. That is the argument for ore-first sensing.

### What to show in the Top-5 round

REEFPRINT Live:

- live scan of real cubes with absorption maps and the work-index decision;
- Bushveld PGE view;
- plant view (honest);
- lab round trip and exports;
- Evidence, including the correction.

Say the MINERAL1 correction **before** a judge finds it.
