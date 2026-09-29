"""Offline dashboard for the measured KHANYA advisory pipeline.

Run with ``streamlit run dashboard/app.py``. The interactive upload control is
Streamlit-native; the result is the offline, inlined Stitch port rendered by
``dashboard.render`` inside a component iframe. Do not replace that renderer
with linked assets: a venue laptop may have no network access.
"""
import os
import sys
import time
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dashboard import render
from dashboard.inputs import load_image, unavailable_reason
from src.segmentation import config


SUBSET = os.environ.get("KHANYA_SUBSET", "S2").upper()
CKPT = config.ROOT / "checkpoints" / f"lumenstone_{SUBSET.lower()}_patches" / "best.pt"
RESULT_FRAME_HEIGHT = 1500
LANDING_FRAME_HEIGHT = 330

# Streamlit remains the upload/model bridge, but it must not look like a
# second dashboard wrapped around the actual Stitch interface. These rules
# remove its chrome and make the one native control visually recede into the
# same offline palette. All result layout still comes from the Jinja template.
UPLOAD_BRIDGE_CSS = """
<style>
[data-testid="stAppViewContainer"], [data-testid="stMain"] {
  background: #00131D;
}
[data-testid="stHeader"], footer, #MainMenu { display: none; }
.block-container { max-width: 1760px; padding: 0.75rem 1rem 2rem; }
[data-testid="stFileUploader"] {
  max-width: 1720px; margin: 0.85rem auto 1.1rem;
  color: #E3EAEB; font-family: "Segoe UI", sans-serif;
}
[data-testid="stRadio"] > label {
  color: #8CA6AE; font-family: "JetBrains Mono", Consolas, monospace;
  font-size: 0.68rem; font-weight: 700; letter-spacing: 0.12em;
  text-transform: uppercase; margin-bottom: 0.35rem;
}
[data-testid="stRadio"] div[role="radiogroup"] {
  display: flex; gap: 4px; padding: 4px; width: fit-content;
  background: #000D14; border: 1px solid #1E3E4B; border-radius: 0.5rem;
}
[data-testid="stRadio"] div[role="radiogroup"] label {
  margin: 0; padding: 0.55rem 0.8rem; border: 1px solid transparent;
  border-radius: 0.3rem; color: #8CA6AE; background: #0B222E;
  transition: background .15s ease, color .15s ease, border-color .15s ease;
}
[data-testid="stRadio"] div[role="radiogroup"] label:hover {
  border-color: #194D5C; color: #E3EAEB; background: #102C3B;
}
[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
  color: #E3EAEB; background: #194D5C; border-color: #2EA5BC;
  box-shadow: 0 0 0 1px rgba(46,165,188,.18);
}
[data-testid="stRadio"] div[role="radiogroup"] input {
  position: absolute; opacity: 0; width: 1px; height: 1px;
}
[data-testid="stFileUploader"] label p {
  color: #8CA6AE; font-family: Consolas, monospace;
  font-size: 0.76rem; font-weight: 700; letter-spacing: 0.12em;
}
[data-testid="stFileUploaderDropzone"] {
  background: #071C27; border: 1px dashed #2EA5BC; border-radius: 0.5rem;
  padding: 1.4rem 1rem; box-shadow: inset 0 0 0 1px rgba(46,165,188,.08);
  transition: border-color .15s ease, background .15s ease;
}
[data-testid="stFileUploaderDropzone"]:hover {
  background: #0B222E; border-color: #FFB539;
}
[data-testid="stFileUploader"] svg { color: #2EA5BC; }
[data-testid="stTooltipIcon"] { color: #8CA6AE; }
button:focus, input:focus, [role="radiogroup"] label:focus-within {
  outline: 2px solid #FFB539 !important; outline-offset: 2px;
}
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzone"] small { color: #8CA6AE; }
[data-testid="stFileUploaderDropzone"] button {
  background: #D22D20; border: 1px solid #D22D20; color: white;
  border-radius: 0.25rem; font-weight: 700;
}
[data-testid="stSpinner"] { color: #FFB539; }
iframe[title="st.iframe"] { background: #00131D; }
</style>
"""

st.set_page_config(page_title="KHANYA — ore processability advisor", layout="wide")
st.markdown(UPLOAD_BRIDGE_CSS, unsafe_allow_html=True)


