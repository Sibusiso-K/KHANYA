# Plan Review Log: REEFPRINT v8 — pilot-ready industry build
Started 2026-10-02 ~08:00 SAST. MAX_ROUNDS=5. Reviewer: Codex gpt-6-astra, model_reasoning_effort=xhigh (from ~/.codex/config.toml), sandbox read-only every round. Builder/orchestrator: Claude Opus 5.5.

## Round 1 — Codex (thread 01a0fb16-c1e4-7062-bdd3-fbd7ced9d2cf)

Material problems remain. The plan is implementable as a **research demonstration and pilot proposal**, but it does not yet support “a concentrator could start this on Monday.” The main blockers are the phase-identification gate, unsupported action selection, the throughput-risk claim, and economics that turn gross scenarios into apparent opportunities.

I reviewed the named files and checked relevant external sources. I made no file changes.

1. **The flowsheet is too generic for the proposed customer.** D10 omits the second milling/flotation stage central to the UG2 story, obscures cleaner recycles, and leaves chrome recovery placement ambiguous. “After secondary crushing, <30 mm” is also a site assumption: an AG/SAG circuit may have a different feed preparation route.  
   **Fix:** Select one explicitly hypothetical UG2 MF2 circuit, show its recycles and optional chrome-recovery branch, and make scanner placement conditional on the actual site flowsheet.

