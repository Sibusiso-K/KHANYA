"""Build one private, hash-bound evaluation of the preselected native model.

This builder reads audited small artifacts; it never opens dataset pixels or
checkpoint weights, trains a model, or contacts Kaggle.
"""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
AUDIT = ROOT / "training/audit_extended_20261001"
SOURCE_NOTEBOOK = AUDIT / "extended-dice/source/reefprint-s2-extended-dice.ipynb"
MANIFEST = AUDIT / "extended-dice/results/khanya-s2-dice-manifest-20260930-s2-seed42-extended-dice-v1.json"
RUN_ID = "20260930-s2-seed42-extended-dice-v1"
EVAL_ID = "native-selected-test-20261001-v1"
KERNEL = "lethabomh14/reefprint-native-selected-test-20261001"


def digest(value):
    return hashlib.sha256(value).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


m = json.loads(MANIFEST.read_text(encoding="utf-8"))
n = json.loads(SOURCE_NOTEBOOK.read_text(encoding="utf-8"))
code = "\n".join("".join(c["source"]) for c in n["cells"] if c["cell_type"] == "code")
encoded = re.search(r'source_bundle_b64 = """(.*?)"""', code, re.S).group(1)
bundle = base64.b64decode(encoded, validate=True)
assert digest(bundle) == m["source_bundle_sha256"] == "4cffd60c88fea1a7553f8f154040cf2ce93f7312f0571f3dc6784b5938988528"
with zipfile.ZipFile(io.BytesIO(bundle)) as z:
    assert z.testzip() is None
    source_hashes = {name: digest(z.read(name)) for name in z.namelist() if name.startswith("src/") and name.endswith(".py")}
assert source_hashes == m["source_file_sha256"] and len(source_hashes) == 35
best = max(m["validation_history"], key=lambda row: row["validation_full_section_metrics"]["foreground_macro_iou"])
assert best["epoch"] == m["best_epoch"] == 12
assert m["best_validation_foreground_macro_iou"] == best["validation_full_section_metrics"]["foreground_macro_iou"]
assert m["checkpoint_sha256"] == "42646cfafbeac5398386dba17f7ad3531ffcea572e6342cc4fcba42ed0b44b3b"
assert m["test_used_for_selection"] is False and m["test_evaluation_performed"] is False
assert m["test_image_ids"] == [f"test_{i:02d}" for i in range(1, 13)]
id_sets = [set(m[k]) for k in ("train_image_ids", "validation_image_ids", "test_image_ids")]
assert list(map(len, id_sets)) == [31, 6, 12]
assert not any(id_sets[i] & id_sets[j] for i in range(3) for j in range(i + 1, 3))

