"""REEFPRINT API: loopback research demo or authenticated Supabase workspace."""
from __future__ import annotations
import hashlib, io, json, time, uuid, warnings, threading, os, re, logging
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, Response, JSONResponse
from webapi import cloud, assistant, candidate_report
import contextvars
import ipaddress
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from PIL import Image
from PIL import UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/raw/lumenstone/S2_v2/imgs/test"
CKPT = ROOT / "checkpoints/lumenstone_s2_patches/best.pt"
STORE = ROOT / ".workbench"
STORE.mkdir(exist_ok=True)
UPLOADS = STORE / "uploads"
UPLOADS.mkdir(exist_ok=True)
KNOWN_SHA = "fb78727d4859947d3605ccf9374f8defbc40897e9cf1b1922a52c1832d387067"
CLASSES = ["background", "chalcopyrite", "magnetite", "pyrrhotite", "pentlandite"]
COLORS = ["#8c96a1", "#f28136", "#d6ac25", "#119eae", "#9562d1"]
MODEL_SHA = hashlib.file_digest(CKPT.open("rb"), "sha256").hexdigest() if CKPT.exists() else ""
CKPT_STAMP = CKPT.stat().st_mtime_ns if CKPT.exists() else None
samples = {p.stem: p for p in sorted(DATA.glob("test_*.jpg"))}
verified_hashes = {s: hashlib.sha256(p.read_bytes()).hexdigest() for s,p in samples.items()}
for p in UPLOADS.glob("upload_*"):
    samples[p.stem] = p
jobs: dict = {}
results: dict = {}
pool = ThreadPoolExecutor(max_workers=1)
model_lock = threading.Lock()
simulation_lock = threading.Lock()
record_lock = threading.Lock()
model = None
model_ready = False
plants: dict[str, float] = {}
plant_sessions: set[str] = set()
@asynccontextmanager
async def lifespan(_app):
    threading.Thread(target=_warm_model, name="khanya-model-warmup", daemon=True).start()
    yield

app = FastAPI(title="REEFPRINT local research API", version="0.1.0", lifespan=lifespan)
CHECKPOINT_METRICS_PATH = ROOT / "reports" / "checkpoint-metrics.json"
CHECKPOINT_RECORD = json.loads(CHECKPOINT_METRICS_PATH.read_text(encoding="utf-8"))
CHECKPOINT_METRICS = CHECKPOINT_RECORD["checkpoints"]
APPROVED_MODEL_SHA = CHECKPOINT_RECORD.get("approved_for_demo", "")
APPROVED_REASON = CHECKPOINT_RECORD.get("approved_reason", "")
_startup_record = CHECKPOINT_METRICS.get(MODEL_SHA)
# uvicorn.error is the logger uvicorn prints at INFO; this module's own logger is silent under it.
logging.getLogger("uvicorn.error").log(
    logging.INFO if MODEL_SHA and MODEL_SHA == APPROVED_MODEL_SHA else logging.WARNING,
    "KHANYA model active sha=%s mIoU=%s %s", MODEL_SHA[:8] or "none",
    _startup_record.get("mean_iou", "unknown") if _startup_record else "unknown",
    "APPROVED" if MODEL_SHA and MODEL_SHA == APPROVED_MODEL_SHA else "NOT APPROVED")

def _warm_model():
    global model, model_ready
    if not CKPT.exists():
        logging.getLogger("uvicorn.error").warning("KHANYA warm-up skipped: checkpoint is missing")
        return
    try:
        import torch
        torch.set_num_threads(2)
        from src.segmentation.model import build_model
        with model_lock:
            if model is None:
                model = build_model(num_classes=5, pretrained=False)
                model.load_state_dict(torch.load(CKPT, map_location="cpu", weights_only=True))
                model.eval()
            ready = model
            with torch.inference_mode():
                model(torch.zeros((1, 3, 512, 512)))
        model_ready = True
    except Exception as exc:
        logging.getLogger("uvicorn.error").warning("KHANYA warm-up failed: %s", exc)

def tenant():
    return cloud.state(STORE, {sid: path for sid, path in samples.items() if sid in verified_hashes})

def workspace_store():
    return tenant()["store"] if cloud.identity.get() else STORE

def workspace_uploads():
    return workspace_store() / "uploads" if cloud.identity.get() else UPLOADS

def workspace_samples():
    return tenant()["samples"] if cloud.identity.get() else samples

