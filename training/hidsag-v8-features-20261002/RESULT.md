# v8 spectral associations: result (2026-10-02 08:48)

The spec (`SPEC.md`) and the analysis script (`analyse_v8_features.py`) were both committed before any output existed (commits 81e75fb and 4e34c04). Full output: `analysis_v8_features.json`.

**Primary endpoint** (v6 mask, pooled mean spectrum, partial Spearman after fraction × line, cluster bootstrap by composite, Holm across H1, H2 and H4):

| Hypothesis | Partial ρ | 95% CI (composites) | Holm p | Verdict |
|---|---|---|---|---|
| H1 Al-OH ↔ muscovite/sericite + kaolinite | +0.135 | −0.10 to +0.39 | 0.27 | inconclusive |
| H2 Fe-OH + Mg-OH ↔ chlorite + biotite | **+0.271** | +0.03 to +0.49 | **0.045** | positive, **below the minimum useful effect (0.30)** |
| H4 Fe³⁺ 900 nm ↔ Fe oxides | +0.032 | −0.20 to +0.28 | 0.39 | inconclusive |
| H3 gypsum 1750 (exploratory) | +0.010 | −0.22 to +0.23 | — | inconclusive |

**Reading:**
- Raw correlations are larger (H1 +0.41, H2 +0.53), but most of that is size fraction and process line: the same confound that sank the MINERAL1 claim.
- No hypothesis passes the full pre-registered gate. H2 is a real but small association.
- **The belt sensor does not earn a "≥3 mineral phases" claim from this data.** The brief's phase deliverable rests on KHANYA's microscope segmentation.

**Sensitivity checks:**
- **No dark mask:** the same conclusions.
- **Median per-pixel aggregation** (secondary, not the endpoint):
  - H4 reaches +0.40, but its raw ρ is −0.48. The sign flips after stratification, so it is unstable and not claimed.
  - H2 stays about +0.26.

**Identity:**
- 99 records, each with 1 crop, from 36 composites across 12 months.
- No duplicates under the pre-set rule (identical QEMSCAN vector and tags). The dataset paper's 94 physical samples are therefore **not reconciled**: 5 records remain unexplained. This is logged, not resolved.

**Power** (Fisher z, 36 clusters, α = 0.05/3): 0.36 at ρ = 0.3 and 0.85 at ρ = 0.5. An honest "inconclusive" was always the likely outcome at this sample size.
