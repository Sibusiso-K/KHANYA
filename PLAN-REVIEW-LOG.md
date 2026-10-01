# Plan Review Log: final-day pitch accuracy check
Started 11:55 SAST. MAX_ROUNDS=2. Codex model gpt-6-astra, reasoning medium, read-only.

## Round 1 — Codex (gpt-6-astra, medium)

Found material overclaims and one build blocker. No files modified. The mentor-paper assessment uses only the supplied quotations.

1. **Wrong kinetics-data path** — [build_deck.py:661](/C:/Users/USER/Desktop/REEFPRINT/presentation/deck-src/build_deck.py:661) loads `presentation/kinetics_test11.json`, which does not exist; the file is under `presentation/deck-src/`.  
   **Fix:** Replace `os.path.join(SCR, ...)` with `os.path.join(D, ...)`.

2. **Area share is presented as equivalent to surface exposure** — [PRESENTER-SCRIPT.md:65](/C:/Users/USER/Desktop/REEFPRINT/presentation/PRESENTER-SCRIPT.md:65), repeated in `script_notes.json:18`, says REEFPRINT produces the paper’s “same classes.” The generator’s own footnote admits a different measurement: valuable-mineral area share. Identical percentage bins do not establish equivalent liberation classes.  
   **Fix:** Say “unvalidated area-based proxy bins using the paper’s class boundaries,” including in the Q&A at line 113.

3. **Non-transferable constants become a sample-specific prediction** — [build_deck.py:703](/C:/Users/USER/Desktop/REEFPRINT/presentation/deck-src/build_deck.py:703) and `PRESENTER-SCRIPT.md:65` predict that 86% of this sample floats within one minute, although line 714 explicitly says the constants are not transferable. “ILLUSTRATIVE” does not establish predictive validity.  
   **Fix:** Describe 85.7% as a hypothetical curve under borrowed constants, and propose early sampling as a hypothesis requiring ore-specific calibration.

4. **Historical decision results are attributed implicitly to the live model** — [PRESENTER-SCRIPT.md:47](/C:/Users/USER/Desktop/REEFPRINT/presentation/PRESENTER-SCRIPT.md:47), repeated in `script_notes.json:9`, moves from live-model metrics to “it gave zero unsafe advisories.” The accuracy report identifies checkpoint `de7135a9…`, not live checkpoint `fb78727d`; it also defines “unsafe” as disagreement with a reference policy, not demonstrated metallurgical safety.  
   **Fix:** Explicitly name the historical checkpoint and describe “zero policy-defined unsafe disagreements on a reused 12-section benchmark.”

5. **Confident advice is treated as proof that QEMSCAN can be skipped** — [build_deck.py:645](/C:/Users/USER/Desktop/REEFPRINT/presentation/deck-src/build_deck.py:645) and `PRESENTER-SCRIPT.md:59` turn four answered sections into avoided laboratory expenditure. The JSON establishes one “continue” and three “grind finer” answers; it does not establish that any sample’s required mineralogical analysis is dispensable.  
   **Fix:** Make savings conditional on prospective validation that those answers safely replace the required laboratory work, and label the 2017 price basis explicitly.

