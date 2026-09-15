"""Preflight: does the pre-staged COCO checkpoint (SBOM.md, session 33) actually let
`torchvision.models.segmentation.deeplabv3_resnet50` construct under Kaggle's
`enable_internet: false`, the way KHANYA's own `build_model()` calls it?

**Why this matters before J0/J1/J2, not after.** `khanya/main:src/segmentation/model.py`
constructs the model as::

    weights = DeepLabV3_ResNet50_Weights.DEFAULT if pretrained else None
    model = deeplabv3_resnet50(weights=weights, weights_backbone=None, aux_loss=True)

Passing the ``weights`` enum makes torchvision fetch the checkpoint from
``download.pytorch.org`` on first use **unless it is already sitting in torch's own hub cache**
(``~/.cache/torch/hub/checkpoints/``) under the exact filename torchvision expects. Merely
mounting the checkpoint as a Kaggle dataset at some arbitrary path does **not** put it there —
this preflight checks whether that gap is real, and if so, hands back the one-line fix, before
any training kernel discovers it after Sibusiso's S1/S2 data has already landed and a GPU-hour
has already started.

Three approaches are tried, in order, each independent of whether the previous one worked:

1. **Naive** — construct with the ``weights=`` enum, exactly as `model.py` does today, with the
   checkpoint mounted but *not* copied into torch's hub cache. Expected to fail offline; this is
   the risk being checked for, not a bug in this script if it does.
2. **Pre-cached** — copy the mounted file into torch's hub cache under the filename torchvision
   expects, then retry the identical construction call. If this succeeds where (1) failed, that
   copy step is the fix — one line, at the top of any training kernel, before `build_model()`.
3. **Explicit state_dict load** — construct with ``weights=None`` (no enum, no hub-cache lookup
   at all) and load the mounted checkpoint's `state_dict` directly. More robust than either of
   the above and does not depend on torchvision's cache-path convention holding across versions,
   at the cost of one extra line versus KHANYA's current code.

Each approach that constructs successfully also runs one forward pass on a dummy tensor, so
"constructed without raising" and "actually produces an output of the right shape" are checked
separately — a state_dict that loads with mismatched keys can do the first and not the second.

CPU only (`enable_gpu: false`) — this is a correctness check, not a speed one, and a forward pass
through one image is seconds either way.
"""

from __future__ import annotations

import hashlib
import shutil
import time
import traceback
from pathlib import Path


def _find(base: Path, fragment: str) -> Path:
    for candidate in base.rglob("*"):
        if candidate.is_dir() and fragment in str(candidate).replace("\\", "/"):
            return candidate
    raise SystemExit(f"could not find a directory matching {fragment!r} under {base}")


#: The exact sha256 recorded in SBOM.md when the checkpoint was staged (session 33). If this
#: does not match what is mounted here, everything below is moot — the file itself is wrong.
EXPECTED_SHA256 = "cd0a25694c4a0f7106b38f4938bf90a874f2f241cc410b8f63c7024399538f06"

