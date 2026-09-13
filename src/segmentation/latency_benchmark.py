"""Segmentation-stage latency, using REEFPRINT's own timing instrument via the
bridge pattern (never reimplemented on this side - see polarimetry.py).

    python -m src.segmentation.latency_benchmark

WORKBOARD.md's P3 measured two REEFPRINT-side stages (Stokes inversion, the
OPC UA round trip) and explicitly named this one as unmeasured and needed in
"the same table". This is that measurement, reported the same way: mean, sd,
median, p95, honest n, named hardware - never a best case.

The review's two design targets (not yet-achieved claims):
    fresh 512x512 field  -> displayed result p95 <= 5s
    fresh full 3396x2547 image -> displayed result p95 <= 30s

n differs by two orders of magnitude between the two stages timed here
because a native-resolution whole-section call costs ~1000x a single patch
call - measure_stage's default n=30 assumes REEFPRINT's millisecond-scale
stages and would cost over an hour on the whole-section path. The smaller n
is reported as what it is, not disguised as the same statistical strength.
"""
import json

import torch
from PIL import Image

from . import config, lumenstone as ls, patches
from .model import build_model, device
from ..polarimetry import ensure_reefprint


def main():
    ensure_reefprint()
    from reefprint.trust.latency import current_hardware_description, measure_stage

    hardware = current_hardware_description()
    dev = device()
    ckpt = config.ROOT / "checkpoints" / f"lumenstone_{ls.SUBSET.lower()}_patches" / "best.pt"
    if not ckpt.is_file():
        raise FileNotFoundError(
            f"{ckpt} not found - this benchmark needs the trained checkpoint, "
            "same as the dashboard."
        )

    model = build_model(num_classes=ls.NUM_CLASSES, pretrained=False).to(dev)
    model.load_state_dict(torch.load(ckpt, map_location=dev))
    model.eval()

    measurements = []

    # Stage 1: one 512px patch through the network - the unit the sliding
    # window is built from. Cheap enough for a real n.
    patch = torch.zeros(1, 3, patches.PATCH, patches.PATCH, device=dev)

    @torch.no_grad()
    def run_patch():
        model(patch)["out"]

    patch_measurement = measure_stage(
        run_patch, stage=f"segmentation: one {patches.PATCH}px patch, model forward only",
        hardware=hardware, n=30, warmup=3,
    )
    print(patch_measurement.summary())
    measurements.append(patch_measurement)

    # Stage 2: sliding_window_predict on a real, full native-resolution test
    # section - the actual call the dashboard makes per upload. Minutes per
    # call, so n is small and stated as small, not disguised.
    _, _, test_ids = ls.split_ids()
    stem = sorted(test_ids)[0]
    image = Image.open(ls.DATA_DIR / "imgs" / "test" / f"{stem}.jpg")

    @torch.no_grad()
    def run_whole_section():
        patches.sliding_window_predict(model, image, dev)

    section_measurement = measure_stage(
        run_whole_section,
        stage=f"segmentation: whole native-resolution section ({stem}, "
              f"{image.width}x{image.height}), sliding-window inference only",
        hardware=hardware, n=3, warmup=0,
    )
    print(section_measurement.summary())
    measurements.append(section_measurement)

    print()
    print("NOT measured here, and not claimed: image decode, EXIF handling, "
          "topology repair, modal mineralogy, advisor logic, HTML render, "
          "Streamlit component round trip. This benchmark is the model-forward "
          "segmentation stage only - see dashboard/app.py's own spinner text "
          "for the current, unmeasured end-to-end estimate it should replace.")

    out = config.REPORT_DIR / "segmentation_latency.json"
    config.REPORT_DIR.mkdir(exist_ok=True)
    payload = {
        "measurements": [
            {
                "stage": m.stage,
                "hardware": m.hardware,
                "n": m.n,
                "mean_seconds": m.mean_seconds,
                "median_seconds": m.median_seconds,
                "stdev_seconds": m.stdev_seconds,
                "p95_seconds": m.p95_seconds,
                "seconds": list(m.seconds),
            }
            for m in measurements
        ],
        "not_measured": [
            "image decode / EXIF handling", "topology repair", "modal mineralogy",
            "advisor logic", "HTML render", "Streamlit component round trip",
        ],
        "design_targets_not_yet_achieved": {
            "fresh_512x512_field_p95_seconds": 5,
            "fresh_full_image_p95_seconds": 30,
            "source": "reports/TECHNICAL-REVIEW-2026-09-12.md, real-time decision section",
        },
    }
    with open(out, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
