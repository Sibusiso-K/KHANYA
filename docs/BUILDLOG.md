# BUILDLOG — what was tried, what worked, what did not

**Append-only.** Newest entry at the top. Never rewrite history here; if an entry turns out to be
wrong, add a new entry saying so and link back. This file and the commit log are the same story
told twice — the commit log says *what changed*, this says *why, and what we learned by getting
it wrong first*.

Rule 8 of the constitution: *commit early, commit often, including failures.* Finalists face
originality authentication after 2 October. A build log with no failures in it is not a record,
it is a press release.

**What goes in an entry**

| Field | Rule |
|---|---|
| Date + commit | absolute date, short SHA |
| Attempted | what we set out to do |
| Worked | with the evidence — a number, a test name, a command output |
| Did not work | the actual failure text where possible, not a paraphrase |
| Learned | only if it generalises. Otherwise leave it out. |
| Left open | anything that became a `docs/00-STATUS.md` finding or a red test |

---

## 2026-08-24 — session 15 · leg (b)'s missing half: a sanctioned path onto the extinction estimator

### Attempted

Merged three unmerged branches a concurrent session had left in the working tree (conformal
coverage's Beta-vs-binomial fix, the week-1 figure's geometry refusal — both described below),
then picked up CONTEXT.md's own stated single next action for week-1 leg (b): the fourth-harmonic
extinction estimator (`reefprint.polarim.extinction`) was built and tested, but nothing routed a
labelled section onto it the way `reefprint.bridge.measure_section` routes one onto the Stokes
inversion. `measure_section` calls `series.require_analyser_rotation()` unconditionally and
refuses a stage series (N3's guard); there was no mirror-image guard refusing an *analyser*
series fed to the extinction fit, which would silently discard its second-harmonic content the
same way a stage series silently zeroes out under the Stokes fit.

### Worked

- **`reefprint.bridge.extinction.measure_section_extinction`**, TDD'd against
  `crossed_polars_stage_series` (the stage phantom already built for N3), 9 new tests in
  `tests/test_bridge_extinction.py`: geometry refusal in both directions (an analyser series is
  refused with `require_specimen_rotation()`, same as an unknown-geometry series), shape
  mismatches and thin-angle counts skipped rather than raised (mirroring `measure_section`'s
  asymmetry between per-section defects and a wrong-geometry archive-wide one), the mineralogical
  payoff — pentlandite reads extinction depth exactly `0.0` while pyrrhotite extincts, recovered
  through the *other* geometry's own physics from the same phantom — and a `crossing_ratio`
  self-test carried per mineral, the extinction path's equivalent of the Stokes path's noise
  floor.
- **The module docstring is load-bearing, not decoration.** `extinction.py`'s own docstring
  already warns that raw extinction depth is not contrast-normalised — crossed polars block the
  unpolarised pedestal, so there is no `S0` to divide out, and comparing raw depth between two
  minerals compares their bireflectance *and* brightness at once, "finding N2 in a new costume".
  `bridge/extinction.py` restates that warning at the point someone will actually call this, and
  the returned `MineralExtinctionStatistic` is deliberately **not** shaped like `MineralStatistic`
  — no `s0_median` field exists to invite a normalisation nobody has the data to do honestly.
  The one claim it is licensed to make — a mineral is exactly dark vs extincts at all — needs no
  such normalisation, because zero is zero regardless of brightness.
- Wired into `reefprint.bridge`'s public exports, package docstring updated to describe both
  guards as one mirrored pair rather than describing only the older one.
- Two branches from a concurrent session, merged onto `main` after independent verification
  rather than trusted on the commit message:
  - **F3: conformal coverage is Beta, not binomial** (`bd4d4a8`, `ed34b10`). Coverage of a
    split-conformal calibration set of size `n` at miscoverage `alpha` is `Beta(n+1-l, l)`,
    `l = floor((n+1)*alpha)` — not the binomial Wald SE `sqrt(0.9*0.1/n)` the finding had used.
    Recomputed myself before merging: `n=100` gives 2.96pp exact vs 3.00pp Wald, `n=20` gives
    6.26pp vs 6.71pp — Wald is *larger*, meaning the original finding had the error's direction
    backwards (a second commit on the same branch caught and corrected its own first commit's
    "buys less precision than it promises," which should have read "overstates the spread").
    `tests/test_docs_conformal_figures.py` pins the corrected figures and was confirmed RED
    against the old ones first.
  - **viz: the week-1 gate figure refuses a geometry it cannot support** (`33bbced`).
    `anisotropy_figure()` never consulted `series.geometry` and hardcoded panel 3's x-axis label
    as "analyser angle (degrees)" regardless of what actually rotated — a silent wrong answer on
    the one figure the week-1 gate is argued from. Now the label follows `series.geometry` and a
    `SPECIMEN` or `UNKNOWN` series draws a visible refusal on the figure rather than a blank
    panel (Rule 5's pattern: still renders, cannot be mistaken for a valid result). This branch
    independently found and flagged the exact same abstract overclaim fixed in session 14
    (`6b32ef2`) — two separate audits landing on the same finding from different files is
    corroboration, not coincidence.
  - Both merged with `--no-ff` after reading the full commit bodies and re-deriving the key
    numbers rather than taking them on faith. `test_docs_counts_are_current.py` (added by the
    conformal branch) caught the resulting staleness in CONTEXT.md's pinned test count
    immediately after each merge — 253→256 after the first, 265→274 after this session's own
    addition — which is exactly the failure mode that test exists to catch.

### Did not work / friction

- **A concurrent session was creating and checking out branches in this same working tree** while
  this session was also committing. A commit made mid-session landed on whatever branch happened
  to be checked out (`fix-run-geometry`) instead of `main`, and had to be fast-forwarded after
  the fact. `git branch --show-current` before committing, from now on, in a tree anyone else
  might be touching concurrently.

### Learned

The repo layout comment in `CLAUDE.md` already says `bridge/` is "the only sanctioned route" from
masks plus frames to a per-mineral number — singular, at the time it was written, because only
the analyser geometry had a route. Building a second sanctioned route for the second geometry,
with its own mirrored guard, is not adding a feature so much as finishing the sentence: the
project's own physics table names two geometries, and only one had a path all the way through the
seam. The guard that stops the *wrong* geometry from being routed around is worth as much on the
new path as N3's original guard was on the old one — which is why it was built alongside the
estimator rather than after something used it wrong, the same reasoning `require_specimen_rotation`
itself gives for existing at all.

### Left open

- **The real archive still is not on this machine.** Everything above is proven against the
  synthetic stage phantom. The moment `S3_v2.zip` is available, leg (b) needs: confirm each
  section's geometry from the frames first (do not assume SPECIMEN from N3's aggregate lean —
  measure it per section, the same discipline N3 itself insists on), then call
  `measure_section_extinction` the way `measure_section` is called today.
- **No script yet drives `measure_section_extinction` over a real archive** the way
  `experiments/002-s3v2-geometry/run.py` drives the geometry discriminator. Writing one now
  would be guessing at the archive's exact directory layout beyond what `run.py` already
  reverse-engineered; better to reuse `run.py`'s section-reading code once the geometry is
  confirmed, than to duplicate it against untested assumptions.

## 2026-08-23 — session 14 · the abstract, and the domain lead's surname was wrong

### Attempted

Write the Mintek SCi Grad Hackathon abstract (**due 30 August 2026, one page**) and render it to
PDF. The letter names three required elements — proposed approach, methods or technologies,
expected outcomes or impact — and states that submissions undergo plagiarism, AI-generation, IP
and originality checks, and that external sources, data and contributions must be acknowledged.

### Worked

- **`docs/06-abstract.md`** — source of truth for the wording, 662 words of body text, plus
  working notes that are explicitly *not* part of the submitted page. The notes carry a
  **provenance table for every number on the page** (claim → source → Rule-1 rank), which is the
  thing that makes the page defensible under originality authentication rather than merely
  well-written.
- **Every number on the page is bounded in the sentence that carries it.** 40.4× is labelled "a
  phantom result, not an ore result"; the factor-of-126 split leak is labelled "on synthetic
  data"; the R5 000 rig is "costed as a design; no hardware is built, and no claim here depends on
  one" (ADR-0002). The 0.2–1.6 µm/pixel figure is **deliberately absent** — it is a design target
  spanning a factor of eight, and an abstract is exactly where such a number gets read as a spec.
- **The negative result is on the page, not hidden.** The N3 `NEITHER` verdict on LumenStone S3 v2
  (29 sections, 116 000 pixels) is stated, along with the decision to route to the fourth-harmonic
  estimator rather than force the convenient inversion. Rule 9's reasoning generalises past the
  falsification test: a team that has run something real has negative results to report, and a
  team that has run nothing does not.
- **Prior art is cited by name.** Pirard, Lebichot & Krier (2007) is real prior art on
  polarised-light *imaging* in ore microscopy. Pre-empting a judge who knows it costs one clause;
  being corrected on stage costs the claim.
- **`docs/06-abstract.html` + headless Chrome → `docs/06-abstract.pdf`, one page, verified.**
  Chrome is a tool we run, not a library we link, so **no SBOM or `05-toolchain.md` entry** — the
  same treatment `docs/05-toolchain.md` already gives git. Page count is checked mechanically:
  `grep -a -o "/Count [0-9]*" docs/06-abstract.pdf` must print `/Count 1`.

### Did not work

- **First render was two pages**, overflowing by 5.2 mm — about one line. Fixed by trimming size
  and paragraph gaps, *not* by cutting evidence and not by squeezing leading first (that is what
  makes a dense page look cramped).
- **Two typographic defects the page count would never have caught**, both found by rendering the
  PDF and *looking* at it rather than trusting that it compiled: `~R5 000` broke across a line
  boundary as `~R5` / `000`, and the author byline wrapped mid-affiliation (`BSc Electrical
  Engineering,` / `University of the Witwatersrand`). Fixed with `&nbsp;` on the numeral and by
  making each author a block unit. Both are the class of detail that separates a submitted
  document from a draft.
- **Measuring overflow in the browser beat guessing at the trim.** No PDF library is installed
  (`pypdf`, `pikepdf`, `fitz` all absent) and adding one to count pages would have been an SBOM
  entry bought for nothing. The screen CSS mirrors the print geometry exactly, so measuring the
  content box in the same engine that paginates gives the overflow in millimetres directly.

### Learned

**The domain lead's surname in the constitution was wrong, and it was inferred, not told.**
`CLAUDE.md` recorded **Lethabo Mphukuile**, taken from the git commit identity, with a note to
correct it if wrong. It is **Lethabo Hoaeane**, confirmed by Lethabo on 2026-08-22. It had already
propagated to `CONTEXT.md` and to the decider line of **all three ADRs** — the documents whose
whole purpose is to record who decided what. Corrected in those four files; **the earlier
entry in this log at "ADR-0001's decider filled in" is left standing, wrong, because this file is
append-only** — this paragraph is the correction it links to.

The generalisable part: a git commit identity is a *convenience string a person typed once*, not
a record of their name, and inferring an identity from one and then writing it into governance
documents is a Rule-1 violation wearing different clothes — a number you did not measure and a
name you were not told are the same mistake. It survived thirteen sessions because it was
plausible and nobody was asked.

Related: the abstract header had **"Team Sonar, University of the Witwatersrand"**, inherited from
`CLAUDE.md`. The team is three people across **three** institutions — Unisa, Wits and TUT. Also
corrected in `CLAUDE.md`. Institutions are written out in full on the submitted page;
abbreviations read as internal shorthand.

### Also this session · the mentor request

**We have no mentor.** Item 5 of the Mintek letter: *"If you require a mentor from Mintek, please
indicate this clearly so that we can assist with the appropriate support."*
`docs/07-mentor-request.md` → `.html` → `.pdf`, one page, same Chrome pipeline and same
typography as the abstract so the two attachments read as one set from one team.

The letter's substance is **an ordered list of the expertise we need**, not the request itself.
"Appropriate support" is a *matching* problem — Mintek cannot assign the right person without
knowing what is wanted, and a bare "we need a mentor please" spends the opportunity to get a good
match. The list is ordered, and says which single area matters most rather than asking for
everything.

Two things the letter does deliberately:

- **Names the gap plainly** — "None of us is a practising mineralogist, and several of our
  load-bearing claims are mineralogical." This is CLAUDE.md **blind spot 8** turned into an
  action: *no load-bearing mineralogical claim rests on the domain lead alone; book external calls
  instead.* A mentor request is the cheapest external check available to us, and naming the gap is
  precisely what makes the request matchable. The domain lead's prior metallurgical-engineering
  background is **not** claimed — still Lethabo's call, and the sentence is true without it.
- **Rules out the obvious objection before it is raised** — "We are not requesting data, samples
  or laboratory access." True (hard constraint: public sources only), and it removes the most
  likely reason to hesitate.

First draft ran **46.8 mm** over one page. Cut by tightening prose and folding "any one of these
would be valuable" into the list introduction — *not* by dropping the expertise list, which is the
only part Mintek cannot act without. A request for someone's scarce time that runs to two pages is
arguing against itself.

### Also this session · the submission packet, and a claim that was not true

Team details supplied, so the packet was completed: team-details PDF, the email body, and the
two documents above, all with **no placeholders**.

- **Three things that were wrong or unsafe, found by finishing rather than by looking for them:**
  1. **The abstract claimed "a continuous *public* commit history."** The KHANYA repo is
     **private**. That is a false statement on a document that goes through originality checks —
     worse than the placeholder we were fixing at the time. Now reads "a continuous, timestamped
     commit history," which is true today, stays true if the repo is opened later, and is the
     claim originality authentication actually cares about. Keeping the repo private until after
     1 October is also the right call competitively, so the wording should not be reverted.
  2. **SA ID numbers must not enter git.** `submission/` is gitignored and holds all three
     members' ID numbers and mobile numbers. The repo is private *today*; git history outlives a
     visibility setting, and the originality defence may yet require opening it. Deleting a file
     later does not remove it from history.
  3. **The ID numbers were checked, not trusted.** All three pass the Luhn check digit, are
     13 digits, carry citizenship digit `0`, and decode to valid dates of birth. Cheap, and a
     transposed digit would otherwise have reached Mintek. Rule 1's habit applied to someone
     else's data: verify before it leaves the building.
- **The team-details document is a document, not a paragraph in an email.** The letter asks for
  five fields per member; a table renders them in a form Mintek can file, and the same details are
  also inline in the email body so nothing depends on an attachment being opened.

### Also this session · the abstract asserted a geometry its own code refuses to name

Picked up from an unmerged branch (`fix-abstract-neither`, `d0ebaff`) produced by a concurrent
session's assumption-auditor, verified against the source, and applied.

**The claim that was wrong.** The submitted page said the S3 v2 result was "evidence that the
published 'rotation sequences' are stage rotations, not analyser rotations." It is not.
`HarmonicVerdict.NEITHER` means *no modulation above the noise floor*, and
`src/reefprint/polarim/geometry.py:99` maps it to `RotationGeometry.UNKNOWN` on purpose, with the
reason in the docstring: *"'I cannot tell' and 'it is the convenient one' must not be the same
value. Rule 1."* Only `SECOND` and `FOURTH` name a geometry.

So the abstract performed, on public data, exactly the substitution the discriminator exists to
refuse — on the same page that advertises **"acquisition geometry is measured, not assumed"**. A
judge who reads the code finds the page contradicting the build's most distinctive decision. It
now reads: *"the geometry of the published 'rotation sequences' is not established by this
archive, and the Stokes inversion is not licensed to run on it."* Weaker, supported, and
rhetorically no worse — "we checked, the data would not tell us, and we declined to assume" is
the same negative-result story, minus the falsifiable overclaim.

**Learned, and it generalises past this sentence.** The overclaim did not come from carelessness;
it came from `CLAUDE.md` §The physics, which says these archives are *"almost certainly stage
rotations."* That is a reasonable **prior from domain knowledge**. The abstract attributed it to
the **discriminator run**. Laundering a prior into a measurement by attribution is Rule 1's
failure mode with better manners — no number was invented, only its provenance was upgraded.
The provenance table now carries the reasoning so the next person to tighten this paragraph finds
out why the wording is careful first.

**Not changed:** `CONTEXT.md` §3 argues `NEITHER` leans stage on SNR grounds (extinction depth
scales as bireflectance *squared*, so a symmetric null is asymmetric evidence). That argument is
far more defensible than the abstract's flat assertion was, and it is a methodology call for
Lethabo and Sibusiso, not a drafting fix. Flagged, left alone.

**Repo hygiene note.** A concurrent session is creating and checking out branches in this working
tree (`swarm-test`, `fix-abstract-neither`, `fix-conformal-distribution`, `fix-run-geometry`).
This session's commits landed on whichever branch happened to be checked out and had to be
fast-forwarded onto `main` before pushing. Check `git branch --show-current` before committing
here.

### Left open

- **Whether Lethabo's credential line should carry "prior metallurgical engineering."** It is
  real, recorded in `CLAUDE.md`, and on a metallurgy submission it is the most relevant credential
  on the page — but a credential line on a submitted document should say exactly what the person
  claims, so it is not a drafting decision. Lethabo's call.
- **"Team Sonar" is unconfirmed** as the registered team name.
- **Mentor: requested, not yet supplied.** `docs/07-mentor-request.md` is drafted and rendered.
  **It carries one placeholder — a mobile number — and must not be sent with it in.** The email
  address on it (`lethabomphukuile14@gmail.com`) carries the *old, wrong* surname; ordinary enough
  that no reviewer will care, but it sits two lines below the correct name, so use a matching
  address if one exists.
- **Per-member admin** — ID number, T-shirt size, contact details. Conference registration for
  2 October is required of all selected teams.
- **Voice pass.** The letter runs AI-generation checks. The ideas and every number are the team's
  own and the commit history evidences that, but the prose should be read aloud and adjusted by
  whoever presents, so the abstract and the ten-minute talk sound like the same people.

---

## 2026-08-21 — session 13 · the week-2 gate gets a statistical core

### Attempted

Build the falsification test's statistics (Rule 9's H0: after controlling for Cr2O3 and pyroxene
fraction, texture carries no additional predictive signal), TDD, against synthetic data with a
known ground truth — no real Bushveld geochemistry is in hand yet.

