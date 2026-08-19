from pathlib import Path

# ROOT / CKPT_DIR / REPORT_DIR below are shared by every live training
# script in this package (train_lumenstone.py, train_patches.py). The
# IMAGE_DIR / MASK_DIR / IMAGE_SIZE / BATCH_SIZE / EPOCHS / LR below them are
# FeM-specific and only consumed by the superseded data.py / train.py /
# evaluate.py in this same directory - see their module banners.

ROOT = Path(__file__).resolve().parent.parent.parent
IMAGE_DIR = ROOT / "data" / "raw" / "fem" / "FeM_v1" / "Reflected_Light_Microscopy"
MASK_DIR = ROOT / "data" / "raw" / "fem" / "FeM_v1" / "Reference"
CKPT_DIR = ROOT / "checkpoints" / "segmentation"
REPORT_DIR = ROOT / "reports"

IMAGE_SIZE = 512  # downsized from 999x756; full-res optional for final report
BATCH_SIZE = 4
EPOCHS = 10
LR = 1e-3
SEED = 42

# FeM has 81 distinct polished sections, no rotation duplicates, so a plain
# image-level split is legitimate here (unlike the MUMDMC classification data).
VAL_FRACTION = 0.15
TEST_FRACTION = 0.15
