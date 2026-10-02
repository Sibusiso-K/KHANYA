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
| Public Sans (font, `@fontsource-variable/public-sans`) | OFL-1.1 | OK | Bundled as `presentation/belt-monitor/fonts/` with its licence file; the workbench already loads it via fontsource. Added to the SBOM 2026-10-01. |
| `scipy` | BSD-3-Clause | OK | |
| `scikit-image` | BSD-3-Clause | OK | |
| `tifffile` | BSD-3-Clause | OK | **Preferred OME-TIFF reader/writer.** See Bio-Formats below. |
| `imagecodecs` | BSD-3-Clause | VERIFY | `tifffile` compression backend. |
| `matplotlib` | PSF-derived (BSD-compatible) | OK | |
| `pillow` | MIT-CMU | OK | JPEG decode for public archives (LumenStone frames are JPEG). Licence read from the installed distribution's own `License-Expression` metadata, 12.3.0, 2026-08-20 — that is the SPDX declaration attached to the wheel we actually install. |
| `opencv-python` | Apache-2.0 (library) / MIT (wheel packaging) | VERIFY | OpenCV relicensed 4.5.0→Apache-2.0. Confirm the pinned wheel. |
| `pydantic` | MIT | VERIFY | Config and acquisition-metadata schemas. |

