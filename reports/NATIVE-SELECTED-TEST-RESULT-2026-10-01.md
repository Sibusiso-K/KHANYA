# Native candidate: fixed test regression evaluation

Completed 2026-09-30T22:33:44Z; evaluation `native-selected-test-20261001-v1`.

Preselected checkpoint: `lethabomh14/reefprint-s2-extended-dice/1`, epoch 12, selected solely by six-section native validation foreground IoU 0.646702.

Measured **five-class mIoU 0.632038**, **foreground macro IoU 0.577958**, **pixel accuracy 0.855093** on all pixels of the fixed twelve whole sections.

Publisher held-out sections have earlier baseline results. This is a fixed final regression set, not fresh blind prospective data; this candidate has no prior test evaluation. Do not tune checkpoint, preprocessing, thresholds, or model selection from these results.

| Class | IoU | Recall | Precision | TP | FP | FN | Ground truth pixels |
|---|---:|---:|---:|---:|---:|---:|---:|
| background | 0.848359 | 0.879473 | 0.959968 | 22774980 | 949747 | 3121185 | 25896165 |
| chalcopyrite | 0.799841 | 0.845366 | 0.936919 | 4458646 | 300194 | 815574 | 5274220 |
| magnetite | 0.247730 | 0.893240 | 0.255289 | 733874 | 2140808 | 87713 | 821587 |
| pyrrhotite | 0.818308 | 0.855543 | 0.949500 | 51800961 | 2755080 | 8746484 | 60547445 |
| pentlandite | 0.445952 | 0.798357 | 0.502557 | 8986251 | 8894803 | 2269676 | 11255927 |

Confusion matrix: rows are ground truth, columns are prediction.

| Truth / Prediction | background | chalcopyrite | magnetite | pyrrhotite | pentlandite |
|---|---:|---:|---:|---:|---:|
| background | 22774980 | 86943 | 2086611 | 715711 | 231920 |
| chalcopyrite | 239294 | 4458646 | 29002 | 56901 | 490377 |
| magnetite | 49184 | 0 | 733874 | 34649 | 3880 |
| pyrrhotite | 395113 | 157693 | 25052 | 51800961 | 8168626 |
| pentlandite | 266156 | 55558 | 143 | 1947819 | 8986251 |

| Section | Five-class mIoU | Foreground IoU | Pixel accuracy |
|---|---:|---:|---:|
| test_01 | 0.627310 | 0.541793 | 0.951386 |
| test_02 | 0.441891 | 0.396104 | 0.981628 |
| test_03 | 0.579484 | 0.494816 | 0.846776 |
| test_04 | 0.482762 | 0.410880 | 0.773531 |
| test_05 | 0.740237 | 0.680297 | 0.965887 |
| test_06 | 0.532533 | 0.489582 | 0.764116 |
| test_07 | 0.329265 | 0.236035 | 0.838435 |
| test_08 | 0.545603 | 0.517648 | 0.934084 |
| test_09 | 0.406557 | 0.374300 | 0.842744 |
| test_10 | 0.288948 | 0.216163 | 0.753364 |
| test_11 | 0.275683 | 0.207081 | 0.758823 |
| test_12 | 0.306645 | 0.262253 | 0.850348 |

Each section’s full per-class IoU, recall, precision, TP/FP/FN and confusion matrix is in `native_selected_test_metrics.json` and the accompanying CSV files.

Protocol: original RGB at native resolution; 512px tiles, 64px overlap; average overlapping logits; fixed argmax; ImageNet normalization; no downsampling or test-time augmentation; no void-border exclusion. Pooled metrics are computed from total pixel counts, not averages over images. Five-class mIoU includes background. Undefined classes have null rates and are excluded from macro means; evaluated-class counts are in the JSON.

Per-section results are not verified independent localities/specimens. This single seed result cannot establish prospective accuracy or a stable improvement. No training, threshold fitting, candidate replacement or deployment occurs in this evaluation.

Provenance:

- Checkpoint SHA256: `42646cfafbeac5398386dba17f7ad3531ffcea572e6342cc4fcba42ed0b44b3b`; `168318771` bytes, independently hashed before and after inference.
- Source bundle SHA256: `4cffd60c88fea1a7553f8f154040cf2ce93f7312f0571f3dc6784b5938988528`; all 35 module hashes unchanged and verified.
- Training manifest SHA256: `cb431fd7101cf1263a613211783051fa7f5bc0d885df87c8a81e1db174853b03`.
- Original publisher archive SHA256: `64aebd108b3306a8b2e83a945c01f2779bbfd1abeb187b1e2cedcac96cf40c1d`; `418742024` bytes.
- Protocol SHA256: `8acb5998b06b67d7b542507dac4630dfea6fc422398d71050ee8e6894a263614`; source commit `f463864d8c81ec77b8ed0381781ba37c81ca4a61`.
- Runtime: Torch `2.10.0+cu128`, torchvision `0.25.0+cu128`, GPU `Tesla T4`.

Deployment remains a separate explicit approval decision after review of common-phase regressions and rare-phase behavior. Do not tune on this test outcome.
