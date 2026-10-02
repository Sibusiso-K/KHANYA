# REEFPRINT / KHANYA: demo video v8 (2:25), storyboard and provenance

**Plays on slide 8 of the deck** (`presentation/output/REEFPRINT-KHANYA-Team-Sonar-pitch-v8.pptx`).
- **Files:** `presentation/video/REEFPRINT-v8-demo.mp4` (1080p) and `REEFPRINT-v8-demo-embed.mp4` (1600 px, for the deck).
- **Built by:** `presentation/video/src_v8/`:
  - `make_vo_v8.py` makes the narration;
  - `capture_v8.py` records the real app;
  - `compose_v8.py` composites the frames and mixes the sound.

**Arc:** the pit → the wait (the problem) → the app (the solution, real screens) → the money → Mintek's values → an inclusive, forward-looking close.

## What is real, and what is illustrative

| Element | Status |
|---|---|
| Mine, haul truck, miner, lab, microscope, office and plant scenes | **Illustrative stock footage, Mixkit free licence.** Every stock shot carries an on-screen "ILLUSTRATIVE STOCK · MIXKIT" label. These are not South African sites, and the people are not users. The raw clips stay out of git (the licence forbids redistributing them standalone). |
| Every app screen (Live scan, Decisions, the decision record, Evidence, Value) | **The real REEFPRINT Live app** (`app_server.py`, guest sandbox, 127.0.0.1:8531), recorded by Playwright on 2 Oct 2026. Labelled "REAL APP · REPLAYED PUBLIC DATA (HIDSAG, CC0)". The approval, the note, Verify chain and the signed checkpoint download are real actions on the sandbox ledger. |
| KHANYA phase overlay | The real KHANYA workbench result on held-out LumenStone S2 test_11 (`handover/real-result-refined.png`): pyrrhotite 60.8%, pentlandite 34.7%, chalcopyrite 0.2%, 78.5 s on a laptop CPU. |
| "RESULT PENDING · 48 h" chip | **A motion graphic** illustrating the wait. It is not a measured turnaround. |
| 24–72 h fire assay | [S] (search-sourced; see docs/17). |
| US$1,500 QEMSCAN | Saskatchewan Research Council price list, 4/2017 [P]. |
| 18.5 kt | Computed: Zondereinde-size plant at 2.25 Mt/yr (indicative [S]) × 72 h. Continuous milling ASSUMED (`training/economics-20261002`, V6). |
| +1.9%, no more overloads | **Simulated** on 146 real held-out HIDSAG samples (sim_). Provisional; a pilot confirms it. Said in the narration. |
| R64–153M | ASSUMED payability and net price (economics V1); said in the narration and tagged on screen. |
| Mintek values and quote | Mintek Shareholder Compact 2023 [P]. |
| Mintek and TIA on the end card | **Named as pathway partners we are asking to work with. No partnership or funding exists**, and the end card says "we are asking". Official logo files are not used: the team has not supplied them, and we do not download third-party logos. To add them, drop the official PNGs into `src_v8/` and draw them in `end_ov()`. |
| REEFPRINT mark | The app's own layered mark, redrawn. |
| Narration | Synthetic voice: Microsoft `en-GB-RyanNeural` via `edge-tts`. "KHANYA" and "REEFPRINT" are respelled for the voice; the captions keep the real spelling. |
| Music | Original, synthesised from scratch (`../src/make_music.py`); no samples. |
| Captions | Burned in, from the narration text. |

## Shot list (times from `out/timeline_v8.json`)

