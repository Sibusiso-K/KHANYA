"""REEFPRINT Live, secure server (PLAN-v8 Track S; docs/19). Stdlib HTTP + SQLite + cryptography + pqcrypto + Pillow.

    python presentation/belt-monitor/manage.py init
    python presentation/belt-monitor/manage.py add-user <name> <role>          # password typed at a hidden prompt
    python presentation/belt-monitor/app_server.py                              # http://127.0.0.1:8531/

Environment:
    REEFPRINT_PORT            default 8531
    REEFPRINT_DATA            data directory (database, keys, uploads); default presentation/belt-monitor/data_secure
    REEFPRINT_DATA_KEY        32-byte base64 data key (production: from a secret store; demo: a key file is created)
    REEFPRINT_HOSTS           extra allowed Host values, comma-separated (e.g. the public hostname behind a tunnel)
    REEFPRINT_SECURE_COOKIES  1 behind TLS (adds Secure to cookies and HSTS)
    REEFPRINT_TRUST_PROXY     1 only behind a trusted proxy (then CF-Connecting-IP, else the first X-Forwarded-For entry, keys rate limits;
                          global per-path ceilings still apply, so a forged header cannot lift the total)
REEFPRINT_FRAME_ANCESTORS space-separated origins allowed to frame the app (default none; e.g. https://huggingface.co)
REEFPRINT_SEED_USERS      staff accounts to create at start if missing: "username:role:scrypt$..." separated by ";".
                          Hashes only (manage.py hash-password); never a password. For hosts without a shell.
    REEFPRINT_ALLOW_EXTERNAL_LLM  1 to let the router call AIML/Featherless (question text leaves the machine)

The offline demo server (server.py) is unchanged and still works without any of this.
"""
import http.cookies
import http.server
import json
import os
import socketserver
import sys
import time
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import server as legacy                     # noqa: E402  static allowlist and the LLM router (unchanged)
from secure import authn, ingest, ledger, rbac, store  # noqa: E402
from secure import vault as vlt              # noqa: E402

PORT = int(os.environ.get("REEFPRINT_PORT", "8531"))
DATA = Path(os.environ.get("REEFPRINT_DATA", str(ROOT / "data_secure")))
DB, SANDBOX, UPLOADS = DATA / "reefprint.db", DATA / "sandbox.db", DATA / "uploads"
HOSTS = {f"127.0.0.1:{PORT}", f"localhost:{PORT}"} | {h.strip() for h in os.environ.get("REEFPRINT_HOSTS", "").split(",") if h.strip()}
SECURE_COOKIE = os.environ.get("REEFPRINT_SECURE_COOKIES") == "1"
TRUST_PROXY = os.environ.get("REEFPRINT_TRUST_PROXY") == "1"
ALLOW_EXT_LLM = os.environ.get("REEFPRINT_ALLOW_EXTERNAL_LLM") == "1"
FRAME_ANCESTORS = " ".join(o for o in os.environ.get("REEFPRINT_FRAME_ANCESTORS", "").split() if o.startswith("https://")) or "'none'"
COOKIE = "reef_sess"
CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' blob: data:; media-src 'self' blob:; "
       "connect-src 'self'; worker-src 'self' blob:; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors " + FRAME_ANCESTORS)
LIMITS = {"/api/login": int(os.environ.get("REEFPRINT_LOGIN_LIMIT_PER_MIN", "10")), "/api/guest": 20, "/api/route": 20, "/api/upload/csv": 10, "/api/upload/image": 10}
GUEST_LIMITS = {"/api/route": 5, "/api/upload/csv": 5, "/api/upload/image": 5}
DEFAULT_LIMIT = 120
GLOBAL_LIMITS = {"/api/login": 120, "/api/guest": 600, "/api/route": 300, "/api/upload/csv": 120, "/api/upload/image": 120}  # all clients together
MAX_BODY = {"/api/upload/csv": ingest.MAX_CSV, "/api/upload/image": ingest.MAX_IMG}
DEFAULT_BODY = 8000

DATA.mkdir(parents=True, exist_ok=True)
store.init(str(DB))
store.init(str(SANDBOX))
VAULT = vlt.Vault(str(DATA / "keys"), os.environ.get("REEFPRINT_DATA_KEY"))
VAULT_SANDBOX = vlt.Vault(str(DATA / "keys_sandbox"))   # guests never get a signature from the production key


