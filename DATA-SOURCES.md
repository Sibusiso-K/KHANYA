# Data sources — research phase

Status as of 2026-08-04. Verify licences again before the report is finalised.

## 0. REEFPRINT target phases — PARTIALLY UNBLOCKED 2026-08-14

**Update 2026-08-14:** LumenStone access has cleared (Section 1) and its **S2
subset is a layered-ultramafic magmatic sulphide assemblage (Norilsk Group)** —
a genuine geological analogue for the REEFPRINT base-metal-sulphide class, with
pixel-level masks and 5 classes. This does not deliver the full REEFPRINT phase
set (no chromite, orthopyroxene, plagioclase or talc/serpentine), but it does
give the project a real multi-class held-out result on the phase that carries
the economic payload. Read the rest of this section as the still-open half of
the problem: the silicate and chromite phases.



Lethabo's submitted abstract (REEFPRINT) commits to five Bushveld-relevant
phases: **chromite, orthopyroxene, plagioclase, base-metal sulphide,
talc/serpentine** (src/config.py REEFPRINT_CLASSES). Searched for a public
petrographic/microscopy dataset covering this phase set on 2026-08-04 - found
nothing. This is the actual data blocker for the real submission target; the
MUMDMC/FeM work below is dev-proxy work done while this is unresolved.

Per the abstract's own Section 3.14, the plan if no Mintek dataset is released
is to run the demonstration on public data with the same architecture. That
still requires finding *some* public multi-class Bushveld-adjacent dataset
(chromitite, UG2, pyroxenite thin sections) that we have not located yet -
worth a dedicated search pass, distinct from the MUMDMC/LumenStone search
already done below.

