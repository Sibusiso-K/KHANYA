"""REEFPRINT Live local server: serves the app and routes assistant questions to an LLM (optional).

    python presentation/belt-monitor/server.py            # http://127.0.0.1:8531/
    REEFPRINT_LLM_PROVIDER=aiml        AIML_API_KEY=...        REEFPRINT_LLM_MODEL=<model id>  python server.py
    REEFPRINT_LLM_PROVIDER=featherless FEATHERLESS_API_KEY=... REEFPRINT_LLM_MODEL=<model id>  python server.py

Where the keys go: ONLY in this server's environment (or a .env you source yourself). They are never written to disk
by this program, never sent to the browser, and never logged. Both providers are OpenAI-compatible:
    AIML        https://api.aimlapi.com/v1/chat/completions
    Featherless https://api.featherless.ai/v1/chat/completions
The language model is a ROUTER only (PLAN-live-v6.md §G): it receives just the user's question plus the tool schema
and must return one allowlisted tool with typed arguments. It never sees data, imported files or tool results, and
nothing it writes is shown to the user — the browser renders answers from code. Without a key the browser's
deterministic offline parser routes instead.

Safety (Codex round-1/2 findings): binds 127.0.0.1 only; Host and Origin checked; per-run session token required on the
API; static allowlist (no listing, no symlinks, no traversal); upstream allowlist; request size, timeout, max tokens,
rate limit and a daily cap; sanitised errors.
"""
import http.server, json, os, re, secrets, socketserver, sys, threading, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = int(os.environ.get("REEFPRINT_PORT", "8531"))
TOKEN = secrets.token_urlsafe(24)
PROVIDERS = {"aiml": ("https://api.aimlapi.com/v1/chat/completions", "AIML_API_KEY"),
             "featherless": ("https://api.featherless.ai/v1/chat/completions", "FEATHERLESS_API_KEY")}
PROVIDER = os.environ.get("REEFPRINT_LLM_PROVIDER", "").strip().lower()
MODEL = os.environ.get("REEFPRINT_LLM_MODEL", "").strip()
KEY = os.environ.get(PROVIDERS[PROVIDER][1], "") if PROVIDER in PROVIDERS else ""
TOOLS = {"explain_prediction": {"sample_id": r"^(GMET|M1)-\d{4}$"}, "query_samples": {"target": r"^WI$", "state": r"^adverse_or_crossing$", "decision": r"^(verify|default)$"},
         "plant_status": {}, "bushveld_status": {}, "compare_with_lab": {}, "switch_view": {"view": r"^(live|bushveld|plant|lab|evidence|where)$"},
         "export": {"kind": r"^(lims|opcua|geojson|prov)$"}, "generate_report": {}, "help": {}}
SYSTEM = ("You are a router for the REEFPRINT Live mining app. Reply with ONLY a JSON object {\"tool\": <name>, \"args\": {...}} "
          "choosing one tool for the user's question. Tools: explain_prediction(sample_id like GMET-0004 or M1-0012); "
          "query_samples(target='WI', state='adverse_or_crossing') or query_samples(decision='verify'|'default'); plant_status(); "
          "bushveld_status(); compare_with_lab(); switch_view(view in live|bushveld|plant|lab|evidence|where); "
          "export(kind in lims|opcua|geojson|prov); generate_report(); help(). Never answer the question yourself.")
STATIC_EXT = {".html", ".js", ".json", ".csv", ".gz", ".woff2", ".png", ".txt"}
ALLOWED_DIRS = {"", "live", "live/showcase", "live/showcase/GEOMET", "live/showcase/MINERAL1", "live/samples", "fonts", "rgb"}
RATE = {"window": [], "day": 0, "day_key": time.strftime("%Y-%m-%d")}
LOCK = threading.Lock()


