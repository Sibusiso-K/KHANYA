# Plan: final-day accuracy check of the REEFPRINT/KHANYA pitch before the 13:00 submission
_Round 0 — initial draft by Claude_

## Goal
Present a 10-minute PowerPoint pitch (deck v3, 20 slides) and a 1:32 demo video at Mintek today, without a single false or overclaimed statement. Mintek's own scientists are judging, and one of them co-wrote the paper used on slide 11.

## Approach (what will be presented; please verify each against the files)
1. Deck generator: `presentation/deck-src/build_deck.py` (slides are built in order; notes from `presentation/deck-src/script_notes.json`). Spoken script: `presentation/PRESENTER-SCRIPT.md`.
2. Slide 2: "Days" (Problem 3 brief), "1 week = expedited turnaround at a major commercial lab" (ALS FAQ), "$1,500 per QEMSCAN modal-mineralogy + liberation analysis" (SRC price list 2017).
3. Slide 3: SA ≈71% of 2024 world platinum mine production (USGS MCS 2025: 120,000 of 170,000 kg); ≈¾ of PGM reserves (63,000,000 of >81,000,000 kg); mining 6.1% of nominal GDP and 474,736 direct jobs in 2024 (DMPR Mining Sector Performance 2024).
4. Slide 8: active model fb78727d mean IoU 0.454, pixel accuracy 77.2%, magnetite IoU 0 (app's recorded evaluation, 12 held-out LumenStone S2 sections); candidate 42646cfa mIoU 0.632, magnetite recall 89.3%, precision 25.5%, not deployed; 98 s fresh six-field CPU run; "0 unsafe advisories vs expert-mask advice on 12 held-out sections (raw: 2); 95% upper bound 22%" (KHANYA `reports/ACCURACY-REPORT.md` §7, historical patches checkpoint).
5. Slide 10: triage = 4/12 confident answers in `reports/decision_gap_patches_refined.json` (Clopper–Pearson 95% CI 10–65%), × $1,500 per 100 samples ≈ $50,000; illustrative value = 250,000 t/month × 4 g/t × Δrecovery × R45,993 per PGM oz (Valterra H1 2026) → ≈R7.4m/month at +0.5 pp. Both labelled ASSUMPTION/ILLUSTRATIVE.
6. Slide 11 (new): test_11 grains (live result 0f041440…, 23 grains) binned into Moodley, Govender et al. (Results in Engineering 32 (2026) 112959) liberation classes by valuable-mineral AREA share (proxy for free-surface exposure); predicted recovery Σ w_c(1−e^(−k_c t)) with k_FUL 0.9097, k_LIB 6.0, k_HM 3.0, k_LM 1.0 min⁻¹ (paper Table C.14), locked → 0; ≈86% at 1 min → "add 15 s and 30 s concentrates"; "screen every timed concentrate optically" (paper future work). Data: `presentation/deck-src/kinetics_test11.json`. Slide 15 (new): measured reflectance spectra (Handbook of Mineralogy, deck-src/spectra.json) — sperrylite vs pentlandite 18.5-pt gap at 420 nm, 0.9 at 640 nm.
7. Slide 9 competitor matrix: SEM automated mineralogy (QEMSCAN/MLA/TIMA/Mineralogic), XRD, XRF, hyperspectral, flotation control e.g. Mintek FloatStar vs REEFPRINT.
8. Slides 11–17: pricing hypotheses (R210k pilot, R12k/site/month), named target companies (Valterra, Implats, Sibanye-Stillwater, Northam, ARM, Tharisa — "segments, not customers"), stack (React 19/TS/Vite, FastAPI, PyTorch DeepLabV3-ResNet50, OpenCV, asyncua OPC UA, Supabase), compliance (POPIA, MHSA, SAMREC, MPRDA, IEC 62443).
9. Theme branch `codex/themes-launch` @ 540e29f in worktree `C:/Users/USER/.codex/worktrees/reefprint-themes` — NOT deployed to the live demo.

## Key decisions & tradeoffs
- Slide 11 applies kinetic constants the authors say are NOT transferable, to a different ore (Ni-Cu-PGE sulphide analogue), using area share instead of free-surface exposure. Labelled ILLUSTRATIVE. Is that defensible in front of the author, or misleading?
- Slide 8 mixes metrics from the active checkpoint (0.454) with a refusal result from the historical patches checkpoint (decision-gap). Footnoted. Acceptable?
- "Hyperspectral" is placed in the roadmap as microscope-scale reflectance, not core-scale SWIR, because PGM grains are micron-scale and opaque.

## Risks / open questions
- Any number on a slide that does not match its cited source, or arithmetic that is wrong.
- Any sentence a Mintek mineralogist would call false (e.g. claims about QEMSCAN, FloatStar, hyperspectral, SAMREC).
- Script lines that overclaim relative to the slide text.

## Out of scope
Rewriting the deck design; new experiments; the live app's behaviour.
