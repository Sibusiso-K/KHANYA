# S2 CE+Dice validation-only experiment — 29 September 2026

**Status: complete; exploratory validation result recorded.** This run deliberately omitted all test evaluation so the existing 12-image test result remains frozen.

## Why this experiment

The completed CE baseline scored 0.4543 pooled native-resolution test mIoU, but magnetite IoU was 0. The training code already supports `--loss dice`, which adds a per-class soft Dice term to cross-entropy. That objective may give rare magnetite patches more useful gradient signal. This is a hypothesis, not an established improvement. The baseline report contains its full metrics and limitations.

## Run design and safeguards

- Kaggle private kernel: [REEFPRINT S2 CE+Dice validation-only experiment](https://www.kaggle.com/code/lethabomh14/reefprint-s2-ce-dice-validation-only-experiment).
- Code branch: `codex/khanya-build-plan`; source snapshot commit is recorded in the Kaggle notebook manifest.
- Dataset: official LumenStone S2 v2 archive; verified SHA-256 `64aebd108b3306a8b2e83a945c01f2779bbfd1abeb187b1e2cedcac96cf40c1d`.
- Training loss: cross-entropy + soft multiclass Dice, default Dice coefficient 1.0.
- Checkpoint selection: the same fixed six validation images and balanced 512-pixel validation patches used by baseline. The best validation patch mIoU is not whole-section accuracy and cannot be compared directly to test mIoU.
- Budget: 8 epochs, 64 sampled train patches/epoch, 32 validation patches/epoch, 512-pixel patches, batch size 2, learning rate 0.0002, seed 42 for Torch and the split.
- Candidate checkpoint path is separate: `checkpoints/lumenstone_s2_patches_dice/best.pt`.
- Notebook contains no test evaluation cell and records `test_evaluation_performed: false`, `test_metrics: null`.
- Patch centres and augmentations use Python's `random.Random(None)` for training; therefore this is one stochastic exploratory run, not a fully reproducible paired comparison. If it appears promising, run at least two more seeds on train/validation before considering one frozen candidate for a single test evaluation.

## Live status and next action

Kaggle run [REEFPRINT S2 CE+Dice validation-only experiment](https://www.kaggle.com/code/lethabomh14/reefprint-s2-ce-dice-validation-only-experiment) completed with run ID `20260929-193456` on a Tesla T4 (PyTorch 2.10.0+cu128, torchvision 0.25.0+cu128, CUDA 12.8). The publisher ZIP hash and source bundle hash match the baseline verification. The private result ZIP passed CRC verification. The checkpoint hash in the manifest was independently verified: `cb5ccc21753b8036149a0e203b32c6c17ec0549a9f78ff66e0391c08ee28e26a` (168,318,771 bytes). It is stored locally at the gitignored `checkpoints/lumenstone_s2_patches_dice/best.pt` and strict-loaded with all 370 keys matching.

Best validation result occurred at epoch 5:

| Phase | Validation patch IoU | Recall | Precision |
|---|---:|---:|---:|
| Background | 0.8795 | 0.9600 | 0.9129 |
| Chalcopyrite | 0.6001 | 0.9089 | 0.6386 |
| Magnetite | 0.0000 | 0.0000 | undefined |
| Pyrrhotite | 0.7131 | 0.7531 | 0.9307 |
| Pentlandite | 0.4572 | 0.6393 | 0.6162 |

Best balanced-patch validation mIoU was `0.5300`, versus the CE baseline's `0.4705` on the same fixed validation patch protocol (+0.0595 absolute). Validation pixel accuracy was `0.8428`. These are patch-level scores, not full-section measurements. Training patch sampling uses unseeded Python randomness, so this one-run gain is promising but not a controlled multi-seed result. Magnetite remains entirely missed. The manifest explicitly states `test_evaluation_performed: false` and `test_metrics: null`; the frozen baseline test score remains the only test result.

The local private bundle and extracted checkpoint are in the ignored `checkpoints/kaggle_runs/s2_dice_20260929/` and `checkpoints/lumenstone_s2_patches_dice/` paths. Do not commit either. No test masks or images were opened for this run or the post-run verification.

After completion:

1. Repeat CE+Dice with at least two independent training seeds on train/validation only; improve seed control first if possible so Python patch sampling, Torch and loader workers are all recorded and reproducible.
2. Investigate magnetite label frequency and validation coverage; do not claim the Dice loss fixed it.
3. If repeated runs support the change, select and freeze one candidate using validation only, then decide whether a single full-section evaluation on the frozen 12-image test set is justified. Never repeatedly tune against that test split.
4. Connect the candidate to an actual dashboard training-image inference and render the accuracy report; keep test and validation provenance visible.

## Repository artifact

The source notebook is `training/kaggle_s2/kaggle_s2_dice_validation.ipynb`; its private Kaggle CLI metadata is `training/kaggle_s2/kernel-metadata-dice-validation.json`. `make_dice_validation_notebook.py` regenerates the notebook from the baseline template while removing test-evaluation cells and replacing the training/manifest cells. The default `kernel-metadata.json` may be temporarily pointed at the experiment when pushing; restore it to the baseline metadata after the upload so a later ordinary push cannot accidentally replace the baseline notebook.
