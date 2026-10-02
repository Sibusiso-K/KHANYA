"""Publish REEFPRINT Live as a free, always-on *static* Hugging Face Space (no server; the laptop can be off).

python deploy/hf_static_deploy.py      (run from presentation/belt-monitor; uses the local HF login, never prints a token)

Static mode: every view, the belt replay, the Decisions flow with a browser-sandbox record (SHA-256 hash chain in the
visitor's browser, unsigned), lab-CSV checks and the offline assistant. Sign-in, the shared record, post-quantum signed
checkpoints and photo upload need the secure server (deploy/hf_deploy.py on a Docker Space, which needs HF PRO, or
Azure / any container host).
"""
import os, shutil, tempfile
from huggingface_hub import HfApi

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SPACE = os.environ.get("REEFPRINT_SPACE", "reefprint")
README = """---
title: REEFPRINT Live
emoji: ⛏️
colorFrom: indigo
colorTo: yellow
sdk: static
pinned: true
license: other
short_description: Belt-to-decision mineral characterisation demo (Team Sonar)
---

# REEFPRINT · KHANYA: Live (static demo)

Built by Team Sonar for the Mintek–SCi Grad Hackathon 2026 (Problem 3).

## What it shows

- Replays of real public data:
  - HIDSAG hyperspectral (CC0);
  - Bushveld chromitite assays (Bachmann et al. 2019, CC BY 4.0);
  - a Brazilian iron-ore flotation plant (CC0).
- Not connected to any plant.

## The static build

- The decision record is a browser sandbox: hash-chained in your browser, unsigned.
- The secure server version adds sign-in, roles, one shared record, Ed25519 + ML-DSA-65 signed checkpoints and encrypted photo upload.
"""

api = HfApi()
user = api.whoami()["name"]
repo = f"{user}/{SPACE}"
api.create_repo(repo, repo_type="space", space_sdk="static", exist_ok=True, private=False)
stage = tempfile.mkdtemp(prefix="reefprint_static_")
try:
    for f in ("index.html", "app.js"):
        shutil.copy2(os.path.join(ROOT, f), os.path.join(stage, f))
    for d in ("live", "fonts"):
        shutil.copytree(os.path.join(ROOT, d), os.path.join(stage, d), ignore=shutil.ignore_patterns("__pycache__"))
    with open(os.path.join(stage, "README.md"), "w", encoding="utf-8") as fh:
        fh.write(README)
    api.upload_folder(folder_path=stage, repo_id=repo, repo_type="space", commit_message="REEFPRINT Live static demo",
                      delete_patterns=["*.html", "*.js", "live/**", "fonts/**"])
    print("space:", f"https://huggingface.co/spaces/{repo}")
    print("app url:", f"https://{user.lower()}-{SPACE}.static.hf.space/index.html?guest=1")
finally:
    shutil.rmtree(stage, ignore_errors=True)
