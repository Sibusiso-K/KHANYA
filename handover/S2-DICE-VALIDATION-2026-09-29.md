# S2 CE+Dice validation-only experiment — 29 September 2026

**Status: launched on Kaggle; outcome pending.** This run is an exploratory training comparison. It deliberately omits all test evaluation so the existing 12-image test result remains frozen.

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

At the time this report was written, Kaggle returned `KernelWorkerStatus.RUNNING`; the CLI logs were not yet available. Do not treat the experiment as completed until status is complete and the private output bundle has been downloaded and hash-checked. Do not launch duplicate runs or inspect/use test masks.

After completion:

1. Retrieve only the private `khanya-s2-dice-validation-*.zip` output bundle. Verify its ZIP CRC, checkpoint hash, source/data hashes, manifest, and full training log.
2. Record the observed best validation patch mIoU and per-class validation patch metrics, then compare only to the baseline's comparable validation patch metric (`0.4705`). State that these are small fixed validation patches; report the stochastic-run caveat.
3. If no candidate checkpoint was saved, record the failure. If the candidate appears better, repeat the run with new run IDs/seeds using validation only. Do not evaluate this exploratory checkpoint on the test split.
4. Keep model weights and raw data in ignored local storage; commit this report and any summary, not the large artifacts.

## Repository artifact

The source notebook is `training/kaggle_s2/kaggle_s2_dice_validation.ipynb`; its private Kaggle CLI metadata is `training/kaggle_s2/kernel-metadata-dice-validation.json`. `make_dice_validation_notebook.py` regenerates the notebook from the baseline template while removing test-evaluation cells and replacing the training/manifest cells. The default `kernel-metadata.json` may be temporarily pointed at the experiment when pushing; restore it to the baseline metadata after the upload so a later ordinary push cannot accidentally replace the baseline notebook.