@st.cache_resource
def load_model(checkpoint_key):
    import torch

    from src.segmentation import lumenstone as ls
    from src.segmentation.model import build_model, device

    dev = device()
    model = build_model(num_classes=ls.NUM_CLASSES, pretrained=False).to(dev)
    model.load_state_dict(torch.load(CKPT, map_location=dev))
    model.eval()
    return model, dev


@st.cache_data(show_spinner=False)
def predict(image_bytes, checkpoint_key):
    """Run the validated native-resolution path, caching only identical bytes."""
    import torch

    from src.segmentation import patches as patch_module

    image = load_image(image_bytes)
    model, dev = load_model(checkpoint_key)
    with torch.no_grad():
        labels, mean_confidence = patch_module.sliding_window_predict(model, image, dev)
    return image, labels, mean_confidence


def predict_with_progress(image_bytes, checkpoint_key, progress_callback):
    """Run the native tiled path while reporting each completed tile."""
    import torch
    from src.segmentation import patches as patch_module

    image = load_image(image_bytes)
    model, dev = load_model(checkpoint_key)
    with torch.no_grad():
        labels, mean_confidence = patch_module.sliding_window_predict(
            model, image, dev, progress_callback=progress_callback
        )
    return image, labels, mean_confidence


def predict_live_field(image_bytes, checkpoint_key, progress_callback=None, reimage=False):
    """The live path: six native-resolution fields sampled across the section,
    one forward pass each, timed end to end on THIS call, including drawing the
    progress frames. A single centre field held 0-20 payload particles and never
    matched the whole section's advice on the held-out set; six fields matched on
    9 of 12 (reports/field_sampling_s2.json). Deliberately not @st.cache_data - a cached
    result reused across uploads would report a stale timing as if it were
    fresh, which is exactly the thing a live demo must not do (JUDGE-READY-
    WORKPLAN.md: "never use cached output as a fresh timing result").
    """
    import time

    import torch

    from src.segmentation import patches as patch_module

    # Model load is a one-time, cache_resource-backed setup cost, not part of
    # per-upload inference latency - loaded before the timer starts, same as
    # latency_benchmark.py's warmup calls being excluded from its measurement.
    model, dev = load_model(checkpoint_key)
    start = time.perf_counter()
    image = load_image(image_bytes)
    if reimage:
        from src.stability import reimaged
        image = reimaged(image)
    with torch.no_grad():
        labels, mean_confidence, mosaic, _boxes = patch_module.multi_field_predict(
            model, image, dev, progress_callback=progress_callback)
    elapsed = time.perf_counter() - start
    return mosaic, labels, mean_confidence, elapsed


landing_slot = st.empty()
progress_slot = st.empty()
opcua_slot = st.empty()
LIVE_FIELD_LABEL = "Live sampled fields — six 512×512 fields across the section, timed live"
FULL_SECTION_LABEL = "Full section — slow, native resolution, whole image"
EVIDENCE_LABEL = "Evidence — held-out S2 test set"
mode = st.radio(
    "ANALYSIS MODE",
    [LIVE_FIELD_LABEL, FULL_SECTION_LABEL, EVIDENCE_LABEL],
    horizontal=True,
    help=(
        "Live sampled fields analyses six 512×512 fields spread across the "
        "section, one model pass each, measured end to end on every run. A "
        "single centre field never matched the whole section's advice on the "
        "held-out set; six fields matched on 9 of 12 (JUDGE-READY-WORKPLAN.md: "
        "full-section inference measures p95 196s, about 6.5x over the "
        "review's 30s design target — unworkable as a live demo beat). "
        "Full section is the validated whole-image path used for the "
        "backup recording (BACKUP-DEMO-SCRIPT.md). Evidence is a separate "
        "view over known held-out S2 test images and never uses live uploads."
    ),
)

if "force_stale_opcua" not in st.session_state:
    st.session_state.force_stale_opcua = False
presenter = st.expander("Presenter controls", expanded=False)
stale_demo = presenter.button(
    "TRIGGER STALE OPC UA REFUSAL",
    help="The next live result is emitted with an expired validity window so the separate consumer must refuse it.",
)
if stale_demo:
    st.session_state.force_stale_opcua = True
    presenter.info("Stale refusal armed for the next upload. It is not applied to a result already on screen.")

