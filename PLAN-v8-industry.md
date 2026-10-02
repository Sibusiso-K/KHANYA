# Plan: REEFPRINT v8 — a credible pilot package for a Bushveld concentrator, with one decision path done properly

_Round 1 revision by Claude (Opus 5.5), 2026-10-02, after Codex round 1 (40 findings, REVISE). What changed and why is in `PLAN-v8-REVIEW-LOG.md`._

**Evidence base:**
- `docs/17-industry-landscape-roles-and-money.md`: the dossier. Every fact is tagged [P] primary-read, [V] vendor, [N] news, or [S] search summary (not citable).
- `training/economics-20261002/economics.py`: scenario arithmetic with `reefprint.quantity` provenance.
- `docs/16-decision-value-chain.md`.
- The constitution (`CLAUDE.md`), `WORKBOARD.md` §0, and doctrine gates.

## Goal (narrowed)

Deliver what a Mintek judge and a plant manager would accept as **"a credible, costed, conditional pilot of one decision path, with the rest of the system honestly scoped"**. Not "start on Monday".

**What the system is:** an **incremental, uncertainty-aware ore-information layer** on top of existing analyser and APC workflows. It is not an unoccupied niche: Mintek's FloatStar already uses feed chemistry to suggest mass-pull setpoints; Blue Cube MQi, Plotlogic, MineSense and bulk-element analysers already exist.

**The one decision path built end to end:** belt hyperspectral → hardness (Bond WI) with a calibrated one-sided upper bound → a feed-rate proposal inside a site-approved envelope, with:
- a typed conservative fallback;
- a validity deadline tied to material arrival;
- escalation and a durable decision record;
- an honest simulated evaluation, including the refusal path.

**Supporting:**
- KHANYA's phase-identification evidence (the ≥3-phases deliverable);
- **validated spectral associations** from the belt sensor (not phase claims);
- corrected economics (incremental contribution and break-even, no gross headlines);
- an installation design computed from real datasheets;
- a pilot protocol with truth matching and an experimental design;
- a 2D map of historical Bushveld PGE sites.

## Approach (phased; each phase leaves the app shippable)

### Phase 1 — Correct what is already claimed (blocking)

**1. Throughput claim** (`value_chain.py`, docs/16, Value tab).
- **Withdraw "same overload risk".**
- **New upper bound: K-fold CV+** (Barber, Candès, Ramdas & Tibshirani 2021, "jackknife+", the K-fold variant). Per test parcel, the 90% one-sided upper bound is the ⌈(1−α)(n+1)⌉-th order statistic of {pred_i + signed out-of-fold residual R_j : j in the other folds}, with α = 0.10.
  - CV+'s guarantee is 1−2α in the worst case. Report the **empirical** one-sided exceedance with a cluster-bootstrap CI.
  - The v6 symmetric 80% `hi` is kept only as a comparator.
- **The deployed policy, simulated as deployed:**

  | OOD state | Feed set for |
  |---|---|
  | refused | the site envelope's conservative setting = training-fold P90 |
  | borderline | the stricter of the CV+ bound and P90 |
  | pass | the CV+ bound |

  Also included:
  - **a ramp limit**: ±X% feed change per parcel. X is ASSUMED and stated; sensitivity at 3 values.
  - **a stale-data rule**: if the prediction is older than the parcel's arrival time, fall back.
- **Pre-registered non-inferiority on overload share.** The margin is +3 pp. The test passes only if the one-sided 95% cluster-bootstrap upper bound of (belt − blind) overload share is ≤ +3 pp, and only then is a throughput gain reported as "at no worse than +3 pp overload risk".
- **Rename "energy shortfall" to "excess energy required"** (true/used − 1), and add the shortfall fraction 1 − used/true. No grind claims.
- **State plainly what the simulation omits:**
  - the comparison is against a static P90 rule, not against APC/feedback;
  - HIDSAG samples are not a time series, so no dynamic baseline can be simulated honestly;
  - the value against APC is unknown until a pilot.

