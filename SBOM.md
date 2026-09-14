# SBOM — KHANYA (`main`)

Software bill of materials for this branch. `reefprint` keeps its own
(`docs/05-toolchain.md` / its own `SBOM.md`) - the two commit histories are
kept deliberately separate (ADR-0003), so this is a from-scratch inventory
for `main`, not a copy.

**Method:** `pip show <package>` against this host's installed environment on
2026-09-14, checked against each project's own published license where
`pip show` returned nothing useful. This is a checked inventory, not a legal
audit - before submission, re-run `pip show` on the actual release
environment and verify nothing has drifted, per the 2026-09-12 review's own
instruction ("audit installed closure, not package-name assumptions").

## Direct dependencies (`requirements.txt`)

| Package | Version (this host) | Licence | Notes |
|---|---|---|---|
| torch | 2.13.0 | BSD-3-Clause | `pip show` returned no License field; BSD-3-Clause is PyTorch's own published licence |
| torchvision | 0.28.0 | BSD | Confirmed by `pip show` |
| numpy | 2.2.1 | BSD-3-Clause | `pip show` returns the copyright notice, not an SPDX id; BSD-3-Clause is numpy's own published licence |
| pillow | 12.2.0 | HPND (Historical Permission Notice and Disclaimer) | Permissive, MIT-like. `pip show` returned no License field |
| scikit-learn | 1.9.0 | BSD-3-Clause | Confirmed via `License-Expression` field |
| scipy | 1.18.0 | BSD-3-Clause | `pip show` returns the copyright notice, not an SPDX id; BSD-3-Clause is scipy's own published licence |
| opencv-python (requirements.txt name) | installed as **opencv-python-headless** 4.10.0.84 | Apache-2.0 | **Naming drift, worth fixing**: `requirements.txt` names `opencv-python`, but the resolved/installed package on this host is `opencv-python-headless` (same underlying OpenCV project, no GUI bindings) - functionally fine since this project never opens a GUI window, but `requirements.txt` should name what actually gets installed |
| matplotlib | 3.11.1 | matplotlib licence (BSD-compatible, PSF-derived) | Permissive |
| pandas | 2.2.3 | BSD-3-Clause | Confirmed by `pip show` |
| streamlit | 1.58.0 | Apache-2.0 | `pip show` returned no License field; Apache-2.0 is Streamlit's own published licence |
| starlette | 1.6.0 | BSD-3-Clause | Pinned `>=1.6` in requirements.txt - see that file's own comment for why |
| tqdm | 4.68.3 | MPL-2.0 AND MIT | Confirmed by `pip show`, dual-licensed |
| jinja2 | 3.1.6 | BSD-3-Clause | `pip show` returned no License field; BSD-3-Clause is Jinja's own published licence |
| pytest (dev/CI only, not in requirements.txt) | 8.0.0 | MIT | Confirmed by `pip show` |

Every direct dependency above is permissive (BSD/MIT/Apache/HPND/MPL-family)
and none is GPL/LGPL-family - consistent with `reefprint`'s own "permissive
licences only, SBOM updated in the same commit" rule (`CLAUDE.md`), applied
here to `main` for the first time.

## Pretrained weights

`src/segmentation/model.py` fine-tunes from torchvision's
`DeepLabV3_ResNet50_Weights.COCO_WITH_VOC_LABELS_V1` (pinned explicitly as
of this commit - previously `.DEFAULT`, which happens to resolve to the same
member today but is not guaranteed to keep doing so on a future torchvision
release). Torchvision's pretrained-weights checkpoints are distributed under
the same BSD-3-Clause licence as the torchvision code itself; the *training
data* those weights were originally learned from (COCO + a VOC-labelled
subset) is not redistributed by this project in any form - only the
resulting numeric weights, via torchvision's own hosted checkpoint.

**Not yet done, and the review's actual "Action" item**: pin this weights
enum's exact revision/hash alongside the fine-tuned checkpoint's own hash in
the accuracy report, so a change in either is auditable. The enum pin above
is the code-side half of this; the hash-recording half is still open.

## LumenStone dataset

Not a code dependency, but a data dependency worth recording here too: see
`DATA-SOURCES.md` §1 for the full licensing discussion (informal "free use
in your own research work" terms, decision not to seek further
clarification, and why that decision is defensible given this project
redistributes neither the raw data nor a derived checkpoint publicly).

## Fonts (dashboard)

`dashboard/static/fonts/` vendors Plus Jakarta Sans and JetBrains Mono, both
SIL Open Font License 1.1 - see `dashboard/build/README.md` for the
regeneration process.

## What this file does not yet cover

- Transitive/native dependencies (wheels bundling their own binaries) -
  the review's own instruction is to "audit installed closure, not
  package-name assumptions," which this file has not done for anything
  below the direct-dependency level.
- A machine-readable format (this is prose, not a CycloneDX/SPDX file) -
  fine for a hackathon submission read by a human reviewer, not sufficient
  for an automated MOTT tooling pipeline if one exists.
