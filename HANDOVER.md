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
