# KHANYA / REEFPRINT: field chemistry, microscopy, and geological visualization

Investigation date: 29 September 2026. Recommendation and architecture proposal; no application code changed, no models trained, and no hardware connection tested.

## Recommendation

**Updated after the user's clarification:** the immediate goal is Problem 3 with no instruments and a free software/data budget. Use the accompanying [KHANYA-HACKATHON-STRATEGY-2026-09-29.md](KHANYA-HACKATHON-STRATEGY-2026-09-29.md) as the primary recommendation. Keep the microscope-image model and demonstrate an auditable, simulated process-control response. XRF, field capture and geological 3D are a future extension, not prerequisites or the recommended hackathon pivot.

For that future extension, evolve KHANYA into a sample-centred evidence system. Keep its existing microscopy-to-advisory pipeline as the analytical core. Add field provenance and imported XRF chemistry first; add 3D presentation when appropriate geometry exists. A full pivot to exploration prospectivity would require a different target user, datasets, validation, and decision workflow.

The current repository records an October 1 submission deadline and an offline laptop demonstration. Under that constraint, field capture and 3D geology belong in a clearly identified extension roadmap, not an untested replacement for the submission. First improve acquisition quality and expose where the present model cannot be trusted.

## 1. What was actually inspected

The GitHub connector could not access the repository, but the configured GitHub CLI could. The live `main` head was verified as `9181668cffd9350211a9a8a2cf0b44c80f8deaee`, dated September 15, 2026. Local `khanya/main` was at `ca2e02f`; the live comparison was checked, and the relevant newer illumination report was read directly. The local REEFPRINT checkout was at `ae5f749`.

Evidence inspected includes KHANYA's model builder, dataset loader, checkpoint configuration, dashboard inference and input checks, advisor, status, README, newer commit corrections, and illumination study. REEFPRINT's status, shared workboard, polarimetry decision and existing modules were also inspected. This was a source and research review, not an independent reproduction of the experiments.

Current components:

| Component | What the inspected code does | Consequence |
|---|---|---|
| `src/segmentation/model.py` | Torchvision DeepLabV3, ResNet-50 backbone, adapted segmentation heads | This is the learned CV component; it is not DeepLabV3+ or an LLM |
| `src/segmentation/train_patches.py` | Patch training, native-resolution sliding-window prediction, single-field inference | Retain this interface for microscope images |
| `checkpoints/lumenstone_s2_patches/best.pt` | Default dashboard checkpoint path | Model code is not trained weights; the file must be supplied and hashed separately. Its availability and inference were not verified here |
| `src/modal.py` | Mask geometry, phase area fractions, topology refinement and apparent 2D sulphide association | These are deterministic measurements of a predicted mask, not direct mass assay or 3D liberation |
| `src/advisor.py` | Role-based decision rules and an empirical uncertainty margin | Several thresholds remain placeholders; the fixed margin is not a guarantee on new field imagery |
| `dashboard/app.py` | Offline Streamlit bridge with local HTML rendering, upload inference, live field and full-section modes | A functioning UI route exists in code; no wholesale rewrite is necessary to add sample metadata |
| `dashboard/opcua.py` and REEFPRINT integration modules | Advisory publishing/refusal integration code | A software integration path is not evidence of deployment to a production plant |
| REEFPRINT polarimetry and bridge | Geometry checks, registration work, Stokes/extinction calculations | Research extension; ADR-0004 explicitly keeps it separate from the submission's main claim |

The default S2 label set includes chalcopyrite, magnetite, pyrrhotite, pentlandite and background. Repository evidence reports a failed magnetite output channel on the evaluated S2 checkpoint. Do not describe all five classes as successfully detected. S2's Norilsk microscopy evidence does not establish performance on Bushveld ore or outdoor phone photographs.

The newer illumination report is especially important: on centre 512-pixel crops, advice changed in 5/10 real V1 re-imaging pairs with the S1 checkpoint, and 8/12 S2 sections under a synthetic exposure shift. These are small fragility studies, not production error rates. They justify capture standardization, quality checks and explicit refusal before adding more confident-looking visualization.

