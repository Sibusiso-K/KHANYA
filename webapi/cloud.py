"""User-token Supabase persistence. No service key or privileged writes."""
from __future__ import annotations
import contextvars
import json
import os
import threading
import uuid
import base64
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from fastapi import HTTPException

identity = contextvars.ContextVar("reefprint_identity", default=None)
tenants: dict = {}
tenant_lock = threading.Lock()

def config():
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
    public = os.getenv("REEFPRINT_DEPLOYMENT", "local") == "public"
    enabled = bool(url and key)
    if key.startswith("sb_secret_"):
        raise RuntimeError("Use a publishable Supabase key, never a secret key")
    if key.count(".") == 2:
        try:
            payload = key.split(".")[1]
            role = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))).get("role")
        except (ValueError, TypeError):
            role = None
        if role == "service_role":
            raise RuntimeError("Use a publishable Supabase key, never a service role key")
    return {"auth_required": public or enabled, "supabase_url": url or None,
            "supabase_publishable_key": key or None, "cloud_sync": enabled}

def request(path, method="GET", body=None, content_type="application/json", token=None, prefer=None):
    cfg = config()
    user = identity.get()
    token = token or (user["token"] if user else None)
    headers = {"apikey": cfg["supabase_publishable_key"], "Authorization": "Bearer " + token,
               "Content-Type": content_type}
    if prefer:
        headers["Prefer"] = prefer
    data = body if isinstance(body, bytes) else json.dumps(body).encode() if body is not None else None
    try:
        with urlopen(Request(cfg["supabase_url"] + path, data=data, method=method, headers=headers), timeout=30) as response:
            raw = response.read()
            return json.loads(raw) if "json" in response.headers.get("Content-Type", "") and raw else raw
    except HTTPError as exc:
        if exc.code in (401, 403):
            raise HTTPException(401, "Session expired or access denied. Sign in again.") from None
        if exc.code == 409:
            raise HTTPException(409, "Sample record changed. Reload before saving.") from None
        raise HTTPException(502, "Cloud persistence failed; retry when Supabase is available.") from None
    except (URLError, TimeoutError):
        raise HTTPException(503, "Supabase is temporarily unavailable.") from None

def verify(token):
    user = request("/auth/v1/user", token=token)
    try:
        uid = str(uuid.UUID(user["id"]))
    except (KeyError, TypeError, ValueError):
        raise HTTPException(401, "Invalid sign-in session")
    if user.get("is_anonymous"):
        raise HTTPException(403, "Sign in with a registered account.")
    return {"id": uid, "token": token}

def state(base, demo):
    user = identity.get()
    if not user:
        return None
    with tenant_lock:
        if user["id"] not in tenants:
            directory = base / "users" / user["id"]
            (directory / "uploads").mkdir(parents=True, exist_ok=True)
            tenants[user["id"]] = {"store": directory, "samples": dict(demo), "jobs": {},
                                    "results": {}, "plants": {}, "plant_sessions": set()}
        return tenants[user["id"]]

def upsert(table, row):
    return request("/rest/v1/" + table, "POST", row, prefer="resolution=merge-duplicates,return=representation")

def storage_path(sid, name):
    return identity.get()["id"] + "/" + sid + "/" + name

def upload_object(path, data, mime="application/octet-stream"):
    # Unique sample/result names make replacement unnecessary.
    return request("/storage/v1/object/reefprint-private/" + quote(path, safe="/"), "POST", data, mime)

def hydrate(state):
    for row in request("/rest/v1/samples?select=sample_id,object_path&object_path=not.is.null"):
        sid = row["sample_id"]
        if not sid.startswith("upload_") or not all(c.isalnum() or c == "_" for c in sid):
            continue
        path = state["store"] / "uploads" / sid
        if not path.exists():
            path.write_bytes(request("/storage/v1/object/authenticated/reefprint-private/" + quote(row["object_path"], safe="/")))
        state["samples"][sid] = path
    for row in request("/rest/v1/results?select=payload,artifacts"):
        result = row["payload"]
        sid, rid = result["id"], result["result_id"]
        if sid not in state["samples"] or not all(c.isalnum() or c == "_" for c in sid) or not rid.isalnum():
            continue
        directory = state["store"] / (sid + "-" + rid)
        directory.mkdir(exist_ok=True)
        for name, object_path in row["artifacts"].items():
            if Path(name).name != name:
                continue
            destination = directory / name
            if not destination.exists():
                destination.write_bytes(request("/storage/v1/object/authenticated/reefprint-private/" + quote(object_path, safe="/")))
        (directory / "result.json").write_text(json.dumps(result))
        state["results"][rid] = result

def save_sample(sid, path, uploaded=False):
    object_path = storage_path(sid, "original") if uploaded else None
    if uploaded:
        upload_object(object_path, path.read_bytes())
    return upsert("samples", {"owner_id": identity.get()["id"], "sample_id": sid,
                              "object_path": object_path, "dataset": "Uploaded micrograph" if uploaded else "LumenStone S2 test"})

def save_result(result, directory):
    artifacts = {}
    for file in directory.iterdir():
        if file.name == "result.json" or not file.is_file():
            continue
        path = storage_path(result["id"], result["result_id"] + "/" + file.name)
        upload_object(path, file.read_bytes())
        artifacts[file.name] = path
    upsert("results", {"owner_id": identity.get()["id"], "result_id": result["result_id"],
                       "sample_id": result["id"], "payload": result, "artifacts": artifacts})

def get_record(sid):
    rows = request("/rest/v1/sample_records?select=sample_id,version,updated_at,record&sample_id=eq." + quote(sid, safe=""))
    return rows[0] if rows else {"sample_id": sid, "version": 0, "updated_at": None, "record": {}}

def save_record(sid, version, record):
    rows = request("/rest/v1/rpc/save_sample_record", "POST", {"p_sample_id": sid, "p_expected_version": version, "p_record": record})
    if not rows:
        raise HTTPException(409, "Sample record changed. Reload before saving.")
    return {key: rows[0][key] for key in ("sample_id", "version", "updated_at", "record")}
