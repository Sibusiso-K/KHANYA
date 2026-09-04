# Why KHANYA matters to Mintek specifically

Researched 2026-08-17. Sources listed at the end. This file exists because our
original value proposition — "cheap optical rig instead of a multi-million-rand
automated mineralogy instrument" — is **the wrong pitch to make to Mintek**, and
we need to know that before 30 August rather than on stage.

---

## 1. The problem with our current framing

**Mintek already owns the expensive instrument.** Their Mineralogy Division hosts
QEMSCAN, plus XRD, SEM-EDS, EPMA and micro-XRF. They are not a customer priced
out of automated mineralogy — they *are* the national provider of it, and they
publish PGM ore and concentrate characterisation as a service.

So "we can replace QEMSCAN cheaply" lands badly in two ways. It tells the room
we have not researched who they are, and it positions us against the capability
they have spent decades building. Every version of the pitch that opens on
instrument cost has this problem.

## 2. The framing that actually fits

Mintek sits inside a specific organisational structure and mandate:

- **Mineral Processing and Characterisation Cluster**, three divisions: Mineral
  Processing, Analytical Chemistry, and Mineralogy.
- **Mineral Processing Division** covers pre-concentration for PGMs, gold, iron
  ore, **chrome**, uranium, titanium, industrial minerals, base metals and rare
  earths — i.e. the African commodity set.
- Stated strategy, per mineral processing executive manager **Dr Lawrence
  Bbosa**: move Africa away from raw ore exports toward **localised
  beneficiation**, with South Africa's Critical Minerals and Metals Strategy as
  the roadmap.
- **The flotation group is explicitly targeting recognition as a global centre of
  excellence in flotation research** (PGM Industry Day, July 2026).
- Mintek's own R&D voice on technology direction (**Dr Khuthadzo Mudzanani**,
  August 2026): the current impact is coming from automation, data analytics,
  remote monitoring and sensor-based technologies, and AI, machine learning,
  digital twins and **advanced process control** will reshape mineral processing.

Read against that, KHANYA is not a cheaper instrument. It is **an advanced
process-control input for flotation circuits**, which is the intersection of two
things Mintek has publicly committed to.

## 3. Five concrete value propositions, strongest first

### 3.1 QEMSCAN triage — spend the scarce resource on the right samples

Automated mineralogy is a **queued, capacity-limited** resource: sample
preparation, instrument time, interpretation, reporting. KHANYA runs on a
reflected-light microscope that any metallurgical lab already owns, in seconds.

The proposition is not replacement, it is **routing**. Screen everything
optically; send to QEMSCAN the samples where the optical result is uncertain,
anomalous, or economically consequential. Our uncertainty band is exactly the
mechanism for this — the system already declines to guess when a measurement
falls within its own error of a decision threshold, and "verify" is precisely the
signal that should trigger instrument time.

This turns our **honesty into throughput**. A system that knows when it does not
know is a triage system; a system that always answers confidently is not.

**Quantified** (added 2026-09-04 — ENDGAME §4 W6, Impact is our lowest-scored
judging criterion and the cheapest to move with a real number instead of an
adjective).

On the 12 held-out S2 test sections — patches model, topology-refined, the
validated pipeline (report §5.0.9) — the deployed recommendation is:

| Recommendation | Sections |
|---|---|
| Continue / Grind finer (confident, actionable) | 6 of 12 |
| Marginal — verify before acting (triage signal) | **6 of 12** |

Source: `reports/decision_gap_patches_refined.json`. **Honest bound on that
50%:** at n=12 the 95% Clopper-Pearson interval is [21%, 79%] — wide, because
12 held-out sections is a small sample. State the interval on stage if asked,
not the point estimate alone.

**What that would mean, if QEMSCAN carried every sample today.** One lab's
published price list (Saskatchewan Research Council, Advanced Microanalysis
Centre, April 2017 — see Sources) lists $1,500/sample for the QEMSCAN service
closest to what our advisor measures: *"modal mineralogy; customizable
liberation criteria, mineral associations and predicted recovery."* Sample
prep ($800 crush/grind/sieve + $150 block mount) is common to both optical and
SEM workflows and is not part of the comparison — the $1,500 is the analysis
step our routing would avoid for the confidently-answered half. ALS Global's
own mineralogy FAQ states turnaround is "not an overnight assay service,"
workload-dependent, with a 1-week *expedited* option available "with the
requisite communication/organisation. Surcharges may apply" — implying
standard turnaround already exceeds a week before anyone pays to jump the
queue.