def workspace_results():
    return tenant()["results"] if cloud.identity.get() else results

def workspace_jobs():
    return tenant()["jobs"] if cloud.identity.get() else jobs

def workspace_plants():
    return tenant()["plants"] if cloud.identity.get() else plants

def workspace_sessions():
    return tenant()["plant_sessions"] if cloud.identity.get() else plant_sessions

@app.middleware("http")
async def workspace_security(request, call_next):
    cfg = cloud.config()
    protected = request.url.path.startswith("/api/") and request.url.path not in (
        "/api/health", "/api/config", "/api/report", "/api/report/download")
    if not protected:
        return await call_next(request)
    token_context = None
    try:
        if cfg["auth_required"]:
            if not cfg["cloud_sync"]:
                raise HTTPException(503, "Public deployment requires Supabase configuration.")
            authorization = request.headers.get("authorization", "")
            if not authorization.startswith("Bearer ") or len(authorization) > 16384:
                raise HTTPException(401, "Sign in to access your workspace.")
            from starlette.concurrency import run_in_threadpool
            user = await run_in_threadpool(cloud.verify, authorization[7:])
            token_context = cloud.identity.set(user)
            # Refresh remote data at the library boundary, avoiding downloads during polling.
            if request.url.path == "/api/samples" and request.method == "GET":
                await run_in_threadpool(cloud.hydrate, tenant())
        else:
            host = request.client.host if request.client else ""
            try:
                local = ipaddress.ip_address(host).is_loopback
            except ValueError:
                local = host == "testclient"
            if not local:
                raise HTTPException(403, "Local demo access is restricted to loopback. Configure Supabase for public access.")
        response = await call_next(request)
        response.headers["Cache-Control"] = "private, no-store"
        return response
    except HTTPException as exc:
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    finally:
        if token_context is not None:
            cloud.identity.reset(token_context)

@app.get("/api/config")
def public_config():
    return cloud.config()

def sample_path(sid):
    if sid not in workspace_samples():
        raise HTTPException(404, "Sample not found")
    return workspace_samples()[sid]

def current_result(sid):
    path = sample_path(sid)
    image_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    candidates = sorted(workspace_store().glob(sid + "-*/result.json"), key=lambda p:p.stat().st_mtime, reverse=True)
    for file in candidates:
        try:
            r = json.loads(file.read_text())
            if r["model_sha"] == MODEL_SHA and r["image_sha"] == image_sha and r.get("contract") == 1:
                r["prediction_source"] = "cached"
                workspace_results()[r["result_id"]] = r
                return r
        except (OSError, ValueError, KeyError):
            pass
    return None

def sample_item(sid):
    with Image.open(sample_path(sid)) as im:
        size = list(im.size)
    return {"id": sid, "dimensions": size, "dataset": "LumenStone S2 test" if sid in verified_hashes else "Uploaded micrograph",
            "thumbnail_url": f"/api/samples/{sid}/image?layer=original", "has_prediction": current_result(sid) is not None}

def blank_result(sid):
    return {"id":sid,"result_id":None,"prediction_source":"unavailable","phases":[],"confidence":None,
            "advisory":{"action":"No recommendation yet","reason":"Run analysis first."},"model_sha":MODEL_SHA,
            "elapsed_seconds":None,"raw_url":f"/api/samples/{sid}/image?layer=original",
            "overlay_url":None,"mask_url":None,"verified":sid in verified_hashes}

@app.get("/api/health")
def health():
    return {"status":"ok","checkpoint_available": bool(MODEL_SHA), "model_sha":MODEL_SHA,
            "model_approved": bool(MODEL_SHA and MODEL_SHA == APPROVED_MODEL_SHA),
            "approved_model_sha": APPROVED_MODEL_SHA,
            "model_ready": model_ready,
            "sample_count":len(workspace_samples()),"deployment":"public" if cloud.config()["auth_required"] else "local","cloud_sync":cloud.config()["cloud_sync"],"auth_required":cloud.config()["auth_required"]}

@app.get("/api/samples")
def list_samples():
    return [sample_item(s) for s in workspace_samples()]

@app.get("/api/samples/{sid}")
def detail(sid:str):
    sample_path(sid)
    return current_result(sid) or blank_result(sid)

class RecordAssay(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)
    element: str = Field(min_length=1, max_length=30)
    value: float = Field(ge=0)
    unit: str = Field(min_length=1, max_length=30)


class SampleRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)
    sample_label: str = Field(default="", max_length=200)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    depth: float | None = Field(default=None, ge=0)
    notes: str = Field(default="", max_length=10000)
    assays: list[RecordAssay] = Field(default_factory=list, max_length=200)
    assayFile: str = Field(default="", max_length=255)


class RecordUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    expected_version: int = Field(ge=0)
    record: SampleRecord


def record_path(sid: str):
    sample_path(sid)
    if not re.fullmatch(r"[A-Za-z0-9_-]+", sid):
        raise HTTPException(400, "Invalid sample identifier")
    return workspace_store() / "records" / (sid + ".json")


def read_record(path: Path, sid: str):
    if not path.exists():
        return {"sample_id": sid, "version": 0, "updated_at": None, "record": {}}
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
        if (envelope["sample_id"] != sid or type(envelope["version"]) is not int
                or envelope["version"] < 1 or not isinstance(envelope["updated_at"], str)):
            raise ValueError("Invalid record envelope")
        SampleRecord.model_validate(envelope["record"])
        return envelope
    except (OSError, ValueError, KeyError, TypeError):
        raise HTTPException(500, "Stored sample record cannot be read. Restore the local record before saving.")


@app.get("/api/samples/{sid}/record")
def get_record(sid: str):
    if cloud.identity.get():
        sample_path(sid)
        return cloud.get_record(sid)
    path = record_path(sid)
    with record_lock:
        return read_record(path, sid)


@app.put("/api/samples/{sid}/record")
def put_record(sid: str, request: RecordUpdate):
    if cloud.identity.get():
        cloud.save_sample(sid, sample_path(sid)) if sid in verified_hashes else None
        return cloud.save_record(sid, request.expected_version, request.record.model_dump(exclude_unset=True))
    path = record_path(sid)
    with record_lock:
        current = read_record(path, sid)
        if request.expected_version != current["version"]:
            raise HTTPException(409, f"Sample record changed (current version {current['version']}). Reload before saving.")
        envelope = {"sample_id": sid, "version": current["version"] + 1,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "record": request.record.model_dump(exclude_unset=True)}
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
        try:
            with temporary.open("x", encoding="utf-8") as handle:
                json.dump(envelope, handle, ensure_ascii=False, allow_nan=False)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
        return envelope


@app.get("/api/samples/{sid}/image")
def image(sid:str, layer:Literal["original","raw","overlay","mask"]="original", result_id:str|None=None):
    path=sample_path(sid)
    if layer=="original":
        with Image.open(path) as im:
            im=im.convert("RGB")
            im.thumbnail((1100,900))
            out=io.BytesIO()
            im.save(out,format="JPEG",quality=88)
        return Response(out.getvalue(),media_type="image/jpeg")
    r=workspace_results().get(result_id) if result_id else current_result(sid)
    if not r or r["id"]!=sid or r["model_sha"]!=MODEL_SHA:
        raise HTTPException(404,"No checkpoint-matched prediction exists.")
    f=workspace_store() / (sid+"-"+r["result_id"]) / (layer+".png")
    if not f.is_file():
        raise HTTPException(404,"Image layer unavailable.")
    return FileResponse(f,media_type="image/png")