### Worked

- **`reefprint.heads.falsification.evaluate_texture_uplift`**: OLS on a baseline model (Cr2O3 +
  pyroxene fraction) and a full model (+ texture), Wald test on the texture coefficients using a
  cluster-robust CR1 covariance (Cameron & Miller 2015, White 1980), clustered by locality — same
  reasoning as Rule 2's split-by-locality guard: observations sharing a locality share unmodeled
  geology, so a plain OLS standard error overstates confidence. F-scaled Wald statistic, small
  cluster finite correction `G/(G-1) * (n-1)/(n-k)`, p-value from `scipy.stats.f.sf`.
- **`MIN_LOCALITIES_FOR_INFERENCE = 5`** refuses (`ValueError`) below that cluster count, mirroring
  the project's other declared-threshold guards (`DETECTION_SNR` in `geometry.py`,
  `LocalitySplit`'s backstop) — Rule 4 as a bound: cluster-robust inference at a handful of
  clusters is not inference.
- **Rule 3 satisfied structurally**: the null model (Cr2O3 + pyroxene fraction, no texture) *is*
  the required trivial baseline, so `FalsificationResult.baseline_r2` is a required, always-present
  field, not bolted on.
- **Honest n reported explicitly**: `FalsificationResult.n_localities` vs `n_obs`, same pattern as
  `LocalitySplit.n_groups`.
- TDD: `tests/test_heads_falsification.py` written first (`ModuleNotFoundError` on the first run,
  the correct RED), then the module. 5 real tests green: a true zero texture effect is not
  rejected, a true nonzero one is, honest n is locality count not row count, too-few-localities
  refuses rather than printing a fake p-value, baseline/full R² both reported. Full suite: **249
  passed, 25 deselected** (placeholders). `ruff check` clean, `ruff format` clean after one
  reformat pass.

### Did not work

- First draft named the public function `test_texture_uplift` — pytest's `test_*` collection
  pattern picked up the *imported* function itself as a phantom test item in
  `tests/test_heads_falsification.py`'s namespace, which then errored trying to satisfy its
  parameters (`target`, `baseline_features`, ...) as fixtures:
  `tests/test_heads_falsification.py::test_texture_uplift ERROR ... fixture 'target' not found`.
  Fixed by renaming to `evaluate_texture_uplift` in both the module and the test file. Generalises:
  never name a public function under test with a `test_` prefix if the test file imports it by
  name — pytest's collector does not distinguish "imported" from "defined here."

### Learned

Rule 3's "trivial baseline" and the falsification test's H0 null model are the same object here —
worth naming, because it means Rule 3 needed no separate mechanism for this head, just an honest
field.

### Left open

- The week-2 gate is not closed: `tests/test_heads_falsification.py::test_the_falsification_test_has_been_run_on_real_bushveld_data`
  is a placeholder — no public dataset combining assay Cr2O3, pyroxene fraction, a texture
  feature, and locality labels has been identified, and the CGS National Core Library phone call
  (§8 open item) is still not made.
- Not routed through Sbu — this piece is self-contained synthetic-data scaffolding, touches
  nothing of his prior work, and needs no data or machine he has. No PR comment sent for it.

---

## 2026-08-21 — session 11 · N3 measured, twice, and the answer is `NEITHER`

### Attempted

Merge Sibusiso's fix for `experiments/002-s3v2-geometry/run.py` (PR #3,
`fix/pool-signatures-not-raw-frames` on the KHANYA repo) and record the real N3 result it
produced against the actual `S3_v2.zip` archive.

### Worked

