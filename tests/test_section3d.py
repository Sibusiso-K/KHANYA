"""The 3D view's blocks: colour = main mineral, height = valuable share, grain attached."""
import json
import re

import numpy as np

from dashboard import render, section3d
from src import grains

NAMES = ["background", "chalcopyrite", "magnetite", "pyrrhotite", "pentlandite"]


def _labels():
    labels = np.zeros((96, 96), dtype=np.int64)
    labels[:, :48] = 3                   # left half pyrrhotite (no value)
    labels[:, 48:] = 4                   # right half pentlandite (all value)
    return labels


def test_towers_stand_where_the_valuable_minerals_are():
    data = section3d.blocks(_labels(), NAMES, ["chalcopyrite", "pentlandite"], None)
    left = [h for x, h in zip(data["x"], data["h"]) if x < 48]
    right = [h for x, h in zip(data["x"], data["h"]) if x >= 48]
    assert left and right and min(right) > max(left)
    assert set(data["valuable"]) == {0, 100}
    assert {data["phase"][i] for i, x in enumerate(data["x"]) if x >= 48} == {4}


def test_resin_blocks_are_left_empty():
    labels = _labels()
    labels[:, :48] = 0
    data = section3d.blocks(labels, NAMES, ["chalcopyrite", "pentlandite"], None)
    assert all(x >= 48 for x in data["x"])


def test_3d_page_is_offline_and_carries_every_block():
    labels = _labels()
    report = grains.grain_report(labels, NAMES)
    html = render.render_section3d(labels, report, ["chalcopyrite", "pentlandite"])
    blocks = json.loads(re.search(r"var B = (\{.*?\}), GRAINS", html).group(1))
    assert len(blocks["x"]) == len(blocks["h"]) == len(blocks["grain"]) > 0
    assert "http://" not in html and "https://" not in html
    assert "Not a 3D reconstruction" in html
