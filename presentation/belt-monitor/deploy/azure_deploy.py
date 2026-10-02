"""Deploy the full REEFPRINT secure server to Azure App Service (Linux, Python 3.12, B1, always on).

python deploy/azure_deploy.py     (from presentation/belt-monitor, after `az login`; spends Azure credit: B1 ~US$13/month)

Never prints secrets: the data key is generated here, sent with --output none, and not written anywhere.
Data lives in /tmp/reefprint (local disk; a restart resets the guest sandbox and the signing keys). Staff accounts:
set the REEFPRINT_SEED_USERS app setting yourself from `python manage.py hash-password`.
"""
import base64, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NAME = os.environ.get("REEFPRINT_AZ_NAME", "reefprint-sonar")
RG = os.environ.get("REEFPRINT_AZ_RG", "reefprint-rg")
LOC = os.environ.get("REEFPRINT_AZ_LOCATION", "southafricanorth")
AZ = shutil.which("az") or shutil.which("az.cmd") or "az"


def az(*args, quiet=False):
    r = subprocess.run([AZ, *args] + (["--output", "none"] if quiet else []), capture_output=True, text=True)
    if r.returncode != 0:
        print("az failed:", " ".join(a for a in args if not a.startswith("REEFPRINT_DATA_KEY")), "\n", r.stderr[-1500:])
        sys.exit(1)
    return r.stdout


stage = tempfile.mkdtemp(prefix="reefprint_az_")
try:
    for f in ("index.html", "app.js", "server.py", "app_server.py", "manage.py"):
        shutil.copy2(os.path.join(ROOT, f), os.path.join(stage, f))
    for d in ("secure", "live", "fonts"):
        shutil.copytree(os.path.join(ROOT, d), os.path.join(stage, d), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(os.path.join(ROOT, "requirements-secure.txt"), os.path.join(stage, "requirements.txt"))
    os.chdir(stage)
    print("deploying (az webapp up)...", flush=True)
    out = az("webapp", "up", "--name", NAME, "--resource-group", RG, "--location", LOC, "--runtime", "PYTHON:3.12",
             "--sku", "B1", "--os-type", "Linux")
    print(out[-600:], flush=True)
    host = f"{NAME}.azurewebsites.net"
    az("webapp", "config", "appsettings", "set", "--name", NAME, "--resource-group", RG, "--settings",
       "REEFPRINT_PORT=8000", "WEBSITES_PORT=8000", "REEFPRINT_BIND=0.0.0.0", "REEFPRINT_DATA=/tmp/reefprint",
       f"REEFPRINT_HOSTS={host}", "REEFPRINT_SECURE_COOKIES=1", "REEFPRINT_TRUST_PROXY=1", "SCM_DO_BUILD_DURING_DEPLOYMENT=true",
       "REEFPRINT_DATA_KEY=" + base64.b64encode(os.urandom(32)).decode(), quiet=True)
    az("webapp", "config", "set", "--name", NAME, "--resource-group", RG, "--startup-file", "python app_server.py", "--always-on", "true", quiet=True)
    az("webapp", "update", "--name", NAME, "--resource-group", RG, "--https-only", "true", quiet=True)
    az("webapp", "restart", "--name", NAME, "--resource-group", RG, quiet=True)
    print("app url:", f"https://{host}/?guest=1")
finally:
    os.chdir(HERE)
    shutil.rmtree(stage, ignore_errors=True)
