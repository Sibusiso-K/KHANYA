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
    Image.fromarray(rgb).save(buf, format="PNG", compress_level=1)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _image_png_b64(image):
    """Original uploaded micrograph as an inline PNG for the component iframe."""
    buf = io.BytesIO()
    image.save(buf, format="PNG", compress_level=1)
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
    base.save(buf, format="PNG", compress_level=1)
    return base64.b64encode(buf.getvalue()).decode("ascii")


# Progress frames are previews. Encoding a full 3396x2547 section twice per frame
# cost about 5 s each, 31 s of a live six-field pass (profiled 2026-09-30);
# screen-sized frames show the same thing. Measurement is unaffected: it runs
# on the full-resolution labels, never on these.
PROGRESS_MAX_SIDE = 900


def _preview_size(width, height):
    scale = min(1.0, PROGRESS_MAX_SIDE / max(width, height))
    return scale, (max(1, round(width * scale)), max(1, round(height * scale)))


def progress_preview(image):
    """The section at progress-frame size. Build once per pass and reuse per frame."""
    _, size = _preview_size(*image.size)
    return image.convert("RGB").resize(size, Image.Resampling.BILINEAR)


def render_progress(image, labels, completed, total, tile_box, tile_confidence):
    """Render a truthful intermediate frame during native tiled inference.

    `image` may already be a progress_preview; labels and tile_box are always in
    full-resolution coordinates and are scaled here.
    """
    height, width = np.asarray(labels).shape
    scale, size = _preview_size(width, height)
    if image.size != size:
        image = image.convert("RGB").resize(size, Image.Resampling.BILINEAR)
    if scale < 1.0:
        labels = np.asarray(Image.fromarray(np.asarray(labels).astype(np.uint8))
                            .resize(size, Image.Resampling.NEAREST))
        tile_box = tuple(round(v * scale) for v in tile_box)
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


def evidence_scores(stem, active_sha256):
    """This section's own score and both advisories, from the committed reports.

    None when a report is missing: the view then shows the images only rather
    than a number it cannot trace. When a report was produced by a different
    checkpoint from the active one, only that fact is returned, so saved scores
    never sit beside a prediction from another model (Lethabo, PR #13 review).
    """
    import json
    from src.segmentation import config
    try:
        stats = json.loads((config.REPORT_DIR / "s2_section_stats.json").read_text())
        sampling = json.loads((config.REPORT_DIR / "field_sampling_s2.json").read_text())
    except (OSError, ValueError):
        return None
    report_shas = {stats.get("checkpoint_sha256"), sampling.get("checkpoint_sha256")}
    if report_shas != {active_sha256}:
        return {"mismatch": True,
                "report_sha": ", ".join(sorted(str(s)[:12] for s in report_shas)),
                "active_sha": str(active_sha256)[:12]}
    stat_row = next((r for r in stats["rows"] if r["section"] == stem), None)
    sample_row = next((r for r in sampling["rows"] if r["section"] == stem), None)
    if stat_row is None or sample_row is None:
        return None
    model_advice = sample_row["model_whole"]["action"]
    expert_advice = sample_row["expert_whole"]["action"]
    return {
        "mismatch": False,
        "section_iou": stat_row["mean_iou_present_classes"],
        "pooled_iou": stats["pooled_mean_iou"],
        "model_advice": model_advice,
        "expert_advice": expert_advice,
        "agree": model_advice == expert_advice,
    }


