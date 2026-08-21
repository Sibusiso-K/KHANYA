"""Prediction heads: entrainment risk, naturally-floating-gangue load, oxidation index.

The three visible properties that survived the v2 retarget:

- **Fine-chromite entrainment risk** — Cr2O3 is the binding constraint on UG2 flotation.
- **Naturally-floating-gangue load** — talc/serpentine, for depressant dosing. Detection
  without SWIR is open question 1, settled empirically in week 2. If it fails, drop to two.
- **Stockpile oxidation index** — sulphide surfaces tarnish with residence time, destroying
  floatability. Macro-visible and unmeasured anywhere.

Killed and not to be revived without arguing the objection away: liberation at target grind P80
(gauntlet F4 — recovery is chrome-constrained, so liberation fights the binding constraint),
grindability to kWh/t (mills run at near-constant power), and T+45 as a hard claim (S1 —
transport lag is a distribution, not a delay).

`falsification.py` is the week-2 gate (Rule 9): whether texture carries predictive signal beyond
Cr2O3 and pyroxene fraction, tested with cluster-robust inference grouped by locality (Rule 2).
Not one of the three heads above — it decides whether texture belongs in them at all.
"""
