# Live result and control audit — 30 September 2026

## Checkpoint status

The approved demo checkpoint is `de7135a96541a46dc0981a991cb954186c7cd669ea1c1b33914d1929ae9b1357` (`de7135a9`). It is approved because it has the best held-out mIoU in `reports/ACCURACY-REPORT.md` (mIoU 0.5725; pixel accuracy 0.8914).

The previously recorded `test_11` live result used `fb78727d` on the Lethabo host. That run is retained for provenance and must be rerun with `de7135a9`; this audit intentionally records no invented replacement result numbers.

## Control contract

The API exposes `model_approved` and `approved_model_sha` in health and report responses. The simulator holds a result whose checkpoint is not approved, even when confidence and validation gates would otherwise pass. Unknown checkpoints have no measured metrics and cannot be approved.

## Outstanding verification

- [ ] Rerun `test_11` through the live browser with `de7135a9`.
- [ ] Capture the approved and non-approved `/api/health` JSON and startup log line.
- [ ] Capture 375 px and desktop screenshots for both states.