- **The pooling bug and its fix, verified before merge.** The original `run.py` concatenated raw
  `(n_angles, n_pixels)` arrays across sections via `np.concatenate`, which requires every
  section to share `n_angles`. The real archive's usable sections range 24–72 frames, so it
  crashed on real data (never hit by the phantom, which is why leg (a) passing didn't catch it).
  Fix: call `harmonic_signature()` once per section at that section's native frame count — it
  already reduces the frame axis to two per-pixel arrays before pooling is needed — then
  concatenate the resulting per-pixel `amplitude_2/floor_2`, `amplitude_4/floor_4` arrays across
  sections and rerun the same selection-and-median rule `harmonic_signature()` uses internally
  (top `MODULATING_FRACTION` pixels by `max(amplitude_2, amplitude_4)`, median SNR over that
  selection). Traced against `src/reefprint/polarim/geometry.py` directly to confirm the pooling
  logic reuses the identical constants (`DETECTION_SNR`, `MODULATING_FRACTION`) and the identical
  `argpartition` selection, not an approximation of it. Tested in an isolated `git worktree`:
  ruff clean, 239/239 tests green. Merged as PR #3 (`gh pr merge 3 --merge`), local `main`
  fast-forwarded `c1e4b83` → `e3a7632`. Confirmed post-merge: 243/243 tests, ruff clean.
- **N3, measured on the real archive, twice, identically.** 29 of 47 sections have real rotation
  data (the other ~18 are single static images — genuinely no acquisition, checked directly, not
  a filename-parsing artefact). 116,000 pixels pooled. 2nd-harmonic SNR 2.5×, 4th-harmonic SNR
  1.1×, `DETECTION_SNR` threshold 5.0×. **Verdict: `NEITHER` clears detection.**
- **`NEITHER` is not neutral.** Extinction depth (stage, 4φ) scales as bireflectance-squared;
  analyser modulation (2θ) scales as bireflectance directly, on a bright S0 — a real signal
  advantage that grows as `2/a` (CLAUDE.md, "the physics"). A null on both harmonics is more
  consistent with a stage rotation buried in noise than an analyser rotation buried in noise,
  because the analyser signal has to be weaker still, relative to its own floor, to vanish the
  same way. Combined with experiment 002's separately measured 38× noise-tolerance gap between
  the two geometries, this leans the open finding toward stage, without closing it.

### Did not work

`uv sync` / `uv python install 3.12` failed reproducibly on Sibusiso's Windows machine
("Missing expected target directory for Python minor version link"), even after a clean cache
retry. Worked around with KHANYA's existing 3.13 venv via `PYTHONPATH`, after confirming
`geometry.py` has no 3.12-only syntax via `ast.parse`. Not yet reproduced here — flagged in case
it recurs; not yet written up in `docs/05-toolchain.md`.

### Learned

A symmetric non-detection (`NEITHER`) on a two-geometry discrimination is not symmetric evidence
when the two geometries' signals scale differently with the same physical quantity — the
asymmetry in *how* each signal degrades is itself informative, and should be stated explicitly
rather than reported as "inconclusive."

### Left open

N3 stays open (not `SECOND`, not cleanly `FOURTH`). Next action: route week-1 leg (b) through
`reefprint.polarim.extinction` (already built and tested) rather than forcing the Stokes
inversion on this archive; re-point KHANYA's ten-mineral symmetry test the same way. See
`CONTEXT.md` §3 and §8 for the full reasoning and the ordered list of what would actually resolve
N3 further. `docs/05-toolchain.md` still needs the `uv`-on-Windows note.

---

## 2026-08-21 — session 12 · a targeted re-run, not a new dataset

### Attempted

Give N3's `NEITHER` verdict a sharper test, per the strategy written into session 11's entry:
if an analyser signal exists at all in S3 v2, it should be least buried on the brightest
grains (2θ modulation scales as bireflectance directly, on a bright S0; 4φ scales as
bireflectance squared). Built `--brightness-quantile` for
`experiments/002-s3v2-geometry/run.py` so this is checkable on Sibusiso's machine without a
new archive.

### Worked

- **TDD'd against a hand-built `HarmonicSignature`, not the real archive** (still not on this
  machine). `test_pool_signatures_can_restrict_to_the_brightest_pixels` constructs 20 synthetic
  pixels, dim half at snr_2 = 2 (below `DETECTION_SNR`), bright half at snr_2 = 6 (above it);
  unrestricted pooling medians to 4 and stays `NEITHER`, restricting to the top half by `dc`
  isolates the bright group and flips the verdict to `SECOND`. Watched it fail first
  (`TypeError: unexpected keyword argument 'brightness_quantile'`), then implemented the
  minimal filter in `pool_signatures` (`experiments/002-s3v2-geometry/run.py`) — quantile the
  pooled `dc` array, keep pixels at or above it, before the existing modulating-fraction
  selection runs.  244/244 tests green (243 → 244), ruff clean.
- **Explicit about what a positive result would and wouldn't mean.** A `SECOND` verdict on the
  brightest-quantile subset is evidence for an analyser signal the unrestricted pool missed —
  not an automatic reversal of N3, since it needs the subset to also be large and representative
  enough to trust. `main()` prints that caveat directly rather than letting a subset flip read
  as a clean overturn.

### Did not work

N/A — this session added a capability, not a fix; nothing was broken first.

### Learned

A `NEITHER` verdict from pooling *everything* can still hide a real signal that only survives
on the most favourable pixels. Testing the favourable subset directly is worth doing before
treating a pooled null as final — but the result has to be reported with its own caveats, or a
subset-level positive quietly becomes a headline the full data doesn't support.

### Left open

The actual command — `--brightness-quantile 0.5` against the real archive — still needs
Sibusiso's machine; this session built and tested the capability, it did not run it. Update
`CONTEXT.md` / this file again once it has.

`docs/05-toolchain.md`'s `uv`-on-Windows note is now written (§1): the failure text, that root
cause wasn't isolated (Developer Mode vs. Defender, untested), the `PYTHONPATH` workaround used,
and what to try if it recurs. Nothing here needed an SBOM change — no dependency changed, only
what to do when the existing one misbehaves on Windows.

---

## 2026-08-21 — session 10 · a third instance, and this one had no gate at all

### Attempted

A deliberate sweep of `trust/` for the same defect class session 8 and 9 fixed — a comparison
that should account for whether *n* can resolve it, and silently doesn't. `split.py` is clean
(pure set logic, no thresholds). `baseline.py` was already fixed in session 9. `abstain.py`'s
`AbstentionAudit.concentrates_at_transitions` was not: a bare
`rate_during_ore_change > rate_when_stable`, comparing two proportions at two different sample
sizes, with **no resolvability check anywhere** — not degenerate at an edge, ungated everywhere.

### Worked

- **Demonstrated the defect before touching the fix.** 1 abstention out of 3 ore-change events
  (33.3%) vs 5 out of 20 stable (25.0%) read as `concentrates_at_transitions = True` — "blind
  spot 1" printed in the summary — despite `noise_during_ore_change` on the same line saying
  ±27.2%. The 8.3-point gap was inside its own printed standard error.
- **Considered and rejected the obvious port first.** The instinct was to reuse the
  single-proportion rule-of-three bound from each side and require the gap to exceed their sum
  — non-overlapping intervals. Traced it against the project's own canonical demonstration
  (2/2 abstained during 2 ore-change events, 0/13 stable) before writing anything: at n = 2,
  `bound_during_ore_change` is already `None` (`3/n >= 1`), so the sum-of-bounds approach would
  return unresolvable there too — silently flipping the headline "blind spot 1, in numbers"
  example from `True` to `False`. Too consequential to do by accident; not attempted.
- **Fisher's exact test instead** (`scipy.stats.fisher_exact`, one-sided `"greater"`). Published
  (Fisher 1922), exact rather than asymptotic, so it does not degenerate at small *n* or at
  p = 0/1 the way the Wald SE does. `scipy>=1.14` was already a declared, licensed dependency
  (BSD-3-Clause) — this is its first live caller in `src/reefprint/`.
