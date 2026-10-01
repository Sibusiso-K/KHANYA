# REEFPRINT / KHANYA promo: narration script

Voice: en-GB-RyanNeural (Microsoft neural TTS via edge-tts), rate +6%; 'bakkie' spoken as 'bucky'. Full cut runtime 224.4 s.

- **0:01.3** (n01) Every shift on a mine starts with the same question.
- **0:05.5** (n02) What is actually in the ore we're sending to the plant today?
- **0:09.4** (n03) Geologists log the core, and a handheld XRF reads the elements: nickel, copper, chrome, sulphur.
- **0:16.9** (n04) But elements are not minerals. XRF can't tell you which mineral carries the nickel, or whether that grain will float free, or stay locked in rock.
- **0:26.7** (n05) That answer lives in the grains. So a polished section goes under a reflected-light microscope,
- **0:33.2** (n06) and the image goes to REEFPRINT.
- **0:35.9** (n07) Open it on a laptop in the bakkie. On a phone at the core yard. At a desk in the plant office.
- **0:43.7** (n08) This is REEFPRINT, also known as KHANYA. Mineral intelligence from a micrograph.
- **0:51.8** (n09) The dashboard puts the specimen library, model readiness and recorded evidence in one view. These are held-out LumenStone S2 sections: public data, from nickel, copper and PGE sulphide ore.
- **1:04.7** (n10) Choose a section and run the analysis. A DeepLabV3 network classifies six fields on an ordinary laptop CPU. No cloud, no GPU. Every tile you see is real model output, sped up here.
- **1:19.3** (n11) Deliverable one: mineral phases. Pyrrhotite, pentlandite and chalcopyrite, mapped pixel by pixel, with the area fraction of each.
- **1:28.9** (n12) Every result carries its model, its checkpoint hash and its runtime. Confidence is shown, and labelled uncalibrated, because it is.
- **1:38.0** (n13) Click any grain for its size, its composition, and whether the valuable mineral is free, or locked. That's liberation: the question a metallurgist actually asks.
- **1:48.6** (n14) Attach an XRF or lab assay to compare the chemistry with the phase map. XRF measures elements. REEFPRINT maps minerals.
- **1:58.1** (n15) Deliverable two: the accuracy report, bound to the exact checkpoint. Across twelve held-out sections, mean IoU is 0.454, and pixel accuracy seventy-seven percent. Magnetite scores zero, and the report says so.
- **2:14.4** (n16) A retrained candidate records 0.632 on the same twelve sections, and now finds most of the magnetite, but with too many false alarms. So it stays quarantined, and the live model is unchanged.
- **2:27.6** (n17) Deliverable three: from mineralogy to a plant parameter. The advisory reads a forty-one percent sulphide association, inside the uncertainty band around the fifty percent floor. So it says: verify before acting.
- **2:41.4** (n18) Test the setpoint in the simulator. This checkpoint isn't approved for control, so the setting is held. When the evidence is thin, REEFPRINT refuses, rather than guesses.
- **2:53.5** (n19) Every decision exports as a traceable record: the result, the checkpoint, and the simulator's response.
- **3:00.4** (n20) Spatial ties samples to survey coordinates, plan maps, sections and 3D, with synthetic geometry clearly marked as synthetic.
- **3:08.9** (n21) And the evidence companion answers questions about the selected result, labelling what's measured, what's predicted, and what's simulated.
- **3:17.4** (n22) The same workbench, in your pocket.
- **3:21.4** (n23) Three mineral phases identified. An accuracy report, with every number traced. And a path to the plant that knows when not to act.
- **3:31.4** (n24) REEFPRINT. Built by Team Sonar.

90-second cut uses n01, n02, n05, n06, n08, n10s, n11, n15s, n18s, n23, n24.

## Scene timeline (full cut)

- A1 aerial: 0.00s, 5.60s (cine)
- A2 haul: 5.20s, 4.40s (cine)
- A3 helmet: 9.20s, 4.60s (cine)
- A4 xrf: 13.30s, 13.63s (cine)
- A5 lab: 26.43s, 3.60s (cine)
- A6 scope: 29.63s, 3.50s (cine)
- A7 micrograph: 32.73s, 3.30s (cine)
- A8 triptych: 35.58s, 8.20s (cine)
- A9 title+laptop: 43.33s, 8.60s (cine)
- B1 dashboard: 51.43s, 13.40s (ui)
- B2 run: 64.38s, 15.20s (ui)
- B3 phases: 79.13s, 10.00s (ui)
- B4 provenance: 88.68s, 9.60s (ui)
- B5 grains: 97.83s, 11.00s (ui)
- B6 assay: 108.38s, 9.90s (ui)
- B7 report: 117.83s, 16.80s (ui)
- B8 candidate: 134.18s, 13.60s (ui)
- B9 advisory: 147.33s, 14.30s (ui)
- B10 simulator: 161.18s, 12.60s (ui)
- B11 export: 173.33s, 7.30s (ui)
- B12 spatial: 180.18s, 9.00s (ui)
- B13 assistant: 188.73s, 8.80s (ui)
- B14 phone: 197.08s, 4.40s (cine)
- C1 montage: 200.98s, 10.40s (cine)
- C2 end: 210.78s, 6.20s (card)
- C3 disclose: 216.38s, 8.00s (card)
