# Meeting the challenge completely: clauses 2, 3 and 4

**Date:** 29 September 2026
**Status:** plan for Lethabo's review. Nothing here is built yet. Estimates are
planning guesses, not measurements.
**Companion to:** `PILOT-GAPS-2026-09-29.md` in this same PR. That document says
what we do not prove; this one says how to close each challenge clause, and
which part of the closing only a pilot can do.

The challenge, verbatim:

> Develop a computer vision or machine learning algorithm that analyses
> high-resolution imagery or sensor data (e.g., hyperspectral) to identify
> mineral phases in real-time, predicts the "processability" of the ore based on
> its visual or spectral characteristics, and integrates with existing sorting or
> flotation controls to provide immediate operational feedback.

Clause 1 (a CV/ML algorithm on high-resolution imagery) is met: DeepLabV3-ResNet50
on native-resolution 3396x2547 micrographs, reproduced 29 September (sha256
`de7135a9`). The other three are met at prototype level only.

**The honest summary:** before 1 October each clause can be met in full *as a
prototype*. Meeting clauses 3 and 4 in the real-world sense needs a site. That
is the pilot, and it should be presented as a specific next step, not as
"future work".

---

## Clause 2: identify mineral phases in real time

**Where we are.** One 512 px field: 4.7 s warm. A full section: 162.3 s mean,
195.7 s p95, on a CPU, from only n=3 whole-section runs
(`reports/segmentation_latency.json`, whose own note records unresolved
run-to-run variance). The single field's
recommendation disagrees with the full section's on **8 of 12** held-out
sections (entry 70). Section preparation is not included.

**Before the deadline:**

| Item | What it proves | Owner | Est. |
|---|---|---|---|
| Time full-section inference on the Kaggle T4 | A measured GPU figure next to the CPU one. No GPU number may be quoted until this exists. | Lethabo (Kaggle already works) | ~1 h |
| Define "real time" on the slide as *the algorithm analyses an image in seconds* | The clause concerns analysing imagery. Preparation is upstream of the algorithm. | Both, wording | minutes |
| *Optional:* multi-field mode. Sample several fields across the section and show each result as it arrives. | Fixes single-field unrepresentativeness while staying fast. The number of fields must be chosen on validation sections, never the 12 test sections. | Sibusiso | ~2-3 h, riskier |

**Only a pilot completes it:** measured time from sample to answer at a real
lab, stage by stage (see `PILOT-GAPS` gap 3).

## Clause 3: predict the ore's processability

**Where we are.** A proxy, never validated against processing outcomes: modal
mineralogy plus an *apparent 2D sulphide association index*, turned into an
advisory. `src/advisor.py` marks **three of its four thresholds "UNSOURCED
placeholder"**: `PAYLOAD_FLOOR = 0.003`, `REJECT_CEILING = 0.60`,
`DELETERIOUS_CEILING = 0.05`. Only `LOW_LIBERATION = 0.50` is sourced.

**Before the deadline:**

| Item | What it proves | Owner | Est. |
|---|---|---|---|
| Show processability as a named quantity with its uncertainty: "apparent sulphide liberation 74% ± 33.5%" plus a category, not only an advice string | The output *is* a prediction with stated error. ±33.5% is the existing `LIBERATION_MARGIN`. It is wide, and showing it is the point. | Sibusiso | ~1 h |
| Make the three unsourced thresholds **site-configurable parameters set by the site metallurgist**, shown on screen as such | Turns an honest weakness into correct deployment design: payload floors and reject ceilings are ore- and plant-specific. | Sibusiso | ~1 h |
| Add REEFPRINT's fine-chromite entrainment-risk head as a second processability output, if it is in the talk | Two processability measures from two halves, through the existing seam | Lethabo | ? |

**Only a pilot completes it:** compare predicted liberation with *measured*
liberation (automated mineralogy on the same sections) and with flotation test
recovery. It cannot be done from public data: the repository already records
that no public texture-plus-chemistry dataset exists for UG2.

## Clause 4: integrate with existing sorting or flotation controls

**Where we are.** Since PR #6, a real local OPC UA exchange drives one simulated
tag (`regrind_enabled`). It holds on abstention and refuses stale commands. The
only client that has ever read it is our own. Reagent advice is display-only.

**Before the deadline:**

| Item | What it proves | Owner | Est. |
|---|---|---|---|
| A **third-party, vendor-neutral OPC UA client** (e.g. UaExpert) reads the advisory node live and sees hold/refuse | It plugs into tools other than ours: the cheapest real evidence for "existing controls". Needs a download, which Sibusiso has to approve. | Either | ~1 h |
| Publish the advice as an **operator-facing tag** (text plus state) a control-room display could show | "Immediate operational feedback" in practice means feedback to operators, not autonomous actuation | Sibusiso | ~1 h |
| Say *"cleaner regrind in the flotation circuit"* | Makes the flotation link explicit | Both, wording | minutes |

**Only a pilot completes it:** a shadow run on a site control network. It writes
advisories to a display tag, operators approve every action, and nothing
actuates automatically. At Mintek the obvious question is whether this could
feed **FloatStar**, Mintek's own flotation control product (evidence register
E3). Ask it at the pitch; do not claim it. We do not know what interfaces
FloatStar exposes.

---

## Proposed order for the remaining time

1. **Deck, backup video, timed rehearsal.** Nothing below matters if the talk
   does not land.
2. Clause 3: named output with uncertainty, and site-configurable thresholds.
3. Clause 4: operator-facing tag; third-party client if the download is approved.
4. Clause 2: GPU timing (Lethabo, Kaggle).
5. Multi-field mode only if all of the above is done.

Each code item goes on its own branch as a PR for review, as #6 did.

## Questions for Lethabo

1. Do you agree with this split between *before deadline* and *pilot only*? Is
   anything in the second column really achievable now, or anything in the
   first too risky?
2. Can you run the full-section GPU timing on Kaggle? It is the one clause-2
   number we cannot produce on this laptop.
3. Is REEFPRINT's fine-chromite entrainment head ready to appear as a second
   processability output, and through which seam?
4. Site-configurable thresholds: do they belong in KHANYA's advisor, or should
   they live in a shared config both halves read?
5. Is the FloatStar question the right one to put to the judges, or is there a
   better-known flotation control integration target we should name?
