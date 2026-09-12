# ADR-0005 — The illumination is unpolarised, not crossed polars

- **Date:** 2026-09-12
- **Status:** Accepted
- **Decider:** Lethabo Hoaeane (single technical decision-maker, CLAUDE.md)
- **Relates to:** CLAUDE.md §The physics · `WORKBOARD.md` §0 C3 and §4 D2 ·
  `docs/BUILDLOG.md` session 18 · `khanya/main:reports/TECHNICAL-REVIEW-2026-09-12.md` finding 5 ·
  ADR-0002 (no instrument is built) · ADR-0004

## Context

The external review of 12 September raised a physics objection against the sentence that carries
the whole polarimetric claim. The objection is correct as written, and the repository has been
carrying an inconsistency that inverts its own headline discriminator.

**What the documents said.** `src/reefprint/polarim/stokes.py` stated *"under crossed polars an
isotropic phase shows no modulation as the analyser turns"*, and CLAUDE.md's geometry table
described the rotating-analyser arrangement as *"analyser, with polariser and specimen fixed"*.
Both name an arrangement in which linearly polarised light illuminates the specimen.

**Why that is false.** At normal incidence an isotropic medium has `r_s = r_p`, so its Jones matrix
is `r·I` and reflection preserves the linear polarisation azimuth. Incident linear light returns
linear light at the same azimuth, giving

    (S0, S1, S2) = (I₀, I₀, 0),    DOLP = 1,    I(θ) = ½I₀(1 + cos 2θ) = I₀cos²θ

which is *full* modulation, not none. An isotropic grain under a fixed polariser goes dark at
exactly one analyser angle — the crossed position — and it is the same angle for every isotropic
grain on the section. The observation that *an isotropic grain stays dark through a full rotation*
belongs to **specimen rotation between fixed crossed polars**, which is the other geometry
entirely, and conflating the two is the exact error CLAUDE.md's own geometry table exists to
prevent. The repository made it in the sentence describing that table.

**What the code actually implements.** `src/reefprint/acquire/phantom.py` sets
`magnitude = anisotropy × reflectance_pct` and `s1 = magnitude·cos(2·aolp)`, so `DOLP = anisotropy`,
with `anisotropy = 0.0` for every cubic phase. That is the forward model for **unpolarised incident
light**, where polarisation is *generated on reflection* by differential reflectance between the
grain's eigen-axes:

| Incident | Grain | Reflected | DOLP |
|---|---|---|---|
| unpolarised | isotropic (`r₁ = r₂`) | unpolarised | **0** — no modulation |
| unpolarised | anisotropic (`r₁ ≠ r₂`) | partially linearly polarised along the eigen-axes | **(\|r₁\|²−\|r₂\|²)/(\|r₁\|²+\|r₂\|²)** = bireflectance contrast |

Both models are correct physics. They describe different instruments, and the repository was
documenting one while computing the other.

**Two independent corroborations that unpolarised is the intended model.** CLAUDE.md's own scaling
argument — that analyser modulation goes as bireflectance `a` while extinction depth goes as `a²`,
so the rotating analyser's advantage is `2/a` and *grows as the anisotropy weakens* — holds only
under the unpolarised model; under a fixed polariser the isotropic baseline is DOLP 1 and the
argument does not run. And the phantom's numbers are internally consistent with it throughout, in
both the analyser and the stage generators.

## Decision

**The illumination is unpolarised (or depolarised) incident light with a rotating analyser. It is
not crossed polars, and no polariser sits in the illumination path.**

The forward model in `reefprint.acquire.phantom` and the inversion in `reefprint.polarim.stokes`
are correct and do not change. What changes is every sentence that described them, plus a test that
prevents the wrong reading returning.

Consequently:

1. `src/reefprint/polarim/stokes.py`'s module docstring is rewritten to state the arrangement
   explicitly and to give the isotropic counterexample by name.
2. CLAUDE.md §The physics, CONTEXT.md §2 and the abstract's wording drop *"crossed polars"* and
   *"stays dark through a full analyser rotation"* wherever they describe **our** measurement. The
   phrase remains correct — and stays — where it describes the *classical stage-rotation*
   observation, which is the other row of the geometry table.
3. `tests/test_polarim.py::test_an_isotropic_grain_under_a_fixed_polariser_modulates_fully` pins
   the counterexample, so the false sentence cannot be reintroduced without a red test.
4. The instrument BOM's *"salvaged LCD polarisers"* (plural) is reconciled to one analyser plus a
   depolarising element. Under ADR-0002 nothing is built, so this is a correction to a design, not
   to hardware.

## What this decision does NOT do

- **It does not rescue the mineralogical interpretation.** The review's deeper point stands and
  must be said on stage: the phantom validates *recovery of the parameters we supplied it*; it does
  **not** validate the mapping from crystal symmetry to those parameters. Leg (a)'s 40.4× is a
  statement about the inversion, never about real ore.
- **It does not make the polarimetric claim validated on real data.** Leg (b) has still never been
  run — see ADR-0004.
- **It does not change the geometry guard.** `RotationGeometry` still defaults to `UNKNOWN`, and
  `require_analyser_rotation()` is still mandatory before any Stokes inversion. The 2θ/4φ
  distinction this ADR clarifies is orthogonal to the stage-vs-analyser distinction that guard
  enforces, and both remain live.

## Consequences

**The honest framing improves the talk rather than damaging it.** *We wrote down the wrong
instrument in our own specification, an external reviewer caught it, we checked our code and found
the model was right and the words were wrong, and we added the counterexample as a test.* That is
rule 10 working in public.

**One question a Mintek judge asks early now has an answer.** *"How is your illumination
polarised?"* was previously answerable two contradictory ways depending on which file was open.

**A named risk is reduced.** The narrow claim — per-pixel full linear Stokes recovery from a
rotating-analyser series — is *further* from Pirard, Lebichot & Krier (2007), which uses a single
fixed polariser for grain-boundary contrast. Finding N1 is unchanged in substance: the full paper
is still unread and still needed before week 6.

## Alternatives rejected

**Flag it and decide later.** Rejected: the abstract and the talk carry the wrong sentence today,
and the fix is roughly half a day against a question a judge asks in the first two minutes.

**Keep the crossed-polars wording and change the phantom to match.** Rejected: it rewrites the
forward model, the phantom, leg (a)'s gate result and the bridge at T-19, to arrive at a
discriminator (azimuth-and-ellipticity rather than DOLP magnitude) that is no stronger and is
closer to the published prior art.
