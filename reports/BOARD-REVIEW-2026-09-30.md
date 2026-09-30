# Board-level review: usability, field value, feasibility

**Date:** 30 September 2026, evening. **Build:** `khanya/preprod-fixes` at `ec9f853` (PR #17, top of the stack).
**Lens:** a 20-year geologist and metallurgical engineer on Mintek's board, asking whether a professional, from student to senior, would use this, on a phone, in the field, and whether it saves time and money.
**Method:**
- Every mode run live at phone width (375 × 812) and on desktop.
- Every branch searched for the features asked about.
- The committed evidence re-read for the time and cost question.

Measured values are marked as measured. Professional judgement is marked as judgement.

---

## Verdict

This is an honest, well-guarded **laboratory triage prototype**. It is not a field tool, a phone tool, an XRF tool or a 3D tool, and it must not be pitched as one. On the inputs it was built for, it declines far more than it decides (2 of 12 held-out sections get a confident call). The time and cost saving has not been demonstrated, and the one impact number in the repo is now out of date.

## The questions asked

| Question | Answer | Evidence |
|---|---|---|
| Easy to use on a phone? | **No.** | Measured at 375 × 812: <ul><li>the Upload button is at y = 802 on an 812 px screen, below the fold;</li><li>the landing card is cut off in a fixed 330 px box with its own scrollbar;</li><li>the result is a 3,315 px page inside a 1,500 px box, scrolling inside a scrolling page;</li><li>the result is 415 px wide in a 343 px box, so "APPLIED", "CLEANER" and "MODEL CONFIDENCE" are clipped;</li><li>40 of 66 text elements are 9-11 px;</li><li>after the 35 s wait the answer sits below the controls.</li></ul> Good: no page-level sideways scroll, and the decision headline is large (30 px). |
| XRF data to the phone? | **Not built.** | No XRF input on any branch; one mention is a comment in an offline script. PR #15 shows XRF tiles marked "NOT CONNECTED". |
| A 3D render of the scan, click for composition? | **Not built, and it should not be built from this input.** | No 3D code on any branch ("three" matches are the English word). The mineral map is a static image: no scripts or click handlers in the result templates. A polished section is a 2D slice: a 3D view needs serial sections, X-ray CT, or drill-hole survey data for a block model. |
| Is it fast? | **Fast enough for a lab bench; irrelevant in the field.** | Measured: <ul><li>35.0 s per sample (six 512 px fields, 18% of the section);</li><li>210 s for a whole section, advisory only;</li><li>25 s cold start.</li></ul> The phone changes nothing: inference runs on the laptop. Making a polished section takes hours before any of this starts (judgement). |
| Does it save time and cut costs? | **Not demonstrated.** | <ul><li>Confident calls past the gates: **2 of 12** held-out (17%), **3 of 37** train/val (8%). About 5 in 6 samples still need the lab.</li><li>The "verify" flags have never been compared with what QEMSCAN or a mineralogist would flag, so there is no evidence the right samples are being sent.</li><li>No time-and-motion study.</li><li>`MINTEK-FIT.md` §3.1 still claims 6 of 12 (50%) answered confidently, anchored to $1,500/sample (SRC, 2017) and a roughly one-week lab turnaround. That was true before today's gates, not now.</li></ul> |
| Usable from student to senior? | **Neither, yet.** | <ul><li>**Student:** unexplained jargon on the result ("apparent 2D sulphide association index", "payload-bearing particles", "provisional floor 9", "conformal band", "verdict state"), and three modes plus "Presenter controls" and a "diagnostic" toggle before the upload. The refusal reasons are well written.</li><li>**Senior:** composition is "% of ore area" (no weight %); no grain-size distribution, no liberation by size class, no association matrix, no PGM or chromite classes, no sample ID, hole or depth, no export to a report or LIMS.</li></ul> |

## Technical feasibility (judgement, with the repo's own numbers)

**What works:**
- offline, CPU-only, pinned install, preflight;
- honest refusals: colour cast, evidence floor, a provisional confidence gate;
- only validated samples touch the simulated plant;
- provenance bound to the checkpoint hash.

For a research prototype, this is unusually disciplined.

**What does not transfer to South African ore:**
- It was trained on Norilsk sulphides.
- There are no chromite or PGM classes; chromite is the main gangue in UG2.
- Magnetite IoU is 0, and UG2 base-metal sulphides are under 1 vol% (HANDOVER), rarer than the class the model already misses.
- Deploying on Bushveld ore needs QEMSCAN-labelled South African sections. The team's proposal to Mintek is the right next step, and it is a data problem, not a code problem.

**Other limits:**
- **Imaging set-up.** It is bound to one: a new microscope or camera must be characterised, and a phone photographed through an eyepiece is outside the validated domain.
- **Plant integration.** It is one simulated tag. A real plant needs DCS integration, management of change and a metallurgist's sign-off.

## Scorecard (this lens; not the pre-production rubric)

This rubric weights what a field professional needs, with usability heavy as asked. It is a different question from the pre-production score (79/100: does the build do what it claims, safely).

| Category | Weight | Score | Why |
|---|---:|---:|---|
| Usability, student | 15 | 5 | clear decision headline and refusal reasons; unexplained jargon and developer controls first |
| Usability, senior professional | 15 | 4 | area % only; no size-by-size liberation, grain size or association; no sample record or export |
| Mobile | 15 | 3 | measured: upload below the fold, nested scroll, clipped result, 9-11 px text |
| Speed | 10 | 6 | 35 s a sample is fine on a bench; the OPC UA overhead remains; section preparation dominates anyway |
| Field value: time and cost | 15 | 3 | 17% actionable on held-out data; flags never compared with QEMSCAN; stale 50% claim |
| Technical feasibility | 15 | 5 | robust offline pipeline on an analogue; no path to UG2 without South African labelled data and new classes |
| XRF to phone | 5 | 0 | not built |
| 3D render, click for composition | 5 | 0 | not built; not meaningful from a 2D section |
| Trust: does it avoid misleading a professional | 5 | 9 | declines when unsure; says why; only validated samples move the plant |
| **Total** | | **40.5 / 100** | |

## What to do, in order

**Before the pitch (hours, no model change):**
1. **Fix two stale claims.**
   - `MINTEK-FIT.md` §3.1: 6 of 12 becomes 2 of 12 after the gates.
   - The landing text still promises refusal when advice "changes with the lighting"; the lighting check is now off by default.
2. **Pitch it as what it is:** lab-bench triage that knows when to say "send this to QEMSCAN". Put XRF, phone capture and any spatial view on the roadmap slide, not in the demo.
3. **Mobile:**
   - upload first;
   - hide Presenter controls and the diagnostic toggle from end users;
   - no nested scroll (size the result frame to its content);
   - stop the strip overflowing at 343 px;
   - text at 12 px or more;
   - jump to the decision after a run.
4. **A one-line plain-language explanation** under each technical term (tooltip or glossary).

**After the pitch:**
1. QEMSCAN-labelled South African sections; chromite and PGM classes.
2. Validate the "verify" flags against QEMSCAN or a mineralogist. That is the real time-and-cost evidence.
3. **Outputs a metallurgist needs:** weight % (via densities), grain size, liberation by size class, association matrix.
4. **Sample records:** ID, hole, depth; export to a report or LIMS.
5. **XRF as a consistency check.** Elements against the predicted mineralogy, e.g. predicted chalcopyrite should imply Cu. Read from the instrument's export or SDK. XRF measures elements, not phases, so it cannot label them.
6. **Spatial view only with survey data.** Results by depth down a logged hole (a strip log), then a block model when collars and surveys exist. Never a 3D picture of a 2D section.
7. **Phone capture** only after the imaging set-up is standardised and characterised. Merge the two OPC UA sessions (about 10 s a run).