**Checked and ruled out (2026-08-10): LITHOS-DATASET.** Kaggle,
paolaruizpuentes/lithos-dataset, companion to a NeurIPS 2025 Datasets and
Benchmarks paper ("Towards Automated Petrography", arXiv:2511.00328). Genuinely
large - 211,604 patches, 105,802 expert-annotated grains, 25 mineral classes,
CC BY-NC-SA 4.0. Its 25 classes (from the paper's Figure 1 caption): Polycrystalline,
Monocrystalline, Feldspar, Rock fragment, Mica, Echinoderm, Quartz, Plagioclase,
Foraminifer, Fossil Fragment, Amphibole, Calcareous fossil, Red Algae, Calcite,
Heavy mineral, Coral, Pyroxene, Dolomite, Hornblende, Muscovite, Crystalline
mosaic, Microcline, Opaque, Sanidine, Other. This is a **sedimentary/carbonate
petrography dataset** (foraminifer, coral, calcareous fossil, echinoderm, red
algae, dolomite are bioclastic/sedimentary features) - wrong rock type for
Bushveld ultramafic-mafic cumulates. Only "Plagioclase" and generic "Pyroxene"
nominally overlap with REEFPRINT_CLASSES, and not in cumulate-rock context.
No chromite, no base-metal sulphide, no talc/serpentine. Does not solve the
data blocker - recorded here so this dead end isn't rediscovered.

## 0b. Dataset search, 2026-08-17 — three new findings

Searched for further masked reflected-light ore microscopy beyond S2. Results in
priority order.

### (i) LumenStone S1 and S3 — available now, and the best test available

Already accessible from the same host we used for S2, no registration:

| Set | v2 | Classes | Size | Assemblage |
|---|---|---|---|---|
| S1 | 64 train / 20 test | **7** | 646 MB | Berezovskoe hydrothermal: sphalerite, pyrite, galena, bornite, tennantite-tetrahedrite, chalcopyrite |
| S3 | 33 train / 14 test (+XPL rotations) | **9** | 5.2 GB | high-temperature hydrothermal: pyrite, arsenopyrite, covelline, bornite, chalcopyrite, magnetite, hematite |

**Why these matter more than any new dataset.** They test whether our central
finding generalises: does repairing particle topology beat raising IoU on a
*different ore genesis* with *more classes*? If the effect holds on S1's seven
hydrothermal phases and S3's nine, it stops being an S2 artefact and becomes a
general claim about image-based mineralogy. If it does not hold, we need to know
that before 1 October rather than after a judge asks.

Requires almost no new code: we already store petroscope's global class
codebook, and S1/S3 codes come from the same 50-class table. Only the class list
and directory change. S3 also contains **magnetite and hematite together** -
directly relevant to our optical argument in report section 3, since that pair is
exactly what SEM/BSE cannot separate, and it would let us test the claim rather
than only assert it.

### (ii) USGS mafic-ultramafic thin sections — CC0, right rock type, NO masks

DOI **10.5066/P1SUMMMI**, ver 2.0 (August 2025), ScienceBase item
65f2321fd34e1403329846c2. Thin sections from hand samples and drill core of
**mafic to ultramafic rocks**, sampled specifically to define **platinum group
element, copper, nickel**, gold and Ti-V-Fe resources across US localities.
Imaged in plane-polarised, cross-polarised **and reflected light** (Keyence
VHX-7000). Licence **CC0 1.0** - the most permissive we have found.

**No mineral identifications and no pixel masks**, so it cannot train supervised
segmentation. Its value is different and still real:

- It is the closest public imagery to Bushveld *rock type and commodity* we have
  located - layered mafic-ultramafic, PGE-Cu-Ni - which is precisely the gap
  named in report section 8 limitation 2.
- Different laboratory, different microscope, different preparation. Running our
  S2-trained model over it is a genuine **cross-laboratory domain-shift test**,
  which is report section 8 limitation 7 and currently unaddressed. Qualitative,
  but a judge asking "would this work on our samples?" deserves better than
  "untested".

Treat as inference-only evaluation material, never as a training set, and never
report a number from it that implies labels exist.

### (iii) Reflected Light Microscopic Iron ore dataset — low value for us

Mendeley Data `6hp82tsb8g` v2; paper *Data in Brief* (2025),
DOI 10.1016/j.dib.2025.111540 (Firdaus, Anwar, Mohapatra, Sahoo). 563
reflected-light images of iron ore from Indian mines, at 10x and 20x, labelled by
**ore grade** - Blue Dust, Hard Laminated, Lateritic, Soft Laminated.

Right modality, wrong label type: these are whole-image grade classes, not
mineral phases, and there are no masks. It cannot exercise the segmentation or
liberation stages, which is where our contribution sits. Recorded so it is not
re-investigated.

## 1. LumenStone — primary target, ACCESS OPEN (re-checked 2026-08-14)

Reflected-light images of **polished ore sections** with pixel-level multi-class
masks. Exact match for Problem 3.

**The HTTP 500 recorded on 2026-08-04 has cleared.** Host returns 200 and every
subset downloads directly from Yandex Disk — no registration, no email needed.
Note the site now carries a **v2** of each set (released 15.06.2025 / 30.12.2025)
that the earlier entry here predates; v2 is a superset of v1 by the site's own
versioning rule ("every new version besides offering new images will contain all
images from the previous version"), with annotations possibly revised.

| Set | v2 images | Task | Assemblage |
|---|---|---|---|
| S1 | 64 train / 20 test | segmentation, 7 classes | Berezovskoe hydrothermal: sphalerite, pyrite, galena, bornite, tennantite-tetrahedrite, chalcopyrite |
| **S2** | **37 train / 12 test** | **segmentation, 5 classes** | **Layered Ultramafic (Norilsk Group): pyrrhotite, chalcopyrite, pentlandite, magnetite** |
| S3 | 33 train / 14 test (+XPL rotations) | segmentation, 9 classes | high-temperature hydrothermal: pyrite, arsenopyrite, covelline, bornite, chalcopyrite, magnetite, hematite |
| V1 | 30 (10 x 3 variations) | colour adaptation | same samples as S1 |
| P1 / P2 | 1552 / 671 | panorama stitching | — |

All x50 magnification, 3396x2547 px. Source material: 30 CIS ore deposits,
Carl Zeiss AxioScope 40 microscope, Canon Powershot G10.

**Licence / Data Usage Agreement** (verbatim from the site, 2026-08-14 and
re-confirmed 2026-09-13, no change): free use in your own research work; if
publishing work that uses the dataset, cite the references. No formal SPDX
licence, and no explicit statement on commercial use or redistribution
either way. Checked the authors' own toolkit repo (`petroscope`) for anything
more specific to the dataset itself, separate from the library's own
GPL-3.0 - nothing found.

**2026-09-13 decision: operate within the published terms as written, and
disclose the ambiguity rather than resolve it by email.** The team decided
against contacting the author for clarification (WORKBOARD.md D5, closed
this way rather than left open). This is a defensible position, not an
avoidance of the question, for three concrete reasons:

1. **We do not redistribute LumenStone's data at all.** `data/raw/` and
   `checkpoints/` are both gitignored - zero files from this dataset, and no
   trained weights derived from it, are present in the public repository
   that Mintek's Office of Technology Transfer will review. Verified:
   `git ls-files | grep "^data/raw\|^checkpoints/"` returns nothing.
2. **What we do is unambiguously "your own research work."** Private
   training, reporting derived metrics (with citation, per the terms), and a
   live academic demonstration at a university-affiliated hackathon are the
   exact activity the published terms describe, not a commercial product
   launch.
3. **Any further commercialisation is Mintek's decision to make, not ours to
   pre-empt.** If this submission is selected and MOTT wants to develop it
   further, licensing LumenStone (or replacing it with cleared data) for that
   specific purpose is squarely within MOTT's own remit and institutional
   standing - better positioned to negotiate that than a student team, and
   only actually necessary if that stage is reached.

**State this explicitly in the submission** rather than silently assuming
it is resolved: cite the dataset per its terms, and note that any
production/commercial use beyond this research demonstration would need a
direct licensing conversation with the authors, which we have not initiated.
That sentence costs nothing and closes the gap the review flagged (D5)
without needing a response from anyone outside the team.

- Author contact, on file if this ever needs to be revisited: Alexander
  Khvostikov, khvostikov@cs.msu.ru, ORCID 0000-0002-4217-7141.
- Benchmark to beat: **mean IoU 0.8373** (ResUNet, S1v1). Also PSPNet+ResNet18 on
  S1+S2: IoU 0.88, pixel accuracy 0.96.

### Why S2 is the one that matters to us

S2 is drawn from the **Norilsk Group — layered ultramafic intrusions hosting
magmatic Ni-Cu-PGE sulphide**. Its four mineral classes are pyrrhotite,
pentlandite, chalcopyrite and magnetite. Pyrrhotite-pentlandite-chalcopyrite is
the same base-metal sulphide assemblage that carries the PGM payload in Bushveld
UG2 and Merensky reef ores, and both are layered ultramafic-mafic intrusions
rather than the hydrothermal or sedimentary settings every other candidate
dataset covers.

That makes S2 a defensible geological analogue for REEFPRINT's
`Base_Metal_Sulphide` class, not a convenience substitute — the transfer argument
is about ore genesis and mineral assemblage, and it should be stated in those
terms rather than as "closest available data". It does not contain chromite,
orthopyroxene, plagioclase or talc/serpentine, so it is an analogue for the
payload phase specifically, not for the full REEFPRINT phase set (see Section 0).

Practical fit: 5 classes clears the brief's >=3 phase floor, masks are
pixel-level, and the authors ship a train/test split so held-out numbers are
directly comparable to their published benchmarks.

**Where the analogue breaks — say this before a judge says it.** Norilsk ore is
massive magmatic sulphide: across S2's 37 training images the base-metal
sulphides (pyrrhotite + chalcopyrite + pentlandite) occupy **62.8% of pixels**.
In UG2 the same assemblage is <1 vol%. So S2 is an analogue for the *mineral
assemblage and its optical appearance*, not for its *abundance*. Any claim we
make from S2 transfers as "these phases are separable in reflected light at
these IoUs", and explicitly not as "we can find sub-1% BMS in UG2" — that second
claim needs the rare-class evidence below, and honestly it is a different and
harder problem.

Partial mitigation already in the data: **magnetite is only 1.58% of S2 pixels**,
so per-class IoU on magnetite is a real, in-dataset test of rare-phase
performance, and is the number to report against the imbalance risk in Section
5.1 of the research report. Report per-class IoU always; a mean IoU here is
flattered by pyrrhotite at 42.8%.

### Verified contents, downloaded and checked 2026-08-14

`data/raw/lumenstone/S2_v2.zip` (418.7 MB) -> `S2_v2/`. 37 train / 12 test,
author-defined split, matching the site.

```
S2_v2/imgs/{train,test}/           JPEG, 3396x2547
S2_v2/masks/{train,test}/          PNG, label in all 3 channels (R==G==B)
S2_v2/masks_colored/{train,test}/  RGB visualisation
S2_v2/masks_human/{train,test}/    human-readable overlay
```

Class codes are indices into petroscope's global 50-class LumenStone codebook
(`petroscope/segmentation/lumenstone.yaml`), shared across S1/S2/S3, so they are
**non-contiguous** and must be remapped to 0-4 before CrossEntropyLoss:

| Code | label | Mineral | Colour | % of train pixels |
|---|---|---|---|---|
| 0 | bg | background / resin | `#000000` | 35.60 |
| 1 | ccp | chalcopyrite | `#ffa500` | 11.65 |
| 3 | mag | magnetite | `#ff4500` | **1.58** |
| 5 | po | pyrrhotite | `#a9a9a9` | 42.80 |
| 7 | pn | pentlandite | `#ffff00` | 8.38 |

Keeping petroscope's codes rather than renumbering ours means their pretrained
weights, metrics and visualisations stay drop-in compatible.

### petroscope — the authors' toolkit
`pip install petroscope` — https://github.com/xubiker/petroscope

Provides LumenStone class definitions, ResUNet baseline, correct dataset-wide
IoU metrics, and a **patch-based self-balancing sampler**. Their README warns that
mineral class imbalance is severe and that loss weighting / class weighting does
NOT fix it. Take this seriously — it is the failure mode for this task.

## 2. FeM iron ore — DOWNLOADABLE NOW

https://zenodo.org/record/5014700

- `FeM_v1.zip`, 112 MB. 999x756 px at 1.05 um/px.
- **CC-BY-4.0**, open, no registration.
- Binary ore/resin masks only — does NOT meet the >=3 phase requirement alone.
- Cite: Filippo et al., Minerals Engineering 170 (2021) 107007.

## 3. MUMDMC2025 — DOWNLOADABLE NOW

- Sample (start here): 2,500 XPL images, 500/class —
  https://figshare.com/articles/dataset/MUMDMC2025_DataSet_sample/29483204
- Full: 14,400 JPEG, 3584x2746 @ 600 DPI, ~84 GB. **CC-BY-4.0**.
- 5 classes: biotite, hornblende, plagioclase, K-feldspar, quartz (2,880 each).
- 72 rotations per specimen under PPL and XPL. Rotations are near-duplicates —
  this is exactly why splits must be grouped by specimen.
- Paper: https://www.nature.com/articles/s41597-025-05879-9

## 4. Weak fallbacks — hand specimens, not micrographs

- https://www.kaggle.com/datasets/asiedubrempong/minerals-identification-dataset
- https://www.kaggle.com/datasets/sergeynesteruk/minerals (MineralImage5k)

Wrong modality for this brief. Use only if everything else fails, and say so.

## 5. South African ore imagery — NONE FOUND OPEN

Searched UG2 / Merensky / Bushveld specifically. Mintek's mineralogical work on
these ores is published as papers, not datasets. No competing team will have local
data either, so asking Mintek directly is the highest-value request available.

## Method references

- DeepLabv3+ opaque/non-opaque segmentation: https://www.sciencedirect.com/science/article/abs/pii/S0892687521002363
- Improved YOLOv8n fine-grained mineral segmentation: https://www.sciencedirect.com/science/article/abs/pii/S0892687525001189
- Polished-section segmentation and labelling: https://link.springer.com/article/10.1007/s42461-025-01205-4
- Res-UNet ensemble, mineral optical microscopy: https://doi.org/10.3390/min14121281
- Korshunov et al., visual diagnostics to deep learning: https://mst.misis.ru/jour/article/view/974

## Domain angle worth citing

SEM/BSE cannot separate hematite from magnetite — near-identical average atomic
number. Reflected-light optical can, on reflectance and colour. This justifies
cheap optical + CNN against a multi-million-rand automated mineralogy instrument.
