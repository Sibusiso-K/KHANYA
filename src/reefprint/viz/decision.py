"""Render a prediction or refusal as an explicit operator-facing figure."""

from __future__ import annotations

from textwrap import fill

from matplotlib.figure import Figure

from reefprint.quantity import require_reportable
from reefprint.trust.abstain import Abstention, Decision, Prediction

__all__ = ["decision_figure"]


def decision_figure(decision: Decision, *, title: str = "REEFPRINT decision") -> Figure:
    """Render a decision without allowing a refusal to collapse into a blank panel.

    A refusal is deliberately rendered as a red, two-line status: the conservative default that
    will be emitted and the specific reason that caused the refusal. This is a display boundary,
    so a prediction's quantity is checked for reportability before it reaches the figure.
    """
    figure = Figure(figsize=(10.0, 5.5), layout="constrained")
    figure.suptitle(title, fontsize=14, fontweight="bold")
    axes = figure.subplots()
    axes.set_axis_off()

    if isinstance(decision, Abstention):
        quantity = decision.default.quantity
        require_reportable(quantity)
        figure.text(
            0.5,
            0.82,
            "SYSTEM REFUSED TO ANSWER",
            ha="center",
            va="center",
            fontsize=18,
            fontweight="bold",
            color="firebrick",
        )
        figure.text(
            0.5,
            0.56,
            fill(f"Reason: {decision.reason}", width=100),
            ha="center",
            va="center",
            fontsize=11,
            wrap=True,
        )
        figure.text(
            0.5,
            0.21,
            fill(f"Conservative default emitted: {quantity.cite()}", width=100)
            + "\n"
            + fill(f"Applies to: {decision.default.applies_to}", width=100),
            ha="center",
            va="center",
            fontsize=11,
            color="firebrick",
        )
        return figure

    if not isinstance(decision, Prediction):
        raise TypeError(f"unsupported decision type: {type(decision).__name__}")
    require_reportable(decision.quantity)
    figure.text(
        0.5,
        0.52,
        f"Prediction: {decision.quantity.cite()}",
        ha="center",
        va="center",
        fontsize=12,
        wrap=True,
    )
    return figure
