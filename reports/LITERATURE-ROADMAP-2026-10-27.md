# From hackathon prototype to real-time PGM mineralogy: what the literature says

27 October 2026. Written as a NotebookLM source and a planning note for Team Sonar.

**How to read this.** Most findings below come from web search results and
abstracts, not full papers read end to end. Each item names its source. Open the
paper before you quote a number to Mintek, a producer or a funder. Items marked
*gap* mean the search found no published work, not that none exists.

---

## 1. What the NotebookLM critique said

Source: NotebookLM debate *Machine Learning versus Metallurgical Reality*
(20.5 min), transcribed locally. The two hosts judged KHANYA only against
Moodley et al. (2026).

**Strengths they credited:** inspectable software, hash-chained provenance back
to each source image, conformal bands with out-of-distribution refusal, the
OPC UA advisory link with the operator in control, and candour about TRL 3 and
public data.

**The three hurdles they set:**
1. **Stereological bias.** A 2D section can make a locked particle look
   liberated, so the system could say "stop grinding" and send metal to tailings.
2. **Brittle models and data reuse.** 12 LumenStone sections reused during
   development; hardness R² falling from 0.479 to 0.25 out of fold.
3. **Fines.** In Moodley's ore about 54% of the Cu sat below 20 µm, where
   optical boundaries blur. "Guessing on half the payload."

**Their fixes:** map output to Moodley's five exposure classes; convert to
recovery at risk with class rate constants; split advice into three diagnoses
(liberation, reagent or hydrodynamics, fine gangue); size-resolved reporting
and a hard refusal when fines dominate; validate on shared identical samples
(QEMSCAN, timed batch flotation, KHANYA micrographs, timed-concentrate
mineralogy); run Moodley-style identifiability and ±25% sensitivity checks;
"go to Mintek and sit down with Moodley".

**Errors in the podcast to correct before relying on it:**
- It calls QEMSCAN "3D volumetric". QEMSCAN maps 2D polished sections; it
  suffers stereological bias too, only with chemistry instead of reflectance.
- It treats R10.69–13.15m as the feasibility pilot. The feasibility stage (P0)
  is capped at R210,000; the R10.69–13.15m figure is the later pilot.
- It says conformal prediction "guarantees" coverage. Only on average, and only
  while new samples are exchangeable with the calibration set.
- It guesses Bushveld BMS at "maybe 3%". The repo's figure for UG2 is under
  1 vol% (`STATUS.md` §0).
- The 54%-below-20 µm figure is Moodley's copper ore, not measured on UG2.

**Its blind spot:** by fixating on one copper-ore paper it never asked what the
wider literature offers. Sections 4–6 below do that.

---

## 2. The shortfalls, in the build's own words

From `STATUS.md` and `reports/ADVERSARIAL-CRITIQUE-2026-09-15.md`:

| # | Shortfall | Evidence in the repo |
|---|---|---|
| S1 | **No South African ore.** Trained on one dataset, LumenStone S2 (Norilsk Ni-Cu-PGE), 37 training and 12 test images | `STATUS.md` §0 |
| S2 | **Wrong abundance regime.** Base-metal sulphide is 62.8% of S2 pixels against under 1 vol% in UG2 | `STATUS.md` §0; critique §1.1 |
| S3 | **The PGM grains themselves are not measured.** Four of five REEFPRINT target phases have no data | `STATUS.md` §0 |
| S4 | **2D association index, not liberation.** Renamed on 13 Sep because particulate mounts are not verified | `STATUS.md` header |
| S5 | **Invented decision thresholds.** One of four advisor thresholds is from literature; three are placeholders | `STATUS.md` §0; critique §1.3 |
| S6 | **Wide uncertainty band.** Split-conformal half-width 0.335; coverage not guaranteed for new uploads | `STATUS.md` header; critique §1.4 |
| S7 | **Small evidence base.** 12 held-out images; best mean IoU 0.5725; fails on the rarest phase | critique §2.5; `STATUS.md` §1 |
| S8 | **Not yet real time.** Input is a polished-section micrograph, which takes hours to prepare | build design |
| S9 | **Unvalidated value case.** Throughput gain and R43.7–84.3m figures are simulated proxies | team report §6 |

