# Handover Log

Required for every collaborator. Before pushing, read the latest entry below.
After pushing, add a new entry — newest on top. Keep entries short and factual:
what changed, what's blocked, what the other person needs to know or do next.

Entry format:

```
## 2026-08-04 — <name>

**Did:** ...
**Changed:** files/paths touched
**Blocked on:** anything waiting on the other person, or "nothing"
**Next:** what the other person should pick up
```

---

## 2026-08-14 — Sibusiso (8)

**Did:** S2 baseline finished. **First result that meets the brief's >=3 phase
floor with a real held-out number: mean IoU 0.545, pixel accuracy 0.879 on 12
unseen sections, 5 classes.** Per-class: pyrrhotite 0.864, background 0.827,
chalcopyrite 0.548, pentlandite 0.485, **magnetite 0.000**. Numbers in
`reports/lumenstone_s2_test_metrics.json`.

**Read this before quoting the headline number.** Magnetite fails completely,
and it IS present in test (0.79% of pixels), so that is total failure on the
rare class, not absence - the exact imbalance failure petroscope warns about,
reproduced in our own numbers. Two separable causes: the class is rare, and the
6.6x downsample from 3396x2547 to 512x688 destroys fine grains before the model
sees them. Also, our val set (6 images) is too small to select checkpoints on -
pentlandite scored 0.026 on val against 0.485 on test, and val is 45.8%
background against test's 25.0%.

Then built `src/decision_gap.py` to answer the question IoU cannot: does being
this wrong change what the plant is told to do? Runs the advisor twice over the
same 12 sections, ground-truth masks vs predicted. **4 of 12 recommendations
flip (33%)** - `reports/decision_gap.json`. Direction matters more than count:
two flips say "continue at setpoint" on ore whose payload is actually locked
(test_04 liberation 9%->75%, test_05 4%->58%), which sends recoverable metal to
tailings and is the expensive direction. One is conservative (test_09, wasted
grinding energy, no metal lost). One is an outright detection miss on a 1%
payload field (test_02). **Conclusion: the model is not yet fit to drive this
advisor**, and the flip rate is a better measure of that than mIoU.

Caught a methodology trap worth knowing about: comparing GT at native
resolution against predictions at 512x688 gave a 50% flip rate, but ~44x fewer
pixels per grain means the minimum-particle-size filter drops far more particles
on the predicted side. Three of those six flips were scale artefacts. GT is now
downsampled to the network's working size before comparison; **33% is the
like-for-like figure, 50% is wrong** - do not quote the 50%.

**Changed:** new `src/decision_gap.py`, `reports/KHANYA-01-research-phase.md`
(new sections 5.0.2 and 5.0.3), `reports/lumenstone_s2_test_metrics.json`,
`reports/decision_gap.json`.
**Blocked on:** nothing. Access check: you (LethaboMH14) have write access and
it is active - clone, pull and push all work.
**Next, in priority order:** (1) patch-based sampling at native resolution -
addresses both magnetite causes at once and is what petroscope's authors say is
necessary; this is the single highest-value experiment left. (2) Grouped
cross-validation over the 37 training sections instead of the 6-image val set.
(3) Re-run decision_gap after both and show the flip rate coming down - that
before/after is the strongest slide we have.

---

## 2026-08-14 — Sibusiso (7)

**Did:** Built the operational feedback layer for real - it was the weakest of
the brief's three deliverables and both its inputs were fake (classifier
confidences standing in for area fractions, liberation coming from a slider the
presenter dragged). Both are now measured from the predicted mask.
`src/modal.py` computes modal mineralogy as a fraction of **ore** area excluding
mounting resin, and computes **liberation by particle composition**: connected
components of non-resin pixels are particles, a particle is liberated when the
payload phase occupies >=50% of it, and the index is the mass-weighted share of
payload sitting in liberated particles. Validated on all 12 held-out S2 test
sections using ground-truth masks - it spans 0% to 100% and tracks the
mineralogy correctly (few large massive-sulphide particles score ~0%, many
small disseminated grains score >80%). `src/advisor.py` rewritten to reason over
metallurgical **roles** (payload/reject/oxide/gangue/deleterious) rather than
mineral names, with the mapping in `modal.py` - so swapping ore body changes a
mapping, not the decision logic, and REEFPRINT data drops straight in if Mintek
releases any. Dashboard rewritten onto the segmentation path end to end.