def seed_users():
    """Create staff accounts from REEFPRINT_SEED_USERS (scrypt hashes) when the host has no shell for manage.py."""
    raw = os.environ.get("REEFPRINT_SEED_USERS", "")
    if not raw.strip():
        return
    con = store.connect(str(DB))
    try:
        for item in raw.replace("\n", ";").split(";"):
            parts = item.strip().split(":", 2)
            if len(parts) != 3:
                continue
            name, role, h = parts
            if role not in rbac.STAFF or not h.startswith("scrypt$") or not name.isascii() or not 2 <= len(name) <= 40:
                continue
            if con.execute("SELECT 1 FROM users WHERE username = ?", (name,)).fetchone() is None:
                con.execute("INSERT INTO users(username, role, pw, created) VALUES (?,?,?,?)", (name, role, h, time.time()))
        con.commit()
    finally:
        con.close()


seed_users()
REGISTRY = json.load(open(ROOT / "live" / "targets.json", encoding="utf-8"))


def reset_sandbox_if_stale():
    """Guests' sandbox ledger resets daily (it is a demo, not a record)."""
    mark = DATA / "sandbox.day"
    today = time.strftime("%Y-%m-%d")
    if not mark.exists() or mark.read_text() != today:
        for suffix in ("", "-wal", "-shm"):
            try:
                os.remove(str(SANDBOX) + suffix)
            except FileNotFoundError:
                pass
        store.init(str(SANDBOX))
        mark.write_text(today)