# The simulated plant outlives a single upload, so a command's before/after is real state.
# A command belongs to one upload in one mode: Streamlit reruns the whole script on every
# click, and without `commanded` a Reset would immediately re-command the image on screen.
reset_plant = presenter.button(
    "RESET SIMULATED PLANT",
    help="Return the simulated regrind tag to 0 (bypass) and clear the command log.",
)
if "plant" not in st.session_state:
    st.session_state.plant = {"regrind_enabled": 0.0, "log": [], "commanded": None, "status": None}
if reset_plant:
    st.session_state.plant.update(regrind_enabled=0.0, log=[], status=None)

def show_landing(reason=None):
    with landing_slot.container():
        st.components.v1.html(
            render.render_landing(reason), height=LANDING_FRAME_HEIGHT, scrolling=True
        )


reason = unavailable_reason(SUBSET, CKPT)
if mode == EVIDENCE_LABEL:
    progress_slot.empty()
    if reason:
        show_landing(f"Evidence unavailable: {reason}")
        st.stop()
    try:
        from src.segmentation import lumenstone as ls
        _train_ids, _val_ids, test_ids = ls.split_ids()
        evidence_stem = st.selectbox(
            "HELD-OUT S2 TEST SECTION",
            sorted(test_ids),
            help="Selection is restricted to the real held-out test IDs returned by the dataset split.",
        )
        evidence_image_path = ls.DATA_DIR / "imgs" / "test" / f"{evidence_stem}.jpg"
        evidence_image = load_image(evidence_image_path.read_bytes())
        from src.segmentation.patches import labels_for
        evidence_labels = labels_for(evidence_stem, "test")
        evidence_bytes = evidence_image_path.read_bytes()
        stat = CKPT.stat()
        evidence_checkpoint_key = (str(CKPT), stat.st_mtime_ns, stat.st_size)
        with st.spinner("Running the real native-resolution model on the selected held-out section…"):
            _image, evidence_predicted, evidence_confidence = predict(
                evidence_bytes, evidence_checkpoint_key
            )
        st.components.v1.html(
            render.render_evidence(
                evidence_stem, evidence_image, evidence_labels,
                evidence_predicted, evidence_confidence, len(test_ids),
            ),
            height=850, scrolling=True,
        )
    except (FileNotFoundError, ImportError, OSError, RuntimeError, ValueError) as exc:
        show_landing(f"Evidence unavailable: {exc}")
    st.stop()

uploaded = st.file_uploader(
    "REFLECTED-LIGHT MICROGRAPH OF A POLISHED SECTION",
    type=["jpg", "jpeg", "png", "tif", "tiff"],
)
if uploaded is None:
    show_landing(reason)
