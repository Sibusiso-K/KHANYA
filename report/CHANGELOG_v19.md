# Report v19 change log and claim-to-evidence ledger (11 October 2026)

Source: POST_V18_REPORT_HANDOVER.md. main_v18 is preserved in git (commit 937047b). Still 12 pages.

## Section-by-section changes

| Location | Change | Handover row |
|---|---|---|
| Abstract | Replaced with the handover's copy-ready abstract, adapted: "aims to provide an earlier reading"; recorded copper domain; 12/20 beside 0/20; EXP subsets and null studies; hardness R² 0.479 beside later R² 0.25; P0 cap and pilot allowance kept; ≤10% stays a target. | Abstract rows |
| §1.2 | "Every step is signed and recorded" scoped to the implemented recorded-data route; current application modes and "no conveyor sensor; 30 s parcel proposed" added. | §1.2 |
| Table 1 | Recorded copper phases and 12/20 vs 0/20 added; plant adjustment status = Simulation; real time = scoring only. | Table 1 |
| §2.1 | Copper mean-spectrum data (99 records, 36 groups; deployed 20 in 7 groups) and paired MLA–HSI data, with reference basis and reuse. | §2 data |
| §2.6 | Phase panel, floor, coverage and joint endpoint; median vs 90% jointly; 80% coverage cannot give 90% all-attempt success; below-floor tolerance separate. | §2.6 |
| §3 | Static-demo/17-of-17 sentence replaced by the Azure revision 7 implementation paragraph; personal workspaces are not team RBAC; latency components separated. | §3 |
| §4.1 | EXP23 Bond result placed beside historical R² 0.479. | Hardness |
| §4.3 (new) + Table 2 | Mineral-composition development results with denominators and evidence levels. | §4 results |
| §4.4 | Microscope sections merged and condensed as supplementary; Fig. (IoU bars) removed, numbers kept in text and Table 3. | Microscope |
| §5.1 | "Belt claim limited to hardness" replaced: belt composition remains a development and pilot question. | Mineralogy primary |
| §6.4 | 1.7–1.9% labelled simulated throughput; hosting cost separated from pilot capital as a scenario. | Economics |
| §7.2 | Causal chain before actuation. | Pilot |
| §9 | Bounded feasibility, no automatic TRL. | Conclusion |
| Back matter | Azure URL (account required); HF demo marked a different build; evidence release v19; precise evidence freeze. | Evidence/demo |

## Claim-to-evidence ledger (new or changed claims)

| Claim | Evidence | Level |
|---|---|---|
| Deployed authenticated app, revision 0000007 | 09_FINAL_RELEASE.json; HTTP 200 signed-out check by Claude, 11 Oct | Handover record + Claude check |
| 12/20 panel, 0/20 all phases | 04 Azure addendum | Bundled report, not rerun |
| EXP21–26 values | 02 alignment, 13 EXP26, handover table | As stated in Table 2 caption |
| EXP23 Bond R² 0.25 | 02 alignment | Developer report |
| QR encodes Azure URL | evidence/REEFPRINT_AZURE_QR.png | Decoded by Claude (OpenCV) |
| Replay +1.7% [+0.8, +2.7] | replay_envelope.py/json | Rerun by Claude, 8 Oct |
| Hosting US$15–35/month | Handover §9 | Scenario, not a bill |

## Open questions for the co-leads

1. Final submission PDF and release freeze need both co-leads' approval (handover §10).
2. Cross-account isolation and team RBAC are untested or unimplemented; keep out of claims.
3. Deck, narration and video still show the old Hugging Face QR; replace with evidence/REEFPRINT_AZURE_QR.png ("Open the research application — account required").
4. External statistics and TIA eligibility are not re-certified by this handover.
