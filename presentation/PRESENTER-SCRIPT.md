# REEFPRINT / KHANYA: presenter script (10 minutes)

**Deck:** `presentation/output/REEFPRINT-KHANYA-Team-Sonar-pitch-v5.pptx` (21 slides: 19 main + 2 appendices; slide 3 is the QEMSCAN-vs-microscope clarification). Reviewed by a two-round ClauDex loop (Codex gpt-6-astra); see `PLAN-REVIEW-LOG.md`.
**Target:** 9:45 spoken, which leaves 15 s of slack. Slide 7 plays the 92-second demo video: click it once and say nothing while it runs.

**Before you start:**
- Open the deck on the presenting laptop.
- Press F5. Use Presenter View so you can see the notes.
- Test the video click once.
- Keep `presentation/video/REEFPRINT-promo-90s-british.mp4` open in a player as a backup in case the embedded video fails.

## Who says what (suggested)

| Slides | Speaker | Time |
|---|---|---|
| 1–5 | Lethabo | 0:00–2:05 |
| 6–8 | Sibusiso | 2:05–4:55 |
| 9–12 | Ipeleng | 4:55–7:10 |
| 13–16 | Sibusiso | 7:10–8:50 |
| 17–19 | Lethabo | 8:50–9:45 |

## The script

**1 · Title (0:00–0:20).** Good morning. We're Team Sonar: Lethabo, Sibusiso and Ipeleng. This is REEFPRINT, which we also call KHANYA. It gives you mineral intelligence from a micrograph in near real time, and, just as important, it's honest enough to say when it doesn't know.

**2 · Problem (0:20–0:55).** Here's the problem, in the brief's own words. Laboratory SEM or XRD characterisation can take days. At a major commercial lab, one week is the expedited turnaround. One published price list puts a QEMSCAN liberation analysis at fifteen hundred dollars a sample. Meanwhile, ore changes by the hour. By the time the plant learns what was in its ore, that ore has already been milled and floated, and its metal is gone. Without real-time feedback, plants overspend on chemicals and lose yield.

**3 · Not a QEMSCAN image: what's new (0:55–1:20).** Let's clear one thing up first. On the left is a real QEMSCAN image: an electron beam reads X-ray chemistry and paints every mineral a colour. It's the reference, but it's lab-bound, slow and costly. On the right is what we use: a reflected-light microscope photo of the same kind of polished section, ready in minutes on a microscope most labs already own. The new part is this. QEMSCAN maps teach our models, cheap optical and multispectral images then do the predicting, and the uncertain ones go back to QEMSCAN, which is a workflow we will validate in the pilot.

**4 · Who it affects (1:20–1:50).** Why does this matter here? South Africa mined about seventy-one percent of the world's platinum in 2024 and holds about three-quarters of its PGM reserves. Mining is six point one percent of GDP and directly employs almost four hundred and seventy-five thousand people. Lost recovery is felt by metallurgists, mineralogists, operators, companies, and the communities that depend on them.

**5 · How it hurts (1:50–2:05).** When ore changes faster than the lab can report, the grind and the reagents become a guess, and locked metal goes to tailings. What's missing is a fast mineral reading that knows when not to act.

**6 · Solution (2:00–2:40).** That's what REEFPRINT does. It takes a reflected-light micrograph of a polished section. On an ordinary laptop, in about a minute and a half, it delivers the brief's three deliverables. One: it identifies mineral phases, pyrrhotite, pentlandite and chalcopyrite, pixel by pixel. Two: it produces an accuracy report tied to the exact model checkpoint, zeros included. Three: it turns the result into a plant parameter over OPC UA. Today that goes to a simulator, and the simulator holds the setting automatically while the model isn't approved. Around those three you also get grain liberation, XRF context, a spatial view and a phone view.

**7 · How it works (2:40–3:15).** Here's how it works. You use standard sample preparation and any lab microscope camera. First, a quality gate rejects bad images. Then there's exactly one learned stage: a DeepLabV3 network segments the mineral phases. Everything after that is deterministic and auditable. Grains are separated and marked free or locked. A conformal uncertainty band sits around every decision threshold. The advisor then says act, verify or hold, always with a reason. A setpoint only moves if the model is approved, and every step is recorded.

**8 · Demo (3:15–4:50).** Let me show you the real app, running live. [CLICK TO PLAY — 92 seconds. Say nothing while it plays.]

**9 · Evidence (4:50–5:30).** Now the evidence, starting with what fails. On twelve held-out sections, the live model scores a mean IoU of zero point four five four and seventy-seven percent pixel accuracy. On magnetite it scores zero, and we show that zero. A retrained candidate reaches zero point six three two and finds eighty-nine percent of the magnetite, but only a quarter of its magnetite calls are correct, so it isn't deployed. A fresh analysis took ninety-eight seconds on a laptop CPU. And with our historical checkpoint, the refusal design produced zero policy-defined unsafe disagreements on that twelve-section benchmark. Every disagreement became a request for a human to verify.