**Two findings worth knowing before you quote anything:**
(1) Calling all three sulphides "payload" made liberation saturate at ~100%
everywhere - in massive sulphide the payload IS the rock. Fixed by the correct
metallurgy: pentlandite + chalcopyrite are payload, **pyrrhotite is the
rejection target** (grade dilution, smelter sulphur load - standard practice in
magmatic Ni-Cu). Caveat: pyrrhotite does carry some Ni/PGE in solid solution, so
that is a grade-vs-recovery trade, not free money. The saturation result is
written up in report section 7.4 as a negative result, not deleted.
(2) Liberation from 2D sections is biased **high** against true volumetric
liberation - a section plane can cut the free rim of a particle with a locked
core. We apply no stereological correction, so our index is an upper bound.
Safe direction for "grind finer", unsafe for "continue at setpoint". Say this
before a judge does.

**Changed:** new `src/modal.py`, rewrote `src/advisor.py`, rewrote
`dashboard/app.py`, `src/segmentation/lumenstone.py` (colours + shared
`preprocess` so demo inference cannot drift from eval inference),
`requirements.txt` (scipy), `reports/KHANYA-01-research-phase.md` (section 7
rewritten).
**Blocked on:** nothing new. S2 baseline training still running (12 epochs, CPU,
~2h); epoch 1 val mIoU 0.09 with all minerals at 0.0, which is normal for a
fresh head but needs watching - if minerals are still at 0.0 by epoch 4 the LR
(1e-3) is too high for a 5-class fine-tune and should come down to ~2e-4.
**Next:** all advisor numbers so far come from GROUND-TRUTH masks, which proves
the measurement logic, not the end-to-end system. Once training finishes, the
same 12 sections need re-running on PREDICTED masks - the gap between those two
liberation numbers is the honest measure of how much segmentation error costs at
the decision layer, and that comparison is a strong slide.

---

## 2026-08-14 — Sibusiso (6)

**Did:** Two things, both significant. (1) **We're in** - acceptance letter
received, we're selected for the hackathon. Read it and put the real dates in
README.md; the ones we had were wrong in shape. 1 Oct is a working day on site
with a **13:00 hard submission cutoff** and a **10-minute** pitch at 14:00, not
a presentation day. A **one-page abstract is due 30 Aug** (approach, methods,
expected outcomes) along with per-member admin: ID number, T-shirt size, contact
details, and either your mentor's details or an explicit request for a Mintek
mentor. 2 Oct conference attendance is compulsory; five finalists announced
there, then originality authentication. Prizes R25k/R15k/R10k, possible vacation
work at Mintek. (2) **LumenStone is back up** - the HTTP 500 has cleared, all
subsets download straight off Yandex Disk, no registration, usage agreement
allows research use with citation. There are now **v2** releases we didn't know
about. The important part: **S2 is a Norilsk Group layered-ultramafic magmatic
sulphide assemblage** - pyrrhotite, pentlandite, chalcopyrite, magnetite. That's
the same BMS assemblage that carries the PGM payload in UG2/Merensky, and the
same intrusion type. It's a real geological analogue for our BMS class, 5
classes with pixel masks and an author-defined split, so it clears the brief's
>=3 phase floor with a legitimate held-out number. Full reasoning in
DATA-SOURCES.md Section 1.
(3) **Downloaded S2 v2 and built the multi-class pipeline.** 418.7 MB, extracted
to `data/raw/lumenstone/S2_v2/` (gitignored - re-download from DATA-SOURCES.md
Section 1). Verified contents against petroscope's codebook: 37 train / 12 test,
author-defined split, five classes - background, chalcopyrite, magnetite,
pyrrhotite, pentlandite. Masks are RGB with the label in all three channels, and
the class codes are non-contiguous (0,1,3,5,7) because they index petroscope's
global 50-class codebook shared with S1/S3 - they need remapping to 0-4 for
CrossEntropyLoss, which `lumenstone.py` does at tensor-build time while keeping
the original codes so petroscope stays drop-in compatible. Wrote
`src/segmentation/lumenstone.py` and `train_lumenstone.py` as **separate**
modules rather than folding S2 into `data.py`/`train.py`, so the FeM 0.872 result
already quoted in the report stays reproducible with zero regression risk.
Carved a 6-image val set out of train; **test/ untouched.** 12-epoch baseline
training running now on CPU (~8-9 min/epoch, ~1.7h).

