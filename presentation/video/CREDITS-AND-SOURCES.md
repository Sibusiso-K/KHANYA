# REEFPRINT / KHANYA promo video: credits, sources and limits

Made 1 October 2026 for the Mintek–SCi Grad Hackathon final. This file is the provenance record for
every element of the video. Read it before you show the video or answer a judge's question about it.

## What is real, and what is illustrative

| Element | Status |
|---|---|
| Mine, haul truck, miner, lab, microscope, bakkie, phone, office, plant scenes | **Illustrative stock footage** (Mixkit, free licence). The people shown are not REEFPRINT users, customers or pilot sites. Every such shot carries an on-screen "ILLUSTRATIVE STOCK FOOTAGE · MIXKIT" label. |
| XRF element tiles (Ni, Cu, Cr, S) | Motion graphic. **No XRF measurement is shown and no element values are claimed.** |
| Pentlandite highlight in the "elements are not minerals" beat | Real output of the active model (`fb78727d`) on LumenStone S2 `test_11`. It is labelled on screen as a model prediction. |
| Micrograph push-in | Real public image: `demo-images/test_11.jpg`, LumenStone S2. |
| Laptop and phone screens | Real REEFPRINT UI screenshots, keyed into green-screen stock clips. |
| Every app screen in Act 2 | Real REEFPRINT / KHANYA workbench (`codex/launch-live-demo` @ `2b763b2`), local server on port 8510, captured headless at 1920×1080 on 1 Oct 2026 between 03:00 and 03:30 SAST. |
| Live-analysis time-lapse | A **real, fresh** six-field CPU inference on `test_11`. 278 screenshots over 220 s; the run finished in about 91–98 s (the app reports runtime 98.2 s). Played at about 10× and labelled "TIME-LAPSE". |
| Accuracy figures | Read from the app's recorded evaluation: mean IoU 0.454, pixel accuracy 77.2 %, magnetite IoU 0 (active `fb78727d`, 12 held-out S2 sections). |
| Retrained candidate | `42646cfa`: mIoU 0.632 and pixel accuracy 85.5 % on the same 12 sections; magnetite recall 89.3 % but precision 25.5 %. **Quarantined, not deployed.** The narration calls 0.632 a recorded figure, not an improvement, because the historical approved model still beats it on pyrrhotite and pentlandite. |
| Simulator | Local simulator only. The screen shows "Checkpoint is not approved for demo control. Setting held." (0 → 0). No live plant, and no recovery gain is claimed. |
| Spatial 3D, plan and section | The app's opt-in **synthetic** demo scene, labelled "Synthetic scene · not measured data" on screen. |
| Narration | Synthetic voice: Microsoft `en-GB-RyanNeural` via `edge-tts` (British English; the first cut used `en-ZA-LukeNeural`, kept in `luke-voice/`). |
| Music and sound effects | Original, synthesised from scratch in NumPy for this video (`make_music.py`). No samples. |
| Typeface | Public Sans (SIL Open Font License), the same face the app uses. |

## Stock clips (Mixkit, "Mixkit Stock Video Free License", checked per clip on 1 Oct 2026)

| Mixkit ID | Title | Used for |
|---|---|---|
| 45821 | Aerial shot of a huge quarry mine being excavated | opening pan; closing montage; phone background |
| 45822 | Mineral resources being removed from a quarry site | haul truck |
| 45753 | Man in a helmet crossing his arms confidently | miner in PPE |
| 32990 | Cave with golden metallic minerals | XRF beat background (darkened) |
| 4767 | Scientist in a laboratory preparing a sample | lab |
| 47783 | Scientist working with the microscope | microscope close-up |
| 40069 | Man driving down a dirt road in a small pickup | "in the bakkie" |
| 24078 | Young construction worker talking on the phone | "at the core yard" |
| 42664 | Professional woman working in an office | "in the plant office" |
| 48285 | Laptop with a green screen slide-in | laptop with the real dashboard keyed in |
| 28300 | Hands using a cellphone with tracking point on a green screen | phone with the real mobile UI keyed in |
| 4380 | Towers and steam outlets of an industrial plant | closing montage |
| 45825 | Aerial view of a truck driving along a long road in a mine | closing montage |

Source pages: `https://mixkit.co/free-stock-video/<slug>-<id>/`. Licence: https://mixkit.co/license/#videoFree.
Mixkit's free licence allows use in a video project without attribution. The clips themselves must not be
redistributed standalone, so the raw clips are kept out of git and out of this folder.

## Known limits of the video

- At 3:44 the full cut is longer than the deck's 90-second demo slot; slide 7 embeds `REEFPRINT-promo-90s-embed.mp4` (the 1:32 cut, compressed).
- Captions are burned in, and also supplied as `REEFPRINT-promo.en.srt`.
- Stock scenes are not South African sites. The narration names the bakkie, the core yard and the plant office as places the app can be opened, not as places shown.
- The phone beat shows the mobile UI **viewing** a result. A phone photograph of loose ore is outside the model's validated input, and the video never shows one being analysed.
