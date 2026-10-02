"""Uploads: lab CSVs and photos. Validate, normalise, strip metadata, encrypt at rest, expire guest files.

Photos are quality-gated only (focus, exposure): no ore prediction is made from a phone photo, because no labelled
phone-camera dataset exists to validate one (rule 5: the conservative default is to route the sample to the lab).
"""
import csv
import io
import json
import os
import re
import secrets
import time

import numpy as np
from PIL import Image, ImageOps

Image.MAX_IMAGE_PIXELS = 40_000_000       # decompression-bomb guard
MAX_CSV, MAX_IMG, MAX_ROWS = 2_000_000, 8_000_000, 20_000
GUEST_TTL_S = 24 * 3600
NEED = ["sample_id", "target_id", "value", "unit", "basis", "size_fraction", "revision", "timestamp"]
NUM = re.compile(r"^-?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$")
SID = re.compile(r"^[A-Za-z0-9_.@\-]{1,64}$")
FORMULA = re.compile(r"^[=+\-@\t\r]")


def sniff_image(raw):
    if raw[:3] == b"\xff\xd8\xff":
        return "JPEG"
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        return "PNG"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "WEBP"
    return None


def process_image(raw):
    """Returns (clean_jpeg_bytes, checks). Raises ValueError with a reason on refusal."""
    if len(raw) > MAX_IMG:
        raise ValueError("image over 8 MB")
    kind = sniff_image(raw)
    if kind is None:
        raise ValueError("not a JPEG, PNG or WebP file (checked by content, not by name)")
    try:
        Image.open(io.BytesIO(raw)).verify()
        im = Image.open(io.BytesIO(raw))
        if im.format != kind:
            raise ValueError("file content and format disagree")
        im = ImageOps.exif_transpose(im).convert("RGB")
    except (Image.DecompressionBombError, OSError, SyntaxError) as e:
        raise ValueError(f"image refused: {type(e).__name__}")
    im.thumbnail((2048, 2048))
    out = io.BytesIO()
    im.save(out, "JPEG", quality=88, optimize=True)          # re-encoded: EXIF, GPS and any trailing payload are dropped
    g = np.asarray(im.convert("L"), dtype=np.float64)
    lap = 4 * g[1:-1, 1:-1] - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
    rgb = np.asarray(im, dtype=np.uint8)
    clip = float(((rgb.max(2) >= 250) | (rgb.min(2) <= 5)).mean())
    checks = {"width": im.width, "height": im.height, "focus_laplacian_var": round(float(lap.var()), 1),
              "focus_ok": bool(lap.var() >= 60), "clipped_fraction": round(clip, 4), "exposure_ok": bool(clip <= 0.05),
              "metadata_stripped": True,
              "decision": "CONSERVATIVE DEFAULT: route the sample to the lab or microscope. No ore prediction is made from photos (no validated phone-camera dataset)."}
    return out.getvalue(), checks


def check_csv(raw, registry):
    """Structural and registry checks mirrored from the browser importer. Returns (accepted_rows, rejects)."""
    if len(raw) > MAX_CSV:
        raise ValueError("CSV over 2 MB")
    if b"\x00" in raw:
        raise ValueError("binary content in a CSV")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError("CSV must be UTF-8")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        raise ValueError("empty CSV")
    head = [h.strip() for h in rows[0]]
    missing = [c for c in NEED if c not in head]
    if missing:
        raise ValueError("missing columns: " + ", ".join(missing))
    if len(rows) - 1 > MAX_ROWS:
        raise ValueError("over 20,000 rows")
    ix = {c: head.index(c) for c in NEED}
    reg = {t["id"]: t for t in registry["targets"]}
    ok, bad, seen = [], [], set()
    for n, r in enumerate(rows[1:], start=2):
        g = lambda c: (r[ix[c]] if ix[c] < len(r) else "").strip()
        if any(len(x) > 200 for x in r):
            bad.append((n, "cell longer than 200 characters")); continue
        sid, tid, val, ts, rev = g("sample_id"), g("target_id"), g("value"), g("timestamp"), g("revision")
        if not SID.match(sid):
            bad.append((n, "invalid sample id")); continue
        if val == "":
            bad.append((n, "blank value is not zero; refused")); continue
        if FORMULA.match(val) and not NUM.match(val):
            bad.append((n, "spreadsheet formula refused")); continue
        if not NUM.match(val):
            bad.append((n, "value is not a plain number")); continue
        if not re.match(r"^\d{1,6}$", rev):
            bad.append((n, "revision must be a whole number")); continue
        if not re.match(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?", ts):
            bad.append((n, "timestamp missing or not ISO 8601")); continue
        t = reg.get(tid)
        if t is None:
            bad.append((n, "unknown target id")); continue
        if g("unit") not in t["units_accepted"]:
            bad.append((n, "unit not accepted for this target")); continue
        if g("basis") != t["basis"]:
            bad.append((n, "basis does not match the registry")); continue
        key = (sid, tid, rev)
        if key in seen:
            bad.append((n, "duplicate sample/target/revision")); continue
        seen.add(key)
        ok.append({"sample_id": sid, "target_id": tid, "value": float(val) * t["units_accepted"][g("unit")],
                   "unit_in": g("unit"), "revision": int(rev), "timestamp": ts})
    return ok, bad


def store(con, vault, updir, owner, kind, content, meta, guest):
    """Encrypt and record an upload. Files live outside the web root and are never served raw."""
    import hashlib
    os.makedirs(updir, exist_ok=True)
    purge(con, updir)
    uid = secrets.token_urlsafe(12)
    with open(os.path.join(updir, uid + ".bin"), "wb") as f:
        f.write(vault.seal(content, uid.encode()))
    now = time.time()
    con.execute("INSERT INTO uploads(id, owner, kind, sha256, size, created, expires, meta) VALUES (?,?,?,?,?,?,?,?)",
                (uid, owner, kind, hashlib.sha256(content).hexdigest(), len(content), now, now + GUEST_TTL_S if guest else None, json.dumps(meta)))
    return uid


def purge(con, updir, now=None):
    now = now or time.time()
    for r in con.execute("SELECT id FROM uploads WHERE expires IS NOT NULL AND expires < ?", (now,)).fetchall():
        try:
            os.remove(os.path.join(updir, r["id"] + ".bin"))
        except FileNotFoundError:
            pass
        con.execute("DELETE FROM uploads WHERE id = ?", (r["id"],))
