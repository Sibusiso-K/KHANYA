# Feasibility, value and pathway

## Who uses it, who benefits, who pays

The first buyer hypothesis is a concentrator technical manager or metallurgical laboratory manager. Daily users are mineralogists validating phase interpretation, metallurgists deciding whether to investigate grinding/flotation settings, and operators reviewing authorised actions. Sample technicians/geologists create records; process-control and OT engineers integrate interfaces. Plant owners gain only if measured operating benefit exceeds acquisition, preparation, maintenance and integration costs.

Start with an on-premises workstation beside an existing lab. The sample path is: collect representative ore -> prepare polished section -> capture calibrated image -> infer/inspect -> review advisory -> controlled plant or laboratory trial. The current public-image replay begins at capture; that boundary must be visible. Later, trained imaging on a side-stream/automated preparation system could reduce acquisition delay, but it requires hardware and an independent validation project.

## Feasible now versus later

| Stage | Evidence needed to graduate |
|---|---|
| Hackathon workstation | Three-phase model, fresh report, measured runtime, offline replay, simulated parameter change |
| Laboratory shadow pilot | Site specimens and expert labels; repeatability; measured report turnaround; no process commands |
| Reviewed advisory pilot | Processability proxy compared with actual lab outcomes; metallurgist approves suggestions |
| Controlled intervention trial | Approved safe operating envelope, interlocks, OT/security review, rollback, matched baseline and statistical plan |
| Production service | Validated benefit, monitoring/drift alarms, support ownership, retraining rules, data/weight rights, installation/service agreements |

No chemistry-only or image-only shortcut establishes grindability, reagent response or recovery. Those require relevant measurements. Integration to PLC/SCADA is not just opening an OPC UA port: named tag ownership, units, timestamps, approval authority, authentication and change control must be agreed with site engineers.

## What impact to measure

| KPI | Measurement plan |
|---|---|
| Interpretation latency | Timestamp image available, analysis complete, expert-approved report; compare with manual workflow |
| Total turnaround | Timestamp collection/preparation/transport as well; state which intervals our system changes |
| Phase accuracy | Expert-labelled specimen-level holdout, per-class metrics and uncertainty; a second expert subset for reference disagreement |
| Decision reliability | Wrong accepted advisories, refusals, coverage, lighting/microscope repeatability; explicit false-action cost |
| Processability | Independently measured size/liberation and/or metallurgical test outcomes matched to the specimen; assess added value over chemistry-only baseline |
| Recovery and grade | Matched feed/product/tailings assays and mass balance; comparable ore windows and appropriate process residence times |
| Resource use | Reagent kg/t, energy kWh/t, water m3/t, throughput and operator time; test for trade-offs, not just improvement in one metric |
| Adoption | Workflow completion, overrides and reasons, staff time/training, downtime |

Choose primary endpoints before trial data is examined. Control for feed grade, ore type, size and operating state. Sample size and duration follow baseline variability and the minimum valuable effect; “100 samples” by itself is not statistical power. Suggested 50–100 specimens is an initial scoping budget, not proof of sufficient validation. Split by specimen and, where possible, collection period/site; never by neighbouring image patches.

## Proposed 8–12-week pilot after the hackathon

| Time | Work and people | Exit gate |
|---|---|---|
| Weeks 1–2 | Metallurgist/mineralogist, ML engineer, lab technician: use-case selection, rights, representative sampling, baseline time/quality measurements | Defined ore/domain, measurable question and approved data protocol |
| Weeks 3–4 | Lab imaging/labels, ML/app engineers: acquisition consistency, inference calibration, sample register | Reproducible paired records and locked evaluation plan |
| Weeks 5–6 | Shadow deployment; expert review and failure analysis | Useful accuracy/coverage and faster interpretation on site data; otherwise stop/revise |
| Weeks 7–8 | Control engineer and metallurgist: simulator/tag mapping, advisory workflow, hazard/change review | Approved bounded intervention plan or remain shadow-only |
| Weeks 9–12, conditional | Site-authorised crossover/controlled trial and evaluation | Quantified net value and no unacceptable grade/resource trade-off |

Site access, sample preparation and ground-truth turnaround can extend this schedule. Scale the domain gradually after success. Do not assume a Norilsk-trained model generalises to UG2/Bushveld. For a South African rollout, obtain local ore examples including the relevant gangue/chromite phases and retrain/revalidate.

## Pilot funding request: a transparent planning estimate

**Illustrative ask: R210,000 plus partner access to an existing laboratory, sample preparation/imaging equipment and site process records.** This is a bottom-up budget hypothesis, not supplier quotations or funding already secured. Currency ZAR; VAT/tax and new major instrument purchases excluded.

| Cost line | Assumed basis | ZAR |
|---|---|---:|
| Combined technical labour | 300 hours x R500/hour | 150,000 |
| Sample preparation/reference analysis allowance | Provisional pooled allowance; obtain lab quote | 20,000 |
| Local hardware/integration/travel allowance | Reuse instruments; small integration expenses only | 15,000 |
| Contingency | Explicit allowance | 25,000 |
| Total | | 210,000 |

