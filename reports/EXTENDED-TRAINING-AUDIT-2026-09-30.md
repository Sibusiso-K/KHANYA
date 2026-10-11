# Extended training completion audit

Prepared 1 October 2026 UTC for the two 30 September runs. Both authenticated Kaggle status checks returned **COMPLETE**. This audit retrieved notebook source, metadata, validation manifests, validation histories and logs only. It did not download checkpoint/data bundles, evaluate test images, train, change services, replace the application checkpoint or publish anything.

## Outcome

The native extended CE+Dice run selects **epoch 12**, with full-section validation foreground macro IoU **0.6467023252**. Magnetite is now predicted: IoU **0.4094622211**, recall **0.6948408551**, precision **0.4992388403**. The earlier matched CE and short Dice checkpoints predicted no magnetite.

The small-grain run also selects epoch 12, with foreground macro IoU **0.5332567828**. It recovers some magnetite but substantially reduces pentlandite recall. The native extended checkpoint is the stronger candidate on the declared validation metric. This is a selected, single-seed validation result; it is not a deployed accuracy claim or a demonstrated stable improvement.

| Run | Training budget | Selected epoch | Validation foreground macro IoU | Five-class mIoU | Pixel accuracy |
|---|---|---:|---:|---:|---:|
| Matched CE control | 8 × 64 patches | 8 | 0.4098991445 | 0.5098732863 | 0.8512649276 |
| Short CE+Dice | 8 × 64 patches | 8 | 0.4316483900 | 0.5241323767 | 0.8511884310 |
| Native extended CE+Dice | 24 × 192 patches | 12 | **0.6467023252** | **0.7036325294** | **0.9201153955** |
| Small-grain CE+Dice | 24 × 192 patches | 12 | 0.5332567828 | 0.6122718852 | 0.8943126775 |

Native foreground macro IoU exceeds short Dice by **0.2150539351** and matched CE by **0.2368031806**. Small-grain exceeds short Dice by 0.1016083927 but is 0.1134455424 below the native run. The extended runs have nine times the nominal training patch budget of the short runs (4,608 versus 512); these comparisons do not isolate a loss effect. Changing `patches_per_epoch` also changes the deterministic patch stream, because the sampler's seed includes epoch × length.

## Per-class results and regressions

IoU and recall below are pooled over the same six complete native-resolution validation sections. Background remains included in the five-class mIoU, and excluded from foreground macro IoU.

| Phase | CE IoU | Short Dice IoU | Native extended IoU | Small-grain IoU |
|---|---:|---:|---:|---:|
| Background | 0.9097698531 | 0.8940683232 | 0.9313533464 | 0.9283322947 |
| Chalcopyrite | 0.5418425255 | 0.5930224185 | 0.7618357666 | 0.7314028845 |
| Magnetite | 0 | 0 | **0.4094622211** | 0.2990660246 |
| Pyrrhotite | 0.7803528406 | 0.7936801293 | 0.8879552116 | 0.8380949422 |
| Pentlandite | 0.3174012121 | 0.3398910123 | 0.5275561015 | **0.2644632799** |

| Phase | CE recall | Short Dice recall | Native extended recall | Small-grain recall |
|---|---:|---:|---:|---:|
| Background | 0.9622227570 | 0.9142215509 | 0.9705543487 | 0.9680239081 |
| Chalcopyrite | 0.9071634469 | 0.8836779735 | 0.8723272574 | 0.8707116349 |
| Magnetite | 0 | 0 | **0.6948408551** | 0.3516959620 |
| Pyrrhotite | 0.8038377209 | 0.8414150649 | 0.9558916040 | 0.9771103812 |
| Pentlandite | 0.4019417606 | 0.5438716844 | 0.6189640177 | **0.2881014845** |

Native improves every pooled common-phase IoU versus both short controls, but its chalcopyrite recall drops by 0.0113507161 against short Dice and 0.0348361895 against CE. The common-phase performance is uneven across sections:

| Native chalcopyrite | Short Dice IoU → native | Short Dice recall → native |
|---|---|---|
| `train_21` | 0.5381400796 → **0.3500366293** | 0.8815276318 → **0.3518562480** |
| `train_27` | 0.4553594686 → **0.2588680104** | 0.8753608983 → **0.2667327204** |

