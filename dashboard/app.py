"""Demo dashboard. Must run offline on one laptop - assume venue wifi fails.

    streamlit run dashboard/app.py

Full path, end to end: micrograph -> segmentation -> modal mineralogy ->
liberation by particle composition -> operational recommendation. Every number
shown is measured from the predicted mask. Nothing here is a slider.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import streamlit as st
import torch
from PIL import Image

from src import advisor as advisor_module, modal
from src.advisor import advise
from src.segmentation import lumenstone as ls
from src.segmentation.model import build_model, device
from src.segmentation.train_lumenstone import CKPT

st.set_page_config(page_title="Ore processability advisor", layout="wide")


@st.cache_resource
def load_model():
    dev = device()
    model = build_model(num_classes=ls.NUM_CLASSES, pretrained=False).to(dev)
    model.load_state_dict(torch.load(CKPT, map_location=dev))
    model.eval()
    return model, dev


def colourise(labels):
    rgb = np.zeros(labels.shape + (3,), dtype=np.uint8)
    for index, hex_colour in enumerate(ls.CLASS_COLORS):
        h = hex_colour.lstrip("#")
        rgb[labels == index] = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    return rgb


st.title("Ore processability advisor")
st.caption("Mintek-SCi Grad Hackathon 2026 - Problem 3 | LumenStone S2, Norilsk Group")

if not CKPT.exists():
    st.error(
        f"No trained model at {CKPT}. Run: python -m src.segmentation.train_lumenstone"
    )
    st.stop()

uploaded = st.file_uploader(
    "Reflected-light micrograph of a polished section",
    type=["jpg", "jpeg", "png", "tif", "tiff"],
)

if uploaded:
    image = Image.open(uploaded).convert("RGB")
    model, dev = load_model()

    x = ls.preprocess(image).to(dev)

    with torch.no_grad():
        logits = model(x)["out"][0]
        probabilities = logits.softmax(0)
        labels = probabilities.argmax(0).cpu().numpy()
        mean_confidence = probabilities.max(0).values.mean().item()

    left, right = st.columns(2)
    left.image(image, caption="Input", use_container_width=True)
    right.image(colourise(labels), caption="Predicted phases", use_container_width=True)

    # refine=True: raw connected components leave predicted liberation
    # uncorrelated with truth (+0.128). Repairing topology - speckle removal,
    # hole filling, watershed separation - takes that to +0.947. The demo must
    # show the pipeline we actually validated, not the one we superseded.
    result = modal.analyse(labels, ls.CLASS_NAMES, refine=True)

    st.subheader("Modal mineralogy")
    st.caption(
        "Area fractions are a proportion of ORE area, excluding mounting resin - "
        "otherwise every number would track how densely the section was mounted."
    )
    st.bar_chart(result.phase_fractions)

    a, b, c = st.columns(3)
    a.metric("Ore in field", f"{result.ore_area_fraction:.1%}")
    b.metric("Particles", result.n_particles)
    c.metric(
        "Liberation",
        "not measurable" if result.liberation is None else f"{result.liberation:.0%}",
    )
    st.caption(
        "Liberation is computed by particle composition: connected components of "
        "non-resin pixels are particles, and a particle counts as liberated when "
        "the payload phase occupies at least "
        f"{modal.LIBERATION_THRESHOLD:.0%} of it. Mass-weighted. This is a 2D "
        "section through 3D particles, so apparent liberation is biased HIGH "
        "against true volumetric liberation - treat it as an upper bound."
    )

    recommendation = advise(result, mean_confidence)
    st.subheader("Recommendation")

    marginal = recommendation.action.startswith("Marginal")
    hedged = marginal or recommendation.action.startswith("Flag")
    if marginal:
        st.warning(f"**{recommendation.action}**")
    elif hedged:
        st.info(f"**{recommendation.action}**")
    else:
        st.metric("Action", recommendation.action)
    st.write(recommendation.reason)
    st.caption(
        f"Model confidence: {recommendation.confidence} "
        f"(mean max-softmax {mean_confidence:.2f})"
    )

    if result.liberation is not None:
        distance = abs(result.liberation - advisor_module.LOW_LIBERATION)
        st.caption(
            f"Liberation sits {distance:.1%} from the "
            f"{advisor_module.LOW_LIBERATION:.0%} decision threshold; the "
            f"uncertainty band is +/-{advisor_module.LIBERATION_MARGIN:.1%}, "
            "which is this estimator's own mean absolute error on held-out "
            "sections. Inside that band the honest output is 'verify', not an "
            "instruction."
        )

    with st.expander("Role fractions and caveats"):
        st.write({k: f"{v:.1%}" for k, v in result.role_fractions.items()})
        st.write(
            "Roles come from src/modal.py. On S2, pentlandite and chalcopyrite "
            "are payload, pyrrhotite is the rejection target, magnetite is oxide. "
            "S2 is Norilsk massive sulphide: it is an analogue for the Bushveld "
            "BMS assemblage and its optical appearance, not for its abundance "
            "(<1 vol% in UG2). See DATA-SOURCES.md Section 1."
        )