**10 · Competition (5:30–6:05).** Who else is in this space? SEM automated mineralogy, meaning QEMSCAN, MLA, TIMA and Mineralogic, is the gold standard, but it sits in a central lab with a queue. XRD is bulk and slow. XRF is fast, but it measures elements, not minerals. Core-scale hyperspectral struggles with opaque minerals. Flotation control, such as Mintek's FloatStar, already stabilises levels and flows, and mineralogy could add a signal it doesn't have today. REEFPRINT identifies phases and liberation in minutes on a laptop, refuses with a reason, and gates any setpoint. It complements all of them, and referring only uncertain samples to QEMSCAN is a workflow we'll validate in the pilot.

**11 · Value (6:05–6:40).** Why would a PGM producer want this? First, triage. A third of our held-out sections got a confident optical answer. If a pilot proves those answers can safely replace the lab analysis, that's roughly fifty thousand dollars per hundred samples at a 2017 list price. Second, decisions happen inside the shift. Third, it never acts on thin evidence. Now the upside. On our assumed concentrator, two hundred and fifty thousand tonnes a month at four grams per tonne, at Valterra's reported H1 2026 basket price, every half a percentage point of recovery is worth about seven point four million rand a month. We haven't measured that gain. The lab pilot measures accuracy and turnaround; recovery needs a later, controlled flotation trial.

