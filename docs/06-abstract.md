# 06-ABSTRACT — Mintek SCi Grad Hackathon 2026 submission

**Due 30 August 2026. One page.** The letter requires three things explicitly: the proposed
approach, the methods or technologies, and the expected outcomes or impact. It also states that
submissions undergo plagiarism, AI-generation, IP and originality checks, and that external
sources, data and contributions must be acknowledged.

**Every number below traces to a run in this repository.** Provenance is noted in the
working notes at the bottom of this file, which are *not* part of the submitted page.

---

## THE SUBMITTED PAGE

---

### A computational ore microscope: per-pixel Stokes polarimetry for characterisation of UG2 ore

**REEFPRINT** (developed as **KHANYA**) — Team Sonar, University of the Witwatersrand
Challenge: *Computer Vision for Real-Time Mineralogical Characterisation*
[TEAM MEMBER NAMES AND DISCIPLINES — see working notes]

**The problem.** PGE recovery from UG2 ore is governed by base-metal sulphide deportment:
pentlandite is the principal PGE host and floats, pyrrhotite is depressed and carries little PGE,
and fine chromite reporting to concentrate is a smelter penalty. Resolving that assemblage today
means SEM-based automated mineralogy — QEMSCAN or MLA — accurate, but offline, slow,
capital-intensive, and therefore never in the control loop. The obvious optical shortcut fails on
physics rather than on engineering: hyperspectral
reflectance identifies minerals by molecular absorption features, and chromite — 50–75 vol% of
UG2 — is an opaque spinel with none. On chromitite, a spectrometer is a brightness meter.

**Our approach.** Opaque ore minerals have been identified since the 1940s by quantitative
specular reflectance, bireflectance and anisotropy under crossed polars, and published automated
optical mineralogy — the Castroviejo–Pirard line, CAMEVA, AMCO — classifies on multispectral
reflectance alone. We add an axis reflectance does not contain: recovery of the **full linear
Stokes vector at every pixel** from a rotating-analyser image series. Reflectance cannot reliably
separate pentlandite (cubic, isotropic) from pyrrhotite (moderately bireflectant, anisotropic);
the per-pixel Stokes signature can — and that separation governs PGE deportment and flotation
response. Polarised-light *imaging* in ore
microscopy is established prior art (Pirard, Lebichot & Krier, 2007); per-pixel Stokes vector
recovery is not, and that narrow claim is the one we defend.

**Methods and technologies.** Segmentation of polished-section imagery (PyTorch, Apache-2.0
backbones), reflectance calibrated against the IMA/COM Quantitative Data File, harmonic inversion
for the Stokes parameters, and conformal prediction for calibrated per-prediction uncertainty.
Three decisions distinguish the build. First, **acquisition geometry is measured, not assumed**: a
rotating analyser modulates at the second harmonic and yields the Stokes vector; stage rotation
under crossed polars modulates at the fourth and yields only extinction depth. Fitting the Stokes
model to a stage rotation returns zero anisotropy for every anisotropic grain, silently — so the
inversion refuses to run until geometry is confirmed from the data. Second, **every quantity
carries its provenance** — measured, cited, stipulated, assumed — through arithmetic, so an
assumption cannot be laundered into a reported result. Third, **the system abstains**: at ore
transitions it emits a conservative default with a stated reason rather than holding the previous
setpoint. It runs fully offline on one laptop, on permissively licensed, SBOM-tracked
dependencies.

**Evidence to date.** The Stokes inversion resolves a 40.4× separation between isotropic and
anisotropic response on a synthetic phantom with analytic ground truth — a phantom result, not an
ore result. Applied to public reflected-light data (LumenStone S3 v2; 29 sections, 116 000 pixels),
our geometry discriminator found neither harmonic above detection threshold — evidence that the
published "rotation sequences" are stage rotations, not analyser rotations. We report that negative
finding and route to a fourth-harmonic extinction estimator rather than force the convenient
inversion. We have also quantified the evaluation trap this domain invites: on synthetic data whose
only signal is section identity, patch-level splitting flatters error by a factor of 126 against an
honest locality-grouped split. All results run under 249 automated tests.