---

## 3. The yardstick: Moodley et al. (2026)

Moodley, Govender, Nkwanyana, Govender and Tshilongo, *Mineralogy-constrained
interpretation of rougher flotation kinetics in a copper sulphide ore*,
Results in Engineering 32 (2026) 112959, Mintek Minerals Processing and
Characterisation Cluster. Read in full.

What it teaches KHANYA:

- **Liberation classes are the currency.** QEMSCAN free-surface exposure grouped
  into locked (0–30%), low middlings (30–50%), high middlings (50–80%),
  liberated (80–<100%), fully liberated (100%), each given its own first-order
  rate. Recovery = the class-weighted sum (its Eq. 8).
- **Bulk curves cannot explain themselves.** One-, two- and three-term Kelsall
  fits matched the same curve; the three-term slow component collapsed to zero.
- **Count your evidence.** 16 independent measurements against 15 parameters
  (one degree of freedom), parameter profiles, 88 near-equivalent fits, ±25%
  weighting sensitivity. Outputs were stable even where parameters were not.
- **Fines dominate.** 38.8% of feed mass under 20 µm held about 54% of the Cu.
- **Its own limits.** One copper ore, one lab condition, no mineralogy of the
  timed concentrates, empirical entrainment term, confidential client data.

It is a copper ore. Nothing in it is shown for PGM, UG2 or chromite.

---

## 4. Shortfall by shortfall: what the wider literature offers

### S1, S2, S7: no SA data, wrong abundance, tiny test set → correlative labels