protocol = {
    "evaluation_id": EVAL_ID,
    "evaluation_kernel": KERNEL,
    "candidate_kernel_source": "lethabomh14/reefprint-s2-extended-dice/1",
    "candidate_run_id": RUN_ID,
    "candidate_epoch": 12,
    "checkpoint_sha256": m["checkpoint_sha256"],
    "checkpoint_relative_path": f"khanya-{RUN_ID}/checkpoints/lumenstone_s2_patches_{RUN_ID}_dice/best.pt",
    "checkpoint_sha256_and_bytes_verification_required_before_inference": True,
    "candidate_manifest_sha256": digest(MANIFEST.read_bytes()),
    "source_notebook_sha256": digest(SOURCE_NOTEBOOK.read_bytes()),
    "source_bundle_sha256": m["source_bundle_sha256"],
    "source_file_sha256": source_hashes,
    "source_commit": m["git_commit"],
    "dataset": "LumenStone S2 v2",
    "publisher_page": "https://imaging.cs.msu.ru/en/research/geology/lumenstone",
    "publisher_download": "https://disk.360.yandex.ru/d/wYK_5JyQy0pIcg",
    "dataset_archive_sha256": m["dataset_archive_sha256"],
    "dataset_archive_bytes": m["dataset_archive_bytes"],
    "selection_rule": "Highest foreground macro IoU on the fixed six whole native-resolution validation sections; chosen before this evaluation.",
    "selected_validation_foreground_macro_iou": m["best_validation_foreground_macro_iou"],
    "train_image_ids": m["train_image_ids"],
    "validation_image_ids": m["validation_image_ids"],
    "test_image_ids": m["test_image_ids"],
    "class_codes": [0, 1, 3, 5, 7],
    "class_names": ["background", "chalcopyrite", "magnetite", "pyrrhotite", "pentlandite"],
    "model": "torchvision DeepLabV3 ResNet50, auxiliary head enabled, strict state_dict load, pretrained=False, weights_only=True",
    "mode": "eval(), torch.inference_mode(), native whole-section sliding window",
    "image_preprocessing": "PIL RGB; native 512x512 tiles; no resizing, sharpening, super-resolution, test-time augmentation, threshold fitting or calibration; tensor /255 with ImageNet mean [0.485,0.456,0.406], std [0.229,0.224,0.225].",
    "tile_overlap_pixels": 64,
    "tile_combination": "Average overlapping raw logits then argmax of softmax, exact source patches.sliding_window_predict.",
    "mask_preprocessing": "Original PNG codes, first channel if replicated RGB; exact source patches.labels_for and lumenstone._LOOKUP map to dense 0..4.",
    "metric_protocol": "All pixels, no void-border exclusion; pooled whole-section confusion (rows truth, columns prediction); source metrics.summarise. Five-class mIoU includes background; foreground macro IoU is mean of four mineral IoUs. Undefined denominators become null and are excluded from the relevant macro mean, with evaluated-class counts reported.",
    "per_section": "Each of the fixed twelve test images; an image is not a verified independent specimen/locality.",
    "historical_test_caveat": "Publisher held-out sections have earlier baseline results. This is a fixed final regression set, not fresh blind prospective data; this candidate has no prior test evaluation. Do not tune checkpoint, preprocessing, thresholds, or model selection from these results.",
    "training_performed": False,
    "test_used_for_selection": False,
    "automatic_deployment": False,
    "launches_authorized": 1,
    "resources": "Private free Kaggle Tesla T4; no paid resources. Free quota read 2026-10-01: 25.38 GPU hours remaining.",
    "expected_runtime": {"torch": "2.10.0+cu128", "torchvision": "0.25.0+cu128"},
    "exported_outputs": ["protocol.json", "native_selected_test_metrics.json", "evaluation_report.md", "test_confusion.csv", "test_per_class.csv", "test_per_section.csv"],
    "rights": "Private research evaluation; publish neither raw dataset nor derived checkpoint. This run exports only small reports and provenance.",
}
protocol_text = json.dumps(protocol, indent=2, ensure_ascii=False) + "\n"
protocol_sha = digest(protocol_text.encode("utf-8"))
(HERE / "protocol.json").write_text(protocol_text, encoding="utf-8", newline="\n")

