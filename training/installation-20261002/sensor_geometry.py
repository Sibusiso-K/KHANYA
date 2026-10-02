"""Belt-scanner geometry from the camera datasheet, with provenance (rule 1 as a type). Code does the arithmetic.

Camera: Specim SX25 (960-2500 nm), datasheet "Specim-SX25-Technical-Datasheet-01" read 2026-10-02 [P]:
640 spatial samples, 392 bands (4 nm sampling, 8 nm FWHM), max 162 fps full frame, 16-bit, binning 1/2/4 and
spectral ROI, fore lens FOV options 38 deg (OLES17) or 66 deg (OLES9), IP40, +5..+40 C non-condensing, 35 W max, 5.3 kg.
Belt widths and speeds are ASSUMED scenarios (a site measures its own). Higher line rates with spectral ROI/binning are
possible per the datasheet, but the achievable fps is a vendor figure we do not have, so it is not used.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))
from reefprint.quantity import assumed, cited  # noqa: E402

DS = "Specim SX25 technical datasheet 01 [P]"
px = cited(640, "px", DS + ": spatial samples")
fps = cited(162, "lines/s", DS + ": maximum frame rate, full frame")
bands = cited(392, "bands", DS + ": spectral bands")
bytes_per = cited(2, "B", DS + ": 16-bit")
fov_deg = {"OLES17_38deg": 38.0, "OLES9_66deg": 66.0}

rows = []
for width in (0.9, 1.2, 1.5):
    W = assumed(width, "m", f"ASSUMED belt width {width} m (mill-feed conveyors vary; site value)")
    for speed in (1.5, 2.0, 3.0):
        V = assumed(speed, "m/s", f"ASSUMED belt speed {speed} m/s (site value)")
        line_pitch_mm = (V / fps).value * 1000
        cross_mm = (W / px).value * 1000
        dist = {k: (width / 2) / math.tan(math.radians(a / 2)) for k, a in fov_deg.items()}
        rows.append({"belt_width_m": width, "belt_speed_m_s": speed, "line_pitch_mm_at_162fps": round(line_pitch_mm, 1),
                     "cross_track_pixel_mm": round(cross_mm, 2), "motion_blur_mm_at_full_exposure": round(line_pitch_mm, 1),
                     "working_distance_m": {k: round(v, 2) for k, v in dist.items()},
                     "lines_per_tonne_note": "parcel-level averaging, not particle mapping", "provenance": "ASSUMED (width, speed) x CITED (datasheet)"})
full_rate = (px * bands * bytes_per * fps).value
roi_rate = (px * assumed(75, "bands", "ASSUMED spectral ROI of 75 bands (the v6 SWIR display set size)") * bytes_per * fps).value
out = {"camera": DS, "rows": rows, "data_rate_MB_s_full_frame": round(full_rate / 1e6, 1), "data_rate_MB_s_75_band_roi": round(roi_rate / 1e6, 1),
       "conclusion": "At plant belt speeds the SWIR line scanner samples the surface in lines about 9-19 mm apart with ~1.4-2.3 mm cross-track pixels: "
                     "adequate for parcel-level averages (our models use pooled pixels), not for particle-by-particle mapping or sorting."}
json.dump(out, open(os.path.join(HERE, "sensor_geometry.json"), "w"), indent=1)
for r in rows:
    print(f"belt {r['belt_width_m']} m @ {r['belt_speed_m_s']} m/s: line pitch {r['line_pitch_mm_at_162fps']} mm, cross-track {r['cross_track_pixel_mm']} mm, "
          f"distance {r['working_distance_m']}")
print("data rate full frame", out["data_rate_MB_s_full_frame"], "MB/s; 75-band ROI", out["data_rate_MB_s_75_band_roi"], "MB/s")
