"""Week 2 gate, pivoted: does chromite composition add PGE-grade signal beyond
Cr2O3 alone, on real Bushveld assay data?

    python -m src.chromite_pge_falsification

CONTEXT.md item T1 found texture_features structurally missing from every public
UG2/Bushveld source. This session checked the next candidate pivot - a genuine
oxidation index - against the one real Bushveld geochemistry dataset in hand
(Bachmann 2019) and it is ALSO structurally unavailable: the CSV reports iron as
a single total FeO_% column, no separate Fe2O3_%, so Fe3+/(Fe2+ + Fe3+) cannot be
recovered from XRF majors - that split needs wet-chemical titration or Mossbauer
spectroscopy, neither of which this survey used. Not administratively missing,
same as T1's texture finding.

This is the pivot that IS measurable from what the CSV actually contains: Cr#
and Mg#, the standard chromite-petrology cation ratios (Barnes, S.J. & Roeder,
P.L. 2001, "The Range of Spinel Compositions in Terrestrial Mafic and Ultramafic
Rocks", Journal of Petrology 42(12):2279-2302). These are used AS PUBLISHED, not
derived here - Rule 6 forbids an LLM computing a NEW normative-mineralogy method
(the pyroxene-fraction problem in CONTEXT.md T2); citing and applying an existing,
named, peer-reviewed index to its own intended inputs is a different act, and
this docstring states the citation so the choice is auditable, not asserted.

Data: Bachmann et al. 2019, Applied Geochemistry, doi:10.1016/j.apgeochem.2019.02.009.
CSV: data.mendeley.com/datasets/dc8jcnbcvk, CC BY 4.0, DOI 10.17632/dc8jcnbcvk.1.
1205 borehole assay rows, 317 boreholes (BH_ID), Bushveld LG/MG chromitite seams.
Fetched via Mendeley's public files API (the dataset page itself is a client-
rendered SPA with no fetchable file list) - see docs/BUILDLOG.md on the
`reefprint` branch, session that found this dataset, for the same method.
"""
import csv
import json

import numpy as np

from . import polarimetry as _polarimetry  # noqa: F401  (side effect: REEFPRINT src on sys.path)
from .segmentation import config

CSV_PATH = (config.ROOT / "data" / "raw" / "bushveld_thaba_chromitite"
            / "DataSet_Thaba_Classification.csv")

#: Standard molar masses (g/mol). Used only to convert wt% oxide to mole
#: fractions for the cation ratios below - not a fitted or estimated value.
MOLAR_MASS = {"Cr2O3": 151.99, "Al2O3": 101.96, "MgO": 40.30, "FeO": 71.85}

NEEDED_COLUMNS = ["Cr2O3_%", "FeO_%", "MgO_%", "Al2O3_%",
                  "Pt_ICP_ppm", "Pd_ICP_ppm", "Rh_ICP_ppm", "Au_ICP_ppm", "BH_ID"]


def load_rows():
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"{CSV_PATH} not found. Download from data.mendeley.com/datasets/"
            "dc8jcnbcvk (Bachmann 2019, CC BY 4.0) - see this module's docstring "
            "for the fetch method."
        )
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def build_arrays(rows):
    """Filter, clean, and compute Cr#/Mg# from the raw CSV rows.

    Filter=='1' is read as "passes the paper's own QC": 1193 of 1205 rows carry
    it, a small minority (12) carry '0'. That is inferred from the column's
    near-unanimous value, not read from the paper's methods section, and is
    stated here so the assumption is checkable rather than silently made.
    """
    kept = [r for r in rows if r["Filter"] == "1"
            and all(r[c].strip() != "" for c in NEEDED_COLUMNS)]

    def col(name):
        return np.array([float(r[name]) for r in kept], dtype=float)

    cr2o3, feo, mgo, al2o3 = col("Cr2O3_%"), col("FeO_%"), col("MgO_%"), col("Al2O3_%")

    # Cr# = Cr/(Cr+Al), Mg# = Mg/(Mg+Fe2+), as cation (mole) ratios - Barnes &
    # Roeder 2001 (see module docstring). Both oxides in each ratio carry the
    # same cation count per formula unit (Cr2O3/Al2O3: 2 each; MgO/FeO: 1
    # each), so that factor cancels and oxide moles are used directly.
    cr_number = (cr2o3 / MOLAR_MASS["Cr2O3"]) / (
        cr2o3 / MOLAR_MASS["Cr2O3"] + al2o3 / MOLAR_MASS["Al2O3"])
    mg_number = (mgo / MOLAR_MASS["MgO"]) / (
        mgo / MOLAR_MASS["MgO"] + feo / MOLAR_MASS["FeO"])

    # 4E PGE (Pt+Pd+Rh+Au) - the standard Bushveld payable-metal convention,
    # not a normative-mineralogy calculation: just which assayed elements are
    # summed. Ir and Ru are assayed in this CSV but are not part of 4E.
    target = col("Pt_ICP_ppm") + col("Pd_ICP_ppm") + col("Rh_ICP_ppm") + col("Au_ICP_ppm")

    # Cr2O3 only. Pyroxene fraction, the other half of the intended baseline,
    # is not available (CONTEXT.md T2) - this baseline is honestly reduced,
    # not padded with an invented column to make it look complete.
    baseline_features = cr2o3.reshape(-1, 1)
    chromite_features = np.column_stack([cr_number, mg_number])

    _, localities = np.unique([r["BH_ID"] for r in kept], return_inverse=True)

    return target, baseline_features, chromite_features, localities, len(kept)


def main():
    from reefprint.heads.falsification import MIN_LOCALITIES_FOR_INFERENCE, evaluate_texture_uplift

    rows = load_rows()
    target, baseline, chromite, localities, n_kept = build_arrays(rows)
    n_localities = int(np.unique(localities).size)
    print(f"{n_kept} rows kept (of {len(rows)}), {n_localities} boreholes")

    if n_localities < MIN_LOCALITIES_FOR_INFERENCE:
        print(f"REFUSED: only {n_localities} localities, need "
              f"{MIN_LOCALITIES_FOR_INFERENCE} for cluster-robust inference "
              "to mean anything.")
        return

    result = evaluate_texture_uplift(target, baseline, chromite, localities)
    print(result.summary())

    out_path = config.ROOT / "reports" / "chromite_pge_falsification.json"
    out_path.write_text(json.dumps({
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
        "source": ("Bachmann et al. 2019, doi:10.1016/j.apgeochem.2019.02.009; "
                    "CSV data.mendeley.com/datasets/dc8jcnbcvk, CC BY 4.0, "
                    "DOI 10.17632/dc8jcnbcvk.1"),
    }, indent=2))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
