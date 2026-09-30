"""Local REEFPRINT workbench API. Bind to loopback; cloud auth is not implemented."""
from __future__ import annotations
import hashlib, io, json, time, uuid, warnings, threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from PIL import Image

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
model = None
plant = 0.0
app = FastAPI(title="REEFPRINT local research API", version="0.1.0")

def sample_path(sid):
    if sid not in samples:
        raise HTTPException(404, "Sample not found")
    return samples[sid]

def current_result(sid):
    path = sample_path(sid)
    image_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    candidates = sorted(STORE.glob(sid + "-*/result.json"), key=lambda p:p.stat().st_mtime, reverse=True)
    for file in candidates:
        try:
            r = json.loads(file.read_text())
            if r["model_sha"] == MODEL_SHA and r["image_sha"] == image_sha and r.get("contract") == 1:
                r["prediction_source"] = "cached"
                results[r["result_id"]] = r
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
            "sample_count":len(samples),"deployment":"local","cloud_sync":False}

@app.get("/api/samples")
def list_samples():
    return [sample_item(s) for s in samples]

@app.get("/api/samples/{sid}")
def detail(sid:str):
    sample_path(sid)
    return current_result(sid) or blank_result(sid)

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
    r=results.get(result_id) if result_id else current_result(sid)
    if not r or r["id"]!=sid or r["model_sha"]!=MODEL_SHA:
        raise HTTPException(404,"No checkpoint-matched prediction exists.")
    f=STORE / (sid+"-"+r["result_id"]) / (layer+".png")
    if not f.is_file():
        raise HTTPException(404,"Image layer unavailable.")
    return FileResponse(f,media_type="image/png")