- **Train an optical model against SEM maps of the same block.** A 2025 arXiv
  paper trains a U-Net on optical thin-section images with the matching QEMSCAN
  maps as targets, explicitly to mimic QEMSCAN cheaply
  ([arXiv 2505.17008](https://arxiv.org/abs/2505.17008); carbonate rocks,
  transmitted light, not reflected light).
- **Registration is the hard part.** A µCT study registered QEMSCAN maps to
  tomogram slices and reports 1–2 voxel shifts and polishing artefacts as error
  sources ([arXiv 2002.05322](https://arxiv.org/pdf/2002.05322)).
- **LumenStone itself** reports IoU up to 0.88 for nine minerals using plane- and
  cross-polarised light ([Mining Science and Technology](https://mst.misis.ru/jour/article/view/974)).
  The critique (§1.2) already notes the published benchmark beats ours.
- **What to build:** a paired dataset. Same UG2/Merensky polished blocks imaged
  in reflected light (KHANYA) and mapped by QEMSCAN/TIMA at Mintek. Labels come
  free from the SEM map; the test set becomes held-out *ore samples*, not images.
- **Kill criterion:** if the optical model cannot reproduce QEMSCAN BMS and
  chromite modal abundance within an agreed tolerance on held-out UG2 blocks,
  stop calling it a QEMSCAN proxy.

### S3: PGM grains are below optical reach → measure the carriers honestly

- PGM recovery from UG2 depends mostly on **mode of occurrence, degree of
  liberation and grain size**
  ([University of Pretoria repository](https://repository.up.ac.za/handle/2263/31530)).
- Automated SEM across a UG2 concentrate bank found liberation and BMS/gangue
  association indices useful where PGM concentration changes strongly, and asked
  for larger datasets
  ([Chetty et al., OneMine](https://onemine.org/documents/automated-sem-study-of-pgm-distribution-across-a-ug2-flotation-concentrate-bank-implications-for-understanding-pgm-floatability-synopsis)).
- Kabemba et al. (2025) modified the Kelsall model with PGM mode of occurrence on
  Platreef, R² above 0.97, and name machine learning for locked textures as
  future work ([Minerals 15(7) 701](https://www.mdpi.com/2075-163X/15/7/701)). *Gap:* no
  published ML model of UG2 PGM recovery from liberation data was found.
- **What to build:** say plainly that optical microscopy measures the PGM
  *carriers* (BMS, chromite, silicates) and their association. Use SEM mode of
  occurrence to link carriers to PGM behaviour per orebody. That is a defensible
  claim; "we see the PGMs" is not.

### S4: 2D index is not liberation → report Moodley classes, correct for stereology

- 2D sections overstate liberation; one study found 2D areal grades off by more
  than 100% in some classes, and uncorrected 2D data can mislead
  ([Minerals 7(11) 222](https://www.mdpi.com/2075-163X/7/11/222);
  [UCL accepted manuscript](https://discovery-pp.ucl.ac.uk/id/eprint/10049193/1/J251_Reyes_Minerals_Eng_accepted_20170421.pdf)).
- µCT avoids the bias but is slow and costly; numerical corrections exist (Gay
  and Morrison 2006) but are rarely applied in practice
  ([Springer review](https://link.springer.com/article/10.1007/s00501-021-01135-w)).
- **What to build:** output the five Moodley exposure classes, not one index.
  Calibrate a 2D→3D correction once per orebody on a few µCT samples.

### S5: invented thresholds → recovery at risk from class kinetics

- Replace the three placeholder thresholds with Moodley's Eq. 8: class fractions
  from KHANYA × class rates fitted from the host's own batch flotation tests.
  Output: "percentage points of recovery at risk from locked and middling
  carriers", which a metallurgist can check.
- Extend the advice from regrind-or-continue to Moodley's three diagnoses: poor
  liberation (comminution), exposed sulphide floating badly (reagents or
  hydrodynamics), fine gangue in concentrate (water recovery and froth).

### S6: uncertainty under drift → adaptive conformal, named sources

- Adaptive conformal prediction was tested on a full-scale plant soft sensor
  under real process drift (wastewater pH)
  ([Lee and Lee, PMLR v329](https://proceedings.mlr.press/v329/lee26a.html)).
  Conformal work in mining exists for geotechnical monitoring
  ([SBA](https://www.sba.org.br/open_journal_systems/index.php/cba/article/view/4309)).
  *Gap:* no deployed conformal soft sensor in comminution or flotation found.
- **What to build:** class-conditional (Mondrian) and drift-adaptive bands;
  state, as Moodley does, which uncertainty each band covers and which it
  does not.

### S3/S7: generalisation to unseen ore → foundation models and domain adaptation

- A 2026 University of Liège thesis found zero-shot Segment Anything (SAM)
  comparable to a fully trained DeepLabV3+ on reflected-light iron and copper
  ore grains, with better cross-dataset generalisation, while DeepLabV3+
  degraded badly outside its training domain
  ([MatheO](https://matheo.uliege.be/handle/2268.2/25195)). KHANYA uses DeepLabV3.
- Segmenteverygrain combines SAM with a U-Net for grain measurement
  ([JOSS 2025](https://www.theoj.org/joss-papers/joss.07953/10.21105.joss.07953.pdf)).
- A preprint applies domain adaptation to reflected-light mineral segmentation
  ([Preprints 202412.0572](https://www.preprints.org/manuscript/202412.0572/v1));
  cross-domain few-shot segmentation methods (PATNet, ECCV 2022; adapter
  methods, [arXiv 2404.10322](https://arxiv.org/abs/2404.10322)) are untested on ore.
- **What to build:** SAM-style grain proposals plus a small mineral classifier
  trained on correlative labels. Benchmark on a held-out *ore type*.

### S8: not real time → three sensing tiers

| Tier | Latency | Evidence | KHANYA role |
|---|---|---|---|
| At-line rapid section | minutes to an hour | build design | Core product: fast, cheap QEMSCAN complement per shift |
| On-belt hyperspectral / LIBS | seconds | Anglo American active hyperspectral sensing over conveyors, 2026 ([Geomechanics.io](https://www.geomechanics.io/news/article/anglo-american-active-hyperspectral-sensing-real-time-ore-control-for-plant-engineers)); Metaspectral ORES ([Global Mining Review](https://www.globalminingreview.com/technology-digitalisation/28052024/metaspectral-introduces-ore-resource-evaluation-system/)); CRC ORE/NRC LIBS ([Mining Technology](https://www.mining-technology.com/news/crc-ore-nrc-canada-libs-minerology/)) | Calibrate belt sensors against at-line mineralogy |
| Froth and feed vision | seconds | Platinum froth grade estimated from image features (Marais and Aldrich, SAIMM 2011; [Curtin](https://espace.curtin.edu.au/handle/20.500.11937/29753?show=full)); review notes no automated PGM control yet ([Stellenbosch](https://scholar.sun.ac.za:443/handle/10019.1/12170)); feed size by Metso RockSense ([brochure](https://metso.com/globalassets/pdfs-and-other-downloads/rocksense3d-brochure-4769-mng-en-web.pdf)) | Later: link feed mineralogy to froth response |

*Gap:* no published model was found that predicts ball-mill throughput from
online feed imaging. That is an opening, and REEFPRINT's hardness half sits in it.

### Chromite: the UG2-specific value

- UG2 concentrates typically carry about 3% Cr₂O₃, which causes smelter
  problems; a secondary milling route cut Cr₂O₃ entrainment by over 30%
  ([UKZN thesis](https://researchspace.ukzn.ac.za/items/74f067f3-9248-48be-bfe5-1c49205c49ce)).
- A mid-circuit chrome extraction plant held chromite under 2.2% at about 80%
  PGM recovery ([WCE 2012](https://www.iaeng.org/publication/WCE2012/WCE2012_pp1482-1486.pdf)).
- Regression predicting UG2 tailings chromite: R² 0.66 for recovery, 0.18 for
  grade ([UJ](https://pure.uj.ac.za/en/publications/application-of-multiple-linear-regression-mlr-analysis-on-the-con/)).
- Valterra and Tharisa are exploring fine chrome recovery
  ([Engineering News, Oct 2026](https://engineeringnews.co.za/article/valterra-joins-northam-as-a-buyer-of-tharisa-pgm-concentrate-2026-10-15)).
- **What to build:** chromite liberation and fines as a measured, at-line
  "Cr₂O₃ risk" signal. It is the UG2 problem producers already pay to solve.

---

## 5. What the product becomes

An **at-line process-mineralogy instrument for UG2 and Merensky feed**: polished
section in, the five liberation classes of BMS and chromite out, converted to
recovery and Cr₂O₃ at risk through host-fitted class kinetics, with drift-aware
uncertainty and refusal. It complements QEMSCAN (fast and cheap per shift,
calibrated against it), and later calibrates on-belt sensors. It does not claim
to see PGM grains.

---

## 6. Getting backing

| Who | Why they care | The ask | Evidence they need first |
|---|---|---|---|
| Mintek Minerals Processing and Characterisation Cluster (Moodley, Govender, Tshilongo) | Their paper needs fast feed liberation; they hold QEMSCAN and flotation testwork | A joint study: replicate Moodley on UG2 with KHANYA estimating feed classes; co-authorship | MOTT IP note; a written method |
| Mintek Measurement and Control (FloatStar, MillStar) | Channel to plants already running APC | Integration test as an advisory input | Shadow-mode safety design |
| Host producers (Valterra, Implats, Sibanye-Stillwater, Northam) | Recovery and Cr₂O₃ cost money | R210,000 three-month feasibility stage on their ore | Paired-sample results; gates |
| TIA | About R100m into mining tech across 15 projects over a decade ([Business Day, Feb 2026](https://www.businessday.co.za/business-times/2026-02-08-modernising-mining-for-the-critical-minerals-era-sas-competitive-edge/)); 2023 call listed mining digitisation ([TIA](https://www.tia.org.za/core/uploads/2023/09/call-for-proposal-energy.pdf)) | Seed via Mintek or Wits, then TDF for the pilot | Host partner and settled IP. No open 2026 call found; check funding.tia.org.za |
| Mandela Mining Precinct / SAMERDI | 2025–2030 RDI strategy; funded by DSTI, Treasury and the Minerals Council ([Mining Weekly](https://www.miningweekly.com/article/programmes-driving-tech-development-2026-02-13)) | Showcase slot; route to the Minerals Council | No open call found; contact the precinct |
| UCT Centre for Minerals Research, Wits Mining Institute, Stellenbosch process monitoring group | µCT, process mineralogy and froth-vision expertise; students | Co-supervised master's projects on S4 and S6 | A shared dataset |

**How to win them:** lead with the honest limits, a paired-sample validation
plan, and a small gated ask. Publish the first UG2 result with Mintek, so the
claim is reviewed before it is sold.
