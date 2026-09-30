# Kaggle S2 retraining: operator checklist

The private **REEFPRINT (aka KHANYA)** Kaggle baseline run is complete. Either Codex Luna or Claude Sonnet can review code and results; Kaggle's GPU performs the numerical training. The chat model choice does not itself improve accuracy.

## What is already true

- The active application branch is [`codex/khanya-build-plan`](https://github.com/Sibusiso-K/KHANYA/tree/codex/khanya-build-plan). The code is in `src/segmentation/`; main training entry point is `python -m src.segmentation.train_patches` and full-section evaluation is `python -m src.segmentation.train_patches --eval`.
- The three required S2 mineral phases are chalcopyrite, pyrrhotite and pentlandite. The model also predicts background and magnetite. The old patch model had magnetite IoU 0; retain that failure if repeated.
- Official [LumenStone S2 v2](https://imaging.cs.msu.ru/en/research/geology/lumenstone) has 37 publisher training and 12 publisher test image/mask pairs. The repo carves six validation images from the 37 with seed 42. Baseline v3 froze the checkpoint, evaluated the 12 publisher test images once, and reported results in [S2-BASELINE-2026-09-29.md](S2-BASELINE-2026-09-29.md). Do not reuse this test split for tuning.
- The user authorized a **private** Kaggle S2 v2 training run. This is an operational instruction, not a legal conclusion about commercial redistribution. The notebook fetches the cited official archive at runtime; no Kaggle dataset mirror was created. Keep the notebook and outputs private.

## Current authenticated run (29 September 2026)

The Kaggle CLI is authenticated as `lethabomh14`. The account has private S1 v1 and S3 v2 datasets, but no S2 v2 dataset. The 418,742,024-byte official publisher archive is staged locally at ignored path `data/lumenstone/kaggle_s2_training_input/S2_v2.zip`; SHA-256 is `64aebd108b3306a8b2e83a945c01f2779bbfd1abeb187b1e2cedcac96cf40c1d`, ZIP CRC passed and the 37/12 paired files were confirmed. A Kaggle dataset upload was stopped at 2% because the observed throughput implied an impractical transfer. The private notebook instead fetches the official archive from the publisher at runtime, validates the same SHA-256 and expected 37/12 pairs, then proceeds. No dataset was created in Kaggle. Kernel v1 could not clone the private GitHub repo without credentials. V2 used an embedded, hash-verified source snapshot and confirmed CUDA on a Tesla T4, but exposed a missing data-link step before training. V3 restored and asserted the trainer path, trained eight epochs, and completed held-out evaluation. The source bundle SHA-256 is `1bf02ae874ca1da61f84e05d7a86d4fd3254b93ae2bea2267c6e8ced31f4c775` and commit is `ac7c058e9a52b9ea1004925085e38071e2892b16`.

**Run completed:** [REEFPRINT S2 v2 private baseline training](https://www.kaggle.com/code/lethabomh14/reefprint-s2-v2-private-baseline-training), private kernel, version 3, GPU and Internet enabled. Status is `COMPLETE`. The measured held-out mIoU is 0.4543; see [full baseline report](S2-BASELINE-2026-09-29.md) for per-class and per-image results, hashes, limitations and next steps.

**Next experiment complete:** [private CE+Dice validation-only run](https://www.kaggle.com/code/lethabomh14/reefprint-s2-ce-dice-validation-only-experiment) completed as run `20260929-193456`. Best validation patch mIoU is 0.5300 at epoch 5 versus the CE baseline 0.4705 on the same patch-validation protocol. Chalcopyrite / pyrrhotite / pentlandite patch IoUs were 0.6001 / 0.7131 / 0.4572; magnetite remained 0.0000. This is one stochastic run, not confirmed general improvement or a test score. The notebook did not evaluate the 12-image test set. The private result ZIP passed CRC and its checkpoint hash was verified; local strict model load succeeded. Full measurements and caveats are in [S2-DICE-VALIDATION-2026-09-29.md](S2-DICE-VALIDATION-2026-09-29.md).

## Candidate prepared 30 September: deterministic full-section selection

The next validation-only notebook is generated from the current `src/**/*.py` on the app branch. It hashes a deterministic source ZIP, asserts required modules exist, preserves the verified S2 archive and `data/raw/lumenstone/S2_v2` link, records the source revision/run ID and file hashes, fixes seed 42, and writes a separate checkpoint directory. The trainer uses whole-section foreground macro IoU on the six validation sections to select `best.pt`; balanced-patch results remain diagnostic. It stores per-epoch full-section metrics and a private run bundle containing the checkpoint, validation history, log and manifest. The 12 publisher test sections remain sealed. Static notebook code-cell parsing and checkpoint-path consistency were inspected locally. Version 2 was submitted to the existing private kernel `lethabomh14/reefprint-s2-ce-dice-validation-only-experiment` on 30 September; Kaggle reported it running. No new score is available or claimed yet.

Generated files are `training/kaggle_s2/kaggle_s2_dice_validation.ipynb` and `training/kaggle_s2/kernel-metadata-dice-validation.json`; generator: `training/kaggle_s2/make_dice_validation_notebook.py`. The previous 0.5300 balanced-patch score cannot be compared directly to the new whole-section selection score. After this candidate runs, repeat the leading recipe across seeds before deciding whether it improves. Any later test-set run is a frozen regression check on a previously examined benchmark, not a fresh external validation.

## Data and privacy decision

The S2 v2 source is the [LumenStone publisher page](https://imaging.cs.msu.ru/en/research/geology/lumenstone). The active private notebook downloads the official archive over Kaggle Internet, checks the known SHA-256 and ZIP integrity, then requires exactly 37 train and 12 test paired image/mask files before training. This avoids an extra persistent Kaggle dataset mirror. The held-out test split has now been evaluated once and must remain frozen for future tuning. The user authorized this private run; that instruction does not establish commercial redistribution rights. Do not publish the source data, notebook outputs, or checkpoint.

Linking Kaggle to Codex is **optional for training**. You can run an interactive Kaggle notebook in the browser, attach data and inspect outputs without MCP or CLI. An MCP connection is useful for an agent to inspect resources; the CLI is the reliable path for scripted notebook versioning, status and output retrieval. Neither connection grants dataset rights, attaches the dataset automatically, chooses a GPU or validates the model.

## Authenticate the Kaggle CLI on this Windows computer

The installed CLI was checked in this workspace: **Kaggle CLI 2.2.4**, which supports browser OAuth. Recommended: use the CLI login; it opens a Kaggle browser approval flow and stores the resulting CLI credential locally. You do not copy a token into Codex or a source file.

```powershell
kaggle auth login
kaggle --version
```

Finish the approval in the browser opened by the CLI, then return to the same terminal. Do not run `kaggle auth print-access-token` just to check login; it prints a secret. If login reports that credentials already exist, continue with that account or deliberately use `kaggle auth login --force` to switch accounts.

If you specifically want to use the named **Access token** in the screenshot, choose **Generate New Token** in the upper “API Tokens” section. Do not use **Create Legacy API Key**; that is a separate compatibility method and Kaggle recommends access tokens. In PowerShell, enter the token through a hidden prompt for this terminal session only:

```powershell
$kaggleSecret = Read-Host 'Paste the Kaggle access token here' -AsSecureString
$env:KAGGLE_API_TOKEN = [System.Net.NetworkCredential]::new('', $kaggleSecret).Password
Remove-Variable kaggleSecret
kaggle --version
```

Paste it only at the PowerShell prompt that appears after the first line. That command does not echo the token or place the token text in the command-history line. The environment variable lasts only for that PowerShell session; close the terminal when finished. Do not save the token in a notebook, `.env` file, chat message, repository file, screenshot, or Kaggle dataset. For routine use, browser OAuth login is simpler than keeping a long-lived token in the environment.

The CLI also supports a token file at `%USERPROFILE%\.kaggle\access_token`, but that stores a reusable credential on disk. Prefer OAuth or the temporary session variable above. Legacy `kaggle.json` credentials are only needed for older clients that do not support the current token/OAuth login methods.

## Optional private dataset upload route (not used)

If the notebook cannot reach the publisher, create a private dataset from the staged official archive:

```powershell
kaggle datasets create -p .\data\lumenstone\kaggle_s2_training_input --dir-mode skip
```

The folder includes `dataset-metadata.json` with the owner's Kaggle slug and source citation. The CLI creates privately by default; **never add `--public`**. Then attach its returned slug in the private training notebook. This fallback was not used for the active run.

The checked-in baseline notebook at `training/kaggle_s2/kaggle_s2_train.ipynb` fetches and verifies the publisher archive at runtime. The validation-only candidate is `training/kaggle_s2/kaggle_s2_dice_validation.ipynb`; its saved metadata is `kernel-metadata-dice-validation.json`. The generic `kernel-metadata.json` is the Kaggle CLI's active metadata and must be restored to the baseline after pushing the candidate. Review the actual kernel `id`, `title`, privacy, GPU and Internet settings before a future push. Check `kaggle kernels status <username>/<slug>` until complete; pull output only after success. Never commit Kaggle credentials or downloaded data.

## Browser-first run

The repository contains [`training/kaggle_s2_train.ipynb`](../training/kaggle_s2_train.ipynb), a private-run template. It fetches the source archive from LumenStone at runtime, clones the public code branch into `/kaggle/working`, and never includes Kaggle credentials. The active run is already launched at [Kaggle](https://www.kaggle.com/code/lethabomh14/reefprint-s2-v2-private-baseline-training).

1. Sign in to [Kaggle](https://www.kaggle.com/), upload the template as a **private notebook**, and enable a GPU and Internet in its settings. Kaggle documents free GPU access but availability is limited; check the machine assigned to the actual session [Kaggle Notebooks](https://www.kaggle.com/docs/notebooks).
2. Allow the notebook to download the official S2 v2 archive. Confirm its SHA-256, ZIP CRC and exactly 37/12 paired files. Stop if any check differs.
3. Pull the exact Git branch into `/kaggle/working`, or attach a source snapshot. Confirm `git rev-parse HEAD` and `torch.cuda.is_available()` in the notebook. Install only dependencies missing from Kaggle's environment; check compatible PyTorch/torchvision imports before training.
4. The notebook links the verified extracted `S2_v2` root at the project snapshot's `data/raw/lumenstone/S2_v2` path. The training code expects `imgs/train`, `imgs/test`, `masks/train`, `masks/test` immediately underneath it.
5. Run the controlled baseline exactly as configured; record the GPU, epoch times, memory use and validation trend. Use validation only to plan any later candidate. The code's default is 8 epochs, 64 sampled patches per training epoch, 32 validation patches, 512-pixel native patches, batch 2 and learning rate `2e-4`. Do not assume the old numbers will reproduce on a different environment.
6. Freeze configuration and checkpoint. Run the official 12-image test **once for that frozen candidate**, including per-class IoU, precision/recall, pooled mIoU, confusion matrix and examples. A benchmark set already used during prior development is not a new external validation set.
7. Save `best.pt`, optional `last.pt`, fresh test JSON, training log, manifest (Git SHA, versions, split IDs, settings, seed, source/data/model hashes) and at least one real predicted-mask image under Kaggle outputs. Download these to an ignored local `checkpoints/`/run-artifact folder; share the run URL and non-secret summary with Sibusiso. Keep old reports untouched.
8. Check the downloaded checkpoint locally in the Streamlit pipeline. GPU success on Kaggle does not establish that the offline laptop can load or run it.

**Code caveat:** older reports use fixed output paths. The current candidate creates a run-specific checkpoint directory and validation history; do not reuse old benchmark caches or overwrite historical report files. The held-out test split must not be used for smoke checks or tuning.

## Optional CLI and MCP connection

The [official Kaggle CLI](https://github.com/Kaggle/kaggle-cli) documents `kaggle auth login`, `kaggle kernels init`, `push`, `status`, `pull`, and `output`. Its [kernel metadata](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels_metadata.md) includes `is_private`, `enable_gpu`, `dataset_sources`, and `code_file`. Use the actual notebook/dataset slug and inspect the generated metadata before pushing a run. Typical workflow after authentication:

```powershell
kaggle --version
kaggle kernels init -p .\training\kaggle_s2
# Edit kernel-metadata.json: your notebook ID, private=true, GPU=true,
# the approved S2 dataset source, and the real code_file.
kaggle kernels push -p .\training\kaggle_s2
kaggle kernels status YOUR_USERNAME/YOUR_NOTEBOOK_SLUG
kaggle kernels output YOUR_USERNAME/YOUR_NOTEBOOK_SLUG -p .\training\outputs
```

The CLI notebook folder `training/kaggle_s2` is now present in this repository. The browser-first workflow needs no CLI setup. Authentication must be completed through Kaggle's own flow; never paste an API token, `kaggle.json`, or notebook secret into chat or Git. On 29 September this Codex session exposes **no Kaggle MCP tool**. Kaggle's [official remote MCP server](https://www.kaggle.com/docs/mcp) advertises `https://www.kaggle.com/mcp`; if you connect it in Codex, we can test its actual tool permissions then. The CLI and MCP may have different capabilities; do not infer that a connected MCP can manage long-running training.

## Review the output before changing the build

| Observed result | Next action |
|---|---|
| Import/GPU/paths fail | Fix setup; do not judge model quality yet. |
| Training loss/validation unstable | Check labels, transforms, learning rate, class sampling, pretrained-weight load and reproducibility. Use validation, not test, to decide. |
| Three sulphides detected with usable per-class scores | Freeze run, evaluate all five classes and test local inference. Then implement simulator control path. |
| One required sulphide collapses | Inspect confusion and rare-pixel distribution; adjust sampling/training budget on train/validation only. Record failed run. |
| Magnetite remains at IoU 0 | Disclose it; do not claim a five-phase model works. Three sulphides can still meet the explicit minimum if they work. |
| Accuracy good but lighting changes advice | Add/report quality screening and refusal; do not claim robustness from mIoU alone. |
| Kaggle GPU run succeeds but laptop fails | Diagnose PyTorch version, checkpoint format, device mapping and offline dependencies before UI work. |

Switching chat models is most useful at a **review boundary**, not in the middle of an unobserved run. Use Luna for repeatable setup, scripts, imports and integration tickets. Use Sonnet if you want a deeper second read of failed training, evaluation design, scientific claims or trade-offs. Give either model the same run manifest and logs, and require it to ground changes in measured validation evidence. The GPU run can continue independently while you switch models. Keep one branch owner at a time to avoid conflicting edits.