preflight = '''from pathlib import Path, PurePosixPath
from urllib.parse import quote
from urllib.request import urlopen
from zipfile import ZipFile
import base64, csv, hashlib, io, json, math, os, random, sys, tempfile, time, zipfile
import numpy as np
import torch, torchvision
from PIL import Image

protocol = json.loads(PROTOCOL_LITERAL)
protocol_text = json.dumps(protocol, indent=2, ensure_ascii=False) + '\\n'
protocol_sha256 = hashlib.sha256(protocol_text.encode('utf-8')).hexdigest()
assert protocol_sha256 == EXPECTED_PROTOCOL_SHA
outdir = Path('/kaggle/working')
assert outdir.is_dir()
runtime = Path(tempfile.mkdtemp(prefix='reefprint-native-test-'))
repo = runtime / 'verified-source'
repo.mkdir()
print('Evaluation:', protocol['evaluation_id'], '| private, evaluation only')
print('Protocol SHA256:', protocol_sha256)
print('Historical-test caveat:', protocol['historical_test_caveat'])
assert torch.__version__ == protocol['expected_runtime']['torch'], 'Runtime differs; stop before test inference.'
assert torchvision.__version__ == protocol['expected_runtime']['torchvision'], 'Torchvision differs; stop before test inference.'
assert torch.cuda.is_available(), 'Free GPU is unavailable; stop without training or paid fallback.'
dev = torch.device('cuda')
print('Torch:', torch.__version__, '| torchvision:', torchvision.__version__, '| GPU:', torch.cuda.get_device_name(0))

def sha_file(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

input_root = Path('/kaggle/input')
checkpoint_parent = 'lumenstone_s2_patches_' + protocol['candidate_run_id'] + '_dice'
checkpoints = [p for p in input_root.rglob('best.pt') if p.parent.name == checkpoint_parent]
assert len(checkpoints) == 1, f'Expected exactly one attached native checkpoint, found {len(checkpoints)}.'
checkpoint = checkpoints[0]
checkpoint_sha256 = sha_file(checkpoint)
assert checkpoint_sha256 == protocol['checkpoint_sha256'], 'Checkpoint bytes differ; stop before opening test images.'
checkpoint_bytes = checkpoint.stat().st_size
assert checkpoint_bytes > 0
manifests = list(input_root.rglob('khanya-s2-dice-manifest-' + protocol['candidate_run_id'] + '.json'))
assert len(manifests) == 1, 'Exactly one attached candidate training manifest is required.'
assert sha_file(manifests[0]) == protocol['candidate_manifest_sha256'], 'Candidate manifest version differs.'
candidate_manifest = json.loads(manifests[0].read_text())
assert candidate_manifest['checkpoint_sha256'] == checkpoint_sha256
assert candidate_manifest['source_file_sha256'] == protocol['source_file_sha256']
assert candidate_manifest['test_evaluation_performed'] is False
assert candidate_manifest['test_used_for_selection'] is False
assert candidate_manifest['best_epoch'] == protocol['candidate_epoch'] == 12
selected = max(candidate_manifest['validation_history'], key=lambda row: row['validation_full_section_metrics']['foreground_macro_iou'])
assert selected['epoch'] == 12
assert selected['validation_full_section_metrics']['foreground_macro_iou'] == protocol['selected_validation_foreground_macro_iou']
print('Checkpoint SHA256 verified:', checkpoint_sha256, '| bytes:', checkpoint_bytes)

source_bundle_b64 = """SOURCE_BUNDLE_LITERAL"""
bundle = base64.b64decode(source_bundle_b64, validate=True)
assert hashlib.sha256(bundle).hexdigest() == protocol['source_bundle_sha256']

def safe_extract(archive, destination):
    assert archive.testzip() is None, 'ZIP CRC check failed.'
    for member in archive.infolist():
        path = PurePosixPath(member.filename)
        assert not path.is_absolute() and '..' not in path.parts and '\\\\' not in member.filename, 'Unsafe ZIP path.'
        assert (member.external_attr >> 16) & 0o170000 != 0o120000, 'ZIP symlink is forbidden.'
        assert (destination / member.filename).resolve().is_relative_to(destination.resolve())
    archive.extractall(destination)

with ZipFile(io.BytesIO(bundle)) as source_zip:
    safe_extract(source_zip, repo)
source_hashes = {str(p.relative_to(repo)).replace('\\\\', '/'): sha_file(p) for p in sorted((repo / 'src').rglob('*.py'))}
assert source_hashes == protocol['source_file_sha256'] and len(source_hashes) == 35
print('All 35 source module hashes verified; no source changes.')
'''
preflight = preflight.replace("PROTOCOL_LITERAL", repr(json.dumps(protocol)))
preflight = preflight.replace("EXPECTED_PROTOCOL_SHA", repr(protocol_sha))
preflight = preflight.replace("SOURCE_BUNDLE_LITERAL", encoded)