**The claim, stated at the precision the evidence supports:** on this
held-out set, roughly half of sections got a confident answer from a
reflected-light microscope in seconds, with no queue and no per-sample fee;
the other half were correctly flagged for the instrument that should see
them. That is a **triage mechanism with a measured operating point**, not
"AI makes QEMSCAN faster" — and it is honest about being measured on S2
(Norilsk BMS analogue), at n=12, not on UG2 or at Mintek's own prices.

**What we have not shown, and must say if asked:** we have not validated that
our "verify" flags agree with what a human mineralogist or QEMSCAN itself
would flag as uncertain — that would need real QEMSCAN results run against
the same sections, which we do not have (DATA-SOURCES.md §1). The claim is
that the *mechanism* — abstain near a calibrated threshold — is the right
shape for triage, evidenced by it costing zero unsafe and zero conservative
errors under the corrected band. It is not yet a claim that our specific 50%
is the economically optimal cut.

Sources for the numbers above:
- Saskatchewan Research Council, Advanced Microanalysis Centre, QEMSCAN®
  Analysis price list, April 2017:
  https://www.src.sk.ca/sites/default/files/files/resource/QEMSCAN_Apr17.pdf
- ALS Global, Mineralogy (metallurgy and mineral processing), turnaround-time
  FAQ: https://www.alsglobal.com/en/metallurgy-and-mineral-processing/mineralogy

### 3.2 Plant-side deployment — where QEMSCAN cannot go

Mintek's clients are concentrators. Those plants cannot each host a QEMSCAN, and
a laboratory turnaround cannot reach the ore that generated the sample before it
has been processed. KHANYA is deployable at the plant on hardware already
present.

This maps directly onto Mintek's **beneficiation and localisation** mandate: a
capability that works at every plant rather than at one central laboratory is
what "localised mineral processing" means in practice.

### 3.3 Complementary physics, not competing physics

BSE contrast is a function of mean atomic number, so it separates phases by
composition and struggles where composition is near-identical — the
hematite/magnetite case. Reflected light responds to reflectance, colour and
anisotropy, which track structure and bonding.

This makes optical **additive to** QEMSCAN rather than a subset of it. LumenStone
S3 contains magnetite and hematite together, so this is testable rather than
merely assertable — see the note in DATA-SOURCES.md section 0b(i).

### 3.4 Mintek holds the labels — and this is also our data ask

This is the highest-leverage item and it runs in both directions.

Supervised optical mineralogy needs pixel-labelled reflected-light images. **A
QEMSCAN map of the same polished section is exactly that label.** Mintek is
therefore one of very few organisations on the continent that can generate
training data for this problem at scale, from work they already perform.

For Mintek the value is a compounding asset: every characterisation job they run
could also produce labelled optical training data, turning a service output into
a data moat for African ore types that no public dataset covers. For us it is the
single thing that would close our largest gap — we currently have **no South
African ore imagery at all**, and four of REEFPRINT's five target phases have no
data.

**This is the specific thing to ask for in the 30 August mentor request.** Not
"can we have some images" but "can QEMSCAN maps of polished sections be used as
segmentation labels for optical images of the same sections".

### 3.5 Flotation decisions, which is their stated ambition

KHANYA's outputs are flotation-circuit decisions: grind finer for liberation,
adjust depressant dosage for a reject or deleterious phase, continue at setpoint,
or verify. The advisor reasons over metallurgical **roles** rather than mineral
names, so retargeting from one ore to another is a mapping change rather than a
rewrite.

Given the flotation group's centre-of-excellence ambition, a tool that closes the
loop from mineralogy to flotation setpoint is aligned with where they have said
they are going.

## 4. Commodity relevance — what we can honestly claim

