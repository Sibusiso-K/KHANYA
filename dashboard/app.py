"""Demo dashboard. Must run offline on one laptop - assume venue wifi fails.

    streamlit run dashboard/app.py

Full path, end to end: micrograph -> segmentation -> modal mineralogy ->
liberation by particle composition -> operational recommendation. Every number
shown is measured from the predicted mask. Nothing here is a slider.

Styling: dashboard/theme.py. Deliberately not Streamlit's default look - a
lab-instrument aesthetic (dark, monospace, amber) rather than the generic
purple-gradient SaaS template, since this is scientific instrumentation, not a
product demo.
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
# Inlined rather than imported: Streamlit adds the script's OWN
# directory to sys.path, which can shadow a proper package import
# of "dashboard.theme" and silently skip the CSS.
KHANYA_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700;800&display=swap');

:root {
  --ink: #e8e3d8;
  --dim: #8a8378;
  --bg: #14120f;
  --panel: #1c1915;
  --line: #3a352c;
  --amber: #ff9d2e;
  --amber-dim: #cc7d1f;
  --ok: #6fae5c;
  --warn: #d6a92c;
  --bad: #c85a4a;
}

html, body, [class*="css"] { font-family: 'JetBrains Mono', monospace !important; }
.stApp { background: var(--bg); color: var(--ink); }

/* kill Streamlit's rounded, gradient, generic chrome */
.block-container { padding-top: 2rem; max-width: 1180px; }
#MainMenu, footer, header { visibility: hidden; }

h1, h2, h3 { font-weight: 800 !important; letter-spacing: -0.01em; color: var(--ink) !important; }

.khanya-mast {
  border: 1px solid var(--line); border-left: 4px solid var(--amber);
  background: var(--panel); padding: 1.1rem 1.4rem; margin-bottom: 1.6rem;
}
.khanya-mast .tag {
  font-size: 0.72rem; letter-spacing: 0.18em; color: var(--amber);
  text-transform: uppercase; font-weight: 700;
}
.khanya-mast .title { font-size: 1.6rem; font-weight: 800; margin: 0.15rem 0 0.1rem; }
.khanya-mast .sub { font-size: 0.82rem; color: var(--dim); }

.khanya-panel {
  border: 1px solid var(--line); background: var(--panel);
  padding: 1rem 1.2rem; margin-bottom: 1rem;
}
.khanya-panel .head {
  font-size: 0.72rem; letter-spacing: 0.14em; color: var(--dim);
  text-transform: uppercase; border-bottom: 1px solid var(--line);
  padding-bottom: 0.5rem; margin-bottom: 0.7rem; font-weight: 700;
}

.khanya-readout {
  display: flex; justify-content: space-between; align-items: baseline;
  padding: 0.35rem 0; border-bottom: 1px dashed var(--line); font-size: 0.88rem;
}
.khanya-readout:last-child { border-bottom: none; }
.khanya-readout .k { color: var(--dim); }
.khanya-readout .v { color: var(--ink); font-weight: 700; font-variant-numeric: tabular-nums; }

.khanya-verdict {
  border: 1px solid var(--line); border-left: 5px solid var(--ok);
  background: var(--panel); padding: 1rem 1.3rem;
}
.khanya-verdict.warn { border-left-color: var(--warn); }
.khanya-verdict.bad { border-left-color: var(--bad); }
.khanya-verdict .action {
  font-size: 1.15rem; font-weight: 800; letter-spacing: -0.01em;
}
.khanya-verdict .reason { color: var(--dim); font-size: 0.85rem; margin-top: 0.4rem; line-height: 1.5; }

.khanya-band {
  height: 6px; background: var(--line); position: relative; margin: 0.6rem 0 0.3rem;
}
.khanya-band .zone {
  position: absolute; top: 0; bottom: 0; background: rgba(214,169,44,0.35);
}
.khanya-band .marker {
  position: absolute; top: -4px; width: 2px; height: 14px; background: var(--amber);
}
.khanya-band .thresh {
  position: absolute; top: -4px; width: 1px; height: 14px; background: var(--dim);
}

[data-testid="stFileUploaderDropzone"] {
  background: var(--panel) !important; border: 1px dashed var(--line) !important;
  border-radius: 0 !important;
}
.stButton>button, [data-testid="stFileUploader"] button {
  border-radius: 0 !important; border: 1px solid var(--amber-dim) !important;
  color: var(--amber) !important; background: transparent !important;
  font-family: 'JetBrains Mono', monospace !important; font-weight: 700 !important;
}
[data-testid="stMetricValue"] { color: var(--amber) !important; font-weight: 800 !important; }
[data-testid="stMetricLabel"] { color: var(--dim) !important; text-transform: uppercase; font-size: 0.7rem !important; letter-spacing: 0.1em; }
[data-testid="stImage"] img { border: 1px solid var(--line); }
.stAlert { border-radius: 0 !important; }
</style>
"""