The small-grain variant substantially regresses pooled pentlandite against both controls: its IoU falls 0.0754277324 and recall falls 0.2557701999 against short Dice. On `train_21`, pentlandite IoU falls from 0.4831413157 to **0.0289461362**, and recall from 0.6144737759 to **0.0294297507**. Small-grain chalcopyrite on `train_27` also falls to IoU 0.0475179893 and recall 0.0476297014. Do not choose that variant based on foreground macro IoU alone.

Magnetite has **105,250 true validation pixels**, present in just `train_21` (75,644) and `train_23` (29,606). Native produces **73,132 TP / 73,355 FP / 32,118 FN**. Small-grain produces **37,016 TP / 18,522 FP / 68,234 FN**, trading lower recall for higher precision (0.6664986136). Native's magnetite false positives include 24,302 pixels on three sections with no true magnetite (`train_06`, `train_10`, `train_13`). Nonzero rare-phase detection does not imply reliable rare-phase identification.

Both validation histories fluctuate considerably. Native's epoch-24 score is 0.5470034538; small-grain's is 0.4663916258. Their selected epoch 12 exceeds their final epoch. Twenty-four epochs therefore do not establish convergence or stable generalization.

## Source, split and protocol verification

The downloaded remote notebooks, manifests and standalone histories passed the offline checks in [audit_extended_validation.py](C:/Users/USER/Desktop/REEFPRINT/training/audit_extended_20261001/audit_extended_validation.py). Structured results, exact per-section counts, histories, deltas and conditional intervals are in [extended_validation_audit.json](C:/Users/USER/Desktop/REEFPRINT/training/audit_extended_20261001/extended_validation_audit.json).

Verified facts:

- All **35 embedded Python module hashes** match each run's manifest; each embedded ZIP SHA and CRC match. Remote notebook execution code equals the prepared notebook's syntax tree. Notebook cells and the seven directly used segmentation modules parse locally.
- Native's module hashes exactly match the matched CE control's source. The two extended source trees differ only in `src/segmentation/patches.py`: small-grain introduces a 50% training-only 256px crop, bilinear RGB upsampling to 512px and nearest-neighbour mask upsampling. Full-validation inference is unchanged. The additional crop RNG draw also shifts subsequent flip RNG draws, so their realized augmentations are not perfectly matched.
- Both use seed **42**, CE+soft multiclass Dice, **24 × 192** training patches, 32 diagnostic validation patches, batch two, AdamW learning rate 0.0002, Torch 2.10.0+cu128, Torchvision 0.25.0+cu128 and Tesla T4. Complete logs show a fresh run rather than a resumed training session.
- All exact image ID lists equal both earlier controls: **31 train / 6 validation / 12 test**, mutually disjoint. Validation IDs are `train_06`, `train_21`, `train_13`, `train_10`, `train_23`, `train_27`. Test IDs remain `test_01` through `test_12`. Thirty-seven is the publisher train-folder count, not the effective training count.
- Both report publisher ZIP SHA **64aebd108b3306a8b2e83a945c01f2779bbfd1abeb187b1e2cedcac96cf40c1d**, 418,742,024 bytes, matching the previously independently verified local archive. This audit did not rehash or download that archive.
- Every one of the 24 saved full-validation rows independently recomputes from TP/FP/FN; every per-section count sums to its pooled count, and all epochs match previously verified true validation counts. Standalone histories equal manifest histories, and all 24 printed training-log foreground scores agree with those histories at log precision. Checkpoint-selection flags and manifest best epochs agree with the declared maximum foreground macro IoU rule.
- Validation uses complete sections, native 512px sliding windows, 64px overlap and averaged logits. Balanced validation patches are diagnostic only. Neither notebook calls `--eval`; both declare `test_used_for_selection: false`, `test_evaluation_performed: false`, `test_metrics: null`.

Native source bundle SHA: `4cffd60c88fea1a7553f8f154040cf2ce93f7312f0571f3dc6784b5938988528`. Small-grain source bundle SHA: `c80b593ed86aff95a47596fa4559af43f773908542f56dce70b0f1c431099c69`. The inherited commit field is `f463864d8c81ec77b8ed0381781ba37c81ca4a61`; actual embedded hashes control these runs. The inherited manifest wording “Matched single-seed CE control” is stale prose in both extended manifests, while the executed command and saved loss field correctly identify Dice.

