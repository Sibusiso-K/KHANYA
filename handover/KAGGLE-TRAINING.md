# Kaggle S2 retraining: operator checklist

This is the next action for **REEFPRINT (aka KHANYA)**. The user will start a Kaggle run; either Codex Luna or Claude Sonnet can prepare/review code and results. Kaggle's GPU performs the numerical training. The chat model choice does not itself improve accuracy.

## What is already true

- The active application branch is [`codex/khanya-build-plan`](https://github.com/Sibusiso-K/KHANYA/tree/codex/khanya-build-plan). The code is in `src/segmentation/`; main training entry point is `python -m src.segmentation.train_patches` and full-section evaluation is `python -m src.segmentation.train_patches --eval`.
- The three required S2 mineral phases are chalcopyrite, pyrrhotite and pentlandite. The model also predicts background and magnetite. The old patch model had magnetite IoU 0; retain that failure if repeated.
- Official [LumenStone S2 v2](https://imaging.cs.msu.ru/en/research/geology/lumenstone) has 37 publisher training and 12 publisher test image/mask pairs. The repo carves six validation images from the 37 with seed 42. Run a new experiment ID and preserve the published test set until the model is frozen.
- S2 is not staged locally; no active Kaggle connection is visible to this Codex chat yet. The existing project's `reports/REDISTRIBUTION-CONTRADICTION-2026-09-15.md` says S1/S2 Kaggle upload was paused because the publisher's terms grant research use but do not explicitly address redistribution. Do not assume an existing S2 Kaggle mirror.

## Choose the data route before starting

The publisher download is the source of truth. First inspect your Kaggle account for an S2 v2 dataset already legitimately staged by the team. If it exists, check it is private, documented with LumenStone attribution and accessible to your notebook. Do not describe it as publisher-hosted data. If it does not exist, download from the publisher into an authorised research workspace and decide with Sibusiso which Kaggle staging approach is acceptable under the project's existing rights/representation decision. A private Kaggle dataset is still a third-party hosted copy. The existing report lays out the choices. We should not silently create a new S2 mirror while the repository explicitly calls that action paused.

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

## Browser-first run

1. Sign in to [Kaggle](https://www.kaggle.com/), create a **private notebook**, and enable a GPU in its settings. Kaggle documents free GPU access but availability is limited; check the machine assigned to the actual session [Kaggle Notebooks](https://www.kaggle.com/docs/notebooks).
2. Attach the permitted S2 v2 dataset. Confirm the notebook sees the four folders `imgs/train`, `imgs/test`, `masks/train`, `masks/test` under one `S2_v2` root. Count 37 and 12 image/mask pairs. Record the source URL, dataset version and archive hash.
3. Pull the exact Git branch into `/kaggle/working`, or attach a source snapshot. Confirm `git rev-parse HEAD` and `torch.cuda.is_available()` in the notebook. Install only dependencies missing from Kaggle's environment; check compatible PyTorch/torchvision imports before training.
4. Place or link the attached S2 root at `/kaggle/working/KHANYA/data/raw/lumenstone/S2_v2` (substitute the actual clone folder). The training code expects `imgs/train`, `imgs/test`, `masks/train`, `masks/test` immediately underneath that path. `/kaggle/input` is read-only; `/kaggle/working` stores outputs.
5. Run a **smoke training step** with a separate output directory/run ID, record GPU name, first-epoch time and memory use. Then select the full budget from validation results and time available. The code's default is 8 epochs, 64 sampled patches per training epoch, 32 validation patches, 512-pixel native patches, batch 2 and learning rate `2e-4`. Do not assume the old numbers will reproduce on a different environment.
6. Freeze configuration and checkpoint. Run the official 12-image test **once for that frozen candidate**, including per-class IoU, precision/recall, pooled mIoU, confusion matrix and examples. A benchmark set already used during prior development is not a new external validation set.
7. Save `best.pt`, optional `last.pt`, fresh test JSON, training log, manifest (Git SHA, versions, split IDs, settings, seed, source/data/model hashes) and at least one real predicted-mask image under Kaggle outputs. Download these to an ignored local `checkpoints/`/run-artifact folder; share the run URL and non-secret summary with Sibusiso. Keep old reports untouched.
8. Check the downloaded checkpoint locally in the Streamlit pipeline. GPU success on Kaggle does not establish that the offline laptop can load or run it.

**Important code caveat:** the current trainer writes to `checkpoints/lumenstone_s2_patches/best.pt` and a fixed report filename. Before repeated runs, add a run-specific output option or use separate clean run directories, and verify `last.pt` belongs to the same configuration. The benchmark command uses cached predictions; regenerate or hash-key them for the new checkpoint. A smoke run should not consume the held-out test images or overwrite historical report files.

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

The placeholder directory is a **proposed** local notebook folder, not already present in this repository. The browser-first workflow needs no CLI setup. Authentication must be completed through Kaggle's own flow; never paste an API token, `kaggle.json`, or notebook secret into chat or Git. On 29 September this Codex session exposes **no Kaggle MCP tool**. Kaggle's [official remote MCP server](https://www.kaggle.com/docs/mcp) advertises `https://www.kaggle.com/mcp`; if you connect it in Codex, we can test its actual tool permissions then. The CLI and MCP may have different capabilities; do not infer that a connected MCP can manage long-running training.

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
