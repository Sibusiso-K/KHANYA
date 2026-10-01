# REEFPRINT / KHANYA: presenter script (10 minutes)

**Deck:** `presentation/output/REEFPRINT-KHANYA-Team-Sonar-pitch-v2.pptx` (19 slides; slide 11 is new). The script below is also in each slide's speaker notes.
**Target:** 9:45 spoken, which leaves 15 s of slack. Slide 7 plays the 92-second demo video: click it once and say nothing while it runs.

**Before you start:**
- Open the deck on the presenting laptop.
- Press F5. Use Presenter View so you can see the notes.
- Test the video click once.
- Keep `presentation/video/REEFPRINT-promo-90s-british.mp4` open in a player as a backup in case the embedded video fails.

## Who says what (suggested)

| Slides | Speaker | Time |
|---|---|---|
| 1–4 (title, problem, who it affects, how it hurts) | Lethabo | 0:00–2:00 |
| 5–7 (solution, how it works, demo) | Sibusiso | 2:00–4:50 |
| 8–10 (evidence, competitors, value) | Ipeleng | 4:50–6:45 |
| 11–14 (next lab test, business, technology, accuracy engine) | Sibusiso | 6:45–8:35 |
| 15–17 (roadmap, compliance, the ask) | Lethabo | 8:35–9:45 |

## The script

**1 · Title (0:00–0:20).** Good morning. We're Team Sonar: Lethabo, Sibusiso and Ipeleng. This is REEFPRINT, which we also call KHANYA. It gives you mineral intelligence from a micrograph in near real time, and, just as important, it's honest enough to say when it doesn't know.

**2 · Problem (0:20–1:00).** Here's the problem, in the brief's own words. Laboratory SEM or XRD characterisation can take days. At a major commercial lab, one week is the *expedited* turnaround. One published price list puts a QEMSCAN liberation analysis at fifteen hundred dollars a sample. Meanwhile, ore changes by the hour. By the time the plant learns what was in its ore, that ore has already been milled and floated, and its metal is gone. Without real-time feedback, plants overspend on chemicals and lose yield.

**3 · Who it affects (1:00–1:35).** Why does this matter here? In 2024 South Africa mined about seventy-one percent of the world's platinum, and it holds about three-quarters of the world's PGM reserves. Mining is six point one percent of GDP and directly employs almost four hundred and seventy-five thousand people. When recovery drops in these flotation cells, everyone feels it: metallurgists, mineralogists buried in routine samples, operators, the companies, and the communities and the fiscus that depend on the margin per ounce.

**4 · How it hurts (1:35–2:00).** Here's how it hurts. The ore changes, and there's no feedback for days. So the grind is a guess: too fine wastes power, too coarse leaves valuable grains locked in rock. Reagents are dosed for yesterday's ore, and the locked metal goes to tailings. The plant already has the levers. What it's missing is a fast, trustworthy mineral reading that also knows when *not* to touch them.

**5 · Solution (2:00–2:40).** That's what REEFPRINT does. It takes a reflected-light micrograph of a polished section. On an ordinary laptop, in about a minute and a half, it delivers the brief's three deliverables.
- **One:** it identifies mineral phases, pyrrhotite, pentlandite and chalcopyrite, pixel by pixel.
- **Two:** it produces an accuracy report tied to the exact model checkpoint, zeros included.
- **Three:** it turns the result into a plant parameter over OPC UA. Today that goes to a simulator, and the simulator holds the setting automatically while the model isn't approved.

Around those three you also get grain liberation, XRF context, a spatial view and a phone view.

**6 · How it works (2:40–3:15).** Here's how it works. You use standard sample preparation and any lab microscope camera. First, a quality gate rejects bad images. Then there's exactly one learned stage: a DeepLabV3 network segments the mineral phases. Everything after that is deterministic and auditable:
- Grains are separated and marked free or locked.
- A conformal uncertainty band sits around every decision threshold.
- The advisor says act, verify or hold, always with a reason.
- A setpoint only moves if the model is approved, and every step is recorded.

**7 · Demo (3:15–4:50).** Let me show you the real app, running live. *[Click to play. 92 seconds. Stay silent.]*

**8 · Evidence (4:50–5:30).** Now the evidence, starting with what fails. On twelve held-out sections, our live model scores a mean IoU of zero point four five four and seventy-seven percent pixel accuracy. On magnetite it scores zero, and we show that zero. A retrained candidate reaches zero point six three two and finds eighty-nine percent of the magnetite, but only a quarter of its magnetite calls are correct, so we haven't deployed it. A fresh analysis took ninety-eight seconds on a laptop CPU. The result we're proudest of: because the system is designed to refuse, it gave zero unsafe advisories on those twelve sections. Every disagreement became a request for a human to verify.

**9 · Competition (5:30–6:05).** Who else is in this space?
- SEM automated mineralogy, meaning QEMSCAN, MLA, TIMA and Mineralogic, is the gold standard, but it sits in a central lab with a queue.
- XRD is bulk and slow.
- XRF is fast, but it measures elements, not minerals.
- Hyperspectral struggles with opaque minerals such as chromite.
- Flotation control acts in real time, but it needs a mineral signal to act on.

REEFPRINT is the only one here that identifies phases and liberation in minutes on a laptop, refuses with a reason, and drives a gated setpoint. It complements all of them: hard samples still go to QEMSCAN, and checked setpoints go to the controllers plants already run.