**2. Economics** (`economics.py`, docs/17 §5, Value tab).
- Fix provenance: shift cadence is ASSUMED; the QEMSCAN price is shown as **CAD, 2017, Canadian lab, excl. prep**, with a local-quote requirement.
- **Remove E2 from any opportunity list.** It stays only as evidence of the grade–recovery–Cr₂O₃ trade-off.
- **Valuation basis.** Each scenario uses one stated basis: an ASSUMED matching 4E net payable price per oz and an ASSUMED payability %, with the FX stated separately and dated. Valterra's basket is shown only as context.
- **E3 becomes incremental contribution:** extra tonnes × grade × recovery × net payable − incremental variable cost per tonne (mining/reclaim, milling, flotation, smelting/refining).
  - Every input is ASSUMED, with three scenarios (low/base/high).
  - It applies only when the mill is the bottleneck; otherwise it is zero.
  - No transferred CI.
- **Break-even:** pp = (annualised installed capex + annual incremental opex) / (annual net contribution per recovery pp). Annualise over 5 years at an ASSUMED discount rate.
  - Capex and opex line items: cameras, lens, enclosure and window, lighting, encoder, edge PC, integration, commissioning, sampling and assays, Bond tests, maintenance, spares, cleaning air, software support.
  - Each is ASSUMED, with a "quote required" flag.
  - Ramp-up and downside cases.
- **E6 Stokes** is labelled a qualitative density-classification illustration, not a cyclone model.

**3. Dossier corrections** (docs/17).
- Chromite-entrainment row → "reduce entrainment through site-tested water-recovery, air and froth-depth adjustments, subject to PGM-recovery limits". This removes "reduce froth depth".
- Spirals only for a characterised, size-appropriate stream, with a PGM-loss balance.
- The categorical rules become diagnostic prompts.
- FloatStar corrected: it does use feed chemistry.
- PGNAA: not always Cf-252 (generator variants exist).
- MRDS = historical locations.
- MillStar 6–10% stays [S].

**4. Import semantics** (app).
- A blank or whitespace value is refused (it was Number("") = 0).
- Keep timestamp and revision on accepted rows.
- Reject unparseable timestamps.
- Unit test with the bad-import sample.

**5. Provenance hashing** (`build_live.py`). Hash every shipped asset, including the full-resolution showcase files and new vendor and data files, into `summary.json`, so the README's claim becomes true.

### Phase 2 — The decision path, done properly

**6. Typed operating envelope** (`live/envelope.json`, versioned). This is a **stipulated demo envelope**, labelled; a site replaces it. Each entry has:
- a manipulated variable (mill feed rate, % of design);
- min, max and conservative settings, with units;
- the ramp limit;
- authority (role);
- version, expiry and source ("STIPULATED for demo").

Every refusal, borderline case or stale case emits the envelope's conservative setting with its reason (rule 5, typed at the application boundary). No "review only" prose without a value.

**7. Advisory timing.**
- Each advice carries a **material-arrival deadline**: belt-to-mill transit, ASSUMED and stated. It also carries a validity window.
- If no human acts before the deadline, the **approved fallback applies immediately** and is logged. Investigation escalates separately (L2 metallurgist review; L3 lab rush sample), with its own clock.
- No "wait for timeout then default".

**8. Durable decision record** (`server.py` + `ledger/`).
- **Single writer.** The server appends to `ledger/decisions.jsonl` with a file lock, fsync and a write-ahead temp file. Recovery on restart truncates only a torn last line, which is detected by parse failure, and logs it.
- **Each event** has: seq, ts, type (advice | action | outcome | checkpoint), the referenced advice id, the model, calibration, policy and envelope hashes, the input hash, role, and an optional note. A note length cap warns against personal data.
- **Outcomes are new linked events**; history is never edited.
- **Hash chain:** sha256(prev || canonical event). **Checkpoints** (seq, final hash, ledger id) are exportable for external retention (print, email, a PR comment).
- **Claim only internal-consistency checking plus externally anchored checkpoints.** No authentication claim: the pilot needs site identity (AD/SSO) and signed checkpoints, which are listed as pilot prerequisites.
- **Browser-only mode** (no server) keeps the in-memory audit and says it is not durable.
- **Tests:** append, restart, torn-write recovery, chain verify, tamper detection (edit a middle line), truncation detected only against an external checkpoint (documented).

