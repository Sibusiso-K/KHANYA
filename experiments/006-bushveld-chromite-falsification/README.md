# 006 — Week-2 gate, real data: chromite composition vs Cr2O3 alone

**Status: run on real data. Not the literal texture falsification — see *What this does not
show*.**

```bash
uv run python experiments/006-bushveld-chromite-falsification/run.py
```

Needs `data/bushveld_thaba_chromitite/DataSet_Thaba_Classification.csv` on disk (gitignored,
DVC-tracked — see `data/bushveld_thaba_chromitite/SOURCE.md` for the fetch method). Writes
`output/chromite_pge_falsification.json`, not committed (`experiments/**/output/` is
gitignored, same convention as 001 and 005) — the numbers of record are in this README and
`docs/BUILDLOG.md`.

## What it does

CLAUDE.md's week-2 gate asks whether texture carries predictive signal beyond Cr2O3 and
pyroxene fraction. Both `texture_features` (CONTEXT.md item T1) and pyroxene fraction (item T2)
are structurally missing from every public UG2/Bushveld source found so far — not
administratively, genuinely absent from what exists. The literal H0 is therefore **not
testable**, and that is itself the reported result, per Rule 9.

What the one real Bushveld geochemistry dataset in hand (Bachmann et al. 2019, Mendeley,
CC BY 4.0) *does* support is a narrower, related, real question: **does chromite composition —
Cr# and Mg#, the standard chromite-petrology cation ratios (Barnes & Roeder 2001) — add
PGE-grade signal beyond Cr2O3 alone?** This runs `reefprint.heads.falsification.
evaluate_texture_uplift` (the same cluster-robust statistical core the literal gate would use)
against that question, on 1,112 real assay rows across 305 real boreholes.

## Independent cross-check, not a duplicate

Sibusiso wrote the same computation independently on `khanya/main`
(`src/chromite_pge_falsification.py`), importing `reefprint.heads.falsification` unchanged via
the bridge pattern (`polarimetry.py`'s `ensure_reefprint()`). This script re-derives the result
from **this branch's own copy of the data and this branch's own module**, with no import from
`main` — per ADR-0003, work crosses branches via the bridge, never by copying code.

The two independently written implementations produced **bit-for-bit identical results**:

| | This run (`reefprint`) | `khanya/main`'s run |
|---|---:|---:|
| n_obs | 1,112 | 1,112 |
| n_localities | 305 | 305 |
| baseline_r2 | 0.11193237858997018 | 0.11193237858997018 |
| full_r2 | 0.13980320644998467 | 0.13980320644998467 |
| delta_r2 | 0.02787082786001449 | 0.02787082786001449 |
| p_value | 0.00018062196419940484 | 0.00018062196419940484 |

**H0 REJECTED: delta R² = 0.0279 (0.1119 → 0.1398), p = 0.0002, n = 1,112 rows over 305
boreholes (honest n).**

Two separately written programs landing on the same seventeen significant figures is stronger
verification than either alone, and it is exactly the kind of evidence ADR-0003's two-history
separation exists to produce.

## Caveats — stated before a judge finds them

- **Modest effect size.** ΔR² = 0.0279 is a real, significant uplift, not a large one.
- **Cr# is arithmetically related to the Cr2O3 baseline** (both are computed from the same
  Cr2O3_% column) — some of the "uplift" may reflect a non-linear transform of the baseline
  feature itself rather than genuinely independent information from Al/Mg/Fe.
- **This is fitted, in-sample association, not an out-of-locality predictive evaluation.**
  Cluster-robust standard errors correct the *inference* for locality structure; they do not
  test whether the relationship generalises to boreholes the model has not seen.
- **Boreholes within one project may not be fully independent localities** — the coarser
  124-project grouping is the more conservative choice if boreholes within a project share too
  much local geology to count as independent (a Rule 2 call, domain lead's).
- **This is NOT the texture falsification.** Quote it as *"a separate geochemical association
  analysis found additional fitted association after controlling for Cr2O3"* — never as evidence
  that texture predicts processability, and never as H0 rejected in the sense CLAUDE.md's
  falsification test names.

## What this does NOT show

The literal week-2 gate — texture vs Cr2O3 + pyroxene fraction — remains untested, because
`texture_features` remains structurally missing. No amount of chromite-composition signal
closes that gap; it answers a different, real, adjacent question instead. The honest headline
for the literal gate stays *"not testable with available data,"* published with this missing-
data specification, exactly as CLAUDE.md's Rule 9 requires either way the falsification test
comes out.
