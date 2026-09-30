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


# Input eligibility (pre-production finding 1): a screenshot of text and a
# greyscale copy of test_11 were measured, advised on and published over OPC UA.
# The rule has no fitted threshold. The image must have colour at all, and the
# warm cast (mean R > G > B) every S2 image has. It passes all 49 S2 sections,
# including their lighting-check copies, and refuses both hostile inputs and 20
# of 30 V1 images from another imaging set-up (reports/input_eligibility.json,
# src/input_eligibility_check.py). It is a colour-cast check: a warm-toned
# picture that is not a micrograph would still pass.
CHROMA_FLOOR = 1.0


def eligibility_reason(image: Image.Image) -> str | None:
    """Why this image is not from the imaging set-up the model was validated on, or None."""
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


def check_eligible(image: Image.Image) -> None:
    """Refuse, before any model pass, publish or command, an input the model was not validated on."""
    reason = eligibility_reason(image)
    if reason:
        raise ValueError(reason)


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