**9. Learning loop, not gamification of people.**
- No per-person scores, no leaderboards, no penalties for overrides.
- **What is reported:**
  - **model** calibration (one-sided exceedance, interval score, coverage);
  - **escalation burden** (count and time per shift);
  - **refusal-resolution time**;
  - **decision records with notes**, reviewed weekly by the metallurgist with lab outcomes beside them.
- A non-competitive **team process tracker**: "refused samples resolved within shift", "advices with a recorded reason". Framed as shared goals, not ranking.
- **Privacy:** purpose, access, retention and non-disciplinary use must be agreed with the site's information officer and workforce representatives before the pilot (a POPIA prerequisite). In the app, roles only, no identities.

**10. Mass balance, minimal.**
- A two-product calculator from feed, concentrate and tails assays of the same element (yield = (f−t)/(c−t), recovery = c·(f−t)/(f·(c−t))).
- **Singularity guard:** refuse when |c−t| is small relative to assay SD, or when f is outside [t, c].
- Uses the typed import; demo inputs **STIPULATED** and labelled.
- General reconciliation is deferred.

**11. External LLM off by default in the pilot profile.**
- `server.py` routes externally only with `REEFPRINT_ALLOW_EXTERNAL_LLM=1`. When on, the UI says "your question text leaves this machine".
- OT boundary: historian/DMZ read interface, least privilege, certificate management. These go in the pilot prerequisites, not in code.

### Phase 3 — Evidence runs (Kaggle)

**12. `reefprint-hidsag-v8-features`: a prospectively specified reanalysis** (not "pre-registered confirmation"; MINERAL1 has been seen in v5, v6 and Q2).
- **Method:** feature-based extraction after continuum removal.
  - Absorption minimum position by a 2nd-order polynomial fit around the minimum, plus relative depth.
  - This follows the feature-extraction practice reviewed by Laukamp et al. 2021 (*Minerals* 11, 347). It does **not** claim Tetracorder.
  - Features: Al-OH 2160–2230, Fe-OH ~2250, Mg-OH/CO₃ 2300–2350, 1750 (exploratory), Fe³⁺ ~900.
- **Masking frozen before the run:** the v6 rule, darkest 5% removed. A **sensitivity analysis without the dark-pixel mask** is reported alongside.
- **Sample identity reconciliation:** 99 records vs 94 physical samples in the dataset paper. Log every record's tags, crops and duplicates.
- **One endpoint per hypothesis.**
  - The **partial Spearman ρ** between the feature and its QEMSCAN group wt%: the Pearson correlation of rank residuals after OLS on size-fraction × line indicator variables.
  - Inference by **cluster bootstrap over composites** (all fractions of a composite resampled together), with a **month-blocked sensitivity** (clusters = month across lines).
  - **Holm across H1, H2 and H4.** H3 (1750 vs pooled anhydrite/gypsum) is exploratory and excluded from Holm.
  - **Minimum useful effect:** partial ρ ≥ 0.30. Power is reported. Roughly ρ ≈ 0.5 is needed for 80% power at this n, so "inconclusive" is likely and acceptable.
