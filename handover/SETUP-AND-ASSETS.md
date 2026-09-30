# Setup and asset register — 29 September 2026

## Checked facts

| Item | Observed status | Action |
|---|---|---|
| Application code | Latest inspected main `9181668`; isolated worktree created | Implement here: `C:\Users\USER\.codex\worktrees\khanya-build-plan\REEFPRINT` |
| GitHub | Authenticated gh; push permission true; no releases or Actions artifacts found | Push source/docs only; no secret output |
| Global Python | 3.11.9 at `C:\Python311\python.exe` | Available, but use dedicated project environment |
| Existing physics venv | Python 3.12.12, works with host filesystem access | Do not modify shared physics environment |
| Existing venv packages | pytest/asyncua found; torch/torchvision/pandas/Streamlit absent | Create and verify application venv |
| Node | v24.18.0 | Only needed for existing CSS rebuild or optional Cesium asset build |
| S2 images and weights | No matches in two supplied project roots; absent in repository artifacts checked | User explicitly approves retraining |
| S3 archive | Local `data/lumenstone/S3_v2.zip`, 5,227,181,560 bytes | Not needed for primary S2 model |
| V1 archive | Local `data/lumenstone/V1_v1.zip`, 104,705,467 bytes | S1 re-imaging experiment only; do not use with S2 as in-domain proof |
| Bushveld chemistry | Local `data/bushveld_thaba_chromitite/DataSet_Thaba_Classification.csv` | Replay optional; original source/units retained; no coordinates |
| GPU | Availability not verified | Inspect before planning training duration |
| QGIS/QField/Cesium | Installation/assets not verified or staged | Optional geography ticket; not a model prerequisite |

The first sandboxed attempt to launch the physics venv failed on its interpreter path; an authorised host check then succeeded. This was an access issue, not evidence the venv was broken.

## Required data and model files

