# ENDGAME — the plan to win Mintek-SCi Grad Hackathon 2026

**Status:** active build plan. Supersedes `PITCH.md` §7 ("what to do with the
remaining time") and extends `JOINT-PLAN.md` §4 phases 2–3.
**Owners:** Sibusiso (KHANYA / `main`) + Lethabo (REEFPRINT / `reefprint`),
with two AI sessions working in parallel — Claude on `main`, Codex on
`reefprint`. Coordination protocol in §6.

---

## 1. Who we are presenting to

Researched 2026-09-03. This is not background colour; three of these facts
should change what we build.

- **Mintek was founded in 1934** (as the National Institute for Metallurgy,
  reconstituted as Mintek in 1989), HQ in Randburg. It is one of the world's
  leading minerals-processing and extractive-metallurgy organisations, with
  patented technology in use in 40+ countries.
- **Mintek's single most famous achievement is making UG2 chromitite ore
  commercially viable — which nearly doubled South Africa's accessible PGM
  reserve base.** We are pitching a UG2/PGM story *to the institution that
  created the UG2 industry*. Two consequences, and both are load-bearing:
  1. Relevance is free. We do not have to explain why UG2 matters.
  2. **Every UG2 claim will be checked by the people who wrote the book.** A
     single overclaim costs more here than at any other venue. Our existing
     discipline (`CLAUDE.md` Rule 1, the abstract's own `NEITHER` correction)
     is not pedantry in this room — it is the price of entry.
- **Mintek's current strategy** (CEO Dr Molefi Motuku) centres on critical
  minerals, local beneficiation, rare earths and precursor materials — and one
  pillar is *exploration and geoscience focused on geological data collection
  and **accessibility***. That word is our opening: our whole argument is that
  optical microscopy is the accessible instrument and SEM/QEMSCAN is the scarce
  one.
- **The 2025 winner** was UJ Chemical Engineering's *H2Optimise* — an
  AI-integrated model for reprocessing tailings-dam water. Judges praised
  "creativity and technical knowledge" and *relevance to actual industry
  needs*. Note the shape: **domain engineering first, AI as the multiplier.**
  Not an ML project wearing a mining hat. Ours must read the same way.
- **2025 theme was "Status Quo is Boring."** The event is explicitly framed
  around challenging conventional practice.

### How we are scored

From the official FAQ, the judges evaluate on five criteria:

> **Innovation · Feasibility · Impact · Technical Execution · Presentation Clarity**

Two process facts that matter:

- **Winners are only announced after Mintek's Office of Technology Transfer
  (MOTT) completes an IP assessment on the top-ranked solutions.** Provable,
  legible authorship is part of winning, not paperwork afterwards. This is the
  hard justification for ADR-0003's two clean parallel commit histories — keep
  them clean.
- **Creators receive invention credits.** Contribution needs to be attributable
  per person. Our commit trail already does this; do not blur it now.

---

## 2. Honest self-assessment against the five criteria

Scored as a judge would, not as we would like.

| Criterion | Where we stand | The gap |
|---|---|---|
| **Innovation** | **Strong.** Per-pixel linear Stokes polarimetry is genuinely distinct from published multispectral-reflectance automated mineralogy. The geometry discriminator (`polarim/geometry.py`) is a piece of rigour most entries will not have. | Say it in one sentence a non-specialist repeats correctly. |
| **Feasibility** | **Strong.** Software-only (ADR-0002), offline on one laptop, permissive licences, SBOM-tracked, no capex. | Must be *demonstrated*, not asserted — see W3. |
| **Impact** | **Weakest link.** Real methodological results, but the headline economic number is not yet one that survives Mintek scrutiny. | Needs the QEMSCAN-triage framing plus the new Bushveld result. See §3. |
| **Technical Execution** | **Split.** REEFPRINT: 282 passing tests, CI, ADRs, SBOM, ruff, pre-commit — excellent. KHANYA `main`: **zero tests, no CI.** | The asymmetry is the liability. See W4. |
| **Presentation Clarity** | **Unproven.** A nine-beat storyboard exists but is explicitly "drafted, not decided." Two project names is a comprehension tax. | Decide it, then rehearse it. See W5. |

### The strategic problem, named

Our most distinctive intellectual asset is **epistemic honesty**. We have, on
the record: N3 came back `NEITHER`; extinction found no separation in S3 v2;
no public texture dataset exists; no oxidation index is computable from XRF
majors. That is genuinely better science than most entries will contain, and
Rule 9 says falsification is a deliverable.

**But a judge scoring *Impact* hears four sentences beginning "we checked, and
it didn't work."**

Do not solve this by hiding the nulls. Solve it by making the nulls the
*evidence for a positive product claim*.

---

## 3. The reframe — one sentence, then the proof

> **We built the part of an automated mineralogy system that knows when its own
> answer is not trustworthy — and we proved it works by turning it on ourselves
> and letting it refuse four times.**

Under this framing every null becomes an asset:

| The null | What it proves about the product |
|---|---|
| Geometry discriminator returns `NEITHER` on S3 v2 | The instrument detects an unusable input instead of returning a confident wrong map. **We measured the cost of not having it: a stage series inverted with the analyser model returns median anisotropy 1.5e-02 — a strongly anisotropic mineral reported as isotropic, no error raised.** |
| Extinction finds no separation (8.2% detection vs 10.0% false-positive floor) | The conformal calibration is honest: it hits its 10% target exactly and declines to manufacture signal. |
| Texture features do not exist publicly (T1) | We searched the literature systematically and documented it, rather than fabricating a feature. |
| Oxidation index not computable (no Fe²⁺/Fe³⁺ split in XRF majors) | We check whether the data can support a claim *before* making it. |

And we now have a **positive, measured result on Mintek's own ore body**:

> On 1,112 real Bushveld chromitite assays across 305 boreholes (Bachmann 2019,
> LG/MG seams, Thaba mine), chromite composition (Cr#, Mg#) adds statistically
> significant PGE-grade signal beyond Cr₂O₃ alone — ΔR² = 0.0279, **p = 0.0002**,
> cluster-robust by borehole.

Carry its caveats out loud (modest effect size; Cr# is arithmetically related to
the Cr₂O₃ baseline). Stating the caveat *before a judge finds it* is worth more
than the number itself in this room.

### What we claim, and what we refuse to claim

- **We claim:** an accessible optical instrument plus a trust layer that
  abstains rather than guessing; a measured result on real Bushveld chromitite;
  a quantified evaluation trap (patch-level splitting flatters error by 126×).
- **We refuse:** UG2 grade estimation (no public chromite imagery exists —
  documented in `DATA-SOURCES.md`), and any claim that we validated
  pentlandite/pyrrhotite separation on real ore (we did not; the phantom is a
  phantom and is labelled as one).

---

## 4. The build — workstreams, in dependency order

No dates. Ordered by what unblocks what, and by scoring value per unit of work.

### W1 — Close the Week-3 bug *(blocks: gate 3 being genuinely green)*
`tests/test_trust.py::test_a_locality_outside_the_band_fails_the_gate_even_if_the_pool_would_pass`
fails on `reefprint@52a9a42`. A locality with perfect held-out coverage (20/20)
is marked outside the band, because `CoverageBand` is sized purely from
*calibration-set* uncertainty (`Beta(19,2)`, legitimately tight near 1.0) while
`LocalityCoverage.within_band` compares it against an empirical proportion from
a *held-out* sample carrying its own binomial noise. Decide which is wrong —
the fixture (n=20 held-out is too small to hit 20/20 safely) or `within_band`
(should be a predictive interval combining both noise sources, or one-sided,
since over-coverage is not the safety failure). **Owner: Codex.** Statistical
design call — do not paper over it.

### W2 — Week 4: zero silent failures under degraded input *(highest judge value per unit work)*
`test_no_silent_failure_under_degraded_input` — defocus, glare, poor polish,
wrong exposure, empty field. Every degraded input yields a result **or a stated
refusal**, never a confident number. This is simultaneously the Week-4 gate, the
best evidence for *Feasibility*, and the most striking beat in the demo (§5,
beat 6). **Owner: Codex** (lives in `reefprint.trust`).

### W3 — Week 5: end-to-end offline on one laptop *(this IS the demo)*
The single highest-value artefact remaining. A judge believes what they watch.
Requirements: runs with the venue wifi off (the Google-Fonts CDN bug is the
precedent — grep for `http` before shipping), on one laptop, from raw rotation
series to a decision with an uncertainty band, **including a live refusal.**
**Owner: Claude (KHANYA dashboard) + Codex (reefprint integrate seam).**

### W4 — Close the Technical Execution asymmetry on `main` *(pure scoring)*
KHANYA `main` has zero tests and no CI against REEFPRINT's 282 + CI. Add
`tests/` covering the real logic: `conformal.py` (band coverage), `advisor.py`
(the liberation decision boundary and `LIBERATION_MARGIN`), `modal.py` (the
empty-particle crash fixed in entry 23), `polarimetry.py` (frame-shape skip,
geometry guard), `chromite_pge_falsification.py` (Cr#/Mg# arithmetic against
hand-worked values). Add a CI workflow mirroring REEFPRINT's. **Owner: Claude.**

### W5 — Decide the ten minutes, then rehearse it *(Presentation Clarity)*
The storyboard is drafted, not decided. Lock the running order, assign who
speaks, and rehearse against a stopwatch. Structure it to hit the rubric
explicitly — see §5. **Owner: both, human decision.**

### W6 — Impact, quantified and bounded *(fixes the weakest criterion)* — DRAFTED
`MINTEK-FIT.md` §3.1 now has the number: on the 12 held-out S2 sections, the
validated patches pipeline gives a confident answer (Continue/Grind finer) for
6 and flags 6 for verification — 50%, 95% CI [21%, 79%] at this n, stated as
an interval, not a point estimate. Anchored to a real, dated, cited QEMSCAN
price ($1,500/sample, SRC Advanced Microanalysis Centre, Apr 2017 — an
order-of-magnitude anchor, not a current or Mintek-specific quote) and a real
turnaround citation (ALS Global: not overnight, workload-dependent, 1-week
*expedited* option at a surcharge). Explicitly states what is NOT shown: no
validation yet that our "verify" flags agree with what QEMSCAN or a human
mineralogist would flag. **Owner: Claude drafted; needs Sibusiso/Lethabo to
sign off the economics before it goes on a slide** — the interval and the
caveats are as important as the 50%, and a domain read on whether $1,500/2017
is a fair anchor for what Mintek would actually compare against.

### W7 — Week 6: backup demo video *(insurance, cheap)*
Record the working demo. If the laptop dies on stage, the talk survives.
Do it the moment W3 is green, not at the end. **Owner: whoever finishes first.**

### W8 — Repo as a finished artefact *(MOTT + Technical Execution)*
See §7. The MOTT IP assessment means someone technical *will* read this repo.

---

## 5. The ten minutes, mapped to the rubric

Each beat should be traceable to a criterion the judges are scoring.

| Beat | Content | Scores |
|---|---|---|
| 1 | The scarce instrument problem, quantified: ~50% of sections (95% CI [21%,79%], n=12) get a confident optical answer with no QEMSCAN queue or fee; the rest are correctly flagged (`MINTEK-FIT.md` §3.1) | Impact |
| 2 | The physics reflectance cannot reach: crystal symmetry under polarised light | Innovation |
| 3 | What we built, one sentence + the architecture | Technical Execution |
| 4 | The positive result: Bushveld chromitite, p = 0.0002, with its caveat stated by us | Impact |
| 5 | **Live demo** on the laptop, wifi off | Feasibility |
| 6 | **The system refuses** — the geometry discriminator declines an unusable input, on stage | Innovation + Feasibility |
| 7 | Why refusing is the product: the 1.5e-02 number — what a confident wrong answer looks like | Impact |
| 8 | What we did not prove, said before anyone asks | Credibility (scores everywhere) |
| 9 | What Mintek gets next, and the mentor ask | Impact |

Beat 6 is the one people will remember. Build the demo around it.

---

## 6. Division of labour and coordination protocol

Two AI sessions are working this repo in parallel. **Claude on `main`. Codex on
`reefprint`.** This is not arbitrary — ADR-0003 keeps the two commit histories
separate for MOTT's originality assessment, and cross-branch commits blur
exactly the evidence that protects us.

**Rules of engagement:**

1. **Stay on your branch.** Claude commits to `main` only; Codex to `reefprint`
   only. Work the other half needs goes through the bridge pattern
   (`src/polarimetry.py` imports `reefprint.*` unchanged) — never by copying
   code across.
2. **Read before you write.** `HANDOVER.md` (main) and `CONTEXT.md` +
   `docs/BUILDLOG.md` (reefprint) are the only channel when we are not both
   online. Read the newest entry first; write one after.
3. **Verify across the boundary.** Codex's host has no Python; Claude's does.
   Claude runs REEFPRINT's suite (`PYTHONPATH=src pytest tests/ -q`) after
   Codex pushes, and reports failures back. Codex reviews KHANYA-side
   statistics for the same reason. *Neither of us merges our own untested work.*
4. **A disagreement is a signal, not noise.** If your reading of a gate or a
   blocker differs from this document, say so before proceeding. Two of this
   project's best findings (the conformal correction, the abstract's geometry
   overclaim) came from exactly that.
5. **Do not fabricate to close a gate.** Rule 1. Four things have already been
   reported as "not possible with available data" and the project is stronger
   for each. A fifth is fine. An invented number is fatal — especially with an
   IP assessment in the loop.

---

## 7. Repo standards — what "clean" means here

The MOTT assessment and the Technical Execution score both mean a technical
reader opens this repository. Judgement applied: **surgical cleanup, not a
restructure.** Renaming packages or moving doc paths four weeks out — with a
parallel agent mid-flight and `DATA-SOURCES.md` referenced from nine files
including runtime error strings — is churn that risks the thing it is meant to
polish.

**Doing:**
- Root clutter (17 stray `.log` files, loose scripts) out of the working
  directory into `logs/` and `scripts/`, both gitignored. Untracked already, so
  zero history risk — this is about what a screen-share shows.
- `README.md` earns its place as the front door: headline result, how to run it,
  an accurate repo map, and a link table to STATUS / HANDOVER / PITCH /
  MINTEK-FIT / JOINT-PLAN / DATA-SOURCES / ENDGAME.
- `tests/` and CI on `main` (W4).

**Deliberately not doing:**
- Renaming `src/` to a package namespace (breaks every import and doc reference
  for cosmetic gain).
- Moving `HANDOVER.md`, `STATUS.md`, `DATA-SOURCES.md` (live surfaces, heavily
  referenced, and HANDOVER is the coordination channel with a second agent
  actively writing to it).
- Merging the branches. ADR-0003 forbids it, and MOTT is the reason.

---

## 8. Definition of done

The project is finished when:

- [ ] Every gate in `CONTEXT.md` §3 is green **or** carries a written, evidenced
      reason it is not — no gate silently unaddressed.
- [ ] The demo runs end-to-end, offline, on the presentation laptop, including a
      live refusal, and has been run start-to-finish at least three times.
- [ ] A backup video of that demo exists.
- [ ] `main` and `reefprint` both have a green test suite, and someone other
      than the author has run each.
- [ ] Every number in the talk traces to a file in the repo, and every claim we
      cannot support is named on a slide before a judge asks.
- [ ] `README.md` on both branches orients a stranger in under two minutes.
- [ ] The ten minutes has been rehearsed against a stopwatch with the running
      order locked.