- **Naming:** passing features are "validated spectral associations" (e.g. "Al-OH depth tracks muscovite/sericite + kaolinite wt%"). Maps are labelled by feature, never by mineral name. **The ≥3-phases deliverable rests on KHANYA's segmentation evidence**, not on these.
- **Also exports a reproducible deployable WI model.** The sklearn pipeline is fitted on all GEOMET under the v6 choice rule (joblib), together with the feature-extraction code and a **CPU latency benchmark**: per-cube feature extraction + inference on Kaggle CPU (labelled "Kaggle CPU, not the edge PC"). Replay animation is never presented as latency.

### Phase 4 — Installation, pilot and site context (docs, plus a 2D map)

**13. Installation design (docs/18), computed from datasheets.**
- **Specific camera options:** Specim FX10 (VNIR) + SX25 (SWIR), or HySpex equivalents. Each spec is quoted from its own datasheet (e.g. SX25 IP40, 162 fps full-frame, per Codex; verified before use).
- **Line pitch** = belt speed / line rate at ASSUMED belt speeds (1.5, 2, 3 m/s) and with ROI or band binning. Also cross-track pixel size = belt width / spatial pixels, exposure-limited blur, SNR notes and data bandwidth.
- **Conclusion stated plainly:** at plant belt speeds the sensor samples the belt surface in lines centimetres apart. That is fine for parcel-level averages and not for particle mapping.
- **Site-engineering acceptance sheet with owners:**
  - optical: enclosure rating, SWIR-transmitting window (sapphire or suitable glass, ASSUMED), purge with clean dry air, air knife;
  - thermal: cooling, dew-point control, lamp heat;
  - mechanical: vibration isolation, guarding, safe access, lockout;
  - electrical: earthing, surge, UPS;
  - laser class of the burden-height sensor;
  - maintenance: window cleaning interval, lamp life, white-reference schedule.
- **Placement conditional on the site flowsheet.** It is shown on a **labelled hypothetical UG2 MF2 circuit** (primary mill → rougher/cleaner → secondary mill → rougher/cleaner, recycles, an optional chrome-spiral branch on a characterised stream). The scanner sits on the primary-mill feed conveyor where the site's feed preparation allows.
- **Wet ore:**
  - quality checks: water-band depth, window-fouling test from the white reference, burden presence;
  - in the pilot, **report usable coverage** by moisture, burden and condition;
  - the fallback and maintenance workload are budgeted;
  - hydrated minerals vs moisture ambiguity is acknowledged.

**14. Pilot protocol (docs/18 §pilot).**
- **Truth matching:** time-aligned, dry-mass-weighted composites over parcel windows with residence-time alignment; assay QA/QC (blanks, duplicates, CRMs).
- **A Bond WI test programme** on the belt-sampled material: N tests over the pilot, ASSUMED, with a cost line.
- **Planned sampling of refused and accepted conditions.**
- **Experimental design:**
  - models **frozen and versioned** within matched or randomised operating blocks (on/off, FloatStar-study style);
  - washout between blocks;
  - pre-specified KPIs and stopping rules;
  - retrained candidates promoted only through a separate chronological validation gate.
- **Plant-manager questions answered as prerequisites:** site sponsor, existing instruments (analysers, froth cameras, APC), actual bottleneck (ore- or mill-constrained), approved intervention range, sample access, budget owner, maintenance owner.

**15. 2D map (MapLibre GL JS, pinned, vendored, offline, no remote style or fonts).**
- **Layers:**
  - Natural Earth South Africa outline (public domain);
  - **USGS MRDS PGE-coded records**: query and response preserved in `data/` and `live/`; deduplicated; classified by `dev_stat` (Producer / Past producer / Plant / Prospect / Occurrence); labelled "historical database locations, positional uncertainty unknown, not current operations";
  - a proposed-pilot marker, labelled hypothetical.
- **A simple layer panel** (toggle, legend, attribute table).
- If the MapLibre bundle fails cold-start or CSP tests, fall back to an SVG map of the same layers.
- `server.py` allowlist updated for the exact files (.css, .geojson), with the CSP adjusted for blob workers. Tests below.

### Phase 5 — Proof and packaging

