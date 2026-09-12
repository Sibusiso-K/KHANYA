"""Week-2 gate, real data, reefprint-native: does chromite composition add PGE-grade signal
beyond Cr2O3 alone, on real Bushveld assay data?

    uv run python experiments/006-bushveld-chromite-falsification/run.py

**This is an independent reproduction, not a copy.** Sibusiso separately wrote
``src/chromite_pge_falsification.py`` on `main`, importing ``reefprint.heads.falsification``
unchanged via the bridge pattern (`polarimetry.py`'s `ensure_reefprint()`), and got
``delta_r2 = 0.0279, p = 0.0002, n = 1112 rows / 305 boreholes`` (`reports/
chromite_pge_falsification.json` on `main`). This script re-derives the same result from this
branch's own copy of the data and this branch's own falsification module, with no import from
`main` — per ADR-0003, work crosses branches via the bridge pattern, never by copying code.
Two independently written implementations of the same computation landing on the same number is
stronger verification than either alone, and it is the originality defence ADR-0003 exists for.

**Texture is not in this run, and cannot honestly be.** CONTEXT.md item T1: no public dataset
pairs polished-section imagery to these exact assay depth intervals, so `texture_features` is
structurally missing, not administratively. This pivots to the measurable question the CSV
actually supports: does chromite composition (Cr#, Mg#) add PGE signal beyond Cr2O3 alone? That
is a different, narrower H0 than CLAUDE.md's literal one (texture vs Cr2O3 + pyroxene fraction)
— reported as exactly that, never as the texture falsification itself. See this experiment's
README for the caveats this result carries.

Cr# and Mg# are the standard chromite-petrology cation ratios (Barnes, S.J. & Roeder, P.L. 2001,
"The Range of Spinel Compositions in Terrestrial Mafic and Ultramafic Rocks", Journal of
Petrology 42(12):2279-2302) — used as published, not derived here. Rule 6 forbids an LLM
computing a *new* normative-mineralogy method (the pyroxene-fraction problem, CONTEXT.md T2);
citing and applying an existing, named, peer-reviewed index to its own intended inputs is a
different act, stated here so the choice is auditable.

Data: Bachmann et al. 2019, Applied Geochemistry, doi:10.1016/j.apgeochem.2019.02.009.
CSV: data.mendeley.com/datasets/dc8jcnbcvk, CC BY 4.0, DOI 10.17632/dc8jcnbcvk.1.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from reefprint.heads.falsification import MIN_LOCALITIES_FOR_INFERENCE, evaluate_texture_uplift

CSV_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "bushveld_thaba_chromitite"
    / "DataSet_Thaba_Classification.csv"
)
OUTPUT = Path(__file__).parent / "output" / "chromite_pge_falsification.json"

#: Standard molar masses (g/mol), used only to convert wt% oxide to mole fractions for the
#: cation ratios below — not a fitted or estimated value.
MOLAR_MASS = {"Cr2O3": 151.99, "Al2O3": 101.96, "MgO": 40.30, "FeO": 71.85}

NEEDED_COLUMNS = [
    "Cr2O3_%",
    "FeO_%",
    "MgO_%",
    "Al2O3_%",
    "Pt_ICP_ppm",
    "Pd_ICP_ppm",
    "Rh_ICP_ppm",
    "Au_ICP_ppm",
    "BH_ID",
]


def load_rows(csv_path: Path) -> list[dict[str, str]]:
    if not csv_path.exists():
        raise FileNotFoundError(
            f"{csv_path} not found. Download from data.mendeley.com/datasets/dc8jcnbcvk "
            "(Bachmann 2019, CC BY 4.0) — see data/bushveld_thaba_chromitite/SOURCE.md."
        )
    with csv_path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


def cation_ratios(
    cr2o3: np.ndarray, feo: np.ndarray, mgo: np.ndarray, al2o3: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Cr# = Cr/(Cr+Al) and Mg# = Mg/(Mg+Fe2+), as cation (mole) ratios (Barnes & Roeder 2001).

    Both oxides in each ratio carry the same cation count per formula unit (Cr2O3/Al2O3: 2
    each; MgO/FeO: 1 each), so that factor cancels and oxide moles are used directly. Kept as a
    pure function of four wt% arrays so the arithmetic is checkable against hand-worked values
    without the CSV on disk — see ``test_cation_ratios_match_a_hand_worked_example``.
    """
    cr_moles = cr2o3 / MOLAR_MASS["Cr2O3"]
    al_moles = al2o3 / MOLAR_MASS["Al2O3"]
    mg_moles = mgo / MOLAR_MASS["MgO"]
    fe_moles = feo / MOLAR_MASS["FeO"]
    return cr_moles / (cr_moles + al_moles), mg_moles / (mg_moles + fe_moles)


