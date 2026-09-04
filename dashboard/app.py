"""Offline dashboard for the measured KHANYA advisory pipeline.

Run with ``streamlit run dashboard/app.py``. The interactive upload control is
Streamlit-native; the result is the offline, inlined Stitch port rendered by
``dashboard.render`` inside a component iframe. Do not replace that renderer
with linked assets: a venue laptop may have no network access.
"""
import io
import os
import sys
from pathlib import Path

import streamlit as st
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dashboard import render
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
def load_model():
    import torch

    from src.segmentation import lumenstone as ls
    from src.segmentation.model import build_model, device

    dev = device()
    model = build_model(num_classes=ls.NUM_CLASSES, pretrained=False).to(dev)
    model.load_state_dict(torch.load(CKPT, map_location=dev))
    model.eval()
    return model, dev


@st.cache_data(show_spinner=False)
def predict(image_bytes):
    """Run the validated native-resolution path, caching only identical bytes."""
    import torch

    from src.segmentation import patches as patch_module

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    model, dev = load_model()
    with torch.no_grad():
        labels, mean_confidence = patch_module.sliding_window_predict(model, image, dev)
    return image, labels, mean_confidence


landing_slot = st.empty()
uploaded = st.file_uploader(
    "REFLECTED-LIGHT MICROGRAPH OF A POLISHED SECTION",
    type=["jpg", "jpeg", "png", "tif", "tiff"],
)

if uploaded is None:
    with landing_slot.container():
        st.components.v1.html(
            render.render_landing(), height=LANDING_FRAME_HEIGHT, scrolling=False
        )
else:
    landing_slot.empty()
    if not CKPT.exists():
        st.error(
            f"No trained model at {CKPT}. Copy the validated checkpoint to that "
            "path before analysing an image."
        )
        st.stop()

    from src import modal
    from src.advisor import advise
    from src.segmentation import lumenstone as ls

    image_bytes = uploaded.getvalue()
    with st.spinner(
        "Tiling and predicting at native resolution — about 2–3 minutes on a "
        "CPU-only laptop the first time; identical uploads are cached."
    ):
        image, labels, mean_confidence = predict(image_bytes)

    result = modal.analyse(labels, ls.CLASS_NAMES, refine=True)
    recommendation = advise(result, mean_confidence)
    html = render.render(image, labels, mean_confidence, result, recommendation)
    st.components.v1.html(html, height=RESULT_FRAME_HEIGHT, scrolling=True)
