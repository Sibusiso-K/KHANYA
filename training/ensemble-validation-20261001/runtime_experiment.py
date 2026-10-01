"""Private training and fixed validation-only ensemble experiment runtime.

This script is embedded by build_experiments.py; it has no Kaggle credentials,
test inference, automatic promotion, or application changes.
"""
from pathlib import Path, PurePosixPath
from urllib.parse import quote
from urllib.request import urlopen
import hashlib
import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys
import time
from zipfile import ZipFile

import numpy as np
from PIL import Image
import torch
import torchvision
from torchvision.transforms import functional as TF


def sha_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def save_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def safe_extract(archive, destination):
    assert archive.testzip() is None, 'ZIP CRC mismatch.'
    for member in archive.infolist():
        path = PurePosixPath(member.filename)
        assert not path.is_absolute() and '..' not in path.parts and '\\' not in member.filename
        assert (member.external_attr >> 16) & 0o170000 != 0o120000, 'Symlink in ZIP.'
        assert (destination / member.filename).resolve().is_relative_to(destination.resolve())
    archive.extractall(destination)


def enrich(matrix, metric_module):
    summary = metric_module.summarise(matrix)
    foreground = [value for value in summary['iou_per_class'][1:] if math.isfinite(value)]
    summary['foreground_macro_iou'] = sum(foreground) / len(foreground)
    summary['confusion_matrix'] = [[int(v) for v in row] for row in matrix.tolist()]
    summary['ground_truth_pixels_per_class'] = [int(v) for v in matrix.sum(1).tolist()]
    return summary


def probability_diagnostics(probabilities, truth):
    """Unfitted validation diagnostics; no calibration parameter is selected."""
    target = torch.from_numpy(truth).long()
    confidence, predicted = probabilities.max(0)
    correct = predicted == target
    bins = []
    for index in range(10):
        low, high = index / 10, (index + 1) / 10
        mask = (confidence >= low) & ((confidence < high) if index < 9 else (confidence <= high))
        count = int(mask.sum())
        bins.append({'count': count, 'confidence_sum': float(confidence[mask].double().sum()),
                     'correct_sum': int(correct[mask].sum())})
    true_probabilities = probabilities.gather(0, target.unsqueeze(0)).squeeze(0)
    nll_sum = float(-true_probabilities.clamp(min=1e-12).double().log().sum())
    brier_sum = float((probabilities.double().square().sum(0) - 2 * true_probabilities.double() + 1).sum())
    entropy_sum = float(-(probabilities.clamp(min=1e-12).double() * probabilities.clamp(min=1e-12).double().log()).sum())
    return {'n_pixels': truth.size, 'nll_sum': nll_sum, 'brier_sum': brier_sum,
            'entropy_sum': entropy_sum, 'confidence_bins': bins}


def diagnostic_summary(sections):
    count = sum(section['n_pixels'] for section in sections)
    bins = [{key: sum(section['confidence_bins'][index][key] for section in sections)
             for key in ('count', 'confidence_sum', 'correct_sum')} for index in range(10)]
    ece = sum(abs(bin_['confidence_sum'] - bin_['correct_sum']) for bin_ in bins) / count
    return {'n_pixels': count, 'mean_nll': sum(s['nll_sum'] for s in sections) / count,
            'multiclass_brier': sum(s['brier_sum'] for s in sections) / count,
            'mean_predictive_entropy': sum(s['entropy_sum'] for s in sections) / count,
            'ece_10_equal_width_bins': ece, 'confidence_bins': bins,
            'note': 'Unfitted validation diagnostics; pixel bins are not independent samples and are not a guarantee of calibrated or out-of-domain accuracy.'}


