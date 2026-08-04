from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
IMAGE_DIR = ROOT / "data" / "raw" / "fem" / "FeM_v1" / "Reflected_Light_Microscopy"
MASK_DIR = ROOT / "data" / "raw" / "fem" / "FeM_v1" / "Reference"
CKPT_DIR = ROOT / "checkpoints" / "segmentation"
REPORT_DIR = ROOT / "reports"

IMAGE_SIZE = 512  # downsized from 999x756; full-res optional for final report
BATCH_SIZE = 4
EPOCHS = 25
LR = 1e-3
SEED = 42

# FeM has 81 distinct polished sections, no rotation duplicates, so a plain
# image-level split is legitimate here (unlike the MUMDMC classification data).
VAL_FRACTION = 0.15
TEST_FRACTION = 0.15
