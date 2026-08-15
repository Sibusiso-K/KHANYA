"""Trust: ensemble, conformal prediction, OOD gate, abstention.

Calibrated uncertainty and the refusal mechanism.

Two rules bite hardest here:

- **Rule 4** — every metric carries a CI sized at honest n. Conformal coverage SD is
  sqrt(0.9 * 0.1 / n_cal): about 3.0 pp at n_cal = 100, about 6.7 pp at n_cal = 20. Do not
  claim tighter than the arithmetic allows.
- **Rule 5** — abstention emits a *conservative default with a stated reason*, never
  "unknown". Blind spot 1: abstention fires exactly when it is least safe, because novel
  texture triggers OOD and novel texture *is* an ore transition. Report abstention rate
  conditioned on ore-change events, not just in aggregate.
"""
