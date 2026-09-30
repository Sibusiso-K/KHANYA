"""Grain-level mineralogy agrees with the advisor's own particle counts."""
import numpy as np
import pytest

from src import grains, modal

NAMES = ["background", "chalcopyrite", "magnetite", "pyrrhotite", "pentlandite"]


def _field():
    labels = np.zeros((120, 120), dtype=np.int64)
    labels[10:40, 10:40] = 1            # a free chalcopyrite grain
    labels[60:110, 60:110] = 3          # a pyrrhotite grain...
    labels[80:90, 80:90] = 4            # ...with a little pentlandite locked inside
    return labels


def test_grain_counts_match_the_advisor():
    labels = _field()
    report = grains.grain_report(labels, NAMES)
    result = modal.analyse(labels, NAMES, refine=True)
    assert report.n_grains == result.n_particles
    assert report.n_payload_grains == result.n_payload_particles


def test_each_grain_knows_its_composition_and_liberation():
    report = grains.grain_report(_field(), NAMES)
    free = [g for g in report.grains if g.phases.get("chalcopyrite", 0) > 0.9]
    locked = [g for g in report.grains if "pentlandite" in g.phases]
    assert free and free[0].liberated
    assert locked and not locked[0].liberated
    assert abs(sum(locked[0].phases.values()) - 1.0) < 1e-6
    assert report.grain_map[25, 25] == free[0].id


def test_weight_percent_uses_density_and_sums_to_100():
    wt = grains.weight_percent({"chalcopyrite": 0.5, "magnetite": 0.5, "pyrrhotite": 0.0, "pentlandite": 0.0})
    assert abs(sum(wt.values()) - 100.0) < 1e-9
    assert wt["magnetite"] > wt["chalcopyrite"]  # denser, so heavier at equal area


def test_association_is_boundary_share_including_free_surface():
    assoc = grains.association(_field(), NAMES)
    assert assoc["pentlandite"] == {"pyrrhotite": 100.0}   # fully locked in pyrrhotite
    assert assoc["chalcopyrite"] == {"resin": 100.0}       # fully free
    assert abs(sum(assoc["pyrrhotite"].values()) - 100.0) < 0.2


def test_sizes_stay_in_pixels_without_a_confirmed_scale(monkeypatch):
    report = grains.grain_report(_field(), NAMES, microns_per_pixel=None)
    assert report.microns_per_pixel is None or grains.MICRONS_PER_PIXEL is not None
    assert [b["from_px"] for b in report.liberation_by_size][:3] == [0, 16, 32]


def test_real_section_matches_the_advisor_when_data_is_present():
    from src.segmentation import config
    from src.segmentation import lumenstone as ls
    if not (ls.DATA_DIR / "masks").exists() and not (config.ROOT / "data" / "raw").exists():
        pytest.skip("held-out data not present (CI)")
    try:
        from src.segmentation.patches import labels_for
        labels = labels_for("test_11", "test")
    except (FileNotFoundError, OSError):
        pytest.skip("held-out data not present (CI)")
    result = modal.analyse(labels, ls.CLASS_NAMES, refine=True)
    report = grains.grain_report(labels, ls.CLASS_NAMES, phase_fractions=result.phase_fractions)
    assert (report.n_grains, report.n_payload_grains) == (result.n_particles, result.n_payload_particles)
