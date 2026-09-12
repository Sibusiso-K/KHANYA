"""The CSV-parsing and cation-ratio arithmetic in ``experiments/006-bushveld-chromite-
falsification/run.py``, tested without the real 1,205-row download — same pattern as
``tests/test_s3v2_reader.py`` for the geometry experiment: the real archive/CSV is not in this
repo (``data/`` is gitignored, DVC-tracked, never committed raw), so what CI can check is the
harness against a synthetic file built to the real layout, plus the one piece of domain
arithmetic (Cr#/Mg#) against a hand-worked example.

Running the real thing, on real data, is `experiments/006-bushveld-chromite-falsification/`,
and its result is recorded in `docs/BUILDLOG.md` — matching the N3 pattern this project already
uses (leg (a), the phantom, proves the maths; leg (b)/the real archive, run separately, proves
nothing about correctness without a known answer to check against — here the "known answer" is
the independent implementation on `khanya/main` producing the identical numbers).
"""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import numpy as np
import pytest


def _load_experiment() -> ModuleType:
    """Import ``experiments/006-bushveld-chromite-falsification/run.py`` by path.

    Experiment directories are numbered so the sequence is legible on disk, which makes them
    illegal package names — loading by path keeps the numbering and still lets the pure
    functions be tested, rather than an un-numbered importable copy that could drift from the
    script actually run.
    """
    path = (
        Path(__file__).resolve().parents[1]
        / "experiments"
        / "006-bushveld-chromite-falsification"
        / "run.py"
    )
    spec = importlib.util.spec_from_file_location(
        "bushveld_chromite_falsification_experiment", path
    )
    if spec is None or spec.loader is None:  # pragma: no cover - would mean the file vanished
        pytest.fail(f"cannot load the experiment script at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


EXPERIMENT = _load_experiment()


def test_cation_ratios_match_a_hand_worked_example() -> None:
    """Barnes & Roeder 2001: Cr# = Cr/(Cr+Al), Mg# = Mg/(Mg+Fe2+), as cation mole ratios.

    Hand-worked at round numbers chosen so the arithmetic is checkable by inspection: equal
    moles of Cr2O3 and Al2O3 give Cr# = 0.5 regardless of scale; equal moles of MgO and FeO
    give Mg# = 0.5 the same way.
    """
    cr2o3 = np.array([151.99, 151.99])  # 1.0 mole each row
    al2o3 = np.array([101.96, 203.92])  # 1.0 and 2.0 moles -> Cr# = 0.5, then 1/3
    mgo = np.array([40.30, 40.30])  # 1.0 mole each row
    feo = np.array([71.85, 71.85])  # 1.0 mole each row

    cr_number, mg_number = EXPERIMENT.cation_ratios(cr2o3, feo, mgo, al2o3)

    assert cr_number == pytest.approx([0.5, 1.0 / 3.0], rel=1e-3)
    assert mg_number == pytest.approx([0.5, 0.5], rel=1e-3)


def _write_synthetic_csv(path: Path, *, n_boreholes: int, rows_per_borehole: int) -> None:
    """A miniature CSV with the real column layout and the real semicolon delimiter, values
    generated so chromite composition genuinely carries extra PGE signal beyond Cr2O3 alone —
    the harness is what is under test here, not the real geological association.
    """
    rng = np.random.default_rng(7)
    fieldnames = [
        "Cr2O3_%",
        "FeO_%",
        "MgO_%",
        "Al2O3_%",
        "Pt_ICP_ppm",
        "Pd_ICP_ppm",
        "Rh_ICP_ppm",
        "Au_ICP_ppm",
        "BH_ID",
        "Filter",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        for borehole in range(n_boreholes):
            for _ in range(rows_per_borehole):
                cr2o3 = float(rng.uniform(20.0, 45.0))
                feo = float(rng.uniform(15.0, 25.0))
                mgo = float(rng.uniform(10.0, 20.0))
                al2o3 = float(rng.uniform(8.0, 14.0))
                cr_number, mg_number = EXPERIMENT.cation_ratios(
                    np.array([cr2o3]), np.array([feo]), np.array([mgo]), np.array([al2o3])
                )
                pge = 2.0 * cr2o3 + 6.0 * float(cr_number[0]) + 4.0 * float(mg_number[0])
                writer.writerow(
                    {
                        "Cr2O3_%": f"{cr2o3:.2f}",
                        "FeO_%": f"{feo:.2f}",
                        "MgO_%": f"{mgo:.2f}",
                        "Al2O3_%": f"{al2o3:.2f}",
                        "Pt_ICP_ppm": f"{pge / 2:.4f}",
                        "Pd_ICP_ppm": f"{pge / 4:.4f}",
                        "Rh_ICP_ppm": f"{pge / 8:.4f}",
                        "Au_ICP_ppm": f"{pge / 8:.4f}",
                        "BH_ID": f"BH{borehole:03d}",
                        "Filter": "1",
                    }
                )
        # One excluded row (Filter == "0") and one row with a missing value, to check both
        # exclusion paths the real CSV actually needs — 12 of 1,205 real rows carry Filter=="0".
        writer.writerow(
            {
                "Cr2O3_%": "30.0",
                "FeO_%": "20.0",
                "MgO_%": "15.0",
                "Al2O3_%": "10.0",
                "Pt_ICP_ppm": "1.0",
                "Pd_ICP_ppm": "1.0",
                "Rh_ICP_ppm": "1.0",
                "Au_ICP_ppm": "1.0",
                "BH_ID": "BH000",
                "Filter": "0",
            }
        )
        writer.writerow(
            {
                "Cr2O3_%": "",
                "FeO_%": "20.0",
                "MgO_%": "15.0",
                "Al2O3_%": "10.0",
                "Pt_ICP_ppm": "1.0",
                "Pd_ICP_ppm": "1.0",
                "Rh_ICP_ppm": "1.0",
                "Au_ICP_ppm": "1.0",
                "BH_ID": "BH000",
                "Filter": "1",
            }
        )


def test_build_arrays_respects_filter_and_drops_incomplete_rows(tmp_path: Path) -> None:
    csv_path = tmp_path / "synthetic_bushveld.csv"
    _write_synthetic_csv(csv_path, n_boreholes=6, rows_per_borehole=5)

    rows = EXPERIMENT.load_rows(csv_path)
    # 6*5 kept rows + 1 excluded by Filter=="0" + 1 dropped for a missing Cr2O3_% value.
    assert len(rows) == 6 * 5 + 2

    target, baseline, chromite, localities, n_kept = EXPERIMENT.build_arrays(rows)
    assert n_kept == 6 * 5
    assert baseline.shape == (n_kept, 1)
    assert chromite.shape == (n_kept, 2)
    assert target.shape == (n_kept,)
    assert np.unique(localities).size == 6


def test_load_rows_refuses_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="mendeley"):
        EXPERIMENT.load_rows(tmp_path / "does-not-exist.csv")


def test_the_harness_recovers_a_real_texture_style_uplift_on_synthetic_data(tmp_path: Path) -> None:
    """End to end on a synthetic file built so chromite composition genuinely carries extra
    signal beyond Cr2O3 alone — the same shape of claim the real run makes, checked against a
    ground truth this test controls, the way leg (a) of the week-1 gate checks the inversion
    before leg (b) is asked to say anything about real ore.
    """
    csv_path = tmp_path / "synthetic_bushveld.csv"
    _write_synthetic_csv(csv_path, n_boreholes=20, rows_per_borehole=15)

    rows = EXPERIMENT.load_rows(csv_path)
    target, baseline, chromite, localities, _ = EXPERIMENT.build_arrays(rows)

    from reefprint.heads.falsification import evaluate_texture_uplift

    result = evaluate_texture_uplift(target, baseline, chromite, localities)
    assert result.rejects_h0
    assert result.delta_r2 > 0.0
