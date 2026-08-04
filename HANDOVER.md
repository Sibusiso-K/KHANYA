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