**16. Tests:**
- unit tests for CV+ bounds, non-inferiority, import semantics, two-product mass balance, ledger (append, restart, torn write, tamper) and envelope fallback;
- a browser end-to-end check of every view in 3 themes;
- cold-start time and bundle size on this laptop;
- the offline backup video.

**17. SBOM** with exact versions, sha256 hashes and retained notices for MapLibre and three.js (if used), Natural Earth and MRDS.

**18. Compliance ledger** (`docs/09`):
- ≥3 phases → KHANYA segmentation evidence, plus spectral associations as supporting evidence;
- accuracy report → v6/v7 + docs/16 (corrected);
- parameter demo → the decision path;
- real-time → the measured CPU latency (not replay);
- integration → reuse the existing OPC UA round-trip evidence from KHANYA (engineering fixture, as recorded in BUILDLOG) plus the tag map.

**19.** Commit, push, BUILDLOG, CONTEXT, tell Sbu.

## Key decisions and tradeoffs

- **D1. One decision path done properly** beats six advice families. The other rows of the docs/17 table appear only as **disabled diagnostic prompts**, each naming the validated measurement it would need (e.g. "locked valuables → needs QEMSCAN/KHANYA liberation on this stream").
- **D2. CV+ for the one-sided bound.** It is computable from stored out-of-fold residuals without rerunning v6. Its worst-case guarantee is weaker (1−2α), so we report the empirical exceedance. A re-run with a dedicated one-sided split-conformal score is the alternative; it is deferred unless CV+ fails.
- **D3. Non-inferiority margin +3 pp,** pre-registered here. Rationale: one overloaded parcel in about 33 extra is a plausible operating tolerance (ASSUMED); the site sets the real margin.
- **D4. No gamification of individuals.** The user asked for it. We are deliberately giving a team learning loop instead, because individual scoring creates perverse incentives and labour/POPIA risk. This is stated to the user, with the reason.
- **D5. A 2D map is kept; the 3D flowsheet is deferred.** The map uses real public-domain locations, and its cost is bounded with an SVG fallback. A 3D flowsheet would be schematic decoration at a high cost; the hypothetical MF2 is shown as a 2D SVG. The three.js cube upgrade is optional, after everything else.
- **D6. Durable ledger in server.py** (stdlib only), not a database. The integrity claim is limited to internal consistency plus external checkpoints.
- **D7. Spectral associations, not phases.** The KHANYA evidence carries the ≥3-phases deliverable.
- **D8. Economics as incremental contribution and break-even with ASSUMED inputs.** No rand headline appears on any slide without its assumption list next to it.

## Risks and open questions

- Whether CV+ gives non-inferior overload at the +3 pp margin. If not, report it and keep the interval policy as a no-gain safety rule.
- Whether the v8 features pass at n = 36 clusters (likely inconclusive).
- Kaggle-to-local model portability (sklearn versions pinned in the export).
- MapLibre worker and CSP behaviour offline.
- Whether `server.py` ledger durability holds on Windows (fsync and rename semantics).
- The team's time. The order above is the cut order from the end: map, then mass balance, then the learning-loop UI.

## Out of scope

- Hardware purchase or build (ADR-0002).
- Measured savings claims.
- The LumenStone test set.
- KHANYA's live worktree or servers.
- Real OPC UA writes and closed-loop control.
- Automatic retraining.
- General mass-balance reconciliation.
- A 3D flowsheet.
- Individual scoring.
- Cloud deployment.


---

## Addendum — round-1b (08:05): new requirements from the user, folded in before Codex round 2

**What the user asked for (summarised):**
- competitors, how our build compares, and the gaps built;
- **security**: RBAC, login, authentication, encryption, a secure SDLC, secure by design, injection- and ransomware-resistant;
- **quantum technology**: post-quantum cryptography (ML-KEM, ML-DSA, SLH-DSA) and anything quantum usable today;
- a **real, working deployment** reachable by a QR code on the slides (ingest data and images, take live photos, talk to the AI);
- a **database**;
- the business case: who we pitch to, cost, timeline, team;
- the story "one mentor session yesterday → this much today".

