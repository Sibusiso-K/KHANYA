"""Renders the REEFPRINT :: KHANYA Jinja2 dashboard from real pipeline output.

    render(image, labels, mean_confidence, result, recommendation) -> html str

Every value fed to templates/khanya.html.jinja is measured, not asserted - see
that file's own header comment for what was cut from the Stitch mockup and
why. Jinja2 is already a Streamlit dependency, not a new one (SBOM.md
unaffected). static/tailwind.css and static/fonts/ are build-time artefacts,
committed as static assets - see dashboard/build/README.md to regenerate them,
never regenerated at demo time.
"""
import base64
import io
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from PIL import Image

from src import advisor as advisor_module
from src.advisor import verdict_state

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "static"
_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True,
                   undefined=StrictUndefined)


def _read_text(relative):
    path = STATIC_DIR / relative
    if not path.exists():
        raise FileNotFoundError(
            f"{path} missing. Run dashboard/build/README.md's compile step "
            "once to generate the static CSS/fonts before running the dashboard."
        )
    return path.read_text(encoding="utf-8")


def _read_b64(relative):
    path = STATIC_DIR / relative
    if not path.exists():
        raise FileNotFoundError(
            f"{path} missing. Run dashboard/build/README.md's compile step "
            "once to generate the static CSS/fonts before running the dashboard."
        )
    return base64.b64encode(path.read_bytes()).decode("ascii")


# Read once at import time, not per request - these are static build
# artefacts, not per-render data.
_TAILWIND_CSS = _read_text("tailwind.css")
_FONT_SANS_B64 = _read_b64("fonts/PlusJakartaSans.ttf")
_FONT_MONO_REGULAR_B64 = _read_b64("fonts/JetBrainsMono-Regular.ttf")
_FONT_MONO_BOLD_B64 = _read_b64("fonts/JetBrainsMono-Bold.ttf")


def _base_context():
    """Assets shared by every Stitch-rendered dashboard state."""
    return {
        "tailwind_css": _TAILWIND_CSS,
        "font_sans_b64": _FONT_SANS_B64,
        "font_mono_regular_b64": _FONT_MONO_REGULAR_B64,
        "font_mono_bold_b64": _FONT_MONO_BOLD_B64,
    }


def render_landing(reason=None):
    """Render the pre-upload dashboard state from the same Stitch assets."""
    template = _env.get_template("landing.html.jinja")
    return template.render(
        **_base_context(),
        subset_label=f"LumenStone {os.environ.get('KHANYA_SUBSET', 'S2').upper()}",
        refusal_reason=reason,
    )


def _colourise_png_b64(labels):
    """Predicted-phase mask as a base64 PNG, embedded inline - no server-side
    static file needed for a per-request image, and no network fetch either."""
    from src.segmentation import lumenstone as ls

    rgb = np.zeros(labels.shape + (3,), dtype=np.uint8)
    for index, hex_colour in enumerate(ls.CLASS_COLORS):
        h = hex_colour.lstrip("#")
        rgb[labels == index] = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    buf = io.BytesIO()
    Image.fromarray(rgb).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _image_png_b64(image):
    """Original uploaded micrograph as an inline PNG for the component iframe."""
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _progress_image_b64(image, labels, tile_box):
    """Render only labels produced so far and mark the tile just classified."""
    from PIL import ImageDraw

    base = image.convert("RGB").copy()
    base.thumbnail((900, 600), Image.Resampling.LANCZOS)
    scale_x = base.width / image.width
    scale_y = base.height / image.height
    draw = ImageDraw.Draw(base)
    left, top, right, bottom = tile_box
    draw.rectangle((left * scale_x, top * scale_y, right * scale_x, bottom * scale_y),
                   outline="#FFB539", width=max(2, round(4 * scale_x)))
    buf = io.BytesIO()
    base.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def render_progress(image, labels, completed, total, tile_box, tile_confidence):
    """Render a truthful intermediate frame during native tiled inference."""
    template = _env.get_template("progress.html.jinja")
    return template.render(
        **_base_context(),
        input_micrograph_b64=_image_png_b64(image),
        predicted_phases_b64=_colourise_png_b64(labels),
        progress_image_b64=_progress_image_b64(image, labels, tile_box),
        completed=completed,
        total=total,
        tile_confidence=tile_confidence,
    )


