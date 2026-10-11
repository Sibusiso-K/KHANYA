# Handover prompt: continue the Team Sonar Mintek report

Paste everything below the line into a new chat.

---

You are continuing work on **Team Sonar's technical, business and pilot report for Mintek** (Mintek–SCi Grad Hackathon 2026, Problem 3, Top-5 refinement round). I (Sibusiso Khumalo, Wits) will keep iterating on the report with you. My teammate Lethabo Hoaeane (UNISA) owns model accuracy, independent testing and the application.

## Where everything is

- **Local repo (git worktree):** `C:\Users\lovilocal.adm\Desktop\Claude Projects\KHANYA-workbench`
  - Branch: `codex/launch-live-demo`. Latest report commit: `abde26a`.
  - Report source: `report/main.tex`. Compiled output: `report/main.pdf` (12 pages).
  - Figures: `report/figures/`.
  - Overleaf bundle: `report/Team-Sonar-Mintek-Technical-Report-overleaf.zip`. Rebuild it after every change.
  - Helper scripts in `report/tools/`:
    - `chk.py` checks that environments are balanced, labels resolve, and the bibliography order matches first citation;
    - `render.py` renders PDF pages to PNG;
    - `belt_calib.py` holds the bound-calibration numbers;
    - `hsi_fig.py` draws Figure 4.
  - Team log: `HANDOVER.md` at the repo root. **Prepend a dated entry every session, then commit and push.** Lethabo learns everything from this file.
- **Remote:** https://github.com/Sibusiso-K/KHANYA (public)
  - Report branch: `codex/launch-live-demo`.
  - Belt and hyperspectral results: branch `codex/pwa-phase-roadmap`, under `training/` (value-chain, v6, v8 and v9 outputs).
  - Never merge the `main` and `reefprint` histories.
- **Static demo:** https://lethabomh14-reefprint.static.hf.space (a replay of precomputed public data, not live).
- **Reviewer handovers that shaped the current version:** in `C:\Users\lovilocal.adm\Downloads\`:
  - `REEFPRINT_KHANYA_Detailed_Revision_Handover.pdf` (+ `_Editing_Agent_Handover.md`)
  - `REEFPRINT_KHANYA_Pilot_Audit_and_Build_Handover.pdf` (+ `_Pilot_Audit_Agent_Handover.md`)
- **My old course reports** (they define the writing style): `C:\Users\lovilocal.adm\Downloads\Power_Project_2026_1732968-1.pdf`, `annotated-Renewables_Project_Report_Group_1.docx.pdf`, `EMC_Project_Report_2026_1732968 (2).pdf`.

## Build

From `report/`:

```
C:\Users\lovilocal.adm\tools\tectonic\tectonic.exe -X compile main.tex
py -3 tools\chk.py main.tex
"C:\Users\lovilocal.adm\Desktop\Claude Projects\KHANYA\.venv\Scripts\python.exe" tools\render.py main.pdf <outdir> 1.4
```

After any layout change, look at every page. The report must stay **≤12 pages including references and appendices**. On this machine, edit LaTeX through Python scripts saved to files: inline bash heredocs mangle backslashes.

## Current state of the report (abde26a)

- **Title:** "REEFPRINT/KHANYA: ore-hardness prediction on the belt and sulphide characterisation in the laboratory. An analogue-data proof of concept and staged validation plan for South African concentrators."
- **Belt:** HIDSAG, 146 composites, out-of-fold R² 0.479 (MAE 1.05 kWh/t). The 90% bound covered 93.2% of samples (CI 88.4–96.6%), with a mean margin of 1.64 kWh/t. The simulated throughput gain is 1.7–1.9% against a fixed design-feed policy. This is a replay without time order, not a plant result.
- **Microscope:** three checkpoints in a model registry (Table 3):
  - `de7135a9` (historically evaluated): IoU pyrrhotite 0.870, chalcopyrite 0.576, pentlandite 0.547, on 12 sections reused during development;
  - `fb78727d` (active in the audited app, not approved): the audit on test_11 found pixel accuracy 64.1%, with pentlandite at 34.8% of the area against 2.0% in the reference;
  - `42646cfa` (candidate, quarantined).
- **Decisions:** 4 definite, 6 verify and 2 too-few outputs out of 12. This is rule agreement, not proof of safety.
- **≤10% error is a validation TARGET, not a result.** Section 2.6 defines the protocol (absolute vs relative error, custodian blind test, 30/10/≥30 specimens).
- **Budget:** one scoped budget (Table 6):
  - a capped R210,000 first tranche (laboratory and feasibility);
  - the v9 one-belt allowance of US$250–400k (R4.10–6.56 M at R16.4/US$, including 25% contingency), released only after gate G1B.
  - The old R8.2–49.2 M grid survives only as a "superseded" sensitivity row.
- **Break-even:** 0.015–0.057% more recovered metal, rising to 0.20% if only a quarter of output passes the belt (Table 7).
- **Gates:** G0, G1A (microscope), G1B (belt transfer), then G2–G5. Microscope success never releases belt spending. The roadmap runs 0–18 months from an agreed readiness event.
- **No partner agreements exist.** Mintek, TIA and producer roles are proposals. LumenStone data is research-use only.

## Rules (non-negotiable)

1. **Never invent numbers, tests, quotes, approvals or partner commitments.** Recompute any figure from committed result files, or flag it.
2. **Five orange `\needstech{...}` flags** ("TECH NUMBERS PENDING") mark where Lethabo's frozen-model results, sample counts and metric definitions will go. Fill them only from evidence Lethabo supplies, then delete the flag.
3. Keep measured, simulated and proposed results distinct. Development-influenced microscope results must never be called independent.
4. **Writing style:** my course-report voice.
   - Open with role framing ("As Team Sonar…") and include a problem statement.
   - Lettered assumptions (a), (b), …
   - Cost equations followed by "which is equivalent to…".
   - "Figure X illustrates…, highlighting…".
   - Plain language for Mintek/TIA judges, South African spelling, money in rand.
   - IEEE references with URLs. Open every URL before citing it.
5. Ipeleng Modise is not an author (my decision). Mentors are thanked by role only. Commits end with my co-author attribution line, if one is configured.
6. Commit and push continuously, and write a `HANDOVER.md` entry each session.

## Open items

- Lethabo's final technical numbers for the 5 flags.
- The v9 deck file was not found locally. Align the deck, narration and video with the report once it is available.
- Team roster: the decks list three people and the report lists two. Decide which changes.
- Still needed from outside the team: the official 2026 brief and rubric, the IP agreement text, LumenStone commercial rights, supplier and lab quotes, a host plant and its affected-output fraction, and a release manifest.

Start by reading `report/main.tex`, the top three entries of `HANDOVER.md`, and the latest compiled PDF. Then ask me what to work on next.
