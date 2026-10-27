# Debate 2 analysis: "Can 2D Optical AI Control Flotation?"

NotebookLM debate, 18 min 15 s, transcribed locally with Whisper (`small.en`)
on 27 October 2026. Transcript: `notebooklm/transcripts/02-Can_2D_Optical_AI_Control_Flotation.txt`.
Each claim below was checked against `STATUS.md`,
`reports/ADVERSARIAL-CRITIQUE-2026-09-15.md` and Moodley et al. (2026).

## The two positions

- **For:** KHANYA is a defensible stepping stone. Its advisor reasons over
  metallurgical roles (payload, gangue, reject), not mineral names, so moving
  to Bushveld ore means changing a mapping, not the logic. It measures
  recommendation flips, not just pixel accuracy, and it discloses its failures.
- **Against:** stereological bias, unrepresentative training data and no
  physical kinetic link make it unsafe for a pilot without a redesign.
- **Where they converged:** the software foundation is real, but a 2D proxy is
  not 3D kinetics. Fix three things before asking for money.

## What this debate added beyond the first one

1. **Conformal band leakage, stated plainly.** The 0.335 band was derived by
   leave-one-out over the same 12 test sections used for evaluation. This is
   **correct** and is in the critique (§1.4). It is the sharpest new point.
2. **The width of the band.** The critique says that around a 0.50 floor, 0.335
   spans 16.5% to 83.5%, so the system abstains on half the sections and that
   abstention was "rebranded" as caution. **Correct** (critique §1.4, §2.2).
3. **The binary 50% threshold.** A particle counts as liberated when payload is
   at least 50% of it. **Correct** (`STATUS.md` line 160). The debate's fix,
   moving to Moodley's five exposure classes, is the right one.
4. **The team already states the direction of the bias.** `STATUS.md` says 2D
   liberation is biased high, so the index is a safe bound for "grind finer"
   and unsafe for "continue". **Correct** (`STATUS.md` §5, line 335). The
   "against" host's reply is fair: stating a bias is not correcting it.
5. **Role-based advisor.** A genuine strength the first debate missed.
6. **The question to ask Moodley's group:** "How do we parameterise your
   empirical entrainment term for UG2 fines, where our optical mapping fails?"
   Good, and worth using.

## Errors to correct

| Claim in the debate | What the sources say |
|---|---|
| "33% of recommendations flipped when evaluated at different resolutions" | `STATUS.md` §6 lists 33% under **numbers that must never be quoted**. It was measured at 512×688, where the particle-size cut-off means a different grain size. The correct figure is **50% at native resolution**. Flips are disagreements between predicted and ground-truth recommendations, not between resolutions. |
| "A statistical margin of 0.335 or 0.089" | 0.089 is **superseded**. It covered only 67% (S2) and 45% (S1) of sections. Quote 0.335 only (`STATUS.md` §5e, §6). |
| Moodley's "maximum recovery change across all of that was less than 0.5 percentage points" | Not quite. The ±25% weighting check changed the bornite contribution by up to 0.440 pp and total Cu recovery by up to **0.686 pp**. Across the 88 near-equivalent fits, the residual contribution varied by up to **0.830 pp** (Moodley Table 11, Fig. 10). Under 0.5 pp holds only for the individual sulphide contributions. |
| "A 3D QEMSCAN assessment" | QEMSCAN maps **2D** polished sections. It has stereological bias too. The 3D route is X-ray micro-CT (Reyes et al. 2017; Guntoro et al. 2021). |
| "The Minerals 2017 paper: 2D cross-sections consistently overestimate true 3D liberation" | The 2017 paper (Ueda, Oki and Koyanaka) compares seven texture indices for *correcting* 2D liberation. 2D sections tend to overstate the extreme classes (fully liberated and fully locked) and understate middlings. "Consistently overestimate" is too blunt. Check the paper before quoting. |
| "Moodley's 16 measurements constrain 15 parameters, so the numbers have nowhere to hide" | Moodley warns the opposite: one degree of freedom leaves the fit only weakly overdetermined. Several parameters hit their bounds, and the parameter vector is **not unique**. What is stable is the outputs, not the parameters. |
| "Lathabo", "Cebu Siso", "Konya", "Norrall's" | Transcription and speech slips for Lethabo, Sibusiso, KHANYA and Norilsk. |

Correct, and worth keeping: LumenStone S2 is Norilsk ore with 62.8% base-metal
sulphide pixels against under 1 vol% in UG2 (`STATUS.md` §0); 12 test images
(critique §2.5); hardness R² fell from 0.479 to 0.25; and Moodley's ore had
53.75% of its Cu below 20 µm (Table 7).

## The verdict, compared with the first debate

| | Debate 1 | Debate 2 |
|---|---|---|
| Main new insight | Fines and stereology | Conformal leakage; role-based advisor |
| Biggest error | "QEMSCAN is 3D"; R13m pilot called the feasibility stage | Quoting the banned 33% flip rate and the superseded 0.089 band |
| Literature beyond Moodley | None | One mention (Minerals 2017) |
| Shared blind spot | Neither uses the wider literature in `reports/LITERATURE-ROADMAP-2026-10-27.md`: correlative SEM labels, foundation models, adaptive conformal, X-ray CT, chromite. |

## Actions for the team

1. **Recalibrate the conformal band on held-out data that is not the test set.**
   With 12 sections you cannot do both. You need more labelled sections, which
   is the case for correlative optical-to-QEMSCAN labels on UG2 blocks.
2. **Replace the 50% binary rule with Moodley's five exposure classes.** Then
   convert them to recovery at risk.
3. **Apply a published 2D-to-3D correction, and say which one.** Calibrate it on
   a few X-ray CT samples per orebody.
4. **Add size-resolved reporting and a fines refusal rule.**
5. **Keep leading with the role-based advisor and the flip metric.** Use the
   correct numbers: 50% flips at native resolution, 0 unsafe under the 0.335 band.
6. **Before the next NotebookLM run,** add `STATUS.md` §6 ("numbers that must
   never be quoted") to the prompt, so the hosts stop quoting superseded figures.

## Prompt line to add next time

```text
Do not quote superseded figures. STATUS.md section 6 lists numbers that must never be quoted (the 33% flip rate, the 0.089 margin, the 17% flip rate, the 8.9% MAE, MUMDMC 98.3%, FeM 0.872). Use the current figures: 50% recommendation flips at native resolution, a 0.335 conformal margin, 0 unsafe flips under that band. QEMSCAN is a 2D technique. Moodley's fit has one degree of freedom and non-unique parameters; only the mineral-specific outputs were stable.
```
