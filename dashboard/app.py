"""Offline dashboard for the measured KHANYA advisory pipeline.

Run with ``streamlit run dashboard/app.py``. The interactive upload control is
Streamlit-native; the result is the offline, inlined Stitch port rendered by
``dashboard.render`` inside a component iframe. Do not replace that renderer
with linked assets: a venue laptop may have no network access.
"""
import io
import sys
from pathlib import Path

import streamlit as st
import torch
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dashboard import render
from src import modal
from src.advisor import advise
from src.segmentation import lumenstone as ls
from src.segmentation import patches as patch_module
from src.segmentation.model import build_model, device
from src.segmentation.train_patches import checkpoint_for


CKPT = checkpoint_for("ce")
RESULT_FRAME_HEIGHT = 1500

st.set_page_config(page_title="KHANYA — ore processability advisor", layout="wide")
st.title("REEFPRINT :: KHANYA")
st.caption(
    "Prototype — upload a reflected-light micrograph to measure modal mineralogy, "
    "liberation, and an advisory recommendation."
)


@st.cache_resource
def load_model():
    dev = device()
    model = build_model(num_classes=ls.NUM_CLASSES, pretrained=False).to(dev)
    model.load_state_dict(torch.load(CKPT, map_location=dev))
    model.eval()
    return model, dev


@st.cache_data(show_spinner=False)
def predict(image_bytes):
    """Run the validated native-resolution path, caching only identical bytes."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    model, dev = load_model()
    with torch.no_grad():
        labels, mean_confidence = patch_module.sliding_window_predict(model, image, dev)
    return image, labels, mean_confidence


if not CKPT.exists():
    st.error(f"No trained model at {CKPT}. Run: python -m src.segmentation.train_patches")
    st.stop()

uploaded = st.file_uploader(
    "REFLECTED-LIGHT MICROGRAPH OF A POLISHED SECTION",
    type=["jpg", "jpeg", "png", "tif", "tiff"],
)

if uploaded:
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
