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
