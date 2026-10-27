# Episode 3 analysis: "Optical AI for South African Platinum Flotation"

Round two of the debate, run as an "engineering clinic" in reply to
`FOUNDER-REBUTTAL-DEBATE-2.md`. 17 min 57 s, transcribed locally with Whisper
on 27 October 2026. Transcript: `notebooklm/transcripts/03-Optical_AI_for_South_African_Platinum_Flotation.txt`.
Claims were checked against `STATUS.md`, `reports/ADVERSARIAL-CRITIQUE-2026-09-15.md`,
`src/advisor.py`, the rebuttal and Moodley et al. (2026).

## Verdict

The best episode so far on **product logic**: it gives usable answers to the
critique's questions about thresholds and shift-level advice, and it puts
chromite first. It is the worst so far on **facts about the build**: it credits
fixes you haven't made and invents a pass/fail gate from a misread Moodley
number. Don't take its feasibility-stage design as written.

## What it got right, and worth keeping

1. **It answers your own critique's six questions** (critique §5), which the
   earlier episodes ignored.
   - **Q1, rare classes:** it states the magnetite collapse correctly (1.84% of
     pixels, IoU 0.000, critique §1.1) and gives the right answer: it won't
     transfer as is. The fix is correlative QEMSCAN labels with heavy
     oversampling of rare phases (arXiv 2505.17008).
   - **Q3, placeholder thresholds:** it names them correctly. `PAYLOAD_FLOOR`
     (0.003), `REJECT_CEILING` (0.60) and `DELETERIOUS_CEILING` (0.05) are all
     marked "UNSOURCED placeholder" in `src/advisor.py`. Its answer is the right
     one: stop defending them as physics and make them **plant-configurable
     settings** that the host metallurgist sets per campaign and smelter penalty.
   - **Q4, band width:** "calibration, not ignorance". It converts invisible
     errors into flagged ones (but see the errors below).
   - **Q5, shift setpoints:** the strongest idea in the episode. **Aggregate
     section results over a shift into a rolling, trend-based advisory**, not a
     per-section instruction. This answers critique §2.4.
2. **Chromite first.** If KHANYA can't separate chromite from payload in UG2,
   nothing else on the roadmap matters. Correct. And sharper than the episode
   knew: **LumenStone S2 has no chromite class at all** (ccp, mag, po, pn,
   background), and `MINTEK-FIT.md` already says "we cannot claim chromite". A
   chromite class has to be trained from new UG2 labels.
3. **Order of work.** Physical validation on real ore before chasing new
   architectures. Spend the R210,000 on physical validation, not simulation.
4. **Same-section comparison.** Image the same UG2 and Merensky sections
   optically and with QEMSCAN, so any difference is the instrument, not the
   sample.
5. **Honest caveat on sources.** It flagged that some cited work is not yet
   established. Lee and Lee 2026 is a three-page proceedings paper (PMLR 329,
   1043–1045), and we read only Kabemba 2026's abstract. Campo 2026 is a
   master's thesis, not a conference abstract as the episode said.

## Errors to correct

| Claim in the episode | What the sources say |
|---|---|
| "They fixed the leaked conformal band using split conformal calibration on held-out sections" | **Not done.** The rebuttal *conceded* the leak and said you'd stop calling it a guarantee. The band is still calibrated by leave-one-out on the same 12 test sections. This is the most important error: don't let anyone repeat it. |
| The 0.335 band is "a mathematically guaranteed confidence interval"; zero unsafe flips mean the math "guarantees" no dangerous advice | No guarantee. The band is leaked and coverage is unproven for new ore. Zero unsafe flips is a **measured result on 12 sections**. |
| "Boundaries are blurry … marker-controlled watershed is urgently needed" | **Already built.** Watershed and hole filling are in the pipeline (`STATUS.md` §5c). In §5c that repair, not better segmentation, is what made the liberation estimate track the truth. The width of the band comes from 12 calibration sections and leave-one-out, not from missing watershed. |
| Pass/fail gate: KHANYA's recovery estimates must stay within **0.440 pp** of QEMSCAN's | A misread. 0.440 pp is the largest change in the **bornite** contribution when Moodley varied his own residual weights by ±25% (Table 11), on a **copper** ore. It measures the model's numerical sensitivity, not an accuracy tolerance. The episode also said this shows outputs are "highly sensitive"; Moodley's conclusion is the opposite (comparatively stable). A defensible gate needs a UG2 basis: for example, no larger than the difference between replicate QEMSCAN runs on the same block. |
| Mintek co-authorship needs "zero hallucination on chromite" | No classifier reaches zero error. A testable gate: chromite modal abundance and liberation classes within an agreed tolerance of QEMSCAN on held-out UG2 blocks. |
| KHANYA gives "near real-time" turnaround against hours for SEM | Both need a polished section, which takes hours to prepare. KHANYA saves analysis time and instrument cost, not preparation time. At-line rapid sectioning, or belt sensing, is what would make it real time. |
| "$210,000" and "$10.69 to $13.15 million" | **Rand**: R210,000 for the feasibility stage and R10.69–13.15m for the pilot. It said R210,000 correctly once, then dollars. |
| Published benchmark is higher because it "didn't penalise topological boundary precision" | A guess. Your own answer (critique §1.2) is whole-section, native-resolution evaluation with no void-border inflation and a different task framing. The critique also notes the authors' pretrained baseline is a pip install: run it. |
| "2D inevitably overestimates liberation" (Reyes 2017, Guntoro 2021) | Too blunt again. 2D sections tend to overstate the extreme classes and understate middlings. |
| "Sibisusu Kumalo", "Latabo Hawani", "Kanya/Konya", "Norwell's", "Toswold Moodle", "Pireya", "Kebemba" | Speech slips for Sibusiso Khumalo, Lethabo Hoaeane, KHANYA, Norilsk, Taswald Moodley, Pereira, Kabemba. |

## Actions for the team

1. **Make the three thresholds plant-configurable**, with a stated default and
   a note that the host metallurgist owns them. Small code change, big answer
   to critique Q3.
2. **Add a shift-level aggregate**: rolling recommendation over a shift's
   sections, with the per-section results behind it. Answers critique Q5.
3. **Plan the chromite class.** It needs UG2 labels; it is the first thing the
   QEMSCAN-paired data must cover.
4. **Recalibrate the band on sections that are not the test set** once more
   labelled sections exist, then measure coverage. Until then, never call it a
   guarantee.
5. **Run the LumenStone authors' pretrained baseline** (`petroscope`) and
   report it beside yours. That is cheaper than arguing about critique Q2.
6. **Define the feasibility gate from UG2 replicate variance**, not from
   Moodley's copper weighting sensitivity.

## Line to add to the next NotebookLM prompt

```text
Facts to respect: the conformal band leak is conceded but NOT fixed; the 0.335 band is still calibrated on the same 12 test sections, so it is not a guarantee. Marker-controlled watershed and hole filling are already in the pipeline (STATUS.md 5c). LumenStone S2 has no chromite class. Moodley's 0.440 pp is the bornite contribution's sensitivity to ±25% residual weighting on a copper ore, not an accuracy tolerance. Polished sections take hours to prepare for both QEMSCAN and KHANYA. All money is in rand: R210,000 feasibility stage, R10.69–13.15m pilot.
```
