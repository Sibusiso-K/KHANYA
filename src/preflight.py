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


def check_checkpoint():
    if not S2_CKPT.exists():
        return False, f"missing: {S2_CKPT}"
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


def check_model_loads():
    import torch
    from .segmentation import lumenstone as ls
    from .segmentation.model import build_model
    model = build_model(num_classes=ls.NUM_CLASSES, pretrained=False)
    model.load_state_dict(torch.load(S2_CKPT, map_location="cpu"))
    return True, f"state dict loads strictly into {ls.NUM_CLASSES}-class DeepLabV3"


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
    ("model loads", check_model_loads),
    ("OPC UA round trip", check_opcua),
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