@app.post("/api/upload")
async def upload(file:UploadFile=File(...)):
    raw=await file.read(25*1024*1024+1)
    if len(raw)>25*1024*1024:
        raise HTTPException(413,"Micrograph exceeds the 25 MB local upload limit.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error",Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as im:
                im.load()
                if min(im.size)<512 or im.width*im.height>30000000:
                    raise ValueError("Use an image at least 512 px on each side and below 30 million pixels.")
                if im.format not in ("PNG","JPEG","TIFF"):
                    raise ValueError("Use a PNG, JPEG or TIFF micrograph.")
    except Exception as exc:
        raise HTTPException(400,f"Cannot analyse this upload: {exc}")
    sid="upload_"+uuid.uuid4().hex[:12]
    path=UPLOADS/sid
    path.write_bytes(raw)
    samples[sid]=path
    return sample_item(sid)

class InferenceRequest(BaseModel):
    sample_id:str
    mode:Literal["field","full"]="field"

def run_inference(jid,sid,mode):
    global model
    jobs[jid]["status"]="running"
    try:
        import torch
        import numpy as np
        from src.segmentation.model import build_model
        from src.segmentation.patches import single_field_predict,sliding_window_predict
        from src import modal,advisor
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
        with Image.open(io.BytesIO(raw)) as im:
            image=im.convert("RGB")
        with torch.inference_mode():
            if mode=="field":
                labels,confidence,image=single_field_predict(model,image,"cpu")
            else:
                labels,confidence=sliding_window_predict(model,image,"cpu")
        measured=modal.analyse(labels,CLASSES,refine=True)
        rec=advisor.advise(measured,float(confidence))
        if confidence<.85:
            action="Hold for manual review"
            reason=f"Mean model confidence {confidence:.1%} is below the provisional 85% floor. The model suggested: {rec.action}. A specialist must verify the image."
        else:
            action,reason=rec.action,rec.reason
        rid=uuid.uuid4().hex
        directory=STORE/(sid+"-"+rid)
        directory.mkdir()
        image.save(directory/"raw.png")
        rgb=np.zeros((*labels.shape,3),dtype=np.uint8)
        for i,color in enumerate(COLORS):
            rgb[labels==i]=[int(color[k:k+2],16) for k in (1,3,5)]
        mask=Image.fromarray(rgb)
        mask.save(directory/"mask.png")
        Image.blend(image.convert("RGB"),mask,.6).save(directory/"overlay.png")
        phases=[{"name":name,"area_pct":float(np.mean(labels==i)*100),"color":COLORS[i]} for i,name in enumerate(CLASSES)]
        r={"contract":1,"id":sid,"result_id":rid,"prediction_source":"fresh","phases":phases,
           "confidence":float(confidence),"advisory":{"action":action,"reason":reason},
           "model_sha":MODEL_SHA,"image_sha":image_sha,"elapsed_seconds":round(time.perf_counter()-start,3),
           "scope":"512 × 512 centre field" if mode=="field" else "Whole section · advisory only",
           "mode":mode,"verified":verified_hashes.get(sid)==image_sha,
           "association_index":None if measured.liberation is None else float(measured.liberation),
           "created_at":time.time()}
        for layer in ("raw","mask","overlay"):
            r[layer+"_url"]=f"/api/samples/{sid}/image?layer={layer}&result_id={rid}"
        (directory/"result.json").write_text(json.dumps(r,indent=2))
        results[rid]=r
        jobs[jid].update(status="complete",result=r)
    except Exception as exc:
        jobs[jid].update(status="failed",error=str(exc))

@app.post("/api/inferences",status_code=202)
def infer(req:InferenceRequest):
    sample_path(req.sample_id)
    if not MODEL_SHA:
        raise HTTPException(503,"Restore the S2 checkpoint before running inference.")
    if any(j["status"] in ("queued","running") for j in jobs.values()):
        raise HTTPException(409,"An analysis is already running. Wait for it to finish.")
    jid=uuid.uuid4().hex
    jobs[jid]={"id":jid,"status":"queued"}
    pool.submit(run_inference,jid,req.sample_id,req.mode)
    return jobs[jid]

@app.get("/api/jobs/{jid}")
def job(jid:str):
    if jid not in jobs:
        raise HTTPException(404,"Job not found")
    return jobs[jid]

class SimulationRequest(BaseModel):
    result_id:str

def refusal(r):
    if not r.get("verified"):return "Unverified upload: advisory only. Nothing sent to OPC UA."
    if r.get("model_sha")!=MODEL_SHA:return "Checkpoint mismatch: generate a new prediction."
    if r.get("mode")!="field":return "Full-section results are advisory only."
    if r.get("confidence",0)<.85:return "Confidence below the provisional 85% floor. Setting held."
    if time.time()-r.get("created_at",0)>1800:return "Result is older than 30 minutes. Run a fresh analysis."
    if r["advisory"]["action"]!="Grind finer":return "This advisory does not request regrinding. Current setting retained."
    return None

@app.post("/api/simulate")
def simulate(req:SimulationRequest):
    global plant
    r=results.get(req.result_id)
    if not r:
        raise HTTPException(404,"Result unavailable; open or analyse the sample first.")
    with simulation_lock:
        reason=refusal(r)
        if reason:
            event={"state":"held","before":plant,"after":plant,"reason":reason}
        else:
            from dashboard.control import send_command
            event=asdict(send_command("Grind finer",plant))
            plant=event["after"]
        event.update(result_id=req.result_id,created_at=time.time(),simulator_only=True)
        with (STORE/"simulation-events.jsonl").open("a") as f:
            f.write(json.dumps(event)+"\n")
        return event

@app.get("/api/report")
def report():
    matched=MODEL_SHA==KNOWN_SHA
    metrics={"mean_iou":.4543,"pixel_accuracy":.7716,"n_test_images":12,
        "classes":[{"name":n,"iou":iou,"recall":recall,"color":c} for n,c,iou,recall in
        zip(CLASSES,COLORS,[.8756,.3537,0,.6866,.3555],[.9266,.9287,0,.7129,.7128])]} if matched else None
    return {"model_sha":MODEL_SHA,"checkpoint_available":bool(MODEL_SHA),"checkpoint_matches_report":matched,
        "report_source":"reports/END-TO-END-LOCAL-DEMO-2026-09-30.md (recorded Kaggle run; not reevaluated by this UI)",
        "metrics":metrics,"historical_baseline":{"model_sha_prefix":"de7135a","mean_iou":.5725,"pixel_accuracy":.8914,"active":False},
        "limitations":["Magnetite IoU is zero: the active checkpoint does not detect that phase.",
        "Only 12 publisher-held-out S2 sections; no prospective South African ore or plant validation.",
        "Live field inference measures one 512 px centre crop. It is not a whole-section estimate.",
        "Mean confidence is uncalibrated; the 85% simulation floor is provisional.",
        "The stronger historical baseline belongs to another checkpoint and is not used for this screen.",
        "Runtime reports server-side decode, inference and analysis; it excludes network upload.",
        "No measured recovery gain, physical XRF device, or live plant connection."],
        "download_url":"/api/report/download"}

@app.get("/api/report/download")
def report_download():
    return FileResponse(ROOT/"reports/END-TO-END-LOCAL-DEMO-2026-09-30.md",media_type="text/markdown",filename="REEFPRINT-recorded-accuracy-report.md")

dist=ROOT/"frontend/dist"
if dist.is_dir():
    app.mount("/",StaticFiles(directory=dist,html=True),name="frontend")