### Evidence gathered for the addendum (docs/17 tags)

- **Ransomware hits SA PGM.** Sibanye-Stillwater's global IT was hit in July 2024. The Columbus smelter was disrupted, RansomHouse claimed 1.2 TB exfiltrated, and a Stillwater breach affected 7,258 employees **[S]**.
- **NIST** finalised FIPS 203 (ML-KEM), 204 (ML-DSA) and 205 (SLH-DSA) on 13 August 2024 **[S]**.
- **Cloudflare** applies hybrid X25519MLKEM768 key agreement by default; about 43% of human connections were PQ-protected by September 2025. For Tunnel it is "post-quantum by default, not by guarantee" **[S]**.
- **Libraries** (versions checked on PyPI 2026-10-02):
  - `pqcrypto` 1.0.0 (Apache-2.0, PQClean bindings): ML-KEM, ML-DSA and SLH-DSA, with a Windows abi3 wheel;
  - `cryptography` (Apache-2.0 / BSD-3): AES-GCM, X25519, Ed25519;
  - `qrcode` (BSD) and Pillow (MIT-CMU);
  - stdlib `sqlite3` and `hashlib.scrypt`.
- **AI-platform competitors:**
  - IntelliSense.io brains.app: flotation recovery +1–3% at a South American copper operation **[V]**;
  - PETRA MAXTA (acquired by Maptek, March 2026): tailings grade predicted 6 h ahead **[V]**.

### Track S — security by design (P0)

**S1. Threat model** (docs/19):
- STRIDE over the app, the server, ingestion, the ledger, the LLM router and the OT link;
- IEC 62443 zones and conduits;
- OWASP ASVS L2 as the requirement list, with NIST SSDF (SP 800-218) practices as the SSDLC;
- ransomware: offline immutable backups, least privilege, no inbound OT connections, segmentation.

**S2. Authentication and RBAC** in `server.py` (stdlib, no framework):
- **SQLite** (WAL) holds users, sessions, uploads and the ledger;
- **scrypt** password hashing;
- server-side sessions with a 256-bit random id, stored only as a hash;
- cookie `HttpOnly; SameSite=Strict; Secure` behind TLS;
- idle and absolute timeouts;
- **CSRF**: a per-session token header on every POST;
- login throttling and lockout;
- optional TOTP (RFC 6238, stdlib) for admin;
- user management **CLI-only**, so there is no web admin attack surface.

**Roles (least privilege, deny by default):**

| Role | Can |
|---|---|
| `guest` | QR demo: read, sandboxed upload, assistant |
| `operator` | acknowledge, apply the envelope |
| `metallurgist` | approve within the envelope, notes |
| `mineralogist` | lab imports, refusal resolution |
| `manager` | reports |
| `admin` | CLI only |

**S3. Ingestion API:**
- `/api/upload/csv`: size caps, magic-byte checks, server-side CSV validation that mirrors the typed import (formula neutralisation);
- `/api/upload/image`: **images re-encoded by Pillow, EXIF/GPS stripped**, stored **encrypted at rest (AES-256-GCM)** outside the web root, never served raw;
- guest uploads are sandboxed and auto-deleted after 24 h;
- photos get quality gates only (no ore prediction, as before).

**S4. Ledger in SQLite:**
- an append-only table with **triggers that refuse UPDATE/DELETE**;
- a hash chain, with outcome events linked;
- **hybrid-signed checkpoints: Ed25519 + ML-DSA-65** (FIPS 204, `pqcrypto`), plus an SLH-DSA option for algorithm diversity;
- a verification CLI and endpoint;
- **encrypted exports to a named recipient**: hybrid KEM (X25519 + ML-KEM-768) → AES-256-GCM.