Labour allocation assumption: ML 80h, app/data 60h, mineralogy/metallurgy 60h, controls 40h, evaluation 40h, coordination 20h. Some people can hold multiple roles; domain review cannot be replaced by an LLM. The rates and hours are not market-validated. If the partner cannot provide existing imaging/preparation hardware or ground truth, obtain quotes and revise the budget before committing. For a lower-cost first step, restrict scope to shadow interpretation of existing site images; defer plant integration.

## Running cost and capacity

- Hackathon: planned incremental software/API licence fees **R0**, using the existing laptop and public research data. Labour, electricity, connectivity and hardware are not free. No cloud is required for inference.
- Production: budget for instrument upkeep, expert review, image storage/backup, monitoring, retraining, cybersecurity and support. Cloud expense is optional and workload-dependent; no cloud vendor price was verified for this plan.
- Initial design target: one site, one inference worker, five active users and up to twenty read-only sessions after authentication is implemented and load-tested. This is a test target, **not measured capacity**. Current Streamlit is a demonstration architecture, not an enterprise multi-tenant service.
- Benchmark queueing before adding users. If one image needs t seconds, ideal single-worker ceiling is 3,600/t images/hour before I/O, contention and utilisation limits. At an assumed 5 seconds it is 720/hour theoretical; this is arithmetic, not a benchmark. Avoid running heavy inference on every UI rerender.
- Example storage planning: 200 images/day x 10 MB x 365 = 730,000 MB/year (about 730 GB decimal), before masks, replicas and backups. Replace those assumed sizes with measured files. Retention controls matter.
- For multiple sites: separate authenticated API, job queue, model registry, PostgreSQL/PostGIS and object storage; keep site deployments isolated initially. Add GPU workers only when measured throughput justifies them. Map visualisation need not wait on inference, and each site may need a different calibrated model.

## Commercial model to test

Sell the maintained, integrated workflow and support, rather than charge a plant for every click. A per-site or per-line annual licence with a defined number of model domains, support hours and update terms is more aligned with plant purchasing than a consumer subscription. Keep custom integration and laboratory services separate. Offer a paid pilot before an annual commitment.

**Price hypothesis for interviews:** R12,000/site/month equivalent on an annual contract, with R30,000–R75,000 one-off deployment/integration depending on scope. These are proposed prices, not observed competitor prices or established willingness to pay. Five interviews with prospective technical/lab managers should test budget ownership, procurement, data rights, preferred deployment and the minimum benefit needed.

Illustrative service unit economics: R12,000 revenue - (8 support hours x R500 + R1,000 infrastructure allowance) = R7,000/month contribution before sales, ongoing R&D, insurance, taxes, hardware and overhead; about 58% of revenue. Extra support or per-site model maintenance can eliminate this margin. Ten sites would be R120,000 monthly revenue at that assumed price, not a sales forecast or profit claim.

## Value calculation without invented benefits

Use site finance inputs:

`monthly incremental recovered metal = ore tonnes/month x feed metal mass fraction x absolute recovery change`

`monthly net value = extra payable metal x net contribution per tonne + verified avoided costs - added processing/support costs`

Illustrative only: 100,000 t/month x 0.01 feed fraction x 0.005 absolute recovery change = 5 t/month incremental metal. At an **assumed**, not quoted market, net contribution of R100,000/t, value before additional costs is R500,000/month. A 0.005 change means **0.5 percentage points**, not a 0.5% relative change. We have no evidence that KHANYA achieves this. Keep this example off the headline slide unless its assumptions are clearly visible; prefer a customer-specific sensitivity table once real inputs exist.

The strongest initial value claim to test may be reduced expert interpretation/reporting time rather than recovery. An honest pilot can still be valuable if recovery is unchanged but workload falls without degraded quality. Do not double-count labour savings already included in other cost reductions.

## Risks and decisions that could change the plan

1. New model cannot distinguish three phases in time: disclose, use the report to identify failures, and do not substitute reference masks as predictions.
2. Polished-section acquisition dominates delay: focus initial customer on lab productivity; investigate side-stream acquisition separately.
3. Quality gate rejects too much: compare accepted error and coverage, improve acquisition/calibration before claiming robustness.
4. Proxy does not correlate with process outcomes: retain phase reporting; remove unsupported process advice until matched tests exist.
5. Commercial rights remain unclear: use partner-owned data with explicit rights; software licences do not clear dataset/model rights.
6. No paired chemistry/geography exists: ship independent evidence views with explicit provenance; collect genuine matched samples in the pilot.

The hackathon ask should therefore be concrete: **one partner lab/concentrator, a mineralogist and process engineer, representative labelled samples, access to reference tests and operating records, and support for the staged R210,000 pilot subject to quotations and scope agreement.**