else:
    if reason:
        show_landing(reason)
        st.stop()
    try:
        image_bytes = uploaded.getvalue()
        load_image(image_bytes)  # Decode before starting expensive model work.
        from src import modal
        from src.advisor import advise
        from src.segmentation import lumenstone as ls
        from dashboard.opcua import publish_result
        from dashboard.control import REGRIND_HEAD, send_command

        # Changing a checkpoint must invalidate both model and prediction caches.
        stat = CKPT.stat()
        checkpoint_key = (str(CKPT), stat.st_mtime_ns, stat.st_size)

        if mode == LIVE_FIELD_LABEL:
            with st.spinner(
                "Six fields across the section, one model pass each, timed "
                "live. Not cached: every run measures fresh."
            ):
                field_image = load_image(image_bytes)

                def on_field(completed, total, partial_labels, box, confidence):
                    with progress_slot.container():
                        st.components.v1.html(
                            render.render_progress(field_image, partial_labels, completed,
                                                   total, box, confidence),
                            height=700, scrolling=False,
                        )

                image, labels, mean_confidence, elapsed = predict_live_field(
                    image_bytes, checkpoint_key, on_field
                )
            with st.spinner(
                "Lighting check: the same six fields, re-measured after the "
                "lighting shift measured between real re-imagings of the same sections."
            ):
                from src.stability import reimaged
                field_image = reimaged(load_image(image_bytes))
                shifted_image, shifted_labels, shifted_confidence, shifted_elapsed = (
                    predict_live_field(image_bytes, checkpoint_key, on_field, reimage=True))
            elapsed += shifted_elapsed
            mode_label = "Live sampled fields, six 512×512 fields, lighting-checked"
        else:
            with st.spinner(
                "Tiling and predicting at native resolution — each frame below is "
                "updated after a real tile classification."
            ):
                progress_image = load_image(image_bytes)

                def on_tile(completed, total, partial_labels, tile_box, tile_confidence):
                    # st.empty() returns a DeltaGenerator, which has no
                    # .components attribute - st.components.v1.html is a
                    # module-level function, not a DeltaGenerator method.
                    # Same pattern already used correctly for landing_slot
                    # above (with landing_slot.container(): ...).
                    with progress_slot.container():
                        st.components.v1.html(
                            render.render_progress(
                                progress_image, partial_labels, completed,
                                total, tile_box, tile_confidence,
                            ),
                            height=700, scrolling=False,
                        )

                image, labels, mean_confidence = predict_with_progress(
                    image_bytes, checkpoint_key, on_tile
                )
            elapsed = None
            mode_label = "Full section, native resolution"

        result = modal.analyse(labels, ls.CLASS_NAMES, refine=True)
        recommendation = advise(result, mean_confidence)
        lighting = None
        if mode == LIVE_FIELD_LABEL:
            from src import stability
            as_imaged = recommendation
            after_shift = advise(modal.analyse(shifted_labels, ls.CLASS_NAMES, refine=True),
                                 shifted_confidence)
            recommendation = stability.gate(as_imaged, after_shift.action)
            lighting = {
                "as_imaged": as_imaged.action, "after_shift": after_shift.action,
                "image": image, "shifted_image": shifted_image,
                "stable": after_shift.action == as_imaged.action,
                "abstained": stability.is_abstaining(as_imaged.action),
            }
        opcua_values = {"model_confidence": float(mean_confidence * 100.0)}
        if result.liberation is not None:
            opcua_values["association_index"] = float(result.liberation * 100.0)
        segmentation_refused = result.liberation is None
        # The run the arming click itself triggers must not consume it.
        stale_requested = False if stale_demo else st.session_state.pop("force_stale_opcua", False)
        opcua_status = publish_result(
            opcua_values,
            stale=stale_requested or segmentation_refused,
            stale_reason=("segmentation refusal" if segmentation_refused
                          else "presenter demonstration"),
            on_event=lambda message: opcua_slot.info(message),
        )
        plant = st.session_state.plant
        command_key = (uploaded.file_id, mode)
        if command_key != plant["commanded"] or stale_requested:
            command = send_command(
                recommendation.action, plant[REGRIND_HEAD], stale=stale_requested,
                on_event=lambda message: opcua_slot.info(message),
            )
            plant.update({REGRIND_HEAD: command.after, "commanded": command_key, "status": command})
            plant["log"].append({
                "time": time.strftime("%H:%M:%S"),
                "image": uploaded.name,
                "advisory": recommendation.action,
                "command": command.state,
                "regrind_enabled": f"{command.before:g} → {command.after:g}",
                "reason": command.reason,
            })
        command = plant["status"]
        evidence_scope = ("six 512 px fields, 18% of the section"
                          if mode == LIVE_FIELD_LABEL else "whole section, native resolution")
        html = render.render(image, labels, mean_confidence, result, recommendation,
                             mode_label=mode_label, elapsed_seconds=elapsed,
                             opcua_status=opcua_status, plant=command,
                             lighting=lighting, evidence_scope=evidence_scope)
    except (ImportError, OSError, RuntimeError, ValueError) as exc:
        show_landing(f"Analysis could not complete: {exc}")
    else:
        landing_slot.empty()
        progress_slot.empty()
        opcua_slot.empty()
        st.components.v1.html(html, height=RESULT_FRAME_HEIGHT, scrolling=True)
        with st.expander("Command log and lighting-check detail", expanded=False):
            if lighting is not None:
                imaged_col, shifted_col = st.columns(2)
                imaged_col.image(lighting["image"], caption=f"As imaged: {lighting['as_imaged']}",
                                 use_container_width=True)
                shifted_col.image(lighting["shifted_image"],
                                  caption=f"After the re-imaging shift: {lighting['after_shift']}",
                                  use_container_width=True)
            if command is None:
                st.write(f"Simulated plant reset: regrind_enabled = "
                         f"{st.session_state.plant['regrind_enabled']:g}. Upload an image to command it.")
            st.dataframe(st.session_state.plant["log"], use_container_width=True, hide_index=True)