2. **The chromite advice contains a dangerous direction error.** The source table in [docs/17:129](/C:/Users/USER/Desktop/REEFPRINT/docs/17-industry-landscape-roles-and-money.md:129) says “Reduce water recovery and froth depth.” Shallower froth commonly reduces drainage and increases entrainment. Deeper froth is not universally beneficial either; air, frother, solids and valuable recovery interact. [UG2 experimental work](https://open.uct.ac.za/items/24746e51-d776-4f63-ba97-351df6e035f8) explicitly examines those interactions.  
   **Fix:** Replace this with “reduce entrainment through site-tested water-recovery, air and froth-depth adjustments, subject to PGM-recovery limits.”

3. **Spirals do not solve the ultrafine-entrainment problem described.** The dossier itself says conventional spiral recovery deteriorates below roughly 53–75 μm, yet recommends spirals in the “chromite fines entrained” row. Removing suitable coarse chromite earlier and recovering ultrafine chromite are different interventions.  
   **Fix:** Restrict spiral advice to a characterized, size-appropriate stream and require a PGM-loss balance before removing it.

4. **Most advice rows have no validated observation feeding them.** Bulk gangue absorption cannot establish “locked valuables,” liberation, or a pentlandite/pyrrhotite shift. MINERAL1 provides modal wt%, not spatially registered liberation truth; the proposed spectral hypotheses do not validate talc detection either.  
   **Fix:** Require a named, validated measurement for each rule prerequisite and disable every row whose prerequisites are unavailable.

5. **The metallurgical rules are too categorical.** “Locked → regrind” ignores partial surface exposure, overgrinding, residence time and existing regrind capacity. “Pyrrhotite carries little PGM” cannot safely become a universal depression rule. PGM grain size is also not the same as the flotation particle-size window.  
   **Fix:** Make these diagnostic prompts for the metallurgist, conditional on site deportment, size-by-size recovery and reagent-response evidence.

6. **The cyclone calculation is an illustration, not a classifier model.** The equal-settling ratio of 1.323 is consistent with the assumed Stokes densities, but industrial cyclone partitioning also depends on pressure, solids concentration, viscosity, geometry, bypass and roping. It does not prove how much chromite is overground.  
   **Fix:** Label E6 a qualitative density-classification illustration and require measured mineral-specific partition curves for control claims.

7. **The hardware specification borrows the wrong camera’s protection rating.** E12 quotes FX17 IP52 while proposing a different SWIR camera. The proposed SX25 is **IP40**, with a full-frame maximum of **162 fps**, according to its [manufacturer datasheet](https://sensing.konicaminolta.us/wp-content/uploads/Specim-SX25-Technical-Datasheet-01.pdf). At an assumed 2 m/s belt speed, that is approximately 12.3 mm between lines before considering exposure blur.  
   **Fix:** Specify an actual camera/lens combination and calculate coverage, line pitch, exposure, SNR, bandwidth and enclosure requirements from its own datasheet.

8. **An equipment shopping list is not an installation design.** The plan protects the edge PC but does not clearly specify the camera enclosure, SWIR-transmitting window, thermal load, dew-point control, clean dry purge supply or safe maintenance access. Halogen heating, conveyor guarding, lockout, laser classification, vibration and earth/surge protection remain unaddressed.  
   **Fix:** Add a site-engineering acceptance sheet covering optical, mechanical, electrical, thermal and maintenance interfaces with named owners.

9. **Wet-ore refusal could eliminate the intended operating domain.** Dust suppression and wet feed may make refusal normal; 1.4/1.9 μm absorption also occurs in hydrated minerals, including the gypsum the plan wants to identify. Software cannot always distinguish moisture, coatings, window fouling and changed mineralogy from spectra alone.  
   **Fix:** Validate independent quality checks and report usable coverage by moisture, burden and ore condition, including the fallback and maintenance workload.

10. **Three passing hypotheses do not establish three distinct phases.** H1 aggregates mica and kaolinite, H2 aggregates chlorite and biotite, H3 combines anhydrite and gypsum, and H4 is an oxide group. Correlation with sample composition does not validate pixel labels. The checked target groups are present in every MINERAL1 record, so this dataset alone provides no absence cases for specificity.  
    **Fix:** Call these “validated spectral associations”; retain KHANYA’s separately evidenced phase-identification deliverable until distinct-phase discrimination is actually tested.

11. **H3 is physically mismatched to its reference label.** The 1.75 μm gypsum feature is associated with structural water; anhydrite is anhydrous. A pooled “Anhydrite/Gypsum” assay cannot validate gypsum abundance without knowing their split. [Spectral mapping research](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2021JB021976) describes the gypsum water features explicitly.  
    **Fix:** Treat H3 as exploratory against the pooled label or obtain gypsum-specific reference measurements before counting it as validation.

12. **“Tetracorder-style” currently overstates the method.** A band-depth scalar is only part of mineral identification: overlapping features require reference spectra, competing-material tests, feature shape and rejection criteria. The [USGS method](https://www.usgs.gov/publications/imaging-spectroscopy-earth-and-planetary-remote-sensing-usgs-tetracorder-and-expert) describes an expert system, not a lookup from one wavelength to one mineral.  
    **Fix:** Specify the exact published scalar implementation and its limitations; add library-based discrimination before using mineral names on maps.

13. **D1 does not defeat the size-fraction confound.** Fixed features still respond to grain size, surface scattering, moisture and intimate mixing. The existing extraction also removes each sample’s darkest 5% of pixels—particularly questionable when transferring to chromite-rich ore—and pixel-area averages are not bulk mass fractions.  
    **Fix:** Freeze and audit masking/aggregation, control fraction-by-line effects, and explicitly test whether feature signal survives nuisance and compositional controls.

14. **“Pre-registered” is too strong after repeated use of these labels.** The team already inspected MINERAL1 in v5, v6 and Q2 and selected hypotheses with its mineral abundances in view. Committing before this run prevents further undisclosed tuning but does not make the dataset untouched confirmation.  
    **Fix:** Describe this as a prospectively specified reanalysis and reserve confirmation for independent site samples.

15. **The statistical protocol remains under-specified and potentially optimistic.** “Pooled within strata” does not define ranking, weighting, residualization or missing strata. MINERAL1 contains monthly composites from three lines: shared monthly conditions may violate independence of all 36 line-month units. The [dataset paper](https://www.nature.com/articles/s41597-023-02061-x) also states 94 physical samples, versus 99 records used here.  
    **Fix:** Publish the sample-identity reconciliation and exact estimator, preserve all related crops/fractions together, and include month-blocked sensitivity analysis.

16. **The gates can reward weak correlations and punish useful improvements.** Raw 95% CIs are insufficient after selecting among four hypotheses; “adds in partial correlation” lacks a practical effect threshold. Conversely, `mineral1_q2.py` applies Mann–Whitney to dependent fraction-level errors, despite paired composite predictions. Roughly, even 36 independent observations need a correlation around 0.52 for 80% power under a conservative four-test adjustment.  
    **Fix:** Predefine one conditional endpoint per hypothesis, Holm-adjust those four tests, use cluster-aware paired inference and report minimum useful effects plus power.

17. **The existing “same overload risk” claim is false.** An 80% symmetric conformal interval does not guarantee 10% upper-tail failure. [value_chain.py:94](/C:/Users/USER/Desktop/REEFPRINT/training/value-chain-20261002/value_chain.py:94) declares risk matched when the upper CI permits **five percentage points more overload**; the observed interval is −4.8 to +4.1 pp. That is not equivalence.  
    **Fix:** Calibrate a one-sided upper bound and preregister an operationally acceptable non-inferiority margin; withdraw “same risk” meanwhile.

18. **The throughput simulation does not simulate the deployed policy.** It uses `hi` for every parcel, including **four GEOMET samples marked OOD-refused** and five borderline samples. It omits escalation, stale data, fallback, feed ramp limits, stockpile mixing and downstream constraints. Its fixed-P90 baseline is also weaker than an operating mill’s feedback/APC baseline.  
    **Fix:** Evaluate the complete refusal-and-control policy against existing APC or a credible dynamic baseline before assigning economic value.

19. **The energy-shortfall metric uses the wrong denominator for its name.** `true/used − 1` measures required energy in excess of provision; fractional shortfall relative to requirement is `1 − used/true`. The latter gives approximately **4.65%**, rather than 4.99%, for the interval policy. Neither directly measures grind coarsening.  
    **Fix:** Rename the current metric or change its denominator, and remove quantitative grind implications without a grind-response model.

20. **The recovery arithmetic is correct, but the valuation basis is not established.** `T × grade × 0.01 / 31.1034768` correctly calculates an absolute recovery percentage point. Multiplying 4E ounces by Valterra’s PGM basket or Northam’s equivalent-refined revenue requires matching metal baskets, downstream yields and payment terms. The basket-price ratio is an implied conversion factor, not independently verified FX.  
    **Fix:** Use metal-specific recoveries and net payable prices, or an explicitly assumed matching 4E basket, with separately dated FX.

21. **E2 is not a recoverable R334 million opportunity or an upper bound.** Jones’s comparison relaxes allowable concentrate Cr₂O₃; it does not demonstrate recovering the same extra PGMs while retaining the original specification. The code also converts a lower-bound recovery difference into an “upper bound” on value.  
    **Fix:** Remove E2 from the opportunity headline and retain it only as evidence that recovery and concentrate quality trade off.

22. **“ASSUMED” labels do not turn gross revenue into benefit.** E3 applies a Chilean powder-model result to Platreef, uses an assumed grade and Implats UG2 recovery, and omits additional mining/reclaim, milling, flotation, smelting and selling costs. More tonnes may merely move the bottleneck downstream; ore-constrained energy savings are also unmeasured.  
    **Fix:** Show incremental contribution cash flow under separately stated bottleneck, grade, recovery and cost scenarios, without a transferred financial confidence interval.

23. **The provenance audit has a concrete failure.** [economics.py:43](/C:/Users/USER/Desktop/REEFPRINT/training/economics-20261002/economics.py:43) marks the assumed three-shifts-every-day sampling schedule `CITED`, making E4’s CAD1.807 million per-stream scenario `CITED`. The plan’s “$1,500” is a **2017 Canadian-dollar** price, not a current South African quote. Search/news production inputs otherwise are correctly downgraded.  
    **Fix:** Mark sampling cadence and utilization as assumptions and display the lab price’s currency, date, preparation exclusions and local-quote requirement.

24. **Break-even needs a time horizon and full ownership costs.** “Recovery improvement that pays capex” leaves out financing, commissioning, sampling, assays, integration, enclosure, cleaning, lamps, compressed air, cooling, maintenance, spares, software support and downtime.  
    **Fix:** Calculate `break-even pp = (annualized installed capex + annual incremental costs) / annual net contribution per recovery pp`, with ramp-up and downside scenarios.

25. **The escalation clock is disconnected from the ore clock.** Five-minute acknowledgement, thirty-minute metallurgist response and within-shift lab work may all arrive after the relevant parcel. Waiting for timeout before falling back is especially weak during transitions.  
    **Fix:** Give each advisory a material-arrival deadline and validity period, apply its approved fallback immediately, and escalate investigation separately.

26. **Rule 5 is still prose at the application boundary.** [app.js:278](/C:/Users/USER/Desktop/REEFPRINT/presentation/belt-monitor/app.js:278) emits “review only” and “do not use these predictions,” not a typed conservative operating value. An SOP card without its version, applicable equipment state and approved settings is similarly incomplete. “More depressant” is not universally conservative.  
    **Fix:** Bind every refusal to a versioned, site-approved operating envelope or recipe with units, reason, authority and expiry.

27. **The hash chain is not tamper-evident against an attacker controlling the file.** They can rewrite the history and recompute every hash, or truncate it to a valid prefix. A pseudonymous ID supplies no authentication, and later lab truth cannot be inserted into an old record without changing the chain.  
    **Fix:** Append linked outcome events, authenticate writers and externally retain signed checkpoints containing the ledger identity, sequence count and final hash; otherwise claim only internal consistency checking.

28. **The ledger requires substantial backend work.** Today `audit()` stores an array in browser memory and exports it on demand; refresh loses it. Append-only JSONL alone does not handle concurrent writers, interrupted writes, disk-full conditions, recovery or authenticated roles.  
    **Fix:** Scope a durable single-writer event store with crash recovery, full model/policy/input hashes and explicit restart tests before adding integrity claims.

29. **The scorecard rewards compliance with the model.** Penalizing an override because a prediction later proved correct ignores constraints the operator knew. Interval hit rate rewards wide intervals; Brier/log scores require probabilities for defined outcomes, not an interval presented as “confidence.” Actions can also change the outcome being scored.  
    **Fix:** Remove gamification and operator penalties; report model calibration, interval score, coverage, escalation burden and independently reviewed decision quality.

30. **“POPIA: no names” is not a privacy design.** Role, shift, timestamps and notes can identify workers; team streaks can still become performance surveillance. Identifiability, not merely a name field, matters under the [government’s POPIA guidance](https://www.westerncape.gov.za/education/popia-protection-personal-information-act-2013).  
    **Fix:** Agree purpose, access, retention, correction, aggregation and non-disciplinary use with the site’s information officer and workforce representatives.

31. **“Read-only OPC UA” and “LLM never data” are incomplete boundaries.** Read-only credentials do not establish OT segmentation, certificate trust, connection limits or stale-quality handling. `server.py` sends the user’s question to the provider; that question can contain plant or personal data.  
    **Fix:** Specify a site-approved historian/DMZ interface with least privilege and certificate management, and disable external routing in the pilot unless outbound content is explicitly governed.

32. **The pilot has no adequate truth-and-time matching protocol.** Twice-weekly QEMSCAN gives roughly 26 composites in three months, before spreading them across streams and operating conditions. Shift composites cannot label individual second-scale parcels without mass/time aggregation and residence-time alignment. The strongest existing target, WI, has no corresponding Bond-test programme.  
    **Fix:** Define representative sampling, dry-mass weighting, stream/time alignment, assay QA/QC, WI reference tests and planned sampling of both accepted and refused conditions.

33. **Three months shadow plus three months advisory is not an experimental design.** Success depends on independent operating blocks, effect size, recovery-accounting noise, ore changes, carryover and adoption. Automatically retraining on each returning batch changes the intervention during evaluation and can leak future information into retrospective replay.  
    **Fix:** Freeze versioned models within randomized or matched operating blocks, define washout and stopping rules, and promote retrained candidates only through a separate chronological validation gate.

34. **The mass-balance helper is a new subsystem, not an extension of current “reconciliation.”** The existing function compares predictions with assays; its importer accepts blank numeric cells as zero and discards timestamps/revisions from accepted records. Two-product recovery also becomes unstable near equal concentrate/tails grades, while reconciliation requires measurement uncertainties and physical constraints.  
    **Fix:** Repair import semantics first, then restrict the demo to a stipulated two-product balance with singularity checks; defer general reconciliation.

35. **Vendoring the graphics libraries will currently break serving.** [server.py:39](/C:/Users/USER/Desktop/REEFPRINT/presentation/belt-monitor/server.py:39) excludes `.css`, `.mjs`, `.pbf` and `.geojson`, and its directory allowlist excludes a vendor directory. Worker loading depends on the pinned MapLibre build and CSP. The existing live bundle is already **34,722,997 bytes**, before new assets.  
    **Fix:** Pin versions, explicitly serve required assets/workers, eliminate remote style/font dependencies and test cold-start latency plus decoded/GPU memory on the presentation laptop.

36. **The licence choices are broadly sound; the packaging evidence is missing.** [three.js is MIT](https://github.com/mrdoob/three.js/blob/dev/LICENSE), [MapLibre is BSD-3-Clause with bundled notices](https://github.com/maplibre/maplibre-gl-js/blob/main/LICENSE.txt), and [Natural Earth data are public domain](https://www.naturalearthdata.com/about/terms-of-use/). Those facts do not license arbitrary basemaps, glyphs, textures or copied example assets.  
    **Fix:** Add exact versions, hashes, retained notices and every shipped data/asset licence to the SBOM.

37. **MRDS availability is less uncertain than the plan says, but the layer’s meaning is wrong.** The dossier’s added §6b reports 178 PGE-coded records with coordinates, including plants and chrome mines. That supports historical location context, not 178 current PGM operations or surveyed concentrator locations; the query and response are not reproduced in the plan. Natural Earth towns are not substitute mine coordinates.  
    **Fix:** Preserve the exact query and response, deduplicate/classify records, label vintage and positional uncertainty, and show towns only as towns.

38. **The novelty claim understates existing decision systems.** Mintek’s published FloatStar work already models feed chemistry to suggest mass-pull setpoints within operator limits—directly contradicting “APC reacts to the process, not the ore.” [The paper](https://www.scielo.org.za/scielo.php?pid=S2225-62532012000300011&script=sci_arttext) is explicit. Blue Cube at Northam, Plotlogic, MineSense and bulk-element analysers belong in the strongest-baseline comparison, not merely the integration diagram. PGNAA/PFTNA should not universally be described as Cf-252 systems; generator configurations exist.  
    **Fix:** Claim incremental, uncertainty-aware ore information over existing analyser/APC workflows, and demonstrate the increment rather than claiming an unoccupied layer.

39. **The brief’s strongest evidence is being replaced by weaker promises.** A CSV tag map does not demonstrate integration; replay animation does not measure acquisition-to-advice latency. `run_v6.py` produces results rather than a packaged edge inference service. `build_live.py` also omits full-resolution display assets from its source-hash manifest despite the README’s blanket hashing claim.  
    **Fix:** Reuse the existing OPC UA round-trip demonstration, benchmark actual inference separately from replay, package a reproducible model pipeline, and hash every shipped evidence asset.

40. **The small-team scope is untenable without explicit cuts.** Feature research, six advice families, durable identity-aware logging, gamification, reconciliation, two graphics engines, mapping, hardware engineering and a pilot protocol are multiple projects. The first plant-manager questions—site sponsor, existing instruments, actual bottleneck, approved intervention, sample access, budget owner and maintenance owner—still lack answers.  
    **Fix:** Ship one validated decision path, its refusal path, corrected economics, the existing phase evidence, a two-dimensional site schematic, a costed conditional pilot protocol and a rehearsed offline backup; defer gamification, 3D flowsheet, GIS panel, general reconciliation and automatic retraining.

VERDICT: REVISE

### Claude's response to round 1

**Accepted outright (code-checked where they referenced code):**
- **1–3, 5, 6** Flowsheet now a labelled hypothetical UG2 MF2 with conditional placement. Chromite-entrainment advice re-worded (the "reduce froth depth" direction error was real). Spirals restricted to characterised, size-appropriate streams. Categorical rules became diagnostic prompts. Stokes is labelled an illustration.
- **7, 8** Camera specs to be quoted per datasheet (the FX17 IP52 was misapplied to a different camera), with line pitch, cross-track size and blur computed. A site-engineering acceptance sheet with owners.
- **9** Wet ore: quality checks plus usable-coverage reporting; the hydrate/moisture ambiguity is acknowledged.
- **10–15** "Validated spectral associations", not phases; KHANYA carries ≥3 phases. H3 exploratory. Tetracorder claim dropped in favour of feature extraction per Laukamp et al. 2021. Masking frozen, with a sensitivity analysis. "Prospectively specified reanalysis", not pre-registration. Sample-identity reconciliation (99 vs 94). Exact estimator: partial Spearman by rank residuals after OLS on fraction × line, cluster bootstrap by composite, month-blocked sensitivity.
- **16** One endpoint per hypothesis, Holm across H1/H2/H4, a minimum useful effect of 0.30 and a power report. Noted: `mineral1_q2.py`'s Mann-Whitney on dependent fraction-level errors is conservative for a "better" verdict, so the MINERAL1 withdrawal stands, but its gate is mis-specified for dependence. Logged for the record.
- **17, 19** Verified in code:
  - `risk_matched` accepted +5 pp. Withdrawn.
  - The 80% symmetric interval does not give a 10% one-sided tail. Replaced by K-fold CV+ (Barber et al. 2021) with a pre-registered +3 pp non-inferiority margin.
  - The energy metric is renamed and the shortfall fraction added.
- **20–24** Valuation basis made explicit; E2 removed from the opportunity list; E3 is now incremental contribution with cost scenarios and no transferred CI; shift cadence ASSUMED (it was CITED — a real provenance error); full-cost break-even formula over a horizon.
- **25, 26** Material-arrival deadlines with an immediate approved fallback. A typed, versioned operating envelope at the app boundary.
- **27, 28** Ledger moves to a single-writer durable store in server.py with torn-write recovery. The claim is limited to internal consistency plus external checkpoints; authentication is a pilot prerequisite.
- **30, 31** POPIA purpose and retention agreed with the site before the pilot. External LLM off by default in the pilot profile. The OT/DMZ boundary listed as a prerequisite.
- **32, 33** Truth/time matching, a Bond test programme, refused-condition sampling, frozen versioned models in blocks, a chronological promotion gate.
- **34** Verified in code: Number("") = 0 accepted a blank value as 0, and timestamps and revisions were dropped. Fixed first. Mass balance reduced to a guarded two-product calculator.
- **35–37** server.py allowlist, cold-start tests, SBOM with hashes and notices, MRDS relabelled as historical locations with the query preserved.
- **38** Positioning corrected: FloatStar uses feed chemistry. The claim is now "incremental, uncertainty-aware ore information".
- **39** Hash every shipped asset (the full-resolution assets were missing — verified). A reproducible exported WI model with a CPU latency benchmark; replay is never presented as latency. Reuse the existing OPC UA round-trip evidence.

**Partly accepted:**
- **18** The deployed refusal path, ramp limit and stale-data rule are now simulated. An APC/feedback baseline **cannot be simulated honestly**, because HIDSAG samples are not a time series. Instead of fabricating one, the limit is stated and the value-vs-APC question is assigned to the pilot.
- **29** Individual gamification is removed, as Codex advised. The user explicitly asked for gamified human-in-the-loop, so a **non-competitive team learning loop** is kept: shared process goals, model calibration, escalation burden, and weekly review of decision records against lab outcomes. No individual scores, no leaderboards, no override penalties. Reason: it honours the user's intent without the perverse incentives or the surveillance risk.
- **40** Scope is cut and phased (Phase 1 corrections are blocking). The **2D map is kept**: the user asked for mapping, real public-domain locations exist, and an SVG fallback bounds the cost. The 3D flowsheet, general reconciliation, automatic retraining and individual scoring are deferred. The three.js cube is optional, last.

**Rejected:** none outright.


### Between rounds 1 and 2 (07:43–08:50): Codex usage limit; work done in the interim (disclosed)

Codex's round-2 resume failed at 07:43 with a usage limit (reset 08:51). Rather than idle, the following was done. **Round 2 reviews the plan and this code together.**

**Phase 1: accepted, verified corrections** (commits e2829e2, d6793a6):
- **Import.** A blank value is now refused (it used to become Number("") = 0). Timestamp and revision are kept and validated.
- **Hashing.** Every shipped asset is hashed into `summary.json`.
- **Economics.** Restated as net payable value per recovery point plus break-even across a capex/opex grid; E2 removed; cadence set to ASSUMED.
- **Dossier advice table.** Rewritten as diagnostic prompts with a prerequisite for each row. The froth-depth direction was fixed and spirals restricted to size-appropriate streams.
- **Value chain** (findings 17–19):
  - "Same risk" withdrawn.
  - The **CV+-style approximation failed** the pre-registered +3 pp non-inferiority test (upper bound +4.8 pp).
  - The plan's stated fallback (D2) was then run: Kaggle `reefprint-hidsag-v8-model` recomputed v6 with **signed calibration scores**, reproducing v6's predictions exactly (max diff 0.0).
  - With the **exact one-sided split-conformal bound**, the deployed policy gains +1.9% [+0.9, +2.9] and is non-inferior on overload: −2.1 pp, one-sided upper bound +1.4 pp.
  - **This is a method switch after a failure, disclosed everywhere, and labelled provisional.** Codex: please judge whether that is acceptable or should be withdrawn.

**Phase 3 evidence:**
- **v8-model** (Kaggle, about 10 min):
  - an exported deployable model that loads locally (sklearn 1.8.0);
  - **92 ms median per parcel** (features + inference + OOD) on a 4-core Kaggle CPU;
  - 159 ms on this laptop, first call.
- **v8-features** (SPEC and the analysis script committed *before* output existed; commits 81e75fb and 4e34c04):
  - **no hypothesis passes the gate**;
  - H2 (Fe-OH + Mg-OH ↔ chlorite + biotite) has partial ρ +0.27 [+0.03, +0.49], Holm p 0.045, below the 0.30 minimum useful effect;
  - the raw correlations are mostly fraction × line;
  - a secondary aggregation's H4 "pass" has an unstable sign and is not claimed;
  - **the belt sensor does not earn ≥3 phases; KHANYA carries that deliverable.**

**Phase 4 docs:**
- docs/18: installation design computed from the **SX25 datasheet [P]**. Line pitch 9–19 mm and cross-track 1.4–2.3 mm (parcel-level, not particle-level). Also the site acceptance sheet, edge cases and the pilot protocol.
- docs/19: security by design.
- docs/20: competitors, business, team and velocity.

**Track S code, written before approval** (commit 830f8e4). It is the new user requirement; standard controls, low rework risk. Code is in `presentation/belt-monitor/secure/`, `app_server.py`, `manage.py` and `test_secure_server.py`:

- **Authentication and access:**
  - RBAC, deny by default;
  - scrypt passwords;
  - server-side sessions (token stored hashed);
  - CSRF header;
  - lockout and throttling;
  - Host and Origin checks;
  - strict CSP with no inline script;
  - CLI-only admin.
- **The decision record:**
  - SQLite ledger, append-only by trigger;
  - hash chain;
  - **hybrid Ed25519 + ML-DSA-65 signed checkpoints** (pqcrypto);
  - **X25519 + ML-KEM-768 sealed exports**.
- **Uploads:**
  - CSV and image ingestion, with EXIF stripped by re-encoding;
  - AES-256-GCM at rest;
  - guest expiry after 24 h.
- **The guest sandbox:** a separate database **and separate signing keys**. A self-review caught that guests could have obtained production signatures; fixed before commit.
- **Gates:**
  - **17 security tests pass**;
  - **Bandit: 0 issues** in 904 lines;
  - **pip-audit found 9 known vulnerabilities in cryptography 46.0.6**, which was upgraded to 50.0.2 and is now clean.

**Not done yet:**
- the UI wiring (login overlay, upload panel, decision-record panel with deadline and envelope);
- the Dockerfile and tunnel runbook;
- the QR code;
- the map;
- the mass balance;
- SBOM and toolchain updates for cryptography, pqcrypto, Pillow and qrcode;
- the BUILDLOG.
