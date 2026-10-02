# 18 — Where it would sit, what it takes to install, and how a pilot would prove it

*2026-10-02, plan v8 (ClauDex round-1 revision), Phase 4. This document is a **conditional design**.*

- Every site-specific value is **ASSUMED** until the site supplies it.
- Camera facts are quoted from manufacturer datasheets that were read: **[P]**.
- Geometry is computed by `training/installation-20261002/sensor_geometry.py`. Nothing here is built (ADR-0002).

## 1. Where it sits: placement is conditional on the site's flowsheet

*The app's "Where it sits" view will draw this circuit.* It is a **labelled hypothetical UG2 MF2 circuit**:

1. ROM → primary and secondary crushing.
2. **Primary-mill feed conveyor ← line scanner here.**
3. Primary ball mill ↔ cyclones → primary rougher / scavenger flotation.
4. Rougher concentrate → cleaners → final concentrate.
5. Rougher tails → secondary mill ↔ cyclones → secondary rougher / cleaner flotation.
6. Final tails → an **optional chrome-spiral plant**, only on a size-characterised stream (spirals work best at about 75 µm–3 mm, and lose < 53 µm chromite **[P]**, Molefe & Baloyi 2022) → tailings facility.

Cleaner tails recycle to the rougher feed. Where the site's feed preparation is AG or SAG, the scanner goes on whichever conveyor carries mill feed at a stable burden. A ROM-reclaim conveyor is a second, earlier option.

**Why the mill-feed belt.** It is the last point where the ore can be measured **before** the decision it informs (the feed rate). It is also where the burden is most uniform.

**Why not slurry.** Blue Cube's MQi already measures slurry chemistry in-line (PGM g/t and Cr₂O₃ % at Northam **[S]**). We would read its output, not duplicate it.

## 2. The sensor, by name, and what its geometry allows

**SWIR camera — Specim SX25 [P]:**
- 960–2500 nm, 640 spatial samples, 392 bands, 8 nm FWHM;
- **maximum 162 fps full frame**, 16-bit, spectral ROI and binning;
- lens 38° (OLES17) or 66° (OLES9);
- **IP40, +5 to +40 °C non-condensing**, 35 W max, 5.3 kg.

It covers the 2.2–2.35 µm Al-OH and Mg-OH features. The Specim FX17 (900–1700 nm, IP52 **[P]**) does not, so it is not sufficient on its own.

**VNIR camera** (400–1000 nm, Fe³⁺ and colour): an FX10-class camera. Its datasheet could not be retrieved this session, so its specifications are **to be quoted**, not stated.

**Geometry** (computed; belt width and speed ASSUMED):

| Belt | Speed | Line pitch at 162 fps | Cross-track pixel | Working distance (38° / 66° lens) |
|---|---|---|---|---|
| 0.9 m | 2.0 m/s | 12.3 mm | 1.41 mm | 1.31 m / 0.69 m |
| 1.2 m | 1.5 m/s | 9.3 mm | 1.88 mm | 1.74 m / 0.92 m |
| 1.2 m | 2.0 m/s | 12.3 mm | 1.88 mm | 1.74 m / 0.92 m |
| 1.2 m | 3.0 m/s | 18.5 mm | 1.88 mm | 1.74 m / 0.92 m |
| 1.5 m | 2.0 m/s | 12.3 mm | 2.34 mm | 2.18 m / 1.15 m |

**Data rate:**
- 81.3 MB/s at full frame;
- 15.6 MB/s with a 75-band spectral ROI;
- GigE-class link, edge PC beside the conveyor.

**Conclusion.** At plant belt speeds the scanner samples the surface in lines about 9–19 mm apart. That suits **parcel-level averages**, which is what our models use. It does not suit particle-by-particle mapping or sorting.

**Line triggering.** A belt-speed encoder (the Specim FX-series datasheet lists shaft-encoder trigger inputs **[P]**) keeps the line pitch constant when the belt speed changes.

## 3. Site-engineering acceptance sheet (each line needs a named owner at the site)

| Area | Requirement | Why | Owner (site role) |
|---|---|---|---|
| **Optical enclosure** | Rated enclosure (IP66 or better, ASSUMED) around an **IP40** camera; SWIR-transmitting window (sapphire or a suitable glass: ASSUMED, to be specified with the vendor) | The camera itself is IP40 | Instrumentation engineer |
| **Window cleanliness** | Clean, dry purge air plus an air knife; a scheduled cleaning interval; fouling detected from the white-reference response | Dust film looks like an absorption change | Instrumentation tech |
| **Thermal** | Cooling (vortex or AC) to stay within **+5 to +40 °C**; **dew-point control** (non-condensing); account for heat load from the halogen line lights | The datasheet is non-condensing | Electrical / HVAC |
| **Illumination** | Broadband halogen line lights (SWIR needs them; LEDs are weak above 1.7 µm); a lamp-life schedule; an automated white-reference shutter | Lamp ageing drifts the spectra | Instrumentation |
| **Mechanical** | Anti-vibration mounts; conveyor guarding unchanged; safe access platform; **lockout/tagout** for maintenance | The conveyor is a hazard zone | Mechanical / safety officer |
| **Burden sensing** | A height laser or lidar for presence and empty-belt detection; record its **laser class** | Empty or overloaded belt, shadows | Instrumentation |
| **Electrical** | Earthing, surge protection, UPS ride-through for power dips | Eskom supply dips | Electrical |
| **Network / OT** | Historian or DMZ read interface, least privilege, certificate management; no write path until sign-off | OT security | OT / IT security |
| **Radiation** | **None.** No radioactive source, unlike isotope PGNAA (Cf-252 needs National Nuclear Regulator authorisation **[S]**) | Licensing burden avoided | Radiation protection officer (sign-off only) |
| **Maintenance budget** | Window cleaning, lamps, reference tiles, spares, software support | Opex line items for the break-even | Maintenance planner |