## Conditional uncertainty and scientific limits

An exploratory 10,000-draw section bootstrap, seed 20261001, gives foreground macro IoU percentile intervals: matched CE **[0.24755, 0.50836]**, short Dice **[0.32242, 0.54336]**, native extended **[0.56961, 0.67210]**, small-grain **[0.46186, 0.56701]**. Native minus short Dice's paired interval is **[0.02745, 0.28094]**; small-grain minus short Dice's is **[-0.00736, 0.22069]**. Metric denominators follow the saved convention, excluding classes with zero TP+FP+FN in a draw.

These intervals are conditional on checkpoints and variants already selected with the same six sections. They do not correct model selection or establish locality-level accuracy. Only two sections contain true magnetite. LumenStone provides no verified specimen/locality grouping, so the frozen split is image-level rather than proven locality-disjoint. This is one seed, one small validation set and an analogue dataset. Paired replication is still needed before a stable gain claim. The earlier train-selected majority-class validation baseline is foreground macro IoU 0.0792558961; a defensible metadata-only baseline remains unavailable. No stronger-baseline uplift or South African transfer claim is made.

The candidate has no test result from either extended run. Historical models have previously used the publisher test set, so any subsequent fixed evaluation is a final regression check rather than a fresh blind test. These validation scores must not be ranked against the application's .4543 or historical .5725 test scores.

## Fixed candidate and continuation contract

If proceeding to a final regression evaluation, freeze **native extended epoch 12** based solely on the declared validation criterion. Do not substitute another epoch or the small-grain variant after viewing test results. Freeze this source, preprocessing, split and inference code; verify actual candidate bytes and SHA before inference. Do not tune thresholds, class definitions or hyperparameters on the 12 test sections. Deployment remains a separate decision after checkpoint identity, the fixed final report, latency, refusal behavior and rights review.

Verified remote native checkpoint name:

`khanya-20260930-s2-seed42-extended-dice-v1/checkpoints/lumenstone_s2_patches_20260930-s2-seed42-extended-dice-v1_dice/best.pt`

Reported native checkpoint SHA: **42646cfafbeac5398386dba17f7ad3531ffcea572e6342cc4fcba42ed0b44b3b**. Small-grain reported SHA: `adb592ff605e37610431ac2fcf65bae149415c4f257f17d831cdec84910cc6af`. These are notebook-reported identities; checkpoint bytes have not been independently rehashed by this audit.

The remote native bundle is `khanya-s2-dice-validation-20260930-s2-seed42-extended-dice-v1.zip`, reported by the restored console log as **149.6 MiB**. Exact best.pt byte size is unavailable: metadata-only HTTP HEAD returned 404; Kaggle file-list size fields also disagree with the known downloaded manifest size, so those fields cannot establish weight size. The evaluation process should record actual bytes and hash when mounting or retrieving the fixed candidate. No body download was attempted by the metadata checker.

The evaluation entry point is `python -m src.segmentation.train_patches --loss dice --eval`, with `KHANYA_SUBSET=S2`, `KHANYA_SEED=42`, `KHANYA_RUN_ID=20260930-s2-seed42-extended-dice-v1`. It builds the model with `pretrained=False`, reads the fixed `best.pt`, and evaluates complete native test sections. The source notebook already contains the publisher download/checksum/extraction path; no Kaggle dataset slug is used. An evaluation-only run must remove the training invocation and retain the verified source, exact checkpoint path and ID lists.

Small artifacts are under [audit_extended_20261001](C:/Users/USER/Desktop/REEFPRINT/training/audit_extended_20261001). The Kaggle CLI initially returned Windows socket denial under the sandbox; authorized network escalation succeeded. Filtered output retrieval saved all requested metric/log files but then hit its Windows console-log encoding bug. The small console logs were recovered separately as UTF-8 using the same authenticated API. No credentials, signed artifact URLs, raw imagery or weights were printed or written to this report. No Git mutations or shared BUILDLOG/STATUS edits were made.
