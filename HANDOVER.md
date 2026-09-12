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
