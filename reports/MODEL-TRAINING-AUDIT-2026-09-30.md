# Model training audit and matched validation control

Audited 30 September 2026. This file concerns model training only. The live application checkpoint has not changed.

## Verified newer result

The authenticated Kaggle CLI lists `lethabomh14/reefprint-s2-ce-dice-validation-only-experiment`, last run 2026-09-29 23:58:30 UTC, with COMPLETE status. Source and small result artifacts were retrieved to `training/audit_ce_dice_20260930/`. Data and checkpoint output download was cancelled before any data bytes were saved; no checkpoint was independently rehashed locally.

The completed run manifest identifies seed 42, eight epochs of 64 native-resolution 512px training patches, batch two, AdamW learning rate 0.0002, CE plus soft multiclass Dice, Tesla T4, Torch 2.10.0+cu128 and Torchvision 0.25.0+cu128. It uses 31 training sections, six validation sections carved from the publisher training folder, and 12 publisher test sections. The original manifest's `train_pairs: 37` is a misleading source-folder count: its exact training ID list contains **31**, excluding six validation IDs. The new control corrects this denominator.

Checkpoint selection is by full-section validation foreground macro IoU; balanced patch validation is diagnostic only. All 35 embedded Python source module hashes were checked against the downloaded manifest; the bundle SHA is `22a6117265bd6c6dd09c2fa4b3b9b28ab1bb60c70ee84cd364bae33db6a990fc`. Source provenance records commit `f463864d8c81ec77b8ed0381781ba37c81ca4a61` from `codex/khanya-build-plan`, with actual embedded hashes controlling the run. This differs from the older application checkout's trainer.

Best epoch is **8**, validation foreground macro IoU **0.4316483900**, pooled five-class validation mIoU **0.5241323767**, validation pixel accuracy **0.8511884310**.

| Phase | Validation IoU | Recall | Precision |
|---|---:|---:|---:|
| background | 0.8940683232 | 0.9142215509 | 0.9759372994 |
| chalcopyrite | 0.5930224185 | 0.8836779735 | 0.6432345184 |
| magnetite | **0** | **0** | undefined: no predictions |
| pyrrhotite | 0.7936801293 | 0.8414150649 | 0.9332891081 |
| pentlandite | 0.3398910123 | 0.5438716844 | 0.4754093143 |

At the selected epoch there are **105,250 true magnetite validation pixels**, zero true-positive magnetite pixels and zero false-positive magnetite pixels: the class is never predicted. It remains a failed channel, including in this newer experiment. The run does not solve rare-phase identification.

Manifest-reported checkpoint SHA: `43de2fabe92fc6149ecbe36f21488636923738495f6658a0f4472148b42d0d21`. This is a reported artifact identity, not an independently verified local checkpoint hash. No held-out test evaluation was performed by this run. Its validation metrics cannot be ranked against the existing .4543 or historical .5725 **test** mIoUs. No accuracy gain or deployment is claimed.

## Next experiment launched

