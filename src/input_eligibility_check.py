"""Would a colour-balance rule refuse inputs that are not micrographs from this set-up?

Shipped as the dashboard's COLOUR-CAST CHECK (dashboard/inputs.py), not as an
out-of-domain detector: warm-toned non-micrographs pass it (Lethabo, PR #11 and
#17 reviews). What may touch the plant is decided by dashboard/validated_samples.json.

Evidence for finding 1 of reports/PREPROD-TEST-2026-09-30.md: a screenshot of
text and a greyscale copy of test_11 were measured, advised on and published
over OPC UA. This script measures, and does not wire anything into the app.

The candidate rule has no fitted threshold. An image is eligible when it has
colour at all (mean pairwise channel difference >= 1 level) and carries the
warm cast every S2 image has on average (mean R - G > 0 and mean G - B > 0).
The 12 held-out test sections are reported descriptively; nothing here was
chosen by looking at them. Each image is also checked after the lighting
check's fixed darkening, so the gate cannot refuse the copy that check makes.

Usage: python -m src.input_eligibility_check
Writes reports/input_eligibility.json
"""
import glob
import json

import numpy as np
from PIL import Image

from src.segmentation import config
from src.segmentation import lumenstone as ls
from src.stability import REIMAGING_SHIFT_RGB

CHROMA_FLOOR = 1.0
RAW = config.ROOT / "data" / "raw" / "lumenstone"


def features(rgb):
    a = np.asarray(rgb, dtype=np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    chroma = float((np.abs(r - g) + np.abs(g - b) + np.abs(r - b)).mean() / 3)
    return {"chroma": chroma, "r_minus_g": float((r - g).mean()), "g_minus_b": float((g - b).mean())}


def eligible(f):
    return f["chroma"] >= CHROMA_FLOOR and f["r_minus_g"] > 0 and f["g_minus_b"] > 0


def load(path):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)


def summarise(paths):
    rows, darkened_pass = [], 0
    for path in paths:
        image = load(path)
        f = features(image)
        darkened_pass += eligible(features(np.clip(image + np.array(REIMAGING_SHIFT_RGB), 0, 255)))
        rows.append({"image": str(path).replace("\\", "/").split("lumenstone/")[-1], **f, "eligible": eligible(f)})
    ranges = {k: [round(min(r[k] for r in rows), 2), round(max(r[k] for r in rows), 2)]
              for k in ("chroma", "r_minus_g", "g_minus_b")} if rows else {}
    return {"n": len(rows), "eligible": sum(r["eligible"] for r in rows),
            "eligible_after_lighting_shift": int(darkened_pass), "ranges": ranges,
            "refused": [r["image"] for r in rows if not r["eligible"]]}


def main():
    train, val, test = ls.split_ids()
    imgs = ls.DATA_DIR / "imgs"
    sets = {
        "S2 train": [imgs / "train" / f"{s}.jpg" for s in train],
        "S2 validation": [imgs / "train" / f"{s}.jpg" for s in val],
        "S2 test (descriptive)": [imgs / "test" / f"{s}.jpg" for s in test],
        "S1 v2 (other ore, LumenStone set-up)": sorted(glob.glob(str(RAW / "S1_v2" / "imgs" / "**" / "*.jpg"), recursive=True)),
        "S3 v1 (other ore, LumenStone set-up)": sorted(glob.glob(str(RAW / "S3_v1" / "imgs" / "**" / "*.jpg"), recursive=True)),
        "V1 (re-imaged on another set-up)": sorted(glob.glob(str(RAW / "V1_v1" / "**" / "*.jpg"), recursive=True)),
    }
    grey = np.asarray(Image.open(imgs / "test" / "test_11.jpg").convert("L").convert("RGB"), dtype=np.float32)
    report = {
        "rule": {"chroma_floor": CHROMA_FLOOR, "requires": "mean R-G > 0 and mean G-B > 0",
                 "fitted_thresholds": 0},
        "sets": {name: summarise(paths) for name, paths in sets.items()},
        "hostile": {
            "test_11 converted to greyscale": {**features(grey), "eligible": eligible(features(grey))},
            "screenshot of text (local test input, not in repo)": {
                "chroma": 21.8, "r_minus_g": -23.56, "g_minus_b": -7.26, "eligible": False,
                "note": "measured 30 Sept on the file used in the live test"},
        },
    }
    out = config.ROOT / "reports" / "input_eligibility.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    for name, s in report["sets"].items():
        print(f"{name:40s} eligible {s['eligible']}/{s['n']}  after lighting shift {s['eligible_after_lighting_shift']}/{s['n']}")
    for name, h in report["hostile"].items():
        print(f"{name:40s} {'eligible' if h['eligible'] else 'REFUSED'}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
