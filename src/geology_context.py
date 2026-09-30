"""The geology context view's data: real, public, and small enough to commit.

    python -m src.geology_context

Writes dashboard/data/geology_context.json from two public sources in data/raw/:

1. USGS Mineral Resources Data System (MRDS), mrds-csv.zip, downloaded
   30 Sept 2026 from mrdata.usgs.gov/mrds. South African sites with
   coordinates: name, commodity, deposit type, status. A USGS product
   (normally public domain; the download page states no licence). USGS stopped
   systematic updates in 2011, so this is a historical inventory of deposit
   locations, not a current mine list.
2. Thaba chromitite borehole assays, Bushveld Complex (Mendeley Data,
   DOI 10.17632/dc8jcnbcvk.1, CC BY 4.0): 1,205 seam intervals in 317 holes,
   with depth, seam (LG/MG), Cr2O3 and PGE assays. The public file carries NO
   collar coordinates, so these holes are shown as downhole logs and are never
   placed on the map.
"""
import csv
import hashlib
import json
from collections import defaultdict

from .segmentation import config

RAW = config.ROOT / "data" / "raw"
MRDS_CSV = RAW / "usgs_mrds" / "mrds.csv"
MRDS_ZIP = RAW / "usgs_mrds" / "mrds-csv.zip"
THABA_CSV = RAW / "bushveld_thaba_chromitite" / "DataSet_Thaba_Classification.csv"
OUT = config.ROOT / "dashboard" / "data" / "geology_context.json"

# South Africa's extent. MRDS has records whose coordinates fall outside it
# (e.g. positive latitudes, apparently sign errors, and one at 65.7 N 65.7 W).
# They are excluded, named in the output, and never corrected by guesswork.
ZA_LAT = (-35.5, -21.5)
ZA_LON = (16.0, 33.5)

GROUPS = [("PGE", ("platinum", "pge", "palladium", "rhodium")), ("Chromium", ("chromium",)),
          ("Nickel-copper", ("nickel", "copper")), ("Gold", ("gold",))]


def _group(commodities):
    text = commodities.lower()
    for name, keys in GROUPS:
        if any(k in text for k in keys):
            return name
    return "Other"


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def deposits():
    sites, excluded = [], []
    with open(MRDS_CSV, encoding="latin-1", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["country"] != "South Africa":
                continue
            lat, lon = _num(row["latitude"]), _num(row["longitude"])
            if lat is None or lon is None:
                continue
            if not (ZA_LAT[0] < lat < ZA_LAT[1] and ZA_LON[0] < lon < ZA_LON[1]):
                excluded.append(f"{row['site_name'].strip()} ({lat}, {lon})")
                continue
            commodities = ", ".join(c for c in (row["commod1"], row["commod2"]) if c)
            sites.append({"name": row["site_name"].strip(), "lat": round(lat, 4), "lon": round(lon, 4),
                          "group": _group(row["commod1"] or commodities), "commodities": commodities[:120],
                          "type": (row["dep_type"] or "").strip()[:60], "status": (row["dev_stat"] or "").strip()})
    return sites, excluded


def holes():
    by_hole = defaultdict(list)
    max_depth = {}
    with open(THABA_CSV, encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            pt, pd = _num(row["Pt_ICP_ppm"]), _num(row["Pd_ICP_ppm"])
            by_hole[row["BH_ID"]].append({
                "from": _num(row["DepthFrom"]), "to": _num(row["DepthTo"]), "seam": row["Stratigraphy"],
                "cr2o3": _num(row["Cr2O3_%"]), "pt_pd": (round(pt + pd, 3) if pt is not None and pd is not None else None),
            })
            max_depth[row["BH_ID"]] = _num(row["MaxDepth"])
    return {hole: {"max_depth": max_depth[hole], "intervals": sorted(rows, key=lambda r: r["from"] or 0)}
            for hole, rows in sorted(by_hole.items())}


def seam_summary(hole_map):
    acc = defaultdict(lambda: {"n": 0, "cr": [], "pge": [], "depth": []})
    for hole in hole_map.values():
        for r in hole["intervals"]:
            a = acc[r["seam"]]
            a["n"] += 1
            if r["cr2o3"] is not None:
                a["cr"].append(r["cr2o3"])
            if r["pt_pd"] is not None:
                a["pge"].append(r["pt_pd"])
            if r["from"] is not None:
                a["depth"].append(r["from"])
    mean = lambda v: round(sum(v) / len(v), 2) if v else None
    return sorted(({"seam": s, "intervals": a["n"], "mean_cr2o3": mean(a["cr"]), "mean_pt_pd": mean(a["pge"]),
                    "mean_depth": mean(a["depth"])} for s, a in acc.items()), key=lambda r: r["seam"])


def main():
    hole_map = holes()
    sites, excluded = deposits()
    data = {
        "sources": {
            "deposits": {"name": "USGS Mineral Resources Data System (MRDS)", "file": "mrds-csv.zip",
                         "sha256": _sha(MRDS_ZIP), "downloaded": "2026-09-30",
                         "note": "USGS stopped systematic updates in 2011: a historical inventory of deposit locations.",
                         "excluded_bad_coordinates": excluded},
            "holes": {"name": "Thaba chromitite borehole assays, Bushveld Complex",
                      "doi": "10.17632/dc8jcnbcvk.1", "licence": "CC BY 4.0", "sha256": _sha(THABA_CSV),
                      "note": "No collar coordinates in the public file: shown as downhole logs, not on the map."},
        },
        "deposits": sites,
        "holes": hole_map,
        "seams": seam_summary(hole_map),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"wrote {OUT}: {len(data['deposits'])} deposits, {len(hole_map)} holes, "
          f"{sum(len(h['intervals']) for h in hole_map.values())} intervals, {OUT.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
