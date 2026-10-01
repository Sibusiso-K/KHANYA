"""Submit one of the two authorized bounded kernels exactly once."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
assert len(sys.argv)==2 and sys.argv[1] in ('fcn-seed42','deeplab-seed43')
target=HERE/sys.argv[1]
marker=target/'launch_attempt.json'
assert not marker.exists(), 'Submission already attempted; do not retry automatically.'
prepared=json.loads((HERE/'prepared_experiments.json').read_text())
entry=next(row for row in prepared if row['slug']==sys.argv[1])
metadata=json.loads((target/'kernel-metadata.json').read_text())
protocol=json.loads((target/'protocol.json').read_text())
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(target/'experiment.ipynb')==entry['notebook_sha256'] and sha(target/'protocol.json')==entry['protocol_sha256']
assert sha(HERE/'runtime_experiment.py')==entry['runtime_script_sha256']
assert metadata['id']==entry['kernel']==protocol['kernel']
assert metadata['is_private'] is True and metadata['enable_gpu'] is True and metadata['machine_shape']=='NvidiaTeslaT4'
assert metadata['kernel_sources']==['lethabomh14/reefprint-s2-extended-dice/1']
assert protocol['max_kernel_runtime_seconds']==7200 and protocol['total_gpu_runtime_cap_seconds']==14400
assert protocol['test_evaluation_performed'] is False and protocol['automatic_deployment'] is False
assert len(list(HERE.glob('*/launch_attempt.json')))<2
record={'attempted_at_utc':datetime.now(timezone.utc).isoformat(),'kernel':metadata['id'],'url':'https://www.kaggle.com/code/'+metadata['id'],
        'notebook_sha256':entry['notebook_sha256'],'protocol_sha256':entry['protocol_sha256'],'max_kernel_runtime_seconds':7200,
        'submission_attempts':1,'test_evaluation_performed':False,'automatic_deployment':False,'status':'submission_started'}
marker.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
result=subprocess.run(['kaggle','kernels','push','-p',str(target),'--timeout','7200'],capture_output=True,text=True,
                      encoding='utf-8',errors='replace',timeout=180)
record.update({'submission_exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr,
               'status':'submitted' if result.returncode==0 else 'submission_failed_do_not_retry_automatically'})
marker.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
print(result.stdout)
if result.stderr:print(result.stderr)
print(json.dumps({k:v for k,v in record.items() if k not in ('stdout','stderr')},indent=2))
raise SystemExit(result.returncode)