@torch.no_grad()
def paired_native_probabilities(candidate, reference, image, dev):
    """Preserve frozen native tiles and mean logits separately for each model."""
    array = np.array(image.convert('RGB'))
    height, width = array.shape[:2]
    patch, stride = 512, 448
    accumulated = [torch.zeros(5, height, width, dtype=torch.float32) for _ in range(2)]
    counts = torch.zeros(1, height, width, dtype=torch.float32)
    tops = list(range(0, max(1, height - patch + 1), stride))
    lefts = list(range(0, max(1, width - patch + 1), stride))
    if tops[-1] != height - patch:
        tops.append(max(0, height - patch))
    if lefts[-1] != width - patch:
        lefts.append(max(0, width - patch))
    forward_seconds = [0.0, 0.0]
    for top in tops:
        for left in lefts:
            tile = array[top:top + patch, left:left + patch]
            tensor = TF.normalize(TF.to_tensor(np.ascontiguousarray(tile)),
                                  (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)).unsqueeze(0).to(dev)
            for index, model in enumerate((candidate, reference)):
                torch.cuda.synchronize(dev)
                started = time.perf_counter()
                logits = model(tensor)['out'][0].cpu()
                torch.cuda.synchronize(dev)
                forward_seconds[index] += time.perf_counter() - started
                accumulated[index][:, top:top+tile.shape[0], left:left+tile.shape[1]] += logits
            counts[:, top:top+tile.shape[0], left:left+tile.shape[1]] += 1
    probabilities = [(array / counts.clamp(min=1)).softmax(0) for array in accumulated]
    return probabilities, {'candidate_forward_seconds': forward_seconds[0],
                           'reference_forward_seconds': forward_seconds[1],
                           'tiles_per_model': len(tops) * len(lefts),
                           'note': 'Synchronized tile forwards including GPU-to-CPU logits transfer; not a complete application latency measurement.'}