**12 · Next lab test (mentor's paper) (6:40–7:10).** This slide builds on Mintek's own paper. Moodley, Govender and colleagues tied QEMSCAN liberation classes to rougher flotation kinetics. We bin our grains with their class boundaries, using area share as a proxy. Their constants come from a different ore, so this is a hypothetical curve, not a prediction. Even so, it says most of the valuable mineral could float in the first minute, which is the interval their test couldn't resolve. So the next test should add fifteen- and thirty-second concentrates, and each timed concentrate should be screened optically, which is their stated future work.

**13 · Business model (7:10–7:40).** Commercially, there's a paid pilot of about two hundred and ten thousand rand, then a site licence of around twelve thousand rand a month plus a one-off deployment fee. These prices are hypotheses we'll test. REEFPRINT runs offline on a lab laptop, works on a phone, and connects to the plant through OPC UA. First buyers are South Africa's PGM and chrome producers, with labs such as Mintek as triage partners.

**14 · Technology (7:40–8:00).** The technology is React and TypeScript in front, FastAPI and PyTorch behind, OPC UA to the plant and Supabase for storage. It's offline first, runs on a CPU, and is permissively licensed.

**15 · Accuracy engine (8:00–8:25).** Different models are good at different minerals. The live model misses magnetite, the candidate finds it, and the historical model is best on pyrrhotite and pentlandite. So next, a router will send each image to specialist models, combine them per mineral with weights learned on validation data, and let a conformal referee decide whether to answer, verify or hold. Two new ensemble members are training on Kaggle right now.

**16 · Spectral imaging at the right scale (8:25–8:50).** This is spectral imaging at the scale where platinum lives. These are reference reflectance spectra. At four hundred and twenty nanometres, sperrylite, a platinum arsenide, is eighteen points brighter than pentlandite, but at six hundred and forty they're almost identical. That suggests a few narrow colour bands through the microscope could separate platinum minerals. We still have to test it on real sections. Our build is multispectral reflectance microscopy with a polariser, labelled pixel for pixel by QEMSCAN maps of the same sections.

**17 · Pathway (8:50–9:10).** The pathway: a twelve-week lab shadow pilot with QEMSCAN labels, then specialist models and a UG2 and chromite domain at one concentrator, then a flotation trial with the spectral microscope. Every step has a hypothesis that could fail.

**18 · Compliance (9:10–9:22).** It's built for a mine's reviews: POPIA, mine safety with an advisory-first design, SAMREC with process decisions rather than resource statements, permissive licences, and disclosed AI assistance.

**19 · The ask (9:22–9:45).** So our ask: one concentrator, one mineralogist, QEMSCAN-labelled sections and twelve weeks. In return, you get measured answers: turnaround, accuracy on your own ore, refusal rates, and value on your own numbers. This has been REEFPRINT, also known as KHANYA. Thank you.

## Facts to have ready if asked

| If they ask… | Say |
|---|---|
| "How do you get a reflected-light image?" | "Crush a sample, set it in epoxy, then grind and polish the face. That's the same polished section QEMSCAN uses. Put it under a standard ore microscope with a camera. Prep is the slow part, and imaging takes minutes." |
| "Is it cheap?" | "Most metallurgical labs already own the microscope. The marginal cost is the polished section, which QEMSCAN needs too. The QEMSCAN analysis step itself listed at $1,500 per sample on one 2017 price list." |
| "What's the difference from QEMSCAN?" | "QEMSCAN is an electron microscope. It reads each spot's X-ray chemistry, so it identifies minerals by composition down to microns, but it's slow and expensive. Today we analyse reflected-light colour images, which is faster and cheaper but less certain. Polarisation and extra colour bands are proposed. We refuse when we're unsure, and referring those samples to QEMSCAN is a workflow we still have to validate." |
| "Is anything training now?" | "Yes. Two ensemble members, an FCN and a DeepLab, launched on Kaggle at 11:53 under a pre-registered protocol. Selection uses validation data only, with no test-set use and no automatic deployment." |

## User journey (a fictional example, for Q&A or if asked "who uses it?")

> **06:00.** The shift starts. Naledi, a concentrator metallurgist (a fictional example), hears the feed is coming from a new stope.
> **06:20.** The lab technician prepares a polished section and captures a reflected-light image.
> **06:22.** REEFPRINT analyses six fields on the lab laptop. The result: pyrrhotite 61%, pentlandite 35%. Grain 4 is free, and several smaller grains are locked.
> **06:24.** The advisory reads "Marginal: verify before acting". Association is 41%, inside the uncertainty band around the 50% floor. Naledi sends *that* section to the QEMSCAN priority queue and asks for one more field.
> **06:40.** The next section comes back confident: grind finer. She reviews it and approves. The setpoint goes through OPC UA under site rules, and the decision record is exported to the shift report.
>
> Without REEFPRINT, both sections wait days in the same queue.

## Q&A crib: the honest answers

| If they ask… | Say |
|---|---|
| "Magnetite is zero?" | "Yes, on the live model. It's a low-reflectance-contrast phase against resin. The dataset's own authors report 0.65, the hardest of their ten classes. Our candidate finds 89% of the magnetite, but it isn't precise enough to deploy, so it's quarantined. QEMSCAN-labelled sections are the fix." |
| "This is Norilsk, not UG2." | "Correct. It's an assemblage analogue for Bushveld base-metal sulphides, not an abundance analogue, and we have no chromite data. That's exactly why the pilot asks for QEMSCAN-labelled Bushveld sections." |
| "Is it really real time?" | "Image to decision is about a minute and a half on a laptop CPU. The real bottleneck is sample preparation, so the first win is the lab queue, and side-stream imaging comes later." |
| "Can I just take a phone photo of ore?" | "Not today. The model is validated on reflected-light micrographs of polished sections. A phone photo of a rock is a different input, and the quality gate should refuse it. Phones are for *viewing* results." |
| "Have you changed a real plant?" | "No. Plant actions run in a local simulator over real OPC UA. The live model isn't approved for control, so the setting is held. That's the design working." |
| "Why trust the 0.632?" | "We don't deploy it yet. It's a fixed regression check on historically reused test images, it's one training seed, and the historical model still beats it on pyrrhotite and pentlandite." |
| "Where does the R7.4 million come from?" | "It's illustrative arithmetic: 250,000 t a month at 4 g/t, plus 0.5 percentage points of recovery, at Valterra's H1 2026 basket price of R45,993 per ounce. Every input is labelled. We have measured no recovery change." |
| "How is this different from QEMSCAN?" | "It isn't a replacement. QEMSCAN is the reference. We propose screening optically and referring uncertain samples to it, a workflow we'll validate prospectively, and QEMSCAN maps become our training labels." |
| "Who owns the IP?" | "Two clean git histories with dated failures. We'll follow Mintek's invention-credit process, and the shipped stack uses only permissive licences." |
| "Did you use AI?" | "Yes, coding assistants, and we disclose that (Appendix B). The problem framing, training, evaluation, measurements and failure logs are ours, and every number was checked against its source." |
| "Aren't those QEMSCAN images?" | "No. They're ordinary reflected-light micrographs from the LumenStone dataset, taken with a lab microscope camera. That's the point: optical images in minutes, with QEMSCAN kept for the samples we flag as uncertain, and QEMSCAN maps used as our training labels." |
| "Why not hyperspectral?" | "Core-scale SWIR hyperspectral identifies minerals by vibrational absorption. Opaque sulphides, chromite and micron-sized PGM grains don't give usable signals at that scale. Our roadmap is microscope-scale multispectral or hyperspectral *reflectance* with polarisation, labelled by QEMSCAN. That's the version of hyperspectral that can see PGM-bearing grains." |
| "Where do your kinetics numbers come from?" | "From your own paper, Moodley et al. 2026, Table C.14. Those constants were fitted for one copper ore and one test condition, and the authors say they're not transferable, so we show it as a hypothesis. We bin our grains with your class boundaries using area share, which is a proxy we still have to validate against your free-surface exposure. The value is designing the next test, not predicting this ore." |

