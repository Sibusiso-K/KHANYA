from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
CKPT_DIR = ROOT / "checkpoints"
REPORT_DIR = ROOT / "reports"

# Target phases per the REEFPRINT abstract (Lethabo, submitted 2026-08-04):
# chosen for metallurgical relevance on Bushveld ores, not dataset convenience.
# Base-metal sulphide (BMS) is <1 vol% but carries the PGM economic payload -
# per-class recall on THIS class matters more than aggregate accuracy.
REEFPRINT_CLASSES = [
    "Chromite", "Orthopyroxene", "Plagioclase", "Base_Metal_Sulphide", "Talc_Serpentine",
]

# No public dataset covering REEFPRINT_CLASSES has been found yet (checked
# 2026-08-04 - see DATA-SOURCES.md). MUMDMC2025 is an igneous-silicate dataset
# used only as a DEV PROXY to keep the training pipeline exercised while real
# Bushveld-phase data is sourced. Its classes do NOT match REEFPRINT_CLASSES -
# do not report MUMDMC results as REEFPRINT results.
MUMDMC_DEV_PROXY_CLASSES = ["Biotite", "Hornblende", "Plagioclase", "Potassium_Feldspar", "Quartz"]
MUMDMC_DIR = RAW_DIR / "mumdmc" / "MUMDMC2025_DataSet" / "Cropped_Images"

# CLASSES is what src/data.py and src/train.py actually run against today.
# Switch this to REEFPRINT_CLASSES the moment real Bushveld-phase data lands.
CLASSES = MUMDMC_DEV_PROXY_CLASSES

IMAGE_SIZE = 224
BATCH_SIZE = 16
EPOCHS = 15
LR = 3e-4
WEIGHT_DECAY = 1e-4
SEED = 42

# Fractions of SPECIMENS (not images) per split.
VAL_FRACTION = 0.15
TEST_FRACTION = 0.15

# ImageNet statistics; the backbone is pretrained on it.
NORM_MEAN = (0.485, 0.456, 0.406)
NORM_STD = (0.229, 0.224, 0.225)
