# SBOM — software bill of materials

Mandated by CLAUDE.md Rule 7 and by gauntlet finding **S3** (*licence stack unassignable*).

**The test every entry must pass:** can this be assigned to Mintek, on a general-purpose
machine, without a further negotiation?

Status key — **OK** permissive, shippable · **DEV** development-only, never shipped ·
**CONDITION** shippable only under a stated constraint · **VERIFY** licence not yet confirmed
from the upstream repository in this project's own records · **BLOCKED** do not ship.

> Rule 1 applies here too. Every row marked **VERIFY** is an assumption until someone reads the
> upstream `LICENSE` file and changes the row. Do not cite an unverified row in the submission.

---

## Shipped — runtime

| Package | Licence | Status | Note |
|---|---|---|---|
| Python 3.12 | PSF-2.0 | OK | |
| `numpy` | BSD-3-Clause | OK | |
| `scipy` | BSD-3-Clause | OK | |
| `scikit-image` | BSD-3-Clause | OK | |
| `tifffile` | BSD-3-Clause | OK | **Preferred OME-TIFF reader/writer.** See Bio-Formats below. |
| `imagecodecs` | BSD-3-Clause | VERIFY | `tifffile` compression backend. |
| `matplotlib` | PSF-derived (BSD-compatible) | OK | |
| `opencv-python` | Apache-2.0 (library) / MIT (wheel packaging) | VERIFY | OpenCV relicensed 4.5.0→Apache-2.0. Confirm the pinned wheel. |
| `pydantic` | MIT | VERIFY | Config and acquisition-metadata schemas. |

## Shipped — models and inference

| Package | Licence | Status | Note |
|---|---|---|---|
| `torch` | BSD-3-Clause | OK | |
| `timm` | Apache-2.0 | OK | **The reason DINOv3 was rejected.** S3. |
| `segmentation_models_pytorch` | MIT | VERIFY | |
| `xgboost` | Apache-2.0 | OK | |
| `MAPIE` | BSD-3-Clause | VERIFY | Conformal prediction. |
| `crepes` | BSD-3-Clause | VERIFY | Conformal alternative; pick one, not both. |
| `onnxruntime` | MIT | OK | |

**Pretrained weights are a separate licence from the library.** A `timm` architecture under
Apache-2.0 may carry weights under a different licence. Record the weight checkpoint's own
licence here before any weight is used in a graded artefact.

| Checkpoint | Licence | Status |
|---|---|---|
| *(none selected yet)* | — | — |

## Shipped — integration

| Package | Licence | Status | Note |
|---|---|---|---|
| `asyncua` | LGPL-3.0 | **CONDITION** | Runs on a general-purpose machine only. Dynamically linked, user-replaceable. **Never on a sealed Pi appliance** — anti-tivoisation, LGPLv3 §4/GPLv3 §6. S3. |
| `omf` | MIT | VERIFY | On the kill list — cut before AASX is cut. |
| Eclipse BaSyx (AASX) | EPL-2.0 / MIT (component-dependent) | VERIFY | On the kill list, above OMF. |

## Development only — not shipped

| Package | Licence | Status |
|---|---|---|
| `uv` | MIT / Apache-2.0 | DEV |
| `ruff` | MIT | DEV |
| `pytest` | MIT | DEV |
| `pytest-cov` | MIT | DEV |
| `hypothesis` | MPL-2.0 | DEV — weak copyleft, file-level. Test-time only; nothing links it. |
| `pre-commit` | MIT | DEV |
| `mlflow` | Apache-2.0 | DEV |
| `dvc` | Apache-2.0 | DEV |
| `napari` | BSD-3-Clause | DEV — dev-time visual inspection. The demo UI must not depend on it. |

## Flagged — resolve before it becomes load-bearing

| Item | Issue | Disposition |
|---|---|---|
| **Bio-Formats** | The OME Bio-Formats distribution is **GPL-2.0**. CLAUDE.md's stack line lists it for OME-TIFF. Linking GPL-2.0 into a deliverable assigned to Mintek is exactly the S3 failure mode. | **Use `tifffile` (BSD-3-Clause)** for OME-TIFF read/write and OME-XML metadata. Bio-Formats stays a *manual, offline* conversion tool if ever needed, never a dependency. Confirm the licence text before citing this. |
| **Micro-Manager / `pymmcore`** | Mixed licensing across core, device adapters, and vendor device SDKs. Vendor camera SDKs are frequently non-redistributable. | Confirm per adapter *before* the acquisition path depends on it. The Pi/`picamera2` path avoids it entirely. |
| **`picamera2` / `libcamera`** | Apache-2.0 / LGPL-2.1 respectively — VERIFY. | Confirm before the Pi build is load-bearing. |
| **Hailo compiler** | EULA non-assignable. S3. | Optional accelerator, never load-bearing. On the kill list. |
| **DINOv3** | Non-transferable, no patent grant, unilaterally amendable, Californian jurisdiction. | **BLOCKED.** Do not use. Use `timm`. |

## Data and reference sources

Licence of *data* is separate from licence of *code*, and it constrains what may be published.

| Source | Terms | Status |
|---|---|---|
| IMA/COM Quantitative Data File | Published reflectance data, GTK-hosted | VERIFY — confirm reuse terms before redistributing values |
| LumenStone | VERIFY | Check before training on it |
| IronOreRLM | VERIFY | Check before training on it |
| CGS National Core Library specimens | Sampling policy — open question 2 | VERIFY — phone call |
| Craig & Vaughan, *Ore Microscopy and Ore Petrography* 2nd ed. | Open access, MSA | Reference only; do not reproduce figures without checking |
| Mine-sourced specimens | Possible MTA restrictions | Blind spot 3 — an MTA can make the open benchmark unreleasable |

---

## Maintenance

Regenerate the installed set with:

```bash
uv pip list --format=json
```

Add a row for every new dependency **in the same commit that adds it**. An SBOM assembled the
week before the final is not a defence — it is a guess. `SBOM.md` is on the never-cut list.