[Private matched CE validation control](https://www.kaggle.com/code/lethabomh14/reefprint-s2-matched-ce-validation-control), version 1, was successfully pushed and confirmed RUNNING. Run ID: `20260930-s2-seed42-fullval-ce-control-v1`.

The scientifically useful missing comparator is CE with the same fixed source, initialization seed, split, patch stream, budget and native-resolution validation as the completed CE+Dice run. **Only the loss changes**. Adding a new architecture, larger budget or focal variant now would confound the comparison. This is an exploratory single-seed control, not a stability study.

Local generator: `training/prepare_matched_ce_control.py`. Prepared notebook, private Kaggle metadata and preregistered protocol: `training/matched_ce_control_20260930/`. Preparation verified notebook code syntax, all 35 source hashes, disjoint 31/6/12 image ID sets, the CE training path, fresh run/checkpoint directories and no `--eval` command. The notebook explicitly packages `test_evaluation_performed: false` and `test_metrics: null`.

The publisher ZIP is downloaded by the same verified notebook mechanism, SHA `64aebd108b3306a8b2e83a945c01f2779bbfd1abeb187b1e2cedcac96cf40c1d`, 418,742,024 bytes. Presence/CRC checks include the publisher test archive entries, but training/checkpoint selection do not decode test images or labels. The split remains image-level; no specimen/locality manifest exists to establish locality-disjoint generalization. Do not silently upgrade image counts to locality counts.

## Local audit and scientific limits

`training/audit_validation_result.py` independently recomputes the saved IoUs from TP/FP/FN, checks best-epoch selection, hashes the existing local publisher archive, and scans **training and validation masks only**. It verifies that actual validation class counts match the recorded TP+FN. It computes a train-selected majority-class baseline on validation and an explicitly exploratory six-section bootstrap of the selected checkpoint. Output: `training/ce_dice_validation_audit_20260930.json`.

The local audit completed successfully: archive SHA and all five validation class pixel counts match. The training-selected majority class is pyrrhotite, with validation foreground macro IoU **0.0792558961**, five-class mIoU **0.0634047169**, and pixel accuracy **0.3170235844**. The exploratory section bootstrap percentile interval for foreground macro IoU is **[0.3213940860, 0.5424030541]**, using 10,000 draws and seed 20260930.

The bootstrap is conditional on a checkpoint already chosen using these six sections; it does not correct for model selection, and sections are not proven independent localities. It is not external accuracy uncertainty. A metadata-only baseline is explicitly unavailable because no verified acquisition/specimen/locality metadata table is present. Stronger-baseline uplift must not be claimed until that gap is resolved or a defensible baseline protocol is approved with real metadata.

Other inherited limits: one seed; very small eight-by-64 budget; best Dice epoch is the last epoch, so convergence is not established; exact cross-device reproducibility has not been demonstrated. The trainer seeds Python/NumPy/Torch/CUDA and fixes patch streams, but deterministic flags alone are not a reproducibility measurement. Historical publisher test sets have already been examined; they are final regression references, not fresh blind tuning sets. LumenStone is a Norilsk reflected-light analogue, not South African transfer evidence. Dataset/checkpoint publication rights remain unresolved. No raw imagery or model weights should be committed.

## Runnable continuation

From `C:/Users/USER/Desktop/REEFPRINT`, using existing Kaggle authentication without printing credentials:

```powershell
kaggle kernels status lethabomh14/reefprint-s2-matched-ce-validation-control
kaggle kernels output lethabomh14/reefprint-s2-matched-ce-validation-control -p training/matched_ce_control_20260930/results --file-pattern '.*(manifest.*json|validation_history.json|training.log|\.log)$'
```

If Windows CLI output raises a `charmap` encoding error after files download, set `$env:PYTHONIOENCODING='utf-8'` for that command and retry the small artifact retrieval. Do not assume an exit code after a log encoding issue means no artifacts were downloaded: inspect existing files. Default `kernels output` downloads dataset/checkpoint bundles; use the filter above.

When COMPLETE, first verify source/dataset hashes, exact split IDs, budget and absence of test metrics. Compare CE versus CE+Dice **validation** foreground macro IoU and every mineral, plus per-section counts and false positives. Report the comparison as exploratory; do not compare it with deployed test scores. If CE and Dice both retain dead magnetite, preregister a bounded training-only rare-patch occupancy diagnostic and budget experiment, not a test-optimized threshold. Replicate candidate and control over matched seeds before any stable improvement claim; preserve the image split independently of training seed. Resume state should additionally capture RNG states for exact optimizer/dropout continuation before relying on resumed comparisons.

Neither experiment authorizes automatic model promotion. Promotion needs a concrete fixed candidate, verified checkpoint bytes, frozen preprocessing/evaluation, baseline and uncertainty reporting, deployment latency/refusal checks and explicitly final regression evaluation. The current serving checkpoint stays bound to its own .4543 report; the historical stronger .5725 model remains a distinct artifact.

## Operational status

No AGENTS.md was found in either project checkout. CLAUDE.md, WORKBOARD.md, CONTEXT.md and current handovers were read. Authenticated Kaggle access initially hit Windows sandbox network denial; the authorized CLI escalation succeeded. No credentials were printed. No UI/API edits, commits, pushes, checkpoint promotion or automatic scheduling were performed. The parent agent should add a concise link to this handover in shared CONTEXT/BUILDLOG to avoid conflicting simultaneous edits.
