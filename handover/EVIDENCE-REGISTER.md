# Evidence register — checked 29 September 2026

Use these labels on slides and reports: **external evidence**, **historical repository result**, **new measured result**, **simulation**, **target**, **commercial assumption**. These are different kinds of evidence. No new model training, inference benchmark, plant experiment or accuracy replication occurred during this planning turn.

## Claims that may enter the pitch

| ID | Claim and source | Status and limits |
|---|---|---|
| E1 | User-supplied Problem 3 screenshot: laboratory SEM/XRD characterisation can take days; deliver three mineral phases, accuracy report and plant-parameter demonstration. Organizer email: ten-minute PowerPoint due 1 October 2026, covering six pitch themes. | Primary supplied brief. Attribute the turnaround statement to the challenge; no universal or site-specific measured duration. Email screenshot contains no deadline hour. Do not expose personal contact details in deck/repo. |
| E2 | [Blue Cube MQi technical data sheet](https://www.draslovka.com/content/files/downloads/Blue%20Cube%20-%20Slurry%20Analyzer%20Tech%20Data%20Sheet.pdf), page 1: spectroscopy, 15-second measurement time, industrial DCS interfaces. | Manufacturer specification, not an independent speed comparison or our capability. Demonstrates existing competition. |
| E3 | [Mintek history](https://mintek.co.za/corporate-profile/history.html): FloatStar industrial test in 1993 and commercialisation in 1994. [Mintek industrial Pb/Zn case study](https://mintek.co.za/clusters/miningmaterialsautomation/measurement-and-control/mac-casestudies/flotation-circuit-stability-using-the-minteks-floatstar-level-stabiliser-control-system.pdf.pdf): two-week daily ON/OFF campaign, recovery improvements reported as 0.51% Pb and 0.12% Zn, with grade maintained. | Primary operator/developer case study; search-indexed full abstract and test description inspected. Preserve the source's percentage notation; do not silently reinterpret it as percentage points. Different system/site, not KHANYA savings or proof of CV's contribution. |
| E4 | [LumenStone official dataset](https://imaging.cs.msu.ru/en/research/geology/lumenstone): S2 v2 has 37 training and 12 test images, reflected-light polished sections, pixel masks, Norilsk assemblage with chalcopyrite, pyrrhotite, pentlandite and magnetite. | Real source data, not generated ore. Research-use terms; explicit blanket commercial/redistribution rights not established. The data is not South African plant feed. |
| E5 | [Historical S2 benchmark JSON](https://github.com/Sibusiso-K/KHANYA/blob/9181668cffd9350211a9a8a2cf0b44c80f8deaee/reports/benchmark_s2_patches.json): 0.572533 pooled mean IoU and 0.891357 pixel accuracy. | Source read at fixed commit. Not replicated here; checkpoint absent. Includes five classes and failed magnetite. No new model may inherit these numbers. |
| E6 | [Illumination report](https://github.com/Sibusiso-K/KHANYA/blob/9181668cffd9350211a9a8a2cf0b44c80f8deaee/reports/ILLUMINATION-STABILITY-2026-09-15.md): S2 synthetic -35 RGB control, n=12, advice changes 8/12; real V1/S1 paired re-imaging n=10, changes 5/10. | Historical repository experiments on centre 512 crops. V1 has no masks: repeatability, not accuracy. Its model is S1, not S2. Both small samples. The gate does not already solve this. |
| E7 | [Bachmann dataset, Mendeley v1](https://data.mendeley.com/datasets/dc8jcnbcvk/1), DOI 10.17632/dc8jcnbcvk.1. Local CSV has 1,205 rows; original Filter column retains 1,193, then analyses apply their own missing-value criteria. | Real South African chromitite chemistry. No coordinates/collar/survey in local CSV and no matched LumenStone imagery. ICP-labelled analytes must remain ICP. Use dataset DOI: old local SOURCE.md has inconsistent journal metadata. |
| E8 | [Molycop OreVia Rock](https://www.molycop.com/products-and-services/measurement-and-analytics/process-characterisation/orevia/orevia-rock): vision-based rock/particle analysis and plant-system integration. | Existing commercial overlap; do not claim first vision-to-control platform or use its name. No verified comparative price/performance obtained. |
| E9 | [ZEISS mining applications](https://www.zeiss.com/microscopy/us/applications/raw-materials-and-industrial-rd/mining.html): automated mineralogy and 3D imaging workflows. | Existing instrumentation-based capabilities; our 2D proxy is not equivalent to their mineralogy/3D measurement. |
| E10 | [IBM Quantum plans](https://quantum.cloud.ibm.com/docs/en/guides/plans-overview): Open Plan up to 10 QPU minutes per 28-day rolling window; page also lists an opt-in promotion. | Access availability is not evidence of algorithmic advantage. No quantum dependency or signup required for MVP. Recheck terms if later used. |
| E11 | [Colab FAQ](https://research.google.com/colaboratory/faq.html): free interactive GPU resources exist but availability, runtime and limits are not guaranteed. | Training contingency only. Do not promise a specific free GPU or use Colab as production hosting. No paid subscription required by plan. |
| E12 | [USGS mafic/ultramafic images, v2](https://www.usgs.gov/data/thin-section-images-hand-samples-and-drill-core-mafic-ultramafic-rocks), DOI 10.5066/P1SUMMMI, CC0. | Future cross-lab imagery lead. No expert pixel masks established; no supervised accuracy claim from unlabelled images. Verify record-to-coordinate association before mapping. |
| E13 | [USGS Geochemical Data Portal](https://www.usgs.gov/tools/geochemical-data-portal-rock-sediment-soil-and-mineral-samples-united-states-and-territories) | Geographic assay source lead. A selected subset, coordinate fields, permissions and hashes are still to be verified; not staged locally. Preserve US geography. |
| E14 | [QGIS 3D map documentation](https://docs.qgis.org/3.40/en/docs/user_manual/map_views/3d_map_view.html), [QField external sensors](https://docs.qfield.org/how-to/advanced-how-tos/sensors/), [CesiumJS](https://cesium.com/platform/cesiumjs/), [GemPy](https://www.gempy.org/) | Tool capabilities, not evidence our integration works. Free library code does not imply every hosted service or terrain dataset is free. |
| E15 | [PyMca](https://github.com/silx-kit/pymca), [XMI-MSIM](https://github.com/tschoonj/xmimsim) | Real open-source spectrum tools; simulation labels and instrument calibration remain necessary. Not installed for this plan. |

## Historical S2 results: the table to show honestly

From E5, plain-border protocol, dataset-wide confusion accumulation:

| Class | IoU |
|---|---:|
| Background | 0.8709 |
| Chalcopyrite | 0.5755 |
| Magnetite | 0.0000 |
| Pyrrhotite | 0.8695 |
| Pentlandite | 0.5468 |
| Mean across all five classes | 0.5725 |

Pixel accuracy 89.14% is dominated by frequent/easier pixels. It is not “89% mineral identification accuracy,” confidence, plant recovery, or evidence that every class works. Keep the failed class in the report. No baseline target should encourage hiding it.

The new training report must include class precision/recall/IoU, confusion matrix, image/sample counts, held-out IDs, model/data hashes, full-section versus crop protocol, hardware, cold/warm runtime, and examples of errors. Reusing the public test set after extensive historical development makes it a benchmark, not an untouched prospective external validation set. A later site holdout must be newly collected and grouped by specimen/site/time.

The S1 benchmark correction is recorded in [the fixed-commit report](https://github.com/Sibusiso-K/KHANYA/blob/9181668cffd9350211a9a8a2cf0b44c80f8deaee/reports/S1-V1-LIKE-FOR-LIKE-2026-09-15.md): exact 16-image v1 protocol gives 0.6881 plain / 0.7224 void-border IoU. Do not compare the old 20-image 0.7116 score directly with a published 16-image result. S1 is optional and not the selected deadline task.

## Proof that data is real: required evidence bundle

For each dataset, archive source URL/DOI, retrieval date, version, licence text/reference, archive byte size and SHA256. For each run, store Git SHA, environment lock, seed, split manifest, training config, model SHA, metrics JSON and run timestamp. Trace each plotted point or screenshot to its actual source row/image and prediction file. A dataset licence and a model architecture do not prove model accuracy; held-out scoring does.

Keep raw data and trained weights outside Git unless redistribution is explicitly cleared and an appropriate artifact destination is chosen. The existing project has private Kaggle mirrors; its own report `REDISTRIBUTION-CONTRADICTION-2026-09-15.md` records uncertainty. Do not duplicate them as a workaround. Keep this sprint's research dataset local or in a private authorised training runtime; commercial deployment needs a separate rights decision or site-owned data.

## Claims to replace before pitching

| Avoid | Use instead |
|---|---|
| “We reduce analysis from days to seconds” | “The brief describes days of delay. We will measure inference latency separately from sample preparation and total turnaround.” |
| “We achieved 89% accuracy” on new weights | “Historical S2 pixel accuracy was 89.14%; here is the new model's per-class report.” |
| “XRF identifies these mineral phases” | “Assay chemistry supports interpretation; image/spectral evidence and calibration distinguish phases.” |
| “This is the ore body below the surface” | “These are located measurements on terrain,” or a clearly hypothetical schematic. |
| “Our AI increases recovery by X%” | “Our simulator demonstrates the command path. Recovery benefit remains a pilot endpoint.” |
| “Confidence guarantees safety” | “These empirical checks screen known failure modes; untested shifts can still fail.” |
| “We are the first” | “We combine traceable mineral evidence and decision checks in this demonstrated workflow.” |
| “Quantum makes it more accurate” | “No relevant advantage has been established; quantum is deferred.” |

## What is not yet evidenced

No new trained model, external laboratory validation, processability/recovery ground truth, paired assay+image+geography dataset, calibrated actuator relationship, customer interviews, willingness-to-pay study, confirmed product name, or measured production capacity. The documents provide methods and explicit assumptions for obtaining these, rather than fabricating certainty.
