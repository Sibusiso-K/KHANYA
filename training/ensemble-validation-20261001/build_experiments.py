"""Prepare at most two bounded private validation-only experiments offline."""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import re
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
AUDIT = ROOT / 'training/audit_extended_20261001/extended-dice'
NOTEBOOK = AUDIT / 'source/reefprint-s2-extended-dice.ipynb'
MANIFEST = AUDIT / 'results/khanya-s2-dice-manifest-20260930-s2-seed42-extended-dice-v1.json'
MAX_KERNEL_SECONDS = 7200


def sha(value):
    return hashlib.sha256(value).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


m = json.loads(MANIFEST.read_text(encoding='utf-8'))
n = json.loads(NOTEBOOK.read_text(encoding='utf-8'))
code = '\n'.join(''.join(cell['source']) for cell in n['cells'] if cell['cell_type'] == 'code')
original_bundle = base64.b64decode(re.search(r'source_bundle_b64 = """(.*?)"""', code, re.S).group(1), validate=True)
assert sha(original_bundle) == m['source_bundle_sha256'] == '4cffd60c88fea1a7553f8f154040cf2ce93f7312f0571f3dc6784b5938988528'
with ZipFile(io.BytesIO(original_bundle)) as z:
    assert z.testzip() is None
    original = {name: z.read(name) for name in z.namelist()}
assert {name: sha(data) for name,data in original.items()} == m['source_file_sha256']
assert m['train_pairs'] == 31 and m['validation_pairs'] == 6 and m['test_pairs'] == 12
assert m['validation_image_ids'] == ['train_06','train_21','train_13','train_10','train_23','train_27']
assert m['test_evaluation_performed'] is False
runner = (HERE / 'runtime_experiment.py').read_bytes()
ast.parse(runner.decode('utf-8'))
reference_model = original['src/segmentation/model.py']

