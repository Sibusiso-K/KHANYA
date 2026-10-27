# Founder's rebuttal to "Can 2D Optical AI Control Flotation?"

Sibusiso Khumalo, co-founder, Team Sonar (REEFPRINT/KHANYA). 27 October 2026.

Written in reply to the second NotebookLM debate. I accept the criticism that
is right, and I push back where the debate misread the build, misquoted our
numbers or misread the yardstick. Figures are from `STATUS.md`,
`reports/ADVERSARIAL-CRITIQUE-2026-09-15.md` and Moodley et al. (2026) unless
another source is named.

---

## 1. What I concede, without qualification

**The conformal band is leaked.** We calibrated the 0.335 margin by
leave-one-out over the same 12 sections we then report results on. Our own
critique (§1.4) says so. From today we stop calling it a coverage guarantee.
It is a calibration on 12 sections, and it means nothing for unseen ore until
we calibrate and test on different samples.

**The band is too wide to be useful yet.** Around a 50% floor, ±0.335 spans
16.5% to 83.5%. On our 12 sections the system flagged six as "marginal, verify"
under the current band. Half the time it declines to advise. That is honest,
but it is not yet valuable.

**The 50% binary rule is too crude.** A particle is "liberated" if payload is
at least half of it. We will replace it with Moodley's five exposure classes:
locked, low middlings, high middlings, liberated, fully liberated.

**Twelve test images is not an evidence base.** Nothing we have is trained on
South African ore. LumenStone S2 is Norilsk ore with 62.8% base-metal sulphide
pixels; UG2 has under 1 vol%. We call it an assemblage analogue, not an
abundance analogue, and that distinction has to carry the whole claim.

---

## 2. Where the debate got the build wrong

**"Control flotation."** KHANYA does not control anything. It is advisory: it
runs read-only in shadow mode, its advice expires, the operator approves every
change, and the decision log is signed. The debate's title asks a question
we have never claimed to answer yes to.

**"33% of recommendations flipped at different resolutions."** That number is
on our own list of figures that must never be quoted (`STATUS.md` §6). It was
measured at 512×688, where the particle-size cut-off means a different grain
size. The honest figure is **50% at native resolution**, and flips are
disagreements between our recommendation and the ground-truth recommendation,
not between resolutions. The point the debate wanted still holds, and it is
stronger with the right number: the corrected band turned every unsafe
disagreement into a flagged one, **0 unsafe flips**, on both models.

**"A margin of 0.335 or 0.089."** 0.089 was retired after we found it covered
only 67% (S2) and 45% (S1) of sections. Only 0.335 is current.

**"We can see the platinum."** We never claimed it. PGM grains are mostly
below what reflected light resolves. KHANYA measures the **carriers**: the
base-metal sulphides, chromite and silicates, and how they are associated.
Linking carriers to PGM behaviour per orebody takes SEM mode-of-occurrence
data, which is what Mintek's characterisation work provides.

---

## 3. Where the debate misread the yardstick

**QEMSCAN is not 3D.** Both debates called it a 3D assessment. QEMSCAN maps
2D polished sections. Moodley's free-surface exposure classes come from 2D
sections too. So the real gap is not "2D proxy against 3D kinetics". It is
**optical against electron-beam measurement of the same 2D section**. That is a
narrower gap, and a testable one: image the same blocks both ways and compare
class by class. The true 3D route, X-ray micro-CT, applies to QEMSCAN and to us
equally (Reyes et al. 2017; Guntoro et al. 2021).

**Moodley is not a straitjacket.** The debate said 16 measurements against 15
parameters leaves "nowhere to hide". Moodley says the opposite: one degree of
freedom leaves the fit only weakly overdetermined, several parameters sat on
their bounds, and the parameter vector is not unique. What Moodley showed is
that the **outputs** were stable even though the parameters were not. That is
the standard I accept for us: show our *recommendations* are stable under
perturbation, not that every internal number is unique.