dataset = '''# Reuse the publisher ZIP already attached with training output when present.
# Otherwise download its exact original bytes inside Kaggle, never on this host.
archives = list(input_root.rglob('S2_v2.zip'))
assert len(archives) <= 1, 'Ambiguous original publisher archive inputs.'
if archives:
    archive = archives[0]
    dataset_delivery = 'unchanged publisher archive attached with candidate kernel output'
else:
    archive = runtime / 'S2_v2.zip'
    api = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key=' + quote(protocol['publisher_download'], safe='')
    with urlopen(api, timeout=60) as response:
        download_url = json.load(response)['href']
    with urlopen(download_url, timeout=180) as source, archive.open('wb') as target:
        while True:
            chunk = source.read(8 * 1024 * 1024)
            if not chunk:
                break
            target.write(chunk)
    dataset_delivery = 'original publisher public-resource download'
dataset_sha256 = sha_file(archive)
assert dataset_sha256 == protocol['dataset_archive_sha256'], 'Dataset SHA mismatch; stop before test inference.'
assert archive.stat().st_size == protocol['dataset_archive_bytes'] == 418742024
extract_base = runtime / 'dataset'
extract_base.mkdir()
with ZipFile(archive) as data_zip:
    safe_extract(data_zip, extract_base)
roots = []
for train_dir in extract_base.rglob('imgs/train'):
    candidate = train_dir.parent.parent
    if all((candidate / p).is_dir() for p in ('imgs/test', 'masks/train', 'masks/test')):
        train_imgs = {p.stem for p in (candidate / 'imgs/train').glob('*.jpg')}
        test_imgs = {p.stem for p in (candidate / 'imgs/test').glob('*.jpg')}
        train_masks = {p.stem for p in (candidate / 'masks/train').glob('*.png')}
        test_masks = {p.stem for p in (candidate / 'masks/test').glob('*.png')}
        if len(train_imgs) == 37 and len(test_imgs) == 12 and train_imgs == train_masks and test_imgs == test_masks:
            roots.append(candidate)
assert len(roots) == 1, 'Exactly one original S2 v2 root with 37/12 paired files is required.'
s2_root = roots[0].resolve()
data_link = repo / 'data/raw/lumenstone/S2_v2'
data_link.parent.mkdir(parents=True)
data_link.symlink_to(s2_root, target_is_directory=True)
print('Original publisher archive verified:', dataset_sha256, '| bytes:', archive.stat().st_size)
'''

setup = '''os.environ['KHANYA_SUBSET'] = 'S2'
os.environ['KHANYA_SEED'] = '42'
os.environ['KHANYA_RUN_ID'] = protocol['candidate_run_id']
sys.path.insert(0, str(repo))
from src.segmentation import lumenstone as ls, metrics, patches
from src.segmentation.model import build_model
assert ls.CLASS_NAMES == protocol['class_names']
assert ls.CLASS_CODES == protocol['class_codes'] and ls.NUM_CLASSES == 5
assert patches.PATCH == 512
train_ids, validation_ids, test_ids = ls.split_ids()
assert train_ids == protocol['train_image_ids'] == candidate_manifest['train_image_ids']
assert validation_ids == protocol['validation_image_ids'] == candidate_manifest['validation_image_ids']
assert test_ids == protocol['test_image_ids'] == candidate_manifest['test_image_ids']
assert [len(train_ids), len(validation_ids), len(test_ids)] == [31, 6, 12]
assert not (set(train_ids) & set(validation_ids) or set(train_ids) & set(test_ids) or set(validation_ids) & set(test_ids))
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)
torch.cuda.manual_seed_all(42)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False
model = build_model(num_classes=ls.NUM_CLASSES, pretrained=False).to(dev)
state = torch.load(checkpoint, map_location=dev, weights_only=True)
assert isinstance(state, dict) and state and all(isinstance(k, str) and isinstance(v, torch.Tensor) for k, v in state.items()), 'Expected tensor-only state_dict.'
model.load_state_dict(state, strict=True)
del state
model.eval()
assert not model.training
print('Frozen checkpoint loaded safely; fixed split and class map verified.')
'''

