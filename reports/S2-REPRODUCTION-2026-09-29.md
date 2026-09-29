# S2 checkpoint reproduced, 29 September 2026

**Why this exists.** The `codex/khanya-build-plan` branch (three commits, 29
September) concludes that the S2 checkpoint and data are missing and plans a
Kaggle retrain two days before submission. Its own evidence register labels the
historical S2 numbers "not replicated here; checkpoint absent". That audit was
run on a different machine. On this machine both exist, and the held-out result
reproduces exactly.

## What was checked

| Item | Observed |
|---|---|
| Checkpoint | `checkpoints/lumenstone_s2_patches/best.pt`, 168,313,587 bytes, modified 2026-08-16 |
| Checkpoint sha256 | `de7135a96541a46dc0981a991cb954186c7cd669ea1c1b33914d1929ae9b1357` |
| Data | `data/raw/lumenstone/S2_v2`: 37 train, 12 test images |
| Command | `python -m src.segmentation.train_patches --eval` (fresh full-section native-resolution inference, not cached predictions) |

## Result

| Class | IoU | Recall | Precision |
|---|---:|---:|---:|
| background | 0.8709 | 0.9198 | 0.9425 |
| chalcopyrite | 0.5755 | 0.7161 | 0.7456 |
| magnetite | 0.0000 | 0.0000 | n/a |
| pyrrhotite | 0.8695 | 0.9343 | 0.9261 |
| pentlandite | 0.5468 | 0.7420 | 0.6752 |
| **mean** | **0.5725** | | |

Pixel accuracy 0.8914. `reports/lumenstone_s2_patches_test_metrics.json` came
out **bit-for-bit identical** to the committed version (mean IoU
0.5725330422082483 before and after), so the file is unchanged in git.

## What follows

- **Retraining is not needed to have a working three-phase model.** It exists
  and produces the reported numbers.
- A new checkpoint would make every current S2 number historical: this table,
  the illumination finding (8/12), the decision-gap severity table, the 0.335
  conformal band, the baselines and `BACKUP-DEMO-SCRIPT.md`'s expected values.
- **The actual gap is distribution**, raised on issue #5 on 15 September and
  never closed: `checkpoints/` is gitignored, so no other machine has this file.
  Moving this checkpoint (and its sha256) to whichever laptop presents is the
  fix, not training a new one.