def route_llm(q):
    body = json.dumps({"model": MODEL, "max_tokens": 120, "temperature": 0,
                       "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": q}]}).encode()
    url = PROVIDERS[PROVIDER][0]
    req = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY})
    with urllib.request.urlopen(req, timeout=20) as r:
        out = json.loads(r.read(200_000))
    text = out["choices"][0]["message"]["content"]
    m = re.search(r"\{.*\}", text, re.S)
    j = json.loads(m.group(0)) if m else {}
    return validate(j)


def validate(j):
    tool, args = j.get("tool"), j.get("args") or {}
    if tool not in TOOLS or not isinstance(args, dict):
        return {"tool": "help", "args": {}}
    clean = {}
    for k, v in args.items():
        pat = TOOLS[tool].get(k)
        if pat and isinstance(v, str) and re.match(pat, v):
            clean[k] = v
    return {"tool": tool, "args": clean}


class Handler(http.server.SimpleHTTPRequestHandler):
    server_version = "REEFPRINT"
    sys_version = ""

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (time.strftime("%H:%M:%S"), fmt % args))   # no headers, no bodies, no keys

    def _host_ok(self):
        return self.headers.get("Host", "") in (f"127.0.0.1:{PORT}", f"localhost:{PORT}")

    def _send(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, {"error": "forbidden host"})
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        rel = path.lstrip("/") or "index.html"
        p = (ROOT / rel)
        try:
            rp = p.resolve(strict=True)
        except (FileNotFoundError, OSError):
            return self._send(404, {"error": "not found"})
        if ROOT not in rp.parents and rp != ROOT or p.is_symlink() or rp.is_dir() or rp.suffix not in STATIC_EXT \
                or str(Path(rel).parent).replace("\\", "/").replace(".", "") not in {d.replace(".", "") for d in ALLOWED_DIRS}:
            return self._send(404, {"error": "not found"})
        if rel == "index.html":
            html = rp.read_text(encoding="utf-8").replace('<meta name="reef-token" content="">', f'<meta name="reef-token" content="{TOKEN}">')
            b = html.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' blob: data:; media-src 'self' blob:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'")
            self.end_headers()
            self.wfile.write(b)
            return
        self.path = "/" + rel
        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/route":
            return self._send(404, {"error": "not found"})
        if not self._host_ok():
            return self._send(403, {"error": "forbidden host"})
        origin = self.headers.get("Origin")
        if origin not in (None, f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"):
            return self._send(403, {"error": "forbidden origin"})
        if not secrets.compare_digest(self.headers.get("X-Reef-Token", ""), TOKEN):
            return self._send(401, {"error": "missing or wrong session token"})
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0 or n > 2000:
            return self._send(413, {"error": "request too large"})
        try:
            q = str(json.loads(self.rfile.read(n)).get("q", ""))[:300]
        except Exception:
            return self._send(400, {"error": "bad request"})
        if not (PROVIDER in PROVIDERS and KEY and MODEL):
            return self._send(200, {"mode": "offline"})
        with LOCK:
            now = time.time()
            RATE["window"] = [t for t in RATE["window"] if now - t < 60]
            if RATE["day_key"] != time.strftime("%Y-%m-%d"):
                RATE["day_key"], RATE["day"] = time.strftime("%Y-%m-%d"), 0
            if len(RATE["window"]) >= 20 or RATE["day"] >= 300:
                return self._send(429, {"error": "rate limit"})
            RATE["window"].append(now)
            RATE["day"] += 1
        try:
            r = route_llm(q)
            r["provider"] = PROVIDER
            return self._send(200, r)
        except Exception:
            return self._send(200, {"mode": "offline", "note": "provider unavailable"})


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    srv = Server(("127.0.0.1", PORT), Handler)
    mode = f"{PROVIDER} ({MODEL})" if (PROVIDER in PROVIDERS and KEY and MODEL) else "offline parser (no LLM key configured)"
    print(f"REEFPRINT Live on http://127.0.0.1:{PORT}/  ·  assistant router: {mode}")
    srv.serve_forever()
