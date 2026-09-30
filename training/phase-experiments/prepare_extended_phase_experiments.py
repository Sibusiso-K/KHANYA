"""Prepare private, matched native-context / small-grain-context Kaggle runs.
No test evaluation, no automatic deployment, no credentials or raw data bundled.
"""
import ast, base64, copy, hashlib, io, json, re, zipfile
from pathlib import Path
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'training/matched_ce_control_20260930/matched_ce_control.ipynb').exists())
base=json.loads((ROOT/'training/matched_ce_control_20260930/matched_ce_control.ipynb').read_text())
combined='\n'.join(''.join(c['source']) for c in base['cells'] if c['cell_type']=='code')
encoded=re.search(r'source_bundle_b64 = """(.*?)"""',combined,re.S).group(1)
archive=zipfile.ZipFile(io.BytesIO(base64.b64decode(encoded)))
original={n:archive.read(n) for n in archive.namelist()}
outputs=[]
for variant in ('extended-dice','small-grain-dice'):
    notebook=copy.deepcopy(base); files=original.copy()
    if variant=='small-grain-dice':
        key='src/segmentation/patches.py'; source=files[key].decode()
        old='half = PATCH // 2'
        assert old in source
        source=source.replace(old,'crop_size = PATCH // 2 if self.train and rng.random() < 0.5 else PATCH\n        half = crop_size // 2',1)
        source=source.replace('max(0, height - PATCH)','max(0, height - crop_size)',1).replace('max(0, width - PATCH)','max(0, width - crop_size)',1)
        source=source.replace('image[top:top + PATCH, left:left + PATCH]','image[top:top + crop_size, left:left + crop_size]',1).replace('labels[top:top + PATCH, left:left + PATCH]','labels[top:top + crop_size, left:left + crop_size]',1)
        anchor='        if self.train:\n'
        assert anchor in source
        source=source.replace(anchor,'        if crop_size != PATCH:\n            image_patch = np.array(Image.fromarray(image_patch).resize((PATCH,PATCH),Image.Resampling.BILINEAR))\n            label_patch = np.array(Image.fromarray(label_patch.astype(np.uint8)).resize((PATCH,PATCH),Image.Resampling.NEAREST))\n\n'+anchor,1)
        ast.parse(source);files[key]=source.encode()
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as out:
        for name,data in sorted(files.items()):out.writestr(zipfile.ZipInfo(name,date_time=(2026,1,1,0,0,0)),data,compress_type=zipfile.ZIP_DEFLATED)
    bundle=stream.getvalue();new_sha=hashlib.sha256(bundle).hexdigest()
    run_id='20260930-s2-seed42-'+variant+'-v1'
    for cell in notebook['cells']:
        if cell['cell_type']!='code':
            cell['source']=[f'REEFPRINT {variant}: seed42, 24 epochs x192 patches, CE+Dice. Matched pair differs only in training crop policy; validation uses unchanged full native sections. Training-only half-size context (small-grain variant) is experimental, not super-resolution. Test not evaluated; no deployment.\n'];continue
        source=''.join(cell['source'])
        source=source.replace(encoded,base64.b64encode(bundle).decode())
        for name,data in original.items():source=source.replace(hashlib.sha256(data).hexdigest(),hashlib.sha256(files[name]).hexdigest())
        source=source.replace('22a6117265bd6c6dd09c2fa4b3b9b28ab1bb60c70ee84cd364bae33db6a990fc',new_sha)
        source=source.replace('20260930-s2-seed42-fullval-ce-control-v1',run_id).replace("'--loss', 'ce'","'--loss', 'dice'")
        source=source.replace("KHANYA_EPOCHS'] = '8'","KHANYA_EPOCHS'] = '24'").replace("KHANYA_PATCHES_PER_EPOCH'] = '64'","KHANYA_PATCHES_PER_EPOCH'] = '192'")
        source=source.replace("'epochs': 8, 'patches_per_epoch': 64","'epochs': 24, 'patches_per_epoch': 192").replace('8 epochs, 64 train patches/epoch','24 epochs, 192 train patches/epoch')
        source=source.replace('cross-entropy (matched CE control)','cross-entropy + soft Dice; extended matched crop experiment').replace('khanya-s2-ce','khanya-s2-dice').replace('_{run_id}_ce','_{run_id}_dice')
        ast.parse(source);cell['source']=source.splitlines(keepends=True);cell['outputs']=[];cell['execution_count']=None
    code='\n'.join(''.join(c['source']) for c in notebook['cells'] if c['cell_type']=='code')
    assert "'--eval'" not in code and "'test_evaluation_performed': False" in code
    dest=ROOT/'training'/variant;dest.mkdir(exist_ok=True)
    (dest/'experiment.ipynb').write_text(json.dumps(notebook,indent=1))
    metadata={'id':'lethabomh14/reefprint-s2-'+variant,'title':'REEFPRINT S2 '+variant,'code_file':'experiment.ipynb','language':'python','kernel_type':'notebook','is_private':True,'enable_gpu':True,'enable_internet':True,'dataset_sources':[],'competition_sources':[],'kernel_sources':[]}
    (dest/'kernel-metadata.json').write_text(json.dumps(metadata,indent=2))
    protocol={'variant':variant,'run_id':run_id,'seed':42,'epochs':24,'patches_per_epoch':192,'loss':'CE+Dice','selection':'native full-validation foreground macro IoU','test_evaluation':False,'automatic_deployment':False,'crop_policy':'50% training 256px crops resized to512; nearest masks' if variant.startswith('small') else 'native512px','source_sha':new_sha,'promotion':'Compare same validation sections; require rare-phase recall/IoU and no substantial common-phase regression; independent quality review before final test/deployment.'}
    (dest/'protocol.json').write_text(json.dumps(protocol,indent=2));outputs.append(protocol)
print(json.dumps(outputs,indent=2))
