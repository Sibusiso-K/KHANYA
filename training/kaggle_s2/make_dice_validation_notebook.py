"""Build a private, test-sealed S2 CE+Dice candidate from the current source tree."""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "kaggle_s2_train.ipynb"
TARGET = HERE / "kaggle_s2_dice_validation.ipynb"
BASELINE_METADATA = HERE / "kernel-metadata-baseline.json"
REPO = HERE.parents[1]


def source_snapshot() -> tuple[bytes, dict[str, str]]:
    """Package current Python source with stable ZIP metadata and per-file hashes."""
    files = sorted((REPO / "src").rglob("*.py"))
    required = {
        "src/segmentation/train_patches.py",
        "src/segmentation/patches.py",
        "src/segmentation/lumenstone.py",
    }
    available = {path.relative_to(REPO).as_posix() for path in files}
    if not files or not required.issubset(available):
        raise RuntimeError(f"Source snapshot is incomplete; missing {sorted(required - available)}")
    output = io.BytesIO()
    hashes: dict[str, str] = {}
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
        for path in files:
            relative = path.relative_to(REPO).as_posix()
            content = path.read_bytes()
            hashes[relative] = hashlib.sha256(content).hexdigest()
            info = zipfile.ZipInfo(relative, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, content)
    return output.getvalue(), hashes


