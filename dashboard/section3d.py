"""A 3D view of the analysed section: honest about being a 2D slice.

The section is cut into small square blocks. Each block is a column:
colour = its main mineral, height = the share of its area that is valuable
mineral (chalcopyrite + pentlandite on S2). Towers are where the valuable
minerals concentrate. It is a way of seeing the 2D measurement, not a 3D
reconstruction of the rock: a polished section has no depth.

Drawn by our own renderer (dashboard/templates/section3d.html.jinja): plain 2D
canvas, inline, offline. Streamlit's bundled deck.gl chart was tried first and
rejected: it fetched map tiles from basemaps.cartocdn.com even with the base map
switched off, and failed an assertion when created inside a hidden tab.
"""
from __future__ import annotations

import numpy as np

TARGET_BLOCKS_ACROSS = 110       # about 110 x 75 columns on a live mosaic
MAX_HEIGHT_IN_BLOCKS = 1.6       # a block fully of valuable mineral stands this many blocks tall
FLOOR_HEIGHT_IN_BLOCKS = 0.12    # every ore block stands at least this tall, so the ore is visible


def blocks(labels, class_names, payload_names, grain_map):
    """Compact column arrays for the renderer: centres, heights, main mineral, valuable %, grain."""
    labels = np.asarray(labels)
    height, width = labels.shape
    block = max(4, int(round(max(width, height) / TARGET_BLOCKS_ACROSS)))
    rows_n, cols_n = height // block, width // block
    cropped = labels[:rows_n * block, :cols_n * block]
    cells = cropped.reshape(rows_n, block, cols_n, block).transpose(0, 2, 1, 3).reshape(rows_n, cols_n, block * block)
    counts = np.stack([(cells == c).sum(axis=2) for c in range(len(class_names))], axis=-1)
    ore = counts[..., 1:].sum(axis=-1)
    payload_idx = [class_names.index(n) for n in payload_names if n in class_names]
    payload = counts[..., payload_idx].sum(axis=-1) if payload_idx else np.zeros_like(ore)
    main = counts[..., 1:].argmax(axis=-1) + 1
    keep = ore >= (block * block) // 4          # mostly resin: leave the floor empty
    rr, cc = np.nonzero(keep)
    share = payload[rr, cc] / np.maximum(ore[rr, cc], 1)
    cy = rr * block + block // 2
    cx = cc * block + block // 2
    grain = np.asarray(grain_map)[cy, cx] if grain_map is not None else np.zeros_like(cx)
    return {
        "block": block, "width": int(cols_n * block), "height": int(rows_n * block),
        "x": cx.astype(int).tolist(), "y": cy.astype(int).tolist(),
        "h": np.round(block * (FLOOR_HEIGHT_IN_BLOCKS + MAX_HEIGHT_IN_BLOCKS * share), 1).tolist(),
        "phase": main[rr, cc].astype(int).tolist(),
        "valuable": np.round(100 * share).astype(int).tolist(),
        "grain": np.asarray(grain).astype(int).tolist(),
    }
