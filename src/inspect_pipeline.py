"""Visual inspection of the whole pipeline, stage by stage.

    python -m src.inspect_pipeline                     # all test sections + summaries
    python -m src.inspect_pipeline --sections test_04  # just one
    python -m src.inspect_pipeline --no-refine         # raw connected components

Writes PNGs to reports/figures/. Uses the CACHED predictions under data/derived/,
so this is pure rendering - no inference, seconds not hours. Run `decision_gap`
first if a cache is missing.

Why this exists. Each stage of the pipeline fails in a visually distinct way, but
until now only one of them was visible: a bad mask can be seen, a bad *particle*
cannot. The topology failure that left predicted liberation uncorrelated with
truth (+0.128) was found statistically, after the fact, by noticing a correlation
was near zero. Panel 5 below would have shown it immediately - which is the point
of building this.

The particle panels are the ones to look at first. Every particle gets its own
random colour, so:

  - a MERGE reads as one colour spanning two grains that should be separate
  - a SPLIT reads as two colours inside a single grain

Both are invisible in a class mask, because the class labels can be entirely
correct while the particle topology is wrong - and it is topology that liberation
depends on.
"""
import argparse
import json

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from PIL import Image

from . import advisor, modal
from .segmentation import config, lumenstone as ls

Image.MAX_IMAGE_PIXELS = None

FIGURE_DIR = config.REPORT_DIR / "figures"

# Native masks are 3396x2547. Particle analysis runs at native resolution
# because that is what the pipeline does, but display is downsampled - a figure
# does not benefit from 8.6M pixels and the file would be enormous.
DISPLAY_WIDTH = 760


def colourise(labels):
    rgb = np.zeros(labels.shape + (3,), dtype=np.uint8)
    for index, hex_colour in enumerate(ls.CLASS_COLORS):
        h = hex_colour.lstrip("#")
        rgb[labels == index] = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    return rgb


def particle_colours(particles, seed=0):
    """One random colour per particle id; background stays black.

    Random rather than sequential on purpose: neighbouring ids would otherwise
    get near-identical colours, and neighbouring particles are exactly the pairs
    we need to tell apart.
    """
    rng = np.random.default_rng(seed)
    count = int(particles.max())
    palette = rng.integers(60, 255, size=(count + 1, 3), dtype=np.uint8)
    palette[0] = 0
    return palette[particles]


def shrink(array):
    image = Image.fromarray(array)
    scale = DISPLAY_WIDTH / image.width
    resample = Image.NEAREST if array.ndim == 3 else Image.NEAREST
    return np.array(image.resize(
        (DISPLAY_WIDTH, int(image.height * scale)), resample
    ))


def particles_of(labels, refine):
    ore = labels != 0
    if refine:
        ore = modal.refine_ore_mask(ore)
        particles, _ = modal.watershed_particles(ore)
    else:
        particles, _ = modal._connected_components(ore)
    return particles


def payload_fractions(labels, particles):
    """(particle size, payload fraction) for particles above the size floor.

    This is the quantity the liberation threshold is applied to, so plotting it
    shows directly how many particles sit near the decision boundary - i.e. how
    fragile the recommendation is for this section.
    """
    payload_indices = [
        i for i, name in enumerate(ls.CLASS_NAMES)
        if modal.LUMENSTONE_ROLES.get(name) == "payload"
    ]
    payload = np.isin(labels, payload_indices)
    ids, sizes = np.unique(particles[particles > 0], return_counts=True)
    if not len(ids):
        return np.array([]), np.array([])
    counts = np.bincount(
        particles[payload & (particles > 0)], minlength=int(ids.max()) + 1
    )
    keep = sizes >= modal.MIN_PARTICLE_PIXELS
    return sizes[keep], counts[ids[keep]] / sizes[keep]