def main() -> None:
    notebook = json.loads(SOURCE.read_text(encoding="utf-8"))
    notebook["cells"] = [
        cell for cell in notebook["cells"] if cell.get("id") not in {"evaluation-notes", "evaluate"}
    ]
    by_id = {cell.get("id"): cell for cell in notebook["cells"]}
    source_bytes, source_hashes = source_snapshot()
    source_bundle_sha256 = hashlib.sha256(source_bytes).hexdigest()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-s2-seed42-fullval-v1"
    git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    source_b64 = base64.b64encode(source_bytes).decode("ascii")

    by_id["reefprint-intro"]["source"] = (
        "# REEFPRINT (aka KHANYA) — S2 CE+Dice full-section validation experiment\n\n"
        "Private exploratory Kaggle run. It trains with cross-entropy + soft Dice and selects the "
        "checkpoint using full-resolution predictions on the fixed six-image validation split. It intentionally does not "
        "run evaluation on the 12-image held-out test split. This is one stochastic run, not a "
        "confirmatory comparison or a production claim. Keep notebook and outputs private.\n\n"
        "The publisher archive is fetched at runtime and hash/CRC checked. No Kaggle dataset mirror "
        "is created. Enable GPU and Internet in notebook settings.\n"
    )

    source_cell = "".join(by_id["source-snapshot"]["source"])
    source_cell = re.sub(r"git_sha = '.*'", f"git_sha = '{git_sha}'", source_cell)
    source_cell = re.sub(r"source_bundle_sha256 = '.*'", f"source_bundle_sha256 = '{source_bundle_sha256}'", source_cell)
    source_cell = re.sub(
        r'source_bundle_b64 = """.*?"""',
        'source_bundle_b64 = """' + source_b64 + '"""',
        source_cell,
        flags=re.DOTALL,
    )
    source_cell = re.sub(r"run_id = time\.strftime\(.*\)", f"run_id = '{run_id}'", source_cell)
    source_cell = source_cell.replace(
        "for path in sorted((repo / 'src/segmentation').glob('*.py')):",
        "for path in sorted((repo / 'src').rglob('*.py')):",
    )
    by_id["source-snapshot"]["source"] = source_cell

    gpu_check = "".join(by_id["gpu-check"]["source"])
    gpu_check = gpu_check.replace("os.environ['KHANYA_SUBSET'] = 'S2'", "os.environ['KHANYA_SUBSET'] = 'S2'\nos.environ['KHANYA_SEED'] = '42'\nos.environ['KHANYA_RUN_ID'] = run_id\nos.environ['KHANYA_EPOCHS'] = '8'\nos.environ['KHANYA_PATCHES_PER_EPOCH'] = '64'\nos.environ['KHANYA_VAL_PATCHES'] = '32'")
    by_id["gpu-check"]["source"] = gpu_check

    by_id["train"]["source"] = f'''import subprocess, sys
from pathlib import Path

ckpt_dir = repo / 'checkpoints' / f'lumenstone_s2_patches_{{run_id}}_dice'
if ckpt_dir.exists():
    raise RuntimeError(f'Run checkpoint directory already exists at {{ckpt_dir}}. Generate a fresh run ID.')
log_path = Path('/kaggle/working') / f'khanya-s2-train-{{run_id}}.log'
with log_path.open('w') as log_file:
    result = subprocess.run([sys.executable, '-m', 'src.segmentation.train_patches', '--loss', 'dice'],
                            cwd=repo, env=os.environ.copy(), stdout=log_file, stderr=subprocess.STDOUT, text=True)
print(log_path.read_text(errors='replace')[-12000:])
if result.returncode != 0 or not (ckpt_dir / 'best.pt').is_file():
    raise RuntimeError('Training did not produce best.pt. Preserve the log and fix the stated failure before evaluation.')
if not (ckpt_dir / 'validation_history.json').is_file():
    raise RuntimeError('Missing full-section validation history; do not package this run.')
print('Candidate checkpoint:', ckpt_dir / 'best.pt')
'''

    by_id["training-notes"]["source"] = (
        "## Exploratory CE+Dice training — test split remains sealed\n\n"
        "This run compares a region-overlap loss against the cross-entropy baseline using only "
        "the fixed six-image validation split. Checkpoint selection uses whole-section foreground "
        "macro IoU; balanced-patch metrics are diagnostics only. A single run still needs repeated-seed "
        "follow-up. The candidate is stored "
        "in a separate checkpoint directory. Do not execute a test evaluation from this notebook.\n"
    )

    by_id["bundle-results"]["source"] = '''import hashlib, json, zipfile
from pathlib import Path
from src.segmentation import lumenstone as ls
train_ids, validation_ids, test_ids = ls.split_ids()

checkpoint = ckpt_dir / 'best.pt'
digest = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
training_log = log_path.read_text(errors='replace')
history_path = ckpt_dir / 'validation_history.json'
if not history_path.is_file():
    raise RuntimeError('Missing full-section validation history.')
history = json.loads(history_path.read_text())
best_validation = max(history, key=lambda row: row['validation_full_section_metrics']['foreground_macro_iou'])
manifest = {
    'run_id': '__RUN_ID__',
    'git_commit': git_sha,
    'code_delivery': 'hash-verified source snapshot embedded by notebook generator',
    'source_bundle_sha256': '__SOURCE_BUNDLE_SHA256__',
    'source_file_sha256': json.loads("""__SOURCE_HASHES_JSON__"""),
    'dataset': 'LumenStone S2 v2',
    'dataset_archive_sha256': archive_sha256,
    'dataset_archive_bytes': size,
    'dataset_source': 'https://imaging.cs.msu.ru/en/research/geology/lumenstone',
    'train_pairs': 37,
    'validation_pairs': 6,
    'test_pairs': 12,
    'loss': 'cross-entropy + soft multiclass Dice (default dice_weight=1.0)',
    'selection_metric': 'full-section validation foreground macro IoU',
    'best_validation_foreground_macro_iou': best_validation['validation_full_section_metrics']['foreground_macro_iou'],
    'best_epoch': best_validation['epoch'],
    'validation_note': 'Full-resolution predictions on the fixed six validation sections; patch validation is diagnostic only.',
    'validation_history': history,
    'test_used_for_selection': False,
    'test_evaluation_performed': False,
    'test_metrics': None,
    'subset': 'S2',
    'split_seed': ls.SEED,
    'train_image_ids': train_ids,
    'validation_image_ids': validation_ids,
    'test_image_ids': test_ids,
    'training_budget': {'epochs': 8, 'patches_per_epoch': 64, 'validation_patches': 32, 'patch_px': 512, 'batch_size': 2, 'learning_rate': 0.0002},
    'seed': 42,
    'stochasticity_note': 'One fixed-seed exploratory run; repeat seeds before claiming stable improvement.',
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
    archive.write(checkpoint, f'checkpoints/lumenstone_s2_patches_{run_id}_dice/best.pt')
    archive.write(log_path, 'logs/training.log')
    archive.write(history_path, 'validation_history.json')
    archive.write(manifest_path, 'run_manifest.json')
print('Checkpoint SHA256:', digest)
print('Best full-section validation foreground macro IoU:', manifest['best_validation_foreground_macro_iou'])
print('Held-out test split: SEALED; no test metrics produced.')
print('Private run bundle:', bundle_path, f'({bundle_path.stat().st_size/2**20:.1f} MiB)')
'''.replace('__RUN_ID__', run_id).replace(
        '__SOURCE_BUNDLE_SHA256__', source_bundle_sha256
    ).replace('__SOURCE_HASHES_JSON__', json.dumps(source_hashes))

    metadata = {
        # Update the existing private notebook so each version stays on the
        # same Kaggle record; the candidate remains private and test-sealed.
        "id": "lethabomh14/reefprint-s2-ce-dice-validation-only-experiment",
        "title": "REEFPRINT S2 CE+Dice whole-section validation-selection experiment",
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