class Handler(http.server.SimpleHTTPRequestHandler):
    server_version = "REEFPRINT"
    sys_version = ""

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (time.strftime("%H:%M:%S"), fmt % args))   # no headers, bodies, cookies or keys

    # -- common ----------------------------------------------------------------------------------------------------
    def end_headers(self):
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("X-Content-Type-Options", "nosniff")
        if FRAME_ANCESTORS == "'none'":
            self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "camera=(self), microphone=(), geolocation=(), payment=(), usb=()")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        if SECURE_COOKIE:
            self.send_header("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        super().end_headers()

    def _json(self, code, obj, cookies=()):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        for c in cookies:
            self.send_header("Set-Cookie", c)
        self.end_headers()
        self.wfile.write(b)

    def _host_ok(self):
        return self.headers.get("Host", "") in HOSTS

    def _origin_ok(self):
        o = self.headers.get("Origin")
        if o is None:                       # same-origin fetches from older browsers; CSRF token still required after login
            return True
        return urllib.parse.urlparse(o).netloc in HOSTS

    def _client(self):
        if TRUST_PROXY:
            if self.headers.get("CF-Connecting-IP"):
                return self.headers["CF-Connecting-IP"][:64]
            xff = self.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            if xff:
                if xff.count(":") == 1:          # Azure's front end sends ip:port
                    xff = xff.split(":")[0]
                return xff[:64]
        return self.client_address[0]

    def _token(self):
        c = http.cookies.SimpleCookie()
        try:
            c.load(self.headers.get("Cookie", ""))
        except http.cookies.CookieError:
            return None
        return c[COOKIE].value if COOKIE in c else None

    def _cookie(self, token, max_age):
        flags = "HttpOnly; SameSite=Strict; Path=/" + ("; Secure" if SECURE_COOKIE else "")
        return f"{COOKIE}={token}; Max-Age={max_age}; {flags}"

    def _rate_ok(self, con, path, who, guest):
        limit = (GUEST_LIMITS.get(path) if guest else None) or LIMITS.get(path, DEFAULT_LIMIT)
        now, key = time.time(), f"{path}|{who}"
        con.execute("DELETE FROM hits WHERE ts < ?", (now - 60,))
        if path in GLOBAL_LIMITS and con.execute("SELECT COUNT(*) FROM hits WHERE key LIKE ? AND ts >= ?",
                                                 (path.replace("%", "") + "|%", now - 60)).fetchone()[0] >= GLOBAL_LIMITS[path]:
            return False
        n = con.execute("SELECT COUNT(*) FROM hits WHERE key = ? AND ts >= ?", (key, now - 60)).fetchone()[0]
        if n >= limit:
            return False
        con.execute("INSERT INTO hits(key, ts) VALUES (?, ?)", (key, now))
        return True

    def _body(self, path):
        cap = MAX_BODY.get(path, DEFAULT_BODY)
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if n < 0 or n > cap:
            return None, (413, {"error": "request too large"})
        return self.rfile.read(n), None

    # -- GET -------------------------------------------------------------------------------------------------------
    def do_GET(self):
        if not self._host_ok():
            return self._json(403, {"error": "forbidden host"})
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/api/"):
            return self._api("GET", parsed.path, urllib.parse.parse_qs(parsed.query))
        rel = parsed.path.lstrip("/") or "index.html"
        p = ROOT / rel
        try:
            rp = p.resolve(strict=True)
        except (FileNotFoundError, OSError):
            return self._json(404, {"error": "not found"})
        parent = str(Path(rel).parent).replace("\\", "/").replace(".", "")
        if (ROOT not in rp.parents) or p.is_symlink() or rp.is_dir() or rp.suffix not in legacy.STATIC_EXT \
                or parent not in {d.replace(".", "") for d in legacy.ALLOWED_DIRS}:
            return self._json(404, {"error": "not found"})
        self.path = "/" + rel
        return super().do_GET()

    def do_POST(self):
        if not self._host_ok():
            return self._json(403, {"error": "forbidden host"})
        if not self._origin_ok():
            return self._json(403, {"error": "forbidden origin"})
        return self._api("POST", urllib.parse.urlparse(self.path).path, {})

    def do_PUT(self):
        return self._json(405, {"error": "method not allowed"})

    do_DELETE = do_PATCH = do_PUT

    # -- API -------------------------------------------------------------------------------------------------------
    def _api(self, method, path, query):
        con = store.connect(str(DB))
        try:
            if (method, path) in rbac.PUBLIC:
                if not self._rate_ok(con, path, self._client(), False):
                    return self._json(429, {"error": "rate limit"})
                body, err = self._body(path)
                if err:
                    return self._json(*err)
                old = self._token()
                if path == "/api/guest":
                    authn.logout(con, old)
                    token, csrf, role = authn.guest(con)
                    return self._json(200, {"role": role, "csrf": csrf}, [self._cookie(token, authn.GUEST_ABS_S)])
                try:
                    req = json.loads(body or b"{}")
                    username, password = str(req.get("username", ""))[:40], str(req.get("password", ""))[:200]
                    authn.logout(con, old)             # session fixation: a login always issues a fresh token
                    token, csrf, role = authn.login(con, username, password)
                except PermissionError:
                    return self._json(401, {"error": "invalid credentials"})
                except (ValueError, json.JSONDecodeError):
                    return self._json(400, {"error": "bad request"})
                return self._json(200, {"role": role, "csrf": csrf}, [self._cookie(token, authn.ABS_S)])
            sess = authn.session(con, self._token())
            if sess is None:
                return self._json(401, {"error": "sign in or continue as guest"})
            allowed = rbac.route_allowed(method, path, sess["role"])
            if allowed is None:
                return self._json(404, {"error": "not found"})
            if not allowed:
                return self._json(403, {"error": "your role may not do this"})
            if method == "POST" and not authn.csrf_ok(sess, self.headers.get("X-CSRF")):
                return self._json(403, {"error": "missing or wrong CSRF token"})
            guest = sess["role"] == "guest"
            if not self._rate_ok(con, path, sess["actor"], guest):
                return self._json(429, {"error": "rate limit"})
            return self._dispatch(con, method, path, query, sess, guest)
        finally:
            con.close()

    def _dispatch(self, con, method, path, query, sess, guest):
        if path == "/api/me":
            return self._json(200, {"role": sess["role"], "actor": sess["actor"], "csrf": sess["csrf"], "sandbox": guest,
                                    "external_llm": ALLOW_EXT_LLM and bool(legacy.KEY and legacy.MODEL)})
        if path == "/api/logout":
            authn.logout(con, self._token())
            return self._json(200, {"ok": True}, [self._cookie("", 0)])
        if path == "/api/route":
            body, err = self._body(path)
            if err:
                return self._json(*err)
            try:
                q = str(json.loads(body or b"{}").get("q", ""))[:300]
            except (ValueError, json.JSONDecodeError):
                return self._json(400, {"error": "bad request"})
            if not (ALLOW_EXT_LLM and legacy.PROVIDER in legacy.PROVIDERS and legacy.KEY and legacy.MODEL):
                return self._json(200, {"mode": "offline"})
            try:
                r = legacy.route_llm(q)
                r["provider"] = legacy.PROVIDER
                return self._json(200, r)
            except Exception:
                return self._json(200, {"mode": "offline", "note": "provider unavailable"})
        if path in ("/api/upload/csv", "/api/upload/image"):
            raw, err = self._body(path)
            if err:
                return self._json(*err)
            try:
                if path.endswith("csv"):
                    ok, bad = ingest.check_csv(raw, REGISTRY)
                    meta = {"accepted": len(ok), "rejected": len(bad), "reasons": bad[:50]}
                    uid = ingest.store(con, VAULT, str(UPLOADS), sess["actor"], "csv", raw, meta, guest)
                    return self._json(200, {"upload_id": uid, "accepted": ok[:200], "rejected": [{"line": a, "reason": b} for a, b in bad[:200]],
                                            "stored": "encrypted at rest" + (", deleted after 24 h (guest)" if guest else "")})
                clean, checks = ingest.process_image(raw)
                uid = ingest.store(con, VAULT, str(UPLOADS), sess["actor"], "image", clean, {"checks": checks}, guest)
                return self._json(200, {"upload_id": uid, "checks": checks,
                                        "stored": "re-encoded, metadata stripped, encrypted at rest" + (", deleted after 24 h (guest)" if guest else "")})
            except ValueError as e:
                return self._json(422, {"error": str(e)})
        if path == "/api/uploads":
            rows = con.execute("SELECT id, kind, size, created, expires, meta FROM uploads WHERE owner = ? ORDER BY created DESC LIMIT 50", (sess["actor"],)).fetchall()
            return self._json(200, {"uploads": [{**dict(r), "meta": json.loads(r["meta"])} for r in rows]})
        # ledger: guests are always routed to the sandbox
        if guest:
            reset_sandbox_if_stale()
        lcon = store.connect(str(SANDBOX)) if guest else con
        try:
            if path == "/api/ledger/event":
                body, err = self._body(path)
                if err:
                    return self._json(*err)
                try:
                    req = json.loads(body or b"{}")
                    etype, ref, ebody = str(req.get("type", "")), req.get("ref"), req.get("body", {})
                    if ref is not None and not isinstance(ref, int):
                        raise ValueError("ref must be an integer")
                    if not rbac.event_allowed(etype, sess["role"]):
                        return self._json(403, {"error": f"your role may not record '{etype[:30]}'"})
                    if guest:
                        ebody = {**ebody, "demo": True}
                    return self._json(200, {**ledger.append(lcon, etype, ref, sess["role"], sess["actor"], ebody), "sandbox": guest})
                except (ValueError, json.JSONDecodeError) as e:
                    return self._json(422, {"error": str(e)[:200]})
            if path == "/api/ledger":
                after = int((query.get("after") or ["0"])[0]) if (query.get("after") or ["0"])[0].isdigit() else 0
                rows = lcon.execute("SELECT seq, ts, type, ref, actor_role, actor, body, hash FROM ledger WHERE seq > ? ORDER BY seq LIMIT 200", (after,)).fetchall()
                return self._json(200, {"sandbox": guest, "events": [{**dict(r), "body": json.loads(r["body"])} for r in rows]})
            if path == "/api/ledger/verify":
                last = lcon.execute("SELECT doc FROM checkpoints ORDER BY id DESC LIMIT 1").fetchone()
                return self._json(200, {"sandbox": guest, "chain": ledger.verify(lcon), "last_checkpoint": json.loads(last["doc"]) if last else None})
            if path == "/api/ledger/checkpoint":
                return self._json(200, {"sandbox": guest, "checkpoint": ledger.checkpoint(lcon, VAULT_SANDBOX if guest else VAULT),
                                        "keep_this": "Store this signed checkpoint outside the server (print, email, ticket). It proves later edits or truncation."})
        finally:
            if lcon is not con:
                lcon.close()
        return self._json(404, {"error": "not found"})


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = os.name != "nt"

    def server_bind(self):
        if os.name == "nt":
            import socket
            if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def make_server(port=PORT, host="127.0.0.1"):
    return Server((host, port), Handler)


if __name__ == "__main__":
    bind = os.environ.get("REEFPRINT_BIND", "127.0.0.1")
    try:
        srv = make_server(PORT, bind)
    except OSError:
        sys.exit(f"Port {PORT} is already in use. Stop the other server or set REEFPRINT_PORT.")
    print(f"REEFPRINT Live (secure) on http://{bind}:{PORT}/  data: {DATA}  external LLM: {'on' if ALLOW_EXT_LLM else 'off'}")
    srv.serve_forever()