st.set_page_config(page_title="KHANYA — ore processability advisor", layout="wide")
st.markdown(KHANYA_CSS, unsafe_allow_html=True)


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


def panel_open(title):
    st.markdown(f'<div class="khanya-panel"><div class="head">{title}</div>',
                unsafe_allow_html=True)


def panel_close():
    st.markdown('</div>', unsafe_allow_html=True)


def readout(label, value):
    st.markdown(
        f'<div class="khanya-readout"><span class="k">{label}</span>'
        f'<span class="v">{value}</span></div>',
        unsafe_allow_html=True,
    )


st.markdown(
    '<div class="khanya-mast">'
    '<div class="tag">Mintek-SCi Grad Hackathon 2026 · Problem 3</div>'
    '<div class="title">KHANYA — ore processability advisor</div>'
    '<div class="sub">LumenStone S2 · Norilsk Group, layered ultramafic Ni-Cu-PGE sulphide'
    ' · reflected-light micrograph &rarr; recommendation</div>'
    '</div>',
    unsafe_allow_html=True,
)

if not CKPT.exists():
    st.error(
        f"No trained model at {CKPT}. Run: python -m src.segmentation.train_lumenstone"
    )
    st.stop()

uploaded = st.file_uploader(
    "REFLECTED-LIGHT MICROGRAPH OF A POLISHED SECTION",
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
    with left:
        panel_open("01 · INPUT")
        st.image(image, use_container_width=True)
        panel_close()
    with right:
        panel_open("02 · PREDICTED PHASES")
        st.image(colourise(labels), use_container_width=True)
        panel_close()

    # refine=True: raw connected components leave predicted liberation
    # uncorrelated with truth (+0.128). Repairing topology - speckle removal,
    # hole filling, watershed separation - takes that to +0.947. The demo must
    # show the pipeline we actually validated, not the one we superseded.
    result = modal.analyse(labels, ls.CLASS_NAMES, refine=True)
    recommendation = advise(result, mean_confidence)

    col_a, col_b = st.columns([1, 1])

    with col_a:
        panel_open("03 · MODAL MINERALOGY (% of ore area)")
        st.bar_chart(result.phase_fractions)
        st.caption(
            "Area fractions exclude mounting resin — otherwise every number "
            "tracks how densely the section was mounted, not the ore."
        )
        panel_close()

        panel_open("04 · MEASUREMENTS")
        readout("ORE IN FIELD", f"{result.ore_area_fraction:.1%}")
        readout("PARTICLES (post-topology-repair)", result.n_particles)
        readout(
            "LIBERATION",
            "N/A" if result.liberation is None else f"{result.liberation:.0%}",
        )
        readout("MODEL CONFIDENCE", f"{mean_confidence:.2f}")
        panel_close()

    with col_b:
        panel_open("05 · LIBERATION vs. DECISION THRESHOLD")
        if result.liberation is not None:
            lo = max(0.0, advisor_module.LOW_LIBERATION - advisor_module.LIBERATION_MARGIN)
            hi = min(1.0, advisor_module.LOW_LIBERATION + advisor_module.LIBERATION_MARGIN)
            st.markdown(
                '<div class="khanya-band">'
                f'<div class="zone" style="left:{lo*100:.1f}%;width:{(hi-lo)*100:.1f}%"></div>'
                f'<div class="thresh" style="left:{advisor_module.LOW_LIBERATION*100:.1f}%"></div>'
                f'<div class="marker" style="left:{result.liberation*100:.1f}%"></div>'
                '</div>',
                unsafe_allow_html=True,
            )
            st.caption(
                f"Amber zone = conformal uncertainty band "
                f"(±{advisor_module.LIBERATION_MARGIN:.0%}, 85% empirical "
                f"coverage on held-out sections). Grey line = {advisor_module.LOW_LIBERATION:.0%} "
                "liberation floor. White marker = this section. Inside the "
                "band, the true value could sit on either side of the "
                "threshold — the honest output is 'verify', not a guess."
            )
        else:
            st.caption("Liberation not measurable for this field.")
        panel_close()

        verdict_class = (
            "warn" if recommendation.action.startswith(("Marginal", "Flag"))
            else "bad" if recommendation.action.startswith("No recommendation")
            else "ok"
        )
        st.markdown(
            f'<div class="khanya-verdict {verdict_class}">'
            f'<div class="action">{recommendation.action}</div>'
            f'<div class="reason">{recommendation.reason}</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with st.expander("ROLE MAPPING AND SCOPE"):
        for role, fraction in result.role_fractions.items():
            readout(role.upper(), f"{fraction:.1%}")
        st.caption(
            "Roles: src/modal.py. On S2, pentlandite and chalcopyrite are "
            "payload, pyrrhotite is the rejection target, magnetite is oxide. "
            "S2 is Norilsk massive sulphide — an analogue for the Bushveld BMS "
            "assemblage and its optical appearance, not for its abundance "
            "(<1 vol% in UG2). See DATA-SOURCES.md §1."
        )
