"""Offline checks using synthetic arrays; no data, weights, network or training."""
import ast
import base64
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import numpy as np
from PIL import Image
import torch
import torchvision

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
torch.set_num_threads(2)

spec = importlib.util.spec_from_file_location('experiment_runtime', HERE/'runtime_experiment.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
manifest_path = ROOT/'training/audit_extended_20261001/extended-dice/results/khanya-s2-dice-manifest-20260930-s2-seed42-extended-dice-v1.json'
manifest = json.loads(manifest_path.read_text())
prepared = json.loads((HERE/'prepared_experiments.json').read_text())
bundles = {}
for entry in prepared:
    dest = HERE/entry['slug']
    notebook = json.loads((dest/'experiment.ipynb').read_text())
    protocol = json.loads((dest/'protocol.json').read_text())
    code = '\n'.join(''.join(c['source']) for c in notebook['cells'] if c['cell_type']=='code')
    tree = ast.parse(code)
    decoded_bundle = next(node for node in ast.walk(tree) if isinstance(node, ast.Assign)
                          and any(isinstance(target,ast.Name) and target.id=='bundle' for target in node.targets))
    bundle = base64.b64decode(ast.literal_eval(decoded_bundle.value.args[0]), validate=True)
    assert hashlib.sha256(bundle).hexdigest()==entry['source_bundle_sha256']==protocol['source_bundle_sha256']
    with ZipFile(io.BytesIO(bundle)) as z:
        assert z.testzip() is None
        files={name:z.read(name) for name in z.namelist()}
    hashes={name:hashlib.sha256(value).hexdigest() for name,value in files.items()}
    assert hashes==protocol['source_file_sha256'] and len(hashes)==35
    differences=[name for name in hashes if hashes[name]!=manifest['source_file_sha256'][name]]
    assert differences==protocol['changed_modules_from_frozen_native']
    assert differences==(['src/segmentation/model.py'] if entry['slug']=='fcn-seed42' else [])
    assert hashlib.sha256((dest/'protocol.json').read_bytes()).hexdigest()==entry['protocol_sha256']
    assert hashlib.sha256((dest/'experiment.ipynb').read_bytes()).hexdigest()==entry['notebook_sha256']
    assert hashlib.sha256((HERE/'runtime_experiment.py').read_bytes()).hexdigest()==entry['runtime_script_sha256']
    assert protocol['test_evaluation_performed'] is False and protocol['automatic_deployment'] is False
    for name in ('train_image_ids','validation_image_ids','test_image_ids'):
        assert protocol[name]==manifest[name]
    assert protocol['max_kernel_runtime_seconds']==7200
    bundles[entry['slug']]=files
    metadata=json.loads((dest/'kernel-metadata.json').read_text())
    assert metadata['is_private'] is True and metadata['machine_shape']=='NvidiaTeslaT4'
    assert metadata['kernel_sources']==['lethabomh14/reefprint-s2-extended-dice/1']
assert len(prepared)==2 and sum(p['max_kernel_runtime_seconds'] for p in prepared)==14400

# Verify changed model head dimensions using random initialization only.
model_namespace={}
exec(compile(bundles['fcn-seed42']['src/segmentation/model.py'].decode(),'fcn_source','exec'), model_namespace)
fcn=model_namespace['build_model'](num_classes=5,pretrained=False).eval()
with torch.no_grad():
    output=fcn(torch.zeros(1,3,64,64))
assert output['out'].shape==(1,5,64,64) and output['aux'].shape==(1,5,64,64)
del fcn,output

# Independently known diagnostic values for a perfect one-hot predictor and
# an uninformative five-class uniform predictor on one class-zero pixel.
truth=np.zeros((1,1),dtype=np.int64)
perfect=torch.tensor([1.,0.,0.,0.,0.]).reshape(5,1,1)
uniform=torch.ones(5,1,1)/5
one=runner.diagnostic_summary([runner.probability_diagnostics(perfect,truth)])
assert one['ece_10_equal_width_bins']==0 and one['mean_nll']==0 and one['multiclass_brier']==0
flat=runner.diagnostic_summary([runner.probability_diagnostics(uniform,truth)])
assert math.isclose(flat['ece_10_equal_width_bins'],.8,abs_tol=1e-7)
assert math.isclose(flat['mean_nll'],math.log(5),abs_tol=1e-7)
assert math.isclose(flat['multiclass_brier'],.8,abs_tol=1e-7)

# Reconstruct the frozen tiling function without importing dataset modules;
# compare both single-model argmax outputs to the new paired helper on a
# synthetic image with edge tiles and overlaps.
patch_tree=ast.parse(bundles['deeplab-seed43']['src/segmentation/patches.py'].decode())
function=next(node for node in patch_tree.body if isinstance(node,ast.FunctionDef) and node.name=='sliding_window_predict')
module=ast.Module(body=[function],type_ignores=[])
namespace={'torch':torch,'np':np,'TF':torchvision.transforms.functional,'PATCH':512,
           'ls':type('Labels',(),{'NUM_CLASSES':5})}
exec(compile(ast.fix_missing_locations(module),'frozen_sliding_window','exec'),namespace)
class FakeModel:
    def __init__(self,offset):self.offset=offset
    def __call__(self,x):
        return {'out':torch.cat([x,x[:,0:1]+self.offset,x[:,1:2]-self.offset],dim=1)}
image=Image.fromarray(np.random.default_rng(7).integers(0,256,(537,571,3),dtype=np.uint8))
models=(FakeModel(.15),FakeModel(-.1))
with patch.object(torch.cuda,'synchronize',lambda dev:None):
    probabilities,timing=runner.paired_native_probabilities(*models,image,torch.device('cpu'))
for model,prob in zip(models,probabilities):
    predicted,_=namespace['sliding_window_predict'](model,image,torch.device('cpu'))
    assert np.array_equal(predicted,prob.argmax(0).numpy())
assert timing['tiles_per_model']==4
assert not list(HERE.rglob('*.pt')) and not list(HERE.rglob('*.zip'))
result={'checks_passed':True,'synthetic_model_shape_checked':True,'native_pair_helper_matches_frozen_tiling_on_synthetic_edges':True,
        'unfitted_probability_diagnostics_checked':True,'source_and_protocol_hashes_checked':True,'two_hour_caps_checked':True,
        'local_test_runtime':{'torch':torch.__version__,'torchvision':torchvision.__version__},
        'note':'Local CPU package versions differ from pinned Kaggle runtime. No real pixels, checkpoints, training, network or test-set evaluation used.'}
(HERE/'preparation_checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(result,indent=2))
