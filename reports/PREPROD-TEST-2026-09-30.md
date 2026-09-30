# Pre-production test, end to end: 30 September 2026

**Build under test:** `khanya/speed` at `5254951` (the top of the #10-#13 stack).
**Machine:** the development laptop, CPU only. **Checkpoint:** sha256 `de7135a9…`.
**Method:** four layers. Static checks. A fresh clone from GitHub. A live run of
every mode through the browser, starting from a cold server. Hostile and
out-of-distribution uploads. Every number below was measured in this session. Nothing is carried over from earlier reports
unless it says so.

---

## Verdict in one paragraph

On the inputs it was built for, the system does what it says in every mode,
and its refusals of broken files are clean. It is **not pre-production ready**,
for three reasons found today. (1) It has **no check that the input is a
micrograph**: a screenshot of text was reported as 68% ore, 100% pentlandite,
with 193 particles, and that "association index" was **published over OPC UA and
acknowledged**. (2) **Full-section mode sends a real command with no lighting
check and no "unguarded" label**: the same section is held in live mode and
commanded 0 → 1 in full mode. (3) **It cannot be installed from the repository
alone**: dependencies are unpinned, Jinja2 is missing from `requirements.txt`,
the checkpoint has no distribution route, and the OPC UA code is loaded from a
REEFPRINT checkout outside the repo.

---

## Layer 1: static

| Check | Result |
|---|---|
| Test suite | **143 passed** |
| CI offline guard | pass; the only URL in the served assets is the Tailwind licence comment (not fetched) |
| `python -m src.preflight` | **READY TO PRESENT** |
| Secrets scan | clean |
| Tracked files under `checkpoints/`, `data/raw/`, `logs/`, `.claude/settings.local.json` | 0 |
| `requirements.txt` | **every entry unpinned** (`torch>=2.2`, `streamlit`, `numpy`, …). Installed here: torch 2.13.0, torchvision 0.28.0, streamlit 1.61.0, numpy 2.5.2, scipy 1.18.0, Pillow 12.3.0, asyncua 2.0.1, opencv-python 5.0.0.93 |
| Jinja2 | imported directly by `dashboard/render.py`, **not listed** (it arrives only as a Streamlit dependency) |

## Layer 2: fresh clone from GitHub

| Check | Result |
|---|---|
| Test suite, no data and no weights | **143 passed** |
| Preflight | **3 CHECK(S) FAILED - do not present from this machine** (checkpoint, data, model load); OPC UA passed |
| Dashboard | refuses cleanly: "The validated S2 model checkpoint is missing. Restore checkpoints/lumenstone_s2_patches/best.pt before analysing an image." |
| Obtaining the checkpoint | **no route documented**: nothing says where the 168 MB file comes from |

The OPC UA check passes in the clone only because `ensure_reefprint()` finds
`Desktop\REEFPRINT\src`, a checkout outside this repo. That checkout is a
**detached HEAD at `73806b2` (14 Sept)**, 14 commits behind `origin/reefprint`.
Its `src/reefprint/integrate/` code is identical to `origin/reefprint` today, so
nothing is wrong yet. But nothing pins it. On a laptop without that folder, the
plant half of the demo does not run.

## Layer 3: live, every mode, from a cold server

| Run | Result | Time |
|---|---|---|
| Server start to upload-ready page | model warmed before first upload | ≈23 s |
| Live, lighting check on, **test_01** | Continue at current setpoint · 52 payload particles · 6 fields, 18% · SIMULATED LIGHTING: STABLE · plant **UNCHANGED 0 → 0** | app reports **59.6 s** |
| Live, lighting check on, **test_11** | No recommendation (changes under simulated lighting shift) · 10 payload particles · UNSTABLE · plant **HELD 0 → 0** | app reports **59.8 s**; upload to rendered result ≈68 s wall |
| **Full section**, test_11 | **Grind finer · 21 payload particles · association 0% across 38 particles · plant APPLIED 0 → 1 · no lighting check** | ≈4 min 50 s wall; **no timing shown** |
| Evidence, test_01 | Section mean IoU 0.41 · model and expert both Continue · agrees · provenance line cites sha256 `de7135a96541…` | first open under ~17 s (includes a one-time hash of the checkpoint) |
| Evidence, test_11 | Section mean IoU 0.38 · model and expert both **Grind finer** · agrees · confidence 90.5% | cached |
| Browser network requests | **only `localhost:8501`** (plus the local test-file server this test used) | – |

The test_11 rows show the trade-off plainly. Its expert reference is **Grind
finer**. The live lighting check withheld that correct call, as
`LIGHTING-CHECK-2026-09-30.md` says it will four times in five. Full-section mode
issued it with no guard.

The live timings are **~60 s today against the 49 s recorded after the PR #13
speed-ups** (n=2 today, one machine; cause not investigated). The app says
"measured, this run: 59.8s end to end", but upload to rendered result took about
68 s: the label leaves out the upload and the render.

## Layer 4: hostile and out-of-distribution inputs (live mode)

| Input | What the system did | Correct? |
|---|---|---|
| Corrupt JPG | "The upload could not be decoded safely… No recommendation has been issued." 2.3 s | **Yes** |
| 300 × 300 PNG | "smaller than one 512x512 field; use the full-section path instead. No recommendation has been issued." 1.1 s | Refusal yes; **the advice sends the operator to the unguarded mode** |
| 300 × 300 PNG in full-section mode | Flag for manual review, association not measurable · 0 payload particles · HELD | **Yes** |
| test_11 as **RGBA PNG** | identical to the JPG: 10 payload particles, pyrrhotite 99.1%, association 1%, UNSTABLE, HELD | **Yes**: format-invariant |
| **Screenshot of text** (1350 × 746) | 2 fields, 52% · **68% "ore", 100.0% pentlandite, 193 particles**, association 48% · confidence 64% ("verify manually") · Marginal, HELD · **OPC UA: published model_confidence, association_index · consumer acknowledged and applied** · labelled "Reflected-light micrograph… Every number below is measured" | **No.** It held only because 48% fell inside the ±33.5% band |
| test_11 as **greyscale** | **pentlandite 97.5%, pyrrhotite 2.5%; association 66%** (colour version: pyrrhotite 99.1%, association 1%) · 36 payload particles · confidence 76% · Marginal, HELD · 31.4 s | **No.** Colour carries the phase identification; greyscale inverts it, unchecked. Held only by the band |

---

## Findings, ranked

| # | Severity | Finding | Where | Fix |
|---|---|---|---|---|
| 1 | **High** | No input-eligibility gate. Non-micrographs and greyscale images get measured, labelled as measurements, and published over OPC UA. | `dashboard/app.py` upload path; `src/advisor.py` | Refuse before any model pass or publish: (a) reject images whose channels are near-identical (greyscale); (b) reject images outside the train set's per-channel colour envelope, with the envelope computed on train/val, never test; (c) state the reason on screen. |
| 2 | **High** | Full-section mode issues commands with no lighting check and no UNGUARDED label. Log says "lighting check: n/a". | `app.py:394-426`, `_control_strip.html.jinja:48` | Either run the check in full mode, or make full mode advisory-only (no command) and label it UNGUARDED exactly like the switched-off live check. |
| 3 | Medium-high | Confidence never gates. It is a label (`advisor.py:145`, 0.85 split); a 64% result and a 91% result reach the same decision logic. | `src/advisor.py` | Choose a floor on train/val data and make it an abstention, not a caption. |
| 4 | Medium | Time claims are wrong or missing. "About three minutes" for a live recompute (`app.py:285, 300`) vs ≈4 min 50 s measured; full mode shows no time; "end to end" excludes ≈8 s of upload and render; live is ~60 s today vs 49 s recorded. | `app.py`, `khanya.html.jinja:189` | Time from upload receipt to render; show it in every mode; replace fixed claims with the measured value. |
| 5 | Medium | Not installable from the repo: unpinned requirements, Jinja2 missing, no checkpoint route, REEFPRINT loaded from an unpinned folder outside the repo. | `requirements.txt`, `src/polarimetry.py`, README | Pin exact versions from this working environment (`pip freeze`); add Jinja2; document the checkpoint's source and sha256; pin the REEFPRINT commit and have preflight check it. |
| 6 | Low | The too-small refusal recommends full-section mode, which is the unguarded path (finding 2). | `src/segmentation/patches.py` message | Change the advice once finding 2 is decided. |
| 7 | Low | "As imaged, this field says…" when six fields were analysed. | `src/stability.py:57` | "these fields". |
| 8 | Low | During a ~5-minute full-section run the previous result stays on screen, faded. | Streamlit default | Clear the result slot when a new run starts. |
| 9 | Known | Carried scientific limits, re-confirmed rather than re-measured today: lighting check discards 4 of 5 correct confident calls; six-field confident calls unsafe 8 of 13 on train/val; magnetite IoU 0; 3 of 4 thresholds unsourced; n = 12 test sections. | reports | Post-deadline. |

### Evidence for the finding-1 fix (added after the test)

`python -m src.input_eligibility_check` -> `reports/input_eligibility.json`.

**A saturation check alone would not work.** Greyscale test_11 has zero colour,
while real S2 images have 7.9-23.6. But the text screenshot's saturation
(21.8) lies inside the real range. What separates it is colour **balance**:
every S2 image is warm on average (red > green > blue), and the screenshot is
cool (red 23.6 below green).

**A min/max envelope fitted on train+val would also fail.** Held-out test
sections reach R-G = 2.41, below the train+val minimum of 4.82, so a fitted
envelope would have wrongly refused a real section.

**A sign-only rule has no fitted threshold:** some colour (mean channel
difference >= 1 level) and a warm cast (mean R-G > 0 and mean G-B > 0).

| Set | Eligible | After the lighting check's darkening |
|---|---:|---:|
| S2 train | 31/31 | 31/31 |
| S2 validation | 6/6 | 6/6 |
| S2 test (descriptive, not used to choose) | 12/12 | 12/12 |
| S1 v2, other ore, LumenStone set-up | 83/84 | 75/84 |
| S3 v1, other ore, LumenStone set-up | 35/35 | 26/35 |
| V1, re-imaged on another set-up | **10/30** | 1/30 |
| greyscale test_11 · text screenshot | **refused** · **refused** | – |

So the rule encodes the **imaging set-up, not the ore**. It refuses most of V1.
That is correct for a gate, since the S2 model was never validated on that
set-up. It also means **a new microscope or camera must be characterised before
the system will advise**, which has to be written into the pilot plan.

Not re-run today: the stale-command refusal and presenter reset (verified in
`BACKUP-DEMO-SCRIPT.md` beat 4 on 30 Sept); the wifi-off run on the presenting
laptop (still outstanding). The browser egress check covers only the requests
the pane buffered in this session. It is not a firewall-level test.

## Score: 57.5 / 100 as pre-production

Weighted; each category is marked down only by the findings above.

| Category | Weight | Score | Why |
|---|---:|---:|---|
| Correct on intended inputs | 15 | 9 | every expected result matched, including the expert reference on test_11 |
| Bad or unexpected inputs | 15 | 4 | broken files refused well; text and greyscale images measured and published (finding 1) |
| Safety guards applied consistently | 20 | 5 | live-mode guards work; full section skips one silently (2); confidence never blocks (3) |
| Speed | 10 | 5 | ~60 s live, ~4 min 50 s full section, 23 s cold start |
| Installable by someone else | 10 | 4 | finding 5 |
| Honesty of on-screen claims | 10 | 7 | evidence bound to the checkpoint hash; but the text screenshot was labelled "measured" and time claims are wrong |
| Security and offline | 5 | 9 | localhost only; wifi-off run on the presenting laptop still to do |
| Scientific validity | 15 | 5 | n=12; lighting check non-selective; magnetite 0; 3 of 4 thresholds unsourced |

Fixing findings 1-5 would take it to about 72 (an estimate, not a
measurement). The scientific-validity row does not move without more data.

## What passed that matters

- Every intended input gave the expected result in every mode, and both
  full-section and Evidence agree with the expert reference on test_11.
- Broken inputs (corrupt, too small) are refused before any command, with a
  reason.
- File format does not change the answer (RGBA PNG = JPG).
- The preflight catches a machine that cannot present, and the dashboard
  refuses rather than guessing.
- The simulated plant never moved on an abstention in any run today.
- OPC UA uses an ephemeral localhost port per transaction, so concurrent
  sessions do not collide.
- Nothing left the machine from the browser.

---

## Re-test after the fixes (PR #17), 30 September, evening

Same four layers, same inputs, same rubric, on `khanya/preprod-fixes`
(`4b526c7`). The score below is a re-score by the side that made the fixes; the
judge review of PR #17 is the real test.

| Check | Morning | After the fixes |
|---|---|---|
| Test suite | 143 passed | **158 passed** (repo, fresh clone, and Linux CI installing `requirements-lock.txt` on Python 3.13) |
| Preflight | 4 checks | **7 checks**: adds REEFPRINT pin (content fingerprint of reefprint `29254718`), telemetry off, a timed live pass (**21.4 s** per six-field pass here) |
| Fresh clone | refused, no route to the checkpoint | refused, pointing to README "Setting up a presenting laptop" (source, sha256, size, why unpublished) |
| Cold start | ≈23 s | ≈25 s |
| Live test_11 | held (lighting check); 59.8 s app / ≈68 s wall | **Grind finer, plant 0 → 1**; 38.6 s server side / 41.5 s wall. Expert: Grind finer |
| Live test_01 | Continue, unchanged | **withheld: confidence 77% < 85%**, held; 32.1 s |
| Live test_04 | (not re-run) | withheld, 4 particles < floor 9, held; 31.5 s |
| Lighting diagnostic ON, test_11 | (default) | UNSTABLE, held; 58.2 s; wording "these fields" |
| Full section test_11 | Grind finer, **APPLIED 0 → 1, no label, no time** | Grind finer, **ADVISORY ONLY · NO LIGHTING CHECK, HELD**, **210.3 s shown** |
| Evidence test_01 | Continue, agrees | same, plus "advisor rules only · at 78% confidence the live pipeline withholds it" |
| Screenshot of text | measured (68% ore, 193 particles), **published over OPC UA** | **refused in 1.0 s** before any model pass: colour balance -23.6 / -7.3 |
| Greyscale test_11 | phases inverted, held by luck | **refused in 2.1 s**: no colour |
| Corrupt / 300 px | refused | refused; the small-image message no longer points at the unguarded path |
| Stale command | (verified 30 Sept) | re-verified: REFUSED, setting stays 0 |
| Previous result during a new run | stayed on screen, faded | cleared at run start |
| Network | localhost only | localhost only |

Where a live result's time goes (`test_11`, measured outside the browser):
- model **24.7 s**, of which progress frames 2.1 s;
- **OPC UA 10.2 s**: publish 5.9 s and command 4.3 s, each starting its own local server;
- modal analysis 2.3 s;
- decode and eligibility 1.4 s;
- render 0.7 s.

Merging the two OPC UA exchanges into one server session is the largest speed
item left. It was not done the night before the demo.

### Score after the fixes: 79 / 100

| Category | Weight | Morning | Now | Why |
|---|---:|---:|---:|---|
| Correct on intended inputs | 15 | 9 | 9 | every result matches the expert; test_01's correct Continue is now withheld (conservative, not wrong) |
| Bad or unexpected inputs | 15 | 4 | **8** | every hostile input refused in 1-2 s before any model pass, publish or command. Limit: a colour-cast rule; a warm-toned non-micrograph would pass |
| Safety guards applied consistently | 20 | 5 | **8** | full section advisory only and labelled. The confidence gate withholds 8 of 8 unsafe train/val calls and 0 of 10 darkened ones pass. Stale refusal still works. Limit: gate evidence is 13 calls, mostly on training sections |
| Speed | 10 | 5 | **7** | live 31.5-38.6 s (was ~60); full section 210 s (was ~290); OPC UA still 10 s of it |
| Installable by someone else | 10 | 4 | **8** | lock file installs and passes on Linux CI; checkpoint route documented; REEFPRINT pinned by content. Limit: the checkpoint still needs a person (licence), transitive deps float |
| Honesty of on-screen claims | 10 | 7 | **9** | no hostile input reaches "measured"; every mode shows a labelled server-side time within ~3 s of the wall clock; full section and Evidence say what the gate does |
| Security and offline | 5 | 9 | 9 | offline test now covers every served file; the wifi-off run on the presenting laptop is still the team's to do |
| Scientific validity | 15 | 5 | **6** | new train/val evidence (confidence gate, darkened copies, eligibility with no fitted threshold) and a measured band undercoverage (75.7% vs nominal 85%). Still n = 12 test sections, magnetite 0, 3 of 4 thresholds unsourced, band not recalibrated |
| **Total** | | **57.5** | **79.0** | |

Not fixed, and why:
- **Scientific limits.** n = 12, magnetite 0 and the unsourced thresholds need
  data or literature.
- **The OPC UA merge.** Transport risk the night before the demo.
- **The wifi-off run.** It needs the presenting laptop.