evaluate = '''# One inference sweep over the predeclared 12 whole test sections.
# Source inference, label mapping and metric functions remain byte-identical.
started_at_utc = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
start = time.perf_counter()
confusion = metrics.new_confusion(ls.NUM_CLASSES)
per_section = {}
test_file_sha256 = {}

def enrich(matrix):
    result = metrics.summarise(matrix)
    foreground_ious = [v for v in result['iou_per_class'][1:] if math.isfinite(v)]
    result['foreground_macro_iou'] = sum(foreground_ious) / len(foreground_ious) if foreground_ious else float('nan')
    result['evaluated_class_count'] = sum(math.isfinite(v) for v in result['iou_per_class'])
    result['evaluated_foreground_class_count'] = len(foreground_ious)
    result['confusion_matrix'] = [[int(v) for v in row] for row in matrix.tolist()]
    result['ground_truth_pixels_per_class'] = [int(v) for v in matrix.sum(1).tolist()]
    result['predicted_pixels_per_class'] = [int(v) for v in matrix.sum(0).tolist()]
    return result

with torch.inference_mode():
    for stem in test_ids:
        section_start = time.perf_counter()
        image_path = ls.DATA_DIR / 'imgs/test' / (stem + '.jpg')
        mask_path = ls.DATA_DIR / 'masks/test' / (stem + '.png')
        test_file_sha256[stem] = {'image_sha256': sha_file(image_path), 'mask_sha256': sha_file(mask_path)}
        with Image.open(image_path) as source_image:
            image = source_image.convert('RGB')
        predicted, _ = patches.sliding_window_predict(model, image, dev, patch=512, overlap=64)
        truth = patches.labels_for(stem, 'test')
        assert predicted.shape == truth.shape == (image.height, image.width)
        assert np.all((truth >= 0) & (truth < 5)), 'Unexpected mask codes.'
        assert np.all((predicted >= 0) & (predicted < 5)), 'Unexpected predicted labels.'
        pred_t, truth_t = torch.from_numpy(predicted), torch.from_numpy(truth)
        section_confusion = metrics.new_confusion(ls.NUM_CLASSES)
        metrics.confusion_from_batch(pred_t, truth_t, ls.NUM_CLASSES, section_confusion)
        assert int(section_confusion.sum()) == image.width * image.height
        confusion += section_confusion
        section = enrich(section_confusion)
        section['image_width'] = image.width
        section['image_height'] = image.height
        section['elapsed_seconds'] = time.perf_counter() - section_start
        per_section[stem] = section
        print(stem, 'complete | mIoU', round(section['mean_iou'], 6), '| foreground IoU', round(section['foreground_macro_iou'], 6), '| seconds', round(section['elapsed_seconds'], 1), flush=True)
        del image, predicted, truth, pred_t, truth_t, section_confusion
assert list(per_section) == protocol['test_image_ids'] and len(per_section) == 12
assert np.array_equal(np.array([s['confusion_matrix'] for s in per_section.values()]).sum(axis=0), np.array(confusion.tolist()))
assert sha_file(checkpoint) == checkpoint_sha256, 'Checkpoint changed during evaluation.'
summary = enrich(confusion)
summary.update({
    'evaluation_id': protocol['evaluation_id'], 'candidate_run_id': protocol['candidate_run_id'],
    'candidate_epoch': protocol['candidate_epoch'], 'class_names': ls.CLASS_NAMES, 'class_codes': ls.CLASS_CODES,
    'n_test_sections': 12, 'test_image_ids': test_ids, 'per_section': per_section,
    'test_file_sha256': test_file_sha256, 'checkpoint_sha256': checkpoint_sha256, 'checkpoint_bytes': checkpoint_bytes,
    'source_bundle_sha256': protocol['source_bundle_sha256'], 'source_file_sha256': source_hashes,
    'candidate_manifest_sha256': protocol['candidate_manifest_sha256'], 'protocol_sha256': protocol_sha256,
    'dataset_archive_sha256': dataset_sha256, 'dataset_archive_bytes': archive.stat().st_size, 'dataset_delivery': dataset_delivery,
    'method': 'sliding window, 512px patches, 64px overlap, native whole sections, average raw logits, no downsampling, all pixels, no void-border exclusion',
    'confusion_orientation': 'rows: ground truth, columns: prediction',
    'selection_rule': protocol['selection_rule'], 'selected_validation_foreground_macro_iou': protocol['selected_validation_foreground_macro_iou'],
    'historical_test_caveat': protocol['historical_test_caveat'],
    'per_section_note': protocol['per_section'], 'training_performed': False, 'test_used_for_selection': False,
    'automatic_deployment': False, 'started_at_utc': started_at_utc,
    'finished_at_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'elapsed_seconds': time.perf_counter() - start,
    'runtime': {'python': sys.version, 'torch': torch.__version__, 'torchvision': torchvision.__version__, 'cuda': torch.version.cuda, 'gpu': torch.cuda.get_device_name(0)},
})
summary = metrics.json_safe(summary)
(outdir / 'native_selected_test_metrics.json').write_text(json.dumps(summary, indent=2, allow_nan=False) + '\\n')
(outdir / 'protocol.json').write_text(protocol_text)
print('Measured test mIoU:', summary['mean_iou'], '| foreground IoU:', summary['foreground_macro_iou'], '| pixel accuracy:', summary['pixel_accuracy'])
'''

