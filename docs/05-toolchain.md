# 05-TOOLCHAIN — every piece of software we install, and what we deliberately do not

**Total cost of this list: R0.** Not "free tier with a card on file" — free.

This answers one question: *what do we actually download?* `SBOM.md` answers a different one —
*what licence is each thing and can it be assigned to Mintek* — and it is the legal record. This
file is the practical one. If they disagree, `SBOM.md` wins and this file is a bug.

Two hard constraints shape everything below:

- **Permissive licences only for anything shipped** (Rule 7). Copyleft is not a style preference
  here; the deliverable has to be assignable to Mintek without a further negotiation.
- **The demo must run fully offline on one laptop** (week-5 gate). Anything that needs a network
  call at runtime is disqualified from the demo path, whatever else it can do.

---

## 1. Install this, in this order

```bash
uv sync
```

That is the whole setup. One command, one lockfile, no conda. It creates `.venv/`, installs the
runtime and dev dependencies, and installs `reefprint` itself in editable mode.

Prerequisites you install once, by hand:

| Tool | What it is | Licence | Get it |
|---|---|---|---|
| **Python 3.12** | pinned `>=3.12,<3.13` | PSF-2.0 | python.org, or `uv python install 3.12` |
| **uv** | package + venv manager, replaces pip/venv/poetry | MIT / Apache-2.0 | astral.sh/uv |
| **git** | version control. Rule 8 — the commit history is the originality defence. | GPL-2.0 *(a tool we run, never a dependency we link)* | git-scm.com |

**Known failure: `uv` on Windows can't install its own Python.** On Sibusiso's Windows machine
(session 11, 2026-08-21), both `uv sync` and `uv python install 3.12` failed reproducibly with
*"Missing expected target directory for Python minor version link"*, even after a clean cache
retry (`uv cache clean`). Root cause not confirmed — the error names a junction/symlink target
`uv` expects and doesn't find, which on Windows is often Developer Mode being off or an AV
product (Defender included) blocking the link creation, but neither was tested in isolation.
Workaround used: point `PYTHONPATH` at an existing 3.13 venv from another project on the same
machine instead of letting `uv` provision one, after confirming the code being run has no
3.12-only syntax (`ast.parse` on the file in question — cheap, and it would have caught a
mismatch immediately). **If this recurs:** try enabling Windows Developer Mode
(`ms-settings:developers`) or temporarily excluding the `uv` cache/install directories from
Defender before falling back to the `PYTHONPATH` workaround, and update this note with whichever
one actually fixes it.

Optional, and genuinely optional:

| Tool | Why you might want it | Licence |
|---|---|---|
| **VS Code** or any editor | — | MIT (VS Code binary is a Microsoft licence; VS Codium is the MIT build) |
| **GitHub CLI (`gh`)** | PR and issue work from the terminal | MIT |

---

## 2. Installed right now — 39 packages, all free, all permissive

Direct runtime dependencies, from `pyproject.toml`:

| Package | Version | Licence | Why it is here |
|---|---|---|---|
| `numpy` | 2.5.2 | BSD-3-Clause | the arrays. Everything. |
| `scipy` | 1.18.0 | BSD-3-Clause | least squares, statistics |
| `scikit-image` | 0.26.0 | BSD-3-Clause | segmentation, morphology, grain extraction |
| `tifffile` | 2026.7.31 | BSD-3-Clause | **OME-TIFF read/write and OME-XML metadata. ADR-0001.** |
| `imagecodecs` | 2026.6.26 | BSD-3-Clause | `tifffile`'s compression backend |
| `matplotlib` | 3.11.1 | PSF-derived, BSD-compatible | the three-panel gate figure. Used via `Figure`, never `pyplot`. |
| `pillow` | 12.3.0 | MIT-CMU | decodes the JPEG frames in LumenStone S3 v2. Was transitive via matplotlib; promoted to a declared dependency on 2026-08-20 when `experiments/002-s3v2-geometry` began importing it directly. |

Direct dev dependencies:

| Package | Version | Licence | Why |
|---|---|---|---|
| `pytest` | 9.1.1 | MIT | the gates |
| `pytest-cov` | 7.1.0 | MIT | coverage |
| `hypothesis` | 6.165.8 | **MPL-2.0** | property-based physics invariants. Weak copyleft, file-level, **test-time only — nothing links it.** It found the `rotated_specimen` sign bug. |
| `ruff` | 0.16.3 | MIT | lint + format, one tool |
| `pre-commit` | 4.6.2 | MIT | runs ruff before every commit |

The remaining ~27 are transitive (`fonttools`, `networkx`, `pyyaml`, `virtualenv`, …).
Regenerate the full list any time with:

```bash
uv pip list --format=freeze
```

**Notably not installed yet:** `torch`, `timm`, `segmentation_models_pytorch`, `xgboost`, `mapie`,
`onnxruntime`, `asyncua`, `napari`. All are declared as optional extras and deliberately left
uninstalled, so a clean checkout can run the entire test suite without downloading PyTorch.

---

## 3. Planned installs, and the week each is actually needed

Install nothing before the week it is needed. An unused dependency is an SBOM row, an install
failure, and a supply-chain surface, in exchange for nothing.

| When | Command | What it pulls | Licences |
|---|---|---|---|
| **Week 2** — falsification test | already covered by `scipy` + `numpy` | — | — |
| **Week 3** — segmentation | `uv sync --extra ml` | `torch`, `timm`, `segmentation_models_pytorch`, `xgboost`, `mapie`, `onnxruntime` | BSD-3 · **Apache-2.0** · MIT · Apache-2.0 · BSD-3 · MIT |
| **Week 3** — conformal | included above (`mapie`) | pick `mapie` **or** `crepes`, never both | BSD-3 |
| **Week 5** — offline packaging | `uv sync --extra ml` then export ONNX | `onnxruntime` | MIT |
| **If the OPC UA demo survives the kill list** | `uv sync --extra integrate` | `asyncua` | **LGPL-3.0 — CONDITION** |
| **Dev-time inspection only, never the demo** | `uv sync --extra viz` | `napari[pyqt6]` | BSD-3 (PyQt6 is GPL/commercial — *this is why napari is dev-only and the demo UI is matplotlib*) |
| **Kaggle kernels only — hyperspectral track** | installed inside the kernel by `run.py` | `h5py` | BSD-3 |
| **When data volume justifies it** | `uv tool install dvc` | `dvc` | Apache-2.0 |
| **When there are runs worth comparing** | `uv add --dev mlflow` | `mlflow` | Apache-2.0 |

Two rules on this table:

1. **`timm`, never DINOv3.** `timm` is Apache-2.0 with a patent grant. DINOv3's licence is
   non-transferable, grants no patent rights, is unilaterally amendable and sits under Californian
   jurisdiction. Gauntlet **S3**. Blocked.
2. **Pretrained weights carry their own licence, separate from the library.** An Apache-2.0 `timm`
   architecture can ship weights under something else entirely. Record the checkpoint's licence in
   `SBOM.md` *before* the weight touches a graded artefact.

Every one of these gets an `SBOM.md` row **in the same commit that adds it**. An SBOM assembled
the week before the final is a guess, not a defence.

---

## 4. What we decided NOT to install, and why

This section exists so nobody helpfully re-adds one of these in month two.