**Expected outcomes and impact.** Per-particle modal mineralogy and base-metal sulphide deportment
from reflected-light optics, carrying calibrated uncertainty and an explicit refusal mechanism,
feeding three operator-facing indices: fine-chromite entrainment risk, naturally-floating-gangue
load for depressant dosing, and stockpile oxidation. A ~R5 000 instrument is costed as a design;
no hardware is built, and no claim here depends on one.

**Falsifiability.** We hold a pre-registered null hypothesis: after controlling for Cr₂O₃ and
pyroxene fraction, texture carries no additional predictive signal. It is tested by nested model
comparison with cluster-robust inference grouped by locality and reported whichever way it
resolves; if it cannot be rejected, we will say so publicly and pivot to the oxidation index.

*Sources: public data only (LumenStone, IronOreRLM), IMA/COM reflectance reference data, and Craig
& Vaughan (open access, MSA). No proprietary Mintek data is used. AI coding assistants supported
implementation and drafting; the scientific direction and system design are the team's own,
evidenced in a continuous public commit history.*

---

## WORKING NOTES — NOT PART OF THE SUBMITTED PAGE

### Provenance of every number on the page

| Claim | Source | Rule-1 status |
|---|---|---|
| Chromite 50–75 vol% of UG2 | `CLAUDE.md` §The physics | CITED |
| 40.4× isotropic/anisotropic separation | `experiments/001-week1-gate/README.md:36` | MEASURED — **on a synthetic phantom**, and labelled as such on the page |
| 29 sections, 116 000 pixels, `NEITHER` verdict | Session-11 run of `experiments/002-s3v2-geometry/run.py` on the real `S3_v2.zip`; `docs/BUILDLOG.md` | MEASURED on real public data |
| MAE 0.0017 vs 0.2119, factor 126 | `reefprint.trust.split` measurement, `CLAUDE.md` rule 2 | MEASURED — **on synthetic patches**; page says "on synthetic data" |
| 249 automated tests | `uv run pytest -q -m "not placeholder"`, 2026-08-21 | MEASURED |
| ~R5 000 instrument | BOM only. ADR-0002. Page says "costed and specified as a design; no hardware is built" | DESIGN — never stated as existing |

Deliberately **excluded**: the 0.2–1.6 µm/pixel figure. It is a design target spanning a factor of
eight, nothing may be derived from it (ADR-0002), and an abstract is exactly where such a number
would get read as a specification.

### Why this reads as professional rather than student work

1. **It leads with the binding constraint, not the technology.** The first paragraph is
   metallurgy; the method does not appear until the second.
2. **It reports a negative result.** The `NEITHER` verdict on LumenStone S3 v2 is the single
   strongest credibility signal on the page. Teams that have never run anything real have no
   negative results to report.
3. **It names the silent-failure mode it engineered against.** Most submissions claim accuracy;
   this one identifies a way its own method could fail undetected, and states the guard.
4. **It cites its nearest prior art by name** rather than claiming novelty in a vacuum. Pirard,
   Lebichot & Krier (2007) is real prior art on polarised-light imaging; a judge may know it, and
   pre-empting that is worth more than the space it costs.
5. **It states what would falsify it.** Almost no hackathon abstract does this.
6. **Every number is bounded by its provenance in the sentence that carries it** — "a phantom
   result, not an ore result", "on synthetic data".

### Open decisions for the team before submission

1. **Team member names, disciplines and institution** — the header placeholder must be filled.
2. **Confirm "Team Sonar"** is the registered team name.
3. **Mentor** — the letter requires either your mentor's name and contact details, or an explicit
   request for a Mintek-assigned mentor. This is a separate submission item, not part of the page.
4. **Whether the R5 000 rig belongs on the page at all.** It is stated correctly as a design, but
   it invites the question "so you built nothing". Argument for keeping it: it shows the work is
   deployable and costed. Argument for cutting it: the software result is stronger without a
   hardware footnote competing for attention. Recommend keeping — it directly answers
   implementability, which the letter names as a criterion for vacation-work consideration.
5. **Voice pass.** The letter runs AI-generation checks. The ideas and every number here are the
   team's own, but the prose should be read aloud and adjusted by whoever presents, so the abstract
   and the ten-minute talk sound like the same people.

### Separate admin items from the letter (not the abstract)

Per team member: ID number · T-shirt size · contact details · mentor name and contact, or an
explicit request for a Mintek mentor. Conference registration for 2 October 2026 is also required
of all selected teams.
