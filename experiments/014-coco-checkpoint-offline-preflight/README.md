# 014 — the COCO checkpoint preflight: `model.py`'s construction call does not work offline as written

**Status: run, and the risk was real.** `khanya/main:src/segmentation/model.py`'s current
construction call (`weights=DeepLabV3_ResNet50_Weights.DEFAULT`) fails on a Kaggle kernel with
`enable_internet: false` — exactly the setting J0/J1/J2 need. Caught before any GPU-hour was
spent on it, not after.

```bash
kaggle kernels push -p experiments/014-coco-checkpoint-offline-preflight
```

Ran as `lethabomh14/reefprint-coco-checkpoint-preflight` (~1 minute, CPU only — this is a
correctness check, not a training run).

## Result

| Check | Result |
|---|---|
| Mounted checkpoint sha256 matches `SBOM.md`'s record | ✅ **True** — the staged file is genuine |
| **Approach 1 — `model.py`'s current code, unmodified** | ❌ **FAILED**: `URLError: Temporary failure in name resolution`. `deeplabv3_resnet50(weights=DeepLabV3_ResNet50_Weights.DEFAULT, ...)` calls `weights.get_state_dict()` internally, which tries `download_url_to_file` to `download.pytorch.org` regardless of whether a same-named file already exists elsewhere on disk — mounting the checkpoint as a Kaggle dataset at an arbitrary path does **not** satisfy this. |
| Approach 2 — copy the mounted file into torch's own hub cache (`~/.cache/torch/hub/checkpoints/deeplabv3_resnet50_coco-cd0a2569.pth`) first, then call the identical construction | ✅ **Succeeded**, 1.8s, output shape `[1, 21, 256, 256]` (21 = COCO-with-VOC-labels classes) |
| Approach 3 — construct with `weights=None`, load the mounted file's `state_dict` explicitly | ✅ **Succeeded**, 1.4s, **0 missing keys, 0 unexpected keys** — the cleanest fit |

## What this means for J0/J1/J2

**`model.py`'s `build_model(pretrained=True)` will crash at model construction, before a single
training step, on any Kaggle kernel run with `enable_internet: false`** — which every kernel in
this project has used so far (`007`–`013`, and by extension the planned J0/J1/J2). This was
invisible until tested directly: the checkpoint being correctly staged and sha-verified (`SBOM.md`,
session 33) is necessary but not sufficient — torchvision's own weight-loading machinery still
tries the network first regardless.

**Two fixes, either sufficient on its own:**

1. **Minimal, no code change**: at the top of the training kernel's entry point, before calling
   `build_model()`, copy the mounted checkpoint into torch's hub cache under the exact filename
   torchvision expects:
   ```python
   import shutil
   from pathlib import Path

   cache_dir = Path.home() / ".cache" / "torch" / "hub" / "checkpoints"
   cache_dir.mkdir(parents=True, exist_ok=True)
   shutil.copy(mounted_checkpoint_path, cache_dir / "deeplabv3_resnet50_coco-cd0a2569.pth")
   ```
2. **More robust, one-line change to `model.py`**: replace the `weights=` enum construction with
   `weights=None` followed by an explicit `model.load_state_dict(torch.load(checkpoint_path))`.
   Does not depend on torchvision's hub-cache filename convention holding across versions, and is
   what approach 3 above already validates cleanly (0 key mismatches).

Either fix is confirmed working end-to-end (construction + a real forward pass producing the
correct output shape) on this exact checkpoint, on a genuine offline Kaggle kernel — not inferred
from reading the source, tested directly.

## What this does not check

This is a construction-time check only — it does not train, and it does not touch
`aux_classifier`/`classifier[4]`'s reshaping to `num_classes` (`model.py`'s own next two lines
after construction), which is a separate, much lower-risk step (plain `torch.nn.Conv2d`
replacement, no network dependency). If J0/J1/J2 still fails after applying one of the two fixes
above, the next thing to check is that reshaping step, not the weight loading this experiment
already cleared.
