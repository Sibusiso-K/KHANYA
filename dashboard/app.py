"""Demo dashboard. Must run offline on one laptop - assume venue wifi fails.

    streamlit run dashboard/app.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import torch
from PIL import Image

from src import config
from src.advisor import advise
from src.data import build_transforms
from src.model import build_model, device


@st.cache_resource
def load_model():
    dev = device()
    model = build_model(pretrained=False).to(dev)
    model.load_state_dict(
        torch.load(config.CKPT_DIR / "best.pt", map_location=dev)
    )
    model.eval()
    return model, dev


st.title("Ore processability advisor")
st.caption("Mintek-SCi Grad Hackathon 2026 - Problem 3")

uploaded = st.file_uploader(
    "Reflected-light micrograph", type=["jpg", "jpeg", "png", "tif", "tiff"]
)

if uploaded:
    image = Image.open(uploaded).convert("RGB")
    st.image(image, width=400)

    model, dev = load_model()
    tensor = build_transforms(train=False)(image).unsqueeze(0).to(dev)
    with torch.no_grad():
        probabilities = model(tensor).softmax(1)[0].cpu()

    fractions = {name: probabilities[i].item() for i, name in enumerate(config.CLASSES)}

    st.subheader("Phase distribution")
    st.bar_chart(fractions)

    # Placeholder: a single-image classifier gives a distribution, not true modal
    # mineralogy. Replace with segmented area fractions once the segmentation
    # model lands in weeks 4-5, and say so out loud if asked before then.
    st.caption(
        "Fractions are classifier confidences, not segmented area fractions. "
        "Replaced by the segmentation model in the final build."
    )

    liberation = st.slider("Liberation (from segmentation)", 0.0, 1.0, 0.7)

    result = advise(fractions, liberation, probabilities.max().item())
    st.subheader("Recommendation")
    st.metric("Action", result.action)
    st.write(result.reason)
    st.caption(f"Confidence: {result.confidence}")