**Changed:** `README.md` (status + real dates + plan to 1 Oct), `DATA-SOURCES.md`
(Sections 0 and 1 rewritten + verified S2 contents), `reports/KHANYA-01-research-phase.md`
(Section 9), new `src/segmentation/lumenstone.py`, new
`src/segmentation/train_lumenstone.py`, `.gitignore`.
**Blocked on:** still no data for chromite/orthopyroxene/plagioclase/
talc-serpentine - S2 covers the BMS payload phase only. R6,000 rig call still
open and now urgent: it needs answering before the 30 Aug abstract, not after.

**Read before quoting any S2 number:** Norilsk is massive sulphide - BMS is 62.8%
of S2 pixels, against <1 vol% in UG2. S2 is an analogue for the assemblage and
its optical appearance, not its abundance. Magnetite at 1.8% is the in-dataset
rare-class test; report per-class IoU, never mean IoU alone. Full caveat in
DATA-SOURCES.md Section 1.
**Next:** Lethabo - three things, all time-boxed by 30 Aug: (a) your ID number,
T-shirt size, contact details, and whether we're requesting a Mintek mentor
(I'd say yes, and ask about polished-section imagery in the same message);
(b) the rig decision; (c) your call on whether the abstract keeps the full
five-phase REEFPRINT scope or re-scopes to what we can actually evidence by
1 October. Read DATA-SOURCES.md Section 1 before answering (c).

---

## 2026-08-10 — Sibusiso (5)

**Did:** Checked in - you'd accepted the GitHub invite but hadn't pushed
anything yet, so the two open asks below (Bushveld-phase data lead, R6,000 rig
decision) are still unanswered. Used this session to keep chasing the data
blocker: found and ruled out LITHOS-DATASET (Kaggle, NeurIPS 2025 paper,
211k patches / 25 classes) - genuinely large, but it's a sedimentary/carbonate
petrography dataset (foraminifer, coral, dolomite etc.), wrong rock type for
Bushveld ultramafic-mafic ores. Only nominal overlap on Plagioclase/Pyroxene,
no chromite/BMS/talc. Full class list and reasoning in DATA-SOURCES.md so this
isn't re-discovered later.
**Changed:** `DATA-SOURCES.md` (LITHOS ruled-out entry).
**Blocked on:** still no public dataset for chromite/orthopyroxene/plagioclase/
BMS/talc-serpentine. Still need the R6,000 rig call.
**Next:** Lethabo - when you're on this, `git pull` and check this file plus
`DATA-SOURCES.md` before starting anything. If you or a contact has any lead
on Bushveld/UG2/Merensky/Platreef thin-section or QEMSCAN imagery, that's the
single thing that unblocks the most work right now.

---

## 2026-08-04 — Sibusiso (4) — end of day

**Did:** Got a real, honest segmentation result. DeepLabv3+ResNet50 on FeM
(ore/resin, reflected-light microscopy), 10 epochs CPU, image-level split
(81 distinct sections, no rotation duplicates so this split is legitimate,
unlike MUMDMC). Held-out TEST SET (12 images the model never saw): **mean IoU
0.872, pixel accuracy 93.75%**. This is a real, defensible number - comparable
to the published PSPNet+ResNet18 LumenStone benchmark (mIoU 0.88) despite far
less compute. Also fixed a real bug along the way: `build_model(pretrained=
False)` silently built a different architecture (no aux classifier head) than
training did, so the saved checkpoint failed to load - fixed by pinning
`aux_loss=True` always in `src/segmentation/model.py`.
**Changed:** `src/segmentation/config.py` (25->10 epochs), `src/segmentation/model.py`
(aux_loss fix), `reports/KHANYA-01-research-phase.md` (added section 5.0.1
with the real numbers).
**Blocked on:** same as entry (3) below - no public dataset yet for the
REEFPRINT phase set (chromite/orthopyroxene/plagioclase/BMS/talc), and the
R6,000 rig decision. The segmentation result above is ore-vs-resin (FeM), not
those five phases - good proof the pipeline works, not yet evidence on the
real target classes.
**Next:** Lethabo - same asks as below (Bushveld-phase data lead, rig
decision). When you're back on this: `git pull`, read this file top-down,
then `reports/KHANYA-01-research-phase.md` section 5 for the current data/
results picture before writing any new code.

---

## 2026-08-04 — Sibusiso (3)

**Did:** Read REEFPRINT (the abstract you submitted) and re-scoped the code's
target phase set to match it: chromite, orthopyroxene, plagioclase,
base-metal sulphide, talc/serpentine. `advisor.py` logic rewritten around
BMS-as-payload (report low-BMS explicitly rather than falling through, per
your Section 1 point about aggregate accuracy hiding the sub-1% class).
Kept MUMDMC as a labelled dev-proxy (its classes don't match REEFPRINT's -
see config.py comments) so the pipeline stays exercised while real data is
missing. Segmentation baseline on FeM (ore/resin, unrelated phase set) still
training in background, unaffected by this change.
**Changed:** `src/config.py`, `src/advisor.py`, `DATA-SOURCES.md`.
**Blocked on:** no public dataset found yet for the REEFPRINT phase set
(chromite/orthopyroxene/plagioclase/BMS/talc). This is now the real data
blocker, not MUMDMC's specimen scarcity. Also: REEFPRINT Section 3.13 specs a
~R6,000 self-funded rig - conflicts with our earlier "no money" decision,
needs a call between us.
**Next:** Lethabo - if you have a lead on Bushveld/UG2/chromitite thin-section
imagery (public or from your own contacts), that unblocks the real target.
Also need your read on the R6,000 rig: build it, scope it down, or cut it and
lean harder on the software/simulation deliverables (plant simulator, OPC UA
advisory channel, conformal calibration) which don't need hardware spend.

---

## 2026-08-04 — Sibusiso (2)

**Did:** Ran the classification baseline on the MUMDMC2025 sample (583 images,
8 specimens across 5 classes). 98.3% train accuracy, but NOT a real accuracy
result — confirmed the full 14,400-image dataset from the paper is not
publicly downloadable (only a 1-image teaser is linked to the paper's actual
DOI); what we have is the largest public version and it's too specimen-poor to
hold out a test set. Pipeline itself (data loader, specimen-grouped split,
training, checkpointing) verified working. Also attempted to move training into
a Lightning AI Studio (khanya-baseline) for visibility — hit a "no hardware
found" infra issue, unrelated to our code; parked for now, ran locally instead.
**Changed:** `src/config.py`, `src/data.py`, `src/train.py`,
`reports/KHANYA-01-research-phase.md` (added section 5.0).
**Blocked on:** need more specimens per class for MUMDMC's 5 minerals (biotite,
hornblende, plagioclase, K-feldspar, quartz), or a decision to de-scope the
classification accuracy claim and lean on segmentation/advisor work instead.
**Next:** Lethabo — if you find any other petrographic thin-section dataset
covering these 5 classes with more than 1-2 specimens each, that unblocks
everything. Otherwise let's decide together whether to keep chasing data or
pivot effort into the FeM segmentation stage and the advisor thresholds, where
evaluation is more tractable.

---

## 2026-08-04 — Sibusiso

**Did:** Scaffolded PyTorch project (specimen-level splits, ResNet18 baseline,
train/eval/advisor), surveyed datasets, invited Lethabo as collaborator, set up
a Lightning AI Studio (khanya-baseline, CPU, free tier) for training.
**Changed:** `src/`, `dashboard/`, `DATA-SOURCES.md`, `reports/KHANYA-01-research-phase.md`
**Blocked on:** MUMDMC2025 full dataset download (4.8GB, in progress locally).
LumenStone (better-fit dataset) inaccessible — host down, no outreach planned
per team decision to wait on official acceptance.
**Next:** Lethabo — accept the GitHub invite (check email/GitHub notifications).
Once accepted, pull `main` and read `DATA-SOURCES.md` + `reports/KHANYA-01-research-phase.md`
before touching code.
