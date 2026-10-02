"""The decision record: append-only (SQLite triggers), hash-chained, with hybrid post-quantum-signed checkpoints.

Claim (docs/19): internal consistency checking plus externally anchored checkpoints. Edits and truncation are detected
against a checkpoint held outside the server. Deleting the whole database is not prevented: offline backups cover that.
Outcomes are new events that reference an earlier seq; history is never edited.
"""
import hashlib
import json
import math
import re
import time

from .vault import verify_hybrid

GENESIS = "0" * 64
KEY_RE = re.compile(r"^[a-z_]{1,32}$")


def canonical(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash(prev, rec):
    return hashlib.sha256((prev + canonical(rec)).encode("utf-8")).hexdigest()


def validate_body(body):
    """A flat, small, typed body: no nested objects, bounded strings, finite numbers. Returns an error string or None."""
    if not isinstance(body, dict) or len(body) > 16:
        return "body must be an object with at most 16 fields"
    for k, v in body.items():
        if not KEY_RE.match(k):
            return f"bad field name {k[:40]!r}"
        if isinstance(v, bool) or v is None:
            continue
        if isinstance(v, (int, float)):
            if not math.isfinite(v):
                return f"{k} is not finite"
        elif isinstance(v, str):
            if len(v) > 500:
                return f"{k} longer than 500 characters"
        elif isinstance(v, list):
            if len(v) > 12 or not all(isinstance(x, str) and len(x) <= 64 for x in v):
                return f"{k} must be a short list of short strings"
        else:
            return f"{k} has an unsupported type"
    return None


def append(con, etype, ref, actor_role, actor, body, now=None):
    err = validate_body(body)
    if err:
        raise ValueError(err)
    con.execute("BEGIN IMMEDIATE")   # single writer: the chain head cannot move under us
    try:
        last = con.execute("SELECT seq, hash FROM ledger ORDER BY seq DESC LIMIT 1").fetchone()
        seq, prev = (last["seq"] + 1, last["hash"]) if last else (1, GENESIS)
        if ref is not None and con.execute("SELECT 1 FROM ledger WHERE seq = ?", (ref,)).fetchone() is None:
            raise ValueError("ref does not exist")
        ts = round(now or time.time(), 3)
        rec = {"seq": seq, "ts": ts, "type": etype, "ref": ref, "actor_role": actor_role, "actor": actor, "body": body}
        h = _hash(prev, rec)
        con.execute("INSERT INTO ledger(seq, ts, type, ref, actor_role, actor, body, prev_hash, hash) VALUES (?,?,?,?,?,?,?,?,?)",
                    (seq, ts, etype, ref, actor_role, actor, canonical(body), prev, h))
        con.execute("COMMIT")
        return {"seq": seq, "hash": h}
    except Exception:
        con.execute("ROLLBACK")
        raise


def verify(con):
    prev, n = GENESIS, 0
    for r in con.execute("SELECT * FROM ledger ORDER BY seq"):
        n += 1
        rec = {"seq": r["seq"], "ts": r["ts"], "type": r["type"], "ref": r["ref"], "actor_role": r["actor_role"],
               "actor": r["actor"], "body": json.loads(r["body"])}
        if r["seq"] != n or r["prev_hash"] != prev or _hash(prev, rec) != r["hash"]:
            return {"ok": False, "first_bad_seq": r["seq"], "n": n}
        prev = r["hash"]
    return {"ok": True, "n": n, "head": prev}


def ledger_id(vault):
    return hashlib.sha256(canonical(vault.public_keys()).encode()).hexdigest()[:24]


def checkpoint(con, vault, now=None):
    v = verify(con)
    if not v["ok"]:
        raise ValueError(f"chain broken at seq {v['first_bad_seq']}; refusing to sign")
    doc = {"ledger_id": ledger_id(vault), "seq": v["n"], "hash": v["head"], "ts": round(now or time.time(), 3),
           "alg": "Ed25519 + ML-DSA-65 (FIPS 204), both must verify", "public_keys": vault.public_keys()}
    doc["signatures"] = vault.sign(canonical(doc).encode("utf-8"))
    con.execute("INSERT INTO checkpoints(seq, hash, ts, doc) VALUES (?,?,?,?)", (doc["seq"], doc["hash"], doc["ts"], canonical(doc)))
    return doc


def verify_checkpoint(con, doc):
    """An externally held checkpoint must be correctly signed AND still match the ledger at its seq (truncation/edit check)."""
    body = {k: v for k, v in doc.items() if k != "signatures"}
    sig_ok = verify_hybrid(canonical(body).encode("utf-8"), doc.get("signatures", {}), doc.get("public_keys", {}))
    row = con.execute("SELECT hash FROM ledger WHERE seq = ?", (doc.get("seq"),)).fetchone()
    chain = verify(con)
    return {"signature_ok": sig_ok, "seq_present": row is not None, "hash_matches": bool(row) and row["hash"] == doc.get("hash"),
            "chain_ok": chain["ok"], "ok": sig_ok and bool(row) and row["hash"] == doc.get("hash") and chain["ok"]}
