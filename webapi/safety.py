"""Input eligibility for the workbench's advisory and local simulator paths."""
from src.input_checks import check_colour_cast, validated_sample


def check_input_colour(image):
    """Refuse inputs outside the measured colour range; this is not an OOD detector."""
    check_colour_cast(image)


def input_evidence(image_bytes: bytes) -> dict:
    """Eligibility evidence is bound to exact source bytes, never sample names."""
    stem = validated_sample(image_bytes)
    return {"verified": stem is not None, "verified_sample": stem}
