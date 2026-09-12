# 008 — Checking experiment 007's own open hypothesis: N3's original method, re-run

**Status: confirmed. The naive-condition discrepancy is a registration-methodology difference,
not a bug or a contradiction.** Closes the first item in `experiments/007-s3v2-registration/
README.md`'s *Left open* list.

```bash
kaggle kernels push -p experiments/008-n3-original-method-rerun
```

Ran as `lethabomh14/reefprint-p5-n3-rerun` (~35 s — this method never warps a frame, only samples
scattered pixel positions from raw JPEGs, so it is far cheaper than experiment 007's full-stack
registration).

## The question

Experiment 007 found that a "naive" condition — every frame de-rotated about the *image centre*
by its nominal angle — already clears `DETECTION_SNR` for the 2nd harmonic on all 5 measurable
sections, a sharp break from N3's original three independent `NEITHER` findings on the same
archive. The README named a hypothesis, not a check: N3's original method
(`experiments/002-s3v2-geometry/run.py::read_section`) samples scattered pixel *positions*
directly from raw, un-rotated frames — genuinely zero registration — while experiment 007's
"naive" condition already applies an approximate correction. This experiment re-runs N3's exact,
unmodified method on the same 5 sections to check that directly.

## Result — confirmed, 5/5

| Section | N3 original snr₂ | N3 original snr₄ | N3 original verdict | exp007 naive snr₂ | exp007 naive verdict |
|---|---:|---:|---|---:|---|
| S3_test_01 | 4.43 | 1.41 | **NEITHER** | 12.54 | SECOND |
| S3_test_02 | 3.12 | 2.03 | **NEITHER** | 11.18 | SECOND |
| S3_test_03 | 2.65 | 2.07 | **NEITHER** | 9.35 | SECOND |
| S3_test_07 | 2.40 | 1.05 | **NEITHER** | 6.89 | SECOND |
| S3_test_12 | 1.78 | 1.29 | **NEITHER** | 7.11 | SECOND |

**N3's original, unmodified method returns `NEITHER` on all 5 — exactly reproducing the
historical finding**, every `snr_2` and `snr_4` well below the 5.0 threshold. This is not close;
the largest N3-original `snr_2` (4.43) still sits under threshold, and the smallest experiment
007 naive `snr_2` (6.89) sits clearly over it.

## What this settles

**The hypothesis in experiment 007's README is confirmed: any sensible de-rotation — even about
the wrong centre — recovers real per-pixel harmonic structure that zero registration cannot see
at all.** This is not a contradiction between the two experiments; it is direct evidence *for*
the project's central registration thesis (`WORKBOARD.md` §0 C1): a pixel that is a different
physical grain in every frame carries no coherent modulation to detect, at any harmonic, and
that is exactly what N3's three original runs measured — correctly, on genuinely unregistered
data. The moment frames are even approximately realigned, real structure appears.

## What this does NOT settle

- **It does not mean experiment 007's "registered" condition is correct.** This experiment only
  checks the *naive* condition against N3's original method. `S3_test_03`'s flip to `FOURTH`
  under proper registration is untouched by this result and still needs the visual sanity check
  `experiments/007-s3v2-registration/README.md` names.
- **It is still 5 sections**, the same convenience sample experiment 007 used, for the same
  reason (which sections carry a full rotation series with a matching mask shape).
