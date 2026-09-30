# REEFPRINT dashboard UI redesign — 2026-09-30

Replaced the old dark, mostly-empty upload landing screen with a responsive light workbench based on the preferred mockup: (1) sample/interval intake, (2) geology/spatial context, and (3) mineral phase analysis. Validation and the model-to-simulator flow sit beneath the three panels. The Streamlit uploader and analysis-mode controls retain the existing local inference and evidence workflows.

The spatial view is labelled schematic and explicitly says that survey data is not connected. XRF is identified as unconnected context, not a mineral-phase measurement. No phase percentages appear before inference. Plant feedback is labelled simulation-only, with no PLC connection.

The validation card uses the latest Kaggle run from `reports/END-TO-END-LOCAL-DEMO-2026-09-30.md`: held-out mean IoU 0.4543, pixel accuracy 0.7716, and nonzero IoU on three ore phases; magnetite IoU is 0.000. It distinguishes that run from the separate 0.5725 baseline in `reports/ACCURACY-REPORT.md`.

Verification: renderer assertions updated; browser checked at `http://127.0.0.1:8501/`. The 700 px landing frame exposes the full dashboard composition before Streamlit's interactive controls.
