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
