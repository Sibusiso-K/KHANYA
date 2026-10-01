# REEFPRINT Live: belt-to-decision showcase

An offline, single-page app in the KHANYA workbench design (Public Sans, the brand mark, and three themes). It replays **real public data** in three labelled evidence tracks plus an integration view.

The plan behind it is `PLAN-live-v6.md`, reviewed in a ClauDex loop (Codex gpt-6-astra, 3 rounds, APPROVED; the argument is in `PLAN-live-v6-REVIEW-LOG.md`).

| View | Data | What it shows |
|---|---|---|
| **Live scan** | HIDSAG VNIR + SWIR cubes, CC0 | A real scan line by line, absorption and cluster maps, the spectrum under the cursor, a 3D data cube, predictions with 80% split-conformal intervals, the total decision table, reasons (occlusion) and an audit log |
| **Bushveld PGE** | Bachmann et al. 2019 chromitite assays, CC BY 4.0 | Belt-type chemistry (Cr₂O₃, FeO, SiO₂, MgO, Al₂O₃, CaO) to seam and Pt / Rh / 4E grade, held out by project, with a downhole log |
| **Plant** | Kaggle iron-ore flotation plant, CC0 | Real plant tags, a silica forecast against the lab assay and against persistence. It does **not** beat the last assay; that is shown |
| **Lab & exports** | target registry | Typed import of QEMSCAN / XRF / XRD / assay CSVs with reasons for each rejection, reconciliation, and LIMS CSV, provenance JSON, OPC UA tag map, GeoJSON (null geometry) and shift report |
| **Evidence** | all of the above | The scoreboard against strongest baselines, v5, and a cheaper camera, plus the MINERAL1 correction |
| **Where it sits** | design | Orchestration (router, referee, policy) and roles |

## Run it

```
python presentation/belt-monitor/server.py
```

Open `http://127.0.0.1:8531/`. Plain `python -m http.server` also works, but the assistant then uses only the offline parser.

URL options: `?theme=mineral-night|field-paper`, `?view=bushveld|plant|lab|evidence|where`, `?auto=1` (run the belt), `?scan=4500` (ms per scan), `?dwell=3500`.

## Where the AIML API and Featherless API keys go

**Only in the environment of `server.py`, on the machine running it.** They are never written to a file by the app, never sent to the browser and never logged.

PowerShell:

```
$env:REEFPRINT_LLM_PROVIDER = "aiml"         # or "featherless"
$env:AIML_API_KEY = "<your key>"             # or $env:FEATHERLESS_API_KEY
$env:REEFPRINT_LLM_MODEL = "<model id from the provider's catalogue>"
python presentation/belt-monitor/server.py
```

Both providers are OpenAI-compatible. The server calls `https://api.aimlapi.com/v1/chat/completions` or `https://api.featherless.ai/v1/chat/completions`, and only those two hosts.

**The language model only routes.** It receives the user's question and the tool list, never data, imported files or results. It returns one allowlisted tool with validated arguments, and the browser renders every answer from code. With no key, an offline parser routes instead.

The KHANYA workbench has its own assistant setting: `REEFPRINT_ASSISTANT_PROVIDER / MODEL / API_KEY` on its server (see that app's docs).

**Server hardening:**
- binds 127.0.0.1 only; checks Host and Origin;
- requires a per-run session token embedded in the page;
- serves a static allowlist (traversal and source files return 404);
- caps request size, timeouts, tokens, rate (20 per minute) and requests per day (300).

## Rebuild the data

1. Kaggle `reefprint-hidsag-v6-live` writes `training/hidsag-v6-live-20261001/output/`.
2. Run the analysis scripts:
   - `python training/hidsag-v6-live-20261001/analyse_v6.py`
   - `python training/hidsag-v6-live-20261001/mineral1_q2.py`
   - `python training/plant-softsensor-20261001/softsensor.py`
   - `python training/bushveld-xrf-pge-20261001/bushveld.py`
3. Build the live data: `python presentation/belt-monitor/build_live.py` writes `live/`, about 25 MB, with every source file sha256-hashed into `live/summary.json`.

## What is not claimed

- **Not live, not one ore.** Nothing here is a live belt, a live plant connection or PGM-ore hyperspectral data. The three tracks are not paired observations of one ore.
- **Few belt targets drive decisions.** Only targets that beat their strongest baseline under every gate are used: Bond work index (belt), and Pt / Rh / 4E (Bushveld).
- **Plant-feed mineralogy is withdrawn.** Its predictions are explained by size fraction and process line, so the earlier "camera reads mineralogy" claim is withdrawn.
- **Phone photos get no prediction.** They pass quality gates only.
- **Thresholds are illustrative.** They come from training folds, not site rules.

Archived versions: `belt-v2.html` (restyled belt monitor, v5 data) and `index-v1-dark.html`.
