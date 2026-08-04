# Data

Nothing here is committed. Download and place manually.

## Sources

1. **MUMDMC2025** — 14,400 photomicrographs, 5 mineral classes, 72 rotations each,
   plane- and cross-polarised. Primary source for the >=3 phase requirement.
   https://www.nature.com/articles/s41597-025-05879-9

2. **FeM iron ore dataset** — 81 reflected-light pairs with binary ore/resin masks
   (itabiritic iron ore, Quadrilatero Ferrifero). Segmentation stage only; binary,
   so it does NOT satisfy the >=3 phase requirement on its own.
   https://zenodo.org/record/5014700

3. **Mintek imagery** — ask `info@mintek.co.za` whether P3 teams get sample imagery
   or a technical mentor. Real South African ore data would be a large edge.

Check each licence before use and record it in the report.

## Expected layout

`src/data.py` expects one directory per class, and filenames whose specimen id is
the part before the first underscore:

```
data/raw/
  hematite/
    SPEC001_rot000_ppl.jpg
    SPEC001_rot005_xpl.jpg
    SPEC002_rot000_ppl.jpg
  magnetite/
  quartz/
  goethite/
```

The specimen id is what the split is grouped on. If a dataset names files
differently, adapt `specimen_id_from_path` in `src/data.py` — do not fall back to
a random split.
