"""Publish REEFPRINT Live to a Hugging Face Docker Space (always on; the laptop can be off).

python deploy/hf_deploy.py            (run from presentation/belt-monitor; uses the local HF login, never prints a token)

- Creates or updates the public Space <user>/reefprint with the Dockerfile and README from deploy/hf/.
- Uploads only what the server needs: page, app, server code, secure/, live/, fonts/. Never data_secure/, tests or keys.
- Sets REEFPRINT_DATA_KEY as a Space secret once (random, never printed or written locally). Staff accounts: set the
  REEFPRINT_SEED_USERS secret yourself in the Space settings with hashes from `python manage.py hash-password`.
"""
import base64, os, shutil, sys, tempfile
from huggingface_hub import HfApi

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SPACE = os.environ.get("REEFPRINT_SPACE", "reefprint")
FILES = ["index.html", "app.js", "server.py", "app_server.py", "manage.py", "requirements-secure.txt"]
DIRS = ["secure", "live", "fonts"]

api = HfApi()
user = api.whoami()["name"]
repo = f"{user}/{SPACE}"
api.create_repo(repo, repo_type="space", space_sdk="docker", exist_ok=True, private=False)
secrets_now = set()
try:
    secrets_now = {s.key for s in api.get_space_secrets(repo)} if hasattr(api, "get_space_secrets") else set()
except Exception:
    secrets_now = set()
if "REEFPRINT_DATA_KEY" not in secrets_now and os.environ.get("REEFPRINT_KEEP_DATA_KEY") != "1":
    api.add_space_secret(repo, "REEFPRINT_DATA_KEY", base64.b64encode(os.urandom(32)).decode(),
                         description="AES-256-GCM data key for uploads and backups (generated once by hf_deploy.py)")

stage = tempfile.mkdtemp(prefix="reefprint_space_")
try:
    for f in FILES:
        shutil.copy2(os.path.join(ROOT, f), os.path.join(stage, f))
    for d in DIRS:
        shutil.copytree(os.path.join(ROOT, d), os.path.join(stage, d), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(os.path.join(HERE, "hf", "Dockerfile"), os.path.join(stage, "Dockerfile"))
    shutil.copy2(os.path.join(HERE, "hf", "README.md"), os.path.join(stage, "README.md"))
    for bad in ("data_secure", "keys", "reefprint.db"):
        assert not any(bad in p for p, _, _ in os.walk(stage)), bad
    info = api.upload_folder(folder_path=stage, repo_id=repo, repo_type="space",
                             commit_message="REEFPRINT Live: deploy from presentation/belt-monitor",
                             delete_patterns=["*.py", "*.html", "*.js", "secure/**", "live/**", "fonts/**"])
    print("uploaded", repo, getattr(info, "oid", "")[:10] if hasattr(info, "oid") else "")
    print("app url:", f"https://{user.lower()}-{SPACE}.hf.space/?guest=1")
finally:
    shutil.rmtree(stage, ignore_errors=True)