report = '''def rate(value):
    return 'undefined' if value is None else f'{value:.6f}'

lines = [
    '# Native candidate: fixed test regression evaluation', '',
    f"Completed {summary['finished_at_utc']}; evaluation `{summary['evaluation_id']}`.", '',
    f"Preselected checkpoint: `{protocol['candidate_kernel_source']}`, epoch 12, selected solely by six-section native validation foreground IoU {protocol['selected_validation_foreground_macro_iou']:.6f}.", '',
    f"Measured **five-class mIoU {rate(summary['mean_iou'])}**, **foreground macro IoU {rate(summary['foreground_macro_iou'])}**, **pixel accuracy {rate(summary['pixel_accuracy'])}** on all pixels of the fixed twelve whole sections.", '',
    protocol['historical_test_caveat'], '',
    '| Class | IoU | Recall | Precision | TP | FP | FN | Ground truth pixels |',
    '|---|---:|---:|---:|---:|---:|---:|---:|',
]
for i, name in enumerate(ls.CLASS_NAMES):
    lines.append(f"| {name} | {rate(summary['iou_per_class'][i])} | {rate(summary['recall_per_class'][i])} | {rate(summary['precision_per_class'][i])} | {summary['tp_per_class'][i]} | {summary['fp_per_class'][i]} | {summary['fn_per_class'][i]} | {summary['ground_truth_pixels_per_class'][i]} |")
lines += ['', 'Confusion matrix: rows are ground truth, columns are prediction.', '', '| Truth / Prediction | ' + ' | '.join(ls.CLASS_NAMES) + ' |', '|---|' + '---:|' * 5]
for name, row in zip(ls.CLASS_NAMES, summary['confusion_matrix']):
    lines.append('| ' + name + ' | ' + ' | '.join(map(str, row)) + ' |')
lines += ['', '| Section | Five-class mIoU | Foreground IoU | Pixel accuracy |', '|---|---:|---:|---:|']
for stem, section in summary['per_section'].items():
    lines.append(f"| {stem} | {rate(section['mean_iou'])} | {rate(section['foreground_macro_iou'])} | {rate(section['pixel_accuracy'])} |")
lines += ['', 'Each section’s full per-class IoU, recall, precision, TP/FP/FN and confusion matrix is in `native_selected_test_metrics.json` and the accompanying CSV files.', '',
    'Protocol: original RGB at native resolution; 512px tiles, 64px overlap; average overlapping logits; fixed argmax; ImageNet normalization; no downsampling or test-time augmentation; no void-border exclusion. Pooled metrics are computed from total pixel counts, not averages over images. Five-class mIoU includes background. Undefined classes have null rates and are excluded from macro means; evaluated-class counts are in the JSON.', '',
    'Per-section results are not verified independent localities/specimens. This single seed result cannot establish prospective accuracy or a stable improvement. No training, threshold fitting, candidate replacement or deployment occurs in this evaluation.', '',
    'Provenance:', '',
    f"- Checkpoint SHA256: `{checkpoint_sha256}`; `{checkpoint_bytes}` bytes, independently hashed before and after inference.",
    f"- Source bundle SHA256: `{protocol['source_bundle_sha256']}`; all 35 module hashes unchanged and verified.",
    f"- Training manifest SHA256: `{protocol['candidate_manifest_sha256']}`.",
    f"- Original publisher archive SHA256: `{dataset_sha256}`; `{archive.stat().st_size}` bytes.",
    f"- Protocol SHA256: `{protocol_sha256}`; source commit `{protocol['source_commit']}`.",
    f"- Runtime: Torch `{torch.__version__}`, torchvision `{torchvision.__version__}`, GPU `{torch.cuda.get_device_name(0)}`.",
    '', 'Deployment remains a separate explicit approval decision after review of common-phase regressions and rare-phase behavior. Do not tune on this test outcome.', '',
]
(outdir / 'evaluation_report.md').write_text('\\n'.join(lines))
with (outdir / 'test_confusion.csv').open('w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['truth / prediction'] + ls.CLASS_NAMES)
    for name, row in zip(ls.CLASS_NAMES, summary['confusion_matrix']):
        writer.writerow([name] + row)
with (outdir / 'test_per_class.csv').open('w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['class', 'iou', 'recall', 'precision', 'tp', 'fp', 'fn', 'ground_truth_pixels', 'predicted_pixels'])
    for i, name in enumerate(ls.CLASS_NAMES):
        writer.writerow([name] + [summary[k][i] for k in ('iou_per_class', 'recall_per_class', 'precision_per_class', 'tp_per_class', 'fp_per_class', 'fn_per_class', 'ground_truth_pixels_per_class', 'predicted_pixels_per_class')])
with (outdir / 'test_per_section.csv').open('w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['section', 'class', 'iou', 'recall', 'precision', 'tp', 'fp', 'fn', 'five_class_miou', 'foreground_macro_iou', 'pixel_accuracy'])
    for stem, section in summary['per_section'].items():
        for i, name in enumerate(ls.CLASS_NAMES):
            writer.writerow([stem, name] + [section[k][i] for k in ('iou_per_class', 'recall_per_class', 'precision_per_class', 'tp_per_class', 'fp_per_class', 'fn_per_class')] + [section['mean_iou'], section['foreground_macro_iou'], section['pixel_accuracy']])
assert all((outdir / name).is_file() for name in protocol['exported_outputs'])
assert not any(p.suffix.lower() in ('.pt', '.zip', '.jpg', '.png', '.npz') for p in outdir.rglob('*') if p.is_file()), 'Raw data or weights must not be exported.'
print('Small private evaluation reports exported:', ', '.join(protocol['exported_outputs']))
'''

