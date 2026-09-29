"""Build a test-sealed Kaggle notebook for the S2 CE+Dice experiment."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "kaggle_s2_train.ipynb"
TARGET = HERE / "kaggle_s2_dice_validation.ipynb"
BASELINE_METADATA = HERE / "kernel-metadata-baseline.json"


def main() -> None:
    notebook = json.loads(SOURCE.read_text(encoding="utf-8"))
    notebook["cells"] = [
        cell for cell in notebook["cells"] if cell.get("id") not in {"evaluation-notes", "evaluate"}
    ]
    by_id = {cell.get("id"): cell for cell in notebook["cells"]}

    by_id["reefprint-intro"]["source"] = (
        "# REEFPRINT (aka KHANYA) — S2 CE+Dice validation experiment\n\n"
        "Private exploratory Kaggle run. It trains with cross-entropy + soft Dice and selects the "
        "checkpoint only using the fixed six-image validation split. It intentionally does not "
        "run evaluation on the 12-image held-out test split. This is one stochastic run, not a "
        "confirmatory comparison or a production claim. Keep notebook and outputs private.\n\n"
        "The publisher archive is fetched at runtime and hash/CRC checked. No Kaggle dataset mirror "
        "is created. Enable GPU and Internet in notebook settings.\n"
    )

    train = by_id["train"]
    train["source"] = train["source"].replace(
        "checkpoints/lumenstone_s2_patches'", "checkpoints/lumenstone_s2_patches_dice'"
    ).replace(
        "[sys.executable, '-m', 'src.segmentation.train_patches']",
        "[sys.executable, '-m', 'src.segmentation.train_patches', '--loss', 'dice']",
    )

    by_id["training-notes"]["source"] = (
        "## Exploratory CE+Dice training — test split remains sealed\n\n"
        "This run compares a region-overlap loss against the cross-entropy baseline using only "
        "the deterministic six-image validation split. The validation patches are balanced and "
        "are not representative whole-section accuracy. A single run has random training patch "
        "sampling, so an apparent gain needs a repeated-seed follow-up. The candidate is stored "
        "in a separate checkpoint directory. Do not execute a test evaluation from this notebook.\n"
    )

    by_id["bundle-results"]["source"] = '''import hashlib, json, zipfile
from pathlib import Path
from src.segmentation import lumenstone as ls
train_ids, validation_ids, test_ids = ls.split_ids()

checkpoint = ckpt_dir / 'best.pt'
digest = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
training_log = log_path.read_text(errors='replace')
best_line = [line for line in training_log.splitlines() if 'best val patch mean IoU:' in line]
if not best_line:
    raise RuntimeError('Could not find the validation-only checkpoint selection metric in the training log.')
best_validation_patch_miou = float(best_line[-1].rsplit(':', 1)[1].strip())
manifest = {
    'run_id': run_id,
    'git_commit': git_sha,
    'code_delivery': 'hash-verified embedded training-module snapshot',
    'source_bundle_sha256': source_bundle_sha256,
    'source_file_sha256': source_hashes,
    'dataset': 'LumenStone S2 v2',
    'dataset_archive_sha256': archive_sha256,
    'dataset_archive_bytes': size,
    'dataset_source': 'https://imaging.cs.msu.ru/en/research/geology/lumenstone',
    'train_pairs': 37,
    'validation_pairs': 6,
    'test_pairs': 12,
    'loss': 'cross-entropy + soft multiclass Dice (default dice_weight=1.0)',
    'selection_metric': 'best validation balanced-patch mean IoU',
    'best_validation_patch_mean_iou': best_validation_patch_miou,
    'validation_note': '32 deterministic balanced 512px validation patches per epoch; patch metric is not whole-section accuracy.',
    'test_used_for_selection': False,
    'test_evaluation_performed': False,
    'test_metrics': None,
    'subset': 'S2',
    'split_seed': ls.SEED,
    'train_image_ids': train_ids,
    'validation_image_ids': validation_ids,
    'test_image_ids': test_ids,
    'training_budget': {'epochs': 8, 'patches_per_epoch': 64, 'validation_patches': 32, 'patch_px': 512, 'batch_size': 2, 'learning_rate': 0.0002},
    'stochasticity_note': 'Python random patch sampling uses a non-fixed seed for training patches; one run is exploratory and not a controlled repeated-seed comparison.',
    'torch': torch.__version__,
    'torchvision': torchvision.__version__,
    'cuda': torch.version.cuda,
    'gpu': torch.cuda.get_device_name(0),
    'checkpoint_sha256': digest,
    'rights_note': 'Private research run. Do not publish dataset or derived checkpoint without rights review.'
}
manifest_path = Path('/kaggle/working') / f'khanya-s2-dice-manifest-{run_id}.json'
manifest_path.write_text(json.dumps(manifest, indent=2))
bundle_path = Path('/kaggle/working') / f'khanya-s2-dice-validation-{run_id}.zip'
with zipfile.ZipFile(bundle_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=3) as archive:
    archive.write(checkpoint, 'checkpoints/lumenstone_s2_patches_dice/best.pt')
    archive.write(log_path, 'logs/training.log')
    archive.write(manifest_path, 'run_manifest.json')
print('Checkpoint SHA256:', digest)
print('Best validation balanced-patch mIoU:', best_validation_patch_miou)
print('Held-out test split: SEALED; no test metrics produced.')
print('Private run bundle:', bundle_path, f'({bundle_path.stat().st_size/2**20:.1f} MiB)')
'''

    metadata = {
        "id": "lethabomh14/reefprint-s2-dice-validation",
        "title": "REEFPRINT S2 CE+Dice validation-only experiment",
        "code_file": TARGET.name,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": "true",
        "enable_gpu": "true",
        "enable_tpu": "false",
        "enable_internet": "true",
        "machine_shape": "",
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
        "model_sources": [],
    }
    # Preserve the original private baseline definition before the first
    # validation experiment is generated; the Kaggle CLI reads only the
    # generic metadata filename, which is deliberately not committed.
    if not BASELINE_METADATA.exists():
        metadata_path = HERE / "kernel-metadata.json"
        if metadata_path.exists():
            BASELINE_METADATA.write_text(metadata_path.read_text(encoding="utf-8"), encoding="utf-8")
    (HERE / "kernel-metadata-dice-validation.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    TARGET.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {TARGET}")


if __name__ == "__main__":
    main()