| Not installing | Reason | Authority |
|---|---|---|
| **Bio-Formats** (`python-bioformats`, `scyjava`) | **GPL-2.0** — unassignable. Also a JVM inside an otherwise pure-Python stack that has to run offline on one laptop. Stays a *manual, offline* conversion tool if a vendor format ever appears; never a dependency. | [ADR-0001](04-decisions/0001-ome-tiff-via-tifffile-not-bioformats.md) |
| **Micro-Manager / `pymmcore`** | Nothing to drive. Mixed licensing across core, device adapters and vendor camera SDKs, many non-redistributable. | [ADR-0002](04-decisions/0002-software-only-no-instrument-is-built.md) |
| **ImageJ / Fiji** | Acquisition- and inspection-side. `scikit-image` covers the analysis, in-process, with no GUI. | ADR-0002 |
| **`picamera2` / `libcamera`** | No rig. Independently: pip-installing it drags in `python-prctl`, which **does not build off Linux** — it failed on this machine in session 1 and the `hardware` extra was removed entirely. | ADR-0002 + a real build failure |
| **`petroscope`** | **GPL-3.0.** The library published alongside LumenStone. Copyleft into an assigned deliverable is the S3 failure mode exactly. *The LumenStone **data** is a separate question — data yes, library never.* | Rule 7 · `SBOM.md` |
| **DINOv3** | Non-transferable, no patent grant, unilaterally amendable. Use `timm`. | Gauntlet S3 |
| **Hailo SDK / compiler** | EULA is non-assignable. Optional accelerator, never load-bearing, and it is on the kill list. | Gauntlet S3 · kill list |
| **conda / Anaconda** | Anaconda's terms changed for organisational use. `uv` is MIT, faster, and produces a lockfile we can hand over. | Rule 7 |
| **Anything needing a network call at demo time** | Week-5 gate is *fully offline on one laptop*. No API, no model hub call, no licence server. | Weekly gates |

---

## 5. Data we will download — separate question, separate licence

Software licences do not govern data. Data terms govern what may be **published**, which is the
part that bites at submission.

| Dataset | Size / route | Terms | Status |
|---|---|---|---|
| **LumenStone S3 v2** — XPL *rotation* sequences on strongly anisotropic ore minerals | ~419 MB, Yandex Disk | **No named licence.** Informally "free to use in research, cite the references". | **Decision pending.** This is the data half of the week-1 gate leg (b). Get terms in writing from `khvostikov@cs.msu.ru` before publishing anything derived. |
| **LumenStone S2** — Norilsk layered ultramafic: pyrrhotite, chalcopyrite, pentlandite, magnetite | same route | as above | same condition. This is the *same Ni-Cu-PGE sulphide assemblage* as Merensky/UG2 BMS — it is the most relevant public data that exists. |
| **IMA/COM Quantitative Data File** — reflectance spectra, 510 species | web lookup, `projects.gtk.fi/com/results/reflectance_data.html` | published reference data; confirm reuse terms before redistributing values | **This is the teacher**, and it is what replaces the three `Provenance.PLACEHOLDER` reflectances in the phantom. |
| **IronOreRLM** — 563 reflected-light images, India | ScienceDirect `S2352340925002720` | VERIFY | domain-shift testing only |
| **MUMDMC2025** — 14,400 photomicrographs, 72 rotations at 5° | *Nature Sci Data* 2025 | VERIFY | **Transmitted light on granite silicates.** Exercises the rotation pipeline; carries none of the reflected-light ore physics. Never cite it as ore evidence. |
| **Craig & Vaughan, *Ore Microscopy and Ore Petrography* 2nd ed.** | free PDF, MSA | open access | Chapters 3, 5, 11. Read, do not reproduce figures without checking. |

**Downloads are a user decision, not an agent decision.** Nothing above gets fetched without
explicit go-ahead, and anything with unresolved terms gets used for *evaluation* only until the
terms are in writing.

---

## 6. Compute — also free, also no card

| Resource | Limit | Note |
|---|---|---|
| This laptop | — | the whole week-1 gate runs here in seconds |
| **Kaggle** | 30 h/week, P100 | the workhorse for week 3 |
| **Google Colab** | 15–30 h/week, T4 | overflow |
| **Lightning AI** | student credits | overflow |
| **Modal** | free tier, CPU burst | batch jobs |
| **CHPC** (chpc.ac.za) | free to SA academics | worth an application; would remove every compute constraint. Not counted on. |

None of these may be on the critical path for the demo. **The demo runs on one laptop, offline.**

---

## 7. Keeping this honest

- New dependency → row in `SBOM.md` **in the same commit**, and a line here if it changes what
  someone has to download.
- A licence marked **VERIFY** in `SBOM.md` is an assumption until someone opens the upstream
  `LICENSE` file. Do not cite an unverified row in the submission.
- If something on the *not installing* list starts to look necessary, that is an ADR, not a
  `uv add`.
