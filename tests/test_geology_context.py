"""The geology context view: real public data, sourced, and never a fabricated location."""
import json

from dashboard import render
from src.segmentation import config

DATA = json.loads((config.ROOT / "dashboard" / "data" / "geology_context.json").read_text(encoding="utf-8"))


def test_sites_are_south_african_and_carry_their_source():
    assert len(DATA["deposits"]) > 500
    assert all(-35.5 < s["lat"] < -21.5 and 16 < s["lon"] < 33.5 for s in DATA["deposits"])
    assert DATA["sources"]["deposits"]["sha256"] and "2011" in DATA["sources"]["deposits"]["note"]


def test_boreholes_are_logs_not_map_points():
    assert len(DATA["holes"]) == 317
    assert sum(len(h["intervals"]) for h in DATA["holes"].values()) == 1205
    assert DATA["sources"]["holes"]["licence"] == "CC BY 4.0"
    assert "No collar coordinates" in DATA["sources"]["holes"]["note"]
    assert not any("lat" in h or "lon" in h for h in DATA["holes"].values())


def test_geology_page_is_offline_and_says_where_results_attach():
    html = render.render_geology()
    assert "http://" not in html and "https://" not in html
    assert "never placed on the map" in html or "not on the map" in html
    assert "Rustenburg" in html


def test_records_with_impossible_coordinates_are_excluded_and_named():
    excluded = DATA["sources"]["deposits"]["excluded_bad_coordinates"]
    assert excluded and all("(" in e for e in excluded)
