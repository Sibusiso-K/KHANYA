"""Which uploads may publish to, or command, the OPC UA simulator.

    python -m src.validated_samples

Writes src/data/validated_samples.json: the sha256 of each of the 12 held-out
S2 test sections, byte for byte (hashes only, no image data). Only these files,
the ones the accuracy report validates against expert annotation, may drive the
simulator. Any other upload is analysed and advised on, but publishes nothing
and commands nothing (Lethabo, PR #11 and #17 reviews: the colour-cast check is
not an out-of-domain detector, so an arbitrary upload must stay advisory-only).

A validated file that has been re-saved, converted or cropped is a different
file and is treated as unverified. src/preflight.py checks the test images on
the presenting machine still match this manifest.
"""
import hashlib
import json

from .segmentation import config, lumenstone as ls

MANIFEST = config.ROOT / "src" / "data" / "validated_samples.json"


def build():
    _, _, test_ids = ls.split_ids()
    samples = {}
    for stem in sorted(test_ids):
        data = (ls.DATA_DIR / "imgs" / "test" / f"{stem}.jpg").read_bytes()
        samples[stem] = hashlib.sha256(data).hexdigest()
    return {
        "purpose": ("files allowed to publish to or command the OPC UA simulator; "
                    "every other upload is advisory only"),
        "set": "LumenStone S2 v2, 12 held-out test sections",
        "sha256": samples,
    }


def main():
    manifest = build()
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {MANIFEST} ({len(manifest['sha256'])} samples)")


if __name__ == "__main__":
    main()
