"""Lightweight upload checks, before loading the segmentation runtime."""
import io
import warnings
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError


def unavailable_reason(subset: str, checkpoint: Path) -> str | None:
    if subset != "S2":
        return (f"The advisory band was derived on S2; {subset} has no validated "
                "dashboard calibration. Use S2 or validate a separate calibration first.")
    if not checkpoint.is_file():
        return ("The validated S2 model checkpoint is missing. Restore "
                "checkpoints/lumenstone_s2_patches/best.pt before analysing an image.")
    return None


# Colour-cast check (pre-production finding 1). NOT an out-of-domain detector.
# It refuses images with no colour and images without the warm cast (mean
# R > G > B) every S2 image has, with no fitted threshold. It passes all 49 S2
# sections and their lighting-check copies, and refuses the greyscale and cool
# screenshot inputs and 20 of 30 V1 images from another imaging set-up
# (reports/input_eligibility.json, src/input_eligibility_check.py). A warm-toned
# picture that is not a micrograph still passes (Lethabo, PR #11/#17 reviews),
# which is why only validated samples may publish or command: see
# validated_sample() below.
CHROMA_FLOOR = 1.0


def colour_cast_reason(image: Image.Image) -> str | None:
    """Why this image's colour rules it out, or None. Passing proves nothing about the content."""
    import numpy as np

    rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    red, green, blue = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    chroma = float((np.abs(red - green) + np.abs(green - blue) + np.abs(red - blue)).mean() / 3)
    red_minus_green = float((red - green).mean())
    green_minus_blue = float((green - blue).mean())
    if chroma < CHROMA_FLOOR:
        return ("This image has no colour (greyscale or a monochrome camera). The model "
                "identifies minerals by colour; a greyscale copy of a real section reads "
                "the wrong phases.")
    if red_minus_green <= 0 or green_minus_blue <= 0:
        return (f"This image's colour balance (mean red-green {red_minus_green:+.1f}, "
                f"green-blue {green_minus_blue:+.1f}) is outside the warm cast of every "
                "reflected-light micrograph the model was validated on. It may not be a "
                "micrograph, or it comes from a camera or microscope that has not been "
                "characterised; characterise a new set-up before relying on its advice.")
    return None


def check_colour_cast(image: Image.Image) -> None:
    """Refuse, before any model pass, publish or command, an image whose colour rules it out."""
    reason = colour_cast_reason(image)
    if reason:
        raise ValueError(reason)


_VALIDATED = None


def validated_sample(image_bytes: bytes) -> str | None:
    """The held-out section this upload is, byte for byte, or None.

    Only these files may publish to or command the OPC UA simulator; every other
    upload is advisory only (Lethabo, PR #11 and #17 reviews). The manifest holds
    sha256 hashes only and is rebuilt by `python -m src.validated_samples`.
    """
    import hashlib
    import json

    global _VALIDATED
    if _VALIDATED is None:
        manifest = json.loads((Path(__file__).parent / "data" / "validated_samples.json").read_text(encoding="utf-8"))
        _VALIDATED = {digest: stem for stem, digest in manifest["sha256"].items()}
    return _VALIDATED.get(hashlib.sha256(image_bytes).hexdigest())


def load_image(image_bytes: bytes) -> Image.Image:
    """Decode fully while the stream is open; reject malformed or oversized data."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(image_bytes)) as image:
                image.load()
                return ImageOps.exif_transpose(image).convert("RGB")
    except (OSError, ValueError, UnidentifiedImageError,
            Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValueError("The upload could not be decoded safely. Choose an intact "
                         "JPG, PNG, or TIFF micrograph.") from exc

