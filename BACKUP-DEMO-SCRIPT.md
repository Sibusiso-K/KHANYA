# Backup demo recording script

ENDGAME.md W7: "Record the working demo. If the laptop dies on stage, the talk
survives. Do it the moment W3 is green, not at the end." This file exists
because that recording has not been made yet (checked 2026-09-14) - it is the
exact, rehearsed sequence to follow, using real images with real, already-
verified results, so whoever records it does not have to improvise or guess
what will happen.

REEFPRINT already has its own backup asset (`reefprint.viz.demo`, a backup
GIF - see WORKBOARD.md §2). This is KHANYA's equivalent.

## Before recording

0. **`.venv\Scripts\python.exe -m src.preflight` must print `READY TO PRESENT`.** It
   checks the S2 checkpoint's sha256, the held-out data, a strict model load and
   a real OPC UA command round trip. Since 29 September two different S2
   checkpoints exist under the same filename (the Kaggle retrain scores 0.4543);
   every number below belongs to sha256 `de7135a9...` only.
1. `cd KHANYA && .venv\Scripts\python.exe -m streamlit run dashboard\app.py --server.port 8501`
   (same command as `.claude/launch.json`'s `khanya-advisor` config).
2. **Before anything else, confirm `asyncua` actually imports in THIS
   venv**: `.venv\Scripts\python.exe -c "import asyncua"`. `requirements.txt`
   listing a package is not the same as the venv the demo command runs
   under actually having it installed (entry 59 found exactly this gap on
   2026-09-14 - `pip install` into the wrong Python left the dashboard
   showing "OPC UA · UNAVAILABLE" live). If it fails: `.venv\Scripts\
   python.exe -m pip install -r requirements.txt` into this exact venv,
   then re-check. Confirm by uploading one test image and reading the OPC
   UA line on the result - it must say "PUBLISHED + ACKNOWLEDGED", not
   "UNAVAILABLE".
3. Confirm the venue laptop's wifi is OFF before starting - this is the actual
   claim being demonstrated (`STATUS.md`, the offline-network CI guard).
4. Have these three files ready in one folder, already renamed something a
   viewer will recognise as arbitrary (not `test_01.jpg` - a judge should not
   read that as "cherry-picked from the training author's own test set" even
   though it correctly is a held-out image the model never trained on):
   - `data/raw/lumenstone/S2_v2/imgs/test/test_01.jpg` -> confident state
   - `data/raw/lumenstone/S2_v2/imgs/test/test_04.jpg` -> marginal state
   - `data/raw/lumenstone/S1_v2/imgs/test/test_02.jpg` -> low-payload refusal
     challenge (this is a different LumenStone subset, S1 not S2, fed to the
     S2-trained model; it is not a corrupted or fake image. KHANYA currently
     has no validated image-level OOD detector, so do not call this an OOD
     detection demonstration.)
5. **Upload each once before recording**, so Streamlit's cache is warm and
   the recorded run doesn't sit on a multi-minute spinner. Confirm each
   produces the expected result below before recording starts.

## The sequence to record

### Beat 1 — confident state (test_01.jpg)

Upload. Expected, exact (verified 2026-09-13/14, this checkpoint): **95%
association index, 78% model confidence, 35% ore in field, 181 particles,
"Continue at current setpoint"**. Scroll to show the side-by-side input/
predicted-phase panel and the modal mineralogy breakdown (Pentlandite 51.3% /
Chalcopyrite 37.2% / Pyrrhotite 11.5% / Magnetite 0.0%).

### Beat 2 — marginal state (test_04.jpg)

Upload. Expected: **74% association index, 82% confidence, 170 particles,
amber "VERDICT STATE: MARGINAL, VERIFY BEFORE ACTING" / "Marginal - verify
before acting"**. Scroll to show the two-candidate breakdown ("if true
liberation >= 50%" / "if true liberation < 50%") and the liberation-vs-
threshold bar with the uncertainty band visible.

### Beat 3 — the low-payload refusal (test_02.jpg, S1 on the S2 model)

**This is the beat the talk is built around (ENDGAME.md §5, beat 6).** Say
out loud before uploading: "this next image is a cross-dataset challenge from
a different LumenStone subset. The model was not trained on it; the current
prototype is testing the measured payload rule, not claiming OOD detection."
Upload. Expected: **2% association index, 74% confidence,
272 particles, amber "MEASUREMENT DECLINED" / REFUSAL, "Flag for manual
review - low payload signal", "Payload phases occupy 0.296% of ore area,
below the 0.300% floor."** The predicted-phase panel will show almost
entirely black/background - point at it. This is the moment the advisor
declines to issue a normal recommendation because the model's predicted
payload signal is below its configured floor. It does not prove that the
model recognised the input as out of domain.

### Beat 4 — guarded vs unguarded on the same section (Live sampled fields)

The brief asks to see the model's output adjust a plant parameter. The strip at
the top of each result shows the **simulated circuit**: one illustrative tag,
`regrind_enabled` (1 = regrind, 0 = bypass), commanded over a real local OPC UA
exchange. Only *Grind finer* commands it. *Continue at current setpoint* changes
nothing (**UNCHANGED**). Every refusal **HOLDS**.

The visible toggle **Simulated lighting-perturbation check** switches the guard.
When ON, a confident recommendation is issued only if it is unchanged on a copy
of the image with a fixed RGB offset (R -34.8, G -32.5, B -29.6, the median
darkening measured between real re-imagings of LumenStone V1 sections). It is a
simulated perturbation, not a second capture.

1. **RESET SIMULATED PLANT** (presenter controls). `regrind_enabled = 0`.
2. Check **ON**. Upload `S2_v2/imgs/test/test_11.jpg`. As imaged it says *Grind
   finer*; on the darker copy it says *no payload detected*. → **SIMULATED
   LIGHTING: UNSTABLE**, no recommendation, plant **HELD at 0**.
3. Switch the check **OFF**. The same section re-runs. → *Grind finer*,
   **LIGHTING CHECK OFF · UNGUARDED**, plant **0 → 1 APPLIED**. Say: *"This is
   what an unguarded system does to your plant, on advice that disappears when
   the image is slightly darker."*
4. Switch the check back **ON**. Upload `test_04.jpg` → **no recommendation: 4
   payload-bearing particles, below the provisional floor of 9** → **HELD**.
5. Upload `test_01.jpg` → *Continue*, stable under the perturbation →
   **UNCHANGED** (no command sent).
6. *Optional, stale refusal, in exactly this order:* switch the check **OFF**
   first, then **RESET**, then **TRIGGER STALE OPC UA REFUSAL**, then upload
   `test_11.jpg` → **REFUSED**: "consumer refused stale command
   regrind_enabled=1 ... setting unchanged", the setting stays 0. (Switching the
   check after arming re-runs the image on screen and spends the armed refusal
   there.)