Repository sources: [model](https://github.com/Sibusiso-K/KHANYA/blob/9181668cffd9350211a9a8a2cf0b44c80f8deaee/src/segmentation/model.py), [dashboard](https://github.com/Sibusiso-K/KHANYA/blob/9181668cffd9350211a9a8a2cf0b44c80f8deaee/dashboard/app.py), [advisor](https://github.com/Sibusiso-K/KHANYA/blob/9181668cffd9350211a9a8a2cf0b44c80f8deaee/src/advisor.py), [illumination evidence](https://github.com/Sibusiso-K/KHANYA/blob/9181668cffd9350211a9a8a2cf0b44c80f8deaee/reports/ILLUMINATION-STABILITY-2026-09-15.md).

## 2. What the named tools contribute

**FieldMove Clino:** smartphone geological compass-clinometer, georeferenced notes, photos, rock-unit observations and offline mapping. Petex documents CSV, MOVE and KMZ exports. It supplies structural and field context. It is not the XRF driver, mineral classifier or subsurface inference engine. Import its CSV and retain the original project/export. Preserve whether orientation means strike/dip or dip-direction/dip, and magnetic versus true north. Check phone compass readings against a suitable reference away from the analyzer and other magnetic interference. [Petex](https://www.petex.com/products/move-suite/digital-field-mapping/)

**QGIS:** desktop GIS for combining sample locations, assays, geological boundaries, topography, imagery and coordinate systems. Its 3D view can display supported spatial layers. It is useful for checking spatial data and preparing project layers, without being a mineral-identification model. Use GeoPackage for the first portable spatial store; retain explicit horizontal and vertical reference systems. [QGIS 3D documentation](https://docs.qgis.org/3.40/en/docs/user_manual/map_views/3d_map_view.html)

**QField:** an optional alternative to building a phone app immediately. Configure a sample form and offline QGIS project, capture location/photos/notes in the field, then synchronize. Evaluate it as the main field-record application; retain Clino where its structural workflow is useful. Do not force the operator to enter the same sample twice. An XRF connection still needs its own supported import or adapter. [QField project](https://github.com/opengisch/QField)

**Leapfrog Geo:** commercial specialist software for constructing interpreted 3D geology from drillholes, contacts, orientations and other geological evidence. It supports CSV point/drillhole inputs and multiple mesh formats. Use it as a geologist's modelling environment if a licence is already available; exchange approved formats with KHANYA. Verify version-specific exports and licence entitlements before promising automatic integration. Its implicit modelling is not an ability to see underground from XRF points. [Seequent product](https://www.seequent.com/products-solutions/leapfrog-geo/), [formats](https://www.seequent.com/help-support/leapfrog-geo/)

**XRF:** X-rays excite characteristic fluorescence; instrument calibration estimates element concentrations in the interrogated material. It provides chemical evidence, not a unique mineral phase assignment. XRD supplies complementary crystal-structure evidence. Results depend on instrument configuration, matrix, preparation, acquisition time and detection limits. Method 6200 is useful background for field QA, but its 2007 instrument capabilities and soil/sediment procedures must not be transplanted wholesale to current ore analyzers. [Bruker mineralogy](https://www.bruker.com/en/applications/academia-materials-science/mineralogy/x-ray-bulk-mineralogy.html), [EPA method](https://www.epa.gov/sites/default/files/2015-12/documents/6200.pdf)

**A web viewer:** makes these records understandable to people who do not operate desktop geology software. CesiumJS is appropriate for georeferenced terrain, site assets and tiled 3D scenes. A small sample mesh needs only a lightweight glTF viewer. Neither renderer computes mineral chemistry or validates a geological interpretation. [CesiumJS](https://cesium.com/platform/cesiumjs)

## 3. Proposed pipeline and deployment

The phone is the field notebook and sample-identity hub. XRF and microscopy remain separate evidence-producing branches.

1. Create a sample UUID and a human-readable/QR label. Record project, location, location accuracy, date, operator and specimen type.
2. Take field photographs and notes; capture structural observations where relevant. Store locally when offline.
3. Attach the instrument's XRF export to that sample. Preserve the original file and original reading identifier. Import results into a normalized assay table without discarding non-detect flags or units.
4. Link laboratory preparation, polished section and microscope fields back to the same sample. A split or subsample gets its own child identifier.
5. Run microscope quality checks, then the existing segmentation model. Calculate 2D phase areas and association measurements. Record refusals and uncertainty, including the field of view and image scale where calibrated.
6. Compare chemistry and image evidence at a compatible sampling scale. An XRF spot, a pulverized bulk sample and a microscope field do not cover the same material merely because they share a sample ID. Start with a visible evidence comparison, not automatic numeric fusion.
7. Present the sample on a map and, if available, its reconstructed surface or interpreted geological context. Every colored output retains a source, method and evidence status.
8. Export reviewed spatial layers to QGIS and supported files to Leapfrog. Keep model versions and interpretation revisions.

**First connection method:** original vendor CSV/JSON export imported through the phone's file/share workflow or a laptop. This is useful before direct pairing exists. A phone operating-system connection is not required for every instrument path: XRF-to-vendor-software-to-laptop-to-sample-record is a valid fallback.

**Later connection method:** instrument-specific vendor app/API/SDK, Bluetooth or Wi-Fi adapter. For example, Evident documents optional wireless connectivity for Vanta, but this does not establish an open protocol for any given instrument. Brand, exact model, firmware, enabled options, mobile OS, export sample and SDK access remain unresolved. [Vanta](https://ims.evidentscientific.com/en/products/xrf-analyzers/vanta)

**Deployment recommendation:** retain the existing offline laptop pipeline for the demonstration; run models locally and serve the dashboard to its browser. A field phone can exchange records by cable/file or a local network where supported. For a later multi-user pilot, put an API over the same analysis library, keep raw assets in file/object storage, and use PostGIS for the shared spatial catalogue. Store-and-forward queues, durable UUIDs and an audit trail make intermittent connectivity manageable. A native acquisition adapter is justified only if the selected instrument requires it.

Minimum data contract:

- Sample: UUID, label, project, parent sample/subsample, specimen/preparation type, collection time, operator.
- Location: coordinates, CRS, elevation datum, accuracy, survey method; laboratory images have specimen coordinates separate from world coordinates.
- Assay: instrument/serial, firmware, method, reading ID, exposure duration, element, numeric value, unit, non-detect/limit, reported uncertainty, calibration/QC status, original-file hash.
- Image: microscope/phone modality, magnification or calibrated scale, illumination, capture settings, field coordinates, raw-file hash.
- Analysis: code version, checkpoint hash, class codebook, preprocessing version, calibration set/version, input hashes, area denominators, quality flags, refusal reason.
- Spatial model: source observations, author, CRS, method, extent, resolution, constraints, model version, support/uncertainty definition.

Element wt%, oxide-equivalent wt%, pixel area%, inferred volume% and model probability must remain distinct fields. Below detection is a censored result, not zero. An element outside the instrument's measurement capability is unknown, not absent.

## 4. Where computer vision and AI belong

| Stage | Method | Where it runs | Why / prerequisites |
|---|---|---|---|
| Capture checks | Blur, exposure, saturation, scale checks; later a validated domain detector | Phone for lightweight checks; laptop for microscopy checks | Improves repeatability and stops unusable inputs early |
| Mineral pixels | Existing DeepLabV3–ResNet-50 with KHANYA-trained weights | Laptop CPU/GPU; later server or validated edge export | Retains the trained task and existing measurements; new ore/phone domains require new validation |
| Label creation | Optional SAM 2.1 assisted masks, corrected and named by an expert | Annotation workstation | Speeds outline work; generic segmentation does not determine mineral identity |
| Chemical consistency | Expert constraints initially; Bayesian or calibrated tabular model only after paired data exist | Laptop/backend | Ranks plausible explanations and identifies conflicts; must allow unresolved mixtures |
| Exterior 3D | COLMAP photogrammetry from overlapping photographs | Offline preprocessing workstation | Reconstructs visible surface and camera geometry; does not recover internal mineral volumes |
| Geological structure | Leapfrog, or evaluate GemPy with geological constraints | Geologist's workstation/backend | Uses contacts and orientations to model geology; interpretation needs geologist review |
| Nearby target ranking | Spatial baseline, then optionally calibrated ML | Backend/workstation | Requires deposit-specific training and spatially held-out evaluation |
| Notes and reporting | Optional speech/OCR/LLM assist with human confirmation | Phone/laptop, or configured service | Structures notes and cites existing records; no mineral verdict or plant command delegated to generated prose |

The existing model's code and weights are separate artifacts. Load the project checkpoint, not merely Torchvision's generic pretrained weights. The reviewed constructor pins its COCO-with-VOC initialization and disables backbone download during evaluation. For a later model registry, bundle weight hash, modality, supported phases, training domains, preprocessing and calibration records.

SAM source and checkpoints: [Meta SAM 2](https://github.com/facebookresearch/sam2). Geometry reconstruction: [COLMAP tutorial](https://colmap.github.io/tutorial). Alternative geological modelling research: [GemPy](https://www.gempy.org/). These are candidates for specific jobs, not recommendations to install every tool or replace the present checkpoint.

A recent research lead is *Minerals in the Wild* (August 2026), whose abstract describes 1,132 European specimens with paired hyperspectral imaging and XRF. It is relevant to future multimodal chemistry research, but not evidence of phone-RGB mineral recognition or a paired UG2 microscopy dataset. Only the abstract was reviewed here; data access, licence, sensor compatibility and transfer validity remain unverified. [Paper](https://arxiv.org/abs/2608.30537)

## 5. Alternative minerals and adjacent minerals are separate problems

**Alternative identity:** a mineral region may be consistent with several phases. Return a candidate set with supporting/contradicting observations and the next useful measurement. Do not relabel a failed class as whichever class remains. A class missing from the trained codebook cannot be discovered by taking the second-largest softmax score. In particular, magnetite not predicted by the present checkpoint is not evidence that magnetite is absent.

**Grain adjacency:** after phase segmentation, derive which labelled regions touch in the 2D image and how much boundary they share. Exclude resin, handle ambiguous boundary pixels and disclose the minimum size/measurement resolution. This is image topology and can be mostly deterministic. It does not establish true 3D liberation or the chemistry of unseen grains.

**Geological association:** a mineral or elemental pattern can make nearby occurrences more plausible in a particular deposit model. Treat this as a conditional exploration hypothesis. It needs lithology, structures, representative samples and validation by spatial blocks/boreholes. Absence of one target alone is not evidence of another, and spatial proximity alone does not prove a shared deposit mechanism.

**Evidence fusion:** learn on paired observations from the same, characterized sampling unit. Compare image-only, chemistry-only, geology-only and combined baselines on held-out specimens/localities. Avoid double-counting correlated evidence. Report calibration and abstention alongside accuracy. For non-detects, account for the instrument's limit and sample support rather than a binary present/absent switch.

## 6. The most convincing visualization

Use a linked journey: **site → sample → microscope field → grain → evidence → suggested next action**. Keep the selected sample synchronized across the map, chemistry record and image viewer.

At microscope scale, show the original micrograph with an opacity-controlled phase mask, fixed phase colors, visible unknown regions, and click-to-inspect grains. Put chemistry alongside it, labelled with its sampling scale. Phase composition is a bar chart in image-area units; elemental composition is a separate chart in assay units. Never combine them into one composition pie.

At specimen scale, show a photo-derived mesh with the actual XRF spot locations and linked cut-section locations. A spot measurement colors its footprint or marker. It must not paint the entire object as if it were an elemental scan. Show photogrammetry texture separately from any analytical overlay. A 2D microscope mask remains a section plane, not an invented internal mineral volume.

At site scale, use terrain and sample locations first. Add boreholes and geologist-authored surfaces when available. Provide observation-only, interpretation and uncertainty/support views; a clip plane should expose the real observation locations behind the model. Use categorical colors for geological units, a sequential scale for an element concentration, and a separate visual channel for uncertainty. Unsampled or unsupported regions remain visibly unknown.

There are three different 3D claims: reconstructed exterior, interpreted subsurface, and measured internal structure. Photogrammetry supports the first, geological modelling supports the second, and CT/serial sections or another suitable volumetric measurement is needed for the third. A beautiful renderer cannot upgrade one into another.

The strongest demonstration is a traceable change: select a sample, show the evidence, show how uncertainty changes when a relevant measurement is added, and show why a recommendation is issued or withheld. Use paired real data if available; otherwise label a worked scenario as illustrative and keep it separate from measured performance.

## 7. Roadmap and gates

**Before the recorded October 1 deadline:** preserve the checkpoint and offline demonstration; make the valid input modality explicit; display phase masks, the apparent 2D association output, limitations and an honest refusal example. Treat the field/3D architecture as a roadmap unless an addition is already stable. Do not claim an XRF connection or plant deployment that has not been demonstrated.

**First extension:** implement one sample record and one vendor export parser. Link one field observation, one assay and one microscope analysis; export a map-ready file. Validate that units, sample IDs, detection flags and timestamps survive round trips. Duplicate imports must not create duplicate assays. A supported failure should be visible rather than silently attached to the wrong sample.

**Second extension:** validate capture repeatability, quality/refusal behavior and a chemistry-versus-image comparison on genuinely paired data. Gather representative examples from the intended ore body. The acquisition/illumination finding makes this a higher-value scientific improvement than changing the backbone for appearance alone.

**Third extension:** add measured sample geometry and 3D navigation. If moving into geological modelling, obtain surveyed locations, contacts, orientations and/or borehole evidence before creating interpreted volumes. Evaluate spatial predictions away from the sites used to build them; report uncertainty and unsupported regions.

**Longer-term pivot gate:** move to exploration targeting only if a geologist user confirms the decision workflow and representative spatial data exist. Keep exploration hypotheses and plant-process advisory outputs distinct. They have different validation targets.

Outstanding inputs: XRF make/model and enabled connectivity; mobile OS; a real export schema; intended first ore/mineral setting; available paired assays and microscopy; surveyed 3D or drillhole data; access to Leapfrog; and whether the immediate goal remains the recorded competition submission.
