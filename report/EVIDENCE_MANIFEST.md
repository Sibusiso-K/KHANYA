# Evidence manifest for the technical report

This file is the linked supplement cited in Appendix A of `main.tex`. It identifies which evidence packages support which statements. It records only hashes the team actually holds; missing items are marked, not guessed.

## Public revision

| Item | Identifier |
|---|---|
| Audited application release | commit `85061d418d8938cf79ba740bbbf84635667b7c2a` (repository `Sibusiso-K/KHANYA`) |

## Checkpoints (SHA-256)

| Role | Full hash |
|---|---|
| Historical evaluated | `de7135a96541a46dc0981a991cb954186c7cd669ea1c1b33914d1929ae9b1357` |
| Audited build (not approved) | `fb78727d4859947d3605ccf9374f8defbc40897e9cf1b1922a52c1832d387067` |
| Candidate (quarantined) | `42646cfafbeac5398386dba17f7ad3531ffcea572e6342cc4fcba42ed0b44b3b` |

## Local evidence packages (not yet public)

| Package | Supports | Identifier | Held by |
|---|---|---|---|
| Continuation bundle (7 Oct 2026) | BatchNorm rejection (§4.4); first smoke check (52.9 s) | ZIP SHA-256 `d21478141ca76a56d6ea82934874cd2ab536609fa96e333b7d4a0b8e3313e831` (67-entry manifest, verified by a separate AI-assisted computational review) | L. Hoaeane |
| Tasks A–D package (7 Oct 2026) | Abstention fixes, support audit (§4.5), 321 passed / 4 skipped, 72.9 s smoke check | 371-file manifest; **archive hash not recorded here; to be added by the build owner** | L. Hoaeane |
| Measurement-feasibility package (7 Oct 2026) | Geometry diagnostic (§4.5: 27,855 edge pixels; 10,263,972 component-excluded pixels) | 37-file manifest; **archive hash not recorded here; to be added by the build owner** | L. Hoaeane |
| B02 spectral-model comparison (7 Oct 2026) | Appendix A: exploratory PLS/kernel comparison on reused HIDSAG copper mineralogy data | protocol.json, completion.json, splits.csv, predictions.csv, metrics.csv; **archive hash not recorded here; to be added by the build owner** | L. Hoaeane |
| B03a app-integrated PLS export (7 Oct 2026) | Appendix A: recorded-spectrum inference. Binding v2: altered intake and misbinding rejected; binding v3: recomputation refuses forged results (reviewer re-ran the 42 wt% reproducer: PREDICTION_RECOMPUTATION_MISMATCH); storage-error codes still to correct | `webapi/belt.py` + `research/belt_real/spectral_inference.py`, model `B03_verified`; **model hash, source revision and release identity to be added by the build owner** | L. Hoaeane |
| B03b standalone SNV service (7 Oct 2026) | Appendix A: stricter units/wavelength contract | `research/belt_b03/` with `reports/belt-b03-20261007/B03/model`; **model hash, source revision and release identity to be added by the build owner** | L. Hoaeane |
| B04 extraction study (8 Oct 2026) | Appendix A: three extraction recipes, 396 metric rows; no recipe promoted | **archive hash and file list to be added by the build owner** | L. Hoaeane |

Counts from different packages overlap and must not be added. None of these packages contains independent local specimens or laboratory references.
