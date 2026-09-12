"""The week-2 gate: H0 (texture carries no signal after Cr2O3 and pyroxene fraction) computed
with a confidence interval, grouped by locality (CLAUDE.md's falsification test, Rule 9).

This tests the statistical core against synthetic data with a known ground truth — a real
texture effect that must be detected, and a real absence of one that must not be manufactured.

**2026-09-12 — the placeholder that used to sit at the bottom of this file has been deleted, per
its own instruction, and the result recorded.** Two things are true at once, and CLAUDE.md's
rule 9 says report both:

1. **The literal H0 — texture vs Cr2O3 + pyroxene fraction — remains untestable.**
   `texture_features` is structurally missing (CONTEXT.md item T1: no public dataset pairs
   polished-section imagery to real assay depth intervals) and pyroxene fraction is not a
   column in the one real geochemistry dataset in hand (item T2). "Not testable with available
   data" is itself the result, published with that missing-data specification — Rule 9 working,
   not a failure.
2. **A narrower, real, related question HAS been run on real data**, as the accepted pivot: does
   chromite composition (Cr#, Mg#, Barnes & Roeder 2001) add PGE-grade signal beyond Cr2O3
   alone? `experiments/006-bushveld-chromite-falsification/` runs `evaluate_texture_uplift`
   against the real Bachmann (2019) Bushveld CSV and gets **delta R^2 = 0.0279, p = 0.0002,
   n = 1,112 rows over 305 boreholes** — bit-for-bit identical to an independent implementation
   on `khanya/main` (`src/chromite_pge_falsification.py`), which is the cross-check, not a
   duplicate: two separately written programs landing on the same seventeen significant figures
   is stronger evidence than either alone. `tests/test_bushveld_chromite_falsification.py`
   exercises the CSV-parsing and cation-ratio harness against synthetic data (the real download
   is gitignored, same reason `test_s3v2_reader.py` does not need the real S3 v2 archive) —
   proves the maths, not the mineralogy, same distinction CLAUDE.md draws for N3's leg (a) vs
   leg (b). **This is not the texture falsification and must never be quoted as one** — see
   `docs/BUILDLOG.md` and `WORKBOARD.md` §3 P4 for the caveats this result carries (modest
   effect size, Cr# is arithmetically related to the Cr2O3 baseline, fitted association rather
   than an out-of-locality predictive test, boreholes within one project may not be fully
   independent localities).
"""

from __future__ import annotations

import numpy as np
import pytest

from reefprint.heads.falsification import (
    MIN_LOCALITIES_FOR_INFERENCE,
    FalsificationResult,
    evaluate_texture_uplift,
)


def _clustered_dataset(
    *,
    n_localities: int,
    n_per_locality: int,
    true_texture_coef: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Synthetic ore data with a locality-level random intercept — the thing a plain OLS
    standard error ignores and a cluster-robust one does not. Two baseline features
    (stand-ins for Cr2O3 and pyroxene fraction) always carry real signal; the texture feature's
    effect is the thing under test.
    """
    rng = np.random.default_rng(seed)
    localities = np.repeat(np.arange(n_localities), n_per_locality)
    n = localities.size

    cr2o3 = rng.normal(15.0, 3.0, size=n)
    pyroxene = rng.normal(0.4, 0.1, size=n)
    texture = rng.normal(0.0, 1.0, size=n)

    locality_shock = rng.normal(0.0, 2.5, size=n_localities)[localities]
    noise = rng.normal(0.0, 1.0, size=n)

    target = 2.0 * cr2o3 + 5.0 * pyroxene + true_texture_coef * texture + locality_shock + noise
    baseline = np.column_stack([cr2o3, pyroxene])
    return target, baseline, texture.reshape(-1, 1), localities


def test_no_real_texture_effect_is_not_rejected() -> None:
    target, baseline, texture, localities = _clustered_dataset(
        n_localities=12, n_per_locality=25, true_texture_coef=0.0, seed=1
    )
    result = evaluate_texture_uplift(target, baseline, texture, localities)

    assert isinstance(result, FalsificationResult)
    assert not result.rejects_h0
    assert result.p_value > 0.05
    assert result.delta_r2 < 0.02


def test_a_real_texture_effect_is_rejected() -> None:
    target, baseline, texture, localities = _clustered_dataset(
        n_localities=12, n_per_locality=25, true_texture_coef=4.0, seed=1
    )
    result = evaluate_texture_uplift(target, baseline, texture, localities)

    assert result.rejects_h0
    assert result.p_value < 0.05
    assert result.delta_r2 > 0.02


def test_honest_n_is_locality_count_not_observation_count() -> None:
    target, baseline, texture, localities = _clustered_dataset(
        n_localities=8, n_per_locality=40, true_texture_coef=1.0, seed=2
    )
    result = evaluate_texture_uplift(target, baseline, texture, localities)

    assert result.n_localities == 8
    assert result.n_obs == 8 * 40
    assert result.n_localities != result.n_obs


def test_too_few_localities_refuses_rather_than_prints_a_fake_p_value() -> None:
    """Rule 4: do not claim tighter than the arithmetic allows. Cluster-robust inference at a
    handful of clusters is not inference, it is a coin flip wearing a p-value.
    """
    target, baseline, texture, localities = _clustered_dataset(
        n_localities=MIN_LOCALITIES_FOR_INFERENCE - 1,
        n_per_locality=10,
        true_texture_coef=1.0,
        seed=3,
    )
    with pytest.raises(ValueError, match="localities"):
        evaluate_texture_uplift(target, baseline, texture, localities)


def test_baseline_r2_is_reported_alongside_full_model_r2() -> None:
    """Rule 3: report the trivial baseline alongside every metric, always. Here the baseline
    IS the H0 model (Cr2O3 + pyroxene fraction, no texture) — reporting it is the whole point.
    """
    target, baseline, texture, localities = _clustered_dataset(
        n_localities=10, n_per_locality=20, true_texture_coef=3.0, seed=4
    )
    result = evaluate_texture_uplift(target, baseline, texture, localities)

    assert 0.0 <= result.baseline_r2 <= 1.0
    assert 0.0 <= result.full_r2 <= 1.0
    assert result.full_r2 >= result.baseline_r2
    assert result.delta_r2 == pytest.approx(result.full_r2 - result.baseline_r2)
