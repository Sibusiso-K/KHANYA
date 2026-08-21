"""The week-2 gate: H0 (texture carries no signal after Cr2O3 and pyroxene fraction) computed
with a confidence interval, grouped by locality (CLAUDE.md's falsification test, Rule 9).

This tests the statistical core against synthetic data with a known ground truth — a real
texture effect that must be detected, and a real absence of one that must not be manufactured.
The real Bushveld geochemistry (Cr2O3, pyroxene fraction) and texture features this needs to
run against real ore are not yet in hand — see the placeholder test at the bottom, matching the
project's N3 pattern (`tests/test_s3v2_reader.py`).
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


@pytest.mark.placeholder
def test_the_falsification_test_has_been_run_on_real_bushveld_data() -> None:
    """The week-2 gate is not closed until this runs on real Cr2O3, pyroxene fraction, and a
    real texture feature, grouped by real localities.

    Everything above tests the statistical core against synthetic data with a known ground
    truth. That proves the maths, not the mineralogy — same distinction CLAUDE.md draws for
    N3's leg (a) vs leg (b). The real geochemistry is not yet in hand: CGS National Core
    Library access is a phone call not yet made (CONTEXT.md open item), and no public dataset
    combining assay Cr2O3/pyroxene with a texture feature and locality labels has been
    identified. Delete this test and record the result in docs/BUILDLOG.md once it has run.
    """
    pytest.fail(
        "NOT MEASURED — week 2 gate open: no real Cr2O3/pyroxene/texture/locality "
        "dataset in hand yet"
    )
