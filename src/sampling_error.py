"""How much does liberation vary between fields of the SAME section?

    python -m src.sampling_error            # 3x3 sub-fields per section
    python -m src.sampling_error --grid 2

Uses ground-truth masks only. No model is involved anywhere in this file, which
is the entire point: this measures the error a perfect model would still make.

The question. Every liberation number in this project comes from one field of
view. Real process mineralogy images many fields per section precisely because
grain populations are not uniform across a polished surface. If liberation varies
substantially between sub-fields of the same section, then part of the
disagreement we have been attributing to the model is really SAMPLING noise, and
would remain after any amount of model improvement.

The comparison that matters is this spread against our model's liberation error
(mean absolute error 0.089 on S2, 0.203 on S1). If they are comparable, the
limiting factor is how many fields you image, not how good the network is - which
would be a more useful conclusion for a plant than any IoU number, and would
change what we tell Mintek to spend effort on.

Method: split each section into a grid of sub-fields, compute liberation
independently within each using the same refined estimator as the pipeline, and
report the spread across sub-fields of the same section. Sub-fields with no
payload are skipped rather than counted as zero - "no measurement" and "zero
liberation" are different statements, the same distinction the advisor makes.
"""
import argparse
import json
import statistics

import numpy as np
from PIL import Image

from . import modal
from .segmentation import config, lumenstone as ls

Image.MAX_IMAGE_PIXELS = None


def truth_labels(stem):
    array = np.array(Image.open(ls.DATA_DIR / "masks" / "test" / f"{stem}.png"))
    if array.ndim == 3:
        array = array[:, :, 0]
    return ls._LOOKUP[array.astype(np.int64)].numpy()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--grid", type=int, default=3,
                        help="split each section into grid x grid sub-fields")
    args = parser.parse_args()

    _, _, test_ids = ls.split_ids()
    rows, all_spreads = [], []

    print(f"\n{ls.SUBSET}: liberation across {args.grid}x{args.grid} sub-fields "
          f"of the same section, ground truth only\n")
    print(f"{'section':10s}{'whole':>8s}{'sub-field mean':>16s}"
          f"{'std':>8s}{'min':>7s}{'max':>7s}{'n':>4s}")
    print("-" * 60)

    for stem in sorted(test_ids):
        labels = truth_labels(stem)
        whole = modal.analyse(labels, ls.CLASS_NAMES, refine=True).liberation
        height, width = labels.shape
        step_y, step_x = height // args.grid, width // args.grid

        values = []
        for gy in range(args.grid):
            for gx in range(args.grid):
                tile = labels[gy * step_y:(gy + 1) * step_y,
                              gx * step_x:(gx + 1) * step_x]
                result = modal.analyse(tile, ls.CLASS_NAMES, refine=True)
                # Skip sub-fields with no measurable payload: "no measurement"
                # is not "zero liberation".
                if result.liberation is not None and result.payload_pixels > 0:
                    values.append(result.liberation)

        if len(values) < 2:
            print(f"{stem:10s}{'-':>8s}{'too few measurable sub-fields':>40s}")
            continue

        spread = statistics.pstdev(values)
        all_spreads.append(spread)
        rows.append({"id": stem, "whole_section": whole,
                     "sub_field_mean": sum(values) / len(values),
                     "sub_field_std": spread,
                     "sub_field_min": min(values), "sub_field_max": max(values),
                     "n_sub_fields": len(values)})
        shown = "n/a" if whole is None else f"{whole:.2f}"
        print(f"{stem:10s}{shown:>8s}{sum(values)/len(values):>16.2f}"
              f"{spread:>8.2f}{min(values):>7.2f}{max(values):>7.2f}"
              f"{len(values):>4d}")

    if not all_spreads:
        print("no sections had enough measurable sub-fields")
        return

    mean_spread = sum(all_spreads) / len(all_spreads)
    print("-" * 60)
    print(f"mean within-section standard deviation: {mean_spread:.3f}")
    print(f"median: {statistics.median(all_spreads):.3f}   "
          f"max: {max(all_spreads):.3f}")
    print("\ncompare against model liberation error on the same sections:")
    print("  S2 patch + refined   MAE 0.089")
    print("  S1 patch + refined   MAE 0.203")
    print(f"\nA single field of view carries an inherent liberation uncertainty "
          f"of about {mean_spread:.2f} on this data, before any model error. "
          f"{'That is COMPARABLE TO OR LARGER THAN our model error, so imaging '
             'more fields matters at least as much as a better network.'
           if mean_spread >= 0.089 else
           'That is smaller than our model error, so model quality remains the '
           'binding constraint.'}")

    out = config.REPORT_DIR / f"sampling_error_{ls.SUBSET.lower()}.json"
    with open(out, "w") as f:
        json.dump({"subset": ls.SUBSET, "grid": args.grid,
                   "mean_within_section_std": mean_spread,
                   "median_within_section_std": statistics.median(all_spreads),
                   "sections": rows}, f, indent=2)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