def section_panel(stem, model_name, refine):
    cache = (config.ROOT / "data" / "derived"
             / f"preds_{ls.SUBSET.lower()}_{model_name}" / f"{stem}.npz")
    if not cache.exists():
        raise FileNotFoundError(
            f"No cached prediction at {cache}. Run:\n"
            f"  python -m src.decision_gap --model {model_name}"
            f"{' --refine' if refine else ''}"
        )
    store = np.load(cache)
    predicted, confidence = store["mask"], float(store["confidence"])

    image = np.array(Image.open(
        ls.DATA_DIR / "imgs" / "test" / f"{stem}.jpg"
    ).convert("RGB"))
    truth_raw = np.array(Image.open(ls.DATA_DIR / "masks" / "test" / f"{stem}.png"))
    if truth_raw.ndim == 3:
        truth_raw = truth_raw[:, :, 0]
    # _LOOKUP is a torch tensor, so indexing it yields a tensor; everything
    # downstream here is numpy.
    truth = ls._LOOKUP[truth_raw.astype(np.int64)].numpy()

    truth_particles = particles_of(truth, refine)
    predicted_particles = particles_of(predicted, refine)

    truth_result = modal.analyse(truth, ls.CLASS_NAMES, refine=refine)
    predicted_result = modal.analyse(predicted, ls.CLASS_NAMES, refine=refine)
    truth_action = advisor.advise(truth_result, 1.0, liberation_margin=0.0).action
    recommendation = advisor.advise(predicted_result, confidence)

    # Error map: correct pixels go grey, wrong pixels take the colour of the
    # class they were MISTAKEN FOR. That is what makes the failure diagnosable -
    # "magnetite is wrong" says little, "magnetite became background" says
    # everything.
    wrong = truth != predicted
    error = np.full(truth.shape + (3,), 70, dtype=np.uint8)
    error[wrong] = colourise(predicted)[wrong]

    figure, axes = plt.subplots(2, 4, figsize=(19, 9))
    figure.suptitle(
        f"{stem}  |  {ls.SUBSET} {model_name} model  |  "
        f"particles: {'watershed + hole-fill' if refine else 'raw connected components'}",
        fontsize=13,
    )
    views = [
        (shrink(image), "1. input micrograph"),
        (shrink(colourise(truth)), "2. ground-truth phases"),
        (shrink(colourise(predicted)), "3. predicted phases"),
        (shrink(error), "4. errors, coloured by what it BECAME"),
        (shrink(particle_colours(truth_particles)),
         f"5. ground-truth particles ({truth_result.n_particles})"),
        (shrink(particle_colours(predicted_particles)),
         f"6. predicted particles ({predicted_result.n_particles})"),
    ]
    for axis, (picture, title) in zip(axes.flat, views):
        axis.imshow(picture)
        axis.set_title(title, fontsize=10)
        axis.axis("off")

    # Panel 7 - per-particle composition against the liberation threshold.
    axis = axes.flat[6]
    for particles, labels, colour, label in (
        (truth_particles, truth, "#2f6f4f", "truth"),
        (predicted_particles, predicted, "#c2571a", "predicted"),
    ):
        sizes, fractions = payload_fractions(labels, particles)
        if len(sizes):
            axis.scatter(sizes, fractions, s=14, alpha=0.55, c=colour, label=label)
    axis.axhline(modal.LIBERATION_THRESHOLD, color="black", lw=1.2, ls="--")
    axis.text(
        0.02, modal.LIBERATION_THRESHOLD + 0.03,
        f"liberated above {modal.LIBERATION_THRESHOLD:.0%}",
        transform=axis.get_yaxis_transform(), fontsize=8,
    )
    axis.set_xscale("log")
    axis.set_xlabel("particle size (px, log)")
    axis.set_ylabel("payload fraction of particle")
    axis.set_title("7. particle composition vs threshold", fontsize=10)
    axis.set_ylim(-0.05, 1.05)
    axis.legend(fontsize=8, loc="lower right")

    # Panel 8 - the decision, and how close it came to going the other way.
    axis = axes.flat[7]
    axis.axis("off")
    show = lambda v: "not measurable" if v is None else f"{v:.0%}"
    agree = "AGREES" if truth_action == recommendation.action else "DISAGREES"
    lines = [
        f"liberation, truth      {show(truth_result.liberation)}",
        f"liberation, predicted  {show(predicted_result.liberation)}",
        f"payload, truth         {truth_result.role_fractions.get('payload', 0):.1%}",
        f"payload, predicted     {predicted_result.role_fractions.get('payload', 0):.1%}",
        f"ore in field           {predicted_result.ore_area_fraction:.1%}",
        f"model confidence       {confidence:.2f}",
        "",
        f"truth would say:  {truth_action}",
        f"model says:       {recommendation.action}",
        "",
        f"--> {agree}",
    ]
    axis.text(0, 1, "8. decision\n\n" + "\n".join(lines), va="top", ha="left",
              family="monospace", fontsize=9.5, transform=axis.transAxes)

    legend = [Patch(facecolor=c, label=n)
              for n, c in zip(ls.CLASS_NAMES, ls.CLASS_COLORS)]
    figure.legend(handles=legend, loc="lower center", ncol=len(legend), fontsize=9,
                  frameon=False, bbox_to_anchor=(0.5, -0.005))
    figure.tight_layout(rect=(0, 0.03, 1, 0.97))

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    suffix = "" if refine else "_raw"
    out = FIGURE_DIR / f"{ls.SUBSET.lower()}_{model_name}_{stem}{suffix}.png"
    figure.savefig(out, dpi=95)
    plt.close(figure)
    return out


