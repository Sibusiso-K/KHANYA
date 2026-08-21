"""The week-2 gate, as a function: does texture survive controlling for Cr2O3 and pyroxene
fraction?

    H0: after controlling for Cr2O3 and pyroxene fraction, texture carries no additional
    predictive signal.

Rule 9 makes this a deliverable, not a risk — the result is reported whichever way it comes out,
and if H0 is not rejected the project pivots to the oxidation index in public, not quietly.

**Why cluster-robust, not a plain OLS F-test.** Rule 2 says split by locality, never by patch
or image, because patch-level structure inflates apparent significance — the same leak, dressed
differently, threatens inference here: observations from the same locality share whatever that
locality's geology did that neither Cr2O3, pyroxene fraction, nor texture captures, so a plain
OLS standard error treats correlated residuals as independent evidence and manufactures
confidence nothing supports. Clustering the covariance estimate by locality (Cameron-Miller
CR1, White 1980) fixes the standard error; :data:`MIN_LOCALITIES_FOR_INFERENCE` refuses the test
below the cluster count where that fix stops being trustworthy (Rule 4 as a bound, not a
suggestion — see the same pattern in :mod:`reefprint.trust.baseline` and
:mod:`reefprint.trust.abstain`).

**Honest n is locality count, not row count**, same as :attr:`~reefprint.trust.split.LocalitySplit.n_groups`.
:attr:`FalsificationResult.n_localities` is that number; :attr:`FalsificationResult.n_obs` is
recorded too, so the gap between them is visible rather than implied.

**Rule 3 is structural here rather than bolted on**: the null model (Cr2O3 + pyroxene fraction,
no texture) *is* the trivial baseline this test is required to report, so
:attr:`FalsificationResult.baseline_r2` is not optional — it is what H0 says the answer should
already be, before texture is allowed to add anything.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from scipy import stats

if TYPE_CHECKING:
    import numpy.typing as npt

    FloatArray = npt.NDArray[np.floating]
    IntArray = npt.NDArray[np.integer]

__all__ = ["MIN_LOCALITIES_FOR_INFERENCE", "FalsificationResult", "evaluate_texture_uplift"]

#: Cluster-robust standard errors need enough clusters to estimate the cluster-level covariance
#: at all. Five is a floor, not a target — Cameron & Miller (2015) flag inference as unreliable
#: well above this in the general case; it exists so the test refuses rather than silently
#: returning a p-value with no real information behind it (Rule 4).
MIN_LOCALITIES_FOR_INFERENCE = 5


@dataclass(frozen=True, slots=True)
class FalsificationResult:
    """The H0 test result. Read ``rejects_h0``; quote ``p_value`` and both R^2 values.

    Attributes:
        n_obs: Row count. Not the honest sample size — see ``n_localities``.
        n_localities: Honest n for this test. Cluster-robust inference is only as good as this
            count, which is why :data:`MIN_LOCALITIES_FOR_INFERENCE` gates construction on it.
        baseline_r2: R^2 of the null model — Cr2O3 and pyroxene fraction alone. Rule 3's
            required baseline, reported because H0 says this is already the right answer.
        full_r2: R^2 with texture added.
        delta_r2: ``full_r2 - baseline_r2``. The uplift H0 claims is zero.
        wald_statistic: Cluster-robust Wald statistic on the texture coefficients, F-scaled.
        p_value: One-sided (texture adds signal) significance of ``wald_statistic`` against
            ``F(q, n_localities - 1)``, ``q`` the number of texture features.
        rejects_h0: ``p_value < alpha``, at the ``alpha`` the call was made with.
    """

    n_obs: int
    n_localities: int
    baseline_r2: float
    full_r2: float
    delta_r2: float
    wald_statistic: float
    p_value: float
    rejects_h0: bool

    def summary(self) -> str:
        """One line for the build log and the talk. States the losing side too."""
        verdict = "REJECTED" if self.rejects_h0 else "NOT REJECTED"
        return (
            f"H0 (texture adds nothing beyond Cr2O3 + pyroxene fraction) {verdict}: "
            f"delta R^2 = {self.delta_r2:.4f} ({self.baseline_r2:.4f} -> {self.full_r2:.4f}), "
            f"p = {self.p_value:.4f}, n = {self.n_obs} rows over {self.n_localities} localities "
            f"(honest n)."
        )


def _design(*feature_blocks: FloatArray) -> FloatArray:
    """Intercept column plus every feature block, concatenated."""
    n = feature_blocks[0].shape[0]
    return np.column_stack([np.ones(n), *feature_blocks])


def _r_squared(target: FloatArray, design: FloatArray) -> tuple[FloatArray, float]:
    """OLS coefficients and R^2 for one design matrix."""
    coefficients, *_ = np.linalg.lstsq(design, target, rcond=None)
    residual = target - design @ coefficients
    tss = float(np.sum((target - target.mean()) ** 2))
    rss = float(np.sum(residual**2))
    r_squared = 1.0 - rss / tss if tss > 0 else 0.0
    return coefficients, r_squared


def _cluster_robust_covariance(
    design: FloatArray, residual: FloatArray, localities: IntArray
) -> FloatArray:
    """CR1 cluster-robust covariance of the OLS coefficients (Cameron & Miller 2015).

    Small-cluster corrected: scaled by ``G/(G-1) * (n-1)/(n-k)``, the standard finite-cluster
    adjustment, so the covariance is not silently optimistic at the small ``G`` this project's
    locality counts actually produce.
    """
    n, k = design.shape
    groups = np.unique(localities)
    bread = np.linalg.inv(design.T @ design)

    meat = np.zeros((k, k))
    for group in groups:
        mask = localities == group
        score = design[mask].T @ residual[mask]
        meat += np.outer(score, score)

    n_groups = groups.size
    correction = (n_groups / (n_groups - 1)) * ((n - 1) / (n - k))
    return correction * (bread @ meat @ bread)


def evaluate_texture_uplift(
    target: FloatArray,
    baseline_features: FloatArray,
    texture_features: FloatArray,
    localities: IntArray,
    *,
    alpha: float = 0.05,
) -> FalsificationResult:
    """Test H0: texture adds no signal beyond ``baseline_features``, clustered by locality.

    Args:
        target: ``(n,)``. Whatever the falsification test is evaluated against — CLAUDE.md's
            H0 does not name the target variable, only the controls and the challenger.
        baseline_features: ``(n, p)``. Cr2O3 and pyroxene fraction, or their stand-ins.
        texture_features: ``(n, q)``. The challenger — what is under test.
        localities: ``(n,)`` group labels. The clustering unit; see the module docstring for
            why this must be locality and not patch or image.
        alpha: Significance level for ``rejects_h0``. Reported alongside ``p_value`` rather
            than baked in, so the same result can be read at a different threshold.

    Returns:
        A :class:`FalsificationResult`.

    Raises:
        ValueError: Fewer than :data:`MIN_LOCALITIES_FOR_INFERENCE` distinct localities.
    """
    n_localities = int(np.unique(localities).size)
    if n_localities < MIN_LOCALITIES_FOR_INFERENCE:
        raise ValueError(
            f"only {n_localities} distinct localities, need at least "
            f"{MIN_LOCALITIES_FOR_INFERENCE} for cluster-robust inference to mean anything"
        )

    design_baseline = _design(baseline_features)
    design_full = _design(baseline_features, texture_features)

    _, baseline_r2 = _r_squared(target, design_baseline)
    coefficients_full, full_r2 = _r_squared(target, design_full)

    residual_full = target - design_full @ coefficients_full
    covariance = _cluster_robust_covariance(design_full, residual_full, localities)

    n_baseline = baseline_features.shape[1]
    texture_slice = slice(1 + n_baseline, design_full.shape[1])
    texture_coefficients = coefficients_full[texture_slice]
    texture_covariance = covariance[texture_slice, texture_slice]

    q = texture_coefficients.size
    wald = float(texture_coefficients @ np.linalg.solve(texture_covariance, texture_coefficients))
    denominator_df = n_localities - 1
    f_statistic = wald / q
    p_value = float(stats.f.sf(f_statistic, q, denominator_df))

    return FalsificationResult(
        n_obs=int(target.shape[0]),
        n_localities=n_localities,
        baseline_r2=baseline_r2,
        full_r2=full_r2,
        delta_r2=full_r2 - baseline_r2,
        wald_statistic=f_statistic,
        p_value=p_value,
        rejects_h0=p_value < alpha,
    )
