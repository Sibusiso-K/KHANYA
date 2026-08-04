# Data sources — research phase

Status as of 2026-08-04. Verify licences again before the report is finalised.

## 1. LumenStone — primary target, ACCESS BLOCKED

Reflected-light images of **polished ore sections** with pixel-level multi-class
masks. Exact match for Problem 3.

| Subset | Images | Minerals |
|---|---|---|
| S1 | 84 (59 train / 16 test) | sphalerite, pyrite/marcasite, galena, bornite, tennantite-tetrahedrite, chalcopyrite, background (7 classes) |
| S2 | 39 | pyrrhotite, pentlandite, chalcopyrite |
| S3 | 35 | arsenopyrite, covellite |
| V1 / P1 | — | colour adaptation; panoramas |

- Host `https://imaging.cs.msu.ru/en/research/geology/lumenstone` returns **HTTP 500**
  (server down, not blocking us). Licence and download links UNCONFIRMED.
- Wayback snapshot exists (2026-03-09) but archive.org is unreachable from here.
- **Action:** email Alexander Khvostikov, ORCID 0000-0002-4217-7141. Repo active
  (last commit 2026-06-16).
- Benchmark to beat: **mean IoU 0.8373** (ResUNet, S1v1). Also PSPNet+ResNet18 on
  S1+S2: IoU 0.88, pixel accuracy 0.96.

### petroscope — the authors' toolkit
`pip install petroscope` — https://github.com/xubiker/petroscope

Provides LumenStone class definitions, ResUNet baseline, correct dataset-wide
IoU metrics, and a **patch-based self-balancing sampler**. Their README warns that
mineral class imbalance is severe and that loss weighting / class weighting does
NOT fix it. Take this seriously — it is the failure mode for this task.

## 2. FeM iron ore — DOWNLOADABLE NOW

https://zenodo.org/record/5014700

- `FeM_v1.zip`, 112 MB. 999x756 px at 1.05 um/px.
- **CC-BY-4.0**, open, no registration.
- Binary ore/resin masks only — does NOT meet the >=3 phase requirement alone.
- Cite: Filippo et al., Minerals Engineering 170 (2021) 107007.

## 3. MUMDMC2025 — DOWNLOADABLE NOW

- Sample (start here): 2,500 XPL images, 500/class —
  https://figshare.com/articles/dataset/MUMDMC2025_DataSet_sample/29483204
- Full: 14,400 JPEG, 3584x2746 @ 600 DPI, ~84 GB. **CC-BY-4.0**.
- 5 classes: biotite, hornblende, plagioclase, K-feldspar, quartz (2,880 each).
- 72 rotations per specimen under PPL and XPL. Rotations are near-duplicates —
  this is exactly why splits must be grouped by specimen.
- Paper: https://www.nature.com/articles/s41597-025-05879-9

## 4. Weak fallbacks — hand specimens, not micrographs

- https://www.kaggle.com/datasets/asiedubrempong/minerals-identification-dataset
- https://www.kaggle.com/datasets/sergeynesteruk/minerals (MineralImage5k)

Wrong modality for this brief. Use only if everything else fails, and say so.

## 5. South African ore imagery — NONE FOUND OPEN

Searched UG2 / Merensky / Bushveld specifically. Mintek's mineralogical work on
these ores is published as papers, not datasets. No competing team will have local
data either, so asking Mintek directly is the highest-value request available.

## Method references

- DeepLabv3+ opaque/non-opaque segmentation: https://www.sciencedirect.com/science/article/abs/pii/S0892687521002363
- Improved YOLOv8n fine-grained mineral segmentation: https://www.sciencedirect.com/science/article/abs/pii/S0892687525001189
- Polished-section segmentation and labelling: https://link.springer.com/article/10.1007/s42461-025-01205-4
- Res-UNet ensemble, mineral optical microscopy: https://doi.org/10.3390/min14121281
- Korshunov et al., visual diagnostics to deep learning: https://mst.misis.ru/jour/article/view/974

## Domain angle worth citing

SEM/BSE cannot separate hematite from magnetite — near-identical average atomic
number. Reflected-light optical can, on reflectance and colour. This justifies
cheap optical + CNN against a multi-million-rand automated mineralogy instrument.