#: The filename torchvision's own hub-cache convention expects for this checkpoint — read from
#: the download URL torchvision uses internally (`deeplabv3_resnet50_coco-cd0a2569.pth`), not
#: guessed.
HUB_CACHE_FILENAME = "deeplabv3_resnet50_coco-cd0a2569.pth"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    import torch
    import torchvision
    from torchvision.models.segmentation import (
        DeepLabV3_ResNet50_Weights,
        deeplabv3_resnet50,
    )

    print(
        f"torch {torch.__version__} / torchvision {torchvision.__version__} / "
        f"cuda available: {torch.cuda.is_available()}"
    )

    kaggle_input = Path("/kaggle/input")
    checkpoint_dir = _find(kaggle_input, "torchvision-deeplabv3-resnet50-coco")
    checkpoint_files = list(checkpoint_dir.rglob("*.pth"))
    if not checkpoint_files:
        raise SystemExit(f"no .pth file found under {checkpoint_dir}")
    mounted_path = checkpoint_files[0]
    print(f"mounted checkpoint: {mounted_path} ({mounted_path.stat().st_size} bytes)")

    actual_sha256 = _sha256(mounted_path)
    sha_ok = actual_sha256 == EXPECTED_SHA256
    print(
        f"sha256 match: {sha_ok} (expected {EXPECTED_SHA256[:16]}..., got {actual_sha256[:16]}...)"
    )
    if not sha_ok:
        print(
            "  ** WARNING: checkpoint does not match the sha recorded in SBOM.md — "
            "everything below is testing the WRONG file. **"
        )

    dummy_input = torch.randn(1, 3, 256, 256)
    results: dict[str, str] = {}

    # --- Approach 1: naive, matching model.py exactly, no cache priming ---
    print("\n[1] naive construction (weights= enum, no hub-cache priming)")
    start = time.time()
    try:
        model = deeplabv3_resnet50(
            weights=DeepLabV3_ResNet50_Weights.DEFAULT, weights_backbone=None, aux_loss=True
        )
        model.eval()
        with torch.no_grad():
            output = model(dummy_input)
        print(f"  SUCCEEDED in {time.time() - start:.1f}s, output shape {output['out'].shape}")
        results["naive"] = "succeeded"
    except Exception as exc:
        print(f"  FAILED after {time.time() - start:.1f}s: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        results["naive"] = f"failed: {type(exc).__name__}"

    # --- Approach 2: pre-cache the mounted file under torchvision's own expected filename ---
    print("\n[2] pre-cached (copy into torch's hub cache first, matching filename)")
    hub_cache_dir = Path.home() / ".cache" / "torch" / "hub" / "checkpoints"
    hub_cache_dir.mkdir(parents=True, exist_ok=True)
    cached_path = hub_cache_dir / HUB_CACHE_FILENAME
    shutil.copy(mounted_path, cached_path)
    print(f"  copied to {cached_path}")
    start = time.time()
    try:
        model = deeplabv3_resnet50(
            weights=DeepLabV3_ResNet50_Weights.DEFAULT, weights_backbone=None, aux_loss=True
        )
        model.eval()
        with torch.no_grad():
            output = model(dummy_input)
        print(f"  SUCCEEDED in {time.time() - start:.1f}s, output shape {output['out'].shape}")
        results["pre_cached"] = "succeeded"
    except Exception as exc:
        print(f"  FAILED after {time.time() - start:.1f}s: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        results["pre_cached"] = f"failed: {type(exc).__name__}"

    # --- Approach 3: explicit state_dict load, no hub cache involved at all ---
    print("\n[3] explicit state_dict load (weights=None, load_state_dict from mounted path)")
    start = time.time()
    try:
        model = deeplabv3_resnet50(weights=None, weights_backbone=None, aux_loss=True)
        state_dict = torch.load(mounted_path, map_location="cpu")
        missing, unexpected = model.load_state_dict(state_dict, strict=False)
        model.eval()
        with torch.no_grad():
            output = model(dummy_input)
        print(
            f"  SUCCEEDED in {time.time() - start:.1f}s, output shape {output['out'].shape}, "
            f"missing keys: {len(missing)}, unexpected keys: {len(unexpected)}"
        )
        if missing or unexpected:
            print(f"    missing: {missing[:5]}{'...' if len(missing) > 5 else ''}")
            print(f"    unexpected: {unexpected[:5]}{'...' if len(unexpected) > 5 else ''}")
        results["explicit_state_dict"] = (
            "succeeded, clean" if not (missing or unexpected) else "succeeded, key mismatch"
        )
    except Exception as exc:
        print(f"  FAILED after {time.time() - start:.1f}s: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        results["explicit_state_dict"] = f"failed: {type(exc).__name__}"

    print("\n=== summary ===")
    print(f"sha256 matches SBOM.md: {sha_ok}")
    for approach, outcome in results.items():
        print(f"  {approach}: {outcome}")

    if results.get("naive") != "succeeded" and (
        results.get("pre_cached") == "succeeded"
        or results.get("explicit_state_dict", "").startswith("succeeded")
    ):
        print(
            "\nRECOMMENDATION: model.py's current construction (the 'naive' approach) does NOT "
            "work unmodified on an offline Kaggle kernel. Use approach 2 (copy the mounted "
            "checkpoint into ~/.cache/torch/hub/checkpoints/ before calling build_model()) or "
            "approach 3 (construct with weights=None and load_state_dict explicitly) in any "
            "J0/J1/J2 kernel."
        )
    elif results.get("naive") == "succeeded":
        print(
            "\nRECOMMENDATION: model.py's current construction worked unmodified — no change "
            "needed for J0/J1/J2 kernels."
        )


if __name__ == "__main__":
    main()