def _candidates(result, recommendation):
    """The two candidate actions for a marginal verdict, equally weighted.

    Only populated when the advisor is genuinely straddling the band - see
    conformal.py's action_set() for the same logic in the CLI tool. Mirrored
    here rather than imported because the CLI version speaks in different
    units (a conformal interval, not a point estimate); this is the
    dashboard's own honest phrasing of the same idea for a single field.
    """
    if not recommendation.action.startswith("Marginal"):
        return []
    floor = advisor_module.LOW_LIBERATION
    return [
        {
            "condition": f"if true liberation ≥ {floor:.0%}",
            "action": "Continue at current setpoint",
            "gate": "Confirm with a second optical field on the same section, "
                    "or an assay, before leaving the circuit unchanged.",
        },
        {
            "condition": f"if true liberation < {floor:.0%}",
            "action": "Grind finer",
            "gate": "Confirm the same way before spending mill power. "
                    "Regrinding on a measurement this close to the floor is "
                    "the expensive half of the error.",
        },
    ]


_VERDICT_CSS = {
    "": {
        "border": "border-success", "bg": "bg-surface-container", "glow": "shadow-glow-success",
        "dot": "bg-success", "pill": "bg-success-container border border-success text-success",
    },
    "grind": {
        "border": "border-primary", "bg": "bg-surface-container", "glow": "shadow-glow-danger",
        "dot": "bg-primary", "pill": "bg-danger-container border border-primary text-primary",
    },
    "hold": {
        "border": "border-warning", "bg": "bg-surface-container", "glow": "shadow-glow-warning",
        "dot": "bg-warning", "pill": "bg-warning-container border border-warning text-warning",
    },
}


def render(image, labels, mean_confidence, result, recommendation,
           mode_label="Full section, native resolution", elapsed_seconds=None):
    """Render the dashboard for one measured field. Returns an HTML string.

    mode_label, elapsed_seconds: which analysis path produced this result
    and how long it actually took, end to end, on this run - never a cached
    or estimated figure (Live Field Mode's caller must time a fresh,
    uncached call; see dashboard/app.py). elapsed_seconds is None for a
    caller that hasn't measured one (e.g. a direct-render test) - the
    template shows nothing rather than a fabricated number.
    """
    from src.segmentation import lumenstone as ls

    css_class, state_label = verdict_state(recommendation.action)
    css = _VERDICT_CSS[css_class]

    floor = advisor_module.LOW_LIBERATION
    margin = advisor_module.LIBERATION_MARGIN
    liberation_pct = None if result.liberation is None else round(result.liberation * 100, 1)

    phases = [
        {"name": name, "fraction": result.phase_fractions.get(name, 0.0), "colour": colour}
        for name, colour in zip(ls.CLASS_NAMES, ls.CLASS_COLORS)
        if name in result.phase_fractions
    ]
    phases.sort(key=lambda p: p["fraction"], reverse=True)

    template = _env.get_template("khanya.html.jinja")
    return template.render(
        **_base_context(),
        subset_label=f"LumenStone {ls.SUBSET}",
        model_name="DeepLabV3 · ResNet-50",
        model_checkpoint="KHANYA S2 native-patch checkpoint",
        model_scope="LumenStone S2 v2 analogue · Bushveld validation pending",
        sample_title="Uploaded polished section",
        sample_caption=(
            "Reflected-light micrograph, user-supplied. Every number below is "
            "measured from the predicted mask, not asserted."
        ),
        liberation_display="N/A" if liberation_pct is None else f"{liberation_pct:.0f}",
        liberation_pct=0 if liberation_pct is None else liberation_pct,
        liberation_floor_pct=round(floor * 100),
        confidence=mean_confidence,
        confidence_label="high" if mean_confidence >= 0.85 else "verify manually",
        ore_area_fraction=result.ore_area_fraction,
        n_particles=result.n_particles,
        input_micrograph_b64=_image_png_b64(image),
        predicted_phases_b64=_colourise_png_b64(labels),
        phases=phases,
        recommendation=recommendation,
        verdict_state_label=state_label,
        verdict_border_class=css["border"],
        verdict_bg_class=css["bg"],
        verdict_glow_class=css["glow"],
        verdict_dot_class=css["dot"],
        verdict_pill_class=css["pill"],
        candidates=_candidates(result, recommendation),
        band_visible=liberation_pct is not None,
        band_lo_pct=max(0.0, (floor - margin) * 100),
        band_width_pct=(min(1.0, floor + margin) - max(0.0, floor - margin)) * 100,
        is_refusal=css_class == "hold" and not recommendation.action.startswith("Marginal"),
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        mode_label=mode_label,
        elapsed_display=None if elapsed_seconds is None else f"{elapsed_seconds:.1f}",
    )
