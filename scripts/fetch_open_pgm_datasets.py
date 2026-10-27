"""Fetch the two open PGM datasets recorded in DATA-SOURCES.md section 6.

Raw data is never committed (see .gitignore), so this script re-creates it under
data/raw/ and refuses any file whose SHA-256 does not match the value recorded
when it was first downloaded on 2026-10-27.

    python scripts/fetch_open_pgm_datasets.py            # both datasets
    python scripts/fetch_open_pgm_datasets.py gfz        # GFZ tables only (about 6 MB)
    python scripts/fetch_open_pgm_datasets.py nist       # NIST archive only (75 MB; about 1.1 GB extracted)

Neither dataset is reflected-light imagery. Read DATA-SOURCES.md section 6
before training on either.
"""
import hashlib
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "data" / "raw"

GFZ_BASE = "https://datapub.gfz.de/download/10.5880.GFZ.DMJQ.2025.006-VGhwej/"
GFZ_PREFIX = "2025-006_Trumbull-et-al_"

DATASETS = {
    "gfz": (
        ROOT / "gfz_thaba_chromitite_2025",
        {
            GFZ_PREFIX + "Data-Description.pdf": "3a45504bd61a9e4adbe09b7463317d9121f5079a5eb80c675736f2fd1a58f54b",
            GFZ_PREFIX + "Figure-1.tiff": "5dd3e77f191c4aa51b58eb431eb3645fb4249b2b2a58499b2913c39a7863a355",
            GFZ_PREFIX + "Figure-2.jpg": "c2d6b6fd6861c2d30cdf27c8eee076d8985aa4f70bfd53140b5ac02352818599",
            GFZ_PREFIX + "Table-1-MG1-EPMA.xlsx": "7d6adb7516ff2d21cb5d06e4c5360cf315d11cbd755646f20b96e338559f2be1",
            GFZ_PREFIX + "Table-2-MG4a-EPMA.xlsx": "74b4698763987db929e7f1c5e8e87c43a198b3131beacd5ddc8170b09bb2da6e",
            GFZ_PREFIX + "Table-3-MG3-EPMA.xlsx": "25d50ac2f87e713504c94339f6632cf59ae02db61f0e0a62b47616c1cac75fed",
            GFZ_PREFIX + "Table-4-PGE.xlsx": "bac1e6e64486ceda195309898c4abc3f90971ee39cffedd75f1f16fafd1594be",
            GFZ_PREFIX + "Table-5-CSD.xlsx": "a23e42222052e5136f0d63c98df5ceba4efbc39c2b58f60d0bf3331c8dff4f3f",
        },
        GFZ_BASE,
    ),
    "nist": (
        ROOT / "nist_pgm_sem_eds_2021",
        {"PGM.tar.gz": "2c81fdde09310d3e2bfcc530094c885de72e1021e2ed6fdf88c9261d9617a162"},
        "https://data.nist.gov/od/ds/mds2-2471/",
    ),
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def download(url, target, attempts=5):
    # data.nist.gov drops long transfers part-way, so resume with a Range header.
    for attempt in range(1, attempts + 1):
        have = target.stat().st_size if target.exists() else 0
        req = urllib.request.Request(url, headers={"Range": f"bytes={have}-"} if have else {})
        try:
            with urllib.request.urlopen(req, timeout=300) as r, open(target, "ab" if have else "wb") as f:
                if have and r.status != 206:
                    f.truncate(0)
                while block := r.read(1 << 20):
                    f.write(block)
            return
        except OSError as e:
            print(f"  attempt {attempt} interrupted ({e}); resuming")
            time.sleep(2)
    raise RuntimeError(f"gave up on {url} after {attempts} attempts")


def fetch(name):
    folder, files, base = DATASETS[name]
    folder.mkdir(parents=True, exist_ok=True)
    for filename, expected in files.items():
        target = folder / filename
        if target.exists() and sha256(target) == expected:
            print(f"ok (cached)  {name}/{filename}")
            continue
        print(f"downloading  {name}/{filename}")
        download(base + filename, target)
        actual = sha256(target)
        if actual != expected:
            target.unlink()
            sys.exit(f"CHECKSUM MISMATCH for {filename}: expected {expected}, got {actual}. File removed.")
        print(f"ok           {name}/{filename}")


if __name__ == "__main__":
    for name in sys.argv[1:] or list(DATASETS):
        if name not in DATASETS:
            sys.exit(f"unknown dataset {name!r}; choose from {', '.join(DATASETS)}")
        fetch(name)
