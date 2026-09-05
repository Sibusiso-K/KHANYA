"""Distribution-free liberation intervals, and conformal sets over actions.

    python -m src.conformal                          # S2 patch+refined
    python -m src.conformal --run decision_gap_refined.json

Reads liberation pairs straight from a decision_gap result, so this costs
milliseconds - no inference, no retraining.

WHY THIS REPLACED THE ORIGINAL BAND. The advisor originally hedged when liberation
fell within LIBERATION_MARGIN = 0.089 of the threshold, and 0.089 was the mean
absolute error measured on S2. Two problems with that. It is a point estimate
dressed as a guarantee - nothing says a +/-MAE band covers any particular
fraction of cases. And it does not transfer: S1's liberation MAE is 20.3%, so on
S1 the same constant is less than half the width it should be, and the advisor
is quietly overconfident on a dataset it was never calibrated for.

Split conformal prediction fixes both. The half-width becomes an empirical
quantile of absolute residuals rather than their mean, which yields a
distribution-free coverage guarantee under exchangeability alone - no assumption
that errors are Gaussian, no model of the error at all. Recalibrating on a new
ore body is one pass over its calibration residuals.

SMALL-SAMPLE HONESTY. Split conformal at level 1-alpha needs
ceil((n+1)(1-alpha)) <= n, so n=6 calibration sections cannot support 90%
coverage at all - the highest achievable level is 1 - 1/(n+1) = 85.7%. With 12
sections it is 92.3%. Here we evaluate a fixed model's residuals leave-one-out
over the test sections, using every section for both calibration and evaluation
in different folds. This is not jackknife+: no predictive models are refitted.
Each fold has n-1 calibration residuals, so its ceiling is 1 - 1/n. We report
EMPIRICAL fold coverage; averaging their half-widths does not give a new
split-conformal guarantee for a fixed deployment band.
"""
import argparse
import json
import math

from . import advisor
from .segmentation import config


def quantile_halfwidth(residuals, alpha):
    """Conformal half-width: the ceil((n+1)(1-alpha))-th smallest residual.

    Returns None when the calibration set is too small to support the level,
    rather than silently falling back to the largest residual and implying a
    guarantee that does not hold.
    """
    if not math.isfinite(alpha) or not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be finite and strictly between zero and one")
    if any(not math.isfinite(value) or value < 0 for value in residuals):
        raise ValueError("residuals must be finite and non-negative")
    n = len(residuals)
    k = math.ceil((n + 1) * (1 - alpha))
    if k > n:
        return None
    return sorted(residuals)[k - 1]


def action_set(liberation, low, high, payload_result_action):
    """Admissible actions when liberation is only known to lie in [low, high].

    Evaluated at the interval endpoints: if the interval straddles the
    liberation floor the two endpoints disagree, and the honest output is the
    SET of actions rather than a pick between them. This is the natural
    generalisation of the fixed band - the band said "we are near a threshold",
    a conformal set says "these are the actions still consistent with the data".
    """
    actions = set()
    for value in (low, high, liberation):
        if value is None:
            continue
        clipped = min(max(value, 0.0), 1.0)
        actions.add(
            "grind finer" if clipped < advisor.LOW_LIBERATION
            else "continue/adjust"
        )
    return actions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", default="decision_gap_patches_refined.json")
    parser.add_argument("--alphas", nargs="*", type=float,
                        default=[0.20, 0.15, 0.10])
    args = parser.parse_args()

    with open(config.REPORT_DIR / args.run) as source:
        data = json.load(source)
    rows = [r for r in data["rows"]
            if r["liberation_truth"] is not None
            and r["liberation_predicted"] is not None]
    n = len(rows)
    if n < 2:
        parser.error("leave-one-out calibration needs at least two measured section pairs")
    residuals = [abs(r["liberation_truth"] - r["liberation_predicted"])
                 for r in rows]

    print(f"\n{args.run}  |  {n} sections  |  "
          f"MAE {sum(residuals)/n:.3f}  max residual {max(residuals):.3f}")
    ceiling = 1 - 1 / n
    print(f"highest finite level per leave-one-out fold (n_cal={n-1}): {ceiling:.1%}")
    fixed_cov = sum(1 for x in residuals
                    if x <= advisor.LIBERATION_MARGIN) / n
    print(f"the advisor's fixed band is +/-{advisor.LIBERATION_MARGIN:.3f}, "
          f"which on this run actually covers {fixed_cov:.0%}")
    print("This retrospective coverage is not a guarantee for new uploads.")
    print()

    print(f"{'level':>8s}{'half-width':>12s}{'vs fixed':>10s}"
          f"{'empirical cov':>15s}{'hedged':>9s}")
    print("-" * 54)

    summary = {"run": args.run, "n_sections": n,
               "mae": sum(residuals) / n,
               "max_residual": max(residuals),
               "coverage_ceiling": ceiling,
               "fixed_band": advisor.LIBERATION_MARGIN,
               "fixed_band_empirical_coverage": fixed_cov,
               "levels": {}}

    for alpha in args.alphas:
        level = 1 - alpha
        # Leave-one-out: each section is scored against a half-width computed
        # from the OTHER sections, so no section calibrates its own interval.
        covered, hedged, widths = 0, 0, []
        for i, row in enumerate(rows):
            others = residuals[:i] + residuals[i + 1:]
            half = quantile_halfwidth(others, alpha)
            if half is None:
                widths = None
                break
            widths.append(half)
            predicted = row["liberation_predicted"]
            low, high = predicted - half, predicted + half
            if low <= row["liberation_truth"] <= high:
                covered += 1
            if len(action_set(predicted, low, high, None)) > 1:
                hedged += 1
        if widths is None:
            print(f"{level:>7.0%}{'n/a':>12s}{'':>10s}"
                  f"{'calibration set too small':>15s}")
            continue

        mean_half = sum(widths) / len(widths)
        print(f"{level:>7.0%}{mean_half:>12.3f}"
              f"{mean_half - advisor.LIBERATION_MARGIN:>+10.3f}"
              f"{covered / n:>14.0%}{hedged:>9d}")
        summary["levels"][f"{level:.2f}"] = {
            "mean_half_width": mean_half,
            "empirical_coverage": covered / n,
            "n_hedged": hedged,
        }

    out = config.REPORT_DIR / f"conformal_{args.run}"
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