## 4. Edge cases: how each is detected, and what the system does

| Condition | Detection (software) | Response |
|---|---|---|
| **Wet ore / dust-suppression water** | 1.4 / 1.9 µm water-band depth above a site-calibrated level | Refuse the parcel → envelope fallback. **Report usable coverage** by moisture class in the pilot (refusal may be common; it is budgeted). Hydrated minerals such as gypsum also absorb there, so this is acknowledged as ambiguous |
| **Fines coating rocks** | Low spectral contrast across all features; a brightness shift | Flag; compare with a periodic grab sample |
| **Empty or overloaded belt** | Burden height and a brightness floor | No prediction; no false "soft ore" |
| **Lamp ageing / reference drift** | White-reference trend; out-of-tolerance → refuse | Recalibrate; lamp change |
| **Window fouling** | Reference response and spatial non-uniformity | Purge, clean, log |
| **Shadows / burden geometry** | Height map + brightness | Mask the pixels |
| **Belt-speed change** | Encoder | Line-trigger adapts |
| **Flooding / extreme weather** | Site event (Valterra Amandelbult flooded in Feb 2025 **[P]**) | System off-line; the plant continues on the existing workflow |
| **Power dip** | UPS | Graceful shutdown; ledger torn-write recovery |
| **Stockpile blending lag** | Transit time is ASSUMED per site | The advice validity window is tied to arrival |
| **Ore-constrained plant** | Site fact | Throughput value = 0; value only via energy and grind stability |
| **Out-of-distribution ore** | Mahalanobis OOD (calibration p95 / p99) | Borderline → stricter; refused → envelope fallback + lab sample |

## 5. Pilot protocol (what would prove or disprove it)

**Prerequisites** (plant-manager questions, answered before day 1):
- the site sponsor;
- existing instruments (analysers, froth cameras, APC such as MillStar/FloatStar);
- whether the plant is ore- or mill-constrained;
- the approved intervention range (envelope);
- sample access;
- the budget owner and maintenance owner;
- information-officer and workforce-representative agreement on the decision record (POPIA purpose, access, retention, non-disciplinary use);
- site identity / SSO for the ledger;
- the OT read interface.

**Phase A — shadow** (about 3 months, ASSUMED):
- Predictions are logged; no actions.
- **Truth matching:** dry-mass-weighted composites over parcel windows, aligned by residence time; assay QA/QC with blanks, duplicates and certified reference materials.
- **A Bond WI test programme** on belt-sampled material (N tests, ASSUMED, with a cost line), because the one validated target, WI, needs site truth.
- QEMSCAN/MLA composites (for example at Mintek, which runs both **[S]**) on a planned schedule that **includes refused and accepted conditions**.
- **Usable coverage** reported by moisture, burden and ore condition.

**Phase B — advisory** (about 3 months, ASSUMED). Operators and metallurgists act through the decision record. Models are **frozen and versioned**.

**Phase C — coupled.** OPC UA into the APC within its limits, only after sign-off.

**Experimental design:**
- matched or randomised **on/off operating blocks**, as in the FloatStar Vale study (about 400 days on/off **[P]**);
- washout between blocks;
- pre-specified KPIs: recovery, Cr₂O₃ in concentrate, kWh/t, reagent g/t, overload/coarse-grind events;
- doctrine gates; pre-specified stopping rules;
- retrained models promoted only through a separate chronological validation gate (no automatic retraining during evaluation).

**Success.** The pre-registered KPI improves under the doctrine gates **and** the overload non-inferiority margin (+3 pp, ASSUMED until the site sets it) holds. Break-even needs only 0.04–0.26 pp of recovery (`economics.py` V4, ASSUMED cost grid).

## 6. Cost lines (all ASSUMED; quotes required)

- SWIR camera class US$50k–300k **[S]**.
- VNIR camera, lenses, enclosure and window, lighting, encoder, burden sensor, edge PC, integration and commissioning.
- Sampling, assays, Bond tests and QEMSCAN/MLA composites.
- Maintenance, spares, purge air, lamps, software support.

The break-even grid in `economics.py` spans US$0.5–3 M capex and US$0.1–0.6 M/yr opex. The conclusion (a fraction of a recovery point) is insensitive to where in that range a quote lands.