def build_arrays(
    rows: list[dict[str, str]],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]:
    """Filter, clean, and compute Cr#/Mg# from the raw CSV rows.

    ``Filter == "1"`` is read as "passes the paper's own QC": 1,193 of 1,205 rows carry it,
    a small minority (12) carry "0" — respected, not overridden, per CLAUDE.md's own note on
    this dataset (it is the source's own judgement about which rows are usable).
    """
    kept = [
        row
        for row in rows
        if row["Filter"] == "1" and all(row[c].strip() != "" for c in NEEDED_COLUMNS)
    ]

    def col(name: str) -> np.ndarray:
        return np.array([float(row[name]) for row in kept], dtype=float)

    cr2o3, feo, mgo, al2o3 = col("Cr2O3_%"), col("FeO_%"), col("MgO_%"), col("Al2O3_%")
    cr_number, mg_number = cation_ratios(cr2o3, feo, mgo, al2o3)

    # 4E PGE (Pt+Pd+Rh+Au) — the standard Bushveld payable-metal convention, not a
    # normative-mineralogy calculation: just which assayed elements are summed. Ir and Ru are
    # assayed in this CSV but are not part of 4E.
    target = col("Pt_ICP_ppm") + col("Pd_ICP_ppm") + col("Rh_ICP_ppm") + col("Au_ICP_ppm")

    # Cr2O3 only. Pyroxene fraction, the other half of the intended baseline, is not available
    # (CONTEXT.md T2) — honestly reduced, not padded with an invented column.
    baseline_features = cr2o3.reshape(-1, 1)
    chromite_features = np.column_stack([cr_number, mg_number])

    _, localities = np.unique([row["BH_ID"] for row in kept], return_inverse=True)

    return target, baseline_features, chromite_features, localities, len(kept)


def main() -> None:
    rows = load_rows(CSV_PATH)
    target, baseline, chromite, localities, n_kept = build_arrays(rows)
    n_localities = int(np.unique(localities).size)
    print(f"{n_kept} rows kept (of {len(rows)}), {n_localities} boreholes")

    if n_localities < MIN_LOCALITIES_FOR_INFERENCE:
        print(
            f"REFUSED: only {n_localities} localities, need {MIN_LOCALITIES_FOR_INFERENCE} "
            "for cluster-robust inference to mean anything."
        )
        return

    result = evaluate_texture_uplift(target, baseline, chromite, localities)
    print(result.summary())

    payload = {
        "n_obs": result.n_obs,
        "n_localities": result.n_localities,
        "baseline_r2": result.baseline_r2,
        "full_r2": result.full_r2,
        "delta_r2": result.delta_r2,
        "wald_statistic": result.wald_statistic,
        "p_value": result.p_value,
        "rejects_h0": result.rejects_h0,
        "target": "4E PGE (Pt+Pd+Rh+Au), ppm",
        "baseline_features": ["Cr2O3_%"],
        "challenger_features": ["Cr# (Barnes & Roeder 2001)", "Mg# (Barnes & Roeder 2001)"],
        "source": (
            "Bachmann et al. 2019, doi:10.1016/j.apgeochem.2019.02.009; "
            "CSV data.mendeley.com/datasets/dc8jcnbcvk, CC BY 4.0, DOI 10.17632/dc8jcnbcvk.1"
        ),
        "note": (
            "This is NOT the texture falsification CLAUDE.md's H0 names. Texture_features is "
            "structurally missing (CONTEXT.md T1). This tests a narrower, real question: does "
            "chromite composition add signal beyond Cr2O3 alone. Cross-check: an independent "
            "implementation on khanya/main (src/chromite_pge_falsification.py) computed the "
            "same test on the same data and reported delta_r2=0.0279, p=0.0002, n=1112/305."
        ),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
