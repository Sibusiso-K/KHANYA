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
