"""Demo dashboard. Must run offline on one laptop - assume venue wifi fails.

    streamlit run dashboard/app.py

Full path, end to end: micrograph -> segmentation -> modal mineralogy ->
liberation by particle composition -> operational recommendation. Every number
shown is measured from the predicted mask. Nothing here is a slider.

Runs the PATCHES model (train_patches.py) via sliding-window inference at
native resolution, not the resize baseline - report section 5.0.9: patches
scores 6/12 flips with 0 conservative errors against resize's 7/12 with 1,
under the same corrected band. The demo must run the pipeline the report calls
primary, not the one it calls a baseline (entry 33 - this used to load the
resize checkpoint; a mismatch nobody had reason to notice until the demo
itself was audited).

Styling: inlined into this file, not a separate theme.py (removed entry 25) -
a lab-instrument aesthetic (dark, monospace, amber) rather than the generic
purple-gradient SaaS template, since this is scientific instrumentation, not a
product demo.

DESIGN SYSTEM, and why it is hand-ported rather than dropped in. The palette
and type scale below come from the REEFPRINT :: KHANYA Stitch design
(reefprint_khanya_mintek_edition/DESIGN.md), whose colours are in turn the real
Mintek brand values read off mintek.co.za's own CSS variables - #00131D
background, #D22D20 primary, #194D5C secondary, #8CA6AE muted, #E3EAEB text,
#FFB539 warning. The exported HTML could NOT be used directly: it loads
Tailwind, Plus Jakarta Sans, JetBrains Mono, Material Symbols and its imagery
from four separate CDNs, so with venue wifi down it renders as unstyled text on
white - the exact failure the "must run offline" rule at the top of this file
exists to prevent, and the one the CI guard now fails the build over. The
Tailwind config is only data, so the tokens are transcribed here as CSS
variables and the fonts fall back through stacks already present on any Windows
laptop. Nothing in this file fetches anything.

Three verdict states carry distinct visual treatments, and amber is reserved:
it appears ONLY on "marginal, verify before acting" and on a refusal. A
confident continue is green, a confident grind-finer is red. Amber means the
instrument is declining to decide, and it is used for nothing else, so that
seeing amber on stage always means the same thing.
"""
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import streamlit as st
import torch
from PIL import Image

from src import advisor as advisor_module, modal
from src.advisor import advise, verdict_state
from src.segmentation import lumenstone as ls
from src.segmentation import patches as patch_module
from src.segmentation.model import build_model, device
from src.segmentation.train_patches import checkpoint_for

