"""The two files that cross into REEFPRINT, tested on this side of the seam.

`polarimetry.py` and `chromite_pge_falsification.py` import Lethabo's package
unchanged. What is ours, and therefore ours to test, is the archive parsing and
the domain arithmetic we feed it. REEFPRINT's own estimators are covered by
REEFPRINT's suite - duplicating that here would test his code twice and ours
not at all.
"""
import numpy as np
import pytest


def test_main_helpers_import_without_a_reefprint_checkout(tmp_path):
    import os
    import subprocess
    import sys

    env = dict(os.environ, REEFPRINT_SRC=str(tmp_path / "absent"))
    proc = subprocess.run(
        [sys.executable, "-c", "from src.polarimetry import list_sections; "
         "from src.chromite_pge_falsification import cation_ratios"],
        env=env, capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0, proc.stderr

from src.chromite_pge_falsification import MOLAR_MASS, cation_ratios
from src.polarimetry import ROTATION_RE, list_sections, section_frames


class TestCationRatios:
    """Barnes & Roeder 2001 indices, pinned against hand-worked values."""

    def test_equal_moles_of_cr_and_al_give_a_cr_number_of_one_half(self):
        # Pick wt% so the mole counts match exactly.
        cr2o3 = np.array([MOLAR_MASS["Cr2O3"]])
        al2o3 = np.array([MOLAR_MASS["Al2O3"]])
        cr_number, _ = cation_ratios(cr2o3, np.array([1.0]), np.array([1.0]), al2o3)
        assert cr_number[0] == pytest.approx(0.5)

    def test_equal_moles_of_mg_and_fe_give_an_mg_number_of_one_half(self):
        mgo = np.array([MOLAR_MASS["MgO"]])
        feo = np.array([MOLAR_MASS["FeO"]])
        _, mg_number = cation_ratios(np.array([1.0]), feo, mgo, np.array([1.0]))
        assert mg_number[0] == pytest.approx(0.5)

    def test_no_aluminium_gives_a_cr_number_of_one(self):
        cr_number, _ = cation_ratios(
            np.array([40.0]), np.array([20.0]), np.array([15.0]), np.array([0.0])
        )
        assert cr_number[0] == pytest.approx(1.0)

    def test_both_indices_stay_inside_the_unit_interval(self):
        rng = np.random.default_rng(0)
        cr2o3, feo, mgo, al2o3 = (rng.uniform(0.1, 50.0, size=200) for _ in range(4))
        cr_number, mg_number = cation_ratios(cr2o3, feo, mgo, al2o3)
        assert np.all((cr_number >= 0.0) & (cr_number <= 1.0))
        assert np.all((mg_number >= 0.0) & (mg_number <= 1.0))

    def test_the_ratios_are_scale_invariant(self):
        """Cation ratios describe composition, not sample mass - doubling every
        oxide must not move them. Catches a normalisation slipped in by hand."""
        args = (np.array([34.96]), np.array([19.29]),
                np.array([16.79]), np.array([10.21]))
        single = cation_ratios(*args)
        doubled = cation_ratios(*(2.0 * a for a in args))
        assert single[0][0] == pytest.approx(doubled[0][0])
        assert single[1][0] == pytest.approx(doubled[1][0])

    def test_a_real_row_lands_in_the_published_chromite_range(self):
        """Row 1 of the Bachmann CSV. Bushveld chromites sit high in Cr# -
        a value near 0.5 or below would mean the oxides are transposed."""
        cr_number, mg_number = cation_ratios(
            np.array([34.96]), np.array([19.29]),
            np.array([16.79]), np.array([10.21]),
        )
        assert 0.55 < cr_number[0] < 0.85
        assert 0.40 < mg_number[0] < 0.80


class TestRotationFrameParsing:
    """The archive layout that a keyword search originally missed entirely."""

    @pytest.mark.parametrize("name", [
        "S3_v2/imgs/train/S3_train_01/S3_train_01_r000.jpg",
        "S3_v2/imgs/test/S3_test_04/S3_test_04_r355.jpg",
    ])
    def test_matches_real_rotation_frames(self, name):
        assert ROTATION_RE.search(name)

    @pytest.mark.parametrize("name", [
        "S3_v2/imgs/train/S3_train_01.jpg",       # the flat reference frame
        "S3_v2/masks/train/S3_train_01.png",      # a mask
        "S3_v2/imgs/train/S3_train_01/.DS_Store",
        "S3_v2/imgs/train/S3_train_01/S3_train_01_r00.jpg",   # two digits, not three
    ])
    def test_rejects_everything_that_is_not_a_rotation_frame(self, name):
        assert ROTATION_RE.search(name) is None

    def test_the_captured_group_is_the_angle_in_degrees(self):
        match = ROTATION_RE.search("x/S3_train_01_r045.jpg")
        assert int(match.group(1)) == 45


def _namelist():
    """A miniature S3 v2 archive: two train sections, one test, 3 angles each."""
    names = []
    for split, stem in (("train", "S3_train_01"), ("train", "S3_train_02"),
                        ("test", "S3_test_01")):
        names.append(f"S3_v2/masks/{split}/{stem}.png")
        names.append(f"S3_v2/imgs/{split}/{stem}.jpg")
        for deg in (0, 5, 10):
            names.append(f"S3_v2/imgs/{split}/{stem}/{stem}_r{deg:03d}.jpg")
    return names


class TestArchiveIndexing:
    def test_sections_come_from_the_masks_and_cover_both_splits(self):
        assert list_sections(_namelist()) == [
            ("train", "S3_train_01"),
            ("train", "S3_train_02"),
            ("test", "S3_test_01"),
        ]

    def test_frames_are_returned_in_ascending_angle_order(self):
        frames = section_frames(_namelist(), "train", "S3_train_01")
        assert [deg for deg, _ in frames] == [0, 5, 10]

    def test_frames_of_one_section_never_leak_into_another(self):
        """S3_train_01 and S3_train_02 share a prefix up to the last digit -
        a startswith() on the wrong boundary would silently pool two sections."""
        frames = section_frames(_namelist(), "train", "S3_train_01")
        assert all("S3_train_01" in name for _deg, name in frames)
        assert len(frames) == 3

    def test_an_unknown_section_yields_no_frames_rather_than_raising(self):
        assert section_frames(_namelist(), "train", "S3_train_99") == []