**The recovery stability figure was overstated.** The debate said Moodley's
recovery moved less than 0.5 percentage points across all checks. That holds
for the individual sulphide contributions. Total Cu recovery moved by up to
0.686 pp under ±25% weighting, and the residual contribution by up to 0.830 pp
across the 88 near-equivalent fits (Table 11, Fig. 10).

**We are not a competitor to Moodley's method. We are its missing input.**
Moodley's framework needs feed liberation classes from QEMSCAN, which takes
days and costs a lab run. Its own conclusion asks for more data across more
ores and conditions. KHANYA's job is to estimate those feed classes in minutes
from a polished section, so the framework could run every shift instead of
once per campaign. The right test is not "does KHANYA match Moodley's
kinetics?" It is "does KHANYA reproduce QEMSCAN's feed classes on the same
blocks, closely enough that Moodley's recovery estimates do not change?"

---

## 4. Where I accept the physics and add the plan

**Fines.** Moodley's copper ore had 53.75% of its Cu below 20 µm (Table 7).
That is copper, not UG2, but the warning stands: optical boundaries blur at
fine sizes. We will report results by size class and refuse to advise when
fines dominate the section.

**Entrainment.** We will not borrow a copper entrainment term for UG2. That is
a question for Mintek's characterisation cluster, and it is the first question
we will ask them.

---

## 5. What the debate left out: the wider literature

Both debates judged us against one copper-ore paper. The wider literature
changes the plan (`reports/LITERATURE-ROADMAP-2026-10-27.md`):

- **Labels from the same blocks.** A U-Net has been trained on optical images
  with QEMSCAN maps as targets (arXiv 2505.17008). That is our route out of
  the 12-image problem: paired optical and QEMSCAN images of UG2 blocks.
- **Generalising to new ore.** A 2026 Liège thesis (Campo) found zero-shot
  Segment Anything comparable to a trained DeepLabV3+ on reflected-light ore
  and better across datasets, where DeepLabV3+ degraded badly. We use
  DeepLabV3. That is a direct, testable upgrade.
- **Machine learning on PGM floatability already works on SEM data.** Kabemba
  et al. (2026, Canadian Metallurgical Quarterly) report a random forest
  classifying Platreef floatability classes from MLA/QEMSCAN descriptors at
  98.13% accuracy (abstract only; not yet read in full). Pereira et al. (2020,
  Minerals Engineering) fit flotation kinetics to single particles from
  automated mineralogy. Our contribution is speed: feeding that kind of model
  from optics.
- **Uncertainty under drift.** Adaptive conformal prediction has been tested
  on a full-scale plant soft sensor under process drift (Lee and Lee 2026).
  That is how the band should behave in a plant.
- **Chromite.** UG2 concentrates carry about 3% Cr₂O₃, which causes smelter
  problems (Maharaj, UKZN thesis). Chromite liberation is visible in reflected
  light. A "Cr₂O₃ at risk" signal may be our most valuable first output.

---

## 6. My position

KHANYA is not ready to advise a plant, and I am not asking anyone to let it.
I am asking for a three-month, R210,000 feasibility stage on one host's ore,
with gates, to answer one question: **can optics reproduce QEMSCAN's
liberation classes on UG2 closely enough to feed a Moodley-style recovery
model?** If the answer is no, the gate stops the spending. If it is yes,
concentrators get process mineralogy every shift instead of every campaign.

The questions I want the next debate to answer:

1. Is "optical against SEM on the same 2D section" the right framing, rather
   than "2D against 3D"?
2. Is "reproduce QEMSCAN's feed classes" the right pass/fail test for the
   feasibility stage? What tolerance should it use?
3. Is chromite liberation a better first product than base-metal sulphide
   liberation for UG2?
4. Should we switch from DeepLabV3 to a foundation-model approach before or
   after we have paired UG2 data?
5. What would make Mintek's characterisation cluster want to co-author the
   first UG2 study?