CKPT = checkpoint_for("ce")
# Inlined rather than imported: Streamlit adds the script's OWN
# directory to sys.path, which can shadow a proper package import
# of "dashboard.theme" and silently skip the CSS.
KHANYA_CSS = """
<style>
/* No @import, no CDN, no webfont fetch anywhere in this file. See the module
   docstring: the Stitch export pulled Tailwind and four font families from
   Google's servers, which is unusable for a demo that has to survive the venue
   wifi failing. Tokens transcribed; fonts fall back through stacks already on
   the machine. Segoe UI stands in for Plus Jakarta Sans (both humanist sans,
   close enough that nothing in the demo depends on the difference), Consolas
   for JetBrains Mono. */
:root {
  /* Surfaces, darkest to lightest. Mintek #00131D is the ground. */
  --bg: #00131D;
  --surface: #071C27;
  --surface-container: #0B222E;
  --surface-high: #122D3B;
  --outline: #1E3E4B;
  --outline-dim: #132D37;

  /* Brand. Read from mintek.co.za's own CSS variables. */
  --primary: #D22D20;        /* --theme-color   */
  --secondary: #194D5C;      /* --hover-color   */
  --muted: #8CA6AE;          /* --gray-color    */
  --ink: #E3EAEB;            /* --light-color   */

  /* State. Amber is reserved: marginal + refusal only, nothing else. */
  --warning: #FFB539;
  --warning-container: #3D2A00;
  --success: #1EA868;
  --success-container: #062B1A;
  --danger: #D22D20;
  --danger-container: #3A0704;

  /* Depth. Layered cards, not flat boxes. */
  --elevation-1: 0 4px 20px -2px rgba(0,19,29,0.8), 0 0 0 1px rgba(30,62,75,0.55);
  --elevation-2: 0 8px 32px -4px rgba(0,13,20,0.9), 0 0 0 1px rgba(30,62,75,0.7);

  --sans: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
  --mono: Consolas, "JetBrains Mono", "Fira Code", monospace;
}

/* Prose in the humanist sans; every measured value in mono, set per element. */
html, body, [class*="css"] { font-family: var(--sans) !important; }
.stApp { background: var(--bg); color: var(--ink); }
.block-container { padding-top: 1.6rem; max-width: 1720px; }
#MainMenu, footer, header { visibility: hidden; }
h1, h2, h3 { font-weight: 700 !important; letter-spacing: -0.01em; color: var(--ink) !important; }

@keyframes khanyaFadeUp {
  0%   { opacity: 0; transform: translateY(12px); }
  100% { opacity: 1; transform: translateY(0); }
}

.khanya-mast {
  border: 1px solid var(--outline); border-left: 3px solid var(--primary);
  background: var(--surface); padding: 1.1rem 1.4rem; margin-bottom: 1.4rem;
  box-shadow: var(--elevation-1);
  animation: khanyaFadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
.khanya-mast .tag {
  font-family: var(--mono); font-size: 0.68rem; letter-spacing: 0.18em;
  color: var(--primary); text-transform: uppercase; font-weight: 600;
}
.khanya-mast .title { font-size: 1.75rem; font-weight: 700; margin: 0.2rem 0 0.15rem; }
.khanya-mast .sub { font-size: 0.85rem; color: var(--muted); }

.khanya-panel {
  border: 1px solid var(--outline); background: var(--surface-container);
  padding: 1rem 1.2rem; margin-bottom: 1rem; box-shadow: var(--elevation-1);
  animation: khanyaFadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
.khanya-panel .head {
  font-family: var(--mono); font-size: 0.68rem; letter-spacing: 0.14em;
  color: var(--muted); text-transform: uppercase; border-bottom: 1px solid var(--outline-dim);
  padding-bottom: 0.5rem; margin-bottom: 0.7rem; font-weight: 600;
}

.khanya-readout {
  display: flex; justify-content: space-between; align-items: baseline;
  padding: 0.4rem 0; border-bottom: 1px solid var(--outline-dim); font-size: 0.85rem;
}
.khanya-readout:last-child { border-bottom: none; }
.khanya-readout .k { color: var(--muted); }
.khanya-readout .v {
  font-family: var(--mono); color: var(--ink); font-weight: 600;
  font-variant-numeric: tabular-nums; font-size: 0.95rem;
}

/* The verdict. Three states, three colours, and amber only ever means
   "the instrument is declining to decide". */
.khanya-verdict {
  border: 1px solid var(--outline); border-left: 4px solid var(--success);
  background: linear-gradient(180deg, var(--success-container), var(--surface-container));
  padding: 1.15rem 1.4rem; box-shadow: var(--elevation-2);
  animation: khanyaFadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
.khanya-verdict.hold {
  border-left-color: var(--warning);
  background: linear-gradient(180deg, var(--warning-container), var(--surface-container));
}
.khanya-verdict.grind {
  border-left-color: var(--danger);
  background: linear-gradient(180deg, var(--danger-container), var(--surface-container));
}
.khanya-verdict .state {
  font-family: var(--mono); font-size: 0.66rem; letter-spacing: 0.16em;
  text-transform: uppercase; font-weight: 600; color: var(--muted);
}
.khanya-verdict.hold .state { color: var(--warning); }
.khanya-verdict.grind .state { color: var(--primary); }
.khanya-verdict .action {
  font-size: 1.5rem; font-weight: 700; letter-spacing: -0.01em; margin-top: 0.2rem;
}
.khanya-verdict .reason {
  color: var(--muted); font-size: 0.86rem; margin-top: 0.5rem; line-height: 1.55;
}

/* Two candidate actions, deliberately equal weight. Neither is styled as the
   recommended one, because inside the band we do not have a recommendation. */
.khanya-candidates { display: flex; gap: 0.75rem; margin-top: 0.9rem; }
.khanya-candidate {
  flex: 1 1 0; border: 1px solid var(--outline); background: var(--surface);
  padding: 0.8rem 0.95rem;
}
.khanya-candidate .cond {
  font-family: var(--mono); font-size: 0.64rem; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--warning); font-weight: 600;
}
.khanya-candidate .act { font-size: 0.95rem; font-weight: 600; margin-top: 0.25rem; }
.khanya-candidate .gate {
  font-size: 0.76rem; color: var(--muted); margin-top: 0.4rem; line-height: 1.45;
}

/* Liberation band. The shaded zone is the conformal interval drawn to scale. */
.khanya-band {
  height: 10px; background: var(--surface-high); position: relative;
  margin: 0.7rem 0 0.35rem; border: 1px solid var(--outline-dim);
}
.khanya-band .zone { position: absolute; top: 0; bottom: 0; background: rgba(255,181,57,0.22); }
.khanya-band .marker {
  position: absolute; top: -5px; width: 2px; height: 20px; background: var(--ink);
}
.khanya-band .thresh {
  position: absolute; top: -5px; width: 1px; height: 20px; background: var(--muted);
}
.khanya-scale {
  display: flex; justify-content: space-between; font-family: var(--mono);
  font-size: 0.62rem; color: var(--muted); letter-spacing: 0.08em;
}

[data-testid="stFileUploaderDropzone"] {
  background: var(--surface-container) !important;
  border: 1px dashed var(--outline) !important; border-radius: 4px !important;
}
.stButton>button, [data-testid="stFileUploader"] button {
  border-radius: 4px !important; border: 1px solid var(--primary) !important;
  color: var(--primary) !important; background: transparent !important;
  font-family: var(--mono) !important; font-weight: 600 !important;
}
[data-testid="stImage"] img { border: 1px solid var(--outline); border-radius: 4px; }
.stAlert { border-radius: 4px !important; }
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


@st.cache_data(show_spinner=False)
def predict(image_bytes):
    """Sliding-window inference, cached on the exact uploaded bytes.

    Native-resolution tiling on a CPU-only laptop measured at ~155s for one
    3396x2547 section (entry 33) - real, and too slow to sit through silently
    on stage. The fix is caching, not weaker inference: tiling parameters stay
    exactly what decision_gap.py validated (same checkpoint_for('ce'), same
    PATCH/overlap), so a cached result is identical to a fresh one, just not
    recomputed. A rehearsed demo run once beforehand on the same laptop is
    then instant during the actual talk; a genuinely new image (the live-
    refusal beat) still pays the real cost, honestly, with the spinner below
    naming it rather than hiding it.
    """
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    model, dev = load_model()
    with torch.no_grad():
        labels, mean_confidence = patch_module.sliding_window_predict(model, image, dev)
    return image, labels, mean_confidence


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


# verdict_state lives in src/advisor.py, not here: which colour a verdict gets
# is a statement about the decision layer's severity, and the reserved-amber
# rule it encodes is pinned by tests/test_advisor.py rather than by eye.


# Masthead. Deliberately NOT what the design mockup shipped: that carried
# "MINTEK SOUTH AFRICA" branding, an "ISO/IEC 17025 ACCREDITED" footer, an
# "ISO 13320 / MINTEK QA" calibration stamp, a fabricated "Dr. K. Vance, Chief
# Metallurgist" as signed-in operator, and a signed audit-trail record. Every
# one of those is a claim of institutional authority and laboratory
# accreditation this project does not hold, presented to the institution that
# would recognise it immediately. Fabricated numbers in a mockup get replaced
# by real pipeline output; fabricated credentials cannot be, so they are gone.
# What is left is true: a prototype, built by two named people, for this event.
st.markdown(
    '<div class="khanya-mast">'
    '<div class="tag">REEFPRINT :: KHANYA &nbsp;·&nbsp; prototype, '
    'Mintek-SCi Grad Hackathon 2026</div>'
    '<div class="title">Ore processability advisor</div>'
    '<div class="sub">Reflected-light micrograph &rarr; segmentation &rarr; modal '
    'mineralogy &rarr; liberation &rarr; recommendation. Every number on this page is '
    'measured from the predicted mask; nothing is a slider. '
    'Sibusiso Khumalo and Lethabo Mphukuile.</div>'
    '</div>',
    unsafe_allow_html=True,
)

if not CKPT.exists():
    st.error(
        f"No trained model at {CKPT}. Run: python -m src.segmentation.train_patches"
    )
    st.stop()

uploaded = st.file_uploader(
    "REFLECTED-LIGHT MICROGRAPH OF A POLISHED SECTION",
    type=["jpg", "jpeg", "png", "tif", "tiff"],
)

if uploaded:
    image_bytes = uploaded.getvalue()
    with st.spinner(
        "Tiling and predicting at native resolution - ~2-3 min on a CPU-only "
        "laptop for a section this size, first time only (cached after)."
    ):
        image, labels, mean_confidence = predict(image_bytes)

    # refine=True: raw connected components leave predicted liberation
    # uncorrelated with truth (+0.128). Repairing topology - speckle removal,
    # hole filling, watershed separation - takes that to +0.947. The demo must
    # show the pipeline we actually validated, not the one we superseded.
    result = modal.analyse(labels, ls.CLASS_NAMES, refine=True)
    recommendation = advise(result, mean_confidence)
    state_class, state_label = verdict_state(recommendation.action)

    # Verdict first, before the imagery. The design this is ported from is
    # dense enough that on a 1366x768 venue laptop the verdict sat below the
    # fold, which is the wrong thing to have to scroll for during a live demo.
    st.markdown(
        f'<div class="khanya-verdict {state_class}">'
        f'<div class="state">{state_label}</div>'
        f'<div class="action">{recommendation.action}</div>'
        f'<div class="reason">{recommendation.reason}</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Inside the band the honest output is a SET of admissible actions, not a
    # pick between them, so both are rendered at equal weight with the
    # condition that would confirm each. Styling one as primary would be the
    # visual version of the overconfidence the band exists to prevent.
    if recommendation.action.startswith("Marginal"):
        floor = advisor_module.LOW_LIBERATION
        st.markdown(
            '<div class="khanya-candidates">'
            '<div class="khanya-candidate">'
            f'<div class="cond">if true liberation &ge; {floor:.0%}</div>'
            '<div class="act">Continue at current setpoint</div>'
            '<div class="gate">Confirm with a second optical field on the same '
            'section, or an assay, before leaving the circuit unchanged.</div>'
            '</div>'
            '<div class="khanya-candidate">'
            f'<div class="cond">if true liberation &lt; {floor:.0%}</div>'
            '<div class="act">Grind finer</div>'
            '<div class="gate">Confirm the same way before spending mill power. '
            'Regrinding on a measurement this close to the floor is the '
            'expensive half of the error.</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    left, right = st.columns(2)
    with left:
        panel_open("01 · INPUT")
        st.image(image, use_container_width=True)
        panel_close()
    with right:
        panel_open("02 · PREDICTED PHASES")
        st.image(colourise(labels), use_container_width=True)
        panel_close()

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
                '</div>'
                '<div class="khanya-scale"><span>0%</span>'
                f'<span>{advisor_module.LOW_LIBERATION:.0%} floor</span>'
                '<span>100%</span></div>',
                unsafe_allow_html=True,
            )
            st.caption(
                f"Amber zone = conformal uncertainty band "
                f"(±{advisor_module.LIBERATION_MARGIN:.0%}, 85% empirical "
                f"coverage on held-out sections). Grey line = {advisor_module.LOW_LIBERATION:.0%} "
                "liberation floor. White marker = this section. Inside the "
                "band, the true value could sit on either side of the "
                "threshold, so the honest output is 'verify', not a guess."
            )
        else:
            st.caption("Liberation not measurable for this field.")
        panel_close()

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