| `cryptography` 50.0.2 | Apache-2.0 OR BSD-3-Clause | OK | Secure server: AES-256-GCM, Ed25519, X25519, HKDF. pip-audit flagged 9 CVEs in 46.0.6; upgraded 2026-10-02. |
| `pqcrypto` 1.0.0 | Apache-2.0 (PQClean bindings) | OK | ML-DSA-65 (FIPS 204) checkpoint signatures, ML-KEM-768 (FIPS 203) export KEM, SLH-DSA available. Not a FIPS-validated module. Added 2026-10-02. |
| Pillow 12.3.0 | MIT-CMU | OK | Upload re-encoding (EXIF/GPS stripped). Added 2026-10-02. |
| `qrcode` 8.2 | BSD | OK | QR code for the demo URL. Added 2026-10-02. |

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
| `torchvision.models.segmentation.deeplabv3_resnet50` architecture code | BSD-3-Clause | OK — `require_permissive_backbone("torchvision", "BSD-3-Clause")` |
| `DeepLabV3_ResNet50_Weights.DEFAULT` (`COCO_WITH_VOC_LABELS_V1`) checkpoint | Not a clean single licence — read 2026-09-15 | **CONDITION.** Confirmed against torchvision's own model docs: trained on **a subset of COCO restricted to the 20 Pascal VOC categories**, with the ResNet50 backbone itself pretrained on **ImageNet** (`ResNet50_Weights.IMAGENET1K_V1`). torchvision's own `LICENSE` (BSD-3-Clause) covers the **code**, and — checked directly, not assumed — makes **no statement about the distributed pretrained weights**. Neither COCO nor ImageNet publish their underlying images under a blanket redistribution licence (COCO's own annotations are CC BY 4.0; the images are third-party-photographer copyright via Flickr). **Do not present this checkpoint as licence-clean** — the code is; the weight's own permission chain is not, and this row exists so nobody re-asks the question having forgotten the answer was "unresolved," not "fine." |
| Kaggle-hosted pin of the above | as above | **Uploaded 2026-09-15**: `lethabomh14/torchvision-deeplabv3-resnet50-coco` (private), file `deeplabv3_resnet50_coco-cd0a2569.pth`. Downloaded directly from `https://download.pytorch.org/models/deeplabv3_resnet50_coco-cd0a2569.pth` (no `torch`/`torchvision` install needed — those are KHANYA's dependency, not REEFPRINT's) and verified: sha256 `cd0a25694c4a0f7106b38f4938bf90a874f2f241cc410b8f63c7024399538f06`, matching the `cd0a2569` prefix torchvision embeds in its own filename as an integrity check. 168,312,152 bytes. This unblocks J0/J1/J2 model construction on `enable_internet: false` kernels; the S1/S2 **data** upload (asked of Sibusiso, issue #5) is the separate, still-open prerequisite |

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
| `h5py` | BSD-3-Clause | DEV — Kaggle-only, reads the HIDSAG hyperspectral cubes in `training/hidsag-hyperspectral-20261001/run.py` (installed in the kernel if absent). Not a runtime dependency. Added 2026-10-01. |

## Flagged — resolve before it becomes load-bearing

| Item | Issue | Disposition |
|---|---|---|
| **Bio-Formats** | The OME Bio-Formats distribution is **GPL-2.0**. CLAUDE.md's stack line lists it for OME-TIFF. Linking GPL-2.0 into a deliverable assigned to Mintek is exactly the S3 failure mode. | **Use `tifffile` (BSD-3-Clause)** for OME-TIFF read/write and OME-XML metadata. Bio-Formats stays a *manual, offline* conversion tool if ever needed, never a dependency. Confirm the licence text before citing this. |
| **`petroscope`** | **GPL-3.0.** The library published alongside LumenStone (github.com/xubiker/petroscope). Copyleft, and funded under a Russian Science Foundation grant — a second, non-licence reason to keep it out of an assigned deliverable. | **BLOCKED as a dependency.** The LumenStone *data* is a separate question and is handled in the data table. Never `pip install petroscope`. |
| **Micro-Manager / `pymmcore`** | Mixed licensing across core, device adapters, and vendor device SDKs. Vendor camera SDKs are frequently non-redistributable. | **Moot — ADR-0002, no rig, nothing to drive.** Removed from the stack. Revisit only if microscope access is ever donated. |
| **`picamera2` / `libcamera`** | Apache-2.0 / LGPL-2.1 respectively — VERIFY. | **Moot — ADR-0002.** Not installed; not an extra. Was documented as an apt package on Raspberry Pi OS. |
| **Hailo compiler** | EULA non-assignable. S3. | Optional accelerator, never load-bearing. On the kill list. |
| **DINOv3** | Non-transferable, no patent grant, unilaterally amendable, Californian jurisdiction. | **BLOCKED.** Do not use. Use `timm`. |

## Data and reference sources

Licence of *data* is separate from licence of *code*, and it constrains what may be published.

| Source | Terms | Status |
|---|---|---|
| IMA/COM Quantitative Data File | Published reflectance data, GTK-hosted (`projects.gtk.fi/com/results/reflectance_data.html`). Also USGS OFR 79-658 and OFR 89-306A/B; Criddle & Stanley 1993, 3rd ed. | VERIFY — confirm reuse terms before redistributing values. **Blocks the `Provenance.PLACEHOLDER` reflectances in `reefprint.acquire.phantom`.** |
| LumenStone (S1, S2, S3, V1) | **Terms of use confirmed 2026-09-14** — no named OSI licence, but an explicit written grant, quoted verbatim from `imaging.cs.msu.ru/en/research/geology/lumenstone`: *"You are free to use the provided data in your own research work. If you intend to publish research work that uses this dataset, you have to cite the references whenever appropriate."* Citations: Korshunov et al. 2025, doi:10.17073/2500-0632-2025-05-416 (dataset authors' own paper). **V1 (colour-adaptation subset) downloaded 2026-09-15** directly from the dataset's own Yandex Disk link (`imaging.cs.msu.ru`'s summary table → 100 MB), verified as 30 images (10 samples × 3 imaging variations) matching the published description; staged at `data/lumenstone/V1_v1.zip` (gitignored, DVC-tracked convention) and uploaded as a private Kaggle dataset, `lethabomh14/lumenstone-v1-reefprint`, for use from either branch's kernels. | **CONDITION, no longer VERIFY** — usable, citation required whenever published. The petroscope README and library remain a **separate, blocked** dependency (GPL-3.0, row above) — this row covers the *data* only. |
| IronOreRLM | 563 reflected-light images. ScienceDirect `S2352340925002720`. | VERIFY — check before training on it |
| MUMDMC2025 | 14,400 photomicrographs, 5 silicate classes, 72 rotational positions at 5° over 360°, PPL + XPL. *Nature Sci Data* 2025. | VERIFY. **Transmitted light on granite silicates** — exercises the rotation pipeline, carries none of the reflected-light ore physics. Do not cite it as ore evidence. |
| Kaggle "Quality Prediction in a Mining Process" (edumagalhaes) | **CC0-1.0**, read from the dataset metadata 2026-10-01. A real iron-ore flotation plant (Brazil), Mar–Sep 2017, 20 s process tags and hourly lab assays. Raw CSV in `data/kaggle_flotation/` (gitignored); hourly derived series ship in `presentation/belt-monitor/live/`. | **OK.** Iron ore, not PGM: a method demonstration for plant parameters. |
| Bachmann et al. 2019, Bushveld chromitite assays (Mendeley 10.17632/dc8jcnbcvk.1) | **CC BY 4.0**, recorded in `data/bushveld_thaba_chromitite/SOURCE.md`. Derived out-of-fold predictions ship in `live/bushveld.json`. | **OK, cite** the dataset and the J. African Earth Sciences paper. |
| HIDSAG (Ehrenfeld et al., *Scientific Data* 2023) | Figshare collection 10.6084/m9.figshare.c.5983921 — records marked **CC0** on Figshare (read 2026-10-01); the paper is CC BY 4.0. Porphyry Cu-Mo, Chile: GEOMET (146 drill-core samples with flotation and grinding tests), MINERAL1 (99 plant-feed size-fraction samples, QEMSCAN wt%). VNIR + SWIR cubes. Used for the belt hyperspectral track, 2026-10-01. | **OK** — cite the paper. Not PGM ore: results transfer as a method, not as numbers. |
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