def grain_evidence_for_result(result_id: str):
    """Return paths for evidence only when its result and source image are current."""
    r = workspace_results().get(result_id)
    if not r or r.get("result_id") != result_id or r.get("model_sha") != MODEL_SHA:
        raise HTTPException(404, "Grain evidence is unavailable for this result.")
    try:
        source = sample_path(r["id"])
        if hashlib.sha256(source.read_bytes()).hexdigest() != r.get("image_sha"):
            raise HTTPException(404, "This inference is stale because its source image changed.")
    except (KeyError, OSError):
        raise HTTPException(404, "Grain evidence is unavailable for this result.")
    directory = workspace_store() / (r["id"] + "-" + result_id)
    try:
        saved = json.loads((directory / "result.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise HTTPException(404, "Grain evidence is unavailable for this result.")
    if (saved.get("result_id") != result_id or saved.get("model_sha") != MODEL_SHA
            or saved.get("image_sha") != r.get("image_sha")):
        raise HTTPException(404, "Grain evidence is unavailable for this result.")
    report_path = directory / "grain-report.json"
    ids_path = directory / "grain-ids.png"
    if not report_path.is_file() or not ids_path.is_file():
        raise HTTPException(404, "Grain evidence is unavailable for this result.")
    return report_path, ids_path


@app.get("/api/results/{result_id}/grains")
def result_grains(result_id: str):
    report_path, _ = grain_evidence_for_result(result_id)
    return json.loads(report_path.read_text(encoding="utf-8"))


@app.get("/api/results/{result_id}/grain-ids.png")
def result_grain_ids(result_id: str):
    _, ids_path = grain_evidence_for_result(result_id)
    return FileResponse(ids_path, media_type="image/png")


@app.post("/api/upload")
async def upload(file:UploadFile=File(...)):
    raw=await file.read(25*1024*1024+1)
    if len(raw)>25*1024*1024:
        raise HTTPException(413,"Micrograph exceeds the 25 MB local upload limit.")
    try:
        from webapi.safety import check_input_colour
        with warnings.catch_warnings():
            warnings.simplefilter("error",Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as im:
                im.load()
                if min(im.size)<512 or im.width*im.height>30000000:
                    raise ValueError("Use an image at least 512 px on each side and below 30 million pixels.")
                if im.format not in ("PNG","JPEG","TIFF"):
                    raise ValueError("Use a PNG, JPEG or TIFF micrograph.")
                check_input_colour(im)
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError,
            Image.DecompressionBombWarning):
        raise HTTPException(400,"This file could not be read as an image. Choose an intact JPG, PNG or TIFF micrograph.")
    except ValueError as exc:
        raise HTTPException(400,f"Cannot analyse this upload: {exc}")
    sid="upload_"+uuid.uuid4().hex[:12]
    path=workspace_uploads()/sid
    path.write_bytes(raw)
    if cloud.identity.get():
        try:
            cloud.save_sample(sid, path, uploaded=True)
        except Exception:
            path.unlink(missing_ok=True)
            raise
    workspace_samples()[sid]=path
    return sample_item(sid)

class InferenceRequest(BaseModel):
    sample_id:str
    mode:Literal["field","full"]="field"

def run_inference(jid,sid,mode):
    global model
    workspace_jobs()[jid].update(status="running",progress={"stage":"preparing"})
    try:
        import torch
        import numpy as np
        from src.segmentation.model import build_model
        from src.segmentation.patches import field_coverage, multi_field_predict, sliding_window_predict
        from src import modal, advisor
        start=time.perf_counter()
        torch.set_num_threads(2)
        if not CKPT.exists() or CKPT.stat().st_mtime_ns!=CKPT_STAMP:
            raise ValueError("Checkpoint changed or disappeared. Restart the service to bind the new model.")
        with model_lock:
            if model is None:
                model=build_model(num_classes=5,pretrained=False)
                model.load_state_dict(torch.load(CKPT,map_location="cpu",weights_only=True))
                model.eval()
        path=sample_path(sid)
        raw=path.read_bytes()
        image_sha=hashlib.sha256(raw).hexdigest()
        from webapi.safety import check_input_colour, input_evidence
        with Image.open(io.BytesIO(raw)) as im:
            image=im.convert("RGB")
        check_input_colour(image)
        eligibility = input_evidence(raw)
        field_count = None
        coverage = None
        if mode == "field":
            field_count, coverage = field_coverage(image.width, image.height)
        from webapi.progress import InferenceEvidence
        evidence = InferenceEvidence(workspace_store(), jid, image.size, CLASSES, COLORS, mode)
        source_size = list(image.size)
        tally={"field_s":[],"confidences":[]}
        def field_progress(completed,total,labels,box,confidence):
            now=time.perf_counter()
            tally["field_s"].append(round(now-tally["last"],3))
            tally["last"]=now
            tally["confidences"].append(float(confidence))
            snapshot = evidence.publish(completed, total, labels, box, confidence)
            workspace_jobs()[jid]["progress"]={"stage":"segmenting","completed":completed,"total":total,
                                              "box":list(box),"image_size":source_size,"evidence":snapshot,
                                              "fields_done":completed,"fields_total":total,
                                              "provisional_phases":snapshot["phases"],
                                              "provisional_confidence":float(np.mean(tally["confidences"]))}
        workspace_jobs()[jid]["progress"]={"stage":"segmenting","completed":0,"total":field_count or 0,
                                          "image_size":source_size,"evidence":evidence.empty()}
        t_inference=tally["last"]=time.perf_counter()
        with torch.inference_mode():
            if mode=="field":
                labels, confidence, mosaic_image, _boxes = multi_field_predict(model, image, "cpu",progress_callback=field_progress)
                # The prediction is a mosaic of actual fields, not a full-section mask.
                # Keep all stored layers aligned and preserve the full-source image at
                # /api/samples/{id}/image?layer=original.
                image = mosaic_image
            else:
                labels,confidence=sliding_window_predict(model,image,"cpu",progress_callback=field_progress)
        t_analysis=time.perf_counter()
        workspace_jobs()[jid]["progress"]={**workspace_jobs()[jid]["progress"],"stage":"measuring"}
        measured=modal.analyse(labels,CLASSES,refine=True)
        rec = advisor.confidence_gate(advisor.advise(measured, float(confidence)), float(confidence))
        action, reason = rec.action, rec.reason
        rid=uuid.uuid4().hex
        directory=workspace_store()/(sid+"-"+rid)
        directory.mkdir()
        from webapi.grain_evidence import write_grain_evidence
        grain_evidence = write_grain_evidence(labels, CLASSES, measured.phase_fractions, directory)
        t_write=time.perf_counter()
        image.save(directory/"raw.png")
        rgb=np.zeros((*labels.shape,3),dtype=np.uint8)
        for i,color in enumerate(COLORS):
            rgb[labels==i]=[int(color[k:k+2],16) for k in (1,3,5)]
        mask=Image.fromarray(rgb)
        mask.save(directory/"mask.png")
        Image.blend(image.convert("RGB"),mask,.6).save(directory/"overlay.png")
        phases=[{"name":name,"area_pct":float(np.mean(labels==i)*100),"color":COLORS[i]} for i,name in enumerate(CLASSES)]
        t_end=time.perf_counter()
        # Measured stage boundaries; the four stages sum to total_s.
        timings={"prepare_s":round(t_inference-start,3),"inference_s":round(t_analysis-t_inference,3),
                 "analysis_s":round(t_write-t_analysis,3),"write_s":round(t_end-t_write,3),
                 "total_s":round(t_end-start,3),"per_field_s":tally["field_s"],
                 "torch_threads":torch.get_num_threads()}
        r={"contract":1,"id":sid,"result_id":rid,"prediction_source":"fresh","phases":phases,
           "confidence":float(confidence),"advisory":{"action":action,"reason":reason},
           "timings":timings,
           "model_sha":MODEL_SHA,"image_sha":image_sha,"elapsed_seconds":timings["total_s"],
           "scope":(f"Quick: {field_count} × 512 px fields across the section · "
                    f"{coverage:.1%} area coverage · mosaic") if mode=="field" else "Full section · advisory only",
           "field_count":field_count,"field_coverage":coverage,
           "grain_count":grain_evidence["n_grains"],
           "payload_grain_count":grain_evidence["n_payload_grains"],
           "mode":mode,
           "association_index":None if measured.liberation is None else float(measured.liberation),
           "created_at":time.time()}
        r.update(eligibility)
        for layer in ("raw","mask","overlay"):
            r[layer+"_url"]=f"/api/samples/{sid}/image?layer={layer}&result_id={rid}"
        if cloud.identity.get():
            workspace_jobs()[jid]["progress"]={**workspace_jobs()[jid]["progress"],"stage":"saving"}
            cloud.save_result(r, directory)
        (directory/"result.json").write_text(json.dumps(r,indent=2))
        workspace_results()[rid]=r
        workspace_jobs()[jid].update(status="complete",result=r)
    except Exception as exc:
        workspace_jobs()[jid].update(status="failed",error=str(exc))

@app.post("/api/inferences",status_code=202)
def infer(req:InferenceRequest):
    sample_path(req.sample_id)
    if not MODEL_SHA:
        raise HTTPException(503,"Restore the S2 checkpoint before running inference.")
    if any(j["status"] in ("queued","running") for j in workspace_jobs().values()):
        raise HTTPException(409,"An analysis is already running. Wait for it to finish.")
    if cloud.identity.get() and req.sample_id in verified_hashes:
        cloud.save_sample(req.sample_id, sample_path(req.sample_id))
    jid=uuid.uuid4().hex
    workspace_jobs()[jid]={"id":jid,"status":"queued","sample_id":req.sample_id,"mode":req.mode,
                           "model_sha":MODEL_SHA,"created_at":time.time()}
    if cloud.identity.get():
        pool.submit(contextvars.copy_context().run,run_inference,jid,req.sample_id,req.mode)
    else:
        pool.submit(run_inference,jid,req.sample_id,req.mode)
    return workspace_jobs()[jid]

@app.get("/api/jobs/{jid}")
def job(jid:str):
    if jid not in workspace_jobs():
        raise HTTPException(404,"Job not found")
    return workspace_jobs()[jid]

@app.get("/api/jobs/{jid}/preview")
def job_preview(jid:str, revision:int|None=None):
    # Job membership is the access boundary, even if a file exists in another
    # workspace. A revision only busts browser caches; this is the latest
    # bounded preview, not an archive of past predictions.
    if jid not in workspace_jobs():
        raise HTTPException(404,"Job not found")
    from webapi.progress import read_preview
    try:
        data, current_revision = read_preview(workspace_store(), jid)
    except (FileNotFoundError, ValueError):
        raise HTTPException(404,"No completed model tile is available yet.")
    return Response(data, media_type="image/png", headers={
        "Cache-Control":"private, no-store", "X-Reefprint-Preview-Revision":str(current_revision),
        "X-Reefprint-Provisional":"true"})

class SimulationRequest(BaseModel):
    result_id:str
    session_id:str

@app.post("/api/simulation-sessions")
def create_simulation_session():
    session_id = uuid.uuid4().hex
    with simulation_lock:
        workspace_plants()[session_id] = 0.0
        workspace_sessions().add(session_id)
    return {"session_id": session_id, "setpoint": workspace_plants()[session_id]}

def refusal(r):
    if not r.get("verified"):return "Unverified upload: advisory only. Nothing sent to OPC UA."
    if not r.get("verified_sample"):return "No byte-for-byte held-out sample match; advisory only. Nothing sent to OPC UA."
    if r.get("model_sha")!=MODEL_SHA:return "Checkpoint mismatch: generate a new prediction."
    if MODEL_SHA != APPROVED_MODEL_SHA:return "Checkpoint is not approved for demo control. Setting held."
    if r.get("mode")!="field":return "Full-section results are advisory only."
    if r.get("confidence",0)<.85:return "Confidence below the provisional 85% floor. Setting held."
    if time.time()-r.get("created_at",0)>1800:return "Result is older than 30 minutes. Run a fresh analysis."
    if r["advisory"]["action"]!="Grind finer":return "This advisory does not request regrinding. Current setting retained."
    return None

@app.post("/api/simulate")
def simulate(req:SimulationRequest):
    r=workspace_results().get(req.result_id)
    if not r:
        raise HTTPException(404,"Result unavailable; open or analyse the sample first.")
    with simulation_lock:
        if req.session_id not in workspace_sessions():
            raise HTTPException(404,"Simulator session unavailable. Start a new local session.")
        reason=refusal(r)
        if reason:
            current=workspace_plants()[req.session_id]
            event={"state":"held","before":current,"after":current,"reason":reason}
        else:
            from dashboard.control import send_command
            event=asdict(send_command("Grind finer",workspace_plants()[req.session_id]))
        workspace_plants()[req.session_id] = event["after"]
        event.update(result_id=req.result_id,created_at=time.time(),simulator_only=True)
        with (workspace_store()/"simulation-events.jsonl").open("a") as f:
            f.write(json.dumps({**event,"session_id":req.session_id})+"\n")
        return event

@app.get("/api/report")
def report():
    checkpoint=CHECKPOINT_METRICS.get(MODEL_SHA)
    metrics={key: checkpoint[key] for key in ("mean_iou","pixel_accuracy","n_test_images","classes")} if checkpoint else None
    return {"model_sha":MODEL_SHA,"checkpoint_available":bool(MODEL_SHA),"model_approved":bool(MODEL_SHA and MODEL_SHA == APPROVED_MODEL_SHA),
        "approved_model_sha":APPROVED_MODEL_SHA,"approved_reason":APPROVED_REASON,"checkpoint_matches_report":checkpoint is not None,
        "report_source":checkpoint["source"] if checkpoint else None,
        "metrics":metrics,
        "metrics_message":None if checkpoint else "Unknown checkpoint; no metrics are available for this SHA-256.",
        "known_checkpoints":[{"model_sha":sha,"mean_iou":record["mean_iou"],
            "pixel_accuracy":record["pixel_accuracy"],"source":record["source"],
            "active":sha==MODEL_SHA} for sha,record in CHECKPOINT_METRICS.items()],
        "limitations":["Magnetite IoU is zero: the active checkpoint does not detect that phase.",
        "Only 12 publisher-held-out S2 sections; no prospective South African ore or plant validation.",
        "Quick inference samples up to six non-overlapping 512 px fields; displayed coverage is the sampled fraction, not a whole-section estimate.",
        "Mean confidence is uncalibrated; the 85% simulation floor is provisional.",
        "Runtime reports server-side decode, inference and analysis; it excludes network upload.",
        "No measured recovery gain, physical XRF device, or live plant connection."],
        "download_url":"/api/report/download"}

CANDIDATE_EVIDENCE_DIR = ROOT / "reports" / "native-selected-test-20261001"

@app.get("/api/reports/native-candidate")
def candidate_evidence():
    try:
        return candidate_report.summary(CANDIDATE_EVIDENCE_DIR, MODEL_SHA)
    except candidate_report.EvidenceUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc

@app.get("/api/reports/native-candidate/download/{artifact_key}")
def candidate_evidence_download(artifact_key: str):
    try:
        # Also binds every download to the measured checkpoint and frozen protocol.
        candidate_report.summary(CANDIDATE_EVIDENCE_DIR, MODEL_SHA)
        path, media_type = candidate_report.verified_artifact(CANDIDATE_EVIDENCE_DIR, artifact_key)
    except KeyError as exc:
        raise HTTPException(404, "Evidence artifact not found.") from exc
    except candidate_report.EvidenceUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    return FileResponse(path, media_type=media_type, filename="REEFPRINT-" + path.name)

class AssistantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    question: str = Field(min_length=1, max_length=3000)
    sample_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    result_id: str | None = Field(default=None, min_length=1, max_length=100)
    use_provider: bool = False
    context_opt_in: bool = False


@app.get("/api/assistant/status")
def assistant_status():
    return assistant.get_status()


@app.post("/api/assistant")
def assistant_respond(request: AssistantRequest):
    source = sample_path(request.sample_id)
    selected = None
    if request.result_id:
        selected = workspace_results().get(request.result_id)
        if selected is None:
            cached = current_result(request.sample_id)
            selected = cached if cached and cached.get("result_id") == request.result_id else None
        if (selected is None or selected.get("id") != request.sample_id
                or selected.get("model_sha") != MODEL_SHA
                or selected.get("image_sha") != hashlib.sha256(source.read_bytes()).hexdigest()):
            raise HTTPException(404, "That result is unavailable for the selected sample and active model.")
    context = {"sample_id": request.sample_id, "result": selected,
               "report": report(), "model_architecture": "DeepLabV3 / ResNet-50",
               "runtime": "local CPU"}
    try:
        return assistant.respond(request.question, context, request.use_provider, request.context_opt_in)
    except assistant.AssistantError as exc:
        raise HTTPException(exc.status_code, str(exc)) from None


@app.get("/api/decisions/{result_id}/download")
def decision_download(result_id: str, event_time: float):
    r = workspace_results().get(result_id)
    if not r:
        raise HTTPException(404, "Open the source sample before exporting its decision.")
    event = None
    log = workspace_store() / "simulation-events.jsonl"
    with simulation_lock:
        if log.exists():
            with log.open() as stream:
                for line in stream:
                    try:
                        candidate = json.loads(line)
                    except ValueError:
                        continue
                    if candidate.get("result_id") == result_id and candidate.get("created_at") == event_time:
                        event = candidate
    if event is None:
        raise HTTPException(404, "No matching simulator event exists for this inference and time.")
    payload = {"sample_id": r["id"], "exported_at": time.time(), "inference": r,
               "simulation": event, "evaluation_source": report()["report_source"],
               "model_sha": r["model_sha"], "scope": "Local simulator only; not live plant control"}
    return Response(json.dumps(payload, indent=2), media_type="application/json",
                    headers={"Content-Disposition": 'attachment; filename="reefprint-decision-evidence.json"'})

@app.get("/api/report/download")
def report_download():
    return FileResponse(ROOT/"reports/END-TO-END-LOCAL-DEMO-2026-09-30.md",media_type="text/markdown",filename="REEFPRINT-recorded-accuracy-report.md")

dist=ROOT/"frontend/dist"
if dist.is_dir():
    app.mount("/",StaticFiles(directory=dist,html=True),name="frontend")




