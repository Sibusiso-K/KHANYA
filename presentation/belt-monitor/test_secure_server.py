"""Security tests for app_server.py (docs/19 section 6). Run: python -m unittest presentation/belt-monitor/test_secure_server.py -v
Starts the real server on a free port with a throwaway data directory, then attacks it."""
import http.client
import io
import json
import os
import shutil
import socket
import sqlite3
import sys
import tempfile
import threading
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TMP = tempfile.mkdtemp(prefix="reef_sec_")
with socket.socket() as _s:
    _s.bind(("127.0.0.1", 0))
    PORT = _s.getsockname()[1]
os.environ.update({"REEFPRINT_DATA": TMP, "REEFPRINT_PORT": str(PORT), "REEFPRINT_LOGIN_LIMIT_PER_MIN": "40"})
os.environ.pop("REEFPRINT_ALLOW_EXTERNAL_LLM", None)
sys.path.insert(0, str(HERE))
import app_server  # noqa: E402
from secure import authn, ledger, store, vault as vlt  # noqa: E402

HOST = f"127.0.0.1:{PORT}"
PW = "correct-horse-battery-9"


def req(method, path, body=None, headers=None, cookie=None, raw=False):
    c = http.client.HTTPConnection("127.0.0.1", PORT, timeout=20)
    h = {"Host": HOST}
    if body is not None and not raw:
        body = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    if cookie:
        h["Cookie"] = f"reef_sess={cookie}"
    h.update(headers or {})
    c.request(method, path, body=body, headers=h)
    r = c.getresponse()
    data = r.read()
    try:
        js = json.loads(data)
    except ValueError:
        js = None
    out = (r.status, dict(r.getheaders()), js, r.getheader("Set-Cookie"))
    c.close()
    return out


def cookie_of(set_cookie):
    return set_cookie.split(";", 1)[0].split("=", 1)[1]


def login(name, pw=PW, cookie=None):
    st, h, js, sc = req("POST", "/api/login", {"username": name, "password": pw}, cookie=cookie)
    return st, (cookie_of(sc) if sc else None), (js or {}).get("csrf")


class SecureServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = app_server.make_server(PORT)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        con = store.connect(str(app_server.DB))
        for name, role in (("op1", "operator"), ("met1", "metallurgist"), ("min1", "mineralogist"), ("lock1", "operator")):
            authn.create_user(con, name, role, PW)
        con.close()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()
        shutil.rmtree(TMP, ignore_errors=True)

    def real_count(self):
        con = sqlite3.connect(str(app_server.DB))
        n = con.execute("SELECT COUNT(*) FROM ledger").fetchone()[0]
        con.close()
        return n

    # -- surface -----------------------------------------------------------------------------------------------
    def test_headers_on_static(self):
        st, h, _, _ = req("GET", "/")
        self.assertEqual(st, 200)
        self.assertIn("script-src 'self'", h["Content-Security-Policy"])
        self.assertNotIn("unsafe-inline';", h["Content-Security-Policy"].split("script-src")[1].split(";")[0])
        self.assertEqual(h["X-Frame-Options"], "DENY")
        self.assertEqual(h["X-Content-Type-Options"], "nosniff")

    def test_traversal_and_private_files_blocked(self):
        for p in ("/../server.py", "/app_server.py", "/secure/vault.py", "/manage.py", "/%2e%2e/CLAUDE.md",
                  "/data_secure/reefprint.db", "/" + Path(TMP).name + "/reefprint.db"):
            self.assertEqual(req("GET", p)[0], 404, p)

    def test_bad_host_and_origin(self):
        self.assertEqual(req("GET", "/", headers={"Host": "evil.example"})[0], 403)
        st, _, _, sc = req("POST", "/api/guest")
        self.assertEqual(st, 200)
        self.assertEqual(req("POST", "/api/guest", headers={"Origin": "https://evil.example"})[0], 403)

    def test_methods_and_body_limits(self):
        self.assertEqual(req("PUT", "/api/me")[0], 405)
        st, _, js, sc = req("POST", "/api/guest")
        ck, csrf = cookie_of(sc), js["csrf"]
        big = b"{" + b" " * 9000 + b"}"
        self.assertEqual(req("POST", "/api/route", big, {"X-CSRF": csrf, "Content-Type": "application/json"}, ck, raw=True)[0], 413)

    # -- authentication --------------------------------------------------------------------------------------------
    def test_api_requires_session(self):
        self.assertEqual(req("GET", "/api/me")[0], 401)
        self.assertEqual(req("GET", "/api/me", cookie="forged-token")[0], 401)

    def test_login_generic_error_and_lockout(self):
        st1, _, _ = login("nobody", "x" * 14)
        st2, _, _ = login("lock1", "wrong-password-123")
        self.assertEqual((st1, st2), (401, 401))
        for _ in range(5):
            login("lock1", "wrong-password-123")
        st3, ck, _ = login("lock1", PW)
        self.assertEqual(st3, 401, "a locked account must refuse even the right password")

    def test_zz_login_rate_limit(self):
        codes = [login("nobody", "wrong-password-123")[0] for _ in range(45)]
        self.assertIn(429, codes, "login attempts from one client must be throttled")

    def test_session_fixation(self):
        _, old, _ = login("op1")
        _, new, _ = login("op1", cookie=old)
        self.assertNotEqual(old, new)
        self.assertEqual(req("GET", "/api/me", cookie=old)[0], 401, "the pre-login token must be invalidated")
        self.assertEqual(req("GET", "/api/me", cookie=new)[0], 200)

    def test_csrf_required(self):
        _, ck, csrf = login("met1")
        ev = {"type": "note", "body": {"note": "csrf test"}}
        self.assertEqual(req("POST", "/api/ledger/event", ev, cookie=ck)[0], 403)
        self.assertEqual(req("POST", "/api/ledger/event", ev, {"X-CSRF": "wrong"}, ck)[0], 403)
        self.assertEqual(req("POST", "/api/ledger/event", ev, {"X-CSRF": csrf}, ck)[0], 200)

    # -- authorisation ---------------------------------------------------------------------------------------------
    def test_role_enforcement(self):
        _, op, op_csrf = login("op1")
        _, met, met_csrf = login("met1")
        st, _, js, _ = req("POST", "/api/ledger/event", {"type": "advice_shown", "body": {"sample": "GMET-0004", "decision": "verify"}}, {"X-CSRF": met_csrf}, met)
        self.assertEqual(st, 200)
        seq = js["seq"]
        self.assertEqual(req("POST", "/api/ledger/event", {"type": "approve", "ref": seq, "body": {"note": "x"}}, {"X-CSRF": op_csrf}, op)[0], 403)
        self.assertEqual(req("POST", "/api/ledger/event", {"type": "acknowledge", "ref": seq, "body": {}}, {"X-CSRF": op_csrf}, op)[0], 200)
        self.assertEqual(req("POST", "/api/ledger/event", {"type": "approve", "ref": seq, "body": {"note": "within envelope"}}, {"X-CSRF": met_csrf}, met)[0], 200)
        self.assertEqual(req("POST", "/api/ledger/checkpoint", {}, {"X-CSRF": op_csrf}, op)[0], 403)
        self.assertEqual(req("POST", "/api/upload/csv", b"x", {"X-CSRF": op_csrf}, op, raw=True)[0], 403)
        self.assertEqual(req("POST", "/api/ledger/event", {"type": "approve", "ref": 999999, "body": {}}, {"X-CSRF": met_csrf}, met)[0], 422)
        self.assertEqual(req("POST", "/api/ledger/event", {"type": "launch_missiles", "body": {}}, {"X-CSRF": met_csrf}, met)[0], 403)
        self.assertEqual(req("POST", "/api/ledger/event", {"type": "note", "body": {"note": {"nested": 1}}}, {"X-CSRF": met_csrf}, met)[0], 422)

    def test_guest_is_sandboxed(self):
        before = self.real_count()
        st, _, js, sc = req("POST", "/api/guest")
        ck, csrf = cookie_of(sc), js["csrf"]
        st, _, js, _ = req("POST", "/api/ledger/event", {"type": "approve", "body": {"note": "demo"}}, {"X-CSRF": csrf}, ck)
        self.assertEqual((st, js["sandbox"]), (200, True))
        self.assertEqual(self.real_count(), before, "a guest must never write the real ledger")
        st, _, cp, _ = req("POST", "/api/ledger/checkpoint", {}, {"X-CSRF": csrf}, ck)
        self.assertEqual(st, 200)
        self.assertNotEqual(cp["checkpoint"]["public_keys"], app_server.VAULT.public_keys(), "guests must not obtain production signatures")

    def test_guest_rate_limit_on_router(self):
        st, _, js, sc = req("POST", "/api/guest")
        ck, csrf = cookie_of(sc), js["csrf"]
        codes = [req("POST", "/api/route", {"q": "help"}, {"X-CSRF": csrf}, ck)[0] for _ in range(6)]
        self.assertEqual(codes[:5], [200] * 5)
        self.assertEqual(codes[5], 429)

    # -- ledger integrity and post-quantum signatures ---------------------------------------------------------------
    def test_ledger_append_only_tamper_and_checkpoint(self):
        _, met, csrf = login("met1")
        for i in range(3):
            req("POST", "/api/ledger/event", {"type": "note", "body": {"note": f"n{i}"}}, {"X-CSRF": csrf}, met)
        st, _, cp, _ = req("POST", "/api/ledger/checkpoint", {}, {"X-CSRF": csrf}, met)
        doc = cp["checkpoint"]
        con = store.connect(str(app_server.DB))
        self.assertTrue(ledger.verify_checkpoint(con, doc)["ok"])
        with self.assertRaises(sqlite3.DatabaseError):
            con.execute("UPDATE ledger SET body = '{}' WHERE seq = 1")
        with self.assertRaises(sqlite3.DatabaseError):
            con.execute("DELETE FROM ledger WHERE seq = 1")
        forged = json.loads(json.dumps(doc))
        forged["hash"] = "f" * 64
        self.assertFalse(ledger.verify_checkpoint(con, forged)["signature_ok"], "editing a signed checkpoint must break both signatures")
        # an attacker with raw DB access drops the trigger and rewrites history: the chain and the checkpoint expose it
        con.execute("DROP TRIGGER ledger_no_update")
        con.execute("UPDATE ledger SET body = ? WHERE seq = 1", (json.dumps({"note": "rewritten"}),))
        self.assertFalse(ledger.verify(con)["ok"])
        self.assertFalse(ledger.verify_checkpoint(con, doc)["ok"])
        con.executescript(store.SCHEMA)
        con.close()

    def test_hybrid_signature_needs_both(self):
        v = vlt.Vault(os.path.join(TMP, "k_sig"))
        msg = b"checkpoint"
        sig = v.sign(msg)
        self.assertTrue(vlt.verify_hybrid(msg, sig, v.public_keys()))
        bad = dict(sig)
        bad["ml_dsa_65"] = sig["ed25519"]
        self.assertFalse(vlt.verify_hybrid(msg, bad, v.public_keys()), "a valid Ed25519 alone must not pass")

    def test_pq_export_roundtrip(self):
        pub, priv = vlt.recipient_keypair()
        env = vlt.seal_for(pub, b"assays and decisions")
        self.assertEqual(env["kem"], "X25519+ML-KEM-768")
        self.assertEqual(vlt.open_for(priv, env), b"assays and decisions")
        _, other = vlt.recipient_keypair()
        with self.assertRaises(Exception):
            vlt.open_for(other, env)

    # -- ingestion -----------------------------------------------------------------------------------------------
    def test_csv_upload_validation(self):
        _, mn, csrf = login("min1")
        head = "sample_id,target_id,value,unit,basis,size_fraction,revision,timestamp\n"
        good = "GMET-0004,GEOMET:WI,14.2,kWh/t,dry_mass,none,1,2026-10-01T08:00:00\n"
        rows = head + good + "GMET-0004,GEOMET:Cu rec,,%,dry_mass,none,1,2026-10-01T08:00:00\n" + \
            'GMET-0004,GEOMET:Mo rec,"=HYPERLINK(""x"")",%,dry_mass,none,1,2026-10-01T08:00:00\n'
        st, _, js, _ = req("POST", "/api/upload/csv", rows.encode(), {"X-CSRF": csrf, "Content-Type": "text/csv"}, mn, raw=True)
        self.assertEqual(st, 200, js)
        self.assertEqual(len(js["accepted"]), 1)
        reasons = " ".join(r["reason"] for r in js["rejected"])
        self.assertIn("blank", reasons)
        self.assertIn("formula", reasons)
        self.assertEqual(req("POST", "/api/upload/csv", b"\xff\xfe\x00bad", {"X-CSRF": csrf}, mn, raw=True)[0], 422)

    def test_image_upload_strips_exif_and_refuses_polyglots(self):
        from PIL import Image
        st, _, js, sc = req("POST", "/api/guest")
        ck, csrf = cookie_of(sc), js["csrf"]
        im = Image.new("RGB", (64, 48), (120, 90, 60))
        exif = Image.Exif()
        exif[0x010F] = "SecretCameraMaker"
        buf = io.BytesIO()
        im.save(buf, "JPEG", exif=exif)
        raw = buf.getvalue() + b"<script>alert(1)</script>"
        self.assertIn(b"SecretCameraMaker", raw)
        st, _, js, _ = req("POST", "/api/upload/image", raw, {"X-CSRF": csrf}, ck, raw=True)
        self.assertEqual(st, 200, js)
        self.assertTrue(js["checks"]["metadata_stripped"])
        con = store.connect(str(app_server.DB))
        uid = js["upload_id"]
        blob = (Path(TMP) / "uploads" / (uid + ".bin")).read_bytes()
        clean = app_server.VAULT.unseal(blob, uid.encode())
        self.assertNotIn(b"SecretCameraMaker", clean)
        self.assertNotIn(b"<script>", clean)
        self.assertNotIn(b"SecretCameraMaker", blob, "stored file must be encrypted")
        con.close()
        self.assertEqual(req("POST", "/api/upload/image", b"\x89PNG\r\n\x1a\n" + b"junk" * 50, {"X-CSRF": csrf}, ck, raw=True)[0], 422)
        self.assertEqual(req("POST", "/api/upload/image", b"MZ\x90\x00 not an image", {"X-CSRF": csrf}, ck, raw=True)[0], 422)


if __name__ == "__main__":
    unittest.main(verbosity=2)