Steps 1-6 verified in the running dashboard on 2026-09-30.

Say: *"The simulated plant moves only on a fresh, confident recommendation that
survives a simulated lighting change and rests on enough particles. Everything
else holds."* Do not call this a real plant, a P80 target or a recovery gain.
Do not call the floor of 9 a statistical bound, or the perturbation a second
capture. On validation data the check withheld 4 of 5 correct confident calls;
say so if asked.

**Why six fields, not one:** a single centre field held 0-20 payload particles
and matched the whole section's advice on 0 of 12 held-out sections; six fields
match on 9 of 12.

**Time it takes on this laptop's CPU:** about a minute when the check runs its
second pass. Rehearse the pause.

## What NOT to show live if the venue timing is tight

The actual native-resolution inference is measured, not estimated:
mean 162.3s / p95 195.7s per section on a CPU-only laptop
(`reports/segmentation_latency.json`, two independent runs pooled, 131-196s
range) - roughly 4-6x over the review's own 30-second design target for a
full image. A live four-minute wait immediately before beat 3 is a real risk
to pacing. If the live demo scope decision (flagged in HANDOVER.md entries
49-52, still open as of 2026-09-14) settles on a single small predeclared
field for the *live* portion, this backup recording is what covers the full-
section case - label it plainly as a recording, not a live claim, per the
review's own instruction ("Record the actual release and distinguish it from
synthetic material").

## After recording

- Save as an actual video file (not just these instructions) somewhere the
  presenting laptop can reach offline - a USB drive, not just cloud storage.
- Note the file's location in `HANDOVER.md`'s next entry so it isn't lost
  between sessions.
- This script's numbers were verified against this exact checkpoint
  (`checkpoints/lumenstone_s2_patches/best.pt`) on 2026-09-13/14. If the
  checkpoint changes before the final, re-verify before recording - do not
  assume these numbers still hold.
