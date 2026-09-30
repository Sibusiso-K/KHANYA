"""Run before rehearsing or presenting: is this laptop about to demo the right thing?

    python -m src.preflight

Every check here is one that has already failed on this project: `asyncua`
missing from the venv the demo runs under (OPC UA showed UNAVAILABLE live), and,
on 29 September, two different S2 checkpoints saved under the same filename.
The dashboard loads whatever sits at that path, so the hash is the only thing
that says the numbers on the slides belong to the model on screen.

Exit code 0 means every check passed.
"""
import hashlib
import sys

from .segmentation import config

# The checkpoint every current S2 number was measured on, reproduced bit-for-bit
# on 2026-09-29 (reports/S2-REPRODUCTION-2026-09-29.md). The Kaggle retrain of
# the same date (fb78727d..., 0.4543 mean IoU) must not be the one on stage.
EXPECTED_S2_SHA256 = "de7135a96541a46dc0981a991cb954186c7cd669ea1c1b33914d1929ae9b1357"
S2_CKPT = config.ROOT / "checkpoints" / "lumenstone_s2_patches" / "best.pt"

# The OPC UA transport is REEFPRINT's code, loaded from a checkout outside this
# repo (ADR-0003: the histories stay unmerged). Pinned by content, not by
# location: sha256 over src/reefprint/integrate/*.py at reefprint commit
# 29254718be5d76b62fabfcdd885f7ce0fe09bbc9 (12 Sept, the last change to that
# folder; identical at origin/reefprint on 30 Sept). Line endings normalised,
# so a Windows checkout matches. See README "Setting up a presenting laptop".
EXPECTED_REEFPRINT_INTEGRATE_SHA256 = "cc3414834373e8a823e61406c41f1844725147858a5ce744e28534f29b8c3041"


def check_checkpoint():
    if not S2_CKPT.exists():
        return False, (f"missing: {S2_CKPT}. It is not in Git; see README "
                       "'Setting up a presenting laptop' for where it comes from")
    digest = hashlib.sha256(S2_CKPT.read_bytes()).hexdigest()
    if digest != EXPECTED_S2_SHA256:
        return False, f"sha256 {digest[:12]}... is not the reported checkpoint {EXPECTED_S2_SHA256[:12]}..."
    return True, f"sha256 {digest[:12]}... matches the reported checkpoint"


def check_data():
    from .segmentation import lumenstone as ls
    _, _, test_ids = ls.split_ids()
    missing = [s for s in test_ids if not (ls.DATA_DIR / "imgs" / "test" / f"{s}.jpg").exists()]
    if len(test_ids) != 12 or missing:
        return False, f"{len(test_ids)} test ids, missing {missing}"
    return True, "12 held-out S2 test sections present"


def check_validated_samples():
    """Only these files may command the simulator; a re-saved copy would silently lose that."""
    import json
    from .segmentation import lumenstone as ls
    manifest = json.loads((config.ROOT / "dashboard" / "validated_samples.json").read_text(encoding="utf-8"))
    expected = manifest["sha256"]
    differ = [stem for stem, digest in expected.items()
              if hashlib.sha256((ls.DATA_DIR / "imgs" / "test" / f"{stem}.jpg").read_bytes()).hexdigest() != digest]
    if len(expected) != 12 or differ:
        return False, f"{len(expected)} manifest entries; files that differ from it: {differ}"
    return True, "12 held-out sections match dashboard/validated_samples.json; only these may command the simulator"


def check_model_loads():
    import torch
    from .segmentation import lumenstone as ls
    from .segmentation.model import build_model
    model = build_model(num_classes=ls.NUM_CLASSES, pretrained=False)
    model.load_state_dict(torch.load(S2_CKPT, map_location="cpu"))
    return True, f"state dict loads strictly into {ls.NUM_CLASSES}-class DeepLabV3"


def reefprint_integrate_sha256(source):
    import hashlib as _hashlib
    folder = source / "reefprint" / "integrate"
    digest = _hashlib.sha256()
    for path in sorted(folder.glob("*.py"), key=lambda p: p.name):
        content = path.read_bytes().replace(bytes([13, 10]), bytes([10]))
        digest.update(path.name.encode() + bytes([0]) + content + bytes([0]))
    return digest.hexdigest()


def check_reefprint_pin():
    from .polarimetry import ensure_reefprint
    source = ensure_reefprint()
    digest = reefprint_integrate_sha256(source)
    if digest != EXPECTED_REEFPRINT_INTEGRATE_SHA256:
        return False, (f"{source}: integrate/ is sha256 {digest[:12]}..., not the pinned "
                       f"{EXPECTED_REEFPRINT_INTEGRATE_SHA256[:12]}... (reefprint 29254718)")
    return True, f"{source}: integrate/ matches the pinned reefprint 29254718"


def check_offline_config():
    text = (config.ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    if "gatherUsageStats = false" not in text:
        return False, ".streamlit/config.toml does not switch off Streamlit's usage statistics"
    return True, "Streamlit usage statistics off; run once with the wifi off to be sure"


def check_live_timing():
    import time

    import torch
    from PIL import Image

    from .segmentation import lumenstone as ls
    from .segmentation.model import build_model
    from .segmentation.patches import multi_field_predict
    model = build_model(num_classes=ls.NUM_CLASSES, pretrained=False)
    model.load_state_dict(torch.load(S2_CKPT, map_location="cpu"))
    model.eval()
    image = Image.open(ls.DATA_DIR / "imgs" / "test" / "test_01.jpg").convert("RGB")
    with torch.no_grad():
        model(torch.zeros(1, 3, 512, 512))  # warm, as the dashboard does before any upload
        start = time.perf_counter()
        multi_field_predict(model, image, "cpu")
        seconds = time.perf_counter() - start
    return True, (f"one six-field pass took {seconds:.1f}s on this machine; a lighting-checked "
                  f"live result runs two, so expect roughly {2 * seconds:.0f}s plus rendering")


def check_opcua():
    import asyncua  # noqa: F401 - the failure this check exists to catch
    from dashboard.control import send_command
    status = send_command("Grind finer", before=0.0)
    if status.state != "applied" or status.after != 1.0:
        return False, f"round trip {status.state}: {status.reason}"
    return True, f"local OPC UA command applied 0 -> 1 ({status.endpoint})"


CHECKS = [
    ("S2 checkpoint", check_checkpoint),
    ("S2 held-out data", check_data),
    ("validated samples", check_validated_samples),
    ("model loads", check_model_loads),
    ("REEFPRINT pinned", check_reefprint_pin),
    ("OPC UA round trip", check_opcua),
    ("offline config", check_offline_config),
    ("live timing (measured here)", check_live_timing),
]


def main():
    failed = 0
    for name, check in CHECKS:
        try:
            ok, detail = check()
        except Exception as exc:  # a preflight reports every failure, it does not stop at one
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        failed += not ok
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    print("\nREADY TO PRESENT" if not failed else f"\n{failed} CHECK(S) FAILED - do not present from this machine")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