def code_cell(source):
    ast.parse(source)
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source.splitlines(keepends=True)}


notebook = {
    "cells": [{"cell_type": "markdown", "metadata": {}, "source": ["# Native selected candidate: one fixed test evaluation\n", "Private evaluation only. Epoch 12 selected before test inference solely by the fixed six-section native validation foreground IoU. Original code, class map and preprocessing are hash-bound. Reports do not imply deployment, a fresh blind test, or a stable gain.\n"]}] + [code_cell(s) for s in (preflight, dataset, setup, evaluate, report)],
    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.12"}},
    "nbformat": 4,
    "nbformat_minor": 5,
}
write_json(HERE / "evaluation.ipynb", notebook)
metadata = {
    "id": KERNEL, "title": "REEFPRINT native selected test 20261001", "code_file": "evaluation.ipynb",
    "language": "python", "kernel_type": "notebook", "is_private": True,
    "enable_gpu": True, "enable_tpu": False, "enable_internet": True,
    "machine_shape": "NvidiaTeslaT4",
    "docker_image": "gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461",
    "docker_image_pinning_type": "original",
    "dataset_sources": [], "competition_sources": [],
    "kernel_sources": [protocol["candidate_kernel_source"]], "model_sources": [],
}
write_json(HERE / "kernel-metadata.json", metadata)
tree = ast.parse("\n".join((preflight, dataset, setup, evaluate, report)))
calls = [x for x in ast.walk(tree) if isinstance(x, ast.Call)]
assert not any(isinstance(x.func, ast.Attribute) and x.func.attr in ("train", "backward", "step", "fit") for x in calls)
assert not any(isinstance(x.func, ast.Name) and x.func.id in ("train", "run_epoch", "build_loaders") for x in calls)
loads = [x for x in calls if isinstance(x.func, ast.Attribute) and x.func.attr == "load" and isinstance(x.func.value, ast.Name) and x.func.value.id == "torch"]
assert len(loads) == 1 and any(x.arg == "weights_only" and isinstance(x.value, ast.Constant) and x.value.value is True for x in loads[0].keywords)
assert len([x for x in calls if isinstance(x.func, ast.Attribute) and x.func.attr == "sliding_window_predict"]) == 1
print(json.dumps({"folder": str(HERE), "kernel": KERNEL, "notebook_sha256": digest((HERE / "evaluation.ipynb").read_bytes()), "protocol_sha256": protocol_sha, "source_modules_verified": len(source_hashes), "test_ids": protocol["test_image_ids"], "code_cells_compiled": 5, "training_calls": 0, "torch_load_weights_only": True}, indent=2))