**What is claimed:** tamper-evidence against edits and truncation, given checkpoints held outside the server. **Not** protection against deletion of the whole database; the offline backups cover that.

**S5. SSDLC gates:**
- **Bandit** (SAST), **pip-audit** (dependencies), secret scanning, the SBOM;
- security unit tests: auth bypass, IDOR, CSRF, injection, traversal, upload polyglots, rate limits, session fixation;
- strict CSP and headers: HSTS behind TLS, `frame-ancestors 'none'`, `nosniff`, `Referrer-Policy`, `Permissions-Policy camera=(self)`;
- ClauDex review of the security diff.

**S6. LLM:** router only (unchanged). External providers off by default; when on, guests get tight caps, and prompt-injection text cannot reach tools beyond the allowlist.

### Track D — deployment (P0 artefacts; the public deploy needs the user's explicit go-ahead)

- **D1.** A `Dockerfile`: python-slim, non-root, read-only root filesystem, a single data volume, a healthcheck. A deployment runbook. **Cloudflare Tunnel** config: no inbound ports, and PQ-hybrid TLS at the edge where the client supports it **[S]**.
- **D2.** SQLite on the volume. Nightly **encrypted backup**, plus an offline copy procedure (ransomware). A restore test.
- **D3.** A **QR code** generated for the final URL. It lands on a guest view: upload a CSV or photo, ask the assistant, browse the evidence.
- **D4.** **The public deploy is not done without the user's explicit approval** of the host, account, cost and data policy (it is publishing). Until then it is local plus a tested container.

### Track B — competitors and business (docs/20) (P0)

**B1. Competitor matrix.** It covers:
- **sensors:** Blue Cube, Plotlogic, MineSense, PGNAA, TOMRA, froth and size cameras;
- **AI platforms:** IntelliSense.io, PETRA/Maptek;
- **APC:** Mintek FloatStar/MillStar;
- **labs:** QEMSCAN/MLA at Mintek.

For each: what they do, with evidence tags; where they are stronger (maturity, installed base); and where we differ:
- the mineralogy-taught belt layer;
- the calibrated refusal plus typed conservative envelope;
- the PGM/chromite physics;
- open validation with published corrections;
- PQ-signed auditability;
- offline operation and cost.

No "way better" claim. Honest axes only.

**B2. Business case** (all ASSUMED, labelled):
- **buyers:** concentrator and metallurgy managers at SA PGM producers (Valterra, Implats, Sibanye-Stillwater, Northam, Tharisa, ARM);
- **partner and channel:** Mintek (truth lab, APC integration, MOTT IP);
- **offer:** a paid pilot, then a per-site subscription, priced against the break-even;
- **timeline:** about 7–9 months to a pilot decision;
- **team:** roles and FTE; budget ranges; a risk register;
- **"velocity" evidence:** git history since the mentor session (commits, analyses, corrections), counted from `git log`.

### Track Q — quantum, honestly

- **Q1. Post-quantum cryptography is real and deployable today.** Done in S4 and D1.
- **Q2. Quantum computing gives no practical advantage today** for our workloads (regression with n = 146, small scheduling and blending problems); classical solvers win. We **will not** claim quantum computing. A QUBO formulation of stockpile blending, solvable by D-Wave Leap later, is a documented idea, not a deliverable.
- **Q3. Quantum sensing** (magnetometers, gravimeters) is exploration-side, not plant control. It is mentioned, not built.

### Revised priority (replaces the earlier cut order)

**P0:**
1. Phase 1 corrections (done).
2. S1–S6.
3. D1–D3 (local and container).
4. Envelope and advisory timing.
5. The SQLite ledger with PQ checkpoints.
6. Ingestion.
7. B1–B2.
8. Integration of the v8 evidence.

**P1:** map, minimal mass balance, learning-loop UI.

**P2:** three.js cube.

**Deferred:** 3D flowsheet, general reconciliation, automatic retraining, quantum computing.