def run(protocol, runtime, repo, output):
    started = time.perf_counter()
    began_utc = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    assert torch.__version__ == protocol['runtime']['torch']
    assert torchvision.__version__ == protocol['runtime']['torchvision']
    assert torch.cuda.is_available(), 'Free GPU unavailable; no paid fallback.'
    os.environ['TORCH_HOME'] = str(runtime / 'torch-cache')
    torch.hub.set_dir(str(runtime / 'torch-cache/hub'))
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    os.environ.update({'KHANYA_SUBSET': 'S2', 'KHANYA_SEED': str(protocol['training_seed']),
                       'KHANYA_RUN_ID': protocol['run_id'], 'KHANYA_EPOCHS': '24',
                       'KHANYA_PATCHES_PER_EPOCH': '192', 'KHANYA_VAL_PATCHES': '32'})
    sys.path.insert(0, str(repo))
    source_hashes = {str(p.relative_to(repo)).replace('\\', '/'): sha_file(p)
                     for p in sorted((repo / 'src').rglob('*.py'))}
    assert source_hashes == protocol['source_file_sha256'] and len(source_hashes) == 35

    input_root = Path('/kaggle/input')
    checkpoint_parent = 'lumenstone_s2_patches_' + protocol['reference']['run_id'] + '_dice'
    refs = [p for p in input_root.rglob('best.pt') if p.parent.name == checkpoint_parent]
    assert len(refs) == 1, 'Exactly one frozen reference checkpoint required.'
    reference_checkpoint = refs[0]
    assert sha_file(reference_checkpoint) == protocol['reference']['checkpoint_sha256']
    assert reference_checkpoint.stat().st_size == protocol['reference']['checkpoint_bytes']
    manifests = list(input_root.rglob('khanya-s2-dice-manifest-' + protocol['reference']['run_id'] + '.json'))
    assert len(manifests) == 1 and sha_file(manifests[0]) == protocol['reference']['manifest_sha256']
    reference_manifest = json.loads(manifests[0].read_text())
    assert reference_manifest['source_file_sha256'] == protocol['reference']['source_file_sha256']
    assert reference_manifest['validation_image_ids'] == protocol['validation_image_ids']

    archives = list(input_root.rglob('S2_v2.zip'))
    assert len(archives) <= 1
    if archives:
        archive = archives[0]
    else:
        archive = runtime / 'S2_v2.zip'
        api_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key=' + quote(protocol['publisher_download'], safe='')
        with urlopen(api_url, timeout=60) as response:
            url = json.load(response)['href']
        with urlopen(url, timeout=180) as response, archive.open('wb') as stream:
            for chunk in iter(lambda: response.read(8 * 1024 * 1024), b''):
                stream.write(chunk)
    assert sha_file(archive) == protocol['dataset_archive_sha256']
    assert archive.stat().st_size == protocol['dataset_archive_bytes']
    dataset = runtime / 'dataset'
    dataset.mkdir()
    with ZipFile(archive) as z:
        safe_extract(z, dataset)
    roots = []
    for train_dir in dataset.rglob('imgs/train'):
        candidate = train_dir.parent.parent
        if all((candidate / p).is_dir() for p in ('imgs/test', 'masks/train', 'masks/test')):
            train_imgs = {p.stem for p in (candidate / 'imgs/train').glob('*.jpg')}
            test_imgs = {p.stem for p in (candidate / 'imgs/test').glob('*.jpg')}
            train_masks = {p.stem for p in (candidate / 'masks/train').glob('*.png')}
            test_masks = {p.stem for p in (candidate / 'masks/test').glob('*.png')}
            if len(train_imgs) == 37 and len(test_imgs) == 12 and train_imgs == train_masks and test_imgs == test_masks:
                roots.append(candidate)
    assert len(roots) == 1
    data_link = repo / 'data/raw/lumenstone/S2_v2'
    data_link.parent.mkdir(parents=True)
    data_link.symlink_to(roots[0].resolve(), target_is_directory=True)
    from src.segmentation import lumenstone as ls, metrics, patches
    from src.segmentation.model import build_model
    assert ls.CLASS_CODES == protocol['class_codes'] and ls.CLASS_NAMES == protocol['class_names']
    train_ids, validation_ids, test_ids = ls.split_ids()
    assert train_ids == protocol['train_image_ids']
    assert validation_ids == protocol['validation_image_ids']
    assert test_ids == protocol['test_image_ids']
    assert [len(train_ids), len(validation_ids), len(test_ids)] == [31, 6, 12]
    assert not (set(train_ids) & set(validation_ids) or set(train_ids) & set(test_ids) or set(validation_ids) & set(test_ids))
    assert patches.PATCH == 512 and patches.SEED == protocol['training_seed']
    output.mkdir(exist_ok=True)
    save_json(output / 'protocol.json', protocol)
    train_log = runtime / 'training.log'
    print('Starting bounded validation-only training:', protocol['run_id'], flush=True)
    command = [sys.executable, '-c', "from src.segmentation.train_patches import train; train('dice')"]
    timed_out = False
    with train_log.open('w', encoding='utf-8') as stream:
        try:
            result = subprocess.run(command, cwd=repo, env=os.environ.copy(), stdout=stream,
                                    stderr=subprocess.STDOUT, timeout=protocol['training_timeout_seconds'])
            training_return_code = result.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            training_return_code = None
    checkpoint_dir = repo / 'checkpoints' / ('lumenstone_s2_patches_' + protocol['run_id'] + '_dice')
    history_path = checkpoint_dir / 'validation_history.json'
    history = json.loads(history_path.read_text()) if history_path.exists() else []
    shutil.copyfile(train_log, output / 'training.log')
    manifest = {'run_id': protocol['run_id'], 'architecture': protocol['architecture'],
                'training_seed': protocol['training_seed'], 'split_seed': 42,
                'protocol_sha256': sha_file(runtime / 'protocol.json'), 'source_bundle_sha256': protocol['source_bundle_sha256'],
                'source_file_sha256': source_hashes, 'dataset_archive_sha256': protocol['dataset_archive_sha256'],
                'dataset_archive_bytes': archive.stat().st_size, 'train_image_ids': train_ids,
                'validation_image_ids': validation_ids, 'test_image_ids': test_ids,
                'training_budget': protocol['training_budget'], 'completed_epochs': len(history),
                'training_timed_out': timed_out, 'training_return_code': training_return_code,
                'test_evaluation_performed': False, 'test_metrics': None, 'test_used_for_selection': False,
                'automatic_deployment': False, 'started_at_utc': began_utc,
                'runtime': {'python': sys.version, 'torch': torch.__version__, 'torchvision': torchvision.__version__,
                            'cuda': torch.version.cuda, 'gpu': torch.cuda.get_device_name(0)},
                'initialization_artifact_sha256': {p.name: sha_file(p) for p in (runtime / 'torch-cache/hub/checkpoints').glob('*.pth')}}
    save_json(output / 'validation_history.json', metrics.json_safe(history))
    if timed_out or training_return_code != 0 or len(history) != 24:
        manifest.update({'status': 'incomplete_no_promotable_checkpoint', 'checkpoint_exported': False,
                         'ensemble_validation_performed': False, 'elapsed_seconds': time.perf_counter() - started})
        save_json(output / 'run_manifest.json', manifest)
        raise RuntimeError('Bounded training did not complete; partial metrics/log preserved. No candidate export, automatic retry, test evaluation, or deployment.')
    assert [row['epoch'] for row in history] == list(range(1, 25))
    best = max(history, key=lambda row: row['validation_full_section_metrics']['foreground_macro_iou'])
    best_checkpoint = checkpoint_dir / 'best.pt'
    checkpoint_sha256 = sha_file(best_checkpoint)
    exported_checkpoint = output / 'checkpoints' / protocol['run_id'] / 'best.pt'
    exported_checkpoint.parent.mkdir(parents=True)
    shutil.copyfile(best_checkpoint, exported_checkpoint)
    assert sha_file(exported_checkpoint) == checkpoint_sha256
    manifest.update({'status': 'training_complete', 'best_epoch': best['epoch'],
                     'best_validation': best['validation_full_section_metrics'],
                     'checkpoint_sha256': checkpoint_sha256, 'checkpoint_bytes': best_checkpoint.stat().st_size,
                     'checkpoint_relative_path': str(exported_checkpoint.relative_to(output)), 'checkpoint_exported': True})

    # Reserve outputs if runtime gets close to the two-hour kernel cap.
    if time.perf_counter() - started > protocol['ensemble_latest_start_seconds']:
        manifest.update({'ensemble_validation_performed': False, 'ensemble_skip_reason': 'runtime reserve before hard cap',
                         'elapsed_seconds': time.perf_counter() - started})
        save_json(output / 'run_manifest.json', metrics.json_safe(manifest))
        print('Training complete; ensemble diagnostic deferred to respect the fixed budget.', flush=True)
        return

    dev = torch.device('cuda')
    candidate_model = build_model(num_classes=5, pretrained=False).to(dev)
    state = torch.load(best_checkpoint, map_location=dev, weights_only=True)
    assert state and all(isinstance(k, str) and isinstance(v, torch.Tensor) for k, v in state.items())
    candidate_model.load_state_dict(state, strict=True)
    del state
    reference_model_path = runtime / 'reference_model.py'
    assert sha_file(reference_model_path) == protocol['reference']['model_source_sha256']
    spec = importlib.util.spec_from_file_location('frozen_reference_model', reference_model_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    reference_model = module.build_model(num_classes=5, pretrained=False).to(dev)
    state = torch.load(reference_checkpoint, map_location=dev, weights_only=True)
    assert state and all(isinstance(k, str) and isinstance(v, torch.Tensor) for k, v in state.items())
    reference_model.load_state_dict(state, strict=True)
    del state
    candidate_model.eval()
    reference_model.eval()
    assert not candidate_model.training and not reference_model.training

    original_open = Image.open
    def validation_only_open(path, *args, **kwargs):
        if isinstance(path, (str, Path)) and Path(path).parent.name == 'test':
            raise RuntimeError('Test pixels are forbidden in this experiment.')
        return original_open(path, *args, **kwargs)
    Image.open = validation_only_open
    results = {name: {'matrix': metrics.new_confusion(5), 'per_section': {}, 'diagnostic_sections': []}
               for name in ('candidate', 'reference', 'equal_probability_ensemble')}
    inference_started = time.perf_counter()
    reference_best = max(reference_manifest['validation_history'], key=lambda row: row['validation_full_section_metrics']['foreground_macro_iou'])
    reference_saved = reference_best['validation_full_section_metrics']
    for stem in sorted(validation_ids):
        with Image.open(ls.DATA_DIR / 'imgs/train' / (stem + '.jpg')) as im:
            image = im.convert('RGB')
        truth = patches.labels_for(stem, 'train')
        (candidate_prob, reference_prob), timing = paired_native_probabilities(candidate_model, reference_model, image, dev)
        ensemble_prob = (candidate_prob + reference_prob) * 0.5
        disagreement = int((candidate_prob.argmax(0) != reference_prob.argmax(0)).sum())
        for name, probabilities in (('candidate', candidate_prob), ('reference', reference_prob),
                                    ('equal_probability_ensemble', ensemble_prob)):
            matrix = metrics.new_confusion(5)
            prediction = probabilities.argmax(0)
            metrics.confusion_from_batch(prediction, torch.from_numpy(truth), 5, matrix)
            assert int(matrix.sum()) == truth.size == image.width * image.height
            results[name]['matrix'] += matrix
            section = enrich(matrix, metrics)
            section.update({'n_pixels': truth.size, 'timing': timing,
                            'candidate_reference_disagreement_pixels': disagreement})
            results[name]['per_section'][stem] = section
            results[name]['diagnostic_sections'].append(probability_diagnostics(probabilities, truth))
        # New helper must reproduce saved single-model validation counts exactly.
        for name, saved in (('candidate', best['validation_full_section_metrics']), ('reference', reference_saved)):
            for key in ('tp_per_class', 'fp_per_class', 'fn_per_class'):
                assert results[name]['per_section'][stem][key] == saved['per_section'][stem][key], 'Frozen single-model validation prediction mismatch.'
        print(stem, 'validation comparison complete', flush=True)
        del image, truth, candidate_prob, reference_prob, ensemble_prob, probabilities, prediction
    comparison = {'run_id': protocol['run_id'], 'fixed_ensemble_weights': [0.5, 0.5],
                  'calibration_fitted': False, 'validation_image_ids': validation_ids, 'n_validation_sections': 6,
                  'test_evaluation_performed': False, 'test_metrics': None, 'automatic_deployment': False,
                  'reference_checkpoint_sha256': protocol['reference']['checkpoint_sha256'],
                  'candidate_checkpoint_sha256': checkpoint_sha256,
                  'elapsed_validation_comparison_seconds': time.perf_counter() - inference_started,
                  'models': {}, 'ood_detector_trained_or_validated': False,
                  'disagreement_is_validated_ood_gate': False,
                  'limitations': 'Same six sections select checkpoints and diagnose ensemble; single new seed per architecture. No independent locality/OOD metadata or test-tuned routing. Fixed equal averaging is an exploratory diagnostic; it may worsen phase performance and roughly adds two model forward costs.'}
    for name, values in results.items():
        summary = enrich(values['matrix'], metrics)
        summary.update({'per_section': values['per_section'],
                        'probability_diagnostics': diagnostic_summary(values['diagnostic_sections'])})
        comparison['models'][name] = summary
    ensemble = comparison['models']['equal_probability_ensemble']
    reference = comparison['models']['reference']
    passes = (ensemble['foreground_macro_iou'] >= reference['foreground_macro_iou'] + 0.01
              and all(ensemble['iou_per_class'][i] >= reference['iou_per_class'][i] - 0.02 for i in (1, 3, 4))
              and ensemble['precision_per_class'][2] >= reference['precision_per_class'][2] - 0.02
              and ensemble['recall_per_class'][2] >= reference['recall_per_class'][2] - 0.02)
    comparison['passes_predeclared_exploratory_validation_gate'] = passes
    comparison['gate_is_deployment_approval'] = False
    assert sha_file(reference_checkpoint) == protocol['reference']['checkpoint_sha256']
    assert sha_file(best_checkpoint) == checkpoint_sha256
    save_json(output / 'validation_comparison.json', metrics.json_safe(comparison))
    manifest.update({'ensemble_validation_performed': True, 'elapsed_seconds': time.perf_counter() - started,
                     'finished_at_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())})
    save_json(output / 'run_manifest.json', metrics.json_safe(manifest))
    assert not any(p.suffix.lower() in ('.zip', '.jpg', '.png', '.npz', '.pth') for p in output.rglob('*') if p.is_file())
    assert not list(output.rglob('last.pt'))
    print('Validation-only experiment complete; no test inference, routing deployment, or automatic promotion.', flush=True)


if __name__ == '__main__':
    protocol = json.loads(Path(sys.argv[1]).read_text())
    runtime = Path(sys.argv[1]).parent
    run(protocol, runtime, runtime / 'source', Path('/kaggle/working'))
