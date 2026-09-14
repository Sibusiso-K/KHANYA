"""Offline dashboard for the measured KHANYA advisory pipeline.

Run with ``streamlit run dashboard/app.py``. The interactive upload control is
Streamlit-native; the result is the offline, inlined Stitch port rendered by
``dashboard.render`` inside a component iframe. Do not replace that renderer
with linked assets: a venue laptop may have no network access.
"""
import os
import sys
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
[data-testid="stFileUploader"] label p {
  color: #8CA6AE; font-family: Consolas, monospace;
  font-size: 0.76rem; font-weight: 700; letter-spacing: 0.12em;
}
[data-testid="stFileUploaderDropzone"] {
  background: #071C27; border: 1px dashed #194D5C; border-radius: 0.5rem;
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


def predict_live_field(image_bytes, checkpoint_key):
    """The Live Field Mode fast path: one field, one forward pass, timed
    end to end on THIS call. Deliberately not @st.cache_data - a cached
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
    with torch.no_grad():
        labels, mean_confidence, field = patch_module.single_field_predict(model, image, dev)
    elapsed = time.perf_counter() - start
    return field, labels, mean_confidence, elapsed


landing_slot = st.empty()
progress_slot = st.empty()
LIVE_FIELD_LABEL = "Live Field Mode — fast, 512×512 field, timed live"
FULL_SECTION_LABEL = "Full section — slow, native resolution, whole image"
EVIDENCE_LABEL = "Evidence — held-out S2 test set"
mode = st.radio(
    "ANALYSIS MODE",
    [LIVE_FIELD_LABEL, FULL_SECTION_LABEL, EVIDENCE_LABEL],
    horizontal=True,
    help=(
        "Live Field Mode analyses one 512×512 field with a single model "
        "pass, measured end to end on every run (JUDGE-READY-WORKPLAN.md: "
        "full-section inference measures p95 196s, about 6.5x over the "
        "review's 30s design target — unworkable as a live demo beat). "
        "Full section is the validated whole-image path used for the "
        "backup recording (BACKUP-DEMO-SCRIPT.md). Evidence is a separate "
        "view over known held-out S2 test images and never uses live uploads."
    ),
)

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

        # Changing a checkpoint must invalidate both model and prediction caches.
        stat = CKPT.stat()
        checkpoint_key = (str(CKPT), stat.st_mtime_ns, stat.st_size)

        if mode == LIVE_FIELD_LABEL:
            with st.spinner(
                "Live Field Mode — one 512×512 field, one model pass, "
                "timed live. Not cached: every run measures fresh."
            ):
                image, labels, mean_confidence, elapsed = predict_live_field(
                    image_bytes, checkpoint_key
                )
            mode_label = f"{LIVE_FIELD_LABEL.split(' — ')[0]}, 512×512 field"
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
        html = render.render(image, labels, mean_confidence, result, recommendation,
                             mode_label=mode_label, elapsed_seconds=elapsed)
    except (ImportError, OSError, RuntimeError, ValueError) as exc:
        show_landing(f"Analysis could not complete: {exc}")
    else:
        landing_slot.empty()
        progress_slot.empty()
        st.components.v1.html(html, height=RESULT_FRAME_HEIGHT, scrolling=True)