def liberation_scatter():
    """Truth vs predicted liberation for every configuration measured.

    This is the single most informative chart we have: recommendation flips are
    literally the off-diagonal quadrants. A point in the lower-right is "truth
    says grind, model says continue" - the error that loses metal.
    """
    runs = [
        ("resize, raw", "decision_gap.json", "#b0b0b0"),
        ("resize, refined", "decision_gap_refined.json", "#7aa6c2"),
        ("patch, raw", "decision_gap_patches.json", "#e0a03c"),
        ("patch, refined", "decision_gap_patches_refined.json", "#2f6f4f"),
    ]
    available = [(n, f, c) for n, f, c in runs
                 if (config.REPORT_DIR / f).exists()]
    if not available:
        print("no decision_gap results yet; skipping scatter")
        return None

    figure, axes = plt.subplots(1, len(available), figsize=(4.6 * len(available), 4.9),
                               squeeze=False)
    threshold = advisor.LOW_LIBERATION
    for axis, (name, filename, colour) in zip(axes[0], available):
        rows = json.load(open(config.REPORT_DIR / filename))["rows"]
        pairs = [(r["liberation_truth"], r["liberation_predicted"], r["id"])
                 for r in rows
                 if r["liberation_truth"] is not None
                 and r["liberation_predicted"] is not None]

        # Quadrants: the two shaded corners are where a recommendation flips.
        axis.axhspan(0, threshold, xmin=threshold, xmax=1,
                     color="#f0d0d0", zorder=0)
        axis.axhspan(threshold, 1, xmin=0, xmax=threshold,
                     color="#ffe9c9", zorder=0)
        axis.axhline(threshold, color="black", lw=1, ls="--", zorder=2)
        axis.axvline(threshold, color="black", lw=1, ls="--", zorder=2)
        axis.axhspan(threshold - advisor.LIBERATION_MARGIN,
                     threshold + advisor.LIBERATION_MARGIN,
                     color="#d9d9d9", alpha=0.55, zorder=1)
        axis.plot([0, 1], [0, 1], color="#888", lw=0.9, zorder=2)

        for truth, predicted, stem in pairs:
            axis.scatter(truth, predicted, s=48, c=colour, edgecolor="black",
                         linewidth=0.4, zorder=3)
            if abs(truth - predicted) > 0.25:
                axis.annotate(stem.replace("test_", ""), (truth, predicted),
                              fontsize=7, xytext=(4, -9),
                              textcoords="offset points", zorder=4)

        flips = sum(1 for r in rows if r["flipped"])
        axis.set_title(f"{name}\n{flips}/{len(rows)} flips", fontsize=10)
        axis.set_xlabel("liberation, ground truth")
        axis.set_xlim(-0.04, 1.04)
        axis.set_ylim(-0.04, 1.04)
    axes[0][0].set_ylabel("liberation, predicted")
    figure.suptitle(
        "Liberation agreement. Grey band = the +/-%.1f%% uncertainty band. "
        "Shaded corners = recommendation flips; pink (lower right) is the "
        "expensive direction." % (advisor.LIBERATION_MARGIN * 100),
        fontsize=10.5,
    )
    figure.tight_layout(rect=(0, 0, 1, 0.93))

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    out = FIGURE_DIR / "liberation_agreement.png"
    figure.savefig(out, dpi=110)
    plt.close(figure)
    return out


def confusion_heatmap(path="reports/magnetite_confusion.json"):
    source = config.ROOT / path
    if not source.exists():
        return None
    data = json.load(open(source))
    matrix = np.array(data["confusion"], dtype=float)
    names = data["class_names"]
    normalised = matrix / np.clip(matrix.sum(1, keepdims=True), 1, None)

    figure, axis = plt.subplots(figsize=(6.4, 5.4))
    axis.imshow(normalised, cmap="Blues", vmin=0, vmax=1)
    axis.set_xticks(range(len(names)), names, rotation=45, ha="right", fontsize=9)
    axis.set_yticks(range(len(names)), names, fontsize=9)
    axis.set_xlabel("predicted")
    axis.set_ylabel("ground truth")
    axis.set_title("Where each phase goes (row-normalised)", fontsize=11)
    for i in range(len(names)):
        for j in range(len(names)):
            value = normalised[i, j]
            if value > 0.005:
                axis.text(j, i, f"{value:.0%}", ha="center", va="center",
                          fontsize=8.5,
                          color="white" if value > 0.55 else "black")
    figure.tight_layout()
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    out = FIGURE_DIR / "phase_confusion.png"
    figure.savefig(out, dpi=110)
    plt.close(figure)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=("resize", "patches"), default="patches")
    parser.add_argument("--sections", nargs="*", default=None,
                        help="section stems; default is every test section")
    parser.add_argument("--no-refine", dest="refine", action="store_false",
                        help="use raw connected components, to see what topology "
                             "repair actually fixes")
    args = parser.parse_args()

    _, _, test_ids = ls.split_ids()
    sections = args.sections or sorted(test_ids)
    for stem in sections:
        print("wrote", section_panel(stem, args.model, args.refine))

    for out in (liberation_scatter(), confusion_heatmap()):
        if out:
            print("wrote", out)


if __name__ == "__main__":
    main()
