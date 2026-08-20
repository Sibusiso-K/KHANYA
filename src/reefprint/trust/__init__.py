"""Trust: ensemble, conformal prediction, OOD gate, abstention.

Calibrated uncertainty and the refusal mechanism.

Four rules bite hardest here, and two of them are now code rather than prose:

- **Rule 2** — split by locality, never by patch or image.
  :mod:`reefprint.trust.split`. :func:`~reefprint.trust.split.split_by_locality` is the
  sanctioned constructor and :func:`~reefprint.trust.split.require_locality_disjoint` is the
  backstop for splits built by hand. Measured on synthetic patches whose only signal is
  section identity: patch split MAE 0.0017, honest locality split MAE 0.2119 — the leak is
  worth **126x**, and it is worth it in the flattering direction.
- **Rule 3** — report the trivial baseline alongside every metric, always.
  :mod:`reefprint.trust.baseline`. :class:`~reefprint.trust.baseline.ScoredMetric` takes
  ``baselines`` as a required field with no default, so a bare metric is a :class:`TypeError`
  rather than a slide. Uplift is measured against the *strongest* baseline, never the weakest.
- **Rule 4** — every metric carries a CI sized at honest n. Conformal coverage SD is
  sqrt(0.9 * 0.1 / n_cal): about 3.0 pp at n_cal = 100, about 6.7 pp at n_cal = 20. Do not
  claim tighter than the arithmetic allows. Honest n for a locality split is
  :attr:`~reefprint.trust.split.LocalitySplit.n_groups` — localities, not sections.
- **Rule 5** — abstention emits a *conservative default with a stated reason*, never
  "unknown". Blind spot 1: abstention fires exactly when it is least safe, because novel
  texture triggers OOD and novel texture *is* an ore transition. Report abstention rate
  conditioned on ore-change events, not just in aggregate.

The same pattern as :class:`~reefprint.acquire.series.RotationGeometry` and
:class:`~reefprint.bridge.section.LabelProvenance`: where a rule protects against a *silent*
wrong answer, the guard has to be structural. Nothing prompts you to re-read the prose.
"""