1. Download **S2 v2** from the [official LumenStone page](https://imaging.cs.msu.ru/en/research/geology/lumenstone), using the S2 v2 link, not S1/S3 or v1. Page currently advertises about 419 MB. Follow the publisher link; don't reuse an expired temporary download URL.
2. Save archive/source metadata and SHA256. Inspect member names before extraction; preserve original data. Expected model layout: `data/raw/lumenstone/S2_v2/imgs/train`, `imgs/test`, `masks/train`, `masks/test`. Avoid accidental duplicate nesting after extraction.
3. Verify 37 image/mask pairs in publisher train and 12 in test. Existing split code carves six validation images from training with seed 42, leaving 31 training images. Check specimen identity/duplicates where metadata permits; disclose any unknown grouping. Never split patches across train/test.
4. Record class codebook from `src/segmentation/lumenstone.py`; labels are not arbitrary display colours.
5. Train to a new run directory or safely preserve any existing `best.pt`/`last.pt`. Expected default output is `checkpoints/lumenstone_s2_patches/best.pt`. New run => new hash and new metrics.

The default patch trainer currently uses 512-pixel patches, batch 2, 64 training patches/epoch, 32 validation patches, eight epochs and learning rate 2e-4. Environment variables override the budgets. Record actual values; an older prose reference to 12 epochs is not a substitute for the executable configuration. A short smoke run validates plumbing, not final model quality. Do not resume an unrelated `last.pt` accidentally.

## Account and software checklist

| Resource | Required signup/payment? | Use |
|---|---|---|
| GitHub | Existing authenticated account sufficient | Already available |
| Python, PyTorch, Streamlit, scientific packages | No paid account | Local train/infer/UI |
| LumenStone publisher download | Public publisher link; no new account expected, verify link availability | Research data; cite source and retain terms |
| Google Colab | Google account, optional free interactive GPU | Contingency if local training is too slow; resources not guaranteed [FAQ](https://research.google.com/colaboratory/faq.html) |
| Kaggle | User intends to train there; account required, free GPU subject to availability | Use [KAGGLE-TRAINING.md](KAGGLE-TRAINING.md). Dataset access, GPU setting and output download remain separate steps. New S2 mirror was paused in the repo's rights report. |
| QGIS / QField | No paid cloud signup needed for local files | Optional field/GIS tooling |
| CesiumJS | No account for self-hosted library/local assets | ion-hosted services are a separate choice and not required |
| USGS | Public data route; inspect chosen record/download | Optional real geolocated sample demo |
| IBM Quantum | Optional IBM account; no need to create now | Deferred experiment only |
| LLM APIs, paid GPU, Leapfrog, XRF hardware | None required for MVP | No purchases or keys requested |

No new accounts have been created, and no paid service is authorised by this document. Existing laptop/power/internet/labour are still costs, even if incremental software/API fees are zero.

## Installation and reproduction runbook for the implementer

Run inside the managed KHANYA worktree. These are **planned commands**, not commands already executed successfully for the application:

```powershell
git status --short
git branch --show-current
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pytest
.\.venv\Scripts\python.exe -c 'import torch, torchvision, streamlit, pandas, asyncua; print(torch.__version__); print(torch.cuda.is_available())'
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest tests/ -q
```

Choose compatible torch/torchvision CPU or CUDA wheels using the [official installer](https://pytorch.org/get-started/locally/) for the available device. Do not assume installing the generic requirements establishes GPU support. Pin the successfully tested environment in a new lock/manifest rather than changing dependencies arbitrarily. The repo currently requires `starlette>=1.6`; its comment explains a historical Streamlit import issue. Verify the actual environment before changing that workaround.

After staging S2 and recording the split:

```powershell
$env:KHANYA_SUBSET = 'S2'
.\.venv\Scripts\python.exe -m src.segmentation.train_patches
.\.venv\Scripts\python.exe -m src.segmentation.train_patches --eval
.\.venv\Scripts\python.exe -m src.decision_gap --model patches --refine
.\.venv\Scripts\python.exe -m src.benchmark
Get-FileHash -Algorithm SHA256 .\checkpoints\lumenstone_s2_patches\best.pt
.\.venv\Scripts\python.exe -m streamlit run dashboard/app.py
```

**Important:** `src.benchmark` uses cached predictions. Preserve historical artifacts and generate fresh inference caches for the new checkpoint; attach their model hash before scoring. The script defaults may overwrite historical report filenames: first add a run-specific output option or make a versioned copy and ensure no stale cache can be accepted. Never overwrite old research evidence without preserving its original provenance.

Training initially downloads upstream pretrained weights. Cache permitted assets before the offline demonstration. Measure a representative epoch and project remaining time; if it will miss the freeze, use an available authorised GPU runtime or reduce scope—not fake model output. Use validation only to choose a training budget/checkpoint. Keep the 12-image test for the final frozen run. Existing public-test exposure must be disclosed in the report.

For OPC UA, `dashboard/opcua.py` imports `reefprint.integrate` through `src.polarimetry.ensure_reefprint`. Inspect that loader, set `REEFPRINT_SRC` to the existing physics checkout's `src` directory if appropriate, and verify the imports with the application interpreter. Do not copy/merge the separate histories. Record both code SHAs in the release manifest. Bundle a permitted pinned physics source dependency for an eventual portable demo; absolute host paths alone are not a release package.

## Conditional geography assets

Required for a genuine marker: source record ID, valid coordinates, known CRS, position uncertainty if available. Required for real borehole trajectory: collar XYZ, datum/CRS, survey azimuth/dip by measured depth. Required for a geological volume: contacts/orientations and an explicit modelling method. None is supplied by the local assay CSV.

Use source-preserving imports, data dictionary, local licensed terrain and an offline fallback. If these cannot be staged and checked in time, ship the real assay-depth view and describe terrain as the next step. Do not turn guessed positions into demo facts.
