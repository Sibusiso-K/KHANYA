from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
CKPT_DIR = ROOT / "checkpoints"
REPORT_DIR = ROOT / "reports"

# Must stay >= 3 to satisfy the brief. Edit to match the dataset actually used.
CLASSES = ["hematite", "magnetite", "quartz", "goethite"]

IMAGE_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 20
LR = 3e-4
WEIGHT_DECAY = 1e-4
SEED = 42

# Fractions of SPECIMENS (not images) per split.
VAL_FRACTION = 0.15
TEST_FRACTION = 0.15

# ImageNet statistics; the backbone is pretrained on it.
NORM_MEAN = (0.485, 0.456, 0.406)
NORM_STD = (0.229, 0.224, 0.225)