fcn_model = '''import torch
from torchvision.models.segmentation import fcn_resnet50, FCN_ResNet50_Weights

def build_model(num_classes: int = 2, pretrained: bool = True):
    weights = FCN_ResNet50_Weights.COCO_WITH_VOC_LABELS_V1 if pretrained else None
    model = fcn_resnet50(weights=weights, weights_backbone=None, aux_loss=True)
    model.classifier[4] = torch.nn.Conv2d(512, num_classes, kernel_size=1)
    if model.aux_classifier is not None:
        model.aux_classifier[4] = torch.nn.Conv2d(256, num_classes, kernel_size=1)
    return model

def device():
    return torch.device('cuda' if torch.cuda.is_available() else 'cpu')
'''.encode('utf-8')
ast.parse(fcn_model.decode())
experiments = [
    ('fcn-seed42', 'FCN-ResNet50', 42, fcn_model),
    ('deeplab-seed43', 'DeepLabV3-ResNet50', 43, reference_model),
]
summaries = []
for slug, architecture, seed, model_bytes in experiments:
    destination = HERE / slug
    destination.mkdir(parents=True, exist_ok=True)
    files = original.copy()
    files['src/segmentation/model.py'] = model_bytes
    buffer = io.BytesIO()
    with ZipFile(buffer, 'w', ZIP_DEFLATED) as z:
        for name, data in sorted(files.items()):
            z.writestr(ZipInfo(name, date_time=(2026,1,1,0,0,0)), data, compress_type=ZIP_DEFLATED)
    bundle = buffer.getvalue()
    hashes = {name: sha(data) for name,data in files.items()}
    protocol = {
        'run_id': '20261001-s2-' + slug + '-native-ensemble-v1',
        'kernel': 'lethabomh14/reefprint-s2-' + slug + '-ensemble-validation',
        'architecture': architecture, 'training_seed': seed, 'split_seed': 42,
        'source_bundle_sha256': sha(bundle), 'source_file_sha256': hashes,
        'runtime_script_sha256': sha(runner), 'base_source_commit_informational': m['git_commit'],
        'changed_modules_from_frozen_native': [name for name in files if files[name] != original[name]],
        'dataset': 'LumenStone S2 v2',
        'publisher_download': 'https://disk.360.yandex.ru/d/wYK_5JyQy0pIcg',
        'dataset_archive_sha256': m['dataset_archive_sha256'], 'dataset_archive_bytes': m['dataset_archive_bytes'],
        'train_image_ids': m['train_image_ids'], 'validation_image_ids': m['validation_image_ids'], 'test_image_ids': m['test_image_ids'],
        'class_codes': [0,1,3,5,7], 'class_names': ['background','chalcopyrite','magnetite','pyrrhotite','pentlandite'],
        'training_budget': {'epochs':24,'patches_per_epoch':192,'validation_patches':32,'patch_px':512,'batch_size':2,'learning_rate':0.0002},
        'loss': 'cross-entropy + unweighted soft multiclass Dice; frozen source losses.py',
        'crop_policy': 'native 512px; frozen balanced-centre sampling and flips; no small-grain resizing',
        'initialization': ('FCN_ResNet50_Weights.COCO_WITH_VOC_LABELS_V1' if slug.startswith('fcn') else 'DeepLabV3_ResNet50_Weights.COCO_WITH_VOC_LABELS_V1'),
        'runtime': {'torch':'2.10.0+cu128','torchvision':'0.25.0+cu128'},
        'selection': 'Maximum fixed-six-section native full-validation foreground macro IoU over completed 24 epochs; diagnostic patch validation does not select weights.',
        'inference': 'Native whole sections, 512px tiles with 64px overlap; mean raw logits separately for each model, then softmax.',
        'ensemble': 'Exactly 0.5 candidate probability + 0.5 frozen native reference probability, argmax; no fitted weights, calibration temperature, thresholds, router, or test-time augmentation.',
        'exploratory_validation_gate': 'Ensemble foreground macro IoU >= reference +0.01; chalcopyrite/pyrrhotite/pentlandite IoU >= reference -0.02; magnetite precision and recall >= reference -0.02. This engineering diagnostic is not a deployment or industry accuracy threshold.',
        'probability_diagnostics': 'Validation-only NLL, multiclass Brier, predictive entropy, ten equal-width confidence bins/ECE, and candidate-reference disagreement; no fitted calibration or validated OOD detector.',
        'reference': {'kernel_source':'lethabomh14/reefprint-s2-extended-dice/1', 'run_id':m['run_id'],'epoch':12,
                      'checkpoint_sha256':m['checkpoint_sha256'],'checkpoint_bytes':168318771,
                      'manifest_sha256':sha(MANIFEST.read_bytes()),'source_file_sha256':m['source_file_sha256'],
                      'model_source_sha256':sha(reference_model),'selected_using':'validation only before the previous fixed test regression evaluation'},
        'new_design_inputs': 'Earlier validation evidence: extended native recovered magnetite; training histories volatile; small-grain variant regressed pentlandite. The already seen 12-section test outcome is not an experiment-selection/tuning input.',
        'test_evaluation_performed': False, 'test_metrics': None, 'test_used_for_selection': False,
        'automatic_deployment': False, 'ood_detector_trained_or_validated': False,
        'validation_limitations': 'Six image sections reused for checkpoint and ensemble diagnosis; no specimen/locality independence established. One run per new configuration cannot prove stable gains. No guarantee of specialist or swarm superiority.',
        'max_kernel_runtime_seconds':MAX_KERNEL_SECONDS,'training_timeout_seconds':6600,'ensemble_latest_start_seconds':6600,
        'run_count_cap':2,'submission_attempts_per_run':1,'total_gpu_runtime_cap_seconds':14400,
        'free_quota_before_launch':{'gpu_remaining_hours':25.33,'gpu_total_weekly_hours':30.0,'refresh_utc':'2026-10-03T00:00:00'},
        'cost': 'Private free Kaggle T4 only; no paid resources. Hard two-hour cap per kernel, at most two launches; no automatic retries.',
        'exports': 'Private best.pt plus small protocol/history/manifest/log/validation-comparison JSON. Runtime data, source, pretrained initializer, optimizer last.pt remain outside /kaggle/working. No host weight/data download.',
        'rights': 'User-authorized private publisher research use; torchvision v0.25 BSD-3-Clause code. Dataset and pretrained/derived checkpoint redistribution or commercial rights remain separate and unapproved.',
        'sources': [
            'https://docs.pytorch.org/vision/0.25/models/generated/torchvision.models.segmentation.fcn_resnet50.html',
            'https://docs.pytorch.org/vision/0.25/models/generated/torchvision.models.segmentation.deeplabv3_resnet50.html',
            'https://github.com/pytorch/vision/blob/v0.25.0/LICENSE',
            'https://arxiv.org/abs/1612.01474',
        ],
    }
    protocol_text = json.dumps(protocol, indent=2) + '\n'
    protocol_sha = sha(protocol_text.encode('utf-8'))
    (destination / 'protocol.json').write_text(protocol_text, encoding='utf-8', newline='\n')
    preflight = '''from pathlib import Path, PurePosixPath
import base64, hashlib, io, json, sys, tempfile
from zipfile import ZipFile
import runpy

protocol = json.loads(PROTOCOL_LITERAL)
protocol_text = json.dumps(protocol, indent=2) + '\\n'
assert hashlib.sha256(protocol_text.encode('utf-8')).hexdigest() == PROTOCOL_SHA
runtime = Path(tempfile.mkdtemp(prefix='reefprint-validation-'))
repo = runtime / 'source'
repo.mkdir()
bundle = base64.b64decode(BUNDLE_LITERAL, validate=True)
assert hashlib.sha256(bundle).hexdigest() == protocol['source_bundle_sha256']
with ZipFile(io.BytesIO(bundle)) as z:
    assert z.testzip() is None
    for member in z.infolist():
        path = PurePosixPath(member.filename)
        assert not path.is_absolute() and '..' not in path.parts and '\\\\' not in member.filename
        assert (member.external_attr >> 16) & 0o170000 != 0o120000
        assert (repo / member.filename).resolve().is_relative_to(repo.resolve())
    z.extractall(repo)
runner = base64.b64decode(RUNNER_LITERAL, validate=True)
assert hashlib.sha256(runner).hexdigest() == protocol['runtime_script_sha256']
runner_path = runtime / 'experiment_runtime.py'
runner_path.write_bytes(runner)
reference_model = base64.b64decode(REFERENCE_MODEL_LITERAL, validate=True)
assert hashlib.sha256(reference_model).hexdigest() == protocol['reference']['model_source_sha256']
(runtime / 'reference_model.py').write_bytes(reference_model)
protocol_path = runtime / 'protocol.json'
protocol_path.write_text(protocol_text, encoding='utf-8')
print('Protocol and source prepared; private validation only:', protocol['run_id'])
'''
    for token, value in [('PROTOCOL_LITERAL',json.dumps(protocol)), ('PROTOCOL_SHA',protocol_sha),
                         ('BUNDLE_LITERAL',base64.b64encode(bundle).decode()),
                         ('RUNNER_LITERAL',base64.b64encode(runner).decode()),
                         ('REFERENCE_MODEL_LITERAL',base64.b64encode(reference_model).decode())]:
        preflight = preflight.replace(token, repr(value))
    execute = "sys.argv = [str(runner_path), str(protocol_path)]\nrunpy.run_path(str(runner_path), run_name='__main__')\n"
    notebook = {'nbformat':4,'nbformat_minor':5,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}},
                'cells':[{'cell_type':'markdown','metadata':{},'source':[f"# REEFPRINT {architecture} seed {seed}: bounded validation-only training and fixed ensemble diagnostic\nNo test inference, fitted routing, automatic promotion or paid resources.\n"]},
                         *[{'cell_type':'code','metadata':{},'source':s.splitlines(keepends=True),'outputs':[],'execution_count':None} for s in (preflight,execute)]]}
    for cell in notebook['cells']:
        if cell['cell_type']=='code':
            ast.parse(''.join(cell['source']))
    write_json(destination / 'experiment.ipynb', notebook)
    metadata = {'id':protocol['kernel'],'title':'REEFPRINT S2 '+slug+' ensemble validation','code_file':'experiment.ipynb',
                'language':'python','kernel_type':'notebook','is_private':True,'enable_gpu':True,'enable_tpu':False,
                'enable_internet':True,'machine_shape':'NvidiaTeslaT4',
                'docker_image':'gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461',
                'docker_image_pinning_type':'original','dataset_sources':[],'competition_sources':[],
                'kernel_sources':['lethabomh14/reefprint-s2-extended-dice/1'],'model_sources':[]}
    write_json(destination / 'kernel-metadata.json',metadata)
    summaries.append({'slug':slug,'kernel':protocol['kernel'],'source_bundle_sha256':protocol['source_bundle_sha256'],
                      'protocol_sha256':protocol_sha,'notebook_sha256':sha((destination/'experiment.ipynb').read_bytes()),
                      'runtime_script_sha256':sha(runner),'changed_modules':protocol['changed_modules_from_frozen_native'],
                      'max_kernel_runtime_seconds':MAX_KERNEL_SECONDS})
assert len(summaries)==2 and sum(row['max_kernel_runtime_seconds'] for row in summaries)==14400
write_json(HERE/'prepared_experiments.json',summaries)
print(json.dumps(summaries,indent=2))