def render_evidence(stem, image, ground_truth, predicted, mean_confidence,
                    n_test_images, source=None, scores=None):
    """Render a held-out test example; never used by the live upload path."""
    template = _env.get_template("evidence.html.jinja")
    return template.render(
        source=source,
        scores=scores,
        **_base_context(),
        stem=stem,
        n_test_images=n_test_images,
        input_micrograph_b64=_image_png_b64(image),
        ground_truth_b64=_colourise_png_b64(ground_truth),
        predicted_phases_b64=_colourise_png_b64(predicted),
        confidence=mean_confidence,
        # The saved advice is the advisor rules before the dashboard's confidence
        # gate; say so when the gate would withhold it (pre-production finding 3).
        withheld_by_gate=(scores is not None and not scores.get("mismatch")
                          and not scores["model_advice"].startswith(advisor_module.ABSTAINING_PREFIXES)
                          and mean_confidence < advisor_module.CONFIDENCE_FLOOR),
        confidence_floor=advisor_module.CONFIDENCE_FLOOR,
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


def _thumbnail_b64(image, width=160):
    """A small inline PNG for the control strip's lighting comparison."""
    small = image.convert("RGB").copy()
    small.thumbnail((width, width), Image.Resampling.LANCZOS)
    return _image_png_b64(small)


def _first_sentence(text):
    head, dot, _ = text.partition(". ")
    return head + ("." if dot else "")


def render(image, labels, mean_confidence, result, recommendation,
           mode_label="Full section, native resolution", elapsed_seconds=None,
           opcua_status=None, plant=None, lighting=None, evidence_scope=None,
           advisory_only=False, sample_stem=None):
    """Render the dashboard for one measured field. Returns an HTML string.

    mode_label, elapsed_seconds: which analysis path produced this result
    and how long it actually took on this run, from the upload being received
    by the server to the result being ready - never a cached or estimated
    figure (see dashboard/app.py). It excludes the browser's upload transfer
    and final drawing. advisory_only: the path issued no plant command (the
    full section, where the lighting check does not run). elapsed_seconds is None for a
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
        confidence_label=("high" if mean_confidence >= advisor_module.CONFIDENCE_FLOOR
                          else "verify manually"),
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
        opcua_status=opcua_status,
        # Control-room strip: decision, evidence and simulated plant in one row.
        action_headline=recommendation.action.replace(" - ", " — "),
        reason_first_sentence=_first_sentence(recommendation.reason),
        state_label=state_label,
        verdict_class=css_class,
        n_payload_particles=result.n_payload_particles,
        min_payload_particles=advisor_module.MIN_PAYLOAD_PARTICLES,
        evidence_scope=evidence_scope or mode_label,
        plant=plant,
        advisory_only=advisory_only,
        sample_stem=sample_stem,
        confidence_floor=advisor_module.CONFIDENCE_FLOOR,
        lighting=None if lighting is None else {
            **{k: lighting[k] for k in ("stable", "abstained", "as_imaged", "after_shift")},
            "off": lighting.get("off", False),
            "as_imaged_b64": _thumbnail_b64(lighting["image"]),
            "shifted_b64": (None if lighting["shifted_image"] is None
                            else _thumbnail_b64(lighting["shifted_image"])),
        },
    )


EXPLORE_MAX_SIDE = 1600


def _ids_png_b64(grain_map):
    """Grain ids as a 24-bit RGB PNG (id = R + 256 G + 65536 B), read back in the page."""
    ids = np.asarray(grain_map).astype(np.uint32)
    rgb = np.stack([(ids & 255), (ids >> 8) & 255, (ids >> 16) & 255], axis=-1).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(rgb).save(buf, format="PNG", compress_level=1)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _nearest(array, size):
    """Resize a label or id map to `size` (w, h) without inventing new values."""
    return np.asarray(Image.fromarray(np.asarray(array).astype(np.int32)).resize(size, Image.Resampling.NEAREST))


def render_explore(image, labels, report, phase_fractions, scope_note=""):
    """The Explore grains view: tap a grain for its composition; ore tables beside it.

    image and labels must share a shape (the live path's mosaic, or the full
    section). Both are shown at no more than EXPLORE_MAX_SIDE pixels; grain
    geometry is scaled to match, and sizes are reported in original pixels (or
    microns when src/grains.MICRONS_PER_PIXEL is set).
    """
    import json

    from src.segmentation import lumenstone as ls

    labels = np.asarray(labels)
    height, width = labels.shape
    scale = min(1.0, EXPLORE_MAX_SIDE / max(width, height))
    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    rgb = image.convert("RGB")
    if rgb.size != (width, height):
        rgb = rgb.resize((width, height), Image.Resampling.BILINEAR)
    shown = rgb.resize(size, Image.Resampling.BILINEAR) if scale < 1.0 else rgb
    shown_labels = _nearest(labels, size) if scale < 1.0 else labels
    shown_ids = _nearest(report.grain_map, size) if scale < 1.0 else report.grain_map
    buf = io.BytesIO()
    shown.save(buf, format="JPEG", quality=85)
    tables = _ore_tables(report, phase_fractions)
    colours = tables["colours"]
    unit = report.microns_per_pixel
    grains = {}
    for g in report.grains:
        d = g.as_dict()
        d["bbox"] = [int(v * scale) for v in d["bbox"]]   # display pixels, for the highlight only
        grains[g.id] = d                                     # ecd_px stays in original image pixels
    template = _env.get_template("explore.html.jinja")
    return template.render(
        micrograph_b64=base64.b64encode(buf.getvalue()).decode("ascii"),
        phases_b64=_colourise_png_b64(shown_labels),
        ids_b64=_ids_png_b64(shown_ids),
        grains_json=json.dumps(grains),
        colours_json=json.dumps(colours),
        # microns per original image pixel, or null: every size shown is in original pixels
        microns_per_pixel_json=json.dumps(unit),
        width=size[0], height=size[1],
        n_grains=report.n_grains, n_payload_grains=report.n_payload_grains,
        phases=tables["phases"], association=tables["association"], colour_of=tables["colour_of"],
        by_size=tables["by_size"], size_unit=tables["size_unit"], unit_note=tables["unit_note"],
        scope_note=scope_note,
    )


def _ore_tables(report, phase_fractions):
    """Composition, contacts and liberation-by-size rows, shared by Explore and the report."""
    from src.segmentation import lumenstone as ls

    colours = dict(zip(ls.CLASS_NAMES, ls.CLASS_COLORS))
    unit = report.microns_per_pixel
    fmt = (lambda v: f"{v * unit:.0f}") if unit else (lambda v: f"{v:g}")
    return {
        "colours": colours,
        "colour_of": {**colours, "resin": "#000000"},
        "phases": [{"name": name, "colour": colours[name],
                    "area_pct": 100.0 * phase_fractions.get(name, 0.0),
                    "wt_pct": report.weight_percent.get(name, 0.0)}
                   for name in ls.CLASS_NAMES if name != "background"],
        "association": [(name, sorted(parts.items(), key=lambda kv: -kv[1]), parts.get("resin", 0.0))
                        for name, parts in report.association.items()],
        "by_size": [{**b, "label": (f"{fmt(b['from_px'])}–{fmt(b['to_px'])}" if b["to_px"] is not None
                                    else f"≥ {fmt(b['from_px'])}")}
                    for b in report.liberation_by_size],
        "size_unit": "µm" if unit else "pixels",
        "unit_note": ("" if unit else "Sizes are in pixels: the imaging scale (microns per pixel) has not "
                      "been confirmed for these images."),
    }


def render_report(report, phase_fractions, *, file_name, file_sha, sample_stem, mode_label,
                  elapsed_seconds, checkpoint_sha, recommendation, mean_confidence, result,
                  evidence_scope, plant, opcua_status):
    """The printable sample report, with a client-side sample record and downloads."""
    import json

    from src.segmentation import lumenstone as ls

    tables = _ore_tables(report, phase_fractions)
    css_class, state_label = verdict_state(recommendation.action)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    phase_names = [n for n in ls.CLASS_NAMES if n != "background"]
    data = {
        "file_name": file_name, "file_sha256": file_sha, "validated_sample": sample_stem,
        "generated_at": generated_at, "mode": mode_label, "seconds_upload_to_result": round(elapsed_seconds, 1),
        "checkpoint_sha256": checkpoint_sha,
        "decision": {"action": recommendation.action, "reason": recommendation.reason, "state": state_label,
                     "model_confidence": round(float(mean_confidence), 4),
                     "confidence_gate": advisor_module.CONFIDENCE_FLOOR,
                     "payload_particles": result.n_payload_particles,
                     "payload_particle_floor": advisor_module.MIN_PAYLOAD_PARTICLES,
                     "association_index": None if result.liberation is None else round(float(result.liberation), 4)},
        "plant": None if plant is None else {"state": plant.state, "before": plant.before, "after": plant.after,
                                             "reason": plant.reason},
        "opcua": None if opcua_status is None else {"state": opcua_status.state, "message": opcua_status.message},
        "composition": {p["name"]: {"area_pct": round(p["area_pct"], 3), "est_weight_pct": round(p["wt_pct"], 3)}
                        for p in tables["phases"]},
        "mineral_contacts_pct": report.association,
        "liberation_by_size": report.liberation_by_size,
        "microns_per_pixel": report.microns_per_pixel,
        "phase_names": phase_names,
        "grains": [g.as_dict() for g in report.grains],
    }
    template = _env.get_template("report.html.jinja")
    return template.render(
        # JSON inside a <script>: no value (a file name is user input) may form a tag
        data_json=(json.dumps(data).replace("<", "\\u003c").replace(">", "\\u003e")
                   .replace("&", "\\u0026")),
        file_name=file_name, file_sha=file_sha, sample_stem=sample_stem, generated_at=generated_at,
        mode_label=mode_label, elapsed=elapsed_seconds, checkpoint_sha=checkpoint_sha,
        action=recommendation.action.replace(" - ", " — "), reason=recommendation.reason,
        confidence=mean_confidence, confidence_floor=advisor_module.CONFIDENCE_FLOOR,
        n_payload=result.n_payload_particles if result.n_payload_particles is not None else "?",
        min_payload=advisor_module.MIN_PAYLOAD_PARTICLES, evidence_scope=evidence_scope,
        plant_state=plant.state if plant else "none",
        plant_before=f"{plant.before:g}" if plant else "–", plant_after=f"{plant.after:g}" if plant else "–",
        plant_reason=plant.reason if plant else "no command",
        opcua=(f"{opcua_status.state}: {opcua_status.message}" if opcua_status else "not published"),
        phases=tables["phases"], association=tables["association"], by_size=tables["by_size"],
        size_unit=tables["size_unit"], unit_note=tables["unit_note"], n_grains=report.n_grains,
    )