| Mintek commodity area | Our evidence | Strength |
|---|---|---|
| PGMs / base metals | LumenStone S2 — Norilsk Ni-Cu-PGE magmatic sulphide, layered ultramafic, same BMS assemblage as UG2/Merensky | **Assemblage analogue.** Not an abundance analogue — 62.8% BMS vs <1 vol% in UG2 |
| Base metals (Cu-Pb-Zn) | LumenStone S1 — Berezovskoe polymetallic, 7 phases | Direct, different ore genesis |
| Iron ore | FeM — itabiritic iron ore, binary ore/resin | Weak; binary only |
| Chrome (chromite) | **None** | No data |
| Gold, uranium, titanium, REE | **None** | No data |

So we can defensibly claim: the method works on two independent ore genesis
types, in the commodity families Mintek serves, with a documented and diagnosed
failure mode. We cannot claim chromite, and therefore cannot claim UG2 grade
estimation. Say so plainly.

## 5. The honest positioning statement

> Mintek already has the best mineralogy instruments in the country. What it does
> not have is a way to put mineralogical decision support inside every
> concentrator, or a way to decide which samples deserve instrument time. KHANYA
> is a reflected-light screening and process-control layer that does both, and
> that gets better every time Mintek runs a QEMSCAN job — because that job can
> label optical images. Our contribution is not a cheaper microscope. It is the
> measurement of whether a mineralogical model is accurate enough to act on,
> which we found is not the same question as whether it is accurate.

## 6. What this changes in our own work

1. **Reframe the report's section 3 cost argument.** Keep the physics
   (BSE cannot separate hematite from magnetite), drop the implication that
   instrument cost is the point. The point is deployment location and turnaround.
2. **The mentor request becomes a QEMSCAN-labelling request**, which is far more
   specific and more valuable than asking for images.
3. **Lead the 10-minute pitch on triage and process control**, not on cost.
4. **Test the hematite/magnetite claim on S3** rather than asserting it, since it
   is now load-bearing for the complementarity argument.

---

## Sources

- Mintek, Mineral Processing and Characterisation Cluster and divisions:
  https://mintek.co.za/clusters/divisions/ and
  https://mintek.co.za/clusters/divisions/minerals-processing.html
- Mintek Mineralogy Division instrumentation (QEMSCAN, XRD, SEM-EDS, EPMA,
  micro-XRF) — division pages above.
- "Mintek targeting global flotation research recognition, PGM Industry Day
  hears", Engineering News, 2026-07-14:
  https://www.engineeringnews.co.za/article/mintek-targeting-global-flotation-research-recognition-pgm-industry-day-hears-2026-07-14
- "Forward-looking critical minerals strategy must drive African beneficiation"
  (Dr Lawrence Bbosa), Engineering News, 2026-06-05:
  https://www.engineeringnews.co.za/article/forward-looking-critical-minerals-strategy-must-drive-african-beneficiation-2026-06-05
- "Women in tech: shaping the intelligent mine" (Dr Khuthadzo Mudzanani, Mintek
  R&D), African Mining, 2026-08-01:
  https://www.africanmining.co.za/2026/08/01/women-in-tech-shaping-the-intelligent-mine/
- "Expanding Africa's footprint through science and partnerships", African
  Mining, 2026-05-25:
  https://www.africanmining.co.za/2026/05/25/expanding-africas-footprint-through-science-and-partnerships/
- QEMSCAN capability description, UCT Centre for Minerals Research:
  https://ebe.uct.ac.za/minerals-research/research-areas-process-mineralogy/qemscan
- Saskatchewan Research Council, Advanced Microanalysis Centre, QEMSCAN®
  Analysis price list (§3.1 quantified triage argument), April 2017:
  https://www.src.sk.ca/sites/default/files/files/resource/QEMSCAN_Apr17.pdf
- ALS Global, Mineralogy turnaround-time FAQ (§3.1):
  https://www.alsglobal.com/en/metallurgy-and-mineral-processing/mineralogy

**Searched and not found:** any open-access image dataset of Bushveld, UG2,
Merensky or Platreef material suitable for supervised segmentation. Published
work on UG2 PGM and BMS mineralogy exists (SEM-EDS-based image analysis in
*Mineralium Deposita*), but as papers rather than released datasets. This
reinforces section 3.4 — the data does not exist publicly, which is precisely why
Mintek's own archive is the asset.