| Time | Shot | Narration | On screen |
|---|---|---|---|
| 0:00 | Aerial open pit, slow push-in (Mixkit 45821) | "Every shift, thousands of tonnes of ore leave the pit and head for the mill." | stock label |
| 0:06 | Haul truck (45822) | "Inside every load is a story: how hard it will be to grind, and where the metal is hiding." | |
| 0:12 | Miner in PPE (45753) | "The people who run the plant have to read that story in minutes." | |
| 0:17 | Lab technician (4767) | "But the answer comes from the lab. A fire assay takes one to three days." | **24–72 h** · SOURCE [S] |
| 0:23 | Microscope close-up (47783) | "A full mineral analysis costs fifteen hundred dollars a sample, and takes days." | **US$1,500** · SRC 2017 |
| 0:30 | Office, waiting (42664) → haul road (45825) | "So the plant is set blind. By the time the answer arrives, up to eighteen thousand tonnes have already gone through the mill." | RESULT PENDING (graphic) → **18.5 kt** · ASSUMPTION |
| 0:39 | Brand card | "REEFPRINT changes the order. See the ore first. Then decide." | REEFPRINT · "See the ore first. Then decide." |
| 0:46 | **Real app:** Live scan, the belt building line by line, then a push-in to the scan and the hardness card | "A hyperspectral camera scans each parcel on the belt. The model predicts how hard it will be to grind, with an honest upper bound, in under a tenth of a second." | REAL APP label |
| 0:57 | **Real app:** Decisions, 98.2% proposal, "awaiting approval", countdown | "That bound becomes a feed-rate proposal, inside limits the site has approved." | |
| 1:03 | **Real app:** a note typed, Approve proposal clicked | "The metallurgist has ninety seconds… Do nothing, and the safe setting applies by itself." | |
| 1:15 | **Real app:** Verify chain → "Chain intact"; Signed checkpoint downloaded (Ed25519 + ML-DSA-65) | "Every decision is hash-chained and signed with post-quantum cryptography, so nobody can quietly rewrite what happened." | |
| 1:23 | **Real KHANYA** phase overlay, push-in to the phase composition | "In the lab, KHANYA reads a polished section in about eighty seconds: pyrrhotite, pentlandite and chalcopyrite, pixel by pixel." | REAL APP · KHANYA label |
| 1:32 | **Real app:** Evidence, "Is it physically possible?", pan from the claims to their status (a rejected row is visible) | "And every claim is tested against its physics. The ones that failed stay on the page." | |
| 1:39 | **Real app:** Value, the +1.9% / 6.8% vs 8.9% cards and the policy chart | "Replayed on a hundred and forty-six real samples… Simulated, and waiting for a pilot." | |
| 1:52 | Concentrator towers (4380) | "At one South African concentrator, a single recovery point is worth sixty-four to a hundred and fifty-three million rand a year, on assumed prices." | **R64–153M** · ASSUMPTION |
| 2:02 | Mintek values card; the five values appear one by one, Integrity highlighted | "Mintek's values ask us to do what we say we will do. So every number here carries its source." | quote + five values |
| 2:10 | Aerial pit → end card | "The next generation of metallurgists, from Rustenburg to Steelpoort, on a laptop or a phone, won't wait three days to know their ore. They'll read it on the belt." | "Read the ore on the belt." · team · hackathon · "Pathway partners we are asking to work with: Mintek · TIA" |
| 2:21–2:25 | End card hold, fade to black | (music resolves) | |

## Rebuild

```bash
python presentation/video/src_v8/make_vo_v8.py
```

```bash
python presentation/video/src_v8/capture_v8.py
```

```bash
python presentation/video/src_v8/compose_v8.py
```

`capture_v8.py` needs the secure app on port 8531 (`python presentation/belt-monitor/app_server.py`).
Re-run it after any app change, so the video shows the current build.
`compose_v8.py --preview 30,60,90` writes stills for checking.
The stock clips are read from `REEF_STOCK`; download them from Mixkit by the IDs above if they are missing.

## Known limits

- The guest sandbox ledger shows earlier test rows from the same day. It resets daily.
- App text is small at 1080p; the zoom regions keep the action readable, and the narration carries the meaning.
- The phone/QR beat is not in this cut. The public deployment needs the team's decision on host and account (`belt-monitor/deploy/RUNBOOK.md`); add a 5-second phone beat once the QR URL is live.
