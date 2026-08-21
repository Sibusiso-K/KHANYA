"""Trust: ensemble, conformal prediction, OOD gate, abstention.

Calibrated uncertainty and the refusal mechanism.

Four rules bite hardest here, and three of them are now code rather than prose:

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
  **That formula is zero at p = 0 and p = 1**, so both
  :attr:`~reefprint.trust.baseline.ScoredMetric.noise_at_honest_n` and
  :attr:`~reefprint.trust.abstain.AbstentionAudit.noise_during_ore_change` return ``None``
  there and quote the rule of three (Hanley & Lippman-Hand 1983) instead. Left alone it does
  not merely print a false ±0.000 — in ``ScoredMetric`` it made the "inside the noise" verdict
  unreachable, so every perfect score read as a clean win however few localities produced it.
- **Rule 5** — abstention emits a *conservative default with a stated reason*, never
  "unknown". :mod:`reefprint.trust.abstain`. A refusal is an
  :class:`~reefprint.trust.abstain.Abstention`, which cannot be built without a
  :class:`~reefprint.trust.abstain.ConservativeDefault` and a reason, and which rejects
  "unknown", "n/a" and their neighbours by name. It has **no field for the previous value**,
  so holding the last setpoint is not reachable through the type — blind spot 1 says
  abstention fires exactly when it is least safe, because novel texture trips the OOD gate
  and novel texture *is* an ore transition. The default's direction is checked against its
  own range, so a default that says "assume high" and emits the low end is a
  :class:`ValueError`. :func:`~reefprint.trust.abstain.audit_abstentions` refuses a run with
  no ore-change events in it, because the only number it could then report is the aggregate,
  and quoting the aggregate is the error blind spot 1 describes.
  :attr:`~reefprint.trust.abstain.AbstentionAudit.concentrates_at_transitions` used to be a
  bare ``rate_during_ore_change > rate_when_stable`` — a comparison of two proportions at two
  different sample sizes, with no resolvability gate at all, so an 8-point gap at n = 3 read
  the same as a real one at n = 50. It is now gated on
  :attr:`~reefprint.trust.abstain.AbstentionAudit.concentration_p_value`, a one-sided Fisher's
  exact test (Fisher 1922) on the 2x2 table — chosen because, unlike the Wald SE above, it does
  not degenerate at p = 0 or p = 1 or need a minimum n, so it is what actually resolves the
  two-event canonical example: p ≈ 0.0095, even though the rate's own rule-of-three bound can
  only say n = 2 "resolves nothing" about the rate in isolation. Direction and significance are
  two statements, not one, and :meth:`~reefprint.trust.abstain.AbstentionAudit.summary` now has
  a third state for "elevated but unresolved" — neither the blind-spot-1 claim nor "does not
  concentrate" is honest there, since the latter overclaims safety exactly where n is weakest.

Rule 1 is enforced one level up, in :mod:`reefprint.quantity`, because it applies to every
subpackage rather than to this one. It meets rule 5 at
:attr:`~reefprint.trust.abstain.ConservativeDefault.quantity`, which is a
:class:`~reefprint.quantity.Quantity` and is checked with
:func:`~reefprint.quantity.require_reportable`: a conservative default derived from a design
target is refused at construction, not on the slide.

The same pattern as :class:`~reefprint.acquire.series.RotationGeometry` and
:class:`~reefprint.bridge.section.LabelProvenance`: where a rule protects against a *silent*
wrong answer, the guard has to be structural. Nothing prompts you to re-read the prose.
"""
