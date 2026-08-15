# The REEFPRINT Gauntlet

A multi-round adversarial design review. Paste the prompt below into a fresh session with a strong reasoning model, attaching `reefprint-deployment-agents-training.md`, `umlilo-system-design.md` and `mintek-2026-build-spec.md`.

Run it once now. Run it again after Week 3. Run it a third time in the week before 1 October with the working system attached.

**How to use it:** it is designed to run in rounds with you in the loop. Do not let it produce all six rounds in one go on the first pass — the value is in Round 2 landing hard before Round 4 responds. If the model tries to sprint to the end, tell it to stop and complete the current round properly.

---

## THE PROMPT

```
You are running an adversarial design gauntlet on a competition build. Your job is
not to encourage me. Your job is to find every way this fails before a panel of
professional metallurgists, control engineers and technology-transfer officers finds
it for me on 1 October 2026.

Assume I can take it. Praise is worthless to me; a fatal flaw found today is worth
more than a compliment. If something in this design is genuinely strong, say so once,
in one sentence, and move on.

## CONTEXT

Competition: Mintek-SCi Grad Hackathon 2026. Mintek is South Africa's national
mineral research organisation. Challenge: Computer Vision for Real-Time
Mineralogical Characterisation. Team Sonar, University of the Witwatersrand:
three Computer Science students, one Electrical Engineering student, one Business
Informatics student with incomplete prior Metallurgical Engineering study. All with
data science and ML capability. Roughly 30 hours per person per week until
1 October. Build period: mid-August to 1 October 2026.

Hard constraints:
- Assume ZERO proprietary data from Mintek. Public sources only, plus paired
  samples we generate ourselves at Wits School of Geosciences.
- Self-funded. Hardware budget approximately R6,000. Free-tier compute only
  (Kaggle 30 hrs/week, Lightning AI student credits, Colab, Modal).
- Final: 13:00 submission, 14:00 presentations, TEN MINUTES per team, in person
  at Mintek Randburg. Five finalists announced 2 October, then originality
  authentication.

Judged on: Innovation & Creativity; Technical Feasibility; Impact and Value;
Originality (plagiarism, AI-generation, IP and originality checks); Clarity of
Presentation.

The design is in the attached documents. Read all of them before responding.

## THE CENTRAL CLAIM TO ATTACK

REEFPRINT infers economically decisive but physically invisible ore properties
(PGM deportment, liberation, processability) from visible macro-scale texture,
trained by distillation from high-resolution mineralogical maps, gated by
calibrated uncertainty so it refuses to act when it should not, and delivered as
a feedforward advisory into plant control 45 minutes ahead of the ore arriving.

UG2 PGM grains are under 10 microns; drill-core hyperspectral runs at 0.5–1.5 mm
per pixel. The entire project rests on inference across a 500–1500x resolution gap.
Attack that first and hardest.

## ROUNDS — complete each fully before moving to the next. Stop after each round
## and wait for me.

### ROUND 1 — STEELMAN
State the strongest possible version of this design in under 400 words, including
the single sharpest sentence that could open the pitch. If the design is weaker
than I think, the steelman will expose it by being hard to write. Say so if it is.

### ROUND 2 — THE PANEL ATTACKS
Adopt each persona fully and separately. Each gets its three most damaging
questions or objections, phrased as they would actually be asked in a room.
Be specific and technical. Generic criticism is failure.

1. MINTEK MINERALOGIST, 25 years on Bushveld ores. Attacks the physics, the
   stereology, the phase definitions, the resolution gap, and whether macro
   texture can carry any information about sub-10-micron sulphide deportment
   at all.
2. MEASUREMENT & CONTROL ENGINEER who built FloatStar installations. Attacks
   the integration, the transport-lag claim, closed-loop confounding, the
   safety boundary, and what happens at 3am when it is wrong.
3. ML RESEARCHER. Attacks leakage, the validity of the conformal guarantee
   under distribution shift, whether the paired sample count supports any claim
   at all, evaluation design, and whether the reported metrics can be gamed.
4. PLANT MANAGER. Attacks the economics, the assumptions behind the rand
   figures, payability, and whether the claimed benefit survives contact with
   an actual budget.
5. MOTT / IP OFFICER. Attacks originality, prior art, what is actually novel
   versus assembled, licence compatibility of every dependency, and whether
   anything here is ownable.
6. RIVAL TEAM. Attacks differentiation. What could a sharp team build in six
   weeks that beats this, and what is the cheapest way to make this look
   ordinary?
7. SCHEDULE REALIST. Attacks feasibility. Given five part-time students and
   seven weeks, which components will not exist on 1 October, and which
   failure cascades?

### ROUND 3 — TRIAGE
Sort every objection into: FATAL (invalidates the approach), STRUCTURAL (requires
redesign), FIXABLE (requires work), NOISE (can be answered in one sentence).
Be ruthless about what is actually fatal. If nothing is fatal, say so plainly and
explain why the fatal candidates fail.

### ROUND 4 — WHAT I AM NOT THINKING ABOUT
This is the most valuable round. Do not repeat Round 2.

- What has no one in this design considered at all?
- What assumption is so embedded that it has never been stated, let alone tested?
- What is the failure mode that only appears in week five?
- What would an expert find obvious and embarrassing that we have missed?
- What adjacent capability is nearly free given what we are already building,
  and would be conspicuous by its absence?
- What is the second-order consequence of the refusal mechanism that we have
  not reasoned through?
- What would make a judge distrust us, independent of technical merit?

Aim for at least ten items. Rank by expected damage.

### ROUND 5 — HARDEN
Redesign against everything FATAL and STRUCTURAL. Then attack the redesign with
the two personas most likely to defeat it. Do not defend the redesign; break it.

### ROUND 6 — OUTPUT
Produce:
(a) The hardened architecture: components, boundaries, data flow, what runs where.
(b) Tech stack with justification per layer — why THIS tool here and not the
    obvious alternative. Flag anything chosen for fashion rather than fit.
(c) The methodology: training regime, evaluation protocol, and the exact
    experiments that would falsify our central claim. If we cannot state what
    would prove us wrong, the claim is not scientific.
(d) A seven-week plan with weekly gates. Each gate is a binary pass/fail on
    evidence, not a feeling.
(e) A KILL LIST: what to cut, in order, when we fall behind. We will fall behind.
(f) The ten-minute presentation structure, minute by minute, and the three
    questions most likely to sink us with the answers rehearsed.
(g) Open questions we must resolve, ranked by how much they block.

## RULES

- Cite sources for factual claims about minerals, processing or standards. Say
  "unverified" where you cannot.
- Never invent a number. Flag every assumption explicitly as an assumption.
- Distinguish "hard because it needs work" from "hard because it may be
  impossible". Only the second matters right now.
- Where you disagree with the design, say so directly and give your alternative.
- Prefer specific over comprehensive. One precise objection beats five vague ones.
- Do not soften. Do not hedge to be agreeable. Do not end with encouragement.
- If you find yourself writing a compliment, delete it and find another flaw.

Begin with ROUND 1. Stop when it is complete.
```

---

## Running it well

**Feed it real artefacts as you go.** Round 1 in week 1 is theoretical. Re-run in week 3 with actual code, actual metrics and actual failures attached, and Round 4 gets dramatically sharper — a model reasoning over your real confusion matrix finds things it cannot find over a design document.

**Round 4 is the whole point.** Rounds 2 and 3 cover ground you can mostly anticipate. Round 4 is where the unknown unknowns live. If a run produces a weak Round 4, push back: *"that was the obvious set — go again, and this time tell me what only shows up in week five."*

**Keep a running defect log.** Every FATAL and STRUCTURAL finding gets an owner and a date. A gauntlet you do not act on is theatre.

**Run the personas separately if you want depth.** Paste only the Mineralogist section and let it go deep for a full session. Seven shallow attacks are worth less than one that goes three levels down.

**Do not let it design for you.** Round 5 will propose changes. Some will be improvements; some will be a model optimising for defensibility over ambition. You decide which. The gauntlet finds problems — it does not get a vote on the answer.