**10 · Value (6:05–6:45).** Why would a PGM producer want this today? For three reasons.
- **First, triage.** A third of our held-out sections got a confident optical answer. Across a hundred samples, that frees roughly fifty thousand dollars of QEMSCAN time for the hard cases.
- **Second, decisions happen inside the shift,** in minutes rather than days.
- **Third, it never acts on thin evidence.**

Now the upside. Take a typical concentrator. Our *assumption* is two hundred and fifty thousand tonnes a month at four grams per tonne. At today's basket price, every half a percentage point of recovery is worth about seven point four million rand a month. We haven't measured that gain yet. That's what the pilot is for.

**11 · Next lab test, built on the mentor's paper (6:45–7:15).** This next step is built on Mintek's own work. Moodley, Govender and colleagues showed that QEMSCAN liberation classes explain rougher flotation kinetics. REEFPRINT produces those same classes from a micrograph in minutes. Run through the paper's own rate constants, it predicts that about eighty-six percent of this sample's valuable mineral floats in the first minute, which is the interval the paper couldn't resolve. So the next lab test should add fifteen- and thirty-second concentrates, and each timed concentrate can be screened optically, which is the paper's stated future work. Those constants come from one copper ore, so this is a hypothesis to test, not a result.

**12 · Business model (7:15–7:45).** Commercially, a paid pilot costs about two hundred and ten thousand rand for eight to twelve weeks. After that, a site licence is around twelve thousand rand a month, plus a one-off deployment fee, and an enterprise tier covers multi-site operations. These prices are hypotheses to test. Customers can run REEFPRINT offline on a lab laptop, use it on a phone, or connect it to the plant through OPC UA. Our first buyers are South Africa's PGM and chrome producers, with labs such as Mintek as triage partners.

These prices are hypotheses we'll test with buyers. Customers can run REEFPRINT offline on a lab laptop, sign in from a phone, or connect it to the plant through OPC UA. Our first buyers are South Africa's PGM and chrome producers, with mineralogy labs such as Mintek as triage partners.

**13 · Technology (7:45–8:05).** On the technology side, the front end is React and TypeScript, with FastAPI and PyTorch behind it, OPC UA to the plant and Supabase for secure storage. It works offline first, runs on a CPU, is permissively licensed, and scales by adding sites, not servers.

The system works offline first, runs on a CPU, is permissively licensed with an SBOM, and scales by adding sites, not servers.

**14 · Accuracy engine (8:05–8:35).** How does accuracy keep improving? Different models are good at different minerals. The live model misses magnetite, the candidate finds it, and the historical model is best on pyrrhotite and pentlandite. So a router sends each image to specialist models, combines their answers per mineral using weights learned on validation data, and a conformal referee decides whether to answer, verify or hold. Every QEMSCAN-labelled section retrains the specialists.

Every QEMSCAN-labelled section retrains the specialists, and no model is promoted unless it holds up.

**15 · Pathway (8:35–9:05).** Here's the pathway. First, a twelve-week lab shadow pilot with QEMSCAN labels. Next, specialist models and a UG2 and chromite domain at one concentrator. After that, a flotation trial, plus QEMSCAN-labelled multispectral and hyperspectral reflectance microscopy with polarisation. Microscope-scale optics matter, because PGM grains are microns across and opaque. Every step has a hypothesis that could fail.

Every step comes with a hypothesis that could fail, and we've said how it could fail.

**16 · Compliance (9:05–9:20).** It's built for a mine's reviews: POPIA; mine safety, meaning it's advisory first and nothing moves without site authorisation; SAMREC, meaning these are process decisions, not resource statements; permissive licences; and disclosed AI assistance.

**17 · The ask (9:20–9:45).** So our ask is simple: one concentrator, one mineralogist, QEMSCAN-labelled sections and twelve weeks. In return, you get measured answers: turnaround, accuracy on your own ore, refusal rates, and the value on your own numbers. This has been REEFPRINT, also known as KHANYA. Thank you.

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
| "How is this different from QEMSCAN?" | "It isn't a replacement. QEMSCAN is the reference. We screen everything optically and send only the uncertain samples to it, and QEMSCAN maps then become our training labels." |
| "Who owns the IP?" | "Two clean git histories with dated failures. We'll follow Mintek's invention-credit process, and the shipped stack uses only permissive licences." |
| "Did you use AI?" | "Yes, coding assistants, and we disclose that (Appendix B). The problem framing, training, evaluation, measurements and failure logs are ours, and every number was checked against its source." |
| "Aren't those QEMSCAN images?" | "No. They're ordinary reflected-light micrographs from the LumenStone dataset, taken with a lab microscope camera. That's the point: optical images in minutes, with QEMSCAN kept for the samples we flag as uncertain, and QEMSCAN maps used as our training labels." |
| "Why not hyperspectral?" | "Core-scale SWIR hyperspectral identifies minerals by vibrational absorption. Opaque sulphides, chromite and micron-sized PGM grains don't give usable signals at that scale. Our roadmap is microscope-scale multispectral or hyperspectral *reflectance* with polarisation, labelled by QEMSCAN. That's the version of hyperspectral that can see PGM-bearing grains." |
| "Where do your kinetics numbers come from?" | "From your own paper, Moodley et al. 2026, Table C.14. Those constants were fitted for one copper ore and one test condition, and the authors say they're not transferable, so we show it as a hypothesis. The real value is the method: our grains drop straight into your liberation classes." |

