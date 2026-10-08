# REEFPRINT dashboard UI redesign — 2026-09-30

Replaced the old dark, mostly-empty upload landing screen with a responsive light workbench based on the preferred mockup: (1) sample/interval intake, (2) geology/spatial context, and (3) mineral phase analysis. Validation and the model-to-simulator flow sit beneath the three panels. The Streamlit uploader and analysis-mode controls retain the existing local inference and evidence workflows.

The spatial view is labelled schematic and explicitly says that survey data is not connected. XRF is identified as unconnected context, not a mineral-phase measurement. No phase percentages appear before inference. Plant feedback is labelled simulation-only, with no PLC connection.

The validation card uses the latest Kaggle run from `reports/END-TO-END-LOCAL-DEMO-2026-09-30.md`: held-out mean IoU 0.4543, pixel accuracy 0.7716, and nonzero IoU on three ore phases; magnetite IoU is 0.000. It distinguishes that run from the separate 0.5725 baseline in `reports/ACCURACY-REPORT.md`.

Verification: renderer assertions updated; browser checked at `http://127.0.0.1:8501/`. The 700 px landing frame exposes the full dashboard composition before Streamlit's interactive controls.

## Full result view correction

The uploaded-image result previously remained a dark two-column layout inside a nested-scroll iframe, and the simulated response was rendered outside the dashboard. It now uses a light responsive three-panel composition (micrograph/mask, phase metrics/advisory, geology/XRF context), places the held-out validation and actual simulator outcome in the same result view, and lets the outer page scroll instead of trapping the user in an iframe scrollbar. Geology and XRF remain explicitly unavailable until real source data/devices are connected.

The app also has a one-click **Run held-out example** action for the real `test_01` S2 image, with an explicit benchmark/not-South-African-ore label. This exercises local inference and simulation without requiring a user image upload. Developer-only stale-record/reset controls are tucked into a collapsed expander.

Final desktop ordering now follows the requested showcase: core image + mask on the left, geology context in the middle, phase/advisory results on the right. The duplicate Streamlit simulator summary is collapsed into a local event-log expander; the parameter before/after remains inside the main report.
