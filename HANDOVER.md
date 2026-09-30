# Handover Log

Required for every collaborator. Before pushing, read the latest entry below.
After pushing, add a new entry — newest on top. Keep entries short and factual:
what changed, what's blocked, what the other person needs to know or do next.

Entry format:

```
## 2026-08-04 — <name>

**Did:** ...
**Changed:** files/paths touched
**Blocked on:** anything waiting on the other person, or "nothing"
**Next:** what the other person should pick up
```

---

**For current state, read `STATUS.md` first** - it is the synthesised snapshot. This log is the append-only session history behind it.

## 2026-09-30 — Sibusiso (82) — pre-production fixes: 57.5 -> 79 on re-test (PR #17)

**Did:** fixed every code-fixable finding from issue #16 on
`khanya/preprod-fixes` (PR #17, stacked on #13). Re-ran all four test layers.
Results and re-score are in `reports/PREPROD-TEST-2026-09-30.md` ("Re-test
after the fixes").

**Two behaviour changes, both yours to veto, both on train/val evidence only:**
1. **Confidence now gates.** The advisor's existing 0.85 "verify manually"
   threshold withholds a confident call.
   - On 37 train/val sections, unsafe confident calls were 0.635-0.822 and
     correct ones 0.834-0.896: 8/8 unsafe withheld, 2/5 correct lost
     (`reports/confidence_calibration_trainval.json`).
   - On darkened copies, 0/10 confident calls pass.
   - `advise()` is unchanged, so the committed reports stay valid.
2. **The lighting check is an optional diagnostic, off by default.** With the
   gate on it caught no extra unsafe call and cost 3 more correct ones.

Effect on held-out data (described afterwards, chose nothing):
- test_11 and test_12 -> Grind finer (correct), so the live demo now moves the
  plant on held-out data. That answers your #12 point.
- test_01's correct Continue is withheld at 77%.

**Other fixes:**
- **Inputs.** Input-eligibility gate: greyscale and non-micrographs are refused
  before any model pass or publish.
- **Full section.** Advisory only, and labelled.
- **Timing.** One labelled server-side timer in every mode.
- **Installability.**
  - `requirements-lock.txt`, installed by CI on Python 3.13;
  - `jinja2` added;
  - README "Setting up a presenting laptop" (where the checkpoint comes from);
  - preflight fingerprints REEFPRINT against 29254718 and times a live pass;
  - the offline test covers templates and CSS.
- **Small items.** Evidence names the gate; the result clears at run start;
  "these fields"; the small-image message is reworded.
- **Evidence found along the way.** The ±0.335 band covers 75.7% of six-field
  errors on train/val against a nominal 85%: documented, not widened.

**Re-test:**
- Live 31.5-38.6 s (was ~60); full section 210 s (was ~290).
- Every hostile input refused in 1-2 s.
- Stale refusal re-verified; 158 tests pass.
- Demo beat 4 is rewritten and re-verified (`BACKUP-DEMO-SCRIPT.md`).

**Not fixed:**
- **OPC UA:** 10.2 s of each Grind-finer run, two server start-ups. Merging
  them is a transport change the night before the demo.
- **Science:** n = 12, magnetite 0, unsourced thresholds.
- **Wifi-off run:** needs the presenting laptop.

**Blocked on:** your reviews: #11 -> #12 -> #13 -> #17.

**Next (Lethabo):** veto or accept the two behaviour changes in #17. They
change the pitch's demo beat.

---

## 2026-09-30 — Sibusiso (81) — stack repaired after #10's merge; #15 reviewed

**Did:**
- **#10 was merged, and deleting its branch auto-closed #11.** The merge was
  approved and `main` is byte-identical to the approved head `2ca8e45`.
  Deleting `khanya/evidence-sufficiency` closed #11 unreviewed. The fix:
  - merged `main` into `khanya/lighting-check` keeping the branch tree (it
    already contains `2ca8e45`, so nothing changes);
  - restored the base branch briefly, reopened #11, retargeted it to `main`,
    and deleted the branch again;
  - cascaded the same no-op merge into #12 and #13.

  All three branch trees are unchanged, all three PRs are mergeable, and each
  shows only its own changes. Re-review requested on #11.
- **Reviewed #15** (Lethabo's `codex/launch-live-demo`): changes requested.
  - It is based on pre-#10 `main` and conflicts with the stack in 5 files.
  - It hard-codes the Kaggle retrain's 0.4543 on screen regardless of the
    loaded checkpoint.
  - Its demo record shows Continue → `regrind_enabled` 1 → 0 as a success.
    That is the #12 bug, still on `main` at `control.py:38`.
  - "Human-reviewed advisory" is false.
  - At 375 px the result is 3,129 px inside a fixed, non-scrolling 1,900 px
    frame, which cuts off the simulation disclaimers.
  - Keep: the held-out example button, the research-mode masthead, and the
    collapsed developer controls.
- **#9's DaisyUI skill vendoring** (73 files, no licence notice) is noted
  here; no comment posted on #9.

**Blocked on:** Lethabo's re-review of #11 -> #12 -> #13, and his replies on
#15 and issue #16.

**Next (Lethabo):**
- Merge #11 -> #12 -> #13 without `--delete-branch`, retargeting each next PR
  to `main` first.
- Then rebase #15 onto the new `main`, or say if I should port its keepers.

---

## 2026-09-30 — Sibusiso (80) — pre-production test, end to end: 58/100, not pilot-ready

**Did:** tested `khanya/speed` (`5254951`) in four layers: static checks, a
fresh GitHub clone, every dashboard mode live from a cold server, and hostile
uploads. Full results: `reports/PREPROD-TEST-2026-09-30.md`. No code changed.

**Passed:** 143 tests (repo and fresh clone); preflight READY here and a
correct 3-check refusal in the clone; test_01 Continue/UNCHANGED, test_11
UNSTABLE/HELD; Evidence agrees with the expert on test_01 and test_11;
corrupt and 300 px files refused before any command; RGBA = JPG; browser
traffic localhost only.

**Failed, ranked:**
1. **No input-eligibility gate.** A screenshot of text came back as 68% ore,
   100% pentlandite, 193 particles, and its association index was **published
   over OPC UA and acknowledged**. Greyscale test_11 inverts the phases
   (pyrrhotite 99.1% -> pentlandite 97.5%, association 1% -> 66%). Both held
   only because the value fell inside the ±33.5% band.
2. **Full-section mode bypasses the lighting check without saying so.**
   test_11: live mode HELD; full mode Grind finer, APPLIED 0 -> 1, no
   UNGUARDED label. (Grind finer is the expert's answer on test_11, so this
   call was right, but it had no guard.)
3. Confidence is a caption, not a gate (`advisor.py:145`).
4. Time claims: "about three minutes" in the app vs about 4 min 50 s measured
   for full section; live ~60 s today vs 49 s recorded; "end to end" leaves
   out about 8 s of upload and render.
5. Not installable from the repo: unpinned requirements, Jinja2 missing, no
   checkpoint route, REEFPRINT loaded from an unpinned folder outside the repo
   (`Desktop\REEFPRINT`, detached at `73806b2`; its integrate/ code matches
   `origin/reefprint` today).

**Score: 57.5/100 as pre-production** (weighted; the breakdown is in the
report's Score section). Fixing 1-5 would take it to about
72 (an estimate, not a measurement). The science caps (n=12, lighting check
non-selective, magnetite 0) remain.

**Added after the test:** `src/input_eligibility_check.py` measures a fix for
finding 1: a colour-balance rule with no fitted threshold passes all 49 S2
sections and refuses both hostile images, but refuses 20 of 30 V1 images (another
imaging set-up). Details in the report.

**Blocked on:** nothing. Re-reviews of #10-#13 still pending.

**Next (Lethabo):** issue #16 has every finding, its fix, and five decisions
(D1-D5) that are yours: full-section mode, refusing unseen camera set-ups,
checkpoint route, REEFPRINT pin, confidence floor. Nothing is implemented
yet beyond the measurement script.

---

## 2026-09-30 — Sibusiso (79) — #13 review: evidence provenance bound to the checkpoint hash

Lethabo's #13 review (changes requested) found three provenance holes, all
fixed:
- **Cached evidence predictions trusted on a file timestamp alone.** They are
  now used only when the stamp matches **and** the active checkpoint's sha256
  (computed once) is the reported `de7135a9`.
- **The scorecard could sit beside a different model's prediction.** It now
  checks both reports' recorded `checkpoint_sha256` against the active one, and
  is hidden, with the reason stated, on a mismatch.
- **"This section's accuracy" was mean IoU.** Renamed "Section mean IoU".

His first point (simulated-perturbation wording) was already fixed by the #11
and #12 changes merged up.

Verified live: Evidence shows the sha-bound source line and the scorecard,
2.5 s. Suite 143 passed.

**Note for later:** Lethabo's new PR #14 (codex/khanya-build-plan -> main)
touches `src/segmentation/patches.py`, which #10 also changes. Expect a merge
conflict; merge #10-#13 first.

---

## 2026-09-30 — Sibusiso (78) — every judge-review point on #10-#12 addressed

**Lethabo's reviews were right on every point; all fixed, pushed and verified
live on the full stack.**

- **#10:** the minimum of 9 payload particles is now a **provisional operating
  floor, not a statistical bound**. The binomial derivation doesn't hold for an
  area-weighted index over dependent particles. The on-screen "even a perfect
  segmentation cannot..." is gone.
  The **six-field sampler no longer repeats or overlaps crops** on small
  uploads (a 512x512 upload got the same crop six times): the grid shrinks to
  fit, overlap is asserted, and coverage is computed. Tested on 200 random
  sizes.
- **#11:** now a **simulated lighting-perturbation check / input-sensitivity
  diagnostic**. It is the same image with a fixed RGB offset, not a second
  capture, and the offset is shown. **Gauge R&R comparison withdrawn.** The
  costs (4 of 5 correct confident calls discarded, double the time) sit at the
  top of the report. Validation re-run with the renamed refusal: **identical
  numbers, deterministic**.
- **#12:**
  - **Continue at current setpoint no longer switches regrind off.** It is a
    no-op (UNCHANGED), and the declared regrind-on preset is removed.
  - A **visible guarded/unguarded toggle** replaces the preset.
  - The tile says "provisional floor", coverage is computed rather than
    asserted, and the strip stacks on phones.

**Verified live (BACKUP-DEMO-SCRIPT beat 4, all six steps):**
- test_11, check ON: UNSTABLE, HELD 0.
- Check OFF: *Grind finer*, UNGUARDED, **0 -> 1**.
- test_04: provisional floor, HELD.
- test_01: *Continue*, STABLE, **UNCHANGED 1 -> 1**.
- Stale refusal: REFUSED, stays 0.
- Phone width: one column.

Script bug found while verifying: arming the stale refusal and *then* toggling
spends it on the image on screen. Order fixed in the script.

Presenter note: in the in-app browser pane, pointer clicks on the toggle
didn't register but keyboard Space did. Check it on the presenting laptop
during rehearsal.

Suite 141 passed; offline guard clean.

**Next:** Lethabo - re-review #10 -> #13 in order.

---

## 2026-09-30 — Sibusiso (77) — fewer spinners: faster live path, instant evidence, offline config (PR D)

**Profiled first:** of a live six-field pass, the model's six forward passes
took 15.3 s, but the **progress frames took 5.2 s each (31 s)**: full-size PNG
encoding of a preview. Batching two fields per forward saves only 2% on this
CPU, so that was not done.

**Did:**
- **Progress frames at screen size, with fast PNG compression**: 5.16 -> 0.41 s
  per frame. Measurement still runs on full-resolution labels.
- **The lighting pass runs only when there is a confident instruction to
  protect.** The gate leaves abstentions untouched, so a second pass could not
  change them.
- **Model warmed once at startup**, before any upload.
- `.streamlit/config.toml`: toolbar hidden (no "Deploy" button), and
  **`gatherUsageStats = false`**. Streamlit's usage statistics would otherwise
  try the network, a hole in the offline claim.
- **Evidence view** loads the cached prediction only when its stored checkpoint
  stamp equals this checkpoint's file stamp (otherwise it runs live), says which
  on screen, and adds a scorecard: the section's own IoU, the model's
  whole-section advice and the expert annotation's advice.

**Measured live (this CPU, single runs, not distributions):**
- test_01, two passes: model part **49.0 s** (was 71-74 s), ~58 s upload to
  result.
- test_04, one pass: 32.2 s, ~50 s upload to result.
- Evidence: **13.5 s** (was ~3 min).

**Still slow and not fixed:** forward passes dominate now, and they ran slower
tonight than in the earlier profile. The ~8-18 s after inference is mostly two
OPC UA transactions, each starting a fresh local server. GPU timing is
Lethabo's (entry 72).

**Next:** Lethabo - judge review of #10-#13.

---

## 2026-09-30 — Sibusiso (76) — control-room screen: decision, evidence, plant in one row (PR C)

**Did:**
- A three-tile strip at the top of every result (`_control_strip.html.jinja`,
  inline SVG and styles because the Tailwind build is offline-compiled):
  - **DECISION:** the full action, verdict and first sentence of the reason.
  - **EVIDENCE:** payload-bearing particles against the ≥9 floor, the field
    coverage, and as-imaged vs re-imaged thumbnails with STABLE/UNSTABLE.
  - **PLANT:** a simulated flotation circuit (feed, mill, rougher, cleaner,
    regrind loop vs bypass) with an APPLIED/HELD/REFUSED badge and before ->
    after.
- The native Streamlit lighting and plant sections are folded into a collapsed
  command log.
- Presenter buttons moved into a collapsed *Presenter controls* panel, plus a
  new **START WITH REGRIND ON (declared setup)**, logged as a manual setup, not
  an advisory.
- The landing page now leads with the problem. The unmeasured "in seconds"
  claim was removed, caught by the render test for fabricated claims.

**Why the preset:** no held-out *Grind finer* survives the lighting check live
(entry 75). So the honest demo of a parameter change is regrind set on as the
declared starting state, then a stable *Continue* (test_01) switches it off.

**Verified live:**
- test_01: *Continue*, 52 payload particles, LIGHTING STABLE, plant **1 -> 0
  APPLIED**, bypass lit.
- test_11: refused, LIGHTING UNSTABLE ("darker lamp: no payload detected"),
  plant **HELD**.

**Flagged, not fixed:** the confidence tile shows 77% "verify manually" while
the decision tile shows *within specification*. That comes from the existing
advisor.

Suite 138 passed.

**Next:** Lethabo - judge review. Sibusiso - PR D (speed, no spinners, hide the
Streamlit toolbar).

---

## 2026-09-30 — Sibusiso (75) — lighting check: honest result is a repeatability gate, not an error detector (PR B)

**Did:** `src/stability.py` re-measures the same six live fields after one fixed
re-imaging shift and refuses a confident recommendation that changes. The shift
is the per-channel median of real darkening across all ten V1 pairs (R -34.8,
G -32.5, B -29.6). No tuned threshold. The dashboard shows both passes and holds
the plant when unstable.

**Validated on train + val only, 0 test sections**
(`reports/lighting_check_trainval.json`, `reports/LIGHTING-CHECK-2026-09-30.md`):
- Advice changed under the shift on **24 of 37**.
- Unsafe **8 -> 3**.
- It caught 5 of 8 wrong confident calls **but threw away 4 of 5 correct ones**.
  It does **not** tell good advice from bad and must not be pitched as "catches
  its own mistakes". Honest framing: measurement-system capability (gauge R&R).
  Advice that moves with the lamp is not fit to drive control.

**Also exposed:** on these 37, six-field confident calls were unsafe against the
expert whole section 8 of 13 times (test set: 0 of 3). This suggests the ±0.335
band, calibrated on whole sections, is too narrow for six fields. It bears on
PR #10.

**Live, verified:**
- test_11 and test_12 (*Grind finer*) lose the pentlandite entirely after the
  shift ("no payload detected"), so both are held.
- **No held-out *Grind finer* survives the check** in live mode.
- test_01 *Continue* is stable.
- Two passes take ~71-74 s end to end; PR D must fix that.

**Next:** Lethabo - judge review. Sibusiso - PR C (control room), including a
declared regrind-on starting state so a stable *Continue* can visibly move the
plant.

---

## 2026-09-30 — Sibusiso (74) — no advice on thin evidence; six fields, not one (PR A)

**Why:** running the build as a judge would, the flagship *Grind finer* that
moved the plant rested on **2 particles** (1 payload-bearing) in a single centre
field. A system whose thesis is refusing weak evidence was commanding a plant on
it.

**Did:**
- **Evidence-sufficiency gate** in `src/advisor.py`: *No recommendation - too
  few payload particles* below `MIN_PAYLOAD_PARTICLES`. It is **derived**, not
  tuned: `ceil((1.96*0.5/LIBERATION_MARGIN)^2) = 9`, the smallest n whose
  worst-case 95% interval on a proportion is narrower than the band the advisor
  already decides against. Missing counts fail closed. `modal.liberation_stats`
  counts payload-bearing particles; `liberation_index`'s interface is unchanged.

  > **CORRECTED 30 September (Lethabo, PR #10 review). The rationale above is
  > withdrawn and kept only as history.** 9 is a **provisional operating floor,
  > a conservative policy choice, not a statistical bound**. The binomial
  > interval is not valid for an area-weighted ratio over spatially dependent
  > particles. The floor is now hard-coded and does not follow the margin. A
  > real uncertainty estimate for this estimator, on training/validation data,
  > is post-deadline work.
- **Six sampled fields** replace the single centre field as the live path
  (`multi_field_predict`, 3x2 grid, fixed by a latency budget before
  measuring). Fields sit in a mosaic with background gaps, so the unchanged
  measurement chain cannot merge particles across fields.
- **Bug fixed:** `decision_gap.classify` counted only Marginal/Flag as hedges,
  so a *No recommendation* abstention would have scored as a confident error. It
  now uses the advisor's own `ABSTAINING_PREFIXES`.

**Measured** (`reports/field_sampling_s2.json`, held-out S2):
- Single field: 0-20 payload particles; matches whole-section advice on
  **0/12**.
- Six fields: match on **9/12**.
- Expert whole sections: never refused (12-224 payload particles).
- Model whole sections: refused on 2 (test_02, test_07: 5 and 8 payload
  particles against the expert's 12 and 13).
- Decision gap, S2 refined: 0 unsafe still, disagreements 6 -> 8, all hedges.
- Decision gap, S2 raw: errors 5 -> 2. The 2 unsafe (test_03/04) are the raw
  estimator's broken particle identity, not thin evidence.
- S1 unchanged.

**Live, in the running dashboard:** test_11 -> six fields -> *Grind finer* on 10
payload particles (24 total), 17.2 s end to end, plant 0 -> 1. test_04 ->
refused on 4 payload particles, plant held.

**Changed:** `src/{advisor,modal,decision_gap}.py`,
`src/segmentation/patches.py`, `src/field_sampling_check.py` (new),
`dashboard/app.py`, tests (+10), S2 decision-gap JSONs,
`reports/field_sampling_s2.json`, `ACCURACY-REPORT.md` s7/s10, `PITCH.md`,
`BACKUP-DEMO-SCRIPT.md` beat 4. Suite 132 passed.

**Next:** Lethabo - review as a hostile Mintek judge (PR). Sibusiso - PR B,
lighting consistency check.

---

## 2026-09-29 — Sibusiso (73) — the accuracy report, as one document (PR for review)

**Did:** The brief says submissions *must include an accuracy report*. The
evidence existed, spread across a dozen files. `reports/ACCURACY-REPORT.md`
assembles it with every number traced to a named file: model and data
provenance, per-class IoU/recall/precision, void-border, confusion matrix,
trivial baselines, the magnetite failure, the like-for-like S1 comparison,
decision-level results with denominators, reproducibility, lighting, speed and
limitations.

**New and checked tonight** (`src/s2_section_stats.py` ->
`reports/s2_section_stats.json`): the headline **0.5725 has a 95% bootstrap
interval of 0.494-0.624** over sections. Lethabo's per-section mean **0.4671
reproduces exactly** (open since 15 Sept), with 10 of 12 sections below the
headline. Live Field matches full-section advice on **4 of 12**.

**Corrections found while checking:** (1) the test set is **103,795,344**
pixels, not the "92.6 million" I have quoted since 15 Sept; I evidently left
one class's row out of the sum. It reached five places on `reefprint`. (2) The
single-field latency (2.64 s mean) is forward pass only; the 4.7 s end-to-end
figure is in no report file. (3) The full-section latency is n=6 on one image,
not "n=3" as PR #7 says.

**Next:** Lethabo - review the report (PR). Sibusiso - deck, video, rehearsal.

---

## 2026-09-29 — Sibusiso (72) — clause-by-clause completion plan, added to PR #7

**Did:** Added `reports/CHALLENGE-CLAUSES-2026-09-29.md` to PR #7, alongside the
pilot-gaps document. It takes the challenge's own wording clause by clause and
says what can be closed before 1 October (with owner and estimate), and what
only a pilot can finish.

**Where each stands:** clause 1 met. Clauses 2-4 are met at prototype level:
real-time only for analysing the image (full section 162.3 s mean on CPU,
n=3); processability is a proxy with three of four advisor thresholds
UNSOURCED; control integration is simulated, read only by our own client.

**Proposed before the deadline, after the deck, video and rehearsal:** show
processability as a named quantity with its ±33.5% band; make the unsourced
thresholds site-configurable; add an operator-facing OPC UA tag and have a
third-party client read it; GPU timing on Kaggle (Lethabo). Each is a separate
PR.

**Next:** Lethabo - the five questions at the end of the new document, plus
PR #7's original five.

---

## 2026-09-29 — Sibusiso (71) — from demo to pilot: five gaps, for Lethabo

**Did:** PR #6 approved and merged by Lethabo (`ced0ca8`); all three literal
deliverables are now demonstrable. The team wants more than a demo: a solution
one credible step from a pilot. Wrote `reports/PILOT-GAPS-2026-09-29.md`, built
on Lethabo's own stage table: what we have, what a pilot needs and a question
for each of five gaps. The gaps are outcome evidence (no plant data), ore domain
(Norilsk, not South African), preparation time (unmeasured; "hours" was my
unsourced figure), moderate accuracy (non-reproducible recipe), and lighting
(disclosed, not gated).

**Also noted from his Dice result:** 0.5300 validation has not beaten the
existing checkpoint's 0.5384. The demo model stays `de7135a9`.

**Next:** Lethabo - answer the five questions on the PR, especially whether
`reefprint.calibrate.reflectance` can sit in front of KHANYA in a pilot.

---

## 2026-09-29 — Sibusiso (70) — the plant parameter now moves on the advisory (PR for review)

**Did:** Built P3 and P0 from Lethabo's plan (`codex/khanya-build-plan`,
`handover/IMPLEMENTATION.md`), on a branch for his review rather than straight
to `main`.

**P3, the brief's plant-parameter deliverable.** New `dashboard/control.py`: the
advisor's action commands one explicitly simulated tag, `regrind_enabled`, over a
real local OPC UA exchange through REEFPRINT's `AdvisoryServer` /
`SimulatedControlClient`, imported unchanged through the existing bridge
(ADR-0003). *Grind finer* -> 1, *Continue* -> 0; every abstaining action issues
**no command** so the setting holds; reagent actions do not touch regrind. State
persists across uploads, with before/after, a reason and a command log on screen.
The consumer is seeded with the plant's actual value, so the before/after is real
state, not a fresh 0.0.

**Verified in the running dashboard with the real held-out files:** test_11 0->1
APPLIED; test_03 1->1 HELD; stale armed with test_03 on screen -> nothing fired;
test_01 while armed -> REFUSED ("regrind_enabled=0 ... setting unchanged", stays
1); Reset with an image on screen -> stays 0; test_11 again 0->1.

**Two stage bugs the live probe caught, both fixed:** (1) the stale button fired
immediately on the image already on screen, because the arming click itself
reruns the script; its message said "next upload". (2) Every rerun re-sent the
command, so Reset re-commanded the loaded image straight back to 1. Commands are
now tied to (upload, mode).

**P0, `python -m src.preflight`:** checks the S2 checkpoint sha256 (`de7135a9`),
the 12 test sections, a strict model load and an OPC UA command round trip;
prints `READY TO PRESENT` or refuses. Probed: the August Dice checkpoint has the
**same byte size** (168,313,587) as the real one and is caught only by its hash.

**Also found:** Live Field and full-section recommendations differ on **8 of 12**
held-out sections, and `BACKUP-DEMO-SCRIPT.md` Beat 2's test_04 is *No
recommendation* in Live Field, not *Marginal*. Script updated with the preflight
step and a new Beat 4.

**Note on the plan's reading of `advisory_influenced`:** it treats `False` as
"not a plant-parameter change". In REEFPRINT's `advisory.py` the field records
whether the *sampled material* was already affected by an earlier advisory
(blind spot 10), so `False` is correct on a command about an untouched held-out
section.

**Changed:** `dashboard/control.py` (new), `dashboard/app.py`,
`src/preflight.py` (new), `tests/test_control.py` (new, 6 tests incl. 3 real
OPC UA exchanges), `BACKUP-DEMO-SCRIPT.md`. Suite 122 passed; CI offline guard
clean.

**Blocked on:** Lethabo's review of the PR.

**Next:** Lethabo - review and critique. Sibusiso - deck, backup video, timed
rehearsal.

---

## 2026-09-29 — Sibusiso (69) — two corrections, and the CE+Dice run is a repeat

**Correcting entry 68.** It said validation patch mIoU was "similar in both
(~0.47), so validation did not catch it". Wrong. The existing checkpoint
validated at **0.5384** (`STATUS.md` line 221); the Kaggle baseline at 0.4705.
0.4739 was the August CE+Dice run, which I conflated. So validation **did**
separate the two models, which is good news: validation-only selection tracks
the test result here.

**Root cause of the 0.12 gap, found by Lethabo's session:**
`src/segmentation/patches.py:156` samples training patches with
`random.Random(None)`, so no two training runs see the same patches. The recipe
is non-reproducible by construction. Real bug, in KHANYA's code, mine to fix -
after the deadline, since fixing it does not change the existing checkpoint.

**The CE+Dice validation run launched at 21:39 repeats a settled experiment.**
It was run on 16 August at the same budget: best val patch mIoU 0.4739 against
CE's 0.5384, magnetite IoU 0.0000 every epoch (`STATUS.md` line 220). Its
checkpoint is on this machine at `checkpoints/lumenstone_s2_patches_dice/best.pt`,
the same path the new run writes to. Magnetite is also not one of the three
phases the brief requires.

**Next:** Lethabo - no further training before submission; the model is done.
The remaining work is the plant-parameter wiring, the deck, the backup video and
a rehearsal.

---

## 2026-09-29 — Sibusiso (68) — the Kaggle retrain scored 0.4543; keep the existing checkpoint

**Did:** Reviewed Lethabo's two later commits on `codex/khanya-build-plan`
(`1bbc33a`, `263939a`, 20:57 and 21:18). His Kaggle run (`20260929-185547`,
started 18:55, before entry 67 was pushed) retrained S2 on a T4 and scored
**0.4543 mean IoU / 0.7716 pixel accuracy**. The existing checkpoint, reproduced
today, scores **0.5725 / 0.8914**.

| Class | existing `de7135a9` | Kaggle `fb78727d` |
|---|---:|---:|
| chalcopyrite | 0.5755 | 0.3537 |
| pyrrhotite | 0.8695 | 0.6866 |
| pentlandite | 0.5468 | 0.3555 |
| magnetite | 0.0000 | 0.0000 |

**Same recipe, run twice.** Data is byte-identical (sha256 `64aebd10...`,
418,742,024 bytes, checked against this machine's archive). Code is main's.
Split is seed 42, 31/6/12. Budget is the default 8 epochs x 64 patches, which is
what the existing checkpoint was trained with (entry near line 3153). What
differs is hardware (CPU vs T4), library versions and sampling randomness. So a
second run of the identical recipe landed **0.12 mIoU lower**. That is n=2, but
it means 0.5725 describes **this checkpoint**, not the method. It also fits the
training-budget reading: 512 patches in total is starved enough that which
patches get sampled decides the result. Validation patch mIoU was similar in
both (~0.47), so validation did not catch it.

**What this means for the build:**
- Demo and report stay on `de7135a9`. Every current number (illumination 8/12,
  severity table, 0.335 band, backup-script values) belongs to it.
- **Both files are named `checkpoints/lumenstone_s2_patches/best.pt`** and the
  dashboard loads whatever is at that path. On Lethabo's machine it is now the
  weaker one. Check the sha256 on the presenting laptop before the talk.
- Say it on stage if asked: the checkpoint reproduces bit-for-bit; the recipe
  does not, and a second run scored 0.4543.

**Credit where due:** the run fetched S2 from the publisher inside the kernel
(`enable_internet: true`, `dataset_sources: []`), so no Kaggle mirror of S2 was
created. That sidesteps the redistribution problem cleanly. Test set untouched
for tuning; limits stated honestly.

**Branches:** `fix/geometry-guard-before-inversion` is already in `main`'s
history and `fix/pool-signatures-not-raw-frames` is already in `reefprint`'s.
Both are dead and safe to delete. Lethabo's call, they are his.

**Next:** Lethabo - keep `fb78727d` as a recorded run, not the demo model.
Sibusiso - copy `de7135a9` to the presenting laptop and verify its sha256.

---

## 2026-09-29 — Sibusiso (67) — the S2 model is not missing; do not retrain

**Did:** Reviewed `codex/khanya-build-plan` (three docs-only commits today,
1,249 lines, authored from Lethabo's account on a machine at `C:/Users/USER`).
Its plan rests on one audit finding: S2 weights and data "not found", so retrain
on Kaggle. **That audit ran on the wrong machine.** On this one the checkpoint
(sha256 `de7135a9...`) and S2 data (37/12) both exist, and a fresh full-section
evaluation today reproduced **0.5725 mean IoU, bit-for-bit identical** to the
committed report, every class included. See
`reports/S2-REPRODUCTION-2026-09-29.md`.

**Why it matters two days out:** retraining would make every current S2 number
historical, including the illumination finding the new plan builds its demo
around (its own evidence item E6). It also needs S2 on Kaggle, which is the
unresolved redistribution decision. The real gap is the one from issue #5 Q1:
`checkpoints/` is gitignored, so the presenting laptop does not have the file.

**What the branch gets right, and should be kept:** OPC UA currently publishes
observations with `advisory_influenced=False`, which is not a plant-parameter
change, so its P3 simulator regrind state closes a real deliverable gap; the
lighting-change-then-hold demo beat; the evidence register and "claims to
replace" table; and flagging that the organiser email confirms 1 October but
not 13:00.

**Changed:** `reports/S2-REPRODUCTION-2026-09-29.md` (new, `1a22051`). Metrics
JSON regenerated and unchanged.

**Blocked on:** a decision on which laptop presents.

**Next:** Lethabo - drop P1 (retrain) and P0's download/train steps; copy this
checkpoint to the presenting machine and check its sha256. Then P3 simulator
state, the P4 hold on the lighting stress test, the PowerPoint (none exists
yet), the backup recording and a timed rehearsal. Cut P6 (chemistry/3D).

---

## 2026-09-15 — Sibusiso (66) — ask 4 settled: the real gap is worse than we were quoting

**Did:** Downloaded LumenStone **S1 v1** (534,897,733 bytes, published 535 MB,
sha256 `80940fb7...`, unpacks to exactly 59 train + 16 test) and settled issue #5
ask 4 by content hashing rather than by filename.

**Membership, proven:** all 16 v1 test images are **byte-identical** (sha256 over
file bytes) to v2's `test_01`-`test_16`. **Zero** appear in v2's 64-image train
split. That second check was not part of the original ask and is the one that
mattered: our checkpoint trains on v2 train, so a v1 test image sitting there
would have made the comparison leakage-contaminated. It is clean. The positional
guess was right; it is now proven instead of assumed.

**The like-for-like number, void-border protocol:**

| | mean IoU | void-border | gap to published 0.8506 |
|---|---:|---:|---:|
| **v1 protocol, 16 images** | **0.6881** | **0.7224** | **-0.1282** |
| our v2 test, 20 images | 0.7116 | 0.7481 | -0.1025 |

**The gap is WORSE on the correct protocol.** The four extra v2 test images were
flattering us by **+0.0257**. Every previous statement of the S1 gap used the
20-image figure, which is not what the published number was measured on. **Use
-0.1282 whenever 0.8373 is in the sentence.**

**We match published on background (-0.0015) and BEAT it on bornite (+0.0020).**
Pyrite and chalcopyrite are within 0.045. Three classes carry the whole gap.

**Correcting entry 63 / `ca2e02f`:** "tennantite is 60.8% of the S1 gap" is true
of the 20-image set. On the correct protocol it is **47.1%**, and **galena rises
from 14.3% to 28.6%**. Together **75.7%**. The framing survives - the gap is
concentrated in a few optically ambiguous phases, not spread across the model -
but the figure 60.8% must not be repeated.

**Galena joining tennantite strengthens the low-contrast reading.** Both are grey
sulphides sitting close in reflectance to their neighbours, as magnetite does to
the resin on S2. The classes we match or beat (bornite, pyrite, chalcopyrite) are
the strongly coloured ones. Published detects all of them (tennantite 0.7601,
galena 0.7464, magnetite 0.650), so the limit stays ours, not the modality's -
still a training-budget claim, still what J0/J1/J2 tests. **The pre-registered
scaling prediction should name galena alongside tennantite and magnetite.**

**Also worth stating plainly:** the published model trained on v1's **59**
images; ours trained on v2's **64**. More training data, worse result.

**Changed:** `reports/S1-V1-LIKE-FOR-LIKE-2026-09-15.md` (new),
`reports/benchmark_s1_v1_protocol.json` (new),
`reports/s1_v1_v2_content_match.json` (new).

**Blocked on:** Lethabo - still the A-or-B redistribution call (S1/S2 Kaggle
upload paused), whether the illumination finding leads the abstention argument,
and a rehearsal date. Issue #4's two items were both already done on 13 Sept and
I have said so there.

**Next:** Sibusiso - correct the 60.8% figure wherever it has propagated; LFS
migration still outstanding. Lethabo - add galena to the pre-registered scaling
prediction in `docs/11-...`, and note ask 4 is closed with a real number.

---

## 2026-09-15 — Sibusiso (65) — the advice changes when only the light changes

**Did:** Ran the V1 work Lethabo flagged as mine. It could not be done as
`robustness.py` intended, and what replaced it found something worse than a
robustness number.

**V1 has no masks.** Read the dataset's own distribution table directly: S1 and
S2 ship "images + masks + visualizations", V1 ships "images (3 variations)".
`robustness.py` scores IoU against ground truth, so its docstring's "real V1
evidence should replace this" is not executable. Built
`src/v1_consistency.py` instead - self-consistency needs no labels, because the
same section must give the same answer twice.

**The finding, from two independent in-domain routes:**

| | n | mean mask IoU, same field twice | recommendation changed |
|---|---|---|---|
| V1, real re-imaging (S1 ckpt) | 10 | **0.3213** | **5/10** |
| S2 held-out, synthetic -35 RGB | 12 | **0.4597** | **8/12** |

Nothing about the rock changed. V1 sample 005 liberation **0.941 -> 0.001**; S2
`test_05` **0.941 -> unmeasurable**. **On half to two thirds of sections the
plant recommendation changes because the illumination changed.** The advisor
refuses on low payload and hedges near the liberation threshold; it has no
notion of "imaged under conditions I cannot vouch for", so it does not refuse
here - it confidently changes its mind.

**A mistake that nearly shipped, logged not buried.** The first run used the
**S2** checkpoint and gave 8/10 and 35.23 pp drift. The dataset page says *"V1:
the same samples as for S1"* - S1 is Berezovskoe, S2 is Norilsk. That run was
the cross-dataset out-of-domain case `BACKUP-DEMO-SCRIPT.md` already uses as its
refusal beat, and it inflated the effect by about 2x. Retracted in the report.
The dramatic first number was the wrong number, which is exactly when this
project is supposed to go looking for the bug.

**Verified rather than assumed:** V1's `NNN`/`NNNb` pairs are pixel-registered
(NCC **0.99 at zero shift**, all ten); `NNNa` is a different camera and field,
peaking at **0.27** over a full scale/offset sweep, so it is **excluded** - ten
valid pairs, not fifteen. This check was run because the S3 rotation series was
assumed registered and was not. Archive is 104,705,467 bytes, sha256
`499c625a...`, byte-identical to REEFPRINT's copy.

**Also found, and it reopens a closed ask:** the **S1 v1** archive (535 MB,
images + masks) is publicly downloadable from the same page. Issue #5 ask 4 was
retracted as unsound because positional filenames cannot establish the v1/v2
subset relation - the sound check is content hashing, and those images are one
download away. That restores the like-for-like comparison against the published
**0.8373** at zero GPU cost. Not downloaded yet.

**Changed:** `src/v1_consistency.py` (new), `src/exposure_control.py` (new),
`reports/ILLUMINATION-STABILITY-2026-09-15.md` (new),
`reports/V1-ROBUSTNESS-PLAN-2026-09-15.md` (new, superseded by the above),
`reports/v1_consistency.json`, `reports/exposure_control_s2.json`,
`.claude/settings.local.json` (gitignored), `.gitignore`.

**Blocked on:** the S1/S2 Kaggle upload is still paused on Lethabo's A-or-B call
about the redistribution contradiction (entry in
`REDISTRIBUTION-CONTRADICTION-2026-09-15.md`).

**Next:** Sibusiso - (1) decide whether the illumination finding goes in the
pitch; my read is that it should lead the abstention argument, since it is the
strongest evidence we have for the central claim and we found it against
ourselves; (2) run `--full` to check the finding survives full-section
inference; (3) LFS migration still outstanding. Lethabo - V1 is S1's samples,
which means it is usable from your side for colour-adaptation work against the
S1 checkpoint, and the registration result (b registered, a not) is the kind of
thing your SIFT+RANSAC estimator could verify independently.

---

## 2026-09-15 — Sibusiso (64) — the stale S1 cache had inverted a claim in the pitch

**Did:** Followed Lethabo's doubt (reefprint `70400db`) that claims resting on
`benchmark_s1_patches.json` were suspect. He was right, and it was worse than he
thought. Ran a full provenance audit of every report against checkpoint mtimes,
then regenerated everything downstream of the stale S1 cache.

**The bad find: `PITCH.md` and the research report carried a factually inverted
claim.** Both said the S1 generalisation test failed because *"the S1
segmentation is much weaker (mean IoU 0.33 against 0.57, two classes at
effectively zero)"*, and used that as the confound - no coherent structure left
to repair. Corrected: **S1 is 0.7116, S2 is 0.5725.** S1 is the *stronger*
segmentation. **No S1 class is near zero** (lowest tennantite 0.3130); the class
at zero is magnetite, in S2. The confound was not weak, it was backwards.

**The good find, and it is a better result than the one it replaces.** The old
decision-gap table reported flips only, and its S2 refined row (2/12, 1 unsafe)
did not match its own JSON. Regenerated all four runs with severity counts:

| | Flips | Unsafe | Conservative | Flagged | Errors |
|---|---|---|---|---|---|
| S2 raw | 6/12 | 2 | 3 | 1 | **5** |
| S2 refined | 6/12 | **0** | **0** | 6 | **0** |
| S1 raw | 4/20 | 0 | 1 | 3 | **1** |
| S1 refined | 14/20 | **0** | **0** | 14 | **0** |

**Topology repair does not reduce how often the system disagrees with ground
truth** - identical on S2 (6/12), and it *increases* disagreement on S1 (4/20 to
14/20). What it does is convert disagreements from **silent errors into explicit
hedges**: unsafe and conservative go to zero on both datasets and everything
becomes a request for manual verification. Lethabo reached the same place
independently from his side (`42118c1`: "the aggregate flip rate 0.50 is not an
artefact of refinement", and raw/refined do not flag the same sections).

So the finding **does** replicate on S1 - the old framing said it did not, because
it was measured on flip rate, which is the wrong metric. New line for the pitch:
*"repairing particle topology did not make the system more accurate - it made it
stop being confidently wrong."* S1 remains weak evidence (its raw run had one
error to remove and no unsafe ones) and that is stated.

**Provenance audit result, and it bounds the damage:** every S2 artifact
postdates its checkpoint (S2 patches checkpoint 16 Aug; S2 reports 16-18 Aug and
13-14 Sep). **Only the S1 artifacts were stale**, plus `magnetite_confusion.json`
which was correctly labelled `"resize baseline"` and miscited by me. The S2
headline numbers stand.

**On Lethabo's `ae5f749` (COCO checkpoint fails offline):** the bug is real but
the description is off and the scope is narrower than stated. `main`'s
`model.py` does **not** use `.DEFAULT` - it pins
`DeepLabV3_ResNet50_Weights.COCO_WITH_VOC_LABELS_V1` explicitly, with a comment
saying why. The offline failure is identical either way, so his finding holds.
But **every inference path already passes `pretrained=False`** (dashboard,
decision_gap, robustness, latency_benchmark, both evaluates, all tests) - only
the four *training* entry points pass `pretrained=True`. **The stage demo is not
affected and the offline claim is safe.** It affects J0/J1/J2 training kernels
only. Preferred fix of his two: `weights=None` + explicit `load_state_dict`
(0 missing/unexpected keys); not applied yet, it is a training-path change.

**Changed:** `PITCH.md`, `reports/KHANYA-01-research-phase.md`,
`reports/decision_gap_patches.json`, `reports/decision_gap_s1_patches.json`,
`reports/decision_gap_s1_patches_refined.json`.

**Blocked on:** nothing.

**Next:** Sibusiso - (1) LFS migration, still the highest-value unblocked item;
(2) apply the `weights=None` fix to `model.py` for the training path; (3) the
morphology sensitivity sweep, now that Lethabo has pre-registered its kill
criterion (14 configs; any config producing one unsafe classification kills the
"driven to zero" claim - `docs/11-...` on reefprint). Lethabo - his unplanned
S2 pooling finding (headline 0.5725 pooled across pixels vs 0.4671 averaging
per-section means, 10 of 12 sections below 0.5725) is **not yet independently
verified on this side**; it is the same two-conventions-one-name shape as the
abundance mix-up and should be settled before either number reaches a slide.

---

## 2026-09-15 — Sibusiso (63) — corrected S1 benchmark: the gap is one class

**Did:** Finished the re-cache entry 62 promised (20/20 sections, ~2.5 min each
on CPU, consistent with the measured 162.3s in `segmentation_latency.json`) and
re-ran `src.benchmark` against the current checkpoint.

**`reports/benchmark_s1_patches.json`: 0.3295 -> 0.7116** (plain), **0.7481**
under the void-border protocol petroscope actually publishes. Against published
ResUNet S1v1 0.8373 / 0.8506. The stale file had been misreporting our S1 result
by **+0.38 mIoU** since 21 August. Lethabo found it from a branch that has
neither the checkpoint nor the data.

**The finding is the decomposition, not the number.** The 0.1025 void-border gap
is not diffuse - it is **one class**:

| class | gap vs published | share of total gap |
|---|---|---|
| tennantite | **-0.4361** | **60.8%** |
| galena | -0.1029 | 14.3% |
| sphalerite | -0.0962 | 13.4% |
| pyrite | -0.0483 | 6.7% |
| chalcopyrite | -0.0199 | 2.7% |
| bornite | -0.0119 | 1.7% |
| background | -0.0023 | 0.3% |

**Excluding tennantite the gap is -0.0469 across six classes**, and background /
bornite / chalcopyrite are effectively matched to published.

**This unifies with the magnetite result into one characterisable failure mode.**
Both tennantite (grey, optically close to the other sulphides) and magnetite
(dark, optically close to the mounting resin) are **low-reflectance-contrast
phases**, and both are detected by published work on the same modality
(tennantite 0.7601, magnetite 0.650 per Korshunov). Rarity is again not the
driver: tennantite is 3.917% of S1 train pixels and scores 0.3130, while
chalcopyrite at a *lower* 2.974% scores 0.8652.

So the honest characterisation is: **this model loses specifically on phases with
low reflectance contrast against their neighbours, and the literature shows that
is a capacity/training-budget limit rather than a limit of the modality.** That
is a claim J0/J1/J2 measures directly - it is the strongest argument yet for
Lethabo's scaling study framed as evidence.

**Changed:** `reports/benchmark_s1_patches.json`,
`reports/decision_gap_s1_patches.json`, `data/derived/preds_s1_patches/`
(regenerated, gitignored).

**Blocked on:** nothing new. Issue #5 Q1-Q4 all answered by Lethabo (Git LFS for
the checkpoint - his reasoning beat mine, it keeps the binary bound to the commit
history MOTT assesses; `checkpoint_sha`+`generated_at` agreed; reproducibility
before GPU time; rehearsal date deferred to Sibusiso).

**Next:** Sibusiso - the LFS migration is now the highest-value unblocked item,
because it is what makes 0.7116 reproducible by anyone other than this machine.
Lethabo - the pre-registered kill criterion for the morphology sensitivity
analysis (see entry 62's correction), and note this benchmark decomposition
strengthens the J0/J1/J2 evidence framing you already set.

---

## 2026-09-15 — Sibusiso (62) — audited the layer every number rests on

**Did:** Answered Lethabo's issue #5 (all four asks), then audited
`modal.refine_ore_mask` + `watershed_particles` - the morphological layer
underneath the decision-gap result, the conformal band and the dashboard's
association index. Nobody had measured what it does. Now measured, reproducibly:
`python -m src.refinement_audit` regenerates every figure in seconds from cached
predictions.

**Two hypotheses formed and both killed by measurement, which is the good news:**
(A) "the repair is compensating for the dead magnetite channel" - REJECTED, only
**3.7%** of the 3,518,530 pixels it adds are true magnetite. (B) "the repair
biases liberation conservative, which is why unsafe errors hit zero" - REJECTED,
mean delta **+0.0840**, direction mixed 5 down / 3 up / 4 unchanged. **The
decision-gap finding survived two confounds that would have invalidated it.**

**What did land:** the refinement is a *replacement*, not a correction - on 3 of
12 sections it moves liberation from ~0.00 to ~0.75-0.80 (test_09: 0.0000 ->
0.8024). It is load-bearing and necessary (raw connected components are
degenerate; speckle fuses the field into one blob). By area it is **83.5% true
background** - enclosed resin and pore space absorbed into particle envelopes, a
metallurgical judgement that is nowhere documented. And it rests on three
hand-set constants (`SPECKLE_KERNEL=3`, `SEED_MIN_DISTANCE=5`,
`PEAK_FOOTPRINT=9`) with **no sensitivity analysis**. A judge who opens
`modal.py` reaches this in five minutes and "we tuned them on held-out data" is
not an available answer.

**Third stale artifact of the day, this one in source code.** `modal.py` had
justified hole filling with "magnetite predicted as background 92.3% of the
time" - that is the *resize baseline*; the shipping checkpoint is **78.32%**.
Preceded by `benchmark_s1_patches.json` (reported S1 mIoU 0.3295 against a real
0.7116; its prediction cache is four days older than the checkpoint - Lethabo
caught this) and `magnetite_confusion.json` (labelled `"resize baseline"` but
cited as current *by me*, in the comment crediting him for catching the first
one; corrected publicly rather than edited away). Three in one day is not
coincidence - every generated artifact needs `checkpoint_sha` + `generated_at`,
and preflight should refuse to start on a mismatch.

**Also settled the magnetite abundance mess:** S2 **train** share 1.841%, S2
**test** share **0.792%**, Lethabo's ledger 1.58% is the pooled figure. Three
correct quantities under one name. Use the **test** share - it is what the model
was scored on, it is already below 1%, and it kills the "you have not tested
below 1%" reply. Across 92.6M test pixels the model predicts magnetite **exactly
zero times** - a dead output channel, not a rounding artifact
(`reports/magnetite_confusion_patches.json`).

**Changed:** `src/refinement_audit.py` (new), `reports/refinement_audit.json`
(new), `reports/magnetite_confusion_patches.json` (new),
`reports/REFINEMENT-AUDIT-2026-09-15.md` (new), `src/modal.py` (corrected the
92.3% comment, flagged the three constants as untuned).

**Blocked on:** Lethabo, four questions on issue #5, none yet answered:
(1) how anyone but Sibusiso reproduces 0.7116 - `checkpoints/` is gitignored and
`git ls-files` confirms no checkpoint is tracked, so the corrected number is not
reproducible by him, a judge, or MOTT; LFS, off-repo host, or accept local-only?
(2) `checkpoint_sha` + `generated_at` on every report - worth a shared schema?
(3) does scheduling the day-20 scaling run make sense before (1) is settled, since
a new checkpoint inherits the same reproducibility problem? (4) a joint rehearsal
slot before day 20 - presentation clarity is the one judging criterion nobody has
touched.

**Next:** Lethabo - **correction to what entry 62 first said:** the sensitivity
analysis on the three morphology constants is **mine**, not yours. `modal.py`
exists only on `main`; `reefprint` has no modal, liberation or morphology code at
any path, so handing you an audit of my own module would blur the attribution
boundary ADR-0003 keeps independently verifiable for MOTT. What is genuinely
yours is **pre-registering the falsification criterion** - fix the perturbation
grid and the kill condition before I run it, so the author of the code under test
cannot widen the range until his finding survives. Until that returns, do not
lead the pitch with the decision-gap finding (the retraction in
`ADVERSARIAL-CRITIQUE` §7 stands, and this audit adds a second reason). S1
benchmark re-cache was still running when this was written - the corrected
`benchmark_s1_patches.json` lands in a follow-up commit.

---

## 2026-09-15 — Sibusiso (61) — build remediation plan, published to be attacked

**Did:** Published `reports/BUILD-REMEDIATION-PLAN-2026-09-15.md` as the
companion to entry 60's critique. The critique says what is wrong; this says
what to do about it. **Status is PROPOSED, not decided** - it is deliberately
published before anyone builds from it so Lethabo, Codex, or a fresh session
can attack it first.

**Five items, priority ordered:** an input eligibility gate (converts the worst
live-demo vulnerability into a beat); settling whether magnetite fails on
rarity or on reflectance contrast (an hour of work against existing S1 results,
and it is the thing that most weakens the critique's sharpest attack); a
preflight check (three environment failures in seven days, all detectable in
seconds); separating the topology-repair confound from the decision-gap finding
before it reaches a slide; and three cheap wins (warm model start, per-phase
confidence, bootstrap intervals).

**Every item carries a kill criterion** - the specific evidence that would mean
"do not do this". P1's is the important one: a gate that refuses legitimate S2
inputs is worse than no gate. P2's is that the contrast hypothesis must not be
claimed if S1's rare classes also fail.

**Section 4 lists five assumptions the plan makes that nobody has verified**,
including the one P2 depends on entirely: that S1 contains a rare but optically
bright class. The per-class S1 numbers are already in the repository and nobody
has read them against the class pixel shares. That check has not been done.

**Explicitly not doing:** new demo features, retraining (a new checkpoint nine
days from freeze invalidates the pitch numbers, the backup script, the conformal
band and the baselines), ONNX/INT8, further polarimetry, refactoring.

**Changed:** `reports/BUILD-REMEDIATION-PLAN-2026-09-15.md` (new), `README.md`.

**Blocked on:** nothing technical. The plan needs a human to accept, amend or
reject it before work starts.

**Next:** the cheapest item is P2's hour-long check against
`reports/lumenstone_s1_patches_test_metrics.json`, and it may change what the
pitch leads with, so it should probably go first regardless of the priority
order above. Section 3 of the plan is the part most likely to be ignored and
most likely to matter: rehearsal, the backup video and the human items from
entry 60 outrank every line of code in section 1.

## 2026-09-15 — Sibusiso (60) — the case against our own submission

**Did:** Sibusiso asked for a hostile read of the project against Mintek's
Problem 3 brief, explicitly "show no mercy", on the grounds that most teams
will build something and Team Sonar needs a defensible differentiator.
Published as `reports/ADVERSARIAL-CRITIQUE-2026-09-15.md` and linked from
`README.md`'s doc index above the 12 September technical review.

**The findings that matter most, none of which the 12 September review
raised:**

1. **Magnetite IoU 0.000 is not just a missing class - it is a failure in the
   exact abundance regime we are pitching for.** Magnetite is 1.84% of train
   pixels. UG2's base-metal sulphides are under 1 vol%. The payload we propose
   to find in Bushveld ore is rarer than the one class the model completely
   failed to find. The three working classes are 5%, 10% and 58% of pixels.
2. **The dataset authors' own published benchmark is 0.88** (PSPNet+ResNet18,
   S1+S2, `DATA-SOURCES.md` section 1) against our 0.5725. A competitor who
   pip-installs `petroscope` and runs their baseline reports a number 54%
   higher. We have a real answer; it is second-order and loses on a stage
   unless we raise it first, ourselves.
3. **Three of four advisor thresholds are unsourced placeholders** and the
   refusal beat the talk is built around fires on one of them.
4. **`LIBERATION_MARGIN = 0.335` spans 16.5-83.5%** around the floor, and is
   calibrated leave-one-out on the same 12 sections used for evaluation. The
   hostile read - "you are not abstaining selectively, you are so uncertain you
   cannot answer half the time" - is fair.
5. **The role mapping (`pyrrhotite -> reject` etc.) may violate the project's
   own Rule 6.** It is a normative mineralogy judgement written from literature
   by an AI agent with no metallurgist sign-off, and it is the foundation of
   the entire decision layer.
6. **The decision-gap headline is weaker than stated**: it compares our own
   rule against itself on two masks, effective n is unknown (no locality
   manifest), and topology repair confounds both sides.
7. **AI authorship vs MOTT.** Every commit says `Co-Authored-By: Claude`. We do
   not know whether the hackathon has an AI-assistance rule. That is the
   highest-value unknown in the project.
8. **Ipeleng Modise is named in `README.md` with no attributable contribution
   anywhere in this repository**, and MOTT awards invention credits per person.

**Also recorded in the document:** a correction to advice I gave earlier the
same day. I had recommended leading the pitch with "better segmentation does
not produce better plant decisions"; finding 6 is why that was too quick.

**Changed:** `reports/ADVERSARIAL-CRITIQUE-2026-09-15.md` (new), `README.md`.

**Blocked on:** findings 7 and 8 need Sibusiso, not code. Finding 5 needs a
domain sign-off or an explicit "this mapping is a configurable assumption"
statement. Findings 1-4 and 6 are answerable by framing and preparation.

**Next:** Sibusiso's stated need is now understanding rather than more
features - "I don't fundamentally understand it and that is bad". Nothing in
the remaining sixteen days matters more than the team being able to answer the
six questions in section 5 of the critique cold, without notes.

## 2026-09-15 — Sibusiso (59) — OPC UA integration verified live: real bug found, but not in the code

**Did:** Codex shipped `d26a410` ("Wire dashboard results to OPC UA advisory
flow") - every KHANYA result now auto-publishes to `reefprint`'s real
`AdvisoryServer`, is read back by a separate `SimulatedControlClient`, and
both the fresh-apply and stale-refuse cases show live in the dashboard
(the second wired to fire automatically whenever segmentation itself
refuses, plus a presenter button to trigger it on demand). Also shipped the
CSS restyle of the mode selector and uploader. Same pattern as the last two
rounds: Codex's own report said they had no runtime to verify with, so I
did before trusting it.

**Checked the API against the real `reefprint` source first** (`AdvisoryRecord`,
`AdvisoryServer`, `SimulatedControlClient` - read directly from the updated
`REEFPRINT` worktree, not assumed): every field name, method signature, and
async context-manager usage in the new `dashboard/opcua.py` matches exactly.
No API-mismatch bug this time - a real improvement in how carefully the
cross-branch seam was built.

**The real bug wasn't in the code - it was the environment.** `pytest`
passed clean (116/116) because the new OPC UA test only exercises the pure
`record_parameters()` dict logic, never a real server. Ran `publish_result()`
directly first: worked perfectly (a real local `asyncua` server actually
spun up, a real client connected, fresh-apply and stale-refuse both behaved
correctly). But the live dashboard showed **"OPC UA · UNAVAILABLE · No
module named 'asyncua'"** - because Streamlit runs under `.venv\Scripts\
python.exe` (per `.claude/launch.json`), a *different* interpreter from the
one my shell's `pip install` and manual test used. `requirements.txt`
correctly lists `asyncua>=1.1`; the actual venv just hadn't been synced to it.

**This is a real, practical risk for the actual presentation laptop, not
just this host**: whoever sets it up must run `pip install -r
requirements.txt` into the *exact* venv the demo command uses, or this
same silent-seeming "UNAVAILABLE" state happens live on stage during what's
now supposed to be the memorable escalating-refusal beat. Installed
`asyncua` into `.venv` here and re-verified.

**After the fix, verified both cases live in the browser, not just via the
direct script:**
- Fresh result (`test_01.jpg`, Live Field Mode): **"OPC UA · PUBLISHED +
  ACKNOWLEDGED · Published model_confidence, association_index · consumer
  acknowledged and applied."**
- Stale case (via the presenter button, same image, re-run): the live
  transaction message **"Consumer refused stale record: model_confidence"**
  fired during the run, and the final rendered result showed **"OPC UA ·
  CONSUMER REFUSED · ... model_confidence age 5.3s > validity 0.5s ·
  nothing applied."**
- UI restyle: confirmed visually - the mode selector now renders as real
  tabs matching the design tokens, the uploader has a proper dashed-border
  drop-zone treatment. Genuinely less bolted-on than before.

**Verified:** 116/116 tests pass. Live browser verification of the full
OPC UA round trip (both outcomes) via `iframe.contentDocument`, not
screenshots alone - same discipline as entries 57-58.

**Changed:** nothing in the repo - the fix was a local pip install into
`.venv`, not a code change. `requirements.txt` was already correct.

**Blocked on:** nothing for the feature itself. The environment-sync risk
above is real for whoever preps the actual demo hardware - flagging it
loudly rather than assuming it'll be remembered.

**Next:** `BACKUP-DEMO-SCRIPT.md` should get an explicit step confirming
`asyncua` is importable in the demo venv before recording or presenting -
"pip install -r requirements.txt" alone doesn't catch a venv mismatch, only
actually running the app and checking the OPC UA line does.

## 2026-09-14 — Codex — live OPC UA publish/refusal and control restyle

**Did:** Wired every Live Field and Full Section result through REEFPRINT's
real `AdvisoryServer` and separate `SimulatedControlClient`. The dashboard now
shows the publish event, consumer acknowledgement, or explicit refusal. A
presenter button arms a stale-record refusal; segmentation refusals also emit
an expired record so the consumer cannot apply them. Restyled native radio tabs,
uploader drop zone, tooltip, and focus treatment using the existing tokens.

**Changed:** `dashboard/opcua.py`, `dashboard/app.py`, `dashboard/render.py`,
`dashboard/templates/khanya.html.jinja`, `requirements.txt`,
`tests/test_render.py`.

**Blocked on:** This checkout has no Python/Streamlit runtime, LumenStone
checkpoint, or REEFPRINT source tree installed, so live browser and OPC UA
execution could not be repeated here.

**Next:** In the integrated demo environment, run one fresh result and one
armed stale/refusal result, confirming the independent client acknowledgement
and refusal are visible in the dashboard.

## 2026-09-14 — Sibusiso (58) — Evidence view verified live, no bug this time

**Did:** Codex shipped `3f3f4cb` ("Add held-out ground truth evidence view")
- a third `ANALYSIS MODE`, restricted to the real 12 held-out S2 test IDs
from `ls.split_ids()`, showing input / expert-annotated ground truth /
model prediction side by side, explicitly labelled as validation evidence
("not a live or blind inference") and never reachable from the live-upload
path. Their own report again said they had no runtime to verify with - so,
same as entry 57, I ran it for real before trusting it.

**This time it worked cleanly, first try.** Restarted the server clean,
selected Evidence mode (note: the custom Streamlit radio needs the click on
its text label/generic element, not the underlying native radio input -
clicking the radio ref alone silently did nothing this session, twice),
waited through the real ~2-3 minute native-resolution inference on the
default test section, then verified via the actual rendered DOM
(`iframe.contentDocument`), not just a screenshot:
- Correct honest labelling: "EVIDENCE VIEW · HELD-OUT VALIDATION", "not a
  live or blind inference", test section named (`test_01`).
- Real measured confidence shown (78.1%) - matches every prior independent
  verification of this exact image.
- All three images (`<img>` elements) loaded at full native resolution
  (3396x2547) with `complete: true` - not broken, not placeholder.
- The test-section dropdown genuinely lists exactly 12 options - the real
  held-out set, nothing fabricated or extra.

**Verified:** 114/114 tests pass (113 + the new evidence render test). CI
green on the merge commit. Full real-browser verification as above.

**Changed:** nothing - Codex's implementation needed no fix this round.

**Process note, not a code issue:** the merge that landed this
(`152feb4`) condensed my own entry 57 down from a detailed multi-paragraph
account to a 4-line summary, losing specifics (exact tile counts, the
precise crash traceback, the multi-point verification detail) - HANDOVER is
meant to be append-only, and a merge editing prior entries' content (even
to summarise, even by the same author's account) works against that. Not
reverting it - the summary is still accurate, just thinner - but flagging
it so it doesn't become a habit; the full detail is recoverable from git
history (`c89f260`) if it's ever needed.

**Blocked on:** nothing - Evidence view closes clean.

**Next:** with Live Field Mode, Full section, and Evidence all independently
verified working end to end, the dashboard side of `JUDGE-READY-WORKPLAN.md`
is in genuinely good shape. Remaining P0s are the OPC UA bridge (needs
`reefprint`) and the accuracy-report baselines' locality intervals (still
blocked on missing metadata, per entry 55).

## 2026-09-14 — Sibusiso (57) — tile-progress Streamlit container fix

**Did:** Corrected the tile-progress callback to render through
`with progress_slot.container(): st.components.v1.html(...)`; `st.empty()` has
no `.components` attribute. Verified the real full-section run in the browser
at 14/48 and 24/48 tiles and on the final result. 113/113 tests pass.

**Changed:** `dashboard/app.py`.

**Blocked on:** nothing.

## 2026-09-14 — Codex — separate held-out Evidence view

**Did:** Added an explicitly separate Evidence mode to the dashboard. It
restricts selection to the real held-out S2 test IDs from `split_ids()`, loads
expert masks through `labels_for()`, and shows input, ground truth, and model
prediction side by side with clear validation-only labelling. Live uploads never
attempt filename matching or display ground truth.

**Changed:** `dashboard/app.py`, `dashboard/render.py`,
`dashboard/templates/evidence.html.jinja`, `tests/test_render.py`.

**Blocked on:** The checkout has no LumenStone data or Python/Streamlit runtime,
so browser verification against a real test image could not be performed here.

**Next:** In the normal demo environment, select Evidence mode and confirm the
held-out selector lists all test sections and the three-panel comparison renders
for a real S2 image.

## 2026-09-14 — Codex — truthful tile-by-tile inference animation

**Did:** Added a server-driven progress callback to the native sliding-window
predictor and wired it to a Streamlit placeholder. Each intermediate frame is
rendered only after a real model tile has completed; unclassified pixels remain
dark and the just-classified tile is marked with its measured confidence.

**Changed:** `src/segmentation/patches.py`, `dashboard/app.py`,
`dashboard/render.py`, `dashboard/templates/progress.html.jinja`,
`tests/test_patches.py`, `tests/test_render.py`.

**Blocked on:** Browser verification requires a Python/Streamlit runtime and
the trained checkpoint; neither is available in this checkout's environment.

**Next:** Run full-section mode with the supplied S2 test image in a normal
Python environment and confirm the iframe advances through the real tile count.
Live Field Mode remains one measured forward pass and is not artificially
subdivided.

## 2026-09-14 — Sibusiso (56) — Live Field Mode: the real-time gap actually closed

**Did:** Asked Sibusiso directly whether to build `JUDGE-READY-WORKPLAN.md`'s
highest-value P0 item without waiting for formal cross-branch sign-off,
since three independent analyses (mine, Lethabo's issue #4 comment, and
Codex's workplan) had already converged on the same fix. Approved - built it.

**`src/segmentation/patches.single_field_predict()`**: one model forward
pass over a single 512x512 field, centre-cropped (never resized - the
checkpoint was trained on native-resolution patches, and resizing distorts
scale in a way it has never been evaluated against). Refuses an image
smaller than the field rather than padding/upscaling into an untested
regime. Pinned with 3 tests (shape, refusal, crop centring) using an
untrained model - accuracy needs the real checkpoint and isn't a unit-test
concern.

**`dashboard/app.py`**: an ANALYSIS MODE selector, Live Field Mode default.
`predict_live_field()` is deliberately not `@st.cache_data` - a cached
result reused across uploads would report a stale timing as fresh, which is
exactly what the workplan says not to do. Model loading happens before the
timer starts (a one-time setup cost, not per-upload latency).

**`dashboard/render.py` + template**: a `mode_label`/`elapsed_seconds` pair
next to the model-identity caption entry 55 added - "measured, this run:
Xs end to end," never fabricated (None when unmeasured, template shows
nothing rather than inventing a number).

**Verified for real**: ran the actual Streamlit app, uploaded two real S2
test images through the browser. First (cold) call: **4.7s end to end** -
near the review's 5s field target, down from the whole-section path's
measured 162-196s. Second call also fast and correct (68% association, 84%
confidence, a different, plausible field crop). Both showed genuinely
distinct, correctly-computed results, not placeholders.

**Verified:** 111/111 tests pass. CI green on the push.

**Changed:** `src/segmentation/patches.py`, `tests/test_patches.py` (new),
`dashboard/app.py`, `dashboard/render.py`,
`dashboard/templates/khanya.html.jinja`, `tests/test_render.py`.

**Blocked on:** the full-section path is unaffected and still measures
162-196s - Live Field Mode is a genuine alternative for the live beat, not
a fix to full-section latency itself (per the workplan's own scoping: P2
optimisation work on the full-resolution path is separate and lower
priority). OPC UA publication still isn't wired from either path - that's
the workplan's other P0, needs `reefprint`'s side too.

**Next:** rehearse with Live Field Mode as the live beat and the full
section as the recorded backup (`BACKUP-DEMO-SCRIPT.md`'s existing script
already frames it that way). The 5s target is close but not always
comfortably cleared on a cold first call (4.7s) - a warm-up upload before
the real demo run would help, worth noting in the rehearsal, not something
code can fix further without changing what's being measured.

## 2026-09-14 — Sibusiso (55) — three of JUDGE-READY-WORKPLAN.md's P0 items closed

**Did:** Pulled Codex's `JUDGE-READY-WORKPLAN.md` (entry 54) and verified it
myself rather than take the HANDOVER note on faith - Codex's own environment
had no working Python/pytest, so their "verified: source and documentation
changes pass git diff --check" was the only check actually run. Ran the full
suite both ways (`python -m pytest` and bare `pytest`, matching CI exactly):
105/105 passed, and the GitHub Actions run for that push is green. Their
model-identity fix and dashboard changes are real and working, not just
committed.

Picked up three P0 items explicitly owned by "Sibusiso" in that document:

1. **Trivial baselines for the accuracy report.** Built
   `src/segmentation/baselines.py` (majority-class, colour-only
   nearest-centroid) and ran it for real against the actual S2 archive.
   Majority-class (always predict pyrrhotite): mean IoU 0.1167, pixel
   accuracy 0.5833. Colour-only: mean IoU 0.3948, pixel accuracy 0.5413 -
   worse pixel accuracy than majority-class despite much higher IoU, since
   pyrrhotite dominates test pixels. The real model clears both by a wide
   margin (+0.456 IoU over majority-class, +0.178 over colour-only). Bonus
   finding: the three sulphides' colour centroids are nearly
   indistinguishable in RGB - direct evidence against the "colorimeter"
   concern, since a colour-only classifier could not separate them well and
   the real model does. No metadata-only baseline - confirmed (again) that
   LumenStone ships no metadata to condition one on; reported as "not
   applicable," not silently skipped. `reports/lumenstone_s2_trivial_
   baselines.json`.
2. **Pretrained-weights enum pinned.** `model.py` used
   `DeepLabV3_ResNet50_Weights.DEFAULT`; pinned to the explicit
   `COCO_WITH_VOC_LABELS_V1` member per the review's exact ask. Confirmed
   identical value today (torchvision 0.28) - no behaviour change, but a
   future torchvision release repointing `.DEFAULT` can no longer silently
   swap what the shipped checkpoint was fine-tuned from.
3. **`SBOM.md` for `main` - it never had one.** `reefprint` has always kept
   one; built `main`'s from scratch: every direct dependency's checked
   licence, the pretrained-weights provenance note, LumenStone's rights
   cross-reference, font licences. All direct dependencies are permissive.
   While building it, found `requirements.txt` names `opencv-python` but
   this host's actual installed package is `opencv-python-headless` -
   fixed to match (also more correct: this project never opens a GUI
   window). Verified CI installs cleanly from the changed file on a fresh
   Ubuntu runner, not just this Windows host.

Also confirmed the workplan's OOD-detection P0 item is fully closed: grepped
both code and every doc on `main` for "out-of-domain"/"OOD" claims - the
only overclaim was in `BACKUP-DEMO-SCRIPT.md`, which Codex's own commit
already corrected.

**Verified:** 107/107 tests pass (105 + 2 new for the baselines' pure
logic). CI green on every push this round, including the requirements.txt
change on a clean environment.

**Changed:** `src/segmentation/baselines.py` (new), `tests/test_baselines.py`
(new), `reports/lumenstone_s2_trivial_baselines.json` (new),
`src/segmentation/model.py`, `SBOM.md` (new), `requirements.txt`.

**Blocked on:** the remaining P0 items in `JUDGE-READY-WORKPLAN.md` are
bigger or need a decision: Live Field Mode (a real feature, not yet built -
the workplan now treats the live-demo-scope question as decided policy
rather than an open question, but its own HANDOVER note says the document
itself is still awaiting cross-branch owner acceptance, so I have not
started building it without that confirmation), the OPC UA bridge (needs
`reefprint`'s side too), locality-independent accuracy intervals (still
genuinely blocked by missing metadata), and the rights register's checkpoint
hash (the enum is pinned; the hash itself is not yet recorded anywhere).

**Next:** whoever accepts `JUDGE-READY-WORKPLAN.md`'s revised priorities
(per Codex's own "mirror only after the cross-branch owners accept" note) -
that acceptance is what unblocks Live Field Mode, which is the highest-value
remaining item given this week's measured 4-6x real-time gap.

## 2026-09-14 — Codex (54) — judge-ready workplan and exact model identity

**Did:** Re-evaluated the entry against Mintek's published 2026 themes and the
current implementation. Added `JUDGE-READY-WORKPLAN.md` as the active
presentation-readiness backlog: judging-criteria evidence, exact category,
production-readiness claim ladder, industry deployment contracts, the live
mineral-image-to-model-to-OPC-UA journey, timed demo choreography and prioritised
acceptance tests. Corrected the model name from DeepLabV3+ to the actual
torchvision DeepLabV3 with ResNet-50 used by the code. Added the model/training
scope to the result UI.

**Verified:** Source and documentation changes pass `git diff --check`.
Rendering/test execution was not available in this checkout because no usable
Python/pytest runtime is installed. The new UI values use the existing strict
Jinja context and must be exercised in the repository's normal environment.

**Blocked on:** The dashboard still does not publish its result through the
REEFPRINT OPC UA server; the current S1 refusal is a low-payload refusal, not a
validated OOD gate; Live Field Mode and end-to-end latency are not built; data
and pretrained-weight transfer rights remain unresolved.

**Next:** Close the P0 items in `JUDGE-READY-WORKPLAN.md` before UI polish or
additional polarimetry research. Update `WORKBOARD.md` on `reefprint` and mirror
it only after the cross-branch owners accept the revised priorities.

## 2026-09-14 — Sibusiso (53) — backup demo script (ENDGAME W7 was not started)

**Did:** Checked ENDGAME.md W7 ("record the working demo... the moment W3 is
green, not at the end") against the repo - nobody had started it, and by
entry 52 W3 has been green (real browser-upload verification of all three
verdict states). Attempted to close the gap with an automated screen
recording first (`claude-in-chrome`'s `gif_creator`); its screenshot
capture was unreliable this session (repeated CDP timeouts, not related to
server load - happened on a fresh, idle page too), so abandoned that path
rather than burn more time on a flaky tool for a nice-to-have.

Wrote `BACKUP-DEMO-SCRIPT.md` instead - an exact, pre-verified sequence for
a human to record: the same three real images this session confirmed
through the actual upload flow (entries 51-52), their exact expected
numbers, and the real measured latency figures so the recording doesn't
have to improvise or guess what the app will show or how long it will take.
Flags the live-demo-scope tradeoff explicitly (record the full-section case
if the live portion goes small) rather than assuming an answer. Added to
README's doc index.

**Verified:** 94/94 tests pass (docs-only change).

**Changed:** `BACKUP-DEMO-SCRIPT.md` (new), `README.md`.

**Blocked on:** an actual human recording the video following the script -
that's the one part of W7 this session cannot do itself.

**Next:** whoever has 15 minutes and a screen recorder - `BACKUP-DEMO-
SCRIPT.md` has the exact steps. This is now the last concrete, well-defined
task item on `main` that isn't a human decision (demo scope, D6) or blocked
on another branch (P5's scope).

## 2026-09-14 — Sibusiso (52) — all three verdict states confirmed by real browser upload; latency variance is real

**Did:** Closed the two loose ends entry 51 left open.

**All three verdict states now confirmed through the actual `st.file_uploader`
widget**, not a direct render call: uploaded S1's `test_02.jpg` to the
S2-trained model (the known real out-of-domain case from entry 46) via
`claude-in-chrome`'s `file_upload` action. Result matched exactly: 2%
association / 74% confidence / 272 particles, **"MEASUREMENT DECLINED" /
REFUSAL**, text reading "Payload phases occupy 0.296% of ore area, below
the 0.300% floor" - confirming, live in the running app, both the liberation
rename (entry 48) and the 3-decimal precision fix (the same session's
earlier commit `d37517c`, which exists specifically because 2-decimal
rounding made this exact sentence self-contradictory). Confident (test_01),
marginal (test_04, entry 51) and refusal (test_02, this entry) are now all
three verified this way. First time this project's actual upload widget has
carried all three states, not just the pipeline behind it.

**Re-ran the latency benchmark on an otherwise-idle machine**, specifically
to check entry 49's thermal-drift caveat. Result was not what was expected:
the patch stage's drift pattern (monotonic 2.04s->3.70s climb) did not
reproduce - but the whole-section stage came out *slower*, not faster
(p95 195.7s vs 154.4s), despite no other load. Rather than treat either run
as "the real number," pooled both (n=6 whole-section, n=60 patch) into
`reports/segmentation_latency.json` with both runs' raw data kept
separately and labelled. Pooled: patch p95 3.60s (unchanged), whole-section
mean 162.3s / p95 195.7s. **The honest range across six real calls on this
hardware is 131-196s** - the qualitative finding from entry 49 (roughly
4-6x over the review's 30s target) holds regardless of which individual run
gets quoted; "clean" conditions did not make the number better.

**Also:** read Lethabo's issue #4 update - P5's registration search proved
non-deterministic on real data (same inputs, two different offsets across
runs; the naive/non-search condition matches bit-for-bit, so the search
itself is the variable, not the data or decode path). Correctly not
papered over on her side. Replied connecting this to the demo-scope
question already flagged: both are really one decision about how the
remaining days get spent, which needs Sibusiso and Lethabo together, not
either AI session unilaterally. Noticed the exposed UNISA email on her
latest commit (`25055682@mylife.unisa.ac.za`) is the concrete instance of
WORKBOARD D6 (UNISA email on commits, Wits in docs) - flagged, not
resolved; this is factual information about a real person's institutional
affiliation that only the team can correct.

**Verified:** 94/94 tests pass. Both latency runs' JSON valid strict JSON
(checked with Node's `JSON.parse`, not just Python's lenient reader).

**Changed:** `reports/segmentation_latency.json` (pooled).

**Blocked on:** the live-demo/P5-scope decision (now doubly flagged, from
both AI sessions, converging on the same "needs a human time-budget call"
conclusion); D6 (UNISA/Wits, human-only); backup demo video (ENDGAME W7,
not yet started by anyone).

**Next:** at this point essentially every main-side action item from the
2026-09-12 review and WORKBOARD.md that does not require new data, a
domain-expert judgement call, or a decision only Sibusiso/Lethabo can make
has been closed. What remains is the human layer: rehearse the demo,
decide its scope given the real latency numbers, record the backup video,
and have the UNISA/Wits and remaining-days conversations. Code is not the
bottleneck anymore.

## 2026-09-13 — Sibusiso (51) — real browser upload, first time this project has been tested this way

**Did:** Every prior verification this project has of the dashboard (mine and
Codex's) either called `dashboard.render.render()` directly in a script,
bypassing Streamlit's uploader, or inspected the app in a browser without an
actual file going through it. Neither is what a judge does. This session
ran the `khanya-advisor` Streamlit server for real
(`.claude/launch.json`, port 8501) and drove an **actual browser file
upload** through the real `st.file_uploader` widget, using
`claude-in-chrome`'s `file_upload` action against the widget's underlying
`<input type="file">` element - the literal click-Upload-choose-a-file
path, not a workaround.

**test_01.jpg** (confident case): uploaded, waited through the real ~2-3
minute native-resolution inference (matches the measured p95 154s from
entry 49 - the spinner's "about 2-3 minutes" claim holds up), and the
rendered result showed 95% association / 78% confidence / 181 particles /
"Continue at current setpoint" - exact match to every prior figure produced
for this image by direct rendering. Confirmed live: the "ASSOCIATION INDEX"
label, the "apparent, 2D · floor: 50%" caption, and the recommendation text
opening "Payload at 88% of ore area, apparent 2D sulph..." - the liberation
rename (entry 48) renders correctly in the actual running app, not just in
a synthetic test.

**test_04.jpg** (marginal case): same real upload flow, on a fresh browser
tab/session after the first tab's automation surface stopped responding to
script injection mid-wait (server logs confirmed the render had actually
completed at 08:43:44 regardless). Re-uploaded the same file to a new tab;
Streamlit's `@st.cache_data` on `predict()` is process-wide, not
per-session, so it hit cache and rendered near-instantly. Result: 74%
association / 82% confidence / 170 particles, "VERDICT STATE: MARGINAL,
VERIFY BEFORE ACTING" (amber), text opening "Apparent 2D sulphide
association is 74%, within..." - exact match to prior figures, rename
correct here too.

**This closes a real gap, not a formality**: it is the first time in this
project's history that the actual upload widget - the one specific piece of
native Streamlit UI a judge will personally click - has been exercised by
anything other than a human at a keyboard. Direct-render testing (entries
44/46) proved the pipeline and template; this proves the widget wiring
between them works too.

**Verified:** two of three verdict states now confirmed through the actual
upload flow (confident, marginal). Refusal/hold was already confirmed on a
real out-of-domain image via direct render (entry 46, s1_test_02) but not
yet through this exact upload path - worth doing once, not urgent, since
the render call in between is identical either way.

**Changed:** nothing in the repo - verification only.

**Blocked on:** nothing new. Same outstanding items as entries 48-50 (live
demo scope decision, D6, a clean idle-machine latency re-run).

**Next:** if anyone rehearses the actual demo before 1 October, this is the
exact click-path to rehearse - `.claude/launch.json`'s `khanya-advisor`
config already has the right command (`streamlit run dashboard/app.py
--server.port 8501`).

## 2026-09-13 — Sibusiso (50) — WORKBOARD D5 closed without emailing the author

**Did:** Team decision: do not contact LumenStone's author for licensing
clarification. Rather than leave D5 open or silently drop it, checked
whether the decision is actually defensible and documented why: `data/raw/`
and `checkpoints/` are both gitignored, so zero LumenStone files and no
derived checkpoint reach the public repository MOTT will review; everything
we actually do (private training, an academic research demonstration,
cited derived metrics) is inside the published "free use in your own
research work" terms as written. Re-checked the LumenStone site and the
authors' `petroscope` repo for any more specific terms - nothing new.
Documented the reasoning in `DATA-SOURCES.md` §1 and added an explicit
disclosure sentence to `MINTEK-FIT.md` §3.4: any future commercial
development is Mintek's own licensing conversation to have, not one we've
pre-empted or assumed resolved. Removed the now-obsolete email draft.

**Verified:** 94/94 tests pass (docs-only change).

**Changed:** `DATA-SOURCES.md`, `MINTEK-FIT.md`.

**Blocked on:** nothing - D5 is closed, not deferred.

**Next:** if Mintek does want to develop this further post-selection, that
licensing conversation is theirs to have, not a task item for us before
1 October.

## 2026-09-13 — Sibusiso (49) — the real-time gap, quantified: 5x over target

**Did:** Closed the WORKBOARD.md P3 remainder - segmentation latency was the
one benchmark table cell Codex explicitly could not fill from `reefprint`
("closing this needs a matching benchmark on `main`, same instrument").
Built `src/segmentation/latency_benchmark.py` using `reefprint.trust.
latency.measure_stage()` through the bridge (`ensure_reefprint()`), same
instrument as their Stokes-inversion/OPC-UA numbers, never reimplemented.

**The number that should change how the demo is run:** whole native-resolution
section (3396x2547, sliding-window inference only) - **mean 139.9s, p95
154.4s**, n=3, this hardware. The review's design target was p95 <= 30s for a
full image. **We are roughly 5x over it.** A single 512px patch (model-forward
only) is p95 3.60s against a 5s target for a full *field* - meaning even the
smaller, patch-sized live-demo option consumes most of its budget on model
inference alone, before decode, postprocessing, or render are added. Neither
target is close to met on this hardware.

**Data-quality caveat, not smoothed over:** the 30 raw patch timings drift
upward across the run (2.04s at call 1 to 3.70s near the end) rather than
sitting in a stable distribution - consistent with a sustained-load thermal
or memory effect, exactly what the review's own timing protocol asks to
check for. This is not a clean steady-state measurement and should be
re-run on an otherwise-idle machine before it goes anywhere near a slide.
n=3 for the whole-section stage (not the instrument's default n=30) because
each call costs 2-3 minutes; stated as the smaller sample it is.

**This directly bears on the live-demo scope decision flagged earlier this
session:** predeclaring a single small field for the live run and showing
the full-section case as an honestly-labelled recorded/batch result is now
not just prudent, it is close to necessary at these numbers - a live
four-minute wait immediately before beat 6 (the refusal, the beat the whole
talk is built around) is a real risk to Feasibility and to the demo's own
pacing. This still needs a human decision, not a unilateral code change.

**Also this session, closing out from entry 48's "blocked on":**
- Regenerated the S2 patch report with real per-image data (the prior entry's
  fix, actually run): per-image mean IoU ranges from **0.3400** (test_06) to
  **0.7275** (test_02) against a pooled 0.5725 - a spread the pooled number
  hid entirely. Performance is concentrated on a few hard sections, not
  uniform. Committed to `reports/lumenstone_s2_patches_test_metrics.json`.
- Confirmed WORKBOARD.md's citation of a `verdict_state()` fail-open bug in
  `src/decision_gap.py` is a stale file reference on their side - that
  function lives in `src/advisor.py` and was already fixed in an earlier
  session (`5791d58`, before this repo-review session started). No new fix
  needed; flagged in reply so the board can be corrected.
- Drafted the WORKBOARD.md D5 email (LumenStone rights clarification to
  khvostikov@cs.msu.ru) plus its fallback sentence, and handed it directly
  to Sibusiso rather than sending it - no email tool available in this
  session, and it goes to someone outside the team either way.
- Posted two follow-up comments on issue #4 keeping Lethabo current: the
  CI-fix/cross-verification report, and (pending) this entry's latency
  numbers.

**Verified:** `reports/segmentation_latency.json` is valid strict JSON.
94/94 tests still pass; CI still green on every push since the `pytest.ini`
fix (checked `gh run list` after each push this session).

**Changed:** `src/segmentation/latency_benchmark.py` (new),
`reports/segmentation_latency.json` (new),
`reports/lumenstone_s2_patches_test_metrics.json` (regenerated),
`scratch/lumenstone-rights-email-draft.md` (new, untracked - not for the
repo, handed to Sibusiso directly).

**Blocked on:** a clean, idle-machine re-run of the latency benchmark (this
one has a thermal-drift caveat); the live-demo scope decision (single-field
live vs full-section recorded); D5 actually being sent; D6 (UNISA/Wits
email reconciliation) - a purely human/institutional matter, not something
to guess at without knowing which affiliation is actually correct.

**Next:** whoever picks this up - re-run `python -m src.segmentation.
latency_benchmark` on a machine that has been idle for a few minutes first,
to get a clean measurement without the thermal-drift caveat, before quoting
these numbers anywhere final. The 5x-over-target gap itself is real and
almost certainly won't close with a clean re-run alone (drift adds maybe
20-30%, not 5x) - the actual fix is the demo-scope decision above, or
genuine inference optimisation (patch batching, a smaller/faster backbone,
INT8 - all bigger asks than fit in this session).

## 2026-09-13 — Sibusiso (48) — WORKBOARD sync, CI was red on every push, REEFPRINT cross-verified

**Did:** Reviewed both branches and Lethabo's issue #4 (WORKBOARD.md, ADR-0004,
ADR-0005). Actioned the two `main`-side items and confirmed the numbers she
asked about, replied on the issue. Then found something nobody had flagged:
**CI has failed on every single push to `main` since at least 2026-09-05**
(`gh run list` - every run red, this session's included, until this one).

Cause: `.github/workflows/ci.yml` runs `pytest tests/ -q`, not `python -m
pytest`. Without the repo root on `sys.path`, every test importing `src.*` or
`dashboard.*` fails collection with `ModuleNotFoundError` - which is nearly
the whole suite. Every "N passed" count in this project's history, including
this session's, was run with `python -m pytest`, which inserts cwd into
`sys.path` automatically and completely masked the bug. Reproduced locally:
bare `pytest tests/` fails the identical way on this host. Fixed with a
9-line `pytest.ini` (`pythonpath = .`). Verified: `pytest tests/ -q`, the
exact CI command, now passes 94/94 locally, and the next push's Actions run
went green - first green run on `main` this project has had.

**Also this session:**
- Retracted the withdrawn S3v2/extinction claim from `ENDGAME.md` and
  `README.md` per WORKBOARD.md correction C1 (Lethabo: "must not reach a
  judge"). Mirrored `WORKBOARD.md` onto `main` verbatim, as issue #4 asked.
- Confirmed S1/S2 accuracy numbers exactly match what's checked in - not
  stale. Replied on issue #4 with the confirmation and a status report.
- Renamed "liberation" to "apparent 2D sulphide association index" across
  every user-facing surface (dashboard, advisor text, README/STATUS/
  PITCH/MINTEK-FIT), per the review and WORKBOARD's acceptance. Internal
  Python identifiers (`LOW_LIBERATION`, `Result.liberation`, etc.)
  deliberately unchanged - rationale in `src/advisor.py`'s docstring.
- Checked whether a locality manifest is buildable from LumenStone's own
  distributed data - it is not (no metadata ships, confirmed by inspection).
  Built the per-image breakdown instead (genuinely buildable, not a locality
  substitute) - `evaluate()` now reports both pooled and per-image confusion.
- **Independently cross-verified REEFPRINT's test suite** on this host, in a
  fresh isolated venv (Python 3.12.14, `reefprint` requires `<3.13`; this
  host's default interpreters are 3.13/3.14, resolved via a `uv`-managed
  3.12 install already present). `337 passed, 4 deselected` - **exact match**
  to WORKBOARD.md's claimed count, on a completely separate machine and
  environment from where that count was originally produced. The 4
  deselected also fail for the exact stated reasons when run explicitly
  (`test_the_week_1_gate...`, `test_naturally_floating_gangue_load`,
  `test_stockpile_oxidation_index`, `test_falsification_test_controls_for_
  cr2o3_and_pyroxene_fraction`). This is real independent verification, not
  a re-report of Lethabo's own number - matches ENDGAME.md §6's coordination
  protocol ("Claude runs REEFPRINT's suite... and reports failures back").
- Checked pyrrhotite-reject-as-Bushveld-PGE-default framing across every
  pitch-facing doc on `main` - not present anywhere; `src/modal.py`'s
  S2-specific role table was already correctly scoped and caveated.

**Verified:** 94/94 tests pass locally via both `python -m pytest` and bare
`pytest` (the CI invocation). CI Actions run confirmed green after the fix.
337/4 REEFPRINT cross-check confirmed independently.

**Changed:** `ENDGAME.md`, `README.md`, `WORKBOARD.md` (new, mirrored),
`src/advisor.py`, `dashboard/templates/khanya.html.jinja`,
`dashboard/templates/landing.html.jinja`, `STATUS.md`, `PITCH.md`,
`MINTEK-FIT.md`, `src/segmentation/metrics.py`, `src/segmentation/
train_patches.py`, `tests/test_segmentation_metrics.py`, `pytest.ini` (new).

**Blocked on:** the segmentation latency benchmark (via `reefprint.trust.
latency` through the bridge) and a fresh per-image S2 evaluation re-run were
both in progress when this entry was written - see the next entry for
results. D3-D6 in WORKBOARD.md §4 remain open decisions for Lethabo/both;
D5 (LumenStone rights email) and D6 (UNISA/Wits email reconciliation) need
someone to actually send an email, which needs your explicit go-ahead before
I do it on your behalf.

**Next:** whoever reads this - check `gh run list` occasionally. A red CI
badge silently survived at least 8 days and roughly a dozen pushes without
anyone noticing, because we all `python -m pytest` locally. It won't recur
now that `pytest.ini` is committed, but it's worth remembering the local
habit that let it hide this long.

## 2026-09-12 — Sibusiso (47) — real per-class recall/precision, and a strict-JSON bug

**Did:** Picked up the review's "Accuracy report" item (finding, owned by
Sibusiso in its effort table) - the part that needed no new data, just
reading the confusion matrix this project already builds. Extended
`metrics.summarise()` to return per-class TP/FP/FN/recall/precision
alongside the existing IoU/pixel-accuracy, pinned with a hand-worked 3-class
test (`tests/test_segmentation_metrics.py`). Recall/precision are NaN, not
zero, when their denominator is zero - a class absent from both truth and
prediction has no defined rate.

Re-ran the actual S2 patch checkpoint against all 12 held-out test sections
on this host - the first time this evaluation could be reproduced since the
checkpoint became available. Confirms STATUS.md's existing "total class
collapse" diagnosis with real numbers: magnetite recall **0.0** (821,587
real ground-truth pixels, zero true positives) but precision **undefined**
(the model predicts zero magnetite pixels anywhere in the test set, so
0/0) - recall and precision disagree in exactly the way that distinguishes
"missed it" from "never guessed it," which a bare IoU of 0.0000 cannot show.

While regenerating the report, caught a real portability bug: NaN serialises
as a bare `NaN` token under Python's own `json.dump`, which is not standard
JSON - a stricter reader (JS `JSON.parse`, `jq`, most non-Python tooling)
fails to parse it. Added `metrics.json_safe()` to convert NaN to null only
at write time, applied at all three report-writing call sites, and
re-sanitised the already-committed S2 patch report. Verified with Node's
own `JSON.parse` that the file now parses strictly.

**Verified:** 93/93 tests pass. Confirmed the regenerated report parses
under both Python's `json.load` and Node's `JSON.parse`.

**Changed:** `src/segmentation/metrics.py`, `src/segmentation/evaluate.py`,
`src/segmentation/train_lumenstone.py`, `src/segmentation/train_patches.py`,
`tests/test_segmentation_metrics.py`,
`reports/lumenstone_s2_patches_test_metrics.json` (regenerated + sanitised).

**Blocked on:** the rest of the review's accuracy-report template still
needs things only the two of us (or Mintek/MOTT) can supply - manifest
hashes, locality/specimen counts, calibration-set independence, the
trivial/metadata/colour-only baselines, and the cluster-bootstrap confidence
intervals. This entry closes the part that was pure arithmetic on data
already in the repo; it is not a substitute for the full template.

**Next:** whoever builds the trivial baselines (constant-class,
metadata-only, colour-only) next can reuse `metrics.summarise()` and
`json_safe()` as-is - the plumbing is now in place, only the baseline
predictions themselves are missing.

## 2026-09-12 — Sibusiso (46) — the refusal state confirmed on a real image, an actual out-of-domain test

**Did:** Closed the last gap from entry 44 - the refusal/hold verdict had only
been exercised with synthetic inputs (per the Sept 5 audit), not a real image.
Ran a genuine out-of-domain challenge: LumenStone S1 test sections (different
geology - Berezovskoe polymetallic hydrothermal ore, different phase
vocabulary) through the S2-trained checkpoint, the same direct-render sequence
used in entry 44. This is the "explicit out-of-domain challenge" the Sept 12
review recommended building - not a corrupted or synthetic image, a real
section the model was never meant to see.

Of 4 S1 sections tried, `s1_test_02` produced a real refusal: predicted
99.7% pyrrhotite / 0.2% pentlandite / 0.0% chalcopyrite, payload at 0.30% of
ore area - exactly at the `PAYLOAD_FLOOR` - triggering "Flag for manual
review - low payload signal" (verdict state: measurement declined). Confirmed
in-browser: the amber refusal panel, honest phrasing, and correct threshold
citation all render as designed. The other three S1 sections landed
"Marginal - verify before acting" rather than outright refusal - a real
mixed result, not a clean pass, worth knowing before the pitch: the model
does not reliably refuse out-of-domain input, it more often lands in the
uncertain band.

**Verified:** All three verdict states (confident-green, marginal-amber,
refusal-amber) now confirmed against real images through the actual compiled
dashboard, not synthetic inputs. Render HTML saved locally
(`s1_test_01/02/03/05.html`) for reference, not committed - these are scratch
verification artifacts, not shipped demo assets.

**Changed:** nothing in the repo - verification only, no code touched.

**Blocked on:** same as entry 45 - the review's data-rights and integration
items need both of us.

**Next:** worth deciding together whether "3 of 4 out-of-domain sections land
Marginal rather than Refused" is a result to show honestly in the pitch (it
supports the review's point that mean-softmax confidence alone doesn't gate
intervention) or a threshold to tighten first. Either way, don't quietly drop
it - it's a real finding about the system's actual out-of-domain behaviour.

## 2026-09-12 — Sibusiso (45) — began triaging the adversarial review; fixed finding 7's fail-open bug

**Did:** Started triage of `reports/TECHNICAL-REVIEW-2026-09-12.md` (entry 43).
It is large and mostly requires data/rights/hardware decisions only the two
of us can make together (locality manifests, OPC UA integration, dataset
permissions, the 19-day schedule) - not actioned here. Picked off the one
finding that was a pure code fix I could verify alone: finding 7 noted
`verdict_state()` fell through to the confident-green css class for any
action string it didn't recognise. Checked every literal action string
`advise()` can actually produce (9 of them, `src/advisor.py`) - only
`"Continue at current setpoint"` is meant to render green. Changed the
fallthrough to abstain (amber/hold) for anything else, so a typo or a future
action added without updating this function fails safe, not open.

**Verified:** New parametrized tests in `tests/test_verdict_state.py` pin
this (empty string, an unrecognised string, and a wrong-case near-match all
now render "hold"). Full suite: 89/90 pass - the one failure
(`test_dashboard_inputs.py::test_application_starts_with_visible_refusal_without_checkpoint`)
is a pre-existing Streamlit/Starlette version-incompatibility in this host's
environment (`ImportError: cannot import name 'DEFAULT_EXCLUDED_CONTENT_TYPES'`
inside Streamlit's own vendored Starlette gzip middleware), not caused by
this change - worth either of us pinning `starlette`/`streamlit` versions to
fix, next session.

**Changed:** `src/advisor.py`, `tests/test_verdict_state.py`.

**Blocked on:** everything else in entry 43's review that isn't a pure code
fix - data rights (LumenStone permissions), locality/specimen manifests,
OPC UA integration, laptop timing measurements, the accuracy-report
corrections (finding 1), and the redesign/schedule decisions. Those need
both of us, not another solo session.

**Next:** Lethabo and Sibusiso - sit down together on the review's Sep 12-13
gate items (data identity, rights requests, report/task mismatch) before
either of us builds further on an unresolved foundation. Whoever picks up
code next: `starlette`/`streamlit` version pin (see Verified above) is a
quick, isolated fix if you want it off the board.

## 2026-09-12 — Sibusiso (44) — real end-to-end verification, and a real layout bug fixed

**Did:** Ran the actual sequence entry 37 through 42 all flagged as the
blocking next step, now that this host has both the validated checkpoint
(`checkpoints/lumenstone_s2_patches/best.pt`) and the original test images.
Called `patch_module.sliding_window_predict` -> `modal.analyse` -> `advise`
-> `dashboard.render.render()` directly (bypassing Streamlit's file picker,
which can't be automated) against `test_01/04/06/09.jpg`. Results: test_01
confidence 0.781, "Continue at current setpoint" (confident/green); test_04
(0.821), test_06 (0.700), test_09 (0.766) all landed "Marginal - verify before
acting" (amber/hold) - matching the decision-gap report's prior expectation
exactly. Screenshotted both states in-browser: side-by-side image panel,
modal mineralogy, verdict card, and the two-candidate marginal breakdown all
render correctly, no em dashes, no fabricated content.

While diagnosing what turned out to be a real bug, found the committed
`dashboard/static/tailwind.css` was missing `.md:grid-cols-2` entirely - it
predated the input/predicted side-by-side panel being added to
`khanya.html.jinja`, so on `main` as pulled, the two images were genuinely
stacking vertically at every viewport width instead of splitting at the md
breakpoint. Recompiled via `dashboard/build` (`npx tailwindcss --minify`)
and confirmed the class is now present in the right `@media` block; visual
render now shows the true side-by-side layout at desktop width.

**Verified:** 87 tests pass on this host (matches Codex's Sept 5 and Sept 12
reports). Real-image inference through the full pipeline (not synthetic
inputs) for the first time in this project's history. Both verdict states
(confident-green, marginal-amber) visually confirmed against the actual
compiled Stitch CSS, not a stale render.

**Changed:** `dashboard/static/tailwind.css` (recompiled, 1-line minified
diff - added the missing responsive grid rule).

**Blocked on:** `reports/TECHNICAL-REVIEW-2026-09-12.md` (entry 43) still
needs triage by both of us - not actioned this session. Grind/red verdict
state (a genuinely below-floor liberation reading) not yet seen on a real
image; none of the four test images landed there.

**Next:** Lethabo - triage entry 43's review together. Whoever picks this up
next: if you find or produce a test image that should land "Grind finer"
(red), run it through the same direct-render sequence above to complete
verification of the third verdict state.

## 2026-09-12 — Codex (43) — publish full adversarial review

**Did:** Preserved the complete team-requested review in
`reports/TECHNICAL-REVIEW-2026-09-12.md`, with reviewed commit IDs and an explicit
distinction between feedback and implemented changes. Added a README entry.
The review covers both branches; publication changes documentation on main only.

**Verified:** Review body matches the full conversation response. No runtime code
changed. The review's attempted test run could not start because the available
Python runtime lacks pytest; reported model metrics and earlier test counts were
not independently reproduced.

**Blocked on:** Model artifacts, specimen/locality metadata, data/weight permissions,
and the other evidence items enumerated at the end of the review remain unresolved.

**Next:** Both authors should triage the findings and proposed schedule. Publishing
the review does not mark its recommendations accepted or its findings fixed.

## 2026-09-05 — Codex (42) — cross-project reliability audit, main changes only

**Did:** Hardened invalid measurements and labels, preserved unknown liberation
when no payload survives particle filtering, disabled implicit pretrained-backbone
downloads, validated conformal inputs, and deferred REEFPRINT discovery until
physics is used (pure main helpers now import without a Desktop checkout).
The real Stitch renderer now escapes untrusted text, visibly refuses missing
checkpoints/unsupported subsets, validates uploaded images, and invalidates model
caches when checkpoint metadata changes. Reagent intervention is not shown green.
Corrected the fixed S2 band's description: retrospective reference, no guarantee
on new uploads. Updated stale status pointers and team spelling.

**Verified:** 87 tests passed on this host with CPU PyTorch; critical Python lint
and diff whitespace checks passed. Browser inspection confirmed the actual Stitch
missing-checkpoint screen at localhost:8501. Three verdict render states are
tested with synthetic inputs, not claimed as real-image inference. Full report:
`reports/PROJECT-AUDIT-2026-09-05.md`.

**Blocked on:** validated `best.pt` and original micrographs are absent. Restore
those for entry 37's real-image checks; report montages are not suitable uploads.
No files from the contaminated older reefprint checkout were committed or reset.
REEFPRINT fixes live in their own branch history and build log.

**Next:** run the validated checkpoint against original test_01/04/06/09 images,
then rehearse the complete offline sequence. Do not infer scientific validation
from the code-test pass count.

## 2026-09-04 — Codex (41) — Stitch dashboard boots without the model stack

**Did:** Fixed the reason the local dashboard link was refusing to run on this
host. The pre-upload Stitch shell no longer imports PyTorch, torchvision, or
the segmentation model before it can render. Those heavyweight imports are
now deferred until an image is uploaded, and the missing validated checkpoint
is reported explicitly at that boundary instead of killing the whole app.

Installed the lightweight local Streamlit/Jinja runtime, launched the app on
port 8501, received HTTP 200, and visually verified the actual Stitch waiting
screen plus the native upload bridge in the in-app browser. The renderer suite
passes (7 tests), including a new contract that prevents heavyweight model
imports from returning to module scope. The dashboard Python offline-network
guard finds no URL references.

**Changed:** `dashboard/app.py`, `dashboard/render.py`,
`tests/test_render.py`.
**Blocked on:** uploaded-image inference still needs the gitignored validated
checkpoint at `checkpoints/lumenstone_s2_patches/best.pt`; it is not present on
this host. The Stitch dashboard itself is live without it.
**Next:** provide/copy the validated checkpoint to that exact path, then run
the three real-image verdict checks from entry 37. Do not substitute or
fabricate a checkpoint merely to make the upload path appear functional.

---

## 2026-09-04 — Codex (40) — Stitch now owns the whole visible dashboard

**Did:** Corrected the integration boundary after Sibusiso pointed out that
entry 38 still showed a generic Streamlit title/upload shell until inference
finished. Added a real Stitch-rendered waiting state using the same compiled
Tailwind bundle and vendored base64 fonts as the result dashboard. Removed the
native Streamlit title/caption/header/footer and themed the one control that
must remain native—the file uploader—as a narrow bridge to the Python model.

After upload, the waiting state is removed and the existing full Stitch result
renderer takes over. Streamlit still owns execution and caching; it no longer
pretends to be the dashboard. No inference, modal-mineralogy, conformal, or
advisor logic changed. Tests now pin both the pre-upload and post-upload Stitch
paths and ensure the waiting state does not reintroduce the fabricated claims
cut in entry 37.

**Changed:** `dashboard/app.py`, `dashboard/render.py`, new
`dashboard/templates/landing.html.jinja`, `tests/test_render.py`, `README.md`.
**Blocked on:** visual and pytest verification still require the paired host
with Python, Streamlit, the checkpoint, and LumenStone images. Source checks
and the offline-network guard pass here.
**Next:** restart Streamlit—not merely browser-refresh it—and confirm the first
screen is the dark Stitch waiting card above the uploader, then upload
`test_01.jpg` and confirm it is replaced by the full bento result dashboard.

---

## 2026-09-04 — Codex (39) — Stitch is the dashboard boundary

**Did:** Closed the integration ambiguity after Sibusiso asked for Stitch to
be the new dashboard. The functional path was already wired in `1c06706`:
Streamlit owns only upload/model execution, then passes measured objects to
`dashboard.render.render()` and embeds its returned Stitch HTML. Added a
regression test that requires that call plus `st.components.v1.html()` and
forbids entry 36's removed `KHANYA_CSS` approximation from returning.

**Changed:** `tests/test_render.py`, `README.md` (repo map now names the
offline Stitch renderer rather than describing the dashboard as generic
Streamlit).
**Blocked on:** this host still has no Python, Streamlit, checkpoint, or
LumenStone test images, so the visual upload pass remains paired-host work.
The source-level offline-network guard passes.
**Next:** run the full tests and upload `test_01.jpg` on the Python-equipped
host. If the page displayed after upload is not the Stitch bento layout, kill
and restart Streamlit before diagnosing it; imported-module hot reload has
already served stale dashboard code twice (entries 23 and 36).

---

## 2026-09-04 — Codex (38) — renderer wired; paired-host visual pass pending

**Did:** Completed entry 37's code path in two small commits. `1c06706`
replaced entry 36's Streamlit/CSS-token result panels with
`render.render(...)` embedded through `st.components.v1.html(...,
height=1500, scrolling=True)`. The upload and the validated native-resolution
prediction path remain Streamlit-native; the resulting report is now the real
offline Stitch HTML, including its inlined CSS and vendored base64 fonts.

`691f54f` made the pending presentation choice: show the original uploaded
micrograph beside the predicted phase mask. This makes the measured-mask claim
auditable and avoids labelling a coloured prediction as a raw micrograph. It
does not add any computed metric or synthetic overlay. The same commit adds
`tests/test_render.py`: a missing static asset must identify the build repair
step, and `_candidates()` returns two equal-weight actions only for a marginal
verdict (zero for confident and refusal verdicts).

**Changed:** `dashboard/app.py`, `dashboard/render.py`,
`dashboard/templates/khanya.html.jinja`, `tests/test_render.py`.
**Blocked on:** this host has no Python/Streamlit and no untracked LumenStone
test image, so it cannot perform entry 37's real upload / visual pass or run
pytest. `git diff --check` passes and the CI-equivalent Python-only offline
guard finds no `https?://` reference under `dashboard/`.
**Next:** paired host: restart Streamlit, upload `test_01.jpg`, then exercise
`test_04`, `test_06`, and `test_09` to confirm all three say Marginal and show
two candidates. Run `pytest tests/` plus the CI guard. Check the 1500px iframe
height on the presentation display; it deliberately scrolls if the viewport is
short rather than clipping the report.

---

## 2026-09-04 — Sibusiso (37) — IN PROGRESS, picking up mid-task

**Did:** Sibusiso decided entry 36's CSS-token restyle wasn't enough - he
wants the actual Stitch-designed HTML driving the dashboard, not a
Streamlit-widget approximation of its palette. This is that build, and it
is genuinely unfinished. Read this whole entry before touching
`dashboard/`.

**Architecture, and why it isn't a Streamlit-native rebuild.** Streamlit's
own layout primitives can't reproduce the Stitch design's exact structure
(12-column bento grid, layered elevation cards, the 3-state verdict
switcher). The approach: render the real ported HTML via Jinja2
(`dashboard/render.py` + `dashboard/templates/khanya.html.jinja`) and
embed it with `st.components.v1.html()`. Tailwind is compiled to a static
CSS file **once, at dev time** (`dashboard/build/`, Node/npm, gitignored
`node_modules/`) - never a runtime dependency, never touches the demo
laptop's "must run offline" guarantee. Fonts (Plus Jakarta Sans, JetBrains
Mono, both SIL OFL) vendored as `.ttf` under `dashboard/static/fonts/`.
Both the compiled CSS and the fonts are inlined into the rendered HTML
(base64 for fonts, raw `<style>` for CSS) rather than linked, because a
Streamlit component renders inside an iframe `srcdoc` with no stable base
path for relative URLs to resolve against.

**What is real and done:**
- `dashboard/templates/khanya.html.jinja` - structurally faithful port of
  the exported `reefprint_khanya_mintek_metallurgical_advisor/code.html`
  (header/nav, hero metric strip, micrograph panel, modal mineralogy,
  the 3-state verdict card, conditional refusal panel). Read its own
  header comment for the full list of what was cut and why.
- **Every fabricated claim stripped**, per Sibusiso's explicit
  instruction after I flagged them: no "MINTEK SOUTH AFRICA" branding, no
  "ISO/IEC 17025 ACCREDITED", no "Dr. K. Vance" operator, no audit-trail
  stamp, no "DISPATCH TO FLOTATION DCS" button (implies a live plant
  connection that does not exist), no fabricated per-grain tooltips, no
  fabricated P80/Ni-recovery/chromite-locking metrics the pipeline does
  not compute. The mineral phase list loops over `ls.CLASS_NAMES` - the
  real active subset's classes - not the mockup's hardcoded UG2 minerals.
- The 4-tier liberation classification (hi-middlings/lo-middlings/locked)
  is cut entirely rather than faked: the pipeline measures one liberation
  number, not those tiers.
- `dashboard/render.py` - maps real `ModalResult`/`Recommendation`
  objects to template variables. `verdict_state()` (entry 36, already
  tested) drives which of the three verdict colours renders; candidate
  actions for the marginal case are built here, mirroring
  `conformal.action_set()`'s logic in the dashboard's own words.
- Tailwind compiled clean: 13KB static CSS, zero runtime network
  references. Fonts downloaded and verified (Plus Jakarta Sans 94KB,
  JetBrains Mono Regular/Bold ~112KB each).
- `dashboard/build/README.md` documents the regenerate-CSS step for
  whoever touches the template next.

**What is NOT done - this is the actual handoff, not just a status note:**
1. `dashboard/app.py` still has NOT been rewired to call
   `render.render(...)` and embed it via
   `st.components.v1.html(html, height=..., scrolling=True)`. It is
   currently still running entry 36's CSS-token version. This is the
   next, immediate step.
2. **Not yet run once, end to end.** Nothing in this entry has been
   verified against a real image - no syntax error has even been ruled
   out beyond `ast.parse`. Do this before anything else: wire `app.py`,
   run `streamlit run dashboard/app.py`, upload
   `data/raw/lumenstone/S2_v2/imgs/test/test_01.jpg` (confirmed-clean
   pipeline run, entry 36), and actually look at the rendered page.
3. **All three verdict states need checking**, not just the confident
   one - `test_04`, `test_06`, `test_09` from that same folder landed in
   "Marginal" in the validated decision-gap run (entry 24/`report
   §5.0.9`) and will exercise the candidate-actions panel and the
   amber styling for real.
4. The predicted-phase image is currently the ONLY view shown (the
   template dropped the mockup's fake AI-overlay/raw toggle since we
   only have one real predicted mask) - worth a look at whether showing
   the raw input image alongside it (like entry 36's two-column layout)
   reads better than the mask alone.
5. No new tests cover `render.py` yet. At minimum: does it raise cleanly
   if the static assets are missing (the `_read_text`/`_read_b64` guards
   have a stated error message but are unexercised); does the marginal
   case actually produce two candidates and the confident/refusal cases
   produce zero.
6. `tests/` and the CI offline-network guard have NOT been re-run since
   this work started. Do that before considering this finished - the
   guard specifically checks `dashboard/` for `https?://`, and this
   entry's fonts/CSS work was designed to pass it, but it has not
   actually been checked.

**Changed:** new `dashboard/render.py`, new
`dashboard/templates/khanya.html.jinja`, new `dashboard/static/`
(`tailwind.css`, `fonts/*.ttf`), new `dashboard/build/` (Tailwind compile
step, `node_modules/` gitignored, not committed).
**Blocked on:** nothing technical - this is genuinely mid-task, paused on
explicit instruction to push and hand off, not stuck.
**Next:** items 1-6 above, in that order. Whoever picks this up should
run the dashboard and actually look at it before writing a single new
line - `app.py` is the only file standing between this and something
real.

---

## 2026-09-04 — Sibusiso (36)

**Did:** Restyled the dashboard to the REEFPRINT :: KHANYA Mintek design
(`922ae88`) and hit the same class of bug entry 23 already documented once.

**Ported the Stitch export by hand, not dropped in.** The exported `.zip`
loads Tailwind and four Google font families from CDNs - unusable given
"must run offline". Real Mintek palette (verified against mintek.co.za's
own CSS variables) transcribed to CSS custom properties, zero network
references, CI's guard still passes. Stripped fabricated institutional
claims the mockup shipped with - "MINTEK SOUTH AFRICA" branding,
"ISO/IEC 17025 ACCREDITED", a fabricated "Dr. K. Vance" operator, a signed
audit trail - on Sibusiso's explicit instruction after I flagged them.
Moved the amber-reservation rule into `advisor.verdict_state()`, pinned by
`tests/test_verdict_state.py`: amber renders on exactly the two abstaining
states, nothing else.

**Regression, same shape as entry 23's font-caching bug: a server left
running from before the edit threw `ImportError: cannot import name
'verdict_state'` even though the function genuinely exists and imports
fine from a fresh interpreter.** Streamlit's hot-reload does not reliably
pick up changes to *imported* modules, only the main script file - a
stale `sys.modules['src.advisor']` from the earlier session survived the
page reload. Fix was the same as last time: kill and restart the server
process, not just reload the page. **Operational note for the actual demo
laptop:** after any `git pull` that touches `src/` or `dashboard/`, restart
the Streamlit process before assuming the code is wrong if something looks
unchanged - this is now the second time hot-reload alone has hidden a real
edit.

**Changed:** `dashboard/app.py` (full CSS/masthead/verdict restyle),
`src/advisor.py` (`verdict_state()` + `ABSTAINING_PREFIXES`), new
`tests/test_verdict_state.py`.
**Blocked on:** nothing technical.
**Next:** the file-upload flow itself is unverified end to end against the
new styling - browser automation can't drive a real `<input type=file>`
picker, so a human still needs to run one real image through the restyled
dashboard before rehearsal. Everything else (52 tests, CSS, offline guard,
no-fabricated-claims audit) is verified.

---

## 2026-09-04 — Sibusiso (35)

**Did:** Two verification passes on Codex's `reefprint` work, then ENDGAME §4
W6 - quantified the Impact argument, our lowest-scored judging criterion.

**1. Verified W1 (`8229353`) and W2 (`923f77b`).** Both real. Ran the suite
myself since Codex's host still has no Python: the Week-3 coverage-band bug I
flagged last session is fixed (the 20/20-locality case now passes - Codex
used a Beta-Binomial predictive interval, which is the right fix: it accounts
for the held-out sample's own binomial noise on top of calibration
uncertainty, exactly the gap I'd named without prescribing the fix). Week 4's
degraded-input gate is genuinely built, not a placeholder - defocus, glare,
poor polish, wrong exposure, empty field, malformed metadata all produce a
stated refusal.

**2. Caught a small, real drift in the same handoff.** `8184277` claimed "286
passed, 21 deselected"; running `pytest tests/ -m "not placeholder"` here
collected 288/21 - a self-referential miscount (the new doc-count test's own
passing tests weren't folded into the hand-counted total). Reported it back
precisely rather than fixing it myself on someone else's branch. Codex fixed
it in `28587ef`; re-verified: **288 passed, 21 deselected, zero failures.**
`reefprint` is genuinely green now, not just claimed green - W1 through W3 are
all solid.

**3. W6 - the Impact number.** `MINTEK-FIT.md` §3.1 had the qualitative
QEMSCAN-triage argument since August but no number. Would not invent one -
same Rule 1 this whole project runs on. Found two real, dated, citable
sources instead: Saskatchewan Research Council's Advanced Microanalysis
Centre publishes a QEMSCAN price list (April 2017) with $1,500/sample for
*"modal mineralogy; customizable liberation criteria, mineral associations
and predicted recovery"* - closely matching what our advisor measures; ALS
Global's own mineralogy FAQ states turnaround is not overnight, is
workload-dependent, and a 1-week *expedited* slot costs a surcharge, implying
standard turnaround already exceeds a week.

**Then paired that with our own real, already-validated number**, not a new
experiment: `reports/decision_gap_patches_refined.json`, the patches+refined
pipeline (report §5.0.9), 12 held-out S2 sections. Predicted recommendations:
6 confident (Continue/Grind finer), 6 "Marginal - verify before acting." That
is the QEMSCAN-triage fraction, directly measured, not estimated - **50%,
95% Clopper-Pearson CI [21%, 79%] at n=12**, stated as an interval because n=12
genuinely does not support more precision than that.

**Stated plainly what this is not.** We have not shown that our "verify"
flags agree with what a human mineralogist or QEMSCAN itself would flag - that
needs real QEMSCAN results run against the same sections, which we do not
have. The claim is that the mechanism (abstain near a calibrated threshold)
is the right shape for triage, evidenced by zero unsafe and zero conservative
errors under the corrected band - not that 50% is proven to be the
economically optimal cut, and not that the $1,500/2017 anchor is Mintek's own
cost.

**Changed:** `MINTEK-FIT.md` §3.1 (quantified argument + two new sources,
also added to the master Sources list), `ENDGAME.md` (W6 marked drafted, beat
1 in the talk table points at the new number).
**Blocked on:** Sibusiso/Lethabo need to sign off the economics before this
goes on a slide - the interval and the "not yet shown" caveat are as load-
bearing as the 50% itself, and whether $1,500/2017 is a fair anchor for what
Mintek would actually compare against is a domain call, not mine.
**Next:** ENDGAME §4. W4 (repo as a finished artefact, §7/§8) and W5 (decide
and rehearse the ten minutes) are the remaining open workstreams; W7 (backup
video) should happen the moment W3's rehearsal pass is done.

---

## 2026-09-04 — Sibusiso (34)

**Did:** ENDGAME §4 W3 - the offline demo. Found and fixed a real bug in it:
**the dashboard was loading the wrong model.**

**1. The dashboard ran the resize baseline, not the patches model.** Traced
through `dashboard/app.py` while starting W3 and found
`from src.segmentation.train_lumenstone import CKPT` - the RESIZE checkpoint.
But report §5.0.9 and the README's own repo map call `train_patches.py` "the
primary pipeline": patches scores 6/12 flips with 0 conservative errors,
resize scores 7/12 with 1, under the same corrected band. **The flagship demo
was quietly running the pipeline the project's own report calls secondary.**
Nobody had reason to notice - the dashboard renders fine either way; only a
side-by-side against the report numbers would show it, and nobody had done
that since the redesign in `c70344c`.

**2. Fixed by wiring in the code that was already validated for this.**
`decision_gap.py`'s patches numbers were never produced by a naive
resize-and-forward-pass - they come from
`patches.sliding_window_predict()`, tiling the full section at native
resolution and stitching overlapping logits. That function already existed
and was already the honest evaluation path; the dashboard just wasn't using
it. Swapped `CKPT` to `train_patches.checkpoint_for('ce')` and replaced the
inline forward pass with `sliding_window_predict`, so demo-time inference is
now provably the same code path as the numbers in the report - not a
reimplementation that could quietly drift from it.

**3. That surfaced a second, real problem: 155 seconds for one section.**
Measured directly (not guessed) by running the exact dashboard pipeline
against a real held-out test image
(`data/raw/lumenstone/S2_v2/imgs/test/test_01.jpg`, 3396x2547, 48 tiles at
512px/64px-overlap) end to end: 155.4s inference, sane output (liberation
95%, 181 particles, "Continue at current setpoint"). **2.5 minutes of silence
does not survive a 10-minute talk.** Fixed the right way, given the dashboard's
own `preprocess()` docstring exists specifically to keep demo-time and
eval-time inference from drifting apart: **cached, not weakened.** New
`predict()`, `@st.cache_data` keyed on the uploaded bytes, same
`checkpoint_for('ce')` / same tiling parameters as `decision_gap.py` either
way - a cached result is identical to a fresh one, just not recomputed. A
rehearsed image is instant on repeat (including during the actual talk, if
run once beforehand on the presentation laptop); a genuinely new image still
pays the real 155s, honestly, with the spinner naming the number rather than
hiding it.

**Scope note for whoever plans beat 6 (the live refusal, ENDGAME §5).** This
155s cost is specific to THIS dashboard's segmentation-based refusals ("no
payload detected", "insufficient ore") - they all require running the CNN
first. The geometry-discriminator refusal on the `reefprint` side
(`harmonic_signature`) is a different, much faster computation with no CNN in
the loop at all. If beat 6 is built around segmentation refusals, it needs a
pre-rehearsed (cached) image; if built around the geometry discriminator, this
latency does not apply to it. Worth deciding which, not assuming.

**4. Verified two ways.** Direct script call of the exact dashboard code path
(above - the real timing number came from this). Separately, launched the
actual Streamlit app in a browser and confirmed it boots clean, no server
errors, correct checkpoint, file uploader renders - could not drive an actual
file-picker dialog from this sandboxed browser (OS-level, not page DOM), so
the upload-through-the-UI path itself needs a human pass before it is called
fully rehearsed. `pytest tests/` and the offline-network grep both still pass
after the change - neither touches `dashboard/`'s import graph in a way either
would catch, so both were re-run rather than assumed.

**Changed:** `dashboard/app.py` (checkpoint swap, sliding-window inference,
result caching, updated module docstring and error message).
**Blocked on:** a human rehearsal pass through the actual file-picker upload
flow - not verifiable from here.
**Next:** ENDGAME §4. W3 is materially further along but not "done" per the
definition in §8 (needs the three-times-through rehearsal, including a fresh,
uncached image, to confirm the 155s spinner reads fine live and doesn't feel
broken). W6 (quantified impact) is still open and mine to draft.

---

## 2026-09-03 — Sibusiso (33)

**Did:** Strategy session, not experiments. Researched the actual competition,
scored ourselves against the real rubric, wrote the plan of record, and closed
the biggest scoring gap on this branch. **Read [`ENDGAME.md`](ENDGAME.md)
before doing any more build work** - it now supersedes `PITCH.md` §7.

**1. Researched Mintek properly. Three findings change what we build.**
- **Mintek made UG2 chromitite commercially viable - it nearly doubled South
  Africa's accessible PGM reserve base.** We are pitching a UG2/PGM story to
  the institution that created the UG2 industry. Relevance is free; overclaims
  are fatal. Our Rule-1 discipline is the price of entry in that room, not
  pedantry.
- **The official judging criteria are Innovation, Feasibility, Impact,
  Technical Execution, Presentation Clarity** (Mintek-SCi Grad Hackathon FAQ).
  Five named criteria, so the ten minutes should be built to hit five things,
  not to tell a story that happens to touch them.
- **Winners are announced only after Mintek's Office of Technology Transfer
  completes an IP assessment on the top-ranked entries, and creators receive
  invention credits.** ADR-0003's two clean parallel commit histories are
  directly responsive to this. Do not blur them now. Also: a technical person
  from MOTT *will* read this repo, which is why §7 of ENDGAME treats the repo
  itself as a deliverable.
- Context, not action: 2025's winner (UJ's *H2Optimise*, tailings-water reuse)
  was domain engineering with AI as the multiplier, not an ML project in a
  mining costume. Judges praised "relevance to actual industry needs". 2025's
  theme was "Status Quo is Boring".

**2. Scored ourselves honestly. Impact is our weakest criterion and Technical
Execution was split.** Innovation and Feasibility are strong. Presentation
Clarity is unproven (the ten minutes is drafted, not decided). The asymmetry
that mattered: REEFPRINT had 282 tests + CI; **KHANYA `main` had zero tests and
no CI.** One half of one project looked professional and the other looked like
research scripts.

**3. The reframe, and it is the most useful thing in this entry.** Our
distinctive asset is that we keep finding and reporting nulls (N3 `NEITHER`, no
extinction separation, no public texture data, no computable oxidation index).
That is better science than most entries will contain - and a judge scoring
*Impact* hears four sentences beginning "we checked and it didn't work". **Do
not hide the nulls; make them the evidence for a positive product claim:** we
built the part of an automated mineralogy system that knows when its own answer
is untrustworthy, and proved it by turning it on ourselves and letting it
refuse four times. ENDGAME §3 has the mapping from each null to what it proves,
and the two numbers that carry it (the 1.5e-02 false-isotropic reading; the
Bushveld p = 0.0002).

**4. Built the test suite `main` never had: 46 tests, all passing, no dataset
required.** `tests/test_conformal.py` (the order statistic, the refusal when n
cannot support the level, empirical coverage), `tests/test_advisor.py` (every
refusal branch, the symmetry of the liberation band, the 0.85 confidence
threshold, the zero-margin ground-truth path), `tests/test_modal.py` (including
a **regression test for the entry-23 sparse-upload crash** that was reachable
from the dashboard), `tests/test_bridge.py` (Cr#/Mg# against hand-worked
values, scale invariance, and the S3 v2 archive parsing whose real convention a
keyword search originally missed entirely). Added `.github/workflows/ci.yml`
mirroring REEFPRINT's, **including a guard that fails the build if `dashboard/`
ever contains a network reference again** - "runs offline" is a claim we make
on stage with the wifi off, so it is now checked rather than remembered.

**5. Extracted `cation_ratios()` out of `build_arrays()`** in
`chromite_pge_falsification.py` so the one piece of domain arithmetic is a pure,
testable function. Verified the refactor is result-preserving: still delta R^2 =
0.0279, p = 0.0002, 1112 rows over 305 boreholes, byte-identical conclusion.

**6. Repo cleanup, deliberately surgical.** 17 stray `.log` files and two loose
scripts left the root (`logs/`, `scripts/`, both gitignored/tidied); the
`.gitignore` had accreted 20 individually-named log files and is now four
patterns. Deleted `smoke_polarim.py` - 12 lines, untracked, and it hardcoded the
stale `REEFPRINT - Copy` path that the geometry guard exists to stop anyone
importing. **README now names REEFPRINT.** It previously never mentioned it,
which ADR-0003 explicitly classes as a defect ("a doc that says only 'KHANYA'
and never 'REEFPRINT' is now a defect, and so is the reverse"). *Not* done, on
purpose: no package rename, no moving `DATA-SOURCES.md` / `HANDOVER.md` /
`STATUS.md`. `DATA-SOURCES.md` alone is referenced from nine files including
runtime error strings, and HANDOVER is the live coordination channel with a
second agent writing to it. Churning paths this close in, for cosmetics, is how
you break something you cannot see.

**Changed:** new `ENDGAME.md`, new `tests/` (4 files, 46 tests), new
`.github/workflows/ci.yml`, new `scripts/`, `README.md` (REEFPRINT naming,
headline results, repo map, seam instructions), `.gitignore` (patterns),
`src/chromite_pge_falsification.py` (`cation_ratios` extracted).
**Blocked on:** nothing on this branch.
**Next:** ENDGAME §4 workstreams. W1 (the Week-3 coverage-band bug) and W2
(Week 4, degraded input) are Codex's on `reefprint`; W3 (the offline demo) is
joint and is the single highest-value artefact left; W6 (quantified impact) is
mine to draft and needs Sibusiso/Lethabo to sign off the economics.

---

## 2026-09-03 — Sibusiso (32)

**Did:** Two things - verified Codex's first `reefprint`-branch commit (a
parallel session, split off to work Week 3 while I fixed (31)'s bug), and
closed Week 2 with a new pivot after the first two candidates both turned
out structurally unavailable.

**1. Codex's Week 3 (`52a9a42`, "Build Week 3 locality conformal coverage
audit") is real, with one genuine bug - verified by actually running the
suite, which Codex's host couldn't.** Codex flagged its own limitation
honestly: "this host has neither Python nor uv," so it could only run
`git diff --check`, not the tests. Installed the missing deps
(scipy/scikit-image/tifffile/imagecodecs/matplotlib/pillow/pytest/
hypothesis) into KHANYA's venv and ran REEFPRINT's suite via
`PYTHONPATH=src` against the actual pulled commit (first attempt used a
stale worktree checkout - fetch alone doesn't update a worktree, had to
`git checkout --detach origin/reefprint` too). Result: 282 passed, 23
failed - 22 of those are the untouched "NOT BUILT" placeholders for weeks
4-6 and other unbuilt modules, exactly as expected. **One real failure:**
`test_a_locality_outside_the_band_fails_the_gate_even_if_the_pool_would_pass`.
A locality with perfect held-out coverage (20/20) gets marked outside the
conformal band, because `CoverageBand` is built purely from
calibration-set uncertainty (`Beta(19,2)`, genuinely tight near 1.0 - not
a bug in the Beta math itself) while `LocalityCoverage.within_band`
compares it directly against a raw empirical proportion from a *held-out*
sample, which carries its own binomial sampling noise the band doesn't
account for. That's either a bad test fixture (n=20 held-out is too small
to safely hit exactly 20/20 without tripping this) or a real gap in
`within_band` (needs a predictive interval combining both noise sources,
not just calibration noise) - a statistical design call, not something I
patched blindly on someone else's branch. Flagged back rather than fixed.

**2. Week 2, pivoted twice more before landing.** Picked up from where I
left off in the last session: `texture_features` (T1) and a genuine
oxidation index (checked this session - the Bushveld CSV reports iron as
one lumped `FeO_%` column, no `Fe2O3_%` split, so Fe3+/Fe2+ cannot be
recovered from XRF majors, same structural absence as T1's, not
administrative) are both dead ends. **Landed on Cr#/Mg#** - the standard
chromite-petrology cation ratios (Barnes & Roeder 2001, J. Petrology
42(12):2279-2302), used as published, not a new normative-mineralogy
formula (Rule 6 is about the latter). Downloaded the real Bachmann 2019
CSV myself (it was gitignored and not actually present in any worktree,
despite CONTEXT.md describing it as "in hand" - fetched via Mendeley's
public files API, `data.mendeley.com/datasets/dc8jcnbcvk`, 157,067 bytes,
verified against the reported size). New `src/chromite_pge_falsification.py`
- KHANYA-side glue that imports `reefprint.heads.falsification` unchanged
(same pattern as `polarimetry.py`'s bridge), computes Cr#/Mg# from
Cr2O3/Al2O3/MgO/FeO by standard molar-mass cation ratios, sums 4E PGE
(Pt+Pd+Rh+Au - the standard Bushveld payable-metal convention, not a
mineralogy calculation) as `target`, and runs `evaluate_texture_uplift`
with Cr2O3 alone as the (honestly reduced - pyroxene fraction still
unavailable) baseline.

**Result: H0 REJECTED.** 1112 of 1205 rows kept (`Filter=='1'`, inferred as
"passes QC" from its 1193/1205 near-unanimous value - not read from the
paper's methods, stated as an assumption), 305 boreholes (honest n, well
above `MIN_LOCALITIES_FOR_INFERENCE=5`). Delta R^2 = 0.0279 (0.1119 ->
0.1398), p = 0.0002. Chromite composition adds real, statistically
significant signal to PGE grade beyond Cr2O3 alone, cluster-robust by
locality. **Caveat worth carrying into the talk:** the effect size is
small in absolute terms (2.8 points of R^2) even though it's a strong
p-value at this n, and Cr# is arithmetically derived from Cr2O3 (one of
the two terms in its own ratio), so some of the "added" signal may not be
fully independent of the baseline - report the number honestly with that
caveat, don't oversell delta R^2 alone as if it were the whole finding.
Report: `reports/chromite_pge_falsification.json`.

**Changed:** new `src/chromite_pge_falsification.py`, new
`reports/chromite_pge_falsification.json`, `data/raw/bushveld_thaba_chromitite/`
(gitignored, not committed - re-run `python -m src.chromite_pge_falsification`
after downloading the CSV per that module's docstring).
**Blocked on:** nothing technical for this entry's own scope. The Week-3
bug above is Codex's/Lethabo's to resolve on `reefprint`.
**Next:** relay the coverage-band bug to whoever owns `reefprint` next.
Weeks 4-6 still not started. Week 2's result should get folded into
whatever document tracks findings for the talk - not done as part of this
entry, since that's a presentation-content decision, not a code one.

---

## 2026-09-03 — Sibusiso (31)

**Did:** Corrected entry (30)'s own mistake, caught by reading Lethabo's work
from the intervening week rather than by anyone reviewing mine.

**(30) was methodologically wrong, not just superseded.** It compared
extinction-depth magnitudes across minerals as a ratio (median isotropic vs
median anisotropic, and a magnetite/hematite "headline pair" ratio).
Lethabo built `reefprint.bridge.measure_section_extinction` on 2026-08-24
specifically to prevent this: its docstring states plainly that raw
extinction depth is not contrast-normalised, so one mineral's number must
never be divided by another's - the only licensed claim is "extinguishes at
all" vs "stays exactly dark". (30)'s "separation ratio 0.81" and "headline
pair 1.14x" were both this exact mistake. Not caught before commit because
nothing in the code enforced it at the time - now something does.

**Fix: call the sanctioned function instead of reimplementing its logic.**
`sample_section` now builds real `LabelledSection`/`RotationSeries` objects
(reshaped to a thin (1, n) pseudo-image so peak memory stays at the sampled
pixels, never the full section - the fit is per-pixel independent, so this
is mathematically identical to a true grid) and calls
`measure_section_extinction` for the per-mineral statistics, rather than
masking and reducing by hand. Removed `summarise_by_class`/`separation`
(now dead - nothing else called them) since the ratio they computed was
exactly the forbidden comparison.

**`run_symmetry_test` now reports two different things and does not conflate
them:** a per-mineral extinction-depth table (kept for the record, printed
with an explicit "not comparable between minerals" warning), and the
S0-binned conformal detection rate (the actual licensed cross-mineral
claim, already being computed correctly since (30) - it just wasn't the
headline before).

**Re-ran on all 47 sections. Same conclusion as (30), now on solid ground:**
8.2% of known-anisotropic pixels flagged vs **10.0%** of known-isotropic
(calibration target 10%) - detection is at or below the false-positive
floor. There is no separating signal in this archive via extinction, full
stop, and this time the number that says so is one the physics actually
licenses. Per-mineral depth medians (not comparable to each other, kept for
the record): chalcopyrite 44.5, galena 54.0, magnetite 36.2, bornite 35.9,
pyrite 53.1, sphalerite 58.0, arsenopyrite 55.8, hematite 31.4, tennantite
41.6 - notice these don't even separate by eye, which is exactly why a
ratio between any two of them was never a safe thing to report.

**The build plan, for whoever reads this next:** Lethabo's Week 1-6 gate
table (`CONTEXT.md` on the `reefprint` branch - same repo, `git fetch` +
`git log origin/reefprint`) is the actual plan. Week 1 is closed. Week 2 is
blocked on a domain-lead call (`texture_features` is structurally missing
from every public UG2/Bushveld source, not administratively missing - see
`CONTEXT.md` §8 item T1). Weeks 3-6 (conformal coverage per locality,
degraded-input robustness, offline end-to-end, demo video) are not started.
Handed Week 3 to a parallel Codex session working the `reefprint` branch;
this entry's fix is the last KHANYA-side loose end from before that split.

**Changed:** `src/polarimetry.py` (sample_section rewritten around
`measure_section_extinction`, `summarise_by_class`/`separation` removed),
`reports/polarimetry_s3.json` (regenerated, corrected fields).
**Blocked on:** nothing technical on KHANYA's side.
**Next:** whatever Codex reports back from Week 3. Week 2's texture_features
decision is still open and still not a KHANYA-side call.

---

## 2026-08-21 — Sibusiso (30)

**Did:** Re-pointed `src/polarimetry.py` at `reefprint.polarim.extinction` per
Lethabo's instruction in `CONTEXT.md` ("do not run the Stokes inversion on S3
v2... re-pointed at extinction, not stokes_from_rotation_series"), and ran the
ten-mineral symmetry test on real S3 v2 data for the first time.

**Set up a live REEFPRINT checkout.** `_resolve_reefprint_src()` (added in the
geometry-guard PR) looks for `~/Desktop/REEFPRINT/src` first; only `REEFPRINT -
Copy` existed on this machine and is stale (missing `geometry.py` and
`extinction.py`). Added a detached git worktree at `~/Desktop/REEFPRINT`
tracking `origin/reefprint`, so the resolver finds the real, current source
without vendoring it - matches this module's own "imported unchanged"
principle. Not committed to KHANYA (it's a worktree, not a copied file).

**Swapped the estimator, kept the geometry guard, inverted which verdict it
gates on.** The old guard raised unless `harmonic_signature` returned
`SECOND` (assumed analyser). Since real data reads `NEITHER` (matches N3
exactly), that guard would have hard-failed every section under the old
logic. Now it raises only on a clean `SECOND` verdict - which would mean a
section really is a rotating-analyser series, wrong physics for extinction's
4th-harmonic model. `anisotropy`/`s0` dict keys kept as-is downstream
(`summarise_by_class`, `conformal_threshold_by_s0`, etc. all use them as
relative quantities only, so no other function needed to change) but now
hold extinction amplitude and `dc`, not Stokes anisotropy and S0 - commented
at the point of substitution since they are not on the same physical footing
(no calibrated S0 exists under crossed polars, extinction.py's own docstring
says so).

**Found and fixed a real, separate data bug on the way: one frame in one
section has swapped pixel dimensions.** `S3_test_04_r045.jpg` decodes as
(3396, 2547) against every sibling frame's (2547, 3396) - no EXIF explains
it, just a bad capture. Was crashing the whole 47-section run at frame-read
time (`IndexError`, twice, before and after the estimator swap - same bug,
unrelated to geometry). Fixed by checking each frame's decoded shape against
the mask's and skipping only that one frame, keeping the other ~71 angles
for that section - a full run should not depend on every one of ~3,384 JPEGs
being clean.

**The result is a real, honest null - a second, independent line of evidence
for the same problem N3 already found, not a contradiction of it.** 47
sections, 137,113 pixels pooled, 9 of 11 S3 classes represented:

| | median extinction amplitude |
|---|---|
| isotropic | 6.024 |
| anisotropic | 4.880 |
| **separation ratio** | **0.81** (anisotropic reads LOWER - wrong direction) |
| magnetite vs hematite (headline pair) | 4.140 vs 4.733, ratio **1.14x** |

For comparison, REEFPRINT's own phantom validated at 40.4x. The S0-bin
conformal threshold (`conformal_threshold_by_s0`) is doing its job correctly
- false-positive rate on known-isotropic pixels landed at 9.99%, right on
its 10% target - but detection rate on known-anisotropic pixels is only
8.2%, barely above the false-positive floor. The calibration machinery
works; there is no separating signal in this archive for it to calibrate
against. Report: `reports/polarimetry_s3.json`.

**Changed:** `src/polarimetry.py` (estimator swap, guard inversion, per-frame
shape check), new `reports/polarimetry_s3.json`, new (uncommitted) worktree
at `~/Desktop/REEFPRINT`.
**Blocked on:** nothing technical - this closes out the immediate re-pointing
task. Whether to keep chasing a signal in S3 v2 at all (brightest-quantile
re-run, a confirmed-analyser archive, or reporting the null itself as
Rule-9-style falsification) is Lethabo's call per his own CONTEXT.md
priority order, not a KHANYA-side decision.
**Next:** read Lethabo's `CONTEXT.md` on the `reefprint` branch for his
current priority order before acting further on this thread - this entry
answers only "does extinction find symmetry-driven separation in S3 v2,"
not "what should be reported instead." Abstract due 30 Aug.

---

## 2026-08-21 — Sibusiso (29)

**Did:** Reviewed the `reefprint` branch end to end, ran experiment 002 against
the real S3 v2 archive, found and fixed a real bug in it, and got it confirmed
twice.

**1. Reviewed `reefprint` branch - it is safe, and well-designed.** First look at
the diff stat (KHANYA files net -9750 lines) looked like a wholesale delete.
It is not: ADR-0003 states explicitly the branch is **never merged** - two
independent commit histories on purpose, better evidence under originality
authentication than one history with a giant replace-everything merge commit.
`main` is untouched. The `bridge/` module (labels in, measurements out, never
returns a mask) is a clean one-way seam, better than what I wrote in
JOINT-PLAN.md - it centralises three project rules at the one interface point
instead of trusting every future caller.

**2. Ran `experiments/002-s3v2-geometry/run.py` against the real
`data/raw/lumenstone/S3_v2.zip` - first time, real answer.** Crashed on a
frame-count mismatch (real sections range 24-72 frames; the pooling
concatenated raw frames across sections, which needs a common count). Traced
it properly rather than patching around it: `harmonic_signature` already
reduces the frame axis to per-pixel amplitude/floor before the mismatch
matters, so the fix pools those per-pixel arrays (correct, uses every frame
every section actually captured) instead of truncating every section down to
the smallest. Opened **PR #3** with the fix, confirmed the archive itself
(not a bug) skips ~29 of 47 sections - those are single static images with no
rotation subdirectory, genuinely no acquisition, not a filename-parsing miss
as I first assumed before checking.

**Real result, twice, identical both times:** 29 sections, 116,000 pixels,
2nd harmonic 2.5x its noise floor, 4th harmonic 1.1x, threshold 5.0x.
**Verdict: NEITHER.** Per the script's own physics (4-phi goes as
bireflectance squared, 2-theta as bireflectance on a bright S0), a null is far
more consistent with stage rotations buried in noise than analyser rotations
buried in noise. **N3 stays open, open-but-leaning toward stage rotation. Not
clearance to run the Stokes inversion on this archive.**

**3. `uv` itself is broken on this Windows machine.** `uv sync` and
`uv python install 3.12` both fail reproducibly with "Missing expected target
directory for Python minor version link", even after a full clean of the uv
python cache directory and a fresh retry. Not a stale-cache issue - second
attempt failed identically to the first. Ran everything through KHANYA's
existing Python 3.13 venv via `PYTHONPATH` instead (`geometry.py` has no
3.12-only syntax, checked with `ast.parse` before relying on it). Flagged on
the PR in case it hits Lethabo's own machine - might be a Windows
junction/Defender issue worth a line in `docs/05-toolchain.md`.

**4. S1 retrain has died and resumed 9 times now.** Same pattern every time -
`last.pt` intact, `run_s1_retrain.cmd` relaunched detached, resumes at the
next epoch with zero loss. At epoch 17/20, mIoU 0.566 (best checkpoint still
epoch 15 at 0.610). This is now just the norm for a >2h CPU job on this
machine, not news each time it happens.

**Changed:** `.gitignore` (N3 log files), and on the `reefprint` branch:
new branch `fix/pool-signatures-not-raw-frames`, PR #3 open against
`reefprint` with the pooling fix.
**Blocked on:** nothing technical.
**Next:** PR #3 needs your review/merge - it's the fix for the crash you'd
have hit running week-1 leg (b) yourself. N3's open-but-leaning verdict is a
real input to whether the abstract can claim the Stokes inversion runs on
public data at all; worth factoring into the phase-set/scope call already
open since (26).


## 2026-08-19 — Sibusiso (28) — session wrap-up

**Did:** Followed on from (27). S3 v2 finished downloading; the ten-mineral
symmetry test does not run yet.

**1. S3 v2 downloaded, full 5227.2 MB, `data/raw/lumenstone/S3_v2.zip`.**
`polarimetry.py` reads directly from the zip archive (no extraction step,
`archive.open(...)` per frame) - confirmed that design is sound: for
`S3_train_33`, both the mask and its r270 rotation frame are `(2547, 3396)`,
consistent, no transposition.

**2. Real-data symmetry test crashes - WIP, committed broken rather than
lost.** `run_symmetry_test()` in `polarimetry.py` samples mask-labelled pixel
coordinates from one section then indexes the SAME coordinates into every
rotation frame for that section. It dies with `IndexError: index 2928 is out
of bounds for axis 1 with size 2547` inside `sample_section`. **This is not
the global transposition bug it looks like** - the one section I checked by
hand (S3_train_33) has matching mask/frame shapes, so whatever is failing is
section-specific: either one particular stem has a mask/frame size mismatch
that others don't, or a coordinate is being sampled from the wrong section's
mask/frame pairing. **Next step is not "fix the transpose" - it's print the
failing stem and compare that ONE section's mask shape against its own frame
shape before touching anything else.** Traceback in `polarimetry_s3.log`
(gitignored, still on disk locally).

**3. S1 retrain died again - 7th time, unresumed.** No python process running;
`s1_retrain.log` stops mid-tqdm-bar at patch 35/64 of what would be epoch 16.
**Last completed epoch is still 15, val mIoU 0.5508 - best of the run so far**,
comfortably past the old 8-epoch attempt's 0.365. Resume command is unchanged
from every prior time this has happened: rerun `run_s1_retrain.cmd` (or the
detached launch it wraps) and it picks up from `last.pt` automatically. This
is now the 7th session-death; treat it as the expected shape of a multi-hour
CPU job on this machine, not a surprise each time.

**Changed:** `src/polarimetry.py` (WIP, broken - see item 2), `.gitignore`
(dedup'd; added `s3v2_download.log`, `polarimetry_s3.log`).
**Blocked on:** you, unchanged from (27) - the chromite/phase-set
reconciliation is still the one decision blocking the 30 Aug abstract.
**Next session, in order:** (a) resume S1 retrain (dead, see item 3); (b) find
the failing stem in `sample_section` and compare its own mask/frame shapes -
do not assume it's the same bug as any prior transposition issue until that
comparison is done; (c) once the symmetry test runs clean, JOINT-PLAN phase 2
- the ten-mineral isotropic/anisotropic split, with magnetite-vs-hematite as
the headline pair; (d) everything from (26)/(27) still ahead of the
polarimetry work in overall priority - QEMSCAN-labelling ask, report
re-voicing, economic case - is untouched this session and still outstanding.


## 2026-08-19 — Sibusiso (27)

**Did:** Acted on all three JOINT-PLAN items. **Lethabo: your open finding N2
is closed, and one of my claims in (26) was wrong.**

**1. CORRECTION to entry (26) - the pentlandite/pyrrhotite experiment cannot be
run.** Pentlandite and pyrrhotite are in **S2, which has no rotation series**;
the XPL rotations are in **S3, which contains neither mineral**. The pair and
the measurement live in different datasets. I should have checked before
proposing it. JOINT-PLAN section 3a has the correction.

**The replacement is better, not a consolation.** S3 splits five isotropic
(cubic: pyrite, galena, sphalerite, magnetite, tennantite) against five
anisotropic (covellite, arsenopyrite, hematite, chalcopyrite, bornite) - a
ten-mineral test rather than one pair. And it contains **magnetite vs
hematite**, which is exactly the pair our report section 3 claims BSE cannot
separate and optical can. That claim is currently *asserted and never
measured*. Magnetite is also KHANYA's total failure (IoU 0.000). So the
replacement lands on the pair our own optical argument stakes itself on.

**2. N2 IS CLOSED.** `python -m src.polarimetry --n2`. Using your own stated
numbers (sigma=0.25 R%, n=36):

| Population | Median aniso | Fixed threshold FP | S0-conditioned FP |
|---|---|---|---|
| isotropic, bright R=50% | 0.0014 | 10.0% | 9.9% |
| isotropic, **dark R=4.75%** | 0.0146 | **98.1%** | **9.9%** |
| anisotropic R=20%, m=0.08 | 0.0801 | 100% (detect) | 100% (detect) |

A fixed threshold flags **98% of dark isotropic pixels** as anisotropic,
exactly as you predicted. The S0-binned conformal bound holds at 10% in every
bin *by construction* and loses no detection sensitivity. Your 1/S0 law is
confirmed in passing: 0.0146/0.0014 = **10.4x** against an S0 ratio of
50/4.75 = **10.5x**.

This is KHANYA's `src/conformal.py` machinery pointed at your physics. You had
N2 open as blocking; the fix was already built over here.

**3. S3 v2 downloading** (5.2 GB, ~45% at time of writing). `src/polarimetry.py
--inspect` will report the archive layout so the OME-TIFF reader is written
against the real convention rather than a guess - that is your named single
next action and the layout should drive it.

**How the bridge works:** `src/polarimetry.py` imports
`reefprint.polarim.stokes` **unchanged** from your repo via sys.path - not
vendored, not reimplemented. If your Stokes code changes, this experiment
changes with it. Smoke-tested: isotropic reads 0.0000, anisotropic reads
0.4000 on injected modulation, residual at machine precision (1e-14).

**Changed:** new `src/polarimetry.py`, `JOINT-PLAN.md` (sections 3a, 3b),
`.gitignore`.
**Blocked on:** you - the phase-set reconciliation (abstract commits to
chromite; no public chromite data exists) is still the one decision only you
can make, and it blocks the 30 Aug abstract.
**Next:** when S3 v2 finishes, `--inspect`, then write the rotation-series
reader and run the ten-mineral symmetry test. Everything in JOINT-PLAN
section 4 phase 2.


## 2026-08-19 — Sibusiso (26)

**Did:** Read Lethabo's REEFPRINT repo end to end and wrote
**[`JOINT-PLAN.md`](JOINT-PLAN.md)**. Lethabo - this one is for you, read it
before the abstract.

**The headline, and it is genuinely a result rather than a framing:** REEFPRINT's
core claim is that pentlandite is cubic (stays dark through analyser rotation)
and pyrrhotite is anisotropic (lights up), phantom-validated at 40.4x
separation. KHANYA's largest mineral-to-mineral error, on held-out data, is
**pentlandite predicted as pyrrhotite 29.2% of the time** - the worst confusion
in the whole matrix, diagnosed as exsolution intergrowth. **Lethabo built a
physical discriminator for exactly the pair my model cannot separate, and
neither of us knew the other's number.** We arrived at the same mineral pair
from opposite ends - his from PGE deportment first principles, mine from a
confusion matrix.

**Second fit:** KHANYA measured that the model is a colorimeter (15% white
balance shift = -0.39 mIoU). REEFPRINT's `calibrate/` module is precisely that
fix and is already on his roadmap. I measured the disease, he specced the cure.

**The module map is close to complementary:** 8 of REEFPRINT's 9 modules are
unbuilt; KHANYA has held-out-validated code for 5 of them (segment, texture,
trust, heads, viz). REEFPRINT has the one thing better modelling cannot give
KHANYA - a physical discriminator plus the calibration story.

**Concrete unlock: download LumenStone S3 v2.** REEFPRINT's week-1 leg (b)
needs a real rotation series. KHANYA already ruled out S3 v2 (5.2 GB) *because*
its XPL rotations are near-duplicates that leak across segmentation splits -
but for polarimetry those rotations ARE the measurement. Same file, opposite
verdict, defensible on both sides.

**The one experiment that decides the joint thesis:** apply REEFPRINT's Stokes
anisotropy to the same sections and measure whether the 29.2% confusion drops.
Falsifiable, uses both codebases, and a null result is still publishable (it
would mean the intergrowth is below optical resolution).

**Also flagged in JOINT-PLAN §5:** merging two architectures in 43 days is
itself the top risk - bridge at the mask/series boundary, do not refactor either
repo into the other. And REEFPRINT's `trust/` open finding **N2** (no fixed
anisotropy threshold is defensible because the noise floor scales as 1/S0) is
**already solved on our side** - conformal conditions on measured error and
reports an interval instead of a threshold. It just needs connecting.

**Changed:** new `JOINT-PLAN.md`.
**Blocked on:** Lethabo - the phase-set reconciliation in JOINT-PLAN §4.2 is a
decision only you can make (the abstract commits to chromite; neither repo has
chromite data and none is public - I searched, see DATA-SOURCES.md).
**Next:** unchanged priority order, now with the joint items folded in - see
JOINT-PLAN §4. S1 retrain still running (epoch 15, val mIoU 0.551, best yet).


## 2026-08-19 — Sibusiso (25)

**Did:** Full repo sweep - senior-dev pass, no experiments. Everything below is
structural/documentation, zero behaviour change.

**1. STATUS.md was genuinely stale, as flagged in (24) - fixed.** It still
quoted the pre-conformal `LIBERATION_MARGIN = 0.089` and the old patch-only
"17% flip / 8.9% MAE" table as if current. Added section 5e stating plainly
that 5d is superseded, with the corrected numbers (margin 0.335, both models
0 unsafe under the shared band) and extended the "never quote" list in
section 6 to cover the old figures explicitly.

**2. README.md was describing a dead pipeline.** It documented `src/train.py`
/ `src/evaluate.py` (the MUMDMC classification pipeline, superseded back in
week 1) as if live, with zero mention of LumenStone, the decision-gap finding,
or any doc written since. Rewrote it as a front door: headline result up top,
a table pointing to STATUS/HANDOVER/PITCH/MINTEK-FIT/DATA-SOURCES, an accurate
repo map distinguishing live from superseded modules, correct setup commands.

**3. Deleted `dashboard/theme.py`.** Dead since (23)'s CSS-inlining fix
(`59e7242`) - still tracked in git, referenced only in a comment, imported by
nothing. Would have misled the next person editing dashboard styling.

**4. Bannered 8 superseded pipeline files** (`src/{config,data,model,train,
evaluate}.py`, `src/segmentation/{data,train,evaluate}.py`) with what they
produced, why they're superseded, and where the live pipeline is - merged
into their existing docstrings, not left as a second floating string literal.
Not deleted: their numbers (MUMDMC 98.3% train-fit, FeM mIoU 0.872) are cited
in the report and must stay reproducible. Left `src/segmentation/model.py`
and `config.py` untouched - confirmed both are genuinely still shared by
`train_lumenstone.py` and `train_patches.py`, not legacy.

**5. Added `.gitattributes`.** Every commit this whole project has printed
"LF will be replaced by CRLF" - pure noise, now fixed at the root
(`* text=auto eol=lf`) instead of tolerated 25 entries running.

**Changed:** README.md (rewrite), STATUS.md (5e + do-not-quote list + date),
HANDOVER.md (this entry + a STATUS.md pointer at the top), deleted
dashboard/theme.py, new .gitattributes, docstring banners on 8 legacy files.
**Blocked on:** nothing.
**Next:** unchanged - S1 retrain to completion (check `s1_retrain.log`, it has
died mid-session 6 times now and always resumes clean, do not treat a dead
process as news), then the QEMSCAN-labelling request, report re-voicing, the
economic case. Abstract due 30 Aug - check today's date before writing it.


## 2026-08-19 — Sibusiso (24)

**Did:** Picked up where (23) left off - both jobs it left running are now
resolved, plus one safety fix.

**1. Resize+refined re-scored under the corrected band - done, and it changes
the model comparison.** `ac3c5c0`. Under the shared +/-0.335 band: resize 7/12
flips (58%), 0 unsafe, 1 conservative; patch 6/12 flips (50%), 0 unsafe, 0
conservative. **Both models now reach zero unsafe errors.** The apparent
quality gap between resize and patch narrows sharply versus the old band's
numbers - most of what looked like a segmentation-quality difference was
partly an artefact of a band too narrow to catch disagreements on either
model consistently. Patch is still marginally better (fewer flips, no
conservative errors) but it's a smaller effect than section 5.0.5 implied.
Report section 5.0.9 has the full table and the framing: the claim to make is
that a calibrated uncertainty band is what prevents the expensive error
*regardless of which segmentation model is deployed* - stronger than a
claim about model accuracy alone, and the one to lead with if asked "why not
just use the better model."

**2. Dashboard had a live offline-safety bug - found and fixed.** `59e7242`.
The redesign in (23)/`c70344c` pulled JetBrains Mono from
`fonts.googleapis.com` in the theme CSS, directly contradicting the module's
own docstring ("must run offline - assume venue wifi fails"). If venue wifi
drops on demo day, that `@import` hangs or fails silently and styling
degrades in an untested way at the worst possible time. Removed; falls back
to the generic `monospace` stack (Consolas on Windows), visually close enough
that nothing depends on the specific typeface. Zero network references left
in `dashboard/app.py` - worth a quick grep for `http` in that file after any
future CSS edit, since this is exactly the kind of thing that's invisible
until the wifi actually cuts.

**3. S1 retrain had died again (6th time) - resumed cleanly, same as every
time before.** Found no python process running and `s1_retrain.log` stopped
mid-epoch-10 at 22:09 last night (session end, not a crash - same pattern as
before). Relaunched `run_s1_retrain.cmd` detached via `Start-Process
-WindowStyle Hidden`; it printed `resuming at epoch 10 (best val mIoU
0.4788)` from `last.pt` and continued. Trend through epoch 9: mIoU climbing
noisily (0.395 -> 0.479 -> 0.364 -> 0.310 -> 0.460, best-checkpoint logic is
carrying it since raw epochs bounce a lot) - still below the 8-epoch/64-patch
run's 0.365 final and well below the published 0.8506 this run exists to
test against. It's running now; nobody needs to watch it, just don't be
surprised if it's dead again next session - that's 6 for 6, worth treating as
the norm for this job rather than a surprise each time.

**Changed:** nothing new this entry beyond confirming/resuming (23)'s
work - see `ac3c5c0` and `59e7242` for the actual diffs (report section 5.0.9,
`reports/decision_gap_refined.json`, `dashboard/app.py`).
**Blocked on:** nothing technical.
**Next:** (a) S1 retrain to completion, then re-derive `LIBERATION_MARGIN` for
S1 specifically - still open, unchanged from (23); (b) **STATUS.md is now
stale** - it still quotes the pre-conformal 0.089 margin and the old
17%/8.9% patch-only figures (lines ~412, ~428) that (23) already superseded
and this entry confirms are superseded twice over. Whoever writes the
abstract should pull numbers from the report (section 5.0.9) or this log, not
STATUS.md, until someone does a full pass to reconcile it; (c) everything
from (22)/(23) already ahead of this in priority is still ahead: the
QEMSCAN-labelling request, re-voicing the report, the economic case. Abstract
due in single digits of days - check the date before writing it.

---

## 2026-08-18 — Sibusiso (23)

**Did:** Four things since entry (22) - the conformal fix is the one to read
first, it changes a number already in the report.

**1. Conformal calibration replaces the fixed uncertainty band, and the old one
was overconfident.** Built `src/conformal.py`. Checked the shipped
+/-8.9% band against its own data: it actually covers only **67% of S2 sections
and 45% of S1 sections**, not the ~90% the word "band" implies to a reader. That
is a real correction to something already stated as fact. Replaced with a
split-conformal half-width - the empirical 85th-percentile residual under
leave-one-out calibration - which is a genuine distribution-free coverage
guarantee rather than a point estimate dressed as one. `LIBERATION_MARGIN` is
now **0.335** (was 0.089). Full derivation in report section 5.0.8, including why
85% and not 90%: with n=12, 1 - 1/(n+1) = 92.3% is the highest level the data can
support at all, so we report the achievable ceiling rather than claim one we
cannot back.

**Re-scored S2 patch+refined under the corrected band - this is a genuinely
better result, not just a more honest one:**

| | Old band (+/-0.089) | Corrected band (+/-0.335) |
|---|---|---|
| Flip rate | 2/12 (17%) | 6/12 (50%) |
| Unsafe | 1 | **0** |
| Conservative | 0 | **0** |
| Flagged | 1 | **6** |

Flip rate triples but **every flip is now a hedge, not an error** - zero unsafe,
zero wasted-energy. The corrected band does not remove disagreements, it
converts all of them into honest ones. This is a better slide than the old 17%
figure, not a worse one, provided it is presented as flip-rate-plus-severity
together and never flip-rate alone. Resize+refined has NOT been re-scored yet
under the new band - queued, running now (`dg_resize_corrected.log`) - do not
quote its old severity numbers, they used the wrong band.

**2. Sampling error, measured independent of the model.** New
`src/sampling_error.py` - splits each ground-truth section into a 3x3 grid and
measures liberation spread across sub-fields of the SAME section, no model
involved. Mean within-section standard deviation **0.174**, comparable to or
larger than our model's liberation error (0.089 on S2, 0.203 on S1). Conclusion,
and it is a good one for the pitch: **a single field of view carries inherent
sampling uncertainty at least as large as our model's error**, so imaging more
fields matters as much as a better network. Also fixed a real crash in
`modal.liberation_index` along the way - it died on a zero-size reduction when
payload pixels survived morphological opening into no particle at all
(reachable from the dashboard on a sparse upload, not just this analysis).

**3. Dashboard redesigned away from Streamlit's default look.** Lab-instrument
aesthetic - dark, monospace, amber accent, numbered panels - instead of generic
SaaS chrome. New: an actual liberation-band visualisation (bar with the 50%
threshold, the conformal zone shaded to scale, a marker at the measured value) -
previously the band was described in text only. **Diagnostic note if it looks
unchanged after an edit:** Streamlit inserts the running script's OWN directory
into `sys.path`, which shadowed a `dashboard.theme` package import and silently
skipped the CSS on first attempt - cost a full server kill+restart to catch,
since hot-reload alone did not surface it. CSS is now inlined into `app.py` to
remove the ambiguity. If a future dashboard edit "doesn't show up," restart the
server process before assuming the code is wrong.

**4. S1 retrain died again and resumed cleanly - the resume support from entry
(21) earned its keep.** Killed at epoch 3 of 20 when the session ended (fifth
time a long job has died this way). `last.pt` had full model+optimiser state;
relaunched and it printed "resuming at epoch 4 (best val mIoU 0.3018)" and
continued rather than restarting from zero. Currently at epoch 3-4,
mIoU 0.181 -> 0.223 -> 0.302, climbing past where the old 8-epoch/64-patch run
plateaued (0.365 final) well before this run's halfway point. Too early to call
whether it approaches the published 0.8506, which is what this run exists to
settle.

**Changed:** new `src/conformal.py`, new `src/sampling_error.py`,
`src/modal.py` (empty-particle crash fix), `src/advisor.py`
(`LIBERATION_MARGIN` 0.089 -> 0.335), `dashboard/app.py` + removed
`dashboard/theme.py` dependency (CSS inlined), report section 5.0.8, new
`reports/conformal_*.json`, `reports/sampling_error_s2.json`.
**Blocked on:** nothing technical.
**Next:** (a) finish re-scoring resize+refined under the corrected band so both
models are reported consistently; (b) S1 retrain to completion, then re-derive
`LIBERATION_MARGIN` for S1 specifically rather than assuming S2's transfers -
S1's own MAE is already known to be larger; (c) everything from entry (22) that
was already ahead of this in priority is still ahead of it: the
QEMSCAN-labelling request, re-voicing the report, the economic case. Abstract
due in single digits of days now - check the date before writing it.

---

## 2026-08-17 — Sibusiso (22)

**Did:** S1 and robustness both finished. **Two results that change what we can
claim — read before writing the abstract.**

**1. The topology finding did NOT generalise to S1.** This is the important one,
because it is our headline claim.

| | Flips | Liberation corr | MAE | Unsafe |
|---|---|---|---|---|
| S2 patch raw | 6/12 (50%) | -0.079 | 46.7% | 0 |
| **S2 patch refined** | **2/12 (17%)** | **+0.947** | 8.9% | 1 |
| S1 patch raw | 15/20 (75%) | +0.295 | 29.7% | 1 |
| **S1 patch refined** | **15/20 (75%)** | +0.198 | 20.3% | 2 |

On S1 topology repair changed the flip rate by nothing. **BUT there is a
confound we cannot resolve:** the S1 segmentation is far weaker (mean IoU 0.33 vs
S2's 0.57, chalcopyrite at 0.0003, tennantite 0.0075), and below some quality
floor there is no coherent particle structure left to repair. So we cannot tell
"the method does not generalise" from "the mask was too broken to fix".

**What this means for the abstract: scope the claim.** Say *"on this dataset,
particle topology mattered more than segmentation accuracy"* and name S1 as the
open question. **Do not claim a general law.** Handled well this is a strength -
we ran a generalisation test nobody asked for, reported that it failed, and can
name the experiment that settles it. That is what originality authentication
rewards. I have scoped the claim in `PITCH.md` and report section 5.0.7.

**2. First true benchmark comparison, and we are well behind.** S1 is the subset
the published ResUnet result uses, with exactly our seven classes. Ours mean IoU
**0.3295** (0.3429 void-borders) against published **0.8373** (0.8506). Gap
-0.508. Two classes collapsed entirely. Sphalerite is the worrying one - 26% of
pixels, not rare at all, and still only 0.28 against a published 0.75.
**The S1 model is undertrained**: seven classes on the same 64-patch, 8-epoch
budget we used for five. The gap is mostly compute, not method. Say that plainly
rather than dressing it up.

**3. Robustness: the model is a colorimeter.** Blur, sensor noise and JPEG 40
cost essentially nothing (+0.0004, -0.0007, -0.014). A 15% white-balance shift
costs **-0.39 mean IoU**, 72% of performance, pixel accuracy 0.879 -> 0.263.
Overexposure hurts more than underexposure because saturation is irreversible -
tell an operator to err dark. This CONFIRMS the optical premise (the model uses
photometry, not texture, exactly as section 3 claims) and is simultaneously our
largest deployment risk.

**4. Grey-world colour constancy fails, informatively.** It achieved invariance
and destroyed the measurement - baseline 0.5448 -> 0.1358. Grey-world assumes the
average scene is achromatic, but in a polished section the average colour is
dominated by the most abundant phase, which is the quantity we are measuring. **No
scene-statistics heuristic can work here.** The conclusion is a deployment spec,
not an apology: *KHANYA requires calibrated illumination against a known
reflectance standard; it does not require a particular microscope, camera or
laboratory.* That is what quantitative reflectance microscopy has always
required.

**Changed:** report sections 5.0.6, 5.0.6.1, 5.0.7; `PITCH.md` (claim scoped);
`src/robustness.py` (grey-world); new `reports/benchmark_s1_patches.json`,
`reports/decision_gap_s1_patches*.json`, `reports/robustness_s2_resize*.json`.
**Blocked on:** nothing.
**Next:** **train S1 to convergence** - it is now the single most informative
experiment left, because it decides whether our headline claim generalises or
was an S2 artefact. Everything else is unchanged and still ahead of it in
priority: the QEMSCAN-labelling request by 30 Aug, re-voicing the report, and the
economic case. Also note `LIBERATION_MARGIN` (0.089) was derived from S2 error;
S1's MAE is 20.3%, so the band is too narrow there and must be re-derived per
dataset rather than assumed to transfer.

---

## 2026-08-17 — Sibusiso (21)

**Did:** Four things, and **`PITCH.md` is the one to read first** - it is how we
win, and it drives what you write in the abstract.

**1. The distinguisher, settled.** We do not win on accuracy: mean IoU 0.5725
against a published 0.8506 on comparable data, trained on a laptop CPU. Any pitch
competing on model quality puts us mid-pack. We compete one level up: *everyone
else shows a model, we show the measurement that says whether a model is good
enough to act on - and we found the accuracy number everyone reports does not
answer that*. Full positioning, abstract structure, 8-slide plan and
weakness-framing table in `PITCH.md`.

**2. Benchmark protocol correction - IMPORTANT, and it affects the abstract.**
Our 0.5725 was being set informally against the published 0.88, and that was
invalid twice: the published numbers are on S1 or S1+S2 jointly, not S2, AND
petroscope evaluate with **void borders** (excluding pixels near class
boundaries, since a hand-drawn boundary is uncertain to a few pixels). They
publish two columns; we were quoting our stricter number against their table
without checking which we were reading. Implemented their protocol - on S2 it
lifts us 0.5725 -> **0.6034**, PA 0.8914 -> 0.9131. **Quote the matching column
or say which one you are using.** `src/benchmark.py` prints both.

**3. S1 finished and is being evaluated.** All 8 epochs, best val patch mIoU
0.3651. Whole-section eval running now. The published ResUnet table covers
**exactly our S1 class set**, so this gives the first true class-by-class
comparison we have ever had. Early rows show large liberation disagreements, so
expect S1 decision numbers to be worse than S2 - useful either way, since it
tells us whether the topology finding generalises or is S2-specific.

**4. Robustness harness added** (`src/robustness.py`), running now. Every image
we have came from ONE microscope, ONE camera, ONE lab. This perturbs exposure,
white balance, contrast, focus, sensor noise and JPEG quality on the held-out
sections and re-measures IoU with masks untouched. It addresses report limitation
7, which was unaddressed. **It does NOT test a genuinely different optical
train** - LumenStone V1 (same samples, varying real conditions) is the proper
test if we get time.

**A correction to head off, because it came up:** the model cannot work on hand
specimens or phone photographs, and this is physics rather than effort.
Liberation is the exposure of a grain at a particle surface and modal mineralogy
is area fraction in a section plane - both exist only at grain scale, tens of
microns. An image that never resolved individual grains does not contain the
information. The brief also specifies reflected-light microscopy explicitly, and
Mintek do quantitative mineralogy on polished sections. Also: our test-set
performance is **not** overfitting - the 12 sections were never seen in training
or checkpoint selection. What varying-camera data would probe is **domain
shift**, which is item 4 above. Do not write "overfitting" in the abstract for
this; someone will correct it.

**Changed:** new `PITCH.md`, new `src/benchmark.py`, new `src/robustness.py`,
new `src/inspect_pipeline.py`, `src/segmentation/metrics.py` (void borders),
`reports/figures/*`, `reports/benchmark_s2_patches.json`.
**Blocked on:** nothing. Two jobs running (S1 eval, robustness).
**Next, ranked by effect on winning:** (1) the mentor/QEMSCAN-labelling request
by 30 Aug - highest leverage, converts our weakest point into a partnership;
(2) re-voice the drafted report sections, originality is authenticated for
finalists; (3) build the economic case, our money argument is currently three
[CITE] markers; (4) rehearse the demo offline. Further modelling is genuinely
last. **13 days to the abstract.**

---

## 2026-08-17 — Sibusiso (20)

**Did:** Three things. Downloaded LumenStone S1, researched Mintek properly, and
**found that our core value proposition is wrong for this audience.**

**1. Read `MINTEK-FIT.md` before writing any part of the abstract.** Our pitch
has been "cheap optical rig instead of a multi-million-rand automated mineralogy
instrument". **Mintek's Mineralogy Division already owns QEMSCAN**, plus XRD,
SEM-EDS, EPMA and micro-XRF - they are the national *provider* of automated
mineralogy, not a customer priced out of it. Opening on instrument cost tells the
room we did not research them and positions us against the capability they built.

The reframe, in one line: we are not a cheaper instrument, we are **an advanced
process-control input for flotation circuits** - and both halves of that are
things Mintek has publicly committed to in 2026. Their flotation group is
targeting recognition as a global centre of excellence (PGM Industry Day, July
2026), and their own R&D voice names AI, ML, digital twins and advanced process
control as what will reshape mineral processing.

**The single highest-leverage item, and it changes our data ask.** A QEMSCAN map
of a polished section IS a pixel-level label for an optical image of that same
section. Mintek runs those jobs routinely. So the 30 August mentor request should
not be "please send us some images" - it should be **"can QEMSCAN maps be used as
segmentation labels for optical images of the same sections"**. That is
specific, it is valuable to them (every characterisation job becomes reusable
training data for African ore types no public dataset covers), and it is the one
thing that closes our largest gap. Confirmed by search that **no open dataset of
Bushveld/UG2/Merensky/Platreef material exists** - published papers, not released
data. That absence is exactly why their archive is the asset.

**2. S1 downloaded and wired up.** 64 train / 20 test, 7 classes, verified by
scanning the masks. Subset now selected by `KHANYA_SUBSET` env var, default S2,
so every existing result reproduces unchanged and S1 cannot overwrite S2
checkpoints or metrics. S1 patch training running now (~2.5h). This tests whether
the topology-over-IoU finding generalises to a different ore genesis, or is an S2
artefact - which we need to know before 1 October, not after a judge asks.

**3. Commodity honesty table is in MINTEK-FIT.md section 4.** We can defensibly
claim PGM/base-metal relevance by assemblage analogue and Cu-Pb-Zn directly. We
have **no chromite data**, so we cannot claim UG2 grade estimation. Do not let
the abstract imply otherwise.

**Changed:** new `MINTEK-FIT.md`, `DATA-SOURCES.md` (section 0b dataset search),
`src/segmentation/lumenstone.py` (subset support + full codebook),
`src/segmentation/patches.py`, `src/segmentation/train_patches.py`,
`src/decision_gap.py`, `src/modal.py` (S1 roles).
**Blocked on:** nothing. S1 training in progress.
**Next:** (a) S1 eval + decision_gap to test generalisation; (b) reframe report
section 3 away from instrument cost toward deployment location and turnaround;
(c) re-voice the drafted report sections and clear the 8 [CITE] markers;
(d) your three calls, now including the reframed mentor/QEMSCAN-labelling ask.
**13 days to the abstract.**

---

## 2026-08-17 — Sibusiso (19)

**Did:** Built the venv and **the demo now runs.** `python -m venv .venv` then
`pip install -r requirements.txt` inside `KHANYA/`. The starlette pin resolved
the launch blocker from entry (18) - venv has streamlit 1.61.0, starlette 1.6.0,
torch 2.13.0+cpu, opencv 5.0.0. Dashboard serves on localhost:8501 and the full
code path was verified inside the venv: test_04 gives liberation 55%, inside the
band, returning "Marginal - verify before acting"; test_06 gives 11% and returns
"Grind finer". **Always run the demo from `.venv`, never global Python** - global
streamlit still cannot import.

Added a `khanya-advisor` entry to the parent repo's `.claude/launch.json` so the
dashboard starts from the venv.

**Changed:** `.venv/` (gitignored), `.gitignore`; parent repo
`.claude/launch.json`.
**Blocked on:** nothing technical. **The demo deliverable is now working.**
**Next:** unchanged and now the whole remaining list - re-voice the drafted report
sections and clear the 8 [CITE] markers, build the energy/cost case, and your
three calls: abstract scope, R6,000 rig, mentor request. **13 days to the
abstract.**

---

## 2026-08-16 — Sibusiso (18)

**Did:** Two things - wrote the report prose, and found that **the demo does not
currently start.**

**1. Report prose written.** Sections 1, 2, 3, 4, 5, 6, 8 and 10 are now written
rather than skeleton; the report is ~6,500 words. **They are marked DRAFT at the
top of the file and must be re-voiced before submission** - Mintek runs explicit
AI-generation checks and originality is scored, so this is mandatory, not
cosmetic. There are **8 `[CITE]` markers** for claims still needing a reference,
and section 10 ends with an explicit list of what is still required. Do not
submit with any [CITE] marker remaining.

Section 4 states plainly that we are NOT targeting mean IoU 0.88 and do not
approach it - our 0.5725 came from 12 CPU epochs. What we target instead is the
recommendation error rate. That framing is deliberate and it is what makes the
weak IoU defensible rather than embarrassing.

**2. LAUNCH BLOCKER FOUND - the dashboard cannot start.** `import streamlit`
fails outright: streamlit 1.58.0's gzip middleware imports
`DEFAULT_EXCLUDED_CONTENT_TYPES` from starlette, which starlette 0.41.3 (what is
installed) does not export. streamlit's own metadata only asks for
`starlette>=0.40.0`, so pip resolved a version that then fails at import -
nothing we did wrong, but it means **the offline demo deliverable is currently
broken on this machine.** Verified fix: starlette 1.6.0, now pinned as
`starlette>=1.6` in `requirements.txt`. I verified it in an isolated directory
rather than upgrading the global package, because other projects on this machine
may depend on the older starlette.

**This is exactly the failure that ruins a venue demo**, so it needs resolving
properly and early - the README already prescribes a venv (`python -m venv
.venv`), and building that venv from `requirements.txt` is the clean fix. Doing
that also gives us a reproducible environment for the 1 October laptop, which we
need anyway.

**3. Dashboard updated to match the validated pipeline.** It was still using raw
connected components and had no uncertainty band, so it would have demonstrated
liberation numbers uncorrelated with truth. Now uses `refine=True` and surfaces
the marginal band explicitly, including how far liberation sits from the
threshold relative to the estimator's own error.

**Changed:** `reports/KHANYA-01-research-phase.md` (sections 1,2,3,4,5,6,8,10),
`dashboard/app.py` (refined estimator, band display), `requirements.txt`
(starlette pin).
**Blocked on:** the venv/starlette fix before the demo can be shown or rehearsed.
**Next:** (a) build the venv and confirm the dashboard runs end to end offline;
(b) re-voice the drafted sections and fill the 8 [CITE] markers; (c) energy/cost
case; (d) your three calls - abstract scope, R6,000 rig, mentor request. 14 days
to the abstract.

---

## 2026-08-16 — Sibusiso (17)

**Did:** Final band results, and **a correction you need before writing
anything.**

| Config | Flips | unsafe | conservative | flagged |
|---|---|---|---|---|
| resize + refined + band | 4/12 (33%) | **0** | 1 | 3 |
| patch + refined + band | 2/12 (17%) | **1** | 0 | 1 |

**CORRECTION: entry (15) claimed patch+refined had ZERO unsafe flips. That was
wrong.** It used a narrow definition counting only a predicted "Continue at
current setpoint". The severity classifier is stricter and right: test_04 has
truth liberation 40% ("grind finer") against predicted 74% ("adjust reagent
dosage"). The plant does not grind, so locked payload still reports to
tailings - unsafe by consequence even if the action is not literally "continue".
**The honest figure is 1 unsafe, not 0. Do not quote the zero.**

**The better model is the LESS safe one, and this is worth presenting rather
than hiding.** On test_04 the resize model predicts 55% - inside the band, so it
hedges. The patch model predicts 74% - outside the band, so it is confidently
wrong. Higher average accuracy, worse calibration on exactly the case that
matters. Real trade-off: patch is more decisive (half the disagreements), resize
is safer (no metal at risk). In flotation an unnecessary check costs far less
than lost metal, so **for a deployed advisory system resize+band is the
defensible default**, with patch reserved for human-in-the-loop use. That is a
more sophisticated answer than "we picked the highest mIoU" and judges will
respect it.

Also note the flip rate barely moves when the band is added. That is expected
and is the point - the band converts dangerous disagreements into honest ones
rather than removing them. **Anyone reading flip rate alone concludes nothing
improved, so always show the severity split alongside it.**

**Changed:** `STATUS.md` section 5d, `reports/decision_gap_patches_refined.json`.
Prediction caches for both models are now populated, so any future threshold or
policy change re-scores in seconds.
**Blocked on:** nothing. **Modelling is finished** - further experiments have
poor expected value versus writing.
**Next:** report prose (sections 1, 2, 4, 6, 8, 10 still skeleton), energy/cost
case, and your three calls: abstract scope, R6,000 rig, mentor request. 14 days
to the abstract.

---

## 2026-08-16 — Sibusiso (16)

**Did:** Built the uncertainty band from entry (15). Three parts:

1. **The band itself** (`src/advisor.py`). When liberation sits within
   `LIBERATION_MARGIN` of the 0.50 floor, the advisor returns **"Marginal -
   verify before acting"** and names both candidate actions instead of asserting
   one. **The width is not invented: 0.089 is this estimator's own mean absolute
   error on the 12 held-out sections** (reports/decision_gap_patches_refined.json).
   If the estimator changes, re-derive it - it is a property of the measurement
   chain, not a preference.

2. **Ground truth gets margin=0.** An annotation carries no estimator error, so
   banding the reference too would compare a hedged reference against a hedged
   prediction and hide the very disagreement we are measuring. `advise()` takes
   `liberation_margin` for this reason.

3. **Flip severity classification** (`src/decision_gap.py`). Counting a hedge
   the same as a confident wrong instruction would understate the band entirely,
   since converting the former into the latter is its whole purpose. Flips are
   now **unsafe** (told to continue while payload is locked - metal at risk),
   **conservative** (acts unnecessarily - energy, not metal), or **flagged**
   (hedged to manual review - costs a check, loses nothing).

**Result on the resize model: unsafe flips 1 -> 0.** Full: 0 unsafe, 1
conservative, 3 flagged, flip rate unchanged at 33%. That flat flip rate is the
point - the band does not make disagreements disappear, it **converts dangerous
disagreements into honest ones.** Report it that way; a judge who sees flip rate
alone will think nothing improved.

**Also added prediction caching.** Predicted masks depend only on the model,
never on advisor policy or the particle estimator, so they are cached to
`data/derived/preds_{model}/` (gitignored). Inference over 12 native-resolution
sections costs over an hour; re-scoring a threshold change against cached masks
now costs seconds. **Threshold and policy work is no longer gated on inference** -
this matters for the remaining weeks, since three of four thresholds are still
placeholders and will need tuning.

**Changed:** `src/advisor.py` (band + `liberation_margin` arg),
`src/decision_gap.py` (severity classification, prediction cache),
`.gitignore`, `reports/decision_gap_refined.json`.
**Blocked on:** nothing. `patches --refine` re-running with the band (~75 min,
also populating its cache so future runs are instant).
**Next:** modelling is done. Report prose, energy/cost case, and your three
calls - abstract scope, R6,000 rig, mentor request. 14 days to the abstract.

---

## 2026-08-16 — Sibusiso (15)

**Did:** Best model + best estimator. **This is our headline result.**

| Setup | Flips | Liberation corr. | MAE | Unsafe "continue" |
|---|---|---|---|---|
| resize + raw | 6/12 (50%) | +0.128 | 38.7% | 2 |
| resize + refined | 4/12 (33%) | +0.709 | 16.4% | 1 |
| patch + raw | 6/12 (50%) | -0.079 | 46.7% | 1 |
| **patch + refined** | **2/12 (17%)** | **+0.947** | **8.9%** | **0** |

**The two changes are complementary and that is the story.** Better segmentation
alone bought nothing (50% -> 50%). Better estimator alone helped (50% -> 33%).
Together: **17% flip rate, liberation correlation 0.947, and ZERO flips in the
expensive direction** - no section is told to continue at setpoint while its
payload is locked. Better per-class accuracy was not useless, it was *unusable*
until particle topology was good enough to exploit it. **Do not present either
change on its own - in isolation each looks far weaker than it is.**

**What still fails is worth knowing precisely:** both remaining flips straddle
the 0.50 liberation threshold (test_04 truth 40% vs predicted 74%; test_05 truth
32% vs predicted 52% - clearing the floor by two points). So the residual issue
is **threshold brittleness**, not gross error: within about one MAE of a trip
point the recommendation is close to a coin toss. The fix is cheap and I would
build it before the event - a declared uncertainty band, so when the estimate
sits within the estimator's own error margin of a threshold the output is
"marginal - verify" rather than a confident instruction. That is also a good
answer to the obvious judge question about trusting the number.

**Changed:** `STATUS.md` section 5c, `reports/KHANYA-01-research-phase.md`
new section 5.0.5, new `reports/decision_gap_patches_refined.json`.
**Blocked on:** nothing.
**Next:** the modelling is now good enough to stop. Remaining work is writing
and decisions, not experiments: report prose (sections 1, 2, 4, 6, 8, 10 are
still skeleton), the energy/cost case, the uncertainty band above, and your
three calls - abstract scope, R6,000 rig, mentor request. 14 days to the
abstract.

---

## 2026-08-16 — Sibusiso (14)

**Did:** Acted on entry (13)'s conclusion and **it worked.** Added a particle
refinement stage to `src/modal.py` - speckle removal, hole filling, and
marker-controlled watershed on the distance transform - applied identically to
ground-truth and predicted masks, because the *estimator* is what changed.

| Setup | Flips | Liberation corr. | MAE |
|---|---|---|---|
| resize, raw components | 6/12 (50%) | +0.128 | 38.7% |
| **resize, watershed+fill** | **4/12 (33%)** | **+0.709** | **16.4%** |
| patch, raw components | 6/12 (50%) | -0.079 | 46.7% |

**Liberation correlation +0.128 -> +0.709, error more than halved, flip rate
50% -> 33% - by changing the estimator, on the WEAKER model, with no
retraining.** That is direct confirmation of the entry (13) diagnosis: the
binding constraint was particle topology, not per-class accuracy.

Why each piece matters, in case you are writing this up: hole filling is not
generic hygiene here, it is specifically repairing the magnetite failure -
magnetite is predicted as background 92.3% of the time, so every magnetite
inclusion punches a hole that splits a grain in two. The three failure modes
(speckle / holes / merged grains) each get their own repair and each is
documented in `modal.py`.

**Important: all liberation numbers before this change are superseded.** The
refinement alters ground-truth liberation too, sometimes drastically (test_10
82% -> 3%, as 209 particles resolve to 51). That is correct rather than
alarming - the raw estimator was counting annotation speckle as fully liberated
particles - but it means every liberation figure in older entries is stale.

**Changed:** `src/modal.py` (refinement stage, `refine=` on `analyse` and
`liberation_index`), `src/decision_gap.py` (`--refine`), `requirements.txt`
(opencv-python), `STATUS.md` section 5c, new `reports/decision_gap_refined.json`.
Both scipy and OpenCV fall back to plain connected components if missing, so the
venue demo cannot die on an import.
**Blocked on:** nothing. `decision_gap --model patches --refine` running
(~75 min) - best model plus best estimator, expected to be our headline number.
**Next:** once that lands, the modelling is in good enough shape to stop and
write. Priorities become the report prose, then the three decisions still with
you - abstract scope, R6,000 rig, mentor request - at 14 days to the abstract.

---

## 2026-08-16 — Sibusiso (13)

**Did:** Ran the decision-gap on the better model, and got the most important
result of the project so far. **It is not the one we were chasing.**

**Better segmentation did NOT buy better decisions.** Both models measured at
native resolution against the same ground truth:

| | Resize | Patch |
|---|---|---|
| Mean IoU | 0.545 | **0.5725** |
| Flips | **6/12 (50%)** | **6/12 (50%)** |
| Liberation corr. vs truth | +0.128 | **-0.079** |
| Liberation mean abs error | 38.7% | 46.7% |

+2.8 points of mean IoU changed the flip rate by **nothing**, and predicted
liberation is **uncorrelated** with true liberation - slightly negative for the
better model. Predicted liberation is currently noise.

**Why, and it is structural not statistical:** liberation comes from connected
components, so particle identity is a matter of **topology**. A few misclassified
boundary pixels bridge two particles into one or split one in two, which changes
that particle's payload fraction discontinuously. Per-class IoU rewards getting
grain *interiors* right, which is nearly independent of getting grain
*boundaries* right. Optimising one does not optimise the other.

**Correction you need to know about: the 33% figure is dead.** It was measured
with both sides at 512x688, and `MIN_PARTICLE_PIXELS` is a fixed pixel count, so
it meant a different *physical* grain size there. Native resolution is the
correct reference and is what a plant actually receives. **50% is the figure,
for both models.** I have corrected `STATUS.md`, the research report section
5.0.3, and added report section 5.0.4. If you already wrote 33% anywhere, change
it.

**What this means for the pitch, and I think it is actually a stronger story:**
the advisor's decision logic is *validated* - on ground-truth masks it gives
coherent recommendations across the full range of ore textures. The *chain* is
not validated, because segmentation cannot yet supply accurate particle
topology. That is honest and defensible, and the finding generalises: **in
image-based mineralogy, per-class IoU is a poor proxy for operational value.**
That is a genuinely useful thing to tell a room full of metallurgists.

**Changed:** `src/decision_gap.py` (all comparisons now at native resolution for
both models - the resize model's prediction is upsampled, which is what a plant
would receive anyway), `STATUS.md` section 5b and section 6,
`reports/KHANYA-01-research-phase.md` sections 5.0.3 and new 5.0.4,
`reports/decision_gap.json`, `reports/decision_gap_patches.json`.
**Blocked on:** nothing technical.
**Next - and this redirects the remaining effort:** stop chasing IoU, it is
demonstrably the wrong target. Go at boundary topology instead: morphological
post-processing and watershed separation; or a liberation estimator less brittle
than raw connected components (erode particles before measuring composition, or
an area-fraction proxy that degrades gracefully); or instance-aware segmentation
that predicts particles directly. Alongside that, the three decisions still with
you - abstract scope, R6,000 rig, mentor request - are now the critical path at
14 days out.

---

## 2026-08-16 — Sibusiso (12)

**Did:** Both jobs from entry (11) finished. Headline: **the patch model is our
best result and should be the primary one from here — whole-section mean IoU
0.5725, pixel accuracy 0.8914**, against the resize baseline's 0.545 / 0.879.
Native resolution improved every class that was already working (pentlandite
0.485 -> 0.547, chalcopyrite 0.548 -> 0.576, background 0.827 -> 0.871).

**CE+Dice did not help.** Full 8 epochs, best val patch mIoU 0.4739 vs CE's
0.5384, magnetite still 0.0000 every epoch. So three independent approaches have
now failed on magnetite. I stopped guessing and diagnosed it.

**Diagnosis, and this is the useful part: the model never predicts magnetite at
all.** Zero pixels across the entire test set against 33,469 in ground truth -
total class collapse, not sloppy boundaries. **92.3% of magnetite is predicted as
BACKGROUND**, not as another sulphide. That is mineralogically coherent:
magnetite has low reflectance, it is dark grey and optically closer to the dark
mounting resin than to the bright sulphides. The model is not confusing two
minerals, it is failing to separate a dark mineral from empty space - which is
exactly why neither more pixels nor a rebalanced loss helped. **Neither
addresses a reflectance ambiguity.**

Bonus finding worth writing up as domain knowledge rather than generic error:
**pentlandite is predicted as pyrrhotite 29.2% of the time** - the classic
exsolution-intergrowth problem, pentlandite exsolves as flames within pyrrhotite
and both are similar bronze-cream colours. That is why pentlandite sits at ~0.55
rather than ~0.85.

**My recommendation: stop attacking magnetite.** Report a **four-phase** result
with magnetite as a named, diagnosed limitation. Four phases still clears the
brief's >=3 floor, and a well-characterised failure with a real mineralogical
explanation is worth more to judges than a fifth class we cannot make work. If
we try anything, try contrast normalisation on the dark end - that targets the
actual mechanism rather than guessing again.

**Untested - do NOT put in the abstract yet:** if magnetite is called background,
it is excluded from ore area, which shrinks the modal-mineralogy denominator and
inflates payload fraction - the direction of both unsafe flips. Plausible causal
chain from rare-class collapse to the expensive operational error, but verify it
first.

**Changed:** `STATUS.md` section 3.0 (full comparison + diagnosis),
`src/decision_gap.py` (takes `--model {resize,patches}`), new
`reports/magnetite_confusion.json`, `reports/lumenstone_s2_patches_test_metrics.json`.
**Blocked on:** nothing. `decision_gap --model patches` running (~75 min) to see
whether the better model actually buys better decisions - not guaranteed, since
the thresholds sit on liberation and payload fraction, not on IoU.
**Next:** that flip rate vs the baseline's 33% is the headline slide. After it,
the priorities are report prose and the three decisions still open with you -
abstract scope, the R6,000 rig, and the mentor request. 14 days to the abstract.

---

## 2026-08-16 — Sibusiso (11)

**Did:** Acted on entry (10)'s finding. Since native-resolution patch sampling
did NOT move magnetite off IoU 0.000, the problem is the objective, not the
data pipeline - so added `src/segmentation/losses.py`: soft Dice combined with
cross-entropy, selectable via `--loss dice`.

**The distinction that makes this legitimate, and it matters for the writeup:**
petroscope warn that class weighting does not fix mineral imbalance. That is a
statement about reweighting the *per-pixel* CE term - each pixel still competes
individually, so a 1.84% class still contributes ~1.84% of gradient no matter
what constant multiplies it. Soft Dice is computed **per class over the whole
batch and then averaged across classes**, so magnetite's term counts as much as
pyrrhotite's despite 24x fewer pixels. Different mechanism, so their warning
does not cover it. **Do not write this up as "petroscope were wrong."**

Verified the loss actually does what is claimed before spending compute: on a
synthetic case with a 1.46% rare class, a model that never predicts it pays
0.829 in the Dice term, and predicting it correctly drops total loss 2.08 ->
1.84. Under plain CE that same correction is nearly free, which is precisely why
the model never bothers. Gradients finite.

Combined with CE rather than used alone - Dice alone is unstable early, its
gradient is near-flat while predictions are diffuse.

**Changed:** new `src/segmentation/losses.py`; `train_patches.py` takes
`--loss {ce,dice}`. Each loss writes to its **own** checkpoint directory and its
own metrics JSON - the CE run's checkpoint must not be clobbered while it is
being evaluated, and a controlled comparison is worthless if runs overwrite each
other.

**Blocked on:** nothing. Two jobs running concurrently on CPU (they share cores,
so both are slower than solo): whole-section eval of the CE patch model
(~56 min), and CE+Dice training.
**Next:** when both land, compare three whole-section results like-for-like -
resize baseline (mIoU 0.545, magnetite 0.000), patch+CE, patch+CE+Dice - then
re-run `python -m src.decision_gap` against the best and check the flip rate
versus 33%. If Dice still leaves magnetite at 0.000, stop attacking it and
report it honestly as a four-phase result with a named limitation; four working
phases still clears the brief's >=3 floor.

---

## 2026-08-16 — Sibusiso (10)

**Did:** Added **`STATUS.md`** - a single snapshot of what exists, what does not,
and what to do next, written for you to build architecture against. Read that
first; this log is the running history, STATUS.md is the current picture.

**The headline, and it is a negative result:** the patch experiment's core
hypothesis is dead. We believed magnetite scored IoU 0.000 because the 6.6x
downsample destroyed fine grains, and that native-resolution patches would fix
it. The patch model trained to epoch 7 at full native resolution with magnetite
present in ~44% of patches, and **magnetite still scored IoU 0.0000 at every
epoch.** Resolution was not the binding constraint.

What that means for architecture: magnetite is not failing because it is small,
it is failing because the model never learns to predict it at all under plain
cross-entropy - the loss stays dominated by pyrrhotite at 45% of pixels.
Balanced sampling fixed **exposure** but not **prior**. The next thing to try is
a region-based loss (Dice / Focal / Tversky), which is a different mechanism
from the class weighting petroscope warns against - worth being precise about
that distinction, they are not the same claim.

Caveat: those are balanced-patch *validation* numbers and are not comparable to
whole-section numbers. The whole-section eval of the patch checkpoint is running
now and settles it. Training itself was cut off at epoch 7 of 8 when the machine
session ended - the checkpoint saved, so nothing was lost.

**Changed:** new `STATUS.md`.
**Blocked on:** nothing technical. Three decisions still sitting with you and now
14 days from the abstract deadline - see issue #1: abstract scope, the R6,000
rig, and the mentor request plus your ID/T-shirt/contact details.
**Next for you:** read `STATUS.md` sections 4 and 5 - section 4 is the pipeline
architecture and where uncertainty enters it, ranked by severity; section 5 is
the priority order. Section 6 lists four numbers that must never be quoted, which
matters most for whatever goes into the abstract.

**Admin note so nobody retries it:** repo-collaborator *admin* cannot be granted
on a personal GitHub repo - only read/write. The API accepts the request and
silently no-ops. You have write, which covers clone/pull/push/branch/PR, i.e.
everything the build needs. Admin would require moving the repo into an org.

---

## 2026-08-14 — Sibusiso (9)

**Did:** Built patch-based sampling at native resolution - the fix for the
magnetite IoU 0.000 failure in entry (8). Two independent changes, deliberately
kept conceptually separate in `src/segmentation/patches.py`:

1. **Native resolution.** Patches are cropped from the full 3396x2547 image and
   never resized, so the model sees real grain boundaries at sensor resolution.
   The resize baseline threw away a 6.6x linear downsample before training.
2. **Balanced patch centres.** A class is picked uniformly first, then a pixel
   of that class, then a 512px patch is cropped around it. Magnetite centres
   ~20% of patches against its 1.84% area share.

**Verified the sampler does what it claims before spending compute on it:**
across 32 sampled patches, magnetite appears in 14 of them (vs 1.84% of pixels
overall). But its pixel share *inside* those patches is still 1.70% - so
**balanced centring fixes EXPOSURE, not PRIOR.** Be precise about that
distinction if asked; claiming it "fixes class imbalance" would be wrong and is
exactly the kind of overclaim the petroscope authors warn against.

Also dropped LR to 2e-4 from the baseline's 1e-3. In the baseline run the
minerals sat at IoU 0.0 for several epochs, which is the signature of too high
an LR for a 5-class fine-tune of a pretrained backbone.

**Changed:** new `src/segmentation/patches.py`, new
`src/segmentation/train_patches.py`, `.gitignore`. Kept separate from
`train_lumenstone.py` on purpose - the whole value here is a controlled
comparison against the resize baseline, which is worthless if the baseline
drifts. A class-coordinate index is cached to
`data/raw/lumenstone/s2_class_index.npz` (gitignored, rebuilds in ~40s).

**Blocked on:** nothing. Training running now (8 epochs, 64 patches/epoch, CPU,
~2.2h).

**Important on how to read the two runs:** the patch model's *validation*
numbers are computed on balanced patches and are therefore NOT comparable to
the resize baseline's whole-section validation - balanced patches flatter rare
classes by construction. The only fair comparison is `--eval`, which runs
sliding-window inference over whole native-resolution sections, exactly like the
baseline scored. **Do not put patch-val numbers next to baseline-val numbers on
a slide.**

**Next:** when training finishes, run `--eval` for the honest whole-section
number, then re-run `python -m src.decision_gap` and compare the flip rate
against the baseline's 33%. That before/after, framed as metal recovered rather
than IoU, is the strongest slide available.

---

## 2026-08-14 — Sibusiso (8)

**Did:** S2 baseline finished. **First result that meets the brief's >=3 phase
floor with a real held-out number: mean IoU 0.545, pixel accuracy 0.879 on 12
unseen sections, 5 classes.** Per-class: pyrrhotite 0.864, background 0.827,
chalcopyrite 0.548, pentlandite 0.485, **magnetite 0.000**. Numbers in
`reports/lumenstone_s2_test_metrics.json`.

**Read this before quoting the headline number.** Magnetite fails completely,
and it IS present in test (0.79% of pixels), so that is total failure on the
rare class, not absence - the exact imbalance failure petroscope warns about,
reproduced in our own numbers. Two separable causes: the class is rare, and the
6.6x downsample from 3396x2547 to 512x688 destroys fine grains before the model
sees them. Also, our val set (6 images) is too small to select checkpoints on -
pentlandite scored 0.026 on val against 0.485 on test, and val is 45.8%
background against test's 25.0%.

Then built `src/decision_gap.py` to answer the question IoU cannot: does being
this wrong change what the plant is told to do? Runs the advisor twice over the
same 12 sections, ground-truth masks vs predicted. **4 of 12 recommendations
flip (33%)** - `reports/decision_gap.json`. Direction matters more than count:
two flips say "continue at setpoint" on ore whose payload is actually locked
(test_04 liberation 9%->75%, test_05 4%->58%), which sends recoverable metal to
tailings and is the expensive direction. One is conservative (test_09, wasted
grinding energy, no metal lost). One is an outright detection miss on a 1%
payload field (test_02). **Conclusion: the model is not yet fit to drive this
advisor**, and the flip rate is a better measure of that than mIoU.

Caught a methodology trap worth knowing about: comparing GT at native
resolution against predictions at 512x688 gave a 50% flip rate, but ~44x fewer
pixels per grain means the minimum-particle-size filter drops far more particles
on the predicted side. Three of those six flips were scale artefacts. GT is now
downsampled to the network's working size before comparison; **33% is the
like-for-like figure, 50% is wrong** - do not quote the 50%.

**Changed:** new `src/decision_gap.py`, `reports/KHANYA-01-research-phase.md`
(new sections 5.0.2 and 5.0.3), `reports/lumenstone_s2_test_metrics.json`,
`reports/decision_gap.json`.
**Blocked on:** nothing. Access check: you (LethaboMH14) have write access and
it is active - clone, pull and push all work.
**Next, in priority order:** (1) patch-based sampling at native resolution -
addresses both magnetite causes at once and is what petroscope's authors say is
necessary; this is the single highest-value experiment left. (2) Grouped
cross-validation over the 37 training sections instead of the 6-image val set.
(3) Re-run decision_gap after both and show the flip rate coming down - that
before/after is the strongest slide we have.

---

## 2026-08-14 — Sibusiso (7)

**Did:** Built the operational feedback layer for real - it was the weakest of
the brief's three deliverables and both its inputs were fake (classifier
confidences standing in for area fractions, liberation coming from a slider the
presenter dragged). Both are now measured from the predicted mask.
`src/modal.py` computes modal mineralogy as a fraction of **ore** area excluding
mounting resin, and computes **liberation by particle composition**: connected
components of non-resin pixels are particles, a particle is liberated when the
payload phase occupies >=50% of it, and the index is the mass-weighted share of
payload sitting in liberated particles. Validated on all 12 held-out S2 test
sections using ground-truth masks - it spans 0% to 100% and tracks the
mineralogy correctly (few large massive-sulphide particles score ~0%, many
small disseminated grains score >80%). `src/advisor.py` rewritten to reason over
metallurgical **roles** (payload/reject/oxide/gangue/deleterious) rather than
mineral names, with the mapping in `modal.py` - so swapping ore body changes a
mapping, not the decision logic, and REEFPRINT data drops straight in if Mintek
releases any. Dashboard rewritten onto the segmentation path end to end.

**Two findings worth knowing before you quote anything:**
(1) Calling all three sulphides "payload" made liberation saturate at ~100%
everywhere - in massive sulphide the payload IS the rock. Fixed by the correct
metallurgy: pentlandite + chalcopyrite are payload, **pyrrhotite is the
rejection target** (grade dilution, smelter sulphur load - standard practice in
magmatic Ni-Cu). Caveat: pyrrhotite does carry some Ni/PGE in solid solution, so
that is a grade-vs-recovery trade, not free money. The saturation result is
written up in report section 7.4 as a negative result, not deleted.
(2) Liberation from 2D sections is biased **high** against true volumetric
liberation - a section plane can cut the free rim of a particle with a locked
core. We apply no stereological correction, so our index is an upper bound.
Safe direction for "grind finer", unsafe for "continue at setpoint". Say this
before a judge does.

**Changed:** new `src/modal.py`, rewrote `src/advisor.py`, rewrote
`dashboard/app.py`, `src/segmentation/lumenstone.py` (colours + shared
`preprocess` so demo inference cannot drift from eval inference),
`requirements.txt` (scipy), `reports/KHANYA-01-research-phase.md` (section 7
rewritten).
**Blocked on:** nothing new. S2 baseline training still running (12 epochs, CPU,
~2h); epoch 1 val mIoU 0.09 with all minerals at 0.0, which is normal for a
fresh head but needs watching - if minerals are still at 0.0 by epoch 4 the LR
(1e-3) is too high for a 5-class fine-tune and should come down to ~2e-4.
**Next:** all advisor numbers so far come from GROUND-TRUTH masks, which proves
the measurement logic, not the end-to-end system. Once training finishes, the
same 12 sections need re-running on PREDICTED masks - the gap between those two
liberation numbers is the honest measure of how much segmentation error costs at
the decision layer, and that comparison is a strong slide.

---

## 2026-08-14 — Sibusiso (6)

**Did:** Two things, both significant. (1) **We're in** - acceptance letter
received, we're selected for the hackathon. Read it and put the real dates in
README.md; the ones we had were wrong in shape. 1 Oct is a working day on site
with a **13:00 hard submission cutoff** and a **10-minute** pitch at 14:00, not
a presentation day. A **one-page abstract is due 30 Aug** (approach, methods,
expected outcomes) along with per-member admin: ID number, T-shirt size, contact
details, and either your mentor's details or an explicit request for a Mintek
mentor. 2 Oct conference attendance is compulsory; five finalists announced
there, then originality authentication. Prizes R25k/R15k/R10k, possible vacation
work at Mintek. (2) **LumenStone is back up** - the HTTP 500 has cleared, all
subsets download straight off Yandex Disk, no registration, usage agreement
allows research use with citation. There are now **v2** releases we didn't know
about. The important part: **S2 is a Norilsk Group layered-ultramafic magmatic
sulphide assemblage** - pyrrhotite, pentlandite, chalcopyrite, magnetite. That's
the same BMS assemblage that carries the PGM payload in UG2/Merensky, and the
same intrusion type. It's a real geological analogue for our BMS class, 5
classes with pixel masks and an author-defined split, so it clears the brief's
>=3 phase floor with a legitimate held-out number. Full reasoning in
DATA-SOURCES.md Section 1.
(3) **Downloaded S2 v2 and built the multi-class pipeline.** 418.7 MB, extracted
to `data/raw/lumenstone/S2_v2/` (gitignored - re-download from DATA-SOURCES.md
Section 1). Verified contents against petroscope's codebook: 37 train / 12 test,
author-defined split, five classes - background, chalcopyrite, magnetite,
pyrrhotite, pentlandite. Masks are RGB with the label in all three channels, and
the class codes are non-contiguous (0,1,3,5,7) because they index petroscope's
global 50-class codebook shared with S1/S3 - they need remapping to 0-4 for
CrossEntropyLoss, which `lumenstone.py` does at tensor-build time while keeping
the original codes so petroscope stays drop-in compatible. Wrote
`src/segmentation/lumenstone.py` and `train_lumenstone.py` as **separate**
modules rather than folding S2 into `data.py`/`train.py`, so the FeM 0.872 result
already quoted in the report stays reproducible with zero regression risk.
Carved a 6-image val set out of train; **test/ untouched.** 12-epoch baseline
training running now on CPU (~8-9 min/epoch, ~1.7h).

**Changed:** `README.md` (status + real dates + plan to 1 Oct), `DATA-SOURCES.md`
(Sections 0 and 1 rewritten + verified S2 contents), `reports/KHANYA-01-research-phase.md`
(Section 9), new `src/segmentation/lumenstone.py`, new
`src/segmentation/train_lumenstone.py`, `.gitignore`.
**Blocked on:** still no data for chromite/orthopyroxene/plagioclase/
talc-serpentine - S2 covers the BMS payload phase only. R6,000 rig call still
open and now urgent: it needs answering before the 30 Aug abstract, not after.

**Read before quoting any S2 number:** Norilsk is massive sulphide - BMS is 62.8%
of S2 pixels, against <1 vol% in UG2. S2 is an analogue for the assemblage and
its optical appearance, not its abundance. Magnetite at 1.8% is the in-dataset
rare-class test; report per-class IoU, never mean IoU alone. Full caveat in
DATA-SOURCES.md Section 1.
**Next:** Lethabo - three things, all time-boxed by 30 Aug: (a) your ID number,
T-shirt size, contact details, and whether we're requesting a Mintek mentor
(I'd say yes, and ask about polished-section imagery in the same message);
(b) the rig decision; (c) your call on whether the abstract keeps the full
five-phase REEFPRINT scope or re-scopes to what we can actually evidence by
1 October. Read DATA-SOURCES.md Section 1 before answering (c).

---

## 2026-08-10 — Sibusiso (5)

**Did:** Checked in - you'd accepted the GitHub invite but hadn't pushed
anything yet, so the two open asks below (Bushveld-phase data lead, R6,000 rig
decision) are still unanswered. Used this session to keep chasing the data
blocker: found and ruled out LITHOS-DATASET (Kaggle, NeurIPS 2025 paper,
211k patches / 25 classes) - genuinely large, but it's a sedimentary/carbonate
petrography dataset (foraminifer, coral, dolomite etc.), wrong rock type for
Bushveld ultramafic-mafic ores. Only nominal overlap on Plagioclase/Pyroxene,
no chromite/BMS/talc. Full class list and reasoning in DATA-SOURCES.md so this
isn't re-discovered later.
**Changed:** `DATA-SOURCES.md` (LITHOS ruled-out entry).
**Blocked on:** still no public dataset for chromite/orthopyroxene/plagioclase/
BMS/talc-serpentine. Still need the R6,000 rig call.
**Next:** Lethabo - when you're on this, `git pull` and check this file plus
`DATA-SOURCES.md` before starting anything. If you or a contact has any lead
on Bushveld/UG2/Merensky/Platreef thin-section or QEMSCAN imagery, that's the
single thing that unblocks the most work right now.

---

## 2026-08-04 — Sibusiso (4) — end of day

**Did:** Got a real, honest segmentation result. DeepLabv3+ResNet50 on FeM
(ore/resin, reflected-light microscopy), 10 epochs CPU, image-level split
(81 distinct sections, no rotation duplicates so this split is legitimate,
unlike MUMDMC). Held-out TEST SET (12 images the model never saw): **mean IoU
0.872, pixel accuracy 93.75%**. This is a real, defensible number - comparable
to the published PSPNet+ResNet18 LumenStone benchmark (mIoU 0.88) despite far
less compute. Also fixed a real bug along the way: `build_model(pretrained=
False)` silently built a different architecture (no aux classifier head) than
training did, so the saved checkpoint failed to load - fixed by pinning
`aux_loss=True` always in `src/segmentation/model.py`.
**Changed:** `src/segmentation/config.py` (25->10 epochs), `src/segmentation/model.py`
(aux_loss fix), `reports/KHANYA-01-research-phase.md` (added section 5.0.1
with the real numbers).
**Blocked on:** same as entry (3) below - no public dataset yet for the
REEFPRINT phase set (chromite/orthopyroxene/plagioclase/BMS/talc), and the
R6,000 rig decision. The segmentation result above is ore-vs-resin (FeM), not
those five phases - good proof the pipeline works, not yet evidence on the
real target classes.
**Next:** Lethabo - same asks as below (Bushveld-phase data lead, rig
decision). When you're back on this: `git pull`, read this file top-down,
then `reports/KHANYA-01-research-phase.md` section 5 for the current data/
results picture before writing any new code.

---

## 2026-08-04 — Sibusiso (3)

**Did:** Read REEFPRINT (the abstract you submitted) and re-scoped the code's
target phase set to match it: chromite, orthopyroxene, plagioclase,
base-metal sulphide, talc/serpentine. `advisor.py` logic rewritten around
BMS-as-payload (report low-BMS explicitly rather than falling through, per
your Section 1 point about aggregate accuracy hiding the sub-1% class).
Kept MUMDMC as a labelled dev-proxy (its classes don't match REEFPRINT's -
see config.py comments) so the pipeline stays exercised while real data is
missing. Segmentation baseline on FeM (ore/resin, unrelated phase set) still
training in background, unaffected by this change.
**Changed:** `src/config.py`, `src/advisor.py`, `DATA-SOURCES.md`.
**Blocked on:** no public dataset found yet for the REEFPRINT phase set
(chromite/orthopyroxene/plagioclase/BMS/talc). This is now the real data
blocker, not MUMDMC's specimen scarcity. Also: REEFPRINT Section 3.13 specs a
~R6,000 self-funded rig - conflicts with our earlier "no money" decision,
needs a call between us.
**Next:** Lethabo - if you have a lead on Bushveld/UG2/chromitite thin-section
imagery (public or from your own contacts), that unblocks the real target.
Also need your read on the R6,000 rig: build it, scope it down, or cut it and
lean harder on the software/simulation deliverables (plant simulator, OPC UA
advisory channel, conformal calibration) which don't need hardware spend.

---

## 2026-08-04 — Sibusiso (2)

**Did:** Ran the classification baseline on the MUMDMC2025 sample (583 images,
8 specimens across 5 classes). 98.3% train accuracy, but NOT a real accuracy
result — confirmed the full 14,400-image dataset from the paper is not
publicly downloadable (only a 1-image teaser is linked to the paper's actual
DOI); what we have is the largest public version and it's too specimen-poor to
hold out a test set. Pipeline itself (data loader, specimen-grouped split,
training, checkpointing) verified working. Also attempted to move training into
a Lightning AI Studio (khanya-baseline) for visibility — hit a "no hardware
found" infra issue, unrelated to our code; parked for now, ran locally instead.
**Changed:** `src/config.py`, `src/data.py`, `src/train.py`,
`reports/KHANYA-01-research-phase.md` (added section 5.0).
**Blocked on:** need more specimens per class for MUMDMC's 5 minerals (biotite,
hornblende, plagioclase, K-feldspar, quartz), or a decision to de-scope the
classification accuracy claim and lean on segmentation/advisor work instead.
**Next:** Lethabo — if you find any other petrographic thin-section dataset
covering these 5 classes with more than 1-2 specimens each, that unblocks
everything. Otherwise let's decide together whether to keep chasing data or
pivot effort into the FeM segmentation stage and the advisor thresholds, where
evaluation is more tractable.

---

## 2026-08-04 — Sibusiso

**Did:** Scaffolded PyTorch project (specimen-level splits, ResNet18 baseline,
train/eval/advisor), surveyed datasets, invited Lethabo as collaborator, set up
a Lightning AI Studio (khanya-baseline, CPU, free tier) for training.
**Changed:** `src/`, `dashboard/`, `DATA-SOURCES.md`, `reports/KHANYA-01-research-phase.md`
**Blocked on:** MUMDMC2025 full dataset download (4.8GB, in progress locally).
LumenStone (better-fit dataset) inaccessible — host down, no outreach planned
per team decision to wait on official acceptance.
**Next:** Lethabo — accept the GitHub invite (check email/GitHub notifications).
Once accepted, pull `main` and read `DATA-SOURCES.md` + `reports/KHANYA-01-research-phase.md`
before touching code.