- **The canonical example survives, and now says why.** Fisher's exact on the 2/2-vs-0/13 table
  gives p ≈ 0.0095 — significant, `concentrates_at_transitions` stays `True`,
  `test_abstention_concentrated_at_transitions_is_flagged_in_words` passes unmodified. The
  summary line used to read as a contradiction — "n = 2, which resolves nothing" next to "blind
  spot 1: refusals concentrate" two clauses later. It now reads `(Fisher's exact p = 0.010)`
  next to the claim, because the two clauses were always answering different questions (the
  rate's own precision vs. whether the *comparison* is real) and the line never said so.
  `resolves_nothing` was never wrong; it just wasn't the test that mattered.
- **`n_stable == 0` is a real, reachable state.** `audit_abstentions` only refuses
  `n_ore_change == 0`; an all-transition run passes it, and `rate_when_stable` returns its `0.0`
  convention rather than a measurement. `concentration_p_value` returns `None` there — no
  baseline, no p-value — rather than letting the comparison read the manufactured `0.0` as a
  real stable rate.
- **`summary()` gets a third state.** Direction down-or-equal (unchanged wording); direction up
  and significant (`"blind spot 1"` + p-value); direction up but *not* significant or with no
  baseline at all — a new clause, because `"do not concentrate"` there would overclaim safety
  exactly where *n* is weakest, which is the same mistake in the other direction.
- 4 new tests, all watched RED first (`AttributeError: no attribute 'concentration_p_value'`,
  then a live assertion failure showing `"blind spot 1"` printing on the noise scenario), then
  GREEN. 243 tests total (was 239), ruff clean. Full suite and every summary shape printed and
  read by eye — session 8's lesson, applied rather than restated a third time.

### Learned

The pattern from sessions 8 and 9 was "a degenerate value used as a threshold answers the same
way every time and says nothing about it." This one generalises the pattern one step further:
the threshold doesn't have to be degenerate to be missing. Two proportions compared directly,
with no resolvability check *at all*, is the same failure with the edge case removed — it fires
on point estimates at every *n*, not just at the extremes. Worth asking of any remaining
comparison in the package: not just "does this degenerate", but "is there a resolvability check
here in the first place."

### Left open

Nothing new. N3 remains the single next action for the project, unchanged by this session:

```
uv run python experiments/002-s3v2-geometry/run.py --archive path/to/S3_v2.zip
```

---

## 2026-08-20 — session 9 · the same degenerate SE in `baseline.py`, and it was worse there

### Attempted

Session 8's *Left open* flagged `ScoredMetric.noise_at_honest_n` as carrying the same
degenerate-Wald defect that had just been fixed in `abstain.py`, and deliberately did not fix
it in a rule-5 commit. This is that commit. It supersedes that *Left open* item.

Expected a mechanical port of the same three-part repair. It was not one — the same formula
failed **differently** here, and worse.

### Worked

- **In `abstain.py` the defect was loud; in `baseline.py` it was silent.** `abstain` printed
  `±0.0%` on the summary line, which is a visibly wrong number. `ScoredMetric` prints no
  interval at all in that state. What it does instead:

  ```python
  elif (noise := self.noise_at_honest_n) is not None and self.uplift <= noise:
  ```

  At a metric of exactly 1.0, `noise` is `0.0`, so the test is `uplift <= 0.0` — **never true
  for a positive uplift.** The middle verdict, the whole point of rule 3's three-state summary,
  **could not fire.** Measured before the fix:

  ```
  balanced accuracy = 1.000 (n = 12) · majority class 0.500 · metadata-only 0.950
    · +0.050 over the strongest baseline (0.950)
  ```

  Twelve localities out of twelve, against a metadata-only baseline of 0.95, reported as a
  clean win. The rule of three puts the 95% lower bound at **0.75 — below the baseline.** The
  correct reading is "we cannot tell", and it read as a result.

- **The fix, in four parts.** `noise_at_honest_n` returns `None` at exactly 0 and 1 as well as
  outside [0, 1]. New `bound_at_honest_n` is the rule of three (Hanley & Lippman-Hand 1983),
  `None` where `3/n >= 1`. New `resolution_at_honest_n` is the single number an uplift has to
  clear — one SE in the middle, the distance from the point estimate to the bound at the ends,
  which works out to `3/n` at both. `uplift_exceeds_noise` and `summary()` both go through it.

- **The two `None` reasons had to be told apart, and that is the part worth keeping.**
  `resolution_at_honest_n` is `None` for two unrelated reasons: *the question does not apply*
  (an RMSE has no binomial SE) and *the question applies and n cannot answer it* (a proportion
  pinned at an end with n ≤ 3). The old code had only the first case and fell back to the plain
  sign of the uplift, which for the second case is the over-claim all over again. Split with
  `_is_proportion`: not a proportion falls back to the sign as before; a proportion that n
  cannot resolve returns `False`, because no uplift clears a band spanning the range.

- **The coverage mismatch is stated, not hidden.** One SE is about 68%; the rule of three is
  95%. So a metric at an end is judged against a wider band than one in the middle. That is
  written into `resolution_at_honest_n`'s docstring as deliberate and in the conservative
  direction — the ends are where n tells you least, and a perfect score on twelve localities
  is the most flattering thing this class can be asked to report.

- **12 tests, 239 green overall**, ruff and format clean. Ten were watched fail first. The
  other two passed on the first run by design, because they are regression guards rather than
  RED tests: `test_the_middle_of_the_range_is_untouched_by_the_fix` and
  `test_a_perfect_score_that_clears_the_bound_still_reads_as_a_win`.

- **Read the output before calling it done**, which is session 8's lesson applied rather than
  restated. All seven summary shapes printed and checked by eye:

  ```
  1.000, n=12 vs 0.950 → uplift +0.050 ... is inside the 0.250 that n = 12 resolves
                          — 95% lower bound 0.750 by the rule of three
  1.000, n=12 vs 0.500 → +0.500 over the strongest baseline (0.500)
  1.000, n=3  vs 0.950 → uplift +0.050 ... cannot be resolved at all: n = 3 resolves
                          nothing at this end of the range
  0.000, n=12 vs -0.200 → ... is inside the 0.250 that n = 12 resolves
                          — 95% upper bound 0.250 by the rule of three
  0.620, n=12 vs 0.600 → ... is inside the ±0.140 that n = 12 resolves
  0.920, n=40 vs 0.600 → +0.320 over the strongest baseline (0.600)
  4.200, n=12 vs 9.000 → does not beat the strongest baseline (9.000, uplift -4.800)
  ```

  The second line is the one worth checking rather than assuming: a perfect score against a
  weak baseline still reads as a win, correctly, because the 0.750 lower bound is still above
  the 0.500 baseline. The conclusion survives the pessimistic end, which is exactly what the
  comparison against `3/n` is asking.

### Did not work

Nothing failed that was not supposed to. The ten RED tests failed for the stated reasons and
passed after the fix; no existing test needed changing, which is the useful signal here —
`test_noise_is_not_estimated_for_a_metric_that_is_not_a_proportion` asserts `"resolves" not in
summary` for an RMSE and still holds, so the new `_is_proportion` split did not disturb the
case that was already right.

### Learned

**The same bug is not the same bug.** The plan was to port a fix. What actually transferred was
the *diagnosis* — `sqrt(p(1-p)/n)` is zero at the ends — and not the symptom, the severity, or
the repair's shape. In `abstain` it printed a wrong number on a line a human reads. Here it
disabled a branch, and a disabled branch produces no output at all to notice. **The louder
instance was the less dangerous one**, and it was the one that got found first, because it
printed something.

**A degenerate value is most dangerous where it is used as a threshold.** Zero as a *reported*
quantity is a visibly silly interval. Zero as the right-hand side of `uplift <= noise` is a
comparison that always answers the same way, and there is nothing in the output to say so. Both
places used the identical expression. Worth checking the other comparisons in this package
against the same question: not "is this number right" but "what does this comparison do when
this number degenerates".

### Left open

- **N3 is still the single next action.** Nine sessions of guards, none of which touches it.
  One command on Sibusiso's machine:
  `uv run python experiments/002-s3v2-geometry/run.py --archive path/to/S3_v2.zip`
- **`TrivialBaselines` still assumes higher is better**, documented in its docstring and not
  enforced. Unchanged by this session, and now the only *stated assumption* left in this
  module.
- **The rule-of-three band and the one-SE band are different coverages** (95% against about
  68%). Documented as deliberate. If a reviewer objects, the answer is to quote a Wilson or
  Jeffreys interval throughout rather than to widen the middle — but that changes every number
  the package has already reported, so it is a decision, not a tidy-up.
- **Rule 4 is still prose.** These two fixes are rule 4 enforced in the two places that happened
  to compute an interval; nothing yet stops a metric being reported without one. That is the
  remaining placeholder `test_reported_coverage_interval_matches_honest_n`.
- **Still no caller** for `split`, `baseline`, `abstain` or `quantity` beyond the rule-1/rule-5
  seam. Unchanged.

---

## 2026-08-20 — session 8 · rule 5 becomes a type, and the guard is a missing field

### Attempted

Rule 5, the last of the silently-failing rules: *abstention emits a conservative default with a
stated reason, never "unknown."* Same treatment as 1, 2 and 3.

Rule 5 is the odd one out, because the failure it guards against is not a bad input. The other
three refuse something malformed — a leaked split, a bare metric, an unlabelled number. Rule 5's
failure is a system that does exactly what it was told: it abstains, correctly, at a genuine
ore transition, and then **holds the last setpoint**, which at a transition is the worst
available action. Nothing is malformed. Every value is real. The plant runs on the previous
ore's setpoint for as long as the refusal lasts.

So the guard could not be a validator. It had to be an **absence**.

TDD: 37 tests written first, watched fail against `NotImplementedError` stubs, then implemented.
Then four more, after the defect below.

### Worked

- **[`reefprint.trust.abstain`](../src/reefprint/trust/abstain.py).** `Abstention` has three
  fields — `default`, `reason`, `trigger` — and **no slot for a previous value**. Holding the
  last setpoint is not discouraged, it is unreachable: there is nowhere to put it.
  `test_an_abstention_cannot_carry_a_previous_value_to_hold` asserts that against
  `dataclasses.fields`, so re-adding one breaks a test rather than passing review.
  `value_to_act_on(decision)` takes one argument for the same reason — a signature of
  `(decision, previous)` is the whole bug, pre-installed.

- **This contradicts the submitted abstract, on purpose.** The abstract says the system
  "abstains and holds the last-known-good setpoint". `CONTEXT.md` §8 already recorded that as
  deliberate; it is now enforced rather than recorded.
  `test_an_abstention_emits_the_conservative_default_not_the_previous_prediction` is that
  contradiction as a test: steady state reads 0.12, the ore changes, and what reaches the
  controller is 0.90 rather than the held 0.12.

- **`"unknown"` is rejected by name.** Rule 5 names it specifically, so the guard does too:
  `unknown`, `n/a`, `na`, `none`, `error`, `tbd`, `?`, `-`, `--`, case- and space-insensitive.
  A blank reason is also refused. The reason is a required positional field, not an optional
  string that defaults to something polite.

- **Rule 1 meets rule 5 at the seam.** `ConservativeDefault.quantity` is a `Quantity` and is
  checked with `require_reportable()`, so a conservative default derived from a design target is
  refused **at construction**, not on the slide. This is `quantity.py`'s **first real caller** —
  the "nothing calls these guards yet" item that has been in *Left open* since session 6 is now
  half closed.

- **"Conservative" has a direction, and only the inversion is machine-checkable.**
  `ASSUME_HIGH` that emits the low half of its own range is a `ValueError`. The check is against
  the **midpoint**, which is the weakest possible statement of "on the safe side" — deliberately
  not a tuned threshold. *How far* along the safe side is domain judgement and is reported, not
  enforced: pinning defaults to the extreme is how you get operators who switch the system off,
  and that is a 100% abstention rate that never reports itself.

- **`audit_abstentions()` refuses a run with no ore-change events in it.** The only number left
  to report would be the aggregate, and quoting the aggregate is precisely blind spot 1's error.
  A gate that has never been tested through a transition has not been tested.

- **41 tests, 227 green overall** (`uv run pytest -m "not placeholder" -q`), ruff and format
  clean. The two rule-5 placeholders in `tests/test_trust.py` are built, so they were removed
  rather than left claiming `NOT BUILT`; deselected drops 26 → 24. `CONTEXT.md` §4 updated
  186 → 227 in the same commit.

### Did not work

**The 37 tests passed on the first run, and the defect was found by reading the printed line.**
The summary said:

```
abstention rate 13.3% overall · 100.0% during ore change (n = 2, ±0.0%) · 0.0% when stable ...
```

`±0.0%`. The Wald standard error `sqrt(p(1-p)/n)` is **exactly zero at p = 0 and p = 1**, so the
*least* informative observation available — two transitions, both refused — prints as the *most*
precise. That is invented precision, rule 4's exact prohibition, inside rule 5's own summary
line. Small runs land on those extremes constantly; this is not an edge case, it is the common
case early on.

Fixed with the **rule of three** (Hanley & Lippman-Hand 1983: 0 events in n gives a 95% upper
bound of 3/n), which is a published result and therefore satisfies rule 1 rather than being a
threshold chosen here. `noise_during_ore_change` now returns `None` at the extremes instead of
a false zero, and `bound_during_ore_change` covers them. Where even 3/n bounds nothing — n = 2,
where 3/n ≥ 1 — the line says *"which resolves nothing"* rather than printing a number:

```
100.0% during ore change (n = 2, which resolves nothing)
100.0% during ore change (n = 10, 95% lower bound 70% by the rule of three)
  0.0% during ore change (n = 10, 95% upper bound 30% by the rule of three)
 50.0% during ore change (n = 12, ±14.4%)
```

Four tests written for it first, watched fail (`4 failed, 37 passed`), then fixed.

**One of those four tests was wrong, and the implementation was right.** It asserted
`"0.0%" not in summary.split("when stable")[0]`, which caught the *stable* rate of 0.0% — a
correct number — rather than the conditional interval. Retargeted at the conditional
parenthetical. Fixing a wrong test, not bending a test to match code.

**A test of my own was internally inconsistent and would have proved nothing.**
`test_the_inversion_is_refused_in_the_other_direction_too` used `assumed(0.95, "percent", ...)`
against a 0.0–100.0 percent range. 0.95 already sits in the safe half, so a correct
implementation would have passed it. Fixed to `95.0` before implementing against it.

**A one-in-five flake in `test_polarim.py`, not caused by this work.** See *Left open*.

### Learned

**Session 7's boundary claim was wrong by one.** It said *"the four guards now cover every rule
that fails silently — rules 1, 2, 3 and the geometry hazard"* and concluded that was a reason to
stop. Rule 5 fails silently too, and worse than any of them: the others produce a number that is
wrong, this one produces a *plant that keeps running on the previous ore's setpoint* while the
software correctly reports that it has abstained. Nothing in the logs looks wrong. The lesson is
not that the boundary should have been drawn wider, it is that **"fails loudly" was assessed on
the software's output rather than on the process's behaviour**, and those are different
questions.

**Tests do not read output.** All 37 passed and not one of them asked whether the printed
precision was real, because every assertion was about values and refusals — the things a test
author naturally thinks to assert. The interval was rendered, not returned, so it lived in the
one place the suite did not look. Printing the summary and reading it took thirty seconds and
found a rule-4 violation inside a rule-5 guard. **Read the output of anything that formats a
number for a human.**

**The strongest guard was the field that is not there.** Rules 1, 2 and 3 are refusals — code
that runs and raises. Rule 5's core guard executes nothing: `Abstention` simply has no slot for
a previous value, and `value_to_act_on` has no parameter for one. There is no check to skip and
no error to catch, which makes it the only one of the four with no route around it at all. Where
a rule forbids an *action* rather than a *value*, look first for a field to leave out.

### Left open

- **N3 is still the single next action.** Eight sessions of guards, none of which touches it.
  One command on Sibusiso's machine:
  `uv run python experiments/002-s3v2-geometry/run.py --archive path/to/S3_v2.zip`
- **`ScoredMetric.noise_at_honest_n` has the same degenerate-Wald defect** that was just fixed
  here — it returns exactly 0 at a metric value of 0 or 1. That is rule 3's guard, so changing
  it is a separate decision and a separate commit, not something to fold into a rule-5 change.
  Flagged, not fixed.
- **`tests/test_polarim.py::test_recovery_does_not_require_uniform_angular_sampling` failed once
  in five full-suite runs** and passes in isolation, over eight random hypothesis seeds, and in
  four subsequent full-suite runs. The test already skips ill-conditioned draws
  (`cond(design) > 100.0`), so a failure means angles that **pass** the conditioning gate can
  still miss `rel=1e-7` — the threshold and the tolerance are not consistent with each other.
  Not caused by this session's work and not fixed in it. Reproduce with a full-suite run, not a
  single-file one; the draw appears to depend on global RNG state set by earlier tests.
- **Rule 5's second clause is built but has no real data behind it.** `audit_abstentions()`
  computes the conditional rate correctly; nothing yet produces a run of real decisions with
  real ore-change flags to feed it. That needs the OOD gate, which needs segmentation.
- **`abstain` has no caller either**, same as `split`, `baseline` and `quantity` before it.
  The first will be the demo path in `viz/`, which is where a refusal has to be *visible*.

---

## 2026-08-20 — session 7 · rule 1 becomes a type, and provenance is contagious

### Attempted

Session 6's *Learned* named this as the remaining silent-failure rule and said it was the
hardest, which was right. Rules 2 and 3 have a shape a guard can grab: a split is a pair of
sets, a metric is a number next to other numbers. Rule 1 has none. **An invented number and a
measured one are the same 64 bits.** `0.35` is `0.35` whether it came from a calibration run, a
textbook, a phantom, a plausible guess, or a spec for hardware that was never built. There is no
malformed state to detect — the number is fine. What is missing is everything *around* it.

So the guard could not be a check on the value, and this is the point the design turned on: it
had to be a property carried **with** the value, and it had to **propagate through arithmetic on
its own**. Contamination does not surface where the assumption is written. It surfaces three
functions downstream, in a variable named something reasonable like `grain_size_um`, at which
point nobody can tell.

TDD throughout: 30 tests written first, watched fail against `NotImplementedError` stubs, then
implemented. Nothing failed after implementation this time, which is a weaker signal than
session 6's disagreement — see *Learned*.

### Worked

- **[`reefprint.quantity`](../src/reefprint/quantity.py).** `Quantity` carries a `Provenance`
  and a **mandatory non-empty `source`**. Arithmetic keeps the **weakest** input's provenance
  and accumulates every source, deduplicated and ordered, so a derived number can always say
  what fed it. Five ranks:

  ```
  MEASURED  →  CITED  →  STIPULATED  →  ASSUMED  →  DESIGN_TARGET
    a result    published   true of the    a guess,    hardware that was
                value      phantom only    labelled    never built
  ```

- **`STIPULATED` is its own rank and that was deliberate.** Experiment 001's phantom ground
  truth is exactly true — of the phantom, and of nothing else. Folding it into `MEASURED` would
  let the week-1 gate's leg (a) quietly read as mineralogy, which is the exact conflation
  `CLAUDE.md` warns about two lines below the gate table.

- **`require_reportable()` is the boundary**, and `__float__` calls it. `float(q)` is the
  obvious way around any wrapper, so it is the route that had to be closed. A **flagged
  assumption passes** — rule 1 permits assumptions, it requires labels, and by the time you hold
  a `Quantity` it has one. `DESIGN_TARGET` never passes.

- **The number that makes ADR-0002 mechanical instead of a preference.** 47 px × **0.2** µm/px
  is 9.4 µm. 47 px × **1.6** µm/px is 75.2 µm. Same design target, a **factor of 8** apart. That
  is not a measurement with wide error bars; it is a figure that could be 9 µm or 75 µm,
  presented to three significant figures. `test_the_design_target_spans_a_factor_of_eight_so_it_
  is_not_a_number` asserts the ratio is exactly 8.0 and that **both** ends are refused.

- **Bare floats cannot join in.** `measured(1.0, "um", ...) + 2.0` raises `TypeError`, because
  the unlabelled literal is precisely the thing rule 1 is about. Units are checked on `+`/`-`
  and cancel on `×`/`÷` (`px` × `um/px` → `um`), because a scale factor is the usual doorway for
  an unlabelled number, and `px*um/px` in a caption is how it stays in.

- **30 tests, 186 green overall** (`uv run pytest -m "not placeholder" -q`), ruff and format
  clean. `CONTEXT.md` §4 updated 156 → 186 in the same commit, which is now the third session
  running where that number would otherwise have gone stale.

### Did not work

Two things needed fixing rather than accepting:

`_multiply_units` shipped its first draft with a vacuous guard — a loop over
`((right, left, left), (left, right, right))` testing `other is denominator`, which is
`True` by construction on both iterations. It gave the right answer for the wrong reason.
Rewritten to two cases and one condition.

`ruff` caught an en dash in `0.2–1.6 µm/pixel` in the module docstring (RUF002) and an
unescaped `match="CLAUDE.md 0.2-1.6 um/px"` in the test (RUF043 — the `.` are metacharacters).
Both are the same class of thing this module exists to stop: a string that looks right and
means something slightly different.

### Learned

**Nothing failed after implementation, and that is worth noticing rather than celebrating.**
Session 6's value came from a test disagreeing with the code once both existed — the
disagreement was where the third summary state came from. Here the tests and the implementation
agreed immediately, which means either the design was clear before it was written, or the tests
were not adversarial enough. Honest answer: some of both. The tests that would have caught a
weak design are the ones asserting *contagion in both directions* and *`float()` cannot escape*,
and those were written first for exactly that reason. But no test here asked a question the
design had not already answered.

**The four guards now cover every rule that fails silently.** Rules 1, 2, 3 and the geometry
hazard. What is left in prose — rules 4 through 9 — fails *loudly* or fails at review: a missing
CI is visible on the slide, an LLM computing a control value is visible in the code, a
non-permissive licence is visible in the SBOM. That is the boundary, and it is a reason to stop
adding guards rather than a reason to keep going.

### Left open

- **N3 is still the single next action.** Seven sessions of guards, none of which touches it.
  One command on Sibusiso's machine:
  `uv run python experiments/002-s3v2-geometry/run.py --archive path/to/S3_v2.zip`
- **Nothing calls `quantity` yet**, same as `split` and `baseline`. The first real caller is
  `calibrate/` — R% conversion is where cited QDF values meet measured intensities, which is
  the exact seam this type exists for. Written before its caller, deliberately.
- **`Quantity` does not vectorise.** It wraps a scalar. Per-pixel Stokes arrays cannot carry
  provenance this way, and pretending otherwise would be worse than not trying — the array-level
  answer is provenance on the *array*, not per element, and that is a different design.
- **The `higher is better` assumption in `TrivialBaselines`** is still documented, not enforced.

---

## 2026-08-20 — session 6 · rules 2 and 3 stop being prose

### Attempted

Session 5's *Learned* section named the next job and this is it. Rules 2 (locality splits) and 3
(trivial baseline) were paragraphs in `CLAUDE.md`. Both fail **silently** when ignored, which is
the property that makes prose the wrong medium — nothing prompts you to go and re-read a rule
you have already forgotten. Turn both into refusals, the same way `RotationGeometry` and
`LabelProvenance` already work.

TDD throughout: 28 tests written first, watched fail with `NotImplementedError` against stubs,
then implemented. The one test that failed *after* implementation was the interesting one — see
*Did not work*.

### Worked

- **Rule 2 — [`reefprint.trust.split`](../src/reefprint/trust/split.py).**
  `split_by_locality()` is the sanctioned constructor; `require_locality_disjoint()` is the
  backstop for the split someone builds by hand in a notebook, which is the route around any
  constructor. Refuses: a locality on both sides, a section filed under two localities, mixed
  label provenance, a held-out name absent from the data, holding out everything, and a
  single-locality dataset. Unmeasured sections are dropped **and counted** — a skipped section
  has no pixels, and leaving it in inflates the denominator.

  Typed against a `Grouped` Protocol rather than `SectionMeasurement`, deliberately: the failure
  happens at the *patch* level, so a guard that only accepts sections is absent exactly when it
  is needed.

- **The number that justifies it.** 192 synthetic patches, 24 sections, 6 localities, where the
  only signal in the feature is *which section this patch came from* — nothing transferable to
  learn. A 1-NN model scores **MAE 0.0017** under a shuffled patch split and **MAE 0.2119**
  under the honest locality split. **126x**, in the flattering direction, from a model that has
  learned nothing. `test_a_patch_level_split_reports_a_far_better_score_than_the_honest_one`.

- **Rule 3 — [`reefprint.trust.baseline`](../src/reefprint/trust/baseline.py).**
  `ScoredMetric` takes `baselines` as a **required field with no default**, so a metric without
  its trivial baselines is a `TypeError` rather than a slide. Uplift is measured against the
  *strongest* baseline, never the weakest — quoting the gap to majority class while
  metadata-only sits higher is the flattering error, and metadata-only is the baseline that most
  often wins. `NotApplicable(reason)` allows a baseline to be genuinely absent but never
  silently; both inapplicable at once is refused.

- **31 tests, 156 green overall** (`uv run pytest -m "not placeholder" -q`), ruff and format
  clean. `CONTEXT.md` §4 was claiming **86 passed** — stale since before session 5, and exactly
  the kind of number that gets trusted. Now 156.

### Did not work

One test failed after implementation, and it was right to:

```
test_a_metric_that_does_not_beat_the_baseline_says_so_in_words
assert "does not beat" in summary.lower()
E  AssertionError: ... '+0.020 over the strongest baseline (0.600)'
```

The test asserted that 0.62 against a 0.60 baseline should read as "does not beat". The
implementation said it beats it by 0.02. **Both were defensible and both were wrong.** +0.02 is
positive, so "does not beat" is a false statement; and +0.02 at n = 12 is a seventh of one
standard error, so reporting it as an uplift is worse than false, it is misleading in the exact
direction the rule exists to prevent.

Fixing the test to match the code would have been the easy move and the wrong one. Instead the
summary gained a **third state**, which is what the test was reaching for: below the baseline;
above it but inside the noise honest *n* resolves; above it by more than that.

```
balanced accuracy = 0.620 (n = 12) · majority class 0.500 · metadata-only 0.600 ·
uplift +0.020 over the strongest baseline (0.600) is inside the ±0.140 that n = 12 resolves
```

`√(p(1-p)/n)` is the formula this package already quoted for conformal coverage SD — reused, not
invented (rule 1). It returns `None` outside [0, 1], because a binomial SE on an RMSE would be an
invented number. `TrivialBaselines` assumes **higher is better**, which an error-like metric
violates; stated in the docstring as an assumption rather than silently mis-ranking.

### Learned

**Where two guards meet, the seam is where the dishonest number lives.** Rule 3 says report the
baseline. Rule 4 says carry a CI at honest n. Each is satisfiable alone by a report that is still
misleading: a baseline with no sense of scale, or a CI with nothing to compare against. The
number that survives both is the one worth putting on a slide, and it took a *failing test* to
find that seam — writing the assertion first is what produced a disagreement sharp enough to
notice. Tests written afterwards agree with the code by construction.

Two rules down. Rule 1 (never invent a number) is the remaining one that fails silently, and it
is the hardest to make structural, because an invented number is indistinguishable from a
measured one at the type level. The nearest available handle is provenance on the value itself —
the `LabelProvenance` pattern, one level down.

### Left open

- **N3 is still the single next action** and none of this touches it. One command on Sibusiso's
  machine.
- **Nothing calls these guards yet.** They are constructors and backstops with no caller until
  week 2's falsification test, which is the first thing that produces a metric. Guard written
  before the code that needs it, deliberately — the alternative is writing it afterwards, which
  is when the flattering split has already been run once.
- **The `higher is better` assumption in `TrivialBaselines`** is documented, not enforced. If an
  error-like head arrives (grain-size RMSE), that assumption needs a type, not a docstring.

---

## 2026-08-20 — session 5 · ADR-0003 the naming, and the guard that goes on someone else's machine

### Attempted

Three things, none of them physics. Settle what the system is *called*, now that it exists under
two names in two repositories. Get REEFPRINT's history somewhere Sibusiso can read it. And close
the gap between a warning written in `CONTEXT.md` and a check that actually runs.

### Worked

- **[ADR-0003](04-decisions/0003-one-build-two-names-reefprint-and-khanya.md): one build, two
  names.** REEFPRINT leads and KHANYA is the same system's other name; both are correct, neither
  is deprecated. The decision that matters is what it *forecloses*: **no package is renamed and
  no histories are merged.** Renaming `reefprint.*` 42 days out would cost an import sweep across
  two repos and blur the two parallel histories that are the rule-8 originality defence, all for
  a label. *Khanya* is "to shine, to give light" in the Nguni languages, which is a better
  description of the measurement than REEFPRINT is — that is a reason to keep the name, not a
  reason to switch to it.

- **REEFPRINT's history pushed to `Sibusiso-K/KHANYA` as the `reefprint` branch, unmerged.**
  Eleven commits, in one place to read, still separate to authenticate. `git fetch && git
  checkout reefprint`. JOINT-PLAN §5 names merging two architectures in 43 days as the single
  biggest risk; a branch is how you share code without taking that risk.

- **The false negative is now blocked in code.**
  [`Sibusiso-K/KHANYA#2`](https://github.com/Sibusiso-K/KHANYA/pull/2). `src/polarimetry.py`
  called `stokes_from_rotation_series` on raw arrays — bypassing `RotationSeries`, and therefore
  bypassing `require_analyser_rotation()`. It now runs `harmonic_signature()` first and refuses
  the whole run unless the verdict is `SECOND`, returning a report that carries the evidence and
  names the next step rather than `None` or a null result (rule 5).

  Refused at the run, not the section, deliberately: geometry is a property of the acquisition,
  so if one S3 v2 section is a stage rotation then all 47 are, and pooling the other 46 into a
  clean null is the exact failure being prevented.

- **The number that justifies the guard.** Synthetic pyrrhotite-like **stage** series at S3 v2's
  real layout — 72 frames, 5° steps, `r₁=0.40 r₂=0.354`, contrast *a* ≈ 0.12 — fed to the
  rotating-analyser inversion: **median anisotropy 1.5e-02**. A strongly anisotropic mineral,
  reported isotropic, no exception and no NaN. Guard verified both ways at the same layout:
  analyser series 2nd harmonic at **29.1×** its noise floor and 4th at 0.9× → passes; stage
  series 2nd at 1.0× and 4th at **65.3×** → refused.

### Did not work

Nothing failed, but one thing was worse than the previous session recorded. `CONTEXT.md` §3 said
KHANYA imported "a frozen snapshot predating the geometry discriminator". Listing it showed the
snapshot's `polarim/` directory in full:

```
~/Desktop/REEFPRINT - Copy/src/reefprint/polarim/
    __init__.py
    stokes.py
```

No `geometry.py`, no `extinction.py`. Not a stale copy of the module set — an inverter with no
way to check what it was inverting and no fallback for the answer coming back "wrong geometry".
The resolver now searches `$REEFPRINT_SRC` → live checkout → sibling checkout → that snapshot
last, and **rejects any candidate missing `polarim/geometry.py` by name**, because a resolver
that silently falls back to a stale tree reproduces the original bug one layer down.

### Learned

**A warning in a document is not a control.** `CONTEXT.md` already said, in bold, *"do not let
that experiment run before this one does"* — correct, prominent, and worth nothing at 2am on
someone else's laptop. The same sentence as a `raise` costs about forty lines and cannot be
skipped. Where a project rule protects against a *silent* wrong answer, prose is the wrong
medium: the whole hazard is that nothing prompts you to go and re-read the prose.

Generalises to the other standing rules. Locality splits (rule 2) and the trivial baseline
(rule 3) are currently prose in the constitution, and both fail silently when ignored.

### Left open

- **N3 itself is untouched by this.** The guard changes what happens when the archive is the
  wrong geometry; it does not say which geometry S3 v2 is. Still one command on Sibusiso's
  machine, still the single next action.
- **The ten-minute storyboard is a draft, not a running order.** Nine beats exist and are being
  refined. Recorded in `CONTEXT.md` §3 so it does not quietly become the specification —
  gauntlet blind spot 11, where the person who owns the narrative also owns the architecture.
- **The dual name now has to be applied consistently** to the abstract, slides and submission:
  both names on first mention, REEFPRINT alone after. A doc naming only one of them is a defect.

---

## 2026-08-20 — session 4 · `4d849f7` the bridge, `e8a3273` the fourth-harmonic estimator

### Attempted

Two things, both about seams. Design the boundary where KHANYA's labelled masks meet a REEFPRINT
rotation series, without merging the two codebases. Then remove finding N3 as a *blocker* rather
than continuing to wait on it — build the estimator that leg (b) needs if the answer comes back
`FOURTH`, so that either verdict has a route.

### Worked

- **`reefprint.bridge` as a data contract, not a merge.** Sibusiso's own `JOINT-PLAN.md` §5 names
  merging two architectures as the largest schedule risk in the project, and it is correct. So the
  contract is *data* — two arrays and four strings. KHANYA can satisfy it by importing the package
  or by writing an `.npz` and never importing REEFPRINT at all. Labels flow in, measurements flow
  out, nothing flows back; a one-way boundary can be reasoned about, a two-way one becomes a merge
  by accident.

  Its real value is that three rules stop being documentation and become structural:

  | Rule | Before | Now |
  |---|---|---|
  | N3 | `require_analyser_rotation` on `RotationSeries`, bypassable | called unconditionally on the only path in, and `test_no_keyword_argument_can_disable_the_geometry_check` asserts the signature so no escape hatch can be added quietly |
  | Rule 2 | locality carried by convention | `LabelledSection.locality` required, never defaulted, error text names Rule 2 |
  | N2 | floor computed where someone remembered to | `MineralStatistic` carries `noise_floor_median` beside `anisotropy_median` in one frozen record; `median_over_floor` is the comparable number |

  The N2 test is the one worth keeping: `test_the_noise_floor_rises_as_reflectance_falls` puts
  pentlandite (R = 50) and chromite (R = 13) side by side, both **exactly** cubic, and asserts the
  *darker* phase reads the **larger** apparent anisotropy. That is the trap, stated as a passing
  test rather than as a warning in a docstring.

- **Raise-vs-skip, asymmetric on purpose.** Wrong geometry raises: which element rotated is a
  property of the acquisition protocol, constant across a dataset, and 47 identical skip records
  inviting someone to pool the zero survivors is worse than one exception naming the cause. Shape
  and angle-count problems skip, and report *both* shapes — their count is the diagnosis, one bad
  mask against a transposed archive. That second path is exactly the crash KHANYA's ten-mineral
  symmetry test is currently dying on.

- **`reefprint.polarim.extinction`.** `I(phi) = A0 + A4c cos4phi + A4s sin4phi`, least-squares per
  pixel, giving extinction depth `|r1-r2|² = 8·A4` and the extinction azimuth mod 90°. N3 is now a
  fork in the road rather than a wall.

- **The N3 failure is symmetric, and that was not obvious.** Fitting `4φ` to a rotating-analyser
  series returns an extinction amplitude of ~0 for every anisotropic grain over a uniform angle
  set — the same silent "everything is isotropic", arrived at from the other direction. Having
  built one guard and watched the first real caller walk around it,
  `RotationSeries.require_specimen_rotation` was written *at the same time as* the estimator, and
  `test_fitting_the_fourth_harmonic_to_an_analyser_series_is_silently_zero` proves the failure
  instead of asserting it: pyrrhotite's depth reads `< 1e-9` while the same pixels under the
  correct inversion read DOLP = 0.12 exactly.

- **`crossing_ratio = dc/amplitude` turned out better than expected.** Working through an analyser
  uncrossed by `ε`, with `P = (r1+r2)/2` and `Q = (r1−r2)/2`:

  ```
  amplitude    = Q²/2                       — independent of ε
  crossing_ratio = 1 + 2 sin²ε (P/Q)²       — exact, not a small-angle expansion
  azimuth      = φ₀ + ε/2
  ```

  So leakage does **not** bias the depth. That is the actual argument for fitting the harmonic
  rather than reading a peak-to-trough range, which absorbs the pedestal in full. And since
  `P/Q ≈ 2/a`, the leak check gets *sharper* as the anisotropy weakens — half a degree of
  uncrossing reads 1.04 on pyrrhotite (a = 0.12) and 1.68 on chalcopyrite (a = 0.03). Weak
  anisotropy is precisely when an operator is tempted to uncross, and that is when this catches
  them. All three predictions verified at `rel=1e-9` against a forward model written independently
  from the reflection matrix, so a sign error in one is not shared by the other.

- **The `2/a` advantage pinned at its root.**
  `test_extinction_depth_is_quadratic_where_analyser_modulation_is_linear`: halve `a` and the
  extinction depth drops 4×, while DOLP drops 2×. This is what experiment 002's measured 38×
  noise-survival ratio comes from, and it is why the estimator is a fallback and never a
  substitute. The talk must not blur the two.

125 passed, 26 deselected. `ruff check .` clean.

### Did not work

- **First draft of `crossing_ratio`'s docstring claimed leakage "biases `extinction_depth` upward".
  It does not.** Writing the test made that obvious — the fitted `A4` is `Q²/2` regardless of `ε`.
  The claim was inherited from thinking about a peak-to-trough estimator, which *is* biased, and
  it survived into prose because nothing had checked it yet. Corrected in place before commit.
- **A first assertion of `crossing_ratio > 2.0` at half a degree of uncrossing failed at 1.042.**
  The derivation was exact to `1e-9`; the *magnitude* claim around it was invented. Replaced with
  the exact formula plus a test of the scaling — which is the more useful property anyway. Rule 1
  applies to adjectives in docstrings, not only to numbers in code.
- **`float()` on a `(1, 1)` array is a `TypeError` in NumPy 2.** The single-pixel test forward
  model returned `(n, 1, 1)`; dropping the spatial dims to `(n,)` matches the existing
  `_single_pixel` idiom in `test_polarim.py` and every recovered quantity reads as a plain float.

### Learned

**A guard is only as good as the narrowest path it sits on.** `require_analyser_rotation` was
correct, tested, and bypassed within a week — not maliciously, but because a caller who builds the
intensity array itself never touches the object carrying the guard. Moving it onto a *mandatory*
boundary and then asserting the function signature is the difference between a rule and a hope.

The corollary, applied for the first time here: when you find yourself building a second estimator
that can fail the same way, write its guard in the same commit. Not after the incident.

### Left open

`reefprint.bridge` measures `ANALYSER` series only — a stage archive raises at the boundary rather
than being routed to `extinction`. That is deliberate for now: the two produce different quantities
in different units and one measurement type per path is the point of the seam. Once experiment 002
returns a verdict, the losing branch can be deleted rather than plumbed.

The estimator's `bireflectance_contrast` needs a mean reflectance from outside the geometry, and
`reefprint.calibrate` does not exist yet. Until it does, any `a` from a stage archive is
conditional on a number this project cannot supply.

---

## 2026-08-20 — session 3 · `52711d3` OME-TIFF store, `19154c5` the geometry discriminator

### Attempted

Close week-1 leg (b): read a stored public rotation series through the same `RotationSeries`
container the phantom uses, and run the identical Stokes inversion on LumenStone S3 v2.

Then, on absorbing Sibusiso's KHANYA repo, stop leg (b) from running into finding N3 — and stop
his ten-mineral symmetry test from doing the same thing first.

### Worked

- **`reefprint.acquire.store`** round-trips a `RotationSeries` through OME-TIFF via `tifffile`,
  angles and geometry carried in the OME-XML header rather than in filenames. ADR-0001 holds; no
  JVM anywhere.

- **`reefprint.polarim.geometry.harmonic_signature` turns N3 from an inference into a
  measurement.** Joint fit of both harmonics,

  ```
  I(a) = A0 + A2c cos2a + A2s sin2a + A4c cos4a + A4s sin4a
  ```

  with each amplitude compared against **its own** noise floor read off the design matrix,
  `cov = σ²(AᵀA)⁻¹`, times the Rayleigh factor `√(π/2)` for the magnitude of a two-component
  Gaussian. Joint rather than sequential: on a non-uniform angle set power leaks between the
  harmonics and a sequential fit hands the leak to whichever was fitted first.

  Evidence it is calibrated rather than decorative: **the losing harmonic reads 1.0× its floor**,
  not merely "smaller" (`test_the_losing_harmonic_sits_at_its_own_noise_floor`, `snr_4 = 1.0 ±
  0.6` at 40% noise while `snr_2 > 10`). A floor wrong by a constant factor would still give the
  right verdict on clean data and fail on noisy data, which is the worst place to find out.

  Four verdicts, two of them refusals. `BOTH` and `NEITHER` map to `RotationGeometry.UNKNOWN`,
  **never to `ANALYSER`** — the module cannot wave the inversion through by failing to decide.

- **The end-to-end proof**, `test_the_discriminator_catches_what_the_stokes_inversion_silently_
  misses`: a stage rotation whose frames demonstrably modulate (`ptp > 0` on every anisotropic
  pixel) inverts to `anisotropy < 1e-9` everywhere, and the same frames are correctly read as
  `SPECIMEN` by the harmonic signature.

- **`experiments/002-s3v2-geometry/`** settles N3 against the real archive, decoding one frame at
  a time out of the zip so peak memory is one frame. Smoke-tested through a synthetic archive
  built to S3 v2's exact layout, JPEG round-trip included: a known stage archive reads back
  `FOURTH` at snr 16.3, with the 2θ channel at exactly 1.0× its floor.

- **`pillow` promoted from transitive to declared**, with `SBOM.md` and `docs/05-toolchain.md`
  rows in the same commit (Rule 7). Licence **MIT-CMU**, read from the installed distribution's
  own `License-Expression` metadata — the SPDX declaration attached to the wheel we actually
  install, not a guess.

86 passed, 26 deselected. ruff clean.

### Did not work

- **The first claim about 8-bit quantisation was wrong, and it was wrong in the flattering
  direction.** The smoke run returned `NEITHER` on a synthetic archive that was a pure stage
  rotation by construction. The story that fit was: crossed-polars intensity goes as
  bireflectance *squared* on a near-black field, so 8 bits should starve it while the analyser
  geometry, riding on a bright S0, survives. A sweep appeared to confirm it — stage detected at
  5% noise raw, undetected at 2% once quantised, analyser untouched. A 3× penalty, asymmetric,
  and a tidy consequence of the physics already in the constitution.

  It was an artefact of my own conversion. `np.ndarray.astype(np.uint8)` **wraps** negative
  values rather than clipping them, and

  ```
  stage frames at 5% noise: min=-0.26787  negatives=1419300 of 3110400 (45.63%)
  np.array([-1.0]).astype(np.uint8)  ->  [255]
  ```

  Nearly half of a crossed-polars stack is below zero, because the signal sits on a near-black
  field and the noise is additive and symmetric. Wrapping that many samples to arbitrary bright
  values destroys the 4th harmonic — which looks exactly like a quantisation penalty and is not
  one. With `np.clip(np.round(...), 0, 255)`, what a sensor and a JPEG encoder actually do:

  ```
  stage, 5% noise:  snr_4 = 6.8 raw   6.9 quantised   -> FOURTH either way
  ```

  **8-bit conversion costs neither geometry its verdict**, 0–5% noise. The caveat had already
  been written into `run.py` and a passing test had already been written to support it. Both were
  wrong, and the test was the more dangerous of the two: it asserted a true-sounding conclusion
  and passed for a reason that had nothing to do with it.

  Nothing in `src/` casts to an integer type — checked, not assumed — so no shipped code was
  affected. The trap is now pinned by the clip in `_to_eight_bit` and stated in its docstring.

### Learned — the 2/a advantage, measured

Chasing the quantisation story to ground produced the number it was a bad imitation of. Sweeping
noise until each geometry stops being detectable:

```
stage    : last detected at noise_pct 0.05,  missed at 0.08
analyser : last detected at noise_pct 2.0,   missed at 3.0
```

**The analyser geometry stays detectable through 38× more noise than the stage geometry.**
CLAUDE.md predicts the advantage is `2/a` and that it *grows as the anisotropy weakens*; across
the phantom's anisotropic phases — pyrrhotite `a = 0.12`, chalcopyrite `a = 0.03` — that spans
16.7× to 66.7×. The measurement lands inside the band.

This is a consistency check, not a derivation: a detection-threshold ratio over a mixed field at a
declared SNR threshold is a different quantity from a per-grain contrast ratio. But it converts
the argument for the rotating analyser from a line of algebra into a measured number, and it is
strongest exactly where the base-metal sulphides live — which is the whole point.

It has a second consequence that matters for reading the real archive: **a `NEITHER` verdict is
not neutral.** A null is far more likely if the frames are stage rotations than if they are
analyser rotations, so a null leans toward N3 being *true*. `run.py` says so in its own output
rather than leaving it to be reasoned out later, and it is explicitly not clearance to invert.

### Learned — the risk arrived from the other repo, not this one

Sibusiso's KHANYA is a separate 46-commit repo that imports `reefprint.polarim.stokes` unchanged
across a path bridge. His `src/polarimetry.py::sample_section` feeds all 72 S3 v2 frames straight
into `stokes_from_rotation_series`, bypassing `require_analyser_rotation()` — which was committed
hours earlier and which he had no way to know about.

If S3 v2 is stage-rotation data, his ten-mineral symmetry test returns a separation ratio near
1.0 and reads as **"polarimetry does not work on real ore"**: a false negative against the
project's central claim, produced by an estimator bug, on the one experiment most likely to be
believed. Two people building carefully against a shared invariant is not enough when the
invariant is four hours old.

The general form, worth keeping: **an inference that everyone agrees with is still an inference,
and a shared codebase propagates it faster than it propagates the correction.** N3 had been
written into `CLAUDE.md` as "almost certainly" and that was sufficient to reason with and
insufficient to build on. It needed to become a file that answers the question.

Not incidentally: his comment asserting that duplicated rows at θ and θ+180 leave `cond(A)`
unchanged is **correct** — all singular values scale by √2, and the SNR improves by √2. It was
checked before being flagged, and not flagged.

### Decided

- N3 is decided **from the frames**, never from filenames, metadata, or the paper's prose.
  `RotationGeometry` defaults to `UNKNOWN` and refusals map there rather than to `ANALYSER`.
- Experiment scripts stay in numbered directories and are loaded **by path** in tests
  (`tests/test_s3v2_reader.py::_load_experiment`). An un-numbered importable copy would drift
  from the script that is actually run.
- A mask/frame shape mismatch is **skipped with both shapes named, not raised**. Dying on the
  first one hides how many there are, which is the number that decides whether it is one bad
  section or a transposed dataset. This is the failure that killed the first real run.

### Left open

- **N3 itself.** The discriminator is built and tested; it has **not been run on the real
  archive**. The 5.2 GB `S3_v2.zip` is on Sibusiso's machine — a `find` for it here returns
  nothing. One command, and it gates the week-1 gate. Pinned by the failing placeholder
  `tests/test_s3v2_reader.py::test_the_real_s3_v2_archive_has_been_measured`.
- **How the two repos join.** KHANYA's `JOINT-PLAN.md` §5 warns against rewriting either into the
  other; the bridge belongs at the mask/series boundary. Not yet designed.
- LumenStone's licence is still informal and unnamed.

## 2026-08-15 — session 2 · `9cc509c` ADR-0002, and the documents

### Attempted

Verify the four week-1 source modules under lint and test, fix what failed, commit. Then write
down the hardware decision the decision-maker had already made verbally, and produce the
onboarding documents — `CONTEXT.md`, this file, `docs/05-toolchain.md`.

### Worked

- **Week-1 gate leg (a) passes.** `experiments/001-week1-gate/run.py` reports
  `GATE  pyrrhotite / pentlandite anisotropy = 40.4x` at 36 analyser angles, σ = 0.25 R%,
  off-cone pixels 0.00%, residual RMS 0.2376 R%. The sharper variant — both sulphides forced to
  identical R = 44.0% so brightness cannot carry the separation — still separates. That is the
  point: reflectance alone would not do this.
- **Suite state: 53 passed, 25 deselected** (`-m "not placeholder"`), and **25 failed**
  (`-m placeholder`). Lint and format clean across 41 files.
- **Property-based testing earned its place immediately** — see the sign bug below. Hypothesis
  found in seconds what no example-based test in the file would have found at all.
- **The placeholder-marker pattern is working.** `pytest.mark.placeholder` splits CI into a
  blocking `check` job and an informational `gates` job, so the red list *is* the backlog and
  nothing has to be tracked outside the repo. `test_stored_rotation_series_loads_from_ome_tiff`
  is currently the whole of the next task, expressed as a failing test.
- **Provenance-on-the-value works.** Reflectances carry a `Provenance` `StrEnum` on the value
  itself, not in a comment, and `test_no_placeholder_value_is_reported_as_measured` fails if a
  `PLACEHOLDER` ever escapes into something presented as measured. Rule 1 with teeth.
- **`matplotlib.figure.Figure` rather than `pyplot`** — no global state, no display backend, and
  the viz tests can read arrays back out of the figure (`figure.axes[i].images[0].get_array()`)
  and assert on what was actually drawn rather than on what was passed in.

### Did not work

- **A real sign bug shipped in `RotationSeries.rotated_specimen`.** It subtracted φ where it
  should add. Rotating the specimen by φ rotates (S1, S2) by **2φ**; getting the sign backwards
  produces a Stokes image that is *self-consistent*, passes every physical-realisability check,
  and is silently reflected about the analyser axis. Hypothesis produced two distinct
  counterexamples (`assert 1.0 == -0.6536…`, `assert -0.909… == 0.909…`). Fixed to `+ phi_rad`
  and the derivation is now in the docstring. **The test was also rewritten to go through the
  shipped method** — the original reimplemented the angle shift, so it could only ever agree with
  itself.
- **`float()` on a numpy array of shape (1,)** raises
  `TypeError: only 0-dimensional arrays can be converted to Python scalars` under numpy 2.x. Was
  a test bug, not a code bug. Use `.item()`.
- **`# noqa: PLR2004` on a rule that is not enabled** → `RUF100 unused noqa`. `PL` is not in the
  ruff select list. Replaced the magic number with a named module constant `_FRAME_NDIM = 3`,
  which reads better anyway.
- **`ruff format` rewraps a multi-line `if` into something worse.** Pre-empted by extracting the
  condition into a named variable (`design`, `WELL_CONDITIONED`). Fighting the formatter is not
  a strategy; naming the thing is.
- **PowerShell here-strings break `git commit -m`.** A message containing apostrophes ("didn't")
  and `&` fragmented into multiple git pathspecs. **Fix: write the message to a file and use
  `git commit -F <path>`.** This will happen again — every commit message in this project has
  prose in it.

### Learned — the anisotropy noise floor, and why it matters

Derived from the design matrix, not guessed: the rotating-analyser inversion has covariance
`cov = σ²(4/n)·diag(1, 2, 2)`, so S1 and S2 each carry independent noise `σ√(8/n)`, their
magnitude is Rayleigh-distributed, and a **truly isotropic** phase therefore reads

```
E[DOLP | isotropic] = σ · √(8/n) · √(π/2) / S0
```

Confirmed against the run output to three significant figures and pinned by
`test_the_anisotropy_noise_floor_scales_as_one_over_reflectance` across R = 4.75–50% and
n = 12–36.

Two consequences that constrain everything downstream:

1. **Any fixed anisotropy threshold is a reflectance-dependent classifier in disguise.** At
   σ = 0.25 R%, n = 36: gangue at R = 4.75% reads DOLP ≈ 0.031 from pure noise while pentlandite
   at R = 50% reads ≈ 0.003. A rule fitted on bright sulphides lights up every dark grain on the
   section. Discrimination must condition on S0 and report an interval.
2. **The floor falls only as 1/√n.** Halving it costs four times the frames. Averaging is not a
   free lunch and there is no exposure trick that beats the arithmetic.

Promoted to repo-level open finding **N2**.

### Learned — the prior-art position is weaker than we had been saying

"Nobody uses polarised light in ore microscopy" is **false**, and a judge may know it. **Pirard,
Lebichot & Krier (2007), *Particle texture analysis using polarized light imaging and grey level
intercepts*** is direct prior art on polarised-light imaging in this exact field. The claim has
been retightened to *per-pixel full linear Stokes recovery*, which is not the same thing as
imaging under crossed polars — but **the paper is unread**. Open finding **N1**, must be closed
before week 6. Do not discover this on stage.

A targeted search for Stokes polarimetry applied to sulphides returned nothing specific. That is
weak support, not clearance.

### Decided

**[ADR-0002](04-decisions/0002-software-only-no-instrument-is-built.md) — software only, no
instrument is built.** Hardware budget R0. The ~R5,000 rig becomes a costed BOM presented as a
design.

This survives only because `RotationSeries` is the acquisition boundary: a rotation series is a
rotation series whether the analyser was turned by a stepper, by a hand on a Leitz stage in 2019,
or by a forward model, and `reefprint.polarim` never learns which. The ADR states the cost rather
than reframing it as a win — no claim about µm/pixel, exposure, LED response, polariser
extinction or achievable R% accuracy may now come from measurement, and the week-4 degraded-input
gate loses real defocus and real polish damage.

Also decided: **ADR-0001's decider filled in** (Lethabo Mphukuile), which closes CLAUDE.md open
question 4.

### Left open

`N1` Pirard 2007 unread · `N2` the 1/S0 floor · LumenStone licence is informal and unnamed
(`khvostikov@cs.msu.ru`) · `docs/03-free-stack.md` §3 and §6 now contradict ADR-0001 and ADR-0002
and are marked superseded in place.

---

## 2026-08-15 — session 1 · `76de236` week-1 gate, `28f374b` scaffold, `c1af1a5` constitution

### Attempted

Stand the repo up from nothing: constitution, design docs, gauntlet findings, a working
environment, and the first physics — rotating-analyser Stokes recovery with a synthetic phantom
that has a closed-form correct answer.

### Worked

- **`uv` as the whole environment story.** One lockfile, one command, no conda. `uv sync` from a
  clean checkout produces a working test suite without pulling PyTorch, because everything heavy
  is an optional extra (`ml`, `integrate`, `viz`).
- **One failing test per unbuilt module, committed on purpose.** Eight modules exist as
  directories with a red test naming exactly what is missing. `--strict-markers` and
  `--strict-config` mean a typo in a marker is an error, not a silently-skipped test.
- **The physics core.** `I(θ) = (S0 + S1·cos2θ + S2·sin2θ)/2`, least-squares inverted per pixel.
  Frozen slotted dataclasses for the Stokes container, `typing.Protocol` +
  `@runtime_checkable` for the acquisition boundary so the phantom and a future file reader are
  interchangeable without inheritance.
- **The identity that makes the whole project one measurement rather than two.**
  `(I_max − I_min)/(I_max + I_min) = √(S1² + S2²)/S0 = DOLP`. The degree of linear polarisation
  *is* the normalised bireflectance contrast of classical ore microscopy. One quantity carries
  both the optics and the mineralogy.
- **Refusing an ill-conditioned angle set rather than returning a plausible answer.**
  `cos 2θ` and `sin 2θ` have period π, so 0°/90°/180° gives only *two* independent equations, not
  three. `stokes_from_rotation_series` checks the design-matrix condition number and refuses.
  A silent rank-deficient least-squares fit would have been the worst possible failure mode: an
  answer, with no error, that is wrong.

### Did not work

- **`picamera2` / `python-prctl` will not build on Windows.** `python-prctl` is Linux-only and
  pip drags it in. The `hardware` extra was **removed entirely** rather than made conditional —
  the Pi is a deployment target, not something a dev laptop should have to resolve. The reasoning
  is preserved as a comment in `pyproject.toml` so nobody re-adds it. (ADR-0002 later made the
  whole question moot.)
- **`Bio-Formats` was in the constitution's stack line and cannot be.** It is GPL-2.0, and the
  deliverable must be assignable to Mintek — the same failure mode gauntlet finding S3 raised and
  the DINOv3 removal was meant to close. Solving it for the model backbone and then reintroducing
  it at the I/O layer would leave the licence argument no better than v1's.
  → **[ADR-0001](04-decisions/0001-ome-tiff-via-tifffile-not-bioformats.md): `tifffile`,
  BSD-3-Clause.** No JVM anywhere.

### Learned

The pivot that produced this repo — v1 hyperspectral → v3 reflected-light polarimetry — is
recorded in `docs/00-STATUS.md` under *How we got here*, and the four fatal findings that forced
it are in `docs/02-gauntlet-findings.md`. Read those before proposing anything; most good ideas
have already been killed here for a stated reason.

### Left open

Everything past `polarim`, `acquire` and `viz`. Deliberately — the red test list is the backlog.