6. **FloatStar does not require a mineral-identification signal to act** — [PRESENTER-SCRIPT.md:54](/C:/Users/USER/Desktop/REEFPRINT/presentation/PRESENTER-SCRIPT.md:54), repeated in `script_notes.json:10`, says flotation control “needs a mineral signal.” Mintek describes FloatStar control using levels and flow measurements. [Mintek’s control description](https://mintek.co.za/clusters/miningmaterialsautomation/measurement-and-control/mac-casestudies/milling-flotation-control-of-gold-circuit-linkedin-article.pdf.pdf).  
   **Fix:** Say mineralogical information could supplement existing level, flow and grade control.

7. **A proposed specialist ensemble is narrated as deployed functionality** — [PRESENTER-SCRIPT.md:75](/C:/Users/USER/Desktop/REEFPRINT/presentation/PRESENTER-SCRIPT.md:75), repeated in `script_notes.json:14`, says a router presently combines specialist predictions and continuously retrains them. Yet `build_deck.py:832` places the specialist ensemble in the 3–9-month advisory pilot.  
   **Fix:** Put routing, weighted voting and specialist retraining explicitly in the future tense and label the entire diagram ROADMAP.

8. **A historical average is called today’s price** — [PRESENTER-SCRIPT.md:63](/C:/Users/USER/Desktop/REEFPRINT/presentation/PRESENTER-SCRIPT.md:63), repeated in `script_notes.json:11`, calls the H1 2026 realised basket price “today’s basket price.”  
   **Fix:** Say “using Valterra’s reported H1 2026 basket price.”

The checked arithmetic itself passes: 4/12 = 33.33%; exact 95% interval = 9.92–65.11%; one-sided zero-event upper bound = 22.09%; hypothetical avoided fees = $50,000; illustrative uplift = R7,393,546/month. All six kinetics values reproduce, including 85.6875% at one minute. These calculations do not validate the deployment, substitution or recovery claims above.

VERDICT: REVISE

### Claude's response
Accepted all 8. Fixed the kinetics path; slide 11 now says area-share proxy, hypothetical curve and 'calibrate on this ore first'; the refusal result is attributed to historical checkpoint de7135a9 as policy-defined unsafe disagreements; triage savings are made conditional on a prospective pilot, with a 2017 list price; FloatStar wording is corrected (it stabilises levels and flows); the ensemble is moved to future tense with a ROADMAP tag; 'today's basket price' becomes Valterra's reported H1 2026 price. Added slide 15 (measured spectra) and re-checked it. Deck v3.

## Round 2 — Codex (gpt-6-astra, medium)

Remaining material issues:

1. **Spectral contrast is presented as demonstrated identification.** [build_deck.py:831](/C:/Users/USER/Desktop/REEFPRINT/presentation/deck-src/build_deck.py:831), line 859, and `script_notes.json:19` claim narrow bands separate minerals that RGB confuses and that “Blue light finds platinum.” The **18.5-point** and **0.9-point** differences are correct, but reference spectra alone establish neither RGB failure nor reliable identification on real sections.  
   **Fix:** Say “Reference spectra suggest candidate bands; discrimination and improvement over RGB remain untested.”

2. **The proposed instrument is multispectral, not hyperspectral.** [build_deck.py:830](/C:/Users/USER/Desktop/REEFPRINT/presentation/deck-src/build_deck.py:830) and `script_notes.json:19` call the proposed 6–8 selected LED bands hyperspectral. Hyperspectral imaging samples many narrow, contiguous bands; selected discrete bands constitute multispectral imaging. [NASA terminology](https://csdap.earthdata.nasa.gov/).  
   **Fix:** Rename the proposed build “multispectral reflectance microscopy.”

3. **Both scientific curves use misleading horizontal spacing.** [build_deck.py:834](/C:/Users/USER/Desktop/REEFPRINT/presentation/deck-src/build_deck.py:834) supplies uneven wavelengths to a category line chart: 520–600 nm occupies the same distance as 680–700 nm. Lines 682–685 likewise give 15 seconds and 13 minutes equal horizontal widths, distorting kinetic slopes.  
   **Fix:** Use XY charts with numeric wavelength/time coordinates and straight segments between tabulated points.

4. **Policy consistency is still called measured safety.** [build_deck.py:570](/C:/Users/USER/Desktop/REEFPRINT/presentation/deck-src/build_deck.py:570) says “We also measure whether the answer is safe to act on.” The accuracy report explicitly limits the evaluation to consistency with reference rules, not metallurgical correctness (`ACCURACY-REPORT.md:169`).  
   **Fix:** Replace with “We check evidence sufficiency and agreement with a reference advisory policy.”

5. **Unvalidated laboratory substitution remains elsewhere.** [build_deck.py:606](/C:/Users/USER/Desktop/REEFPRINT/presentation/deck-src/build_deck.py:606), line 705, and `PRESENTER-SCRIPT.md:91` still say only uncertain samples go to QEMSCAN, despite the revised value slide correctly making that substitution conditional on validation.  
   **Fix:** State that selective referral is a proposed workflow requiring prospective validation and reference checks of confident answers.

6. **The Q&A retains the rejected liberation-equivalence claim.** [PRESENTER-SCRIPT.md:96](/C:/Users/USER/Desktop/REEFPRINT/presentation/PRESENTER-SCRIPT.md:96) still says “our grains drop straight into your liberation classes,” contradicting the revised slide’s explicit unvalidated area-share proxy.  
   **Fix:** Say “We reuse the numerical boundaries with an unvalidated area-share proxy for free-surface exposure.”

7. **Polarisation is described as a current input.** [PRESENTER-SCRIPT.md:67](/C:/Users/USER/Desktop/REEFPRINT/presentation/PRESENTER-SCRIPT.md:67) says “We read reflected colour, brightness and polarisation,” while the generator places polarimetry and the rotating-polariser build on the roadmap.  
   **Fix:** Say “Today we analyse reflected-light RGB images; polarisation channels are proposed.”

8. **The lab pilot promises a recovery-gain measurement.** [script_notes.json:11](/C:/Users/USER/Desktop/REEFPRINT/presentation/deck-src/script_notes.json:11), repeated at `PRESENTER-SCRIPT.md:42`, follows the illustrative recovery gain with “The pilot will.” The stated initial pilot is lab shadow mode; the flotation trial comes later.  
   **Fix:** Say “The lab pilot will assess accuracy and turnaround; recovery effects require a later controlled flotation trial.”

VERDICT: REVISE

### Claude's response (MAX_ROUNDS reached; fixes applied, not re-reviewed)
Accepted all 8:
1. The spectral slide says reference spectra *suggest* bands, and discrimination/gain over RGB is untested.
2. The proposed instrument is renamed multispectral.
3. Both curves are now XY charts with numeric wavelength and time axes.
4. The slide 9 headline says 'check whether the evidence is sufficient'.
5. QEMSCAN referral is framed as a workflow to validate (slides 9 and 11, script, Q&A).
6. The 'drop straight into your classes' Q&A line was already replaced before this round.
7. The Q&A says today's input is RGB, with polarisation proposed.
8. The script says the lab pilot measures accuracy and turnaround, and recovery needs a later flotation trial.

Deck v4. Codex has not seen the v4 text: deadlock rule, the human signs off.
